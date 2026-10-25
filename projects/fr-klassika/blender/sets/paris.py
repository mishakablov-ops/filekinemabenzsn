"""Style 1 (classic) test: a French city at golden hour, all built from code (no downloaded models).
shot: {"variant": "aerial"|"cafe"|"boulevard"}
Grid of Haussmann blocks (cream stone, dark mansard roofs, lit shop fronts), a central boulevard along +Y,
a square with café terraces, side streets with walkers, and the Eiffel Tower over the Champ de Mars at the end.
"""
import bpy, math, random
import bmesh
from mathutils import Vector
import lib
import civ
import city
import people2 as P2

BLVD = 12.0                 # half width of the boulevard (road 16 + sidewalks)
SIDE = 14.0                 # side street width
BW, BL = 44.0, 48.0         # block size (x, y)
ROWS = range(-3, 14)         # block rows along y (period BL + SIDE)
COLS = 6                    # block columns on each side
TOWER = (0.0, 560.0, 0.0)
SQUARE = (40.0, 112.0)      # y range of the square (blocks removed next to the boulevard)


def _stone_mats():
    out = []
    for i, base in enumerate(['#D6C6AA', '#CDBA9C', '#DCCDB3']):
        m, v = city.facade_mat(f'Stone{i}', base, glow='#FFC98E')
        v.outputs[0].default_value = 0.22
        ramp = next(n for n in m.node_tree.nodes if n.type == 'VALTORGB')
        cols = ['#D6C6AA', '#C4B092', '#B9A486']
        for e, c in zip(sorted(ramp.color_ramp.elements, key=lambda e: e.position), (base, cols[(i + 1) % 3], cols[(i + 2) % 3])):
            e.color = lib.C(c)
        out.append(m)
    return out


def mansard(x, y, w, d, z, m, coll, along_y=True):
    """Dark sloped roof on top of a building (trapezoid profile)."""
    s = min(2.2, w * 0.2)
    pts = [(-w / 2, 0), (w / 2, 0), (w / 2 - s, 3.4), (-w / 2 + s, 3.4)]
    if along_y:
        return lib.poly_prism(pts, d, (x, y + d / 2, z), m, rot=(math.pi / 2, 0, 0), name='Mansard', coll=coll)
    return lib.poly_prism(pts, w, (x - w / 2, y, z), m, rot=(math.pi / 2, 0, math.pi / 2), name='Mansard', coll=coll)


# ----------------------------------------------------------------------------- Eiffel Tower (lattice via Wireframe)
def _tube(bm, centers, halves, sides=3):
    rings = []
    for c, h in zip(centers, halves):
        ring = []
        corners = [(-h, -h), (h, -h), (h, h), (-h, h)]
        for k in range(4):
            (x0, y0), (x1, y1) = corners[k], corners[(k + 1) % 4]
            for s in range(sides):
                t = s / sides
                ring.append(bm.verts.new((c[0] + x0 + (x1 - x0) * t, c[1] + y0 + (y1 - y0) * t, c[2])))
        rings.append(ring)
    n = len(rings[0])
    for a, b in zip(rings, rings[1:]):
        for i in range(n):
            bm.faces.new((a[i], a[(i + 1) % n], b[(i + 1) % n], b[i]))


def eiffel(loc, height=300.0, col='#5A4A3E', coll=None):
    s = height / 300.0
    m = lib.mat('Eiffel', col, rough=0.7, metal=0.2)
    bm = bmesh.new()
    for sx in (-1, 1):
        for sy in (-1, 1):
            cs, hs = [], []
            for i in range(9):
                t = i / 8
                d = lib.lerp(58, 21, t ** 0.8)
                cs.append((sx * d * s, sy * d * s, 57 * t * s))
                hs.append(lib.lerp(9, 5, t) * s)
            _tube(bm, cs, hs, 2)
    cs, hs = [], []
    for i in range(7):
        t = i / 6
        cs.append((0, 0, (57 + 58 * t) * s)); hs.append(lib.lerp(27, 13, t) * s)
    _tube(bm, cs, hs, 4)
    cs, hs = [], []
    for i in range(13):
        t = i / 12
        cs.append((0, 0, (115 + 161 * t) * s)); hs.append(lib.lerp(11, 2.2, t ** 0.75) * s)
    _tube(bm, cs, hs, 3)
    tw = lib.mesh_from_bm(bm, 'EiffelLattice', m, loc=loc, smooth=False, coll=coll)
    w = tw.modifiers.new('Lattice', 'WIREFRAME')
    w.thickness = 0.9 * s
    w.use_even_offset = True
    x, y, z = loc
    for zz, half, th in ((57, 36, 4.5), (115, 17, 3.5), (276, 4.5, 4.0)):
        lib.box((2 * half * s, 2 * half * s, th * s), (x, y, z + zz * s), m, bevel=0.2 * s, name='EiffelDeck', coll=coll, origin='bottom')
    lib.cyl(0.9 * s, 24 * s, (x, y, z + 292 * s), m, name='EiffelTop', coll=coll)
    for rot in (0, math.pi / 2):
        arch = lib.cyl(40 * s, 3 * s, (x, y, z + 18 * s), m, rot=(math.pi / 2, 0, rot), verts=48, name='EiffelArch', coll=coll)
        sol = arch.modifiers.new('Ring', 'SOLIDIFY'); sol.thickness = 2.5 * s
    # warm lights on the decks (it is evening)
    lm, _ = lib.emission_mat('EiffelGlow', '#FFC27A', 6.0)
    for zz, half in ((57, 36), (115, 17)):
        lib.box((2 * half * s + 0.4, 2 * half * s + 0.4, 0.6 * s), (x, y, z + zz * s + 1.0 * s), lm, bevel=0, name='EiffelDeckLight', coll=coll)
    lib.sphere(1.6 * s, (x, y, z + 317 * s), _beacon(), 10, 8, name='EiffelBeacon', coll=coll)
    return tw


def _beacon():
    m, _ = lib.emission_mat('Beacon', '#FFD9A0', 30.0)
    return m


# ----------------------------------------------------------------------------- café furniture and people sitting
def parasol(x, y, coll, col):
    pole = lib.mat('ParasolPole', '#3A3430', rough=0.6)
    lib.cyl(0.04, 2.3, (x, y, 0.18), pole, verts=8, name='ParasolPole', coll=coll, origin='bottom')
    lib.cyl(1.35, 0.42, (x, y, 2.25), lib.mat('Parasol' + col, col, rough=0.9), verts=8, r2=0.05, name='Parasol', coll=coll)


def table_set(x, y, coll, rng, sit_p=0.75):
    wood = lib.mat('CafeTable', '#3B302A', rough=0.6)
    top = lib.mat('CafeTop', '#E9DFCD', rough=0.5)
    lib.cyl(0.05, 0.72, (x, y, 0.18), wood, verts=8, name='TableLeg', coll=coll, origin='bottom')
    lib.cyl(0.42, 0.04, (x, y, 0.92), top, verts=20, name='TableTop', coll=coll)
    cup = lib.mat('Cup', '#F1EBE0', rough=0.4)
    for k in range(2):
        lib.cyl(0.05, 0.08, (x + 0.15 * (k * 2 - 1), y + 0.05, 0.98), cup, verts=10, name='Cup', coll=coll)
    for side in (-1, 1):
        cx = x + side * 0.75
        heading = math.pi / 2 if side > 0 else -math.pi / 2     # face the table (forward = local -Y)
        chair = lib.empty('Chair', (cx, y, 0.18), (0, 0, heading), coll=coll)
        for o in (lib.box((0.44, 0.44, 0.05), (0, 0, 0.45), wood, bevel=0.01, name='Seat', coll=coll),
                  lib.box((0.44, 0.05, 0.5), (0, 0.22, 0.72), wood, bevel=0.01, name='Back', coll=coll)):
            o.parent = chair
        for lx in (-0.18, 0.18):
            for ly in (-0.18, 0.18):
                lib.cyl(0.02, 0.45, (lx, ly, 0.0), wood, verts=6, name='ChairLeg', coll=coll, origin='bottom').parent = chair
        if rng.random() < sit_p:
            sit(cx, y, heading, coll, rng)


def sit(x, y, heading, coll, rng):
    """Seated person on a café chair: thighs on the seat, shins down, shoes on the floor (paving top 0.18)."""
    h = rng.uniform(0.95, 1.05)
    p = P2.person((x, y, 0.18), heading, height=h, rng=rng, coll=coll, name='Sitter')
    P2.sit(p, rng)
    return p


def walker(x, y, heading_y, coll, rng, length=40.0, name='W', z=0.18):
    h = rng.uniform(0.92, 1.06)
    sp = rng.uniform(0.95, 1.35)
    p = P2.person((x, y, z), 0, height=h, rng=rng, coll=coll, bag=rng.random() < 0.3, name=name)
    P2.walk(p, speed=sp, phase=rng.random(), height=h)
    lib.move_root(p, [(x, y, z), (x, y + heading_y * length, z)], t0=0, speed=sp)
    return p


def walker_x(x, y, dir_x, coll, rng, length=30.0, name='S', z=0.18):
    h = rng.uniform(0.92, 1.06)
    sp = rng.uniform(0.95, 1.3)
    p = P2.person((x, y, z), 0, height=h, rng=rng, coll=coll, bag=rng.random() < 0.25, name=name)
    P2.walk(p, speed=sp, phase=rng.random(), height=h)
    lib.move_root(p, [(x, y, z), (x + dir_x * length, y, z)], t0=0, speed=sp)
    return p


def group(x, y, coll, rng, n=2, name='G'):
    """People standing and talking in a small circle."""
    for k in range(n):
        a = 2 * math.pi * k / n + rng.uniform(-0.3, 0.3)
        px, py = x + 0.55 * math.cos(a), y + 0.55 * math.sin(a)
        heading = math.atan2(y - py, x - px) + math.pi / 2      # face the centre (forward = -Y)
        p = P2.person((px, py, 0.18), heading, height=rng.uniform(0.93, 1.05), rng=rng, coll=coll, name=f'{name}{k}')
        P2.stand(p, rng)


def flag(x, y, facing, coll):
    pole = lib.mat('FlagPole', '#3A3430', rough=0.5)
    lib.cyl(0.03, 1.8, (x + facing * 0.7, y, 7.2), pole, rot=(0, math.radians(60) * -facing, 0), verts=6, name='FlagPole', coll=coll)
    for i, c in enumerate(('#2A4D8F', '#EFE8DC', '#C8473F')):
        lib.box((0.02, 0.34, 0.75), (x + facing * 1.25, y - 0.34 + i * 0.34, 7.2), lib.mat('Flag' + c, c, rough=0.9), bevel=0,
                name='Flag', coll=coll)


# ----------------------------------------------------------------------------- the set
def build(shot, fps=60):
    dur = shot['dur']
    variant = shot.get('variant', 'aerial')
    rng = random.Random(23)
    coll = lib.collection('Paris')
    lib.FOG_BOX = (3000.0, 3000.0, 300.0)

    # golden hour behind the tower: warm, bright, soft shadows (classic rules: warm evening sky, few shadows)
    sun_dir = Vector((0.12, 1.0, 0.16))
    lib.world_sky_view_gradient('#55657E', '#F09A60', '#3A332D', strength=1.6, fog=0.0015, fog_col='#E8D0B4', aniso=0.5,
                                glow_dir=sun_dir, glow_col='#FF9A55', glow_size=0.34, glow_strength=2.4)
    s = lib.light('SUN', (0, 0, 0), energy=3.4, color='#FFC995', size=1.0, name='Sun', volume=1.0)
    s.rotation_euler = (-sun_dir).normalized().to_track_quat('-Z', 'Y').to_euler()
    s.data.angle = math.radians(10)

    ground = lib.mat('Asphalt', '#4A4440', rough=0.85, var=0.12, var_scale=0.3)
    lib.plane((4000, 4000), (0, 0, 0), ground, name='Ground', coll=coll)
    paving = lib.mat('Paving', '#8E8170', rough=0.9, var=0.12, var_scale=2)
    line_m = lib.mat('RoadLine', '#D8CDBB', rough=0.6)
    stones = _stone_mats()
    roof_m = lib.mat('Zinc', '#56565C', rough=0.55, metal=0.25, var=0.1, var_scale=1)
    shop_m, _ = lib.emission_mat('ShopGlow', '#FFC583', 2.6)
    awn_cols = ['#7A2E2A', '#2F4A3A', '#3A3F5A', '#8A5A2A']

    # boulevard sidewalks + dashes
    y0, y1 = -200, 470
    for sx in (-1, 1):
        lib.box((4.0, y1 - y0, 0.18), (sx * (BLVD - 2.0), (y0 + y1) / 2, 0), paving, bevel=0, name='BlvdSide', coll=coll, origin='bottom')
    for y in range(y0, y1, 9):
        lib.box((0.2, 4.0, 0.02), (0, y, 0.03), line_m, bevel=0, name='Dash', coll=coll, origin='bottom')

    # blocks
    xs = []
    x = BLVD + SIDE / 2 + BW / 2 - SIDE / 2
    for c in range(COLS):
        xs.append(x); x += BW + SIDE
    period = BL + SIDE
    for sx in (-1, 1):
        for ci, cx in enumerate(xs):
            for r in ROWS:
                cy = r * period
                if ci == 0 and SQUARE[0] - BL / 2 < cy < SQUARE[1] + BL / 2:
                    continue          # the square
                if 440 < cy < 660 and abs(cx) < 200:
                    continue          # Champ de Mars
                X = sx * cx
                xa, xb = X - BW / 2 - 2, X + BW / 2 + 2
                if sx > 0:
                    xa = max(xa, BLVD)          # no overlap with the boulevard sidewalk (coplanar tops flicker)
                else:
                    xb = min(xb, -BLVD)
                lib.box((xb - xa, BL + 4, 0.18), ((xa + xb) / 2, cy, 0), paving, bevel=0, name='BlockPave', coll=coll, origin='bottom')
                # two rows of buildings, split along y into 12–18 m houses
                for half in (-1, 1):
                    bx = X + half * BW / 4
                    yy = cy - BL / 2
                    while yy < cy + BL / 2 - 4:
                        w = min(rng.uniform(12, 18), cy + BL / 2 - yy)
                        h = rng.choice([17.5, 19.0, 20.5, 22.0]) if ci < 3 else rng.uniform(15, 24)
                        m = rng.choice(stones)
                        lib.box((BW / 2 - 0.4, w - 0.3, h), (bx, yy + w / 2, 0.18), m, bevel=0.15, name='Haussmann', coll=coll, origin='bottom')
                        mansard(bx, yy + w / 2, BW / 2 - 0.4, w - 0.3, 0.18 + h, roof_m, coll)
                        # chimneys
                        for k in range(rng.randint(1, 3)):
                            lib.box((0.9, 2.2, 1.6), (bx + rng.uniform(-3, 3), yy + rng.uniform(1, w - 1), 0.18 + h + 3.0),
                                    stones[0], bevel=0.05, name='Chimney', coll=coll, origin='bottom')
                        # lit shop fronts + awnings facing the boulevard / square (inner column only)
                        if ci == 0 and ((sx > 0 and half < 0) or (sx < 0 and half > 0)):
                            fx = X - sx * (BW / 2 - 0.1)
                            lib.box((0.12, w - 2.0, 3.0), (fx - sx * 0.08, yy + w / 2, 1.8), shop_m, bevel=0, name='ShopWin', coll=coll)
                            if cy < 330:
                                ac = rng.choice(awn_cols)
                                lib.box((1.8, w - 2.4, 0.1), (fx - sx * 0.9, yy + w / 2, 3.6), lib.mat('Awning' + ac, ac, rough=0.9),
                                        rot=(0, sx * math.radians(14), 0), bevel=0.02, name='Awning', coll=coll)
                                if rng.random() < 0.35:
                                    flag(fx, yy + 1.5, -sx, coll)
                        yy += w

    # side streets get cross dashes too (reads as a grid from above)
    for r in ROWS:
        yy = r * period + period / 2
        for x in range(-int(xs[-1]), int(xs[-1]), 9):
            if abs(x) > BLVD:
                lib.box((4.0, 0.2, 0.02), (x, yy, 0.03), line_m, bevel=0, name='Dash', coll=coll, origin='bottom')

    # Champ de Mars: lawn, gravel alleys, tree rows, the tower
    lawn = lib.mat('Lawn', '#7C8A55', rough=0.95, var=0.15, var_scale=0.3)
    lib.box((150, 130, 0.12), (0, 530, 0), lawn, bevel=0, name='Lawn', coll=coll, origin='bottom')
    for tx in (-82, -70, 70, 82):
        civ.tree_line((tx, 470), (tx, 640), coll, n=16, h=(9, 12), jitter=0.8, seed=int(tx) + 100)
    eiffel(TOWER, 300, coll=coll)

    # boulevard trees and lamps
    lamp_pole = lib.mat('LampPole', '#2B2A28', rough=0.5, metal=0.5)
    lamp_m, _ = lib.emission_mat('StreetLamp', '#FFD9A8', 16)
    for y in range(y0 + 6, 440, 14):
        for sx in (-1, 1):
            if SQUARE[0] < y < SQUARE[1] and sx > 0:
                continue
            civ.tree(sx * (BLVD - 1.2), y, coll, h=rng.uniform(8, 10), rng=rng, kind='round')
            lib.cyl(0.08, 5.0, (sx * (BLVD - 3.6), y + 7, 0.18), lamp_pole, verts=8, name='LampPole', coll=coll, origin='bottom')
            lib.sphere(0.28, (sx * (BLVD - 3.6), y + 7, 5.3), lamp_m, 10, 8, name='LampBall', coll=coll)

    # the square (right side of the boulevard): paving, fountain, café terraces
    sq_x0, sq_x1 = BLVD, xs[0] + BW / 2 + 2
    lib.box((sq_x1 - sq_x0, SQUARE[1] - SQUARE[0] + 20, 0.16), ((sq_x0 + sq_x1) / 2, (SQUARE[0] + SQUARE[1]) / 2, 0), paving,
            bevel=0, name='Square', coll=coll, origin='bottom')
    fx, fy = (sq_x0 + sq_x1) / 2 + 6, (SQUARE[0] + SQUARE[1]) / 2
    stone = lib.mat('FountainStone', '#CDBEA4', rough=0.85)
    water = lib.mat('Water', '#6F8FA0', rough=0.1, spec=0.8)
    lib.cyl(6.0, 0.7, (fx, fy, 0.16), stone, verts=48, name='FountainRim', coll=coll, origin='bottom')
    lib.cyl(5.6, 0.6, (fx, fy, 0.3), water, verts=48, name='FountainWater', coll=coll, origin='bottom')
    lib.cyl(0.8, 3.2, (fx, fy, 0.3), stone, verts=24, r2=0.4, name='FountainCol', coll=coll, origin='bottom')
    lib.cyl(2.0, 0.4, (fx, fy, 3.4), stone, verts=32, name='FountainBowl', coll=coll, origin='bottom')
    cafe_rng = random.Random(5)
    par_cols = ['#EFE6D6', '#C8473F', '#E7DCC6']
    for ty in range(int(SQUARE[0]) + 4, int(SQUARE[1]) - 2, 4):
        for tx in (BLVD + 2.0, BLVD + 7.4):          # 3.9 m aisle between the inner chairs for the café camera
            table_set(tx, ty, coll, cafe_rng)
            parasol(tx, ty, coll, cafe_rng.choice(par_cols))
    # café building on the far side of the square gets a sign
    sign_m = lib.mat('SignText', '#F3EDE2', rough=0.6)
    lib.text_obj('CAFÉ DE LA PLACE', size=1.1, loc=(sq_x1 - 2.4, fy, 5.0), rot=(math.pi / 2, 0, -math.pi / 2), mat_=sign_m, coll=coll)

    # people: boulevard sidewalks, square, side streets
    prs = random.Random(9)
    for i in range(70):
        sx = prs.choice([-1, 1])
        x = sx * prs.uniform(BLVD - 3.4, BLVD - 0.6)
        y = prs.uniform(-30, 260)
        if sx > 0 and SQUARE[0] - 8 < y < SQUARE[0] + 14:
            continue      # keep the café camera clear
        walker(x, y, prs.choice([-1, 1]), coll, prs, name=f'B{i}')
    for i in range(26):
        walker(prs.uniform(sq_x0 + 10, sq_x1 - 4), prs.uniform(SQUARE[0], SQUARE[1]), prs.choice([-1, 1]), coll, prs, length=20, name=f'Q{i}')
    for r in ROWS:
        yy = r * period + period / 2
        for i in range(6):
            X = prs.choice([-1, 1]) * xs[prs.choice([0, 1, 2])]
            x = X + prs.uniform(-18, 18)
            # stay on this block's paving (no floating over the crossing)
            walker_x(x, yy + prs.choice([-1, 1]) * prs.uniform(5.6, 6.6), -1 if x > X else 1, coll, prs, length=15, name=f'S{r}_{i}')
    for i in range(7):
        group(prs.uniform(sq_x0 + 12, sq_x1 - 6), prs.uniform(SQUARE[0] + 4, SQUARE[1] - 4), coll, prs, n=prs.choice([2, 2, 3]), name=f'G{i}_')

    # traffic: boulevard both ways, some side streets
    crs = random.Random(3)
    for i in range(16):
        lane = crs.choice([-1, 1])
        x = lane * crs.choice([2.4, 5.6])
        y = crs.uniform(-60, 400)
        c = lib.car((x, y, 0), math.pi / 2 if lane > 0 else -math.pi / 2, coll=coll, kind=crs.choice(['sedan', 'sedan', 'van']), rng=crs)
        lib.drive(c, [(x, y, 0), (x, y + lane * 200, 0)], t0=crs.uniform(0, 1.0), speed=crs.uniform(5, 9), accel=2.0)
    for r in ROWS:
        if crs.random() < 0.5:
            yy = r * period + period / 2 + 2.4
            x = crs.uniform(-200, 200)
            c = lib.car((x, yy, 0), 0, coll=coll, rng=crs)
            lib.drive(c, [(x, yy, 0), (x + 150, yy, 0)], t0=0, speed=crs.uniform(5, 8))

    # civilisation beyond the city
    civ.town((-520, 900), coll, n=30, spread=(260, 90), hmin=14, hmax=40, seed=12)
    civ.town((560, 980), coll, n=30, spread=(260, 90), hmin=14, hmax=48, seed=13)

    # cameras (9:16)
    if variant == 'aerial':        # drone drifts over the roofs towards the tower
        cam = lib.camera((-70, 20, 105), (0, 560, 90), lens=30)
        lib.animate_camera(cam, [(0, (-70, 20, 105)), (dur, (-52, 75, 98))], [(0, (0, 560, 80)), (dur, (0, 560, 90))])
    elif variant == 'cafe':        # down the aisle between the terrace tables, fountain and square ahead
        ax = BLVD + 4.7                            # middle of the aisle, ~2 m from the inner chairs
        cam = lib.camera((ax, SQUARE[0] - 1, 1.45), (ax + 1.0, SQUARE[0] + 22, 1.1), lens=30)
        lib.animate_camera(cam, [(0, (ax, SQUARE[0] - 1, 1.45)), (dur, (ax, SQUARE[0] + 4, 1.5))],
                           [(0, (ax + 1.0, SQUARE[0] + 22, 1.1)), (dur, (ax + 1.5, SQUARE[0] + 27, 1.2))])
    else:                          # boulevard: walk forward and tilt up to the tower
        cam = lib.camera((0.0, -10, 1.7), (0.0, 200, 8), lens=30)
        lib.animate_camera(cam, [(0, (0.0, -10, 1.7)), (dur, (0.0, -10 + 1.4 * dur, 3.7))],
                           [(0, (0.0, 200, 8)), (dur, (0.0, 300, 78))])
    # depth precision: with clip_start 0.02 the asphalt plane under the 18 cm paving flickered through the sidewalks
    # in whole frames (the "road lag" on the aerial). Nothing is ever closer than 0.1 m to these cameras.
    cam.data.clip_start = 1.0 if variant == 'aerial' else 0.1
    lib.bloom(strength=0.3, threshold=1.2, size=7)
    return dict(samples=48, fill=1.0, exposure=0.38)
