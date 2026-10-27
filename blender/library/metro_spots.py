"""Camera places in «Метрополис» anywhere on the map (style «блендер», 26.10.2026). Pure Python, no bpy.

The user: «точки можешь делать на разных местах карты, по своему усмотрению, тк если мы будем часто юзать данный
город, то ролики будут однотипными с одними и теми же местами». So every reel gets new places: a kind of shot plus a
seed (reel id / shot id) gives a camera, a target, a lens and a time of day; places used by earlier reels are avoided.

    python3 metro_spots.py --kinds street,skyline,aerial --seed my-reel            # print spots as JSON
    python3 metro_spots.py --kinds street,lookup --seed my-reel --log my-reel        # and remember them
    python3 metro_spots.py --all --seed demo                                         # one spot of every kind
    python3 metro_spots.py --shots projects/<id>/blender/shots.json --log <id>       # fill a reel's shots.json

Kinds: street, avenue, borough, corner, lookup, waterfront, skyline, river, aerial, rooftop, bridge, deck, park.
In a reel's shots.json write "spot": {"kind": "street"} and run --shots before the render: the places are written into
the shot (cam/target/lens/preset) and into the journal projects/metro-city/spots_used.json, so later reels avoid them.
The eight v1 spots of metro_plan count as used too.
"""
import hashlib
import json
import math
import os
import random
import sys

import metro_plan as MP

HERE = os.path.dirname(os.path.abspath(__file__))
USED = os.path.join(HERE, '..', '..', 'projects', 'metro-city', 'spots_used.json')
KINDS = ['street', 'avenue', 'borough', 'corner', 'lookup', 'waterfront', 'skyline', 'river', 'aerial', 'rooftop',
         'bridge', 'deck', 'park']
PRESET_W = {  # how often each time of day suits a kind (day, golden, dusk, night)
    'street': (0.35, 0.25, 0.2, 0.2), 'avenue': (0.3, 0.25, 0.2, 0.25), 'borough': (0.35, 0.35, 0.15, 0.15),
    'corner': (0.3, 0.2, 0.2, 0.3), 'lookup': (0.4, 0.25, 0.2, 0.15), 'waterfront': (0.2, 0.35, 0.3, 0.15),
    'skyline': (0.15, 0.25, 0.35, 0.25), 'river': (0.15, 0.3, 0.35, 0.2), 'aerial': (0.2, 0.25, 0.2, 0.35),
    'rooftop': (0.2, 0.35, 0.3, 0.15), 'bridge': (0.15, 0.3, 0.35, 0.2), 'deck': (0.25, 0.3, 0.3, 0.15),
    'park': (0.5, 0.35, 0.1, 0.05),
}
_P = None
_GRID = None


def plan():
    global _P
    if _P is None:
        _P = MP.build_plan()
    return _P


def rng_for(*parts):
    h = hashlib.md5('/'.join(str(p) for p in parts).encode('utf-8')).hexdigest()
    return random.Random(int(h[:12], 16))


# ----------------------------------------------------------------------------- what stands where
def grid():
    global _GRID
    if _GRID is None:
        _GRID = {}
        for b in plan()['buildings']:
            xs, ys = [p[0] for p in b['poly']], [p[1] for p in b['poly']]
            for i in range(int(min(xs) // 50), int(max(xs) // 50) + 1):
                for j in range(int(min(ys) // 50), int(max(ys) // 50) + 1):
                    _GRID.setdefault((i, j), []).append(b)
    return _GRID


def _inside(poly, x, y):
    n, c = len(poly), False
    for i in range(n):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            c = not c
    return c


def building_at(x, y, margin=0.0):
    for b in grid().get((int(x // 50), int(y // 50)), []):
        if _inside(b['poly'], x, y):
            return b
        if margin:
            for dx, dy in ((margin, 0), (-margin, 0), (0, margin), (0, -margin)):
                if _inside(b['poly'], x + dx, y + dy):
                    return b
    return None


def clear(cam, tgt, dist=60.0, step=2.0):
    """No building wall right in front of the lens (2D march, height-aware)."""
    dx, dy, dz = tgt[0] - cam[0], tgt[1] - cam[1], tgt[2] - cam[2]
    L = math.hypot(dx, dy) or 1.0
    s = 1.0
    while s < min(dist, L):
        x, y = cam[0] + dx / L * s, cam[1] + dy / L * s
        z = cam[2] + dz * s / L
        b = building_at(x, y)
        if b is not None and b['h'] > z:
            return False
        s += step
    return True


def free(x, y, z=1.7):
    b = building_at(x, y, 1.2)
    return b is None or b['h'] + 0.5 < z


# ----------------------------------------------------------------------------- helpers
def roads(kind, main=True):
    out = []
    for r in plan()['roads']:
        if r['kind'] != kind:
            continue
        ym = (r['a'][1] + r['b'][1]) / 2
        if (ym > 0) == main:
            out.append(r)
    return out


def crossings(r):
    """Distances along r where it crosses perpendicular roads (axis-aligned plan roads)."""
    ax, ay = r['a']
    bx, by = r['b']
    vert = abs(bx - ax) < 1e-6
    out = []
    for o in plan()['roads']:
        if o is r or o['kind'] == 'diagonal':
            continue
        if vert and abs(o['b'][1] - o['a'][1]) < 1e-6 and min(o['a'][0], o['b'][0]) <= ax <= max(o['a'][0], o['b'][0]):
            out.append(((o['a'][1] - ay) * (1 if by > ay else -1), o['road'] / 2 + o['walk']))
        if not vert and abs(o['b'][0] - o['a'][0]) < 1e-6 and min(o['a'][1], o['b'][1]) <= ay <= max(o['a'][1], o['b'][1]):
            out.append(((o['a'][0] - ax) * (1 if bx > ax else -1), o['road'] / 2 + o['walk']))
    return out


def along(r, u, v):
    ax, ay = r['a']
    bx, by = r['b']
    L = math.hypot(bx - ax, by - ay)
    ux, uy = (bx - ax) / L, (by - ay) / L
    return ax + ux * u - uy * v, ay + uy * u + ux * v, (ux, uy), L


def landmarks():
    p = plan()
    return [(lm['at'][0], lm['at'][1], lm['h']) for lm in p['landmarks'].values() if lm['h'] > 200] + \
           [(d['center'][0], d['center'][1], d['peak']) for d in p['districts'] if d['peak'] > 300]


def rot(dx, dy, a):
    c, s = math.cos(a), math.sin(a)
    return dx * c - dy * s, dx * s + dy * c


# ----------------------------------------------------------------------------- kinds
def k_street(rng, kind='street', main=True, look_up=(15, 70), label='улица'):
    rs = roads(kind, main)
    for _ in range(80):
        r = rng.choice(rs)
        x, y, (ux, uy), L = along(r, 0, 0)
        u = rng.uniform(30, L - 30)
        if any(abs(u - c) < h + 8 for c, h in crossings(r)):
            continue
        side = rng.choice((-1, 1))
        v = side * (r['road'] / 2 + r['walk'] * rng.uniform(0.3, 0.55))
        cx, cy, _, _ = along(r, u, v)
        dr = rng.choice((-1, 1))
        dx, dy = rot(ux * dr, uy * dr, math.radians(rng.uniform(-8, 8)) - side * dr * math.radians(rng.uniform(0, 10)))
        dist = rng.uniform(250, 600)
        hz = MP.height_field(cx, cy)
        tz = rng.uniform(*look_up) * (1.6 if hz > 150 else 1.0)
        cam, tgt = [cx, cy, rng.uniform(1.6, 1.8)], [cx + dx * dist, cy + dy * dist, tz]
        if free(cx, cy) and clear(cam, tgt, 30):
            return cam, tgt, rng.uniform(22, 32), f'{label}: тротуар, взгляд вдоль'
    return None


def k_corner(rng):
    aves, sts = MP.avenues(), [y for y in MP.streets() if not MP.in_park(0, y)]
    for _ in range(80):
        ax, sy = rng.choice(aves[1:-1]), rng.choice(sts[1:-2])
        sx, sy_ = rng.choice((-1, 1)), rng.choice((-1, 1))
        # on the avenue sidewalk a few metres back from the corner (zebras and signals stay in front of the lens)
        walk = (MP.AVE_ROW - MP.AVE_ROAD) / 2
        cx = ax + sx * (MP.AVE_ROAD / 2 + walk * rng.uniform(0.35, 0.6))
        cy = sy + sy_ * (MP.ST_ROW / 2 + rng.uniform(5, 16))
        tx, ty = ax - sx * rng.uniform(60, 130), sy - sy_ * rng.uniform(50, 90)
        hz = MP.height_field(tx, ty)
        cam, tgt = [cx, cy, 1.7], [tx, ty, rng.uniform(20, 60) + hz * 0.25]
        if free(cx, cy) and not MP.in_park(cx, cy):
            return cam, tgt, rng.uniform(20, 26), 'перекрёсток: угол тротуара, взгляд через перекрёсток'
    return None


def k_lookup(rng):
    tall = [b for b in plan()['buildings'] if b['h'] > 150]
    for _ in range(80):
        b = rng.choice(tall)
        poly = b['poly']
        i = rng.randrange(len(poly))
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % len(poly)]
        L = math.hypot(x2 - x1, y2 - y1)
        if L < 15:
            continue
        nx, ny = (y2 - y1) / L, -(x2 - x1) / L
        if MP.area(poly) < 0:
            nx, ny = -nx, -ny
        t = rng.uniform(0.2, 0.8)
        d = rng.uniform(7, 13)
        cx, cy = x1 + (x2 - x1) * t + nx * d, y1 + (y2 - y1) * t + ny * d
        c = MP.centroid(poly)
        cam, tgt = [cx, cy, 1.6], [c[0] + (x2 - x1) * 0.1, c[1] + (y2 - y1) * 0.1, b['h'] * rng.uniform(0.6, 0.9)]
        if free(cx, cy):
            return cam, tgt, rng.uniform(16, 22), f'взгляд вверх вдоль башни {int(b["h"])} м'
    return None


def k_waterfront(rng):
    for _ in range(80):
        main = rng.random() < 0.6
        x = rng.uniform(MP.X0 + 100, MP.X1 - 100)
        if any(abs(x - bx) < 60 for bx, _ in MP.BRIDGES):
            continue
        if main:
            cam = [x, rng.uniform(3, 9), 2.0]
            dr = rng.choice((-1, 1))
            a = math.radians(rng.uniform(4, 22)) * rng.choice((-1, 1))
            dx, dy = rot(dr, 0, a)
            tgt = [x + dx * 600, cam[1] + dy * 600, rng.uniform(10, 50)]
            desc = 'набережная, вдоль берега'
        else:
            cam = [x, MP.RIVER_S - rng.uniform(3, 9), 2.0]
            lm = rng.choice(landmarks())
            tgt = [lm[0] + rng.uniform(-300, 300), lm[1], lm[2] * rng.uniform(0.3, 0.5)]
            desc = 'набережная Боро, через реку на город'
        if clear(cam, tgt, 20):
            return cam, tgt, rng.uniform(24, 35), desc
    return None


def k_skyline(rng):
    for _ in range(80):
        mode = rng.choice(['boro', 'boro_high', 'north', 'east', 'west'])
        # east/west stand above the river: beyond the plan the city is only filler blocks, not for the foreground
        lm = rng.choice(landmarks())
        if mode in ('boro', 'boro_high'):
            x = lm[0] + rng.uniform(-1500, 1500)
            y = MP.RIVER_S - (rng.uniform(4, 10) if mode == 'boro' else rng.uniform(30, 500))
            z = 2.0 if mode == 'boro' else rng.uniform(40, 140)
            lens = rng.uniform(35, 60)
        elif mode == 'north':
            x, y, z = rng.uniform(-1500, 1500), MP.Y_TOP - rng.uniform(80, 450), rng.uniform(120, 300)
            lens = rng.uniform(35, 60)
        else:
            sx = 1 if mode == 'east' else -1
            x, y, z = sx * rng.uniform(2000, 2600), rng.uniform(MP.RIVER_S + 150, -150), rng.uniform(60, 200)
            lens = rng.uniform(45, 70)                 # long lens: the skyline big through the haze
        cam = [x, y, z]
        tgt = [lm[0] + rng.uniform(-200, 200), lm[1] + rng.uniform(-200, 200), lm[2] * rng.uniform(0.25, 0.45)]
        if free(x, y, z) and clear(cam, tgt, 80):
            return cam, tgt, lens, f'скайлайн ({mode})'
    return None


def k_river(rng):
    sx = rng.choice((-1, 1))
    x = sx * rng.uniform(2300, 3400)
    y = rng.uniform(MP.RIVER_S + 120, -120)
    z = rng.uniform(15, 120)
    tgt = [-sx * rng.uniform(0, 800), rng.uniform(-400, 300), rng.uniform(40, 120)]
    return [x, y, z], tgt, rng.uniform(28, 45), 'над рекой, вдоль реки на город'


def k_aerial(rng):
    p = plan()
    centres = landmarks() + [(d['center'][0], d['center'][1], d['peak']) for d in p['districts']] + \
              [(br['x'], -350.0, 100.0) for br in p['bridges']] + [(0.0, 3000.0, 30.0)]
    c = rng.choice(centres)
    a = rng.uniform(0, 2 * math.pi)
    d = rng.uniform(600, 2000)
    cam = [c[0] + math.cos(a) * d, c[1] + math.sin(a) * d, rng.uniform(180, 650)]
    tgt = [c[0], c[1], c[2] * rng.uniform(0.1, 0.4)]
    return cam, tgt, rng.uniform(24, 35), 'с высоты'


def k_rooftop(rng):
    p = plan()
    lms = landmarks()
    cand = [b for b in p['buildings'] if 20 < b['h'] < 90 and b['zone'] != 'borough' and
            min(math.hypot(MP.centroid(b['poly'])[0] - lx, MP.centroid(b['poly'])[1] - ly) for lx, ly, _ in lms) < 1300]
    for _ in range(120):
        b = rng.choice(cand)
        c = MP.centroid(b['poly'])
        lm = min(lms, key=lambda l: math.hypot(l[0] - c[0], l[1] - c[1]) + rng.uniform(0, 400))
        dx, dy = lm[0] - c[0], lm[1] - c[1]
        L = math.hypot(dx, dy) or 1.0
        w = MP.min_width(b['poly'])
        cx, cy = c[0] + dx / L * w * 0.3, c[1] + dy / L * w * 0.3
        cam = [cx, cy, b['h'] + 2.1]
        tgt = [lm[0], lm[1], lm[2] * rng.uniform(0.35, 0.6)]
        if MP.centroid(b['poly']) and _inside(b['poly'], cx, cy) and clear(cam, tgt, 120):
            return cam, tgt, rng.uniform(24, 32), f'крыша дома {int(b["h"])} м'
    return None


def k_bridge(rng):
    """From the Boro side the city stands behind the bridge; from the city side only Boro, so that one by day."""
    br = rng.choice(plan()['bridges'])
    side = rng.choice((-1, 1))
    main = rng.random() < 0.3
    y = rng.uniform(3, 9) if main else MP.RIVER_S - rng.uniform(3, 9)
    x = br['x'] + side * rng.uniform(120, 450)
    tgt = [br['x'] - side * rng.uniform(0, 60), rng.uniform(-550, -150), rng.uniform(40, 80)]
    if main:
        return [x, y, 2.0], tgt, rng.uniform(22, 30), f'{br["name"]} с набережной города', (0.6, 0.4, 0.0, 0.0)
    return [x, y, 2.0], tgt, rng.uniform(22, 30), f'{br["name"]} с набережной Боро, город за мостом'


def k_deck(rng):
    br = rng.choice(plan()['bridges'])
    y = rng.uniform(-620, -80)
    side = rng.choice((-1, 1))
    x = br['x'] + side * (br['width'] / 2 - 1.0)
    z = MP.deck_z(br, y) + 1.75
    north = rng.random() < 0.85
    tgt = [br['x'] + rng.uniform(-80, 80), (y + 900) if north else (y - 900), rng.uniform(30, 120) if north else 20]
    return [x, y, z], tgt, rng.uniform(22, 28), f'на пешеходной части: {br["name"]}'


def k_park(rng):
    pk = plan()['parks'][0]
    xs, ys = [p[0] for p in pk['poly']], [p[1] for p in pk['poly']]
    lc, lr = pk['lake']['c'], pk['lake']['r']
    for _ in range(80):
        x, y = rng.uniform(min(xs) + 30, max(xs) - 30), rng.uniform(min(ys) + 30, max(ys) - 30)
        ex, ey = (x - lc[0]) / (lr[0] + 6), (y - lc[1]) / (lr[1] + 6)
        if ex * ex + ey * ey < 1.0:
            continue
        lm = rng.choice(landmarks() + [(lc[0], lc[1], 5.0)])
        tgt = [lm[0], lm[1], max(5.0, lm[2] * rng.uniform(0.3, 0.5))]
        return [x, y, 1.9], tgt, rng.uniform(24, 34), 'в парке'
    return None


MAKERS = dict(street=k_street, avenue=lambda r: k_street(r, 'avenue', look_up=(25, 110), label='проспект'),
              borough=lambda r: k_street(r, 'street', main=False, look_up=(5, 25), label='Боро'), corner=k_corner,
              lookup=k_lookup,
              waterfront=k_waterfront, skyline=k_skyline, river=k_river, aerial=k_aerial, rooftop=k_rooftop,
              bridge=k_bridge, deck=k_deck, park=k_park)


def load_used(path=USED):
    """Places taken by earlier reels plus the eight v1 spots of the plan (they are the most familiar ones)."""
    try:
        used = json.load(open(path, encoding='utf-8'))
    except (OSError, ValueError):
        used = []
    return used + [dict(reel='v1', key=f'v1:{k}', cam=s['cam']) for k, s in plan()['spots'].items()]


def make_spot(kind, seed, preset=None, used=None, min_gap=180.0):
    """A new place of the given kind; deterministic for (kind, seed); keeps min_gap metres from used places."""
    used = load_used() if used is None else used
    for u in used:                         # already chosen for this reel: same place again
        if u.get('key') == f'{kind}:{seed}':
            return dict(kind=kind, cam=u['cam'], target=u['target'], lens=u['lens'], preset=preset or u['preset'],
                        desc=u.get('desc', ''), seed=u['seed'])
    for attempt in range(40):
        rng = rng_for(kind, seed, attempt)
        res = MAKERS[kind](rng)
        if not res:
            continue
        cam, tgt, lens, desc = res[:4]
        w = res[4] if len(res) > 4 else PRESET_W[kind]      # a maker may narrow the time of day
        if any(math.hypot(cam[0] - u['cam'][0], cam[1] - u['cam'][1]) < min_gap and abs(cam[2] - u['cam'][2]) < 60
               for u in used):
            continue
        return dict(kind=kind, cam=[round(c, 1) for c in cam], target=[round(c, 1) for c in tgt], lens=round(lens),
                    preset=preset or rng.choices(['day', 'golden', 'dusk', 'night'], w)[0], desc=desc,
                    seed=f'{seed}#{attempt}')
    raise RuntimeError(f'no free place of kind {kind}')


def log_used(spots, reel, path=USED):
    try:
        used = json.load(open(path, encoding='utf-8'))
    except (OSError, ValueError):
        used = []
    keys = {u.get('key') for u in used}
    for s in spots:
        key = f'{s["kind"]}:{s["seed"].rsplit("#", 1)[0]}'
        if key not in keys:
            used.append(dict(reel=reel, key=key, kind=s['kind'], cam=s['cam'], target=s['target'], lens=s['lens'],
                             preset=s['preset'], desc=s['desc'], seed=s['seed']))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    json.dump(used, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


def fill_shots(path, reel):
    """Give every shot with "spot": {"kind": ...} its own new place (cam/target/lens/preset) and log the places."""
    data = json.load(open(path, encoding='utf-8'))
    used, out = load_used(), []
    for sh in data['shots']:
        sp = sh.get('spot')
        if not sp or 'cam' in sh:
            continue
        s = make_spot(sp['kind'], sp.get('seed', f'{reel}/{sh["id"]}'), sh.get('preset') or sp.get('preset'),
                      used + [dict(cam=o['cam']) for o in out])
        sh.update(cam=s['cam'], target=s['target'], lens=s['lens'], preset=s['preset'])
        sp.update(seed=s['seed'].rsplit('#', 1)[0], desc=s['desc'])
        out.append(s)
    json.dump(data, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    log_used(out, reel)
    return out


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--kinds', default='')
    ap.add_argument('--all', action='store_true')
    ap.add_argument('--seed', default='')
    ap.add_argument('--preset', default=None)
    ap.add_argument('--log', default='', help='reel id: remember the places in projects/metro-city/spots_used.json')
    ap.add_argument('--shots', default='', help='shots.json of a reel: fill shots that have "spot" (needs --log)')
    a = ap.parse_args()
    if a.shots:
        out = fill_shots(a.shots, a.log or os.path.basename(os.path.dirname(os.path.dirname(os.path.abspath(a.shots)))))
    else:
        kinds = KINDS if a.all else [k for k in a.kinds.split(',') if k]
        used = load_used()
        out = []
        for i, k in enumerate(kinds):
            s = make_spot(k, f'{a.seed}/{i}', a.preset, used + [dict(cam=o['cam']) for o in out])
            out.append(s)
        if a.log:
            log_used(out, a.log)
    print(json.dumps(out, ensure_ascii=False, indent=1))
