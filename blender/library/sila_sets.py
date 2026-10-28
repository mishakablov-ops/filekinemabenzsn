"""Small sets of «Каждому по способности» built from code (the rest is filmed in «Метрополис»):
room()      the hero's room on the 3rd floor, a wide window onto a Boro street (the neighbour flies past it)
kitchen()   his kitchen: table, the mug he stares at for an hour, a wall clock whose hands race
airport()   an empty apron: terminal, jet bridges, parked jets, control tower, the city in the haze
plant()     a power plant: cooling towers with steam, turbine hall, chimney, pylons; a storm wall behind it
bench(), hedge(), aisle()
"""
import math
import random

import bpy
from mathutils import Vector

import lib
import pcity
import pcommon as pc
import prooms as PR
import sila_fx as FX

F = lib.sec2f


def day(sun_dir=(0.45, -0.55, 0.5), energy=3.6, top='#4C7DB8', horizon='#D2DEE8', fog=0.0008, fog_col='#C9D6E2'):
    pc.day_sky(sun_dir, top, horizon, fog=fog, fog_col=fog_col)
    return pc.sun(sun_dir, energy, '#FFF1DE', 1.5)


def _shift(coll, dz):
    for o in coll.objects:
        if o.parent is None:
            o.location.z += dz


# ----------------------------------------------------------------------------- the hero's room
def room(coll, rng, morning=True):
    """Room 4.4 x 4.0 m, floor at z=0, window wall at y=1.8 (sill 0.85, top 2.4); outside a street 9 m below."""
    floor = lib.mat('RoomFloor', '#9A7552', rough=0.5, var=0.22, var_scale=6, bump=0.1, bump_scale=40)
    PR.shell(coll, 4.4, 4.0, 2.7, wall='#DCD3C3', floor=floor, back=False, y0=-2.2, name='Rm')
    PR.window_wall(coll, 1.8, 4.4, 2.7, sill=0.85, top=2.45, wall='#DCD3C3', panes=2)
    lib.box((4.0, 0.32, 0.04), (0, 1.62, 0.85), lib.mat('Sill', '#F2F0EA', rough=0.4), bevel=0.01, name='Sill', coll=coll, origin='bottom')
    wood = lib.mat('RmWood', '#6E4F37', rough=0.55, var=0.2, var_scale=8)
    # desk with a laptop and a lamp, a plant on the sill, a poster, a bed edge
    lib.box((1.4, 0.7, 0.04), (-1.4, 1.05, 0.74), wood, bevel=0.01, name='Desk', coll=coll, origin='bottom')
    for lx in (-2.05, -0.75):
        for ly in (0.75, 1.35):
            lib.box((0.04, 0.04, 0.74), (lx, ly, 0.0), wood, bevel=0.005, name='DeskLeg', coll=coll, origin='bottom')
    lib.box((0.34, 0.24, 0.015), (-1.35, 1.0, 0.78), lib.mat('Laptop', '#2B2D30', rough=0.3), bevel=0.004, name='Laptop', coll=coll,
            origin='bottom')
    lib.box((0.34, 0.015, 0.22), (-1.35, 1.12, 0.79), lib.mat('Laptop', '#2B2D30', rough=0.3), rot=(-0.25, 0, 0), bevel=0.004,
            name='Screen', coll=coll, origin='bottom')
    pot = lib.cyl(0.08, 0.14, (1.3, 1.65, 0.89), lib.mat('Pot', '#B4643C', rough=0.7), verts=16, r2=0.06, name='Pot', coll=coll,
                  origin='bottom')
    for k in range(5):
        lib.sphere(0.07, (1.3 + rng.uniform(-0.06, 0.06), 1.65 + rng.uniform(-0.05, 0.05), 1.08 + k * 0.035),
                   lib.mat('Plant', '#4E7A3A', rough=0.8, var=0.3, var_scale=10), 8, 6, scale=(1, 1, 1.3), name='Leaf', coll=coll)
    lib.box((0.6, 0.02, 0.85), (2.19, -0.4, 1.2), lib.mat('Poster', '#2F4E6B', rough=0.7), rot=(0, 0, math.pi / 2), bevel=0.0,
            name='Poster', coll=coll, origin='bottom')
    lib.box((1.5, 2.0, 0.45), (1.4, -1.0, 0.0), lib.mat('Bed', '#5E6B73', rough=0.9, var=0.08, var_scale=20), bevel=0.06, name='Bed',
            coll=coll, origin='bottom')
    # outside: a Boro street seen from the 3rd floor
    out = lib.collection('RoomOutside')
    walk = lib.mat('OutWalk', '#A39E95', rough=0.9)
    lib.box((120, 5, 0.15), (0, 4.5, 0), walk, bevel=0, name='OutWalk', coll=out, origin='bottom')
    lib.box((120, 14, 0.02), (0, 14.0, 0), lib.mat('Asphalt', '#5A5C5F', rough=0.86), bevel=0, name='OutRoad', coll=out, origin='bottom')
    lib.box((120, 5, 0.15), (0, 23.5, 0), walk, bevel=0, name='OutWalk2', coll=out, origin='bottom')
    for x in range(-50, 51, 6):
        lib.box((0.12, 3.0, 0.02), (x, 14.0, 0.02), lib.mat('Dash', '#E8E4D8', rough=0.6), bevel=0, name='Dash', coll=out, origin='bottom')
    facs = pcity.facade_set(0.0, prefix='RmF')
    x = -60.0
    while x < 60:
        L = rng.uniform(9, 16)
        h = rng.choice([4, 5, 6]) * 3.1
        lib.box((L - 0.4, 12, h), (x + L / 2, 32.0, 0), rng.choice(facs)[0], bevel=0.1, name='OutBld', coll=out, origin='bottom')
        lib.box((L - 0.2, 12.4, 0.5), (x + L / 2, 32.0, h), lib.mat('Roof', '#6E5F52', rough=0.8), bevel=0.05, name='OutRoof', coll=out,
                origin='bottom')
        x += L
    for k in range(6):
        pcity.tree(-25 + k * 10 + rng.uniform(-2, 2), 6.0, out, rng, h=rng.uniform(7, 9))
    pc.stopped_car((rng.uniform(-6, 6), 8.8, 0.0), 0.0, out, rng, name='OutCar')
    pc.stopped_car((rng.uniform(10, 16), 19.5, 0.0), math.pi, out, rng, name='OutCar2')
    lib.plane((600, 600), (0, 100, -0.02), lib.mat('OutGround', '#7D7A72', rough=0.9), name='OutGround', coll=out)
    _shift(out, -9.0)
    sun = day((0.35, 0.75, 0.55) if morning else (-0.4, 0.8, 0.3), 3.8)
    lib.light('AREA', (0, 1.4, 1.7), (math.radians(-90), 0, 0), energy=260, color='#EAF1FF', size=3.5, name='WinFill', coll=coll)
    return out, sun


# ----------------------------------------------------------------------------- kitchen
def kitchen(coll, rng):
    """Kitchen 3.6 x 3.4 m: table at (0, 0.4), chair behind it at y=0.95 (the hero sits facing -y), window behind him."""
    floor = lib.mat('KFloor', '#C9C2B3', rough=0.4, var=0.1, var_scale=3, bump=0.05, bump_scale=10)
    PR.shell(coll, 3.6, 3.4, 2.6, wall='#E4DCC8', floor=floor, back=False, y0=-1.8, name='Kt')
    PR.window_wall(coll, 1.6, 3.6, 2.6, sill=0.95, top=2.3, wall='#E4DCC8', panes=2)
    wood = lib.mat('KWood', '#8A6A48', rough=0.5, var=0.2, var_scale=8)
    lib.box((1.1, 0.75, 0.04), (0, 0.4, 0.74), wood, bevel=0.01, name='Table', coll=coll, origin='bottom')
    for lx in (-0.5, 0.5):
        for ly in (0.08, 0.72):
            lib.box((0.04, 0.04, 0.74), (lx, ly, 0.0), wood, bevel=0.005, name='TLeg', coll=coll, origin='bottom')
    PR.chair(0.0, 0.98, 0.0, coll)
    # the mug (white with a red stripe), a sugar bowl, a plate
    cer = lib.mat('Mug', '#F3F1EC', rough=0.3, spec=0.6)
    mug = lib.cyl(0.045, 0.1, (0, 0.18, 0.78), cer, verts=28, name='Mug', coll=coll, origin='bottom')
    lib.cyl(0.0455, 0.018, (0, 0.18, 0.84), lib.mat('MugStripe', '#C8282A', rough=0.4), verts=28, name='MugStripe', coll=coll,
            origin='bottom')
    lib.cyl(0.04, 0.004, (0, 0.18, 0.865), lib.mat('Tea', '#6B3A1A', rough=0.1, spec=0.7), verts=24, name='Tea', coll=coll)
    hp = [(0.045 + 0.03 * math.sin(a), 0.18, 0.83 + 0.028 * math.cos(a)) for a in [i * math.pi / 8 for i in range(9)]]
    lib.curve_poly('MugHandle', [hp], bevel=0.007, mat_=cer, coll=coll)
    lib.cyl(0.11, 0.015, (-0.3, 0.45, 0.78), cer, verts=28, r2=0.09, name='Plate', coll=coll, origin='bottom')
    # cabinets, fridge, a kettle on the counter
    cab = lib.mat('Cab', '#7FA3A0', rough=0.5)
    lib.box((0.6, 2.2, 0.88), (-1.48, -0.3, 0.0), cab, bevel=0.01, name='Counter', coll=coll, origin='bottom')
    lib.box((0.62, 2.22, 0.04), (-1.48, -0.3, 0.88), lib.mat('Top', '#E9E5DC', rough=0.3), bevel=0.005, name='Top', coll=coll,
            origin='bottom')
    lib.box((0.35, 2.2, 0.7), (-1.6, -0.3, 1.5), cab, bevel=0.01, name='Upper', coll=coll, origin='bottom')
    lib.box((0.65, 0.65, 1.8), (1.45, -1.3, 0.0), lib.mat('Fridge', '#ECEBE6', rough=0.3), bevel=0.03, name='Fridge', coll=coll,
            origin='bottom')
    lib.cyl(0.09, 0.2, (-1.45, 0.4, 0.92), lib.mat('Kettle', '#C9CACC', rough=0.25, metal=1.0), verts=20, r2=0.07, name='Kettle',
            coll=coll, origin='bottom')
    # wall clock on the right wall (faces -x); hands spin through the hour
    face = lib.cyl(0.2, 0.04, (1.78, 0.0, 1.85), lib.mat('ClockFace', '#F7F5EE', rough=0.5), rot=(0, math.pi / 2, 0), verts=40,
                   name='Clock', coll=coll)
    lib.cyl(0.215, 0.03, (1.79, 0.0, 1.85), lib.mat('ClockRim', '#2B2D30', rough=0.4), rot=(0, math.pi / 2, 0), verts=40, name='ClockRim',
            coll=coll)
    dark = lib.mat('ClockHand', '#1B1C1E', rough=0.4)
    for k in range(12):
        a = k * math.pi / 6
        lib.box((0.01, 0.012, 0.035), (1.755, 0.17 * math.sin(a), 1.85 + 0.17 * math.cos(a)), dark, rot=(-a, 0, 0), bevel=0,
                name='Tick', coll=coll)
    hands = []
    for nm, L, w in (('Min', 0.15, 0.012), ('Hour', 0.1, 0.018)):
        piv = lib.empty('Clock' + nm, (1.75, 0.0, 1.85), coll=coll)
        hb = lib.box((0.008, w, L), (0, 0, L / 2 - 0.015), dark, bevel=0, name='Hand' + nm, coll=coll)
        hb.parent = piv
        hands.append(piv)
    sun = day((-0.3, 0.9, 0.35), 3.2, top='#5B7FB0', horizon='#E8D4B8')
    out = lib.collection('KtOutside')
    facs = pcity.facade_set(0.0, prefix='KtF')
    for (x, y, w, h) in ((-12, 30, 18, 22), (10, 34, 20, 28), (0, 60, 40, 34)):
        lib.box((w, 12, h), (x, y, 0), rng.choice(facs)[0], bevel=0.1, name='KtOut', coll=out, origin='bottom')
    for k in range(3):
        pcity.tree(-8 + k * 7, 12.0, out, rng, h=9.0)
    lib.plane((400, 400), (0, 80, 0), lib.mat('KtGround', '#7D7A72', rough=0.9), name='KtGround', coll=out)
    _shift(out, -9.0)
    lib.light('AREA', (0, 1.3, 1.6), (math.radians(-90), 0, 0), energy=180, color='#FFF1DC', size=2.5, name='KWinFill', coll=coll)
    return mug, hands, sun


# ----------------------------------------------------------------------------- park furniture
def bench(coll, loc, heading=0.0, name='Bench'):
    wood = lib.mat('BenchWood', '#9A6B43', rough=0.6, var=0.2, var_scale=8)
    iron = lib.mat('BenchIron', '#2B2D30', rough=0.4, metal=0.6)
    root = lib.empty(name, loc, (0, 0, heading), coll=coll)
    parts = []
    for k in range(4):
        parts.append(lib.box((1.8, 0.1, 0.035), (0, -0.2 + k * 0.12, 0.45), wood, bevel=0.008, name=name + 'Slat', coll=coll))
    for k in range(2):
        parts.append(lib.box((1.8, 0.035, 0.1), (0, 0.25, 0.62 + k * 0.14), wood, rot=(0.25, 0, 0), bevel=0.008, name=name + 'Back',
                             coll=coll))
    for sx in (-0.8, 0.8):
        parts.append(lib.box((0.06, 0.5, 0.45), (sx, 0.0, 0.0), iron, bevel=0.01, name=name + 'Leg', coll=coll, origin='bottom'))
        parts.append(lib.box((0.05, 0.05, 0.5), (sx, 0.27, 0.45), iron, rot=(0.25, 0, 0), bevel=0.01, name=name + 'Arm', coll=coll,
                             origin='bottom'))
    for p in parts:
        p.parent = root
    return root


def hedge(coll, rng, p0, p1, h=1.0, w=0.9, name='Hedge'):
    """Clipped bushes along p0 -> p1 (ground z from the points): rounded boxes and lumps of leaves."""
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    L = d.length
    a = math.atan2(d.y, d.x)
    m = lib.mat('HedgeLeaf', '#4C6E33', rough=0.85, var=0.3, var_scale=6, bump=0.6, bump_scale=14)
    lib.box((L, w, h), tuple((p0 + p1) / 2), m, rot=(0, 0, a), bevel=0.25, name=name, coll=coll, origin='bottom')
    n = int(L / 0.7)
    lumps = []
    for k in range(n):
        q = p0.lerp(p1, (k + 0.5) / n)
        lumps.append(lib.sphere(rng.uniform(0.35, 0.5), (q.x, q.y, q.z + h * rng.uniform(0.8, 0.95)), m, 10, 8,
                                scale=(1.1, 1.0, 0.7), name=name + 'Lump', coll=coll))
    return lumps


def leaves_burst(coll, center, t, rng, n=40, col=('#5E8A3C', '#4C6E33', '#7FA14A'), name='LeafBurst'):
    """Leaves fly up and out of a bush when someone crashes into it."""
    out = []
    for i in range(n):
        m = lib.mat('BurstLeaf' + col[i % len(col)], col[i % len(col)], rough=0.8)
        lf = lib.box((0.07, 0.05, 0.004), center, m, bevel=0.0, name=f'{name}{i}', coll=coll)
        a = rng.uniform(0, 2 * math.pi)
        v = Vector((math.cos(a) * rng.uniform(1.0, 3.0), math.sin(a) * rng.uniform(1.0, 3.0), rng.uniform(2.0, 4.5)))
        c = Vector(center)
        keys = [(0, c), (t, c)]
        for k in range(1, 7):
            tt = k * 0.18
            p = c + v * tt + Vector((0, 0, -4.9 * tt * tt * 0.45))
            p.z = max(p.z, c.z - 0.6)
            keys.append((t + tt, p))
        FX.key_loc(lf, [(tt, tuple(p)) for tt, p in keys])
        FX.key_hide(lf, [(0, False), (t, True)])
        lf.rotation_euler = (rng.uniform(0, 6), rng.uniform(0, 6), rng.uniform(0, 6))
        lib.add_sine(lf, 'rotation_euler', 0, 1.5, rng.uniform(0.3, 0.6), rng.uniform(0, 6))
        out.append(lf)
    return out


# ----------------------------------------------------------------------------- airport
def airport(coll, rng):
    """Apron around (0, 0), terminal along y = 140 facing -y, gates at x = -150..150; the camera looks north."""
    day((0.4, -0.5, 0.45), 4.0, top='#4F82BE', horizon='#D9E2E8', fog=0.0009, fog_col='#CBD5DD')
    conc = lib.mat('Apron', '#9C9992', rough=0.85, var=0.12, var_scale=0.08, bump=0.05, bump_scale=2)
    lib.plane((3000, 3000), (0, 0, 0), conc, name='Apron', coll=coll)
    yel = lib.mat('Mark', '#E2B93B', rough=0.6)
    wht = lib.mat('MarkW', '#ECEAE4', rough=0.6)
    for k, x in enumerate(range(-180, 181, 60)):
        lib.box((0.35, 120, 0.02), (x, 70, 0.0), yel, bevel=0, name='Lead', coll=coll, origin='bottom')
        lib.box((14, 0.35, 0.02), (x, 30, 0.0), yel, bevel=0, name='Stop', coll=coll, origin='bottom')
    lib.box((600, 0.5, 0.02), (0, 10, 0.0), wht, bevel=0, name='Line', coll=coll, origin='bottom')
    glass = lib.mat('TermGlass', '#5F7B8E', rough=0.08, spec=0.9)
    frame = lib.mat('TermFrame', '#D8DADB', rough=0.4)
    lib.box((520, 46, 20), (0, 165, 0), glass, bevel=0.2, name='Terminal', coll=coll, origin='bottom')
    lib.box((530, 52, 2.0), (0, 165, 20), frame, bevel=0.3, name='TermRoof', coll=coll, origin='bottom')
    for x in range(-255, 256, 15):
        lib.box((0.6, 0.6, 20), (x, 141.8, 0), frame, bevel=0, name='Mullion', coll=coll, origin='bottom')
    lib.box((520, 0.8, 0.6), (0, 141.8, 10), frame, bevel=0, name='TermBand', coll=coll, origin='bottom')
    pc.text('АЭРОПОРТ', 6.0, (0, 140.8, 22.5), (math.pi / 2, 0, 0), '#2B4A7A', coll=coll, name='AirSign')
    bridge = lib.mat('Bridge', '#C9CCCE', rough=0.5)
    for k, x in enumerate(range(-180, 181, 60)):
        lib.box((4, 30, 3.4), (x - 6, 126, 4.0), bridge, rot=(0, 0, 0.12), bevel=0.2, name='JetBridge', coll=coll, origin='bottom')
        lib.cyl(0.6, 4.0, (x - 6, 112, 0), frame, verts=12, name='BridgeLeg', coll=coll, origin='bottom')
        if k % 3 != 1:
            FX.plane_model(coll, (x, 80, 0), heading=math.pi, livery='#F2F2F0', tail=rng.choice(['#C8282A', '#2B4A9A', '#1F7A5A']),
                           name=f'Parked{k}')
    # control tower, hangars, the city in the haze
    lib.cyl(4.0, 60, (330, 260, 0), frame, verts=24, r2=3.2, name='Tower', coll=coll, origin='bottom')
    lib.cyl(9.0, 7, (330, 260, 60), glass, verts=24, r2=10.0, name='TowerCab', coll=coll, origin='bottom')
    lib.cyl(10.5, 1.2, (330, 260, 67), frame, verts=24, name='TowerRoof', coll=coll, origin='bottom')
    for x in (-420, -330):
        lib.box((80, 60, 24), (x, 230, 0), lib.mat('Hangar', '#9DA4AA', rough=0.6), bevel=0.5, name='Hangar', coll=coll, origin='bottom')
    sky = lib.mat('FarCity', '#9AA6B0', rough=0.9)
    for k in range(60):
        x = rng.uniform(-2500, 2500)
        lib.box((rng.uniform(30, 90), 40, rng.uniform(30, 160)), (x, rng.uniform(2200, 3000), 0), sky, bevel=0, name='Far', coll=coll,
                origin='bottom')
    # one forgotten baggage cart
    cart = lib.mat('Cart', '#3B4A5A', rough=0.5)
    lib.box((3.2, 1.6, 0.25), (22, 40, 0.5), cart, bevel=0.05, name='Cart', coll=coll, origin='bottom')
    for k in range(3):
        lib.box((0.6, 0.4, 0.35), (21 + k * 0.9, 40, 0.75), lib.mat('Bag' + str(k), ['#C8282A', '#2F3B45', '#D9A23A'][k], rough=0.6),
                bevel=0.05, name='Bag', coll=coll, origin='bottom')


# ----------------------------------------------------------------------------- power plant
def plant(coll, rng, dur):
    """Cooling towers at y = 300..500, the camera south of them; the storm stands on the horizon behind."""
    pc.day_sky((0.3, -0.6, 0.35), '#4E5560', '#8A9097', fog=0.0012, fog_col='#7F868C')
    pc.sun((0.3, -0.6, 0.35), 1.4, '#E8E2D8', 3.0)
    grass = lib.mat('PlantGround', '#6E7357', rough=0.95, var=0.2, var_scale=0.05)
    lib.plane((8000, 8000), (0, 0, 0), grass, name='Ground', coll=coll)
    lib.box((900, 600, 0.05), (0, 380, 0), lib.mat('Yard', '#9A978F', rough=0.9), bevel=0, name='Yard', coll=coll, origin='bottom')
    conc = lib.mat('Cooling', '#C9C5BC', rough=0.85, var=0.12, var_scale=0.2)
    towers = [(-220, 420), (-60, 470), (120, 430)]
    for k, (x, y) in enumerate(towers):
        lib.cyl(52, 70, (x, y, 0), conc, verts=48, r2=34, name='CoolLow', coll=coll, origin='bottom', cap=False)
        lib.cyl(34, 45, (x, y, 70), conc, verts=48, r2=38, name='CoolTop', coll=coll, origin='bottom', cap=False)
        FX.smoke(coll, (x, y, 112), 160, -1.0, dur + 1.0, rng, col='#F2F2F0', r0=30.0, n=9, rise=14.0, name=f'Steam{k}')
    hall = lib.mat('Hall', '#8E9AA3', rough=0.6)
    lib.box((260, 60, 40), (40, 300, 0), hall, bevel=0.5, name='Hall', coll=coll, origin='bottom')
    lib.box((120, 50, 55), (-150, 290, 0), lib.mat('Boiler', '#B0A79A', rough=0.7), bevel=0.5, name='Boiler', coll=coll, origin='bottom')
    red, white = lib.mat('ChimR', '#B8473B', rough=0.6), lib.mat('ChimW', '#E9E7E1', rough=0.6)
    for k in range(8):
        lib.cyl(7.5 - k * 0.4, 25, (240, 330, k * 25), red if k % 2 else white, verts=24, r2=7.1 - k * 0.4, name='Chimney', coll=coll,
                origin='bottom')
    steel = lib.mat('Pylon', '#8C9196', rough=0.4, metal=0.6)
    wires = []
    for k in range(7):
        x = 300 + k * 160
        y = 250 - k * 60
        lib.cyl(2.6, 55, (x, y, 0), steel, verts=4, r2=0.6, name='Pylon', coll=coll, origin='bottom')
        lib.box((26, 1.0, 1.0), (x, y, 44), steel, rot=(0, 0, -0.36), bevel=0, name='Arm', coll=coll)
        lib.box((18, 1.0, 1.0), (x, y, 52), steel, rot=(0, 0, -0.36), bevel=0, name='Arm', coll=coll)
        wires.append((x, y))
    wm = lib.mat('Wire', '#3A3D40', rough=0.5)
    for off in (-12, -6, 6, 12):
        pts = []
        for (x0, y0), (x1, y1) in zip(wires, wires[1:]):
            for j in range(9):
                u = j / 8
                pts.append((x0 + (x1 - x0) * u + off * 0.94, y0 + (y1 - y0) * u + off * 0.34, 44 - 9 * math.sin(math.pi * u)))
        lib.curve_poly('Wire', [pts], bevel=0.12, mat_=wm, coll=coll)
    # the storm on the horizon: a huge dark wall and a funnel, far behind the plant
    FX.cloud_deck(coll, (0, 4200, 1600), 3600, rng, n=90, col='#59606A', alpha=0.95, name='StormDeck', spin=0.01)
    FX.vortex(coll, (300, 4800, 0), 1500, 40, 1500, 200, rng, rings=8, per=30, period=14.0, col='#666E78', name='FarVortex')
