"""Main hero of the channel (reference from mike, 26.10.2026), built from code:
a chibi guy with a big head, short black fade haircut, big brown eyes, thick brows, black hoodie with a kangaroo
pocket and grey drawstrings, black joggers, chunky white sneakers.

Same rig contract as people2.person: root pivot at the feet, forward = local -Y, root.scale = height factor
(1.0 = 1.75 m), parts in a dict (root, hips, pelvis, torso, neck, head, thigh/shin/shoe/upper/fore/hand + L/R),
so lib.move_root works. Chibi legs are shorter than people2 legs, so use hero.walk / hero.sit (own leg lengths),
people2.stand works as is. Drop-in for pcommon.hero: hero(loc, heading, coll, pose, name, rng).
"""
import bpy, bmesh, math, random
from mathutils import Vector
import lib
import people2 as P2

L1, L2, ANKLE = 0.22, 0.22, 0.1                  # thigh, shin, ankle height (unscaled)
HIP = ANKLE + L1 + L2                            # 0.54
SHOULDER = (0.255, 0.35)                        # x, z relative to the hip joint
UPPER, FORE = 0.16, 0.14
HEAD_Z = 0.805                                   # head centre above the hip joint (top of hair ~1.71 m)
HEAD_R = (0.298, 0.278, 0.302)                   # head ellipsoid radii x, y (depth), z
A_SWING = 0.42

COL = dict(hoodie='#17181B', pants='#16171A', skin='#E6AE88', hair='#0E0C0B', iris='#4E2C18', shoe='#F3F3F0',
           sole='#E4E3DF', string='#45464B', brow='#1B1612', lips='#B0705E')

_meshes = {}


# ----------------------------------------------------------------------------- mesh helpers
def _mesh(name, bm, smooth=True):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    if smooth:
        me.polygons.foreach_set('use_smooth', [True] * len(me.polygons))
    return me


def _rbox(sx, sy, sz, p=0.55, pz=None, segs=32, rings=20):
    """Rounded box (superellipsoid): half sizes sx, sy, sz; p < 1 makes it boxier, 1 = ellipsoid."""
    pz = p if pz is None else pz
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=rings, radius=1.0)
    for v in bm.verts:
        x, y, z = v.co
        v.co = Vector((math.copysign(abs(x) ** p, x) * sx, math.copysign(abs(y) ** p, y) * sy,
                       math.copysign(abs(z) ** pz, z) * sz))
    return bm


def _head_shape(co):
    """Unit sphere point -> head surface (narrower jaw, fuller cheeks)."""
    x, y, z = co
    if z < 0:
        x *= 1.0 - 0.16 * (-z) ** 1.6
        y *= 1.0 - 0.06 * (-z) ** 1.6
    if y < 0:                                    # flatter face, rounder skull at the back
        y *= 0.94
    return Vector((x * HEAD_R[0], y * HEAD_R[1], z * HEAD_R[2]))


def _on_head(x, z, out=0.0):
    """Point on the face (front, -Y) at head-local x, z, pushed `out` along the normal; returns (point, normal)."""
    best = None
    for i in range(60):                          # a few iterations on the unit sphere are enough
        uz = max(-0.999, min(0.999, z / HEAD_R[2] if best is None else best[2]))
        ux = x / HEAD_R[0] / max(0.2, 1.0 - (0.16 * (-uz) ** 1.6 if uz < 0 else 0))
        uy = -math.sqrt(max(0.0, 1 - ux * ux - uz * uz))
        p = _head_shape((ux, uy, uz))
        best = (ux, uy, uz + (z - p.z) / HEAD_R[2])
        if abs(p.z - z) < 1e-4:
            break
    ux, uy, uz = best[0], best[1], best[2]
    p = _head_shape((ux, uy, uz))
    e = 1e-3
    a = _head_shape((ux + e, uy, uz)) - p
    b = _head_shape((ux, uy, uz + e)) - p
    n = b.cross(a).normalized()
    if n.y > 0:
        n = -n
    return p + n * out, n


def _parts():
    if _meshes:
        return _meshes
    m = _meshes
    # legs (joggers, a bit baggy) and sleeves
    m['thigh'] = _mesh('H_thigh', P2._capsule(0.098, 0.084, L1, 18, 12))
    m['shin'] = _mesh('H_shin', P2._capsule(0.084, 0.08, L2, 18, 12))
    m['upper'] = _mesh('H_upper', P2._capsule(0.085, 0.075, UPPER, 18, 12))
    m['fore'] = _mesh('H_fore', P2._capsule(0.075, 0.07, FORE, 18, 12))
    m['pelvis'] = _mesh('H_pelvis', _rbox(0.205, 0.145, 0.11, 0.8))
    # hoodie body: roomy rounded box, a touch narrower at the shoulders
    bm = _rbox(0.25, 0.168, 0.235, 0.62, 0.7, 36, 24)
    for v in bm.verts:
        t = (v.co.z + 0.235) / 0.47
        v.co.x *= 1.0 - 0.06 * t
        v.co.y *= 1.0 - 0.05 * t
    m['torso'] = _mesh('H_torso', bm)
    # ribbed hem and cuffs
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=False, segments=40, radius1=1.0, radius2=1.0, depth=1.0)
    m['ring'] = _mesh('H_ring', bm)
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=20, v_segments=12, radius=1.0)
    m['ball'] = _mesh('H_ball', bm)
    # head
    m['head'] = _mesh('H_head', _head_bm())
    # hand: mitten with a thumb towards the front
    bm = _rbox(0.042, 0.038, 0.06, 0.85)
    for v in bm.verts:
        v.co.z -= 0.05
    th = _rbox(0.019, 0.019, 0.032, 0.9, segs=12, rings=8)
    for v in th.verts:
        v.co += Vector((0, -0.035, -0.035))
    _merge(bm, th)
    m['hand'] = _mesh('H_hand', bm)
    m['shoe'] = _mesh('H_shoe', _shoe_bm())
    m['sole'] = _mesh('H_sole', _sole_bm())
    return m


def _merge(bm, other):
    me = bpy.data.meshes.new('_tmp')
    other.to_mesh(me)
    other.free()
    bm.from_mesh(me)
    bpy.data.meshes.remove(me)


def _hair_w(co):
    """Hair weight for a point of the head (1 = hair, 0 = skin): straight hairline over the forehead,
    skin fade on the sides and the back of the head."""
    d = co.normalized()
    front = max(0.0, -d.y)                       # 1 at the forehead
    side = abs(d.x)
    t = max(0.0, min(1.0, (front - 0.42) / 0.22))
    t = t * t * (3 - 2 * t)                      # straight line across the forehead, corners at the temples
    zs = -0.02 - 0.06 * side ** 2 - 0.16 * max(0.0, d.y) ** 1.2
    z0 = zs + (0.13 - zs) * t
    band = 0.025 + 0.17 * (1 - t)                 # sharp at the forehead, long fade on the sides/back
    w = max(0.0, min(1.0, (co.z - z0) / band))
    return w * w * (3 - 2 * w)


def _head_bm():
    """Head with the buzz cut baked in: colour attribute 'Col' = hair weight, the hair adds ~1 cm of volume."""
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=96, v_segments=64, radius=1.0)
    for v in bm.verts:
        d = v.co.normalized()
        v.co = _head_shape(d)
        v.co += d * 0.011 * _hair_w(v.co)
    lay = bm.loops.layers.color.new('Col')
    for f in bm.faces:
        for lp in f.loops:
            w = _hair_w(lp.vert.co)
            lp[lay] = (w, w, w, 1.0)
    return bm


def _shoe_bm():
    """Chunky low sneaker, pivot at the ankle, toe towards -Y. Upper only (sole is separate)."""
    bm = _rbox(0.066, 0.145, 0.055, 0.55, 0.7, 32, 18)
    for v in bm.verts:
        x, y, z = v.co
        t = (y + 0.145) / 0.29                   # 0 toe .. 1 heel
        z = z * (0.6 + 0.55 * t)                 # low toe box, high heel collar
        if z > 0:
            z *= 1.0 - 0.25 * (1 - t) ** 2
        v.co = Vector((x * (0.92 + 0.08 * t), y - 0.06, z - 0.03))
    return bm


def _sole_bm():
    bm = _rbox(0.072, 0.155, 0.02, 0.35, 0.6, 32, 10)
    for v in bm.verts:
        v.co.y -= 0.06
        v.co.z -= 0.068
    return bm


# ----------------------------------------------------------------------------- materials
def _rib_mat(name, color, rough=0.92):
    """Knitted rib (vertical ridges around a ring) by bump, for the hem and cuffs."""
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = lib.mat(name, color, rough=rough)
    nt = m.node_tree
    p = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['Object'], sep.inputs[0])
    at = nt.nodes.new('ShaderNodeMath'); at.operation = 'ARCTAN2'
    nt.links.new(sep.outputs['Y'], at.inputs[0]); nt.links.new(sep.outputs['X'], at.inputs[1])
    s = nt.nodes.new('ShaderNodeMath'); s.operation = 'SINE'
    mul = nt.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'; mul.inputs[1].default_value = 34.0
    nt.links.new(at.outputs[0], mul.inputs[0]); nt.links.new(mul.outputs[0], s.inputs[0])
    b = nt.nodes.new('ShaderNodeBump'); b.inputs['Strength'].default_value = 0.45; b.inputs['Distance'].default_value = 0.004
    nt.links.new(s.outputs[0], b.inputs['Height']); nt.links.new(b.outputs['Normal'], p.inputs['Normal'])
    return m


def _head_mat():
    """Skin + buzz cut: colour attribute fades hair -> skin, fine stubble noise breaks up the fade."""
    m = bpy.data.materials.get('HeroHeadHair')
    if m:
        return m
    m = bpy.data.materials.new('HeroHeadHair')
    m.use_nodes = True
    nt = m.node_tree
    L = nt.links
    p = nt.nodes['Principled BSDF']
    p.inputs['Roughness'].default_value = 0.55
    attr = nt.nodes.new('ShaderNodeVertexColor'); attr.layer_name = 'Col'
    tc = nt.nodes.new('ShaderNodeTexCoord')
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 420.0; nz.inputs['Detail'].default_value = 2.0
    L.new(tc.outputs['Object'], nz.inputs['Vector'])
    # stubble density: where the fade is partial, only some dots are dark
    sep = nt.nodes.new('ShaderNodeSeparateColor'); L.new(attr.outputs['Color'], sep.inputs[0])
    jit = nt.nodes.new('ShaderNodeMath'); jit.operation = 'MULTIPLY_ADD'
    L.new(nz.outputs['Fac'], jit.inputs[0]); jit.inputs[1].default_value = 0.6; jit.inputs[2].default_value = -0.3
    thr = nt.nodes.new('ShaderNodeMath'); thr.operation = 'ADD'
    L.new(sep.outputs[0], thr.inputs[0]); L.new(jit.outputs[0], thr.inputs[1])
    dens = nt.nodes.new('ShaderNodeMapRange'); dens.inputs['From Min'].default_value = 0.0
    dens.inputs['From Max'].default_value = 0.75
    L.new(thr.outputs[0], dens.inputs['Value'])
    mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'
    mix.inputs['A'].default_value = lib.C(COL['skin'])
    mix.inputs['B'].default_value = lib.C(COL['hair'])
    L.new(dens.outputs['Result'], mix.inputs['Factor'])
    L.new(mix.outputs['Result'], p.inputs['Base Color'])
    bump = nt.nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = 0.35
    bump.inputs['Distance'].default_value = 0.002
    hb = nt.nodes.new('ShaderNodeMath'); hb.operation = 'MULTIPLY'
    L.new(nz.outputs['Fac'], hb.inputs[0]); L.new(sep.outputs[0], hb.inputs[1])
    L.new(hb.outputs[0], bump.inputs['Height']); L.new(bump.outputs['Normal'], p.inputs['Normal'])
    rr = nt.nodes.new('ShaderNodeMapRange'); rr.inputs['To Min'].default_value = 0.5; rr.inputs['To Max'].default_value = 0.9
    L.new(sep.outputs[0], rr.inputs['Value']); L.new(rr.outputs['Result'], p.inputs['Roughness'])
    return m


def mats():
    return dict(
        hoodie=lib.mat('HeroHoodieBlack', COL['hoodie'], rough=0.93, var=0.05, var_scale=40, bump=0.08, bump_scale=160),
        rib=_rib_mat('HeroHoodieRib', COL['hoodie']),
        pants=lib.mat('HeroJoggers', COL['pants'], rough=0.92, var=0.05, var_scale=40, bump=0.06, bump_scale=160),
        skin=lib.mat('HeroSkinPeach', COL['skin'], rough=0.5),
        neck=lib.mat('HeroNeckShade', '#B88A6C', rough=0.6),
        head=_head_mat(),
        brow=lib.mat('HeroBrow', COL['brow'], rough=0.8),
        white=lib.mat('HeroEyeWhite', '#F7F6F2', rough=0.25),
        iris=lib.mat('HeroIris', COL['iris'], rough=0.2),
        pupil=lib.mat('HeroPupil', '#0E0B09', rough=0.15),
        glint=lib.mat('HeroGlint', '#FFFFFF', rough=0.1, emit='#FFFFFF', emit_strength=2.0),
        lips=lib.mat('HeroLips', COL['lips'], rough=0.5),
        shoe=lib.mat('HeroSneaker', COL['shoe'], rough=0.55, bump=0.05, bump_scale=90),
        sole=lib.mat('HeroSneakerSole', COL['sole'], rough=0.7),
        string=lib.mat('HeroDrawstring', COL['string'], rough=0.7),
        aglet=lib.mat('HeroAglet', '#2F3034', rough=0.35, metal=0.3),
    )


# ----------------------------------------------------------------------------- building
def _part(name, key, parent, loc, m, coll, scale=None, rot=None):
    ob = bpy.data.objects.new(name, _parts()[key])
    lib._link(ob, coll)
    lib._obj_mat(ob, m)
    ob.parent = parent
    ob.location = loc
    if scale:
        ob.scale = scale
    if rot:
        ob.rotation_euler = rot
    return ob


def _curve(name, pts, radii, m, parent, coll, bevel=1.0, res=3):
    cu = bpy.data.curves.new(name, 'CURVE')
    cu.dimensions = '3D'
    cu.bevel_depth = bevel
    cu.bevel_resolution = res
    cu.use_fill_caps = True
    sp = cu.splines.new('NURBS')
    sp.points.add(len(pts) - 1)
    for i, (p, r) in enumerate(zip(pts, radii)):
        sp.points[i].co = (p[0], p[1], p[2], 1.0)
        sp.points[i].radius = r
    sp.use_endpoint_u = True
    sp.order_u = min(4, len(pts))
    sp.resolution_u = 8
    cu.materials.append(m)
    ob = bpy.data.objects.new(name, cu)
    lib._link(ob, coll)
    ob.parent = parent
    return ob


def _face(name, head, M, coll):
    """Eyes, brows, nose, mouth, ears on the head object (head-local coordinates)."""
    for side, sx in (('L', 1), ('R', -1)):
        # eye: tall oval sclera sunk into the face, big brown iris looking slightly to the hero's left
        pos, n = _on_head(sx * 0.104, -0.045, out=-0.006)
        eye = lib.empty(name + '_eye' + side, pos, coll=coll)
        eye.parent = head
        eye.rotation_euler = n.to_track_quat('-Y', 'Z').to_euler()
        eye.empty_display_size = 0.03
        _part(name + '_white' + side, 'ball', eye, (0, 0, 0), M['white'], coll, scale=(0.046, 0.022, 0.056))
        look = (0.012, 0.004)                    # iris shift x (towards hero's left), z
        _part(name + '_iris' + side, 'ball', eye, (look[0], -0.012, look[1]), M['iris'], coll,
              scale=(0.036, 0.016, 0.043))
        _part(name + '_pupil' + side, 'ball', eye, (look[0] * 1.15, -0.02, look[1]), M['pupil'], coll,
              scale=(0.016, 0.012, 0.019))
        _part(name + '_glint' + side, 'ball', eye, (look[0] - 0.012, -0.029, look[1] + 0.016), M['glint'], coll,
              scale=(0.0075, 0.005, 0.0085))
        # upper lash line
        arc = [(0.047 * math.cos(a), -0.012 - 0.008 * math.sin(a), 0.057 * math.sin(a) - 0.002)
               for a in [math.radians(d) for d in (190, 160, 125, 90, 55, 20, -5)]]
        _curve(name + '_lash' + side, arc, [0.3, 0.8, 1.0, 1.0, 1.0, 0.85, 0.4], M['pupil'], eye, coll, bevel=0.0055)
        # thick brow, heavier at the inner end, slightly arched
        xs = [0.045, 0.075, 0.11, 0.145, 0.172]
        zs = [0.068, 0.082, 0.09, 0.087, 0.072]
        pts = [_on_head(sx * x, z, out=0.006)[0] for x, z in zip(xs, zs)]
        _curve(name + '_brow' + side, pts, [1.0, 1.05, 1.0, 0.85, 0.55], M['brow'], head, coll, bevel=0.0135)
        # ear: flattened ball on the side, slightly forward-tilted
        _part(name + '_ear' + side, 'ball', head, (sx * (HEAD_R[0] * 0.93), 0.03, -0.07), M['skin'], coll,
              scale=(0.026, 0.05, 0.068), rot=(0.15, 0, sx * -0.25))
    nose, n = _on_head(0.0, -0.118, out=-0.004)
    _part(name + '_nose', 'ball', head, nose, M['skin'], coll, scale=(0.028, 0.026, 0.026))
    mouth = [_on_head(x, z, out=0.002)[0] for x, z in ((-0.036, -0.178), (-0.012, -0.186), (0.014, -0.185),
                                                       (0.038, -0.174))]
    _curve(name + '_mouth', mouth, [0.6, 1.0, 1.0, 0.6], M['lips'], head, coll, bevel=0.0045)


def _hoodie(name, hips, M, coll):
    p = {}
    p['torso'] = _part(name + '_torso', 'torso', hips, (0, 0, 0.215), M['hoodie'], coll)
    _part(name + '_hem', 'ring', hips, (0, 0, -0.005), M['rib'], coll, scale=(0.236, 0.158, 0.05))
    # kangaroo pocket on the belly
    pk = bpy.data.objects.new(name + '_pocket', _mesh('H_pocket', _rbox(0.125, 0.018, 0.068, 0.45, 0.6, 24, 12)))
    lib._link(pk, coll); lib._obj_mat(pk, M['hoodie'])
    pk.parent = p['torso']; pk.location = (0, -0.166, -0.09); pk.rotation_euler = (0.06, 0, 0)
    # hood: collar around the neck and the folded hood on the back
    col = bpy.data.objects.new(name + '_collar', _collar_mesh())
    lib._link(col, coll); lib._obj_mat(col, M['hoodie'])
    col.parent = hips; col.location = (0, 0.005, 0.455); col.scale = (1.08, 1.08, 1.15)
    _part(name + '_hood', 'ball', hips, (0, 0.11, 0.43), M['hoodie'], coll, scale=(0.17, 0.085, 0.1),
          rot=(-0.35, 0, 0))
    # drawstrings with aglets
    for sx in (1, -1):
        pts = [(sx * 0.045, -0.13, 0.445), (sx * 0.05, -0.172, 0.41), (sx * 0.055, -0.182, 0.33),
               (sx * 0.06, -0.183, 0.26), (sx * 0.062, -0.183, 0.215)]
        _curve(name + '_string' + ('L' if sx > 0 else 'R'), pts, [1, 1, 1, 1, 1], M['string'], hips, coll, bevel=0.006)
        ag = lib.cyl(0.0085, 0.032, (sx * 0.062, -0.183, 0.2), M['aglet'], verts=12, name=name + '_aglet', coll=coll)
        ag.parent = hips
    return p


def _collar_mesh():
    """Thick rolled hood edge around the neck: a torus, fatter at the back, dipping into a V at the front."""
    if 'collar' in _meshes:
        return _meshes['collar']
    bm = bmesh.new()
    seg, mseg = 40, 14
    rows = []
    for i in range(seg):
        a = 2 * math.pi * i / seg
        cx, cy = math.sin(a) * 0.125, -math.cos(a) * 0.115   # a = 0 at the front (-Y)
        front = max(0.0, math.cos(a))
        r = 0.035 + 0.03 * (1 - front)
        zc = -0.035 * front ** 3
        row = []
        for j in range(mseg):
            b = 2 * math.pi * j / mseg
            dx, dy = math.sin(a), -math.cos(a)
            rr = r * (1.0 + 0.25 * max(0.0, math.cos(b)))
            row.append(bm.verts.new((cx + dx * math.cos(b) * rr, cy + dy * math.cos(b) * rr, zc + math.sin(b) * r)))
        rows.append(row)
    for i in range(seg):
        for j in range(mseg):
            a, b = rows[i][j], rows[i][(j + 1) % mseg]
            c, d = rows[(i + 1) % seg][(j + 1) % mseg], rows[(i + 1) % seg][j]
            bm.faces.new((a, b, c, d))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    _meshes['collar'] = _mesh('H_collar', bm)
    return _meshes['collar']


def hero(loc=(0, 0, 0), heading=0.0, coll=None, pose='stand', name='Hero', rng=None, height=1.0, subsurf=1):
    """Build the hero. pose: 'stand' | 'cheer' | 'point' | 'sit' | 'still' (no idle motion) | 'walk' (key it
    yourself with hero.walk). Returns the parts dict (people2 layout)."""
    rng = rng or random.Random(7)
    M = mats()
    root = lib.empty(name, loc, (0, 0, heading), coll=coll)
    root.scale = (height, height, height)
    hips = lib.empty(name + '_hips', (0, 0, HIP), coll=coll)
    hips.parent = root
    p = dict(root=root, hips=hips)
    p['pelvis'] = _part(name + '_pelvis', 'pelvis', hips, (0, 0, 0.0), M['pants'], coll)
    p.update(_hoodie(name, hips, M, coll))
    p['neck'] = _part(name + '_neck', 'ball', hips, (0, 0.01, 0.47), M['neck'], coll, scale=(0.065, 0.065, 0.09))
    p['head'] = _part(name + '_head', 'head', hips, (0, 0, HEAD_Z), M['head'], coll)
    _face(name, p['head'], M, coll)
    for side, sx in (('L', 1), ('R', -1)):
        th = _part(name + '_thigh' + side, 'thigh', hips, (sx * 0.1, 0, 0), M['pants'], coll)
        sh = _part(name + '_shin' + side, 'shin', th, (0, 0, -L1), M['pants'], coll)
        _part(name + '_cuffLeg' + side, 'ball', sh, (0, 0, -L2 + 0.03), M['pants'], coll, scale=(0.085, 0.088, 0.045))
        ft = _part(name + '_shoe' + side, 'shoe', sh, (0, 0, -L2), M['shoe'], coll, scale=(1.18, 1.15, 1.12))
        _part(name + '_sole' + side, 'sole', ft, (0, 0, 0), M['sole'], coll)
        for k in range(4):                       # laces across the tongue
            y = -0.125 + k * 0.03
            lc = lib.box((0.05, 0.009, 0.006), (0, y, -0.01 - (3 - k) * 0.0085), M['shoe'], rot=(-0.35, 0, 0),
                         bevel=0.002, name=name + '_lace', coll=coll)
            lc.parent = ft
        ua = _part(name + '_upper' + side, 'upper', hips, (sx * SHOULDER[0], 0, SHOULDER[1]), M['hoodie'], coll)
        fa = _part(name + '_fore' + side, 'fore', ua, (0, 0, -UPPER), M['hoodie'], coll)
        _part(name + '_cuff' + side, 'ring', fa, (0, 0, -FORE - 0.035), M['rib'], coll, scale=(0.068, 0.068, 0.05))
        hd = _part(name + '_hand' + side, 'hand', fa, (0, 0, -FORE - 0.05), M['skin'], coll)
        hd.rotation_euler.z = sx * 0.35          # thumbs turn slightly inwards to the front
        ua.rotation_euler.y = sx * 0.2
        p['thigh' + side], p['shin' + side], p['shoe' + side] = th, sh, ft
        p['upper' + side], p['fore' + side], p['hand' + side] = ua, fa, hd
    if subsurf:
        for ob in [o for o in bpy.data.objects if o.name.startswith(name + '_') and o.type == 'MESH']:
            if ob.data.name in ('H_torso', 'H_head', 'H_pocket', 'H_shoe', 'H_sole', 'H_collar', 'H_hand',
                                'H_pelvis'):
                md = ob.modifiers.new('Subsurf', 'SUBSURF')
                md.levels = subsurf
                md.render_levels = subsurf
    pose_hero(p, pose, rng)
    return p


def pose_hero(p, pose='stand', rng=None):
    rng = rng or random.Random(7)
    if pose == 'stand':
        P2.stand(p, rng)
    elif pose == 'cheer':
        p['upperL'].rotation_euler.y = 2.5
        p['upperR'].rotation_euler.y = -2.5
        p['foreL'].rotation_euler.y = 0.35
        p['foreR'].rotation_euler.y = -0.35
        p['head'].rotation_euler.x = 0.15
    elif pose == 'point':
        p['upperR'].rotation_euler.x = -1.35
        p['upperR'].rotation_euler.y = -0.12
        p['foreR'].rotation_euler.x = -0.08
        p['head'].rotation_euler.z = 0.2
        p['upperL'].rotation_euler.x = 0.1
    elif pose == 'sit':
        sit(p, rng)
    return p


# ----------------------------------------------------------------------------- motion (chibi leg lengths)
def _cycle(obs):
    """Loop the keyed channels; works with Blender 4.5 actions and the layered actions of Blender 5."""
    for ob in obs:
        ad = ob.animation_data
        if not (ad and ad.action):
            continue
        if hasattr(ad.action, 'fcurves'):
            fcs = list(ad.action.fcurves)
        else:
            fcs = [fc for ly in ad.action.layers for st in ly.strips for cb in st.channelbags for fc in cb.fcurves]
        for fc in fcs:
            if not any(m.type == 'CYCLES' for m in fc.modifiers):
                fc.modifiers.new('CYCLES')


def _leg(u, A):
    """people2 gait with a later, higher knee and a lifted toe in the swing: the big sneakers must clear the
    ground on these short legs."""
    if u < 0.5:
        return P2._leg(u, A)
    s = (u - 0.5) / 0.5
    e = (1 - math.cos(math.pi * s)) / 2
    th = A - 2 * A * e
    k = 1.15 * math.sin(math.pi * s ** 0.8) ** 1.1
    f = -(th + k) - 0.2 * math.sin(math.pi * s)       # toe up (+x rotation would point it down)
    return th, k, f


def walk(p, speed=1.0, phase=0.0, height=1.0, fps=None, samples=24):
    """Keyed looping walk matched to the root speed (m/s), feet planted: people2 gait with the hero's leg lengths."""
    fps = fps or lib.FPS
    A = A_SWING
    step = 2 * (L1 + L2) * math.sin(A) * height
    P = 2 * step / max(0.3, speed)
    f0 = 1 - phase * P * fps
    for j in range(samples + 1):
        t = j / samples
        fr = f0 + t * P * fps
        legs = {}
        for side, u in (('L', t % 1.0), ('R', (t + 0.5) % 1.0)):
            th, k, f = _leg(u, A)
            legs[side] = (u, th, k)
            P2._key(p['thigh' + side], 'rotation_euler', 0, fr, th)
            P2._key(p['shin' + side], 'rotation_euler', 0, fr, k)
            P2._key(p['shoe' + side], 'rotation_euler', 0, fr, f)
            arm = -0.8 * th
            P2._key(p['upper' + side], 'rotation_euler', 0, fr, arm)
            P2._key(p['fore' + side], 'rotation_euler', 0, fr, -0.2 - 0.3 * max(0.0, -arm) / (0.8 * A))
        u, th, k = legs['L'] if legs['L'][0] < 0.5 else legs['R']
        P2._key(p['hips'], 'location', 2, fr, ANKLE + L1 * math.cos(th) + L2 * math.cos(th + k))
        P2._key(p['torso'], 'rotation_euler', 2, fr, 0.06 * math.sin(2 * math.pi * t))
        P2._key(p['head'], 'rotation_euler', 1, fr, 0.03 * math.sin(2 * math.pi * t))   # big head sways a little
    _cycle([p[k] for k in ('thighL', 'thighR', 'shinL', 'shinR', 'shoeL', 'shoeR', 'upperL', 'upperR', 'foreL',
                              'foreR', 'hips', 'torso', 'head')])
    return P


def sit(p, rng=None):
    """Seated: root at floor level under the hips; seat height = ANKLE + L2 (~0.3 m at height 1.0)."""
    rng = rng or random
    for side in ('L', 'R'):
        p['thigh' + side].rotation_euler.x = -math.pi / 2
        p['shin' + side].rotation_euler.x = math.pi / 2 - rng.uniform(-0.1, 0.12)
        p['upper' + side].rotation_euler.x = -rng.uniform(0.4, 0.6)
        p['fore' + side].rotation_euler.x = -rng.uniform(0.7, 0.9)
    p['hips'].location.z = ANKLE + L2
    lib.add_sine(p['head'], 'rotation_euler', 0, 0.06, rng.uniform(2.2, 3.6), rng.uniform(0, 6))
    lib.add_sine(p['head'], 'rotation_euler', 2, 0.1, rng.uniform(3.0, 5.0), rng.uniform(0, 6))
    return p
