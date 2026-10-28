"""The hero of «Каждому по способности»: loads the rigged model (hero/rig_hero.py -> hero_rig.blend) and poses it.

Poses are written as directions of the limbs in the character's own space (x = his left, -y = forward, z = up), so a
pose reads like a description: upper arm 20 degrees out from the body, forearm a bit forward, thigh forward 90 (sitting).
The pose maths runs on the rest matrices only (no depsgraph per bone), keys go into rotation_quaternion.

    h = load(coll, loc, heading)              -> dict(rig=..., body=...)
    key_pose(h, t, POSES['stand'])            # one key at t seconds
    key_pose(h, t, pose('stand', head=(25, -5, 0)))
    walk(h, t0, t1, path=[(x, y), ...], speed=0.9)   # gait keyed along a path (root moves, feet planted)
"""
import math
import os

import bpy
from mathutils import Matrix, Quaternion, Vector

import lib

HERE = os.path.dirname(os.path.abspath(__file__))
CANDIDATES = [os.environ.get('SILA_HERO', ''),
              os.path.join(HERE, '..', 'assets', 'hero_rig.blend'),
              os.path.join(HERE, '..', '..', '..', '..', 'assets3d', 'people', 'own', 'sposobnosti-hero', 'hero_rig.blend')]
F = lib.sec2f
SIDES = (('L', 'Left', 1.0), ('R', 'Right', -1.0))


def blend_path():
    for p in CANDIDATES:
        if p and os.path.exists(p):
            return os.path.abspath(p)
    raise SystemExit('hero_rig.blend not found: ' + ' | '.join(CANDIDATES))


def load(coll=None, loc=(0, 0, 0), heading=0.0, name='Hero', scale=1.0):
    path = blend_path()
    with bpy.data.libraries.load(path, link=False) as (src, dst):
        dst.objects = [n for n in src.objects if n in ('HeroRig', 'Hero')]
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
             order=[b.name for b in _topo(rig.data.bones)])
    h['len'] = {b.name: b.length for b in rig.data.bones}
    hip = rig.data.bones['Hips'].head_local
    ank = rig.data.bones['LeftFoot'].head_local
    h['leg'] = (h['len']['LeftUpLeg'], h['len']['LeftLeg'], hip.z - ank.z, ank.z)
    for m in body.data.materials:
        _matte(m)
    return h


def _matte(m):
    """Back light made the short hair read white (grazing specular): less specular, rougher."""
    if m is None or not m.use_nodes or m.get('sila_matte'):
        return
    nt = m.node_tree
    for n in list(nt.nodes):
        if n.type != 'BSDF_PRINCIPLED':
            continue
        n.inputs['Specular IOR Level'].default_value = 0.12
        r = n.inputs['Roughness']
        if r.is_linked:
            src = r.links[0].from_socket
            mr = nt.nodes.new('ShaderNodeMapRange')
            mr.inputs['To Min'].default_value = 0.65
            mr.inputs['To Max'].default_value = 1.0
            nt.links.new(src, mr.inputs['Value'])
            nt.links.new(mr.outputs['Result'], r)
        else:
            r.default_value = max(r.default_value, 0.7)
    m['sila_matte'] = 1


def _topo(bones):
    out, seen = [], set()

    def add(b):
        if b.name in seen:
            return
        if b.parent:
            add(b.parent)
        seen.add(b.name)
        out.append(b)
    for b in bones:
        add(b)
    return out


# ----------------------------------------------------------------------------- directions
def V3(x, y, z):
    v = Vector((x, y, z))
    return v.normalized() if v.length > 1e-9 else Vector((0, 0, -1))


def limb(s, out=0.0, fwd=0.0, back=False):
    """Direction of an arm segment: `out` degrees raised sideways from hanging down, `fwd` degrees raised forward
    (180 = straight up). s = +1 left, -1 right."""
    a, f = math.radians(out), math.radians(fwd)
    return V3(s * math.sin(a), -math.sin(f), -math.cos(a) * math.cos(f))


def leg(s, th, spread=4.0):
    """Leg segment: th degrees forward from vertical (negative = backward)."""
    t, sp = math.radians(th), math.radians(spread)
    return V3(s * math.sin(sp), -math.sin(t), -math.cos(t))


# ----------------------------------------------------------------------------- poses
BASE = dict(arm=(24, 4), fore=(18, 16), thigh=0.0, shin=0.0, foot=0.0, spread=3.0, lean=0.0, side=0.0, twist=0.0,
            head=(0.0, 0.0, 0.0), hips=0.0)


def pose(base='stand', **kw):
    """A pose dict; per-side values are (left, right) tuples or one value for both sides."""
    p = dict(POSES[base]) if isinstance(base, str) else dict(base)
    p.update(kw)
    return p


def _sidev(v, k):
    """per-side value: ((a, b), (c, d)) -> per side; (a, b) -> same both; scalar for legs: (l, r) or x."""
    if isinstance(v, (tuple, list)) and len(v) == 2 and isinstance(v[0], (tuple, list)):
        return v[k]
    return v


def _legv(v, k):
    return v[k] if isinstance(v, (tuple, list)) else v


POSES = {
    'tpose': dict(BASE, arm=(90, 0), fore=(90, 0)),
    'stand': dict(BASE),
    'hands_front': dict(BASE, arm=(16, 30), fore=(10, 80), head=(0, 22, 0)),        # looking at his palms
    'arms_up': dict(BASE, arm=(28, 165), fore=(24, 175), head=(0, -12, 0)),
    'crouch': dict(BASE, arm=(20, -35), fore=(18, -20), thigh=55.0, shin=-30.0, foot=0.0, lean=28.0, hips=-0.13),
    'reach': dict(BASE, arm=((14, 70), (24, 4)), fore=((10, 80), (18, 16)), lean=4.0),   # left hand forward (a shoulder)
    'reach_r': dict(BASE, arm=((24, 4), (14, 70)), fore=((18, 16), (10, 80)), lean=4.0),
    'sit': dict(BASE, arm=(16, 30), fore=(12, 70), thigh=88.0, shin=8.0, foot=0.0, hips=0.0),
    'sit_stare': dict(BASE, arm=(18, 42), fore=(30, 120), thigh=88.0, shin=6.0, lean=18.0, head=(0, 8, 0)),
    'sill': dict(BASE, arm=(12, 52), fore=(8, 70), lean=10.0, head=(0, -4, 0)),       # hands on a window sill
    'flat': dict(BASE, arm=(40, 165), fore=(40, 172), thigh=-4.0, shin=-10.0, foot=-40.0, head=(0, -30, 0)),  # face down
    'superman': dict(BASE, arm=(8, 150), fore=(8, 160), head=(0, -20, 0)),
    'shrug': dict(BASE, arm=(30, 10), fore=(50, 80), head=(0, -6, 8)),
    'point': dict(BASE, arm=((24, 4), (8, 85)), fore=((18, 16), (6, 88))),
}


# ----------------------------------------------------------------------------- forward kinematics on rest matrices
def _solve(h, p):
    """Local quaternions per bone for pose p, plus the hips offset in metres (world up)."""
    rest, par = h['rest'], h['parent']
    q = {n: Quaternion() for n in rest}
    P = {}

    def A_of(n):
        pn = par[n]
        if pn is None:
            return rest[n].copy()
        return P[pn] @ rest[pn].inverted() @ rest[n]

    def aim(n, d):
        A = A_of(n)
        y0 = (A.to_3x3() @ Vector((0, 1, 0))).normalized()
        r = y0.rotation_difference(d)
        Aq = A.to_quaternion()
        q[n] = Aq.inverted() @ r @ Aq
        P[n] = A @ q[n].to_matrix().to_4x4()

    def keep(n, extra=None):
        A = A_of(n)
        if extra is not None:
            q[n] = extra
        P[n] = A @ q[n].to_matrix().to_4x4()

    lean, side, twist = math.radians(p['lean']), math.radians(p.get('side', 0.0)), math.radians(p.get('twist', 0.0))
    for n in h['order']:
        if n == 'Hips':
            keep(n, Quaternion((0, 1, 0), twist * 0.3))
        elif n in ('Spine', 'Spine1', 'Spine2'):
            k = {'Spine': 1, 'Spine1': 2, 'Spine2': 3}[n]
            a = lean * k / 3
            sd = side * k / 3
            aim(n, V3(math.sin(sd), -math.sin(a), math.cos(a) * math.cos(sd)))
            q[n] = q[n] @ Quaternion((0, 1, 0), twist * 0.23)
            P[n] = A_of(n) @ q[n].to_matrix().to_4x4()
        elif n == 'Neck':
            aim(n, V3(0, 0, 1))
        elif n == 'Head':
            yaw, pitch, roll = (math.radians(v) for v in p['head'])
            aim(n, V3(0, 0, 1))
            q[n] = q[n] @ Quaternion((0, 1, 0), yaw) @ Quaternion((1, 0, 0), pitch) @ Quaternion((0, 0, 1), -roll)
            P[n] = A_of(n) @ q[n].to_matrix().to_4x4()
        else:
            for k, (a, nm, s) in enumerate(SIDES):
                if not n.startswith(nm):
                    continue
                part = n[len(nm):]
                if part == 'Shoulder':
                    keep(n)
                elif part == 'Arm':
                    aim(n, limb(s, *_sidev(p['arm'], k)))
                elif part == 'ForeArm':
                    aim(n, limb(s, *_sidev(p['fore'], k)))
                elif part == 'Hand':
                    keep(n)
                elif part == 'UpLeg':
                    aim(n, leg(s, _legv(p['thigh'], k), _legv(p['spread'], k)))
                elif part == 'Leg':
                    aim(n, leg(s, _legv(p['shin'], k), _legv(p['spread'], k) * 0.5))
                elif part == 'Foot':
                    r = rest[n]
                    d0 = (r.to_3x3() @ Vector((0, 1, 0))).normalized()
                    pitch = math.radians(_legv(p['foot'], k))
                    aim(n, (Quaternion((1, 0, 0), -pitch) @ d0).normalized())
                else:
                    keep(n)
    return q


def apply(h, p):
    q = _solve(h, p)
    rig = h['rig']
    for n, v in q.items():
        rig.pose.bones[n].rotation_quaternion = v
    hb = rig.pose.bones['Hips']
    up = h['rest']['Hips'].to_3x3().inverted() @ Vector((0, 0, p.get('hips', 0.0)))
    hb.location = up
    return q


def key_pose(h, t, p, interp=None):
    apply(h, p)
    fr = F(t)
    for pb in h['rig'].pose.bones:
        pb.keyframe_insert('rotation_quaternion', frame=fr)
    h['rig'].pose.bones['Hips'].keyframe_insert('location', frame=fr)
    if interp:
        lib._set_interp(h['rig'], interp)


def mix(a, b, w):
    """Blend two poses (numbers and tuples linearly)."""
    out = {}
    for k in set(a) | set(b):
        va, vb = a.get(k, b.get(k)), b.get(k, a.get(k))
        out[k] = _lerp(va, vb, w)
    return out


def _lerp(a, b, w):
    if isinstance(a, (tuple, list)):
        return tuple(_lerp(x, y, w) for x, y in zip(a, b))
    return a + (b - a) * w


def key_root(h, t, loc=None, heading=None):
    rig = h['rig']
    if loc is not None:
        rig.location = loc
        rig.keyframe_insert('location', frame=F(t))
    if heading is not None:
        rig.rotation_euler.z = heading
        rig.keyframe_insert('rotation_euler', index=2, frame=F(t))


# ----------------------------------------------------------------------------- walk
def gait(h, u, A=22.0, base=None, arms=True):
    """Pose at gait phase u in [0, 1): left heel strike at 0, right at 0.5 (people2 gait, in degrees)."""
    base = dict(base or POSES['stand'])
    L1, L2, HIPZ, _ = h['leg']
    th, kn, ft = [], [], []
    for uu in (u % 1.0, (u + 0.5) % 1.0):
        if uu < 0.5:
            s = uu / 0.5
            a = A - 2 * A * s                     # forward -> back while planted
            k = 10.0 * math.sin(math.pi * s)
            f = 0.0
        else:
            s = (uu - 0.5) / 0.5
            e = (1 - math.cos(math.pi * s)) / 2
            a = -A + 2 * A * e
            k = 62.0 * math.sin(math.pi * s) ** 1.3
            f = -18.0 * math.sin(math.pi * s)
        th.append(a)
        kn.append(a - k)
        ft.append(f)
    st = 0 if (u % 1.0) < 0.5 else 1
    ta, sa = math.radians(th[st]), math.radians(kn[st])
    hz = L1 * math.cos(ta) + L2 * math.cos(sa) - (L1 + L2)
    p = dict(base, thigh=tuple(th), shin=tuple(kn), foot=tuple(ft), hips=hz)
    if arms:
        out = base['arm'][0] if not isinstance(base['arm'][0], (tuple, list)) else base['arm'][0][0]
        p['arm'] = ((out, 0.8 * th[1] + 2), (out, 0.8 * th[0] + 2))
        p['fore'] = ((out - 6, 0.8 * th[1] + 22), (out - 6, 0.8 * th[0] + 22))
    p['twist'] = 4.0 * math.sin(2 * math.pi * u)
    return p


def walk(h, t0, t1, path, speed=0.9, A=22.0, base=None, per=8, arms=True, phase=0.0):
    """Walk along `path` [(x, y), ...] from t0 to t1 at `speed` m/s (stops at the end of the path)."""
    L1, L2, _, _ = h['leg']
    step = 2 * (L1 + L2) * math.sin(math.radians(A)) * h['rig'].scale[0]
    P = 2 * step / max(0.2, speed)
    pts = [Vector((x, y, h['rig'].location.z)) for x, y in path]
    seg = [(pts[i + 1] - pts[i]).length for i in range(len(pts) - 1)]
    total = sum(seg)
    dur = min(t1 - t0, total / speed)

    def at(d):
        for i, L in enumerate(seg):
            if d <= L or i == len(seg) - 1:
                w = min(1.0, d / max(L, 1e-6))
                return pts[i].lerp(pts[i + 1], w), pts[i + 1] - pts[i]
            d -= L

    n = max(2, int(dur / P * per) + 1)
    for j in range(n + 1):
        t = t0 + dur * j / n
        p, dv = at(speed * (t - t0))
        hd = math.atan2(dv.x, -dv.y)
        key_root(h, t, tuple(p), hd)
        key_pose(h, t, gait(h, phase + (t - t0) / P, A, base, arms))
    return t0 + dur


# ----------------------------------------------------------------------------- test sheet (rig_hero.py)
def test_sheet(rig, body, out):
    h = dict(rig=rig, body=body, rest={b.name: b.matrix_local.copy() for b in rig.data.bones},
             parent={b.name: (b.parent.name if b.parent else None) for b in rig.data.bones},
             order=[b.name for b in _topo(rig.data.bones)], len={b.name: b.length for b in rig.data.bones})
    hip = rig.data.bones['Hips'].head_local
    ank = rig.data.bones['LeftFoot'].head_local
    h['leg'] = (h['len']['LeftUpLeg'], h['len']['LeftLeg'], hip.z - ank.z, ank.z)
    for pb in rig.pose.bones:
        pb.rotation_mode = 'QUATERNION'
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.samples = 16
    sc.cycles.use_denoising = True
    sc.render.resolution_x, sc.render.resolution_y = 420, 620
    sc.world = bpy.data.worlds.new('w')
    sc.world.use_nodes = True
    sc.world.node_tree.nodes['Background'].inputs[0].default_value = (0.72, 0.73, 0.76, 1)
    sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN'))
    sun.data.energy = 2.5
    sun.rotation_euler = (math.radians(50), 0, math.radians(-30))
    sc.collection.objects.link(sun)
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
    sc.collection.objects.link(cam)
    sc.camera = cam
    cam.data.type = 'ORTHO'
    cam.data.ortho_scale = 2.0
    shots = [('stand', POSES['stand'], 35), ('walk', gait(h, 0.12), 60), ('arms_up', POSES['arms_up'], 30),
             ('crouch', POSES['crouch'], 70), ('sit', POSES['sit'], 70), ('reach', POSES['reach'], 60),
             ('hands_front', POSES['hands_front'], 25), ('flat', POSES['flat'], 90)]
    files = []
    for nm, p, ang in shots:
        apply(h, p)
        a = math.radians(ang)
        cam.location = (5 * math.sin(a), -5 * math.cos(a), 0.78)
        cam.rotation_euler = (math.pi / 2, 0, a)
        sc.render.filepath = out.replace('.png', f'_{nm}.png')
        bpy.ops.render.render(write_still=True)
        files.append(sc.render.filepath)
    print('TEST', files)
