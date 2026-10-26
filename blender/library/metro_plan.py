"""Plan of the permanent city «Метрополис» (style «блендер», 26.10.2026). Pure Python, no bpy: the same seed always gives
the same city, so every reel films the same streets. Writes metro_plan.json next to this file.

    python3 blender/library/metro_plan.py            # rebuild the plan
    python3 blender/library/metro_plan.py --map map.png   # + a 2D map (needs Pillow)

How the city is laid out (x east, y north, metres, z up):
- A river 700 m wide runs east-west; the main bank (y > 0) is the city, the south bank (y < -700) a low borough.
- Along the main bank: promenade (y 0..12) and a six-lane embankment highway (y 12..42).
- Grid: avenues north-south every 240 m (ROW 32 m), streets east-west every 90 m (ROW 20 m). Blocks ~208 x 70 m.
- A diagonal avenue (like Broadway) cuts the grid from the waterfront to the park, leaving wedge buildings and a plaza
  with billboards where it crosses the main avenue (x = 0).
- Height follows land value: two clusters of towers (downtown at the water, midtown with the spire landmark), a lower
  «valley» between them, mid-rise residential around, warehouses and piers on the west bank, brownstones over the river.
- Blocks are cut into lots the way real ones are: towers take whole blocks with a podium on the street line, mid-rises
  fill narrow lots facing the street with rear yards behind, corners are often taller.
- A big park north of midtown with a lake; two suspension bridges cross the river along avenues.
"""
import json
import math
import os
import random
import sys

SEED = 7
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'metro_plan.json')

RIVER_S = -700.0            # south shore line
PROM, HWY0, HWY1 = 12.0, 12.0, 42.0
CITY_Y0 = 50.0              # first street centre line is at 60
AVE_STEP, AVE_ROW, AVE_ROAD = 240.0, 32.0, 20.0
ST_STEP, ST_ROW, ST_ROAD = 90.0, 20.0, 11.0
X0, X1 = -1920.0, 1920.0
Y_TOP = 4260.0
PARK = (-480.0, 2400.0, 480.0, 3600.0)          # x0, y0, x1, y1 (avenue centres / street centres)
DIAG_A, DIAG_B, DIAG_ROW = (-1300.0, 30.0), (283.0, 2400.0), 26.0
BRIDGES = [(-1200.0, 'Старый мост'), (960.0, 'Новый мост')]
CLUSTERS = [  # name, centre, radius, peak height
    ('Даунтаун', (-150.0, 560.0), 620.0, 440.0),
    ('Мидтаун', (330.0, 1980.0), 760.0, 420.0),
    ('Ист-сайд', (1350.0, 1150.0), 480.0, 170.0),
    ('Аптаун', (0.0, 3950.0), 520.0, 120.0),
]
LANDMARKS = {  # the skyline people remember; placed on fixed blocks
    'spire': dict(at=(250.0, 1880.0), h=443.0, type='deco_tower', name='Башня со шпилем'),
    'black': dict(at=(-370.0, 470.0), h=442.0, type='black_tubes', name='Чёрная башня'),
    'needle': dict(at=(120.0, 380.0), h=520.0, type='glass_tower', name='Игла', shape='taper'),
    'crown': dict(at=(-620.0, 1560.0), h=320.0, type='deco_tower', name='Корона', crown='arch'),
    'billboards': dict(at=(0.0, 1982.0), h=60.0, type='billboard_block', name='Площадь'),
}


# ----------------------------------------------------------------------------- geometry helpers
def clip(poly, a, b, keep_left=True):
    """Sutherland-Hodgman: keep the part of a convex polygon on the left (or right) of the line a->b."""
    def side(p):
        s = (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])
        return s if keep_left else -s
    out = []
    n = len(poly)
    for i in range(n):
        p, q = poly[i], poly[(i + 1) % n]
        sp, sq = side(p), side(q)
        if sp >= 0:
            out.append(p)
        if (sp >= 0) != (sq >= 0):
            t = sp / (sp - sq)
            out.append((p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t))
    return out


def area(poly):
    return 0.5 * sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1]
                     for i in range(len(poly)))


def centroid(poly):
    return (sum(p[0] for p in poly) / len(poly), sum(p[1] for p in poly) / len(poly))


def rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def min_width(poly):
    """Smallest extent over the polygon's edge directions (rotating calipers, fine for small convex polys)."""
    best = 1e9
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy)
        if L < 1e-6:
            continue
        nx, ny = -dy / L, dx / L
        ds = [(p[0] - a[0]) * nx + (p[1] - a[1]) * ny for p in poly]
        best = min(best, max(ds) - min(ds))
    return best


def r2(poly):
    return [[round(p[0], 2), round(p[1], 2)] for p in poly]


# ----------------------------------------------------------------------------- the plan
def height_field(x, y):
    h = 0.0
    for _, (cx, cy), r, peak in CLUSTERS:
        d = math.hypot(x - cx, y - cy)
        h = max(h, peak * math.exp(-(d / r) ** 2))
    return h


def diag_side(p):
    a, b = DIAG_A, DIAG_B
    return (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])


def diag_lines():
    """Two edges of the diagonal's right-of-way, extended past the city."""
    a, b = DIAG_A, DIAG_B
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy)
    ux, uy = dx / L, dy / L
    nx, ny = -uy, ux
    ext = 400.0
    A = (a[0] - ux * ext, a[1] - uy * ext)
    B = (b[0] + ux * ext, b[1] + uy * ext)
    h = DIAG_ROW / 2
    left = ((A[0] + nx * h, A[1] + ny * h), (B[0] + nx * h, B[1] + ny * h))
    right = ((A[0] - nx * h, A[1] - ny * h), (B[0] - nx * h, B[1] - ny * h))
    return left, right


def avenues():
    n = int(round((X1 - X0) / AVE_STEP))
    return [X0 + i * AVE_STEP for i in range(n + 1)]


def streets():
    out, y = [], CITY_Y0 + 10.0
    while y <= Y_TOP:
        out.append(y)
        y += ST_STEP
    return out


def in_park(x, y):
    return PARK[0] < x < PARK[2] and PARK[1] < y < PARK[3]


def zone_of(cx, cy, hb):
    if cy < 0:
        return 'borough'
    if cx < -1560 and cy < 1500:
        return 'industrial'
    if hb > 150:
        return 'cbd'
    if hb > 55:
        return 'commercial'
    return 'residential'


TYPES = {
    # type: (floor height, facade kind, palette)
    'glass_tower': (4.0, 'curtain', ['#5F7F8E', '#43606F', '#7C909A', '#334650', '#8FA7B2', '#5B6E5E', '#6E7F8F']),
    'dark_tower': (4.0, 'curtain_dark', ['#1D1F22', '#24262A', '#2A2724']),
    'black_tubes': (4.0, 'curtain_dark', ['#1C1D20']),
    'deco_tower': (3.8, 'punched', ['#B9AE9A', '#A89D8B', '#C9BFAD', '#9C9384', '#BDB2A0']),
    'office': (3.9, 'ribbon', ['#9C9B95', '#B2ADA2', '#80837F', '#A59886', '#C2BDB3', '#6F6E6A']),
    'brick_midrise': (3.4, 'brick', ['#7B3F2E', '#8E4A35', '#6B3A2E', '#9C6B52', '#A0745A', '#5E3428', '#B08A6E']),
    'residential': (3.1, 'punched', ['#C9C2B4', '#B7B9B6', '#D8CFC0', '#A9A49A', '#C4B49C', '#9EA4A6']),
    'townhouse': (3.3, 'brick', ['#5E3E30', '#704A38', '#7E5A44', '#8C5B42', '#6A4F44', '#B79B7E']),
    'shop': (4.5, 'shopfront', ['#CFC6B6', '#B9B2A6', '#8C8478', '#D6CDBD']),
    'warehouse': (6.0, 'industrial', ['#8A6E5A', '#6E6A64', '#7D7468', '#5C5F60', '#9A8A72']),
    'billboard_block': (4.2, 'ribbon', ['#55504C']),
}


def pick_type(rng, h, zone, lot_w):
    if zone == 'industrial':
        return 'warehouse' if rng.random() < 0.8 else 'brick_midrise'
    if zone == 'borough':
        if h < 14:
            return rng.choice(['townhouse', 'townhouse', 'shop', 'warehouse'])
        return rng.choice(['brick_midrise', 'brick_midrise', 'residential', 'townhouse'])
    if h > 180:
        return rng.choices(['glass_tower', 'dark_tower', 'deco_tower'], [0.55, 0.2, 0.25])[0]
    if h > 85:
        return rng.choices(['glass_tower', 'office', 'deco_tower', 'dark_tower', 'residential'], [0.35, 0.3, 0.12, 0.08, 0.15])[0]
    if h > 32:
        return rng.choices(['office', 'brick_midrise', 'residential', 'glass_tower'], [0.3, 0.3, 0.32, 0.08])[0]
    if lot_w < 9:
        return 'townhouse'
    return rng.choices(['brick_midrise', 'townhouse', 'shop', 'residential'], [0.45, 0.25, 0.12, 0.18])[0]


def tiers_for(btype, h, rng, fw):
    """Vertical massing: list of (inset_m, z0, z1). Inset is measured from the lot footprint."""
    if btype == 'deco_tower':
        cuts = sorted(rng.sample([0.42, 0.55, 0.66, 0.76, 0.84, 0.9], k=rng.randint(3, 4)))
        out, z0, ins = [], 0.0, 0.0
        for c in cuts + [1.0]:
            z1 = h * c
            out.append((ins, z0, z1))
            z0 = z1
            ins += max(2.5, min(fw * 0.12, 7.0))
            if fw - 2 * ins < 8:
                break
        return out
    if btype in ('glass_tower', 'dark_tower'):
        if h > 120 and rng.random() < 0.55:      # podium on the street line, tower set back
            pod = rng.choice([4, 5, 6, 8]) * 4.0
            ins = min(fw * 0.18, rng.uniform(5, 12))
            out = [(0.0, 0.0, pod), (ins, pod, h)]
            if rng.random() < 0.35:
                out[-1] = (ins, pod, h * 0.78)
                out.append((ins + min(fw * 0.1, 5.0), h * 0.78, h))
            return out
        return [(0.0, 0.0, h)]
    if btype == 'office' and h > 50 and rng.random() < 0.5:
        return [(0.0, 0.0, h * 0.7), (min(fw * 0.12, 4.0), h * 0.7, h)]
    return [(0.0, 0.0, h)]


def roof_for(btype, h, rng):
    r = {}
    if btype == 'brick_midrise' and rng.random() < 0.6:
        r['tank'] = True                         # wooden water tank on legs
    if btype in ('office', 'residential', 'glass_tower', 'dark_tower') and h > 25:
        r['hvac'] = rng.randint(1, 4)
    if btype == 'glass_tower' and h > 200 and rng.random() < 0.3:
        r['helipad'] = True
    if btype in ('dark_tower', 'black_tubes') or (h > 260 and rng.random() < 0.5):
        r['antennas'] = rng.choice([1, 2, 2, 3])
    if btype == 'deco_tower':
        r['crown'] = rng.choice(['spire', 'pyramid', 'lantern'])
    if h > 150:
        r['aviation'] = True                     # red obstruction lights at night
    if btype in ('brick_midrise', 'townhouse', 'deco_tower'):
        r['cornice'] = True
    return r


def subdivide_block(rng, blk, hb, zone):
    """Cut a rectangular block into lots. Returns list of (poly, kind) with kind 'tower' | 'row' | 'corner'."""
    x0, y0, x1, y1 = blk
    w, d = x1 - x0, y1 - y0
    lots = []
    if zone in ('cbd',) or (zone == 'commercial' and rng.random() < 0.5):
        # 1-3 big lots across the full depth
        n = rng.choice([1, 2, 2, 3, 3, 4]) if hb > 150 else rng.choice([2, 3, 3, 4, 5])
        cuts = sorted(rng.uniform(0.25, 0.75) * w for _ in range(n - 1))
        xs = [x0] + [x0 + c for c in cuts] + [x1]
        for a, b in zip(xs, xs[1:]):
            if b - a > 14:
                lots.append((rect(a, y0, b, y1), 'tower'))
        return lots
    if zone == 'industrial':
        xs, x = [x0], x0
        while x < x1 - 30:
            x += rng.uniform(40, 90)
            xs.append(min(x, x1))
        if xs[-1] < x1:
            xs.append(x1)
        for a, b in zip(xs, xs[1:]):
            if b - a > 10:
                lots.append((rect(a + 2, y0 + 4, b - 2, y1 - 4), 'shed'))
        return lots
    # row lots facing the north and the south street, rear yards in between
    dep = min(d * 0.5 - 4, rng.uniform(24, 32))
    for side in (0, 1):
        ya, yb = (y0, y0 + dep) if side == 0 else (y1 - dep, y1)
        x = x0
        while x < x1 - 4:
            if zone == 'borough':
                wl = rng.choice([6.5, 7.0, 7.5, 8.0, 12.0, 18.0, 25.0])
            elif hb < 25:
                wl = rng.choice([8.0, 10.0, 12.0, 16.0, 20.0, 25.0, 30.0])
            else:
                wl = rng.uniform(14, 40)
            b = min(x + wl, x1)
            if x1 - b < 6:
                b = x1
            kind = 'corner' if (x == x0 or b == x1) else 'row'
            lots.append((rect(x, ya, b, yb), kind))
            x = b
    return lots


def build_plan(seed=SEED):
    rng = random.Random(seed)
    aves, sts = avenues(), streets()
    plan = dict(version=1, seed=seed, name='Метрополис', units='m', axes='x east, y north, z up',
                extent=[X0 - 300, RIVER_S - 1000, X1 + 300, Y_TOP + 200], river=dict(y0=RIVER_S, y1=0.0, z=-1.2),
                promenade=[0.0, PROM], highway=[HWY0, HWY1], roads=[], blocks=[], buildings=[], parks=[], bridges=[],
                piers=[], plazas=[], districts=[dict(name=n, center=list(c), r=r, peak=p) for n, c, r, p in CLUSTERS],
                landmarks={})
    R = plan['roads']
    # --- roads: highway, avenues, streets, diagonal; borough grid
    R.append(dict(kind='highway', a=[X0 - 300, 27.0], b=[X1 + 300, 27.0], road=26.0, walk=0.0, lanes=6))
    for x in aves:
        segs = [(CITY_Y0, PARK[1]), (PARK[3], Y_TOP)] if PARK[0] < x < PARK[2] else [(CITY_Y0, Y_TOP)]
        for a, b in segs:
            R.append(dict(kind='avenue', a=[x, a], b=[x, b], road=AVE_ROAD, walk=(AVE_ROW - AVE_ROAD) / 2, lanes=4))
    for y in sts:
        if PARK[1] < y < PARK[3]:
            for a, b in ((X0, PARK[0]), (PARK[2], X1)):
                R.append(dict(kind='street', a=[a, y], b=[b, y], road=ST_ROAD, walk=(ST_ROW - ST_ROAD) / 2, lanes=2))
        else:
            R.append(dict(kind='street', a=[X0, y], b=[X1, y], road=ST_ROAD, walk=(ST_ROW - ST_ROAD) / 2, lanes=2))
    R.append(dict(kind='diagonal', a=list(DIAG_A), b=list(DIAG_B), road=18.0, walk=4.0, lanes=4))
    b_aves = [x for x in aves if abs(x) % 480 < 1 or True][::1]
    b_sts = []
    y = RIVER_S - 60.0
    while y > RIVER_S - 960:
        b_sts.append(y)
        y -= ST_STEP
    R.append(dict(kind='highway', a=[X0 - 300, RIVER_S - 27.0], b=[X1 + 300, RIVER_S - 27.0], road=22.0, walk=0.0, lanes=4))
    for x in aves[::2]:
        R.append(dict(kind='avenue', a=[x, RIVER_S - 50.0], b=[x, RIVER_S - 990.0], road=AVE_ROAD, walk=6.0, lanes=4))
    for y in b_sts:
        R.append(dict(kind='street', a=[X0, y], b=[X1, y], road=ST_ROAD, walk=4.5, lanes=2))

    # --- bridges
    for bx, name in BRIDGES:
        plan['bridges'].append(dict(name=name, x=bx, y0=RIVER_S - 160.0, y1=150.0, towers=[-150.0, -550.0], tower_h=95.0,
                                    deck_z=[10.0, 32.0], width=24.0))
    # --- park
    plan['parks'].append(dict(name='Центральный парк', poly=r2(rect(PARK[0] + AVE_ROW / 2, PARK[1] + ST_ROW / 2,
                                                                    PARK[2] - AVE_ROW / 2, PARK[3] - ST_ROW / 2)),
                              lake=dict(c=[60.0, 3080.0], r=[170.0, 110.0])))
    plan['parks'].append(dict(name='Набережная Боро', poly=r2(rect(X0 - 300, RIVER_S - 50.0, X1 + 300, RIVER_S - 38.0)), kind='strip'))
    # --- piers on the west bank and promenade piers
    for k, x in enumerate(range(-1880, -1500, 95)):
        plan['piers'].append(dict(poly=r2(rect(x, -230.0, x + 42.0, 0.0)), kind='cargo'))
    for x in (-700.0, 300.0, 1500.0):
        plan['piers'].append(dict(poly=r2(rect(x, -90.0, x + 30.0, 0.0)), kind='promenade'))

    # --- blocks and lots
    (dl_a, dl_b), (dr_a, dr_b) = diag_lines()
    bid = 0
    rows = []
    for i in range(len(aves) - 1):
        for j in range(-1, len(sts) - 1):
            x0, x1 = aves[i] + AVE_ROW / 2, aves[i + 1] - AVE_ROW / 2
            if j == -1:
                y0, y1 = CITY_Y0, sts[0] - ST_ROW / 2
            else:
                y0, y1 = sts[j] + ST_ROW / 2, sts[j + 1] - ST_ROW / 2
            if y1 - y0 < 8:
                continue
            rows.append((x0, y0, x1, y1, False))
    for i in range(0, len(aves) - 2, 2):
        for j in range(len(b_sts) - 1):
            x0, x1 = aves[i] + AVE_ROW / 2, aves[i + 2] - AVE_ROW / 2
            y1, y0 = b_sts[j] - ST_ROW / 2, b_sts[j + 1] + ST_ROW / 2
            rows.append((x0, y0, x1, y1, True))
        rows.append((aves[i] + AVE_ROW / 2, b_sts[0] + ST_ROW / 2, aves[i + 2] - AVE_ROW / 2, RIVER_S - 50.0, True))

    for x0, y0, x1, y1, boro in rows:
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        if in_park(cx, cy):
            continue
        hb = 0.0 if boro else height_field(cx, cy)
        zone = 'borough' if boro else zone_of(cx, cy, hb)
        blk_poly = rect(x0, y0, x1, y1)
        plan['blocks'].append(dict(id=len(plan['blocks']), poly=r2(blk_poly), zone=zone, h=round(hb, 1)))
        brng = random.Random(seed * 1000 + int(cx * 7 + cy * 13))
        for poly, kind in subdivide_block(brng, (x0, y0, x1, y1), hb, zone):
            # the diagonal cuts lots into wedges; slivers are dropped
            pieces = [poly]
            if not boro:
                s = [diag_side(p) for p in poly]
                if not (all(v > DIAG_ROW * 30 for v in s) or all(v < -DIAG_ROW * 30 for v in s)):
                    pieces = [clip(poly, dl_a, dl_b, True), clip(poly, dr_a, dr_b, False)]
                    if not (DIAG_A[1] - 60 < cy < DIAG_B[1] + 60):
                        pieces = [poly]
            for pc in pieces:
                if len(pc) < 3 or area(pc) < 40 or min_width(pc) < 5.5:
                    continue
                # bridge approaches keep a clear corridor
                if any(abs(centroid(pc)[0] - bx) < 30 and (centroid(pc)[1] < 170 or centroid(pc)[1] < RIVER_S + 10 and centroid(pc)[1] > RIVER_S - 200)
                       for bx, _ in BRIDGES):
                    continue
                pcx, pcy = centroid(pc)
                lw = min_width(pc)
                if boro:
                    h = brng.choice([10, 12, 13, 15, 16, 20, 24, 30]) if kind != 'shed' else 9
                elif zone == 'industrial':
                    h = brng.uniform(9, 22)
                else:
                    base = height_field(pcx, pcy)
                    if kind == 'tower' and brng.random() < min(0.85, max(0.2, base / 260.0)):
                        h = max(60.0, base * math.exp(brng.gauss(-0.1, 0.38)))
                        h = min(h, 30 + lw * 8.0, 380.0)             # slenderness; landmarks stay taller
                    elif kind == 'tower':
                        h = brng.uniform(24, 26 + base * 0.35)       # mid-rise between the towers
                        kind = 'corner'
                    else:
                        floors = max(3, int(round((14 + base * 0.22) * math.exp(brng.gauss(0, 0.3)) / 3.3)))
                        if kind == 'corner':
                            floors += brng.choice([0, 1, 2, 4])
                        h = floors * 3.3
                    if pcy < 160:
                        h = min(h, 9999)
                btype = pick_type(brng, h, zone, lw)
                fh, fkind, pal = TYPES[btype]
                h = max(fh * 2, round(h / fh) * fh) if btype not in ('shop', 'warehouse') else (fh * brng.choice([1, 2]) if btype == 'shop' else h)
                fw = lw
                retail = (zone in ('cbd', 'commercial') or (zone == 'residential' and brng.random() < 0.45) or
                          (zone == 'borough' and brng.random() < 0.3)) and btype not in ('warehouse',)
                plan['buildings'].append(dict(
                    id=bid, poly=r2(pc), h=round(h, 1), type=btype, facade=fkind, floor_h=fh, color=brng.choice(pal),
                    tiers=[[round(a, 2), round(b, 2), round(c, 2)] for a, b, c in tiers_for(btype, h, brng, fw)],
                    roof=roof_for(btype, h, brng), retail=bool(retail), zone=zone, seed=brng.randint(0, 99999),
                    bay=round(brng.choice([1.5, 1.5, 3.0]) if fkind.startswith('curtain') else brng.uniform(2.6, 3.6), 2)))
                bid += 1

    # --- landmarks replace the generated building whose lot holds their point
    for key, lm in LANDMARKS.items():
        px, py = lm['at']
        # the nearest lot to the landmark point (the point may sit on a road)
        best = min(plan['buildings'], key=lambda b: math.hypot(centroid(b['poly'])[0] - px, centroid(b['poly'])[1] - py))
        bc = centroid(best['poly'])
        # a landmark takes the whole block: drop the other lots of that block
        blk = next(k for k in plan['blocks'] if min(p[0] for p in k['poly']) <= bc[0] <= max(p[0] for p in k['poly'])
                   and min(p[1] for p in k['poly']) <= bc[1] <= max(p[1] for p in k['poly']))
        px = min(max(px, min(p[0] for p in blk['poly']) + 41), max(p[0] for p in blk['poly']) - 41)
        bx0, by0 = min(p[0] for p in blk['poly']), min(p[1] for p in blk['poly'])
        bx1, by1 = max(p[0] for p in blk['poly']), max(p[1] for p in blk['poly'])
        if key == 'billboards':
            best['type'], best['h'], best['landmark'] = 'billboard_block', lm['h'], key
            best['facade'] = 'ribbon'
            plan['plazas'].append(dict(name=lm['name'], c=list(lm['at']), r=70.0, billboards=True))
            plan['landmarks'][key] = dict(name=lm['name'], id=best['id'], at=[px, py], h=lm['h'])
            continue
        plan['buildings'] = [b for b in plan['buildings'] if b is best or not (
            bx0 <= centroid(b['poly'])[0] <= bx1 and by0 <= centroid(b['poly'])[1] <= by1)]
        w = min(bx1 - bx0, by1 - by0)
        if key == 'black':
            lot = rect(px - 33, by0 + 1, px + 33, by0 + 67)
        else:
            lot = rect(max(bx0, px - 40), by0, min(bx1, px + 40), by1)
        fh, fkind, pal = TYPES[lm['type']]
        best.update(poly=r2(lot), h=lm['h'], type=lm['type'], facade=fkind, floor_h=fh, landmark=key,
                    color=pal[0] if key != 'needle' else '#6F8A99', retail=True)
        if lm['type'] == 'deco_tower':
            best['tiers'] = [[0.0, 0.0, lm['h'] * 0.18], [5.0, lm['h'] * 0.18, lm['h'] * 0.6], [11.0, lm['h'] * 0.6, lm['h'] * 0.78],
                             [16.0, lm['h'] * 0.78, lm['h'] * 0.86], [21.0, lm['h'] * 0.86, lm['h'] * 0.9]]
            best['roof'] = dict(crown=lm.get('crown', 'spire'), aviation=True, spire=lm['h'] * 0.1 if key == 'spire' else 0)
        elif lm['type'] == 'black_tubes':
            best['tiers'] = []
            best['tubes'] = [[i, j, h] for (i, j), h in zip(
                [(0, 0), (1, 0), (2, 0), (0, 1), (1, 1), (2, 1), (0, 2), (1, 2), (2, 2)],
                [0.6, 1.0, 0.6, 0.82, 1.0, 0.82, 0.48, 0.92, 0.48])]
            best['roof'] = dict(antennas=2, aviation=True)
        elif key == 'needle':
            best['tiers'] = [[0.0, 0.0, 30.0], [8.0, 30.0, lm['h'] * 0.86]]
            best['shape'] = 'taper'
            best['roof'] = dict(spire=lm['h'] * 0.14, aviation=True)
        plan['landmarks'][key] = dict(name=lm['name'], id=best['id'], at=[px, py], h=lm['h'])

    # --- camera spots: named places every reel can reuse
    plan['spots'] = {
        'skyline_dusk': dict(cam=[300.0, -950.0, 80.0], target=[420.0, 1500.0, 140.0], lens=35, preset='dusk',
                             desc='скайлайн через реку с набережной Боро, мост справа (как второй референс)'),
        'aerial_night': dict(cam=[1100.0, -420.0, 280.0], target=[-600.0, 380.0, 60.0], lens=24, preset='night',
                             desc='с высоты над рекой: набережная с потоком фар, огни кварталов (как первый референс)'),
        'avenue': dict(cam=[-226.0, 230.0, 1.7], target=[-236.0, 1400.0, 90.0], lens=26, preset='day',
                       desc='на тротуаре проспекта в даунтауне, башни по сторонам'),
        'plaza': dict(cam=[-13.0, 1905.0, 1.7], target=[5.0, 2060.0, 28.0], lens=22, preset='night',
                      desc='площадь с рекламными экранами на диагонали'),
        'embankment': dict(cam=[-300.0, 4.0, 1.7], target=[600.0, 60.0, 30.0], lens=26, preset='golden',
                           desc='прогулочная набережная, шоссе и башни даунтауна'),
        'bridge': dict(cam=[1180.0, -702.5, 2.0], target=[960.0, -350.0, 60.0], lens=24, preset='dusk',
                       desc='Новый мост с набережной Боро, город за ним'),
        'park': dict(cam=[-60.0, 3255.0, 1.9], target=[250.0, 1880.0, 120.0], lens=30, preset='day',
                     desc='с северного берега озера в парке на Мидтаун и башню со шпилем'),
        'rooftop': dict(cam=[-760.0, 880.0, 60.0], target=[-200.0, 500.0, 160.0], lens=30, preset='golden',
                        desc='с крыши кирпичного дома на даунтаун'),
    }
    return plan


def draw_map(plan, path, px_per_m=0.3):
    from PIL import Image, ImageDraw, ImageFont
    try:
        font = ImageFont.truetype('DejaVuSans.ttf', 22)
        small = ImageFont.truetype('DejaVuSans.ttf', 16)
    except OSError:
        font = small = ImageFont.load_default()
    ex = plan['extent']
    W, H = int((ex[2] - ex[0]) * px_per_m), int((ex[3] - ex[1]) * px_per_m)
    im = Image.new('RGB', (W, H), '#2B2F33')
    d = ImageDraw.Draw(im)

    def P(x, y):
        return ((x - ex[0]) * px_per_m, H - (y - ex[1]) * px_per_m)

    d.rectangle([P(ex[0], plan['river']['y1']), P(ex[2], plan['river']['y0'])], fill='#1E3A4E')
    for r in plan['roads']:
        w = max(1, int((r['road'] + 2 * r['walk']) * px_per_m))
        d.line([P(*r['a']), P(*r['b'])], fill='#4A4E52' if r['kind'] != 'highway' else '#6A5A3A', width=w)
    for p in plan['parks']:
        d.polygon([P(*q) for q in p['poly']], fill='#2F5A36')
        if 'lake' in p:
            c, rr = p['lake']['c'], p['lake']['r']
            d.ellipse([P(c[0] - rr[0], c[1] + rr[1]), P(c[0] + rr[0], c[1] - rr[1])], fill='#1E3A4E')
    for p in plan['piers']:
        d.polygon([P(*q) for q in p['poly']], fill='#6B6258')

    def col(h):
        t = min(1.0, h / 300.0)
        return (int(140 + 115 * t), int(130 + 40 * (1 - t)), int(120 - 60 * t))

    for b in sorted(plan['buildings'], key=lambda b: b['h']):
        d.polygon([P(*q) for q in b['poly']], fill=col(b['h']), outline='#222')
    for br in plan['bridges']:
        d.line([P(br['x'], br['y0']), P(br['x'], br['y1'])], fill='#C9A15A', width=max(2, int(br['width'] * px_per_m)))
    for name, s in plan['spots'].items():
        cx, cy = P(s['cam'][0], s['cam'][1])
        tx, ty = P(s['target'][0], s['target'][1])
        d.line([(cx, cy), (cx + (tx - cx) * 0.15, cy + (ty - cy) * 0.15)], fill='#FFD24A', width=2)
        d.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill='#FFD24A')
        d.text((cx + 8, cy - 8), name, fill='#FFD24A', font=small)
    for key, lm in plan['landmarks'].items():
        x, y = P(*lm['at'])
        d.ellipse([x - 5, y - 5, x + 5, y + 5], outline='#FFFFFF', width=2)
        d.text((x + 9, y - 10), lm['name'], fill='#FFFFFF', font=font)
    for dd in plan['districts']:
        x, y = P(*dd['center'])
        d.text((x - 40, y - 60), dd['name'].upper(), fill='#E8E2D6', font=font)
    d.text(P(ex[0] + 60, -330), 'РЕКА', fill='#7FA7C4', font=font)
    d.text(P(ex[0] + 60, RIVER_S - 300), 'БОРО (малоэтажный берег)', fill='#E8E2D6', font=font)
    for p in plan['parks'][:1]:
        x, y = P(*centroid(p['poly']))
        d.text((x - 110, y + 60), p['name'], fill='#CFE8C8', font=font)
    # legend: height colours
    lx, ly = 20, H - 120
    d.rectangle([lx - 10, ly - 34, lx + 430, ly + 60], fill='#1E2226')
    d.text((lx, ly - 30), 'высота зданий', fill='#E8E2D6', font=small)
    for i, hh in enumerate((10, 30, 80, 150, 250, 400)):
        d.rectangle([lx + i * 70, ly, lx + i * 70 + 60, ly + 22], fill=col(hh))
        d.text((lx + i * 70 + 4, ly + 28), f'{hh} м', fill='#E8E2D6', font=small)
    im.save(path)
    return path


if __name__ == '__main__':
    plan = build_plan()
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(plan, f, ensure_ascii=False, separators=(',', ':'))
    hs = sorted(b['h'] for b in plan['buildings'])
    from collections import Counter
    print('buildings', len(plan['buildings']), 'blocks', len(plan['blocks']), 'roads', len(plan['roads']),
          'tallest', hs[-5:], 'median', hs[len(hs) // 2])
    print(Counter(b['type'] for b in plan['buildings']))
    if '--map' in sys.argv:
        print('map', draw_map(plan, sys.argv[sys.argv.index('--map') + 1]))
