"""The baroness of «Баронесса-пулемётчица» (style «Мемы»): the realistic rigged model (hero/rig_baroness.py ->
assets/baroness_rig.blend, в git — assets3d/people/own/baronessa/) posed with the channel hero's pose code (same bone names, so sila_hero's poses, key_pose
and walk work as they are).

    b = load(coll, loc, heading)                      -> dict like sila_hero.load
    sila_hero.key_pose(b, t, P('stand_strict'))
    alive(b, t0, t1, seed)                            # blinks, breathing, head drift
"""
import math
import os

import bpy
from mathutils import Vector

import lib
import sila_hero as SH

HERE = os.path.dirname(os.path.abspath(__file__))
CANDIDATES = [os.environ.get('BARONESS_RIG', ''),
              os.path.join(HERE, '..', 'assets', 'baroness_rig.blend'),                                        # <id>/blender/assets (ПК)
              os.path.join(HERE, '..', '..', '..', '..', 'assets3d', 'people', 'own', 'baronessa', 'baroness_rig.blend')]  # projects/<id>/blender/sets
BLEND = next((p for p in CANDIDATES if p and os.path.exists(p)), CANDIDATES[1])
# eyes on the rest mesh (metres): x, z, half width, half height
EYES = ((-0.037, 1.540, 0.017, 0.009), (0.041, 1.540, 0.017, 0.009))     # v2 model (baroness_c)


def load(coll=None, loc=(0, 0, 0), heading=0.0, name='Baroness', scale=1.0):
    with bpy.data.libraries.load(os.path.abspath(BLEND), link=False) as (src, dst):
        dst.objects = [n for n in src.objects if n in ('BaronessRig', 'Baroness')]
    rig = next(o for o in dst.objects if o.type == 'ARMATURE')
    body = next(o for o in dst.objects if o.type == 'MESH')
    coll = coll or bpy.context.scene.collection
    for o in (rig, body):
        coll.objects.link(o)
    rig.name, body.name = name + 'Rig', name
    body.parent = rig
    for m in body.modifiers:
        if m.type == 'ARMATURE':
            m.object = rig
    rig.location = loc
    rig.rotation_euler = (0, 0, heading)
    rig.scale = (scale, scale, scale)
    for pb in rig.pose.bones:
        pb.rotation_mode = 'QUATERNION'
    h = dict(rig=rig, body=body, rest={b.name: b.matrix_local.copy() for b in rig.data.bones},
             parent={b.name: (b.parent.name if b.parent else None) for b in rig.data.bones},
             order=[b.name for b in SH._topo(rig.data.bones)])
    h['len'] = {b.name: b.length for b in rig.data.bones}
    hip = rig.data.bones['LeftUpLeg'].head_local
    ank = rig.data.bones['LeftFoot'].head_local
    h['leg'] = (h['len']['LeftUpLeg'], h['len']['LeftLeg'], hip.z - ank.z, ank.z)
    me = body.data
    if 'rest_pos' not in me.attributes:
        co = [0.0] * (3 * len(me.vertices))
        me.vertices.foreach_get('co', co)
        me.attributes.new('rest_pos', 'FLOAT_VECTOR', 'POINT').data.foreach_set('vector', co)
    for m in me.materials:
        _lids(m)
    body['bar_blink'] = 0.0
    return h


def _lids(m):
    """Eyelids for a blink: skin colour drawn over both eyes (rest-pose coordinates) when bar_blink -> 1."""
    if m is None or not m.use_nodes or m.get('bar_lids'):
        return
    nt = m.node_tree
    N, L = nt.nodes, nt.links
    bsdf = next(n for n in N if n.type == 'BSDF_PRINCIPLED')
    src = bsdf.inputs['Base Color'].links[0].from_socket

    def M(op, a, b=0.0):
        n = N.new('ShaderNodeMath')
        n.operation = op
        for s, v in ((n.inputs[0], a), (n.inputs[1], b)):
            if isinstance(v, (int, float)):
                s.default_value = v
            else:
                L.new(v, s)
        return n.outputs[0]
    rest = N.new('ShaderNodeAttribute')             # rest positions stored on the mesh: the lids follow the face
    rest.attribute_type, rest.attribute_name = 'GEOMETRY', 'rest_pos'
    xyz = N.new('ShaderNodeSeparateXYZ')
    L.new(rest.outputs['Vector'], xyz.inputs['Vector'])
    X, Y, Z = xyz.outputs['X'], xyz.outputs['Y'], xyz.outputs['Z']
    blink = N.new('ShaderNodeAttribute')
    blink.attribute_type, blink.attribute_name = 'OBJECT', 'bar_blink'
    mask = None
    for cx, cz, ax, az in EYES:
        u = M('DIVIDE', M('SUBTRACT', X, cx), ax)
        v = M('DIVIDE', M('SUBTRACT', Z, cz), az)
        r = M('ADD', M('MULTIPLY', u, u), M('MULTIPLY', v, v))
        e = M('LESS_THAN', r, 1.0)
        mask = e if mask is None else M('MAXIMUM', mask, e)
    mask = M('MULTIPLY', M('MULTIPLY', mask, M('LESS_THAN', Y, -0.05)), blink.outputs['Fac'])
    mix = N.new('ShaderNodeMix')
    mix.data_type = 'RGBA'
    L.new(mask, mix.inputs['Factor'])
    L.new(src, mix.inputs[6])
    mix.inputs[7].default_value = (0.62, 0.42, 0.34, 1.0)
    L.new(mix.outputs[2], bsdf.inputs['Base Color'])
    m['bar_lids'] = 1


# ----------------------------------------------------------------------------- talking mouth (mike 29.10: «чтобы у неё
# рот под реплики открывался»): a shape key drops the chin/lower lip, the shader draws a dark gap between the lips;
# both follow the loudness of her lines (voice.wav) inside the word spans the timeline gives (shot['mouth']).
F = lib.sec2f
MOUTH = (0.0, 1.477, 0.024)           # x, z of the lips' line on the rest mesh (metres), half width


def _mouth_setup(body):
    me = body.data
    if me.shape_keys and 'MouthOpen' in me.shape_keys.key_blocks:
        return
    if not me.shape_keys:
        body.shape_key_add(name='Basis', from_mix=False)
    sk = body.shape_key_add(name='MouthOpen', from_mix=False)
    mx, mz, mw = MOUTH
    for i, v in enumerate(me.vertices):
        x, y, z = v.co
        if y > -0.03 or abs(x - mx) > mw * 2.6 or not (mz - 0.085 < z < mz + 0.002):
            continue
        wx = max(0.0, 1 - (abs(x - mx) / (mw * 2.6)) ** 2)
        wz = max(0.0, min(1.0, (z - (mz - 0.085)) / 0.03)) if z < mz - 0.055 else 1.0
        sk.data[i].co = v.co + Vector((0, 0.002, -0.011 * wx * wz))
    for m in me.materials:
        _mouth_shader(m)


def _mouth_shader(m):
    if m is None or not m.use_nodes or m.get('bar_mouth'):
        return
    nt = m.node_tree
    N, L = nt.nodes, nt.links
    bsdf = next(n for n in N if n.type == 'BSDF_PRINCIPLED')
    src = bsdf.inputs['Base Color'].links[0].from_socket

    def Mth(op, a, b=0.0):
        n = N.new('ShaderNodeMath')
        n.operation = op
        for s, v in ((n.inputs[0], a), (n.inputs[1], b)):
            if isinstance(v, (int, float)):
                s.default_value = v
            else:
                L.new(v, s)
        return n.outputs[0]
    rest = N.new('ShaderNodeAttribute')
    rest.attribute_type, rest.attribute_name = 'GEOMETRY', 'rest_pos'
    xyz = N.new('ShaderNodeSeparateXYZ')
    L.new(rest.outputs['Vector'], xyz.inputs['Vector'])
    op = N.new('ShaderNodeAttribute')
    op.attribute_type, op.attribute_name = 'OBJECT', 'bar_mouth'
    mx, mz, mw = MOUTH
    hh = Mth('ADD', Mth('MULTIPLY', op.outputs['Fac'], 0.0085), 0.0004)  # gap half height grows with the opening
    u = Mth('DIVIDE', Mth('SUBTRACT', xyz.outputs['X'], mx), mw)
    v = Mth('DIVIDE', Mth('SUBTRACT', xyz.outputs['Z'], mz - 0.004), hh)
    r = Mth('ADD', Mth('MULTIPLY', u, u), Mth('MULTIPLY', v, v))
    inside = Mth('MULTIPLY', Mth('LESS_THAN', r, 1.0), Mth('LESS_THAN', xyz.outputs['Y'], -0.03))
    inside = Mth('MULTIPLY', inside, Mth('GREATER_THAN', op.outputs['Fac'], 0.04))
    mix = N.new('ShaderNodeMix')
    mix.data_type = 'RGBA'
    L.new(inside, mix.inputs['Factor'])
    L.new(src, mix.inputs[6])
    mix.inputs[7].default_value = (0.09, 0.025, 0.025, 1.0)
    L.new(mix.outputs[2], bsdf.inputs['Base Color'])
    m['bar_mouth'] = 1


def lipsync(h, spans, wav, offset, rate=15.0):
    """Key the mouth from the loudness of `wav` (seconds offset+t) inside `spans` [(t0, t1)] of the shot."""
    import wave
    import numpy as np
    body = h['body']
    _mouth_setup(body)
    w = wave.open(wav, 'rb')
    sr, n, ch, sw = w.getframerate(), w.getnframes(), w.getnchannels(), w.getsampwidth()
    a = np.frombuffer(w.readframes(n), dtype=np.int16 if sw == 2 else np.int32).astype(np.float32)
    if ch > 1:
        a = a.reshape(-1, ch).mean(axis=1)
    a /= (np.abs(a).max() + 1e-9)
    kb = body.data.shape_keys.key_blocks['MouthOpen']
    body['bar_mouth'] = 0.0

    def key(t, v):
        body['bar_mouth'] = v
        body.keyframe_insert('["bar_mouth"]', frame=F(t))
        kb.value = v
        kb.keyframe_insert('value', frame=F(t))
    key(0, 0.0)
    for t0, t1 in spans:
        key(max(0, t0 - 0.05), 0.0)
        t = t0
        while t < t1:
            i0, i1 = int((offset + t) * sr), int((offset + t + 1 / rate) * sr)
            seg = a[max(0, i0):max(i0 + 1, min(len(a), i1))]
            rms = float(np.sqrt(np.mean(seg ** 2))) if len(seg) else 0.0
            key(t, min(1.0, max(0.0, (rms - 0.02) * 5.0)))
            t += 1 / rate
        key(t1 + 0.04, 0.0)


def alive(h, t0, t1, seed=0, breath=True, head=True):
    """Blinks every 2.5-5 s (she is stern: fewer blinks than the hero), breathing and a slow head drift."""
    import random
    rnd = random.Random(seed)
    body = h['body']
    SH._key_prop(body, 'bar_blink', t0, 0.0, 'CONSTANT')
    t = t0 + rnd.uniform(0.6, 1.6)
    while t < t1 - 0.2:
        SH._key_prop(body, 'bar_blink', t - 0.06, 0.0, 'LINEAR')
        SH._key_prop(body, 'bar_blink', t, 1.0, 'LINEAR')
        SH._key_prop(body, 'bar_blink', t + 0.06, 1.0, 'LINEAR')
        SH._key_prop(body, 'bar_blink', t + 0.15, 0.0, 'CONSTANT')
        t += rnd.uniform(2.5, 5.0)
    rig = h['rig']
    act = rig.animation_data.action if rig.animation_data else None
    if not act:
        return
    if breath:
        for bn, amp in (('Spine2', 0.010), ('Spine1', 0.005)):
            fc = act.fcurves.find(f'pose.bones["{bn}"].rotation_quaternion', index=1)
            if fc:
                s = fc.modifiers.new('FNGENERATOR')
                s.function_type, s.use_additive = 'SIN', True
                s.amplitude, s.phase_multiplier = amp, 2 * math.pi / (3.8 * lib.FPS)
                s.phase_offset = rnd.uniform(0, 6.28)
    if head:
        for i, amp in ((1, 0.018), (2, 0.014), (3, 0.024)):
            fc = act.fcurves.find('pose.bones["Head"].rotation_quaternion', index=i)
            if fc:
                n = fc.modifiers.new('NOISE')
                n.blend_type, n.strength, n.scale = 'REPLACE', amp, 2.0 * lib.FPS
                n.phase, n.offset = rnd.uniform(1, 50), rnd.uniform(0, 500)


# her poses: hands behind the back (inspection), salute-like hand to the cap, holding the coupon gun, arms crossed
POSES = {
    # v2 is very plump: the arms hang a little away from the body so they do not sink into it
    'stand': dict(SH.BASE, arm=(24, 2), fore=(20, 14)),
    'strict': dict(SH.BASE, arm=(22, -2), fore=(18, 3), head=(0, 3, 0)),            # at attention, arms down
    'hold_gun': dict(SH.BASE, arm=((12, 32), (10, 36)), fore=((-18, 78), (-14, 82)), head=(0, 8, 0), lean=4.0),
    'point': dict(SH.BASE, arm=((10, 2), (6, 88)), fore=((8, 14), (4, 90)), head=(0, -4, 0)),
    'hand_up': dict(SH.BASE, arm=((10, 2), (50, 120)), fore=((8, 14), (30, 170)), head=(0, -6, 0)),
    'bag': dict(SH.BASE, arm=((10, 2), (14, 30)), fore=((8, 14), (8, 95))),          # handbag on the right forearm
    'sit': dict(SH.BASE, arm=(14, 30), fore=(10, 66), thigh=86.0, shin=6.0, spread=2.0),
}


def P(name='stand', **kw):
    p = dict(POSES[name])
    p.update(kw)
    return p


def hand_world(h, side='Right', frame=None):
    """World position of the wrist (to attach props), at the current frame."""
    if frame is not None:
        bpy.context.scene.frame_set(frame)
    rig = h['rig']
    pb = rig.pose.bones[side + 'Hand']
    return rig.matrix_world @ pb.head
