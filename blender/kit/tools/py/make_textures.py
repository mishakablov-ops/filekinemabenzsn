"""PIL textures: Europe paper map (political / Schengen), passport pages with stamps, passport cover."""
import json, os, math, random
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops
HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.abspath(os.path.join(HERE, '..', '..'))
D = os.path.join(PROJ, 'data')
TEX = os.path.join(PROJ, 'blender', 'tex'); os.makedirs(TEX, exist_ok=True)
FONTDIR = os.path.join(PROJ, '..', 'AIpollon-Reel-Studio', 'skills', 'reel-studio', 'engine', 'node_modules', '@fontsource')
def font(w=700, size=40, fam='inter-tight'):
    return ImageFont.truetype(os.path.join(FONTDIR, fam, 'files', f'{fam}-cyrillic-{w}-normal.woff'), size)
def font_lat(w=700, size=40, fam='inter-tight'):
    return ImageFont.truetype(os.path.join(FONTDIR, fam, 'files', f'{fam}-latin-{w}-normal.woff'), size)
SCHENGEN = set("Austria Belgium Bulgaria Croatia Czechia Denmark Estonia Finland France Germany Greece Hungary Iceland Italy Latvia Liechtenstein Lithuania Luxembourg Malta Netherlands Norway Poland Portugal Romania Slovakia Slovenia Spain Sweden Switzerland".split())

def paper(W, H, base=(226, 213, 190), seed=1):
    rnd = random.Random(seed)
    im = Image.new('RGB', (W, H), base)
    n = Image.effect_noise((W // 4, H // 4), 22).resize((W, H), Image.BICUBIC)
    n2 = Image.effect_noise((W, H), 10)
    tint = Image.merge('RGB', [n, n, n])
    im = ImageChops.add(im, ImageChops.subtract(tint, Image.new('RGB', (W, H), (128, 128, 128))), 1.0, -0)
    im = Image.blend(im, Image.merge('RGB', [n2, n2, n2]), 0.04)
    return im

def europe_maps():
    t = json.load(open(os.path.join(D, 'countries-50m.json')))
    sx, sy = t['transform']['scale']; tx, ty = t['transform']['translate']
    arcs = []
    for a in t['arcs']:
        x = y = 0; pts = []
        for dx, dy in a:
            x += dx; y += dy; pts.append((x * sx + tx, y * sy + ty))
        arcs.append(pts)
    geoms = t['objects']['countries']['geometries']
    lon0, lon1, lat0, lat1 = -25.0, 45.0, 33.0, 72.0
    k = math.cos(math.radians(52))
    W = 3000; H = int(W * (lat1 - lat0) / ((lon1 - lon0) * k))
    def xy(p): return ((p[0] - lon0) / (lon1 - lon0) * W, (lat1 - p[1]) / (lat1 - lat0) * H)
    def ring_pts(ring):
        pts = []
        for a in ring:
            ap = arcs[a] if a >= 0 else arcs[~a][::-1]
            pts.extend(ap if not pts else ap[1:])
        un = []
        for lo, la in pts:
            if un:
                while lo - un[-1][0] > 180: lo -= 360
                while lo - un[-1][0] < -180: lo += 360
            un.append((lo, la))
        if un and min(p[0] for p in un) < -180:
            un = [(lo + 360, la) for lo, la in un]
        return [xy(p) for p in un]
    pal = [(214, 178, 140), (190, 196, 160), (222, 196, 150), (184, 186, 182), (206, 170, 168), (226, 186, 150), (198, 190, 150)]
    from collections import defaultdict
    users = defaultdict(set)
    def rings(g):
        return [g['arcs']] if g['type'] == 'Polygon' else (g['arcs'] if g['type'] == 'MultiPolygon' else [])
    for gi, g in enumerate(geoms):
        for poly in rings(g):
            for ring in poly:
                for a in ring: users[a if a >= 0 else ~a].add(gi)
    adj = defaultdict(set)
    for u in users.values():
        for a in u:
            for b in u:
                if a != b: adj[a].add(b)
    col = {}
    for gi in sorted(range(len(geoms)), key=lambda g: -len(adj[g])):
        used = {col[n] for n in adj[gi] if n in col}
        col[gi] = next(c for c in range(len(pal)) if c not in used)
    for variant in ('political', 'schengen'):
        im = paper(W, H, (214, 205, 186), seed=3)  # sea = paper slightly cooler
        sea = Image.new('RGB', (W, H), (196, 192, 178))
        im = Image.blend(im, sea, 0.35)
        land = Image.new('RGB', (W, H)); lm = Image.new('L', (W, H), 0)
        dl, dm = ImageDraw.Draw(land), ImageDraw.Draw(lm)
        for gi, g in enumerate(geoms):
            name = g['properties']['name']
            c = pal[col[gi]]
            if variant == 'schengen' and name in SCHENGEN:
                c = (226, 150, 108)
            for poly in rings(g):
                for kk, ring in enumerate(poly):
                    pp = ring_pts(ring)
                    if len(pp) < 3: continue
                    if kk == 0:
                        dl.polygon(pp, fill=c); dm.polygon(pp, fill=255)
                    else:
                        dl.polygon(pp, fill=(0, 0, 0)); dm.polygon(pp, fill=0)
        pap = paper(W, H, (236, 226, 206), seed=5)
        land = ImageChops.multiply(land, pap)
        im.paste(land, (0, 0), lm)
        d = ImageDraw.Draw(im)
        # coast
        for i, u in users.items():
            pts = [xy(p) for p in arcs[i]]
            if any(abs(a[0] - b[0]) > W / 2 for a, b in zip(pts, pts[1:])): continue
            if len(u) == 1:
                d.line(pts, fill=(92, 70, 52), width=3)
        # borders (dash-dot) — schengen variant drops internal Schengen borders
        for i, u in users.items():
            if len(u) < 2: continue
            nm = {geoms[g]['properties']['name'] for g in u}
            internal = nm <= SCHENGEN
            if variant == 'schengen' and internal: continue
            pts = [xy(p) for p in arcs[i]]
            # dashed
            acc = 0; on = True; seg = []
            for a, b in zip(pts, pts[1:]):
                L = math.dist(a, b)
                seg.append(a)
                acc += L
                if acc > (16 if on else 7):
                    seg.append(b)
                    if on and len(seg) > 1: d.line(seg, fill=(120, 54, 38), width=4)
                    seg = []; acc = 0; on = not on
            if on and len(seg) > 1: d.line(seg + [pts[-1]], fill=(120, 54, 38), width=4)
        # graticule
        for lo in range(-20, 46, 10):
            x = xy((lo, 0))[0]; d.line([(x, 0), (x, H)], fill=(150, 140, 120), width=1)
        for la in range(35, 72, 5):
            y = xy((0, la))[1]; d.line([(0, y), (W, y)], fill=(150, 140, 120), width=1)
        im = im.filter(ImageFilter.GaussianBlur(0.6))
        im.save(os.path.join(TEX, f'europe_{variant}.jpg'), quality=92)
    print('maps', W, H)

def pages():
    W, H = 2200, 1560  # two pages side by side (each 1100 x 1560 ~ 88x125mm)
    rnd = random.Random(9)
    im = paper(W, H, (231, 224, 206), seed=11)
    d = ImageDraw.Draw(im)
    # guilloche background
    for k in range(0, 260):
        pts = []
        for x in range(0, W + 20, 20):
            y = 40 + k * 6 + 10 * math.sin(x / 70 + k * 0.4) + 6 * math.sin(x / 23 + k)
            pts.append((x, y))
        d.line(pts, fill=(196, 208, 190) if k % 2 else (214, 200, 186), width=1)
    d.line([(W // 2, 0), (W // 2, H)], fill=(170, 160, 140), width=3)
    inks = [(92, 52, 132), (170, 44, 40), (40, 70, 140), (44, 110, 80), (120, 40, 90)]
    fb = font_lat(800, 46); fs = font_lat(600, 30); fsm = font_lat(600, 24)
    def stamp(cx, cy, kind, ink, rot):
        S = 520
        st = Image.new('RGBA', (S, S), (0, 0, 0, 0))
        sd = ImageDraw.Draw(st)
        c = ink + (215,)
        if kind == 'rect':
            sd.rounded_rectangle([60, 120, 460, 400], radius=28, outline=c, width=9)
            sd.rounded_rectangle([78, 138, 442, 382], radius=20, outline=c, width=3)
            sd.text((260, 200), rnd.choice(['ENTRY', 'ARRIVAL', 'ADMITTED']), font=fb, fill=c, anchor='mm')
            sd.text((260, 270), f'{rnd.randint(1,28):02d}.{rnd.randint(1,12):02d}.{rnd.randint(14,25)}', font=fs, fill=c, anchor='mm')
            sd.text((260, 330), f'No {rnd.randint(100,999)}', font=fsm, fill=c, anchor='mm')
        elif kind == 'circle':
            sd.ellipse([70, 70, 450, 450], outline=c, width=9)
            sd.ellipse([105, 105, 415, 415], outline=c, width=3)
            sd.text((260, 230), rnd.choice(['EXIT', 'DEPARTED', 'TRANSIT']), font=fb, fill=c, anchor='mm')
            sd.text((260, 300), f'{rnd.randint(1,28):02d}.{rnd.randint(1,12):02d}.{rnd.randint(14,25)}', font=fs, fill=c, anchor='mm')
            for a in range(0, 360, 30):
                x = 260 + 170 * math.cos(math.radians(a)); y = 260 + 170 * math.sin(math.radians(a))
                sd.ellipse([x - 5, y - 5, x + 5, y + 5], fill=c)
        else:
            sd.polygon([(260, 60), (460, 200), (420, 440), (100, 440), (60, 200)], outline=c, width=8)
            sd.text((260, 250), 'VISA', font=fb, fill=c, anchor='mm')
            sd.text((260, 320), f'{rnd.randint(1,28):02d}.{rnd.randint(1,12):02d}.{rnd.randint(14,25)}', font=fs, fill=c, anchor='mm')
        # worn ink
        n = Image.effect_noise((S, S), 90).point(lambda v: 255 if v > 95 else 0)
        a = ImageChops.multiply(st.split()[3], n)
        st.putalpha(a)
        st = st.rotate(rot, resample=Image.BICUBIC)
        im.paste(st, (int(cx - S / 2), int(cy - S / 2)), st)
    spots = [(330, 380), (800, 520), (420, 1000), (860, 1180), (1420, 340), (1850, 560), (1500, 980), (1880, 1220), (620, 1360)]
    for (x, y) in spots:
        stamp(x + rnd.randint(-40, 40), y + rnd.randint(-40, 40), rnd.choice(['rect', 'circle', 'rect', 'tri']),
              rnd.choice(inks), rnd.uniform(-28, 28))
    d.text((W - 90, H - 60), '07', font=fs, fill=(120, 110, 90), anchor='mm')
    d.text((90, H - 60), '06', font=fs, fill=(120, 110, 90), anchor='mm')
    im.save(os.path.join(TEX, 'passport_pages.jpg'), quality=92)

def cover():
    W, H = 1100, 1560
    im = Image.new('RGB', (W, H), (92, 28, 30))
    n = Image.effect_noise((W, H), 30)
    im = Image.blend(im, Image.merge('RGB', [n, n, n]), 0.06)
    gold = (214, 172, 98)
    d = ImageDraw.Draw(im)
    d.text((W / 2, 260), 'ПАСПОРТ', font=font(800, 96), fill=gold, anchor='mm')
    cx, cy, r = W / 2, 780, 230
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=gold, width=12)
    for k in (-0.62, -0.25, 0.25, 0.62):
        rr = r * math.sqrt(1 - k * k)
        d.line([(cx - rr, cy + k * r), (cx + rr, cy + k * r)], fill=gold, width=7)
    for e in (0.35, 0.7):
        d.ellipse([cx - r * e, cy - r, cx + r * e, cy + r], outline=gold, width=7)
    d.line([(cx, cy - r), (cx, cy + r)], fill=gold, width=7)
    d.text((W / 2, 1310), 'PASSPORT', font=font_lat(700, 70), fill=gold, anchor='mm')
    im.save(os.path.join(TEX, 'passport_cover.jpg'), quality=92)
    # gold mask for metallic
    m = Image.new('L', (W, H), 0); md = ImageDraw.Draw(m)
    md.bitmap((0, 0), Image.new('1', (1, 1)))
    gm = im.convert('RGB').split()
    mask = Image.eval(ImageChops.subtract(gm[1], Image.new('L', (W, H), 90)), lambda v: 255 if v > 40 else 0)
    mask.save(os.path.join(TEX, 'passport_cover_gold.png'))

europe_maps(); pages(); cover()
print('ok', os.listdir(TEX))
