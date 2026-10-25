"""Remove the US star / serial numbers from the jeep's 512 px metallicRoughness map (they made the star glossy).
    python -I clean_mr.py <in.png> <out.png>
Regions are the same as in clean_marks.py (4096 px base colour), scaled by 1/8; each is filled with the median of a ring around it.
"""
import sys

import numpy as np
from PIL import Image

src, dst = sys.argv[1], sys.argv[2]
a = np.asarray(Image.open(src).convert("RGB")).astype(np.float32)
H, W, _ = a.shape
k = W / 4096
yy, xx = np.mgrid[0:H, 0:W]
lum = a.mean(axis=2)
regions = []
for cx, cy, r in [(3590, 2205, 185), (2030, 335, 58), (1675, 1250, 62)]:
    regions.append(((xx - cx * k) ** 2 + (yy - cy * k) ** 2 < (r * k + 3) ** 2, ((xx - cx * k) ** 2 + (yy - cy * k) ** 2 < (r * k + 10) ** 2)))
for x0, y0, x1, y1 in [(3115, 1945, 3255, 2495), (3895, 1945, 4015, 2495), (1005, 2945, 1195, 3025), (1532, 3185, 1582, 3465)]:
    inner = (xx >= x0 * k - 3) & (xx <= x1 * k + 3) & (yy >= y0 * k - 3) & (yy <= y1 * k + 3)
    outer = (xx >= x0 * k - 10) & (xx <= x1 * k + 10) & (yy >= y0 * k - 10) & (yy <= y1 * k + 10)
    regions.append((inner, outer))
gutter = lum < 30
for inner, outer in regions:
    ring = outer & ~inner & ~gutter
    if ring.sum() < 5:
        continue
    fill = np.median(a[ring], axis=0)
    a[inner & ~gutter] = fill
Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).save(dst)
print("cleaned", len(regions), "regions")
