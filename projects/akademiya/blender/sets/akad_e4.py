"""Episode 4 «Пять утра»: a month of dawns on the scrap beach behind the Academy. The hero drags scrap and squeezes his
circle (his radius, the season's one shape) from six metres down to a palm; CJ jogs past and laughs, Denise stops time so
he sleeps ten more seconds, Emmet silently carries iron next to him; rule two; CJ throws a glove.
Times inside a shot come from shot['events'] (tools/build_timeline.py), with defaults for a dry run.
"""
import math
import random

import bpy
from mathutils import Vector as V

import akad as A
import akad_e3 as E3
import cast as K
import lib
import pcommon as pc
import people2 as P2
import sila as S
import sila_fx as FX
import sila_hero as H

F = lib.sec2f
ev = A._ev
cam = E3.cam
face = E3.face
pose_all = E3.pose_all

SHORE = 9.0           # the waterline (y); the sea is +y, the Academy cliff is -y; the sun rises over the sea


# ----------------------------------------------------------------------------- the beach
def rust_mats():
    return dict(rust=lib.mat('Rust', '#7B4A2C', rough=0.92, var=0.35, var_scale=2.0, bump=0.35, bump_scale=9),
                iron=lib.mat('Iron', '#5D5A57', rough=0.7, metal=0.6, var=0.25, var_scale=3.0, bump=0.2, bump_scale=12),
                white=lib.mat('FridgeWhite', '#E7E2D6', rough=0.45, var=0.18, var_scale=1.5, bump=0.12, bump_scale=6),
                blue=lib.mat('BarrelBlue', '#2F5D8C', rough=0.6, var=0.25, var_scale=2.0),
                tyre=lib.mat('Tyre', '#151414', rough=0.85),
                glass=lib.mat('WreckGlass', '#1E2328', rough=0.25, spec=0.6))


def fridge(coll, loc, rot, m, name='Fridge'):
    o = lib.box((0.7, 0.66, 1.7), loc, m['white'], rot=rot, bevel=0.05, name=name, coll=coll, origin='bottom')
    h = lib.box((0.04, 0.05, 0.5), (0.26, -0.35, 1.15), m['iron'], bevel=0.01, name=name + 'Handle', coll=coll)
    h.parent = o
    return o


def wreck(coll, loc, heading, rng, m, name='Wreck'):
    root = lib.empty(name, loc, (rng.uniform(-0.08, 0.08), rng.uniform(-0.1, 0.1), heading), coll=coll)
    body = lib.box((4.2, 1.8, 0.7), (0, 0, 0.35), m['rust'], bevel=0.05, name=name + 'Body', coll=coll, origin='bottom')
    cab = lib.box((2.1, 1.62, 0.55), (-0.25, 0, 1.05), m['rust'], bevel=0.06, name=name + 'Cab', coll=coll, origin='bottom')
    win = lib.box((2.0, 1.66, 0.38), (-0.25, 0, 1.12), m['glass'], bevel=0.03, name=name + 'Win', coll=coll, origin='bottom')
    parts = [body, cab, win]
    for sx in (-1.4, 1.4):
        for sy in (-0.85, 0.85):
            if rng.random() < 0.7:
                parts.append(lib.cyl(0.33, 0.22, (sx, sy, 0.3), m['tyre'], rot=(math.pi / 2, 0, 0), verts=16, name=name + 'Tyre',
                                     coll=coll))
    for p in parts:
        p.parent = root
    return root


def scrap(coll, rng, box=((-26, 26), (-9, 9)), n=70, keep=None, name='Scrap'):
    """Heaps of scrap: fridges, car wrecks, rails, barrels, tyres. keep(x, y) -> False drops a piece (the beach clears)."""
    m = rust_mats()
    out = []
    heaps = [(rng.uniform(*box[0]), rng.uniform(*box[1])) for _ in range(9)]
    for k in range(n):
        hx, hy = heaps[k % len(heaps)]
        x, y = hx + rng.gauss(0, 2.2), hy + rng.gauss(0, 1.6)
        kind = rng.choices(('fridge', 'wreck', 'rail', 'barrel', 'tyre'), (4, 1, 3, 3, 3))[0]
        hd = rng.uniform(0, math.tau)
        if keep and not keep(x, y):
            continue
        if kind == 'fridge':
            lie = rng.random() < 0.6
            o = fridge(coll, (x, y, 0.33 if lie else 0.0), (math.pi / 2 if lie else rng.uniform(-0.15, 0.15), 0, hd), m,
                       name=f'{name}Fridge')
        elif kind == 'wreck':
            o = wreck(coll, (x, y, 0.0), hd, rng, m, name=f'{name}Wreck')
        elif kind == 'rail':
            o = lib.box((rng.uniform(4.0, 7.0), 0.16, 0.18), (x, y, 0.09 + rng.uniform(0, 0.4)), m['iron'],
                        rot=(0, rng.uniform(-0.12, 0.12), hd), bevel=0.02, name=f'{name}Rail', coll=coll)
        elif kind == 'barrel':
            lie = rng.random() < 0.5
            o = lib.cyl(0.3, 0.9, (x, y, 0.3 if lie else 0.45), rng.choice((m['rust'], m['blue'])),
                        rot=(math.pi / 2 if lie else 0, 0, hd), verts=18, bevel=0.02, name=f'{name}Barrel', coll=coll)
        else:
            o = lib.cyl(0.36, 0.22, (x, y, 0.11), m['tyre'], rot=(0, 0, hd), verts=18, bevel=0.03, name=f'{name}Tyre', coll=coll)
        out.append(o)
    return out


def sea(coll, dur):
    """The sea from the waterline to the horizon, gentle waves (noise bump) and a strip of foam that runs in and out."""
    w = lib.mat('Sea', '#1F5677', rough=0.08, spec=0.8, bump=0.35, bump_scale=0.9, var=0.2, var_scale=0.04)
    lib.plane((1200, 900), (0, SHORE + 450, -0.06), w, name='Sea', coll=coll)
    wet = lib.mat('WetSand', '#B59C74', rough=0.35, spec=0.6)
    lib.plane((1200, 4.0), (0, SHORE - 1.0, -0.02), wet, name='WetSand', coll=coll)
    fm, _, fa = FX.glow('FoamMat', '#F4F1EA', 0.6, alpha=0.75)
    foam = lib.box((1200, 0.9, 0.02), (0, SHORE, -0.01), fm, bevel=0, name='Foam', coll=coll)
    lib.add_sine(foam, 'location', 1, 1.1, 3.2, 0.0)
    return foam


def beach(coll, rng, kind='morning', dur=4.0, scrap_n=70, keep=None):
    """Dawn on the scrap beach: sand, the sea with the low sun, the Academy towers on the cliff behind."""
    if kind == 'morning':                                     # dawn over the sea: clearer than the arena morning
        d = (0.55, 0.8, 0.16)
        lib.world_color('#000000', 0.0)
        pc.day_sky(d, top='#3A72BE', horizon='#F6BE84', below='#8F8576', strength=0.95, glow='#FFC98A', fog=0.0,
                   fog_col='#E9CFAE', glow_size=0.04, glow_strength=0.9)
        sun = pc.sun(d, 4.0, '#FFCF94', 1.2, name='AkSun')
    else:                                                     # sunset over the sea, a small sun disc instead of a haze
        d = (0.6, 0.78, 0.1)
        lib.world_color('#000000', 0.0)
        pc.day_sky(d, top='#34508C', horizon='#F59E62', below='#5C4A4E', strength=0.9, glow='#FF9A55', fog=0.0,
                   fog_col='#B98E86', glow_size=0.05, glow_strength=1.2)
        sun = pc.sun(d, 2.6, '#FF9E62', 1.5, name='AkSun')
    sand = lib.mat('BeachSand', '#DCC39A', rough=0.95, var=0.12, var_scale=0.35, bump=0.12, bump_scale=28)
    lib.plane((1200, 400), (0, SHORE - 200, 0.0), sand, name='Beach', coll=coll)
    sea(coll, dur)
    gm = A.glass_mat('AkGlass0')
    white = lib.mat('AkWhite', '#EEEBE4', rough=0.55)
    cliff = lib.mat('Cliff', '#A8957A', rough=0.95, var=0.2, var_scale=0.08, bump=0.3, bump_scale=3)
    for k in range(14):                                       # a low rocky cliff under the Academy
        lib.sphere(rng.uniform(9, 16), (-130 + 20 * k + rng.uniform(-5, 5), -72 + rng.uniform(-4, 4), -4.0), cliff, 14, 9,
                   scale=(1.4, 0.8, 0.55), name='Cliff', coll=coll)
    A.tower(coll, -26, -12, -100, -86, 64, gm, white, 'BeachTowerL')
    A.tower(coll, 10, 24, -100, -86, 64, gm, white, 'BeachTowerR')
    lib.box((16, 8, 6), (-1, -93, 46), gm, bevel=0.1, name='BeachBridge', coll=coll, origin='bottom')
    pieces = scrap(coll, rng, n=scrap_n, keep=keep) if scrap_n else []
    return sun, pieces


def circle(coll, center, keys, name='Radius'):
    """The hero's circle on the sand (one thin line). keys [(t, radius m)]; alpha follows the radius > 0."""
    m, s_sock, a_sock = FX.glow(name + 'Mat', '#FFF2C8', 1.5, alpha=0.75)
    r = A.ring(name, (0.97, 0.97), (1.0, 1.0), 0.02, 0.03, m, coll, n=128)
    r.location = center
    FX.key_scale(r, [(t, (max(rad, 0.01), max(rad, 0.01), 1.0)) for t, rad in keys])
    return r, a_sock


# ----------------------------------------------------------------------------- helpers
def clear_zone(*zones):
    """keep(x, y) for scrap(): no piece inside any circle (cx, cy, r) - room for the actors and the camera."""
    return lambda x, y: all(math.hypot(x - cx, y - cy) > r for cx, cy, r in zones)


def carry_with(ob, rig):
    """Parent a prop to a rig object keeping its world placement (it then follows the rig's root keys)."""
    bpy.context.view_layer.update()
    mw = ob.matrix_world.copy()
    ob.parent = rig
    ob.matrix_parent_inverse = rig.matrix_world.inverted()
    ob.matrix_world = mw


def push_pose(lean=26.0):
    return H.pose('stand', arm=(14, 78), fore=(8, 86), lean=lean, head=(0, -14, 0))


def eyes_closed(h, t0=0.0):
    H._key_prop(h['body'], 'eye_blink', t0, 1.0, 'CONSTANT')


def lie_on_back(h, loc, heading=0.0):
    """The hero lies on the sand, face up (the rig is tipped back about its feet, then lowered)."""
    rig = h['rig']
    rig.rotation_mode = 'XYZ'
    rig.rotation_euler = (-math.pi / 2, 0, heading)
    rig.location = (loc[0], loc[1], 0.17)
    for i in range(3):
        rig.keyframe_insert('rotation_euler', index=i, frame=1)
    rig.keyframe_insert('location', frame=1)


def gull(coll, path, t0, t1, stop=None, name='Gull'):
    """A white gull gliding along path [(x, y, z) ...]; stop=t freezes it there (Denise stops time)."""
    m = lib.mat('GullWhite', '#F2F0EA', rough=0.6)
    root = lib.empty(name, path[0], coll=coll)
    body = lib.sphere(0.12, (0, 0, 0), m, 12, 8, scale=(0.6, 1.6, 0.6), name=name + 'Body', coll=coll)
    body.parent = root
    for sx in (-1, 1):
        w = lib.box((0.42, 0.14, 0.015), (sx * 0.24, 0, 0.02), m, bevel=0, name=name + 'Wing', coll=coll)
        w.parent = root
        if stop is None:
            lib.add_sine(w, 'rotation_euler', 1, 0.35 * sx, 0.5, 0.0)
    n = len(path) - 1
    for j, pnt in enumerate(path):
        t = t0 + (t1 - t0) * j / n
        if stop is not None and t > stop:
            break
        lib.key_obj(root, F(t), loc=pnt, rot=(0, 0, math.atan2(path[-1][0] - path[0][0], -(path[-1][1] - path[0][1]))),
                    interp='LINEAR')
    return root


def beach_shot(shot, seed, kind='morning', zones=((0, 0, 6.0),), scrap_n=70):
    rng = random.Random(seed)
    coll = lib.collection('Beach')
    beach(coll, rng, kind=kind, dur=shot['dur'], scrap_n=scrap_n, keep=clear_zone(*zones))
    return coll, rng


# ============================================================================= d00 hook: a month of hauling junk
def v_haul(shot, fps):
    """«Месяц в Академии героев я таскал мусор»: he pushes a fridge across the sand at dawn, the sun behind him."""
    dur = shot['dur']
    coll, rng = beach_shot(shot, 61, zones=((0, 0, 5.0), (-3, -4, 3.0)))
    m = rust_mats()
    fr = fridge(coll, (0.45, -1.6 + 0.58, 0.0), (0, 0, math.pi), m, name='HaulFridge')
    h = H.load(coll, (0.45, -1.6, 0), math.pi)
    carry_with(fr, h['rig'])
    H.walk(h, 0, dur, [(0.45, -1.6), (0.45, -1.6 + 0.45 * dur)], speed=0.45, A=14.0, base=push_pose(), arms=False)
    cam((-3.0, -1.8, 0.9), (0.45, -0.9, 0.85), (-3.0, -0.4, 0.9), (0.45, 0.5, 0.85), 26, dur)
    return dict(fill=0.45, exposure=0.0, samples=32)


def v_lesson(shot, fps):
    """«И это был мой первый урок»: Emmet sits on a wreck in front, watching; the hero far behind with his fridge."""
    dur = shot['dur']
    coll, rng = beach_shot(shot, 62, zones=((0, 0, 7.0),))
    m = rust_mats()
    for k in range(3):                                        # he sits on a stack of rails
        lib.box((2.4, 0.17, 0.17), (-1.0, -2.8 + 0.17 * (k - 1), 0.085 + 0.17 * (k % 2)), m['iron'], rot=(0, 0, 0.3), bevel=0.02,
                name='SeatRail', coll=coll)
    em = K.load('emmet', coll, (-1.0, -2.75, 0), math.pi * 0.9)
    em['rig'].location.z = E3.seat_root(em, 0.34)
    pose_all(em, dur, H.pose('sit', head=(0, 10, 0)))
    fr = fridge(coll, (2.0, 3.98, 0.0), (0, 0, math.pi), m, name='FarFridge')
    h = H.load(coll, (2.0, 3.4, 0), math.pi)
    carry_with(fr, h['rig'])
    H.walk(h, 0, dur, [(2.0, 3.4), (2.0, 3.4 + 0.4 * dur)], speed=0.4, A=14.0, base=push_pose(), arms=False)
    cam((-1.9, -5.0, 1.5), (1.2, 3.0, 0.8), (-1.8, -4.7, 1.48), (1.2, 3.2, 0.8), 28, dur)
    return dict(fill=0.45, exposure=0.0, samples=32)


# ============================================================================= d01 - d03 the beach
def v_dawn(shot, fps):
    """«Пять утра. Пляж за Академией»: wide - the scrap beach, the sea with the low sun, the Academy on the cliff."""
    dur = shot['dur']
    coll, rng = beach_shot(shot, 63, zones=((0, -20, 4.0),), scrap_n=110)
    cam((-6.0, -16.0, 3.2), (2.0, 2.0, 0.5), (-5.0, -14.0, 2.8), (2.0, 2.0, 0.8), 24, dur)
    return dict(fill=0.3, exposure=0.0, samples=32)


def v_heaps(shot, fps):
    """«Тридцать лет туда свозили старое железо»: a low dolly along a heap."""
    dur = shot['dur']
    coll, rng = beach_shot(shot, 64, zones=((0, -9, 3.0),), scrap_n=0)
    scrap(coll, random.Random(640), box=((-6, 6), (-2, 3)), n=55)
    cam((-5.0, -6.5, 0.8), (-2.0, 0.5, 0.9), (3.5, -6.0, 0.9), (2.0, 0.5, 1.0), 26, dur)
    return dict(fill=0.45, exposure=0.0, samples=32)


def v_junk(shot, fps):
    """«Холодильники, машины, рельсы»: the camera slides past a fridge, a wreck and a pile of rails, one per word."""
    dur = shot['dur']
    coll, rng = beach_shot(shot, 65, zones=((0, 0, 12.0),), scrap_n=60)
    m = rust_mats()
    fridge(coll, (-3.0, 0.6, 0.0), (0, 0, 0.3), m, name='JFridge')
    fridge(coll, (-2.2, 1.4, 0.33), (math.pi / 2, 0, 1.2), m, name='JFridge2')
    wreck(coll, (0.6, 1.4, 0), 0.4, random.Random(7), m, name='JWreck')
    for k in range(6):
        lib.box((6.0, 0.16, 0.18), (4.6, 0.8 + 0.1 * k, 0.09 + 0.18 * (k % 3)), m['iron'], rot=(0, 0, 0.15 + 0.05 * k), bevel=0.02,
                name='JRail', coll=coll)
    cam((-4.6, -3.6, 1.4), (-2.8, 1.0, 0.8), (4.4, -3.4, 1.1), (4.6, 1.0, 0.3), 28, dur)
    return dict(fill=0.45, exposure=0.0, samples=32)


# ============================================================================= d04 - d05b the circle and the order
def v_circle6(shot, fps):
    """«Мой круг гасит любую силу рядом. Сейчас он шесть метров»: the ring runs out from him to six metres."""
    dur = shot['dur']
    coll, rng = beach_shot(shot, 66, zones=((0, 0, 8.0),))
    h = H.load(coll, (0, 0, 0), 0.0)
    pose_all(h, dur, H.pose('stand', arm=(30, 10), fore=(30, 20), head=(0, 10, 0)))
    t = ev(shot, 'ring', 0.4)
    r, a = circle(coll, (0, 0, 0), [(0, 0.05), (t, 0.05), (t + 0.5, 6.0), (dur, 6.0)])
    FX.key(a, [(0, 0.0), (t, 0.0), (t + 0.1, 0.75), (dur, 0.75)])
    cam((1.2, -3.0, 1.2), (0, 0, 0.6), (3.0, -9.5, 7.5), (0, 0.5, 0.0), 26, dur)
    return dict(fill=0.45, exposure=0.0, samples=32)


def mentor_beach(shot, seed):
    coll, rng = beach_shot(shot, seed, zones=((0, 0, 6.0),))
    h = H.load(coll, (0.55, 0, 0), -0.25)
    em = K.load('emmet', coll, (-0.55, 0.1, 0), 0.3)
    return coll, rng, h, em


def v_order(shot, fps):
    """«Эммет сказал: Расчисти пляж»: Emmet points down the beach at the heaps, the hero follows his hand."""
    dur = shot['dur']
    coll, rng, h, em = mentor_beach(shot, 67)
    pose_all(h, dur, H.pose('stand', head=(0, 4, -10)))
    pt = ev(shot, 'point', 0.4)
    H.key_pose(em, 0, H.pose('stand'))
    H.key_pose(em, pt, H.pose('stand'))
    H.key_pose(em, pt + 0.35, H.pose('point', head=(0, -4, 0)))
    H.key_pose(em, dur, H.pose('point', head=(0, -4, 0)))
    K.talk(em, 0.1, dur - 0.1, rate=6, amp=0.55, seed=11)
    cam((1.2, -4.0, 1.1), (0, 0.5, 1.15), (1.0, -3.4, 1.1), (0, 0.5, 1.2), 32, dur)
    return dict(fill=0.5, exposure=0.0, samples=32)


def v_palm(shot, fps):
    """«И сожми его до ладони»: close on Emmet's open palm raised in front of him."""
    dur = shot['dur']
    coll, rng, h, em = mentor_beach(shot, 68)
    pose_all(h, dur, H.pose('stand', head=(0, -6, -10)))
    H.key_pose(em, 0, H.pose('stand', head=(0, 4, 0)))
    H.key_pose(em, 0.35, H.pose('stand', arm=((24, 4), (10, 95)), fore=((18, 16), (4, 120)), head=(0, 6, 0)))
    H.key_pose(em, dur, H.pose('stand', arm=((24, 4), (10, 98)), fore=((18, 16), (4, 124)), head=(0, 6, 0)))
    K.talk(em, 0.1, dur - 0.1, rate=6, amp=0.55, seed=12)
    cam((0.9, -1.6, 1.45), (-0.5, 0.0, 1.35), (0.8, -1.35, 1.45), (-0.5, 0.0, 1.38), 38, dur)
    return dict(fill=0.5, exposure=0.0, samples=32)


# ============================================================================= d06 - d09 the failing week
def v_cantmove(shot, fps):
    """«Первую неделю я не мог сдвинуть холодильник»: he pushes an upright fridge, his feet slide, it does not move."""
    dur = shot['dur']
    coll, rng = beach_shot(shot, 69, zones=((0, 0, 5.0),))
    m = rust_mats()
    fridge(coll, (0, 0.62, 0), (0, 0, 0), m, name='StuckFridge')
    h = H.load(coll, (0, -0.02, 0), math.pi)
    for k in range(int(dur / 0.5) + 1):
        t = k * 0.5
        H.key_pose(h, t, push_pose(lean=30.0 + 6 * (k % 2)) | dict(thigh=(10.0 if k % 2 else -30.0, -30.0 if k % 2 else 10.0)))
        H.key_root(h, t, (0, -0.02 - 0.06 * (k % 2), 0), math.pi)
    cam((2.4, 0.6, 0.7), (0, 0.2, 0.8), (2.1, 0.2, 0.7), (0, 0.2, 0.8), 30, dur)
    return dict(fill=0.5, exposure=0.0, samples=32)


def v_jog(shot, fps):
    """«Си-Джей бегал мимо и смеялся»: CJ jogs along the waterline towards us, laughing; the hero small by his fridge."""
    dur = shot['dur']
    coll, rng = beach_shot(shot, 70, zones=((0, 4, 6.0),))
    cj = K.load('cj', coll, (-6.0, 6.5, 0), math.pi / 2)
    H.walk(cj, 0, dur, [(-6.0, 6.5), (6.0, 6.5)], speed=3.2, A=34.0,
           base=H.pose('stand', arm=(18, 20), fore=(30, 90), lean=8.0, head=(0, -14, 0)))
    K.talk(cj, 0.2, dur, rate=9, amp=0.9, seed=4)
    m = rust_mats()
    fridge(coll, (1.5, 1.6, 0), (0, 0, 0.2), m, name='HFridge')
    h = H.load(coll, (1.5, 0.95, 0), math.pi * 0.9)
    pose_all(h, dur, push_pose(lean=30.0))
    cam((4.0, 3.0, 1.0), (-1.0, 6.5, 1.0), (4.0, 3.4, 1.0), (2.5, 6.5, 1.0), 30, dur)
    return dict(fill=0.5, exposure=0.0, samples=32)


def v_mock(shot, fps):
    """«Ноль тренируется!»: CJ close, jogging on the spot, points at the hero and laughs."""
    dur = shot['dur']
    coll, rng = beach_shot(shot, 71, zones=((0, 0, 6.0),))
    cj = K.load('cj', coll, (0, 1.6, 0), 0.0)
    E3.laugh(cj, 0.0, dur, seed=5, period=0.32, point=True)
    for k in range(int(dur / 0.16) + 1):                          # jogging on the spot: a small bounce
        H.key_root(cj, k * 0.16, (0, 1.6, 0.04 * (k % 2)))
    cam((0.3, -1.0, 1.1), (0, 1.6, 1.35), (0.25, -0.8, 1.1), (0, 1.6, 1.38), 32, dur)
    return dict(fill=0.5, exposure=0.0, samples=32)


def v_fizzle(shot, fps):
    """«Круг не сжимался. Он просто гас»: arms out, he squeezes; the ring wobbles at six metres and goes out."""
    dur = shot['dur']
    coll, rng = beach_shot(shot, 72, zones=((0, 0, 8.0),))
    h = H.load(coll, (0, 0, 0), 0.0)
    out = ev(shot, 'out', dur * 0.6)
    H.key_pose(h, 0, H.pose('stand', arm=(20, 80), fore=(16, 90), lean=4.0, head=(0, 10, 0)))
    H.key_pose(h, out, H.pose('stand', arm=(22, 86), fore=(10, 96), lean=8.0, head=(0, 16, 0)))
    H.key_pose(h, out + 0.4, H.pose('stand', arm=(24, 10), fore=(18, 20), lean=0.0, head=(0, 24, 0)))
    H.key_pose(h, dur, H.pose('stand', arm=(24, 6), fore=(18, 18), head=(0, 26, 0)))
    keys = [(0, 6.0)] + [(0.25 + 0.25 * k, 6.0 - (0.5 if k % 2 == 0 else 0.0) - 0.15 * k) for k in range(int(out / 0.25))]
    r, a = circle(coll, (0, 0, 0), keys + [(dur, keys[-1][1])])
    FX.key(a, [(0, 0.75), (out - 0.05, 0.75), (out + 0.05, 0.15), (out + 0.12, 0.6), (out + 0.2, 0.0), (dur, 0.0)])
    cam((2.5, -7.5, 5.0), (0, 0, 0.3), (2.2, -6.8, 4.4), (0, 0, 0.4), 26, dur)
    return dict(fill=0.45, exposure=0.0, samples=32)


def v_asleep(shot, fps):
    """«На десятый день я уснул прямо на песке»: top-down, he lies on his back by the fridge, eyes shut."""
    dur = shot['dur']
    coll, rng = beach_shot(shot, 73, zones=((0, 0, 4.0),))
    m = rust_mats()
    fridge(coll, (-0.75, 0.2, 0.33), (math.pi / 2, 0, 0.1), m, name='SleepFridge')
    h = H.load(coll, (0.3, -0.5, 0), 0.0)
    H.key_pose(h, 0, H.pose('stand', arm=(40, 8), fore=(46, 4), head=(0, -4, 10)))
    lie_on_back(h, (0.3, -0.5), heading=0.3)
    eyes_closed(h)
    cam((0.6, 0.0, 4.2), (0.3, 0.1, 0.0), (0.55, 0.05, 3.4), (0.3, 0.1, 0.0), 30, dur)
    return dict(fill=0.45, exposure=0.0, samples=32)


# ============================================================================= d10 - d14 Emmet works next to him
def v_silent(shot, fps):
    """«Эммет ничего не сказал»: low, from the sleeper's head: Emmet stands over him against the dawn sky."""
    dur = shot['dur']
    coll, rng = beach_shot(shot, 74, zones=((0, 0, 4.0),))
    h = H.load(coll, (0.0, 0.0, 0), 0.0)
    H.key_pose(h, 0, H.pose('stand', arm=(40, 8), fore=(46, 4)))
    lie_on_back(h, (0.0, 0.0), heading=math.pi / 2)
    eyes_closed(h)
    em = K.load('emmet', coll, (1.3, 0.6, 0), face((1.3, 0.6), (0, 0)))
    pose_all(em, dur, H.pose('stand', head=(0, 26, 0)))
    cam((-0.2, -1.3, 0.3), (1.3, 0.6, 1.3), (-0.15, -1.2, 0.32), (1.3, 0.6, 1.35), 24, dur)
    return dict(fill=0.5, exposure=0.0, samples=32)


def rail_between(coll, a, b, z, m, name='CarryRail'):
    d = V(b) - V(a)
    mid = (V(a) + V(b)) / 2
    return lib.box((d.length + 1.4, 0.14, 0.16), (mid.x, mid.y, z), m['iron'], rot=(0, 0, math.atan2(d.y, d.x)), bevel=0.02,
                   name=name, coll=coll)


def v_together(shot, fps):
    """«Он встал рядом и тоже взял железо»: Emmet and the hero carry a rail together, one at each end."""
    dur = shot['dur']
    coll, rng = beach_shot(shot, 75, zones=((0, 0, 7.0),))
    m = rust_mats()
    carry = H.pose('stand', arm=((26, 30), (26, 30)), fore=((20, 60), (20, 60)), lean=6.0)
    y0, sp = -2.0, 0.55
    h = H.load(coll, (-1.6, y0, 0), 0.0)
    em = K.load('emmet', coll, (1.6, y0, 0), 0.0)
    rail = rail_between(coll, (-1.6, y0), (1.6, y0), 0.66, m)
    lift = 0.5
    H.key_pose(h, 0, H.pose('crouch'))
    H.key_pose(em, 0, H.pose('crouch'))
    lib.key_obj(rail, F(0), loc=(0, y0, 0.12))
    lib.key_obj(rail, F(lift), loc=(0, y0, 0.66))
    for p in (h, em):
        H.key_pose(p, lift, carry)
    t_end = dur
    H.walk(h, lift, t_end, [(-1.6, y0), (-1.6, y0 - sp * (t_end - lift))], speed=sp, A=14.0, base=carry, arms=False)
    H.walk(em, lift, t_end, [(1.6, y0), (1.6, y0 - sp * (t_end - lift))], speed=sp, A=12.0, base=carry, arms=False, phase=0.5)
    lib.key_obj(rail, F(t_end), loc=(0, y0 - sp * (t_end - lift), 0.66))
    cam((3.6, -7.0, 1.3), (0, -2.5, 0.8), (3.2, -7.4, 1.25), (0, -3.2, 0.8), 28, dur)
    return dict(fill=0.5, exposure=0.0, samples=32)


def v_days(shot, fps):
    """«Каждый день. В пять утра»: a time-lapse from above - the sun swings, shadows sweep, the heaps melt away."""
    dur = shot['dur']
    rng = random.Random(76)
    coll = lib.collection('Beach')
    sun, pieces = beach(coll, rng, dur=dur, scrap_n=110, keep=clear_zone((0, -20, 4.0)))
    order = sorted(pieces, key=lambda o: rng.random())
    for k, o in enumerate(order):
        t = 0.2 + (dur - 0.5) * k / max(1, len(order))
        for c in [o] + list(o.children):
            FX.key_hide(c, [(0, False), (t, True)])
    d0, d1 = V((0.55, 0.8, 0.16)), V((-0.6, 0.7, 0.35))
    for t, d in ((0, d0), (dur, d1)):
        sun.rotation_euler = (-d.normalized()).to_track_quat('-Z', 'Y').to_euler()
        sun.keyframe_insert('rotation_euler', frame=F(t))
    cam((-6.0, -16.0, 3.2), (2.0, 2.0, 0.5), (-5.8, -15.6, 3.1), (2.0, 2.0, 0.5), 24, dur)
    return dict(fill=0.3, exposure=0.0, samples=32)


def v_empty(shot, fps):
    """«Через месяц пляж был пустой»: the clean beach, the hero alone in the middle; the camera rises."""
    dur = shot['dur']
    coll, rng = beach_shot(shot, 77, scrap_n=0)
    h = H.load(coll, (0, 0, 0), math.pi * 0.85)
    pose_all(h, dur, H.pose('stand', head=(0, -4, 0)))
    cam((2.0, -5.0, 1.2), (0, 2.0, 0.8), (6.0, -16.0, 9.0), (0, 2.0, 0.0), 24, dur)
    return dict(fill=0.4, exposure=0.0, samples=32)


def v_palmring(shot, fps):
    """«А круг сжался до ладони»: his raised palm; the ring, now palm-sized, closes round it."""
    dur = shot['dur']
    coll, rng = beach_shot(shot, 78, scrap_n=0)
    h = H.load(coll, (0, 0, 0), 0.0)
    up = H.pose('stand', arm=((24, 4), (14, 100)), fore=((18, 16), (6, 130)), head=(0, -12, 0))
    H.key_pose(h, 0, H.pose('stand'))
    H.key_pose(h, 0.3, up)
    H.key_pose(h, dur, up)
    bpy.context.scene.frame_set(F(0.3) + 2)
    bpy.context.view_layer.update()
    rig = h['rig']
    hand = rig.matrix_world @ rig.pose.bones['RightHand'].tail
    t = ev(shot, 'shrink', 0.35)
    r, a = circle(coll, (hand.x, hand.y - 0.02, hand.z + 0.06), [(0, 1.6), (t, 1.6), (t + 0.55, 0.14), (dur, 0.13)])
    r.rotation_euler = (math.pi / 2, 0, 0)                    # upright, round the palm, facing us
    FX.key(a, [(0, 0.0), (t - 0.05, 0.0), (t + 0.05, 0.8), (dur, 0.8)])
    cam((0.25, -1.3, 1.0), (hand.x, hand.y, hand.z), (0.2, -1.1, 1.0), (hand.x, hand.y, hand.z), 36, dur)
    return dict(fill=0.5, exposure=0.0, samples=32)


# ============================================================================= d15 - d17 his own people
def v_denise(shot, fps):
    """«Дениз приходила каждое утро»: Denise walks over the sand to the hero dozing against a fridge."""
    dur = shot['dur']
    coll, rng = beach_shot(shot, 79, zones=((0, 0, 7.0),))
    m = rust_mats()
    fridge(coll, (0.0, 0.9, 0.0), (0, 0, math.pi), m, name='LeanFridge')
    h = H.load(coll, (0.0, 0.25, 0), 0.0)
    h['rig'].location.z = E3.seat_root(h, 0.0) - 0.05
    pose_all(h, dur, H.pose('sit', thigh=70.0, shin=-40.0, head=(0, 22, 10)))
    eyes_closed(h)
    dn = K.load('denise', coll, (-4.5, -2.5, 0), 0.0)
    H.walk(dn, 0, dur, [(-4.5, -2.5), (-1.1, -0.4)], speed=1.1, A=20.0)
    cam((2.6, -3.6, 1.0), (-1.2, -0.6, 0.9), (2.3, -3.2, 1.0), (-0.8, -0.3, 0.9), 28, dur)
    return dict(fill=0.5, exposure=0.0, samples=32)


def v_sleep10(shot, fps):
    """«Останавливала время, чтобы я поспал ещё десять секунд»: she lifts a hand, the foam and a gull stop, he sleeps."""
    dur = shot['dur']
    coll, rng = beach_shot(shot, 80, zones=((0, 0, 7.0),))
    m = rust_mats()
    fridge(coll, (0.0, 0.9, 0.0), (0, 0, math.pi), m, name='LeanFridge')
    h = H.load(coll, (0.0, 0.25, 0), 0.0)
    h['rig'].location.z = E3.seat_root(h, 0.0) - 0.05
    pose_all(h, dur, H.pose('sit', thigh=70.0, shin=-40.0, head=(0, 22, 10)))
    eyes_closed(h)
    stop = ev(shot, 'stop', 0.4)
    dn = K.load('denise', coll, (-1.1, -0.5, 0), face((-1.1, -0.5), (0, 0.25)))
    H.key_pose(dn, 0, H.pose('stand', head=(0, 14, 0)))
    H.key_pose(dn, stop - 0.15, H.pose('stand', head=(0, 14, 0)))
    H.key_pose(dn, stop + 0.15, H.pose('point', head=(0, 10, 0)))
    H.key_pose(dn, dur, H.pose('point', head=(0, 12, 0)))
    foam = bpy.data.objects.get('Foam')
    if foam:                                                  # the waves stop where they are
        foam.animation_data_clear()
        t = 0.0
        while True:
            foam.location.y = SHORE + 1.1 * math.sin(math.tau * min(t, stop) / 3.2)
            foam.keyframe_insert('location', index=1, frame=F(t))
            if t >= stop:
                break
            t = min(stop, t + 0.2)
    gull(coll, [(-8, 6, 3.0), (-2, 5, 3.4), (4, 4.6, 3.2), (10, 4.0, 3.0)], 0.0, 3.0, stop=stop)
    cam((2.2, -2.6, 1.2), (-0.4, 0.3, 0.9), (2.0, -2.3, 1.2), (-0.4, 0.3, 0.9), 28, dur)
    return dict(fill=0.5, exposure=0.0, samples=32)


def v_alone(shot, fps):
    """«Я тоже так начинал. Один. Сорок лет назад»: from behind, both sit on a wreck facing the sun over the sea."""
    dur = shot['dur']
    coll, rng = beach_shot(shot, 81, zones=((0, 0, 7.0),), scrap_n=0)
    m = rust_mats()
    for k in range(3):                                        # a stack of rails as a bench
        lib.box((2.6, 0.17, 0.17), (0, 2.0 + 0.17 * (k - 1), 0.085 + 0.17 * (k % 2)), m['iron'], rot=(0, 0, 0.02 * k), bevel=0.02,
                name='BenchRail', coll=coll)
    em = K.load('emmet', coll, (-0.5, 2.05, 0), math.pi)
    h = H.load(coll, (0.45, 2.05, 0), math.pi)
    for p in (em, h):
        p['rig'].location.z = E3.seat_root(p, 0.34)
    pose_all(h, dur, H.pose('sit', head=(0, 4, 0)))
    pose_all(em, dur, H.pose('sit', head=(0, 6, -12)))
    K.talk(em, 0.1, dur - 0.1, rate=5, amp=0.5, seed=13)
    cam((0.7, -1.2, 1.3), (0, 6.0, 1.0), (0.6, -0.9, 1.28), (0, 6.0, 1.05), 30, dur)
    return dict(fill=0.35, exposure=0.0, samples=32)


# ============================================================================= d18 rule two
def v_rule2(shot, fps):
    """«Правило второе. Повторение сильнее таланта»: on the clean beach Emmet raises a finger (the RuleCard goes on top)."""
    dur = shot['dur']
    coll, rng = beach_shot(shot, 82, scrap_n=0)
    h = H.load(coll, (0, 0, 0), 0.0)
    em = K.load('emmet', coll, (0, -1.5, 0), math.pi)
    pose_all(h, dur, H.pose('stand', head=(0, 6, 0)))
    up = ev(shot, 'rule', 0.3)
    H.key_pose(em, 0, H.pose('stand', head=(0, -4, 0)))
    H.key_pose(em, up, H.pose('stand', head=(0, -4, 0)))
    H.key_pose(em, up + 0.4, H.pose('point', arm=((24, 4), (30, 150)), fore=((18, 16), (10, 30)), head=(0, -6, 0)))
    H.key_pose(em, dur, H.pose('point', arm=((24, 4), (30, 150)), fore=((18, 16), (10, 30)), head=(4, -6, 0)))
    K.talk(em, 0.1, dur - 0.2, rate=6, amp=0.6, seed=14)
    cam((-1.15, 1.0, 1.7), (0, -1.5, 1.45), (-1.0, 0.8, 1.68), (0, -1.5, 1.46), 45, dur)
    return dict(fill=0.5, exposure=0.0, samples=32)


# ============================================================================= d19 - d20 the glove
def glove(coll, name='Glove'):
    m = lib.mat('GloveRed', '#B8322C', rough=0.55)
    g = lib.sphere(0.13, (0, 0, 0), m, 16, 10, scale=(1.0, 1.25, 0.8), name=name, coll=coll)
    c = lib.cyl(0.08, 0.14, (0, -0.16, 0), lib.mat('GloveCuff', '#F2EEE4', rough=0.6), rot=(math.pi / 2, 0, 0), verts=14,
                name=name + 'Cuff', coll=coll)
    c.parent = g
    return g


def v_glove(shot, fps):
    """«Вечером Си-Джей кинул мне перчатку»: sunset; CJ throws a red training glove, it lands at the hero's feet."""
    dur = shot['dur']
    coll, rng = beach_shot(shot, 83, kind='sunset', zones=((0, 0, 7.0),), scrap_n=0)
    h = H.load(coll, (0, 0, 0), math.pi)
    pose_all(h, dur, H.pose('stand', head=(0, 6, 0)))
    cj = K.load('cj', coll, (0, 3.6, 0), 0.0)
    th = ev(shot, 'throw', 0.5)
    H.key_pose(cj, 0, H.pose('stand', arm=((24, 4), (20, -30)), fore=((18, 16), (40, 60))))
    H.key_pose(cj, th - 0.1, H.pose('stand', arm=((24, 4), (20, -30)), fore=((18, 16), (40, 60))))
    H.key_pose(cj, th + 0.15, H.pose('stand', arm=((24, 4), (10, 70)), fore=((18, 16), (6, 76)), lean=8.0))
    H.key_pose(cj, dur, H.pose('stand', arm=((24, 4), (24, 20)), fore=((18, 16), (20, 30))))
    g = glove(coll)
    a, b = V((0.25, 3.3, 1.2)), V((0.15, 0.45, 0.11))
    lib.key_obj(g, F(0), loc=tuple(a), rot=(0, 0, 0))
    lib.key_obj(g, F(th), loc=tuple(a), rot=(0, 0, 0))
    for k in range(1, 7):
        w = k / 6
        p = a.lerp(b, w) + V((0, 0, 1.4 * 4 * w * (1 - w)))
        lib.key_obj(g, F(th + 0.6 * w), loc=tuple(p), rot=(2.5 * w, 0.4 * w, 0), interp='LINEAR')
    lib.key_obj(g, F(dur), loc=tuple(b), rot=(2.5, 0.4, 0))
    cam((2.2, -2.2, 1.0), (0, 2.0, 0.9), (2.0, -1.9, 1.0), (0, 1.8, 0.8), 26, dur)
    return dict(fill=0.45, exposure=0.15, samples=32)


def v_duel(shot, fps):
    """«Завтра учебный бой. Ты и я»: CJ close against the sunset, points at the hero, then at himself."""
    dur = shot['dur']
    coll, rng = beach_shot(shot, 84, kind='sunset', zones=((0, 0, 7.0),), scrap_n=0)
    cj = K.load('cj', coll, (0, 2.0, 0), 0.0)
    me = ev(shot, 'me', dur * 0.6)
    H.key_pose(cj, 0, H.pose('point', arm=((24, 4), (-14, 84)), fore=((18, 16), (-18, 88)), head=(0, -6, 0)))
    H.key_pose(cj, me - 0.15, H.pose('point', arm=((24, 4), (-14, 84)), fore=((18, 16), (-18, 88)), head=(0, -6, 0)))
    H.key_pose(cj, me + 0.15, H.pose('stand', arm=((24, 4), (30, 40)), fore=((18, 16), (-80, 80)), head=(0, -10, 0)))
    H.key_pose(cj, dur, H.pose('stand', arm=((24, 4), (30, 40)), fore=((18, 16), (-80, 80)), head=(0, -12, 0)))
    K.talk(cj, 0.1, dur - 0.1, rate=7, amp=0.7, seed=15)
    cam((0.35, -0.6, 1.15), (0, 2.0, 1.45), (0.3, -0.4, 1.15), (0, 2.0, 1.48), 32, dur)
    return dict(fill=0.5, exposure=0.15, samples=32)


def v_rest4(shot, fps):
    """«Следующая серия скоро в профиле»: calm - he picks up the glove and looks at the sunset, wide."""
    dur = shot['dur']
    coll, rng = beach_shot(shot, 85, kind='sunset', scrap_n=0)
    h = H.load(coll, (0, 0, 0), math.pi * 0.9)
    H.key_pose(h, 0, H.pose('stand', head=(0, 20, 0)))
    H.key_pose(h, 1.0, H.pose('stand', arm=((24, 4), (14, 60)), fore=((18, 16), (10, 70)), head=(0, 14, 0)))
    H.key_pose(h, dur, H.pose('stand', arm=((24, 4), (14, 62)), fore=((18, 16), (10, 72)), head=(0, -6, 0)))
    g = glove(coll)
    g.location = (0.15, 0.45, 0.11)
    cam((-1.5, -5.0, 1.0), (0, 2.0, 1.2), (-2.5, -9.0, 2.6), (0, 4.0, 1.4), 28, dur)
    return dict(fill=0.35, exposure=0.15, samples=32)
