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
        _eyes(m)
    for k in ('eye_gx', 'eye_gz', 'eye_blink'):
        body[k] = 0.0
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


# ----------------------------------------------------------------------------- living eyes (28.10.2026)
# The generated model has its eyes painted into the texture. The shader draws new eyes over them on the undeformed
# mesh (Generated coordinates = rest pose, so they stay on the face whatever the bones do): white, brown iris with
# pupil and two highlights, the upper lash line and an eyelid that closes for a blink. Driven by the body object's
# custom properties eye_gx / eye_gz (gaze, -1..1, + = his left / up) and eye_blink (0 open .. 1 closed).
BOX = ((-0.63782, -0.32114, 0.0), (1.27564, 0.64227, 1.55))       # texture space of the mesh (its bounding box)
EYES = ((-0.1309, 1.1428, 0.0640, 0.0570), (0.1350, 1.1442, 0.0677, 0.0583))   # x, z, half width, half height (m)


def _lin(hexc):
    c = hexc.lstrip('#')
    return tuple(((v / 255) / 12.92 if v / 255 <= 0.04045 else ((v / 255 + 0.055) / 1.055) ** 2.4)
                 for v in (int(c[i:i + 2], 16) for i in (0, 2, 4))) + (1.0,)


def _eyes(m):
    if m is None or not m.use_nodes or m.get('sila_eyes'):
        return
    nt = m.node_tree
    N, L = nt.nodes, nt.links
    bsdf = next(n for n in N if n.type == 'BSDF_PRINCIPLED')

    def node(t, **kw):
        n = N.new(t)
        for k, v in kw.items():
            setattr(n, k, v)
        return n

    def put(sock, v):
        if isinstance(v, (int, float)):
            sock.default_value = v
        else:
            L.new(v, sock)

    def M(op, a, b=0.0, c=None, clamp=False):
        n = node('ShaderNodeMath', operation=op, use_clamp=clamp)
        put(n.inputs[0], a)
        put(n.inputs[1], b)
        if c is not None:
            put(n.inputs[2], c)
        return n.outputs[0]

    def smooth(x, lo, hi):                       # 0 below lo, 1 above hi
        n = node('ShaderNodeMapRange', interpolation_type='SMOOTHSTEP')
        put(n.inputs['Value'], x)
        put(n.inputs['From Min'], lo)
        put(n.inputs['From Max'], hi)
        return n.outputs['Result']

    def mixc(a, b, fac):
        n = node('ShaderNodeMix', data_type='RGBA', clamp_factor=True)
        put(n.inputs['Factor'], fac)
        for sock, v in ((n.inputs[6], a), (n.inputs[7], b)):
            if isinstance(v, tuple):
                sock.default_value = v
            else:
                L.new(v, sock)
        return n.outputs[2]

    def attr(name):
        return node('ShaderNodeAttribute', attribute_type='OBJECT', attribute_name=name).outputs['Fac']

    tc = node('ShaderNodeTexCoord')
    mp = node('ShaderNodeMapping', vector_type='POINT')
    mp.inputs['Location'].default_value = BOX[0]
    mp.inputs['Scale'].default_value = BOX[1]
    L.new(tc.outputs['Generated'], mp.inputs['Vector'])
    xyz = node('ShaderNodeSeparateXYZ')
    L.new(mp.outputs['Vector'], xyz.inputs['Vector'])
    X, Y, Z = xyz.outputs['X'], xyz.outputs['Y'], xyz.outputs['Z']
    gx, gz, blink = attr('eye_gx'), attr('eye_gz'), attr('eye_blink')
    front = M('LESS_THAN', Y, -0.12)
    lid = M('MULTIPLY_ADD', blink, -1.38, 1.03)              # lid line in eye units: above the eye (open) .. -0.35
    shut = smooth(blink, 0.7, 1.0)                           # the lower part goes too: a closed eye is one lash arc
    icu = M('MULTIPLY', gx, 0.36)
    icv = M('MULTIPLY_ADD', gz, 0.22, -0.03)

    col, masks = bsdf.inputs['Base Color'].links[0].from_socket, []
    for cx, cz, ax, az in EYES:
        u = M('DIVIDE', M('SUBTRACT', X, cx), ax)
        v = M('DIVIDE', M('SUBTRACT', Z, cz), az)
        r2 = M('ADD', M('MULTIPLY', u, u), M('MULTIPLY', v, v))
        eye = M('MULTIPLY', M('SUBTRACT', 1.0, smooth(r2, 0.90, 1.0)), front)
        du = M('DIVIDE', M('SUBTRACT', u, icu), 0.58)
        dv = M('DIVIDE', M('SUBTRACT', v, icv), 0.75)
        ri2 = M('ADD', M('MULTIPLY', du, du), M('MULTIPLY', dv, dv))
        iris = M('SUBTRACT', 1.0, smooth(ri2, 0.88, 1.0))
        pupil = M('SUBTRACT', 1.0, smooth(ri2, 0.14, 0.19))

        def spot(ox, oy, rx, ry):
            hu = M('DIVIDE', M('SUBTRACT', M('SUBTRACT', u, icu), ox), rx)
            hv = M('DIVIDE', M('SUBTRACT', M('SUBTRACT', v, icv), oy), ry)
            return M('SUBTRACT', 1.0, smooth(M('ADD', M('MULTIPLY', hu, hu), M('MULTIPLY', hv, hv)), 0.6, 1.0))
        shine = M('MULTIPLY', M('MAXIMUM', spot(-0.20, 0.33, 0.17, 0.19), spot(0.17, -0.40, 0.08, 0.09)), iris)
        vv = M('MULTIPLY_ADD', M('MULTIPLY', u, u), -0.22, v)          # the lid edge bows down in the middle
        above = smooth(vv, M('SUBTRACT', lid, 0.04), M('ADD', lid, 0.04))
        below = M('MULTIPLY', M('SUBTRACT', 1.0, smooth(vv, M('SUBTRACT', lid, 0.30), M('SUBTRACT', lid, 0.22))), shut)
        skin = M('MAXIMUM', above, below)
        lash = M('MULTIPLY', smooth(vv, M('SUBTRACT', lid, 0.26), M('SUBTRACT', lid, 0.17)), M('SUBTRACT', 1.0, skin))
        shade = smooth(vv, M('SUBTRACT', lid, 0.95), M('SUBTRACT', lid, 0.15))
        rim = smooth(r2, 0.70, 0.86)
        c = mixc(_lin('#F2EEE9'), _lin('#C9BDB4'), M('MULTIPLY', shade, 0.7))
        irc = mixc(_lin('#2B1A12'), _lin('#7A4B2D'), smooth(dv, 0.05, -0.95))
        irc = mixc(irc, _lin('#140C08'), smooth(ri2, 0.62, 0.92))
        c = mixc(c, irc, iris)
        c = mixc(c, _lin('#0B0706'), pupil)
        c = mixc(c, _lin('#FFFFFF'), shine)
        c = mixc(c, _lin('#2A1C17'), rim)
        c = mixc(c, _lin('#181010'), lash)
        c = mixc(c, _lin('#DDB096'), skin)
        col = mixc(col, c, eye)
        masks.append((eye, skin))
    L.new(col, bsdf.inputs['Base Color'])
    inside = M('ADD', masks[0][0], masks[1][0], clamp=True)
    nm = next((n for n in N if n.type == 'NORMAL_MAP'), None)
    if nm:
        L.new(M('SUBTRACT', 1.0, inside), nm.inputs['Strength'])
    r = bsdf.inputs['Roughness']
    gloss = M('MULTIPLY', inside, M('SUBTRACT', 1.0, M('MAXIMUM', masks[0][1], masks[1][1])))
    if r.is_linked:
        src = r.links[0].from_socket
        L.new(M('ADD', M('MULTIPLY', src, M('SUBTRACT', 1.0, gloss)), M('MULTIPLY', gloss, 0.32)), r)
    m['sila_eyes'] = 1


def _key_prop(ob, k, t, v, interp='BEZIER'):
    ob[k] = v
    ob.keyframe_insert(f'["{k}"]', frame=F(t))
    fc = ob.animation_data.action.fcurves.find(f'["{k}"]')
    for kp in fc.keyframe_points if fc else []:
        if abs(kp.co.x - F(t)) < 0.01:
            kp.interpolation = interp


def alive(h, t0, t1, seed=0, gaze=(0.0, 0.0), spread=0.45, looks=(), breath=True, head=True):
    """Blinks, small eye moves around `gaze`, breathing and a slight head drift for one hero over [t0, t1] s.
    `looks`: windows (ta, tb, gx, gz) where he looks at one thing (the eyes jump there at ta and back at tb)."""
    import random
    rnd = random.Random(seed)
    body, rig = h['body'], h['rig']
    # blinks: every 2.2-4.5 s, sometimes a double blink
    _key_prop(body, 'eye_blink', t0, 0.0, 'CONSTANT')
    t = t0 + rnd.uniform(0.5, 1.4)
    while t < t1 - 0.2:
        for b in ([t] if rnd.random() > 0.2 else [t, t + 0.32]):
            _key_prop(body, 'eye_blink', b - 0.07, 0.0, 'LINEAR')
            _key_prop(body, 'eye_blink', b, 1.0, 'LINEAR')
            _key_prop(body, 'eye_blink', b + 0.05, 1.0, 'LINEAR')
            _key_prop(body, 'eye_blink', b + 0.16, 0.0, 'CONSTANT')
        t += rnd.uniform(2.2, 4.5)
    # gaze: hold 0.5-1.8 s, jump in 0.07 s; now and then a longer look aside
    t, gx, gz = t0, gaze[0], gaze[1]
    _key_prop(body, 'eye_gx', t0, gx, 'CONSTANT')
    _key_prop(body, 'eye_gz', t0, gz, 'CONSTANT')
    marks = sorted(x for a, b, *_ in looks for x in (a, b))
    while t < t1:
        nt = t + rnd.uniform(0.5, 1.8)
        t = next((x for x in marks if t + 0.1 < x <= nt), nt)
        cx, cz, sp = next(((x, z, 0.05) for a, b, x, z in looks if a <= t < b), (gaze[0], gaze[1], spread))
        far = rnd.random() < 0.25
        nx = max(-1.0, min(1.0, cx + rnd.uniform(-1, 1) * (min(0.85, sp * 2.5) if far else sp)))
        nz = max(-0.8, min(0.8, cz + rnd.uniform(-1, 1) * sp * 0.6))
        for k, a, b in (('eye_gx', gx, nx), ('eye_gz', gz, nz)):
            _key_prop(body, k, t, a, 'LINEAR')
            _key_prop(body, k, t + 0.07, b, 'CONSTANT')
        gx, gz = nx, nz
    act = rig.animation_data.action if rig.animation_data else None
    if not act:
        return
    if breath:                                   # chest: about 1.5 degrees, one breath in 3.4 s
        for bn, amp in (('Spine2', 0.013), ('Spine1', 0.006)):
            fc = act.fcurves.find(f'pose.bones["{bn}"].rotation_quaternion', index=1)
            if fc:
                s = fc.modifiers.new('FNGENERATOR')
                s.function_type, s.use_additive = 'SIN', True
                s.amplitude, s.phase_multiplier = amp, 2 * math.pi / (3.4 * lib.FPS)
                s.phase_offset = rnd.uniform(0, 6.28)
    if head:                                     # head: slow drift of a couple of degrees
        for i, amp in ((1, 0.030), (2, 0.022), (3, 0.040)):
            fc = act.fcurves.find('pose.bones["Head"].rotation_quaternion', index=i)
            if fc:
                n = fc.modifiers.new('NOISE')
                n.blend_type, n.strength, n.scale = 'REPLACE', amp, 1.6 * lib.FPS
                n.phase, n.offset = rnd.uniform(1, 50), rnd.uniform(0, 500)


def alive_all(scene, seed=0):
    """build_pc.py hook: every hero in the scene comes alive for the whole shot."""
    t1 = scene.frame_end / lib.FPS
    for i, ob in enumerate(o for o in scene.objects if o.type == 'MESH' and 'eye_blink' in o.keys()):
        rig = ob.parent
        if rig is None or rig.type != 'ARMATURE':
            continue
        ad = ob.animation_data
        if ad and ad.action and ad.action.fcurves.find('["eye_blink"]'):
            continue                             # the scene keyed its own eyes
        alive(dict(body=ob, rig=rig), 0.0, t1 + 0.5, seed=seed * 7 + i, gaze=tuple(ob.get('eye_look', (0.0, 0.0))),
              spread=ob.get('eye_spread', 0.45), looks=[tuple(w) for w in ob.get('eye_looks', [])])


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
