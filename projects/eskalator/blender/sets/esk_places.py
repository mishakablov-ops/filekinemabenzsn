"""Места для «Эскалатора», кроме метро: разрез земли с туннелем и домом в 20 этажей, старый универмаг 1900-х,
документ со штампом 1950, торговый центр с эскалаторами крест-накрест. Всё из кода, Blender 5.2."""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix
import esk_mech as E
import esk_metro as MT


def _txt(col, body, size, mat, loc=(0, 0, 0), rot=(math.pi / 2, 0, 0), align='CENTER', extrude=0.0, name='Txt'):
    cu = bpy.data.curves.new(name, 'FONT')
    cu.body = body
    cu.size = size
    cu.align_x = align
    cu.align_y = 'CENTER'
    cu.extrude = extrude
    f = MT.font()
    if f:
        cu.font = f
    ob = bpy.data.objects.new(name, cu)
    col.objects.link(ob)
    ob.data.materials.append(mat)
    ob.location = loc
    ob.rotation_euler = rot
    return ob


# ----------------------------------------------------------------------------- дома, машины, деревья
def panel_building(col, x0, y0, z0, w=30.0, d=12.0, floors=20, fh=3.15, seed=1, name='House'):
    """панельная многоэтажка: корпус, окна (часть светится тёплым), балконы, крыша с надстройкой"""
    rnd = random.Random(seed)
    H = floors * fh
    wall = E.mat('HouseWall', '#E7E1D6', rough=0.8)
    stripe = E.mat('HouseStripe', '#B9584A', rough=0.7)
    glass = E.mat('HouseGlass', '#3B4C5E', rough=0.15, metal=0.3)
    warm = E.mat('HouseWarm', '#FFD9A0', rough=0.4, emit=3.0)
    bm = bmesh.new()
    E.bm_box(bm, (x0, y0, z0), (x0 + w, y0 + d, z0 + H), 0)
    E.bm_box(bm, (x0 + w * 0.35, y0 + 2, z0 + H), (x0 + w * 0.65, y0 + d - 2, z0 + H + 2.6), 0)
    for f in range(floors):
        z = z0 + f * fh
        E.bm_box(bm, (x0 - 0.05, y0 - 0.06, z + 2.9), (x0 + w + 0.05, y0 + 0.02, z + 3.15), 1)
    ob = E.obj_from_bm(bm, name, [wall, stripe], col)
    bw = bmesh.new()
    bl = bmesh.new()
    nx = int(w / 3.0)
    for f in range(floors):
        z = z0 + f * fh + 0.9
        for i in range(nx):
            x = x0 + 0.9 + i * (w - 1.8) / max(1, nx - 1) - 0.7
            mi = 1 if rnd.random() < 0.28 else 0
            E.bm_box(bw, (x, y0 - 0.05, z), (x + 1.4, y0 + 0.02, z + 1.5), mi)
            if i % 3 == 1 and f > 0:
                E.bm_box(bl, (x - 0.3, y0 - 1.1, z - 0.9), (x + 1.7, y0 - 0.02, z - 0.75), 0)
                E.bm_box(bl, (x - 0.3, y0 - 1.1, z - 0.75), (x + 1.7, y0 - 1.0, z + 0.1), 0)
    E.obj_from_bm(bw, name + 'Win', [glass, warm], col)
    E.obj_from_bm(bl, name + 'Balc', [E.mat('HouseBalc', '#CFC7B8', rough=0.8)], col)
    return ob, H


def car(col, loc, rot_z=0.0, colr='#C0392B', name='Car'):
    bm = bmesh.new()
    E.bm_box(bm, (-2.2, -0.9, 0.25), (2.2, 0.9, 0.95), 0)
    E.bm_box(bm, (-1.2, -0.82, 0.95), (1.0, 0.82, 1.45), 1)
    for sx in (-1.4, 1.4):
        for sy in (-0.85, 0.85):
            E.bm_cyl(bm, Vector((sx, sy, 0.33)), 0.33, 0.22, 'Y', 16, 2)
    ob = E.obj_from_bm(bm, name, [E.mat('Car' + colr, colr, rough=0.25, coat=0.8),
                                  E.mat('CarGlass', '#1C2630', rough=0.1, metal=0.4),
                                  E.mat('CarTyre', '#151515', rough=0.8)], col, loc=loc, smooth=True)
    ob.rotation_euler = (0, 0, rot_z)
    return ob


def tree(col, loc, h=6.0, seed=0):
    rnd = random.Random(seed)
    bm = bmesh.new()
    E.bm_cyl(bm, Vector((0, 0, h * 0.25)), 0.18, h * 0.5, 'Z', 10, 0)
    for k in range(4):
        r = h * rnd.uniform(0.18, 0.26)
        res = bmesh.ops.create_icosphere(bm, subdivisions=2, radius=r)
        c = Vector((rnd.uniform(-0.8, 0.8), rnd.uniform(-0.8, 0.8), h * rnd.uniform(0.6, 0.85)))
        bmesh.ops.translate(bm, verts=res['verts'], vec=c)
        for v in res['verts']:
            for f in v.link_faces:
                f.material_index = 1
    return E.obj_from_bm(bm, 'Tree', [E.mat('TreeTrunk', '#5A3E2B', rough=0.9),
                                      E.mat('TreeLeaf', ['#C9842B', '#B5502A', '#9AA33A'][seed % 3], rough=0.8)], col, loc=loc)


# ----------------------------------------------------------------------------- разрез: туннель 63 м и дом
def ground_section(rise=63.0, seed=2):
    """Разрез земли (срез по плоскости y=0, камера с -Y). Наклонный туннель с тремя эскалаторами от вестибюля
    на поверхности до станции на глубине; рядом на поверхности дом в 20 этажей = высота подъёма."""
    col = E.coll('Section')
    rnd = random.Random(seed)
    L = rise / math.sin(math.radians(30))
    run = L * math.cos(math.radians(30))
    # земля: слои; вырезы (туннель, шахта к вестибюлю, зал станции) делаем колонками, без boolean
    layers = [('#6B4A2F', 0, 4), ('#8A6A45', 4, 15), ('#A88A5C', 15, 30), ('#7D7468', 30, 48), ('#5E5953', 48, 90)]
    tun_r = 4.2
    def zc0(x):
        return -6.0 - x * math.tan(math.radians(30))
    zst = zc0(run) - 1.0
    holes = [  # (x_from, x_to, lo(x), hi(x), y задней стенки)
        (-2.0, run + 2.0, lambda x: zc0(x) - 1.6, lambda x: zc0(x) + 1.0 + tun_r * 0.8 + 0.3, 8.6),
        (-4.0, 1.0, lambda x: -8.0, lambda x: 0.5, 8.6),
        (run - 3.0, run + 41.0, lambda x: zst - 1.5, lambda x: zst + 7.6, 12.5),
    ]
    bm = bmesh.new()
    def prism(xa, xb, ya, yb, flo, fhi, mi):
        za0, za1, zb0, zb1 = flo(xa), fhi(xa), flo(xb), fhi(xb)
        za1 = max(za0, za1); zb1 = max(zb0, zb1)
        if za1 - za0 < 1e-3 and zb1 - zb0 < 1e-3:
            return
        P = [(xa, ya, za0), (xb, ya, zb0), (xb, ya, zb1), (xa, ya, za1), (xa, yb, za0), (xb, yb, zb0), (xb, yb, zb1), (xa, yb, za1)]
        v = [bm.verts.new(p) for p in P]
        for q in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (3, 7, 6, 2), (0, 4, 7, 3), (1, 2, 6, 5)):
            bm.faces.new([v[i] for i in q]).material_index = mi
    dx = 0.5
    x = -70.0
    while x < run + 60:
        xa, xb = x, min(x + dx, run + 60)
        xm = (xa + xb) / 2
        cuts = [h for h in holes if h[0] <= xm <= h[1]]
        for li, (c, a_, b_) in enumerate(layers):
            pieces = [((lambda z: (lambda x: z))(-b_), (lambda z: (lambda x: z))(-a_))]
            inside = []
            for (h0, h1, hlo, hhi, yb) in cuts:
                nxt = []
                for (flo, fhi) in pieces:
                    lo, hi, hl, hh = flo(xm), fhi(xm), hlo(xm), hhi(xm)
                    if hh <= lo or hl >= hi:
                        nxt.append((flo, fhi)); continue
                    if hl > lo:
                        nxt.append((flo, hlo))
                    if hh < hi:
                        nxt.append((hhi, fhi))
                    inside.append(((lambda f, g: (lambda x: max(f(x), g(x))))(flo, hlo),
                                   (lambda f, g: (lambda x: min(f(x), g(x))))(fhi, hhi), yb))
                pieces = nxt
            for (flo, fhi) in pieces:
                prism(xa, xb, 0.0, 30.0, flo, fhi, li)
            for (flo, fhi, yb) in inside:
                prism(xa, xb, yb, 30.0, flo, fhi, li)
        x = xb
    earth = E.obj_from_bm(bm, 'Earth', [E.mat('Earth%d' % i, c, rough=0.95) for i, (c, a, b) in enumerate(layers)], col)
    # улица на поверхности за срезом: асфальт и тротуар (до плоскости среза ничего нет)
    bm = bmesh.new()
    E.bm_box(bm, (-70, 0.0, 0.0), (run + 60, 30, 0.02), 0)
    E.bm_box(bm, (2.0, 15.0, 0.02), (run + 60, 22.0, 0.04), 1)
    E.obj_from_bm(bm, 'Surface', [E.mat('Pavement', '#9C9A96', rough=0.9), E.mat('Asphalt', '#3A3B3E', rough=0.85)], col)
    bm = bmesh.new()
    n = 18
    xs = [i * 1.0 for i in range(int(run) + 1)]
    def zc(x):
        return -6.0 - x * math.tan(math.radians(30))
    rings = []
    for x in xs:
        ring = [bm.verts.new((x, 4.0 + tun_r * math.cos(math.pi * k / n), zc(x) + tun_r * math.sin(math.pi * k / n) * 0.8 + 1.0))
                for k in range(n + 1)]
        rings.append(ring)
    for r0, r1 in zip(rings, rings[1:]):
        for k in range(n):
            bm.faces.new([r0[k], r1[k], r1[k + 1], r0[k + 1]])
    E.obj_from_bm(bm, 'TunnelVault', [E.mat('SecVault', '#EDE6D6', rough=0.6)], col, smooth=True)
    # срез стенки туннеля на плоскости y=0: красная кромка, как у разрезанной модели
    bm = bmesh.new()
    E.bm_tube(bm, [Vector((x, 0.02, zc(x) + 1.0 - 0.6)) for x in (0, run)], 0.25, 0.25, 0)
    E.bm_tube(bm, [Vector((x, 0.02, zc(x) + 1.0 + tun_r * 0.8 + 0.4)) for x in (0, run)], 0.25, 0.25, 0)
    E.obj_from_bm(bm, 'TunnelCut', [E.mat('SecCut', '#D21F26', rough=0.5)], col)
    # три полосы ступеней (лентой, у них свой рельеф ступенек)
    bm = bmesh.new()
    steps = int(L / 0.4)
    for lane in range(3):
        y = 2.0 + lane * 2.0
        for i in range(steps):
            x = i * 0.4 * math.cos(math.radians(30))
            z = zc(x) - 0.8
            E.bm_box(bm, (x, y - 0.5, z), (x + 0.34, y + 0.5, z + 0.03), 0)
            E.bm_box(bm, (x, y - 0.5, z - 0.2), (x + 0.02, y + 0.5, z), 0)
        # поручни
        E.bm_tube(bm, [Vector((0, y - 0.6, zc(0) + 0.2)), Vector((run, y - 0.6, zc(run) + 0.2))], 0.07, 0.05, 1)
        E.bm_tube(bm, [Vector((0, y + 0.6, zc(0) + 0.2)), Vector((run, y + 0.6, zc(run) + 0.2))], 0.07, 0.05, 1)
    E.obj_from_bm(bm, 'SecSteps', [E.mat('SecStep', '#A9AFB5', rough=0.35, metal=0.8), E.mat('SecRail', '#111214', rough=0.4)], col)
    # лампы-торшеры между лентами
    bm = bmesh.new()
    for lane in range(2):
        y = 3.0 + lane * 2.0
        x = 2.0
        while x < run - 1:
            E.bm_box(bm, (x - 0.12, y - 0.12, zc(x) + 0.4), (x + 0.12, y + 0.12, zc(x) + 0.75), 0)
            x += 4.0
    E.obj_from_bm(bm, 'SecLamps', [E.mat('SecLamp', '#FFF3DC', rough=0.3, emit=12.0)], col)
    # станция внизу (зал) и вестибюль наверху
    bm = bmesh.new()
    zb = zc(run) - 1.0
    E.bm_box(bm, (run - 2, 0.3, zb - 0.4), (run + 40, 12, zb), 0)
    E.bm_box(bm, (run - 2, 0.3, zb + 6.5), (run + 40, 12, zb + 7.0), 0)
    for i in range(10):
        x = run + 3 + i * 4
        E.bm_box(bm, (x - 0.5, 5.5, zb), (x + 0.5, 6.5, zb + 6.5), 1)
    E.obj_from_bm(bm, 'Station', [E.mat('StationGranite', '#7A746E', rough=0.3), E.mat('StationMarble', '#C9BBA6', rough=0.25)], col)
    bm = bmesh.new()
    E.bm_box(bm, (-14, 0.3, 0), (0, 16, 6.0), 0)
    E.bm_box(bm, (-14.5, -0.2, 6.0), (0.5, 16.5, 6.6), 1)
    E.obj_from_bm(bm, 'Vestibule', [E.mat('VestGlass', '#BFD6E2', rough=0.08, alpha=0.35), E.mat('VestRoof', '#D9D4CC', rough=0.5)], col)
    mm = MT.M()
    _txt(col, 'M', 2.2, mm['metro_m'], loc=(-7, -0.35, 7.6), extrude=0.15, name='MetroM')
    # дом в 20 этажей рядом с вестибюлем: высота = подъём эскалатора
    hs, H = panel_building(col, run - 34, 1.0, 0.0, w=30, d=12, floors=20, fh=rise / 20.0, seed=5)
    # улица: машины, деревья, фонари
    cols = ['#C0392B', '#2C3E50', '#ECF0F1', '#16A085', '#7F8C8D', '#F1C40F', '#2980B9']
    for i in range(14):
        car(col, (5 + i * 7.5 + rnd.uniform(-1, 1), 16.8 + (i % 2) * 3.4, 0.04), 0 if i % 2 else math.pi, cols[i % len(cols)])
    for i in range(14):
        xt = -68 + i * 11 + rnd.uniform(-1, 1)
        if run - 36 < xt < run - 2 or -16 < xt < 2:
            continue
        tree(col, (xt, 3.0, 0.02), h=rnd.uniform(5, 7), seed=i)
    bm = bmesh.new()
    for i in range(9):
        x = 4 + i * 11
        E.bm_cyl(bm, Vector((x, 14.0, 3.5)), 0.08, 7.0, 'Z', 8, 0)
        E.bm_box(bm, (x - 0.1, 14.0, 6.9), (x + 0.1, 15.1, 7.05), 0)
    E.obj_from_bm(bm, 'StreetLamps', [E.mat('LampPole', '#3A3D42', rough=0.4, metal=0.7)], col)
    # высотные метки «63 м»: рядом с домом и у туннеля
    red = E.mat('SecMark', '#E21B23', rough=0.4, emit=2.0)
    bm = bmesh.new()
    E.bm_tube(bm, [Vector((run - 37.0, -0.5, 0.0)), Vector((run - 37.0, -0.5, H))], 0.25, 0.25, 0)
    E.bm_tube(bm, [Vector((run + 2, -0.5, zb)), Vector((run + 2, -0.5, 0.0))], 0.25, 0.25, 0)
    for z in (0.0, H):
        E.bm_tube(bm, [Vector((run - 38.5, -0.5, z)), Vector((run - 35.5, -0.5, z))], 0.25, 0.25, 0)
    for z in (zb, 0.0):
        E.bm_tube(bm, [Vector((run + 0.5, -0.5, z)), Vector((run + 3.5, -0.5, z))], 0.25, 0.25, 0)
    E.obj_from_bm(bm, 'HeightMarks', [red], col)
    return dict(col=col, run=run, zb=zb, H=H, zc=zc)


# ----------------------------------------------------------------------------- универмаг 1900-х
def old_store(rise=4.0):
    """Нарядный универмаг около 1900 года: деревянный эскалатор, колонны, люстры, прилавки, вывеска ESCALATOR®"""
    col = E.coll('OldStore')
    esk = E.Escalator(origin=(0, 0, 0), rise=rise, name='OldEsk', cutaway=False, machine=False, truss=True,
                      chain=False, rails=False, sprockets=False, glass=False, prints=False, land_lo=2.0, land_hi=2.0)
    wood = E.mat('OldWood', '#7A4A24', rough=0.45, coat=0.3)
    wood2 = E.mat('OldWoodDark', '#4A2A14', rough=0.4, coat=0.3)
    brass = E.mat('OldBrass', '#B8893A', rough=0.3, metal=0.9)
    # перекрасить эскалатор под дерево и латунь
    for ob in esk.col.objects:
        if ob.type != 'MESH':
            continue
        for i, m in enumerate(ob.data.materials):
            if m is None:
                continue
            if m.name.startswith(('EskAlu', 'EskSkirt', 'EskPlate', 'EskPanel', 'EskTruss')):
                ob.data.materials[i] = wood
            elif m.name.startswith(('EskYellow', 'EskComb')):
                ob.data.materials[i] = brass
            elif m.name.startswith('EskHandrail'):
                ob.data.materials[i] = wood2
            elif m.name.startswith('EskSteel'):
                ob.data.materials[i] = wood2
    P = esk.path
    # зал: паркет, стены с панелями, колонны, второй этаж-галерея
    bm = bmesh.new()
    E.bm_box(bm, (-14, -10, E.TREAD_Z - 0.2), (P.x1 + 14, 10, E.TREAD_Z), 0)
    E.bm_box(bm, (P.x1 - 0.6, -10, P.rise + E.TREAD_Z - 0.4), (P.x1 + 14, 10, P.rise + E.TREAD_Z), 0)
    E.bm_box(bm, (-14, 9.8, 0), (P.x1 + 14, 10.2, 12), 1)
    E.bm_box(bm, (-14, -10, 11.6), (P.x1 + 14, 10, 12), 1)
    E.obj_from_bm(bm, 'StoreShell', [E.mat('Parquet', '#9A6A3C', rough=0.35, coat=0.4), E.mat('StoreWall', '#E8D9B8', rough=0.7)], col)
    bm = bmesh.new()
    for i in range(7):
        x = -10 + i * 4.5
        for y in (-6.5, 6.5):
            E.bm_cyl(bm, Vector((x, y, 6)), 0.32, 12, 'Z', 20, 0)
            E.bm_box(bm, (x - 0.5, y - 0.5, 11.2), (x + 0.5, y + 0.5, 11.6), 1)
            E.bm_box(bm, (x - 0.45, y - 0.45, 0), (x + 0.45, y + 0.45, 0.5), 1)
    E.obj_from_bm(bm, 'Columns', [E.mat('OldMarble', '#EFE6D2', rough=0.25), brass], col, smooth=True)
    # прилавки с товарами, люстры
    bm = bmesh.new()
    bt = bmesh.new()
    rnd = random.Random(4)
    for i in range(6):
        x = -11 + i * 3.2
        for y in (-8.5, 8.0):
            E.bm_box(bm, (x - 1.2, y - 0.4, 0.3), (x + 1.2, y + 0.4, 1.3), 0)
            for k in range(5):
                E.bm_box(bt, (x - 1.0 + k * 0.45, y - 0.2, 1.3), (x - 0.75 + k * 0.45, y + 0.2, 1.3 + rnd.uniform(0.15, 0.45)), k % 3)
    E.obj_from_bm(bm, 'Counters', [wood], col)
    E.obj_from_bm(bt, 'Goods', [E.mat('Hatbox', '#C9A27E', rough=0.6), E.mat('Fabric', '#7A2E3A', rough=0.8),
                                E.mat('Fabric2', '#2E4A7A', rough=0.8)], col)
    bm = bmesh.new()
    for x in (-6, 1, 8, 14):
        for y in (-3, 3):
            res = bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=10, radius=0.45)
            bmesh.ops.translate(bm, verts=res['verts'], vec=Vector((x, y, 9.6)))
    E.obj_from_bm(bm, 'Chandeliers', [E.mat('OldLamp', '#FFE2B0', rough=0.3, emit=14.0)], col, smooth=True)
    # вывеска над эскалатором
    sign_m = E.mat('OldSignGold', '#D9A441', rough=0.25, metal=0.9)
    bm = bmesh.new()
    E.bm_box(bm, (-2.6, -0.06, -0.45), (2.6, 0.06, 0.45), 0)
    sx = (P.x0 + P.x1) / 2
    E.obj_from_bm(bm, 'SignBoard', [wood2], col, loc=(sx, 1.2, P.rise + 3.4))
    _txt(col, 'ESCALATOR®', 0.55, sign_m, loc=(sx, 1.12, P.rise + 3.4), extrude=0.02, name='SignTxt')
    return dict(esk=esk, col=col, path=P)


# ----------------------------------------------------------------------------- документ и штамп 1950
def stamp_doc(sc, f_hit, n):
    """лист с надписью ESCALATOR®; штамп «1950» падает на f_hit, значок ® отлетает"""
    col = E.coll('Doc')
    bm = bmesh.new()
    E.bm_box(bm, (-3, -3, -0.2), (3, 3, 0), 0)
    E.obj_from_bm(bm, 'Desk', [E.mat('DeskWood', '#6E4526', rough=0.4, coat=0.3)], col)
    bm = bmesh.new()
    E.bm_box(bm, (-0.42, -0.30, 0.0), (0.42, 0.30, 0.004), 0)
    E.obj_from_bm(bm, 'Paper', [E.mat('Paper', '#F4EEDC', rough=0.8)], col)
    ink = E.mat('Ink', '#1C1C1C', rough=0.6)
    _txt(col, 'ESCALATOR', 0.11, ink, loc=(-0.03, 0.06, 0.006), rot=(0, 0, 0), name='Word')
    reg = _txt(col, '®', 0.07, ink, loc=(0.32, 0.10, 0.006), rot=(0, 0, 0), name='Reg')
    # строки «текста» на листе
    bm = bmesh.new()
    for i in range(7):
        w = 0.62 if i % 3 else 0.48
        E.bm_box(bm, (-0.33, -0.05 - i * 0.032, 0.0045), (-0.33 + w, -0.04 - i * 0.032, 0.005), 0)
    E.obj_from_bm(bm, 'Lines', [E.mat('InkGrey', '#8C8678', rough=0.7)], col)
    red = E.mat('StampRed', '#C8102E', rough=0.6, emit=0.4)
    # оттиск: рамка + «1950», появляется в момент удара
    bm = bmesh.new()
    E.bm_box(bm, (-0.16, -0.075, 0.0), (0.16, -0.065, 0.001), 0)
    E.bm_box(bm, (-0.16, 0.065, 0.0), (0.16, 0.075, 0.001), 0)
    E.bm_box(bm, (-0.16, -0.075, 0.0), (-0.15, 0.075, 0.001), 0)
    E.bm_box(bm, (0.15, -0.075, 0.0), (0.16, 0.075, 0.001), 0)
    mark = E.obj_from_bm(bm, 'StampMark', [red], col, loc=(0.12, -0.12, 0.0055))
    mark.rotation_euler = (0, 0, math.radians(-8))
    t = _txt(col, '1950', 0.10, red, loc=(0, 0, 0.0002), rot=(0, 0, 0), name='StampTxt')
    t.parent = mark
    # сам штамп
    bm = bmesh.new()
    E.bm_box(bm, (-0.17, -0.085, 0.0), (0.17, 0.085, 0.05), 0)
    E.bm_cyl(bm, Vector((0, 0, 0.12)), 0.03, 0.14, 'Z', 16, 1)
    res = bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=10, radius=0.06)
    bmesh.ops.translate(bm, verts=res['verts'], vec=Vector((0, 0, 0.22)))
    for v in res['verts']:
        for f in v.link_faces:
            f.material_index = 1
    st = E.obj_from_bm(bm, 'Stamp', [red, E.mat('StampWood', '#5A3A22', rough=0.4, coat=0.4)], col, smooth=True)
    st.rotation_euler = (0, 0, math.radians(-8))
    for f in range(1, n + 1):
        if f < f_hit:
            u = (f - 1) / max(1, f_hit - 1)
            z = 0.55 * (1 - u * u)
        else:
            u = (f - f_hit) / 6.0
            z = 0.006 + (0.5 * min(1.0, u) ** 1.5 if f > f_hit + 2 else 0.0)
        st.location = (0.12, -0.12, z + 0.0055)
        st.keyframe_insert('location', frame=f)
        s = 0.0 if f < f_hit else 1.0
        mark.scale = (s, s, s)
        mark.keyframe_insert('scale', frame=f)
        # ® отлетает после удара
        if f <= f_hit:
            reg.location = (0.32, 0.10, 0.006); reg.rotation_euler = (0, 0, 0)
        else:
            u = (f - f_hit) / 30.0
            reg.location = (0.32 + 0.35 * u, 0.10 + 0.25 * u, 0.006 + 0.30 * u - 0.45 * u * u)
            reg.rotation_euler = (2.5 * u, 1.5 * u, 3.0 * u)
        reg.keyframe_insert('location', frame=f)
        reg.keyframe_insert('rotation_euler', frame=f)
    for ob in (st, mark, reg):
        ad = ob.animation_data
        for fc in E.iter_fcurves(ad.action):
            for kp in fc.keyframe_points:
                kp.interpolation = 'CONSTANT' if ob is mark else 'LINEAR'
    return dict(col=col)


# ----------------------------------------------------------------------------- торговый центр
def mall():
    """атриум ТЦ: две пары эскалаторов крест-накрест между тремя этажами, витрины с вывесками, световой фонарь"""
    col = E.coll('Mall')
    lvl = 5.0
    escs = []
    for k, (ox, oy, z, flip) in enumerate([(0, -1.4, 0, False), (0, 1.4, 0, True), (0, -1.4, lvl, True), (0, 1.4, lvl, False)]):
        e = E.Escalator(origin=(ox, oy, z), rise=lvl, name=f'MallEsk{k}', cutaway=False, machine=False, truss=True,
                        chain=False, rails=False, sprockets=False, glass=True, glass_truss=False, land_lo=1.6, land_hi=1.6)
        if flip:
            e.root.rotation_euler = (0, 0, math.pi)
            e.root.location = (e.path.x1 + e.path.x0, oy, z)
        escs.append(e)
    P = escs[0].path
    white = E.mat('MallWhite', '#F2F1EE', rough=0.35)
    floor_m = E.mat('MallFloor', '#D8D2C8', rough=0.15, coat=0.5)
    glass = E.mat('MallGlass', '#DDEFF5', rough=0.03, alpha=0.2)
    bm = bmesh.new()
    E.bm_box(bm, (-30, -30, E.TREAD_Z - 0.3), (40, 30, E.TREAD_Z), 0)
    for k in (1, 2):
        z = k * lvl + E.TREAD_Z
        # перекрытия с вырезом-атриумом посередине
        E.bm_box(bm, (-30, -30, z - 0.5), (P.x0 - 1.0, 30, z), 0)
        E.bm_box(bm, (P.x1 + 1.0, -30, z - 0.5), (40, 30, z), 0)
        E.bm_box(bm, (P.x0 - 1.0, -30, z - 0.5), (P.x1 + 1.0, -6, z), 0)
        E.bm_box(bm, (P.x0 - 1.0, 6, z - 0.5), (P.x1 + 1.0, 30, z), 0)
    fl = E.obj_from_bm(bm, 'MallFloors', [floor_m], col)
    bm = bmesh.new()
    for k in (1, 2):
        z = k * lvl + E.TREAD_Z
        for (a, b) in (((P.x0 - 1.0, -6), (P.x1 + 1.0, -6)), ((P.x0 - 1.0, 6), (P.x1 + 1.0, 6))):
            E.bm_box(bm, (a[0], a[1] - 0.03, z), (b[0], b[1] + 0.03, z + 1.05), 0)
    g = E.obj_from_bm(bm, 'MallRails', [glass], col)
    g.visible_shadow = False
    # витрины по периметру трёх этажей
    rnd = random.Random(9)
    names = ['КОФЕ', 'ОБУВЬ', 'КНИГИ', 'ИГРУШКИ', 'СПОРТ', 'ЦВЕТЫ', 'ЧАСЫ', 'ТЕХНИКА', 'ОДЕЖДА', 'КИНО', 'АПТЕКА', 'ПИЦЦА']
    for k in range(3):
        z = k * lvl + E.TREAD_Z
        for i in range(6):
            for side in (-1, 1):
                x = P.x0 - 6 + i * 4.2
                y = side * 13.0
                bm = bmesh.new()
                E.bm_box(bm, (x - 1.9, y - 0.1, z), (x + 1.9, y + 0.1, z + 3.4), 0)
                c = MT.AD_COLS[rnd.randrange(len(MT.AD_COLS))]
                E.obj_from_bm(bm, 'Shop', [E.mat('ShopWin' + c, c, rough=0.4, emit=0.9)], col)
                _txt(col, names[(i + k * 3 + (side > 0) * 5) % len(names)], 0.42, MT.M()['signw'],
                     loc=(x, y - side * 0.15, z + 3.0), rot=(math.pi / 2, 0, 0 if side > 0 else math.pi), name='ShopTxt')
    # световой фонарь
    bm = bmesh.new()
    E.bm_box(bm, (P.x0 - 4, -10, 3 * lvl + 0.8), (P.x1 + 4, 10, 3 * lvl + 1.0), 0)
    E.obj_from_bm(bm, 'Skylight', [E.mat('Sky', '#FFFFFF', rough=0.3, emit=1.5)], col)
    return dict(col=col, escs=escs, path=P, lvl=lvl)
