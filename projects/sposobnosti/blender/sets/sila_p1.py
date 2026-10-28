"""Part 1 of «Каждому по способности»: the night everybody got a power, the crazy morning, the hero without one.
One function per scene (variant), times inside the shot come from shot['events'] (tools/build_timeline.py).
"""
import math
import random

import bpy
from mathutils import Vector as V

import lib
import metro_mats as MM
import people2 as P2
import prooms as PR
import sila as S
import sila_fx as FX
import sila_hero as H
import sila_sets as SS

F = lib.sec2f
AURA = ['#FFC857', '#7FD8FF', '#FF7AB6', '#9DFF8A', '#C59BFF', '#FF9C5B', '#6FFFE1', '#FFE66B']


def _ev(shot, k, d):
    return shot.get('events', {}).get(k, d)


def hide_person(p, t, visible=False):
    """Switch a people2 figure (all its parts) off or on at t."""
    for o in [p['root']] + list(p['root'].children_recursive):
        FX.key_hide(o, [(0, not visible), (t, visible)])


def road_side(shot, d=8.0):
    """+1 if the road is to the right of the shot camera, -1 if to the left (the lower ground of the two probes)."""
    zs = []
    for s in (1, -1):
        p, _, _ = S.ahead(shot, d, s * 4.5)
        zs.append(S.ground(p.x, p.y))
    return 1 if zs[0] < zs[1] - 0.05 else -1 if zs[1] < zs[0] - 0.05 else 1


def wall_dist(p, direction, z=1.2, far=25.0):
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    hit, loc, n, i, ob, M = bpy.context.scene.ray_cast(dg, V((p.x, p.y, z)), V(direction).normalized(), distance=far)
    return (loc - V((p.x, p.y, z))).length if hit else far


def palm(p, coll, name, side='R'):
    """An empty on a people2 hand that cancels the hand's scale (fire, sparks sit on it at true size)."""
    hd = p['hand' + side]
    e = lib.empty(name, (0, 0, 0), coll=coll)
    e.parent = hd
    e.scale = tuple(1.0 / max(1e-6, s) for s in hd.scale)
    return e


# ============================================================================= a01 the night of the gifts
def v_night(shot, fps):
    dur = shot['dur']
    cam, tgt = V(shot['cam']), V(shot['target'])
    p, c = S.city(shot, fps, cam_keys=[(0, cam, tgt), (dur, cam.lerp(tgt, 0.06), tgt + V((0, 0, -25)))])
    coll = lib.collection('Gifts')
    rng = random.Random(1)
    far = cam.lerp(tgt, 0.75)
    near = cam.lerp(tgt, 0.3)
    FX.sparks(coll, (far.x, far.y), 900, 650, 0, 700, 0.0, dur, rng, size=2.6, speed=(160, 240), strength=26, name='GiftFar')
    FX.sparks(coll, (near.x, near.y), 320, 520, 0, 220, 0.0, dur, rng, size=1.4, speed=(120, 180), strength=30, name='GiftNear')
    gift = _ev(shot, 'gift', 1.9)
    MM.set_global('Lit', p['lit'], F(0))
    MM.set_global('Lit', p['lit'], F(gift))
    MM.set_global('Lit', min(0.7, p['lit'] * 2.4), F(gift + 1.2))       # everybody wakes up: windows light up
    return dict(fill=0, exposure=p['exposure'], samples=32)


# ============================================================================= a02 every person on Earth
def golden_wave(r, t0, t1, col='#FFC95A'):
    """A golden band that sweeps over the globe from west to east (object x from -1.1 r to 1.1 r)."""
    m = bpy.data.materials.new('GoldWave')
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    L = nt.links
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    tc = nt.nodes.new('ShaderNodeTexCoord')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    L.new(tc.outputs['Object'], sep.inputs[0])
    val = nt.nodes.new('ShaderNodeValue')
    sub = nt.nodes.new('ShaderNodeMath'); sub.operation = 'SUBTRACT'
    L.new(sep.outputs['X'], sub.inputs[0]); L.new(val.outputs[0], sub.inputs[1])
    ab = nt.nodes.new('ShaderNodeMath'); ab.operation = 'ABSOLUTE'
    L.new(sub.outputs[0], ab.inputs[0])
    mr = nt.nodes.new('ShaderNodeMapRange')
    mr.inputs['From Min'].default_value = 0.0
    mr.inputs['From Max'].default_value = 0.12 * r
    mr.inputs['To Min'].default_value = 1.0
    mr.inputs['To Max'].default_value = 0.0
    L.new(ab.outputs[0], mr.inputs['Value'])
    # behind the band the night side keeps a faint golden glow
    tr = nt.nodes.new('ShaderNodeMath'); tr.operation = 'LESS_THAN'
    L.new(sep.outputs['X'], tr.inputs[0]); L.new(val.outputs[0], tr.inputs[1])
    trail = nt.nodes.new('ShaderNodeMath'); trail.operation = 'MULTIPLY'; trail.inputs[1].default_value = 0.12
    L.new(tr.outputs[0], trail.inputs[0])
    fac = nt.nodes.new('ShaderNodeMath'); fac.operation = 'MAXIMUM'
    L.new(mr.outputs['Result'], fac.inputs[0]); L.new(trail.outputs[0], fac.inputs[1])
    em = nt.nodes.new('ShaderNodeEmission')
    em.inputs['Color'].default_value = lib.C(col)
    em.inputs['Strength'].default_value = 6.0
    trn = nt.nodes.new('ShaderNodeBsdfTransparent')
    mix = nt.nodes.new('ShaderNodeMixShader')
    L.new(fac.outputs[0], mix.inputs['Fac'])
    L.new(trn.outputs[0], mix.inputs[1]); L.new(em.outputs[0], mix.inputs[2])
    L.new(mix.outputs[0], out.inputs['Surface'])
    FX._blend(m)
    shell = lib.sphere(r * 1.004, (0, 0, 0), m, 128, 64, name='GoldShell')
    shell.visible_shadow = False
    s = val.outputs[0]
    for t, v in ((0, -1.15), (t0, -1.15), (t1, 1.15)):
        s.default_value = v * r * 1.004
        s.keyframe_insert('default_value', frame=F(t))
    return shell


def v_earth(shot, fps):
    import pearth  # noqa: F401  (sets spacekit.TEX to the NASA maps on the PC)
    import planet
    import spacekit as sk
    dur = shot['dur']
    one, forever = _ev(shot, 'one', 1.6), _ev(shot, 'forever', 2.3)
    sk.SUN_SOCKETS.clear()
    sk.stars(1.0, 0.8)
    sd = V((0.62, 0.74, 0.25)).normalized()
    e, cl, shells, spin = sk.earth(sd, night=3.0, r=sk.R, seg=(512, 256))
    lamp = sk.sun_light(sd, 4.5)
    lamp.data.use_shadow = False
    planet.facing(spin, 45.0, 32.0, 0.0, 4.0, dur)
    pearth.backlit(e, shells, sd, moon=0.04)
    golden_wave(sk.R, 0.15, one + 0.35)
    # golden glints pop on the night side as the band passes: people getting their powers
    rng = random.Random(2)
    m, s, _ = FX.glow('Glint', '#FFD27A', 9.0)
    base = lib.sphere(0.32, (0, 0, 0), m, 8, 6, name='GlintBase')
    base.hide_render = base.hide_viewport = True
    coll = lib.collection('Glints')
    for i in range(420):
        x, z = rng.uniform(-0.95, 0.95), rng.uniform(-0.9, 0.9)
        if x * x + z * z > 0.9:
            continue
        y = -math.sqrt(max(0.0, 1 - x * x - z * z))
        ob = bpy.data.objects.new(f'Glint{i}', base.data)
        coll.objects.link(ob)
        ob.location = (x * sk.R * 1.003, y * sk.R * 1.003, z * sk.R * 1.003)
        t = 0.15 + (x + 1.15) / 2.3 * (one + 0.2)
        FX.key_scale(ob, [(0, 0.001), (t - 0.02, 0.001), (t + 0.08, 1.6), (t + 0.5, rng.uniform(0.5, 1.0))])
    c = lib.camera((0, -255, 30), (0, 0, 4), 36)
    c.data.clip_end = 5000
    c.data.clip_start = 1.0
    lib.animate_camera(c, [(0, (0, -255, 30)), (forever, (0, -238, 26)), (dur, (0, -226, 22))],
                       [(0, (0, 0, 4)), (dur, (0, 0, 6))])
    lib.bloom(0.35, 1.0, 8)
    return dict(fill=0.0, exposure=0.1, samples=32)


# ============================================================================= a03 8 billion powers (avenue, morning)
def v_crowd(shot, fps):
    dur = shot['dur']
    rng = random.Random(3)
    cam = V(shot['cam'])
    spots = [(d, rng.uniform(-1.4, 1.4)) for d in (3.6, 5.0, 6.4, 7.6, 9.0, 10.5, 12.0, 14.0, 16.5, 19.0, 22.0, 26.0)]
    keep = []
    for d, sd in spots:
        p, f, r = S.ahead(shot, d, sd)
        keep.append(((p.x, p.y), (p.x, p.y), 1.2))
    f0 = S.ahead(shot, 1)[1]
    end = cam + f0 * 2.2
    tgt0 = cam + f0 * 30 + V((0, 0, 2.5))
    p_, c = S.city(shot, fps, keep=keep, cam_keys=[(0, cam + V((0, 0, -0.1)), tgt0), (dur, end, tgt0 + V((0, 0, 1.0)))])
    coll = lib.collection('Crowd')
    order = list(range(len(spots)))
    rng.shuffle(order)
    t_of = {k: 0.25 + i * (dur - 0.9) / len(order) for i, k in enumerate(order)}
    looks = [None, 'girl', 'kid', None, 'sparky', None, 'neighbour', None, None, 'girl', None, None]
    for k, (d, sd) in enumerate(spots):
        p, f, r = S.ahead(shot, d, sd)
        z = S.ground(p.x, p.y)
        towards = rng.random() < 0.5
        hd = S.face(p, p - f) if towards else S.face(p, p + f)
        pp = S.folk((p.x, p.y, z), hd, rng, coll, looks[k], name=f'Cr{k}')
        t = t_of[k]
        col = AURA[k % len(AURA)]
        if k in (1, 6):                          # walk on
            P2.walk(pp, 1.1, rng.random(), 0.9, fps)
            dv = (-f if towards else f) * 1.1 * dur
            lib.move_root(pp, [(p.x, p.y, z), (p.x + dv.x, p.y + dv.y, z)], 0.0, 1.1)
        else:
            P2.stand(pp, rng)
        FX.aura(coll, pp['root'], col, r=0.5, z=0.95, t_on=t, strength=3.5, alpha=0.5, name=f'CrAura{k}', scale=(1, 1, 1.9))
        FX.flash(coll, (p.x, p.y, z + 1.0), t, col=col, size=0.6, energy=600.0, name=f'CrFlash{k}')
        if k == 0:                               # a flame in the palm
            FX.flame(coll, palm(pp, coll, 'CrPalm'), (0, 0, 0.05), t + 0.1, None, scale=0.4, rng=rng, name='CrFlame')
        if k == 3:                               # floats up
            FX.key_loc(pp['root'], [(0, (p.x, p.y, z)), (t, (p.x, p.y, z)), (t + 1.2, (p.x, p.y, z + 0.7))])
        if k == 4:                               # sparks between the hands
            FX.bolt(coll, (p.x - r.x * 0.3, p.y - r.y * 0.3, z + 1.0), (p.x + r.x * 0.3, p.y + r.y * 0.3, z + 1.05),
                    [t + 0.1 + 0.18 * i for i in range(int((dur - t) / 0.18))], rng, width=0.012, strength=30, light=300.0,
                    name='CrBolt')
    return dict(fill=0.35, exposure=p_['exposure'], samples=32)


# ============================================================================= a04 / a05 the window
def _room_shot(shot, fps, mode):
    dur = shot['dur']
    rng = random.Random(4)
    coll = lib.collection('Room')
    out, sun = SS.room(coll, rng, morning=True)
    h = H.load(coll, (0.35, 1.22, 0.0), math.pi)
    fly_t = _ev(shot, 'fly', 0.65)
    # people on the street below
    for k, (x, y, sp) in enumerate(((-14, 4.2, 1.2), (9, 4.8, -1.0), (-3, 23.4, 1.1))):
        pp = S.folk((x, y, -8.85), math.pi / 2 if sp > 0 else -math.pi / 2, rng, out, name=f'Street{k}')
        P2.walk(pp, abs(sp), rng.random(), 0.9, fps)
        lib.move_root(pp, [(x, y, -8.85), (x + sp * dur * 1.2, y, -8.85)], 0.0, abs(sp))
    if mode == 'window':
        H.key_pose(h, 0, H.pose('sill', head=(8, 6, 0)))
        H.key_pose(h, dur, H.pose('sill', head=(-6, 10, 0)))
        cam = lib.camera((-1.3, -1.5, 1.55), (0.5, 4.0, 0.7), 30)
        lib.animate_camera(cam, [(0, (-1.3, -1.5, 1.55)), (dur, (-1.05, -1.15, 1.55))], [(0, (0.5, 4.0, 0.7)), (dur, (0.4, 4.0, 0.6))])
        # the neighbour is already on his way: far up the street, flying off
        nb = S.folk((-30, 12, 6), 0, rng, out, 'neighbour', name='Nb')
        S.fly_pose(nb, 'one')
        S.fly(nb, [(0, (-12, 18, 2.5)), (dur, (-30, 26, 4.0))])
    else:
        # the neighbour drops past the window from above and flies away down the street, his head follows him
        nb = S.folk((0, 0, 0), 0, rng, coll, 'neighbour', name='Nb')
        S.fly_pose(nb, 'one')
        S.fly(nb, [(0, (-5.5, 4.2, 4.5)), (fly_t, (-2.5, 3.6, 2.2)), (fly_t + 0.7, (1.5, 4.4, 0.4)), (dur, (7.0, 7.5, -1.2))],
              tilt=1.25, bob=0.0)
        H.key_pose(h, 0, H.pose('sill', head=(-26, 4, 0)))
        H.key_pose(h, fly_t + 0.2, H.pose('sill', head=(-10, 2, 0)))
        H.key_pose(h, dur, H.pose('sill', head=(22, 12, 0), lean=14.0))
        cam = lib.camera((0.95, 0.15, 1.5), (-0.6, 6.0, 1.2), 34)
        lib.animate_camera(cam, [(0, (0.95, 0.15, 1.5)), (dur, (0.85, 0.35, 1.48))], [(0, (-0.8, 6.0, 1.3)), (dur, (0.8, 6.0, 0.6))])
    cam.data.clip_start = 0.05
    lib.bloom(0.2, 1.2, 6)
    return dict(fill=0.35, exposure=0.35, samples=32)


def v_window(shot, fps):
    return _room_shot(shot, fps, 'window')


def v_flyer(shot, fps):
    return _room_shot(shot, fps, 'flyer')


# ============================================================================= a06 / a07 / a08 the hero's street in Boro
def _home_layout(shot):
    """Fixed spots on the hero's street (same for every scene there): granny, the car, the courier, the door."""
    return dict(granny=S.ahead(shot, 8.0, 0.0)[0], car_d=10.5, courier=S.ahead(shot, 6.5, 0.0)[0], door_d=11.5)


def _home_city(shot, fps, keep_pts, cam_keys):
    keep = [((q.x, q.y), (q.x, q.y), 2.5) for q in keep_pts]
    return S.city(shot, fps, keep=keep, cam_keys=cam_keys)


def _granny_car(shot, fps, mode):
    dur = shot['dur']
    rng = random.Random(6)
    L = _home_layout(shot)
    gp = L['granny']
    pcar = S.ahead(shot, L['car_d'], 0.0)[0]
    f = S.ahead(shot, 1)[1]
    r = V((f.y, -f.x, 0))
    cam0 = V(shot['cam'])
    if mode == 'granny':
        ck = [(0, cam0 + V((0, 0, -0.2)), pcar + V((0, 0, 1.5))), (dur, cam0 + f * 1.2 + V((0, 0, -0.25)), pcar + V((0, 0, 3.0)))]
    else:
        c0 = gp - f * 1.6 + V((0, 0, 0.6))
        ck = [(0, c0, pcar + V((0, 0, 3.4))), (dur, c0 + f * 0.5 + V((0, 0, -0.1)), pcar + V((0, 0, 4.0)))]
    p_, c = _home_city(shot, fps, [gp, pcar], ck)
    side = road_side(shot, 9.0)
    coll = lib.collection('Granny')
    zc = S.ground(pcar.x + r.x * side * 4.2, pcar.y + r.y * side * 4.2)
    car_xy = pcar + r * side * 4.2
    car = lib.car((car_xy.x, car_xy.y, zc), math.atan2(f.y, f.x), color='#8A2E25', coll=coll, lights=False, rng=rng, name='Lada')
    gz = S.ground(gp.x + r.x * side * 0.6, gp.y + r.y * side * 0.6)
    g_xy = gp + r * side * 0.6
    g = S.folk((g_xy.x, g_xy.y, gz), S.face(g_xy, car_xy), rng, coll, 'granny', height=0.82, name='Granny')
    P2.stand(g, rng)
    lift = _ev(shot, 'lift', 0.9)
    if mode == 'granny':
        S.key_people(g, 'upperR', 0, [(0, 0.0), (lift - 0.25, 0.0), (lift + 0.1, -1.25), (dur, -1.3)])
        FX.float_glow(coll, car, lift, dur + 0.8, lift=3.6, col='#B48CFF', spin=0.25, name='CarLift')
        FX.aura(coll, g['root'], '#B48CFF', r=0.5, z=0.9, t_on=lift - 0.2, strength=3.0, alpha=0.45, name='GrAura', scale=(1, 1, 1.8))
    else:
        # continues in the air: rises a bit more, turns slowly, the purple ring stays under it
        car.location.z = zc + 2.8
        FX.float_glow(coll, car, 0.0, dur + 0.5, lift=1.0, col='#B48CFF', spin=0.18, name='CarLift')
        S.key_people(g, 'upperR', 0, [(0, -1.3), (dur, -1.35)])
        FX.aura(coll, g['root'], '#B48CFF', r=0.5, z=0.9, t_on=-1.0, strength=3.0, alpha=0.45, name='GrAura', scale=(1, 1, 1.8))
    return dict(fill=0.35, exposure=p_['exposure'], samples=32)


def v_granny(shot, fps):
    return _granny_car(shot, fps, 'granny')


def v_car(shot, fps):
    return _granny_car(shot, fps, 'car')


def v_courier(shot, fps):
    dur = shot['dur']
    rng = random.Random(8)
    L = _home_layout(shot)
    cp = L['courier']
    f = S.ahead(shot, 1)[1]
    r = V((f.y, -f.x, 0))
    cam0 = V(shot['cam'])
    door0 = S.ahead(shot, L['door_d'], 0.0)[0]
    ck = [(0, cam0 + V((0, 0, -0.25)), door0 + V((0, 0, 1.2))), (dur, cam0 + f * 1.0 + V((0, 0, -0.25)), door0 + V((0, 0, 1.2)))]
    p_, c = _home_city(shot, fps, [cp, door0], ck)
    side = road_side(shot, 9.0)
    coll = lib.collection('Courier')
    wd = wall_dist(door0, -r * side, 1.2, 12.0)
    door_xy = door0 - r * side * max(0.0, wd - 0.75)
    vanish, appear = _ev(shot, 'vanish', 0.55), _ev(shot, 'appear', 2.2)
    cz = S.ground(cp.x, cp.y)
    a = S.folk((cp.x, cp.y, cz), S.face(cp, cp + f), rng, coll, 'courier', name='Cour')
    P2.walk(a, 1.0, 0.0, 0.9, fps)
    lib.move_root(a, [(cp.x, cp.y, cz), (cp.x + f.x * 2, cp.y + f.y * 2, cz)], 0.0, 1.0)
    hide_person(a, vanish + 0.05, visible=False)
    FX.flash(coll, (cp.x + f.x * 0.55, cp.y + f.y * 0.55, cz + 1.0), vanish, col='#9FE0FF', size=1.0, energy=1500, name='CourOut')
    dz = S.ground(door_xy.x, door_xy.y)
    b = S.folk((door_xy.x, door_xy.y, dz), S.face(door_xy, door_xy - r * side), random.Random(8), coll, 'courier', name='Cour2')
    P2.stand(b, rng)
    for o in [b['root']] + list(b['root'].children_recursive):
        FX.key_hide(o, [(0, False), (appear, True)])
    FX.flash(coll, (door_xy.x, door_xy.y, dz + 1.0), appear, col='#9FE0FF', size=1.0, energy=1500, name='CourIn')
    S.key_people(b, 'upperR', 0, [(appear, -0.2), (appear + 0.35, -1.6), (appear + 0.5, -1.4), (appear + 0.65, -1.6),
                                  (appear + 0.8, -1.4)])
    return dict(fill=0.35, exposure=p_['exposure'], samples=32)


# ============================================================================= a09 no traffic jams
def v_empty(shot, fps):
    dur = shot['dur']
    rng = random.Random(9)
    cam, tgt = V(shot['cam']), V(shot['target'])
    p_, c = S.city(shot, fps, cars=False, cam_keys=[(0, cam, tgt), (dur, cam.lerp(tgt, 0.05), tgt)])
    coll = lib.collection('Commute')
    f = (tgt - cam).normalized()
    r = V((f.y, -f.x, 0)).normalized()
    for k in range(14):
        d = rng.uniform(70, 260)
        q = cam + f * d + r * rng.uniform(-0.45, 0.45) * d
        q.z = max(25.0, cam.z - rng.uniform(40, 160))
        pp = S.folk((0, 0, 0), 0, rng, coll, None, name=f'Cm{k}')
        S.fly_pose(pp, rng.choice(['forward', 'one']))
        v = (r * rng.choice((-1, 1)) + f * rng.uniform(-0.3, 0.3)).normalized() * rng.uniform(9, 14)
        S.fly(pp, [(0, tuple(q)), (dur, tuple(q + v * dur))], bob=0.0)
        pp['root'].scale = (2.2, 2.2, 2.2)          # readable at this distance
        FX.aura(coll, pp['root'], AURA[k % len(AURA)], r=0.45, z=0.9, t_on=-1, strength=4.0, alpha=0.4, name=f'CmA{k}',
                scale=(1, 1, 1.9))
    return dict(fill=0, exposure=p_['exposure'], samples=32)


# ============================================================================= a10 half the city flies to work
def v_flyers(shot, fps):
    dur = shot['dur']
    rng = random.Random(10)
    cam, tgt = V(shot['cam']), V(shot['target'])
    p_, c = S.city(shot, fps, cam_keys=[(0, cam, tgt), (dur, cam + V((0, 0, 0.2)), tgt + V((0, 0, 12)))])
    coll = lib.collection('Flyers')
    f = (tgt - cam).normalized()
    fh = V((f.x, f.y, 0)).normalized()
    r = V((fh.y, -fh.x, 0))
    for k in range(24):
        d = rng.uniform(14, 90)
        q = cam + f * d + r * rng.uniform(-0.5, 0.5) * d * 0.6
        q.z = cam.z + max(6.0, f.z * d) + rng.uniform(-4, 6)
        pp = S.folk((0, 0, 0), 0, rng, coll, None, name=f'Fl{k}')
        S.fly_pose(pp, rng.choice(['forward', 'one', 'forward']))
        sgn = 1 if k % 3 else -1
        v = (r * sgn + fh * rng.uniform(-0.4, 0.4)).normalized() * rng.uniform(6, 11)
        a = q - v * dur * 0.5
        S.fly(pp, [(0, tuple(a)), (dur, tuple(a + v * dur))], tilt=rng.uniform(1.25, 1.5), bob=0.1)
        if rng.random() < 0.6:
            FX.aura(coll, pp['root'], AURA[k % len(AURA)], r=0.45, z=0.9, t_on=-1, strength=3.0, alpha=0.35, name=f'FlA{k}',
                    scale=(1, 1, 1.9))
    return dict(fill=0.2, exposure=p_['exposure'], samples=32)


# ============================================================================= a11 100 000 flights a day
def v_planes(shot, fps):
    dur = shot['dur']
    rng = random.Random(11)
    cam, tgt = V(shot['cam']), V(shot['target'])
    up = V((0, 0, 260))
    p_, c = S.city(shot, fps, cam_keys=[(0, cam, tgt + up), (dur, cam, tgt + up + V((60, 0, 30)))])
    coll = lib.collection('Jets')
    f = (tgt - cam).normalized()
    fh = V((f.x, f.y, 0)).normalized()
    r = V((fh.y, -fh.x, 0))
    for k, (d, sd, alt, sp, sgn) in enumerate(((900, -0.15, 380, 75, 1), (1500, 0.2, 560, 80, -1), (2300, -0.3, 700, 85, 1),
                                              (1200, 0.35, 470, 70, 1), (2800, 0.05, 820, 90, -1))):
        q = cam + fh * d + r * sd * d
        q.z = alt
        v = r * sgn * sp
        a = q - v * dur * 0.5
        hd = math.atan2(v.x, -v.y)
        jet = FX.plane_model(coll, tuple(a), heading=hd, livery='#F4F4F2', tail=['#C8282A', '#2B4A9A', '#1F7A5A', '#D98A1E', '#5A2B7A'][k],
                             name=f'Jet{k}')
        jet.rotation_euler.x = 0.04
        FX.key_loc(jet, [(0, tuple(a)), (dur, tuple(a + v * dur))], 'LINEAR')
        # contrail-ish haze behind
        m, s, al = FX.glow(f'Trail{k}', '#FFFFFF', 0.6, alpha=0.25)
        tr = lib.cyl(1.2, 260, (0, 155, 3.6), m, rot=(math.pi / 2, 0, 0), verts=12, r2=6.0, name=f'Trail{k}', coll=coll)
        tr.parent = jet
    return dict(fill=0, exposure=p_['exposure'], samples=32)


# ============================================================================= a12 empty airports
def v_airport(shot, fps):
    dur = shot['dur']
    rng = random.Random(12)
    coll = lib.collection('Airport')
    SS.airport(coll, rng)
    cam = lib.camera((-30, -70, 7.5), (10, 150, 9), 30)
    lib.animate_camera(cam, [(0, (-30, -70, 7.5)), (dur, (-22, -52, 6.8))], [(0, (10, 150, 9)), (dur, (14, 150, 10))])
    cam.data.clip_start = 0.5
    cam.data.clip_end = 8000
    # nobody: only a few birds walk on the empty apron
    import pcommon as pc
    pc.birds(coll, rng, 6, (0, 20, 12), (6, 2, 0), dur, spread=(8, 6, 2), size=0.3)
    lib.bloom(0.2, 1.3, 6)
    return dict(fill=0.25, exposure=0.3, samples=32)


# ============================================================================= a13 / a14 the park: looking for his power
def v_search(shot, fps):
    dur = shot['dur']
    hp = S.ahead(shot, 3.2, 0.0)[0]
    cam0 = V(shot['cam'])
    f = S.ahead(shot, 1)[1]
    c0 = cam0 + V((0, 0, -0.5))
    p_, c = S.city(shot, fps, keep=[((hp.x, hp.y), (hp.x, hp.y), 2.5)],
                   cam_keys=[(0, c0, hp + V((0, 0, 0.95))), (dur, c0 + f * 0.6, hp + V((0, 0, 0.95)))])
    c.data.lens = 40
    coll = lib.collection('Search')
    z = S.ground(hp.x, hp.y)
    h = H.load(coll, (hp.x, hp.y, z), S.face(hp, cam0) + math.radians(28))
    a, b = H.pose('hands_front', head=(0, 26, 0)), H.pose('hands_front', arm=(22, 38), fore=(30, 95), head=(10, 20, 6))
    H.key_pose(h, 0, a)
    H.key_pose(h, dur * 0.45, b)
    H.key_pose(h, dur * 0.8, H.pose('shrug', head=(-8, -4, 6)))
    H.key_pose(h, dur, H.pose('shrug', head=(-10, -6, 8)))
    rng = random.Random(13)
    _sky_flyers(lib.collection('ParkFlyers'), rng, cam0, f, dur, n=5, dmin=40, dmax=120, hmin=18, hmax=50)
    return dict(fill=0.45, exposure=p_['exposure'], samples=32)


def _sky_flyers(coll, rng, cam, f, dur, n=6, dmin=40, dmax=150, hmin=20, hmax=80, scale=1.0, aura=True):
    fh = V((f.x, f.y, 0)).normalized()
    r = V((fh.y, -fh.x, 0))
    out = []
    for k in range(n):
        d = rng.uniform(dmin, dmax)
        q = cam + fh * d + r * rng.uniform(-0.6, 0.6) * d
        q.z = cam.z + rng.uniform(hmin, hmax)
        pp = S.folk((0, 0, 0), 0, rng, coll, None, name=f'Sky{k}_{rng.randint(0, 999)}')
        S.fly_pose(pp, rng.choice(['forward', 'one']))
        v = (r * rng.choice((-1, 1)) + fh * rng.uniform(-0.5, 0.5)).normalized() * rng.uniform(5, 10)
        S.fly(pp, [(0, tuple(q - v * dur * 0.5)), (dur, tuple(q + v * dur * 0.5))], bob=0.1)
        pp['root'].scale = (scale,) * 3
        if aura:
            FX.aura(coll, pp['root'], AURA[k % len(AURA)], r=0.45, z=0.9, t_on=-1, strength=3.5, alpha=0.4,
                    name=f'SkyA{k}_{rng.randint(0, 999)}', scale=(1, 1, 1.9))
        out.append(pp)
    return out


def v_bench(shot, fps):
    dur = shot['dur']
    jump, fall = _ev(shot, 'jump', 1.15), _ev(shot, 'fall', 2.1)
    f = S.ahead(shot, 1)[1]
    r = V((f.y, -f.x, 0))
    j = (r * 0.8 - f * 0.6).normalized()          # he jumps to the right and a bit towards the camera
    bp = S.ahead(shot, 5.5, -0.8)[0]
    cam0 = V(shot['cam'])
    c0 = cam0 + f * 1.2 + V((0, 0, -0.75))
    land = bp + j * 1.9
    p_, c = S.city(shot, fps, keep=[((bp.x, bp.y), (land.x, land.y), 2.5)],
                   cam_keys=[(0, c0, bp + j * 0.5 + V((0, 0, 1.0))), (dur, c0 + r * 0.6, bp + j * 1.2 + V((0, 0, 0.6)))])
    c.data.lens = 30
    coll = lib.collection('Bench')
    z = S.ground(bp.x, bp.y)
    hd = S.face(bp, bp + j)
    SS.bench(coll, (bp.x, bp.y, z), hd)
    r = j
    seat = z + 0.485
    zl = S.ground(land.x, land.y)
    h = H.load(coll, (bp.x, bp.y, seat), hd)
    H.key_root(h, 0, (bp.x, bp.y, seat), hd)
    H.key_pose(h, 0, H.pose('stand', head=(0, -18, 0)))
    H.key_pose(h, jump - 0.6, H.pose('arms_up', head=(0, -25, 0)))
    H.key_pose(h, jump - 0.22, H.pose('crouch', head=(0, -10, 0)))
    H.key_root(h, jump - 0.22, (bp.x, bp.y, seat))
    H.key_pose(h, jump + 0.05, H.pose('superman', thigh=-10.0, shin=-25.0, foot=-30.0))
    apex = bp + r * 0.9
    H.key_root(h, jump + 0.35, (apex.x, apex.y, seat + 0.7))
    H.key_pose(h, fall - 0.12, H.pose('superman', thigh=-12.0, shin=-30.0, foot=-30.0, head=(0, -30, 0)))
    H.key_pose(h, fall, H.pose('flat'))
    H.key_root(h, fall, (land.x, land.y, zl + 0.16))
    rig = h['rig']
    rig.rotation_euler.x = 0.0
    rig.keyframe_insert('rotation_euler', index=0, frame=F(jump + 0.05))
    rig.rotation_euler.x = math.radians(35)
    rig.keyframe_insert('rotation_euler', index=0, frame=F(jump + 0.4))
    rig.rotation_euler.x = math.radians(90)
    rig.keyframe_insert('rotation_euler', index=0, frame=F(fall))
    H.key_pose(h, fall + 0.25, H.pose('flat', arm=(40, 150), fore=(40, 160)))
    H.key_pose(h, dur, H.pose('flat', arm=(40, 150), fore=(40, 160), head=(0, -10, 0)))
    H.key_root(h, dur, (land.x, land.y, zl + 0.16))
    # a little dust where he lands
    FX.smoke(coll, (land.x + r.x * 0.6, land.y + r.y * 0.6, zl), 0.6, fall, fall + 0.6, random.Random(14), col='#B8A98E', r0=0.25,
             n=4, rise=0.9, name='Dust')
    return dict(fill=0.45, exposure=p_['exposure'], samples=32)


# ============================================================================= a15 an hour staring at a mug
def v_mug(shot, fps):
    dur = shot['dur']
    rng = random.Random(15)
    coll = lib.collection('Kitchen')
    mug, hands, sun = SS.kitchen(coll, rng)
    h = H.load(coll, (0.0, 0.98, 0.075), 0.0)
    H.key_pose(h, 0, H.pose('sit_stare', head=(0, 14, 0)))
    H.key_pose(h, dur * 0.5, H.pose('sit_stare', lean=24.0, head=(0, 18, -4)))
    H.key_pose(h, dur, H.pose('sit_stare', lean=27.0, head=(0, 20, 4)))
    for piv, turns in zip(hands, (6.0, 0.5)):
        piv.rotation_euler.x = 0.0
        piv.keyframe_insert('rotation_euler', index=0, frame=F(0))
        piv.rotation_euler.x = -2 * math.pi * turns
        piv.keyframe_insert('rotation_euler', index=0, frame=F(dur))
        lib._set_interp(piv, 'LINEAR')
    cam = lib.camera((0.32, -0.95, 1.02), (0.0, 0.5, 0.95), 42)
    lib.animate_camera(cam, [(0, (0.32, -0.95, 1.02)), (dur, (0.16, -0.55, 0.96))], [(0, (0.0, 0.5, 0.97)), (dur, (0.0, 0.4, 0.92))])
    cam.data.clip_start = 0.03
    lib.bloom(0.2, 1.2, 6)
    return dict(fill=0.35, exposure=0.45, samples=32)


# ============================================================================= a16 / a17 / a18 / a19 the evening street
def _eve(shot):
    f = S.ahead(shot, 1)[1]
    r = V((f.y, -f.x, 0))
    return f, r, V(shot['cam'])


def v_evening(shot, fps):
    dur = shot['dur']
    rng = random.Random(16)
    f, r, cam0 = _eve(shot)
    a, b = S.ahead(shot, 11.0)[0], S.ahead(shot, 6.2)[0]
    over = _ev(shot, 'over', 2.35)
    c0 = cam0 + V((0, 0, -0.45))
    p_, c = S.city(shot, fps, keep=[((a.x, a.y), (b.x, b.y), 2.5)],
                   cam_keys=[(0, c0, a + V((0, 0, 1.6))), (dur, c0 - f * 0.6, b + V((0, 0, 2.2)))])
    c.data.lens = 30
    coll = lib.collection('Evening')
    z = S.ground(a.x, a.y)
    h = H.load(coll, (a.x, a.y, z), S.face(a, b))
    H.walk(h, 0.0, dur, [(a.x, a.y), (b.x, b.y)], speed=(a - b).length / dur * 0.98)
    # the neighbour comes over his head from behind the camera and flies off down the street
    hp = a.lerp(b, over / dur)
    nb = S.folk((0, 0, 0), 0, rng, coll, 'neighbour', name='NbEve')
    S.fly_pose(nb, 'one')
    p0 = cam0 - f * 4.0 + V((0, 0, 4.5))
    p1 = hp + V((0, 0, 3.3))
    p2 = hp + f * 30 + V((0, 0, 7.0))
    t0 = over - (p1 - p0).length / 7.0
    S.fly(nb, [(t0, tuple(p0)), (over, tuple(p1)), (dur + 0.5, tuple(p2))], tilt=1.3, bob=0.05)
    return dict(fill=0.45, exposure=p_['exposure'], samples=32)


def v_crash(shot, fps):
    dur = shot['dur']
    rng = random.Random(17)
    f, r, cam0 = _eve(shot)
    crash = _ev(shot, 'crash', 0.6)
    hp = S.ahead(shot, 4.2)[0]
    bush_c = S.ahead(shot, 12.5)[0]
    c0 = cam0 + V((0, 0, -0.3))
    p_, c = S.city(shot, fps, keep=[((hp.x, hp.y), (bush_c.x, bush_c.y), 3.0)],
                   cam_keys=[(0, c0, bush_c + V((0, 0, 1.2))), (dur, c0 + f * 0.4, bush_c + V((0, 0, 0.9)))])
    c.data.lens = 34
    coll = lib.collection('Crash')
    side = road_side(shot, 10.0)
    wd = wall_dist(bush_c, -r * side, 1.0, 10.0)
    off = min(wd - 1.0, 2.6)
    q = bush_c - r * side * off
    z = S.ground(q.x, q.y)
    SS.hedge(coll, rng, (q.x - f.x * 3.5, q.y - f.y * 3.5, z), (q.x + f.x * 3.5, q.y + f.y * 3.5, z), h=1.0)
    z0 = S.ground(hp.x, hp.y)
    h = H.load(coll, (hp.x, hp.y, z0), S.face(hp, hp + f))
    H.key_pose(h, 0, H.pose('stand', head=(0, -22, 0)))
    H.key_pose(h, crash - 0.1, H.pose('stand', head=(0, -10, 0)))
    H.key_pose(h, crash + 0.2, H.pose('shrug', head=(0, 5, 0)))
    H.key_pose(h, dur, H.pose('shrug', arm=(30, 20), head=(0, 8, 0)))
    nb = S.folk((0, 0, 0), 0, rng, coll, 'neighbour', name='NbCrash')
    S.fly_pose(nb, 'forward')
    root = nb['root']
    hd = S.face(q, q + f)
    for t, loc, tilt in ((0, q - f * 3 + V((0, 0, z + 6.0)), 1.4), (crash - 0.25, q - f * 0.8 + V((0, 0, z + 3.2)), 2.0),
                         (crash, q + V((0, 0, z + 1.0)), 2.6), (crash + 0.25, q + V((0, 0, z + 0.55)), 2.9),
                         (dur, q + V((0, 0, z + 0.5)), 2.95)):
        root.location = loc
        root.rotation_euler = (tilt, 0, hd)
        root.keyframe_insert('location', frame=F(t))
        root.keyframe_insert('rotation_euler', frame=F(t))
    S.key_people(nb, 'thighL', 0, [(crash + 0.3, 0.1), (crash + 0.6, 0.6), (crash + 0.9, 0.1), (dur, 0.5)])
    SS.leaves_burst(coll, (q.x, q.y, z + 1.0), crash, rng)
    return dict(fill=0.45, exposure=p_['exposure'], samples=32)


def v_realize(shot, fps):
    dur = shot['dur']
    rng = random.Random(18)
    f, r, cam0 = _eve(shot)
    wave, others = _ev(shot, 'wave', 3.4), _ev(shot, 'others', 2.3)
    hp = S.ahead(shot, 3.4)[0]
    gp = S.ahead(shot, 6.4, 1.3)[0]
    bp = S.ahead(shot, 7.2, -1.4)[0]
    c0 = cam0 + V((0, 0, -0.4))
    p_, c = S.city(shot, fps, keep=[((hp.x, hp.y), (bp.x, bp.y), 3.0), ((gp.x, gp.y), (gp.x, gp.y), 1.5)],
                   cam_keys=[(0, c0, hp + V((0, 0, 1.0))), (dur, c0 + f * 0.9, hp + V((0, 0, 1.05)))])
    c.data.lens = 52
    coll = lib.collection('Realize')
    z = S.ground(hp.x, hp.y)
    h = H.load(coll, (hp.x, hp.y, z), S.face(hp, cam0) + math.radians(18))
    H.key_pose(h, 0, H.pose('hands_front', head=(0, 24, 0)))
    H.key_pose(h, others - 0.4, H.pose('hands_front', head=(0, 20, 0)))
    H.key_pose(h, others, H.pose('stand', head=(-30, 0, 0)))
    H.key_pose(h, wave - 0.2, H.pose('stand', head=(-26, -2, 0)))
    H.key_pose(h, wave + 0.6, H.pose('shrug', head=(0, -4, 6)))
    H.key_pose(h, dur, H.pose('shrug', head=(4, -6, 8)))
    # a girl with a flame on her palm, a guy floating above the pavement: both lose it in the wave
    zg = S.ground(gp.x, gp.y)
    g = S.folk((gp.x, gp.y, zg), S.face(gp, hp), rng, coll, 'girl', name='GirlF')
    P2.stand(g, rng)
    S.key_people(g, 'upperR', 0, [(0, -1.1), (wave + 0.4, -1.1), (wave + 0.8, -0.2)])
    S.key_people(g, 'foreR', 0, [(0, -0.6), (wave + 0.4, -0.6), (wave + 0.8, -0.2)])
    FX.flame(coll, palm(g, coll, 'GirlPalm'), (0, 0, 0.05), -1.0, wave + 0.2, scale=0.45, rng=rng, name='GirlFlame')
    zb = S.ground(bp.x, bp.y)
    b = S.folk((bp.x, bp.y, zb + 0.8), S.face(bp, hp), rng, coll, 'sparky', name='FloatGuy')
    P2.stand(b, rng)
    FX.key_loc(b['root'], [(0, (bp.x, bp.y, zb + 0.75)), (wave + 0.25, (bp.x, bp.y, zb + 0.82)), (wave + 0.5, (bp.x, bp.y, zb))])
    lib.add_sine(b['root'], 'location', 2, 0.04, 1.4)
    FX.aura(coll, b['root'], '#7FD8FF', r=0.5, z=0.9, t_on=-1.0, t_off=wave + 0.2, strength=3.5, alpha=0.5, name='FgAura',
            scale=(1, 1, 1.9))
    FX.aura(coll, g['root'], '#FF9C5B', r=0.5, z=0.9, t_on=-1.0, t_off=wave + 0.2, strength=3.0, alpha=0.4, name='GfAura',
            scale=(1, 1, 1.9))
    FX.ripple(coll, (hp.x, hp.y, z + 0.05), wave, 1.1, 10.0)
    return dict(fill=0.45, exposure=p_['exposure'], samples=32)


def v_ordinary(shot, fps):
    dur = shot['dur']
    rng = random.Random(19)
    f, r, cam0 = _eve(shot)
    one = _ev(shot, 'one', 2.3)
    hp = S.ahead(shot, 5.0)[0]
    c0 = hp - f * 3.2 + r * 0.6 + V((0, 0, 1.5))
    c1 = hp - f * 26 + r * 6 + V((0, 0, 85))
    p_, c = S.city(shot, fps, keep=[((hp.x, hp.y), (hp.x, hp.y), 3.0)],
                   cam_keys=[(0, c0, hp + V((0, 0, 1.0))), (one, c0.lerp(c1, 0.35), hp + V((0, 0, 0.5))), (dur, c1, hp)])
    c.data.lens = 30
    coll = lib.collection('Ordinary')
    z = S.ground(hp.x, hp.y)
    h = H.load(coll, (hp.x, hp.y, z), S.face(hp, c0))
    H.key_pose(h, 0, H.pose('stand', head=(0, -30, 0)))
    H.key_pose(h, dur, H.pose('stand', head=(10, -38, 0)))
    # around and above him: people with powers, glowing in the dusk
    _sky_flyers(coll, rng, hp - f * 10, f, dur, n=22, dmin=-10, dmax=70, hmin=6, hmax=70)
    for k in range(10):
        q = hp + f * rng.uniform(-12, 18) + r * rng.uniform(-6, 6)
        if (q - hp).length < 3:
            continue
        zq = S.ground(q.x, q.y)
        pp = S.folk((q.x, q.y, zq), rng.uniform(0, 6.28), rng, coll, None, name=f'Ord{k}')
        P2.stand(pp, rng)
        FX.aura(coll, pp['root'], AURA[k % len(AURA)], r=0.5, z=0.9, t_on=-1, strength=3.5, alpha=0.45, name=f'OrdA{k}', scale=(1, 1, 1.9))
    # one ordinary man: a plain white ring around him lights up
    m, s, a = FX.glow('PlainRing', '#FFFFFF', 3.0, alpha=0.8)
    bpy.ops.mesh.primitive_torus_add(major_radius=1.1, minor_radius=0.03, major_segments=64, minor_segments=8, location=(hp.x, hp.y, z + 0.04))
    ring = bpy.context.active_object
    for cc in ring.users_collection:
        cc.objects.unlink(ring)
    coll.objects.link(ring)
    ring.data.materials.append(m)
    FX.key(a, [(0, 0.0), (one - 0.1, 0.0), (one + 0.3, 0.85), (dur, 0.85)])
    return dict(fill=0.35, exposure=p_['exposure'], samples=32)


# ============================================================================= a20 the knock (under the profile card)
def v_knock(shot, fps):
    out = PR.v_knock(shot, 'knock')
    coll = lib.collection('Hall')
    h = H.load(coll, (-0.3, -1.45, 0.0), math.pi + 0.15)
    kn = _ev(shot, 'knock', 1.55)
    H.key_pose(h, 0, H.pose('stand', head=(0, 6, 0)))
    H.key_pose(h, kn, H.pose('stand', head=(0, 4, 0)))
    H.key_pose(h, kn + 0.35, H.pose('shrug', head=(-8, -4, 0)))
    H.key_pose(h, shot['dur'], H.pose('shrug', head=(-6, -6, 0)))
    out['fill'] = 0.3
    return out
