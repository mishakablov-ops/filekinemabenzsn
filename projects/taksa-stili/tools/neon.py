"""Неон из проходов ID + глубина (scene.py ids): ровные трубки одной толщины, белая сердцевина,
цветной ореол, отсвет на стене. python neon.py <ids_dir> <frame> <out.png> [variant] [on=1.0] [seed]

variant: wall  — вывеска на тёмной кирпичной стене (собака главная, фон тонкими трубками)
         night — ночная полянка: трубки + слабая заливка цветом, свет от трубок на объектах
         mono  — одна линия одного цвета (минимализм)
on: 0..1 — доля «включившихся» трубок (для анимации включения вывески).
"""
import json, sys
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from skimage.morphology import skeletonize, remove_small_objects

D, F, OUT = sys.argv[1], int(sys.argv[2]), sys.argv[3]
VAR = sys.argv[4] if len(sys.argv) > 4 else 'wall'
ON = float(sys.argv[5]) if len(sys.argv) > 5 else 1.0
SEED = int(sys.argv[6]) if len(sys.argv) > 6 else 0

IDX = json.load(open(f'{D}/ids.json'))
lab = np.asarray(Image.open(f'{D}/id_{F:04d}.png'))[..., 0].astype(np.int32)
z = np.asarray(Image.open(f'{D}/z_{F:04d}.png')).astype(np.float32) / 65535 * 100
H, W = lab.shape
K = W / 1080.0  # масштаб под разрешение

# ---------- палитра: 3 семьи цветов, а не радуга ----------
HOT = (1.0, 0.30, 0.55)    # собака — розово-коралловый
WARM = (1.0, 0.62, 0.18)   # тёплые акценты
COOL = (0.15, 0.75, 1.0)   # окружение — голубой
MINT = (0.25, 1.0, 0.65)   # трава/холмы
WHITE = (0.92, 0.95, 1.0)
PAL = dict(body=HOT, ear=HOT, nose=HOT, mouth=HOT, eyew=WHITE, pupil=WHITE, collar=COOL, tag=WARM, tagtxt=WARM,
           hill1=MINT, hill2=MINT, grass=MINT, bush=COOL, bush2=MINT, leaf=MINT, trunk=WARM, cloud=COOL,
           roof=WARM, wall=WARM, wood=WARM, petal=WARM, petal2=HOT, fcore=WARM, stem=MINT, butterfly=WARM)
DOG = {'body', 'ear', 'nose', 'mouth', 'eyew', 'pupil', 'collar', 'tag'}
SKIP = {'tagtxt', 'fcore', 'pupil'}
FILL = {'nose'}
if VAR == 'mono':
    PAL = {k: HOT for k in PAL}
inv = {v: k for k, v in IDX.items()}
pal_arr = np.zeros((256, 3), np.float32)
is_dog = np.zeros(256, bool); skip = np.zeros(256, bool); fill_l = np.zeros(256, bool)
for k, i in IDX.items():
    pal_arr[i] = PAL.get(k, WHITE); is_dog[i] = k in DOG; skip[i] = k in SKIP; fill_l[i] = k in FILL
if VAR == 'sign':
    skip |= ~is_dog; skip[0] = True

# ---------- границы: смена материала или скачок глубины; линия принадлежит ближнему объекту ----------
B = np.zeros((H, W), bool); BL = np.zeros((H, W), np.int32)
for dy, dx in ((0, 1), (1, 0), (1, 1), (1, -1)):
    l2 = np.roll(np.roll(lab, -dy, 0), -dx, 1); z2 = np.roll(np.roll(z, -dy, 0), -dx, 1)
    jump = np.abs(z - z2) > np.maximum(0.06 * np.minimum(z, z2), 0.04)
    edge = (lab != l2) | jump
    near_here = z <= z2
    m1 = edge & near_here & (lab > 0)
    B |= m1; BL = np.where(m1, lab, BL)
    # пиксель-сосед ближе — помечаем его
    m2 = edge & ~near_here & (l2 > 0)
    m2s = np.roll(np.roll(m2, dy, 0), dx, 1)
    l2s = np.roll(np.roll(l2 * m2, dy, 0), dx, 1)
    B |= m2s; BL = np.where(m2s & (BL == 0), l2s, BL)
B[:2] = B[-2:] = False; B[:, :2] = B[:, -2:] = False
B &= ~skip[BL]

# ---------- чистка: тонкий скелет, без мусора ----------
S = skeletonize(B)
S = remove_small_objects(S, max_size=int(70 * K), connectivity=2)
import os
TXT = 255
TEXT = os.environ.get('NEON_TEXT', '')
# метка у каждого пикселя скелета (ближайшая из границы)
_, (iy, ix) = ndi.distance_transform_edt(~B, return_indices=True)
SL = np.where(S, BL[iy, ix], 0)

if TEXT:
    from PIL import ImageDraw, ImageFont
    fnt = ImageFont.truetype(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'nunito-cyrillic-900.ttf'), int(170 * K))
    tm = Image.new('L', (W, H), 0); dr = ImageDraw.Draw(tm)
    dr.text((W / 2, H * float(os.environ.get('NEON_TEXT_Y', '0.71'))), TEXT, font=fnt, fill=255, anchor='mm')
    TS = skeletonize(np.asarray(tm) > 128)
    TS = remove_small_objects(TS, max_size=int(10 * K), connectivity=2)
    S = S | TS; SL = np.where(TS, TXT, SL); pal_arr[TXT] = COOL; is_dog[TXT] = True
    z = np.where(TS, 3.0, z)
# ---------- толщина трубки по глубине: ближе — толще; собака всегда толще фона ----------
zs = np.where(S, z, 0)
r_all = np.clip(2.6 * K * (3.2 / np.maximum(zs, 0.5)) ** 0.6, 1.4 * K, 6.0 * K)
r_all = np.where(is_dog[SL], np.maximum(r_all, 4.2 * K), r_all * 0.8)
bright = np.where(is_dog[SL], 1.0, 0.55)

# включение трубок по группам (для анимации): каждая компонента загорается в своё время
if ON < 1.0:
    # время включения стабильно от кадра к кадру: части собаки по своим меткам, надпись, потом фон волной слева направо
    ORDER = {'body': 0.04, 'ear': 0.10, 'mouth': 0.13, 'eyew': 0.15, 'nose': 0.17, 'collar': 0.19, 'tag': 0.22}
    t_lab = np.full(256, 2.0)
    for k, v in ORDER.items():
        if k in IDX: t_lab[IDX[k]] = v
    t_lab[TXT] = 0.33
    tpix = t_lab[SL]
    envm = S & ~is_dog[SL]
    comp, n = ndi.label(envm, structure=np.ones((3, 3)))
    if n:
        cx = np.array([c[1] for c in ndi.center_of_mass(envm, comp, range(1, n + 1))])
        t_env = np.concatenate([[2.0], 0.45 + 0.45 * np.clip(cx / W, 0, 1)])
        tpix = np.where(envm, t_env[comp], tpix)
    dt = ON - tpix
    fl = np.where(dt > 0.12, 1.0, np.where((np.floor(dt * 60).astype(np.int64) % 3) != 0, 1.0, 0.15))
    bright = bright * np.where(dt < 0, 0.0, fl)

dist, (jy, jx) = ndi.distance_transform_edt(~S, return_indices=True)
R = r_all[jy, jx]; Lnear = SL[jy, jx]; Bn = bright[jy, jx]
C = pal_arr[Lnear]
tube = np.clip(R + 0.5 - dist, 0, 1) * Bn
core = np.clip(R * 0.38 + 0.5 - dist, 0, 1) * Bn

FM = ndi.binary_erosion(fill_l[lab], iterations=int(2 * K))
# зрачок — круглая точка в центре области зрачка
pm = lab == IDX.get('pupil', -1)
if pm.any():
    pl, pn = ndi.label(pm)
    yy0, xx0 = np.mgrid[0:H, 0:W]
    for cy, cx in ndi.center_of_mass(pm, pl, range(1, pn + 1)):
        if (pl == 0).all(): break
        FM |= (yy0 - cy) ** 2 + (xx0 - cx) ** 2 < (9 * K) ** 2
    lab = np.where(FM & pm, IDX['pupil'], lab)
if ON < 1.0:
    FM = FM & (ON > 0.25)
fillm = ndi.gaussian_filter(FM.astype(np.float32), 0.8 * K)
C = np.where(fillm[..., None] > tube[..., None], pal_arr[lab], C)
tube = np.maximum(tube, fillm); core = np.maximum(core, 0.3 * np.clip(ndi.gaussian_filter((ndi.binary_erosion(FM, iterations=int(5 * K))).astype(np.float32), 1.5 * K), 0, 1))
E = C * tube[..., None] * 1.1 + (C * 0.35 + 0.9) * core[..., None] * 1.2


if VAR == 'ink':
    # плоский мультик с ровным чернильным контуром: заливка цветами сцены + трубки тёмной краской
    import ast, re
    src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scene.py'), encoding='utf-8').read()
    body = src[src.index('BASE = dict(') + len('BASE = dict('):src.index(')\n\n', src.index('BASE = dict('))]
    base = {k: ast.literal_eval(v) for k, v in re.findall(r'(\w+)=(\([^)]*\))', body)}
    lin = np.zeros((256, 3), np.float32)
    for k, i in IDX.items():
        lin[i] = base.get(k, (1, 0, 1))
    lin[0] = (0.98, 0.93, 0.85)
    srgb = np.where(lin <= 0.0031308, lin * 12.92, 1.055 * np.power(lin, 1 / 2.4) - 0.055)
    img = srgb[lab]
    a_ink = np.clip(R * 0.75 + 0.5 - dist, 0, 1)
    ink = np.array([0.12, 0.06, 0.04], np.float32)
    img = img * (1 - a_ink[..., None]) + ink * a_ink[..., None]
    Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).save(OUT)
    sys.exit(0)


def blur(img, s):
    # широкое размытие — на уменьшенной копии, быстро
    f = max(1, int(s // 6))
    if f > 1:
        small = img[::f, ::f]
        sm = np.stack([ndi.gaussian_filter(small[..., c], s / f) for c in range(3)], -1)
        up = np.stack([ndi.zoom(sm[..., c], (H / sm.shape[0], W / sm.shape[1]), order=1) for c in range(3)], -1)
        return up[:H, :W]
    return np.stack([ndi.gaussian_filter(img[..., c], s) for c in range(3)], -1)


G1 = blur(E, 3.0 * K); G2 = blur(E, 14 * K); G3 = blur(E, 55 * K)

# ---------- фон ----------
rng = np.random.default_rng(5)
if VAR in ('wall', 'mono', 'sign'):
    # тёмная кирпичная стена: кирпичи 1080/9 x 1080/27, шов, шум
    bw, bh = int(120 * K), int(42 * K)
    yy, xx = np.mgrid[0:H, 0:W]
    row = yy // bh; off = (row % 2) * (bw // 2)
    bx = (xx + off) // bw
    mort = ((yy % bh) < 3 * K) | (((xx + off) % bw) < 3 * K)
    tint = rng.uniform(0.75, 1.15, (H // bh + 2, W // bw + 3))
    base = np.array([0.075, 0.055, 0.06], np.float32) * tint[row, bx][..., None]
    base = np.where(mort[..., None], np.array([0.03, 0.028, 0.032], np.float32), base)
    base = base * (1 + rng.normal(0, 0.08, (H, W)))[..., None]
    albedo = np.clip(base, 0, 1) * 5.0
    amb = 0.16
else:  # night
    fill = pal_arr[lab] * 0.10
    fill[lab == 0] = np.array([0.012, 0.01, 0.03])
    yy = np.mgrid[0:H, 0:W][0]
    sky = (lab == 0)[..., None] * np.array([0.02, 0.015, 0.06], np.float32) * (1 - yy[..., None] / H)
    albedo = fill + sky
    albedo = albedo * 3.0
    amb = 0.25

light = amb + 1.6 * G3 + 0.8 * G2
img = albedo * light + E + G1 * 0.9 + G2 * 0.7 + G3 * 0.35
# тон-маппинг с мягким плечом: сердцевины уходят в белый, как у настоящего неона
img = 1 - np.exp(-img * 1.25)
# лёгкое зерно и виньетка
img += rng.normal(0, 0.008, img.shape)
yy, xx = np.mgrid[0:H, 0:W]
vig = 1 - 0.28 * (((xx - W / 2) / (W / 2)) ** 2 + ((yy - H * 0.45) / (H * 0.6)) ** 2)
img *= vig[..., None]
Image.fromarray((np.clip(img, 0, 1) ** (1 / 1.1) * 255).astype(np.uint8)).save(OUT)
