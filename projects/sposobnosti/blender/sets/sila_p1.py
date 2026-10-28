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
    FX.sparks(coll, (near.x, near.y), 320, 380, 0, 220, 0.0, dur, rng, size=0.9, speed=(120, 180), strength=22, name='GiftNear')
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
    mr.inputs['From Max'].default_value = 0.08 * r
    mr.inputs['To Min'].default_value = 1.0
    mr.inputs['To Max'].default_value = 0.0
    L.new(ab.outputs[0], mr.inputs['Value'])
    # behind the band the night side keeps a faint golden glow
    tr = nt.nodes.new('ShaderNodeMath'); tr.operation = 'LESS_THAN'
    L.new(sep.outputs['X'], tr.inputs[0]); L.new(val.outputs[0], tr.inputs[1])
    trail = nt.nodes.new('ShaderNodeMath'); trail.operation = 'MULTIPLY'; trail.inputs[1].default_value = 0.03
    L.new(tr.outputs[0], trail.inputs[0])
    fac = nt.nodes.new('ShaderNodeMath'); fac.operation = 'MAXIMUM'
    L.new(mr.outputs['Result'], fac.inputs[0]); L.new(trail.outputs[0], fac.inputs[1])
    em = nt.nodes.new('ShaderNodeEmission')
    em.inputs['Color'].default_value = lib.C(col)
    em.inputs['Strength'].default_value = 3.5
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
    m, s, _ = FX.glow('Glint', '#FFB547', 4.0)
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
        FX.key_scale(ob, [(0, 0.001), (t - 0.02, 0.001), (t + 0.08, 1.0), (t + 0.5, rng.uniform(0.3, 0.6))])
    c = lib.camera((0, -255, 30), (0, 0, 4), 36)
    c.data.clip_end = 5000
    c.data.clip_start = 1.0
    lib.animate_camera(c, [(0, (0, -255, 30)), (forever, (0, -238, 26)), (dur, (0, -226, 22))],
                       [(0, (0, 0, 4)), (dur, (0, 0, 6))])
    lib.bloom(0.35, 1.0, 8)
    return dict(fill=0.0, exposure=0.1, samples=32)


# ============================================================================= a03 8 billion powers
def v_crowd(shot, fps):
    """28.10.2026: a tiny toy planet covered with people whose auras light up in a wave (sila_tiny.py), not the avenue."""
    import sila_tiny
    return sila_tiny.v_crowd(shot, fps)


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
        # the neighbour flies past the window, a metre outside the glass, waving; the hero's head follows him
        nb = S.folk((0, 0, 0), 0, rng, coll, 'neighbour', name='Nb')
        S.fly_pose(nb, 'one')
        S.fly(nb, [(0, (-7.5, 3.5, 2.7)), (fly_t, (-1.8, 3.0, 1.9)), (fly_t + 0.9, (1.4, 3.05, 1.8)), (dur, (5.5, 3.6, 2.3))],
              tilt=1.3, bob=0.0)
        FX.aura(coll, nb['root'], '#FFC857', r=0.45, z=0.9, t_on=-1.0, strength=3.0, alpha=0.5, name='NbAura', scale=(1, 1, 1.9))
        H.key_pose(h, 0, H.pose('sill', head=(30, 4, 0)))
        H.key_pose(h, fly_t, H.pose('sill', head=(22, 2, 0)))
        H.key_pose(h, fly_t + 0.9, H.pose('sill', head=(-8, 0, 0)))
        H.key_pose(h, dur, H.pose('sill', head=(-34, 4, 0), lean=10.0))
        cam = lib.camera((-0.95, -0.15, 1.45), (0.3, 3.2, 1.6), 28)
        lib.animate_camera(cam, [(0, (-0.95, -0.15, 1.45)), (dur, (-0.8, 0.1, 1.45))], [(0, (0.0, 3.2, 1.65)), (dur, (0.7, 3.2, 1.6))])
    cam.data.clip_start = 0.05
    lib.bloom(0.2, 1.2, 6)
    return dict(fill=0.35, exposure=0.35, samples=32)


def v_window(shot, fps):
    return _room_shot(shot, fps, 'window')


def v_flyer(shot, fps):
    return _room_shot(shot, fps, 'flyer')


# ============================================================================= a06 / a07 / a08 the courtyard and the stairwell
def v_granny(shot, fps):
    """28.10.2026: granny lifts the car in the courtyard by the entrance (sila_yard.py), not on the street."""
    import sila_yard
    return sila_yard.v_granny(shot, fps)


def v_car(shot, fps):
    import sila_yard
    return sila_yard.v_car(shot, fps)


def v_courier(shot, fps):
    """28.10.2026: the courier is now in the stairwell (sila_stair.py), not on the street."""
    import sila_stair
    return sila_stair.v_courier(shot, fps)


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
    mid_t = tgt + V((0, 0, 6))
    for k, (q, r) in enumerate(S.sky_spots(cam, mid_t, shot.get('lens', 21), 16, 5, 26, rng, u=(-0.7, 0.7), v=(-0.75, 0.75))):
        pp = S.folk((0, 0, 0), 0, rng, coll, None, name=f'Fl{k}')
        S.fly_pose(pp, rng.choice(['forward', 'one', 'forward']))
        sgn = 1 if k % 3 else -1
        v = r * sgn * rng.uniform(5, 9)
        a = q - v * dur * 0.5
        S.fly(pp, [(0, tuple(a)), (dur, tuple(a + v * dur))], tilt=rng.uniform(1.25, 1.5), bob=0.1)
        FX.aura(coll, pp['root'], AURA[k % len(AURA)], r=0.45, z=0.9, t_on=-1, strength=3.0, alpha=0.5, name=f'FlA{k}',
                scale=(1, 1, 1.9))
    return dict(fill=0.2, exposure=p_['exposure'], samples=32)


# ============================================================================= a11 100 000 flights a day
def v_planes(shot, fps):
    """28.10.2026: above a sea of clouds, jets with contrails (sila_sky.py), not over the city."""
    import sila_sky
    return sila_sky.v_planes(shot, fps)


# ============================================================================= a12 empty airports
def v_airport(shot, fps):
    dur = shot['dur']
    rng = random.Random(12)
    coll = lib.collection('Airport')
    SS.airport(coll, rng)
    import pcommon as pc
    # inside the terminal: the glass wall fills the frame, a parked jet noses at it, rows of empty seats, every flight cancelled
    bpy.data.objects['Terminal'].hide_render = True
    bpy.data.objects['Terminal'].hide_viewport = True
    lib.box((520, 46, 0.03), (0, 165, 0.0), lib.mat('TermFloor', '#BDB8AE', rough=0.22, spec=0.6), bevel=0, name='TermFloor',
            coll=coll, origin='bottom')
    lib.box((520, 0.6, 0.5), (0, 142.1, 0.0), lib.mat('TermSill', '#8F9296', rough=0.4), bevel=0, name='TermSill', coll=coll,
            origin='bottom')
    seat_m = lib.mat('Seat', '#2E3A48', rough=0.45)
    leg_m = lib.mat('SeatLeg', '#9AA0A6', rough=0.3, metal=0.6)
    for row, y in enumerate((147.0, 149.6, 152.2)):
        for x0 in (-21.0, -12.0, -1.0, 8.0):
            w = 6.0
            cx = x0 + w / 2
            lib.box((w, 0.5, 0.07), (cx, y, 0.42), seat_m, bevel=0.02, name='SeatPan', coll=coll, origin='bottom')
            lib.box((w, 0.06, 0.45), (cx, y + 0.26, 0.5), seat_m, rot=(-0.12, 0, 0), bevel=0.02, name='SeatBack', coll=coll,
                    origin='bottom')
            lib.box((w, 0.08, 0.06), (cx, y, 0.12), leg_m, bevel=0, name='SeatBeam', coll=coll, origin='bottom')
            for k in range(11):
                lib.box((0.05, 0.42, 0.2), (x0 + k * 0.6, y, 0.49), leg_m, bevel=0.01, name='SeatArm', coll=coll, origin='bottom')
            for lx in (x0 + 0.4, x0 + w - 0.4):
                lib.box((0.06, 0.06, 0.42), (lx, y, 0.0), leg_m, bevel=0, name='SeatLeg', coll=coll, origin='bottom')
    # departures board hanging over the seats, facing the camera
    bx, by, bz = -10.5, 146.0, 4.6
    lib.box((6.4, 0.25, 3.3), (bx, by, bz), lib.mat('Board', '#14171B', rough=0.5), bevel=0.05, name='Board', coll=coll,
            origin='bottom')
    for lx in (bx - 2.6, bx + 2.6):
        lib.cyl(0.03, 12.0, (lx, by, bz + 3.3), leg_m, verts=6, name='BoardWire', coll=coll, origin='bottom')
    rot = (math.pi / 2, 0, math.pi)
    pc.text('ВЫЛЕТ', 0.42, (bx, by + 0.14, bz + 2.75), rot, '#F2F2F0', strength=2.0, coll=coll, name='BoardHead')
    flights = [('SU 1402', 'СОЧИ'), ('S7 2041', 'НОВОСИБИРСК'), ('U6 263', 'ЕКАТЕРИНБУРГ'), ('DP 405', 'КАЛИНИНГРАД'),
               ('SU 1130', 'КАЗАНЬ'), ('FV 6551', 'МИНСК')]
    for k, (no, city) in enumerate(flights):
        zz = bz + 2.25 - k * 0.38
        pc.text(no, 0.22, (bx + 2.85, by + 0.14, zz), rot, '#E8C15A', strength=1.6, coll=coll, align='LEFT', name=f'BNo{k}')
        pc.text(city, 0.22, (bx + 1.6, by + 0.14, zz), rot, '#E8C15A', strength=1.6, coll=coll, align='LEFT', name=f'BCity{k}')
        pc.text('ОТМЕНЕН', 0.22, (bx - 1.35, by + 0.14, zz), rot, '#FF4A3D', strength=2.6, coll=coll, align='LEFT', name=f'BSt{k}')
    cam = lib.camera((-7.0, 158.5, 1.55), (-4.0, 80, 4.5), 24)
    lib.animate_camera(cam, [(0, (-7.0, 158.5, 1.55)), (dur, (-7.3, 156.8, 1.6))], [(0, (-4.0, 80, 4.5)), (dur, (-4.6, 80, 4.9))])
    cam.data.clip_start = 0.1
    cam.data.clip_end = 8000
    # nobody: only a few birds cross the empty apron
    pc.birds(coll, rng, 6, (-40, 95, 7), (7, 1.5, 0), dur, spread=(6, 4, 2), size=0.3)
    lib.bloom(0.2, 1.3, 6)
    return dict(fill=0.3, exposure=-0.15, samples=32)


# ============================================================================= a13 / a14 looking for his power (roof, playground)
def v_search(shot, fps):
    """28.10.2026: on the roof of his block, trying to call up a power (sila_yard.py), not the city park."""
    import sila_yard
    return sila_yard.v_search(shot, fps)


def _sky_flyers(coll, rng, cam, f, dur, n=6, dmin=40, dmax=150, hmin=20, hmax=80, scale=1.0, aura=True, view=None):
    """People flying past. view=(cam, target, lens): put them where the camera sees open sky (sila.sky_spots)."""
    fh = V((f.x, f.y, 0)).normalized()
    r = V((fh.y, -fh.x, 0))
    if view:
        spots = S.sky_spots(view[0], view[1], view[2], n, dmin, dmax, rng, v=(0.0, 0.85))
    else:
        spots = []
        for k in range(n):
            d = rng.uniform(dmin, dmax)
            q = cam + fh * d + r * rng.uniform(-0.6, 0.6) * d
            q.z = cam.z + rng.uniform(hmin, hmax)
            spots.append((q, r))
    out = []
    for k, (q, rr) in enumerate(spots):
        pp = S.folk((0, 0, 0), 0, rng, coll, None, name=f'Sky{k}_{rng.randint(0, 999)}')
        S.fly_pose(pp, rng.choice(['forward', 'one']))
        v = (rr * rng.choice((-1, 1)) + fh * rng.uniform(-0.4, 0.4)).normalized() * rng.uniform(5, 10)
        S.fly(pp, [(0, tuple(q - v * dur * 0.5)), (dur, tuple(q + v * dur * 0.5))], bob=0.1)
        pp['root'].scale = (scale,) * 3
        if aura:
            FX.aura(coll, pp['root'], AURA[k % len(AURA)], r=0.45, z=0.9, t_on=-1, strength=3.5, alpha=0.5,
                    name=f'SkyA{k}_{rng.randint(0, 999)}', scale=(1, 1, 1.9))
        out.append(pp)
    return out


def v_bench(shot, fps):
    """28.10.2026: the bench jump is on the courtyard playground (sila_yard.py)."""
    import sila_yard
    return sila_yard.v_bench(shot, fps)


# ============================================================================= a15 an hour staring at a mug
def v_mug(shot, fps):
    dur = shot['dur']
    rng = random.Random(15)
    coll = lib.collection('Kitchen')
    mug, hands, sun = SS.kitchen(coll, rng)
    h = H.load(coll, (0.0, 0.98, 0.075), 0.0)
    h['body']['eye_look'], h['body']['eye_spread'] = (0.0, -0.4), 0.08     # he stares at the mug
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


# ============================================================================= a16 / a17 / a18 / a19 the evening
# 28.10.2026: in his courtyard at dusk (sila_yard.py), not the city street: the neighbour falls into a bush there
def v_evening(shot, fps):
    import sila_yard
    return sila_yard.v_evening(shot, fps)


def v_crash(shot, fps):
    import sila_yard
    return sila_yard.v_crash(shot, fps)


def v_realize(shot, fps):
    import sila_yard
    return sila_yard.v_realize(shot, fps)


def v_ordinary(shot, fps):
    import sila_yard
    return sila_yard.v_ordinary(shot, fps)


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
