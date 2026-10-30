"""Low-poly friends of the hero (LowPolyShorts pack of KINEMA, CC-BY-4.0, see CREDITS in engine/public/packs/lowpoly-shorts):
Denise, CJ, Emmet, Cesar, Saul. GLB rigs (18 bones) are imported, their bones renamed to the hero's names (LeftArm,
LeftForeArm, LeftUpLeg, LeftLeg, Spine2 ...) by their real side, so every pose of sila_hero.py works on them:
    p = load('cj', coll, loc, heading, height=1.7)
    sila_hero.key_pose(p, t, sila_hero.pose('stand')); sila_hero.walk(p, t0, t1, path)
mouth(p, keys) opens the jaw (shape key jawOpen). Pack clips (Run, FastNod, Scream, ShockRecoil, IdlePhone) can be played
with clip(p, 'Run', t0, t1).
"""
import math
import os

import bpy
from mathutils import Vector

import lib

HERE = os.path.dirname(os.path.abspath(__file__))
DIRS = [os.environ.get('AK_CAST', ''), os.path.join(HERE, '..', 'assets', 'cast')]
F = lib.sec2f
RIG_H = 3.57
NAMES = {'UpperArm': 'Arm', 'Forearm': 'ForeArm', 'Hand': 'Hand', 'Thigh': 'UpLeg', 'Shin': 'Leg', 'Foot': 'Foot'}
HEIGHT = dict(denise=1.62, cj=1.74, emmet=1.70, cesar=1.72, saul=1.70)


def path_of(name):
    for d in DIRS:
        p = os.path.join(d, name + '.glb') if d else ''
        if p and os.path.exists(p):
            return p
    raise SystemExit('cast model not found: ' + name)


def load(name, coll=None, loc=(0, 0, 0), heading=0.0, height=None, keep_clips=False):
    coll = coll or bpy.context.scene.collection
    before = set(bpy.data.objects)
    acts = set(bpy.data.actions)
    bpy.ops.import_scene.gltf(filepath=path_of(name))
    new = [o for o in bpy.data.objects if o not in before]
    rig = next(o for o in new if o.type == 'ARMATURE')
    bodies = []
    for o in new:
        for c in list(o.users_collection):
            c.objects.unlink(o)
        if o.type == 'MESH' and o.parent is None:          # the pack's helper icosphere
            bpy.data.objects.remove(o)
            continue
        coll.objects.link(o)
        if o.type == 'MESH':
            bodies.append(o)
    clips = {a.name.split('.')[0]: a for a in bpy.data.actions if a not in acts}
    if rig.animation_data:
        rig.animation_data.action = None
    # bones by their real side: +x is the character's left (it faces -y like the hero)
    for b in list(rig.data.bones):
        for side in ('Left', 'Right'):
            if b.name.startswith(side) and b.name[len(side):] in NAMES:
                real = 'Left' if b.head_local.x > 0 else 'Right'
                b.name = '_' + real + NAMES[b.name[len(side):]]
    for b in rig.data.bones:
        if b.name.startswith('_'):
            b.name = b.name[1:]
    if 'Chest' in rig.data.bones:
        rig.data.bones['Chest'].name = 'Spine2'
    s = (height or HEIGHT.get(name, 1.7)) / RIG_H
    rig.name = name.capitalize() + 'Rig'
    rig.location = loc
    rig.rotation_mode = 'XYZ'
    rig.rotation_euler = (0, 0, heading)
    rig.scale = (s, s, s)
    for pb in rig.pose.bones:
        pb.rotation_mode = 'QUATERNION'
        pb.rotation_quaternion = (1, 0, 0, 0)
        pb.location = (0, 0, 0)
    for o in bodies:
        for m in o.data.materials:
            _matte(m)
    import sila_hero as H
    h = dict(rig=rig, body=bodies[0] if bodies else None, bodies=bodies, clips=clips, name=name,
             rest={b.name: b.matrix_local.copy() for b in rig.data.bones},
             parent={b.name: (b.parent.name if b.parent else None) for b in rig.data.bones},
             order=[b.name for b in H._topo(rig.data.bones)])
    h['len'] = {b.name: b.length for b in rig.data.bones}
    hip = rig.data.bones['Hips'].head_local
    ank = rig.data.bones['LeftFoot'].head_local
    h['leg'] = (h['len']['LeftUpLeg'], h['len']['LeftLeg'], hip.z - ank.z, ank.z)
    return h


def _matte(m):
    """Game textures: keep the colour map, kill the plastic shine."""
    if not m or not m.use_nodes:
        return
    for n in m.node_tree.nodes:
        if n.type == 'BSDF_PRINCIPLED':
            n.inputs['Roughness'].default_value = 0.8
            try:
                n.inputs['Specular IOR Level'].default_value = 0.25
            except Exception:
                pass
            if not n.inputs['Metallic'].is_linked:
                n.inputs['Metallic'].default_value = 0.0


def mouth(h, keys):
    """keys [(t, 0..1)] on the jawOpen shape key of every body."""
    for o in h['bodies']:
        sk = o.data.shape_keys
        if not sk or 'jawOpen' not in sk.key_blocks:
            continue
        kb = sk.key_blocks['jawOpen']
        for t, v in keys:
            kb.value = v
            kb.keyframe_insert('value', frame=F(t))


def talk(h, t0, t1, rate=7.0, amp=0.6, seed=0):
    import random
    r = random.Random(seed)
    t, ks = t0, [(t0, 0.0)]
    while t < t1:
        t += 1.0 / rate * r.uniform(0.7, 1.3)
        ks.append((min(t, t1), r.uniform(0.25, 1.0) * amp if len(ks) % 2 else 0.05))
    ks.append((t1 + 0.1, 0.0))
    mouth(h, ks)


def clip(h, name, t0, t1=None, speed=1.0):
    """Play a pack clip (NLA strip) from t0; repeats until t1."""
    act = h['clips'].get(name)
    if act is None:
        raise SystemExit(f'no clip {name} on {h["name"]}')
    rig = h['rig']
    rig.animation_data_create()
    tr = rig.animation_data.nla_tracks.new()
    st = tr.strips.new(name, F(t0), act)
    st.scale = 1.0 / speed
    if t1 is not None:
        n = (F(t1) - F(t0)) / max(1.0, (act.frame_range[1] - act.frame_range[0]) * st.scale)
        st.repeat = max(1.0, n)
    st.extrapolation = 'HOLD'
    return st
