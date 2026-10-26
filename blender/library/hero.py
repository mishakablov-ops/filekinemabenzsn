"""Main hero of the channel (reference from mike, 26.10.2026: assets3d/people/own/hero-aipollon/reference-v2.png),
built from code: a chibi guy with a big egg-shaped head, short black fade haircut, big brown eyes, thick brows, black
hoodie with a kangaroo pocket and grey drawstrings, wide straight black trousers, white court sneakers.

Same rig contract as people2.person: root pivot at the feet, forward = local -Y, root.scale = height factor * SCALE
(1.0 = 1.75 m), parts in a dict (root, hips, pelvis, torso, neck, head, thigh/shin/shoe/upper/fore/hand + L/R),
so lib.move_root works. Chibi legs are shorter than people2 legs, so use hero.walk / hero.sit (own leg lengths),
people2.stand works as is. Drop-in for pcommon.hero: hero(loc, heading, coll, pose, name, rng).
"""
import bpy, bmesh, math, random
from mathutils import Vector
import lib
import people2 as P2

# proportions measured on the reference: head 44 %, hoodie 27 %, legs and shoes 29 % (model units; the whole
# figure is scaled by SCALE so that height=1.0 is 1.75 m tall like people2)
L1, L2, ANKLE = 0.205, 0.205, 0.14               # thigh, shin, ankle height (unscaled)
HIP = ANKLE + L1 + L2                            # 0.55 = hoodie hem
SHOULDER = (0.325, 0.39)                         # x, z relative to the hip joint
UPPER, FORE = 0.195, 0.145                       # short chibi arms: the cuffs end at the hem
HEAD_Z = 0.962                                   # head centre above the hip joint: chin just over the collar
HEAD_R = (0.285, 0.285, 0.30)                    # head radii x, y (depth), z (top half), before HEAD_S
HEAD_S = 1.21                                    # head object scale (face features are built in unscaled units)
JAW = 1.17                                       # the lower half of the head is longer: full cheeks, rounded chin
SCALE = 1.75 / (HIP + HEAD_Z + HEAD_R[2] * HEAD_S + 0.01)   # root scale at height=1.0: 1.75 m to the top of the hair
A_SWING = 0.42

COL = dict(hoodie='#0D0E10', pants='#0E0F11', skin='#DD9A6E', hair='#0E0C0B', iris='#4E2C18', shoe='#F3F3F0',
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
    """Unit-sphere direction -> head surface: a rounded box of a skull (flat-ish top, full cheeks and jaw, wide
    rounded chin) with a flatter face, like the reference."""
    x, y, z = co
    n = (2.5 if z > 0 else 2.5 + 0.2 * min(1.0, -z * 1.5)) + 0.5 * max(0.0, -y)   # flatter, broad face
    f = (abs(x) ** n + abs(y) ** n + abs(z) ** n) ** (-1.0 / n)
    x, y, z = x * f, y * f, z * f
    if z < 0:                                    # full cheeks, the jaw rounds off only towards the chin
        x *= 1.0 - 0.36 * (-z) ** 2.2
        y *= 1.0 - 0.1 * (-z) ** 2.0
        z *= JAW
    if y < 0:
        y *= 0.9
    return Vector((x * HEAD_R[0], y * HEAD_R[1], z * HEAD_R[2]))


def _on_head(x, z, out=0.0):
    """Point on the face (front, -Y) at head-local x, z, pushed `out` along the normal; returns (point, normal)."""
    def surf(a, b):
        return _head_shape((math.cos(b) * math.sin(a), -math.cos(b) * math.cos(a), math.sin(b)))
    a = math.asin(max(-0.95, min(0.95, x / HEAD_R[0])))
    b = math.asin(max(-0.95, min(0.95, z / HEAD_R[2])))
    e = 1e-4
    for _ in range(30):                          # Newton on (azimuth, elevation) so that p.x, p.z hit x, z
        p = surf(a, b)
        fx, fz = p.x - x, p.z - z
        if abs(fx) + abs(fz) < 1e-6:
            break
        pa, pb = surf(a + e, b), surf(a, b + e)
        j11, j12 = (pa.x - p.x) / e, (pb.x - p.x) / e
        j21, j22 = (pa.z - p.z) / e, (pb.z - p.z) / e
        det = j11 * j22 - j12 * j21 or 1e-9
        a -= (fx * j22 - fz * j12) / det
        b -= (j11 * fz - j21 * fx) / det
        a, b = max(-1.5, min(1.5, a)), max(-1.5, min(1.5, b))
    p = surf(a, b)
    nrm = (surf(a, b + e) - p).cross(surf(a + e, b) - p).normalized()
    if nrm.y > 0:
        nrm = -nrm
    return p + nrm * out, nrm


def _parts():
    if _meshes:
        return _meshes
    m = _meshes
    # legs (joggers, a bit baggy) and sleeves
    # straight wide trousers: the shin is an open-ended tube that falls over the top of the sneaker
    m['thigh'] = _mesh('H_thigh', P2._capsule(0.11, 0.104, L1, 20, 12))
    bm = P2._capsule(0.104, 0.114, L2 + 0.02, 20, 12)
    for v in bm.verts:
        if v.co.z < -(L2 + 0.02):
            v.co.z = -(L2 + 0.02) - (-(L2 + 0.02) - v.co.z) * 0.12
    m['shin'] = _mesh('H_shin', bm)
    m['upper'] = _mesh('H_upper', P2._capsule(0.096, 0.088, UPPER, 18, 12))
    m['fore'] = _mesh('H_fore', P2._capsule(0.088, 0.083, FORE, 18, 12))
    m['pelvis'] = _mesh('H_pelvis', _rbox(0.235, 0.155, 0.11, 0.8))
    # hoodie body: roomy rounded box, round shoulders
    bm = _rbox(0.295, 0.195, 0.255, 0.6, 0.72, 36, 24)
    for v in bm.verts:
        t = (v.co.z + 0.255) / 0.51
        v.co.x *= 1.0 - 0.07 * t ** 2
        v.co.y *= 1.0 - 0.06 * t
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
    bm = _rbox(0.064, 0.056, 0.074, 0.85)
    for v in bm.verts:
        v.co.z -= 0.06
    th = _rbox(0.025, 0.025, 0.04, 0.9, segs=12, rings=8)
    for v in th.verts:
        v.co += Vector((0, -0.046, -0.042))
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
    """Hair weight for a point of the head (1 = hair, 0 = skin), like the reference: a straight hairline across the
    forehead that turns back at the temples with a sharp corner, dark on the sides down to the top of the ears,
    then a short skin fade; lower at the back."""
    d = co.normalized()
    front = max(0.0, -d.y)                       # 1 at the forehead
    back = max(0.0, d.y)
    t = max(0.0, min(1.0, (front - 0.52) / 0.12))
    t = t * t * (3 - 2 * t)                      # 1 on the forehead, 0 from the temple corner backwards
    z_side = -0.15 - 0.08 * back ** 1.3          # bottom of the fade: at the top of the ears, lower at the back
    band_side = 0.21 + 0.02 * back
    z0 = z_side + (0.105 - z_side) * t
    band = band_side + (0.012 - band_side) * t
    w = max(0.0, min(1.0, (co.z - z0) / band))
    return w * w * (3 - 2 * w)


def _head_bm():
    """Head with the buzz cut baked in: colour attribute 'Col' = hair weight, the hair adds ~1 cm of volume."""
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=96, v_segments=64, radius=1.0)
    for v in bm.verts:
        d = v.co.normalized()
        v.co = _head_shape(d)
        v.co += d * 0.006 * _hair_w(v.co)
    lay = bm.loops.layers.color.new('Col')
    for f in bm.faces:
        for lp in f.loops:
            w = _hair_w(lp.vert.co) ** 1.8         # the fade stays light until close to the cap
            lp[lay] = (w, w, w, 1.0)
    return bm


SHOE_TOE, SHOE_HEEL = -0.29, 0.125             # big chibi sneaker, 0.415 along y (pivot at the ankle)
SOLE_H = 0.064                                   # thick white cupsole (like an Air Force 1)
SOLE_TOP = -ANKLE + SOLE_H
SHOE_W = 0.088                                   # half width of the upper


def _shoe_h(t):
    """Height of the sneaker upper above the sole, t = 0 toe .. 1 heel: a tall rounded toe box, then up to the
    padded collar."""
    e = max(0.0, min(1.0, (t - 0.22) / 0.55))
    return 0.072 + 0.08 * e * e * (3 - 2 * e)


def _shoe_xy(x, y, grow=0.0):
    """Shared footprint of the upper and the sole (unit superellipsoid coords -> shoe x, y, t)."""
    t = (y + 1) / 2                              # 0 toe .. 1 heel
    yy = SHOE_TOE + 0.01 - grow + t * (SHOE_HEEL - SHOE_TOE - 0.02 + 2 * grow)
    xx = x * (SHOE_W * (0.9 + 0.1 * math.sin(math.pi * min(1.0, t * 1.4))) + grow)
    return xx, yy, t


def _shoe_bm():
    """Chunky low sneaker (white leather court shoe), pivot at the ankle, toe towards -Y. Upper only: its rounded
    bottom sits inside the cupsole, so the sole wall and the upper meet in a crisp line."""
    bm = _rbox(1.0, 1.0, 1.0, 0.72, 0.6, 36, 18)
    for v in bm.verts:
        x, y, z = v.co
        xx, yy, t = _shoe_xy(x, y)
        zz = SOLE_TOP - 0.03 + (z + 1) / 2 * (_shoe_h(t) + 0.03)
        v.co = Vector((xx, yy, zz))
    return bm


def _sole_bm():
    """Cupsole: the footprint of the upper grown by a few mm, straight side walls."""
    bm = _rbox(1.0, 1.0, 1.0, 0.72, 0.22, 36, 10)
    for v in bm.verts:
        x, y, z = v.co
        xx, yy, t = _shoe_xy(x, y, grow=0.006)
        v.co = Vector((xx, yy, -ANKLE + (z + 1) / 2 * SOLE_H))
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


def _sole_mat():
    """White cupsole with a thin grey groove running round it (object z of the sole mesh)."""
    m = bpy.data.materials.get('HeroSneakerSole')
    if m:
        return m
    m = lib.mat('HeroSneakerSole', COL['sole'], rough=0.7)
    nt = m.node_tree
    tc = nt.nodes.new('ShaderNodeTexCoord')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['Object'], sep.inputs[0])
    d = nt.nodes.new('ShaderNodeMath'); d.operation = 'SUBTRACT'; d.inputs[1].default_value = -ANKLE + 0.5 * SOLE_H
    nt.links.new(sep.outputs['Z'], d.inputs[0])
    a = nt.nodes.new('ShaderNodeMath'); a.operation = 'ABSOLUTE'; nt.links.new(d.outputs[0], a.inputs[0])
    g = nt.nodes.new('ShaderNodeMath'); g.operation = 'LESS_THAN'; g.inputs[1].default_value = 0.003
    nt.links.new(a.outputs[0], g.inputs[0])
    mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'
    mix.inputs['A'].default_value = lib.C(COL['sole']); mix.inputs['B'].default_value = lib.C('#9C9C97')
    nt.links.new(g.outputs[0], mix.inputs['Factor'])
    nt.links.new(mix.outputs['Result'], nt.nodes['Principled BSDF'].inputs['Base Color'])
    return m


def _shoe_mat():
    """White leather upper: soft grain bump plus rows of perforations on the toe box (object coords of the upper)."""
    m = bpy.data.materials.get('HeroSneaker')
    if m:
        return m
    m = lib.mat('HeroSneaker', COL['shoe'], rough=0.55, bump=0.05, bump_scale=90)
    nt = m.node_tree
    L = nt.links
    p = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ'); L.new(tc.outputs['Object'], sep.inputs[0])
    vor = nt.nodes.new('ShaderNodeTexVoronoi'); vor.inputs['Scale'].default_value = 85.0
    vor.inputs['Randomness'].default_value = 0.0
    L.new(tc.outputs['Object'], vor.inputs['Vector'])
    dot = nt.nodes.new('ShaderNodeMath'); dot.operation = 'LESS_THAN'; dot.inputs[1].default_value = 0.2
    L.new(vor.outputs['Distance'], dot.inputs[0])
    toe = nt.nodes.new('ShaderNodeMapRange')       # only on the front of the toe box
    toe.inputs['From Min'].default_value = SHOE_TOE + 0.1; toe.inputs['From Max'].default_value = SHOE_TOE + 0.08
    L.new(sep.outputs['Y'], toe.inputs['Value'])
    up = nt.nodes.new('ShaderNodeMapRange')        # above the sole line
    up.inputs['From Min'].default_value = SOLE_TOP + 0.02; up.inputs['From Max'].default_value = SOLE_TOP + 0.03
    L.new(sep.outputs['Z'], up.inputs['Value'])
    a = nt.nodes.new('ShaderNodeMath'); a.operation = 'MULTIPLY'; L.new(dot.outputs[0], a.inputs[0])
    L.new(toe.outputs['Result'], a.inputs[1])
    b = nt.nodes.new('ShaderNodeMath'); b.operation = 'MULTIPLY'; L.new(a.outputs[0], b.inputs[0])
    L.new(up.outputs['Result'], b.inputs[1])
    mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'
    mix.inputs['A'].default_value = lib.C(COL['shoe']); mix.inputs['B'].default_value = lib.C('#A3A29C')
    L.new(b.outputs[0], mix.inputs['Factor']); L.new(mix.outputs['Result'], p.inputs['Base Color'])
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
    dens.inputs['From Max'].default_value = 0.95
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
        neck=lib.mat('HeroNeckShade', '#8C6650', rough=0.6),
        earIn=lib.mat('HeroEarInner', '#B27658', rough=0.55),
        strands=lib.mat('HeroHairStrands', '#110E0C', rough=0.45),
        head=_head_mat(),
        brow=_brow_mat(),
        white=lib.mat('HeroEyeWhite', '#F7F6F2', rough=0.45),
        iris=_iris_mat(),
        pupil=lib.mat('HeroPupil', '#0E0B09', rough=0.5),
        glint=lib.mat('HeroGlint', '#FFFFFF', rough=0.1, emit='#FFFFFF', emit_strength=2.0),
        lips=lib.mat('HeroLips', COL['lips'], rough=0.5),
        shoe=_shoe_mat(),
        sole=_sole_mat(),
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


EYE_Z = -0.112                                   # eye centre on the head (head-local z)
EYE_X = 0.122
EYE = (0.055, 0.026, 0.056)                      # sclera half sizes: width, depth, height
GAZE = (-0.009, -0.003)                          # iris shift in the eye: like the reference, to the hero's right


def _brow_mesh(sx, name):
    """Thick brow like the reference: flat bottom, slightly arched top, heavy inner end, tip tapering at the
    outer end. A thin slab wrapped onto the head surface; UV u runs along the brow (for the hair strokes)."""
    nu, nv = 18, 6
    x0, x1 = 0.03, 0.19                          # inner / outer end (head x)
    zb = EYE_Z + 0.084                           # bottom line
    def top(u):                                  # full height to ~45 %, then tapers to a point at the outer end
        return 0.036 + 0.004 * math.sin(math.pi * min(1.0, u / 0.5)) - 0.026 * max(0.0, (u - 0.5) / 0.5) ** 1.3
    def bot(u):
        return 0.007 * max(0.0, (u - 0.6) / 0.4) ** 2
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new('UVMap')
    grids = []
    for layer, out0 in ((0, 1), (1, 0)):         # front surface (bulging out), back surface (inside the skin)
        g = []
        for i in range(nu + 1):
            u = i / nu
            row = []
            for j in range(nv + 1):
                v = j / nv
                z = zb + bot(u) + (top(u) - bot(u)) * v
                bulge = 0.0065 * math.sin(math.pi * v) ** 0.6 * min(1.0, u / 0.08 + 0.35, (1 - u) / 0.12 + 0.2)
                pt, n = _on_head(sx * (x0 + (x1 - x0) * u), z, out=(0.0025 + bulge) if out0 else -0.003)
                row.append(bm.verts.new(pt))
            g.append(row)
        grids.append(g)
    f, bk = grids
    def face(vs, uvs):
        fc = bm.faces.new(vs)
        for lp, c in zip(fc.loops, uvs):
            lp[uv].uv = c
    for i in range(nu):
        for j in range(nv):
            q = [(i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)]
            face([f[a][b] for a, b in q], [(a / nu, b / nv) for a, b in q])
            face([bk[a][b] for a, b in reversed(q)], [(a / nu, b / nv) for a, b in reversed(q)])
    for i in range(nu):                          # bottom and top rims
        for j in (0, nv):
            face([f[i][j], bk[i][j], bk[i + 1][j], f[i + 1][j]], [(i / nu, 0)] * 4)
    for i in (0, nu):                            # ends
        for j in range(nv):
            face([f[i][j], f[i][j + 1], bk[i][j + 1], bk[i][j]], [(0, j / nv)] * 4)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _mesh(name, bm)


def _iris_mat():
    """Iris like the reference: big black pupil, warm brown, lighter towards the bottom, dark ring at the edge
    (object coords of the unit-ball mesh)."""
    m = bpy.data.materials.get('HeroIrisRing')
    if m:
        return m
    m = bpy.data.materials.new('HeroIrisRing')
    m.use_nodes = True
    nt = m.node_tree
    L = nt.links
    p = nt.nodes['Principled BSDF']
    p.inputs['Roughness'].default_value = 0.45
    p.inputs['Base Color'].default_value = lib.C(COL['iris'])   # what plain exporters (glTF) keep
    tc = nt.nodes.new('ShaderNodeTexCoord')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ'); L.new(tc.outputs['Object'], sep.inputs[0])
    comb = nt.nodes.new('ShaderNodeCombineXYZ')
    L.new(sep.outputs['X'], comb.inputs['X']); L.new(sep.outputs['Z'], comb.inputs['Y'])
    ln = nt.nodes.new('ShaderNodeVectorMath'); ln.operation = 'LENGTH'; L.new(comb.outputs[0], ln.inputs[0])
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    el = ramp.color_ramp.elements
    el[0].position = 0.5; el[0].color = lib.C('#060404')          # pupil
    e = el.new(0.545); e.color = lib.C('#311A0D')
    el[1].position = 1.0; el[1].color = lib.C('#170B05')
    e = el.new(0.8); e.color = lib.C('#4A2A16')
    e = el.new(0.9); e.color = lib.C('#24120A')
    L.new(ln.outputs['Value'], ramp.inputs['Fac'])
    low = nt.nodes.new('ShaderNodeMapRange')       # lighter lower half
    low.inputs['From Min'].default_value = 0.0; low.inputs['From Max'].default_value = -0.8
    low.inputs['To Max'].default_value = 0.3
    L.new(sep.outputs['Z'], low.inputs['Value'])
    mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'; mix.blend_type = 'SCREEN'
    ring = nt.nodes.new('ShaderNodeMath'); ring.operation = 'GREATER_THAN'; ring.inputs[1].default_value = 0.54
    L.new(ln.outputs['Value'], ring.inputs[0])
    fac = nt.nodes.new('ShaderNodeMath'); fac.operation = 'MULTIPLY'
    L.new(low.outputs['Result'], fac.inputs[0]); L.new(ring.outputs[0], fac.inputs[1])
    L.new(fac.outputs[0], mix.inputs['Factor'])
    L.new(ramp.outputs['Color'], mix.inputs['A']); mix.inputs['B'].default_value = lib.C('#5E3820')
    L.new(mix.outputs['Result'], p.inputs['Base Color'])
    return m


def _brow_mat():
    """Dark brow with fine hair strokes along it (UV u along the brow)."""
    m = bpy.data.materials.get('HeroBrowHair')
    if m:
        return m
    m = bpy.data.materials.new('HeroBrowHair')
    m.use_nodes = True
    nt = m.node_tree
    L = nt.links
    p = nt.nodes['Principled BSDF']
    p.inputs['Roughness'].default_value = 0.85
    p.inputs['Base Color'].default_value = lib.C(COL['brow'])
    uvn = nt.nodes.new('ShaderNodeUVMap'); uvn.uv_map = 'UVMap'
    mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (3.0, 40.0, 1.0)
    mp.inputs['Rotation'].default_value = (0, 0, 0.12)
    L.new(uvn.outputs['UV'], mp.inputs['Vector'])
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 2.5; nz.inputs['Detail'].default_value = 3
    L.new(mp.outputs['Vector'], nz.inputs['Vector'])
    mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'
    mix.inputs['A'].default_value = lib.C('#0B0909'); mix.inputs['B'].default_value = lib.C('#272221')
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = 0.5
    mr.inputs['From Max'].default_value = 0.75
    L.new(nz.outputs['Fac'], mr.inputs['Value']); L.new(mr.outputs['Result'], mix.inputs['Factor'])
    L.new(mix.outputs['Result'], p.inputs['Base Color'])
    b = nt.nodes.new('ShaderNodeBump'); b.inputs['Strength'].default_value = 0.4; b.inputs['Distance'].default_value = 0.001
    L.new(nz.outputs['Fac'], b.inputs['Height']); L.new(b.outputs['Normal'], p.inputs['Normal'])
    return m


def _face(name, head, M, coll, gaze=GAZE):
    """Eyes, brows, nose, mouth, ears on the head object (head-local coordinates)."""
    gx, gz = gaze
    for side, sx in (('L', 1), ('R', -1)):
        # eye: big round-oval sclera set into the face; the iris and pupil are caps on the same centre, so the
        # sclera clips them like a real eyeball; two glints (big upper, small lower)
        sink = 0.008
        pos, n = _on_head(sx * EYE_X, EYE_Z, out=-sink)
        eye = lib.empty(name + '_eye' + side, pos, coll=coll)
        eye.parent = head
        eye.rotation_euler = n.to_track_quat('-Y', 'Z').to_euler()
        eye.empty_display_size = 0.03
        ex, ey, ez = EYE
        _part(name + '_white' + side, 'ball', eye, (0, 0, 0), M['white'], coll, scale=(ex, ey, ez))
        _part(name + '_iris' + side, 'ball', eye, (gx, 0, gz), M['iris'], coll, scale=(0.048, ey * 1.17, 0.053))
        _part(name + '_glint' + side, 'ball', eye, (gx - 0.012, -ey * 1.25 - 0.001, gz + 0.014), M['glint'], coll,
              scale=(0.0088, 0.003, 0.0095))
        _part(name + '_glint2' + side, 'ball', eye, (gx + 0.014, -ey * 1.2 - 0.001, gz - 0.018), M['glint'], coll,
              scale=(0.0045, 0.002, 0.005))
        # upper lid: thick black line over the top of the eye, heavier towards the outer corner, small wing
        # upper lid: thick black line along the top edge of the visible eye (where the sclera comes out of the skin),
        # heavier towards the outer corner, ending in a small wing
        R = eye.rotation_euler.to_matrix()
        arc = []
        for d in (172, 155, 132, 108, 84, 60, 38, 18, 4):
            c, sn = math.cos(math.radians(d)), math.sin(math.radians(d))
            t = 1.0
            while t > 0.3:
                e = Vector((sx * ex * t * c, -ey * math.sqrt(max(0.0, 1 - t * t)), ez * t * sn))
                q = Vector(pos) + R @ e
                if q.y < _on_head(q.x, q.z)[0].y:
                    break
                t -= 0.01
            arc.append(_on_head(q.x, q.z + 0.001, out=0.006)[0])
        wing = arc[-1] + (arc[-1] - arc[-2]).normalized() * 0.01
        arc.append(_on_head(wing.x, wing.z + 0.001, out=0.003)[0])
        _curve(name + '_lid' + side, arc, [0.35, 0.7, 0.9, 1.0, 1.05, 1.12, 1.15, 1.1, 0.9, 0.35], M['pupil'], head,
               coll, bevel=0.011)
        # brow
        br = bpy.data.objects.new(name + '_brow' + side, _brow_mesh(sx, 'H_brow' + side))
        lib._link(br, coll); lib._obj_mat(br, M['brow'])
        br.parent = head
        # ear: flattened oval shell on the side at eye height, a rolled rim (helix) round the top and back like a
        # C open to the front, darker bowl inside
        eloc, erot, esc = Vector((sx * HEAD_R[0] * 0.93, 0.0, -0.128)), (0.1, 0, sx * -0.5), (0.032, 0.07, 0.09)
        ear = _part(name + '_ear' + side, 'ball', head, eloc, M['skin'], coll, scale=esc, rot=erot)
        _part(name + '_earIn' + side, 'ball', ear, (sx * 0.6, -0.12, -0.04), M['earIn'], coll,
              scale=(0.3, 0.55, 0.62))
        ER = ear.rotation_euler.to_matrix()
        rim = []
        for a in (-55, -20, 15, 55, 95, 135, 172):
            c, sn = math.cos(math.radians(a)), math.sin(math.radians(a))
            rim.append(eloc + ER @ Vector((sx * 0.75 * esc[0], 0.86 * sn * esc[1], 0.86 * c * esc[2])))
        _curve(name + '_helix' + side, rim, [0.4, 0.85, 1.0, 1.0, 1.0, 0.85, 0.55], M['skin'], head, coll,
               bevel=0.0105)
    nose, n = _on_head(0.0, -0.18, out=-0.008)
    _part(name + '_nose', 'ball', head, nose, M['skin'], coll, scale=(0.042, 0.04, 0.037))
    # soft closed smile, the hero's left corner a little higher (smirk like the reference)
    mouth = [_on_head(x, z, out=0.002)[0] for x, z in ((-0.052, -0.247), (-0.026, -0.257), (0.004, -0.26),
                                                       (0.032, -0.254), (0.056, -0.24))]
    _curve(name + '_mouth', mouth, [0.5, 0.9, 1.0, 0.9, 0.5], M['lips'], head, coll, bevel=0.004)


def _add_hair(head, mat, count=110000):
    """Buzz cut as real short strands (particle hair) where the hair weight is > 0: fuzzy top like the reference,
    shorter and sparser strands in the fade."""
    me = head.data
    vg = head.vertex_groups.new(name='hair')       # strand length
    vd = head.vertex_groups.new(name='hair_density')
    for v in me.vertices:
        x = _hair_w(v.co)
        if x > 0.01:
            vg.add([v.index], 0.35 + 0.65 * x, 'REPLACE')
            vd.add([v.index], x ** 3, 'REPLACE')     # the fade thins out fast, scalp shows through
    if mat.name not in [m.name for m in me.materials if m]:
        me.materials.append(mat)
    md = head.modifiers.new('Hair', 'PARTICLE_SYSTEM')
    ps = md.particle_system
    ps.vertex_group_density = 'hair_density'
    ps.vertex_group_length = 'hair'
    st = ps.settings
    st.type = 'HAIR'
    st.count = count
    st.emit_from = 'FACE'
    st.use_advanced_hair = True                  # strand length = initial velocity (local units, before HEAD_S)
    st.normal_factor = 0.0024
    st.factor_random = 0.0012
    st.material_slot = mat.name
    st.render_type = 'PATH'
    st.display_percentage = 10
    try:
        st.root_radius, st.tip_radius, st.radius_scale = 1.0, 0.2, 0.0009
        st.use_close_tip = True
    except AttributeError:
        pass
    st.child_type = 'NONE'
    return md


def _hoodie(name, hips, M, coll):
    p = {}
    p['torso'] = _part(name + '_torso', 'torso', hips, (0, 0, 0.24), M['hoodie'], coll)
    _part(name + '_hem', 'ring', hips, (0, 0, 0.0), M['rib'], coll, scale=(0.285, 0.19, 0.05))
    # kangaroo pocket on the belly: wide flap, slanted hand openings at the sides
    bm = _rbox(0.16, 0.02, 0.072, 0.42, 0.6, 28, 12)
    for v in bm.verts:
        v.co.x *= 1.0 - 0.12 * max(0.0, v.co.z / 0.075)
    pk = bpy.data.objects.new(name + '_pocket', _mesh('H_pocket', bm))
    lib._link(pk, coll); lib._obj_mat(pk, M['hoodie'])
    pk.parent = p['torso']; pk.location = (0, -0.19, -0.082); pk.rotation_euler = (0.05, 0, 0)
    # hood: collar around the neck and the folded hood on the back
    col = bpy.data.objects.new(name + '_collar', _collar_mesh())
    lib._link(col, coll); lib._obj_mat(col, M['hoodie'])
    col.parent = hips; col.location = (0, 0.01, 0.495); col.scale = (1.25, 1.25, 1.3)
    _part(name + '_hood', 'ball', hips, (0, 0.14, 0.5), M['hoodie'], coll, scale=(0.23, 0.11, 0.12),
          rot=(-0.35, 0, 0))
    # drawstrings with aglets
    for sx in (1, -1):
        pts = [(sx * 0.05, -0.155, 0.485), (sx * 0.056, -0.206, 0.44), (sx * 0.062, -0.214, 0.34),
               (sx * 0.068, -0.215, 0.25), (sx * 0.07, -0.215, 0.22)]
        _curve(name + '_string' + ('L' if sx > 0 else 'R'), pts, [1, 1, 1, 1, 1], M['string'], hips, coll, bevel=0.006)
        ag = lib.cyl(0.0085, 0.032, (sx * 0.07, -0.215, 0.205), M['aglet'], verts=12, name=name + '_aglet', coll=coll)
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


def hero(loc=(0, 0, 0), heading=0.0, coll=None, pose='stand', name='Hero', rng=None, height=1.0, subsurf=1,
         gaze=GAZE, hair=True):
    """Build the hero. pose: 'stand' | 'cheer' | 'point' | 'sit' | 'still' (no idle motion) | 'walk' (key it
    yourself with hero.walk). gaze = iris shift (x, z) in metres, (0, 0) looks straight ahead.
    hair=False skips the strand hair (faster previews; the haircut stays painted on the head).
    Returns the parts dict (people2 layout)."""
    rng = rng or random.Random(7)
    M = mats()
    root = lib.empty(name, loc, (0, 0, heading), coll=coll)
    root.scale = (height * SCALE,) * 3
    hips = lib.empty(name + '_hips', (0, 0, HIP), coll=coll)
    hips.parent = root
    p = dict(root=root, hips=hips)
    p['pelvis'] = _part(name + '_pelvis', 'pelvis', hips, (0, 0, 0.0), M['pants'], coll)
    p.update(_hoodie(name, hips, M, coll))
    p['neck'] = _part(name + '_neck', 'ball', hips, (0, 0.02, 0.52), M['neck'], coll, scale=(0.075, 0.075, 0.08))
    p['head'] = _part(name + '_head', 'head', hips, (0, 0, HEAD_Z), M['head'], coll, scale=(HEAD_S,) * 3)
    _face(name, p['head'], M, coll, gaze)
    if hair:
        _add_hair(p['head'], M['strands'])
    for side, sx in (('L', 1), ('R', -1)):
        th = _part(name + '_thigh' + side, 'thigh', hips, (sx * 0.118, 0, 0), M['pants'], coll)
        sh = _part(name + '_shin' + side, 'shin', th, (0, 0, -L1), M['pants'], coll)
        ft = _part(name + '_shoe' + side, 'shoe', sh, (0, 0, -L2), M['shoe'], coll)
        ft.rotation_euler.z = sx * -0.08          # toes slightly out
        _part(name + '_sole' + side, 'sole', ft, (0, 0, 0), M['sole'], coll)
        for k in range(5):                       # laces across the tongue (mostly hidden under the trousers)
            t = 0.2 + k * 0.075
            y = SHOE_TOE + 0.01 + t * (SHOE_HEEL - SHOE_TOE - 0.02)
            lc = lib.box((0.066, 0.011, 0.007), (0, y, SOLE_TOP + _shoe_h(t) + 0.001), M['shoe'], rot=(-0.3, 0, 0),
                         bevel=0.0025, name=name + '_lace', coll=coll)
            lc.parent = ft
        ua = _part(name + '_upper' + side, 'upper', hips, (sx * SHOULDER[0], 0, SHOULDER[1]), M['hoodie'], coll)
        fa = _part(name + '_fore' + side, 'fore', ua, (0, 0, -UPPER), M['hoodie'], coll)
        _part(name + '_cuff' + side, 'ring', fa, (0, 0, -FORE - 0.04), M['rib'], coll, scale=(0.088, 0.088, 0.065))
        hd = _part(name + '_hand' + side, 'hand', fa, (0, 0, -FORE - 0.055), M['skin'], coll)
        hd.rotation_euler.z = sx * 0.35          # thumbs turn slightly inwards to the front
        ua.rotation_euler.y = sx * -0.1           # arms hang a little away from the roomy hoodie
        p['thigh' + side], p['shin' + side], p['shoe' + side] = th, sh, ft
        p['upper' + side], p['fore' + side], p['hand' + side] = ua, fa, hd
    if subsurf:
        for ob in [o for o in bpy.data.objects if o.name.startswith(name + '_') and o.type == 'MESH']:
            if ob.data.name.split('.')[0] in ('H_torso', 'H_head', 'H_pocket', 'H_shoe', 'H_sole', 'H_collar',
                                              'H_hand', 'H_browL', 'H_browR', 'H_pelvis'):
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
    step = 2 * (L1 + L2) * math.sin(A) * height * SCALE
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
    """Seated: root at floor level under the hips; seat height = (ANKLE + L2) * SCALE (~0.32 m at height 1.0)."""
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
