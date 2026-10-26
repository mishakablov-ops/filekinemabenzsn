"""Street level of «Метрополис» around the camera (style «блендер», 26.10.2026): what makes a close shot read as a
real city. Built only within detail_r of the focus point, so far shots stay light.

- facades facing the street: floor ledges, window sills and lintels, fire escapes on brick houses, balconies on
  apartment blocks, shop signs (some with Cyrillic names), awnings, doors, stoops of townhouses, tower canopies;
- streets: trees in pits, parked cars along the kerb, cars driving in the lanes (they replace the painted traffic of
  metro_mats.traffic_mat inside FocusR), traffic lights, zebra crossings, bins, hydrants, benches, a metro entrance;
- at night: real point lights under the nearest street lamps.
"""
import math
import random
import bpy
import lib
import metro_plan as MP
import metro_mats as MM
import metro_build as MB
from metro_build import Acc

CAR_COLS = ['#8A2E25', '#2F3B45', '#C9C1B2', '#3E4A3A', '#6B6259', '#1F2124', '#A67C45', '#4B5E73', '#E8E6E1',
            '#14161A', '#B8BCC0', '#7A1F1F', '#2B4A6E', '#5E6A70', '#D9D4C7']
TAXI = '#F2B51E'
AWNING_COLS = ['#7A1F1F', '#1F4A2E', '#1F2E4A', '#2E2E2E', '#8A6A2A', '#5A2A4A', '#A0522D', '#3B5B4F']
SIGN_COLS = ['#C8102E', '#0B3D91', '#0F7B3E', '#1E1E1E', '#7A1F5C', '#D4A017', '#2B2B2B', '#00587A']
SHOP_NAMES = ['АПТЕКА', 'КОФЕ', 'ПРОДУКТЫ', 'ЦВЕТЫ', 'ХЛЕБ', 'БАР', 'ОПТИКА', 'КНИГИ', 'ПИЦЦА', 'ОБУВЬ', 'ДЕЛИ',
              'ЛОМБАРД', 'ПРАЧЕЧНАЯ', 'ПЕКАРНЯ', 'ЧАСЫ', 'СУШИ', 'ГАСТРОНОМ', 'КИНО', 'ХИМЧИСТКА', 'БУРГЕРЫ', 'ВИНО',
              'ТАБАК', 'ЛАПША', 'ОТЕЛЬ', 'БАНК', 'ФОТО', 'ЗАКУСОЧНАЯ', 'ЦИРЮЛЬНЯ', 'МОРОЖЕНОЕ', 'ТАКО']
FONT = r'C:\Windows\Fonts\arialbd.ttf'
CAR_ATTRS = dict(bcol=(0.5, 0.5, 0.5, 1.0), brnd=0.0)


def dmats(M):
    D = dict(
        paint=MM.paint_mat('MF_carpaint', 0.28, 0.0, 0.7),
        fabric=MM.paint_mat('MF_fabric', 0.9, 0.0, 0.2),
        board=MM.paint_mat('MF_signboard', 0.5, 0.0, 0.4, glow=0.6),
        glass=MM.flat_mat('MF_carglass', '#0E1114', 0.06, 0.0, 1.0),
        tyre=MM.flat_mat('MF_tyre', '#141414', 0.9),
        rim=MM.flat_mat('MF_rim', '#9A9C9E', 0.25, 0.9),
        plastic=MM.flat_mat('MF_plastic', '#1C1C1D', 0.6),
        head=MM.glow_mat('MF_headlight', '#FFF4DE', 30.0, 'Night'),
        tail=MM.glow_mat('MF_taillight', '#FF2010', 14.0, 'Night'),
        lamp_off=MM.flat_mat('MF_lamp_off', '#6A6460', 0.2, 0.0, 1.0),
        sig_r=MM.glow_mat('MF_sig_red', '#FF2A10', 30.0, 'Signal'),
        sig_g=MM.glow_mat('MF_sig_green', '#2BFF9A', 30.0, 'Signal'),
        sig_off=MM.flat_mat('MF_sig_off', '#202020', 0.3),
        signtext=MM.glow_mat('MF_signtext', '#FFF4E0', 7.0, 'Neon'),
        metro_m=MM.glow_mat('MF_metro_m', '#E8231B', 8.0, 'Signal'),
        rail=MM.flat_mat('MF_railglass', '#55666E', 0.08, 0.3, 0.9),
        door=MM.flat_mat('MF_door', '#2A211B', 0.4),
        iron=MM.flat_mat('MF_iron', '#1E1F21', 0.55, 0.6),
        green=MM.flat_mat('MF_greenpaint', '#2E4B3A', 0.5),
        red=MM.flat_mat('MF_hydrant', '#A8281C', 0.45),
        stripe=MM.flat_mat('MF_zebra', '#DAD6CC', 0.7),
        pit=MM.flat_mat('MF_treepit', '#3A2E24', 0.95),
    )
    D.update({k: v for k, v in M.items() if k not in D})
    return D


# ----------------------------------------------------------------------------- small helpers
def wbox(A, a, u, n, s0, s1, d0, d1, z0, z1, mat, at=None, bottom=False):
    """Box against a wall: s along the wall (unit u from point a), d outwards (unit n), z up."""
    P = lambda s, d: (a[0] + u[0] * s + n[0] * d, a[1] + u[1] * s + n[1] * d)
    A.prism(MB.ccw([P(s0, d0), P(s1, d0), P(s1, d1), P(s0, d1)]), z0, z1, mat, at, cap=True, bottom=bottom)


def beam(A, p, q, r, mat, at=None):
    A.tube([p, q], r, mat, at)


def zone_at(x, y):
    if y < MP.RIVER_S:
        return 'borough'
    return MP.zone_of(x, y, MP.height_field(x, y))


def dist_seg(px, py, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L2 = dx * dx + dy * dy or 1.0
    t = max(0.0, min(1.0, ((px - a[0]) * dx + (py - a[1]) * dy) / L2))
    return math.hypot(px - a[0] - dx * t, py - a[1] - dy * t), t


# ----------------------------------------------------------------------------- cars
def fbox(A, T, x0, x1, y0, y1, z0, z1, t, mat, at=None, bottom=False):
    """Box with a smaller top (t = (tx0, tx1, ty0, ty1)) in local car coords; T maps local -> world."""
    tx0, tx1, ty0, ty1 = t
    bot = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    top = [(tx0, ty0), (tx1, ty0), (tx1, ty1), (tx0, ty1)]
    for i in range(4):
        a, b = bot[i], bot[(i + 1) % 4]
        ta, tb = top[i], top[(i + 1) % 4]
        A.face([T(a[0], a[1], z0), T(b[0], b[1], z0), T(tb[0], tb[1], z1), T(ta[0], ta[1], z1)], None, mat, at)
    A.face([T(p[0], p[1], z1) for p in top], None, mat, at)
    if bottom:
        A.face([T(p[0], p[1], z0) for p in bot[::-1]], None, mat, at)


def car(A, D, x, y, z, hd, col, kind='sedan', lights=False, rnd=0.0):
    c, s = math.cos(hd), math.sin(hd)
    T = lambda lx, ly, lz: (x + c * lx - s * ly, y + s * lx + c * ly, z + lz)
    at = dict(bcol=lib.C(col), brnd=rnd)
    if kind == 'van':
        L, W, H = 5.0, 1.95, 2.0
        fbox(A, T, -L / 2, L / 2, -W / 2, W / 2, 0.35, 1.1, (-L / 2, L / 2, -W / 2, W / 2), D['paint'], at, True)
        fbox(A, T, -L / 2, L / 2 - 0.4, -W / 2, W / 2, 1.1, H, (-L / 2, L / 2 - 1.0, -W / 2 + 0.05, W / 2 - 0.05), D['paint'], at)
        fbox(A, T, L / 2 - 0.45, L / 2 - 0.38, -W / 2 + 0.1, W / 2 - 0.1, 1.15, H - 0.15, (L / 2 - 0.98, L / 2 - 0.9, -W / 2 + 0.12, W / 2 - 0.12), D['glass'], at)
        hz = 0.75
    else:
        suv = kind == 'suv'
        L, W = (4.7, 1.9) if suv else (4.5, 1.8)
        zb, zs, zr = (0.42, 1.05, 1.75) if suv else (0.3, 0.82, 1.42)
        fbox(A, T, -L / 2, L / 2, -W / 2, W / 2, zb, zs, (-L / 2 + 0.05, L / 2 - 0.05, -W / 2, W / 2), D['paint'], at, True)
        fbox(A, T, -L / 2 + 0.05, L / 2 - 0.05, -W / 2, W / 2, zs, zs + 0.12, (-L / 2 + 0.15, L / 2 - 0.2, -W / 2 + 0.04, W / 2 - 0.04), D['paint'], at)
        cx0, cx1 = (-L / 2 + 0.5, L / 2 - 1.3) if suv else (-1.25, 1.05)
        tx0, tx1 = (cx0 + 0.15, cx1 - 0.35) if suv else (-0.95, 0.5)
        fbox(A, T, cx0, cx1, -W / 2 + 0.08, W / 2 - 0.08, zs + 0.12, zr, (tx0, tx1, -W / 2 + 0.2, W / 2 - 0.2), D['glass'], at)
        fbox(A, T, tx0, tx1, -W / 2 + 0.2, W / 2 - 0.2, zr, zr + 0.05, (tx0 + 0.03, tx1 - 0.03, -W / 2 + 0.23, W / 2 - 0.23), D['paint'], at)
        hz = zb + 0.32
        if col == TAXI:
            fbox(A, T, -0.4, 0.1, -0.25, 0.25, zr + 0.05, zr + 0.3, (-0.4, 0.1, -0.25, 0.25), D['head'] if lights else D['lamp_off'], at)
    # bumpers, lights
    for sx in (-1, 1):
        fbox(A, T, sx * L / 2 - (0.08 if sx > 0 else -0.08) - 0.04, sx * L / 2 + 0.04, -W / 2 + 0.05, W / 2 - 0.05, hz - 0.3, hz - 0.12,
             (sx * L / 2 - 0.12, sx * L / 2 + 0.04, -W / 2 + 0.05, W / 2 - 0.05), D['plastic'], at)
        for sy in (-1, 1):
            m = (D['head'] if sx > 0 else D['tail']) if lights else D['lamp_off']
            x0 = sx * L / 2 - 0.02
            fbox(A, T, min(x0, x0 + sx * 0.05), max(x0, x0 + sx * 0.05), sy * (W / 2 - 0.12) - 0.16, sy * (W / 2 - 0.12) + 0.16,
                 hz - 0.06, hz + 0.08, (min(x0, x0 + sx * 0.05), max(x0, x0 + sx * 0.05), sy * (W / 2 - 0.12) - 0.16, sy * (W / 2 - 0.12) + 0.16), m, at)
    # wheels
    r, seg = 0.33, 10
    for wx in (-L * 0.31, L * 0.31):
        for sy in (-1, 1):
            y0, y1 = sy * (W / 2 - 0.22), sy * (W / 2 + 0.01)
            ring = [(wx + r * math.cos(2 * math.pi * i / seg), r + r * math.sin(2 * math.pi * i / seg)) for i in range(seg)]
            for i in range(seg):
                a, b = ring[i], ring[(i + 1) % seg]
                pts = [T(a[0], y0, a[1]), T(b[0], y0, b[1]), T(b[0], y1, b[1]), T(a[0], y1, a[1])]
                A.face(pts if sy > 0 else pts[::-1], None, D['tyre'], at)
            cap = [T(px, y1, pz) for px, pz in ring]
            A.face(cap[::-1] if sy > 0 else cap, None, D['tyre'], at)
            hub = [T(wx + 0.19 * math.cos(2 * math.pi * i / 8), y1 + sy * 0.005, r + 0.19 * math.sin(2 * math.pi * i / 8)) for i in range(8)]
            A.face(hub[::-1] if sy > 0 else hub, None, D['rim'], at)


def pick_car(rng):
    col = TAXI if rng.random() < 0.12 else rng.choice(CAR_COLS)
    kind = 'sedan' if col == TAXI else rng.choices(['sedan', 'suv', 'van'], [0.6, 0.3, 0.1])[0]
    return col, kind


# ----------------------------------------------------------------------------- trees
_ICO = None


def ico():
    """Unit icosphere (1 subdivision): (verts, tris)."""
    global _ICO
    if _ICO:
        return _ICO
    t = (1 + 5 ** 0.5) / 2
    V = [(-1, t, 0), (1, t, 0), (-1, -t, 0), (1, -t, 0), (0, -1, t), (0, 1, t), (0, -1, -t), (0, 1, -t),
         (t, 0, -1), (t, 0, 1), (-t, 0, -1), (-t, 0, 1)]
    V = [tuple(c / math.sqrt(sum(q * q for q in v)) for c in v) for v in V]
    F = [(0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11), (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6),
         (7, 1, 8), (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9), (4, 9, 5), (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1)]
    mid = {}

    def m(a, b):
        k = (min(a, b), max(a, b))
        if k not in mid:
            p = [(V[a][i] + V[b][i]) / 2 for i in range(3)]
            l = math.sqrt(sum(q * q for q in p))
            V.append(tuple(q / l for q in p))
            mid[k] = len(V) - 1
        return mid[k]
    F2 = []
    for a, b, c in F:
        ab, bc, ca = m(a, b), m(b, c), m(c, a)
        F2 += [(a, ab, ca), (b, bc, ab), (c, ca, bc), (ab, bc, ca)]
    _ICO = (V, F2)
    return _ICO


def blob(A, cx, cy, cz, r, rng, mat, at, squash=0.85):
    V, F = ico()
    vv = [(cx + x * r * (1 + rng.uniform(-0.18, 0.18)), cy + y * r * (1 + rng.uniform(-0.18, 0.18)),
           cz + z * r * squash * (1 + rng.uniform(-0.18, 0.18))) for x, y, z in V]
    A.shared(vv, F, mat, at)


def street_tree(A, D, x, y, z, rng, scale=1.0):
    h = rng.uniform(7.5, 11.0) * scale
    at = dict(brnd=rng.random())
    A.cyl(x, y, z, 0.16, h * 0.55, D['wood'], at, seg=6, r_top=0.1, cap=False)
    beam(A, (x, y, z + h * 0.42), (x + rng.uniform(-1.4, 1.4), y + rng.uniform(-1.4, 1.4), z + h * 0.7), 0.07, D['wood'], at)
    r = h * 0.3
    blob(A, x, y, z + h * 0.68, r, rng, D['tree'], at)
    for _ in range(3):
        a = rng.uniform(0, 2 * math.pi)
        blob(A, x + math.cos(a) * r * 0.7, y + math.sin(a) * r * 0.7, z + h * rng.uniform(0.6, 0.82), r * rng.uniform(0.55, 0.75), rng, D['tree'], at)


# ----------------------------------------------------------------------------- facades
def street_edges(b, blocks):
    """Edges of the lot that face a street (the point 3 m outside is not inside the same block)."""
    poly = MB.ccw(b['poly'])
    out = []
    cx, cy = MP.centroid(poly)
    blk = next((k for k in blocks if k[0] - 0.5 <= cx <= k[2] + 0.5 and k[1] - 0.5 <= cy <= k[3] + 0.5), None)
    for i in range(len(poly)):
        a, q = poly[i], poly[(i + 1) % len(poly)]
        L = math.hypot(q[0] - a[0], q[1] - a[1])
        if L < 3:
            continue
        u = ((q[0] - a[0]) / L, (q[1] - a[1]) / L)
        n = (u[1], -u[0])
        px, py = (a[0] + q[0]) / 2 + n[0] * 3, (a[1] + q[1]) / 2 + n[1] * 3
        inside = blk is not None and blk[0] < px < blk[2] and blk[1] < py < blk[3]
        if inside and a[1] > MP.RIVER_S:
            d, _ = dist_seg(px, py, MP.DIAG_A, MP.DIAG_B)
            if d < MP.DIAG_ROW / 2:
                inside = False
        if not inside:
            out.append((a, u, n, L))
    return out


def facade_detail(A, T, D, b, blocks, near, rng, shops):
    kind, h, fh, typ = b['facade'], b['h'], b['floor_h'], b['type']
    gf = MB.gf_of(b)
    k = MM.KINDS[kind]
    edges = street_edges(b, blocks)
    zwall = b['tiers'][0][2] if b.get('tiers') else h
    floors_top = min(zwall, 70.0)
    for a, u, n, L in edges:
        nb = max(1, round(L / b['bay']))
        bw = L / nb
        nfl = int((floors_top - gf) / fh)
        # floor ledges
        if kind in ('punched', 'brick', 'shopfront') and h < 90:
            for i in range(1, nfl + 1):
                z = gf + i * fh
                if z < zwall - 0.5:
                    wbox(A, a, u, n, -0.1, L + 0.1, 0.0, 0.12, z - 0.14, z, D['cornice'], bottom=True)
        # sills and lintels of each window
        if kind in ('punched', 'brick') and near < 110:
            u0, u1 = k['u']
            v0, v1 = k['v']
            for i in range(min(nfl, 14)):
                zf = gf + i * fh
                for j in range(nb):
                    s0, s1 = (j + u0) * bw, (j + u1) * bw
                    wbox(A, a, u, n, s0 - 0.08, s1 + 0.08, 0.0, 0.16, zf + v0 * fh - 0.08, zf + v0 * fh, D['cornice'], bottom=True)
                    wbox(A, a, u, n, s0 - 0.05, s1 + 0.05, 0.0, 0.06, zf + v1 * fh, zf + v1 * fh + 0.14, D['cornice'])
        # fire escapes on brick walk-ups
        if typ in ('brick_midrise',) and h <= 45 and b['seed'] % 3 == 0 and nb >= 3 and nfl >= 3:
            j0 = nb // 2 - 1
            s0, s1 = j0 * bw + 0.2, (j0 + 3) * bw - 0.2 if nb >= 3 else L - 0.2
            for i in range(1, nfl):
                z = gf + i * fh if gf else i * fh
                wbox(A, a, u, n, s0, s1, 0.0, 1.15, z - 0.08, z, D['iron'], bottom=True)
                P = lambda s, d, zz: (a[0] + u[0] * s + n[0] * d, a[1] + u[1] * s + n[1] * d, zz)
                beam(A, P(s0, 1.12, z + 1.0), P(s1, 1.12, z + 1.0), 0.025, D['iron'])
                beam(A, P(s0, 1.12, z + 0.5), P(s1, 1.12, z + 0.5), 0.015, D['iron'])
                ss = s0
                while ss <= s1:
                    beam(A, P(ss, 1.12, z), P(ss, 1.12, z + 1.0), 0.015, D['iron'])
                    ss += 0.9
                # stair to the next floor, alternating direction
                if i < nfl - 1:
                    sa, sb = (s0 + 0.4, s1 - 1.2) if i % 2 else (s1 - 0.4, s0 + 1.2)
                    for dd in (0.45, 1.0):
                        beam(A, P(sa, dd, z), P(sb, dd, z + fh), 0.035, D['iron'])
                    for st in range(1, 9):
                        tt = st / 9
                        beam(A, P(sa + (sb - sa) * tt, 0.45, z + fh * tt), P(sa + (sb - sa) * tt, 1.0, z + fh * tt), 0.03, D['iron'])
        # balconies on apartment blocks
        if typ == 'residential' and b['seed'] % 2 == 0 and bw * 0.9 > 1.8 and h <= 70:
            for i in range(1, nfl):
                z = gf + i * fh
                for j in range(0, nb, 2):
                    s0, s1 = (j + 0.05) * bw, (j + 0.95) * bw
                    wbox(A, a, u, n, s0, s1, 0.0, 1.35, z - 0.18, z, D['concrete'], bottom=True)
                    P = lambda s, d, zz: (a[0] + u[0] * s + n[0] * d, a[1] + u[1] * s + n[1] * d, zz)
                    A.quad(P(s0, 1.3, z), P(s1, 1.3, z), P(s1, 1.3, z + 1.05), P(s0, 1.3, z + 1.05), D['rail'])
                    A.quad(P(s1, 1.3, z), P(s0, 1.3, z), P(s0, 1.3, z + 1.05), P(s1, 1.3, z + 1.05), D['rail'])
                    beam(A, P(s0, 1.3, z + 1.08), P(s1, 1.3, z + 1.08), 0.03, D['iron'])
        # shops: sign board over each pair of bays, awning under it, now and then a Cyrillic name
        if gf > 0 and kind != 'curtain' and kind != 'curtain_dark':
            unit = 2 * bw
            nu = max(1, int(L / unit))
            for j in range(nu):
                s0, s1 = j * unit + 0.25, (j + 1) * unit - 0.25
                col = rng.choice(SIGN_COLS)
                wbox(A, a, u, n, s0, s1, 0.0, 0.14, gf * 0.82, gf * 0.97, D['board'], dict(bcol=lib.C(col), brnd=0.0), bottom=True)
                if rng.random() < 0.55:
                    P = lambda s, d, zz: (a[0] + u[0] * s + n[0] * d, a[1] + u[1] * s + n[1] * d, zz)
                    at = dict(bcol=lib.C(rng.choice(AWNING_COLS)), brnd=0.0)
                    zt, zo, dep = gf * 0.8, gf * 0.8 - 0.75, 1.5
                    A.quad(P(s0, 0.0, zt), P(s1, 0.0, zt), P(s1, dep, zo), P(s0, dep, zo), D['fabric'], at)
                    A.quad(P(s0, dep, zo), P(s1, dep, zo), P(s1, 0.0, zt), P(s0, 0.0, zt), D['fabric'], at)
                    A.quad(P(s0, dep, zo - 0.3), P(s1, dep, zo - 0.3), P(s1, dep, zo), P(s0, dep, zo), D['fabric'], at)
                    for ss in (s0, s1):
                        A.face([P(ss, 0.0, zt), P(ss, dep, zo), P(ss, dep, zo - 0.3)], None, D['fabric'], at)
                        A.face([P(ss, dep, zo - 0.3), P(ss, dep, zo), P(ss, 0.0, zt)], None, D['fabric'], at)
                if near < 90 and rng.random() < 0.7:
                    shops.append((a, u, n, (s0 + s1) / 2, gf * 0.895, min(0.5, (s1 - s0) / 7.0)))
        # one entrance per street wall
        mid = (nb // 2) * bw + bw / 2 if nb > 1 else L / 2
        if typ == 'townhouse' and gf == 0:
            for st in range(6):                                           # stoop
                wbox(A, a, u, n, mid - 0.9, mid + 0.9, 0.0, 2.4 - st * 0.4, 0.15, 0.4 + st * 0.25, D['stone'])
            wbox(A, a, u, n, mid - 0.6, mid + 0.6, -0.05, 0.06, 1.65, 4.0, D['door'])
        elif typ in ('glass_tower', 'dark_tower', 'deco_tower', 'office', 'black_tubes'):
            wbox(A, a, u, n, mid - 4.0, mid + 4.0, 0.0, 3.5, 4.6, 4.9, D['dark'], bottom=True)
            wbox(A, a, u, n, mid - 1.8, mid + 1.8, -0.05, 0.08, 0.15, 3.4, D['glass'])
        else:
            wbox(A, a, u, n, mid - 0.7, mid + 0.7, -0.05, 0.08, 0.15, 2.6, D['door'])


def tower_fins(A, D, b):
    """Real depth on glass and office towers near the camera: mullion fins at every window bay and spandrel ledges
    at every floor (curtain walls), sill ledges under the window ribbons (offices)."""
    kind, typ = b['facade'], b['type']
    if kind not in ('curtain', 'curtain_dark', 'ribbon') or b.get('tubes') or b.get('shape') == 'taper':
        return
    poly = MB.ccw(b['poly'])
    cham = typ in ('glass_tower', 'dark_tower') and b['seed'] % 4 == 0 and MP.min_width(poly) > 24
    fh, gf = b['floor_h'], MB.gf_of(b)
    fin = D['dark'] if kind == 'curtain_dark' else D['metal']
    for ins, z0, z1 in (b['tiers'] or [[0.0, 0.0, b['h']]]):
        p = MB.inset(poly, ins)
        if cham:
            p = MB.chamfer(p, min(6.0, MP.min_width(p) * 0.15))
        floors = []
        z = gf + fh if gf else fh
        while z < z1 - 0.5:
            if z > z0 + 0.3:
                floors.append(z)
            z += fh
        for i in range(len(p)):
            a, q = p[i], p[(i + 1) % len(p)]
            L = math.hypot(q[0] - a[0], q[1] - a[1])
            if L < 2.0:
                continue
            u = ((q[0] - a[0]) / L, (q[1] - a[1]) / L)
            n = (u[1], -u[0])
            k = max(1, round(L / b['bay']))
            bw = L / k
            if kind == 'ribbon':
                v0 = MM.KINDS['ribbon']['v'][0]
                for zf in [gf] + floors if gf else [0.0] + floors:
                    zs = zf + v0 * fh
                    if z0 < zs < z1:
                        wbox(A, a, u, n, -0.05, L + 0.05, 0.0, 0.2, zs - 0.12, zs, fin, bottom=True)
                continue
            step = 1 if bw >= 2.5 else 2
            for j in range(0, k + 1, step):
                s = j * bw
                wbox(A, a, u, n, s - 0.06, s + 0.06, 0.0, 0.28, max(z0, gf), z1, fin)
            for zf in floors:
                wbox(A, a, u, n, -0.05, L + 0.05, 0.0, 0.14, zf - 0.12, zf, fin, bottom=True)


def shop_texts(shops, D, coll, rng):
    names = SHOP_NAMES[:]
    rng.shuffle(names)
    for k, (a, u, n, s, z, size) in enumerate(shops[:36]):
        x, y = a[0] + u[0] * s + n[0] * 0.16, a[1] + u[1] * s + n[1] * 0.16
        th = math.atan2(n[0], -n[1])
        ob = lib.text_obj(names[k % len(names)], size=size, loc=(x, y, z), rot=(math.pi / 2, 0, th), mat_=D['signtext'],
                          font=FONT, extrude=0.015, name='MetroShopText', coll=coll)
        ob.data.align_y = 'CENTER'


# ----------------------------------------------------------------------------- streets
def lane_offsets(r):
    """Driving lanes inside the focus: (offset, dir); parking lanes stay at the kerbs."""
    if r['kind'] == 'street':
        return [(-2.0, 1.0), (2.0, -1.0)]
    if r['kind'] in ('avenue', 'diagonal'):
        return [(-5.6, 1.0), (-2.0, 1.0), (2.0, -1.0), (5.6, -1.0)]
    half = r['lanes'] // 2
    lw = (r['road'] / 2 - 1.0) / half
    return [(sd * (1.0 + (k + 0.5) * lw), -sd) for sd in (-1, 1) for k in range(half)]


def build_detail(plan, M, coll, roads, focus, R, fps=24, frames=48, night=0.0, seed=11, keep=()):
    """keep: camera paths [((x0, y0), (x1, y1), r)]: no trees, bins, poles or walkers there, the lens passes freely."""
    import time
    t0 = time.time()
    kept = lambda x, y, rr=0.0: any(dist_seg(x, y, a, b)[0] < r + rr for a, b, r in keep)
    D = dmats(M)
    rng = random.Random(seed)
    fx, fy = focus
    A = Acc(dict(MB.BLD_ATTRS))                 # facades, furniture
    C = Acc(dict(CAR_ATTRS))                    # parked cars
    Tr = Acc(dict(brnd=0.0))                    # trees
    blocks = [(min(p[0] for p in k['poly']), min(p[1] for p in k['poly']), max(p[0] for p in k['poly']),
               max(p[1] for p in k['poly'])) for k in plan['blocks']]
    st = dict(facades=0, trees=0, parked=0, moving=0, signals=0, lights=0)
    # --- facades
    shops = []
    RB = min(R, 170.0)
    for b in plan['buildings']:
        cx, cy = MP.centroid(b['poly'])
        near = math.hypot(cx - fx, cy - fy)
        if near > RB + 40:
            continue
        facade_detail(A, None, D, b, blocks, near, random.Random(b['seed'] + 1), shops)
        if near < RB:
            tower_fins(A, D, b)
        st['facades'] += 1
    shops.sort(key=lambda s: math.hypot(s[0][0] - fx, s[0][1] - fy))
    shop_texts(shops, D, coll, rng)
    # --- along every road that passes the focus
    lamps = []
    moving = []
    for r in roads:
        a, b = r['a'], r['b']
        d, t = dist_seg(fx, fy, a, b)
        if d > R:
            continue
        L, gaps = MB.road_gaps(r, roads)
        sp = MB.spans(L, gaps)
        ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
        nx, ny = -uy, ux
        w = r['road']
        hw = w / 2
        tc = t * L
        half = math.sqrt(max(0.0, R * R - d * d))
        lo, hi = max(0.0, tc - half), min(L, tc + half)
        P = lambda uu, vv, a=a, ux=ux, uy=uy, nx=nx, ny=ny: (a[0] + ux * uu + nx * vv, a[1] + uy * uu + ny * vv)
        zr = MB.ROAD_Z.get(r['kind'], 0.03)
        hd = math.atan2(uy, ux)
        in_span = lambda uu, m=3.0: any(s0 + m < uu < s1 - m for s0, s1 in sp)
        # kerb lamps (same places as metro_build) -> real lights at night
        if r['kind'] in ('avenue', 'street', 'diagonal'):
            for side, off in ((-1, 0.0), (1, 15.0)):
                uu = off
                while uu < L:
                    if lo <= uu <= hi and in_span(uu):
                        x, y = P(uu, side * (hw - 1.2))
                        lamps.append((x, y, 7.6, 1.0 if r['kind'] != 'street' else 0.0))
                    uu += 30.0
        if r['kind'] == 'highway':
            continue
        zone = zone_at(*P(tc, 0))
        p_tree = dict(cbd=0.25, commercial=0.55, residential=0.85, borough=0.8, industrial=0.15).get(zone, 0.5)
        for side in (-1, 1):
            # trees in pits on the sidewalk
            uu = lo + rng.uniform(0, 6)
            while uu < hi:
                lamp_near = min(abs(((uu - (0 if side < 0 else 15)) + 15) % 30 - 15), 99)
                if in_span(uu, 6.0) and lamp_near > 3.0 and rng.random() < p_tree:
                    x, y = P(uu, side * (hw + 1.5))
                    if math.hypot(x - fx, y - fy) > 4 and not kept(x, y, 1.8):
                        Tr.prism(MB.ccw([(x - 0.7, y - 0.7), (x + 0.7, y - 0.7), (x + 0.7, y + 0.7), (x - 0.7, y + 0.7)]), 0.15, 0.17, D['pit'])
                        street_tree(Tr, D, x, y, 0.17, rng)
                        st['trees'] += 1
                uu += rng.uniform(8, 11)
            # parked cars along the kerb
            uu = lo + rng.uniform(0, 4)
            while uu < hi:
                if in_span(uu, 9.0) and rng.random() < 0.7:
                    x, y = P(uu, side * (hw - 1.15))
                    col, kind = pick_car(rng)
                    car(C, D, x, y, zr, hd + (0 if side < 0 else math.pi), col, kind, False, rng.random())
                    st['parked'] += 1
                uu += rng.uniform(5.8, 7.5)
            # bins, hydrants, newspaper boxes
            uu = lo + rng.uniform(0, 20)
            while uu < hi:
                x, y = P(uu, side * (hw + 0.8))
                if in_span(uu, 4.0) and not kept(x, y, 1.0):
                    k = rng.random()
                    if k < 0.45:
                        A.cyl(x, y, 0.15, 0.28, 0.85, D['green'], seg=8)
                    elif k < 0.7:
                        A.cyl(x, y, 0.15, 0.13, 0.6, D['red'], seg=8)
                        A.cyl(x, y, 0.75, 0.15, 0.12, D['red'], seg=8, r_top=0.05)
                    elif k < 0.85:
                        A.box(x, y, 0.15, 0.5, 0.45, 1.1, D['board'], dict(MB.BLD_ATTRS, bcol=lib.C(rng.choice(SIGN_COLS))), rot=hd)
                    else:
                        A.box(x, y, 0.15, 1.8, 0.5, 0.45, D['wood'], rot=hd)
                uu += rng.uniform(18, 35)
        # moving cars in the driving lanes
        if r['kind'] in ('avenue', 'street', 'diagonal'):
            dur = frames / fps
            for off, dr in lane_offsets(r):
                v = rng.uniform(9, 13) if r['kind'] != 'street' else rng.uniform(6, 8)
                uu = lo - v * dur * (1 if dr > 0 else 0) + rng.uniform(0, 30)
                end = hi + (v * dur if dr < 0 else 0)
                while uu < end:
                    moving.append((r, uu, off, dr, v, P, hd, zr))
                    uu += rng.uniform(25, 70)
        # traffic lights and zebra crossings where this avenue meets a street
        if r['kind'] == 'avenue':
            for g0, g1 in gaps:
                c = (g0 + g1) / 2
                if not (lo - 20 < c < hi + 20):
                    continue
                st['signals'] += 1
                sh = MP.ST_ROAD / 2
                for sv, su in ((-1, -1), (1, 1)):
                    x, y = P(c + su * (sh + 1.0), sv * (hw + 1.0))
                    if not kept(x, y, 0.6):
                        signal(A, D, x, y, hd + (0 if su < 0 else math.pi), hd - math.pi / 2 * sv, w)
                # zebras across the avenue (both sides of the crossing) and across the street
                for su in (-1, 1):
                    cu = c + su * (sh + 2.6)
                    vv = -hw + 0.6
                    while vv < hw - 0.5:
                        p0, p1 = P(cu - 1.5, vv), P(cu + 1.5, vv)
                        A.strip(p0, p1, 0.5, zr + 0.015, D['stripe'])
                        vv += 1.1
                for sv in (-1, 1):
                    cv = sv * (hw + 2.2)
                    uu = c - sh + 0.5
                    while uu < c + sh - 0.4:
                        p0, p1 = P(uu, cv - 1.4), P(uu, cv + 1.4)
                        A.strip(p0, p1, 0.5, MB.ROAD_Z['street'] + 0.015, D['stripe'])
                        uu += 1.1
    # metro entrance at the nearest station corner (stations every other avenue, every third street)
    metro_entrance(A, D, plan, focus, coll, kept)
    # promenades: benches facing the water, trees between the lamps
    for y_bench, y_tree, face in ((9.0, 11.6, -1), (MP.RIVER_S - 9.0, MP.RIVER_S - 11.6, 1)):
        if abs(fy - y_bench) > R:
            continue
        x = math.floor((fx - R) / 25.0) * 25.0 + 12.5
        while x < fx + R:
            if math.hypot(x - fx, y_tree - fy) > 4 and not kept(x, y_tree, 2.0):
                street_tree(Tr, D, x, y_tree, 0.3, rng, scale=1.1)
                st['trees'] += 1
            for bx in (x - 6.0, x + 6.0):
                if kept(bx, y_bench, 1.4):
                    continue
                A.box(bx, y_bench, 0.3, 1.9, 0.5, 0.45, D['wood'])
                A.box(bx, y_bench - face * 0.25, 0.75, 1.9, 0.08, 0.45, D['wood'])
                for sx in (-0.8, 0.8):
                    A.box(bx + sx, y_bench, 0.3, 0.08, 0.5, 0.45, D['iron'])
            x += 25.0
    st['people'] = pedestrians(roads, focus, R, fps, frames, coll, rng, kept=kept)
    # --- moving cars: one object each, driven at constant speed
    moving.sort(key=lambda m: math.hypot(m[5](m[1], m[2])[0] - fx, m[5](m[1], m[2])[1] - fy))
    for k, (r, uu, off, dr, v, P, hd, zr) in enumerate(moving[:160]):
        col, kind = pick_car(rng)
        Cm = Acc(dict(CAR_ATTRS))
        car(Cm, D, 0.0, 0.0, 0.0, hd + (0 if dr > 0 else math.pi), col, kind, night > 0.3, rng.random())
        ob = Cm.build(f'MetroCar_{k}', coll)
        x0, y0 = P(uu, off)
        x1, y1 = P(uu + dr * v * frames / fps, off)
        ob.location = (x0, y0, zr)
        ob.keyframe_insert('location', frame=1)
        ob.location = (x1, y1, zr)
        ob.keyframe_insert('location', frame=frames)
        ad = ob.animation_data
        if ad and ad.action:
            for fc in ad.action.fcurves:
                for kp in fc.keyframe_points:
                    kp.interpolation = 'LINEAR'
        st['moving'] += 1
    # --- night: real lights under the nearest lamps (streets and the promenade lamps of metro_build, every 25 m)
    for ly in (12.5, MP.RIVER_S - 12.5):
        if abs(fy - ly) < R:
            x = math.floor((fx - R) / 25.0) * 25.0
            while x < fx + R:
                lamps.append((x, ly, 4.3, 1.0))
                x += 25.0
    if night > 0.3:
        lamps.sort(key=lambda l: math.hypot(l[0] - fx, l[1] - fy))
        for k, (x, y, z, led) in enumerate(lamps[:40]):
            lib.light('POINT', (x, y, z), energy=350 * night, color='#FFE2BC' if led else '#FFA65A', size=0.25,
                      name='MetroStreetLight', shadow=k < 12, coll=coll)
            st['lights'] += 1
        if lamps:
            far = lamps[:40][-1]
            MM.set_global('LampR', math.hypot(far[0] - fx, far[1] - fy) + 1.0)
    A.build('MetroDetail', coll)
    C.build('MetroParked', coll)
    Tr.build('MetroTrees', coll)
    st['seconds'] = round(time.time() - t0, 1)
    return st


def pedestrians(roads, focus, R, fps, frames, coll, rng, max_n=32, kept=lambda x, y, rr=0.0: False):
    """People walking along the sidewalks and the promenade near the camera (people2: jointed legs, real gait)."""
    try:
        import people2
    except ImportError:
        return 0
    fx, fy = focus
    dur = frames / fps
    cand = []
    Rp = min(R, 110.0)
    for r in roads:
        if r['kind'] not in ('avenue', 'street', 'diagonal'):
            continue
        a, b = r['a'], r['b']
        d, t = dist_seg(fx, fy, a, b)
        if d > Rp:
            continue
        L, gaps = MB.road_gaps(r, roads)
        sp = MB.spans(L, gaps)
        ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
        nx, ny = -uy, ux
        hw, walk = r['road'] / 2, r['walk']
        tc = t * L
        uu = max(0.0, tc - Rp) + rng.uniform(0, 8)
        while uu < min(L, tc + Rp):
            if any(s0 + 2 < uu < s1 - 2 for s0, s1 in sp):
                side = rng.choice((-1, 1))
                off = side * (hw + rng.uniform(2.6, max(2.7, walk - 0.5)))
                x, y = a[0] + ux * uu + nx * off, a[1] + uy * uu + ny * off
                dr = rng.choice((-1, 1))
                cand.append((x, y, 0.15, ux * dr, uy * dr))
            uu += rng.uniform(5, 14)
    for y0 in (5.0, MP.RIVER_S - 5.0):
        if abs(fy - y0) < Rp:
            x = fx - Rp
            while x < fx + Rp:
                dr = rng.choice((-1, 1))
                cand.append((x, y0 + rng.uniform(-3, 3), 0.3, float(dr), 0.0))
                x += rng.uniform(6, 15)
    cand = [c for c in cand if math.hypot(c[0] - fx, c[1] - fy) > 3.0 and
            not any(kept(c[0] + c[3] * 1.5 * dur * f, c[1] + c[4] * 1.5 * dur * f, 0.8) for f in (0.0, 0.5, 1.0))]
    cand.sort(key=lambda c: math.hypot(c[0] - fx, c[1] - fy))
    n = 0
    for k, (x, y, z, dx, dy) in enumerate(cand[:max_n]):
        h = rng.uniform(0.92, 1.07)
        sp_ = rng.uniform(1.1, 1.55)
        p = people2.person((x, y, z), math.atan2(dx, -dy), h, rng, coll, bag=rng.random() < 0.3, name=f'MetroWalker{k}')
        people2.walk(p, sp_, rng.random(), h, fps)
        lib.move_root(p, [(x, y, z), (x + dx * sp_ * dur * 1.1, y + dy * sp_ * dur * 1.1, z)], 0.0, sp_)
        n += 1
    return n


def signal(A, D, x, y, hd_mast, hd_face, w):
    """Traffic-light pole on a corner with a mast arm over the avenue and two heads."""
    A.box(x, y, 0.15, 0.22, 0.22, 6.2, D['dark'])
    c, s = math.cos(hd_face), math.sin(hd_face)
    ex, ey = x + c * (w * 0.55), y + s * (w * 0.55)
    beam(A, (x, y, 6.0), (ex, ey, 6.0), 0.09, D['dark'])
    for (hx, hy, hz), lit in (((ex - c * 0.5, ey - s * 0.5, 5.0), 'g'), ((x + c * 0.3, y + s * 0.3, 2.6), 'r')):
        A.box(hx, hy, hz, 0.36, 0.36, 1.05, D['dark'], rot=hd_face)
        # three lenses facing the approaching traffic (both ways along the mast)
        for k, colr in enumerate(('r', 'a', 'g')):
            m = D['sig_r'] if (colr == lit == 'r') else D['sig_g'] if (colr == lit == 'g') else D['sig_off']
            for sd in (-1, 1):
                A.box(hx + math.cos(hd_mast) * 0.0 + sd * (-s) * 0.19, hy + sd * c * 0.19, hz + 0.18 + k * 0.32,
                      0.22, 0.04, 0.22, m, rot=hd_face)


def metro_entrance(A, D, plan, focus, coll, kept=lambda x, y, rr=0.0: False):
    fx, fy = focus
    aves, sts = MP.avenues(), MP.streets()
    st = [(ax, sy, i, j) for i, ax in enumerate(aves) for j, sy in enumerate(sts) if i % 2 == 0 and j % 3 == 1 and
          not MP.in_park(ax, sy)]
    if fy < MP.CITY_Y0 or not st:
        return
    ax, sy, i, j = min(st, key=lambda s: math.hypot(s[0] - fx, s[1] - fy))
    sx, sy_ = (1, -1)[(i // 2 + j) % 2], (1, -1)[(i + j // 3) % 2]      # which corner of the crossing
    x = ax + sx * (MP.AVE_ROAD / 2 + 3.2)
    y = sy + sy_ * (MP.ST_ROW / 2 + 8.0)
    if math.hypot(x - fx, y - fy) > 250 or kept(x, y, 4.0):
        return
    # opening with railings, globe lamps and a red «М» on a pole
    A.box(x, y, 0.15, 2.2, 6.0, 0.02, D['dark'])
    for sx in (-1, 1):
        beam(A, (x + sx * 1.15, y - 3.0, 1.2), (x + sx * 1.15, y + 3.0, 1.2), 0.04, D['green'])
        for k in range(7):
            beam(A, (x + sx * 1.15, y - 3.0 + k, 0.15), (x + sx * 1.15, y - 3.0 + k, 1.2), 0.025, D['green'])
    A.box(x, y + 3.0, 0.15, 2.3, 0.08, 1.2, D['green'])
    A.box(x + 1.4, y - 3.2, 0.15, 0.14, 0.14, 3.6, D['dark'])
    t = lib.text_obj('М', size=0.9, loc=(x + 1.4, y - 3.3, 4.2), rot=(math.pi / 2, 0, 0), mat_=D['metro_m'], font=FONT,
                     extrude=0.06, name='MetroM', coll=coll)
    t.data.align_y = 'CENTER'
