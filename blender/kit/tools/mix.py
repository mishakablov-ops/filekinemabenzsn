"""Soundtrack for 'Мир без границ': music arrangement + designed SFX, ducked under the narration.

Output: engine/public/projects/__PROJECT__/soundtrack.wav (48 kHz stereo). The voice itself is played by the engine.
"""
import json, os, re, subprocess, sys, wave
import numpy as np
PROJ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
RS = os.path.abspath(os.path.join(PROJ, '..', 'AIpollon-Reel-Studio', 'skills', 'reel-studio'))
PUB = os.path.join(RS, 'engine', 'public')
RP = os.path.join(PUB, 'projects', '__PROJECT__')
SR = 48000
FF = 'ffmpeg'

def load(path, mono=False):
    raw = subprocess.run([FF, '-v', 'error', '-i', path, '-ac', '1' if mono else '2', '-ar', str(SR), '-f', 'f32le', '-'],
                         capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.float32).astype(np.float64)
    return x if mono else x.reshape(-1, 2)

W = json.load(open(os.path.join(RP, 'words.json'), encoding='utf-8'))
words = W['words']
shots = {s['id']: s for s in json.load(open(os.path.join(PROJ, 'blender', 'shots.json'), encoding='utf-8'))['shots']}
END = max(s['start'] + s['dur'] for s in shots.values())
N = int(END * SR) + SR
out = np.zeros((N, 2))
voice = load(os.path.join(RP, 'voice.wav'), mono=True)

def norm(t):
    return re.sub(r'[^0-9a-zа-я%$ ]+', '', t.lower().replace('ё', 'е')).strip()
TOK = [norm(w['text']) for w in words]
def at(phrase, nth=1):
    parts = [norm(p) for p in phrase.split()]
    hits = 0
    for i in range(len(TOK)):
        if all(i + k < len(TOK) and TOK[i + k] == parts[k] for k in range(len(parts))):
            hits += 1
            if hits == nth:
                return words[i]['start']
    raise SystemExit('anchor ' + phrase)

def put(x, t, gain=1.0, fade_in=0.0, fade_out=0.0, length=None):
    global out
    if x.ndim == 1:
        x = np.stack([x, x], 1)
    if length is not None:
        n = int(length * SR)
        if len(x) < n:
            reps = int(np.ceil(n / len(x)))
            x = np.concatenate([x] * reps)
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

SFXDIR = os.path.join(PROJ, 'audio', 'sfx')
idx = {m['id']: m for m in json.load(open(os.path.join(PUB, 'sfx', 'index.json'), encoding='utf-8'))}
def lib_sfx(i):
    m = idx[i]
    for _ in range(5):
        if m.get('alias'):
            m = idx[m['alias']]
    return load(os.path.join(PUB, m['file'])), m.get('peak', 0.0)
cache = {}
def sfx(name, t, gain, peak_align=False, **kw):
    if name not in cache:
        if name.startswith('mbg-'):
            cache[name] = (load(os.path.join(SFXDIR, name + '.wav')), 0.0)
        else:
            cache[name] = lib_sfx(name)
    x, pk = cache[name]
    put(x, t - (pk if peak_align else 0.0), gain * SFX_GAIN, **kw)

S = lambda k: shots[k]['start']
D = lambda k: shots[k]['dur']
E = lambda k, e: shots[k]['start'] + (shots[k]['events'][e] if not isinstance(shots[k]['events'][e], list) else 0)
SFX_GAIN = 0.42

# ------------------------------------------------------------------ music arrangement
amb = load(os.path.join(PUB, 'music', 'ambient-air.m4a'))
dark = load(os.path.join(PUB, 'music', 'dark-cinematic.m4a'))
t_army, t_final = S('sh10_army'), S('sh13_final')
music = np.zeros((N, 2))
def mput(x, t, off, length, fi, fo, g=1.0):
    seg = x[int(off * SR): int(off * SR) + int(length * SR)]
    if len(seg) < int(length * SR):
        seg = np.concatenate([seg, x[:int(length * SR) - len(seg)]])
    seg = seg.copy(); n = len(seg)
    k = int(fi * SR); seg[:k] *= np.linspace(0, 1, k)[:, None]
    k = int(fo * SR); seg[n - k:] *= np.linspace(1, 0, k)[:, None]
    s = int(t * SR); e = min(N, s + n); music[s:e] += seg[:e - s] * g
mput(amb, 0.0, 0.0, t_army + 1.2, 0.25, 1.6, 1.0)
mput(dark, t_army - 0.6, 0.0, t_final - t_army + 1.6, 1.0, 2.0, 0.95)
mput(amb, t_final - 0.4, 24.0, END - t_final + 0.4, 1.8, 1.6, 1.0)
# duck under speech (sidechain from the narration envelope)
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

# ------------------------------------------------------------------ designed sound
sfx('space-drone', 0.0, 0.55, length=S('sh03_wall') + 0.4, fade_in=0.3, fade_out=0.6)
sfx('mbg-dissolve', E('sh01_globe_hook', 'dissolve') - 0.05, 0.9)
sfx('hit-sub', E('sh01_globe_hook', 'dissolve'), 0.5)
sfx('mbg-scribble', E('sh01_globe_hook', 'redraw'), 0.55)
sfx('pk-digital-data-load-sfx-1', E('sh01_globe_hook', 'redraw') + 0.15, 0.35)
sfx('mbg-lamp-hum', S('sh03_wall'), 0.18, length=D('sh03_wall'), fade_in=0.2, fade_out=0.3)
sfx('thud', at('стен') - 0.02, 0.7)
sfx('hit-soft', at('стен'), 0.45)
sfx('mbg-gate-motor', E('sh04_gate_lift', 'lift'), 0.8)
sfx('mbg-leather-close', E('sh05_passport', 'close') + 0.8, 0.9)
sfx('mbg-paper-slide', E('sh05_passport', 'slide'), 0.55)
sfx('pk-shimmer-ui-dissolvre-sfx', E('sh05_passport', 'schengen') + 0.1, 0.5)
sfx('mbg-crowd-walk', S('sh06_crowd'), 0.75, length=D('sh06_crowd'), fade_in=0.3, fade_out=0.4)
sfx('pk-digital-digitasl-burst-sfx', S('sh07_globe_arcs') + 0.1, 0.4)
sfx('space-drone', S('sh07_globe_arcs'), 0.35, length=D('sh07_globe_arcs'), fade_in=0.2, fade_out=0.4)
sfx('city-hum', S('sh08_city_grow'), 0.55, length=D('sh08_city_grow') + D('sh09a_city_crush'), fade_in=0.3, fade_out=0.4)
sfx('riser-medium', at('удвоиться') - 1.6, 0.35)
sfx('mbg-crowd-dense', S('sh09a_city_crush'), 0.85, length=D('sh09a_city_crush'), fade_in=0.15, fade_out=0.3)
sfx('mbg-car-horns', S('sh09a_city_crush') + 0.3, 0.35)
sfx('mbg-swing-creak', S('sh09b_village') + 0.1, 0.55)
sfx('mbg-march-boots', S('sh10_army'), 0.9, length=D('sh10_army'), fade_in=0.2, fade_out=0.5)
sfx('mbg-tank-engine', S('sh10_army'), 0.28, length=D('sh10_army'), fade_in=0.4, fade_out=0.5)
sfx('hit-sub', at('охранять'), 0.45)
sfx('mbg-coins', at('налоги') - 0.1, 0.75)
sfx('mbg-road-crumble', at('дороги') - 0.05, 0.65)
sfx('mbg-gavel', E('sh11_state', 'gavel'), 1.1)
sfx('mbg-scribble', E('sh12_globe_redraw', 'start'), 0.6, length=2.4, fade_out=0.6)
sfx('marker', at('границы', 2), 0.45)
sfx('mbg-pumpjack', S('sh12b_oil'), 0.6, length=D('sh12b_oil'), fade_in=0.2, fade_out=0.3)
sfx('mbg-gunfire-far', S('sh12c_battle'), 0.75, length=D('sh12c_battle'), fade_in=0.1, fade_out=0.5)
sfx('mbg-fire', S('sh12c_battle'), 0.45, length=D('sh12c_battle'), fade_out=0.5)
for i, tb in enumerate(shots['sh12c_battle']['events'].get('blasts', [])):
    sfx('mbg-explosion-far', S('sh12c_battle') + tb, [0.7, 0.85, 1.0][min(i, 2)])
sfx('rumble-distant', at('воевать'), 0.5)
sfx('door-creak', S('sh13_final') + 0.2, 0.25)
sfx('reveal-glow', at('договор') - 0.2, 0.4)
sfx('hit-soft', at('открыл'), 0.4)
sfx('pk-shimmer-ui-dissolvre-sfx', at('Кстати'), 0.6)
sfx('pk-pop-ui-menu', at('агент') + 0.5, 0.55)
sfx('pk-click-ui-button', at('шапку'), 0.7, peak_align=True)
sfx('pk-notify-notification-sfx-1', at('профиля'), 0.8, peak_align=True)

# gentle safety limiter
pk = np.max(np.abs(out))
if pk > 0.95:
    out *= 0.95 / pk
data = (np.clip(out, -1, 1) * 32767).astype('<i2')
with wave.open(os.path.join(RP, 'soundtrack.wav'), 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(data.tobytes())
print('soundtrack', round(N / SR, 2), 's peak', round(20 * np.log10(np.max(np.abs(out)) + 1e-9), 1), 'dB')
