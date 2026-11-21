"""v3 «1 такса — 7 стилей»: как v2, но камера облетает таксу (виден объём), такса двигается, бабочка кружит."""
import os, subprocess, sys, wave
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from PIL import Image, ImageDraw, ImageFont

D = os.path.dirname(os.path.abspath(__file__))
V2 = os.path.join(D, 'v3'); IDS = os.path.join(D, 'ids3')
OUT = os.path.join(D, 'seq3'); CACHE = os.path.join(D, 'post3')
os.makedirs(OUT, exist_ok=True); os.makedirs(CACHE, exist_ok=True)
PY = sys.executable
W, H = 1080, 1920
BOLD = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
REG = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
NUN = os.path.join(D, 'nunito-cyrillic-900.ttf')
FPS = 30
DARK, RAMP = 3, 36

# (подпись, первый кадр сцены, число кадров, источник, шаг)
SEGS = [
    ('Неон', 1, 75, 'neon', 1),
    ('Мягкое 3D', 76, 60, 'soft3d', 1),
    ('Плоский мультик', 136, 60, 'ink', 1),
    ('Полутон', 196, 60, 'halftone', 1),
    ('Силуэт', 256, 60, 'silhouette', 1),
    ('Пластилин', 316, 60, 'clay', 2),
    ('Low poly 90-х', 376, 60, 'lowpoly', 1),
]
END = (436, 90, 'soft3d', 2)


def src_frame(kind, f, local):
    """Путь к готовому кадру 1080x1920 для стиля kind и кадра сцены f."""
    if kind in ('neon', 'ink', 'halftone'):
        out = os.path.join(CACHE, '%s_%04d.png' % (kind, f))
        if not os.path.exists(out):
            env = dict(os.environ)
            args = [PY, os.path.join(D, 'neon.py'), IDS, str(f), out]
            if kind == 'neon':
                on = float(np.clip((local - DARK) / RAMP, 0, 1)) if local >= DARK else 0.0
                env['NEON_TEXT'] = 'такса'; env['NEON_TEXT_Y'] = '0.80'
                args += ['wall', str(on)]
            elif kind == 'ink':
                args += ['ink']
            else:
                env['NEON_SHADE'] = os.path.join(V2, 'shade', 'f_%04d.png' % f)
                args += ['halftone']
            subprocess.run(args, check=True, env=env, stderr=subprocess.DEVNULL)
        return out
    return os.path.join(V2, kind, 'f_%04d.png' % f)


def load(kind, f, local, step):
    if step > 1:
        f = f - (local % step)  # держим кадр (стоп-моушн / «на двойках»)
    im = Image.open(src_frame(kind, f, local)).convert('RGB')
    if im.size != (W, H):
        im = im.resize((W, H), Image.Resampling.LANCZOS)
    return im


def overlay(cur):
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    d.rounded_rectangle([36, 90, W - 36, 590], 44, fill=(12, 12, 18, 205))
    ft = ImageFont.truetype(BOLD, 70); fs = ImageFont.truetype(REG, 36); fl = ImageFont.truetype(BOLD, 40)
    d.text((W / 2, 172), '1 ТАКСА — 7 СТИЛЕЙ', font=ft, fill=(255, 255, 255), anchor='mm')
    d.text((W / 2, 245), 'какой твой? пиши номер', font=fs, fill=(200, 200, 210), anchor='mm')
    for k, (name, *_ ) in enumerate(SEGS):
        col, row = (0, k) if k < 4 else (1, k - 4)
        x = 80 + col * 520; y = 318 + row * 62
        label = '%d  %s' % (k + 1, name)
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


PAW_T = [12, 20, 28, 36]


def ending(k):
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    a = min(1, k / 8)
    d.rounded_rectangle([60, 150, W - 60, 620], 50, fill=(12, 12, 18, int(215 * a)))
    f1 = ImageFont.truetype(NUN, 74); f2 = ImageFont.truetype(REG, 42)
    d.text((W / 2, 268), 'ПОДДЕРЖИ ЛАЙКОМ', font=f1, fill=(255, 255, 255, int(255 * a)), anchor='mm')
    d.text((W / 2, 362), 'И ПОДПИСКОЙ', font=f1, fill=(255, 255, 255, int(255 * a)), anchor='mm')
    d.text((W / 2, 462), 'такса уже виляет хвостом', font=f2, fill=(220, 220, 230, int(255 * a)), anchor='mm')
    for j, t0 in enumerate(PAW_T):
        if k >= t0:
            paw(d, 250 + j * 190, 560 - (j % 2) * 20, 22, (255, 120, 160, int(255 * a)))
    return ov


def build_frame(job):
    n, kind, f, local, step, cur, endk = job
    out = os.path.join(OUT, 's_%04d.png' % n)
    im = load(kind, f, local, step).convert('RGBA')
    im.alpha_composite(ending(endk) if endk is not None else overlay(cur))
    im.convert('RGB').save(out)
    return n


def main():
    jobs = []; n = 0; cuts = []
    for i, (name, f0, cnt, kind, step) in enumerate(SEGS):
        cuts.append(n / FPS)
        for local in range(cnt):
            jobs.append((n, kind, f0 + local, local, step, i, None)); n += 1
    end_t = n / FPS
    f0, cnt, kind, step = END
    for k in range(cnt):
        jobs.append((n, kind, f0 + k, k, step, None, k)); n += 1
    with ThreadPoolExecutor(4) as ex:
        for done in ex.map(build_frame, jobs):
            if done % 60 == 0: print('frame', done, flush=True)
    total = n / FPS
    # ---------- звук ----------
    sr = 48000; aud = np.zeros(int(sr * (total + 0.3))); t = np.arange(aud.size) / sr
    rng = np.random.default_rng(3)
    neon_end = cuts[1]
    # неон: гул 50 Гц + щелчки поджига
    hum = (np.sin(2 * np.pi * 50 * t) * 0.5 + np.sin(2 * np.pi * 100 * t) * 0.35 + np.sin(2 * np.pi * 150 * t) * 0.2)
    henv = np.clip((t - (DARK + 0.04 * RAMP) / FPS) * 4, 0, 1) * np.clip((neon_end - t) * 8, 0, 1)
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
    # смена стиля — мягкий «поп»
    for c in cuts[1:] + [end_t]:
        t0 = int(sr * c); L = int(sr * 0.12); tt = np.arange(L) / sr
        fr = 700 * np.exp(-tt * 18) + 260
        aud[t0:t0 + L] += np.sin(2 * np.pi * np.cumsum(fr) / sr) * np.exp(-tt * 38) * 0.5
    # полянка: шелест + птички (после неона)
    noise = rng.normal(0, 1, aud.size); rustle = np.convolve(noise, np.ones(400) / 400, 'same') * 0.6
    aud += rustle * 0.15 * (t > neon_end)
    for t1 in rng.uniform(neon_end + 0.3, total - 1, 6):
        L = int(sr * 0.09); tt = np.arange(L) / sr
        for rep in range(3):
            s0 = int(sr * (t1 + rep * 0.13))
            aud[s0:s0 + L] += np.sin(2 * np.pi * (3200 + 1800 * tt / 0.09) * tt) * np.sin(np.pi * tt / 0.09) * 0.06
    # пластилин: тихие «щелчки» затвора стоп-моушена на каждый снятый кадр
    c0, c1 = cuts[5], cuts[6]
    for tk in np.arange(c0, c1, 2 / FPS):
        s0 = int(tk * sr); L = int(0.006 * sr)
        aud[s0:s0 + L] += rng.normal(0, 1, L) * 0.05
    # концовка: лапки «топ»
    for t0 in PAW_T:
        tt = np.arange(int(0.08 * sr)) / sr; s0 = int((end_t + t0 / FPS) * sr)
        aud[s0:s0 + tt.size] += np.sin(2 * np.pi * (180 - 600 * tt) * tt) * np.exp(-tt * 45) * 0.6
    # v3: камера в концовке разворачивается к морде — мягкий «вжух»; такса подпрыгивает — тихие «топ» при приземлении
    L = int(2.0 * sr); s0 = int(end_t * sr); tt = np.arange(L) / sr
    wh = np.convolve(rng.normal(0, 1, L), np.ones(60) / 60, 'same') * np.sin(np.pi * np.clip(tt / 2.0, 0, 1)) ** 2
    aud[s0:s0 + L] += wh[:max(0, min(L, aud.size - s0))] * 0.5
    for fl in (478, 510):
        tt = np.arange(int(0.07 * sr)) / sr; s0 = int((end_t + (fl - 436) / FPS) * sr)
        aud[s0:s0 + tt.size] += np.sin(2 * np.pi * (120 - 400 * tt) * tt) * np.exp(-tt * 50) * 0.35
    aud = aud / np.abs(aud).max() * 0.8
    wp = os.path.join(D, 'sound_v3.wav')
    with wave.open(wp, 'w') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((aud * 32767).astype(np.int16).tobytes())
    # громкость: компрессор + loudnorm в 2 прохода (−14 LUFS, пик −1,5 dBFS), как в v2
    import json as _json, re as _re
    AF = 'acompressor=threshold=-28dB:ratio=8:attack=1:release=60:makeup=4,loudnorm=I=-14:TP=-1.5:LRA=11'
    r = subprocess.run(['ffmpeg', '-hide_banner', '-i', wp, '-af', AF + ':print_format=json', '-f', 'null', '-'],
                       capture_output=True, text=True).stderr
    m = _json.loads(_re.search(r'\{[^{}]*"input_i"[^{}]*\}', r).group(0))
    wpn = os.path.join(D, 'sound_v3n.wav')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', wp, '-af', AF + ':measured_I=%s:measured_TP=%s:measured_LRA=%s:'
                    'measured_thresh=%s:offset=%s:linear=true' % (m['input_i'], m['input_tp'], m['input_lra'],
                                                                 m['input_thresh'], m['target_offset']),
                    '-ar', '48000', wpn], check=True)
    wp = wpn
    mp4 = os.path.join(D, 'taksa-7-stiley-v3.mp4')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', str(FPS), '-i', os.path.join(OUT, 's_%04d.png'),
                    '-i', wp, '-vf', 'format=yuv420p', '-c:v', 'libx264', '-preset', 'slow', '-b:v', '10M',
                    '-maxrate', '12M', '-bufsize', '20M', '-c:a', 'aac', '-b:a', '192k',
                    '-shortest', '-movflags', '+faststart', mp4], check=True)
    print('MP4', mp4, total)


if __name__ == '__main__':
    main()
