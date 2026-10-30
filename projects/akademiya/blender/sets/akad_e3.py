"""Episode 3 «Академия»: the letter, the Academy and director Saul, the entrance exam on the arena (CJ lifts a bus,
Cesar runs a lap, Denise stops time), the hero shows nothing, the golem, Emmet takes him, the evening on the steps.
Times inside a shot come from shot['events'] (tools/build_timeline.py), with defaults for a dry run.
"""
import math
import random

import bpy
from mathutils import Vector as V

import akad as A
import cast as K
import lib
import people2 as P2
import sila as S
import sila_fx as FX
import sila_hero as H
import sila_sets as SS

F = lib.sec2f
ev = A._ev


def face(a, b):
    return S.face(V(a), V(b))


def cam(c0, t0, c1=None, t1=None, lens=35, dur=3.0, clip=0.1):
    c = lib.camera(tuple(c0), tuple(t0), lens)
    lib.animate_camera(c, [(0, tuple(c0)), (dur, tuple(c1 or c0))], [(0, tuple(t0)), (dur, tuple(t1 or t0))])
    c.data.clip_start = clip
    return c


def pose_all(h, dur, p, t=0.0):
    H.key_pose(h, t, p)
    H.key_pose(h, dur, p)


# ----------------------------------------------------------------------------- the arena
def arena_set(rng, crowd=2200, kind='day', zero=None):
    """zero: None - the board shows a dash for the new guy (before his turn); a time - his '0' lights up then."""
    coll = lib.collection('Arena')
    A.sky(kind, sun_dir=(-0.35, -0.55, 0.55))
    info = A.arena(coll, rng, crowd=crowd)
    A.scoreboard(coll, zero=zero)
    return coll, info


def fans_laugh(rng, amp=0.05):
    for o in bpy.data.objects:
        if o.name.startswith('Fan_'):
            lib.add_sine(o, 'location', 2, amp, 0.28, rng.uniform(0, 6))


def bus(coll, loc=(0, 0, 0), heading=0.0, name='Bus'):
    """A yellow city bus 11.5 x 2.5 x 3 m, forward = local +X, pivot at the middle of its floor line."""
    root = lib.empty(name, loc, (0, 0, heading), coll=coll)
    paint = lib.mat('BusPaint', '#F2B632', rough=0.35, coat=0.4)
    glass = lib.mat('BusGlass', '#2A3540', rough=0.08, spec=0.8)
    trim = lib.mat('BusTrim', '#EDEBE6', rough=0.5)
    rub = lib.mat('Tyre', '#151414', rough=0.85)
    parts = [lib.box((11.5, 2.5, 2.6), (0, 0, 0.45), paint, bevel=0.18, name=name + 'Body', coll=coll, origin='bottom'),
             lib.box((11.2, 2.52, 0.9), (0.1, 0, 1.55), glass, bevel=0.05, name=name + 'Win', coll=coll, origin='bottom'),
             lib.box((0.05, 2.2, 1.3), (5.76, 0, 1.25), glass, bevel=0, name=name + 'Wind', coll=coll, origin='bottom'),
             lib.box((11.6, 2.56, 0.18), (0, 0, 0.95), trim, bevel=0.02, name=name + 'Stripe', coll=coll, origin='bottom'),
             lib.box((1.2, 2.54, 0.4), (4.9, 0, 2.62), lib.emission_mat('BusSign', '#FFB34A', 3.0)[0], bevel=0.02, name=name + 'Sign',
                     coll=coll, origin='bottom')]
    for sx in (-3.6, 3.8):
        for sy in (-1.1, 1.1):
            parts.append(lib.cyl(0.5, 0.35, (sx, sy, 0.5), rub, rot=(math.pi / 2, 0, 0), verts=20, bevel=0.04, name=name + 'Wheel', coll=coll))
    for p in parts:
        p.parent = root
    return root


# ============================================================================= c00 the hook: «я получил ноль»
def v_board(shot, fps):
    """The hero alone on the field, his back to us, under the giant board; his '0' lights up on the word «ноль»."""
    dur = shot['dur']
    rng = random.Random(30)
    coll, info = arena_set(rng, zero=ev(shot, 'zero', min(1.2, dur * 0.5)))
    h = H.load(coll, (0, 0, 0), math.pi)
    pose_all(h, dur, H.pose('stand', head=(0, -14, 0)))
    fans_laugh(rng)
    cam((0.6, -6.5, 1.0), (0, 34.9, 10.5), (0.45, -5.6, 1.0), (0, 34.9, 10.3), 45, dur)
    lib.bloom(0.3, 1.0, 7)
    return dict(fill=0.45, exposure=0.38, samples=32)


def v_first(shot, fps):
    """Flash-forward «и меня взяли первым»: the hero and Emmet side by side, the board with the 0 behind them."""
    dur = shot['dur']
    rng = random.Random(29)
    coll, info = arena_set(rng, zero=0.0)
    h = H.load(coll, (0.45, 0, 0), 0.0)
    H.key_pose(h, 0, H.pose('stand', head=(0, 4, 0)))
    H.key_pose(h, dur, H.pose('stand', head=(0, -2, 0)))
    em = K.load('emmet', coll, (-0.55, 0.2, 0), 0.0)
    H.key_pose(em, 0, H.pose('stand', head=(24, 0, 0)))
    H.key_pose(em, dur, H.pose('stand', head=(18, -2, 0)))
    cam((0.1, -2.9, 0.85), (0, 0, 1.4), (0.08, -2.5, 0.88), (0, 0, 1.38), 24, dur)
    lib.bloom(0.3, 1.0, 7)
    return dict(fill=0.5, exposure=0.4, samples=32)


# ============================================================================= c01 the letter
def v_letter(shot, fps):
    """The envelope flies in through the window, he catches it and turns to us with it (camera inside the room)."""
    dur = shot['dur']
    rng = random.Random(31)
    coll = lib.collection('Room')
    SS.room(coll, rng, morning=True)
    h = H.load(coll, (0.2, 1.05, 0), math.pi)
    catch = ev(shot, 'catch', min(1.3, dur * 0.45))
    turn = min(dur - 0.2, catch + 0.55)
    H.key_pose(h, 0, H.pose('sill', head=(0, 6, 0)))
    H.key_root(h, 0, (0.2, 1.05, 0), math.pi)
    H.key_root(h, catch - 0.3, (0.2, 1.05, 0), math.pi)
    H.key_pose(h, catch - 0.15, H.pose('reach_r', head=(0, -10, 0)))
    H.key_pose(h, catch + 0.2, H.pose('hands_front', head=(0, 20, 0)))
    H.key_root(h, turn, (0.2, 0.95, 0), 0.0)
    H.key_pose(h, turn, H.pose('hands_front', head=(0, 22, 0)))
    H.key_pose(h, dur, H.pose('hands_front', head=(4, 26, 0)))
    env_m = lib.mat('Envelope', '#F4EFE4', rough=0.6)
    seal_m = lib.mat('Seal', '#C9302C', rough=0.35)
    env = lib.box((0.26, 0.18, 0.006), (0, 0, 0), env_m, bevel=0.003, name='Envelope', coll=coll)
    seal = lib.cyl(0.03, 0.008, (0, 0, 0.004), seal_m, verts=16, name='Seal', coll=coll)
    seal.parent = env
    gold = lib.mat('AkGold', '#E7B64A', rough=0.3, metal=0.85)
    A.text('А', 0.04, (0, 0, 0.009), (0, 0, 0), gold, coll, extrude=0.002, name='SealA').parent = env
    lib.key_obj(env, F(0), loc=(1.4, 4.2, 2.3), rot=(0.4, 0.2, 0.3))
    lib.key_obj(env, F(catch * 0.6), loc=(0.8, 2.3, 1.6), rot=(1.1, -0.4, 0.9))
    # in the right hand at the catch, then held in both hands at chest height (wrists at z 0.61)
    lib.key_obj(env, F(catch), loc=(0.5, 1.08, 0.72), rot=(1.2, 0.0, 0.6))
    lib.key_obj(env, F(catch + 0.23), loc=(0.3, 0.76, 0.67), rot=(1.45, 0.0, 0.25))
    lib.key_obj(env, F(turn), loc=(0.2, 0.7, 0.68), rot=(math.pi / 2 - 0.25, 0.0, 0.0))
    lib.key_obj(env, F(dur), loc=(0.2, 0.69, 0.69), rot=(math.pi / 2 - 0.3, 0.0, 0.0))
    cam((0.75, -1.1, 1.3), (0.2, 1.0, 1.0), (0.6, -0.8, 1.26), (0.2, 1.0, 0.98), 30, dur)
    return dict(fill=0.35, exposure=0.05, samples=32)


# ============================================================================= c02 / c03 the Academy
def v_gate(shot, fps):
    dur = shot['dur']
    rng = random.Random(32)
    coll = lib.collection('Academy')
    A.sky('morning', sun_dir=(-0.5, -0.65, 0.3))
    A.academy(coll, rng, dur=dur)
    A.flyers(coll, rng, dur, n=7, box=((-35, 35), (-40, 0), (18, 45)))
    h = H.load(coll, (0.6, -88, -2.4), 0.0)
    H.walk(h, 0, dur, [(0.6, -88), (0.6, -88 + 0.9 * dur)], speed=0.9)
    for k in range(6):
        x = rng.uniform(-5, 5)
        y0 = rng.uniform(-86, -70)
        p = S.folk((x, y0, -2.4), math.pi, rng, coll, rng.choice(['girl', 'kid', 'sparky', None]), height=0.9, name=f'Stud{k}')
        sp = rng.uniform(1.0, 1.3)
        P2.walk(p, sp, rng.random(), 0.9)
        lib.move_root(p, [(x, y0, -2.4), (x, y0 + sp * dur, -2.4)], 0.0, sp)
    cam((2.6, -94.0, -1.2), (0, -40, 16), (1.6, -91.5, -0.8), (0, -40, 21), 24, dur)
    lib.bloom(0.25, 1.0, 7)
    return dict(fill=0.45, exposure=0.35, samples=32)


def v_opened(shot, fps):
    dur = shot['dur']
    rng = random.Random(33)
    coll = lib.collection('Academy')
    A.sky('morning', sun_dir=(-0.55, -0.6, 0.35))
    A.academy(coll, rng, dur=dur)
    A.flyers(coll, rng, dur, n=8, box=((-28, 28), (-30, -5), (8, 30)))
    for k in range(14):
        x, y = rng.uniform(-18, 18), rng.uniform(-30, -12)
        p = S.folk((x, y, 0), rng.uniform(-math.pi, math.pi), rng, coll, rng.choice(['girl', 'kid', 'sparky', None]), height=0.9,
                   name=f'Plaza{k}')
        P2.stand(p, rng)
        if k % 3 == 0:
            FX.aura(coll, p['torso'], rng.choice(A.AURA), r=0.55, z=0.0, strength=2.5, alpha=0.45, name=f'PlazaAura{k}')
    cam((6, -46, 1.2), (0, -12, 6), (5, -42, 6.5), (0, -9, 22), 22, dur)
    lib.bloom(0.25, 1.0, 7)
    return dict(fill=0.45, exposure=0.35, samples=32)


# ============================================================================= c04 / c05 director Saul
def saul_steps(shot, rng, coll, close=False):
    dur = shot['dur']
    A.sky('morning', sun_dir=(-0.6, -0.5, 0.35))
    A.academy(coll, rng, dur=dur, city=not close)
    sl = K.load('saul', coll, (0, -12.5, 0), 0.0)
    H.key_pose(sl, 0, H.pose('stand', arm=((12, 4), (16, 40)), fore=((8, 10), (14, 80)), head=(0, -4, 0)))
    H.key_pose(sl, dur * 0.4, H.pose('stand', arm=((12, 4), (20, 55)), fore=((8, 10), (16, 95)), head=(-6, -2, 0)))
    H.key_pose(sl, dur, H.pose('stand', arm=((12, 4), (16, 45)), fore=((8, 10), (14, 85)), head=(5, -4, 0)))
    K.talk(sl, 0.1, dur - 0.1, seed=4)
    lst = []
    for k in range(16):
        x = -9 + (k % 8) * 2.5 + rng.uniform(-0.4, 0.4)
        y = -22 - (k // 8) * 2.2
        p = S.folk((x, y, 0), face((x, y), (0, -12.5)), rng, coll, rng.choice(['girl', 'kid', 'sparky', None]), height=0.9,
                   name=f'Listener{k}')
        lst.append(p)
    return sl, lst


def nod(p, t0, t1, period=0.7, amp=0.22):
    t = t0
    while t < t1:
        S.key_people(p, 'head', 0, [(t, 0.0), (t + period * 0.5, amp)])
        t += period
    S.key_people(p, 'head', 0, [(t1, 0.0)])


def laugh(p, t0, t1, seed=0, period=0.42, point=False):
    """A cast member laughs: doubles over (hands on the belly, head down) and throws the head back, in turn;
    point=True: the right hand points at the camera (at the hero) the whole time.
    Pack clips (FastNod ...) keep the GLB bone names, so after cast.load renames the bones they leave a T-pose."""
    r = random.Random(seed)
    H.key_pose(p, 0, H.pose('stand', arm=(18, 20), fore=(-36, 64)))
    t, k = t0, 0
    while t < t1:
        if k % 2 == 0:
            H.key_pose(p, t, H.pose('stand', arm=((18, 24), (-14, 80)) if point else (18, 24),
                                    fore=((-42, 70), (-18, 86)) if point else (-42, 70), lean=13.0 + r.uniform(-3, 3),
                                    head=(0, 16 + r.uniform(-4, 4), r.uniform(-6, 6))))
        else:
            H.key_pose(p, t, H.pose('stand', arm=((20, 14), (-14, 86)) if point else (20, 14),
                                    fore=((-30, 58), (-18, 92)) if point else (-30, 58), lean=-5.0 + r.uniform(-2, 2),
                                    head=(0, -18 + r.uniform(-4, 4), r.uniform(-6, 6))))
        t += period * r.uniform(0.85, 1.15)
        k += 1
    K.talk(p, t0, t1, rate=9, amp=0.9, seed=seed)


def v_saul(shot, fps):
    dur = shot['dur']
    rng = random.Random(34)
    coll = lib.collection('Academy')
    sl, lst = saul_steps(shot, rng, coll)
    for p in lst:
        P2.stand(p, rng)
    cam((2.8, -19.5, 1.5), (0, -12.5, 1.7), (2.2, -18.0, 1.45), (0, -12.5, 1.75), 32, dur)
    return dict(fill=0.5, exposure=0.38, samples=32)


def v_nospeak(shot, fps):
    """One student raises a hand to object, Saul says a word, the hand goes down and the whole crowd nods."""
    dur = shot['dur']
    rng = random.Random(35)
    coll = lib.collection('Academy')
    sl, lst = saul_steps(shot, rng, coll, close=True)
    obj = lst[3]
    up = ev(shot, 'up', 0.3)
    S.key_people(obj, 'upperR', 0, [(0, 0.0), (up, 0.0), (up + 0.25, -2.9), (up + 1.0, -2.9), (up + 1.3, 0.0)])
    for p in lst:
        nod(p, up + 1.2, dur, period=0.75)
    cam((-3.5, -27.5, 1.3), (0.5, -13.0, 1.95), (-2.6, -24.0, 1.25), (0.2, -13.0, 1.9), 34, dur)
    return dict(fill=0.5, exposure=0.38, samples=32)


# ============================================================================= c06 the arena
def v_arena(shot, fps):
    dur = shot['dur']
    rng = random.Random(36)
    coll, info = arena_set(rng)
    for n, x in (('cj', -4.0), ('cesar', -2.0), ('denise', 2.0)):
        p = K.load(n, coll, (x, -4.0, 0), 0.0)
        H.key_pose(p, 0, H.pose('stand', head=(rng.uniform(-10, 10), 0, 0)))
    h = H.load(coll, (0.0, -4.2, 0), 0.0)
    pose_all(h, dur, H.pose('stand', head=(0, 8, 0)))
    cam((0, -40, 22), (0, 0, 2), (0, -26, 9), (0, -2, 2), 22, dur, clip=0.5)
    lib.bloom(0.25, 1.0, 7)
    return dict(fill=0.45, exposure=0.38, samples=32)


# ============================================================================= c07 / c08 CJ lifts a bus
def v_bus(shot, fps, close=False):
    dur = shot['dur']
    rng = random.Random(37)
    coll, info = arena_set(rng)
    cj = K.load('cj', coll, (0, 0, 0), 0.0)
    lift = ev(shot, 'lift', 0.5 if not close else 0.0)
    b = bus(coll, (0, 0.6, 0), 0.0)
    top = 2.17 - 0.45                      # the body's underside (0.45 above the pivot) rests on CJ's raised palm
    lib.key_obj(b, F(0), loc=(0, 0.6, 0.0), rot=(0, 0, 0))
    lib.key_obj(b, F(lift), loc=(0, 0.6, 0.0), rot=(0, 0, 0))
    lib.key_obj(b, F(lift + 0.6), loc=(0, 0.25, top), rot=(0.0, 0.0, 0.0))
    lib.key_obj(b, F(dur), loc=(0, 0.25, top + 0.04), rot=(0.0, 0.03, 0.0))
    H.key_pose(cj, 0, H.pose('crouch', arm=((20, -10), (20, 60)), fore=((18, 0), (10, 90))))
    H.key_pose(cj, lift, H.pose('crouch', arm=((20, -10), (10, 120)), fore=((18, 0), (6, 150))))
    H.key_pose(cj, lift + 0.6, H.pose('stand', arm=((30, 10), (4, 178)), fore=((26, 30), (2, 178)), head=(0, -25, 0)))
    H.key_pose(cj, dur, H.pose('stand', arm=((34, 14), (4, 178)), fore=((30, 40), (2, 178)), head=(4, -22, 0)))
    FX.aura(coll, cj['rig'], '#FF9C5B', r=0.5, z=1.0, t_on=max(0.0, lift - 0.2), strength=2.0, alpha=0.18, name='CJAura')
    if close:
        cam((1.8, -3.2, 0.5), (0, 0.3, 2.6), (1.4, -2.9, 0.45), (0, 0.3, 2.8), 20, dur)
    else:
        cam((5.0, -9.5, 1.3), (0, 0.4, 2.0), (3.8, -8.0, 1.2), (0, 0.4, 2.3), 28, dur)
    return dict(fill=0.5, exposure=0.38, samples=32)


def v_tons(shot, fps):
    return v_bus(shot, fps, close=True)


# ============================================================================= c09 Cesar runs a lap in a second
def v_cesar(shot, fps):
    """Set like a sprinter on the start line, gone in a streak round the track, back on the line a second later."""
    dur = shot['dur']
    rng = random.Random(38)
    coll, info = arena_set(rng)
    R = (38.0, 27.0)
    go = ev(shot, 'go', 0.4)
    n, lap = 48, 1.0
    cz = K.load('cesar', coll, (0, -R[1], 0), math.pi / 2)
    rig = cz['rig']
    lib.key_obj(rig, F(0), loc=(0, -R[1], 0), rot=(0, 0, math.pi / 2), interp='LINEAR')
    for j in range(n + 1):
        t = go + lap * j / n
        a = -math.pi / 2 + math.tau * j / n
        p = (math.cos(a) * R[0], math.sin(a) * R[1], 0)
        hd = math.pi / 2 + math.tau * j / n
        lib.key_obj(rig, F(t), loc=p, rot=(0, 0, hd), interp='LINEAR')
    lib.key_obj(rig, F(dur), loc=(0, -R[1], 0), rot=(0, 0, math.pi / 2 + math.tau), interp='LINEAR')
    # set - sprint (legs swap every 0.07 s) - upright on the line again
    H.key_pose(cz, 0, H.pose('crouch', arm=(14, -25), fore=(10, -10), lean=34.0, head=(0, -16, 0)))
    H.key_pose(cz, go - 0.05, H.pose('crouch', arm=(14, -25), fore=(10, -10), lean=34.0, head=(0, -16, 0)))
    t, k = go, 0
    while t < go + lap:
        H.key_pose(cz, t, H.pose('stand', arm=((20, -40 if k % 2 else 60), (20, 60 if k % 2 else -40)),
                                 fore=(30, 90), thigh=(60.0, -25.0) if k % 2 == 0 else (-25.0, 60.0),
                                 shin=(-70.0, -20.0) if k % 2 == 0 else (-20.0, -70.0),
                                 lean=22.0))
        t += 0.07
        k += 1
    H.key_pose(cz, go + lap + 0.12, H.pose('stand', arm=(22, 8), fore=(30, 40), lean=6.0, head=(0, -6, 0)))
    H.key_pose(cz, dur, H.pose('stand', arm=(22, 8), fore=(30, 40), lean=2.0, head=(0, -10, 6)))
    m, s_sock, a_sock = FX.glow('LapTrail', '#FFE7B0', 2.5, alpha=0.6)
    A.ring('LapTrail', (R[0] - 0.08, R[1] - 0.08), (R[0] + 0.08, R[1] + 0.08), 0.02, 0.04, m, coll, n=128)
    FX.key(a_sock, [(0, 0.0), (go, 0.0), (go + lap, 0.6), (dur, 0.15)])
    cam((2.3, -31.2, 1.3), (-0.4, -26.0, 1.0), (2.0, -30.6, 1.25), (-0.4, -26.0, 1.1), 30, dur, clip=0.3)
    return dict(fill=0.45, exposure=0.38, samples=32)


# ============================================================================= c10 Denise stops time
def v_denise(shot, fps):
    dur = shot['dur']
    rng = random.Random(39)
    coll, info = arena_set(rng)
    dn = K.load('denise', coll, (0, 0, 0), 0.0)
    stop = ev(shot, 'stop', 0.8)
    H.key_pose(dn, 0, H.pose('stand'))
    H.key_pose(dn, stop - 0.2, H.pose('point', head=(0, -6, 0)))
    H.key_pose(dn, dur, H.pose('point', head=(-8, -6, 0)))
    sm = lib.mat('Grain', '#E3C995', rough=0.9)
    for k in range(60):
        x, y = rng.uniform(-4, 4), rng.uniform(1, 9)
        g = lib.sphere(rng.uniform(0.03, 0.08), (x, y, 0.2), sm, 6, 4, name='Grain', coll=coll)
        z1 = rng.uniform(0.6, 3.0)
        lib.key_obj(g, F(0), loc=(x, y, 0.2), interp='LINEAR')
        lib.key_obj(g, F(stop), loc=(x, y + 0.3, z1), interp='LINEAR')
        lib.key_obj(g, F(dur), loc=(x, y + 0.31, z1 + 0.01), interp='LINEAR')
    for o in bpy.data.objects:                                # the flags stop waving
        if o.name.startswith('ArFlag') and o.animation_data:
            o.animation_data_clear()
    FX.ripple(coll, (0, 0, 1.0), stop, dur=1.0, rmax=14.0, col='#9FD8FF', strength=2.5, name='TimeRipple')
    FX.aura(coll, dn['rig'], '#7FD8FF', r=0.55, z=0.95, t_on=max(0.0, stop - 0.3), strength=3.0, alpha=0.45, name='DnAura')
    cam((1.8, -4.4, 1.15), (0, 0, 1.2), (1.3, -3.8, 1.1), (0, 0, 1.25), 34, dur)
    return dict(fill=0.5, exposure=0.38, samples=32)


# ============================================================================= c11 / c12 «what will you show?» - nothing
def v_askyou(shot, fps):
    dur = shot['dur']
    rng = random.Random(40)
    coll, info = arena_set(rng)
    h = H.load(coll, (0, 0, 0), math.pi)
    pose_all(h, dur, H.pose('stand', head=(0, -10, 0)))
    sl = K.load('saul', coll, (0, 36.6, 3.1), math.pi)
    K.talk(sl, 0.2, dur - 0.3, seed=9)
    H.key_pose(sl, 0, H.pose('point', head=(0, 10, 0)))
    lib.box((3.0, 1.0, 1.0), (0, 35.6, 3.1), lib.mat('Desk', '#2F4F7A', rough=0.5), bevel=0.05, name='JudgeDesk', coll=coll,
            origin='bottom')
    cam((0.7, 4.0, 1.35), (0, 0, 1.25), (0.5, 3.3, 1.3), (0, 0, 1.3), 30, dur)
    return dict(fill=0.45, exposure=0.38, samples=32)


def v_laugh(shot, fps):
    dur = shot['dur']
    rng = random.Random(41)
    coll, info = arena_set(rng)
    h = H.load(coll, (0, 0, 0), 0.0)
    sh = ev(shot, 'shrug', 0.4)
    H.key_pose(h, 0, H.pose('stand'))
    H.key_pose(h, sh, H.pose('shrug'))
    H.key_pose(h, dur, H.pose('shrug', head=(0, 8, 6)))
    cj = K.load('cj', coll, (-1.9, 2.6, 0), face((-1.9, 2.6), (0, 0)))
    laugh(cj, 0.1, dur, seed=2)
    for o in bpy.data.objects:
        if o.name.startswith('Fan_'):
            lib.add_sine(o, 'location', 2, 0.05, 0.28, rng.uniform(0, 6))
    cam((0.5, -3.0, 0.95), (-0.3, 0, 0.9), (0.35, -2.5, 0.95), (-0.3, 0, 0.92), 30, dur)
    return dict(fill=0.5, exposure=0.38, samples=32)


def v_zero(shot, fps):
    """«На табло — ноль»: close on the board, the dash flips to a burning 0."""
    dur = shot['dur']
    rng = random.Random(52)
    coll, info = arena_set(rng, zero=ev(shot, 'zero', 0.35))
    cam((2.5, 13.0, 8.0), (0.5, 34.9, 11.3), (1.8, 15.5, 8.6), (0.5, 34.9, 11.2), 26, dur)
    lib.bloom(0.35, 1.0, 7)
    return dict(fill=0.45, exposure=0.38, samples=32)


def v_laugh2(shot, fps):
    """«Все смеялись»: CJ and Cesar laugh at the hero (his point of view), the stands bob."""
    dur = shot['dur']
    rng = random.Random(53)
    coll, info = arena_set(rng, zero=0.0)
    for n, x, y, seed in (('cj', -0.55, 2.1, 2), ('cesar', 0.6, 2.35, 6)):
        p = K.load(n, coll, (x, y, 0), face((x, y), (0, 0)))
        laugh(p, 0.0, dur, seed=seed, period=0.36 + 0.02 * seed, point=(n == 'cj'))
    fans_laugh(rng, 0.07)
    cam((0.5, -0.4, 1.0), (0.15, 2.2, 1.3), (0.45, -0.1, 1.0), (0.15, 2.2, 1.35), 30, dur)
    return dict(fill=0.5, exposure=0.38, samples=32)


# ============================================================================= c13 - c16 the golem
def golem_scene(shot, rng, walk=None, crumble=None, rise=None, heading=math.pi):
    coll, info = arena_set(rng, zero=0.0)
    g = A.golem(coll, (0, 14, 0), heading, rng, scale=1.0)
    if rise is not None:
        lib.key_obj(g['root'], F(0), loc=(0, 14, -7.5))
        lib.key_obj(g['root'], F(rise), loc=(0, 14, 0))
        FX.smoke(coll, (0, 14, 0), 2.0, 0.0, rise + 0.4, rng, col='#D8BF8E', r0=4.0, n=14, rise=3.0, name='GolemDust')
    if walk:
        A.golem_walk(g, *walk)
    if crumble is not None:
        A.golem_crumble(g, crumble, rng)
    return coll, info, g


def golem_wakes(g, t):
    """The exam golem stands hunched with dim eyes; at t it straightens up, throws its arms up and the eyes flare."""
    root, ch, hd = g['root'], g['chest'], g['head']
    z0 = root.location.z
    for o, path, idx, keys in ((ch, 'rotation_euler', 0, [(0, 0.42), (t, 0.42), (t + 0.3, -0.14), (t + 0.9, -0.08)]),
                               (hd, 'rotation_euler', 0, [(0, 0.3), (t, 0.3), (t + 0.25, -0.25), (t + 0.9, -0.15)]),
                               (root, 'location', 2, [(0, z0 - 0.45), (t, z0 - 0.45), (t + 0.3, z0 + 0.1), (t + 0.6, z0)])):
        for tt, v in keys:
            getattr(o, path)[idx] = v
            o.keyframe_insert(path, index=idx, frame=F(tt))
    for side in ('L', 'R'):
        a = g['arm' + side]
        for tt, v in ((0, 0.12), (t, 0.12), (t + 0.32, -2.5), (t + 0.9, -2.35)):
            a.rotation_euler.x = v
            a.keyframe_insert('rotation_euler', index=0, frame=F(tt))
    em = bpy.data.materials.get('GolemEye')
    if em:
        st = next(n for n in em.node_tree.nodes if n.type == 'EMISSION').inputs['Strength']
        FX.key(st, [(0, 1.5), (t, 1.5), (t + 0.12, 24.0), (t + 0.5, 12.0)])
    li = bpy.data.objects.get('Golem_eyeLight')
    if li:
        for tt, v in ((0, 4.0), (t, 4.0), (t + 0.12, 300.0), (t + 0.5, 140.0)):
            li.data.energy = v
            li.data.keyframe_insert('energy', frame=F(tt))


def v_golem(shot, fps):
    """«И тут каменный голем вышел из-под контроля»: the hunched exam golem; on the word it straightens up, arms up, the
    eyes flare (no dust in front of it; the boy who drove it read as a black post at the frame edge and was dropped)."""
    dur = shot['dur']
    rng = random.Random(42)
    rise = ev(shot, 'rise', min(1.6, dur * 0.6))
    coll, info, g = golem_scene(shot, rng, heading=0.0)
    golem_wakes(g, rise)
    cam((4.6, 3.2, 0.8), (-0.4, 14, 4.0), (4.1, 4.2, 0.75), (-0.4, 14, 4.4), 23, dur)
    return dict(fill=0.45, exposure=0.38, samples=32)


def v_stands(shot, fps):
    dur = shot['dur']
    rng = random.Random(43)
    coll, info, g = golem_scene(shot, rng, walk=(0, dur, (0, 14, 0), (0, 22, 0)), heading=math.pi)
    for k in range(18):                                       # the people on the north stands run aside
        x = rng.uniform(-16, 16)
        p = S.folk((x, 36.5, 2.6), math.pi, rng, coll, rng.choice(['girl', 'kid', 'sparky', None]), height=0.9, name=f'Flee{k}')
        sp = rng.uniform(2.2, 2.8)
        P2.walk(p, sp, rng.random(), 0.9)
        x1 = x + (1 if x > 0 else -1) * sp * dur * 1.1
        lib.move_root(p, [(x, 36.5, 2.6), (x1, 36.5 + 0.8, 2.6 + 0.4)], rng.uniform(0.0, 0.3), sp)
    cam((-5.5, -1.0, 1.1), (0, 22, 4.2), (-4.6, 2.0, 1.1), (0, 24, 4.6), 28, dur)
    return dict(fill=0.45, exposure=0.38, samples=32)


def v_toward(shot, fps):
    dur = shot['dur']
    rng = random.Random(44)
    coll, info, g = golem_scene(shot, rng, walk=(0, dur, (0, 20, 0), (0, 18, 0)), heading=0.0)
    h = H.load(coll, (0, 4, 0), 0.0)
    H.walk(h, 0, dur, [(0, 4), (0, 4 + 0.9 * dur)], speed=0.9)
    cam((0.8, 2.2, 0.35), (0, 18, 6.0), (0.7, 2.6, 0.35), (0, 18, 6.2), 18, dur)
    return dict(fill=0.45, exposure=0.38, samples=32)


def v_crumble(shot, fps):
    dur = shot['dur']
    rng = random.Random(45)
    hit = ev(shot, 'hit', 0.45)
    coll, info, g = golem_scene(shot, rng, walk=(0, hit, (0, 13.2, 0), (0, 12.6, 0)), crumble=hit, heading=0.0)
    h = H.load(coll, (0, 9.5, 0), 0.0)
    H.walk(h, 0, hit, [(0, 9.5), (0, 9.5 + 0.9 * hit)], speed=0.9)
    H.key_pose(h, hit + 0.1, H.pose('stand', head=(0, -30, 0)))
    H.key_pose(h, dur, H.pose('stand', head=(0, -12, 0)))
    # the hero's radius: one thin ring on the sand runs out from him on the word (the motif of the season)
    m, s_sock, a_sock = FX.glow('RadiusRing', '#FFF2C8', 1.5, alpha=0.7)
    r = A.ring('Radius', (5.9, 5.9), (6.0, 6.0), 0.02, 0.03, m, coll)
    r.location = (0, 9.5 + 0.9 * hit, 0)
    FX.key_scale(r, [(0, 0.05), (max(0.0, hit - 0.1), 0.05), (hit + 0.3, 1.0), (dur, 1.03)])
    FX.key(a_sock, [(0, 0.0), (max(0.0, hit - 0.1), 0.7), (dur, 0.2)])
    cam((6.5, 3.0, 1.2), (0, 11.5, 3.4), (5.8, 3.8, 1.1), (0, 11.5, 2.2), 20, dur)
    return dict(fill=0.45, exposure=0.38, samples=32)


# ============================================================================= c17 - c19 Emmet
def clear_fans(inside):
    """Take the cheap egg-spectators out where the camera comes close (inside(centre) -> True): every person is two
    UV spheres of 52 verts in a Fan_ mesh, so whole spheres are deleted by their centre."""
    import bmesh
    for o in [o for o in bpy.data.objects if o.name.startswith('Fan_') and o.type == 'MESH']:
        bm = bmesh.new()
        bm.from_mesh(o.data)
        bm.verts.ensure_lookup_table()
        nv, kill = 52, []
        for j in range(len(bm.verts) // nv):
            vs = bm.verts[j * nv:(j + 1) * nv]
            c = sum((v.co for v in vs), V()) / nv
            if inside(c):
                kill.extend(vs)
        if kill:
            bmesh.ops.delete(bm, geom=kill, context='VERTS')
            bm.to_mesh(o.data)
        bm.free()


def seat_folk(rng, rows, xs, skip=(), R=(46.0, 34.0), sd=1.1, sh=0.55, name='Seat'):
    """Low-poly spectators (people2 + chibi heads) seated on the south stands, rows x xs, facing the field."""
    out = []
    for i in rows:
        rx, ry = R[0] + 0.9 + i * sd + 0.3, R[1] + 0.9 + i * sd + 0.3
        for x0 in xs:
            x = x0 + rng.uniform(-0.15, 0.15)
            if (i, round(x0, 1)) in skip or rng.random() < 0.18:
                continue
            y = -ry * math.sqrt(max(0.0, 1.0 - (x / rx) ** 2))
            z = 1.8 + (i + 1) * sh - 0.43
            p = S.folk((x, y, z), face((x, y), (0, 0)), rng, None, rng.choice(['girl', 'kid', 'sparky', None]), height=0.9,
                       name=f'{name}{i}_{len(out)}')
            P2.sit(p, rng)
            out.append(p)
    return out


def v_emmet(shot, fps):
    dur = shot['dur']
    rng = random.Random(46)
    coll, info = arena_set(rng, zero=0.0)
    sd, sh = info['step_d'], info['step_h']
    i = 5
    y = -(34.0 + 0.9 + (i + 0.55) * sd)
    z = 1.8 + (i + 1) * sh
    em = K.load('emmet', coll, (2.0, y, z - 0.45), 0.0)
    up = ev(shot, 'up', 0.5)
    # close to the camera the egg crowd looks cheap: real low-poly people sit around Emmet instead
    clear_fans(lambda c: abs(c.x - 2.0) < 4.6 and -(34.9 + 10 * sd) < c.y < -34.0)
    xs = [-2.0 + 0.9 * k for k in range(10)]
    seat_folk(rng, range(0, 10), xs, skip={(i, round(-2.0 + 0.9 * k, 1)) for i in (i,) for k in (4, 5)})
    H.key_pose(em, 0, H.pose('sit', head=(0, 10, 0)))
    H.key_root(em, 0, (2.0, y, z - 0.45))
    H.key_root(em, up, (2.0, y, z - 0.45))
    H.key_pose(em, up, H.pose('sit', head=(0, 10, 0)))
    H.key_pose(em, up + 0.7, H.pose('stand', head=(0, 12, 0)))
    H.key_root(em, up + 0.7, (2.0, y - 0.1, z))
    H.key_pose(em, dur, H.pose('stand', head=(0, 14, 0)))
    FX.aura(coll, em['rig'], '#FFE7A0', r=0.55, z=1.0, t_on=up + 0.4, strength=2.0, alpha=0.2, name='EmAura')
    c0 = V((2.0, y + 6.5, z + 0.6))
    cam(c0, (2.0, y, z + 1.4), c0 + V((-0.6, -1.2, 0.2)), (2.0, y, z + 1.6), 32, dur)
    return dict(fill=0.5, exposure=0.4, samples=32)


def v_secret(shot, fps):
    """In a blink Emmet is down on the field behind the hero (no streak or dust: one figure carries the move)."""
    dur = shot['dur']
    rng = random.Random(47)
    coll, info = arena_set(rng, zero=0.0)
    h = H.load(coll, (0, 0, 0), math.pi)
    pose_all(h, dur, H.pose('stand'))
    start = (2.0, -(34.9 + 5.55 * info['step_d']), 1.8 + 6 * info['step_h'])      # where c17 left him on the stands
    em = K.load('emmet', coll, start, 0.0)
    go = ev(shot, 'go', 0.5)
    land = (0.0, -1.6, 0.0)
    for t, p, hd in ((0, start, math.pi), (go, start, math.pi), (go + 0.25, (1.0, -16.0, 4.0), math.pi), (go + 0.45, land, math.pi),
                     (dur, land, math.pi)):
        lib.key_obj(em['rig'], F(t), loc=p, rot=(0, 0, hd), interp='LINEAR')
    H.key_pose(em, 0, H.pose('stand'))
    H.key_pose(em, go + 0.1, H.pose('crouch'))
    H.key_pose(em, go + 0.5, H.pose('crouch'))
    H.key_pose(em, go + 0.9, H.pose('stand', head=(0, 10, 0)))
    H.key_pose(em, dur, H.pose('stand', head=(0, 12, 0)))
    cam((3.0, 2.8, 2.1), (0.2, -1.2, 1.0), (2.6, 2.4, 2.0), (0.2, -1.2, 0.95), 30, dur)
    return dict(fill=0.5, exposure=0.4, samples=32)


def v_mine(shot, fps):
    dur = shot['dur']
    rng = random.Random(48)
    coll, h, em = mentor_pair(shot, rng)
    pose_all(h, dur, H.pose('stand', head=(0, 6, 0)))
    pt = ev(shot, 'point', 0.4)
    H.key_pose(em, 0, H.pose('stand', head=(0, 4, 0)))
    H.key_pose(em, pt, H.pose('point', head=(0, 4, 0)))
    H.key_pose(em, dur, H.pose('point', head=(6, 6, 0)))
    K.talk(em, pt, min(dur, pt + 1.2), rate=6, amp=0.7, seed=5)
    sl = K.load('saul', coll, (3.0, -0.5, 0.0), face((3.0, -0.5), (0, -1)))
    pose_all(sl, dur, H.pose('shrug'))
    cam((1.5, 1.9, 1.5), (0, -1.5, 1.35), (1.25, 1.5, 1.48), (0, -1.5, 1.38), 34, dur)
    return dict(fill=0.5, exposure=0.4, samples=32)


def mentor_pair(shot, rng):
    """The hero (0, 0) and Emmet (0, -1.5) face to face on the field after the golem."""
    coll, info = arena_set(rng, zero=0.0)
    h = H.load(coll, (0, 0, 0), 0.0)
    em = K.load('emmet', coll, (0.0, -1.5, 0.0), math.pi)
    return coll, h, em


def v_why(shot, fps):
    """«Почему я?» - over Emmet's shoulder on the hero, who opens his hands."""
    dur = shot['dur']
    rng = random.Random(54)
    coll, h, em = mentor_pair(shot, rng)
    q = ev(shot, 'ask', 0.2)
    H.key_pose(h, 0, H.pose('stand', head=(0, 6, 0)))
    H.key_pose(h, q, H.pose('stand', head=(0, 6, 0)))
    H.key_pose(h, q + 0.35, H.pose('shrug', head=(0, 4, 6)))
    H.key_pose(h, dur, H.pose('shrug', head=(0, 6, 4)))
    pose_all(em, dur, H.pose('stand', head=(0, -4, 0)))
    cam((0.5, -2.75, 1.62), (0, 0, 1.5), (0.42, -2.45, 1.6), (0, 0, 1.52), 40, dur)
    return dict(fill=0.5, exposure=0.4, samples=32)


def v_rule(shot, fps):
    """«Правило первое…» - over the hero's shoulder on Emmet: he raises a finger, a warm glow around him."""
    dur = shot['dur']
    rng = random.Random(55)
    coll, h, em = mentor_pair(shot, rng)
    pose_all(h, dur, H.pose('stand', head=(0, 6, 0)))
    up = ev(shot, 'rule', 0.3)
    H.key_pose(em, 0, H.pose('stand', head=(0, -4, 0)))
    H.key_pose(em, up, H.pose('stand', head=(0, -4, 0)))
    H.key_pose(em, up + 0.4, H.pose('point', arm=((24, 4), (30, 150)), fore=((18, 16), (10, 30)), head=(0, -6, 0)))
    H.key_pose(em, dur, H.pose('point', arm=((24, 4), (30, 150)), fore=((18, 16), (10, 30)), head=(4, -6, 0)))
    K.talk(em, 0.1, dur - 0.2, rate=6, amp=0.6, seed=8)
    cam((-1.15, 1.0, 1.7), (0, -1.5, 1.45), (-1.0, 0.8, 1.68), (0, -1.5, 1.46), 45, dur)
    lib.bloom(0.3, 1.0, 7)
    return dict(fill=0.5, exposure=0.4, samples=32)


# ============================================================================= c20 - c22 the evening on the steps
def seat_root(h, seat_z):
    """Root height for a sitting pose on a ledge whose top is seat_z (the root is at the soles)."""
    rig = h['rig']
    return seat_z - rig.data.bones['Hips'].head_local.z * rig.scale.z + 0.06


def steps_evening(shot, rng, coll):
    """Both sit on the edge of the plaza (top step, z = 0) at y = -36.55, facing the avenue and the sunset."""
    A.sky('sunset', sun_dir=(0.25, -0.9, 0.12))
    A.academy(coll, rng, lit=0.35, dur=shot['dur'])
    h = H.load(coll, (0.5, -36.55, 0.0), 0.0)
    em = K.load('emmet', coll, (-0.5, -36.55, 0.0), 0.0)
    for p in (h, em):
        p['rig'].location.z = seat_root(p, 0.0)
    return h, em, h['rig'].location.z


def v_evening(shot, fps):
    dur = shot['dur']
    rng = random.Random(49)
    coll = lib.collection('Academy')
    h, em, z = steps_evening(shot, rng, coll)
    pose_all(h, dur, H.pose('sit', head=(-14, 4, 0)))
    cough = ev(shot, 'cough', 1.2)
    sitc = dict(arm=((16, 30), (14, 70)), fore=((12, 70), (8, 140)))
    H.key_pose(em, 0, H.pose('sit', head=(0, 6, 0)))
    H.key_pose(em, cough - 0.1, H.pose('sit', head=(0, 6, 0)))
    H.key_pose(em, cough + 0.15, H.pose('sit', lean=26.0, head=(0, 30, 0), **sitc))
    H.key_pose(em, cough + 0.45, H.pose('sit', lean=12.0, head=(0, 18, 0), **sitc))
    H.key_pose(em, cough + 0.75, H.pose('sit', lean=26.0, head=(0, 30, 0), **sitc))
    H.key_pose(em, dur, H.pose('sit', lean=10.0, head=(0, 14, 0)))
    K.mouth(em, [(cough, 0.0), (cough + 0.1, 0.8), (cough + 0.3, 0.1), (cough + 0.65, 0.8), (cough + 0.85, 0.0)])
    cam((2.4, -40.6, z + 1.05), (0, -36.55, z + 1.15), (1.9, -40.0, z + 1.0), (0, -36.55, z + 1.18), 30, dur)
    lib.bloom(0.3, 1.0, 7)
    return dict(fill=0.4, exposure=0.42, samples=32)


def v_burn(shot, fps, alt=False):
    """Close on Emmet: embers rise off him (the power burns him) and die down when the hero moves closer.
    alt (c21b «а рядом с тобой… отдыхаю»): the calm comes at once, a wider two-shot from the front."""
    dur = shot['dur']
    rng = random.Random(50)
    coll = lib.collection('Academy')
    h, em, z = steps_evening(shot, rng, coll)
    calm = ev(shot, 'calm', 0.45 if alt else dur + 1.0)
    H.key_pose(h, 0, H.pose('sit', head=(-18, 0, 0)))
    H.key_root(h, 0, (0.5, -36.55, z))
    H.key_root(h, calm - 0.4, (0.5, -36.55, z))
    H.key_root(h, calm, (0.15, -36.55, z))
    H.key_pose(h, dur, H.pose('sit', head=(-24, 4, 0)))
    pose_all(em, dur, H.pose('sit', lean=14.0, head=(8, 16, 0)))
    K.talk(em, 0.1, calm - 0.2, rate=6, amp=0.5, seed=7)
    em_m, s_sock, a_sock = FX.glow('Ember', '#FF8A3A', 9.0, alpha=0.9)
    for k in range(70):
        e = lib.sphere(0.012, (0, 0, 0), em_m, 6, 4, name='Ember', coll=coll)
        x0, y0 = -0.5 + rng.uniform(-0.25, 0.25), -36.55 + rng.uniform(-0.15, 0.15)
        t0 = rng.uniform(-1.0, calm)
        z0 = z + rng.uniform(0.9, 1.6)
        lib.key_obj(e, F(max(0.0, t0)), loc=(x0, y0, z0 + max(0.0, -t0) * 0.85), interp='LINEAR')
        lib.key_obj(e, F(t0 + 1.4), loc=(x0 + rng.uniform(-0.2, 0.2), y0, z0 + 1.2), interp='LINEAR')
        FX.key_hide(e, [(0, True), (t0 + 1.4, False)])
    au, s = FX.aura(coll, em['rig'], '#FF9A55', r=0.5, z=0.55, strength=3.0, alpha=0.4, name='BurnAura')
    FX.key(s, [(0, 3.5), (calm - 0.2, 4.0), (calm + 0.5, 0.0), (dur, 0.0)])
    if alt:
        cam((0.3, -39.6, z + 0.95), (-0.05, -36.55, z + 1.05), (0.25, -39.0, z + 0.98), (-0.05, -36.55, z + 1.08), 32, dur)
    else:
        cam((-1.3, -38.9, z + 1.25), (-0.45, -36.55, z + 1.25), (-1.0, -38.5, z + 1.25), (-0.4, -36.55, z + 1.25), 40, dur)
    lib.bloom(0.35, 1.0, 7)
    return dict(fill=0.4, exposure=0.42, samples=32)


def v_calm(shot, fps):
    return v_burn(shot, fps, alt=True)


def v_rest(shot, fps):
    dur = shot['dur']
    rng = random.Random(51)
    coll = lib.collection('Academy')
    h, em, z = steps_evening(shot, rng, coll)
    H.key_root(h, 0, (0.15, -36.55, z))
    pose_all(h, dur, H.pose('sit', head=(-20, 2, 0)))
    pose_all(em, dur, H.pose('sit', lean=4.0, head=(-8, -6, 0)))
    cam((0.0, -42, -0.6), (0, -36.55, 0.4), (0.0, -46, -0.9), (0, -30, 4.0), 30, dur, clip=0.3)
    lib.bloom(0.35, 1.0, 7)
    return dict(fill=0.35, exposure=0.42, samples=32)


# ----------------------------------------------------------------------------- previews
def v_test_cast(shot, fps):
    coll = lib.collection('Cast')
    A.sky('day')
    lib.plane((200, 200), (0, 0, 0), lib.mat('T', '#C9C2B4'), coll=coll)
    h = H.load(coll, (0, 0, 0), 0.0)
    H.key_pose(h, 0, H.pose('stand'))
    for k, n in enumerate(['denise', 'cj', 'emmet', 'cesar', 'saul']):
        p = K.load(n, coll, ((k - 2) * 1.0 + (0.5 if k >= 2 else -0.5) * 1.0, 0.6, 0), 0.0)
        H.key_pose(p, 0, H.pose('stand'))
    cam((0, -7.0, 1.2), (0, 0, 0.95), lens=40, dur=shot['dur'])
    return dict(fill=0.5, exposure=0.35, samples=32)
