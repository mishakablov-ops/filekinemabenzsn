"""TopoJSON (world-atlas) -> border polylines + equirectangular land textures for the Blender globe."""
import json, sys, os, random
from collections import defaultdict
from PIL import Image, ImageDraw

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data')
D = os.path.abspath(D)

def load(name):
    t = json.load(open(os.path.join(D, name)))
    sx, sy = t['transform']['scale']; tx, ty = t['transform']['translate']
    arcs = []
    for a in t['arcs']:
        x = y = 0; pts = []
        for dx, dy in a:
            x += dx; y += dy
            pts.append((round(x * sx + tx, 4), round(y * sy + ty, 4)))
        arcs.append(pts)
    return t, arcs

def arc_pts(arcs, i):
    return arcs[i] if i >= 0 else arcs[~i][::-1]

def rings_of(geom):
    if geom['type'] == 'Polygon':
        return [geom['arcs']]
    if geom['type'] == 'MultiPolygon':
        return geom['arcs']
    return []

def process(name, tag, W, H, textures):
    t, arcs = load(name)
    geoms = t['objects']['countries']['geometries']
    users = defaultdict(set)
    for gi, g in enumerate(geoms):
        for poly in rings_of(g):
            for ring in poly:
                for a in ring:
                    users[a if a >= 0 else ~a].add(gi)
    borders = [arcs[i] for i, u in users.items() if len(u) >= 2]
    coast = [arcs[i] for i, u in users.items() if len(u) == 1]
    json.dump(borders, open(os.path.join(D, f'borders_{tag}.json'), 'w'), separators=(',', ':'))
    json.dump(coast, open(os.path.join(D, f'coast_{tag}.json'), 'w'), separators=(',', ':'))
    print(tag, 'border arcs', len(borders), 'pts', sum(map(len, borders)), 'coast arcs', len(coast))
    if not textures:
        return
    # adjacency + greedy colouring (neighbours differ)
    adj = defaultdict(set)
    for i, u in users.items():
        u = list(u)
        for a in u:
            for b in u:
                if a != b: adj[a].add(b)
    pal = ['#8E5D40', '#6E7A5B', '#A98A5C', '#5D6A72', '#7B5465', '#9C6E4E', '#6A6248']
    order = sorted(range(len(geoms)), key=lambda g: -len(adj[g]))
    col = {}
    rnd = random.Random(7)
    for g in order:
        used = {col[n] for n in adj[g] if n in col}
        free = [c for c in range(len(pal)) if c not in used]
        col[g] = rnd.choice(free[:3]) if free else 0
    pol = Image.new('RGB', (W, H), (0, 0, 0))
    mask = Image.new('L', (W, H), 0)
    dp, dm = ImageDraw.Draw(pol), ImageDraw.Draw(mask)
    def xy(p):
        return ((p[0] + 180) / 360 * W, (90 - p[1]) / 180 * H)
    for gi, g in enumerate(geoms):
        c = pal[col[gi]]
        for poly in rings_of(g):
            for k, ring in enumerate(poly):
                pts = []
                for a in ring:
                    ap = arc_pts(arcs, a)
                    pts.extend(ap if not pts else ap[1:])
                un = []
                for lo, la in pts:
                    if un:
                        while lo - un[-1][0] > 180: lo -= 360
                        while lo - un[-1][0] < -180: lo += 360
                    un.append((lo, la))
                if len(un) < 3: continue
                for off in (-360, 0, 360):
                    pp = [xy((lo + off, la)) for lo, la in un]
                    if k == 0:
                        dp.polygon(pp, fill=c); dm.polygon(pp, fill=255)
                    else:  # hole
                        dp.polygon(pp, fill=(0, 0, 0)); dm.polygon(pp, fill=0)
    pol.save(os.path.join(D, 'land_political.png'))
    mask.save(os.path.join(D, 'land_mask.png'))
    print('textures', W, H)

process('countries-110m.json', '110m', 0, 0, False)
process('countries-50m.json', '50m', 8192, 4096, True)
