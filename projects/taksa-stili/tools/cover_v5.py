"""Обложка 1080x1920 для «1 такса — 8 стилей»: заголовок + сетка 2x4 из кадров стилей.
Текст и сетка — в центральной зоне 1080x1440 (её показывает сетка профиля Reels/TikTok).
python cover_v5.py <out.jpg>   — берёт готовые кадры из seq5/post5/v5."""
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import assemble_v5 as A

W, H = 1080, 1920
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(A.D, 'oblozhka-v5.jpg')
PICK = [(0, 75), (1, 100), (2, 165), (3, 225), (4, 285), (5, 326), (6, 405), (7, 470)]
CROP = (20, 690, 1060, 1260)       # такса в кадре: 40–62 % высоты

bg = A.style_frame(1, 110).resize((W, H)).filter(ImageFilter.GaussianBlur(28))
bg = Image.blend(bg, Image.new('RGB', (W, H), (10, 10, 18)), 0.62).convert('RGBA')
d = ImageDraw.Draw(bg)
FT = A.MixFont(900, 150); FS = A.MixFont(900, 92); FQ = A.MixFont(700, 44); FN = A.MixFont(900, 34)
FT.draw(d, (W / 2, 360), '1 ТАКСА', (255, 255, 255, 255))
FS.draw(d, (W / 2, 486), '8 СТИЛЕЙ', (255, 214, 92, 255))
FQ.draw(d, (W / 2, 572), 'какой твой?', (225, 225, 235, 255))
tw, th, gap = 486, 262, 24
x0 = (W - 2 * tw - gap) / 2; y0 = 640
for j, (i, f) in enumerate(PICK):
    im = A.style_frame(i, f).crop(CROP).resize((tw, th), Image.Resampling.LANCZOS)
    mask = Image.new('L', (tw, th), 0); ImageDraw.Draw(mask).rounded_rectangle([0, 0, tw - 1, th - 1], 26, fill=255)
    col, row = j % 2, j // 2
    x, y = int(x0 + col * (tw + gap)), int(y0 + row * (th + gap))
    sh = Image.new('RGBA', (tw + 40, th + 40), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([20, 24, tw + 20, th + 24], 26, fill=(0, 0, 0, 140))
    bg.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)), (x - 20, y - 20))
    bg.paste(im, (x, y), mask)
    dd = ImageDraw.Draw(bg)
    dd.ellipse([x + 14, y + 14, x + 70, y + 70], fill=(255, 255, 255, 255))
    FN.draw(dd, (x + 42, y + 42), str(j + 1), (15, 15, 22, 255))
    name = A.SEGS[i][0]
    L = FN.length(name)
    dd.rounded_rectangle([x + tw - L - 40, y + th - 56, x + tw - 12, y + th - 12], 20, fill=(12, 12, 20, 200))
    FN.draw(dd, (x + tw - 26, y + th - 34), name, (255, 255, 255, 255), 'rm')
bg.convert('RGB').save(OUT, quality=93)
print('cover', OUT)
