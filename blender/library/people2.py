"""Better simple people for the classic style (built from code, same matte look as lib.person).
Jointed legs (thigh / shin / shoe), arms (upper / fore / hand), neck, hair, nose. Root pivot at the feet,
forward = local -Y, root.scale = height factor (1.0 = 1.75 m), exactly like lib.person, so lib.move_root works.
walk(): a keyed gait cycle where the stance foot stays planted on the ground (hip height follows the stance leg),
the swing knee bends and the foot clears the ground; stride is matched to the walking speed so feet do not slide.
"""
import bpy, bmesh, math, random
import lib

L1, L2, ANKLE, HIP = 0.42, 0.42, 0.06, 0.90     # thigh, shin, ankle height, hip joint height (unscaled)
SHOULDER = (0.19, 0.47)                          # x, z relative to the hip joint
A_SWING = 0.38                                   # thigh swing amplitude, rad
HAIR = ['#2B2420', '#3D2B20', '#5A3E2A', '#8A6A48', '#1E1C1B', '#B9A38A', '#6B4A33']
SHOES = ['#1F1C1A', '#2E2824', '#4A3A2E', '#3A3631']
PANTS = ['#2B2826', '#3A3631', '#4A4540', '#2E3236', '#5A4B3E', '#6E6458', '#3C4652']

_meshes = {}


def _mesh(name, bm, smooth=True):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    if smooth:
        me.polygons.foreach_set('use_smooth', [True] * len(me.polygons))
    return me


def _capsule(rt, rb, length, segs=14, rings=10):
    """Limb from a joint at z=0 down to z=-length; spherical caps of radius rt (top) and rb (bottom)."""
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=rings, radius=1.0)
    for v in bm.verts:
        if v.co.z >= 0:
            v.co = v.co * rt
        else:
            v.co = v.co * rb
            v.co.z -= length
    return bm


def _parts():
    if _meshes:
        return _meshes
    _meshes['thigh'] = _mesh('P2_thigh', _capsule(0.075, 0.058, L1))
    _meshes['shin'] = _mesh('P2_shin', _capsule(0.056, 0.045, L2))
    _meshes['upper'] = _mesh('P2_upper', _capsule(0.052, 0.045, 0.27))
    _meshes['fore'] = _mesh('P2_fore', _capsule(0.043, 0.037, 0.24))
    _meshes['torso'] = _mesh('P2_torso', _capsule(0.17, 0.15, 0.32, segs=18, rings=12))
    _meshes['neck'] = _mesh('P2_neck', _capsule(0.048, 0.05, 0.06, segs=10, rings=6))
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=20, v_segments=14, radius=0.105)
    _meshes['head'] = _mesh('P2_head', bm)
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=8, radius=1.0)
    _meshes['ball'] = _mesh('P2_ball', bm)
    # hair: a sphere cap that keeps the face free (front-lower part removed)
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=20, v_segments=14, radius=0.113)
    kill = [v for v in bm.verts if (v.co.z < -0.01 and v.co.y < 0.03) or v.co.z < -0.075]
    bmesh.ops.delete(bm, geom=kill, context='VERTS')
    _meshes['hair'] = _mesh('P2_hair', bm)
    # shoe: pivot at the ankle (top back), toe forward (-Y)
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= 0.095
        v.co.y = -0.055 + v.co.y * 0.25          # y from -0.18 to +0.07
        v.co.z = -0.03 + v.co.z * 0.065          # z from -0.0625 to 0.0025
    bmesh.ops.bevel(bm, geom=[e for e in bm.edges], offset=0.018, segments=2, affect='EDGES')
    _meshes['shoe'] = _mesh('P2_shoe', bm)
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= 0.1; v.co.y *= 0.3; v.co.z *= 0.24
    _meshes['bag'] = _mesh('P2_bag', bm, smooth=False)
    return _meshes


def _part(name, key, parent, loc, m, coll, scale=None):
    ob = bpy.data.objects.new(name, _parts()[key])
    lib._link(ob, coll)
    lib._obj_mat(ob, m)
    ob.parent = parent
    ob.location = loc
    if scale:
        ob.scale = scale
    return ob


def person(loc=(0, 0, 0), heading=0.0, height=1.0, rng=None, coll=None, bag=False, name='P'):
    rng = rng or random
    top = lib.pmat(rng.choice(lib.PEOPLE_COLS))
    pants = lib.pmat(rng.choice(PANTS))
    skin = lib.pmat(rng.choice(lib.SKIN))
    hair = lib.pmat(rng.choice(HAIR))
    shoe = lib.pmat(rng.choice(SHOES))
    root = lib.empty(name, loc, (0, 0, heading), coll=coll)
    root.scale = (height, height, height)
    hips = lib.empty(name + '_hips', (0, 0, HIP), coll=coll)
    hips.parent = root
    p = dict(root=root, hips=hips)
    p['pelvis'] = _part(name + '_pelvis', 'ball', hips, (0, 0, 0.03), pants, coll, scale=(0.16, 0.11, 0.11))
    p['torso'] = _part(name + '_torso', 'torso', hips, (0, 0, 0.40), top, coll, scale=(1.0, 0.66, 1.0))
    p['neck'] = _part(name + '_neck', 'neck', hips, (0, 0.0, 0.63), skin, coll)
    p['head'] = _part(name + '_head', 'head', hips, (0, 0, 0.72), skin, coll, scale=(0.92, 1.0, 1.06))
    _part(name + '_hair', 'hair', p['head'], (0, 0.012, 0.012), hair, coll)
    _part(name + '_nose', 'ball', p['head'], (0, -0.1, -0.012), skin, coll, scale=(0.017, 0.022, 0.02))
    for side, sx in (('L', 1), ('R', -1)):
        th = _part(name + '_thigh' + side, 'thigh', hips, (sx * 0.085, 0, 0), pants, coll)
        sh = _part(name + '_shin' + side, 'shin', th, (0, 0, -L1), pants, coll)
        ft = _part(name + '_shoe' + side, 'shoe', sh, (0, 0, -L2), shoe, coll)
        ua = _part(name + '_upper' + side, 'upper', hips, (sx * SHOULDER[0], 0, SHOULDER[1]), top, coll)
        fa = _part(name + '_fore' + side, 'fore', ua, (0, 0, -0.27), top, coll)
        hd = _part(name + '_hand' + side, 'ball', fa, (0, 0, -0.27), skin, coll, scale=(0.036, 0.03, 0.048))
        ua.rotation_euler.y = sx * 0.06      # arms hang slightly away from the body
        p['thigh' + side], p['shin' + side], p['shoe' + side] = th, sh, ft
        p['upper' + side], p['fore' + side], p['hand' + side] = ua, fa, hd
    if bag:
        b = _part(name + '_bag', 'bag', hips, (0.2, 0.0, 0.0), lib.pmat(rng.choice(['#3A3631', '#6B4E3D', '#5D6A72'])), coll)
        p['bag'] = b
    return p


# ----------------------------------------------------------------------------- gait
def _leg(u, A):
    """Thigh angle th, knee bend k, shoe angle f for gait phase u (0 = heel strike, stance until 0.5)."""
    if u < 0.5:
        s = u / 0.5
        th = -A + 2 * A * s                       # linear: the planted foot moves back at constant speed
        k = 0.14 * math.sin(math.pi * s)
        f = -(th + k)                             # shoe flat on the ground
    else:
        s = (u - 0.5) / 0.5
        e = (1 - math.cos(math.pi * s)) / 2
        th = A - 2 * A * e
        k = 1.05 * math.sin(math.pi * s) ** 1.3
        f = -(th + k) + 0.3 * math.sin(math.pi * s)
    return th, k, f


def _key(ob, path, idx, frame, value):
    getattr(ob, path)[idx] = value
    ob.keyframe_insert(path, index=idx, frame=frame)


def _cycle(obs):
    for ob in obs:
        ad = ob.animation_data
        if ad and ad.action:
            for fc in ad.action.fcurves:
                if not any(m.type == 'CYCLES' for m in fc.modifiers):
                    fc.modifiers.new('CYCLES')


def walk(p, speed=1.2, phase=0.0, height=1.0, fps=None, samples=24):
    """Keyed, looping walk cycle matched to `speed` (m/s) of the root (use lib.move_root with the same speed)."""
    fps = fps or lib.FPS
    A = A_SWING
    step = 2 * (L1 + L2) * math.sin(A) * height
    P = 2 * step / max(0.3, speed)                # one cycle = two steps
    f0 = 1 - phase * P * fps
    for j in range(samples + 1):
        t = j / samples
        fr = f0 + t * P * fps
        uL, uR = t % 1.0, (t + 0.5) % 1.0
        legs = {}
        for side, u in (('L', uL), ('R', uR)):
            th, k, f = _leg(u, A)
            legs[side] = (u, th, k)
            _key(p['thigh' + side], 'rotation_euler', 0, fr, th)
            _key(p['shin' + side], 'rotation_euler', 0, fr, k)
            _key(p['shoe' + side], 'rotation_euler', 0, fr, f)
            arm = -0.75 * th
            _key(p['upper' + side], 'rotation_euler', 0, fr, arm)
            _key(p['fore' + side], 'rotation_euler', 0, fr, -0.28 - 0.35 * max(0.0, -arm) / (0.75 * A))
        u, th, k = legs['L'] if legs['L'][0] < 0.5 else legs['R']
        _key(p['hips'], 'location', 2, fr, ANKLE + L1 * math.cos(th) + L2 * math.cos(th + k))
        _key(p['torso'], 'rotation_euler', 2, fr, 0.08 * math.sin(2 * math.pi * t))   # shoulders counter-rotate
    _cycle([p[k] for k in ('thighL', 'thighR', 'shinL', 'shinR', 'shoeL', 'shoeR', 'upperL', 'upperR', 'foreL', 'foreR',
                           'hips', 'torso')])
    return P


def sit(p, rng=None):
    """Seated pose (root at floor level under the hips, see sit_root_z). Small living motion on head and one arm."""
    rng = rng or random
    for side in ('L', 'R'):
        p['thigh' + side].rotation_euler.x = -math.pi / 2
        p['shin' + side].rotation_euler.x = math.pi / 2 - rng.uniform(-0.1, 0.15)
        p['upper' + side].rotation_euler.x = -rng.uniform(0.45, 0.7)
        p['fore' + side].rotation_euler.x = -rng.uniform(0.8, 1.1)
    p['hips'].location.z = ANKLE + L2
    lib.add_sine(p['head'], 'rotation_euler', 0, 0.07, rng.uniform(2.2, 3.6), rng.uniform(0, 6))
    lib.add_sine(p['head'], 'rotation_euler', 2, 0.12, rng.uniform(3.0, 5.0), rng.uniform(0, 6))
    lib.add_sine(p['foreR'], 'rotation_euler', 0, 0.18, rng.uniform(1.6, 2.8), rng.uniform(0, 6))
    return p


def stand(p, rng=None):
    """Standing idle: weight shift and small arm/head motion."""
    rng = rng or random
    lib.add_sine(p['hips'], 'rotation_euler', 1, 0.025, rng.uniform(3.0, 4.5), rng.uniform(0, 6))
    lib.add_sine(p['head'], 'rotation_euler', 2, 0.15, rng.uniform(3.0, 5.0), rng.uniform(0, 6))
    lib.add_sine(p['foreR'], 'rotation_euler', 0, 0.25, rng.uniform(1.5, 2.5), rng.uniform(0, 6), offset=-0.4)
    return p
