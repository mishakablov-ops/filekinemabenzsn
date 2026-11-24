"""Приветствие v2: модель героя из Hunyuan3D (T-поза, mike 24.11) + голова из v1 (кудри, венок, аниме-глаза),
скелет рук вручную, взмах правой рукой, фон из v1. Бесшовный цикл 120 кадров.
  python3 build2.py --still 6 18 --out /tmp/s_#.png --size 720
  python3 build2.py --frames /tmp/f --size 1080 --samples 24
Пути: MODEL — glb из Hunyuan, REF — папка с референсами (tex_front/back.png готовит prep.py)."""
import bpy, bmesh, math, sys, os, argparse, numpy as np
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE)); sys.path.insert(0, HERE)
import build as v1                      # голова, материалы, фон
import pal_tpose as pal                 # раскраска палитрой по референсу
MODEL = os.environ.get('MODEL', '/tmp/claude-0/v3/tpose.glb')
N = 120; TAU = math.tau
LIFT = 1.0                              # модель стоит ногами на z=0
HEAD_Z = 0.485 + LIFT                   # основание черепа (шея модели кончается на 0.50)


def sm(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t)


def load_body():
    bpy.ops.import_scene.gltf(filepath=MODEL)
    o = [x for x in bpy.context.scene.objects if x.type == 'MESH'][0]; o.name = 'apollon'
    bpy.context.view_layer.objects.active = o; o.select_set(True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    # срезать голову модели (лицо у Hunyuan размазано) — ставим свою голову из v1
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0005)
    bm.to_mesh(o.data); bm.free()
    pal.paint(o)
    smooth_classes(o, 3)
    drop_islands(o, 30)
    head_texture(o)
    painterly(o)
    o.location.z = LIFT
    bpy.ops.object.transform_apply(location=True)
    return o


def smooth_classes(o, it=2):
    me = o.data; bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
    mi = np.array([f.material_index for f in bm.faces])
    nb = [[g.index for e in f.edges for g in e.link_faces if g.index != f.index] for f in bm.faces]
    bm.free()
    for _ in range(it):
        new = mi.copy()
        for i, n in enumerate(nb):
            if not n: continue
            c = np.bincount(mi[n], minlength=8)
            if c.max() * 2 > len(n) and c.argmax() != mi[i]: new[i] = c.argmax()
        mi = new
    me.polygons.foreach_set('material_index', mi)


def islands(bm, idx):
    seen = set(); out = []
    for f in bm.faces:
        if f.material_index != idx or f.index in seen: continue
        st = [f]; seen.add(f.index); comp = []
        while st:
            g = st.pop(); comp.append(g)
            for e in g.edges:
                for h in e.link_faces:
                    if h.material_index == idx and h.index not in seen: seen.add(h.index); st.append(h)
        out.append(comp)
    return out


BROOCH = Vector((0.114, -0.097, 0.396))      # брошь на модели (до подъёма на LIFT)


def drop_islands(o, minsize):
    """мелкие пятна золота/кожи/тёмного -> ткань; брошь модели -> ткань (ставим чистую брошь кодом)"""
    me = o.data; names = [m.name for m in me.materials]
    bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
    cloth = names.index('ap_cloth'); hair = names.index('ap_hair')
    for nm in ('ap_gold', 'ap_skin', 'ap_dark'):
        for comp in islands(bm, names.index(nm)):
            c = sum((g.calc_center_median() for g in comp), Vector()) / len(comp)
            brooch = nm == 'ap_gold' and ((c - BROOCH).length < 0.06 or (c - Vector((0.113, 0.006, 0.421))).length < 0.07)
            torso = nm == 'ap_gold' and abs(c.x) < 0.24 and -0.12 < c.z < 0.33 and c.y < 0.0   # пояс: рисуем чистую кайму кодом
            if len(comp) < minsize or brooch or torso:
                tgt = hair if c.z > 0.5 and abs(c.x) < 0.22 else cloth
                for g in comp: g.material_index = tgt
    bm.to_mesh(me); bm.free()


def painterly(o):
    """мягкая живописная светотень: AO в складках + тёплый край (сфумато)"""
    for m in o.data.materials:
        nt = m.node_tree; b = nt.nodes['Principled BSDF']; L = nt.links
        src = b.inputs['Base Color'].links[0].from_socket if b.inputs['Base Color'].is_linked else None
        rgb = nt.nodes.new('ShaderNodeRGB'); rgb.outputs[0].default_value = b.inputs['Base Color'].default_value
        base = src or rgb.outputs[0]
        ao = nt.nodes.new('ShaderNodeAmbientOcclusion'); ao.inputs['Distance'].default_value = 0.12; ao.samples = 8
        mao = nt.nodes.new('ShaderNodeMix'); mao.data_type = 'RGBA'; mao.blend_type = 'MULTIPLY'; mao.inputs['Factor'].default_value = 0.45
        L.new(base, mao.inputs[6]); L.new(ao.outputs['AO'], mao.inputs[7])
        lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.35
        warm = nt.nodes.new('ShaderNodeMix'); warm.data_type = 'RGBA'; warm.blend_type = 'MULTIPLY'
        warm.inputs[7].default_value = (*v1.srgb('#f0d2b0'), 1)
        mf = nt.nodes.new('ShaderNodeMath'); mf.operation = 'MULTIPLY'; mf.inputs[1].default_value = 0.8
        L.new(lw.outputs['Facing'], mf.inputs[0]); L.new(mf.outputs[0], warm.inputs['Factor'])
        L.new(mao.outputs[2], warm.inputs[6]); L.new(warm.outputs[2], b.inputs['Base Color'])
        if m.name == 'ap_gold':
            b.inputs['Metallic'].default_value = 0.65; b.inputs['Roughness'].default_value = 0.32
            b.inputs['Coat Weight'].default_value = 0.2


def add_trim(o):
    """чистая золотая кайма гиматия по диагонали пояса: точки лучом на поверхность модели"""
    from mathutils.bvhtree import BVHTree
    dg = bpy.context.evaluated_depsgraph_get(); bvh = BVHTree.FromObject(o, dg)
    for k, (dz, w) in enumerate(((0.0, 0.022), (-0.04, 0.009))):
        pts = []
        for i in range(25):
            t = i / 24; x = -0.20 + 0.40 * t; z = 0.035 + 0.15 * t + dz + LIFT
            hit = bvh.ray_cast(Vector((x, -1.0, z)), Vector((0, 1, 0)))
            if hit[0] is not None: pts.append(hit[0] + hit[1] * 0.006)
        if len(pts) > 3:
            v1.ribbon('trim%d' % k, pts, w, v1.M['gold'], twist_fn=lambda t: 0.0)


def add_brooch(arm):
    """чистая брошь-солнце на груди, привязана к кости chest"""
    root = v1.empty('brooch2', BROOCH + Vector((0, -0.022, LIFT)))
    core = v1.ico('b_core', 0.026, v1.M['gold'], 1, 0.0, (1, 0.45, 1), (0, 0, 0), root, seed=1)
    for k in range(12):
        r = v1.leaf('b_ray', 0.03 if k % 2 else 0.042, 0.014, v1.M['gold'], root)
        r.matrix_basis = Matrix.Rotation(math.tau * k / 12, 4, 'Y') @ Matrix.Translation((0, 0, 0.022))
    ring = v1.ribbon('b_ring', [Vector((0.031 * math.cos(a_), 0, 0.031 * math.sin(a_))) for a_ in [math.tau * i / 24 for i in range(24)]],
                     0.006, v1.M['gold2'], twist_fn=lambda t: math.pi / 2, parent=root, closed=True)
    root.rotation_euler = (0.12, 0, -0.35)
    bpy.context.view_layer.update()
    mw = root.matrix_world.copy()
    root.parent = arm; root.parent_type = 'BONE'; root.parent_bone = 'chest'
    bone = arm.data.bones['chest']
    root.matrix_parent_inverse = (arm.matrix_world @ bone.matrix_local @ Matrix.Translation((0, bone.length, 0))).inverted()
    root.matrix_basis = mw
    return root


HEAD_TEX = os.environ.get('HEAD_TEX', '/tmp/claude-0/v3/tex_tfront_hq.png')


def head_texture(o):
    """голова модели: фото-проекция фронтального T-референса (лицо, глаза, венок) на видимые спереди грани.
    Привязка по меткам: верхний шип z=0.958 -> y=99 px, боковые шипы x=-0.238/0.198 -> 442.5/615 px, 395 px/м."""
    from mathutils.bvhtree import BVHTree
    me = o.data; K = 395.0; X0 = 536.5
    li = np.empty(len(me.loops), int); me.loops.foreach_get('vertex_index', li)
    co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
    P = co[li]
    uv = np.stack([(X0 + P[:, 0] * K) / 1024, 1 - (99 + (0.958 - P[:, 2]) * K) / 1024], 1)
    l = me.uv_layers.new(name='proj'); l.data.foreach_set('uv', uv.ravel())
    m = bpy.data.materials.new('ap_headtex'); m.use_nodes = True; nt = m.node_tree
    b = nt.nodes['Principled BSDF']; b.inputs['Roughness'].default_value = 0.7
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(HEAD_TEX); t.interpolation = 'Linear'
    u = nt.nodes.new('ShaderNodeUVMap'); u.uv_map = 'proj'; nt.links.new(u.outputs[0], t.inputs[0])
    hs = nt.nodes.new('ShaderNodeHueSaturation'); hs.inputs['Value'].default_value = 1.03
    nt.links.new(t.outputs[0], hs.inputs['Color']); nt.links.new(hs.outputs[0], b.inputs['Base Color'])
    me.materials.append(m); mi = len(me.materials) - 1
    bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table(); bvh = BVHTree.FromBMesh(bm)
    d = Vector((0, -1, 0)); sel = []
    for f in bm.faces:
        c = f.calc_center_median()
        if c.z < 0.47 or abs(c.x) > 0.26 or f.normal.y > -0.25:
            continue
        if bvh.ray_cast(c + d * 0.002, d)[0] is None:
            sel.append(f.index)
    bm.free()
    mat_idx = np.empty(len(me.polygons), int); me.polygons.foreach_get('material_index', mat_idx)
    mat_idx[sel] = mi; me.polygons.foreach_set('material_index', mat_idx)
    print('head tex faces', len(sel))


def rig(o):
    ad = bpy.data.armatures.new('rig'); arm = bpy.data.objects.new('rig', ad)
    bpy.context.scene.collection.objects.link(arm)
    bpy.context.view_layer.objects.active = arm; bpy.ops.object.mode_set(mode='EDIT')
    E = ad.edit_bones; y = 0.03; zA = 0.35 + LIFT

    def bone(n, h, t, parent=None, conn=False):
        b = E.new(n); b.head = h; b.tail = t
        if parent: b.parent = E[parent]; b.use_connect = conn
    bone('hips', (0, 0, 0.0), (0, 0, 0.2 + LIFT))
    bone('chest', (0, 0, 0.2 + LIFT), (0, 0, 0.48 + LIFT), 'hips', True)
    for s, sd in ((-1, 'R'), (1, 'L')):
        bone('up.' + sd, (s * 0.20, y, zA), (s * 0.52, y, zA), 'chest')
        bone('fo.' + sd, (s * 0.52, y, zA), (s * 0.82, y, zA), 'up.' + sd, True)
        bone('ha.' + sd, (s * 0.82, y, zA), (s * 0.97, y, zA), 'fo.' + sd, True)
    bpy.ops.object.mode_set(mode='OBJECT')
    o.parent = arm; md = o.modifiers.new('arm', 'ARMATURE'); md.object = arm
    co = np.array([v.co[:] for v in o.data.vertices])
    ax = np.abs(co[:, 0]); z = co[:, 2]
    armzone = (z > 0.15 + LIFT) & (z < 0.52 + LIFT)
    a = np.where(armzone, sm(0.19, 0.25, ax), 0.0)
    W = {
        'hips': 1 - sm(0.15 + LIFT, 0.30 + LIFT, z),
        'chest': sm(0.15 + LIFT, 0.30 + LIFT, z) * (1 - a),
        'up': a * (1 - sm(0.49, 0.55, ax)),
        'fo': a * sm(0.49, 0.55, ax) * (1 - sm(0.79, 0.84, ax)),
        'ha': a * sm(0.79, 0.84, ax)}
    W['hips'] = W['hips'] * (1 - a)
    R = co[:, 0] < 0
    groups = {n: o.vertex_groups.new(name=n) for n in ['hips', 'chest', 'up.R', 'fo.R', 'ha.R', 'up.L', 'fo.L', 'ha.L']}
    for n, w in W.items():
        for sd, mask in (('R', R), ('L', ~R)):
            name = n if n in ('hips', 'chest') else n + '.' + sd
            if n in ('hips', 'chest') and sd == 'L':
                continue
            ww = w if n in ('hips', 'chest') else w * mask
            g = groups[name]
            for i in np.nonzero(ww > 0.003)[0]:
                g.add([int(i)], float(ww[i]), 'REPLACE')
    return arm


def aim(arm, name, d, roll=0.0):
    pb = arm.pose.bones[name]; rest = pb.bone.matrix_local
    d = Vector(d).normalized(); yax = (rest.to_3x3() @ Vector((0, 1, 0))).normalized()
    q = yax.rotation_difference(d)
    from mathutils import Quaternion
    q = Quaternion(d, roll) @ q
    head = arm.pose.bones[pb.parent.name].tail.copy() if pb.bone.use_connect else (arm.matrix_world @ pb.bone.head_local)
    pb.matrix = Matrix.Translation(head) @ (q @ rest.to_quaternion()).to_matrix().to_4x4()
    bpy.context.view_layer.update()


def pose(arm, f, P):
    for pb in arm.pose.bones: pb.rotation_mode = 'QUATERNION'
    arm.pose.bones['chest'].rotation_quaternion = (1, 0, 0, 0)
    bpy.context.view_layer.update()
    br = math.sin(TAU * f / 60)
    ch = arm.pose.bones['chest']
    ch.rotation_mode = 'XYZ'; ch.rotation_euler = (0.01 * br, 0.0, 0.03 * math.sin(TAU * f / N)); bpy.context.view_layer.update()
    w = math.sin(TAU * f / 24)
    aim(arm, 'up.R', (-P['ux'], -0.25, P['uz'] + 0.03 * w), P['roll_u'])
    a = P['fa'] + P['amp'] * w
    aim(arm, 'fo.R', (-math.sin(a), -0.22, math.cos(a)), P['roll_f'])
    b = a + 0.22 * math.sin(TAU * f / 24 - 0.9)
    aim(arm, 'ha.R', (-math.sin(b), -0.18, math.cos(b)), P['roll_f'])
    aim(arm, 'up.L', (0.30, 0.02, -1.0 + 0.01 * br))
    aim(arm, 'fo.L', (0.18, -0.12, -1.0))
    aim(arm, 'ha.L', (0.15, -0.12, -1.0))


def soft_light():
    sun = bpy.data.lights['sun']; sun.energy = 2.3; sun.angle = math.radians(35)
    fill = bpy.data.lights['fill']; fill.energy = 140; fill.size = 5
    fo = bpy.data.objects['fill']; fo.location = (1.2, -2.6, 2.0)
    key = bpy.data.lights.new('key', 'AREA'); key.energy = 160; key.size = 4; key.color = v1.srgb('#fff3e2')
    ko = bpy.data.objects.new('key', key); bpy.context.scene.collection.objects.link(ko)
    ko.location = (-1.8, -2.4, 2.6); ko.rotation_euler = (ko.location * -1).to_track_quat('-Z', 'Y').to_euler()
    rim = bpy.data.lights.new('rim', 'AREA'); rim.energy = 90; rim.size = 2.5; rim.color = v1.srgb('#ffd9a0')
    ro = bpy.data.objects.new('rim', rim); bpy.context.scene.collection.objects.link(ro)
    ro.location = (0.6, 1.6, 2.4); ro.rotation_euler = (Vector((0, 0, 1.5)) - ro.location).to_track_quat('-Z', 'Y').to_euler()
    bg = bpy.context.scene.world.node_tree.nodes['Background']; bg.inputs[1].default_value = 0.8
    bpy.context.scene.view_settings.exposure = -0.42
    w = bpy.context.scene.world.node_tree
    for n in w.nodes:
        if n.type == 'BACKGROUND' and n.name != 'Background': n.inputs[1].default_value = 1.36


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser()
    ap.add_argument('--still', type=int, nargs='*'); ap.add_argument('--frames'); ap.add_argument('--out', default='/tmp/s_#.png')
    ap.add_argument('--size', type=int, default=1080); ap.add_argument('--samples', type=int, default=24)
    ap.add_argument('--cam', default='main'); ap.add_argument('--roll_u', type=float, default=0.0)
    ap.add_argument('--roll_f', type=float, default=-1.57)
    a = ap.parse_args(argv)
    P = dict(ux=0.52, uz=0.80, fa=0.12, amp=0.30, roll_u=a.roll_u, roll_f=a.roll_f)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    v1.make_mats()
    o = load_body(); arm = rig(o)
    add_brooch(arm)
    add_trim(o)
    head = v1.empty('head', (0, 0, HEAD_Z))   # пустышка: голова модели своя, двигается с грудью
    anim = v1.build_world()
    halo = bpy.data.objects['halo']; halo.location = (0, 0.32, 0.74 + LIFT)
    sc = bpy.context.scene
    base = {ob.name: (ob.location.copy(), ob.rotation_euler.copy(), ob.scale.copy()) for k, ob, i in anim}
    bl = []
    for f in range(N + 1):
        sc.frame_set(f); t = f / N
        pose(arm, f, P)
        for pb in arm.pose.bones:
            pb.keyframe_insert('rotation_quaternion'); pb.keyframe_insert('rotation_euler'); pb.keyframe_insert('location')
        head.rotation_euler = (0.04 + 0.03 * math.sin(TAU * f / 60 + 1), -0.10 + 0.04 * math.sin(TAU * t + 0.5), 0.08 + 0.04 * math.sin(TAU * t))
        head.keyframe_insert('rotation_euler')
        k = math.sin(math.pi * (f - 70) / 6) if 70 <= f <= 76 else 0.0
        for b in bl: b.scale = (1, 1, max(k, 1e-4)); b.keyframe_insert('scale')
        for kind, ob, i in anim:
            loc, rot, scl = base[ob.name]
            if kind == 'crystal':
                ob.location = loc + Vector((0, 0, 0.05 * math.sin(TAU * t + i * 1.3))); ob.rotation_euler = (rot.x, rot.y, rot.z + TAU / 4 * t)
            elif kind == 'star':
                s_ = 0.75 + 0.35 * math.sin(TAU * f / 60 + i * 1.7); ob.scale = (s_, s_, s_); ob.rotation_euler = (0, TAU / 4 * t * (1 if i % 2 else -1), 0)
            elif kind == 'halo':
                ob.rotation_euler = (0, TAU / 4 * t, 0)
            elif kind == 'ribbon':
                ob.rotation_euler = (rot.x, rot.y, TAU / 3 * t * (1 if i else -1))
            ob.keyframe_insert('location'); ob.keyframe_insert('rotation_euler'); ob.keyframe_insert('scale')
    v1.CAM = {'main': ((-0.1, -2.6, 1.62), (-0.1, 0.0, 1.47)), 'face': ((0.0, -0.9, 1.70), (0.0, 0.0, 1.66)),
              'wide': ((0.0, -4.2, 1.2), (0.0, 0.0, 1.0))}[a.cam]
    v1.setup(a.size, 'CYCLES', a.samples)
    soft_light()
    sc.render.use_motion_blur = True; sc.render.motion_blur_shutter = 0.4
    sc.cycles.use_adaptive_sampling = True; sc.cycles.adaptive_threshold = 0.01
    if a.still is not None:
        for f in a.still:
            sc.frame_set(f); sc.render.filepath = a.out.replace('#', '%03d' % f); bpy.ops.render.render(write_still=True)
    if a.frames:
        sc.render.filepath = a.frames.rstrip('/') + '/f_###'; bpy.ops.render.render(animation=True)


if __name__ == '__main__':
    main()
