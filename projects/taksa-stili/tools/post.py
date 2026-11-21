"""Пост-обработка кадра под стиль: python post.py <style> in.png out.png"""
import sys
import numpy as np
from PIL import Image, ImageFilter, ImageDraw

style, src, dst = sys.argv[1:4]
im = Image.open(src).convert('RGB')
W, H = im.size
rng = np.random.default_rng(int(sys.argv[4]) if len(sys.argv) > 4 else 1)


def palette_quant(img, colors):
    return img.quantize(colors=colors, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).convert('RGB')


def edge_mask(img, thr=40, width=3):
    a = np.asarray(img).astype(np.int32)
    e = np.zeros(a.shape[:2], bool)
    for dy, dx in ((0, 1), (1, 0), (1, 1)):
        d = np.abs(a - np.roll(np.roll(a, dy, 0), dx, 1)).max(2)
        e |= d > thr
    m = Image.fromarray((e * 255).astype(np.uint8))
    if width > 1:
        m = m.filter(ImageFilter.MaxFilter(width))
    return m.filter(ImageFilter.GaussianBlur(0.6))


def comp(base, mask, color):
    b = np.asarray(base).astype(np.float32)
    m = np.asarray(mask).astype(np.float32)[..., None] / 255
    return Image.fromarray((b * (1 - m) + np.array(color, np.float32) * m).astype(np.uint8))


if style == 'flatline':
    out = comp(im, edge_mask(im, width=3), (30, 15, 8))

elif style == 'lineart':
    out = comp(Image.new('RGB', (W, H), (8, 8, 10)), edge_mask(im, width=3), (245, 245, 240))

elif style == 'blueprint':
    bg = Image.new('RGB', (W, H), (18, 62, 140)); d = ImageDraw.Draw(bg)
    g = W // 18
    for x in range(0, W, g): d.line([(x, 0), (x, H)], fill=(40, 90, 170), width=1)
    for y in range(0, H, g): d.line([(0, y), (W, y)], fill=(40, 90, 170), width=1)
    out = comp(bg, edge_mask(im, width=1), (225, 238, 255))

elif style == 'neonline':
    from PIL import ImageEnhance
    m = edge_mask(im, width=3)
    col = ImageEnhance.Color(ImageEnhance.Brightness(im).enhance(1.6)).enhance(3.0)
    base = comp(Image.new('RGB', (W, H), (6, 2, 16)), m, (0, 0, 0))
    a = np.asarray(base).astype(np.float32)
    mm = np.asarray(m).astype(np.float32)[..., None] / 255
    a = a + np.asarray(col).astype(np.float32) * mm
    lines = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    g1 = np.asarray(lines.filter(ImageFilter.GaussianBlur(W / 150))).astype(np.float32)
    g2 = np.asarray(lines.filter(ImageFilter.GaussianBlur(W / 50))).astype(np.float32)
    a = np.asarray(lines).astype(np.float32) + g1 * 1.5 + g2 * 1.5
    out = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))

elif style in ('pixel16', 'pixel8'):
    px = 150 if style == 'pixel16' else 90
    from PIL import ImageEnhance
    src_im = ImageEnhance.Contrast(ImageEnhance.Color(im).enhance(1.5)).enhance(1.15)
    small = src_im.resize((px, int(px * H / W)), Image.Resampling.BOX)
    small = palette_quant(small, 40 if style == 'pixel16' else 22)
    # тёмный контур в 1 пиксель по границам цветов
    sa = np.asarray(small).astype(np.int32)
    lum = sa.sum(2)
    edge = np.zeros(lum.shape, bool)
    for dy, dx in ((0, 1), (1, 0)):
        diff = np.abs(lum - np.roll(np.roll(lum, dy, 0), dx, 1)) > 150
        edge |= diff & (lum < np.roll(np.roll(lum, dy, 0), dx, 1))
    sa[edge] = (sa[edge] * 0.35).astype(np.int32)
    small = Image.fromarray(sa.clip(0, 255).astype(np.uint8))
    out = small.resize((W, H), Image.Resampling.NEAREST)

elif style == 'halftone2':
    # плоские цвета (светлее, как печать) + чёрный растр в тенях по мягкому рендеру + контур
    shade = Image.open(sys.argv[5]).convert('L').resize((W, H))
    a = np.asarray(im).astype(np.float32)
    a = a * 0.8 + 255 * 0.2
    sh = np.asarray(shade).astype(np.float32) / 255
    flatl = np.asarray(im.convert('L')).astype(np.float32) / 255
    dark = np.clip((flatl - sh) * 2.2 + 0.05, 0, 1)  # где мягкий рендер темнее плоского цвета — тень
    raw = np.asarray(im).astype(np.float32)
    skyc = raw[3, W // 2]
    sky = np.abs(raw - skyc).max(2) < 12
    dark = np.where(flatl < 0.35, np.maximum(dark, 0.22), dark)
    dark[sky | (flatl > 0.9)] = 0
    cell = max(7, W // 60)
    lay = Image.new('L', (W * 2, H * 2), 0); d = ImageDraw.Draw(lay)
    th = np.radians(45); c, s_ = np.cos(th), np.sin(th)
    R = int(max(W, H) * 1.5)
    for u in range(-R, R, cell):
        for v in range(-R, R, cell):
            x = W / 2 + u * c - v * s_; y = H / 2 + u * s_ + v * c
            if 0 <= x < W and 0 <= y < H:
                r = cell * 0.58 * np.sqrt(dark[int(y), int(x)])
                if r > 0.5:
                    d.ellipse([2 * (x - r), 2 * (y - r), 2 * (x + r), 2 * (y + r)], fill=255)
    m = np.asarray(lay.resize((W, H), Image.Resampling.LANCZOS)).astype(np.float32)[..., None] / 255
    a = a * (1 - m * 0.85) + 20 * m * 0.85
    out = comp(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)), edge_mask(im, width=3), (20, 15, 15))

elif style == 'halftone':
    # CMY-растр: точки разного размера по каждому каналу под своим углом + чёрный контур по краям
    a = np.asarray(im).astype(np.float32) / 255
    cell = max(8, W // 48)
    canvas = Image.new('RGB', (W, H), (250, 245, 232))
    layers = []
    for ch, ang, ink in ((0, 15, (0, 170, 220)), (1, 75, (225, 30, 140)), (2, 0, (250, 215, 0))):
        lay = Image.new('L', (W * 2, H * 2), 0)
        d = ImageDraw.Draw(lay)
        th = np.radians(ang)
        c, s = np.cos(th), np.sin(th)
        R = int(max(W, H) * 1.5)
        for u in range(-R, R, cell):
            for v in range(-R, R, cell):
                x = W / 2 + u * c - v * s; y = H / 2 + u * s + v * c
                if 0 <= x < W and 0 <= y < H:
                    val = 1 - a[int(y), int(x), ch]
                    r = cell * 0.62 * np.sqrt(val)
                    if r > 0.4:
                        d.ellipse([2 * (x - r), 2 * (y - r), 2 * (x + r), 2 * (y + r)], fill=255)
        layers.append((lay.resize((W, H), Image.Resampling.LANCZOS), ink))
    base = np.asarray(canvas).astype(np.float32) / 255
    for lay, ink in layers:
        m = np.asarray(lay).astype(np.float32)[..., None] / 255
        inkc = np.array(ink, np.float32) / 255
        base = base * (1 - m * (1 - inkc))  # умножение красок
    # контур
    edges = im.convert('L').filter(ImageFilter.FIND_EDGES)
    e = np.asarray(edges).astype(np.float32) / 255
    e = np.clip((e - 0.12) * 4, 0, 1)[..., None]
    base = base * (1 - e * 0.85)
    out = Image.fromarray((np.clip(base, 0, 1) * 255).astype(np.uint8))

elif style == 'comic':
    # старая бумага: желтизна, зерно, лёгкий сдвиг цвета и виньетка
    im = comp(im, edge_mask(im, thr=55, width=3), (25, 15, 10))
    a = np.asarray(im).astype(np.float32) / 255
    paper = np.array([0.96, 0.90, 0.76], np.float32)
    a = a * 0.85 + 0.15 * paper
    a = a * paper * 1.04
    a[..., 0] = np.roll(a[..., 0], 2, axis=1)
    noise = rng.normal(0, 0.035, a.shape[:2])[..., None]
    a = a + noise
    yy, xx = np.mgrid[0:H, 0:W]
    vig = 1 - 0.35 * (((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
    a = a * vig[..., None]
    out = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))

elif style == 'neon':
    a = np.asarray(im).astype(np.float32) / 255
    glow = np.asarray(im.filter(ImageFilter.GaussianBlur(W / 120))).astype(np.float32) / 255
    glow2 = np.asarray(im.filter(ImageFilter.GaussianBlur(W / 40))).astype(np.float32) / 255
    a = a + glow * 1.6 + glow2 * 2.2
    out = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))

elif style == 'clay':
    out = im  # всё в рендере

else:
    out = im
out.save(dst)
