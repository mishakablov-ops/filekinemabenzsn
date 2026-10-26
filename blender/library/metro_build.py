"""Geometry of the permanent city «Метрополис» (style «блендер», 26.10.2026): turns the plan of metro_plan.py into
Blender meshes. Every building is extruded from its lot (tiers with setbacks, cornices, roof gear, crowns, spires);
facade windows come from the material (metro_mats.facade) through UV u = metres along the footprint (whole window
bays per wall) and v = height, plus per-face attributes. Buildings are merged into 500 m tiles so Eevee can cull them.

    import metro_build as MB
    stats = MB.build_city(focus=(x, y), detail_r=0)     # everything; detail_r > 0 adds street furniture near focus

Pure geometry and materials only: time of day, camera and lights are set by metro.py.
"""
import math
import random
import bpy
import lib
import metro_plan as MP
import metro_mats as MM

TILE = 500.0
FAR = 9000.0                 # waterfront, highways and the river run this far east and west
_PLAN = None


def get_plan():
    global _PLAN
    if _PLAN is None:
        _PLAN = MP.build_plan()
    return _PLAN


# ----------------------------------------------------------------------------- polygons
def ccw(poly):
    p = [(float(q[0]), float(q[1])) for q in poly]
    return p if MP.area(p) > 0 else p[::-1]


def scale_about(poly, s):
    cx, cy = MP.centroid(poly)
    return [(cx + (x - cx) * s, cy + (y - cy) * s) for x, y in poly]


def inset(poly, d):
    """Offset a convex CCW polygon inwards by d metres (negative = outwards)."""
    if abs(d) < 1e-6:
        return poly
    n = len(poly)
    lines = []
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy)
        if L < 1e-6:
            continue
        lines.append(((a[0] - dy / L * d, a[1] + dx / L * d), (dx / L, dy / L)))
    out = []
    for i in range(len(lines)):
        (p1, d1), (p2, d2) = lines[i - 1], lines[i]
        den = d1[0] * d2[1] - d1[1] * d2[0]
        if abs(den) < 1e-9:
            out.append(p2)
            continue
        t = ((p2[0] - p1[0]) * d2[1] - (p2[1] - p1[1]) * d2[0]) / den
        out.append((p1[0] + d1[0] * t, p1[1] + d1[1] * t))
    ok = len(out) >= 3 and MP.area(out) > 1.0
    if ok:
        for i in range(len(out)):      # an edge that flipped means the inset was too deep
            a, b = out[i], out[(i + 1) % len(out)]
            if (b[0] - a[0]) * lines[i][1][0] + (b[1] - a[1]) * lines[i][1][1] <= 0:
                ok = False
                break
    if not ok:
        w = max(MP.min_width(poly), 1e-3)
        return scale_about(poly, max(0.15, 1 - 2 * d / w))
    return out


def chamfer(poly, c):
    out = []
    n = len(poly)
    for i in range(n):
        p0, p, p1 = poly[i - 1], poly[i], poly[(i + 1) % n]
        la, lb = math.hypot(p0[0] - p[0], p0[1] - p[1]), math.hypot(p1[0] - p[0], p1[1] - p[1])
        cc = min(c, la * 0.3, lb * 0.3)
        out.append((p[0] + (p0[0] - p[0]) / la * cc, p[1] + (p0[1] - p[1]) / la * cc))
        out.append((p[0] + (p1[0] - p[0]) / lb * cc, p[1] + (p1[1] - p[1]) / lb * cc))
    return out


def inside(poly, x, y, margin=0.0):
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        L = math.hypot(b[0] - a[0], b[1] - a[1]) or 1.0
        if ((b[0] - a[0]) * (y - a[1]) - (b[1] - a[1]) * (x - a[0])) / L < margin:
            return False
    return True


def rand_in(rng, poly, margin):
    xs, ys = [p[0] for p in poly], [p[1] for p in poly]
    for _ in range(12):
        x, y = rng.uniform(min(xs), max(xs)), rng.uniform(min(ys), max(ys))
        if inside(poly, x, y, margin):
            return x, y
    return MP.centroid(poly)


# ----------------------------------------------------------------------------- mesh accumulator
class Acc:
    """Collects faces (each with its own vertices, so shading is flat), UVs, material slots and per-face attributes,
    then writes one mesh with foreach_set. attrs: name -> default (float, or 4-tuple for a colour)."""

    def __init__(self, attrs=None):
        self.V, self.F, self.UV, self.MI = [], [], [], []
        self.attrs = attrs or {}
        self.AV = {k: [] for k in self.attrs}
        self.mats, self.mi = [], {}

    def face(self, pts, uvs, mat, at=None):
        base = len(self.V)
        self.V.extend(pts)
        self.F.append(tuple(range(base, base + len(pts))))
        self.UV.extend(uvs if uvs is not None else [(0.0, 0.0)] * len(pts))
        k = self.mi.get(mat.name)
        if k is None:
            k = self.mi[mat.name] = len(self.mats)
            self.mats.append(mat)
        self.MI.append(k)
        for a in self.attrs:
            self.AV[a].append(at.get(a, self.attrs[a]) if at else self.attrs[a])

    def __len__(self):
        return len(self.F)

    # --- primitives (UV zero unless given: no windows on gear)
    def quad(self, a, b, c, d, mat, at=None, uvs=None):
        self.face([a, b, c, d], uvs, mat, at)

    def box(self, x, y, z, sx, sy, sz, mat, at=None, rot=0.0, bottom=False):
        c, s = math.cos(rot), math.sin(rot)
        hx, hy = sx / 2, sy / 2
        pts = [(x + c * px - s * py, y + s * px + c * py) for px, py in ((-hx, -hy), (hx, -hy), (hx, hy), (-hx, hy))]
        self.prism(pts, z, z + sz, mat, at, cap=True, bottom=bottom)

    def prism(self, poly, z0, z1, mat, at=None, cap=True, bottom=False, top_mat=None, uv_walls=False, bay=3.0):
        n = len(poly)
        u = 0
        for i in range(n):
            a, b = poly[i], poly[(i + 1) % n]
            uvs = None
            if uv_walls:
                L = math.hypot(b[0] - a[0], b[1] - a[1])
                k = max(1, round(L / bay))
                uvs = [(u * bay, z0), ((u + k) * bay, z0), ((u + k) * bay, z1), (u * bay, z1)]
                u += k
            self.face([(a[0], a[1], z0), (b[0], b[1], z0), (b[0], b[1], z1), (a[0], a[1], z1)], uvs, mat, at)
        if cap:
            self.face([(x, y, z1) for x, y in poly], [(x, y) for x, y in poly], top_mat or mat, at)
        if bottom:
            self.face([(x, y, z0) for x, y in poly[::-1]], None, mat, at)

    def cyl(self, x, y, z, r, h, mat, at=None, seg=8, r_top=None, cap=True):
        rt = r if r_top is None else r_top
        ring = [(math.cos(2 * math.pi * i / seg), math.sin(2 * math.pi * i / seg)) for i in range(seg)]
        for i in range(seg):
            a, b = ring[i], ring[(i + 1) % seg]
            self.face([(x + a[0] * r, y + a[1] * r, z), (x + b[0] * r, y + b[1] * r, z),
                       (x + b[0] * rt, y + b[1] * rt, z + h), (x + a[0] * rt, y + a[1] * rt, z + h)], None, mat, at)
        if cap and rt > 0:
            self.face([(x + c * rt, y + s * rt, z + h) for c, s in ring], None, mat, at)

    def pyramid(self, poly, z, h, mat, at=None, apex=None):
        cx, cy = apex or MP.centroid(poly)
        n = len(poly)
        for i in range(n):
            a, b = poly[i], poly[(i + 1) % n]
            self.face([(a[0], a[1], z), (b[0], b[1], z), (cx, cy, z + h)], None, mat, at)

    def strip(self, a, b, w, z, mat, at=None, u0=0.0):
        """Flat quad along a->b, w wide, UV u = metres along (from u0), v = metres across (signed, left +)."""
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy)
        if L < 1e-6:
            return
        nx, ny = -dy / L * w / 2, dx / L * w / 2
        self.face([(a[0] - nx, a[1] - ny, z), (b[0] - nx, b[1] - ny, z), (b[0] + nx, b[1] + ny, z), (a[0] + nx, a[1] + ny, z)],
                  [(u0, -w / 2), (u0 + L, -w / 2), (u0 + L, w / 2), (u0, w / 2)], mat, at)

    def tube(self, pts, r, mat, at=None):
        """Square-section tube along a 3D polyline (cables)."""
        for p, q in zip(pts, pts[1:]):
            dx, dy, dz = q[0] - p[0], q[1] - p[1], q[2] - p[2]
            L = math.sqrt(dx * dx + dy * dy + dz * dz) or 1.0
            # side vector: horizontal, perpendicular to the segment
            sx, sy = -dy, dx
            sl = math.hypot(sx, sy) or 1.0
            sx, sy = sx / sl * r, sy / sl * r
            for (ax, ay, az), (bx, by, bz) in (((sx, sy, 0), (0, 0, r)), ((0, 0, r), (-sx, -sy, 0)),
                                               ((-sx, -sy, 0), (0, 0, -r)), ((0, 0, -r), (sx, sy, 0))):
                self.face([(p[0] + ax, p[1] + ay, p[2] + az), (q[0] + ax, q[1] + ay, q[2] + az),
                           (q[0] + bx, q[1] + by, q[2] + bz), (p[0] + bx, p[1] + by, p[2] + bz)], None, mat, at)

    def build(self, name, coll=None):
        if not self.F:
            return None
        me = bpy.data.meshes.new(name)
        me.from_pydata(self.V, [], self.F)
        uvl = me.uv_layers.new(name='UVMap')
        uvl.data.foreach_set('uv', [c for uv in self.UV for c in uv])
        sizes = [len(f) for f in self.F]
        for a, vals in self.AV.items():
            if isinstance(self.attrs[a], tuple):
                at = me.attributes.new(a, 'FLOAT_COLOR', 'CORNER')
                at.data.foreach_set('color', [c for v, n in zip(vals, sizes) for _ in range(n) for c in v])
            else:
                at = me.attributes.new(a, 'FLOAT', 'CORNER')
                at.data.foreach_set('value', [v for v, n in zip(vals, sizes) for _ in range(n)])
        for m in self.mats:
            me.materials.append(m)
        me.polygons.foreach_set('material_index', self.MI)
        try:
            me.polygons.foreach_set('use_smooth', [False] * len(self.F))
        except Exception:
            pass
        me.update()
        ob = bpy.data.objects.new(name, me)
        (coll or bpy.context.scene.collection).objects.link(ob)
        return ob


BLD_ATTRS = dict(bcol=(0.5, 0.5, 0.5, 1.0), brnd=0.0, fh=3.5, bay=3.0, gf=0.0, crown=0.0)


# ----------------------------------------------------------------------------- materials
def mats():
    M = {k: MM.facade(k) for k in MM.KINDS}
    M.update(
        roof=MM.roof_mat(),
        cornice=MM.flat_mat('MF_cornice', '#C4BBA9', 0.85),
        cornice_dark=MM.flat_mat('MF_cornice_dark', '#3E3A36', 0.6, 0.3),
        wood=MM.flat_mat('MF_wood', '#5A4231', 0.9, var=0.5, var_scale=1.5),
        metal=MM.flat_mat('MF_metal', '#7A7C7E', 0.45, 0.6),
        dark=MM.flat_mat('MF_darkmetal', '#2B2D30', 0.4, 0.7),
        helipad=MM.flat_mat('MF_helipad', '#3C3F42', 0.7),
        aviation=MM.glow_mat('MF_aviation', '#FF1A0A', 60.0, 'Night', blink=0.6),
        aviation_still=MM.glow_mat('MF_aviation_still', '#FF2010', 45.0, 'Night'),
        road=MM.road_mat(),
        marking=MM.marking_mat(),
        traffic=MM.traffic_mat(),
        sidewalk=MM.sidewalk_mat(),
        promenade=MM.sidewalk_mat('MF_promenade', '#8E8378', 0.9),
        plaza=MM.sidewalk_mat('MF_plaza', '#B3ADA4', 3.0),
        ground=MM.flat_mat('MF_ground', '#36383B', 0.9, var=0.4, var_scale=0.01),
        stone=MM.flat_mat('MF_stone', '#6F6A62', 0.85, var=0.5, var_scale=0.3),
        concrete=MM.flat_mat('MF_concrete', '#9A968E', 0.8),
        steel=MM.flat_mat('MF_steel', '#5B6670', 0.5, 0.5),
        water=MM.water_mat(),
        grass=MM.grass_mat(),
        tree=MM.tree_mat(),
        lamp=MM.glow_mat('MF_lamp', '#FFC27A', 22.0, 'Street'),
        lamp_led=MM.glow_mat('MF_lamp_led', '#FFF0DA', 26.0, 'Street'),
        cable_light=MM.glow_mat('MF_cable_light', '#FFF4E0', 40.0, 'Night'),
    )
    return M


# ----------------------------------------------------------------------------- buildings
def walls(A, bot, top, z0, z1, mat, at):
    """Facade walls of one tier: UV u = whole window bays along the perimeter, v = height in metres."""
    bay = at['bay']
    n = len(bot)
    u = 0
    for i in range(n):
        a, b = bot[i], bot[(i + 1) % n]
        ta, tb = top[i], top[(i + 1) % n]
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        if L < 0.05:
            continue
        k = max(1, round(L / bay))
        A.face([(a[0], a[1], z0), (b[0], b[1], z0), (tb[0], tb[1], z1), (ta[0], ta[1], z1)],
               [(u * bay, z0), ((u + k) * bay, z0), ((u + k) * bay, z1), (u * bay, z1)], mat, at)
        u += k


def cap(A, poly, z, mat, at=None):
    A.face([(x, y, z) for x, y in poly], [(x, y) for x, y in poly], mat, at)


def gf_of(b):
    """Height of the shop / lobby floor (0 = none); the facade shader draws shop windows below it."""
    if b['type'] == 'shop':
        return 4.5
    if b.get('retail') and b['facade'] in ('punched', 'brick', 'ribbon') and b['h'] >= 9:
        return 4.5
    if b.get('retail') and b['facade'].startswith('curtain') and b['h'] >= 30:
        return 6.0
    return 0.0


def building(A, R, b, M):
    poly = ccw(b['poly'])
    h, kind, typ = b['h'], b['facade'], b['type']
    rng = random.Random(b['seed'])
    col = lib.C(b['color'])
    j = rng.uniform(0.88, 1.1)
    col = (col[0] * j, col[1] * j, col[2] * j, 1.0)
    gf = gf_of(b)
    at = dict(bcol=col, brnd=(b['seed'] % 997) / 997.0, fh=b['floor_h'], bay=b['bay'], gf=gf, crown=0.0)
    ra = dict(brnd=at['brnd'])
    fm = M[kind]
    roof = b.get('roof', {})
    top, ztop = poly, h
    if b.get('tubes'):                                   # bundled tubes (the black tower)
        x0, y0 = min(p[0] for p in poly), min(p[1] for p in poly)
        t = (max(p[0] for p in poly) - x0) / 3.0
        for i, jj, f in b['tubes']:
            p = MP.rect(x0 + i * t, y0 + jj * t, x0 + (i + 1) * t, y0 + (jj + 1) * t)
            walls(A, p, p, 0.0, h * f, fm, at)
            cap(A, p, h * f, M['roof'])
            if f >= 0.99:
                top = p
        A_top = top
    else:
        tiers = b['tiers'] or [[0.0, 0.0, h]]
        cham = typ in ('glass_tower', 'dark_tower') and b['seed'] % 4 == 0 and MP.min_width(poly) > 24
        cornice = roof.get('cornice')
        for idx, (ins, z0, z1) in enumerate(tiers):
            p = inset(poly, ins)
            if cham:
                p = chamfer(p, min(6.0, MP.min_width(p) * 0.15))
            tp = p
            if b.get('shape') == 'taper' and idx == len(tiers) - 1:
                tp = scale_about(p, 0.55)
            lit_top = typ == 'deco_tower' and idx >= len(tiers) - 2 and h > 100
            walls(A, p, tp, z0, z1, fm, dict(at, crown=1.0) if lit_top else at)
            last = idx == len(tiers) - 1
            if last and cornice:
                cp = inset(tp, -0.45)
                cm = M['cornice'] if kind != 'brick' or rng.random() < 0.5 else M['cornice_dark']
                A.prism(cp, z1 - 0.7, z1 + 0.35, cm, None, cap=False)
                cap(A, cp, z1 + 0.35, M['roof'])
            else:
                cap(A, tp, z1, M['roof'])
            # setback terraces of towers get a thin parapet line
            if not last and ins == 0 and typ in ('glass_tower', 'dark_tower', 'office'):
                A.prism(inset(p, -0.25), z1 - 0.4, z1 + 0.9, M['metal'], None, cap=False)
            top, ztop = tp, z1 + (0.35 if (last and cornice) else 0.0)
        A_top = top
    w = MP.min_width(A_top)
    cx, cy = MP.centroid(A_top)
    crown_at = dict(at, crown=1.0)
    # --- roof gear
    if roof.get('hvac'):
        for _ in range(roof['hvac']):
            x, y = rand_in(rng, A_top, 3.0)
            sx, sy = rng.uniform(2.0, min(6.0, w * 0.3)), rng.uniform(2.0, min(4.5, w * 0.25))
            R.box(x, y, ztop, sx, sy, rng.uniform(1.4, 2.6), M['metal'], ra, rot=0.0)
    if roof.get('tank'):
        x, y = rand_in(rng, A_top, 3.2)
        for lx, ly in ((-1.3, -1.3), (1.3, -1.3), (1.3, 1.3), (-1.3, 1.3)):
            R.box(x + lx, y + ly, ztop, 0.22, 0.22, 2.3, M['dark'], ra)
        R.cyl(x, y, ztop + 2.3, 2.1, 3.4, M['wood'], ra, seg=10, cap=False)
        R.cyl(x, y, ztop + 5.7, 2.2, 1.1, M['dark'], ra, seg=10, r_top=0.15)
    if roof.get('helipad') and w > 26:
        R.cyl(cx, cy, ztop, min(w * 0.36, 13.0), 0.6, M['helipad'], ra, seg=16)
    apex = []
    crown = roof.get('crown')
    if crown == 'spire':
        sh = roof.get('spire') or h * 0.12
        A.pyramid(inset(A_top, w * 0.3), ztop, sh * 0.35, M[kind], crown_at)
        A.cyl(cx, cy, ztop + sh * 0.3, max(w * 0.06, 1.0), sh * 0.7, M['metal'], crown_at, seg=8, r_top=0.12, cap=False)
        apex.append((cx, cy, ztop + sh))
    elif crown == 'pyramid':
        ph = w * 0.45
        A.pyramid(inset(A_top, 1.0), ztop, ph, M[kind], crown_at)
        apex.append((cx, cy, ztop + ph))
    elif crown in ('lantern', 'arch'):
        lp = inset(A_top, w * 0.22)
        lh = b['floor_h'] * (3 if crown == 'arch' else 2)
        walls(A, lp, lp, ztop, ztop + lh, fm, crown_at)
        if crown == 'arch':
            lp2 = inset(lp, w * 0.12)
            walls(A, lp2, lp2, ztop + lh, ztop + lh * 1.7, fm, crown_at)
            A.pyramid(lp2, ztop + lh * 1.7, w * 0.3, M[kind], crown_at)
            sh = w * 0.3 + lh * 1.7
        else:
            A.pyramid(lp, ztop + lh, w * 0.25, M[kind], crown_at)
            sh = w * 0.25 + lh
        apex.append((cx, cy, ztop + sh))
    elif roof.get('spire'):                                # the needle
        sh = roof['spire']
        A.cyl(cx, cy, ztop, max(w * 0.12, 1.5), sh, M['metal'], crown_at, seg=8, r_top=0.15)
        apex.append((cx, cy, ztop + sh))
    if roof.get('antennas'):
        for k in range(roof['antennas']):
            x, y = rand_in(rng, A_top, w * 0.25) if k else (cx, cy)
            ah = rng.uniform(18, 50) if typ != 'black_tubes' else 75.0 - 10 * k
            R.cyl(x, y, ztop, 0.7, ah, M['dark'], ra, seg=6, r_top=0.12)
            apex.append((x, y, ztop + ah))
    if roof.get('aviation'):
        for x, y in inset(A_top, 1.0)[::max(1, len(A_top) // 4)]:
            R.box(x, y, ztop, 1.6, 1.6, 0.9, M['aviation_still'], ra)
        for x, y, z in apex:
            R.box(x, y, z - 0.6, 2.0, 2.0, 1.2, M['aviation'], ra)


def build_buildings(plan, M, coll, skip=None):
    tiles = {}
    for b in plan['buildings']:
        if skip and b['id'] in skip:
            continue
        cx, cy = MP.centroid(b['poly'])
        tiles.setdefault((int(math.floor(cx / TILE)), int(math.floor(cy / TILE))), []).append(b)
    n = 0
    for (i, j), bs in sorted(tiles.items()):
        A, R = Acc(BLD_ATTRS), Acc(dict(brnd=0.0))
        for b in bs:
            building(A, R, b, M)
        A.build(f'MetroBld_{i}_{j}', coll)
        R.build(f'MetroGear_{i}_{j}', coll)
        n += len(A) + len(R)
    return n


# ----------------------------------------------------------------------------- streets
ROAD_Z = dict(street=0.02, avenue=0.05, diagonal=0.08, highway=0.06)


def road_gaps(r, roads):
    """Intervals (in metres along r) where r crosses another road: no lane lines or kerb lamps there."""
    ax, ay = r['a']
    bx, by = r['b']
    L = math.hypot(bx - ax, by - ay)
    gaps = []
    vert = abs(bx - ax) < 1e-6
    horiz = abs(by - ay) < 1e-6
    for o in roads:
        if o is r or o['kind'] == 'diagonal':
            continue
        oax, oay = o['a']
        obx, oby = o['b']
        half = o['road'] / 2 + o['walk'] + 1.0
        if vert and abs(oby - oay) < 1e-6 and min(oax, obx) - 5 <= ax <= max(oax, obx) + 5:
            c = (oay - ay) * (1 if by > ay else -1)
            gaps.append((c - half, c + half))
        elif horiz and abs(obx - oax) < 1e-6 and min(oay, oby) - 5 <= ay <= max(oay, oby) + 5:
            c = (oax - ax) * (1 if bx > ax else -1)
            gaps.append((c - half, c + half))
    gaps = sorted(g for g in gaps if g[1] > 0 and g[0] < L)
    return L, gaps


def spans(L, gaps):
    out, s = [], 0.0
    for g0, g1 in gaps:
        if g0 > s:
            out.append((s, g0))
        s = max(s, g1)
    if s < L:
        out.append((s, L))
    return out


def far_roads(plan):
    """The plan's roads, with the two waterfront highways stretched to the horizon."""
    out = []
    for r in plan['roads']:
        if r['kind'] == 'highway':
            r = dict(r, a=[-FAR, r['a'][1]], b=[FAR, r['b'][1]])
        out.append(r)
    return out


def build_streets(plan, M, coll, roads):
    S = Acc(dict(hw=5.0, led=0.0))
    K = Acc(dict(dash=0.0))
    T = Acc(dict(dir=1.0, lane=0.0, tx=1.0, ty=0.0))
    L_ = Acc(dict(brnd=0.0))
    lane_id = 0
    lamps = 0
    for r in roads:
        a, b = r['a'], r['b']
        w = r['road']
        z = ROAD_Z.get(r['kind'], 0.03)
        led = 1.0 if r['kind'] in ('highway', 'avenue', 'diagonal') else 0.0
        S.strip(a, b, w, z, M['road'], dict(hw=w / 2, led=led))
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy)
        ux, uy = dx / L, dy / L
        nx, ny = -uy, ux
        L, gaps = road_gaps(r, roads)
        sp = spans(L, gaps)
        n = r['lanes']
        if r['kind'] == 'highway':                     # median in the middle, lanes on both sides
            half = n // 2
            lw = (w / 2 - 1.0) / half
            centres = [sd * (1.0 + (k + 0.5) * lw) for sd in (-1, 1) for k in range(half)]
            offs = [(sd * (1.0 + k * lw), 1.0) for sd in (-1, 1) for k in range(1, half)] + [(-1.2, 0.0), (1.2, 0.0)]
        else:
            lw = w / n
            centres = [-w / 2 + (k + 0.5) * lw for k in range(n)]
            offs = [(-w / 2 + k * lw, 0.0 if k == n // 2 else 1.0) for k in range(1, n)]
        offs += [(-w / 2 + 0.5, 0.0), (w / 2 - 0.5, 0.0)]
        for s0, s1 in sp:
            for o, dash in offs:
                pa = (a[0] + ux * s0 + nx * o, a[1] + uy * s0 + ny * o)
                pb = (a[0] + ux * s1 + nx * o, a[1] + uy * s1 + ny * o)
                K.strip(pa, pb, 0.16, z + 0.012, M['marking'], dict(dash=dash), u0=s0)
        # traffic: one strip per lane; right-hand traffic: lanes right of the centre drive along a->b
        for o in centres:
            dr = 1.0 if o < 0 else -1.0
            pa = (a[0] + nx * o, a[1] + ny * o)
            pb = (b[0] + nx * o, b[1] + ny * o)
            T.strip(pa, pb, 2.0, z + 0.022, M['traffic'], dict(dir=dr, lane=float(lane_id % 97), tx=ux, ty=uy))
            lane_id += 1
        # kerb lamps where the road shader paints the pools (every 30 m, sides staggered)
        if r['kind'] in ('avenue', 'street', 'diagonal'):
            for side, off in ((-1, 0.0), (1, 15.0)):
                u = off
                while u < L:
                    if any(s0 + 3 < u < s1 - 3 for s0, s1 in sp):
                        px = a[0] + ux * u + nx * side * (w / 2 + 0.7)
                        py = a[1] + uy * u + ny * side * (w / 2 + 0.7)
                        hx = a[0] + ux * u + nx * side * (w / 2 - 1.2)
                        hy = a[1] + uy * u + ny * side * (w / 2 - 1.2)
                        lamp(L_, M, px, py, hx, hy, 8.0, M['lamp_led'] if led else M['lamp'])
                        lamps += 1
                    u += 30.0
        elif r['kind'] == 'highway':                   # tall double lamps on the median
            u = 0.0
            while u < L:
                px, py = a[0] + ux * u, a[1] + uy * u
                L_.box(px, py, 0.0, 0.35, 0.35, 12.0, M['dark'])
                for side in (-1, 1):
                    hx, hy = px + nx * side * 3.0, py + ny * side * 3.0
                    L_.box((px + hx) / 2, (py + hy) / 2, 11.8, 3.0, 0.15, 0.15, M['dark'], rot=math.atan2(hy - py, hx - px))
                    L_.box(hx, hy, 11.55, 0.9, 0.9, 0.3, M['lamp_led'])
                u += 40.0
            # concrete median barrier
            S.prism([(a[0] - nx * 0.3, a[1] - ny * 0.3), (b[0] - nx * 0.3, b[1] - ny * 0.3),
                     (b[0] + nx * 0.3, b[1] + ny * 0.3), (a[0] + nx * 0.3, a[1] + ny * 0.3)], z, z + 0.9, M['concrete'])
    S.build('MetroRoads', coll)
    K.build('MetroMarkings', coll)
    T.build('MetroTraffic', coll)
    L_.build('MetroLamps', coll)
    return lamps


def lamp(L_, M, px, py, hx, hy, h, head):
    L_.box(px, py, 0.15, 0.18, 0.18, h, M['dark'])
    L_.box((px + hx) / 2, (py + hy) / 2, h - 0.1, math.hypot(hx - px, hy - py), 0.12, 0.12, M['dark'], rot=math.atan2(hy - py, hx - px))
    L_.box(hx, hy, h - 0.35, 0.7, 0.7, 0.25, head)


def block_platforms(plan, M, coll):
    """Raised sidewalks (kerb 15 cm) around every block, cut by the diagonal avenue."""
    P = Acc()
    (la, lb), (ra, rb) = diag_edges(9.0)
    for blk in plan['blocks']:
        xs, ys = [p[0] for p in blk['poly']], [p[1] for p in blk['poly']]
        x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
        boro = y1 < MP.RIVER_S
        aw = (MP.AVE_ROW - MP.AVE_ROAD) / 2
        sw = (MP.ST_ROW - MP.ST_ROAD) / 2
        y0e = 40.0 if abs(y0 - MP.CITY_Y0) < 1 else y0 - sw
        y1e = y1 + sw
        if boro and y1 > MP.RIVER_S - 60:
            y1e = MP.RIVER_S - 38.0
        poly = MP.rect(x0 - aw, y0e, x1 + aw, y1e)
        pieces = [poly]
        if not boro:
            s = [MP.diag_side(p) for p in poly]
            if not (all(v > 0 for v in s) or all(v < 0 for v in s)) and MP.DIAG_A[1] - 60 < (y0 + y1) / 2 < MP.DIAG_B[1] + 60:
                pieces = [MP.clip(poly, la, lb, True), MP.clip(poly, ra, rb, False)]
        for pc in pieces:
            if len(pc) >= 3 and MP.area(pc) > 4:
                P.prism(ccw(pc), 0.0, 0.15, M['sidewalk'])
    # park, plaza
    for pk in plan['parks']:
        poly = ccw(pk['poly'])
        P.prism(poly, 0.0, 0.18, M['concrete'] if pk.get('kind') == 'strip' else M['sidewalk'], cap=False)
        cap(P, [(x, y) for x, y in poly], 0.18, M['grass'])
    for pz in plan['plazas']:
        c, r = pz['c'], pz['r']
        ring = [(c[0] + r * math.cos(2 * math.pi * i / 24), c[1] + r * math.sin(2 * math.pi * i / 24)) for i in range(24)]
        cap(P, [(c[0] + (x - c[0]) * 0.65, c[1] + (y - c[1]) * 0.65) for x, y in ring], 0.16, M['plaza'])
    P.build('MetroSidewalks', coll)


def diag_edges(half):
    a, b = MP.DIAG_A, MP.DIAG_B
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy)
    ux, uy = dx / L, dy / L
    nx, ny = -uy, ux
    A = (a[0] - ux * 400, a[1] - uy * 400)
    B = (b[0] + ux * 400, b[1] + uy * 400)
    left = ((A[0] + nx * half, A[1] + ny * half), (B[0] + nx * half, B[1] + ny * half))
    right = ((A[0] - nx * half, A[1] - ny * half), (B[0] - nx * half, B[1] - ny * half))
    return left, right


# ----------------------------------------------------------------------------- water, banks, piers
def build_waterfront(plan, M, coll):
    W, B, L_ = Acc(), Acc(BLD_ATTRS), Acc(dict(brnd=0.0))
    rz = plan['river']['z']
    W.strip((-FAR * 1.5, (MP.RIVER_S) / 2), (FAR * 1.5, MP.RIVER_S / 2), -MP.RIVER_S + 40, rz, M['water'])
    for y, s in ((0.0, -1), (MP.RIVER_S, 1)):
        # embankment wall from below the water up to the promenade, facing the river
        a, b = (-FAR, y), (FAR, y)
        if s < 0:
            B.quad((a[0], y, rz - 2), (b[0], y, rz - 2), (b[0], y, 0.3), (a[0], y, 0.3), M['stone'])
        else:
            B.quad((b[0], y, rz - 2), (a[0], y, rz - 2), (a[0], y, 0.3), (b[0], y, 0.3), M['stone'])
        # promenade slab and railing
        y0, y1 = (0.0, 14.0) if s < 0 else (MP.RIVER_S - 14.0, MP.RIVER_S)
        B.prism(MP.rect(-FAR, y0, FAR, y1), 0.0, 0.3, M['promenade'], cap=True)
        ry = 0.4 if s < 0 else MP.RIVER_S - 0.4
        B.prism(MP.rect(-FAR, ry - 0.05, FAR, ry + 0.05), 1.15, 1.25, M['dark'])
        B.prism(MP.rect(-FAR, ry - 0.03, FAR, ry + 0.03), 0.3, 1.15, M['dark'], cap=False)
        # promenade lamps every 25 m
        ly = 12.5 if s < 0 else MP.RIVER_S - 12.5
        x = -FAR
        while x < FAR:
            L_.box(x, ly, 0.3, 0.16, 0.16, 4.2, M['dark'])
            L_.box(x, ly, 4.5, 0.5, 0.5, 0.45, M['lamp'])
            x += 25.0
    # piers
    for p in plan['piers']:
        poly = ccw(p['poly'])
        B.prism(poly, rz - 1.5, 0.9, M['concrete'])
        if p['kind'] == 'cargo':
            sh = inset(poly, 4.0)
            B.prism(sh, 0.9, 9.5, M['industrial'], dict(bcol=lib.C('#7C6E60'), brnd=0.3, fh=6.0, bay=4.0, gf=0.0, crown=0.0),
                    cap=True, top_mat=M['roof'], uv_walls=True, bay=4.0)
        else:
            xs, ys = [q[0] for q in poly], [q[1] for q in poly]
            for x in (min(xs) + 1.5, max(xs) - 1.5):
                L_.box(x, (min(ys) + max(ys)) / 2, 0.9, 0.16, 0.16, 4.0, M['dark'])
                L_.box(x, (min(ys) + max(ys)) / 2, 4.9, 0.5, 0.5, 0.4, M['lamp'])
    W.build('MetroRiver', coll)
    B.build('MetroBanks', coll)
    L_.build('MetroWaterLamps', coll)


# ----------------------------------------------------------------------------- bridges
def deck_z(br, y):
    """Deck height: 12 m over the waterfront roads, ramps down inland, an arch up to deck_z[1] over the river."""
    lo, hi = br['deck_z']
    shore = lo + 2.0
    if y >= 0 or y <= MP.RIVER_S:
        d = y if y >= 0 else MP.RIVER_S - y                 # metres inland from the bank
        ramp = br['y1'] if y >= 0 else MP.RIVER_S - br['y0']
        return shore * min(1.0, max(0.0, 1 - (d - 50) / (ramp - 50)))
    t = (y - MP.RIVER_S / 2) / (-MP.RIVER_S / 2)
    return shore + (hi - shore) * (1 - t * t)


def build_bridges(plan, M, coll):
    for br in plan['bridges']:
        D = Acc(dict(hw=10.0, led=1.0))
        T = Acc(dict(dir=1.0, lane=0.0, tx=0.0, ty=1.0))
        S = Acc(dict(brnd=0.0))
        x, hw = br['x'], br['width'] / 2
        ys = []
        y = br['y1']
        while y > br['y0']:
            ys.append(y)
            y -= 10.0
        ys.append(br['y0'])
        u = 0.0
        for ya, yb in zip(ys, ys[1:]):
            za, zb = deck_z(br, ya), deck_z(br, yb)
            L = math.hypot(ya - yb, za - zb)
            # road surface (runs south = along -y; +x is left, so v = x offset)
            e = hw - 2
            D.face([(x - e, ya, za + 0.05), (x - e, yb, zb + 0.05), (x + e, yb, zb + 0.05), (x + e, ya, za + 0.05)],
                   [(u, -e), (u + L, -e), (u + L, e), (u, e)], M['road'], dict(hw=e, led=1.0))
            for k in range(4):
                o = -e + (k + 0.5) * 2 * e / 4
                dr = 1.0 if o < 0 else -1.0
                T.face([(x + o - 1, ya, za + 0.08), (x + o - 1, yb, zb + 0.08), (x + o + 1, yb, zb + 0.08), (x + o + 1, ya, za + 0.08)],
                       [(u, -1), (u + L, -1), (u + L, 1), (u, 1)], M['traffic'],
                       dict(dir=dr, lane=float(200 + k + int(abs(x)) % 50), tx=0.0, ty=-1.0))
            # girder sides, walkways, underside
            for sx in (-1, 1):
                xx = x + sx * hw
                pts = [(xx, ya, za - 2.6), (xx, ya, za + 1.1), (xx, yb, zb + 1.1), (xx, yb, zb - 2.6)]
                S.face(pts if sx > 0 else pts[::-1], None, M['steel'])
                x0_, x1_ = (x - hw, x - e) if sx < 0 else (x + e, x + hw)
                S.face([(x0_, ya, za + 0.05), (x0_, yb, zb + 0.05), (x1_, yb, zb + 0.05), (x1_, ya, za + 0.05)], None, M['concrete'])
            S.face([(x - hw, ya, za - 2.6), (x + hw, ya, za - 2.6), (x + hw, yb, zb - 2.6), (x - hw, yb, zb - 2.6)], None, M['steel'])
            u += L
        # towers: two legs, portal beams; top = tower_h above the deck at the tower
        tops = []
        for ty in br['towers']:
            zd = deck_z(br, ty)
            zt = zd + br['tower_h']
            for sx in (-1, 1):
                xx = x + sx * (hw + 2.5)
                S.prism(ccw(MP.rect(xx - 3.0, ty - 4.0, xx + 3.0, ty + 4.0)), -3.0, zt * 0.55, M['steel'], cap=False)
                S.prism(ccw(MP.rect(xx - 2.3, ty - 3.0, xx + 2.3, ty + 3.0)), zt * 0.55, zt, M['steel'])
                S.box(xx, ty, zt, 2.0, 2.0, 1.0, M['aviation'], dict(brnd=0.2 + 0.3 * sx))
            for zb_ in (zd - 4.0, zt * 0.6, zt - 7.0):
                S.box(x, ty, zb_, 2 * hw + 6, 4.0, 4.5, M['steel'])
            S.prism(ccw(MP.rect(x - hw - 9, ty - 8, x + hw + 9, ty + 8)), -4.0, 0.0, M['concrete'])   # caisson
            tops.append((ty, zt))
        # main cables: anchorage -> tower -> sag -> tower -> anchorage
        (tn, ztn), (ts, zts) = tops
        an_n, an_s = (8.0, deck_z(br, 8.0) + 1.5), (MP.RIVER_S - 8.0, deck_z(br, MP.RIVER_S - 8.0) + 1.5)
        mid = (tn + ts) / 2
        zmid = deck_z(br, mid) + 3.0

        def cable_z(y):
            if y >= tn:
                t = (an_n[0] - y) / (an_n[0] - tn)
                return an_n[1] + (ztn - an_n[1]) * t - 10.0 * math.sin(math.pi * t)
            if y <= ts:
                t = (y - an_s[0]) / (ts - an_s[0])
                return an_s[1] + (zts - an_s[1]) * t - 10.0 * math.sin(math.pi * t)
            t = (y - mid) / (tn - mid)
            return zmid + (ztn - zmid) * t * t

        cy = [an_n[0] - k * 5.0 for k in range(int((an_n[0] - an_s[0]) / 5.0) + 1)]
        for sx in (-1, 1):
            xx = x + sx * (hw + 2.5)
            pts = [(xx, y, cable_z(y)) for y in cy]
            S.tube(pts, 0.45, M['steel'])
            for k, (px, py, pz) in enumerate(pts):
                if k % 2 == 0:
                    S.box(px, py, pz + 0.45, 0.6, 0.6, 0.5, M['cable_light'])
                zd = deck_z(br, py)
                if k % 2 == 1 and pz - zd > 3.0:
                    S.box(px, py, zd + 1.0, 0.18, 0.18, pz - zd - 1.0, M['steel'])
        D.build(f'MetroBridgeDeck_{int(x)}', coll)
        T.build(f'MetroBridgeTraffic_{int(x)}', coll)
        S.build(f'MetroBridge_{int(x)}', coll)


# ----------------------------------------------------------------------------- park
def build_park(plan, M, coll, focus=None, R=0.0):
    """Lawns, the lake and trees: low-poly cones far away, full crowns within R of the focus."""
    P = Acc(dict(brnd=0.0))
    rng = random.Random(77)
    MD = None
    if R > 0:
        import metro_detail as MD
    for pk in plan['parks']:
        poly = ccw(pk['poly'])
        xs, ys = [p[0] for p in poly], [p[1] for p in poly]
        lake = pk.get('lake')
        if lake:
            c, r = lake['c'], lake['r']
            ring = [(c[0] + r[0] * math.cos(2 * math.pi * i / 48), c[1] + r[1] * math.sin(2 * math.pi * i / 48)) for i in range(48)]
            cap(P, ring, 0.2, M['water'])
        step = 13.0 if not pk.get('kind') else 9.0
        y = min(ys) + 4
        while y < max(ys) - 4:
            x = min(xs) + 4 + rng.uniform(0, step)
            while x < max(xs) - 4:
                px, py = x + rng.uniform(-4, 4), y + rng.uniform(-4, 4)
                ok = True
                if lake:
                    ex, ey = (px - c[0]) / (r[0] + 12), (py - c[1]) / (r[1] + 12)
                    ok = ex * ex + ey * ey > 1
                # two paths across the park
                if ok and not pk.get('kind') and (abs(px - (py - 2400) * 0.35 + 300) < 6 or abs(py - 3000) < 5):
                    ok = False
                if ok and rng.random() < (0.8 if not pk.get('kind') else 0.6):
                    if MD and math.hypot(px - focus[0], py - focus[1]) < R:
                        if math.hypot(px - focus[0], py - focus[1]) > 5:
                            MD.street_tree(P, M, px, py, 0.18, rng, scale=1.35)
                    else:
                        tree(P, M, px, py, 0.18, rng)
                x += step
            y += step
    P.build('MetroPark', coll)


def tree(P, M, x, y, z, rng):
    h = rng.uniform(6, 11)
    r = h * rng.uniform(0.35, 0.5)
    at = dict(brnd=rng.random())
    P.box(x, y, z, 0.4, 0.4, h * 0.45, M['wood'], at)
    # crown: two crossed low-poly blobs
    for k, (s, zz) in enumerate(((1.0, h * 0.62), (0.75, h * 0.85))):
        rr = r * s
        seg = 6
        rot = rng.uniform(0, math.pi)
        ring = [(x + rr * math.cos(rot + 2 * math.pi * i / seg), y + rr * math.sin(rot + 2 * math.pi * i / seg)) for i in range(seg)]
        top, bot = (x, y, zz + rr * 0.9), (x, y, zz - rr * 0.8)
        for i in range(seg):
            a, b = ring[i], ring[(i + 1) % seg]
            P.face([(a[0], a[1], zz), (b[0], b[1], zz), top], None, M['tree'], at)
            P.face([(b[0], b[1], zz), (a[0], a[1], zz), bot], None, M['tree'], at)


# ----------------------------------------------------------------------------- plaza screens, rooftop signs
SCREENS = [('#FF2E88', '#2EE6FF'), ('#FF8A1E', '#7A2EFF'), ('#2E6BFF', '#E8F0FF'), ('#FF2A2A', '#FFD21E'),
           ('#00D68F', '#1E2EFF'), ('#FFFFFF', '#FF4FB0')]


def build_signs(plan, M, coll):
    S = Acc()
    scr = [MM.screen_mat(f'MF_screen{i}', a, c, 0.2 + 0.07 * i) for i, (a, c) in enumerate(SCREENS)]
    rng = random.Random(5)
    for pz in plan['plazas']:
        c = pz['c']
        for b in plan['buildings']:
            bc = MP.centroid(b['poly'])
            if math.hypot(bc[0] - c[0], bc[1] - c[1]) > 200 or b['h'] < 12:
                continue
            poly = ccw(b['poly'])
            for i in range(len(poly)):
                a, q = poly[i], poly[(i + 1) % len(poly)]
                L = math.hypot(q[0] - a[0], q[1] - a[1])
                mx, my = (a[0] + q[0]) / 2, (a[1] + q[1]) / 2
                nx, ny = (q[1] - a[1]) / L, -(q[0] - a[0]) / L          # outward normal (CCW)
                tx, ty = c[0] - mx, c[1] - my
                if L < 10 or (nx * tx + ny * ty) / (math.hypot(tx, ty) or 1) < 0.25:
                    continue
                z = 6.0
                top = min(b['h'] - 3, 60.0)
                while z < top - 5:
                    hh = min(rng.uniform(7, 18), top - z)
                    ww = min(L * rng.uniform(0.6, 0.95), 40.0)
                    s0 = rng.uniform(0, L - ww)
                    ux, uy = (q[0] - a[0]) / L, (q[1] - a[1]) / L
                    p0 = (a[0] + ux * s0 + nx * 0.5, a[1] + uy * s0 + ny * 0.5)
                    p1 = (p0[0] + ux * ww, p0[1] + uy * ww)
                    S.quad((p0[0], p0[1], z), (p1[0], p1[1], z), (p1[0], p1[1], z + hh), (p0[0], p0[1], z + hh), rng.choice(scr),
                           uvs=[(0, 0), (ww / 10, 0), (ww / 10, hh / 10), (0, hh / 10)])
                    z += hh + rng.uniform(0.8, 3.0)
    # rooftop signs on mid-rises along the waterfront, facing the river
    for b in plan['buildings']:
        bc = MP.centroid(b['poly'])
        if not (60 < bc[1] < 700 and 20 < b['h'] < 110 and b['seed'] % 9 == 0):
            continue
        xs = [p[0] for p in b['poly']]
        ys = [p[1] for p in b['poly']]
        w = min(max(xs) - min(xs) - 2, 24.0)
        if w < 8:
            continue
        x0, y0, z0 = (min(xs) + max(xs)) / 2 - w / 2, min(ys) + 2, b['h'] + 2.0
        hh = w * 0.3
        S.quad((x0, y0, z0), (x0 + w, y0, z0), (x0 + w, y0, z0 + hh), (x0, y0, z0 + hh), rng.choice(scr),
               uvs=[(0, 0), (w / 10, 0), (w / 10, hh / 10), (0, hh / 10)])
        for x in (x0 + 1, x0 + w - 1):
            S.box(x, y0 + 0.4, b['h'], 0.3, 0.3, 2.0 + hh, M['dark'])
    S.build('MetroSigns', coll)


# ----------------------------------------------------------------------------- the city beyond the plan
FAR_CLUSTERS = [((3600.0, 5600.0), 1100.0, 170.0), ((-4300.0, 2400.0), 900.0, 120.0), ((5200.0, -2400.0), 800.0, 90.0),
                ((-3000.0, 6800.0), 1000.0, 80.0)]


def build_filler(plan, M, coll, reach=7500.0):
    """Generic blocks out to the horizon so the city never ends at the edge of the plan; the fog swallows them."""
    ex = plan['extent']
    core = (MP.X0 - 30, MP.RIVER_S - 1010, MP.X1 + 30, MP.Y_TOP + 60)
    rng = random.Random(99)
    kinds = ['punched', 'punched', 'ribbon', 'brick', 'curtain']
    pal = ['#B9B2A4', '#9C968C', '#C7BDAA', '#8A7F72', '#7B5A48', '#A69A88', '#6F7A82', '#5F6E78']
    tiles = {}
    cw, ch = 150.0, 110.0
    y = MP.RIVER_S - 60 - reach * 0.6
    while y < reach:
        if MP.RIVER_S - 40 < y < 40:
            y += ch
            continue
        x = -reach
        while x < reach:
            if not (core[0] < x + cw and x < core[2] and core[1] < y + ch and y < core[3]) and rng.random() < 0.9:
                hb = 14.0
                for (cx, cy), r, pk in FAR_CLUSTERS:
                    hb = max(hb, pk * math.exp(-((x - cx) ** 2 + (y - cy) ** 2) / (r * r)))
                key = (int(math.floor(x / 1500)), int(math.floor(y / 1500)))
                A = tiles.setdefault(key, Acc(BLD_ATTRS))
                xa = x + 8
                while xa < x + cw - 18:
                    bw = rng.uniform(18, 60)
                    xb = min(xa + bw, x + cw - 8)
                    h = max(8.0, hb * math.exp(rng.gauss(-0.3, 0.45)))
                    k = rng.choice(kinds if hb < 60 else ['curtain', 'ribbon', 'curtain_dark', 'punched'])
                    fh = 3.3 if k in ('punched', 'brick') else 3.9
                    at = dict(bcol=lib.C(rng.choice(pal)), brnd=rng.random(), fh=fh, bay=3.0 if not k.startswith('curtain') else 1.5,
                              gf=0.0, crown=0.0)
                    p = MP.rect(xa, y + 8 + rng.uniform(0, 8), xb, y + ch - 8 - rng.uniform(0, 8))
                    walls(A, p, p, 0.0, h, M[k], at)
                    cap(A, p, h, M['roof'])
                    xa = xb + rng.uniform(3, 12)
            x += cw
        y += ch
    for (i, j), A in sorted(tiles.items()):
        A.build(f'MetroFar_{i}_{j}', coll)
    G = Acc()
    for y0, y1 in ((40.0, reach + 200), (MP.RIVER_S - reach, MP.RIVER_S - 20)):
        G.face([(-reach - 200, y0, -0.02), (reach + 200, y0, -0.02), (reach + 200, y1, -0.02), (-reach - 200, y1, -0.02)],
               None, M['ground'])
    G.build('MetroGround', coll)


# ----------------------------------------------------------------------------- everything
def build_city(focus=(0.0, 0.0), detail_r=0.0, filler=True, skip=None, fps=24, frames=48, night=0.0):
    """Build the whole city into collection 'Metro'. Returns a stats dict."""
    import time
    t0 = time.time()
    plan = get_plan()
    coll = bpy.data.collections.new('Metro')
    bpy.context.scene.collection.children.link(coll)
    M = mats()
    st = dict(buildings=len(plan['buildings']))
    st['bld_faces'] = build_buildings(plan, M, coll, skip)
    roads = far_roads(plan)
    st['lamps'] = build_streets(plan, M, coll, roads)
    block_platforms(plan, M, coll)
    build_waterfront(plan, M, coll)
    build_bridges(plan, M, coll)
    build_park(plan, M, coll, focus, min(detail_r, 260.0))
    build_signs(plan, M, coll)
    if filler:
        build_filler(plan, M, coll)
    if detail_r > 0:
        import metro_detail
        st['detail'] = metro_detail.build_detail(plan, M, coll, roads, focus, detail_r, fps, frames, night)
    st['objects'] = len(coll.objects)
    st['faces'] = sum(len(o.data.polygons) for o in coll.objects if o.type == 'MESH')
    st['seconds'] = round(time.time() - t0, 1)
    return st
