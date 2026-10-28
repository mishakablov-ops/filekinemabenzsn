"""«Подъезд» for «Каждому по способности» (28.10.2026): the stairwell of the hero's old five-storey block on a sunny
morning. Not the city (the user: «с добавлением города разнообразия меньше стало, дай волю креативности»).

Plan (metres): the hero's landing is z = 0, y in [0, YL], the wall with his door at y = 0 (door at x = DOOR_X, it opens
onto the landing), the neighbour's door on the right wall. From the landing a flight goes DOWN on the right (x > 0) to
the half landing at z = -1.4 with the window (wall y = YW), another goes UP on the left. The queue stands on the flight
down. Two-tone walls (soft teal paint up to 1.5 m, whitewash above), terracotta tiles, a varnished handrail on dark
balusters, a yellow gas pipe, geraniums and a sleeping ginger cat on the sill, morning sun through the window into
a little dust.

stairwell(coll, rng) builds it; gz(x, y) is the floor height for people; the scenes are at the end of the file.
"""
import math
import random

import bmesh
import bpy
from mathutils import Vector as V

import lib
import pcity
import pcommon as pc
import people2 as P2
import sila as S
import sila_fx as FX
import sila_hero as H

F = lib.sec2f
W = 1.4                      # x in [-W, W]
YL = 1.5                     # the floor landing: y in [0, YL]
RUN = 2.4                    # one flight along y
YH = YL + RUN                # the half landings start here
YW = 5.2                     # the window wall
HF = 2.8                     # floor to floor
N = 9                        # risers in a flight
TR, RS = RUN / (N - 1), HF / 2 / N
GAP = 0.12                   # half the gap between the flights
DOOR_X, DOOR_W = -0.72, 0.9  # his door
PAINT, PAINT_LINE, WHITE = '#86AFA3', '#5C8679', '#EEE7DA'
AURA = ['#FFC857', '#7FD8FF', '#FF7AB6', '#9DFF8A', '#C59BFF', '#FF9C5B', '#6FFFE1', '#FFE66B']


def gz(x, y):
    """Floor height at (x, y) on the landing, the flight down (x > 0) and the lower half landing."""
    if y <= YL:
        return 0.0
    if y >= YH:
        return -HF / 2
    if x > 0:
        return -min(N - 1, int((y - YL) / TR) + 1) * RS
    return min(N - 1, int((y - YL) / TR) + 1) * RS


# ----------------------------------------------------------------------------- geometry helpers
def _prism(name, pts, axis, a0, a1, m, coll):
    """Polygon pts in the plane across `axis` ('x': points are (y, z); 'y': points are (x, z)) extruded from a0 to a1."""
    bm = bmesh.new()

    def P(u, v, a):
        return (a, u, v) if axis == 'x' else (u, a, v)
    f0 = bm.faces.new([bm.verts.new(P(u, v, a0)) for u, v in pts])
    f1 = bm.faces.new([bm.verts.new(P(u, v, a1)) for u, v in reversed(pts)])
    n = len(pts)
    v0, v1 = list(f0.verts), list(reversed(list(f1.verts)))
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new([v0[j], v0[i], v1[i], v1[j]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return lib.mesh_from_bm(bm, name, m, smooth=False, coll=coll)


def _tiles():
    """Terracotta and cream tiles 10 cm, with grout and wear."""
    m = bpy.data.materials.new('StairTiles')
    m.use_nodes = True
    nt = m.node_tree
    p = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord')
    ch = nt.nodes.new('ShaderNodeTexChecker')
    ch.inputs['Scale'].default_value = 10.0
    ch.inputs['Color1'].default_value = lib.C('#9C5539')
    ch.inputs['Color2'].default_value = lib.C('#D8C7A6')
    br = nt.nodes.new('ShaderNodeTexBrick')
    br.offset = 0.0
    br.inputs['Scale'].default_value = 10.0
    br.inputs['Mortar Size'].default_value = 0.006
    br.inputs['Brick Width'].default_value = 1.0
    br.inputs['Row Height'].default_value = 1.0
    nz = nt.nodes.new('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = 3.0
    mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (0.1, 0.1, 0.1)
    nt.links.new(tc.outputs['Object'], ch.inputs['Vector'])
    nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
    nt.links.new(mp.outputs['Vector'], br.inputs['Vector'])
    nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
    grout = nt.nodes.new('ShaderNodeMix'); grout.data_type = 'RGBA'
    nt.links.new(br.outputs['Fac'], grout.inputs['Factor'])
    nt.links.new(ch.outputs['Color'], grout.inputs['A'])
    grout.inputs['B'].default_value = lib.C('#7A7166')
    wear = nt.nodes.new('ShaderNodeMix'); wear.data_type = 'RGBA'; wear.blend_type = 'MULTIPLY'
    mr = nt.nodes.new('ShaderNodeMapRange')
    mr.inputs['To Min'].default_value = 0.85
    nt.links.new(nz.outputs['Fac'], mr.inputs['Value'])
    wear.inputs['Factor'].default_value = 1.0
    nt.links.new(grout.outputs['Result'], wear.inputs['A'])
    nt.links.new(mr.outputs['Result'], wear.inputs['B'])
    nt.links.new(wear.outputs['Result'], p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = 0.42
    return m


def _flight(coll, x0, x1, y0, z0, dy, dz, step_m, slab_m, name):
    """N-1 treads from the landing edge (y0, z0) along dy (+1/-1), each dz*RS higher, plus the sloping slab under them."""
    for i in range(1, N):
        ya, yb = y0 + dy * (i - 1) * TR, y0 + dy * i * TR
        top = z0 + dz * i * RS
        h = 2 * RS + 0.05
        lib.box((x1 - x0, TR + 0.002, h), ((x0 + x1) / 2, (ya + yb) / 2, top - h / 2), step_m, bevel=0.008, name=name + 'Step', coll=coll)
        # a darker worn strip on the nose of each tread
        lib.box((x1 - x0 - 0.04, 0.05, 0.004), ((x0 + x1) / 2, ya + dy * 0.03, top), slab_m, bevel=0, name=name + 'Nose', coll=coll,
                origin='bottom')
    ye = y0 + dy * RUN
    za, zb = z0 - 1.2 * RS, z0 + dz * HF / 2 - 1.2 * RS - dz * RS
    t = 0.24
    pts = [(y0, za), (ye, zb), (ye, zb - t), (y0, za - t)]
    _prism(name + 'Slab', pts if dy > 0 else list(reversed(pts)), 'x', x0, x1, slab_m, coll)


def _rail(coll, pts, name, wood, iron, floor, step=0.3):
    """Varnished handrail along pts (z = handrail height) on dark balusters every `step` m down to floor(x, y) (or 0.92 m
    below the rail where it turns over a landing)."""
    lib.curve_poly(name, [pts], bevel=0.03, mat_=wood, coll=coll)
    for a, b in zip(pts, pts[1:]):
        a, b = V(a), V(b)
        L = (V((b.x, b.y, 0)) - V((a.x, a.y, 0))).length
        for k in range(max(1, int(L / step))):
            q = a.lerp(b, (k + 0.5) / max(1, int(L / step)))
            z0 = floor(q.x, q.y) if YL <= q.y <= YH else q.z - 0.92
            hgt = q.z - 0.03 - z0
            lib.box((0.016, 0.016, hgt), (q.x, q.y, z0), iron, bevel=0, name=name + 'Bal', coll=coll, origin='bottom')


def _door(coll, x0, y, name, leaf_m, frame_m, number=None, hinge_left=True, open_=0.0):
    """A door on the wall y (facing +y): frame, leaf on a hinge empty (rot z opens it onto the landing)."""
    w = DOOR_W
    for dx in (-w / 2 - 0.03, w / 2 + 0.03):
        lib.box((0.07, 0.06, 2.1), (x0 + dx, y + 0.02, 0), frame_m, bevel=0.008, name=name + 'Jamb', coll=coll, origin='bottom')
    lib.box((w + 0.13, 0.06, 0.07), (x0, y + 0.02, 2.06), frame_m, bevel=0.008, name=name + 'Lintel', coll=coll, origin='bottom')
    hx = x0 - w / 2 + 0.02 if hinge_left else x0 + w / 2 - 0.02
    sgn = 1 if hinge_left else -1
    hinge = lib.empty(name + 'Hinge', (hx, y + 0.03, 0.0), (0, 0, sgn * open_), coll=coll)
    leaf = lib.box((w - 0.04, 0.05, 2.0), (sgn * (w / 2 - 0.02), 0.0, 1.01), leaf_m, bevel=0.012, name=name + 'Leaf', coll=coll)
    leaf.parent = hinge
    steel = lib.mat('DoorSteel', '#C9CACC', rough=0.25, metal=1.0)
    hx2 = sgn * (w - 0.14)
    for o in (lib.box((0.03, 0.02, 0.2), (hx2, 0.035, 1.02), steel, bevel=0.005, name=name + 'Plate', coll=coll),
              lib.box((0.13, 0.03, 0.022), (hx2 - sgn * 0.05, 0.055, 1.08), steel, bevel=0.006, name=name + 'Handle', coll=coll),
              lib.cyl(0.016, 0.012, (hx2, 0.035, 0.93), steel, rot=(math.pi / 2, 0, 0), verts=12, name=name + 'Lock', coll=coll),
              lib.cyl(0.012, 0.06, (sgn * (w / 2 - 0.02), 0.03, 1.55), steel, rot=(math.pi / 2, 0, 0), verts=12, name=name + 'Peep',
                      coll=coll)):
        o.parent = hinge
    if number:
        plate = lib.box((0.12, 0.012, 0.08), (sgn * (w / 2 - 0.02), 0.032, 1.78), lib.mat('NumPlate', '#C9A65A', rough=0.3, metal=0.8),
                        bevel=0.004, name=name + 'Num', coll=coll)
        plate.parent = hinge
        try:
            t = lib.text_obj(number, 0.06, (sgn * (w / 2 - 0.02), 0.04, 1.757), (math.pi / 2, 0, 0), lib.mat('NumInk', '#2A1E14', rough=0.5),
                             extrude=0.002, name=name + 'NumText', coll=coll)
            t.parent = hinge
        except Exception:
            pass
    return hinge, leaf


def _leatherette(coll, hinge, name):
    """Brass studs in a diamond grid over the leaf (the Soviet padded door, like the one inside in a20 / b01)."""
    brass = lib.mat('Brass', '#B8944E', rough=0.3, metal=1.0)
    for i in range(4):
        for j in range(8):
            s = lib.sphere(0.008, (0.15 + i * 0.19 + (0.095 if j % 2 else 0.0), 0.03, 0.22 + j * 0.23), brass, 8, 6, name=name + 'Stud',
                           coll=coll)
            s.parent = hinge


def _cat(coll, loc, rng):
    """A ginger cat asleep in a ring on the sill; it breathes."""
    fur = lib.mat('CatFur', '#D9823B', rough=0.9, var=0.25, var_scale=18, bump=0.15, bump_scale=60)
    pale = lib.mat('CatPale', '#F1D6B4', rough=0.9)
    root = lib.empty('Cat', loc, (0, 0, rng.uniform(0, 6.28)), coll=coll)
    body = lib.sphere(0.13, (0, 0, 0.08), fur, 24, 14, scale=(1.25, 0.95, 0.62), name='CatBody', coll=coll)
    head = lib.sphere(0.075, (0.13, -0.06, 0.08), fur, 20, 12, scale=(1.0, 1.05, 0.9), name='CatHead', coll=coll)
    muzzle = lib.sphere(0.035, (0.185, -0.1, 0.06), pale, 12, 8, scale=(1.0, 0.8, 0.7), name='CatMuzzle', coll=coll)
    ears = [lib.cyl(0.028, 0.05, (0.12 + dx, -0.05 + dy, 0.135), fur, verts=4, r2=0.0, rot=(0.2, 0.0, 0.7), name='CatEar', coll=coll)
            for dx, dy in ((-0.03, 0.03), (0.04, -0.035))]
    tail = lib.curve_poly('CatTail', [[(-0.15, 0.02, 0.04), (-0.12, -0.12, 0.03), (0.0, -0.16, 0.03), (0.12, -0.13, 0.03)]], bevel=0.022,
                          mat_=fur, coll=coll)
    for o in [body, head, muzzle, tail] + ears:
        o.parent = root
    lib.add_sine(body, 'scale', 2, 0.03, 2.6, rng.uniform(0, 6))
    return root


def _geranium(coll, loc, rng, name):
    pot = lib.mat('Terracotta', '#B4643C', rough=0.75, var=0.15, var_scale=10)
    lib.cyl(0.075, 0.13, loc, pot, verts=18, r2=0.055, name=name + 'Pot', coll=coll, origin='bottom')
    leaf = lib.mat('GeraniumLeaf', '#4F7D38', rough=0.8, var=0.3, var_scale=12)
    flower = lib.mat('Geranium', '#E0393E', rough=0.6, emit='#E0393E', emit_strength=0.15)
    x, y, z = loc
    for k in range(7):
        lib.sphere(0.06, (x + rng.uniform(-0.07, 0.07), y + rng.uniform(-0.06, 0.06), z + 0.15 + rng.uniform(0, 0.08)), leaf, 10, 6,
                   scale=(1.2, 1.2, 0.6), name=name + 'Leaf', coll=coll)
    for k in range(4):
        cx, cy, cz = x + rng.uniform(-0.06, 0.06), y + rng.uniform(-0.05, 0.05), z + 0.27 + rng.uniform(0, 0.08)
        for j in range(6):
            lib.sphere(0.017, (cx + rng.uniform(-0.025, 0.025), cy + rng.uniform(-0.025, 0.025), cz + rng.uniform(-0.01, 0.02)), flower,
                       8, 6, name=name + 'Petal', coll=coll)


def _window(coll, z_sill, frame_m, sill_m, name):
    """A tall wooden window in the wall y = YW over x in [-0.65, 0.65], from z_sill + 0.85 for 1.5 m."""
    zb, zt = z_sill + 0.85, z_sill + 2.35
    for x in (-0.65, 0.0, 0.65):
        lib.box((0.07, 0.08, zt - zb), (x, YW + 0.12, zb), frame_m, bevel=0.006, name=name + 'Stile', coll=coll, origin='bottom')
    for z in (zb, zb + 1.05, zt - 0.035):
        lib.box((1.37, 0.08, 0.07), (0, YW + 0.12, z - 0.035), frame_m, bevel=0.006, name=name + 'Rail', coll=coll, origin='bottom')
    lib.box((1.5, 0.34, 0.05), (0, YW - 0.02, zb - 0.05), sill_m, bevel=0.01, name=name + 'Sill', coll=coll, origin='bottom')
    return zb, zt


def stairwell(coll, rng, dust=0.018):
    lib.world_color('#000000', 0.0)
    sun_dir = (0.2, 0.8, 0.56)
    pc.day_sky(sun_dir, top='#7FAEDC', horizon='#F7E6C8', below='#B8A890', strength=1.0, glow='#FFE6BE', fog=0.0, glow_size=0.12,
               glow_strength=2.2)
    sun = pc.sun(sun_dir, 5.5, '#FFE3B8', 1.2, name='StairSun')
    white = lib.mat('Whitewash', WHITE, rough=0.95, var=0.07, var_scale=3, bump=0.05, bump_scale=40)
    paint = lib.mat('WallPaint', PAINT, rough=0.45, var=0.06, var_scale=4)
    line = lib.mat('PaintLine', PAINT_LINE, rough=0.5)
    tiles = _tiles()
    concrete = lib.mat('StepConcrete', '#ADA597', rough=0.8, var=0.12, var_scale=6, bump=0.08, bump_scale=60)
    worn = lib.mat('StepWorn', '#8E877C', rough=0.7, var=0.1, var_scale=10)
    slab = lib.mat('Slab', '#D9D3C7', rough=0.95, var=0.05, var_scale=4)
    wood = lib.mat('Handrail', '#7A4528', rough=0.35, var=0.2, var_scale=30, coat=0.4)
    iron = lib.mat('Baluster', '#2C3530', rough=0.45, metal=0.6)
    frame_m = lib.mat('WinFrame', '#F2EFE8', rough=0.45)

    # floors: our landing, the half landings below / above, the floor landings below / above, a floor deep down
    for (y0, y1, z, nm) in ((0.0, YL, 0.0, 'Landing'), (YH, YW, -HF / 2, 'HalfLow'), (YH, YW, HF / 2, 'HalfUp'),
                            (0.0, YL, -HF, 'LandLow'), (0.0, YL, HF, 'LandUp')):
        lib.box((2 * W, y1 - y0, 0.22), (0, (y0 + y1) / 2, z - 0.11), tiles if nm != 'LandUp' else slab, bevel=0, name=nm, coll=coll)
        lib.box((2 * W, y1 - y0, 0.004), (0, (y0 + y1) / 2, z - 0.222), slab, bevel=0, name=nm + 'Under', coll=coll)
    lib.box((2 * W, YW, 0.2), (0, YW / 2, -HF - 0.3), slab, bevel=0, name='Pit', coll=coll)
    # flights: down on the right, up on the left, from the low half landing down on the left, from the high one up on the right
    _flight(coll, GAP, W, YL, 0.0, 1, -1, concrete, worn, 'FlA')
    _flight(coll, -W, -GAP, YL, 0.0, 1, 1, concrete, worn, 'FlB')
    _flight(coll, -W, -GAP, YH, -HF / 2, -1, -1, concrete, worn, 'FlC')
    _flight(coll, GAP, W, YH, HF / 2, -1, 1, concrete, worn, 'FlD')

    # walls (whitewash), 20 cm thick, from the pit to the top
    zt, zb = 4.5, -HF - 0.3
    hz = (zb + zt) / 2
    lib.box((0.2, YW + 0.4, zt - zb), (W + 0.1, YW / 2, hz), white, bevel=0, name='WallR', coll=coll)
    lib.box((0.2, YW + 0.4, zt - zb), (-W - 0.1, YW / 2, hz), white, bevel=0, name='WallL', coll=coll)
    # the door wall: an opening for his door
    dl, dr = DOOR_X - DOOR_W / 2 - 0.02, DOOR_X + DOOR_W / 2 + 0.02
    lib.box((dl + W + 0.2, 0.2, zt - zb), ((dl - W - 0.2) / 2, -0.1, hz), white, bevel=0, name='WallBackL', coll=coll)
    lib.box((W + 0.2 - dr, 0.2, zt - zb), ((dr + W + 0.2) / 2, -0.1, hz), white, bevel=0, name='WallBackR', coll=coll)
    lib.box((dr - dl, 0.2, zt - 2.07), ((dl + dr) / 2, -0.1, 2.07 + (zt - 2.07) / 2), white, bevel=0, name='WallBackTop', coll=coll)
    lib.box((dr - dl, 0.2, 0 - zb), ((dl + dr) / 2, -0.1, zb / 2), white, bevel=0, name='WallBackLow', coll=coll)
    # the window wall with two window holes (low and high half landings)
    holes = [(-HF / 2 + 0.85, -HF / 2 + 2.35), (HF / 2 + 0.85, HF / 2 + 2.35)]
    lib.box((W + 0.2 - 0.65, 0.25, zt - zb), (-(0.65 + W + 0.2) / 2, YW + 0.125, hz), white, bevel=0, name='WallWinL', coll=coll)
    lib.box((W + 0.2 - 0.65, 0.25, zt - zb), ((0.65 + W + 0.2) / 2, YW + 0.125, hz), white, bevel=0, name='WallWinR', coll=coll)
    edges = [zb] + [z for hl in holes for z in hl] + [zt]
    for k in range(0, len(edges), 2):
        a, b = edges[k], edges[k + 1]
        lib.box((1.3, 0.25, b - a), (0, YW + 0.125, (a + b) / 2), white, bevel=0, name='WallWinMid', coll=coll)
    lib.box((2 * W + 0.4, YW + 0.4, 0.2), (0, YW / 2, zt + 0.1), slab, bevel=0, name='Roof', coll=coll)

    # two-tone paint: 1.5 m bands that follow the stairs, a darker line on top
    bands_r = [[(0, 0), (YL, 0), (YH, -1.4), (YW, -1.4), (YW, 0.1), (YH, 0.1), (YL, 1.5), (0, 1.5)],
               [(0, HF), (YL, HF), (YH, 1.4), (YW, 1.4), (YW, 2.9), (YH, 2.9), (YL, HF + 1.5), (0, HF + 1.5)]]
    bands_l = [[(0, 0), (YL, 0), (YH, 1.4), (YW, 1.4), (YW, 2.9), (YH, 2.9), (YL, 1.5), (0, 1.5)],
               [(0, -HF), (YL, -HF), (YH, -1.4), (YW, -1.4), (YW, 0.1), (YH, 0.1), (YL, -1.3), (0, -1.3)]]
    for pts in bands_r:
        lo = [(y, z - 0.2) for y, z in pts[:4]]           # the bottom edge hides under the floors and the treads
        _prism('PaintR', lo + pts[4:], 'x', W - 0.006, W, paint, coll)
        lib.curve_poly('PaintLineR', [[(W - 0.006, y, z) for y, z in reversed(pts[4:])]], bevel=0.009, mat_=line, coll=coll)
    for pts in bands_l:
        lo = [(y, z - 0.2) for y, z in pts[:4]]
        _prism('PaintL', lo + pts[4:], 'x', -W, -W + 0.006, paint, coll)
        lib.curve_poly('PaintLineL', [[(-W + 0.006, y, z) for y, z in reversed(pts[4:])]], bevel=0.009, mat_=line, coll=coll)
    for z0 in (0.0, HF, -HF):
        for (x0, x1) in ((-W, dl), (dr, W)) if z0 == 0.0 else ((-W, W),):
            _prism('PaintBack', [(x0, z0), (x1, z0), (x1, z0 + 1.5), (x0, z0 + 1.5)], 'y', 0.0, 0.006, paint, coll)
        lib.curve_poly('PaintLineB', [[(-W, 0.006, z0 + 1.5), (W, 0.006, z0 + 1.5)]], bevel=0.009, mat_=line, coll=coll)
    for z0 in (-HF / 2, HF / 2):
        zw = z0 + 0.85
        for (x0, x1, a, b) in ((-W, W, z0, zw), (-W, -0.65, zw, z0 + 1.5), (0.65, W, zw, z0 + 1.5)):
            _prism('PaintWin', [(x0, a), (x1, a), (x1, b), (x0, b)], 'y', YW - 0.006, YW, paint, coll)
        for (x0, x1) in ((-W, -0.65), (0.65, W)):
            lib.curve_poly('PaintLineW', [[(x0, YW - 0.006, z0 + 1.5), (x1, YW - 0.006, z0 + 1.5)]], bevel=0.009, mat_=line, coll=coll)

    # handrails: down our flight, round the half landing, down again; up the other flight
    hr = 0.92
    zA = lambda y: -RS - (y - YL) * RS / TR + hr + 0.03      # noqa: E731
    zB = lambda y: RS + (y - YL) * RS / TR + hr + 0.03       # noqa: E731
    xr = GAP + 0.03
    zC = lambda y: -HF / 2 - RS - (YH - y) * RS / TR + hr + 0.03    # noqa: E731
    fA = lambda y: -min(N - 1, int((y - YL) / TR) + 1) * RS                # noqa: E731
    fB = lambda y: min(N - 1, int((y - YL) / TR) + 1) * RS                 # noqa: E731
    fC = lambda y: -HF / 2 - min(N - 1, int((YH - y) / TR) + 1) * RS       # noqa: E731
    _rail(coll, [(xr, YL - 0.03, hr), (xr, YL + 0.05, zA(YL + 0.05)), (xr, YH - 0.05, zA(YH - 0.05)), (xr, YH + 0.12, -HF / 2 + hr),
                 (-xr, YH + 0.12, -HF / 2 + hr), (-xr, YH - 0.05, zC(YH - 0.05)), (-xr, YL + 0.05, zC(YL + 0.05))],
          'RailA', wood, iron, lambda x, y: fA(y) if x > 0 else fC(y))
    _rail(coll, [(-xr, YL - 0.03, hr), (-xr, YL + 0.05, zB(YL + 0.05)), (-xr, YH - 0.05, zB(YH - 0.05)), (-xr, YH + 0.12, HF / 2 + hr),
                 (xr, YH + 0.12, HF / 2 + hr)], 'RailB', wood, iron, lambda x, y: fB(y))
    lib.curve_poly('RailTurn', [[(xr, YL - 0.03, hr), (0, YL - 0.09, hr), (-xr, YL - 0.03, hr)]], bevel=0.03, mat_=wood, coll=coll)

    # the window of the low half landing: sill with geraniums and the cat, a cast-iron radiator under it
    sill_m = lib.mat('WinSill', '#F4F1EA', rough=0.35)
    for z0 in (-HF / 2, HF / 2):
        _window(coll, z0, frame_m, sill_m, 'Win')
    zs = -HF / 2 + 0.85
    _geranium(coll, (-0.48, YW - 0.06, zs), rng, 'GerA')
    _geranium(coll, (-0.28, YW - 0.04, zs), rng, 'GerB')
    cat = _cat(coll, (0.32, YW - 0.08, zs), rng)
    rad = lib.mat('Radiator', '#EDE6D6', rough=0.5)
    for k in range(10):
        lib.box((0.07, 0.09, 0.55), (-0.33 + k * 0.074, YW - 0.12, -HF / 2 + 0.18), rad, bevel=0.025, name='RadFin', coll=coll,
                origin='bottom')
    # the door wall: his door (padded, brass studs, № 47), the neighbour's (painted metal, № 48) on the right wall,
    # doormats, a bell, the electricity cabinet, a yellow gas pipe, the ceiling lamp
    leather = lib.mat('Leatherette', '#4A3124', rough=0.55, var=0.12, var_scale=12, bump=0.35, bump_scale=18)
    dframe = lib.mat('DoorFrame', '#3B2A20', rough=0.5)
    hinge, leaf = _door(coll, DOOR_X, 0.0, 'HDoor', leather, dframe, '47', hinge_left=True)
    _leatherette(coll, hinge, 'HDoor')
    nb = lib.empty('NbDoorRoot', (W, 0.78, 0), (0, 0, math.pi / 2), coll=coll)
    nh, _ = _door(coll, 0.0, 0.0, 'NDoor', lib.mat('NbDoor', '#8C5A3C', rough=0.4, var=0.08, var_scale=6), dframe, '48',
                  hinge_left=False)
    for o in list(coll.objects):
        if o.name.startswith('NDoor') and o.parent is None:
            o.parent = nb
    lib.box((0.8, 0.5, 0.012), (DOOR_X, 0.4, 0.0), lib.mat('Doormat', '#7A4E35', rough=0.95, bump=0.3, bump_scale=120), bevel=0,
            name='Doormat', coll=coll, origin='bottom')
    lib.box((0.5, 0.75, 0.012), (W - 0.3, 0.78, 0.0), lib.mat('Doormat2', '#4A5A3E', rough=0.95, bump=0.3, bump_scale=120), bevel=0,
            name='Doormat2', coll=coll, origin='bottom')
    lib.box((0.05, 0.02, 0.07), (DOOR_X + DOOR_W / 2 + 0.16, 0.012, 1.45), lib.mat('Bell', '#E9E4D8', rough=0.4), bevel=0.006,
            name='Bell', coll=coll)
    lib.cyl(0.012, 0.012, (DOOR_X + DOOR_W / 2 + 0.16, 0.025, 1.45), lib.mat('BellBtn', '#2B2B2B', rough=0.4), rot=(math.pi / 2, 0, 0),
            verts=10, name='BellBtn', coll=coll)
    cab = lib.mat('Cabinet', '#9AA3A0', rough=0.55, metal=0.3)
    lib.box((0.55, 0.14, 0.8), (0.55, 0.07, 1.35), cab, bevel=0.01, name='Cabinet', coll=coll, origin='bottom')
    lib.box((0.02, 0.02, 0.08), (0.78, 0.15, 1.75), lib.mat('CabLock', '#2B2B2B', rough=0.4), bevel=0.003, name='CabLock', coll=coll)
    gas = lib.mat('GasPipe', '#E8B923', rough=0.35)
    lib.curve_poly('GasPipe', [[(-W + 0.06, 0.06, 2.25), (W - 0.06, 0.06, 2.25), (W - 0.06, YW - 0.06, 2.25)]], bevel=0.018, mat_=gas,
                   coll=coll)
    for x in (-1.0, -0.2, 0.6):
        lib.box((0.03, 0.06, 0.04), (x, 0.03, 2.25), gas, bevel=0.004, name='GasClip', coll=coll)
    dome = lib.mat('LampDome', '#FFF2D8', rough=0.3, emit='#FFE2B0', emit_strength=6.0)
    lib.sphere(0.13, (0.0, 0.75, HF - 0.24), dome, 24, 12, scale=(1, 1, 0.55), name='Lamp', coll=coll)
    lamp = lib.light('POINT', (0.0, 0.75, HF - 0.36), energy=30, color='#FFCB8A', size=0.15, name='LampLight', coll=coll)
    lib.light('AREA', (0.0, YW - 0.35, -HF / 2 + 1.6), (math.radians(90), 0, 0), energy=60, color='#FFE9CF', size=1.2,
              name='WinBounce', coll=coll)
    lib.light('AREA', (0.0, YW - 0.35, HF / 2 + 1.6), (math.radians(90), 0, 0), energy=40, color='#FFE9CF', size=1.2,
              name='WinBounceUp', coll=coll)

    # behind his door: a bit of the warm hallway (seen when it opens)
    paper = lib.mat('Wallpaper', '#BFAF93', rough=0.9, var=0.12, var_scale=25, bump=0.1, bump_scale=200)
    lam = lib.mat('Laminate', '#7E5E42', rough=0.5, var=0.22, var_scale=6, bump=0.1, bump_scale=40)
    lib.box((1.8, 2.6, 0.1), (DOOR_X, -1.5, -0.05), lam, bevel=0, name='HallFloor', coll=coll)
    for x in (DOOR_X - 0.9, DOOR_X + 0.9):
        lib.box((0.1, 2.6, 2.6), (x, -1.5, 1.3), paper, bevel=0, name='HallWall', coll=coll)
    lib.box((1.8, 0.1, 2.6), (DOOR_X, -2.8, 1.3), paper, bevel=0, name='HallEnd', coll=coll)
    lib.box((1.8, 2.6, 0.1), (DOOR_X, -1.5, 2.6), lib.mat('HallCeil', '#ECE9E2', rough=0.9), bevel=0, name='HallCeil', coll=coll)
    for k, c in enumerate(('#2D3B54', '#6B4E3D', '#D9682A')):
        lib.box((0.16, 0.42, 0.85), (DOOR_X - 0.78, -0.9 - k * 0.3, 1.32), lib.mat('Coat' + c, c, rough=0.85), rot=(0, 0.05, 0),
                bevel=0.06, name='Coat', coll=coll, origin='bottom')
    lib.light('AREA', (DOOR_X, -1.6, 2.4), (0, 0, 0), energy=45, color='#FFC98E', size=1.0, name='HallGlow', coll=coll)

    # outside: a birch and a maple in autumn colours, the block across the yard, a bit of sky
    out = lib.collection('StairOutside')
    for k, (x, y, hgt, b) in enumerate(((-3.5, 10.0, 11.0, True), (4.0, 12.5, 12.0, False), (0.5, 16.0, 10.0, True))):
        pcity.tree(x, y, out, rng, h=hgt, greens=('#C9A23A', '#9DB04A', '#D98A2E', '#7E9A3E'), birch=b)
    facs = pcity.facade_set(0.0, prefix='StF')
    lib.box((60, 12, 16.5), (0, 34.0, -HF * 2), facs[2][0], bevel=0.1, name='OppBlock', coll=out, origin='bottom')
    lib.plane((200, 200), (0, 60, -HF * 2), lib.mat('Yard', '#7E8A62', rough=0.95, var=0.2, var_scale=0.5), name='Yard', coll=out)
    for o in out.objects:
        if o.name.startswith(('Trunk', 'Leaf')) and o.parent is None:
            o.location.z += -HF * 2
    if dust:
        fog, _ = lib.fog_box((2 * W, YW, 7.0), (0, YW / 2, 0.6), density=dust, color='#FFF1DE', aniso=0.55, noise=0.5, noise_scale=1.2,
                             name='Dust')
        for c in fog.users_collection:
            c.objects.unlink(fog)
        coll.objects.link(fog)
    return dict(sun=sun, door=hinge, nb_door=nh, cat=cat, lamp=lamp)


# ----------------------------------------------------------------------------- the people of the queue
QUEUE = [('sparky', 'bolt'), ('girl', 'float'), ('kid', None), (None, 'flame'), ('neighbour', 'aura'), (None, 'aura'), ('girl', None),
         (None, 'aura')]


def queue_spots(n=8):
    """The first one in front of his door, then along the landing edge and down the flight on the right."""
    pts = [V((DOOR_X + 0.15, 0.62, 0.0)), V((0.05, 0.95, 0.0)), V((0.62, 1.25, 0.0))]
    for i in range(1, N):
        if len(pts) >= n:
            break
        if i % 2 == 0:
            continue
        y = YL + (i - 0.5) * TR
        pts.append(V((0.72 + (0.12 if i % 4 == 1 else -0.08), y, gz(0.7, y))))
    while len(pts) < n:
        pts.append(V((0.4 + 0.3 * (len(pts) % 2), YH + 0.4 + 0.45 * (len(pts) - 7), -HF / 2)))
    return pts[:n]


def queue_people(coll, rng, n=8, calm_t=None, calm_all=None, skip=0):
    """calm_t: the first one stops sparking at that time; calm_all: (t0, t1) every power fades out from the door down;
    skip: the first ones have already been seen to and gone."""
    out = []
    spots = queue_spots(n)
    for k, q in enumerate(spots):
        if k < skip:
            continue
        look, power = QUEUE[k % len(QUEUE)]
        nxt = spots[k - 1] if k else V((DOOR_X, 0.0, 0.0))
        p = S.folk(tuple(q), S.face(q, nxt), rng, coll, look, height=0.82 if look == 'kid' else 0.9, name=f'Q{k}')
        P2.stand(p, rng)
        col = AURA[(k + 2) % len(AURA)]
        off = None
        if calm_all:
            off = calm_all[0] + (calm_all[1] - calm_all[0]) * k / max(1, n - 1)
        if k == 0 and calm_t is not None:
            off = calm_t
        FX.aura(coll, p['root'], col, r=0.42, z=0.9, t_on=-1.0, t_off=off, strength=2.6, alpha=0.32, name=f'QA{k}', scale=(1, 1, 1.9))
        if power == 'flame':
            FX.flame(coll, _palm(p, coll, f'QPalm{k}'), (0, 0, 0.05), -1.0, off, scale=0.35, rng=rng, name=f'QFlame{k}')
            S.key_people(p, 'upperR', 0, [(0, -1.0)])
        if power == 'float':
            p['root'].location.z += 0.45
            lib.add_sine(p['root'], 'location', 2, 0.1, 1.6, k)
        out.append((p, q, power, off))
    return out


def _palm(p, coll, name):
    e = lib.empty(name, (0, 0, 0), coll=coll)
    e.parent = p['handR']
    e.location = (0, 0, -1.0)
    return e


def bolt_hands(coll, rng, p, q, t0, t1, name):
    times = [t0 + 0.09 * i + rng.uniform(0, 0.03) for i in range(max(1, int((t1 - t0) / 0.09)))]
    return FX.bolt(coll, (q.x - 0.26, q.y, q.z + 1.0), (q.x + 0.26, q.y, q.z + 1.07), times, rng, width=0.011, strength=30,
                   light=300.0, name=name)


def _cam(loc, tgt, lens, keys=None, tkeys=None):
    c = lib.camera(loc, tgt, lens)
    if keys:
        lib.animate_camera(c, keys, tkeys)
    c.data.clip_start = 0.03
    return c


def _ev(shot, k, d):
    return shot.get('events', {}).get(k, d)


# ============================================================================= a08 the courier vanishes and stands at the door
def v_courier(shot, fps):
    dur = shot['dur']
    rng = random.Random(8)
    coll = lib.collection('Stair')
    stairwell(coll, rng)
    vanish, appear = _ev(shot, 'vanish', 0.53), _ev(shot, 'appear', 2.19)
    # down on the half landing by the window, the courier with his yellow box looks up the stairs - and is gone
    cp = V((0.7, YH + 0.45, -HF / 2))
    a = S.folk(tuple(cp), S.face(cp, (0.7, 0.0, 0.0)), rng, coll, 'courier', name='Cour')
    P2.stand(a, rng)
    S.key_people(a, 'head', 0, [(0, -0.25)])
    for o in [a['root']] + list(a['root'].children_recursive):
        FX.key_hide(o, [(0, True), (vanish + 0.04, False)])
    FX.flash(coll, (cp.x, cp.y, cp.z + 1.0), vanish, col='#9FE0FF', size=0.9, energy=900, name='CourOut')
    FX.ripple(coll, (cp.x, cp.y, cp.z + 0.02), vanish, 0.6, 1.4, strength=2.0, name='CourRip')
    # ...and a second later he is up here at the door of flat 47, and knocks
    dp = V((DOOR_X + 0.22, 0.55, 0.0))
    b = S.folk(tuple(dp), S.face(dp, (DOOR_X, -1.0, 0)), random.Random(8), coll, 'courier', name='Cour2')
    P2.stand(b, rng)
    for o in [b['root']] + list(b['root'].children_recursive):
        FX.key_hide(o, [(0, False), (appear, True)])
    FX.flash(coll, (dp.x, dp.y, 1.0), appear, col='#9FE0FF', size=0.9, energy=900, name='CourIn')
    S.key_people(b, 'upperR', 0, [(appear, -0.2), (appear + 0.35, -1.6), (appear + 0.5, -1.4), (appear + 0.65, -1.6),
                                  (appear + 0.8, -1.4)])
    c0, c1 = V((1.05, 0.25, 1.62)), V((0.95, 0.75, 1.55))
    _cam(tuple(c0), tuple(cp + V((0, 0, 0.9))), 30,
         [(0, tuple(c0)), (vanish + 0.4, tuple(c0.lerp(c1, 0.3))), (dur, tuple(c1))],
         [(0, tuple(cp + V((0, -0.3, 0.9)))), (vanish + 0.45, tuple(cp + V((0, -0.6, 1.0)))),
          (appear - 0.15, (DOOR_X + 0.1, 0.1, 1.05)), (dur, (DOOR_X + 0.15, 0.15, 1.1))])
    lib.bloom(0.3, 1.0, 7)
    return dict(fill=0.3, fill_col='#FFF1E0', exposure=0.35, samples=32)


# ============================================================================= b16 the queue on the stairs to his door
def v_queue(shot, fps):
    dur = shot['dur']
    rng = random.Random(36)
    coll = lib.collection('Stair')
    st = stairwell(coll, rng)
    ppl = queue_people(coll, rng)
    p0, q0, _, _ = ppl[0]
    bolt_hands(coll, rng, p0, q0, 0.0, dur, 'QBolt')
    # his door opens: he looks out at the queue
    hinge = st['door']
    for t, v in ((0, 0.0), (0.35, 0.0), (1.1, 1.25), (dur, 1.35)):
        P2._key(hinge, 'rotation_euler', 2, F(t), v)
    h = H.load(coll, (DOOR_X + 0.1, -0.55, 0.0), math.pi)
    H.key_pose(h, 0, H.pose('stand', head=(0, 4, 0)))
    H.walk(h, 1.0, 1.9, [(DOOR_X + 0.1, -0.55), (DOOR_X + 0.12, -0.12)], speed=0.5)
    H.key_root(h, 2.2, None, math.pi + 0.35)
    H.key_pose(h, dur, H.pose('stand', head=(18, 10, 0)))
    h['body']['eye_look'], h['body']['eye_spread'] = (0.5, -0.2), 0.25
    # the camera stands on the flight up, across the gap: the queue stacks down the stairs, then it turns to his door
    c0, c1 = V((-0.85, 2.95, 1.72)), V((-0.8, 2.5, 1.78))
    _cam(tuple(c0), (0.7, 2.6, -0.2), 28, [(0, tuple(c0)), (dur, tuple(c1))],
         [(0, (0.7, 2.7, -0.25)), (1.0, (0.45, 1.6, 0.2)), (dur * 0.75, (DOOR_X + 0.15, 0.05, 1.0)), (dur, (DOOR_X + 0.15, 0.05, 1.05))])
    lib.bloom(0.3, 1.0, 7)
    return dict(fill=0.35, fill_col='#FFF1E0', exposure=0.35, samples=32)


# ============================================================================= b17 those who can't cope with their power
def v_struggle(shot, fps):
    dur = shot['dur']
    rng = random.Random(36)
    coll = lib.collection('Stair')
    stairwell(coll, rng)
    ppl = queue_people(coll, rng)
    c0 = V((1.15, 2.35, 0.75))
    for p, q, _, _ in ppl:                          # the ones standing on the flight right at the lens are left out
        if (q - c0).xy.length < 1.3:
            for ob in [p['root']] + list(p['root'].children_recursive):
                ob.hide_render = ob.hide_viewport = True
    p0, q0, _, _ = ppl[0]
    bolt_hands(coll, rng, p0, q0, 0.0, dur, 'QBolt')
    # the floating girl drifts up into the stairwell gap, the kid grabs her hand and pulls her down
    g, qg, _, _ = ppl[1]
    FX.key_loc(g['root'], [(0, (qg.x, qg.y, qg.z + 0.45)), (dur * 0.6, (qg.x - 0.05, qg.y + 0.05, qg.z + 1.15)),
                           (dur, (qg.x - 0.05, qg.y + 0.05, qg.z + 0.95))])
    S.key_people(g, 'upperL', 0, [(0, 0.0), (dur * 0.5, 0.8)])
    kid, qk, _, _ = ppl[2]
    S.key_people(kid, 'upperR', 0, [(0, -0.5), (dur * 0.4, -2.6), (dur, -2.4)])
    S.key_people(kid, 'upperL', 0, [(0, -0.3), (dur * 0.45, -2.4), (dur, -2.3)])
    # the flame man's palm flares up
    h = H.load(coll, (DOOR_X + 0.05, -0.1, 0.0), math.pi + 0.5)
    H.key_pose(h, 0, H.pose('stand', head=(20, 12, 0)))
    aim = qg.lerp(qk, 0.5) + V((0, 0, 1.3))
    _cam(tuple(c0), tuple(aim), 26, [(0, tuple(c0)), (dur, tuple(c0 + V((-0.05, -0.25, 0.1))))],
         [(0, tuple(aim)), (dur, tuple(aim + V((0, -0.1, 0.25))))])
    lib.bloom(0.3, 1.0, 7)
    return dict(fill=0.35, fill_col='#FFF1E0', exposure=0.35, samples=32)


# ============================================================================= b18 he touches the first one: every power on the stairs goes quiet
def v_calm(shot, fps):
    dur = shot['dur']
    rng = random.Random(36)
    touch, still = _ev(shot, 'touch', 0.57), _ev(shot, 'still', 2.57)
    coll = lib.collection('Stair')
    st = stairwell(coll, rng)
    P2._key(st['door'], 'rotation_euler', 2, F(0), 1.35)
    ppl = queue_people(coll, rng, calm_t=touch + 0.15, calm_all=(touch + 0.4, still))
    p0, q0, _, _ = ppl[0]
    bolt_hands(coll, rng, p0, q0, 0.0, touch + 0.2, 'QBolt')
    S.key_people(p0, 'upperL', 0, [(0, -1.0), (touch + 0.2, -1.0), (touch + 0.7, 0.0)])
    S.key_people(p0, 'upperR', 0, [(0, -1.0), (touch + 0.2, -1.0), (touch + 0.7, 0.0)])
    S.key_people(p0, 'head', 0, [(touch + 0.3, 0.0), (touch + 0.8, -0.15), (dur, -0.1)])
    g, qg, _, off = ppl[1]                          # the floating girl comes down softly when her power fades
    FX.key_loc(g['root'], [(0, (qg.x, qg.y, qg.z + 0.45)), (off or still, (qg.x, qg.y, qg.z + 0.45)),
                           ((off or still) + 0.6, (qg.x, qg.y, qg.z))])
    hp = V((DOOR_X + 0.05, 0.12, 0.0))
    h = H.load(coll, tuple(hp), S.face(hp, q0))
    H.key_pose(h, 0, H.pose('stand', head=(0, 6, 0)))
    H.key_pose(h, touch, H.pose('reach_r', head=(0, 8, 0)))
    H.key_pose(h, still - 0.2, H.pose('reach_r', head=(0, 6, 0)))
    H.key_pose(h, still + 0.5, H.pose('stand', head=(-30, -4, 0)))
    H.key_pose(h, dur, H.pose('stand', head=(-36, -6, 0)))
    FX.ripple(coll, (q0.x, q0.y, 0.05), touch + 0.1, 1.6, 4.0, strength=2.0)
    # from the foot of the flight up: the touch close, then a pan right - the queue on the landing and the stairs is calm
    ca, cb = V((-1.2, 1.25, 1.4)), V((-1.15, 1.0, 1.55))
    t_a = (hp + q0) / 2 + V((0, 0, 1.1))
    _cam(tuple(ca), tuple(t_a), 28, [(0, tuple(ca)), (dur, tuple(cb))],
         [(0, tuple(t_a)), (still, (0.3, 1.3, 0.9)), (dur, (0.8, 2.2, 0.3))])
    lib.bloom(0.3, 1.0, 7)
    return dict(fill=0.35, fill_col='#FFF1E0', exposure=0.35, samples=32)


# ============================================================================= b19 «а какую силу выбрал бы ты?» - at his door
def v_you(shot, fps):
    dur = shot['dur']
    rng = random.Random(36)
    turn = _ev(shot, 'turn', 0.53)
    coll = lib.collection('Stair')
    st = stairwell(coll, rng)
    P2._key(st['door'], 'rotation_euler', 2, F(0), 1.35)
    queue_people(coll, rng, calm_all=(-2.0, -1.0), skip=2)
    hp = V((DOOR_X + 0.1, 0.18, 0.0))
    cam_p = V((DOOR_X + 0.5, 1.3, 1.2))
    look = hp + V((0, 0, 1.12))
    h = H.load(coll, tuple(hp), S.face(hp, (0.7, 2.5, 0)))
    H.key_pose(h, 0, H.pose('stand', head=(-20, 4, 0)))
    H.key_pose(h, turn, H.pose('stand', head=(-20, 2, 0)))
    H.key_root(h, turn, None, S.face(hp, (0.7, 2.5, 0)))
    H.key_pose(h, turn + 0.45, H.pose('stand', head=(0, 0, 3)))
    H.key_root(h, turn + 0.6, None, S.face(hp, cam_p))
    H.key_pose(h, dur, H.pose('stand', head=(0, -2, 4)))
    h['body']['eye_looks'] = [(turn + 0.35, dur + 1.0, 0.0, 0.0)]
    _cam(tuple(cam_p), tuple(look), 45, [(0, tuple(cam_p)), (dur, tuple(cam_p + (look - cam_p).normalized() * 0.2))],
         [(0, tuple(look)), (dur, tuple(look))])
    lib.bloom(0.3, 1.0, 7)
    return dict(fill=0.4, fill_col='#FFF1E0', exposure=0.35, samples=32)
