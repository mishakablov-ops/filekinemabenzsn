"""v6 «1 такса — 8 стилей»: два ролика из одних кадров (VARIANT=kanal | bot).
kanal — для канала: в концовке «поддержи лайком и подпиской» + «сделать так же можно у нас в боте — напиши «стиль»
в комментариях»; bot — пример для бота: «пример монтажа по запросу», в концовке «так смонтируем и твой ролик».
Отличия от v5: low poly из v6 (голова отдельной семьёй метаболов), у пластилина нет щелчков затвора.
Дальше — описание v5:
Все стили в 1080, переход между стилями — шторка со светящейся линией (камера одна, стиль «сканирует» кадр),
надписи в безопасных зонах TikTok/Reels/Shorts, шрифт Nunito, звук: неон, «вжух» на переходах, полянка, −14 LUFS.
Запуск: VARIANT=kanal python assemble_v6.py; VARIANT=bot python assemble_v6.py
(env: FFMPEG — путь к ffmpeg, JOBS — потоков постобработки)"""
import json, os, re, subprocess, sys, wave
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from fontTools.ttLib import TTFont
from scipy import ndimage as ndi

D = os.path.dirname(os.path.abspath(__file__))
V5 = os.path.join(D, 'v5'); IDSH = os.path.join(D, 'ids5h'); IDSV = os.path.join(D, 'ids5v')
V6 = os.path.join(D, 'v6')                       # перерендер v6: только low poly
VARIANT = os.environ.get('VARIANT', 'kanal')
assert VARIANT in ('kanal', 'bot'), VARIANT
CACHE = os.path.join(D, 'post5'); OUT = os.path.join(D, 'seq6_' + VARIANT)
os.makedirs(CACHE, exist_ok=True); os.makedirs(OUT, exist_ok=True)
PY = sys.executable
FFMPEG = os.environ.get('FFMPEG', 'ffmpeg')
JOBS = int(os.environ.get('JOBS', 4))
W, H = 1080, 1920
FPS = 30
T = 8                      # кадров на переход-шторку
DARK, RAMP = 3, 36         # неон: темнота и включение
FONT_DIR = os.environ.get('FONT_DIR', D)

# (подпись, первый кадр сцены, число кадров, источник, шаг)
SEGS = [
    ('Неон', 1, 75, 'neon', 1),
    ('Мягкое 3D', 76, 60, 'soft3d', 1),
    ('Плоский мультик', 136, 60, 'ink', 1),
    ('Полутон', 196, 60, 'halftone', 1),
    ('Силуэт', 256, 60, 'silhouette', 1),
    ('Пластилин', 316, 60, 'clay', 2),
    ('Low poly 90-х', 376, 60, 'lowpoly', 1),
    ('Аниме', 436, 60, 'anime', 1),
    ('', 496, 90, 'ending', 2),            # концовка
]
NSTYLE = len(SEGS) - 1
TOTAL = SEGS[-1][1] + SEGS[-1][2] - 1    # последний кадр сцены


# ---------------- шрифты: кириллица Nunito + латиница/цифры из второго файла ----------------
class MixFont:
    def __init__(self, weight, size):
        self.f = [ImageFont.truetype(os.path.join(FONT_DIR, 'nunito-%s-%d.ttf' % (sub, weight)), size)
                  for sub in ('cyrillic', 'latin')]
        self.cm = [set(TTFont(os.path.join(FONT_DIR, 'nunito-%s-%d.ttf' % (sub, weight))).getBestCmap())
                   for sub in ('cyrillic', 'latin')]
        self.size = size

    def pick(self, ch):
        return self.f[0] if ord(ch) in self.cm[0] and ch != ' ' else self.f[1]

    def length(self, text):
        return sum(self.pick(c).getlength(c) for c in text)

    def draw(self, d, xy, text, fill, anchor='mm'):
        x, y = xy
        L = self.length(text)
        if anchor[0] == 'm': x -= L / 2
        elif anchor[0] == 'r': x -= L
        base = y + 0.36 * self.size if anchor[1] == 'm' else y
        for c in text:
            fnt = self.pick(c)
            d.text((x, base), c, font=fnt, fill=fill, anchor='ls')
            x += fnt.getlength(c)
        return L


F_TITLE = MixFont(900, 76); F_SUB = MixFont(700, 38); F_LIST = MixFont(900, 42)
F_END = MixFont(900, 80); F_END2 = MixFont(700, 44); F_CTA = MixFont(700, 40); F_CTAB = MixFont(900, 40)
SUB_TEXT = 'какой твой? пиши номер в комментариях' if VARIANT == 'kanal' else 'пример монтажа по запросу'
CODEWORD = 'стиль'                                 # слово в комменты (канал)


# ---------------- кадры стилей ----------------
def post(kind, f, local):
    out = os.path.join(CACHE, '%s_%04d.png' % (kind, f))
    if os.path.exists(out):
        return out
    env = dict(os.environ)
    if kind == 'neon':
        on = float(np.clip((local - DARK) / RAMP, 0, 1)) if local >= DARK else 0.0
        env['NEON_TEXT'] = 'такса'; env['NEON_TEXT_Y'] = '0.80'
        args = [IDSH, str(f), out, 'wall', str(on)]
    elif kind == 'ink':
        args = [IDSH, str(f), out, 'ink']
    elif kind == 'halftone':
        env['NEON_SHADE'] = os.path.join(V5, 'shade', 'f_%04d.png' % f)
        args = [IDSH, str(f), out, 'halftone']
    else:  # anime
        env['NEON_SHADE'] = os.path.join(V5, 'shadeA', 'f_%04d.png' % f)
        env['NEON_KEY'] = os.path.join(V5, 'key', 'f_%04d.png' % f)
        args = [IDSV, str(f), out, 'anime']
    subprocess.run([PY, os.path.join(D, 'neon.py')] + args, check=True, env=env, stderr=subprocess.DEVNULL)
    return out


def style_frame(i, f):
    """Готовый кадр 1080x1920 стиля сегмента i для кадра сцены f (f может заходить на T кадров за конец сегмента)."""
    name, f0, cnt, kind, step = SEGS[i]
    if kind == 'neon':
        f = min(f, f0 + cnt - 1)   # вывеска на шторке замирает: камера облёта начинается только в 3D
    local = f - f0
    if step > 1:
        f = f - (local % step); local = f - f0
    if kind in ('neon', 'ink', 'halftone', 'anime'):
        p = post(kind, f, local)
    else:
        p = os.path.join(V6 if kind == 'lowpoly' else V5, kind, 'f_%04d.png' % f)
    im = Image.open(p).convert('RGB')
    if im.size != (W, H):
        im = im.resize((W, H), Image.Resampling.LANCZOS)
    return im


def seg_of(f):
    for i in range(len(SEGS) - 1, -1, -1):
        if f >= SEGS[i][1]:
            return i
    return 0


def ease(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)
SLANT = np.tan(np.radians(14))


def wipe(old, new, k):
    """Шторка слева направо с наклоном и светящейся линией. k = 0..T-1."""
    p = ease((k + 0.5) / T)
    x0 = -0.30 * W + p * 1.60 * W
    xb = x0 + (YY - H / 2) * SLANT
    dist = XX - xb                                     # <0 — уже новый стиль
    m = np.clip(0.5 - dist / 3.0, 0, 1)[..., None]
    a = np.asarray(old, np.float32); b = np.asarray(new, np.float32)
    img = a * (1 - m) + b * m
    core = np.exp(-(dist / 2.2) ** 2)
    glow = np.exp(-(dist / 26.0) ** 2) * 0.55 + np.exp(-(dist / 90.0) ** 2) * 0.18
    inten = np.sin(np.pi * (k + 0.5) / T) ** 0.6
    col = np.array([255, 250, 235], np.float32)
    add = (core * 0.95 + glow)[..., None] * inten
    img = img + (col - img) * np.clip(add, 0, 1)
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))


# ---------------- надписи ----------------
PANEL = (40, 170, W - 40, 655)          # ниже верхних вкладок платформ, вне правой колонки кнопок


def layer():
    return Image.new('RGBA', (W, H), (0, 0, 0, 0))


def fade(ov, alpha):
    if alpha >= 1.0:
        return ov
    ov.putalpha(ov.getchannel('A').point(lambda v: int(v * alpha)))
    return ov


def overlay_list(cur, k_in, alpha=1.0):
    """Плашка со списком. Панель, «пилюля» текущего стиля и текст — на отдельных слоях (честное наложение)."""
    ov = layer(); ImageDraw.Draw(ov).rounded_rectangle(PANEL, 46, fill=(12, 12, 20, 200))
    tx = layer(); d = ImageDraw.Draw(tx)
    F_TITLE.draw(d, (W / 2, 252), '1 ТАКСА — %d СТИЛЕЙ' % NSTYLE, (255, 255, 255, 255))
    F_SUB.draw(d, (W / 2, 322), SUB_TEXT, (205, 205, 215, 255))
    for j in range(NSTYLE):
        name = SEGS[j][0]
        col, row = (0, j) if j < 4 else (1, j - 4)
        x = 92 + col * 500; y = 404 + row * 62
        label = '%d  %s' % (j + 1, name)
        if j == cur:
            s_ = ease(k_in / 5.0)                     # «выпрыгивает» за 5 кадров
            tw = F_LIST.length(label); pad = 18
            pl = layer(); ImageDraw.Draw(pl).rounded_rectangle(
                [x - pad, y - 32, x + tw + pad, y + 32], 32, fill=(255, 255, 255, 255))
            if s_ < 1:
                cx, cy = x + tw / 2, y
                sc = 0.7 + 0.3 * s_
                box = (int(cx - (tw / 2 + pad) - 4), int(cy - 36), int(cx + tw / 2 + pad + 4), int(cy + 36))
                crop = pl.crop(box)
                crop = crop.resize((max(1, int(crop.width * sc)), max(1, int(crop.height * sc))), Image.Resampling.LANCZOS)
                crop.putalpha(crop.getchannel('A').point(lambda v: int(v * s_)))
                pl = layer(); pl.alpha_composite(crop, (int(cx - crop.width / 2), int(cy - crop.height / 2)))
            ov.alpha_composite(pl)
            c = tuple(int(255 + (v - 255) * s_) for v in (15, 15, 22))
            F_LIST.draw(d, (x, y), label, c + (255,), 'lm')
        elif j < cur:
            F_LIST.draw(d, (x, y), label, (165, 165, 178, 255), 'lm')
        else:
            F_LIST.draw(d, (x, y), '%d  ' % (j + 1) + '_' * 8, (105, 105, 118, 255), 'lm')
    ov.alpha_composite(tx)
    return fade(ov, alpha)


def paw(d, cx, cy, s, fill):
    d.ellipse([cx - 1.0 * s, cy - 0.7 * s, cx + 1.0 * s, cy + 0.9 * s], fill=fill)
    for dx, dy in ((-1.15, -1.25), (-0.4, -1.75), (0.4, -1.75), (1.15, -1.25)):
        d.ellipse([cx + dx * s - 0.38 * s, cy + dy * s - 0.45 * s, cx + dx * s + 0.38 * s, cy + dy * s + 0.45 * s], fill=fill)


PAW_T = [16, 24, 32, 40]


def draw_parts(d, y, parts):
    """Строка из кусков [(текст, шрифт, цвет)], по центру."""
    L = sum(fn.length(t) for t, fn, c in parts); x = W / 2 - L / 2
    for t, fn, c in parts:
        x += fn.draw(d, (x, y), t, c, 'lm')


def overlay_end(k):
    a = ease(k / 8)
    ov = layer(); ImageDraw.Draw(ov).rounded_rectangle([60, 200, W - 60, 700], 50, fill=(12, 12, 20, 210))
    tx = layer(); d = ImageDraw.Draw(tx)
    if VARIANT == 'kanal':
        F_END.draw(d, (W / 2, 300), 'ПОДДЕРЖИ ЛАЙКОМ', (255, 255, 255, 255))
        F_END.draw(d, (W / 2, 392), 'И ПОДПИСКОЙ', (255, 255, 255, 255))
    else:
        F_END.draw(d, (W / 2, 300), 'ТАК СМОНТИРУЕМ', (255, 255, 255, 255))
        F_END.draw(d, (W / 2, 392), 'И ТВОЙ РОЛИК', (255, 255, 255, 255))
    for j, t0 in enumerate(PAW_T):
        if k >= t0:
            s_ = 20 * (1 + 0.35 * (1 - ease((k - t0) / 4)))
            paw(d, 250 + j * 190, 494 - (j % 2) * 16, s_, (255, 120, 160, 255))
    # нижние строки появляются чуть позже заголовка, мягко
    b = ease((k - 14) / 8)
    if b > 0:
        g = int(255 * b); w2 = (222, 222, 232, g); gold = (255, 214, 92, g)
        if VARIANT == 'kanal':
            draw_parts(d, 584, [('сделать так же можно у нас в боте —', F_CTA, w2)])
            draw_parts(d, 640, [('напиши ', F_CTA, w2), ('«' + CODEWORD + '»', F_CTAB, gold),
                                (' в комментариях', F_CTA, w2)])
        else:
            draw_parts(d, 584, [('по запросу,', F_CTA, w2)])
            draw_parts(d, 640, [('в любом из этих ', F_CTA, w2), ('8 стилей', F_CTAB, gold)])
    ov.alpha_composite(tx)
    return fade(ov, a)


# ---------------- сборка кадра ----------------
def build(n):
    f = n + 1
    i = seg_of(f)
    f0 = SEGS[i][1]
    k = f - f0
    im = style_frame(i, f)
    if i > 0 and k < T:
        im = wipe(style_frame(i - 1, f), im, k)
    im = im.convert('RGBA')
    if SEGS[i][3] == 'ending':
        if k < T:
            im.alpha_composite(overlay_list(i - 1, 99, 1 - ease((k + 1) / T)))
        im.alpha_composite(overlay_end(k))
    else:
        # подсветка переключается, когда шторка проходит середину
        cur, kin = (i, k - T // 2) if (i == 0 or k >= T // 2) else (i - 1, 99)
        im.alpha_composite(overlay_list(cur, max(kin, 0) if cur == i else 99))
    im.convert('RGB').save(os.path.join(OUT, 's_%04d.png' % n))
    return n


def main():
    nframes = TOTAL
    # сначала постобработка (неон, мультик, полутон, аниме) — параллельно
    jobs = []
    for i, (name, f0, cnt, kind, step) in enumerate(SEGS):
        if kind in ('neon', 'ink', 'halftone', 'anime'):
            last = f0 + cnt - 1 + (T if i < len(SEGS) - 1 else 0)
            for f in range(f0, last + 1):
                jobs.append((kind, f, f - f0))
    with ThreadPoolExecutor(JOBS) as ex:
        for _ in ex.map(lambda j: post(*j), jobs):
            pass
    print('post ok', len(jobs), flush=True)
    with ThreadPoolExecutor(JOBS) as ex:
        for n in ex.map(build, range(nframes)):
            if n % 60 == 0: print('frame', n, flush=True)
    sound(nframes)


def sound(nframes):
    total = nframes / FPS
    sr = 48000; aud = np.zeros(int(sr * (total + 0.3))); t = np.arange(aud.size) / sr
    rng = np.random.default_rng(3)
    cut = [(SEGS[i][1] - 1) / FPS for i in range(len(SEGS))]
    neon_end = cut[1]
    hum = np.sin(2 * np.pi * 50 * t) * 0.5 + np.sin(2 * np.pi * 100 * t) * 0.35 + np.sin(2 * np.pi * 150 * t) * 0.2
    henv = np.clip((t - (DARK + 0.04 * RAMP) / FPS) * 4, 0, 1) * np.clip((neon_end + T / FPS * 0.6 - t) * 6, 0, 1)
    aud += hum * henv * 0.09

    def click(t0, amp):
        s0 = int(t0 * sr); L = int(0.03 * sr)
        if s0 + L >= aud.size: return
        aud[s0:s0 + L] += rng.normal(0, 1, L) * np.exp(-np.arange(L) / (0.004 * sr)) * amp
        tt = np.arange(int(0.12 * sr)) / sr
        aud[s0:s0 + tt.size] += np.sin(2 * np.pi * 1900 * tt) * np.exp(-tt * 30) * amp * 0.15
    for tr in (0.04, 0.10, 0.13, 0.15, 0.17, 0.19, 0.22, 0.33):
        b = (DARK + tr * RAMP) / FPS; click(b, 0.55); click(b + 0.05, 0.25)
    for k in range(8):
        click((DARK + (0.45 + 0.45 * k / 7) * RAMP) / FPS, 0.22)
    # переходы: «вжух» по ходу шторки + мягкий «поп» на середине
    Lw = int(sr * T / FPS * 1.4)
    for c in cut[1:]:
        s0 = int((c - 0.05) * sr); tt = np.arange(Lw) / sr
        nz = rng.normal(0, 1, Lw)
        # полоса шума, которая «едет» вверх по частоте
        sweep = np.convolve(nz, np.ones(12) / 12, 'same') - np.convolve(nz, np.ones(90) / 90, 'same')
        env = np.sin(np.pi * np.clip(tt / (Lw / sr), 0, 1)) ** 1.5
        seg = sweep * env * 0.55
        aud[s0:s0 + Lw] += seg[:max(0, min(Lw, aud.size - s0))]
        t1 = int((c + T / 2 / FPS) * sr); L = int(sr * 0.10); tt = np.arange(L) / sr
        fr = 650 * np.exp(-tt * 18) + 260
        aud[t1:t1 + L] += np.sin(2 * np.pi * np.cumsum(fr) / sr) * np.exp(-tt * 40) * 0.32
    # полянка: шелест + птички
    noise = rng.normal(0, 1, aud.size); rustle = np.convolve(noise, np.ones(400) / 400, 'same') * 0.6
    aud += rustle * 0.15 * np.clip((t - neon_end) * 3, 0, 1)
    for t1 in rng.uniform(neon_end + 0.4, total - 1.2, 7):
        L = int(sr * 0.09); tt = np.arange(L) / sr
        for rep in range(3):
            s0 = int(sr * (t1 + rep * 0.13))
            aud[s0:s0 + L] += np.sin(2 * np.pi * (3200 + 1800 * tt / 0.09) * tt) * np.sin(np.pi * tt / 0.09) * 0.06
    # пластилин: без щелчков затвора (mike 25.11: «на пластилине какой-то звук странный») — только полянка
    # аниме: «дзынь» искорок, подскок — «топ» при приземлении
    an = cut[7]
    for k, fr in enumerate((2600, 3300, 3950)):
        tt = np.arange(int(0.6 * sr)) / sr; s0 = int((an + 0.30 + 0.09 * k) * sr)
        aud[s0:s0 + tt.size] += (np.sin(2 * np.pi * fr * tt) + 0.4 * np.sin(2 * np.pi * fr * 2.01 * tt)) * np.exp(-tt * 7) * 0.05

    def thud(t0, amp=0.35):
        tt = np.arange(int(0.07 * sr)) / sr; s0 = int(t0 * sr)
        aud[s0:s0 + tt.size] += np.sin(2 * np.pi * (120 - 400 * tt) * tt) * np.exp(-tt * 50) * amp
    thud((482 - 1) / FPS); thud((532 - 1) / FPS)
    # концовка: лапки «топ»
    for t0 in PAW_T:
        thud(cut[8] + t0 / FPS, 0.6)
    aud = aud / np.abs(aud).max() * 0.8
    wp = os.path.join(D, 'sound_v6.wav')
    with wave.open(wp, 'w') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((aud * 32767).astype(np.int16).tobytes())
    AF = 'acompressor=threshold=-28dB:ratio=8:attack=1:release=60:makeup=4,loudnorm=I=-14:TP=-1.5:LRA=11'
    r = subprocess.run([FFMPEG, '-hide_banner', '-i', wp, '-af', AF + ':print_format=json', '-f', 'null', '-'],
                       capture_output=True, text=True).stderr
    m = json.loads(re.search(r'\{[^{}]*"input_i"[^{}]*\}', r).group(0))
    wpn = os.path.join(D, 'sound_v6n.wav')
    subprocess.run([FFMPEG, '-v', 'error', '-y', '-i', wp, '-af', AF + ':measured_I=%s:measured_TP=%s:measured_LRA=%s:'
                    'measured_thresh=%s:offset=%s:linear=true' % (m['input_i'], m['input_tp'], m['input_lra'],
                                                                 m['input_thresh'], m['target_offset']),
                    '-ar', '48000', '-ac', '2', wpn], check=True)
    mp4 = os.path.join(D, 'taksa-8-stiley-%s-v6.mp4' % VARIANT)
    subprocess.run([FFMPEG, '-v', 'error', '-y', '-framerate', str(FPS), '-i', os.path.join(OUT, 's_%04d.png'),
                    '-i', wpn, '-map', '0:v', '-map', '1:a',
                    '-vf', 'format=yuv420p', '-c:v', 'libx264', '-profile:v', 'high', '-level', '4.2', '-preset', 'slow',
                    '-b:v', '12M', '-maxrate', '16M', '-bufsize', '24M', '-g', '30', '-r', str(FPS),
                    '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv',
                    # loudnorm даёт около −14,7, добираем до −14; звук обрезаем ровно по видео (-shortest оставлял +0,3 с)
                    '-af', 'volume=0.7dB,alimiter=limit=0.82:level=false:attack=2:release=40,'
                           'afade=t=out:st=%.3f:d=0.25' % (total - 0.25),
                    '-c:a', 'aac', '-b:a', '256k', '-ar', '48000',
                    '-t', '%.3f' % total, '-movflags', '+faststart', mp4], check=True)
    print('MP4', mp4, total)


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'range':
        # заранее собрать кадры a..b: python assemble_v5.py range <a> <b>
        with ThreadPoolExecutor(JOBS) as ex:
            list(ex.map(build, range(int(sys.argv[2]), int(sys.argv[3]) + 1)))
        print('range ok')
    elif len(sys.argv) > 1 and sys.argv[1] == 'frame':
        # проба одного кадра: python assemble_v5.py frame <n>
        print(build(int(sys.argv[2])))
    else:
        main()
