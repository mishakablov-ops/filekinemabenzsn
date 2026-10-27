"""Interiors in real colours (posledniy-chelovek-blender). Variants:
cafe (a window table, the coffee is still steaming, nobody there), station (power plant control room, emergency stop),
shops (supermarket aisle, the hero with arms up), bread (bakery shelf), cans (shelf of tins),
room (living room at night, the hero alone on the sofa, a candle), knock (the front door, light under it),
cta (the same door, a crack open, light behind it).
"""
import bpy, math, random
from mathutils import Vector
import lib
from lib import C
import pcommon as pc
import people2 as P2
import pcity

F = lib.sec2f


# ----------------------------------------------------------------------------- shared furniture
def shell(coll, w, d, h, wall='#D6D0C4', floor=None, back=True, left=True, right=True, ceiling=True, y0=-3.0, name='Room'):
    """Floor + walls of a room spanning x in [-w/2, w/2], y in [y0, y0 + d] (back wall at y0 + d)."""
    fm = floor or lib.mat(name + 'Floor', '#8A6A4C', rough=0.6, var=0.2, var_scale=4, bump=0.1, bump_scale=30)
    wm = lib.mat(name + 'Wall', wall, rough=0.9, var=0.06, var_scale=2)
    yb = y0 + d
    lib.box((w, d, 0.1), (0, y0 + d / 2, -0.1), fm, bevel=0, name=name + 'Floor', coll=coll, origin='bottom')
    if back:
        lib.box((w, 0.12, h), (0, yb + 0.06, 0), wm, bevel=0, name=name + 'Back', coll=coll, origin='bottom')
    if left:
        lib.box((0.12, d, h), (-w / 2 - 0.06, y0 + d / 2, 0), wm, bevel=0, name=name + 'Left', coll=coll, origin='bottom')
    if right:
        lib.box((0.12, d, h), (w / 2 + 0.06, y0 + d / 2, 0), wm, bevel=0, name=name + 'Right', coll=coll, origin='bottom')
    if ceiling:
        lib.box((w + 0.3, d, 0.1), (0, y0 + d / 2, h), lib.mat(name + 'Ceil', '#ECE9E2', rough=0.9), bevel=0, name=name + 'Ceil',
                coll=coll, origin='bottom')
    return wm


def chair(x, y, heading, coll, wood='#6B4A32', name='Chair'):
    m = lib.mat('ChairWood' + wood, wood, rough=0.6, var=0.15, var_scale=6)
    root = lib.empty(name, (x, y, 0), (0, 0, heading), coll=coll)
    parts = [lib.box((0.44, 0.44, 0.04), (0, 0, 0.45), m, bevel=0.01, name='Seat', coll=coll),
             lib.box((0.42, 0.04, 0.42), (0, 0.21, 0.7), m, bevel=0.01, name='Back', coll=coll)]
    for lx in (-0.19, 0.19):
        for ly in (-0.19, 0.19):
            parts.append(lib.cyl(0.018, 0.45, (lx, ly, 0), m, verts=8, name='Leg', coll=coll, origin='bottom'))
    for p in parts:
        p.parent = root
    return root


def cup(x, y, z, coll, steam=False, coffee='#3E2414', name='Cup'):
    cer = lib.mat('Ceramic', '#F3F1EC', rough=0.25, spec=0.6)
    lib.cyl(0.075, 0.01, (x, y, z + 0.005), cer, verts=32, r2=0.068, name=name + 'Saucer', coll=coll)
    body = lib.cyl(0.042, 0.075, (x, y, z + 0.01), cer, verts=28, r2=0.047, name=name + 'Body', coll=coll, origin='bottom')
    lib.cyl(0.042, 0.004, (x, y, z + 0.075), lib.mat('Coffee', coffee, rough=0.15, spec=0.7), verts=28, name=name + 'Coffee', coll=coll)
    lib.cyl(0.02, 0.003, (x + 0.006, y - 0.004, z + 0.0775), lib.mat('Crema', '#B07A4A', rough=0.3), verts=16, name=name + 'Crema', coll=coll)
    hpts = [(x + 0.045 + 0.028 * math.sin(a), y, z + 0.047 + 0.022 * math.cos(a)) for a in [i * math.pi / 8 for i in range(9)]]
    lib.curve_poly(name + 'Handle', [hpts], bevel=0.006, mat_=cer, coll=coll)
    lib.box((0.012, 0.11, 0.003), (x - 0.055, y - 0.02, z + 0.012), lib.mat('Spoon', '#C9CACC', rough=0.2, metal=1.0), rot=(0, 0, 0.3),
            bevel=0.001, name=name + 'Spoon', coll=coll)
    if steam:
        sm = lib.mat('Steam', '#FFFFFF', rough=1.0, emit='#FFFFFF', emit_strength=0.25, alpha=0.1)
        rng = random.Random(4)
        for k in range(4):
            ph = rng.uniform(0, 6)
            pts = [(x + 0.012 * (k - 1.5) + 0.018 * math.sin(ph + i * 0.9), y + 0.01 * math.cos(ph + i * 0.7), z + 0.085 + i * 0.022)
                   for i in range(12)]
            ob = lib.curve_poly(name + 'Steam', [pts], bevel=0.0035 + 0.001 * k, mat_=sm, coll=coll)
            ob.visible_shadow = False
    return body


def window_wall(coll, y, w, h, sill=0.6, top=2.7, wall='#D6D0C4', frame='#F0EEE8', panes=3):
    """Wall at y with a wide window (sill..top), white frames, glass that does not block the sun."""
    wm = lib.mat('WinWall' + wall, wall, rough=0.9)
    fm = lib.mat('WinFrame' + frame, frame, rough=0.5)
    lib.box((w, 0.2, sill), (0, y, 0), wm, bevel=0, name='WallLow', coll=coll, origin='bottom')
    lib.box((w, 0.2, h - top), (0, y, top), wm, bevel=0, name='WallTop', coll=coll, origin='bottom')
    gw = w - 0.4
    for k in range(panes + 1):
        x = -gw / 2 + gw * k / panes
        lib.box((0.07, 0.12, top - sill), (x, y, sill), fm, bevel=0.005, name='Mullion', coll=coll, origin='bottom')
    for z in (sill, top - 0.06):
        lib.box((gw + 0.07, 0.14, 0.06), (0, y, z), fm, bevel=0.005, name='Transom', coll=coll, origin='bottom')
    for sx in (-1, 1):
        lib.box((0.2, 0.2, top - sill), (sx * (w / 2 - 0.1), y, sill), wm, bevel=0, name='WallSide', coll=coll, origin='bottom')
    g = lib.box((gw, 0.01, top - sill), (0, y, sill), lib.mat('WinGlass', '#C8D6DE', rough=0.02, spec=1.0, alpha=0.12), bevel=0,
                name='Glass', coll=coll, origin='bottom')
    g.visible_shadow = False
    return g


def outside_street(coll, y0, rng, lit=0.0, day=True):
    """What the window shows: a sidewalk, the road, a row of houses across it, a parked car, trees."""
    walk = lib.mat('OutWalk', '#A39E95', rough=0.9)
    lib.box((60, 4, 0.05), (0, y0 + 2, -0.05), walk, bevel=0, name='OutWalk', coll=coll, origin='bottom')
    lib.box((60, 14, 0.02), (0, y0 + 11, -0.12), lib.mat('Asphalt', '#5A5C5F', rough=0.86), bevel=0, name='OutRoad', coll=coll, origin='bottom')
    lib.box((60, 4, 0.05), (0, y0 + 20, -0.05), walk, bevel=0, name='OutWalk2', coll=coll, origin='bottom')
    facs = pcity.facade_set(lit, prefix='OutF')
    x = -30.0
    while x < 30:
        L = rng.uniform(12, 22)
        h = rng.choice([5, 6, 9]) * 3.1
        lib.box((L - 0.5, 14, h), (x + L / 2, y0 + 29, 0), rng.choice(facs)[0], bevel=0.1, name='OutBld', coll=coll, origin='bottom')
        x += L
    for k in range(4):
        pcity.tree(rng.uniform(-12, 12), y0 + 2.5, coll, rng, h=rng.uniform(7, 9))
    if day:
        pc.stopped_car((rng.uniform(-3, 3), y0 + 5.5, -0.12), 0.0, coll, rng, name='OutCar')


# ----------------------------------------------------------------------------- cafe
def v_cafe(shot):
    dur = shot['dur']
    rng = random.Random(14)
    coll = lib.collection('Cafe')
    sd = (0.35, 1.0, 0.55)
    pc.day_sky(sd, fog=0.0)
    pc.sun(sd, 3.8, '#FFF1DE', angle=2.0)
    floor = lib.mat('CafeFloor', '#7B5A40', rough=0.55, var=0.25, var_scale=5, bump=0.15, bump_scale=40)
    shell(coll, 7.0, 4.6, 3.1, wall='#E3D9C8', floor=floor, back=False, right=False, y0=-3.4, name='Cafe')
    window_wall(coll, 1.3, 7.0, 3.1, sill=0.65, top=2.75, wall='#E3D9C8')
    outside_street(coll, 1.5, rng)
    # our table: marble top on a cast-iron foot
    marble = lib.mat('Marble', '#ECE8E1', rough=0.22, var=0.08, var_scale=9, spec=0.6)
    iron = lib.mat('Iron', '#2A2A2B', rough=0.45, metal=0.7)
    lib.cyl(0.36, 0.03, (0, 0, 0.74), marble, verts=48, name='TableTop', coll=coll)
    lib.cyl(0.035, 0.72, (0, 0, 0.02), iron, verts=12, name='TableLeg', coll=coll, origin='bottom')
    lib.cyl(0.22, 0.03, (0, 0, 0.0), iron, verts=24, name='TableFoot', coll=coll, origin='bottom')
    cup(0.05, -0.05, 0.755, coll, steam=True)
    plate = lib.mat('Ceramic', '#F3F1EC', rough=0.25, spec=0.6)
    lib.cyl(0.1, 0.012, (-0.17, 0.1, 0.761), plate, verts=32, r2=0.085, name='Plate', coll=coll)
    crs = lib.mat('Croissant', '#C88B3E', rough=0.55, var=0.25, var_scale=40, bump=0.4, bump_scale=60)
    for k in range(5):
        a = -0.9 + k * 0.45
        r = 0.028 + 0.012 * (1 - abs(k - 2) / 2)
        lib.sphere(r, (-0.17 + 0.07 * math.sin(a), 0.1 + 0.05 * math.cos(a) - 0.03, 0.79), crs, 14, 10, scale=(1.1, 0.9, 0.75),
                   name='Croissant', coll=coll)
    # the phone face down, a bag left on the opposite chair, sugar sticks
    lib.box((0.075, 0.155, 0.008), (0.2, 0.12, 0.759), lib.mat('PhoneBack', '#2C3A4F', rough=0.35, metal=0.3), rot=(0, 0, 0.35),
            bevel=0.004, name='Phone', coll=coll)
    for k in range(2):
        lib.box((0.016, 0.1, 0.006), (-0.02 + k * 0.024, -0.2, 0.758), lib.mat('Sugar', '#F0E6D2', rough=0.8), rot=(0, 0, 0.2),
                bevel=0.002, name='Sugar', coll=coll)
    chair(0.0, 0.62, math.pi, coll)
    lib.box((0.32, 0.14, 0.26), (0.05, 0.6, 0.6), lib.mat('Bag', '#8A5A3C', rough=0.7), rot=(0, 0, 0.2), bevel=0.03, name='Bag', coll=coll)
    chair(0.62, -0.1, math.pi / 2 + 0.3, coll)
    # other tables, also abandoned mid-coffee
    for (x, y) in ((-1.7, 0.35), (1.8, 0.5), (-2.6, -1.5)):
        lib.cyl(0.36, 0.03, (x, y, 0.74), marble, verts=48, name='TableTop', coll=coll)
        lib.cyl(0.035, 0.72, (x, y, 0.02), iron, verts=12, name='TableLeg', coll=coll, origin='bottom')
        cup(x + 0.1, y - 0.05, 0.755, coll, name='Cup2')
        chair(x - 0.55, y, -math.pi / 2, coll)
        chair(x + 0.55, y, math.pi / 2, coll)
    # warm pendant lamps (off), counter at the back left
    for x in (-1.7, 0.0, 1.8):
        lib.curve_poly('Cord', [[(x, 0.1, 3.1), (x, 0.1, 2.25)]], bevel=0.004, mat_=iron, coll=coll)
        lib.cyl(0.16, 0.18, (x, 0.1, 2.12), lib.mat('Shade', '#2F4A3E', rough=0.5), verts=24, r2=0.05, name='Shade', coll=coll)
    lib.light('AREA', (0, 0.9, 1.8), (math.radians(-90), 0, 0), energy=120, color='#EEF3FF', size=3.0, name='WindowSoft', coll=coll)
    # the steam keeps rising and swaying: the coffee was poured a minute ago
    for k, ob in enumerate(o for o in coll.objects if o.name.startswith('CupSteam')):
        lib.key_obj(ob, 1, loc=(0, 0, 0))
        lib.key_obj(ob, F(dur) + 1, loc=(0, 0, 0.03), interp='LINEAR')
        lib.add_sine(ob, 'location', 0, 0.006, 2.4 + 0.3 * k, phase=k * 1.3)
        lib.add_sine(ob, 'location', 1, 0.004, 3.1 - 0.2 * k, phase=k * 0.7)
    # slow push in over the cup, focus follows it
    cam = lib.camera((0.06, -0.66, 1.04), (0.04, 0.1, 0.8), lens=42, dof=0.66, fstop=2.2)
    lib.animate_camera(cam, [(0, (0.06, -0.66, 1.04)), (dur, (0.0, -0.5, 0.99))], [(0, (0.04, 0.1, 0.8)), (dur, (0.05, 0.05, 0.79))],
                       focus_keys=[(0, 0.66), (dur, 0.52)])
    cam.data.clip_start = 0.05
    return dict(fill=0.45, exposure=0.2, still_t=0.5)


# ----------------------------------------------------------------------------- control room
def v_station(shot):
    dur = shot['dur']
    rng = random.Random(15)
    coll = lib.collection('Station')
    lib.world_color('#1A1C20', 0.4)
    floor = lib.mat('Lino', '#646B72', rough=0.45, var=0.12, var_scale=2)
    shell(coll, 8.0, 6.0, 3.3, wall='#CFCBC1', floor=floor, y0=-3.2, name='CR')
    beige = lib.mat('Console', '#C3BEB2', rough=0.6, var=0.08, var_scale=3)
    dark = lib.mat('Bezel', '#1C1D20', rough=0.4)
    lib.box((5.2, 0.85, 0.78), (0, 0.15, 0), beige, bevel=0.03, name='Desk', coll=coll, origin='bottom')
    panel = lib.box((5.2, 0.5, 0.05), (0, -0.05, 0.86), lib.mat('PanelTop', '#A9A79E', rough=0.6), rot=(-0.42, 0, 0), bevel=0.01,
                    name='SlopePanel', coll=coll)
    cols = [('#FF3B2E', 7.0), ('#FF3B2E', 7.0), ('#3E4044', 0.0), ('#3E4044', 0.0), ('#E8A62E', 3.0), ('#2E8A4A', 0.0)]
    for i in range(30):
        for j in range(3):
            c, s = rng.choice(cols)
            bm = lib.emission_mat('Btn' + c + str(s), c, s)[0] if s else lib.mat('Btn' + c, c, rough=0.4)
            b = lib.cyl(0.022, 0.02, (-2.4 + i * 0.165, -0.12 + j * 0.13, 0.03), bm, verts=12, name='Btn', coll=coll)
            b.parent = panel
    # monitors on the desk
    screens = [('ЭНЕРГОБЛОК 2\n0 МВт', '#0C1A2A', '#F2B13A', -1.2), ('АВАРИЙНЫЙ\nОСТАНОВ', '#7A0C08', '#FFFFFF', 0.0),
               ('ГОРОД\nОБЕСТОЧЕН', '#0C1A2A', '#FF5A4A', 1.2)]
    for body, bg, fg, x in screens:
        lib.box((1.08, 0.06, 0.66), (x, 0.42, 1.12), dark, bevel=0.02, name='Monitor', coll=coll, origin='bottom')
        lib.box((0.08, 0.08, 0.34), (x, 0.47, 0.78), dark, bevel=0.01, name='MonStand', coll=coll, origin='bottom')
        sm, _ = lib.emission_mat('Screen' + bg, bg, 1.4)
        lib.box((1.0, 0.01, 0.58), (x, 0.385, 1.16), sm, bevel=0, name='Screen', coll=coll, origin='bottom')
        pc.text(body, 0.12 if x == 0 else 0.1, (x, 0.375, 1.45), (math.pi / 2, 0, 0), fg, strength=5.0, coll=coll, name='ScreenText')
    # mimic board on the back wall with the big alarm panel
    board = lib.mat('Mimic', '#8F9C92', rough=0.7, var=0.06, var_scale=3)
    lib.box((7.4, 0.1, 2.3), (0, 2.72, 0.75), board, bevel=0.02, name='Board', coll=coll, origin='bottom')
    line = lib.mat('MimicLine', '#2B2F2E', rough=0.6)
    for k in range(9):
        z = 1.0 + k * 0.2
        x0 = rng.uniform(-3.5, -1.0)
        lib.box((rng.uniform(1.5, 5.5), 0.02, 0.03), (x0 + 2.0, 2.66, z), line, bevel=0, name='MimicH', coll=coll)
    for k in range(14):
        lib.box((0.03, 0.02, rng.uniform(0.3, 1.2)), (rng.uniform(-3.4, 3.4), 2.66, rng.uniform(1.1, 2.2)), line, bevel=0, name='MimicV', coll=coll)
    redm, _ = lib.emission_mat('AlarmLamp', '#FF2E22', 9.0)
    offm = lib.mat('LampOff', '#3A3532', rough=0.4)
    for k in range(60):
        lib.sphere(0.035, (rng.uniform(-3.5, 3.5), 2.66, rng.uniform(0.9, 2.9)), redm if rng.random() < 0.45 else offm, 8, 6,
                   name='MimicLamp', coll=coll)
    alarm, _ = lib.emission_mat('AlarmPanel', '#B3120C', 3.0)
    lib.box((3.0, 0.04, 0.62), (0, 2.65, 2.2), alarm, bevel=0.01, name='AlarmPanel', coll=coll, origin='bottom')
    pc.text('АВАРИЙНЫЙ ОСТАНОВ', 0.3, (0, 2.62, 2.51), (math.pi / 2, 0, 0), '#FFFFFF', strength=6.0, coll=coll, name='AlarmText')
    pc.text('ТЭЦ-2 · ЩИТ УПРАВЛЕНИЯ', 0.15, (0, 2.66, 2.93), (math.pi / 2, 0, 0), '#2B2F2E', coll=coll, name='BoardTitle')
    # empty office chair pushed back, a cold mug, papers, the handset off the hook
    fab = lib.mat('ChairFab', '#2E3A4A', rough=0.85)
    ch = lib.empty('OfficeChair', (0.55, -1.05, 0), (0, 0, 0.75), coll=coll)
    for o in (lib.box((0.52, 0.5, 0.09), (0, 0, 0.48), fab, bevel=0.03, name='OSeat', coll=coll),
              lib.box((0.48, 0.08, 0.6), (0, 0.26, 0.86), fab, bevel=0.03, name='OBack', coll=coll),
              lib.cyl(0.03, 0.42, (0, 0, 0.06), iron_mat(), verts=10, name='OPost', coll=coll, origin='bottom')):
        o.parent = ch
    for k in range(5):
        a = 2 * math.pi * k / 5
        lib.box((0.32, 0.04, 0.03), (0.16 * math.cos(a), 0.16 * math.sin(a), 0.06), iron_mat(), rot=(0, 0, a), bevel=0.01, name='OLeg',
                coll=coll).parent = ch
    cup(1.9, -0.05, 0.78, coll, coffee='#2A1A10', name='Mug')
    for k in range(3):
        lib.box((0.21, 0.297, 0.002), (-1.9 + k * 0.05, 0.0 + k * 0.03, 0.782 + k * 0.002), lib.mat('Paper', '#F4F2EC', rough=0.9),
                rot=(0, 0, 0.1 * k), bevel=0, name='Paper', coll=coll)
    lib.box((0.06, 0.22, 0.05), (2.25, 0.25, 0.8), dark, rot=(0, 0, 0.8), bevel=0.02, name='Handset', coll=coll)
    # red emergency light on the wall + dim screen glow
    beacon = lib.light('POINT', (-3.6, 2.4, 2.9), energy=220, color='#FF3A2A', size=0.2, name='Beacon', coll=coll)
    bm, bsock = lib.emission_mat('BeaconLamp', '#FF2E22', 9.0)
    lib.sphere(0.12, (-3.6, 2.6, 2.9), bm, 12, 8, name='BeaconLamp', coll=coll)
    lib.light('AREA', (0, -0.6, 3.1), (0, 0, 0), energy=260, color='#E9EEF5', size=4.0, name='Emergency', coll=coll)
    # the alarm is alive: beacon breathes, the panel and the centre monitor blink once a second
    period = 0.8
    pc.pulse(bsock.inputs['Strength'], 2.0, 14.0, 0, dur + 0.5, period=period)
    pc.key_light(beacon, [(i * period / 2, 380 if i % 2 else 60) for i in range(int((dur + 0.5) / (period / 2)) + 1)])
    pc.blink(alarm.node_tree.nodes['Emission'].inputs['Strength'], 4.5, 0.6, 0, dur + 0.5, period=1.0, duty=0.55)
    for ob in coll.objects:
        if ob.name.startswith('AlarmText'):
            pc.blink(ob.active_material.node_tree.nodes['Emission'].inputs['Strength'], 7.0, 1.2, 0, dur + 0.5, period=1.0, duty=0.55)
    cam = lib.camera((0.55, -1.75, 1.5), (0.0, 0.6, 1.5), lens=27)
    lib.animate_camera(cam, [(0, (0.55, -1.75, 1.5)), (dur, (0.25, -1.2, 1.42))], [(0, (0.0, 0.6, 1.5)), (dur, (0.0, 0.6, 1.62))])
    cam.data.clip_start = 0.05
    lib.bloom(0.35, 0.9, 7)
    return dict(fill=0.45, fill_col='#F2EEE8', exposure=0.35, still_t=0.5)


def iron_mat():
    return lib.mat('Iron', '#2A2A2B', rough=0.45, metal=0.7)


# ----------------------------------------------------------------------------- supermarket
PACK = ['#C8282A', '#E8B730', '#2B5AA0', '#2F8A4A', '#F1EDE3', '#E46A1F', '#7A2E7E', '#1E1E1E', '#D9D0BC', '#4AA0C8', '#B5182E',
        '#F4D46A', '#3C6E2E', '#E1E0DA']


def shelf_unit(x0, x1, y0, y1, face, coll, rng, levels=(0.12, 0.52, 0.92, 1.32, 1.72), h=2.05, metal='#B8BBBE', fill='packs'):
    """Shelving along y between y0, y1 (front edge at x0 facing `face` = +1/-1 in x), filled with products."""
    sm = lib.mat('Shelf' + metal, metal, rough=0.45, metal=0.4)
    back = lib.mat('ShelfBack', '#DCDAD5', rough=0.7)
    depth = abs(x1 - x0)
    xc = (x0 + x1) / 2
    xb = x1
    lib.box((0.03, y1 - y0, h), (xb, (y0 + y1) / 2, 0), back, bevel=0, name='ShelfBack', coll=coll, origin='bottom')
    price = lib.mat('PriceStrip', '#F3D23C', rough=0.5)
    for z in levels:
        lib.box((depth, y1 - y0, 0.025), (xc, (y0 + y1) / 2, z), sm, bevel=0, name='ShelfBoard', coll=coll, origin='bottom')
        lib.box((0.012, y1 - y0, 0.045), (x0 + face * 0.006, (y0 + y1) / 2, z - 0.01), price, bevel=0, name='Price', coll=coll, origin='bottom')
        y = y0 + 0.04
        zt = z + 0.025
        clear = 0.36
        while y < y1 - 0.1:
            kind = rng.random()
            col = rng.choice(PACK)
            pm = lib.mat('Pack' + col, col, rough=0.45, var=0.12, var_scale=30)
            if kind < 0.65:
                w = rng.uniform(0.07, 0.2); hh = rng.uniform(0.14, clear - 0.02); dd = rng.uniform(0.16, 0.28)
                n = rng.randint(1, 4)
                for k in range(n):
                    if y + w > y1 - 0.05:
                        break
                    lib.box((dd, w - 0.006, hh), (x0 + face * (dd / 2 + 0.02), y + w / 2, zt), pm, bevel=0.004, name='Pack', coll=coll, origin='bottom')
                    y += w
            else:
                r = rng.uniform(0.03, 0.045); hh = rng.uniform(0.18, clear - 0.02)
                n = rng.randint(2, 6)
                for k in range(n):
                    if y + 2 * r > y1 - 0.05:
                        break
                    lib.cyl(r, hh * 0.8, (x0 + face * (r + 0.03), y + r, zt), pm, verts=14, name='Bottle', coll=coll, origin='bottom')
                    lib.cyl(r, hh * 0.2, (x0 + face * (r + 0.03), y + r, zt + hh * 0.8), pm, verts=14, r2=r * 0.35, name='BottleTop', coll=coll,
                            origin='bottom')
                    y += 2 * r + 0.004
            y += rng.uniform(0.0, 0.02)
    for y in (y0, y1):
        lib.box((depth, 0.04, h), (xc, y, 0), sm, bevel=0, name='Upright', coll=coll, origin='bottom')


def v_shops(shot):
    dur = shot['dur']
    rng = random.Random(16)
    coll = lib.collection('Market')
    lib.world_color('#DADCDF', 0.6)
    floor = lib.mat('MarketFloor', '#D6D2C8', rough=0.22, var=0.05, var_scale=1, spec=0.6)
    shell(coll, 9.0, 26.0, 3.8, wall='#E6E3DC', floor=floor, y0=-3.0, name='Mk')
    for sx in (-1, 1):
        shelf_unit(sx * 1.3, sx * 2.3, 0.0, 20.0, -sx, coll, rng)
    strip, _ = lib.emission_mat('Tube', '#F4F7FF', 8.0)
    for x in (-2.95, 0.0, 2.95):
        for y in range(0, 22, 4):
            lib.box((0.22, 3.4, 0.05), (x, y + 1.8, 3.65), strip, bevel=0, name='Tube', coll=coll)
    for y in (2.0, 8.0, 14.0):
        lib.light('AREA', (0, y, 3.5), (0, 0, 0), energy=520, color='#F2F5FF', size=2.6, name='CeilL', coll=coll)
    signm = lib.mat('AisleSign', '#1F5AA6', rough=0.5)
    for y, label in ((7.0, 'ХЛЕБ  ·  КОНСЕРВЫ'), (15.0, 'НАПИТКИ')):
        lib.box((2.4, 0.05, 0.5), (0, y, 3.0), signm, bevel=0.02, name='AisleSign', coll=coll)
        pc.text(label, 0.2, (0, y - 0.03, 3.0), (math.pi / 2, 0, 0), '#FFFFFF', coll=coll, name='AisleText')
        lib.curve_poly('SignWire', [[(-1.0, y, 3.25), (-1.0, y, 3.8)], [(1.0, y, 3.25), (1.0, y, 3.8)]], bevel=0.004, mat_=iron_mat(), coll=coll)
    # a basket dropped in the aisle
    lib.box((0.46, 0.32, 0.24), (-0.55, 3.2, 0.0), lib.mat('Basket', '#C8282A', rough=0.5), rot=(0, 0, 0.4), bevel=0.02, name='Basket',
            coll=coll, origin='bottom')
    h = pc.hero((0.0, 6.2, 0), heading=0.0, coll=coll, pose='cheer')
    # arms go up on «твои» with a little hop
    tc = shot.get('events', {}).get('cheer', dur * 0.5)
    t0, t1 = max(0.0, tc - 0.2), tc + 0.2
    for part, down, up in (('upperL', -0.12, -2.5), ('upperR', 0.12, 2.5), ('foreL', -0.15, -0.35), ('foreR', 0.15, 0.35)):
        pc.key_rot(h[part], 1, [(0, down), (t0, down), (t1, up), (dur, up * 1.02)])
    pc.key_rot(h['head'], 0, [(0, 0.0), (t0, 0.0), (t1, 0.18), (dur, 0.2)])
    for t, z in ((0, 0.0), (t1 - 0.05, 0.0), (t1 + 0.13, 0.11), (t1 + 0.32, 0.0), (dur, 0.0)):
        P2._key(h['root'], 'location', 2, F(t), z)
    cam = lib.camera((0.25, 1.4, 1.3), (0.0, 9.0, 1.55), lens=46)
    lib.animate_camera(cam, [(0, (0.25, 1.4, 1.3)), (dur, (0.15, 2.6, 1.3))], [(0, (0.0, 9.0, 1.5)), (dur, (0.0, 9.0, 1.6))])
    cam.data.clip_start = 0.1
    return dict(fill=0.4, exposure=0.15, still_t=0.5)


# ----------------------------------------------------------------------------- bakery shelf
def v_bread(shot):
    dur = shot['dur']
    rng = random.Random(17)
    coll = lib.collection('Bread')
    lib.world_color('#D8CFC2', 0.5)
    shell(coll, 5.0, 4.0, 3.0, wall='#E4DACB', y0=-3.0, name='Bk', ceiling=False)
    wood = lib.mat('BakeryWood', '#9A6A40', rough=0.6, var=0.2, var_scale=8)
    tile = lib.mat('Tile', '#EDE6DA', rough=0.4, var=0.05, var_scale=10)
    lib.box((3.0, 0.05, 2.2), (0, 0.6, 0.4), tile, bevel=0, name='TileWall', coll=coll, origin='bottom')
    for z in (0.75, 1.12, 1.49):
        lib.box((2.6, 0.5, 0.035), (0, 0.33, z), wood, bevel=0.005, name='Board', coll=coll, origin='bottom')
        lib.box((2.6, 0.02, 0.07), (0, 0.075, z - 0.02), wood, bevel=0.005, name='Lip', coll=coll, origin='bottom')
    for x in (-1.3, 1.3):
        lib.box((0.04, 0.5, 1.6), (x, 0.33, 0.0), wood, bevel=0.005, name='Side', coll=coll, origin='bottom')
    crust = [lib.mat('Crust' + c, c, rough=0.6, var=0.3, var_scale=25, bump=0.6, bump_scale=45) for c in ('#C98B45', '#B4733A', '#D9A35E', '#A5652E')]
    rye = lib.mat('Rye', '#5A3A26', rough=0.7, var=0.2, var_scale=20, bump=0.5, bump_scale=40)
    tag = lib.mat('Tag', '#F7F5EF', rough=0.6)
    for z in (0.785, 1.155, 1.525):
        x = -1.22
        while x < 1.2:
            k = rng.random()
            if k < 0.35:      # батон
                lib.sphere(1.0, (x + 0.1, 0.3 + rng.uniform(-0.05, 0.05), z + 0.05), rng.choice(crust), 18, 12, scale=(0.15, 0.075, 0.06),
                           name='Loaf', coll=coll)
                for s in range(3):
                    lib.box((0.012, 0.06, 0.004), (x + 0.04 + s * 0.06, 0.3, z + 0.108), lib.mat('Slash', '#E9C995', rough=0.7), rot=(0, 0, 0.6),
                            bevel=0, name='Slash', coll=coll)
                x += 0.26
            elif k < 0.6:     # каравай
                lib.sphere(1.0, (x + 0.12, 0.3, z + 0.06), rng.choice(crust), 18, 12, scale=(0.115, 0.115, 0.07), name='Round', coll=coll)
                x += 0.25
            elif k < 0.8:     # бородинский
                lib.box((0.11, 0.2, 0.09), (x + 0.06, 0.3, z), rye, bevel=0.025, name='Rye', coll=coll, origin='bottom')
                x += 0.14
            else:             # багеты стоят в корзине
                lib.cyl(0.11, 0.16, (x + 0.12, 0.3, z), lib.mat('Wicker', '#B08452', rough=0.8, var=0.3, var_scale=60, bump=0.5, bump_scale=120),
                        verts=20, name='Basket', coll=coll, origin='bottom')
                for b in range(4):
                    lib.sphere(1.0, (x + 0.12 + rng.uniform(-0.05, 0.05), 0.3 + rng.uniform(-0.05, 0.05), z + 0.25),
                               rng.choice(crust), 12, 8, scale=(0.03, 0.03, 0.2), name='Baguette', coll=coll).rotation_euler = (
                        rng.uniform(-0.25, 0.25), rng.uniform(-0.25, 0.25), 0)
                x += 0.26
            lib.box((0.07, 0.004, 0.045), (x - 0.08, 0.06, z + 0.005), tag, bevel=0, name='Tag', coll=coll)
    lib.light('AREA', (0.2, -0.6, 2.3), (math.radians(35), 0, 0), energy=160, color='#FFE6C4', size=1.6, name='BakeryL', coll=coll)
    # slow slide along the shelf, as if walking past it
    cam = lib.camera((0.45, -0.95, 1.32), (0.2, 0.25, 1.12), lens=40, dof=1.2, fstop=2.8)
    lib.animate_camera(cam, [(0, (0.45, -0.95, 1.32)), (dur, (-0.05, -0.9, 1.3))], [(0, (0.2, 0.25, 1.12)), (dur, (-0.25, 0.25, 1.12))])
    cam.data.clip_start = 0.05
    return dict(fill=0.5, fill_col='#FFF1E2', exposure=0.2, still_t=0.5)


# ----------------------------------------------------------------------------- tins
def label_mat(col):
    """Can label: colour with a white band around the middle (Generated z)."""
    key = 'Label' + col
    if key in bpy.data.materials:
        return bpy.data.materials[key]
    m = bpy.data.materials.new(key)
    m.use_nodes = True
    nt = m.node_tree; L = nt.links
    p = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ'); L.new(tc.outputs['Generated'], sep.inputs[0])
    g1 = nt.nodes.new('ShaderNodeMath'); g1.operation = 'GREATER_THAN'; g1.inputs[1].default_value = 0.36
    g2 = nt.nodes.new('ShaderNodeMath'); g2.operation = 'LESS_THAN'; g2.inputs[1].default_value = 0.66
    L.new(sep.outputs['Z'], g1.inputs[0]); L.new(sep.outputs['Z'], g2.inputs[0])
    band = nt.nodes.new('ShaderNodeMath'); band.operation = 'MULTIPLY'
    L.new(g1.outputs[0], band.inputs[0]); L.new(g2.outputs[0], band.inputs[1])
    mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'
    L.new(band.outputs[0], mix.inputs['Factor'])
    mix.inputs['A'].default_value = C(col); mix.inputs['B'].default_value = C('#EFEBE1')
    L.new(mix.outputs['Result'], p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = 0.4
    return m


def v_cans(shot):
    dur = shot['dur']
    rng = random.Random(18)
    coll = lib.collection('Cans')
    lib.world_color('#D9DBDE', 0.6)
    shell(coll, 6.0, 4.0, 3.0, wall='#E4E2DC', y0=-3.0, name='Cn', ceiling=False)
    shelf_m = lib.mat('ShelfGrey', '#B8BBBE', rough=0.45, metal=0.4)
    lib.box((3.2, 0.03, 2.0), (0, 0.55, 0.0), lib.mat('ShelfBack', '#DCDAD5', rough=0.7), bevel=0, name='Back', coll=coll, origin='bottom')
    tin = lib.mat('Tin', '#C9CCCF', rough=0.28, metal=1.0)
    price = lib.mat('PriceStrip', '#F3D23C', rough=0.5)
    groups = ['#B32D2A', '#3E7B3A', '#E5B532', '#2C5A8E', '#C9622B', '#2F5FA8', '#7A1F2B']
    for z in (0.72, 1.06, 1.4, 1.74):
        lib.box((3.2, 0.55, 0.025), (0, 0.28, z), shelf_m, bevel=0, name='Board', coll=coll, origin='bottom')
        lib.box((3.2, 0.012, 0.045), (0, 0.0, z - 0.01), price, bevel=0, name='Price', coll=coll, origin='bottom')
        x = -1.55
        while x < 1.5:
            col = rng.choice(groups)
            n = rng.randint(6, 12)
            lm = label_mat(col)
            for k in range(n):
                if x > 1.52:
                    break
                for row in (0, 1):
                    y = 0.06 + row * 0.085
                    zt = z + 0.025
                    lib.cyl(0.038, 0.1, (x, y, zt + 0.005), lm, verts=20, name='Can', coll=coll, origin='bottom')
                    lib.cyl(0.036, 0.006, (x, y, zt + 0.105), tin, verts=20, name='CanTop', coll=coll, origin='bottom')
                    lib.cyl(0.036, 0.006, (x, y, zt), tin, verts=20, name='CanBottom', coll=coll, origin='bottom')
                x += 0.08
            x += 0.03
    lib.light('AREA', (0.3, -0.8, 2.4), (math.radians(30), 0, 0), energy=170, color='#F4F6FF', size=2.0, name='ShopL', coll=coll)
    # dolly along the shelf
    cam = lib.camera((0.95, -0.72, 1.33), (-0.1, 0.2, 1.17), lens=40, dof=1.15, fstop=2.8)
    lib.animate_camera(cam, [(0, (0.95, -0.72, 1.33)), (dur, (0.4, -0.68, 1.31))], [(0, (-0.1, 0.2, 1.17)), (dur, (-0.65, 0.2, 1.15))])
    cam.data.clip_start = 0.05
    return dict(fill=0.5, exposure=0.15, still_t=0.5)


# ----------------------------------------------------------------------------- living room at night
def v_room(shot):
    dur = shot['dur']
    rng = random.Random(19)
    coll = lib.collection('Living')
    pc.night_sky(milky=0.6)
    pc.sun((-0.35, 1.0, 0.45), 0.35, '#A9BEE6', angle=1.0, name='Moon')
    floor = lib.mat('Parquet', '#8B6A4B', rough=0.5, var=0.25, var_scale=6, bump=0.12, bump_scale=40)
    shell(coll, 5.2, 4.6, 2.7, wall='#CFC5B5', floor=floor, back=False, y0=-2.4, name='Lv')
    window_wall(coll, 2.2, 5.2, 2.7, sill=0.85, top=2.45, wall='#CFC5B5', panes=2)
    # dark houses across the yard
    facs = pcity.facade_set(0.0, prefix='YardF')
    for (x, y, w, h) in ((-26, 70, 30, 22), (24, 80, 26, 26), (0, 120, 44, 34)):
        lib.box((w, 14, h), (x, y, -6), rng.choice(facs)[0], bevel=0.1, name='Yard', coll=coll, origin='bottom')
    lib.plane((400, 400), (0, 60, -6), lib.mat('YardGround', '#2A2D2C', rough=0.9), name='YardGround', coll=coll)
    # sofa against the window
    fab = lib.mat('SofaFab', '#5E6B73', rough=0.9, var=0.08, var_scale=20, bump=0.2, bump_scale=120)
    lib.box((2.2, 0.92, 0.3), (0, 1.62, 0.0), fab, bevel=0.06, name='SofaBase', coll=coll, origin='bottom')
    for sx in (-0.52, 0.52):
        lib.box((1.02, 0.78, 0.12), (sx, 1.55, 0.3), fab, bevel=0.05, name='Cushion', coll=coll, origin='bottom')
        lib.box((1.0, 0.24, 0.48), (sx, 1.98, 0.38), fab, bevel=0.08, rot=(-0.12, 0, 0), name='BackCushion', coll=coll, origin='bottom')
    for sx in (-1.1, 1.1):
        lib.box((0.2, 0.92, 0.6), (sx, 1.62, 0.0), fab, bevel=0.06, name='Arm', coll=coll, origin='bottom')
    lib.box((0.42, 0.14, 0.36), (-0.75, 1.88, 0.42), lib.mat('Pillow', '#C9A66B', rough=0.9), rot=(-0.25, 0, 0.15), bevel=0.06,
            name='Pillow', coll=coll, origin='bottom')
    h = pc.hero((0.15, 1.55, 0.0), heading=0.0, coll=coll, pose='sit')
    pc.key_rot(h['head'], 2, [(0, 0.0), (dur * 0.45, 0.0), (dur * 0.8, -0.28), (dur, -0.3)])
    # coffee table with a candle, a rug, a dark TV, a bookcase
    wood = lib.mat('RoomWood', '#6E4F37', rough=0.55, var=0.2, var_scale=8)
    lib.box((2.6, 1.7, 0.012), (0, 0.6, 0.0), lib.mat('Rug', '#7A3F36', rough=0.95, var=0.15, var_scale=8), bevel=0, name='Rug', coll=coll,
            origin='bottom')
    lib.box((1.0, 0.55, 0.04), (0, 0.55, 0.42), wood, bevel=0.01, name='CTable', coll=coll, origin='bottom')
    for lx in (-0.44, 0.44):
        for ly in (0.33, 0.77):
            lib.box((0.04, 0.04, 0.42), (lx, ly, 0.0), wood, bevel=0.005, name='CTLeg', coll=coll, origin='bottom')
    lib.cyl(0.032, 0.11, (0.18, 0.5, 0.46), lib.mat('Wax', '#F1E9D8', rough=0.5), verts=16, name='Candle', coll=coll, origin='bottom')
    flame, _ = lib.emission_mat('Flame', '#FFB15A', 40.0)
    fl = lib.sphere(1.0, (0.18, 0.5, 0.595), flame, 10, 8, scale=(0.011, 0.011, 0.03), name='Flame', coll=coll)
    candle = lib.light('POINT', (0.18, 0.5, 0.62), energy=45, color='#FFA552', size=0.03, name='CandleL', coll=coll)
    # the candle is alive: the flame sways and the light breathes
    pc.flicker_light(candle, 45, 9, 0, dur + 0.2, rate=9.0, seed=5)
    lib.add_sine(fl, 'scale', 2, 0.004, 0.37)
    lib.add_sine(fl, 'location', 0, 0.0015, 0.53, phase=1.1)
    lib.box((0.14, 0.2, 0.03), (-0.25, 0.6, 0.46), lib.mat('Book', '#2F4E6B', rough=0.7), rot=(0, 0, 0.3), bevel=0.003, name='Book', coll=coll,
            origin='bottom')
    lib.box((1.3, 0.06, 0.76), (-2.45, 0.4, 0.9), lib.mat('TV', '#0E0F10', rough=0.15, spec=0.8), rot=(0, 0, math.pi / 2), bevel=0.01,
            name='TV', coll=coll, origin='bottom')
    lib.box((0.45, 1.6, 0.55), (-2.35, 0.4, 0.0), wood, bevel=0.01, name='TVStand', coll=coll, origin='bottom')
    lib.box((0.35, 1.2, 2.0), (2.42, 0.2, 0.0), wood, bevel=0.01, name='Bookcase', coll=coll, origin='bottom')
    for z in (0.4, 0.85, 1.3, 1.75):
        y = -0.35
        while y < 0.75:
            w = rng.uniform(0.03, 0.06)
            c = rng.choice(['#7A2E2A', '#2F4E6B', '#C9A66B', '#3E5A3A', '#D8D0BC', '#5A3A5E'])
            lib.box((0.22, w, rng.uniform(0.2, 0.3)), (2.3, y, z), lib.mat('Book' + c, c, rough=0.7), bevel=0.002, name='Book', coll=coll, origin='bottom')
            y += w + 0.004
    lib.cyl(0.02, 1.55, (1.45, 1.75, 0.0), iron_mat(), verts=8, name='LampPole', coll=coll, origin='bottom')
    lib.cyl(0.2, 0.25, (1.45, 1.75, 1.5), lib.mat('LampShade', '#E8DFCC', rough=0.8), verts=24, r2=0.13, name='LampShade', coll=coll)
    cam = lib.camera((1.25, -1.55, 1.42), (0.05, 1.35, 0.82), lens=40)
    lib.animate_camera(cam, [(0, (1.25, -1.55, 1.42)), (dur, (1.0, -1.15, 1.38))], [(0, (0.05, 1.35, 0.82)), (dur, (0.1, 1.35, 0.84))])
    cam.data.clip_start = 0.05
    lib.bloom(0.35, 0.9, 7)
    return dict(fill=0.35, fill_col='#C9D3EA', exposure=1.4, still_t=0.5)


# ----------------------------------------------------------------------------- the front door
def hallway(coll, rng, door_open=0.0, outside=6.0):
    lib.world_color('#000000', 0.0)
    paper = lib.mat('Wallpaper', '#BFAF93', rough=0.9, var=0.12, var_scale=25, bump=0.1, bump_scale=200)
    floor = lib.mat('Laminate', '#7E5E42', rough=0.5, var=0.22, var_scale=6, bump=0.1, bump_scale=40)
    shell(coll, 1.7, 4.4, 2.6, wall='#BFAF93', floor=floor, back=False, y0=-3.4, name='Hall')
    for o in bpy.data.objects:
        if o.name.startswith('HallLeft') or o.name.startswith('HallRight'):
            o.data.materials.clear(); o.data.materials.append(paper)
    yb = 1.0
    frame_m = lib.mat('DoorFrame', '#3B2A20', rough=0.5)
    wallm = paper
    # end wall with the door opening (0.9 x 2.05)
    lib.box((0.4, 0.14, 2.6), (-0.65, yb + 0.07, 0), wallm, bevel=0, name='EndL', coll=coll, origin='bottom')
    lib.box((0.4, 0.14, 2.6), (0.65, yb + 0.07, 0), wallm, bevel=0, name='EndR', coll=coll, origin='bottom')
    lib.box((0.9, 0.14, 0.55), (0, yb + 0.07, 2.05), wallm, bevel=0, name='EndTop', coll=coll, origin='bottom')
    for x in (-0.47, 0.47):
        lib.box((0.07, 0.18, 2.1), (x, yb + 0.05, 0), frame_m, bevel=0.01, name='Jamb', coll=coll, origin='bottom')
    lib.box((1.01, 0.18, 0.07), (0, yb + 0.05, 2.06), frame_m, bevel=0.01, name='Lintel', coll=coll, origin='bottom')
    # door leaf: brown leatherette with brass studs, hinge on the left, opens outwards
    hinge = lib.empty('DoorHinge', (-0.43, yb + 0.1, 0.0), (0, 0, door_open), coll=coll)
    leather = lib.mat('Leatherette', '#4A3124', rough=0.55, var=0.12, var_scale=12, bump=0.35, bump_scale=18)
    leaf = lib.box((0.86, 0.06, 2.0), (0.43, 0.0, 1.02), leather, bevel=0.01, name='DoorLeaf', coll=coll)
    leaf.parent = hinge
    brass = lib.mat('Brass', '#B8944E', rough=0.3, metal=1.0)
    for i in range(4):
        for j in range(8):
            s = lib.sphere(0.008, (0.15 + i * 0.19, -0.032, 0.22 + j * 0.23), brass, 8, 6, name='Stud', coll=coll)
            s.parent = hinge
    steel = lib.mat('Handle', '#C9CACC', rough=0.25, metal=1.0)
    for o in (lib.box((0.03, 0.02, 0.2), (0.76, -0.04, 1.02), steel, bevel=0.005, name='HandlePlate', coll=coll),
              lib.box((0.14, 0.03, 0.022), (0.7, -0.065, 1.08), steel, bevel=0.006, name='Handle', coll=coll),
              lib.cyl(0.018, 0.012, (0.76, -0.04, 0.92), steel, rot=(math.pi / 2, 0, 0), verts=14, name='Keyhole', coll=coll),
              lib.cyl(0.012, 0.07, (0.43, 0.0, 1.55), steel, rot=(math.pi / 2, 0, 0), verts=14, name='Peephole', coll=coll)):
        o.parent = hinge
    # outside: the landing, lit by someone's torch
    land_m, land_s = pc.glow_mat('Landing', '#FFF1DA', outside * 0.15)
    lib.plane((3, 2), (0, yb + 1.3, 0.001), land_m, name='LandingGlow', coll=coll)
    lib.light('AREA', (0.1, yb + 0.9, 0.35), (math.radians(-80), 0, 0), energy=outside * 22, color='#FFF0D8', size=0.6, name='Torch',
              coll=coll)
    lib.box((2.0, 0.1, 2.6), (0, yb + 2.4, 0), lib.mat('LandingWall', '#6E7A6E', rough=0.9), bevel=0, name='LandingWall', coll=coll,
            origin='bottom')
    lib.box((2.4, 2.4, 0.1), (0, yb + 1.3, 2.6), lib.mat('LandingCeil', '#5A5E58', rough=0.9), bevel=0, name='LandingCeil', coll=coll,
            origin='bottom')
    # inside: a doormat, shoes, a coat rack, a key bowl on a small cabinet
    lib.box((0.8, 0.5, 0.012), (0, yb - 0.35, 0.0), lib.mat('Mat', '#4A4038', rough=0.95, bump=0.3, bump_scale=120), bevel=0, name='Doormat',
            coll=coll, origin='bottom')
    for k, (x, c) in enumerate(((-0.25, '#1F1C1A'), (-0.08, '#1F1C1A'), (0.22, '#E9E7E1'), (0.36, '#E9E7E1'))):
        lib.box((0.1, 0.27, 0.09), (x, yb - 0.4 + (k % 2) * 0.02, 0.012), lib.mat('Shoe' + c, c, rough=0.6), rot=(0, 0, 0.1 * (k - 1.5)),
                bevel=0.03, name='Shoe', coll=coll, origin='bottom')
    lib.box((0.04, 0.9, 0.06), (-0.83, -0.2, 1.75), frame_m, bevel=0.01, name='Rack', coll=coll)
    for k, c in enumerate(('#2D3B54', '#6B4E3D', '#D9682A')):
        lib.box((0.16, 0.42, 0.85), (-0.74, -0.5 + k * 0.3, 1.32), lib.mat('Coat' + c, c, rough=0.85), rot=(0, 0.05, 0), bevel=0.06,
                name='Coat', coll=coll, origin='bottom')
    lib.box((0.36, 0.7, 0.85), (0.66, -0.4, 0.0), lib.mat('Cabinet', '#D9D2C4', rough=0.6), bevel=0.01, name='Cabinet', coll=coll, origin='bottom')
    lib.cyl(0.1, 0.035, (0.62, -0.35, 0.85), lib.mat('Bowl', '#3E5A6B', rough=0.3), verts=24, r2=0.06, name='Bowl', coll=coll, origin='bottom')
    lib.box((0.02, 0.5, 0.8), (0.84, -0.4, 1.2), lib.mat('Mirror', '#C9D2D8', rough=0.03, metal=1.0), bevel=0.005, name='Mirror', coll=coll,
            origin='bottom')
    # weak warm light from the room behind the camera (a candle there)
    lib.light('AREA', (0.0, -3.2, 1.6), (math.radians(90), 0, 0), energy=26, color='#FFC98E', size=1.2, name='RoomGlow', coll=coll)
    return land_s


def v_knock(shot, variant):
    dur = shot['dur']
    rng = random.Random(20)
    coll = lib.collection('Hall')
    ev = shot.get('events', {})
    if variant == 'knock':
        land_s = hallway(coll, rng, door_open=0.0, outside=14.0)
        hinge, torch = bpy.data.objects['DoorHinge'], bpy.data.objects['Torch']
        # someone stands outside: the light on the landing dips (a shadow), then three knocks rattle the door
        tk = ev.get('knock', dur * 0.55)
        e0 = 14.0 * 22
        pc.key_light(torch, [(0, e0), (tk - 0.75, e0), (tk - 0.4, e0 * 0.35), (tk - 0.1, e0 * 0.55), (dur, e0 * 0.5)])
        for t, v in ((0, 14 * 0.15), (tk - 0.75, 14 * 0.15), (tk - 0.4, 14 * 0.05), (tk - 0.1, 14 * 0.08), (dur, 14 * 0.075)):
            lib.key_value(land_s, F(t), v)
        keys = [(0, 0.0)]
        for k in range(3):
            t = tk + k * 0.22
            keys += [(t - 0.02, 0.0), (t + 0.02, -0.006), (t + 0.08, 0.0)]
        for t, v in keys:
            P2._key(hinge, 'rotation_euler', 2, F(t), v)
        cam = lib.camera((0.22, -2.7, 1.55), (0.0, 1.0, 1.08), lens=36)
        lib.animate_camera(cam, [(0, (0.22, -2.7, 1.55)), (dur, (0.16, -2.2, 1.5))], [(0, (0.0, 1.0, 1.08)), (dur, (0.0, 1.0, 1.05))])
        out = dict(fill=0.22, fill_col='#FFE9D2', exposure=0.75, still_t=0.5)
    else:
        land_s = hallway(coll, rng, door_open=0.0, outside=14.0)
        hinge, torch = bpy.data.objects['DoorHinge'], bpy.data.objects['Torch']
        # the door slowly opens and the light from the landing floods in
        P2._key(hinge, 'rotation_euler', 2, F(0), 0.0)
        P2._key(hinge, 'rotation_euler', 2, F(0.5), 0.0)
        P2._key(hinge, 'rotation_euler', 2, F(min(6.0, dur)), 0.35)
        pc.key_light(torch, [(0, 14 * 22), (0.5, 14 * 22), (min(6.0, dur), 30 * 22)])
        for t, v in ((0, 14 * 0.15), (0.5, 14 * 0.15), (min(6.0, dur), 30 * 0.15)):
            lib.key_value(land_s, F(t), v)
        cam = lib.camera((0.2, -2.45, 1.55), (0.05, 1.0, 1.1), lens=36)
        lib.animate_camera(cam, [(0, (0.2, -2.45, 1.55)), (dur, (0.14, -1.85, 1.5))], [(0, (0.05, 1.0, 1.1)), (dur, (0.1, 1.2, 1.08))])
        out = dict(fill=0.22, fill_col='#FFE9D2', exposure=0.75, still_t=0.3)
    cam.data.clip_start = 0.05
    lib.bloom(0.4, 0.9, 8)
    return out


def build(shot, fps=60):
    lib.FPS = fps
    v = shot['variant']
    if v in ('knock', 'cta'):
        return v_knock(shot, v)
    return {'cafe': v_cafe, 'station': v_station, 'shops': v_shops, 'bread': v_bread, 'cans': v_cans, 'room': v_room}[v](shot)
