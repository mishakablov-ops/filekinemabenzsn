"""Soundtrack for 'Космос для всех': music arrangement + designed SFX, ducked under the narration.

Output: engine/public/projects/kosmos-dlya-vseh/soundtrack.wav (48 kHz stereo). The voice itself is played by the engine.
Run in the VM:  python3 mix.py
"""
import json, os, re, subprocess, sys, wave
import numpy as np
PROJ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
RS = os.path.abspath(os.path.join(PROJ, '..', 'AIpollon-Reel-Studio', 'skills', 'reel-studio'))
PUB = os.path.join(RS, 'engine', 'public')
RP = os.path.join(PUB, 'projects', os.environ.get('KOSMOS_PID', 'kosmos-dlya-vseh'))
SR = 48000
FF = 'ffmpeg'
rng = np.random.default_rng(5)


def load(path, mono=False):
    raw = subprocess.run([FF, '-v', 'error', '-i', path, '-ac', '1' if mono else '2', '-ar', str(SR), '-f', 'f32le', '-'],
                         capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.float32).astype(np.float64)
    return x if mono else x.reshape(-1, 2)


W = json.load(open(os.path.join(RP, 'words.json'), encoding='utf-8'))
words = W['words']
shots = {s['id']: s for s in json.load(open(os.environ.get('KOSMOS_SHOTS', os.path.join(PROJ, 'blender', 'shots.json')), encoding='utf-8'))['shots']}
END = max(s['start'] + s['dur'] for s in shots.values())
N = int(END * SR) + SR
out = np.zeros((N, 2))
voice = load(os.path.join(RP, 'voice.wav'), mono=True)


def norm(t):
    return re.sub(r'[^0-9a-zа-я%$ ]+', '', t.lower().replace('ё', 'е')).strip()


TOK = [norm(w['text']) for w in words]


def at(phrase, nth=1, end=False):
    whole = norm(phrase)
    hits = 0
    for i, t in enumerate(TOK):          # numbers like "$750 000" are one token
        if t == whole or t == '$' + whole:
            hits += 1
            if hits == nth:
                return words[i]['end'] if end else words[i]['start']
    parts = [norm(p) for p in phrase.split()]
    hits = 0
    for i in range(len(TOK)):
        if all(i + k < len(TOK) and TOK[i + k] == parts[k] for k in range(len(parts))):
            hits += 1
            if hits == nth:
                return words[i + len(parts) - 1]['end'] if end else words[i]['start']
    raise SystemExit('anchor ' + phrase)


def put(x, t, gain=1.0, fade_in=0.0, fade_out=0.0, length=None):
    global out
    if x.ndim == 1:
        x = np.stack([x, x], 1)
    if length is not None:
        n = int(length * SR)
        if len(x) < n:
            x = np.concatenate([x] * int(np.ceil(n / len(x))))
        x = x[:n].copy()
    else:
        x = x.copy()
    n = len(x)
    if fade_in:
        k = min(n, int(fade_in * SR)); x[:k] *= np.linspace(0, 1, k)[:, None]
    if fade_out:
        k = min(n, int(fade_out * SR)); x[n - k:] *= np.linspace(1, 0, k)[:, None]
    s = int(max(0, t) * SR)
    e = min(N, s + n)
    out[s:e] += x[:e - s] * gain


idx = {m['id']: m for m in json.load(open(os.path.join(PUB, 'sfx', 'index.json'), encoding='utf-8'))}


def lib_sfx(i):
    m = idx[i]
    for _ in range(5):
        if m.get('alias'):
            m = idx[m['alias']]
    return load(os.path.join(PUB, m['file'])), m.get('peak', 0.0)


cache = {}
SYN = {}


def sfx(name, t, gain, peak_align=False, **kw):
    if name not in cache:
        cache[name] = (SYN[name], 0.0) if name in SYN else lib_sfx(name)
    x, pk = cache[name]
    put(x, t - (pk if peak_align else 0.0), gain * SFX_GAIN, **kw)


# ------------------------------------------------------------------ synthesized sounds
def lowpass(x, fc, order=1):
    """First-order-like low-pass done in the frequency domain (no scipy in the VM)."""
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1.0 / SR)
    X *= 1.0 / np.sqrt(1.0 + (f / fc) ** (2 * order))
    return np.fft.irfft(X, len(x))


def rocket(dur):
    n = int(dur * SR)
    w = rng.standard_normal(n)
    rumble = lowpass(lowpass(w, 90), 140) * 9.0
    roar = lowpass(w, 900) * 1.3
    crackle = (rng.random(n) < 0.004) * rng.standard_normal(n) * 0.9
    crackle = lowpass(crackle, 2500)
    env = np.minimum(1, np.arange(n) / (0.4 * SR))
    x = (rumble + roar + crackle) * env
    x /= np.max(np.abs(x)) + 1e-9
    l = x; r = np.roll(x, 240)
    return np.stack([l, r], 1)


def flyby(dur=2.5):
    n = int(dur * SR); t = np.arange(n) / SR
    w = lowpass(rng.standard_normal(n), 600)
    tone = 0.0
    env = np.exp(-((t - dur * 0.45) / (dur * 0.28)) ** 2)
    x = (w * 2.0 + tone) * env
    x /= np.max(np.abs(x)) + 1e-9
    pan = np.clip(t / dur, 0, 1)
    return np.stack([x * (1 - 0.6 * pan), x * (0.4 + 0.6 * pan)], 1)


def wind(dur, fc=500, gust=0.35):
    n = int(dur * SR); t = np.arange(n) / SR
    w = lowpass(rng.standard_normal(n), fc, 2)
    mod = 1 + gust * np.sin(2 * np.pi * 0.23 * t + 1.0) + 0.5 * gust * np.sin(2 * np.pi * 0.61 * t)
    x = w * mod
    x /= np.max(np.abs(x)) + 1e-9
    return np.stack([x, np.roll(x, 900)], 1)


def breath(dur, period=3.2):
    n = int(dur * SR); t = np.arange(n) / SR
    w = lowpass(rng.standard_normal(n), 1800, 2) - lowpass(rng.standard_normal(n), 250, 2) * 0.3
    ph = (t % period) / period
    env = np.where(ph < 0.4, np.sin(np.pi * ph / 0.4) ** 2, 0.6 * np.sin(np.pi * np.clip((ph - 0.45) / 0.5, 0, 1)) ** 2)
    x = w * env
    x /= np.max(np.abs(x)) + 1e-9
    return x


SYN['wind'] = wind(9.0)
SYN['mars-wind'] = wind(9.0, 320, 0.5)
SYN['breath'] = breath(9.0)

S = lambda k: shots[k]['start']
D = lambda k: shots[k]['dur']
E = lambda k, e: shots[k]['start'] + shots[k]['events'][e]
SFX_GAIN = 0.42

# ------------------------------------------------------------------ music arrangement
amb = load(os.path.join(PUB, 'music', 'ambient-air.m4a'))
dark = load(os.path.join(PUB, 'music', 'dark-cinematic.m4a'))
t_dark, t_dream = S('sh08a_debris'), S('sh09a_dream')
music = np.zeros((N, 2))


def mput(x, t, off, length, fi, fo, g=1.0):
    seg = x[int(off * SR): int(off * SR) + int(length * SR)]
    if len(seg) < int(length * SR):
        seg = np.concatenate([seg, x[:int(length * SR) - len(seg)]])
    seg = seg.copy(); n = len(seg)
    k = int(fi * SR); seg[:k] *= np.linspace(0, 1, k)[:, None]
    k = int(fo * SR); seg[n - k:] *= np.linspace(1, 0, k)[:, None]
    s = int(t * SR); e = min(N, s + n); music[s:e] += seg[:e - s] * g


mput(amb, 0.0, 0.0, t_dark + 1.0, 0.2, 1.4, 1.0)
mput(dark, t_dark - 0.5, 0.0, t_dream - t_dark + 1.0, 0.9, 1.4, 0.9)
mput(amb, t_dream - 0.3, 30.0, END - t_dream + 0.3, 1.2, 1.6, 1.0)
env = np.abs(voice)
win = int(0.03 * SR)
env = np.convolve(env, np.ones(win) / win, mode='same')
act = (env > 0.02).astype(float)
att, rel = int(0.08 * SR), int(0.35 * SR)
sm = np.zeros_like(act); v = 0.0
step = 64
for i in range(0, len(act), step):
    target = act[i]
    k = att if target > v else rel
    v += (target - v) * min(1.0, step / k)
    sm[i:i + step] = v
duck = 1.0 - 0.6 * sm
duck = np.pad(duck, (0, max(0, N - len(duck))), constant_values=1.0)[:N]
MUSIC_GAIN = 0.24
out += music * (duck[:, None] * MUSIC_GAIN)

# ------------------------------------------------------------------ designed sound (only non-retired library ids)
sfx('space-drone', 0.0, 0.5, length=S('sh02_pad') + 0.3, fade_in=0.2, fade_out=0.4)
if 'flyby' in SYN:
    sfx('flyby', 0.1, 0.5)
sfx('wind', S('sh02_pad'), 0.3, length=D('sh02_pad'), fade_in=0.3, fade_out=0.4)
sfx('pk-digital-data-load-sfx-1', at('746'), 0.45)
sfx('hit-punch', at('750 000'), 0.45)
if 'rocket' in SYN:
    sfx('rocket', S('sh03_ascent') - 0.1, 0.85, fade_out=0.6)
sfx('riser-long', at('километров') - 3.6, 0.4)
sfx('trans-riser-hit', at('километров'), 0.4, peak_align=True)
sfx('space-drone', S('sh04_sunrise'), 0.4, length=D('sh04_sunrise'), fade_in=0.2, fade_out=0.3)
sfx('reveal-glow', E('sh04_sunrise', 'rise') - 0.3, 0.55)
sfx('pk-pop-ui-menu', at('16'), 0.4, peak_align=True)
sfx('downlifter-short', S('sh05_moon') - 0.1, 0.35)
sfx('breath', S('sh05_moon') + 0.2, 0.22, length=D('sh05_moon') - 0.3, fade_in=0.3, fade_out=0.4)
sfx('pk-pop-ui-menu', at('выходные'), 0.45, peak_align=True)
sfx('mars-wind', S('sh06_mars'), 0.4, length=D('sh06_mars'), fade_in=0.3, fade_out=0.4)
sfx('pk-digital-data-load-sfx-1', E('sh06_mars', 'pulse'), 0.45)
sfx('hit-soft', at('22'), 0.4)
sfx('breath', S('sh07a_eva'), 0.25, length=D('sh07a_eva'), fade_in=0.3, fade_out=0.4)
sfx('reveal-glow', S('sh07a_eva') + 0.2, 0.35)
sfx('pk-shimmer-ui-dissolvre-sfx', at('обзора'), 0.45)
sfx('downlifter', S('sh07b_earth') - 0.1, 0.3)
sfx('hit-soft', at('хрупкой'), 0.4)
sfx('dread-rise', S('sh08a_debris') - 0.2, 0.45)
sfx('pk-digital-data-load-sfx-1', at('40 000'), 0.45)
sfx('pk-digital-digitasl-burst-sfx', at('миллиона'), 0.35)
sfx('pk-notify-system-alert-sfx', at('пробку'), 0.45, peak_align=True)
sfx('reveal-glow', at('мечта') - 0.5, 0.5)
sfx('thud', at('свалку'), 0.6)
sfx('hit-punch', at('свалку') + 0.02, 0.35)
sfx('pk-shimmer-ui-dissolvre-sfx', at('Кстати'), 0.6)
sfx('tone-rise-short', at('нейросеть') - 0.4, 0.35)
sfx('pk-click-ui-button', at('шапке'), 0.7, peak_align=True)
sfx('pk-notify-notification-sfx-1', at('профиля'), 0.8, peak_align=True)

pk = np.max(np.abs(out))
if pk > 0.95:
    out *= 0.95 / pk
data = (np.clip(out, -1, 1) * 32767).astype('<i2')
with wave.open(os.path.join(RP, 'soundtrack.wav'), 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(data.tobytes())
print('soundtrack', round(N / SR, 2), 's peak', round(20 * np.log10(np.max(np.abs(out)) + 1e-9), 1), 'dB')
