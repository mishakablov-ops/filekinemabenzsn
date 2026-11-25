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
    fnt = ImageFont.truetype(os.path.join(os.environ.get('FONT_DIR', os.path.dirname(os.path.abspath(__file__))), 'nunito-cyrillic-900.ttf'), int(170 * K))
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


if VAR == 'anime':
    # Аниме: персонаж — заливка с жёсткой тенью (2 тона, холодная тень) и тонкий контур; фон — живописный, без линий,
    # с воздушной дымкой; глубокое небо; глаза с радужкой и бликами; румянец; искорки.
    from PIL import ImageDraw
    ANI = dict(body=(0.84, 0.50, 0.26), ear=(0.58, 0.29, 0.14), nose=(0.16, 0.10, 0.11), eyew=(1.0, 1.0, 1.0),
               pupil=(0.10, 0.06, 0.06), collar=(0.22, 0.48, 0.96), tag=(1.0, 0.82, 0.28), tagtxt=(0.50, 0.28, 0.06),
               mouth=(0.40, 0.14, 0.12), grass=(0.47, 0.80, 0.33), hill1=(0.44, 0.76, 0.38), hill2=(0.58, 0.85, 0.45),
               bush=(0.95, 0.60, 0.78), bush2=(0.30, 0.62, 0.34), leaf=(0.36, 0.70, 0.34), trunk=(0.52, 0.35, 0.24),
               cloud=(1.0, 1.0, 1.0), roof=(0.88, 0.38, 0.32), wall=(0.99, 0.94, 0.84), wood=(0.74, 0.54, 0.35),
               petal=(1.0, 0.87, 0.28), petal2=(1.0, 0.64, 0.74), fcore=(1.0, 0.62, 0.22), stem=(0.32, 0.64, 0.27),
               butterfly=(1.0, 0.76, 0.22))
    CEL = {'body', 'ear', 'nose', 'collar', 'tag', 'mouth', 'butterfly', 'petal', 'petal2', 'fcore', 'stem', 'cloud'}
    col = np.zeros((256, 3), np.float32); cel = np.zeros(256, bool)
    for k, i in IDX.items():
        col[i] = ANI.get(k, (1, 0, 1)); cel[i] = k in CEL
    LB = {k: lab == i for k, i in IDX.items()}
    sky = lab == 0
    base = col[lab]
    sh = np.asarray(Image.open(os.environ['NEON_SHADE']).convert('L').resize((W, H), Image.BILINEAR)).astype(np.float32) / 255
    ref = np.percentile(sh[~sky], 92) if (~sky).any() else 1.0
    L = ndi.gaussian_filter(sh / max(ref, 1e-3), 0.8 * K)
    # граница света и тени — из прохода «только солнце» (NEON_KEY), иначе из мягкого
    if os.environ.get('NEON_KEY'):
        kk = np.asarray(Image.open(os.environ['NEON_KEY']).convert('L').resize((W, H), Image.BILINEAR)).astype(np.float32) / 255
        kk = ndi.gaussian_filter(kk / max(np.percentile(kk[~sky], 95), 1e-3), 0.7 * K)
        lit = np.clip((kk - 0.28) / 0.06 + 0.5, 0, 1)
    else:
        lit = np.clip((L - 0.52) / 0.05 + 0.5, 0, 1)
    # персонаж и мелочи: 2 тона (холодная тень), блик по кромке — третий тон
    SHT = np.array([0.64, 0.58, 0.88], np.float32)
    cel_img = base * (SHT + (1 - SHT) * lit[..., None])
    bm = LB.get('body', np.zeros_like(sky))
    t_hi = np.percentile(L[bm], 94) if bm.any() else 9.0
    hi = np.clip((L - t_hi) / 0.02 + 0.5, 0, 1) * bm * lit
    cel_img = cel_img + (np.array([1.0, 0.92, 0.78], np.float32) - cel_img) * (0.35 * hi)[..., None]
    # фон: мягкая живописная светотень + тёплый свет / холодная тень
    soft = np.clip(L, 0.15, 1.25)
    paint = base * (0.55 + 0.45 * soft)[..., None] * (1 + 0.06 * (soft - 0.8))[..., None]
    paint = paint + (np.array([0.35, 0.40, 0.75], np.float32) - paint) * (0.18 * np.clip(0.6 - soft, 0, 1) / 0.45)[..., None]
    rng_p = np.random.default_rng(3)
    tex = ndi.gaussian_filter(rng_p.normal(0, 1, (H // 4, W // 4)), 2.0)
    tex = ndi.zoom(tex, (H / tex.shape[0], W / tex.shape[1]), order=1)[:H, :W]
    paint = paint * (1 + 0.035 * tex)[..., None]
    # падающие тени на фоне — тоже чёткие, но мягче по цвету
    SHB = np.array([0.74, 0.74, 0.94], np.float32)
    paint = paint * (SHB + (1 - SHB) * lit[..., None])
    # трава: живописные пятна, привязанные к земле (мировые координаты из прохода p_####)
    pp = os.path.join(D, 'p_%04d.png' % F)
    if os.path.exists(pp):
        P3 = np.asarray(Image.open(pp)).astype(np.float32) / 65535.0
        wx, wy = (P3[..., 0] - 0.5) * 100, (P3[..., 1] - 0.5) * 100
        rg = np.random.default_rng(9)
        n1 = ndi.gaussian_filter(rg.normal(0, 1, (256, 256)), 3.0, mode='wrap'); n1 /= n1.std()
        n2 = ndi.gaussian_filter(rg.normal(0, 1, (256, 256)), 1.0, mode='wrap'); n2 /= n2.std()
        s1 = ndi.map_coordinates(n1, [wy * 9.0, wx * 9.0], order=1, mode='grid-wrap')
        s2 = ndi.map_coordinates(n2, [wy * 30.0, wx * 30.0], order=1, mode='grid-wrap')
        amp = np.exp(-np.maximum(z - 1.0, 0) / 9.0) * (LB.get('grass', 0) | LB.get('hill1', 0) | LB.get('hill2', 0))
        gv = 0.07 * s1 + 0.05 * s2 * np.exp(-np.maximum(z - 1.0, 0) / 4.0)
        paint = paint * (1 + gv * amp)[..., None]
        paint = paint + (np.array([0.80, 0.95, 0.45], np.float32) - paint) * (0.25 * np.clip(s1 - 1.2, 0, 1) * amp)[..., None]
    img = np.where(cel[lab][..., None], cel_img, paint)
    # глаза не затеняем: белки и зрачки остаются чистыми
    for k in ('eyew', 'pupil'):
        if k in LB: img = np.where(LB[k][..., None], base, img)
    # воздушная дымка по глубине (дальше — светлее и голубее)
    zz = np.where(sky, 100.0, z)
    haze = (1 - np.exp(-np.maximum(zz - 5.0, 0) / 28.0)) * 0.62
    HZ = np.array([0.80, 0.90, 1.0], np.float32)
    img = img + (HZ - img) * haze[..., None]
    # небо: глубокий синий сверху → светлый у горизонта
    rows = np.where((~sky).any(1))[0]
    first = np.argmax(~sky, axis=0).astype(np.float32); first[~(~sky).any(0)] = H
    hy = float(np.median(first))
    yy, xx = np.mgrid[0:H, 0:W]
    tsky = np.clip(yy / max(hy, 1.0), 0, 1) ** 1.6
    TOP = np.array([0.13, 0.38, 0.88], np.float32); MID = np.array([0.40, 0.66, 0.98], np.float32)
    skyc = np.where((tsky < 0.55)[..., None], TOP + (MID - TOP) * (tsky / 0.55)[..., None],
                    MID + (HZ - MID) * ((tsky - 0.55) / 0.45)[..., None])
    img = np.where(sky[..., None], skyc, img)
    # облака сцены: белые, тень сиреневая
    if 'cloud' in LB:
        cm = LB['cloud']
        cl = np.where(lit[..., None] > 0.5, np.array([1.0, 1.0, 1.0], np.float32), np.array([0.80, 0.83, 0.97], np.float32))
        img = np.where(cm[..., None], cl * 0.85 + img * 0.15, img)
    # сглаживание заливки (без зубцов на краях масок)
    img = np.stack([ndi.gaussian_filter(img[..., c], 0.6 * K) for c in range(3)], -1)
    # ---- глаза: радужка с градиентом, зрачок, два блика ----
    hl = []
    if 'eyew' in LB:
        eye_l, ne = ndi.label(LB['eyew'])
        areas = ndi.sum(LB['eyew'], eye_l, range(1, ne + 1)) if ne else []
        big = [i + 1 for i, a in enumerate(areas) if a > 0.25 * max(areas) and a > 150 * K * K]
        pm = LB.get('pupil', np.zeros_like(sky))
        nose_c = ndi.center_of_mass(LB['nose']) if LB.get('nose') is not None and LB['nose'].any() else None
        for e in big:
            em = eye_l == e
            ea = em.sum(); re_ = np.sqrt(ea / np.pi)
            ey, ex = ndi.center_of_mass(em)
            near_p = pm & ndi.binary_dilation(em, iterations=int(4 * K) + 1)
            if near_p.sum() > 20 * K * K:
                cy, cx = ndi.center_of_mass(near_p); rp = np.sqrt(near_p.sum() / np.pi)
                ri = max(rp * 1.5, re_ * 0.62)
            else:
                cy, cx = ey, ex
                if nose_c is not None:
                    dy_, dx_ = nose_c[0] - ey, nose_c[1] - ex; dn = np.hypot(dy_, dx_) + 1e-6
                    cy += dy_ / dn * re_ * 0.32; cx += dx_ / dn * re_ * 0.32
                ri = re_ * 0.62
            region = em | near_p
            d2 = (yy - cy) ** 2 + (xx - cx) ** 2
            iris = (d2 < ri ** 2) & region
            g = np.clip((yy - (cy - ri)) / (2 * ri), 0, 1)[..., None]
            irc = np.array([0.08, 0.05, 0.06], np.float32) * (1 - g) + np.array([0.62, 0.34, 0.12], np.float32) * g
            img = np.where(iris[..., None], irc, img)
            img = np.where(((d2 < (ri * 0.45) ** 2) & region)[..., None], np.array([0.04, 0.02, 0.03], np.float32), img)
            hl.append((cy, cx, ri, region))
            if near_p.sum() > 20 * K * K:
                img = np.where(near_p[..., None] & ~iris[..., None], np.array([0.08, 0.05, 0.06], np.float32), img)
    # ---- контур: только у таксы и бабочки, тонкий ----
    linek = {'body', 'ear', 'nose', 'mouth', 'eyew', 'collar', 'tag', 'butterfly'}
    lm = np.zeros(256, bool)
    for k in linek:
        if k in IDX: lm[IDX[k]] = True
    a_ink = np.clip(R * 0.45 + 0.5 - dist, 0, 1) * lm[Lnear]
    img = img * (1 - a_ink[..., None]) + np.array([0.20, 0.09, 0.07], np.float32) * a_ink[..., None]
    # блики поверх контура
    for cy, cx, ri, region in hl:
        for oy, ox, rr in ((-0.38, -0.30, 0.36), (0.42, 0.36, 0.15)):
            d2 = (yy - (cy + oy * ri)) ** 2 + (xx - (cx + ox * ri)) ** 2
            a = np.clip((rr * ri - np.sqrt(d2)) / (1.2 * K) + 0.5, 0, 1) * region
            img = img * (1 - a[..., None]) + a[..., None]
    # ---- румянец под ближним глазом ----
    if hl and 'body' in LB and 'nose' in LB and LB['nose'].any():
        cy, cx, ri, _ = max(hl, key=lambda h: h[2])
        ny, nx = ndi.center_of_mass(LB['nose'])
        by, bx = cy + 0.45 * (ny - cy) + 1.3 * ri, cx + 0.45 * (nx - cx)
        rx_, ry_ = 1.15 * ri, 0.62 * ri
        e = ((xx - bx) / rx_) ** 2 + ((yy - by) / ry_) ** 2
        a = np.clip(1 - e, 0, 1) ** 0.7 * 0.55 * LB['body']
        img = img * (1 - a[..., None]) + np.array([1.0, 0.50, 0.56], np.float32) * a[..., None]
        lay = Image.new('L', (W, H), 0); d = ImageDraw.Draw(lay)
        for i in range(3):
            x0 = bx - 0.55 * rx_ + i * 0.45 * rx_
            d.line([(x0, by + 0.35 * ry_), (x0 + 0.28 * rx_, by - 0.45 * ry_)], fill=255, width=max(2, int(3 * K)))
        st = np.asarray(lay).astype(np.float32) / 255 * LB['body'] * 0.75
        img = img * (1 - st[..., None]) + np.array([0.93, 0.33, 0.43], np.float32) * st[..., None]
    # ---- искорки вокруг (мерцают) ----
    lay = Image.new('L', (W, H), 0); d = ImageDraw.Draw(lay)
    rs = np.random.default_rng(21)
    for j in range(9):
        px, py = rs.uniform(0.08, 0.92) * W, rs.uniform(0.33, 0.62) * H
        ph = rs.uniform(0, 6.28)
        s = (14 + 16 * rs.random()) * K * max(0.0, np.sin(F * 0.22 + ph)) ** 2
        if s < 2: continue
        w_ = s * 0.18
        d.polygon([(px, py - s), (px + w_, py - w_), (px + s, py), (px + w_, py + w_), (px, py + s),
                   (px - w_, py + w_), (px - s, py), (px - w_, py - w_)], fill=255)
    sp = np.asarray(lay).astype(np.float32) / 255
    dogm = ndi.binary_dilation(np.isin(lab, [IDX[k] for k in linek if k in IDX]), iterations=int(12 * K))
    sp = sp * ~dogm
    glow = ndi.gaussian_filter(sp, 4 * K) * 1.5
    img = img + (np.array([1.0, 0.97, 0.85], np.float32) - img) * np.clip(sp + glow, 0, 1)[..., None]
    # ---- мягкое свечение светлых мест и лёгкая насыщенность ----
    br = np.clip(img.max(-1) - 0.82, 0, 1)
    small = ndi.zoom(br, 0.25, order=1); small = ndi.gaussian_filter(small, 6 * K)
    bloom = ndi.zoom(small, (H / small.shape[0], W / small.shape[1]), order=1)[:H, :W]
    img = img + bloom[..., None] * np.array([1.0, 0.95, 0.85], np.float32) * 0.6
    gray = img.mean(-1, keepdims=True); img = gray + (img - gray) * 1.08
    Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).save(OUT)
    sys.exit(0)


if VAR in ('ink', 'halftone'):
    # плоский мультик с ровным чернильным контуром: заливка цветами сцены + трубки тёмной краской
    import ast, re
    _here = os.path.dirname(os.path.abspath(__file__))
    _sp = os.environ.get('SCENE_PY') or next(p for p in (os.path.join(_here, 'scene.py'),
                                                         os.path.join(_here, '..', 'blender', 'scene.py')) if os.path.exists(p))
    src = open(_sp, encoding='utf-8').read()
    body = src[src.index('BASE = dict(') + len('BASE = dict('):src.index(')\n\n', src.index('BASE = dict('))]
    base = {k: ast.literal_eval(v) for k, v in re.findall(r'(\w+)=(\([^)]*\))', body)}
    lin = np.zeros((256, 3), np.float32)
    for k, i in IDX.items():
        lin[i] = base.get(k, (1, 0, 1))
    lin[0] = (0.98, 0.93, 0.85)
    srgb = np.where(lin <= 0.0031308, lin * 12.92, 1.055 * np.power(lin, 1 / 2.4) - 0.055)
    img = srgb[lab]
    if VAR == 'halftone':
        from PIL import ImageDraw
        paper = np.array([0.98, 0.95, 0.88], np.float32)
        img = img * 0.82 + paper * 0.18
        sh = np.asarray(Image.open(os.environ['NEON_SHADE']).convert('L').resize((W, H), Image.BILINEAR)).astype(np.float32) / 255
        ref = np.percentile(sh[lab > 0], 92) if (lab > 0).any() else 1.0
        dark = np.clip((0.74 - sh / max(ref, 1e-3)) * 2.0, 0, 1) ** 0.8
        dark[lab == IDX.get('cloud', -1)] = 0
        dark[lab == 0] = 0
        cell = 15 * K
        def screen(val, ang, scale):
            lay = Image.new('L', (W * 2, H * 2), 0); d = ImageDraw.Draw(lay)
            th = np.radians(ang); c, s_ = np.cos(th), np.sin(th)
            Rr = int(max(W, H) * 0.75 / cell) + 2
            for u in range(-Rr, Rr):
                for v in range(-Rr, Rr):
                    x = W / 2 + (u * c - v * s_) * cell; y = H / 2 + (u * s_ + v * c) * cell
                    if 0 <= x < W and 0 <= y < H:
                        r = cell * scale * np.sqrt(val[int(y), int(x)])
                        if r > 0.6:
                            d.ellipse([2 * (x - r), 2 * (y - r), 2 * (x + r), 2 * (y + r)], fill=255)
            return np.asarray(lay.resize((W, H), Image.LANCZOS)).astype(np.float32)[..., None] / 255
        m = screen(dark, 45, 0.55)
        img = img * (1 - m * 0.88) + np.array([0.10, 0.06, 0.07], np.float32) * m * 0.88
        skyv = np.where(lab == 0, 0.22, 0.0).astype(np.float32)
        m2 = screen(skyv, 15, 0.5)
        img = img * (1 - m2) + np.array([0.95, 0.55, 0.68], np.float32) * m2
        img = img * (1 + np.random.default_rng(F).normal(0, 0.025, (H, W)))[..., None]
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
