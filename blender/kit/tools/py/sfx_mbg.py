"""Custom sound effects for 'Мир без границ' (numpy synthesis on top of Reel Studio's dsp.py)."""
import sys, os, math
from pathlib import Path
HERE = Path(__file__).resolve().parent
PROJ = HERE.parents[1]
sys.path.insert(0, str(PROJ.parent / 'AIpollon-Reel-Studio' / 'skills' / 'reel-studio' / 'scripts'))
import numpy as np
import dsp as D
SR = D.SR
OUT = PROJ / 'audio' / 'sfx'
rng = np.random.default_rng(11)

def env(n, a, d):
    t = np.arange(n) / SR
    return np.minimum(1, t / max(a, 1e-4)) * np.exp(-np.maximum(0, t - a) / d)

def burst(dur, fc, width=1.0, a=0.001, d=0.05, gain=1.0):
    n = D.n_of(dur)
    x = rng.standard_normal(n) * env(n, a, d)
    return D.bandpass(x, fc, width) * gain

def modes(dur, freqs, decays, amps, a=0.0005):
    n = D.n_of(dur); t = np.arange(n) / SR; x = np.zeros(n)
    for f, dc, am in zip(freqs, decays, amps):
        x += am * np.sin(2 * np.pi * f * t + rng.uniform(0, 6)) * np.exp(-t / dc)
    return x * np.minimum(1, t / a)

def stereo_spread(x, ms=8):
    return D.widen(D.to_stereo(x), ms) if hasattr(D, 'widen') else D.to_stereo(x)

def save(name, x, peak=-1.0, rev=None):
    if rev:
        x = D.reverb(x if x.ndim == 1 else x.mean(axis=1), wet=rev[0], rt60=rev[1])
    D.write_wav(OUT / f'{name}.wav', D.trim_tail(D.to_stereo(x) if x.ndim == 1 else x, -70), peak)
    print('ok', name)

# 1 barrier gate: motor whine + gear rattle, ends with a clunk
def gate_motor(dur=1.9):
    n = D.n_of(dur); t = np.arange(n) / SR
    f = 95 + 55 * np.clip(t / 0.4, 0, 1) - 20 * np.clip((t - dur + 0.35) / 0.35, 0, 1)
    mot = D.lowpass(D.saw(f, dur), 900) * 0.5 + D.sine(f * 2, dur) * 0.15
    rattle = D.bandpass(rng.standard_normal(n), 1800, 1.2) * (0.5 + 0.5 * np.sin(2 * np.pi * 34 * t)) * 0.18
    e = np.minimum(1, t / 0.06) * np.minimum(1, (dur - t) / 0.12)
    x = (mot + rattle) * e
    clunk = modes(0.6, [180, 420, 1310, 2650], [0.09, 0.05, 0.03, 0.02], [1, 0.6, 0.35, 0.2]) + burst(0.6, 900, 1.5, d=0.03, gain=0.6)
    x = D.place(x, clunk * 1.4, dur - 0.08)
    return x
save('mbg-gate-motor', gate_motor(), rev=(0.18, 0.9))
# 2 passport closing: soft leather slap
x = burst(0.35, 500, 1.6, d=0.025, gain=1.0) + modes(0.35, [130, 260], [0.05, 0.03], [0.5, 0.2])
save('mbg-leather-close', x, peak=-3, rev=(0.12, 0.5))
# 3 paper slide (map / passport sliding)
n = D.n_of(1.0); t = np.arange(n) / SR
x = D.svf(rng.standard_normal(n), 1500 + 2500 * np.sin(np.pi * t), 0.8, 'band') * np.sin(np.pi * t) ** 1.5 * 0.6
save('mbg-paper-slide', x, peak=-4)
# 4 crowd: footsteps + murmur
def step(gain=1.0):
    return (burst(0.12, rng.uniform(250, 600), 1.6, d=0.018) * 0.8 + burst(0.12, rng.uniform(1800, 3500), 1.2, d=0.01) * 0.25) * gain
def murmur(dur, voices=24):
    n = D.n_of(dur); out = np.zeros(n)
    for v in range(voices):
        src = D.lowpass(rng.standard_normal(n), 3000)
        f1, f2 = rng.uniform(400, 800), rng.uniform(1000, 2200)
        syl = np.clip(np.sin(2 * np.pi * rng.uniform(3.2, 5.0) * np.arange(n) / SR + rng.uniform(0, 6)), 0, 1) ** 2
        gate = (D.lowpass(rng.standard_normal(n), 1.2) > -0.2).astype(float)
        out += (D.bandpass(src, f1, 0.6) + 0.6 * D.bandpass(src, f2, 0.5)) * syl * D.lowpass(gate, 6)
    return out / voices
def crowd(dur, rate, voices, mgain):
    n = D.n_of(dur); x = np.zeros(n)
    tt = 0.0
    while tt < dur:
        x = D.place(x, step(rng.uniform(0.4, 1.0)), tt)[:n]
        tt += rng.exponential(1 / rate)
    return x * 0.7 + murmur(dur, voices) * mgain
save('mbg-crowd-walk', crowd(4.5, 22, 18, 1.4), peak=-3, rev=(0.15, 1.2))
save('mbg-crowd-dense', crowd(3.5, 40, 40, 2.2), peak=-2, rev=(0.22, 1.6))
# 5 car horns in a city (two cars, far)
def horn(dur, f):
    tt = np.arange(D.n_of(dur)) / SR
    x = sum(np.sign(np.sin(2 * np.pi * f * k * tt)) / k for k in (1, 2, 3)) + np.sign(np.sin(2 * np.pi * f * 1.26 * tt)) * 0.7
    return D.lowpass(x, 2200) * np.minimum(1, tt / 0.02) * np.minimum(1, (dur - tt) / 0.04)
h = np.zeros(D.n_of(2.2)); h = D.place(h, horn(0.35, 410), 0.1); h = D.place(h, horn(0.22, 360), 0.9); h = D.place(h, horn(0.5, 360), 1.25)
save('mbg-car-horns', h, peak=-6, rev=(0.35, 2.2))
# 6 swing squeak (one squeak = one swing pass)
def squeak(dur=0.55):
    tt = np.arange(D.n_of(dur)) / SR
    f = 950 + 220 * np.sin(np.pi * tt / dur) + 25 * np.sin(2 * np.pi * 37 * tt)
    x = D.sine(f, dur) * 0.6 + D.sine(f * 2.01, dur) * 0.25 + D.sine(f * 3.03, dur) * 0.1
    rough = 0.6 + 0.4 * (rng.random(len(tt)) > 0.5)
    return x * np.sin(np.pi * tt / dur) ** 2 * D.lowpass(rough, 120)
sw = np.zeros(D.n_of(3.3)); sw = D.place(sw, squeak(), 0.2); sw = D.place(sw, squeak(0.5) * 0.8, 1.8)
save('mbg-swing-creak', sw, peak=-6, rev=(0.3, 1.8))
# 7 marching boots: 56 soldiers in step, one step every 0.5 s
def boots(dur=5.0, period=0.5, men=56):
    n = D.n_of(dur); x = np.zeros(n)
    k = 0.0
    while k < dur:
        for m in range(men):
            j = rng.normal(0, 0.012)
            x = D.place(x, (burst(0.18, rng.uniform(140, 380), 1.4, d=0.03) * 1.0 + burst(0.18, rng.uniform(1500, 3000), 1.0, d=0.012) * 0.35)
                        * rng.uniform(0.3, 1.0), max(0, k + j))[:n]
        k += period
    return x
save('mbg-march-boots', boots(), peak=-2, rev=(0.18, 1.4))
# 8 tank engine idle
def engine(dur=5.0):
    n = D.n_of(dur); tt = np.arange(n) / SR
    puls = np.clip(np.sin(2 * np.pi * 26 * tt), 0, 1) ** 4
    x = D.lowpass(rng.standard_normal(n), 220) * (0.4 + 0.8 * puls) + D.sine(52, dur) * 0.25 + D.sine(26, dur) * 0.4
    x += D.bandpass(rng.standard_normal(n), 900, 1.0) * 0.05 * (0.5 + puls)
    return x * np.minimum(1, tt / 0.6)
save('mbg-tank-engine', engine(), peak=-3)
# 9 coins clink
c = np.zeros(D.n_of(1.0))
for k in range(5):
    f0 = rng.uniform(2600, 4200)
    c = D.place(c, modes(0.5, [f0, f0 * 1.52, f0 * 2.31, f0 * 3.07], [0.12, 0.08, 0.05, 0.03], [1, 0.6, 0.4, 0.2]) * rng.uniform(0.4, 1), 0.05 + k * rng.uniform(0.05, 0.12))
save('mbg-coins', c, peak=-4, rev=(0.15, 0.8))
# 10 gavel knock (wood on wood) + small room
g = modes(0.7, [430, 1080, 2210, 3400], [0.07, 0.04, 0.025, 0.015], [1, 0.8, 0.45, 0.2]) + burst(0.7, 1600, 1.6, d=0.006, gain=0.8)
g += modes(0.7, [118], [0.08], [0.6])
save('mbg-gavel', g, peak=-1, rev=(0.22, 1.1))
# 11 plastic cone tap / asphalt crumble
cr = np.zeros(D.n_of(1.0))
for k in range(18):
    cr = D.place(cr, burst(0.08, rng.uniform(1500, 5000), 1.0, d=0.006) * rng.uniform(0.2, 0.8), rng.uniform(0, 0.7))
cr = D.place(cr, modes(0.3, [310, 790], [0.04, 0.02], [0.8, 0.4]), 0.0)
save('mbg-road-crumble', cr, peak=-5, rev=(0.12, 0.7))
# 12 pumpjack: rhythmic metal groan + motor
def pump(dur=4.5, period=4.0):
    n = D.n_of(dur); tt = np.arange(n) / SR
    x = D.lowpass(D.saw(48, dur), 400) * 0.25 + D.lowpass(rng.standard_normal(n), 160) * 0.3
    for k0 in (0.3, 0.3 + period / 2):
        if k0 < dur:
            d = 1.1
            f = 230 + 60 * np.sin(np.pi * np.arange(D.n_of(d)) / SR / d)
            gro = (D.saw(f, d) * 0.3 + D.sine(f * 1.5, d) * 0.2) * np.sin(np.pi * np.arange(D.n_of(d)) / SR / d) ** 2
            x = D.place(x, D.lowpass(gro, 1600), k0)[:n]
    return x
save('mbg-pumpjack', pump(), peak=-4, rev=(0.25, 1.6))
# 13 distant gunfire bursts + explosions + fire crackle
def shot(dist=1.0):
    s = burst(0.5, 1200, 2.5, a=0.0003, d=0.012, gain=1.0) + burst(0.5, 300, 1.5, d=0.08, gain=0.7)
    return D.lowpass(s, 4000 / dist)
def gunfire(dur=4.0):
    n = D.n_of(dur); x = np.zeros(n); tt = 0.15
    while tt < dur - 0.3:
        shots = rng.integers(2, 6); dist = rng.uniform(1.0, 2.5)
        for k in range(shots):
            x = D.place(x, shot(dist) * rng.uniform(0.3, 0.8) / dist, tt + k * rng.uniform(0.07, 0.11))[:n]
        tt += rng.uniform(0.25, 0.7)
    return x
save('mbg-gunfire-far', gunfire(), peak=-3, rev=(0.4, 2.2))
def boom():
    n = D.n_of(3.0); tt = np.arange(n) / SR
    x = D.sine(55 * np.exp(-tt * 1.2) + 28, 3.0) * np.exp(-tt / 0.6) * 0.9
    x += D.lowpass(rng.standard_normal(n), 500) * np.exp(-tt / 0.9) * 0.8
    x += burst(3.0, 900, 2.0, d=0.04, gain=0.5)
    return D.lowpass(x, 1800)
save('mbg-explosion-far', boom(), peak=-1, rev=(0.45, 3.0))
def fire(dur=4.0):
    n = D.n_of(dur); x = D.lowpass(rng.standard_normal(n), 300) * 0.35
    tt = 0.0
    while tt < dur:
        x = D.place(x, burst(0.05, rng.uniform(2000, 6000), 1.2, d=0.004) * rng.uniform(0.1, 0.6), tt)[:n]
        tt += rng.exponential(0.03)
    return x
save('mbg-fire', fire(), peak=-6)
# 14 sodium lamp / searchlight hum
n = D.n_of(4.0); tt = np.arange(n) / SR
hum = sum(np.sin(2 * np.pi * 100 * k * tt) / k ** 1.3 for k in range(1, 9)) * (0.8 + 0.2 * np.sin(2 * np.pi * 0.7 * tt))
hum += D.bandpass(rng.standard_normal(n), 3000, 1.0) * 0.08
save('mbg-lamp-hum', D.lowpass(hum, 2500) * np.minimum(1, tt / 0.3), peak=-8)
# 15 border lines dissolving: glassy descending shimmer
n = D.n_of(2.2); tt = np.arange(n) / SR
x = np.zeros(n)
for k in range(40):
    f0 = rng.uniform(1800, 7000)
    st = rng.uniform(0, 0.9)
    seg = D.sine(f0 * np.exp(-np.arange(D.n_of(1.2)) / SR * 0.6), 1.2) * env(D.n_of(1.2), 0.004, 0.25) * rng.uniform(0.2, 0.6)
    x = D.place(x, seg, st)[:n]
x += D.sine(110 * np.exp(-tt * 0.5), 2.2) * np.exp(-tt / 0.8) * 0.6
save('mbg-dissolve', x, peak=-3, rev=(0.35, 2.4))
# 16 lines drawn on the globe: soft electric scribble
n = D.n_of(2.6); tt = np.arange(n) / SR
x = D.svf(rng.standard_normal(n), 2500 + 1500 * np.sin(2 * np.pi * 3.1 * tt), 3.0, 'band') * (0.4 + 0.6 * np.abs(np.sin(2 * np.pi * 5.3 * tt)))
x *= np.minimum(1, tt / 0.15) * np.minimum(1, (2.6 - tt) / 0.4)
save('mbg-scribble', x, peak=-8)
print('DONE')
