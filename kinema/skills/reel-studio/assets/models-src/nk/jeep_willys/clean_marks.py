"""Paint out white stencil marks (US star, serial numbers) on the jeep texture, keeping the paint grain.
    python -I clean_marks.py <in.png> <out.png> <preview.png>
"""
import sys

import numpy as np
from PIL import Image, ImageFilter

src, dst, prev = sys.argv[1], sys.argv[2], sys.argv[3]
a = np.asarray(Image.open(src).convert("RGB")).astype(np.float32)
lum = a @ np.array([0.299, 0.587, 0.114], np.float32)
H, W = lum.shape

boxes = [(3110, 1930, 3260, 2500),   # hood serial, left (vertical)
         (3880, 1930, 4030, 2500),   # hood serial, right
         (3330, 2010, 3830, 2420),   # hood star in a circle
         (1990, 290, 2070, 380),     # side star 1
         (1620, 1200, 1730, 1300),   # side star 2
         (1000, 2940, 1200, 3030),   # bumper serial
         (1530, 3180, 1580, 3470)]   # strip serial (vertical)


def _box(x, r, axis):
    pad = [(0, 0)] * x.ndim
    pad[axis] = (r + 1, r)
    c = np.cumsum(np.pad(x, pad, mode="edge"), axis=axis, dtype=np.float64)
    hi = np.take(c, np.arange(2 * r + 1, c.shape[axis]), axis=axis)
    lo = np.take(c, np.arange(0, c.shape[axis] - 2 * r - 1), axis=axis)
    return ((hi - lo) / (2 * r + 1)).astype(np.float32)


def blur(x, r):
    k = max(1, int(r * 0.85))
    for _ in range(3):
        x = _box(_box(x, k, 0), k, 1)
    return x


# 1. mask = pixels clearly brighter than the panel paint inside each box, grown a little
mask = np.zeros(lum.shape, bool)
for x0, y0, x1, y1 in boxes:
    reg = lum[y0:y1, x0:x1]
    mask[y0:y1, x0:x1] |= reg > np.median(reg[reg > 30]) + 18
# worn stencil edges are barely brighter than the paint: repaint the whole star discs and number plates as well
yy, xx = np.mgrid[0:H, 0:W]
for cx, cy, r in [(3590, 2205, 185), (2030, 335, 58), (1675, 1250, 62)]:
    mask |= (xx - cx) ** 2 + (yy - cy) ** 2 < r * r
for x0, y0, x1, y1 in [(3115, 1945, 3255, 2495), (3895, 1945, 4015, 2495), (1005, 2945, 1195, 3025), (1532, 3185, 1582, 3465)]:
    mask[y0:y1, x0:x1] = True
mask &= lum > 30  # never paint the black gutters between UV islands
m_img = Image.fromarray((mask * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(1.5))
m = np.asarray(m_img).astype(np.float32)[..., None] / 255.0
hard = m[..., 0] > 0.02

# 2. paint colour from clean neighbours only (not marks, not the black gutter between UV islands)
valid = (lum > 30) & ~hard
keep = valid.astype(np.float32)[..., None]
w40, w160 = blur(keep, 40), blur(keep, 160)
low = np.where(w40 > 0.08, blur(a * keep, 40) / np.maximum(w40, 1e-3), blur(a * keep, 160) / np.maximum(w160, 1e-3))  # wide patches: wider neighbourhood
detail = a - blur(a * keep, 6) / np.maximum(blur(keep, 6), 1e-3)
clean_area = blur(keep, 6)[..., 0] > 0.97  # donor pixel and its neighbourhood are clean paint

# 3. grain borrowed from the nearest clean donor offset, so patches are not flat
fill = low.copy()
for x0, y0, x1, y1 in boxes:
    ys, xs = np.nonzero(hard[y0:y1, x0:x1])
    ys, xs = ys + y0, xs + x0
    w, h = x1 - x0, y1 - y0
    cands = [(w, 0), (-w, 0), (0, h), (0, -h), (w // 2, 0), (-w // 2, 0), (0, h // 2), (0, -h // 2),
             (w, h), (-w, -h), (w, -h), (-w, h)]
    got = np.zeros(len(ys), bool)
    det = np.zeros((len(ys), 3), np.float32)
    for dx, dy in cands:
        sy, sx = ys + dy, xs + dx
        inside = (sy >= 0) & (sy < H) & (sx >= 0) & (sx < W)
        sy, sx = np.clip(sy, 0, H - 1), np.clip(sx, 0, W - 1)
        ok = inside & clean_area[sy, sx] & ~got
        det[ok] = detail[sy[ok], sx[ok]]
        got |= ok
    fill[ys, xs] = low[ys, xs] + det * 0.9

out = np.clip(a * (1 - m) + fill * m, 0, 255).astype(np.uint8)
Image.fromarray(out).save(dst)
Image.fromarray(out).crop((3060, 1860, 4060, 2560)).save(prev)
print("cleaned px", int(hard.sum()))
