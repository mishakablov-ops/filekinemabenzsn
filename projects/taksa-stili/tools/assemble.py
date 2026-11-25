"""Сборка тест-клипа «1 такса — 10 стилей»: стиль кадра, плашка со списком, концовка, звук, MP4."""
import os, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

D = os.path.dirname(os.path.abspath(__file__))
FR = os.path.join(D, 'frames')
OUT = os.path.join(D, 'seq'); os.makedirs(OUT, exist_ok=True)
PY = sys.executable
W, H = 1080, 1920
BOLD = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
REG = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'

SEGS = [  # (подпись, рендер, обработка, новый?)
    ('Мягкое 3D', 'soft3d', None, False),
    ('Плоский мультик', 'flat', 'flatline', False),
    ('Полутон', 'flat', 'halftone2', False),
    ('16-бит', 'soft3d', 'pixel16', False),
    ('Силуэт', 'silhouette', None, False),
    ('Пластилин', 'clay', None, True),
    ('Гжель', 'gzhel', None, True),
    ('Неон', 'flat', 'neonline', True),
    ('Чертёж', 'flat', 'blueprint', True),
    ('Low poly 90-х', 'lowpoly', None, False),
]


def fpath(style, f):
    return os.path.join(FR, style, 'f_%04d.png' % f)


def styled(i, f):
    _, rnd, post, _ = SEGS[i]
    src = fpath(rnd, f)
    if post is None:
        im = Image.open(src).convert('RGB')
    else:
        tmp = os.path.join(D, 'tmp_post.png')
        args = [PY, os.path.join(D, 'post.py'), post, src, tmp, str(f)]
        if post == 'halftone2':
            args.append(fpath('soft3d', f))
        subprocess.run(args, check=True)
        im = Image.open(tmp).convert('RGB')
    rs = Image.Resampling.NEAREST if post in ('pixel16',) else Image.Resampling.LANCZOS
    return im.resize((W, H), rs)


def overlay(cur, t_in):
    """Плашка сверху: заголовок + список стилей, текущий в белой капсуле."""
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    d.rounded_rectangle([36, 90, W - 36, 640], 44, fill=(12, 12, 18, 205))
    ft = ImageFont.truetype(BOLD, 68); fs = ImageFont.truetype(REG, 38); fl = ImageFont.truetype(BOLD, 38)
    d.text((W / 2, 175), '1 ТАКСА — 10 СТИЛЕЙ', font=ft, fill=(255, 255, 255), anchor='mm')
    d.text((W / 2, 250), 'какой твой? пиши номер', font=fs, fill=(200, 200, 210), anchor='mm')
    for k, (name, _, _, new) in enumerate(SEGS):
        col, row = k // 5, k % 5
        x = 80 + col * 530; y = 330 + row * 60
        label = '%d  %s' % (k + 1, name) + ('  ★' if new else '')
        if k == cur:
            tw = d.textlength(label, font=fl)
            d.rounded_rectangle([x - 16, y - 28, x + tw + 16, y + 28], 28, fill=(255, 255, 255, 255))
            d.text((x, y), label, font=fl, fill=(15, 15, 20), anchor='lm')
        elif k < cur:
            d.text((x, y), label, font=fl, fill=(170, 170, 180), anchor='lm')
        else:
            d.text((x, y), '%d  ' % (k + 1) + '_' * 9, font=fl, fill=(110, 110, 120), anchor='lm')
    return ov


def paw(d, cx, cy, s, fill):
    d.ellipse([cx - 1.0 * s, cy - 0.7 * s, cx + 1.0 * s, cy + 0.9 * s], fill=fill)
    for dx, dy in ((-1.15, -1.25), (-0.4, -1.75), (0.4, -1.75), (1.15, -1.25)):
        d.ellipse([cx + dx * s - 0.38 * s, cy + dy * s - 0.45 * s, cx + dx * s + 0.38 * s, cy + dy * s + 0.45 * s], fill=fill)


def ending(k, n):
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    a = min(1, k / 8)
    d.rounded_rectangle([60, 150, W - 60, 620], 50, fill=(12, 12, 18, int(215 * a)))
    f1 = ImageFont.truetype(BOLD, 68); f2 = ImageFont.truetype(REG, 44)
    d.text((W / 2, 270), 'ПОДДЕРЖИ ЛАЙКОМ', font=f1, fill=(255, 255, 255, int(255 * a)), anchor='mm')
    d.text((W / 2, 370), 'И ПОДПИСКОЙ', font=f1, fill=(255, 255, 255, int(255 * a)), anchor='mm')
    d.text((W / 2, 470), 'такса уже виляет хвостом', font=f2, fill=(220, 220, 230, int(255 * a)), anchor='mm')
    # лапки «топают» по одной
    for j in range(4):
        if k > 10 + j * 6:
            paw(d, 250 + j * 190, 570 - (j % 2) * 20, 22, (255, 120, 160, int(255 * a)))
    return ov


def main():
    n = 0
    for i in range(len(SEGS)):
        ov = overlay(i, 0)
        for f in range(60 * i + 1, 60 * i + 61, 2):
            im = styled(i, f).convert('RGBA'); im.alpha_composite(ov)
            im.convert('RGB').save(os.path.join(OUT, 's_%04d.png' % n)); n += 1
        print('seg', i, 'ok', flush=True)
    for k, f in enumerate(range(601, 691, 2)):
        im = Image.open(fpath('soft3d', f)).convert('RGB').resize((W, H), Image.Resampling.LANCZOS).convert('RGBA')
        im.alpha_composite(ending(k, 45)); im.convert('RGB').save(os.path.join(OUT, 's_%04d.png' % n)); n += 1
    total = n / 15.0
    # звук: мягкий «поп» на каждой смене стиля, без музыки
    sr = 48000; aud = np.zeros(int(sr * (total + 0.5)))
    rng = np.random.default_rng(3)
    for i in range(1, len(SEGS) + 1):
        t0 = int(sr * 2.0 * i); L = int(sr * 0.12); tt = np.arange(L) / sr
        fr = 700 * np.exp(-tt * 18) + 260
        pop = np.sin(2 * np.pi * np.cumsum(fr) / sr) * np.exp(-tt * 38)
        aud[t0:t0 + L] += pop * 0.5
    # лёгкий фон полянки: шелест (фильтрованный шум) + редкие птички
    noise = rng.normal(0, 1, aud.size)
    k = np.ones(400) / 400; rustle = np.convolve(noise, k, 'same') * 0.6
    aud += rustle * 0.15
    for t in rng.uniform(0.5, total - 1, 7):
        L = int(sr * 0.09); tt = np.arange(L) / sr
        for rep in range(3):
            s0 = int(sr * (t + rep * 0.13))
            chirp = np.sin(2 * np.pi * (3200 + 1800 * tt / 0.09) * tt) * np.sin(np.pi * tt / 0.09)
            aud[s0:s0 + L] += chirp * 0.06
    aud = aud / np.abs(aud).max() * 0.7
    wp = os.path.join(D, 'sound.wav')
    with wave.open(wp, 'w') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((aud * 32767).astype(np.int16).tobytes())
    mp4 = os.path.join(D, 'taksa-10-stiley-test-v1.mp4')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', '15', '-i', os.path.join(OUT, 's_%04d.png'),
                    '-i', wp, '-vf', 'fps=30,format=yuv420p', '-c:v', 'libx264', '-preset', 'slow', '-b:v', '10M',
                    '-maxrate', '12M', '-bufsize', '20M', '-c:a', 'aac', '-b:a', '192k',
                    '-af', 'loudnorm=I=-14:TP=-1.5:LRA=11', '-shortest', '-movflags', '+faststart', mp4], check=True)
    print('MP4', mp4, total)


if __name__ == '__main__':
    main()
