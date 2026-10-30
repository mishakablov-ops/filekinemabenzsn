"""Sets of the series «Каждому по способности», episodes 3-5 («Академия», «Наставник», «Нападение»), Blender 5.2:
sky()        light presets: morning, day, sunset, night
academy()    the Academy of heroes on a hill over the city: two glass towers, a sky bridge, the hall with the emblem,
             the plaza with wide steps, the gate with the sign, an avenue of autumn trees, the city in the haze
arena()      the exam arena: an oval bowl of stands, a sand field, flags, a crowd (cheap two-piece people)
golem()      a stone golem from boulders (walks, swings, crumbles into a heap)
atlant()     the mentor Atlant: a big hero (blue suit, red cape, two golden tufts) and his thin true form
One function per scene lives in akad_e3.py / akad_e4.py / akad_e5.py; build() dispatches by shot['part'].
"""
import math
import os
import random

import bpy
from mathutils import Vector as V

import lib
import pcity
import pcommon as pc
import people2 as P2
import sila as S
import sila_fx as FX

F = lib.sec2f
FONTS = (r'C:\Windows\Fonts\arialbd.ttf', '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
         '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf')
FONT = next((f for f in FONTS if os.path.exists(f)), None)
AURA = ['#FFC857', '#7FD8FF', '#FF7AB6', '#9DFF8A', '#C59BFF', '#FF9C5B', '#6FFFE1', '#FFE66B']


def _ev(shot, k, d):
    return shot.get('events', {}).get(k, d)


# ============================================================================= light
def sky(kind='day', sun_dir=None):
    """Warm, light skies (Классика): morning gold, clear day, sunset orange, a blue night with lit windows."""
    lib.world_color('#000000', 0.0)
    if kind == 'morning':
        d = sun_dir or (-0.6, -0.5, 0.28)
        pc.day_sky(d, top='#7FA9D6', horizon='#F6D9B0', below='#A59A88', strength=1.1, glow='#FFD9A0', fog=0.0018,
                   fog_col='#EBD8BE', glow_size=0.12, glow_strength=2.4)
        return pc.sun(d, 4.2, '#FFD7A2', 1.2, name='AkSun')
    if kind == 'sunset':
        d = sun_dir or (0.7, 0.55, 0.12)
        pc.day_sky(d, top='#3B5287', horizon='#F7A869', below='#5C4A4E', strength=0.95, glow='#FF9A55', fog=0.002,
                   fog_col='#B98E86', glow_size=0.18, glow_strength=2.8)
        return pc.sun(d, 2.6, '#FF9E62', 1.5, name='AkSun')
    if kind == 'night':
        d = sun_dir or (0.3, 0.6, 0.35)
        pc.day_sky(d, top='#121C38', horizon='#3A4A78', below='#1A1D2A', strength=0.7, glow='#8FA6E0', fog=0.0016,
                   fog_col='#2E3958', glow_size=0.05, glow_strength=0.6)
        return pc.sun(d, 0.35, '#9DB5FF', 2.0, name='AkMoon')
    d = sun_dir or (-0.45, -0.6, 0.5)
    pc.day_sky(d, top='#5F97D3', horizon='#E8E4D8', below='#9C9484', strength=1.1, glow='#FFF0D0', fog=0.0012,
               fog_col='#DCE2E6', glow_size=0.1, glow_strength=1.8)
    return pc.sun(d, 4.6, '#FFEBD0', 1.0, name='AkSun')


def text(body, size, loc, rot, m, coll, extrude=0.05, name='AkText', align='CENTER'):
    return lib.text_obj(body, size=size, loc=loc, rot=rot, mat_=m, font=FONT, extrude=extrude, align=align, name=name,
                        coll=coll)


# ============================================================================= the academy
def glass_mat(name, glass='#5C8DBA', frame='#EEF1F2', px=2.4, pz=3.6, lit=0.0, glow='#FFD9A0', seed=0.0):
    """Curtain wall: glass panels in a white grid (object coords: x+y across, z up). lit > 0: that share of panels
    glows warm (evening/night windows)."""
    key = f'{name}'
    m = bpy.data.materials.get(key)
    if m:
        return m
    m = bpy.data.materials.new(key)
    m.use_nodes = True
    nt = m.node_tree
    L = nt.links
    p = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    L.new(tc.outputs['Object'], sep.inputs[0])

    def mth(op, a=None, b=None, v1=None, v2=None):
        n = nt.nodes.new('ShaderNodeMath')
        n.operation = op
        if a is not None:
            L.new(a, n.inputs[0])
        elif v1 is not None:
            n.inputs[0].default_value = v1
        if b is not None:
            L.new(b, n.inputs[1])
        elif v2 is not None:
            n.inputs[1].default_value = v2
        return n.outputs[0]

    u = mth('ADD', sep.outputs['X'], sep.outputs['Y'])
    fu = mth('FRACT', mth('DIVIDE', u, v2=px))
    fz = mth('FRACT', mth('DIVIDE', sep.outputs['Z'], v2=pz))
    # frame where the fraction is near 0 or 1 (mullions 0.12 m wide, floor bands 0.35 m)
    eu = mth('MINIMUM', fu, mth('SUBTRACT', None, fu, v1=1.0))
    ez = mth('MINIMUM', fz, mth('SUBTRACT', None, fz, v1=1.0))
    fr_u = mth('LESS_THAN', eu, v2=0.06 / px)
    fr_z = mth('LESS_THAN', ez, v2=0.18 / pz)
    fr = mth('MAXIMUM', fr_u, fr_z)
    mix = nt.nodes.new('ShaderNodeMix')
    mix.data_type = 'RGBA'
    L.new(fr, mix.inputs['Factor'])
    mix.inputs['A'].default_value = lib.C(glass)
    mix.inputs['B'].default_value = lib.C(frame)
    L.new(mix.outputs['Result'], p.inputs['Base Color'])
    rough = mth('ADD', mth('MULTIPLY', fr, v2=0.55), v2=0.06)
    L.new(rough, p.inputs['Roughness'])
    metal = mth('SUBTRACT', None, fr, v1=0.55)
    L.new(mth('MAXIMUM', metal, v2=0.0), p.inputs['Metallic'])
    if lit > 0:
        cell = nt.nodes.new('ShaderNodeCombineXYZ')
        L.new(mth('FLOOR', mth('DIVIDE', u, v2=px)), cell.inputs['X'])
        L.new(mth('FLOOR', mth('DIVIDE', sep.outputs['Z'], v2=pz)), cell.inputs['Y'])
        cell.inputs['Z'].default_value = seed
        wn = nt.nodes.new('ShaderNodeTexWhiteNoise')
        wn.noise_dimensions = '3D'
        L.new(cell.outputs[0], wn.inputs['Vector'])
        on = mth('LESS_THAN', wn.outputs['Value'], v2=lit)
        on = mth('MULTIPLY', on, mth('SUBTRACT', None, fr, v1=1.0))
        L.new(on, p.inputs['Emission Strength'])
        p.inputs['Emission Color'].default_value = lib.C(glow)
        em = p.inputs['Emission Strength']
        L.new(mth('MULTIPLY', on, v2=4.0), em)
    return m


def tower(coll, x0, x1, y0, y1, h, gm, cap, name):
    lib.box((x1 - x0, y1 - y0, h), ((x0 + x1) / 2, (y0 + y1) / 2, 0), gm, bevel=0.15, name=name, coll=coll, origin='bottom')
    lib.box((x1 - x0 + 0.6, y1 - y0 + 0.6, 0.8), ((x0 + x1) / 2, (y0 + y1) / 2, h), cap, bevel=0.1, name=name + 'Cap', coll=coll,
            origin='bottom')


def academy(coll, rng, lit=0.0, crowd=True, dur=4.0, trees=True, city=True):
    """The Academy faces -Y. Plaza at z=0, the steps from y=-24 down to the avenue (z=-2.4), the gate at y=-70."""
    white = lib.mat('AkWhite', '#EEEBE4', rough=0.55)
    stone = lib.mat('AkStone', '#D9D2C4', rough=0.8, var=0.08, var_scale=2.0)
    gold = lib.mat('AkGold', '#E7B64A', rough=0.3, metal=0.85)
    gm = glass_mat(f'AkGlass{int(lit * 100)}', lit=lit)
    gm2 = glass_mat(f'AkGlassHall{int(lit * 100)}', glass='#6E9CC4', px=3.0, pz=5.0, lit=lit * 0.8, seed=3.0)
    # two towers and the sky bridge
    tower(coll, -30, -14, -6, 10, 64, gm, white, 'AkTowerL')
    tower(coll, 14, 30, -6, 10, 64, gm, white, 'AkTowerR')
    lib.box((28, 10, 7), (0, 2, 44), gm, bevel=0.1, name='AkBridge', coll=coll, origin='bottom')
    lib.box((28.6, 10.6, 0.6), (0, 2, 51), white, bevel=0.08, name='AkBridgeCap', coll=coll, origin='bottom')
    lib.box((28.6, 10.6, 0.6), (0, 2, 43.4), white, bevel=0.08, name='AkBridgeBase', coll=coll, origin='bottom')
    # the hall between the towers with the golden emblem
    lib.box((28, 18, 18), (0, 1, 0), gm2, bevel=0.15, name='AkHall', coll=coll, origin='bottom')
    lib.box((29, 19, 0.8), (0, 1, 18), white, bevel=0.1, name='AkHallCap', coll=coll, origin='bottom')
    lib.box((10, 0.6, 6.5), (0, -8.2, 0), white, bevel=0.1, name='AkPortal', coll=coll, origin='bottom')
    lib.box((7.6, 0.3, 5.2), (0, -8.55, 0), glass_mat('AkDoor', glass='#3E5E7E', px=1.9, pz=5.2, lit=lit), bevel=0.02,
            name='AkDoor', coll=coll, origin='bottom')
    disc = lib.cyl(4.2, 0.5, (0, -8.6, 12.2), white, rot=(math.pi / 2, 0, 0), verts=64, bevel=0.1, name='AkEmblemDisc', coll=coll)
    em = text('А', 6.0, (0, -8.95, 12.2), (math.pi / 2, 0, 0), gold, coll, extrude=0.25, name='AkEmblem')
    lib.cyl(4.5, 0.4, (0, -8.7, 12.2), gold, rot=(math.pi / 2, 0, 0), verts=64, name='AkEmblemRing', coll=coll)
    hole = lib.cyl(4.15, 0.6, (0, -8.7, 12.2), white, rot=(math.pi / 2, 0, 0), verts=64, name='AkEmblemIn', coll=coll)
    text('АКАДЕМИЯ ГЕРОЕВ', 1.5, (0, -9.0, 7.6), (math.pi / 2, 0, 0), gold, coll, extrude=0.08, name='AkHallSign')
    # plaza, steps, avenue
    lib.box((120, 60, 1.0), (0, -6, -1.0), stone, bevel=0.05, name='AkPlaza', coll=coll, origin='bottom')
    for k in range(8):                                   # wide steps from the plaza edge down to the avenue
        lib.box((44, 1.0, 0.3), (0, -36.0 - (7 - k) * 1.0 + 0.0, -2.4 + k * 0.3), stone, bevel=0.03, name='AkStepB', coll=coll,
                origin='bottom')
    walk = lib.mat('AkWalk', '#CFC6B6', rough=0.85, var=0.1, var_scale=1.2)
    lawn = lib.mat('AkLawn', '#7D9A4A', rough=0.95, var=0.18, var_scale=0.15)
    lib.plane((900, 900), (0, 0, -2.45), lawn, name='AkLawn', coll=coll)
    lib.box((14, 60, 0.1), (0, -73, -2.45), walk, bevel=0, name='AkAvenue', coll=coll, origin='bottom')
    # the gate with the sign
    for sx in (-8.5, 8.5):
        lib.box((1.6, 1.6, 9), (sx, -78, -2.4), white, bevel=0.08, name='AkGatePost', coll=coll, origin='bottom')
        lib.sphere(0.7, (sx, -78, 7.4), gold, 20, 12, name='AkGateBall', coll=coll)
    lib.box((19, 1.2, 1.8), (0, -78, 5.0), white, bevel=0.08, name='AkGateBeam', coll=coll, origin='bottom')
    text('АКАДЕМИЯ ГЕРОЕВ', 1.05, (0, -78.65, 5.9), (math.pi / 2, 0, 0), gold, coll, extrude=0.05, name='AkGateSign')
    # flags on the plaza
    flag_cols = ('#C8323A', '#2F64B0', '#E7B64A')
    for k, x in enumerate((-22, -14, 14, 22)):
        lib.cyl(0.12, 14, (x, -26, 0), white, verts=10, name='AkFlagPole', coll=coll, origin='bottom')
        fl = lib.box((3.2, 0.05, 2.0), (x + 1.7, -26, 12.4), lib.mat('AkFlag' + str(k), flag_cols[k % 3], rough=0.7), bevel=0,
                     name='AkFlag', coll=coll)
        lib.add_sine(fl, 'rotation_euler', 2, 0.18, 1.6 + k * 0.17, k * 1.3)
    if trees:
        autumn = ('#D9A13A', '#E0B54A', '#C9732E', '#9DB04A', '#B8842F', '#E37C4B')
        for side in (-1, 1):
            for k in range(7):
                pcity.tree(side * rng.uniform(10.5, 12.5), -50 - k * 7.5, coll, rng, h=rng.uniform(9, 12), greens=autumn)
            for k in range(5):
                pcity.tree(side * rng.uniform(40, 60), rng.uniform(-60, 20), coll, rng, h=rng.uniform(10, 14), greens=autumn)
    if city:                                              # the city far below and behind, in the haze
        facs = pcity.facade_set(lit, prefix='AkC')
        for k in range(40):
            a = rng.uniform(-math.pi * 0.95, math.pi * 0.95)
            r = rng.uniform(260, 700)
            x, y = math.sin(a) * r, -math.cos(a) * r * 0.6 + 380
            if abs(x) < 120 and y < 200:
                continue
            w, hh = rng.uniform(25, 55), rng.uniform(50, 170)
            lib.box((w, w * rng.uniform(0.7, 1.2), hh), (x, y, -40), facs[k % 4][0], bevel=0.5, name='AkFarTower', coll=coll,
                    origin='bottom')
    return dict(emblem=em, disc=disc)


def flyers(coll, rng, dur, n=6, box=((-40, 40), (-60, 20), (14, 40)), name='AkFlyer'):
    """Students flying around the towers: people2 in the superman pose with a coloured trail aura."""
    out = []
    for k in range(n):
        p = S.folk((0, 0, 0), 0, rng, coll, rng.choice(['girl', 'kid', 'sparky', None]), height=0.9, name=f'{name}{k}')
        S.fly_pose(p, 'forward' if k % 2 else 'one')
        x0, y0, z0 = (rng.uniform(*box[0]), rng.uniform(*box[1]), rng.uniform(*box[2]))
        ang = rng.uniform(0, math.tau)
        sp = rng.uniform(5, 9)
        a = (x0, y0, z0)
        b = (x0 + math.sin(ang) * sp * dur, y0 - math.cos(ang) * sp * dur, z0 + rng.uniform(-3, 3))
        S.fly(p, [(0, a), (dur, b)], tilt=1.3)
        FX.aura(coll, p['torso'], rng.choice(AURA), r=0.5, z=0.0, strength=2.5, alpha=0.4, name=f'{name}Aura{k}')
        out.append(p)
    return out


# ============================================================================= the arena

def ring(name, rin, rout, z0, h, m, coll, n=96, arc=(0.0, math.tau)):
    """Elliptic annulus (a stand row, a wall): inner radii rin=(rx, ry), outer rout, from z0 up by h; arc limits it."""
    import bmesh
    bm = bmesh.new()
    full = abs(arc[1] - arc[0] - math.tau) < 1e-6
    cnt = n if full else n + 1
    rows = []
    for (rx, ry), z in ((rin, z0), (rout, z0), (rout, z0 + h), (rin, z0 + h)):
        row = []
        for k in range(cnt):
            a = arc[0] + (arc[1] - arc[0]) * k / n
            row.append(bm.verts.new((math.cos(a) * rx, math.sin(a) * ry, z)))
        rows.append(row)
    for j in range(4):
        A, B = rows[j], rows[(j + 1) % 4]
        for k in range(cnt if full else cnt - 1):
            k2 = (k + 1) % cnt
            bm.faces.new((A[k], A[k2], B[k2], B[k]))
    if not full:
        for k in (0, cnt - 1):
            bm.faces.new([rows[j][k] for j in range(4)])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return lib.mesh_from_bm(bm, name, m, coll=coll, smooth=False)

def arena(coll, rng, R=(46.0, 34.0), rows=16, crowd=2200, lit=0.0, banner=True):
    """An oval bowl around (0, 0): sand field inside the ellipse R, stands rising outwards, a crowd of cheap people,
    flags on the rim, a roof canopy over the far side, the academy towers peeking over the rim."""
    sand = lib.mat('ArSand', '#D8BF8E', rough=0.95, var=0.12, var_scale=0.4, bump=0.1, bump_scale=30)
    line = lib.mat('ArLine', '#F4EFE6', rough=0.8)
    stand = lib.mat('ArStand', '#CFC8BC', rough=0.85, var=0.05)
    seat_cols = ('#3D6FB4', '#C8473C', '#E5B44A', '#F2F0EA')
    f = lib.cyl(1.0, 0.1, (0, 0, -0.1), sand, verts=96, name='ArField', coll=coll, origin='bottom')
    f.scale = (R[0], R[1], 1)
    ring('ArRing', (R[0] * 0.35 - 0.25, R[1] * 0.35 - 0.25), (R[0] * 0.35, R[1] * 0.35), 0.0, 0.015, line, coll)
    # the wall around the field
    ring('ArWall', (R[0] + 0.3, R[1] + 0.3), (R[0] + 0.9, R[1] + 0.9), -0.1, 2.0, lib.mat('ArWall', '#2F4F7A', rough=0.6), coll)
    # stands: stepped elliptic rows rising outwards
    step_d, step_h = 1.1, 0.55
    for i in range(rows):
        r0 = (R[0] + 0.9 + i * step_d, R[1] + 0.9 + i * step_d)
        r1 = (r0[0] + step_d, r0[1] + step_d)
        m = stand if i % 4 else lib.mat(f'ArSeat{(i // 4) % 4}', seat_cols[(i // 4) % 4], rough=0.7)
        ring(f'ArStand{i}', r0, r1, -0.1, 1.9 + (i + 1) * step_h, m, coll)
    top_z = 1.8 + rows * step_h
    ring('ArRim', (R[0] + 0.9 + rows * step_d, R[1] + 0.9 + rows * step_d), (R[0] + 2.4 + rows * step_d, R[1] + 2.4 + rows * step_d),
         -0.1, top_z + 1.6, lib.mat('ArRim', '#EEEBE4', rough=0.6), coll)
    # canopy over the far (+y) stands
    can = lib.mat('ArCanopy', '#F4F2EC', rough=0.5)
    for k in range(9):
        a = math.pi * (0.15 + 0.7 * k / 8)
        x, y = math.cos(a) * (R[0] + rows * step_d), math.sin(a) * (R[1] + rows * step_d)
        lib.cyl(0.25, 9, (x, y, top_z), can, verts=10, name='ArMast', coll=coll, origin='bottom')
    ring('ArCanopy', (R[0] + 2.0, R[1] + 2.0), (R[0] + rows * step_d + 3.0, R[1] + rows * step_d + 3.0), top_z + 8.5, 0.35, can, coll,
         n=48, arc=(math.pi * 0.12, math.pi * 0.88))
    flag_cols = ('#C8323A', '#2F64B0', '#E7B64A', '#2E9C6A')
    for k in range(24):
        a = math.tau * k / 24
        x, y = math.cos(a) * (R[0] + 2.6 + rows * step_d), math.sin(a) * (R[1] + 2.6 + rows * step_d)
        lib.cyl(0.08, 5, (x, y, top_z + 1.6), line, verts=8, name='ArPole', coll=coll, origin='bottom')
        fl = lib.box((1.6, 0.04, 1.0), (x + 0.85, y, top_z + 6.0), lib.mat('ArFlag' + str(k % 4), flag_cols[k % 4], rough=0.7), bevel=0,
                     name='ArFlag', coll=coll)
        lib.add_sine(fl, 'rotation_euler', 2, 0.2, 1.5 + (k % 5) * 0.13, k * 0.9)
    if banner:
        gold = lib.mat('AkGold', '#E7B64A', rough=0.3, metal=0.85)
        text('ВСТУПИТЕЛЬНЫЙ ЭКЗАМЕН', 1.4, (0, R[1] + 0.25, 1.0), (math.pi / 2, 0, 0), gold, coll, extrude=0.03,
             name='ArBanner')
    if crowd:
        people_cheap(coll, rng, R, rows, step_d, step_h, crowd)
    # the academy towers peeking over the rim
    gm = glass_mat('AkGlass0')
    white = lib.mat('AkWhite', '#EEEBE4', rough=0.55)
    tower(coll, -20, -8, 120, 132, 70, gm, white, 'ArBgTowerL')
    tower(coll, 8, 20, 120, 132, 70, gm, white, 'ArBgTowerR')
    lib.box((16, 8, 6), (0, 126, 50), gm, bevel=0.1, name='ArBgBridge', coll=coll, origin='bottom')
    lib.plane((900, 900), (0, 0, -0.12), lib.mat('AkLawn', '#7D9A4A', rough=0.95, var=0.18, var_scale=0.15), name='ArOutside', coll=coll)
    return dict(top_z=top_z, step_d=step_d, step_h=step_h)


BOARD_ROWS = (('СИ-ДЖЕЙ', '96'), ('СЕЗАР', '94'), ('ДЕНИЗ', '99'))


def scoreboard(coll, zero=None, loc=(0.0, 35.2, 12.5), name='Board'):
    """The exam board hanging under the canopy over the north stands, facing the field (-y).
    zero: None - the new guy's score is a dash; a time - the big '0' lights up then (with a flash); 0.0 - lit from the start."""
    x0, y0, z0 = loc
    W, Hh = 18.0, 9.6
    frame = lib.mat('BoardFrame', '#EEEBE4', rough=0.5)
    lib.box((W + 0.8, 0.7, Hh + 0.8), (x0, y0 + 0.1, z0 - Hh / 2 - 0.4), frame, bevel=0.12, name=name + 'Frame', coll=coll,
            origin='bottom')
    scr, _ = lib.emission_mat(name + 'Screen', '#141B26', 0.6)
    lib.box((W, 0.2, Hh), (x0, y0 - 0.3, z0 - Hh / 2), scr, bevel=0.02, name=name + 'Screen', coll=coll, origin='bottom')
    for sx in (-6.0, 6.0):                                    # the cables up to the canopy
        lib.cyl(0.06, 19.1 - (z0 + Hh / 2 + 0.4), (x0 + sx, y0 + 0.1, z0 + Hh / 2 + 0.4), frame, verts=6, name=name + 'Cable',
                coll=coll, origin='bottom')
    fy = y0 - 0.45
    rot = (math.pi / 2, 0, 0)
    gold, _ = lib.emission_mat(name + 'Gold', '#F2C15A', 2.2)
    txt, _ = lib.emission_mat(name + 'Txt', '#F4EFE6', 1.8)
    hot, hot_s = lib.emission_mat(name + 'Hot', '#FF6A3D', 4.0)
    text('ВСТУПИТЕЛЬНЫЙ ЭКЗАМЕН', 0.95, (x0, fy, z0 + 3.75), rot, gold, coll, extrude=0.0, name=name + 'Head')
    for k, (who, sc) in enumerate(BOARD_ROWS):
        z = z0 + 2.2 - k * 1.25
        text(who, 0.85, (x0 - 8.0, fy, z), rot, txt, coll, extrude=0.0, name=name + 'Who', align='LEFT')
        text(sc, 0.85, (x0 + 8.0, fy, z), rot, txt, coll, extrude=0.0, name=name + 'Sc', align='RIGHT')
    lib.box((W - 1.2, 0.05, 0.06), (x0, fy + 0.02, z0 - 0.9), gold, bevel=0, name=name + 'Rule', coll=coll)
    text('НОВЕНЬКИЙ', 1.25, (x0 - 8.0, fy, z0 - 3.0), rot, txt, coll, extrude=0.0, name=name + 'New', align='LEFT')
    if zero is None:
        text('—', 1.6, (x0 + 6.4, fy, z0 - 3.0), rot, txt, coll, extrude=0.0, name=name + 'Dash')
        return None
    big = text('0', 4.4, (x0 + 6.4, fy, z0 - 3.0), rot, hot, coll, extrude=0.0, name=name + 'Zero')
    if zero > 0:
        dash = text('—', 1.6, (x0 + 6.4, fy, z0 - 3.0), rot, txt, coll, extrude=0.0, name=name + 'Dash')
        FX.key_hide(dash, [(0, True), (zero, False)])
        FX.key_hide(big, [(0, False), (zero, True)])
        FX.key(hot_s.inputs['Strength'], [(zero, 14.0), (zero + 0.35, 4.0)])
    return big


def people_cheap(coll, rng, R, rows, step_d, step_h, n, skip=None, name='Fan'):
    """n spectators on the stands: a body capsule and a head, joined into one mesh per colour (fast).
    30.10.2026: vertices are collected in plain lists and written once per colour (bmesh.ops per person was O(n^2):
    3 minutes for 2200 people); the random sequence is the same, so the crowd is the same."""
    import bmesh
    skin_cols = ('#E0B99A', '#C69C7B', '#8D5E42', '#F1D3B8')
    tops = ('#3D6FB4', '#C8473C', '#E5B44A', '#F2F0EA', '#2E9C6A', '#7A4FA0', '#EE8B3A', '#2C2F36', '#F6C7D2')
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=6, radius=1.0)
    bm.verts.index_update()
    unit = [tuple(v.co) for v in bm.verts]
    tris = [tuple(v.index for v in f.verts) for f in bm.faces]
    bm.free()
    nv = len(unit)
    parts = {}
    for k in range(n):
        i = rng.randrange(rows)
        a = rng.uniform(0, math.tau)
        if skip and skip(a, i):
            continue
        rx, ry = R[0] + 0.9 + (i + 0.55) * step_d, R[1] + 0.9 + (i + 0.55) * step_d
        x, y, z = math.cos(a) * rx, math.sin(a) * ry, 1.8 + (i + 1) * step_h
        top, skin = rng.choice(tops), rng.choice(skin_cols)
        for col, (cz, sx, sz) in ((top, (0.42, 0.26, 0.42)), (skin, (0.86, 0.15, 0.17))):
            verts, faces = parts.setdefault(col, ([], []))
            stand_up = rng.random() < 0.25
            h = 1.0 if not stand_up else 1.35
            o = len(verts)
            verts.extend((vx * sx + x, vy * sx + y, vz * sz + z + cz * h) for vx, vy, vz in unit)
            faces.extend(tuple(j + o for j in f) for f in tris)
    for col, (verts, faces) in parts.items():
        me = bpy.data.meshes.new(f'{name}_{col}')
        me.from_pydata(verts, [], faces)
        me.update()
        me.polygons.foreach_set('use_smooth', [True] * len(me.polygons))
        me.materials.append(lib.pmat(col))
        ob = bpy.data.objects.new(f'{name}_{col}', me)
        (coll or bpy.context.scene.collection).objects.link(ob)
    assert nv > 0


# ============================================================================= the golem
def rock_mat():
    return lib.mat('GolemRock', '#8C847A', rough=0.95, var=0.25, var_scale=1.5, bump=0.4, bump_scale=6)


def boulder(coll, r, loc, rng, m, name='Rock'):
    o = lib.sphere(r, loc, m, 10, 7, scale=(1.0, rng.uniform(0.8, 1.1), rng.uniform(0.75, 1.0)), name=name, coll=coll)
    me = o.data
    for v in me.vertices:
        v.co *= rng.uniform(0.86, 1.12)
    o.rotation_euler = (rng.uniform(0, 3), rng.uniform(0, 3), rng.uniform(0, 3))
    for poly in me.polygons:
        poly.use_smooth = False
    return o


def golem(coll, loc, heading, rng, scale=1.0, glow='#FF9C5B', name='Golem'):
    """A ~7 m stone giant: hips, chest, head, arms and legs are empties carrying boulders. Returns the parts and a list of
    all rocks (for the crumble)."""
    m = rock_mat()
    eye, _ = lib.emission_mat('GolemEye', glow, 12.0)
    root = lib.empty(name, loc, (0, 0, heading), coll=coll)
    root.scale = (scale, scale, scale)
    g = dict(root=root, rocks=[])

    def part(key, par, at, rocks):
        e = lib.empty(f'{name}_{key}', at, coll=coll)
        e.parent = par
        g[key] = e
        for r, off in rocks:
            b = boulder(coll, r, off, rng, m, name=f'{name}_{key}_rock')
            b.parent = e
            g['rocks'].append(b)
        return e

    hips = part('hips', root, (0, 0, 3.2), [(1.1, (0, 0, 0)), (0.8, (0.7, 0.1, 0.2)), (0.8, (-0.7, 0.1, 0.2))])
    chest = part('chest', hips, (0, 0, 1.1), [(1.5, (0, 0, 0.9)), (1.0, (1.1, 0.2, 1.2)), (1.0, (-1.1, 0.2, 1.2)),
                                              (0.9, (0, 0.5, 0.2))])
    head = part('head', chest, (0, -0.2, 2.5), [(0.75, (0, 0, 0.3))])
    for sx in (-0.28, 0.28):
        lib.sphere(0.12, (sx, -0.66, 0.38), eye, 10, 6, name=f'{name}_eye', coll=coll).parent = head
    for side, sx in (('L', 1), ('R', -1)):
        sh = part('arm' + side, chest, (sx * 1.9, 0, 1.4), [(0.8, (sx * 0.2, 0, -0.3)), (0.75, (sx * 0.3, 0, -1.3)),
                                                           (0.7, (sx * 0.3, -0.1, -2.3)), (0.85, (sx * 0.35, -0.2, -3.2))])
        lg = part('leg' + side, hips, (sx * 0.9, 0, -0.4), [(0.85, (0, 0, -0.6)), (0.8, (0, 0, -1.6)), (0.9, (0, -0.25, -2.5))])
    lib.light('POINT', (0, -1.2, 0.3), energy=60.0, color=glow, size=0.3, name=f'{name}_eyeLight').parent = head
    return g


def golem_walk(g, t0, t1, p0, p1, period=1.4):
    """Heavy stomping walk from p0 to p1 (root keys), legs and arms swing, the chest sways."""
    root = g['root']
    n = max(2, int((t1 - t0) / (period / 4)))
    for j in range(n + 1):
        t = t0 + (t1 - t0) * j / n
        w = j / n
        ph = (t - t0) / period * math.tau
        lib.key_obj(root, F(t), loc=tuple(V(p0).lerp(V(p1), w) + V((0, 0, 0.18 * abs(math.sin(ph))))))
        for side, s in (('L', 1), ('R', -1)):
            g['leg' + side].rotation_euler.x = 0.35 * math.sin(ph) * s
            g['leg' + side].keyframe_insert('rotation_euler', index=0, frame=F(t))
            g['arm' + side].rotation_euler.x = -0.3 * math.sin(ph) * s
            g['arm' + side].keyframe_insert('rotation_euler', index=0, frame=F(t))
        g['chest'].rotation_euler.y = 0.06 * math.sin(ph)
        g['chest'].keyframe_insert('rotation_euler', index=1, frame=F(t))


def golem_crumble(g, t, rng, ground=0.0, spread=4.0):
    """At t every rock leaves its limb: a short arc outwards and down into a heap (keys on world positions)."""
    sc = bpy.context.scene
    sc.frame_set(max(1, F(t)))
    bpy.context.view_layer.update()
    world = {o: o.matrix_world.copy() for o in g['rocks']}
    centre = g['root'].matrix_world.translation.copy()
    for o, M in world.items():
        loc = M.translation.copy()
        rot = M.to_euler()
        sc_ = M.to_scale()
        # keep it in place until t
        o.parent = None
        o.matrix_world = M
        lib.key_obj(o, F(t), loc=tuple(loc), rot=tuple(rot), scale=tuple(sc_), interp='LINEAR')
        d = V((loc.x - centre.x, loc.y - centre.y, 0))
        d = d.normalized() if d.length > 0.01 else V((rng.uniform(-1, 1), rng.uniform(-1, 1), 0)).normalized()
        end = V((loc.x, loc.y, 0)) + d * rng.uniform(0.5, spread) + V((0, 0, ground + 0.4 * sc_.x))
        fall = 0.35 + math.sqrt(max(0.1, loc.z) / 9.8) * 0.9
        mid = loc.lerp(end, 0.5) + V((0, 0, rng.uniform(0.2, 0.8)))
        lib.key_obj(o, F(t + fall * 0.45), loc=tuple(mid))
        lib.key_obj(o, F(t + fall), loc=tuple(end), rot=(rot.x + rng.uniform(-2, 2), rot.y + rng.uniform(-2, 2), rot.z))
        lib._set_interp(o, 'LINEAR')
    # the rest of the hierarchy (and the eye light) switches off
    for k in ('head',):
        for c in g[k].children:
            if c.type in ('LIGHT',) or '_eye' in c.name:          # Golem_eye, Golem_eye.001
                FX.key_hide(c, [(0, True), (t, False)])          # keys are (t, visible)


# ============================================================================= the mentor
ATLANT = dict(top='#2F5FB3', pants='#2F5FB3', hair='#F2C94C', skin='#E7BE98', shoe='#C8323A')
ATLANT_THIN = dict(top='#B7B0A3', pants='#4E5258', hair='#E8C860', skin='#E2C3A7', shoe='#3A3631')


def atlant(coll, loc, heading, rng, thin=False, name='Atlant'):
    """The mentor. Big: a broad hero (height 1.45 of a people2 adult, chest 1.5 wide), blue suit with white stripes, red
    cape, red boots, golden hair with two upright tufts and a wide smile. Thin: the same man in a baggy grey shirt,
    narrow, hollow cheeks (the true form)."""
    lk = ATLANT_THIN if thin else ATLANT
    h = 1.12 if thin else 1.45
    p = S.folk(loc, heading, rng, coll, lk, height=h, head=1.15 if not thin else 1.25, name=name)
    if not thin:
        p['torso'].scale = (p['torso'].scale.x * 1.55, p['torso'].scale.y * 1.35, p['torso'].scale.z * 1.05)
        for sd in ('L', 'R'):
            for k, s in (('upper', 1.55), ('fore', 1.4), ('thigh', 1.35), ('shin', 1.25)):
                o = p[k + sd]
                o.scale = (o.scale.x * s, o.scale.y * s, o.scale.z)
            p['upper' + sd].location.x *= 1.45
        white = lib.pmat('#F4F2EC')
        stripe = lib.box((0.07, 0.02, 0.5), (0.0, -0.16, 0.38), white, bevel=0.005, name=name + '_stripe', coll=coll)
        stripe.parent = p['hips']
        belt = lib.cyl(0.2, 0.06, (0, 0, 0.12), lib.pmat('#E7B64A'), verts=20, name=name + '_belt', coll=coll)
        belt.parent = p['hips']
        belt.scale = (1.35, 1.0, 1.0)
        cape = lib.box((0.62, 0.03, 0.95), (0, 0.17, 0.12), lib.pmat('#C8323A'), bevel=0.01, name=name + '_cape', coll=coll)
        cape.parent = p['hips']
        cape.rotation_euler.x = 0.12
        lib.add_sine(cape, 'rotation_euler', 0, 0.06, 1.3, rng.uniform(0, 6), offset=0.12)
    else:
        p['torso'].scale = (p['torso'].scale.x * 0.8, p['torso'].scale.y * 0.8, p['torso'].scale.z)
        for sd in ('L', 'R'):
            for k in ('upper', 'fore', 'thigh', 'shin'):
                o = p[k + sd]
                o.scale = (o.scale.x * 0.72, o.scale.y * 0.72, o.scale.z)
    # two golden tufts (the hero's sign) and a smile
    hair = lib.pmat(lk['hair'])
    for sx in (-1, 1):
        t = lib.cyl(0.035, 0.22, (sx * 0.05, -0.02, 0.1), hair, verts=8, r2=0.005, name=name + '_tuft', coll=coll, origin='bottom')
        t.parent = p['head']
        t.rotation_euler = (-0.35, sx * 0.55, 0)
        if thin:
            t.rotation_euler = (0.9, sx * 1.1, 0)            # the tufts droop
    sm = lib.box((0.1, 0.01, 0.015), (0, -0.112, -0.05), lib.pmat('#FFFFFF' if not thin else '#6B4E3D'), bevel=0.005,
                 name=name + '_smile', coll=coll)
    sm.parent = p['head']
    for sx in (-1, 1):
        e = lib.sphere(0.012, (sx * 0.038, -0.105, 0.01), lib.pmat('#1E2A44'), 8, 6, name=name + '_eye', coll=coll)
        e.parent = p['head']
    p['thin'] = thin
    return p


def puff(coll, loc, t, rng, n=14, r=1.6, col='#F4F1EC', name='Puff'):
    """A white steam puff (Atlant deflating): soft spheres that grow and fade."""
    m, _, _ = FX.glow(name + 'Mat', col, strength=1.2, alpha=0.75)
    for k in range(n):
        o = lib.sphere(1.0, (loc[0] + rng.uniform(-r, r) * 0.5, loc[1] + rng.uniform(-r, r) * 0.5, loc[2] + rng.uniform(-0.3, 1.6)),
                       m, 14, 8, name=name, coll=coll)
        o.visible_shadow = False
        s0, s1 = rng.uniform(0.05, 0.12), rng.uniform(0.5, 1.0) * r
        FX.key_scale(o, [(0, s0 * 0.01), (t, s0), (t + 0.35, s1), (t + 1.6, s1 * 1.35)])
        FX.key_hide(o, [(0, True), (t, False), (t + 1.7, True)])
        lib.key_obj(o, F(t + 1.6), loc=(o.location.x, o.location.y, o.location.z + 1.2))


# ============================================================================= dispatcher
def build(shot, fps=30):
    lib.FPS = fps
    import importlib
    mod = importlib.import_module('akad_e' + str(shot.get('part', '3')))
    fn = getattr(mod, 'v_' + shot['variant'], None)
    if fn is None:
        raise SystemExit('unknown variant ' + shot['variant'])
    return fn(shot, fps) or {}
