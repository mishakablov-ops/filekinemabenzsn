"""Part 2 of «Каждому по способности»: they come for the hero, the world breaks, the weather man's hurricane,
the walk into the storm, the queue at his door. One function per scene (variant).
"""
import math
import random

import bpy
from mathutils import Vector as V

import lib
import metro_build as MB
import metro_mats as MM
import people2 as P2
import prooms as PR
import sila as S
import sila_fx as FX
import sila_hero as H
import sila_sets as SS
from sila_p1 import _ev, _sky_flyers, road_side

F = lib.sec2f
STORM_C = '#6A727C'


# ============================================================================= b01 / b02 they came for me
def _hall(shot, fps, mode):
    dur = shot['dur']
    rng = random.Random(21)
    coll = lib.collection('Hall')
    land_s = PR.hallway(coll, rng, door_open=0.0, outside=22.0)
    hinge, torch = bpy.data.objects['DoorHinge'], bpy.data.objects['Torch']
    torch.data.color = lib.C('#E4ECFF')[:3]
    yb = 1.0
    agents = []
    for k, (x, y) in enumerate(((0.12, yb + 1.25), (0.62, yb + 1.75))):
        a = S.folk((x, y, 0.0), 0.0, rng, coll, 'agent', height=0.95, name=f'Agent{k}')
        P2.stand(a, rng)
        agents.append(a)
    h = H.load(coll, (0.05, -0.35, 0.0), math.pi)
    if mode == 'door':
        op = _ev(shot, 'open', 0.5)
        for t, v in ((0, 0.0), (op, 0.0), (op + 0.55, 1.45), (dur, 1.55)):
            P2._key(hinge, 'rotation_euler', 2, F(t), v)
        pc_key = [(0, 22 * 8), (op, 22 * 8), (op + 0.4, 22 * 22)]
        for t, e in pc_key:
            torch.data.energy = e
            torch.data.keyframe_insert('energy', frame=F(t))
        H.key_pose(h, 0, H.pose('stand', arm=((26, 30), (24, 4)), fore=((20, 60), (18, 16)), head=(0, -4, 0)))
        H.key_pose(h, op + 0.1, H.pose('stand', head=(0, -6, 0)))
        H.key_pose(h, op + 0.6, H.pose('stand', lean=-6.0, head=(0, -8, 0)))
        cam = lib.camera((0.4, -2.45, 1.4), (0.05, 2.0, 1.25), 34)
        lib.animate_camera(cam, [(0, (0.4, -2.45, 1.4)), (dur, (0.32, -2.0, 1.38))], [(0, (0.05, 2.0, 1.25)), (dur, (0.1, 2.0, 1.3))])
    else:
        need = _ev(shot, 'need', 1.4)
        P2._key(hinge, 'rotation_euler', 2, F(0), 1.55)
        torch.data.energy = 22 * 22
        a = agents[0]
        S.key_people(a, 'upperR', 0, [(0, 0.0), (need - 0.3, 0.0), (need + 0.05, -1.45), (dur, -1.4)])
        S.key_people(a, 'foreR', 0, [(0, -0.3), (need - 0.3, -0.3), (need + 0.05, -0.05)])
        S.key_people(a, 'head', 0, [(0, 0.0), (need, 0.12)])
        H.key_pose(h, 0, H.pose('stand', lean=-6.0, head=(0, -10, 0)))
        H.key_pose(h, dur, H.pose('stand', lean=-8.0, head=(4, -12, 0)))
        cam = lib.camera((0.62, -1.55, 1.3), (0.2, 2.3, 1.4), 36)
        lib.animate_camera(cam, [(0, (0.62, -1.55, 1.3)), (dur, (0.58, -1.25, 1.3))], [(0, (0.2, 2.3, 1.4)), (dur, (0.18, 2.3, 1.45))])
    cam.data.clip_start = 0.03
    lib.bloom(0.35, 0.9, 8)
    return dict(fill=0.3, fill_col='#E9EEFF', exposure=0.7, samples=32)


def v_door(shot, fps):
    return _hall(shot, fps, 'door')


def v_agents(shot, fps):
    return _hall(shot, fps, 'agents')


# ============================================================================= b03 the world broke in a week
def v_broken(shot, fps):
    dur = shot['dur']
    rng = random.Random(23)
    cam, tgt = V(shot['cam']), V(shot['target'])
    p_, c = S.city(shot, fps, cam_keys=[(0, cam, tgt), (dur, cam.lerp(tgt, 0.05) + V((20, 0, 0)), tgt)])
    coll = lib.collection('Chaos')
    f = (tgt - cam)
    f.z = 0
    f.normalize()
    r = V((f.y, -f.x, 0))
    for k in range(7):
        q = tgt + f * rng.uniform(-250, 450) + r * rng.uniform(-500, 500)
        z = S.ground(q.x, q.y)
        FX.smoke(coll, (q.x, q.y, z + 5), rng.uniform(160, 260), -3.0, dur + 1.0, rng, col=rng.choice(['#3E3B39', '#55504B', '#2E2C2B']),
                 r0=rng.uniform(10, 18), n=10, rise=rng.uniform(25, 40), name=f'Smoke{k}')
        m, s, _ = FX.glow(f'Fire{k}', '#FF7A1A', 25.0)
        lib.sphere(rng.uniform(6, 10), (q.x, q.y, z + 3), m, 12, 8, scale=(1.4, 1.4, 0.6), name=f'Fire{k}', coll=coll)
        L = lib.light('POINT', (q.x, q.y, z + 12), energy=4e5, color='#FF8A30', size=8, name=f'FireL{k}')
        FX.key(s, [(i * 0.13, rng.uniform(18, 32)) for i in range(int(dur / 0.13) + 2)])
    # somebody throws a car through the air, somebody else fires lightning at a roof
    car = lib.car((0, 0, 0), 0.0, color='#2F3B45', coll=coll, lights=False, rng=rng, name='ThrownCar')
    a = tgt + r * 120 + V((0, 0, 60))
    b = tgt + r * 260 + f * 80 + V((0, 0, 20))
    FX.key_loc(car, [(0, tuple(a)), (dur, tuple(b))])
    car.scale = (3, 3, 3)
    lib.add_sine(car, 'rotation_euler', 0, 2.0, 1.6)
    lib.add_sine(car, 'rotation_euler', 1, 1.2, 2.1)
    q = tgt - r * 180 + f * 120
    FX.bolt(coll, (q.x, q.y, 240), (q.x + 20, q.y, S.ground(q.x, q.y) + 30), [0.3, 0.55, 1.2, 1.6], rng, width=1.2, strength=40,
            light=2e7, name='ChaosBolt')
    return dict(fill=0, exposure=p_['exposure'], samples=32)


# ============================================================================= b04 the invisible men clean out the shops
def v_shop(shot, fps):
    dur = shot['dur']
    rng = random.Random(24)
    coll = lib.collection('Shop')
    lib.world_color('#DADCDF', 0.6)
    floor = lib.mat('ShopFloor', '#D6D2C8', rough=0.22, var=0.05, var_scale=1, spec=0.6)
    PR.shell(coll, 9.0, 26.0, 3.8, wall='#E6E3DC', floor=floor, y0=-3.0, name='Sh')
    for sx in (-1, 1):
        PR.shelf_unit(sx * 1.3, sx * 2.3, 0.0, 20.0, -sx, coll, rng)
    strip, _ = lib.emission_mat('Tube', '#F4F7FF', 8.0)
    for x in (-2.95, 0.0, 2.95):
        for y in range(0, 22, 4):
            lib.box((0.22, 3.4, 0.05), (x, y + 1.8, 3.65), strip, bevel=0, name='Tube', coll=coll)
    for y in (2.0, 8.0, 14.0):
        lib.light('AREA', (0, y, 3.5), (0, 0, 0), energy=520, color='#F2F5FF', size=2.6, name='CeilL', coll=coll)
    # two shopping bags float down the aisle at hand height: nobody carries them
    bag_m = lib.mat('BagPlastic', '#F1F0EA', rough=0.6)
    bags = []
    for k, (x, y0) in enumerate(((-0.45, 5.6), (0.5, 7.4))):
        b = lib.box((0.36, 0.2, 0.42), (x, y0, 0.55), bag_m, bevel=0.05, name=f'Bag{k}', coll=coll, origin='bottom')
        hd = lib.curve_poly(f'BagHandle{k}', [[(-0.12, 0, 0.42), (-0.1, 0, 0.6), (0.1, 0, 0.6), (0.12, 0, 0.42)]], bevel=0.008,
                            mat_=bag_m, coll=coll)
        hd.parent = b
        v = 1.25
        FX.key_loc(b, [(0, (x, y0, 0.55)), (dur, (x, y0 - v * dur, 0.55))], 'LINEAR')
        lib.add_sine(b, 'location', 2, 0.03, 0.55, k * 1.3)
        lib.add_sine(b, 'rotation_euler', 1, 0.12, 0.55, k * 1.3 + 0.4)
        bags.append((b, x, y0, v))
    # goods jump off the shelves into the bags
    pm = [lib.mat('Good' + c, c, rough=0.45) for c in ('#C8282A', '#2F6FB0', '#E8B92E', '#3E8A4A', '#F0EDE4', '#7A3E8A')]
    for i in range(34):
        b, x, y0, v = bags[i % 2]
        sx = -1 if x < 0 else 1
        t0 = rng.uniform(0.0, dur - 0.5)
        yb = y0 - v * (t0 + 0.45)
        src = V((sx * 1.4, yb + rng.uniform(-1.0, 2.0), rng.choice((0.6, 1.0, 1.4, 1.8))))
        dst = V((x, yb, 0.85))
        g = lib.box((0.14, rng.uniform(0.08, 0.16), rng.uniform(0.14, 0.24)), tuple(src), rng.choice(pm), bevel=0.01, name=f'Good{i}',
                    coll=coll)
        mid = src.lerp(dst, 0.5) + V((0, 0, 0.35))
        FX.key_loc(g, [(0, tuple(src)), (t0, tuple(src)), (t0 + 0.22, tuple(mid)), (t0 + 0.45, tuple(dst))])
        FX.key_scale(g, [(0, 1.0), (t0 + 0.3, 1.0), (t0 + 0.45, 0.01)])
        lib.add_sine(g, 'rotation_euler', 2, 1.0, 0.7, i)
    cam = lib.camera((0.25, 0.4, 0.95), (0.0, 9.0, 0.8), 32)
    lib.animate_camera(cam, [(0, (0.25, 0.4, 0.95)), (dur, (0.15, 0.7, 0.92))], [(0, (0.0, 9.0, 0.8)), (dur, (0.0, 8.0, 0.75))])
    cam.data.clip_start = 0.05
    return dict(fill=0.4, exposure=0.15, samples=32)


# ============================================================================= b05 the lightning guy cuts the district off
def v_sparky(shot, fps):
    dur = shot['dur']
    rng = random.Random(25)
    zap, out = _ev(shot, 'zap', 0.5), _ev(shot, 'out', 1.8)
    gp = S.ahead(shot, 9.0, 0.0)[0]
    f = S.ahead(shot, 1)[1]
    r = V((f.y, -f.x, 0))
    cam0 = V(shot['cam'])
    c0 = cam0 + V((0, 0, -0.35))
    p_, c = S.city(shot, fps, keep=[((gp.x, gp.y), (gp.x, gp.y), 3.0)],
                   cam_keys=[(0, c0, gp + V((0, 0, 3.0))), (dur, c0 + f * 1.0, gp + V((0, 0, 3.6)))])
    c.data.lens = 28
    coll = lib.collection('Sparky')
    side = road_side(shot, 9.0)
    z = S.ground(gp.x, gp.y)
    g = S.folk((gp.x, gp.y, z), S.face(gp, gp + r * side), rng, coll, 'sparky', name='Sparky')
    P2.stand(g, rng)
    for sd in ('L', 'R'):
        S.key_people(g, 'upper' + sd, 0, [(0, -0.3), (zap - 0.3, -0.3), (zap, -2.5), (dur, -2.6)])
    FX.aura(coll, g['root'], '#9FD0FF', r=0.55, z=0.95, t_on=zap - 0.2, strength=5.0, alpha=0.55, name='SpAura', scale=(1, 1, 1.9))
    top = gp + r * side * 4.5 + f * 2.0
    hit = V((top.x, top.y, z + 8.5))
    times = [zap + 0.08 * i + rng.uniform(0, 0.04) for i in range(int((out + 0.35 - zap) / 0.08))]
    FX.bolt(coll, (gp.x, gp.y, z + 1.9), tuple(hit), times, rng, width=0.05, strength=60, light=9000.0, name='SpBolt', seeds=4)
    FX.flash(coll, tuple(hit), out, col='#CFE6FF', size=2.5, energy=60000, name='Transformer')
    # the whole district goes dark at «света»
    for k, v in (('Lit', p_['lit']), ('Street', p_['street']), ('Neon', p_['neon'])):
        MM.set_global(k, v, F(0))
        MM.set_global(k, v, F(out - 0.02))
        MM.set_global(k, 0.0, F(out + 0.08))
    for o in bpy.data.objects:
        if o.type == 'LIGHT' and o.name.startswith('MetroStreetLight'):
            e = o.data.energy
            for t, v in ((0, e), (out - 0.02, e), (out + 0.06, 0.0)):
                o.data.energy = v
                o.data.keyframe_insert('energy', frame=F(t))
    return dict(fill=0.15, exposure=p_['exposure'], samples=32)


# ============================================================================= b06 300 million volts
def v_volts(shot, fps):
    dur = shot['dur']
    rng = random.Random(26)
    st = _ev(shot, 'strike', 0.3)
    cam, tgt = V(shot['cam']), V(shot['target'])
    lm = MB.get_plan()['landmarks']['needle']
    top = V((lm['at'][0], lm['at'][1], lm['h']))
    look = top * 0.55 + tgt * 0.45
    look.z = top.z * 0.7
    shake = [(0, cam, look), (st, cam, look), (st + 0.05, cam + V((1.2, 0, 0.6)), look), (st + 0.12, cam + V((-0.8, 0, -0.4)), look),
             (st + 0.25, cam, look), (dur, cam + (look - cam).normalized() * 25, look)]
    p_, c = S.city(shot, fps, cam_keys=shot.get('cam_keys') or shake)
    coll = lib.collection('Volts')
    FX.cloud_deck(coll, (top.x, top.y + 300, top.z + 650), 2600, rng, n=80, col='#1E2228', alpha=0.95, name='NightDeck', spin=0.01)
    FX.bolt(coll, (top.x + 180, top.y + 250, top.z + 640), tuple(top + V((0, 0, 2))), [st, st + 0.32, st + 1.0, st + 1.9],
            rng, width=2.2, strength=70, light=6e7, name='Strike', seeds=3)
    FX.flash(coll, tuple(top), st, col='#DCEBFF', size=18.0, energy=2e7, name='Spire')
    return dict(fill=0, exposure=p_['exposure'], samples=32)


# ============================================================================= b07 the weather man
def _storm_master(coll, center, rng, z_top, z_bot, r_top, r_bot, rings=10, per=30, period=7.0, name='Storm'):
    piv = FX.vortex(coll, center, z_top, z_bot, r_top, r_bot, rng, rings=rings, per=per, period=period, col=STORM_C, name=name)
    m = lib.empty(name + 'Master', (center[0], center[1], 0), coll=coll)
    for p in piv:
        mw = p.matrix_world.copy()
        p.parent = m
        p.location = (p.location.x - center[0], p.location.y - center[1], p.location.z)
    return m


def v_stormman(shot, fps):
    dur = shot['dur']
    rng = random.Random(27)
    raise_t = _ev(shot, 'raise', 1.9)
    mp = S.ahead(shot, 4.5, 0.6)[0]
    cam0, tgt = V(shot['cam']), V(shot['target'])
    f = S.ahead(shot, 1)[1]
    c0 = cam0 + V((0, 0, -0.6))
    p_, c = S.city(shot, fps, cam_keys=[(0, c0, tgt), (dur, c0 - f * 0.8 + V((0, 0, 0.2)), tgt + V((0, 0, 60)))])
    coll = lib.collection('Weather')
    z = S.ground(mp.x, mp.y, z0=cam0.z + 5)
    g = S.folk((mp.x, mp.y, z), S.face(mp, tgt), rng, coll, 'storm', height=1.0, name='Weather')
    P2.stand(g, rng)
    for sd, sgn in (('L', 1), ('R', -1)):
        S.key_people(g, 'upper' + sd, 0, [(0, -0.2), (raise_t - 0.4, -0.3), (raise_t + 0.2, -2.7), (dur, -2.8)])
        S.key_people(g, 'upper' + sd, 1, [(0, sgn * 0.1), (raise_t + 0.2, sgn * 0.45)])
    FX.aura(coll, g['root'], '#B9D4FF', r=0.6, z=0.95, t_on=raise_t - 0.3, strength=4.0, alpha=0.5, name='WxAura', scale=(1, 1, 1.9))
    m = _storm_master(coll, (tgt.x, tgt.y), rng, 900, 120, 700, 90, rings=9, per=26, period=6.0, name='Twister')
    FX.key_scale(m, [(0, 0.25), (raise_t, 0.35), (dur, 1.0)])
    FX.cloud_deck(coll, (tgt.x, tgt.y, 1000), 2400, rng, n=70, col='#5A616A', alpha=0.9, name='WxDeck', spin=0.06)
    FX.rain(coll, mp.x - 18, mp.x + 18, mp.y - 18, mp.y + 18, z + 14, 900, rng, speed=16, slant=(4.0, 2.0), dur=dur,
            col='#C9D6E2', name='WxRain')
    return dict(fill=0.25, exposure=p_['exposure'], samples=32)


# ============================================================================= b08 the hurricane over the city
def v_hurricane(shot, fps):
    dur = shot['dur']
    rng = random.Random(28)
    cam, tgt = V(shot['cam']), V(shot['target'])
    p_, c = S.city(shot, fps, cam_keys=[(0, cam, tgt + V((0, 0, 300))), (dur, cam.lerp(tgt, 0.06), tgt + V((0, 0, 330)))])
    coll = lib.collection('Hurricane')
    _storm_master(coll, (tgt.x, tgt.y), rng, 1600, 0, 1500, 110, rings=12, per=34, period=5.0, name='Huracan')
    FX.cloud_deck(coll, (tgt.x, tgt.y, 1650), 4200, rng, n=110, col='#59606A', alpha=0.95, name='HDeck', spin=0.05)
    m, s, a = FX.glow('RainShaft', '#8E959C', 0.4, alpha=0.3)
    lib.cyl(700, 1600, (tgt.x, tgt.y, 0), m, verts=48, r2=1200, name='RainShaft', coll=coll, origin='bottom', cap=False)
    for k in range(10):
        a_ = rng.uniform(0, 6.28)
        rr = rng.uniform(140, 320)
        ob = lib.box((5, 2.2, 1.6), (tgt.x + rr * math.cos(a_), tgt.y + rr * math.sin(a_), rng.uniform(40, 260)),
                     lib.mat('Debris', rng.choice(['#8A2E25', '#2F3B45', '#C9C1B2']), rough=0.5), bevel=0.2, name=f'Swirl{k}', coll=coll)
        piv = lib.empty(f'SwirlPiv{k}', (tgt.x, tgt.y, 0), coll=coll)
        ob.location = (ob.location.x - tgt.x, ob.location.y - tgt.y, ob.location.z)
        ob.parent = piv
        piv.rotation_euler.z = 0
        piv.keyframe_insert('rotation_euler', index=2, frame=F(0))
        piv.rotation_euler.z = 2.2 * dur / 3.0
        piv.keyframe_insert('rotation_euler', index=2, frame=F(dur))
        lib._set_interp(piv, 'LINEAR')
        lib.add_sine(ob, 'rotation_euler', 0, 2.0, 1.1, k)
    for k in range(4):
        q = V((tgt.x + rng.uniform(-900, 900), tgt.y + rng.uniform(-900, 900), 0))
        FX.bolt(coll, (q.x, q.y, 1500), (q.x + 60, q.y, rng.uniform(700, 1000)), [rng.uniform(0.2, dur - 0.3)], rng, width=3.0,
                strength=50, light=3e7, name=f'CloudBolt{k}')
    return dict(fill=0, exposure=p_['exposure'], samples=32)


# ============================================================================= b09 250 km/h: wind in the street
def _debris(coll, rng, origin, f, r, dur, n=14, speed=(14, 26)):
    mats = [lib.mat('Junk' + c, c, rough=0.6) for c in ('#C9B79A', '#E9E7E1', '#2F3B45', '#8A2E25', '#D9A23A', '#3E8A4A')]
    for k in range(n):
        kind = k % 4
        if kind == 0:
            ob = lib.box((0.5, 0.4, 0.35), (0, 0, 0), mats[0], bevel=0.02, name=f'Box{k}', coll=coll)
        elif kind == 1:
            ob = lib.box((0.3, 0.42, 0.003), (0, 0, 0), mats[1], bevel=0, name=f'Paper{k}', coll=coll)
        elif kind == 2:
            ob = lib.cyl(0.5, 0.35, (0, 0, 0), mats[rng.randint(2, 5)], verts=12, r2=0.02, name=f'Umbrella{k}', coll=coll)
        else:
            ob = lib.cyl(0.28, 0.05, (0, 0, 0), mats[2], verts=16, name=f'Lid{k}', coll=coll)
        d = rng.uniform(4, 22)
        h = rng.uniform(0.4, 6)
        sp = rng.uniform(*speed)
        t0 = rng.uniform(-1.0, dur - 0.3)
        p0 = origin + f * d - r * 18 + V((0, 0, h))
        p1 = p0 + r * sp * 2.5 + V((0, 0, rng.uniform(-1.5, 2.5)))
        FX.key_loc(ob, [(t0, tuple(p0)), (t0 + 2.5, tuple(p1))], 'LINEAR')
        for i in range(3):
            lib.add_sine(ob, 'rotation_euler', i, rng.uniform(2, 5), rng.uniform(0.4, 0.9), rng.uniform(0, 6))


def v_wind(shot, fps):
    dur = shot['dur']
    rng = random.Random(29)
    cam0, tgt = V(shot['cam']), V(shot['target'])
    f = S.ahead(shot, 1)[1]
    r = V((f.y, -f.x, 0))
    c0 = cam0 + V((0, 0, -0.3))
    p_, c = S.city(shot, fps, cam_keys=[(0, c0, tgt), (dur, c0 + f * 0.8, tgt)])
    for i, amp in ((0, 0.012), (1, 0.01), (2, 0.008)):
        lib.add_sine(c, 'rotation_euler', i, amp, 0.23 + 0.05 * i, i)
    coll = lib.collection('Wind')
    mid = cam0 + f * 12
    FX.rain(coll, mid.x - 16, mid.x + 16, mid.y - 16, mid.y + 16, 16, 2600, rng, speed=20, slant=(r.x * 14 + f.x * 3, r.y * 14 + f.y * 3),
            dur=dur, col='#D0DAE4', name='WindRain')
    _debris(coll, rng, cam0, f, r, dur)
    return dict(fill=0.2, exposure=p_['exposure'], samples=32)


# ============================================================================= b10 the eye from above
def v_eye(shot, fps):
    dur = shot['dur']
    rng = random.Random(30)
    tgt = V(shot['target'])
    ctr = V((tgt.x, tgt.y, 0))
    c0 = ctr + V((-200, -900, 3400))
    c1 = ctr + V((-120, -500, 2900))
    p_, c = S.city(shot, fps, cam=tuple(c0), target=tuple(ctr), lens=30, cam_keys=[(0, c0, ctr), (dur, c1, ctr)])
    c.data.clip_end = 30000
    coll = lib.collection('Eye')
    # the storm from above: three flat discs of spiral cloud bands at different heights, turning at different speeds,
    # the city shows through the clear eye in the middle
    for k, (z, r_eye, r_max, al, sp, col, dk) in enumerate(((1250, 330, 5200, 0.9, 0.30, '#AEB4BA', '#4F565E'),
                                                            (1550, 280, 6200, 1.0, 0.22, '#EEF0F2', '#8F969E'),
                                                            (1850, 420, 6800, 0.45, 0.16, '#F6F7F8', '#B5BBC1'))):
        m = FX.spiral_cloud_mat(f'EyeMat{k}', r_eye, r_max, arms=2 + (k == 1), twist=1.6 + 0.15 * k, col=col, dark=dk,
                                alpha=al, seed=k * 0.37)
        lib.plane((r_max * 2.1, r_max * 2.1), (ctr.x, ctr.y, z), m, name=f'EyeDisc{k}', coll=coll)
        FX.key(m.node_tree.nodes['Spin'].outputs[0], [(0, 0.0), (dur, sp * dur)], 'LINEAR')
    return dict(fill=0, exposure=p_['exposure'] + 0.2, samples=32)


# ============================================================================= b11 x200 the power of all power stations
def v_power(shot, fps):
    dur = shot['dur']
    rng = random.Random(31)
    coll = lib.collection('Plant')
    SS.plant(coll, rng, dur)
    cam = lib.camera((-240, -300, 16), (0, 700, 330), 40)
    lib.animate_camera(cam, [(0, (-240, -300, 16)), (dur, (-215, -235, 20))], [(0, (0, 700, 330)), (dur, (30, 700, 360))])
    cam.data.clip_start = 0.5
    cam.data.clip_end = 30000
    for k in range(3):
        q = V((rng.uniform(-1500, 1500), rng.uniform(4000, 5500), 0))
        FX.bolt(coll, (q.x, q.y, 1500), (q.x + 80, q.y, 0), [rng.uniform(0.4, dur - 0.4)], rng, width=6.0, strength=50, light=4e7,
                name=f'FarBolt{k}')
    lib.bloom(0.25, 1.2, 7)
    return dict(fill=0.25, exposure=0.45, samples=32)


# ============================================================================= b12-b15 into the storm (avenue)
def _storm_scene(shot, fps, cam_keys, keep, rain_box, calm=None, calm_r=3.0, n_rain=2400, vortex_d=480.0, gone=None):
    """The storm avenue: grey light, the funnel at the end of the avenue, rain (with an optional calm circle)."""
    dur = shot['dur']
    rng = random.Random(32)
    p_, c = S.city(shot, fps, keep=keep, cam_keys=cam_keys)
    coll = lib.collection('Storm')
    f = S.ahead(shot, 1)[1]
    ctr = S.ahead(shot, vortex_d)[0]
    m = _storm_master(coll, (ctr.x, ctr.y), rng, 1300, 0, 1100, 80, rings=11, per=30, period=5.0, name='AveStorm')
    deck = FX.cloud_deck(coll, (ctr.x, ctr.y, 1300), 3800, rng, n=90, col='#5F666F', alpha=0.95, name='AveDeck', spin=0.04)
    x0, x1, y0, y1 = rain_box
    ca, cb = cam_keys[0][1], cam_keys[-1][1]
    FX.rain(coll, x0, x1, y0, y1, 15, n_rain, rng, speed=18, slant=(f.x * -6 + 3, f.y * -6 + 2), calm=calm, calm_r=calm_r, dur=dur,
            col='#D0DAE4', name='AveRain', clear=[((ca.x, ca.y), (cb.x, cb.y), 2.4, (ca.z + cb.z) / 2)])
    if gone is not None:
        # the funnel collapses into the ground and fades, the ceiling melts away (no leftover puffs in the sky)
        FX.key_scale(m, [(0, 1.0), (gone, 1.0), (gone + 0.7, 0.02)])
        for mn in ('AveStormMat', 'AveDeckMat'):
            if bpy.data.materials.get(mn):
                FX.fade_cloud(bpy.data.materials[mn], [(0, 1.0), (gone + 0.05, 1.0), (gone + 0.8, 0.0)])
        rm = bpy.data.materials.get('AveRainMat')
        if rm:
            mix = next(n for n in rm.node_tree.nodes if n.type == 'MIX_SHADER')
            FX.key(mix.inputs['Fac'], [(0, 0.55), (gone + 0.15, 0.55), (gone + 0.4, 0.0)])
        sun = bpy.data.objects.get('MetroSun')
        if sun:
            e = sun.data.energy
            for t, v in ((0, e), (gone + 0.2, e), (gone + 0.9, 4.2)):
                sun.data.energy = v
                sun.data.keyframe_insert('energy', frame=F(t))
    return p_, c, coll


def _ave(shot):
    f = S.ahead(shot, 1)[1]
    r = V((f.y, -f.x, 0))
    return f, r, V(shot['cam'])


def v_dropped(shot, fps):
    dur = shot['dur']
    rng = random.Random(33)
    f, r, cam0 = _ave(shot)
    edge = _ev(shot, 'edge', 1.7)
    hp = S.ahead(shot, 6.5, 0.0)[0]
    vp = S.ahead(shot, 5.5, 0.0)[0]
    c0 = cam0 + V((0, 0, -0.55))
    box = (cam0.x - 18, cam0.x + 18, cam0.y - 18, cam0.y + 18)
    keep = [((hp.x, hp.y), (vp.x, vp.y), 4.0)]
    p_, c, coll = _storm_scene(shot, fps, [(0, c0, hp + f * 20 + V((0, 0, 4))), (dur, c0 + f * 0.8, hp + f * 20 + V((0, 0, 6)))],
                               keep, box)
    c.data.lens = 26
    side = road_side(shot, 6.0)
    vx = vp + r * side * 3.6
    zv = S.ground(vx.x, vx.y)
    van = lib.car((vx.x, vx.y, zv), math.atan2(f.y, f.x), color='#1F2124', coll=coll, kind='van', lights=True, rng=rng, name='Van')
    lib.add_sine(van, 'rotation_euler', 0, 0.01, 0.5)
    z = S.ground(hp.x, hp.y)
    h = H.load(coll, (hp.x, hp.y, z), S.face(hp, hp + f))
    H.key_pose(h, 0, H.pose('stand', head=(14, -6, 0)))
    H.key_pose(h, edge - 0.3, H.pose('stand', head=(0, -10, 0)))
    H.walk(h, edge, dur, [(hp.x, hp.y), (hp.x + f.x * 3, hp.y + f.y * 3)], speed=0.85)
    return dict(fill=0.3, exposure=p_['exposure'], samples=32)


def v_walk(shot, fps):
    dur = shot['dur']
    f, r, cam0 = _ave(shot)
    calm_t = _ev(shot, 'calm', 2.8)
    a = S.ahead(shot, 12.0)[0]
    b = a + f * 3.6
    c0 = a - f * 4.2 + V((0, 0, 1.55))
    c1 = b - f * 3.2 + V((0, 0, 1.3))
    mid = a.lerp(b, 0.5)
    box = (mid.x - 15, mid.x + 15, mid.y - 15, mid.y + 15)

    def at(t):
        q = a.lerp(b, max(0.0, min(1.0, t / dur)))
        return q.x, q.y

    p_, c, coll = _storm_scene(shot, fps, [(0, c0, a + f * 12 + V((0, 0, 1.6))), (dur, c1, b + f * 12 + V((0, 0, 1.4)))],
                               [((c0.x, c0.y), (b.x, b.y), 3.5)], box, calm=at, calm_r=3.2, n_rain=3000)
    c.data.lens = 28
    z = S.ground(a.x, a.y)
    h = H.load(coll, (a.x, a.y, z), S.face(a, b))
    H.walk(h, 0.0, dur, [(a.x, a.y), (b.x, b.y)], speed=(b - a).length / dur)
    bub, s_ = FX.aura(coll, h['rig'], '#DCEBFF', r=3.0, z=1.2, t_on=calm_t - 0.3, strength=0.8, alpha=0.18, name='Calm',
                      scale=(1, 1, 0.75))
    return dict(fill=0.35, exposure=p_['exposure'], samples=32)


def _pair(shot):
    f, r, cam0 = _ave(shot)
    mp = S.ahead(shot, 17.0)[0]
    return f, r, cam0, mp


def v_hand(shot, fps):
    dur = shot['dur']
    rng = random.Random(34)
    touch = _ev(shot, 'touch', 1.0)
    f, r, cam0, mp = _pair(shot)
    h0 = mp - f * 2.6 + r * 0.7
    h1 = mp - f * 0.55 + r * 0.32
    c0 = mp - f * 1.8 - r * 3.4 + V((0, 0, 1.45))
    box = (mp.x - 15, mp.x + 15, mp.y - 15, mp.y + 15)

    def at(t):
        q = h0.lerp(h1, max(0.0, min(1.0, t / max(0.1, touch - 0.15))))
        return q.x, q.y

    p_, c, coll = _storm_scene(shot, fps, [(0, c0, mp + V((0, 0, 1.0))), (dur, c0 + r * 0.6 + f * 0.3, mp + V((0, 0, 1.05)))],
                               [((h0.x, h0.y), (mp.x, mp.y), 3.0), ((c0.x, c0.y), (c0.x, c0.y), 1.5)], box, calm=at, calm_r=2.6)
    c.data.lens = 34
    z = S.ground(mp.x, mp.y)
    g = S.folk((mp.x, mp.y, z), S.face(mp, mp + f), rng, coll, 'storm', height=1.0, name='WeatherMan')
    P2.stand(g, rng)
    for sd, sgn in (('L', 1), ('R', -1)):
        S.key_people(g, 'upper' + sd, 0, [(0, -2.7), (touch + 0.4, -2.7), (dur, -1.8)])
        S.key_people(g, 'upper' + sd, 1, [(0, sgn * 0.45)])
    FX.aura(coll, g['root'], '#B9D4FF', r=0.6, z=0.95, t_on=-1.0, t_off=touch + 0.25, strength=4.0, alpha=0.5, name='WmAura',
            scale=(1, 1, 1.9))
    zh = S.ground(h0.x, h0.y)
    h = H.load(coll, (h0.x, h0.y, zh), S.face(h0, h1))
    H.walk(h, 0.0, touch - 0.15, [(h0.x, h0.y), (h1.x, h1.y)], speed=(h1 - h0).length / max(0.1, touch - 0.15))
    H.key_pose(h, touch, H.pose('reach_r', head=(0, 4, 0)))
    H.key_root(h, touch, (h1.x, h1.y, zh), S.face(h1, mp + f * 3))
    H.key_pose(h, dur, H.pose('reach_r', head=(-6, 6, 0)))
    return dict(fill=0.35, exposure=p_['exposure'], samples=32)


def v_vanish(shot, fps):
    dur = shot['dur']
    rng = random.Random(35)
    gone = _ev(shot, 'gone', 0.42)
    f, r, cam0, mp = _pair(shot)
    hp = mp - f * 0.55 + r * 0.32
    c0 = mp - f * 5.2 - r * 1.6 + V((0, 0, 0.9))
    box = (mp.x - 18, mp.x + 18, mp.y - 18, mp.y + 18)
    p_, c, coll = _storm_scene(shot, fps, [(0, c0, mp + f * 30 + V((0, 0, 14))), (dur, c0 - f * 0.4, mp + f * 30 + V((0, 0, 20)))],
                               [((mp.x, mp.y), (hp.x, hp.y), 3.0), ((c0.x, c0.y), (c0.x, c0.y), 1.5)], box,
                               calm=lambda t: (hp.x, hp.y), calm_r=2.6, gone=gone)
    c.data.lens = 26
    z = S.ground(mp.x, mp.y)
    g = S.folk((mp.x, mp.y, z), S.face(mp, mp + f), rng, coll, 'storm', height=1.0, name='WeatherMan')
    P2.stand(g, rng)
    for sd in ('L', 'R'):
        S.key_people(g, 'upper' + sd, 0, [(0, -1.8), (dur, -0.4)])
    h = H.load(coll, (hp.x, hp.y, z), S.face(hp, mp + f * 3))
    H.key_pose(h, 0, H.pose('reach_r'))
    H.key_pose(h, dur, H.pose('reach_r', head=(0, -12, 0)))
    FX.ripple(coll, (hp.x, hp.y, z + 0.05), gone, 1.0, 60.0, strength=4.0)
    return dict(fill=0.3, exposure=p_['exposure'], samples=32)


# ============================================================================= b16-b19 the queue at his door: since 28.10.2026 in the stairwell
def v_queue(shot, fps):
    import sila_stair
    return sila_stair.v_queue(shot, fps)


def v_struggle(shot, fps):
    import sila_stair
    return sila_stair.v_struggle(shot, fps)


def v_calm(shot, fps):
    import sila_stair
    return sila_stair.v_calm(shot, fps)


def v_you(shot, fps):
    import sila_stair
    return sila_stair.v_you(shot, fps)


# ============================================================================= b20 the golden city (under the CTA)
def v_cta(shot, fps):
    dur = shot['dur']
    rng = random.Random(40)
    cam, tgt = V(shot['cam']), V(shot['target'])
    p_, c = S.city(shot, fps, cam_keys=[(0, cam, tgt), (dur, cam.lerp(tgt, 0.05), tgt + V((0, 0, 15)))])
    coll = lib.collection('Gold')
    f = (tgt - cam).normalized()
    _sky_flyers(coll, rng, cam, f, dur, n=14, dmin=60, dmax=260, hmin=-60, hmax=40, scale=2.5)
    return dict(fill=0, exposure=p_['exposure'], samples=32)
