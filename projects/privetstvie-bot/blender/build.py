"""Приветствие для Telegram-бота: low-poly Аполлон (герой аватарки канала) машет рукой.

Сцена целиком из кода, бесшовный цикл 4 с (120 кадров @30). Запуск:
  python3 build.py --still 30 --out /tmp/x.png          # один кадр
  python3 build.py --frames /tmp/frames/ [--size 1080]   # все кадры (PNG), дальше ffmpeg
Работает и как модуль bpy (pip install bpy), и внутри Blender 5.x (`blender -b -P build.py -- ...`).
"""
import bpy, bmesh, math, random, sys, argparse
from mathutils import Vector, Euler, Matrix

N = 120          # кадров в цикле
TAU = math.tau
rnd = random.Random(7)


def ph(f, period=N, phase=0.0):
    """фаза 0..2pi, кратная циклу"""
    return TAU * (f / period) + phase


# ------------------------------------------------------------------ материалы
def mat(name, col, rough=0.75, metal=0.0, emit=0.0, sheen=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*col, 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    if emit:
        b.inputs['Emission Color'].default_value = (*col, 1)
        b.inputs['Emission Strength'].default_value = emit
    if sheen:
        b.inputs['Sheen Weight'].default_value = sheen
    return m


def srgb(h):
    h = h.lstrip('#')
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


M = {}


def make_mats():
    M['skin'] = mat('skin', srgb('#f6dcc8'), 0.6, sheen=0.3)
    M['blush'] = mat('blush', srgb('#f2b8a6'), 0.6)
    M['cloth'] = mat('cloth', srgb('#f3ece2'), 0.8, sheen=0.4)
    M['cloth2'] = mat('cloth2', srgb('#e9dfd1'), 0.8, sheen=0.4)
    M['hair'] = mat('hair', srgb('#f4e6cf'), 0.7)
    M['gold'] = mat('gold', srgb('#e8a63e'), 0.4, metal=0.5, emit=0.0)
    M['gold2'] = mat('gold2', srgb('#f0b850'), 0.45, metal=0.3, emit=0.1)
    M['marble'] = mat('marble', srgb('#f1e9de'), 0.7)
    M['iris'] = mat('iris', srgb('#b27a2c'), 0.3, emit=0.2)
    M['pupil'] = mat('pupil', srgb('#5a3714'), 0.3)
    M['lash'] = mat('lash', srgb('#8a5a2a'), 0.6)
    M['white'] = mat('white', (1, 1, 1), 0.2, emit=2.0)
    M['eyewhite'] = mat('eyewhite', srgb('#fffaf2'), 0.4)
    M['mouth'] = mat('mouth', srgb('#c98a78'), 0.6)


# ------------------------------------------------------------------ меш-хелперы
def obj_from_bm(name, bm, material, parent=None, flat=True):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    if isinstance(material, (list, tuple)):
        for mm in material:
            me.materials.append(mm)
    else:
        me.materials.append(material)
    for p in me.polygons:
        p.use_smooth = not flat
    if parent:
        o.parent = parent
    return o


def ico(name, r, material, sub=1, jitter=0.0, scale=(1, 1, 1), loc=(0, 0, 0), parent=None, seed=None):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=r)
    rr = random.Random(seed if seed is not None else rnd.random())
    for v in bm.verts:
        v.co = Vector((v.co.x * scale[0], v.co.y * scale[1], v.co.z * scale[2]))
        if jitter:
            v.co += Vector((rr.uniform(-1, 1), rr.uniform(-1, 1), rr.uniform(-1, 1))) * jitter * r
    o = obj_from_bm(name, bm, material, parent)
    o.location = loc
    return o


def poly_prism(name, pts2d, depth, material, parent=None):
    """плоская фигура из контура (x,z) толщиной depth по Y"""
    bm = bmesh.new()
    vs = [bm.verts.new((x, 0, z)) for x, z in pts2d]
    f = bm.faces.new(vs)
    r = bmesh.ops.extrude_face_region(bm, geom=[f])
    for v in [e for e in r['geom'] if isinstance(e, bmesh.types.BMVert)]:
        v.co.y += depth
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return obj_from_bm(name, bm, material, parent)


def empty(name, loc=(0, 0, 0), parent=None):
    e = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(e)
    e.location = loc
    if parent:
        e.parent = parent
    return e


def loft(name, rings, material, parent=None, cap=True, flat=True):
    """rings: список колец одинаковой длины (списки Vector) -> труба из квадов"""
    bm = bmesh.new()
    vv = [[bm.verts.new(p) for p in ring] for ring in rings]
    n = len(rings[0])
    for i in range(len(vv) - 1):
        for j in range(n):
            bm.faces.new((vv[i][j], vv[i][(j + 1) % n], vv[i + 1][(j + 1) % n], vv[i + 1][j]))
    if cap:
        bm.faces.new(list(reversed(vv[0])))
        bm.faces.new(vv[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return obj_from_bm(name, bm, material, parent, flat)


def ring(c, rx, ry, n=8, rot=0.0, z=None):
    out = []
    for k in range(n):
        a = TAU * k / n + rot
        out.append(Vector((c[0] + rx * math.cos(a), c[1] + ry * math.sin(a), c[2])))
    return out


def star4(name, size, material, parent=None, thin=0.18, depth=0.02):
    pts = []
    for k in range(8):
        a = TAU * k / 8 + math.pi / 2
        r = size if k % 2 == 0 else size * thin
        pts.append((r * math.cos(a), r * math.sin(a)))
    # пирамидка с двух сторон: центр выдвинут
    bm = bmesh.new()
    ring_v = [bm.verts.new((x, 0, z)) for x, z in pts]
    front = bm.verts.new((0, -depth, 0))
    back = bm.verts.new((0, depth, 0))
    for i in range(8):
        bm.faces.new((ring_v[i], ring_v[(i + 1) % 8], front))
        bm.faces.new((ring_v[(i + 1) % 8], ring_v[i], back))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return obj_from_bm(name, bm, material, parent)


def leaf(name, length, width, material, parent=None):
    bm = bmesh.new()
    a = bm.verts.new((0, 0, 0))
    b = bm.verts.new((width / 2, -width * 0.25, length * 0.45))
    c = bm.verts.new((0, 0, length))
    d = bm.verts.new((-width / 2, -width * 0.25, length * 0.45))
    e = bm.verts.new((0, width * 0.15, length * 0.45))
    for f in ((a, b, c), (a, c, d), (a, e, b), (b, e, c), (c, e, d), (d, e, a)):
        bm.faces.new(f)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return obj_from_bm(name, bm, material, parent)


def ribbon(name, path, width, material, twist_fn=None, parent=None, closed=False):
    """плоская лента вдоль точек path; ширина вдоль нормали (по умолчанию вверх)"""
    bm = bmesh.new()
    n = len(path)
    L, R = [], []
    for i, p in enumerate(path):
        t = (path[(i + 1) % n] - path[i - 1]) if closed else (path[min(i + 1, n - 1)] - path[max(i - 1, 0)])
        t.normalize()
        up = Vector((0, 0, 1))
        side = t.cross(up).normalized()
        nrm = side.cross(t).normalized()
        ang = twist_fn(i / (n if closed else n - 1)) if twist_fn else 0
        w = nrm * math.cos(ang) + side * math.sin(ang)
        wd = width(i / (n if closed else n - 1)) if callable(width) else width
        L.append(bm.verts.new(p + w * wd / 2))
        R.append(bm.verts.new(p - w * wd / 2))
    rng = range(n) if closed else range(n - 1)
    for i in rng:
        j = (i + 1) % n
        bm.faces.new((L[i], L[j], R[j], R[i]))
    bm2 = bm
    me_o = obj_from_bm(name, bm2, material, parent)
    sol = me_o.modifiers.new('s', 'SOLIDIFY')
    sol.thickness = 0.012
    return me_o


# ------------------------------------------------------------------ герой
def build_hero():
    root = empty('hero_root', (0, 0, 0))
    body = empty('body', (0, 0, 1.0), root)            # пивот на поясе: дыхание и покачивание

    # --- торс (хитон): лофт из 8-угольных колец
    rings = []
    prof = [  # z, rx, ry
        (-0.30, 0.20, 0.14), (-0.10, 0.19, 0.13), (0.10, 0.20, 0.13),
        (0.28, 0.215, 0.125), (0.40, 0.205, 0.115), (0.46, 0.14, 0.09), (0.49, 0.07, 0.06)]
    for z, rx, ry in prof:
        rings.append(ring((0, 0, z), rx, ry, 10, rot=0.1))
    torso = loft('torso', rings, M['cloth'], body)
    # плечи — лёгкие шары
    for s in (-1, 1):
        ico('shoulder', 0.085, M['cloth'], 1, 0.08, (1.1, 0.95, 0.8), (s * 0.2, 0, 0.42), body, seed=3 + s)

    # --- драпировка (гиматий) через левое плечо, с золотой каймой
    drape_rings = []
    pts = [Vector((-0.24, -0.02, 0.46)), Vector((-0.18, -0.12, 0.30)), Vector((-0.05, -0.15, 0.12)),
           Vector((0.10, -0.155, -0.05)), Vector((0.21, -0.14, -0.22)), Vector((0.25, -0.10, -0.32))]
    ribbon('drape', pts, lambda t: 0.30 - 0.08 * t, M['cloth2'], twist_fn=lambda t: 0.25, parent=body)
    trim = [p + Vector((0.035, -0.012, 0.05)) for p in pts]
    ribbon('drape_trim', trim, 0.035, M['gold'], twist_fn=lambda t: 0.25, parent=body)
    # складки на груди — 3 узкие светлые плашки
    for k in range(3):
        f = [Vector((0.02 + 0.05 * k, -0.135, 0.36 - 0.02 * k)), Vector((0.06 + 0.05 * k, -0.14, 0.12)),
             Vector((0.10 + 0.04 * k, -0.135, -0.10))]
        ribbon('fold%d' % k, f, 0.04, M['cloth'], twist_fn=lambda t: 0.6, parent=body)
    # брошь-солнце на правом плече героя (слева в кадре)
    brooch = empty('brooch', (0.17, -0.12, 0.40), body)
    s = star4('brooch_core', 0.035, M['gold'], brooch, thin=0.45, depth=0.025)
    for k in range(8):
        r = leaf('ray', 0.05, 0.016, M['gold'], brooch)
        r.rotation_euler = (math.pi / 2, TAU * k / 8, 0)
        r.rotation_mode = 'XYZ'
        r.rotation_euler = Euler((0, TAU * k / 8, 0)) .to_matrix().to_euler()
        r.matrix_basis = Matrix.Rotation(TAU * k / 8, 4, 'Y') @ Matrix.Translation((0, 0, 0.03))
    brooch.rotation_euler = (0.25, 0, 0)

    # --- шея и голова
    neck = loft('neck', [ring((0, 0, 0.44), 0.062, 0.058, 8), ring((0, 0, 0.60), 0.052, 0.05, 8)], M['skin'], body)
    head = empty('head', (0, 0.0, 0.50), body)          # пивот у основания черепа
    head.scale = (1.15, 1.15, 1.15)
    build_head(head)

    # --- правая рука героя машет (в кадре слева)
    sh = empty('r_shoulder', (-0.22, 0, 0.41), body)
    upper = loft('r_upper', [ring((0, 0, 0), 0.06, 0.06, 8), ring((0, 0, -0.26), 0.048, 0.05, 8)],
                 M['skin'], sh)
    # рукав хитона
    loft('r_sleeve', [ring((0, 0, 0.04), 0.085, 0.085, 9), ring((0, 0, -0.12), 0.075, 0.072, 9)], M['cloth'], sh)
    elbow = empty('r_elbow', (0, 0, -0.26), sh)
    loft('r_fore', [ring((0, 0, 0), 0.046, 0.046, 8), ring((0, 0, -0.23), 0.036, 0.032, 8)], M['skin'], elbow)
    # золотой браслет
    loft('r_cuff', [ring((0, 0, -0.17), 0.045, 0.042, 9), ring((0, 0, -0.21), 0.042, 0.039, 9)], M['gold'], elbow)
    wrist = empty('r_wrist', (0, 0, -0.235), elbow)
    build_hand(wrist)
    # левая рука вниз под драпировкой
    lsh = empty('l_shoulder', (0.22, 0, 0.41), body)
    loft('l_upper', [ring((0, 0, 0), 0.075, 0.075, 8), ring((0, 0, -0.30), 0.06, 0.06, 8)], M['cloth2'], lsh)
    lsh.rotation_euler = (0.05, -0.12, 0)
    return root


def build_hand(wrist):
    # ладонь развёрнута к камере (-Y); пальцы вдоль -Z локально (рука вверх => пальцы вверх)
    palm = ico('palm', 0.05, M['skin'], 1, 0.03, (0.9, 0.45, 1.0), (0, 0, -0.045), wrist, seed=11)
    fingers = [(-0.027, 0.07, 0.0115), (-0.009, 0.082, 0.012), (0.01, 0.077, 0.0115), (0.028, 0.062, 0.0105)]
    for i, (x, l, w) in enumerate(fingers):
        f = loft('finger%d' % i, [ring((x, 0, -0.08), w, w * 0.85, 6), ring((x * 1.7, 0, -0.08 - l), w * 0.75, w * 0.7, 6)],
                 M['skin'], wrist)
    th = empty('thumb', (-0.045, -0.01, -0.05), wrist)
    loft('thumb_m', [ring((0, 0, 0), 0.017, 0.016, 6), ring((0, 0, -0.045), 0.014, 0.013, 6)], M['skin'], th)
    th.rotation_euler = (0, 0.9, 0)


def build_head(head):
    # череп: яйцо, чуть заострённый подбородок
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=9, radius=0.13)
    for v in bm.verts:
        x, y, z = v.co
        k = 1.0
        if z < 0:  # нижняя половина уже -> подбородок
            k = 1 - 0.35 * (-z / 0.13) ** 1.5
            y = y * (1 - 0.15 * (-z / 0.13))
        v.co = Vector((x * 0.92 * k, y * 0.98 * (k if y < 0 else 1.05), z * 1.12))
        if y < -0.08 and abs(x) < 0.03 and -0.04 < z < 0.02:  # намёк на нос
            v.co.y -= 0.012
    sk = obj_from_bm('skull', bm, M['skin'], head)
    sk.location = (0, 0, 0.16)

    face = empty('face', (0, 0, 0.16), head)
    # глаза аниме: белок, радужка, зрачок, блик, верхнее веко-ресницы
    eyes = []
    for s in (-1, 1):
        e = empty('eye%d' % s, (s * 0.045, -0.118, 0.0), face)
        e.rotation_euler = (0, 0, s * 0.30)
        poly_prism('ew', [(math.cos(a) * 0.026, math.sin(a) * 0.022) for a in [TAU * k / 10 for k in range(10)]],
                   0.004, M['eyewhite'], e)
        ir = poly_prism('iris', [(math.cos(a) * 0.017, math.sin(a) * 0.021 - 0.001) for a in [TAU * k / 10 for k in range(10)]],
                        0.004, M['iris'], e)
        ir.location = (0, -0.003, 0)
        pu = poly_prism('pupil', [(math.cos(a) * 0.008, math.sin(a) * 0.011) for a in [TAU * k / 8 for k in range(8)]],
                        0.003, M['pupil'], e)
        pu.location = (0, -0.0055, 0)
        hl = poly_prism('hl', [(math.cos(a) * 0.0055 + 0.006, math.sin(a) * 0.0055 + 0.009) for a in [TAU * k / 6 for k in range(6)]],
                        0.002, M['white'], e)
        hl.location = (0, -0.0075, 0)
        lid = poly_prism('lash', [(-0.03, 0.012), (-0.02, 0.026), (0.0, 0.03), (0.022, 0.026), (0.033, 0.016),
                                  (0.022, 0.021), (0.0, 0.024), (-0.02, 0.02)], 0.004, M['lash'], e)
        lid.location = (0, -0.008, 0)
        brow = poly_prism('brow', [(-0.024, 0.042), (0.0, 0.05), (0.026, 0.046), (0.0, 0.045)], 0.003, M['hair'], e)
        brow.location = (0, -0.002, 0.004)
        # веко для моргания: пластина цвета кожи, масштаб по Z
        blink = empty('blink%d' % s, (0, -0.011, 0.028), e)
        poly_prism('lidskin', [(-0.032, 0.0), (0.034, 0.0), (0.034, -0.05), (-0.032, -0.05)], 0.003, M['skin'], blink)
        blink.scale = (1, 1, 0.0)
        eyes.append((e, blink))
        # румянец
        bl = poly_prism('blush', [(math.cos(a) * 0.016, math.sin(a) * 0.006) for a in [TAU * k / 8 for k in range(8)]],
                        0.002, M['blush'], face)
        bl.location = (s * 0.062, -0.104, -0.04)
        bl.rotation_euler = (0, 0, s * 0.45)
    # улыбка: дуга
    sm = [(-0.02, 0.0), (-0.01, -0.007), (0.0, -0.009), (0.01, -0.007), (0.02, 0.0), (0.01, -0.0035), (0.0, -0.005), (-0.01, -0.0035)]
    mo = poly_prism('smile', sm, 0.003, M['mouth'], face)
    mo.location = (0, -0.118, -0.075)
    # уши
    for s in (-1, 1):
        ico('ear', 0.025, M['skin'], 1, 0.1, (0.45, 0.6, 1.0), (s * 0.118, 0.0, -0.005), face, seed=20 + s)

    # кудри: облако комков поверх и сзади, чёлка
    hair = empty('hair', (0, 0, 0.16), head)
    rr = random.Random(42)
    count = 0
    for i in range(260):
        # равномерно по сфере
        u, v = rr.random(), rr.random()
        th = TAU * u
        phi = math.acos(2 * v - 1)
        d = Vector((math.sin(phi) * math.cos(th), math.sin(phi) * math.sin(th), math.cos(phi)))
        # оставляем: верх, затылок, бока выше ушей, чёлку
        if d.z < -0.25:
            continue
        if d.y < -0.35 and d.z < 0.42:      # лицо открыто
            continue
        if d.y < 0 and abs(d.x) > 0.7 and d.z < 0.1:   # виски у глаз открыты
            continue
        p = Vector((d.x * 0.135, d.y * 0.14, d.z * 0.155 + 0.01))
        r = rr.uniform(0.028, 0.045)
        o = ico('curl', r, M['hair'], 1, 0.22, (1, 1, 0.8), p * 1.0, hair, seed=100 + i)
        o.rotation_euler = (rr.uniform(0, 3), rr.uniform(0, 3), rr.uniform(0, 3))
        count += 1
    # чёлка — несколько вытянутых прядей на лоб
    for i, x in enumerate((-0.07, -0.035, 0.0, 0.04, 0.075)):
        o = ico('fringe', 0.03, M['hair'], 1, 0.15, (0.8, 0.6, 1.3), (x, -0.118, 0.065 - 0.01 * abs(x) / 0.07), hair, seed=300 + i)
        o.rotation_euler = (0.3, x * 3, x * 2)
    # прядки-спиральки торчат
    for i in range(10):
        a = TAU * i / 10
        o = leaf('spike', 0.06, 0.03, M['hair'], hair)
        o.matrix_basis = (Matrix.Translation((0.13 * math.cos(a), 0.12 * math.sin(a) + 0.02, 0.07)) @
                          Matrix.Rotation(-a + math.pi / 2, 4, 'Z') @ Matrix.Rotation(1.2, 4, 'X'))

    # лавровый венок: два полукольца листьев от висков к центру лба
    wreath = empty('wreath', (0, 0, 0.17), head)
    rx, ry = 0.15, 0.155
    for side in (-1, 1):
        for k in range(9):
            t = k / 8
            a = -math.pi / 2 + side * (0.25 + 2.5 * t)     # от лба (−Y) назад
            pos = Vector((rx * math.cos(a), ry * math.sin(a), 0.035 + 0.02 * math.sin(t * math.pi)))
            for j, off in enumerate((-0.45, 0.45)):
                lf = leaf('laurel', 0.07, 0.03, M['gold'], wreath)
                tang = Vector((-math.sin(a), math.cos(a), 0)) * -side
                outw = Vector((math.cos(a), math.sin(a), 0))
                axis = (tang + outw * off * 0.9 + Vector((0, 0, 0.45))).normalized()
                q = Vector((0, 0, 1)).rotation_difference(axis)
                lf.matrix_basis = Matrix.Translation(pos) @ q.to_matrix().to_4x4()
    # лучи-шипы короны (как на аватарке)
    for i, a in enumerate((-2.2, -1.75, -1.3, -0.85, 0.7, 1.15)):
        sp = leaf('crownray', 0.10, 0.035, M['gold2'], wreath)
        aa = a - math.pi / 2
        p = Vector((0.16 * math.cos(aa), 0.16 * math.sin(aa), 0.06))
        axis = (Vector((math.cos(aa), math.sin(aa), 0)) * 0.8 + Vector((0, 0, 0.75))).normalized()
        sp.matrix_basis = Matrix.Translation(p) @ Vector((0, 0, 1)).rotation_difference(axis).to_matrix().to_4x4()
    head['eyes'] = [e.name for e, b in eyes]


# ------------------------------------------------------------------ окружение
def build_world():
    sc = bpy.context.scene
    w = bpy.data.worlds.new('w')
    sc.world = w
    w.use_nodes = True
    nt = w.node_tree
    bg = nt.nodes['Background']
    lp = nt.nodes.new('ShaderNodeLightPath')
    mix = nt.nodes.new('ShaderNodeMixShader')
    b2 = nt.nodes.new('ShaderNodeBackground')
    bg.inputs[0].default_value = (*srgb('#fff4e4'), 1)
    bg.inputs[1].default_value = 0.45
    b2.inputs[0].default_value = (*srgb('#fffaf3'), 1)
    b2.inputs[1].default_value = 1.0
    out = nt.nodes['World Output']
    nt.links.new(bg.outputs[0], mix.inputs[1])
    nt.links.new(b2.outputs[0], mix.inputs[2])
    nt.links.new(lp.outputs['Is Camera Ray'], mix.inputs[0])
    nt.links.new(mix.outputs[0], out.inputs[0])

    sun = bpy.data.lights.new('sun', 'SUN')
    sun.energy = 3.8
    sun.color = srgb('#fff1dc')
    sun.angle = 0.2
    so = bpy.data.objects.new('sun', sun)
    sc.collection.objects.link(so)
    so.rotation_euler = (math.radians(50), math.radians(-25), math.radians(-30))
    fill = bpy.data.lights.new('fill', 'AREA')
    fill.energy = 70
    fill.size = 3
    fill.color = srgb('#ffe2b8')
    fo = bpy.data.objects.new('fill', fill)
    sc.collection.objects.link(fo)
    fo.location = (1.6, -1.8, 1.6)
    fo.rotation_euler = (math.radians(60), 0, math.radians(40))

    # пол-облако: белые низкополигональные холмы под краем кадра
    for i in range(14):
        x = -2.2 + i * 0.34
        ico('cloud', rnd.uniform(0.25, 0.42), M['marble'], 1, 0.25, (1.3, 0.8, 0.6),
            (x, rnd.uniform(0.6, 1.6), rnd.uniform(0.25, 0.45)), seed=500 + i)

    # колонны и арки сзади
    def column(x, y, h, broken=False):
        base = empty('col', (x, y, 0.2))
        loft('shaft', [ring((0, 0, 0), 0.09, 0.09, 8), ring((0, 0, h), 0.08, 0.08, 8)], M['marble'], base)
        ico('capital', 0.12, M['marble'], 0, 0.0, (1.1, 1.1, 0.4), (0, 0, h + 0.02), base, seed=1)
        ico('basecap', 0.12, M['marble'], 0, 0.0, (1.1, 1.1, 0.35), (0, 0, 0.02), base, seed=2)
        if broken:
            ico('chip', 0.09, M['marble'], 0, 0.3, (1, 1, 0.6), (0, 0, h + 0.12), base, seed=3)
        return base
    for x, y, h, br in ((-1.55, 2.6, 2.2, False), (-1.05, 3.4, 1.9, True), (1.2, 2.8, 2.0, False),
                        (1.75, 3.6, 2.4, True), (0.65, 4.2, 1.6, False), (-0.6, 4.6, 1.5, False)):
        column(x, y, h, br)
    # перемычка между колоннами справа
    ico('lintel', 0.3, M['marble'], 0, 0.0, (1.7, 0.4, 0.2), (1.45, 3.2, 2.45), seed=4)
    ico('lintel', 0.3, M['marble'], 0, 0.0, (1.5, 0.4, 0.2), (-1.3, 3.0, 2.3), seed=5)

    anim = []
    # летающие кристаллы (октаэдры, крутятся на 90° за цикл)
    for i, (x, y, z, r) in enumerate(((-1.6, 1.8, 2.25, 0.13), (1.35, 1.6, 1.85, 0.11), (-0.95, 1.2, 0.95, 0.07),
                                      (1.05, 1.0, 1.15, 0.06), (0.55, 2.6, 2.35, 0.09), (-1.7, 2.8, 1.4, 0.1))):
        bm = bmesh.new()
        top = bm.verts.new((0, 0, r * 1.5)); bot = bm.verts.new((0, 0, -r * 1.9))
        mid = [bm.verts.new((r * math.cos(TAU * k / 4), r * math.sin(TAU * k / 4), 0)) for k in range(4)]
        for k in range(4):
            bm.faces.new((mid[k], mid[(k + 1) % 4], top)); bm.faces.new((mid[(k + 1) % 4], mid[k], bot))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        o = obj_from_bm('crystal', bm, M['marble'] if i % 2 else M['gold2'])
        o.location = (x, y, z)
        anim.append(('crystal', o, i))
    # звёзды-искры
    for i, (x, y, z, s) in enumerate(((-0.62, -0.05, 1.95, 0.09), (0.66, -0.1, 1.82, 0.075), (-0.95, 0.5, 1.45, 0.06),
                                      (0.92, 0.3, 1.35, 0.1), (-0.35, 0.8, 2.25, 0.05), (0.38, 0.6, 2.3, 0.06),
                                      (1.25, 0.9, 2.2, 0.07), (-1.3, 0.9, 1.15, 0.05))):
        o = star4('star', s, M['gold2'], thin=0.16)
        o.location = (x, y, z)
        anim.append(('star', o, i))
    # нимб-кольцо за головой (12 лучей, поворот на 30° за цикл)
    halo = empty('halo', (0, 0.32, 1.78))
    ring_pts = ring((0, 0, 0), 0.42, 0.42, 48)
    ring_pts = [Vector((p.x, 0, p.y)) for p in ring_pts]
    rb = ribbon('halo_ring', ring_pts, 0.018, M['gold2'], twist_fn=lambda t: math.pi / 2, parent=halo, closed=True)
    for k in range(12):
        a = TAU * k / 12
        st = star4('halo_star', 0.05 if k % 3 else 0.09, M['gold2'], halo, thin=0.16, depth=0.01)
        st.location = (0.42 * math.cos(a), 0, 0.42 * math.sin(a))
        st.hide_render = k % 3 != 0
    anim.append(('halo', halo, 0))
    # золотые ленты: кольцо вокруг героя с тремя волнами, поворот на 120° за цикл
    ribs = []
    for j, (z, rr_, tilt, wid) in enumerate(((1.12, 0.62, 0.10, 0.055),)):
        piv = empty('ribbon_piv', (0, 0.05, z))
        pts = []
        for k in range(96):
            a = TAU * k / 96
            pts.append(Vector((rr_ * math.cos(a), rr_ * math.sin(a), 0.07 * math.sin(3 * a + j))))
        spin = empty('ribbon_spin', (0, 0, 0), piv)     # вращение вокруг своей оси, наклон — у родителя
        rbn = ribbon('ribbon', pts, lambda t: wid * (0.65 + 0.35 * math.sin(3 * TAU * t)), M['gold'],
                     twist_fn=lambda t: 0.5 * math.sin(3 * TAU * t), parent=spin, closed=True)
        piv.rotation_euler = (tilt, 0.15 * (1 if j else -1), 0)
        piv.scale = (1, 0.75, 1)          # эллипс даёт масштаб родителя, сама лента круглая -> поворот бесшовный
        anim.append(('ribbon', spin, j))
    # широкие диагональные ленты на фоне
    for j, (z0, z1, y) in enumerate(((0.6, 2.4, 1.5), (2.3, 0.9, 2.2))):
        pts = [Vector((-2.4 + 4.8 * t, y + 0.3 * math.sin(t * 5), z0 + (z1 - z0) * t + 0.25 * math.sin(t * 6 + j)))
               for t in [i / 40 for i in range(41)]]
        ribbon('bgribbon', pts, 0.16 if j == 0 else 0.1, M['gold'], twist_fn=lambda t: 0.9 * math.sin(t * 7),)
    return anim


# ------------------------------------------------------------------ анимация (покадрово, бесшовно)
def animate(anim):
    sc = bpy.context.scene
    O = bpy.data.objects
    body, head = O['body'], O['head']
    sh, el, wr = O['r_shoulder'], O['r_elbow'], O['r_wrist']
    bl = [O['blink-1'], O['blink1']]
    base = {}
    for kind, o, i in anim:
        base[o.name] = (o.location.copy(), o.rotation_euler.copy(), o.scale.copy())
    for f in range(N + 1):
        sc.frame_set(f)
        t = f / N
        # дыхание + покачивание корпуса
        body.scale = (1, 1, 1 + 0.012 * math.sin(ph(f, 60)))
        body.rotation_euler = (0.0, 0.025 * math.sin(ph(f, 120)), -0.05 + 0.02 * math.sin(ph(f, 120)))
        body.keyframe_insert('scale'); body.keyframe_insert('rotation_euler')
        # голова: лёгкий наклон к машущей руке, кивок
        head.rotation_euler = (0.05 + 0.03 * math.sin(ph(f, 60, 1)), -0.10 + 0.04 * math.sin(ph(f, 120, 0.5)),
                               0.10 + 0.04 * math.sin(ph(f, 120)))
        head.keyframe_insert('rotation_euler')
        # рука поднята, предплечье машет: 5 взмахов за 4 с
        sh.rotation_euler = (-0.25, 2.2 + 0.04 * math.sin(ph(f, 24)), 0.0)
        el.rotation_euler = (0.0, 0.75 + 0.30 * math.sin(ph(f, 24)), 0.0)
        wr.rotation_euler = (0.0, 0.18 * math.sin(ph(f, 24, -0.9)), 0.0)
        for o in (sh, el, wr):
            o.keyframe_insert('rotation_euler')
        # моргание на кадрах 70–76
        k = 0.0
        if 70 <= f <= 76:
            k = math.sin(math.pi * (f - 70) / 6)
        for b in bl:
            b.scale = (1, 1, max(k, 0.0001))
            b.keyframe_insert('scale')
        for kind, o, i in anim:
            loc, rot, scl = base[o.name]
            if kind == 'crystal':
                o.location = loc + Vector((0, 0, 0.05 * math.sin(ph(f, 120, i * 1.3))))
                o.rotation_euler = (rot.x, rot.y, rot.z + (TAU / 4) * t)
            elif kind == 'star':
                s = 0.75 + 0.35 * math.sin(ph(f, 60, i * 1.7))
                o.scale = (s, s, s)
                o.rotation_euler = (0, (TAU / 4) * t * (1 if i % 2 else -1), 0)
            elif kind == 'halo':
                o.rotation_euler = (0, (TAU / 4) * t, 0)   # видны 4 звезды через 90°
            elif kind == 'ribbon':
                o.rotation_euler = (rot.x, rot.y, (TAU / 3) * t * (1 if i else -1))
            o.keyframe_insert('location'); o.keyframe_insert('rotation_euler'); o.keyframe_insert('scale')
    for a in bpy.data.actions:
        for fc in getattr(a, 'fcurves', []):
            for kp in fc.keyframe_points:
                kp.interpolation = 'LINEAR'


def setup(size, engine, samples):
    sc = bpy.context.scene
    cam = bpy.data.cameras.new('cam')
    co = bpy.data.objects.new('cam', cam)
    sc.collection.objects.link(co)
    sc.camera = co
    co.location = CAM[0]
    tgt = Vector(CAM[1])
    co.rotation_euler = (tgt - co.location).to_track_quat('-Z', 'Y').to_euler()
    cam.lens = 50
    cam.dof.use_dof = True
    cam.dof.focus_distance = (Vector(CAM[0]) - Vector((0, 0, 1.6))).length
    cam.dof.aperture_fstop = 4.0
    sc.render.resolution_x = size
    sc.render.resolution_y = size
    sc.render.fps = 30
    sc.frame_start, sc.frame_end = 0, N - 1
    sc.render.engine = engine
    sc.view_settings.view_transform = 'Standard'
    sc.view_settings.look = 'None'
    sc.view_settings.exposure = 0.0
    if engine == 'CYCLES':
        sc.cycles.samples = samples
        sc.cycles.use_denoising = True
        sc.cycles.device = 'CPU'
    else:
        sc.eevee.taa_render_samples = samples
        sc.eevee.use_shadows = True
        try:
            sc.eevee.use_raytracing = True
        except Exception:
            pass
    sc.render.film_transparent = False


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser()
    ap.add_argument('--still', type=int, nargs='*')
    ap.add_argument('--frames')
    ap.add_argument('--out', default='/tmp/still.png')
    ap.add_argument('--size', type=int, default=1080)
    ap.add_argument('--engine', default='BLENDER_EEVEE')
    ap.add_argument('--samples', type=int, default=32)
    ap.add_argument('--save')
    ap.add_argument('--cam', default='main')
    a = ap.parse_args(argv)
    global CAM
    CAM = {'main': ((0.0, -2.05, 1.62), (0.0, 0.0, 1.5)), 'face': ((0.0, -0.9, 1.78), (0.0, 0.0, 1.74)),
           'wide': ((0.0, -3.4, 1.62), (0.0, 0.0, 1.45))}[a.cam]
    bpy.ops.wm.read_factory_settings(use_empty=True)
    make_mats()
    build_hero()
    anim = build_world()
    animate(anim)
    setup(a.size, a.engine, a.samples)
    sc = bpy.context.scene
    if a.save:
        bpy.ops.wm.save_as_mainfile(filepath=a.save)
    if a.still is not None:
        for f in a.still:
            sc.frame_set(f)
            sc.render.filepath = a.out.replace('#', '%03d' % f)
            bpy.ops.render.render(write_still=True)
    if a.frames:
        sc.render.filepath = a.frames.rstrip('/') + '/f_###'
        sc.render.image_settings.file_format = 'PNG'
        bpy.ops.render.render(animation=True)


if __name__ == '__main__':
    main()
