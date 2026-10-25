"""Small numpy DSP toolkit used by the SFX and music generators.

Everything is 48 kHz float32/float64, mono arrays unless a function says stereo
(shape (n, 2)). No scipy needed.
"""
from __future__ import annotations

import math
import wave
from pathlib import Path

import numpy as np

SR = 48000
RNG = np.random.default_rng(7)


def seed(n: int) -> None:
    global RNG
    RNG = np.random.default_rng(n)


def t_axis(dur: float) -> np.ndarray:
    return np.arange(n_of(dur)) / SR


def n_of(dur: float) -> int:
    return int(round(dur * SR))


# ---------------------------------------------------------------- oscillators
def phase_from_freq(freq: np.ndarray | float, n: int) -> np.ndarray:
    f = np.broadcast_to(np.asarray(freq, dtype=np.float64), (n,))
    return 2 * np.pi * np.cumsum(f) / SR


def sine(freq, dur: float, phase0: float = 0.0) -> np.ndarray:
    n = n_of(dur)
    return np.sin(phase_from_freq(freq, n) + phase0)


def tri(freq, dur: float) -> np.ndarray:
    n = n_of(dur)
    ph = phase_from_freq(freq, n) / (2 * np.pi)
    return 2 * np.abs(2 * (ph - np.floor(ph + 0.5))) - 1


def saw(freq, dur: float) -> np.ndarray:
    """Band-limited-ish saw via additive partials (cheap PolyBLEP alternative)."""
    n = n_of(dur)
    f = np.broadcast_to(np.asarray(freq, dtype=np.float64), (n,))
    ph = phase_from_freq(f, n)
    out = np.zeros(n)
    fmax = float(np.max(f)) if np.ndim(f) else float(f)
    k_max = max(1, int((SR / 2.2) / max(fmax, 1)))
    k_max = min(k_max, 60)
    for k in range(1, k_max + 1):
        out += np.sin(k * ph) / k
    return out * (2 / np.pi)


def square(freq, dur: float, harmonics: int = 25) -> np.ndarray:
    n = n_of(dur)
    ph = phase_from_freq(freq, n)
    out = np.zeros(n)
    for k in range(1, harmonics * 2, 2):
        out += np.sin(k * ph) / k
    return out * (4 / np.pi)


def noise(dur: float) -> np.ndarray:
    return RNG.uniform(-1, 1, n_of(dur))


def pink(dur: float) -> np.ndarray:
    n = n_of(dur)
    spec = np.fft.rfft(RNG.normal(0, 1, n))
    f = np.fft.rfftfreq(n, 1 / SR)
    f[0] = 1
    spec /= np.sqrt(f)
    x = np.fft.irfft(spec, n)
    return x / (np.max(np.abs(x)) + 1e-9)


# ---------------------------------------------------------------- envelopes
def env_exp(dur: float, decay: float, attack: float = 0.002) -> np.ndarray:
    t = t_axis(dur)
    a = np.clip(t / max(attack, 1e-5), 0, 1)
    return a * np.exp(-t / max(decay, 1e-5)) * taper_curve(len(t))


def taper_curve(n: int, frac: float = 0.18) -> np.ndarray:
    """1.0 then a raised-cosine fall to 0 over the last `frac` of the buffer (kills end clicks)."""
    c = np.ones(n)
    k = max(1, int(n * frac))
    c[-k:] = 0.5 * (1 + np.cos(np.linspace(0, np.pi, k)))
    return c


def taper(x: np.ndarray, frac: float = 0.18) -> np.ndarray:
    c = taper_curve(len(x), frac)
    return x * (c if x.ndim == 1 else c[:, None])


def env_adsr(dur: float, a=0.01, d=0.1, s=0.7, r=0.2) -> np.ndarray:
    n = n_of(dur)
    t = t_axis(dur)
    e = np.zeros(n)
    rel_start = max(dur - r, a + d)
    e = np.where(t < a, t / max(a, 1e-6), e)
    m = (t >= a) & (t < a + d)
    e = np.where(m, 1 - (1 - s) * (t - a) / max(d, 1e-6), e)
    m = (t >= a + d) & (t < rel_start)
    e = np.where(m, s, e)
    m = t >= rel_start
    e = np.where(m, s * np.clip(1 - (t - rel_start) / max(r, 1e-6), 0, 1), e)
    return e


def env_bell(dur: float, peak: float = 0.5, sharp: float = 2.0) -> np.ndarray:
    """Smooth rise to `peak` (0..1 of duration) then fall. Classic whoosh shape."""
    t = np.linspace(0, 1, n_of(dur))
    up = np.clip(t / peak, 0, 1) ** sharp
    down = np.clip((1 - t) / (1 - peak), 0, 1) ** (sharp * 0.8)
    return np.where(t < peak, up, down)


def fade(x: np.ndarray, fin: float = 0.002, fout: float = 0.01) -> np.ndarray:
    x = x.copy()
    ni, no = n_of(fin), n_of(fout)
    if ni > 0:
        ramp = np.linspace(0, 1, ni)
        x[:ni] *= ramp if x.ndim == 1 else ramp[:, None]
    if no > 0:
        ramp = np.linspace(1, 0, no)
        x[-no:] *= ramp if x.ndim == 1 else ramp[:, None]
    return x


# ---------------------------------------------------------------- filters
def svf(x: np.ndarray, fc, q: float = 0.707, mode: str = "low") -> np.ndarray:
    """TPT state-variable filter; fc may be an array (time-varying sweep)."""
    n = len(x)
    fc = np.clip(np.broadcast_to(np.asarray(fc, dtype=np.float64), (n,)), 10, SR * 0.45)
    g = np.tan(np.pi * fc / SR)
    k = 1.0 / q
    a1 = 1.0 / (1.0 + g * (g + k))
    a2 = g * a1
    a3 = g * a2
    out = np.empty(n)
    ic1 = ic2 = 0.0
    xs = x.tolist()
    a1l, a2l, a3l = a1.tolist(), a2.tolist(), a3.tolist()
    if mode == "low":
        for i in range(n):
            v3 = xs[i] - ic2
            v1 = a1l[i] * ic1 + a2l[i] * v3
            v2 = ic2 + a2l[i] * ic1 + a3l[i] * v3
            ic1 = 2 * v1 - ic1
            ic2 = 2 * v2 - ic2
            out[i] = v2
    elif mode == "band":
        for i in range(n):
            v3 = xs[i] - ic2
            v1 = a1l[i] * ic1 + a2l[i] * v3
            v2 = ic2 + a2l[i] * ic1 + a3l[i] * v3
            ic1 = 2 * v1 - ic1
            ic2 = 2 * v2 - ic2
            out[i] = v1 * k  # normalised peak gain
    else:  # high
        for i in range(n):
            v3 = xs[i] - ic2
            v1 = a1l[i] * ic1 + a2l[i] * v3
            v2 = ic2 + a2l[i] * ic1 + a3l[i] * v3
            ic1 = 2 * v1 - ic1
            ic2 = 2 * v2 - ic2
            out[i] = xs[i] - k * v1 - v2
    return out


def fft_filter(x: np.ndarray, gain_fn) -> np.ndarray:
    """Static zero-phase filter: gain_fn(freqs_hz) -> linear gain."""
    n = len(x)
    spec = np.fft.rfft(x)
    f = np.fft.rfftfreq(n, 1 / SR)
    return np.fft.irfft(spec * gain_fn(f), n)


def lowpass(x, fc, order=2):
    return fft_filter(x, lambda f: 1 / np.sqrt(1 + (f / fc) ** (2 * order)))


def highpass(x, fc, order=2):
    return fft_filter(x, lambda f: 1 / np.sqrt(1 + (fc / np.maximum(f, 1e-3)) ** (2 * order)))


def bandpass(x, fc, width_oct=1.0):
    return fft_filter(x, lambda f: np.exp(-0.5 * (np.log2(np.maximum(f, 1) / fc) / (width_oct / 2)) ** 2))


def stft_filter(x: np.ndarray, gain_fn, hop: int = 256, win: int = 1024) -> np.ndarray:
    """Time-varying spectral filter. gain_fn(freqs, t_seconds) -> gain per bin."""
    n = len(x)
    pad = np.concatenate([np.zeros(win), x, np.zeros(win)])
    w = np.hanning(win)
    frames = 1 + (len(pad) - win) // hop
    out = np.zeros(len(pad))
    norm = np.zeros(len(pad))
    f = np.fft.rfftfreq(win, 1 / SR)
    for i in range(frames):
        s = i * hop
        seg = pad[s:s + win] * w
        t = (s + win / 2 - win) / SR
        spec = np.fft.rfft(seg) * gain_fn(f, t)
        out[s:s + win] += np.fft.irfft(spec, win) * w
        norm[s:s + win] += w ** 2
    out /= np.maximum(norm, 1e-6)
    return out[win:win + n]


# ---------------------------------------------------------------- effects
def make_ir(rt60: float = 1.2, dur: float | None = None, damp: float = 0.6, predelay: float = 0.01) -> np.ndarray:
    """Synthetic stereo room impulse response."""
    dur = dur or rt60 * 1.1
    n = n_of(dur)
    t = t_axis(dur)
    tau = rt60 / 6.91
    ir = np.zeros((n, 2))
    for ch in range(2):
        nz = RNG.normal(0, 1, n) * np.exp(-t / tau)
        # high frequencies die faster
        nz = stft_filter(nz, lambda f, tt: np.exp(-tt * damp * (f / 2000.0)), hop=512, win=2048)
        ir[:, ch] = nz
    pd = n_of(predelay)
    ir = np.vstack([np.zeros((pd, 2)), ir])
    ir /= np.sqrt(np.sum(ir ** 2) / 2) + 1e-9
    return ir


def convolve(x: np.ndarray, ir: np.ndarray) -> np.ndarray:
    """Mono or stereo x convolved with stereo IR -> stereo."""
    if x.ndim == 1:
        x = np.stack([x, x], axis=1)
    n = len(x) + len(ir) - 1
    nfft = 1 << (n - 1).bit_length()
    out = np.zeros((n, 2))
    for ch in range(2):
        out[:, ch] = np.fft.irfft(np.fft.rfft(x[:, ch], nfft) * np.fft.rfft(ir[:, ch], nfft), nfft)[:n]
    return out


_IR_CACHE: dict = {}


def reverb(x: np.ndarray, wet: float = 0.25, rt60: float = 1.2, damp: float = 0.6, tail: bool = True) -> np.ndarray:
    key = (round(rt60, 2), round(damp, 2))
    if key not in _IR_CACHE:
        _IR_CACHE[key] = make_ir(rt60, damp=damp)
    ir = _IR_CACHE[key]
    dry = taper(to_stereo(x), 0.05)
    w = convolve(dry, ir) * 0.35
    if not tail:
        w = w[: len(dry)]
    out = np.zeros_like(w)
    out[: len(dry)] += dry * (1 - wet * 0.5)
    out += w * wet
    return out


def to_stereo(x: np.ndarray) -> np.ndarray:
    return np.stack([x, x], axis=1) if x.ndim == 1 else x


def pan(x: np.ndarray, p) -> np.ndarray:
    """p in -1..1 (array allowed for auto-pan). Equal-power."""
    m = x if x.ndim == 1 else x.mean(axis=1)
    p = np.broadcast_to(np.asarray(p, dtype=np.float64), (len(m),))
    ang = (p + 1) * np.pi / 4
    return np.stack([m * np.cos(ang), m * np.sin(ang)], axis=1)


def widen(x: np.ndarray, ms: float = 12.0) -> np.ndarray:
    """Haas widening of a mono signal."""
    m = x if x.ndim == 1 else x.mean(axis=1)
    d = n_of(ms / 1000)
    r = np.concatenate([np.zeros(d), m])[: len(m)]
    return np.stack([m, 0.85 * r + 0.15 * m], axis=1)


def softclip(x: np.ndarray, drive: float = 1.5) -> np.ndarray:
    return np.tanh(x * drive) / np.tanh(drive)


def bitcrush(x: np.ndarray, bits: int = 6, down: int = 4) -> np.ndarray:
    y = np.repeat(x[::down], down)[: len(x)]
    q = 2 ** (bits - 1)
    return np.round(y * q) / q


def place(dst: np.ndarray, src: np.ndarray, at: float, gain: float = 1.0) -> np.ndarray:
    """Mix src into dst starting at `at` seconds (grows dst if needed)."""
    s = n_of(at)
    src = to_stereo(src) if dst.ndim == 2 else src
    need = s + len(src)
    if need > len(dst):
        pad = np.zeros((need - len(dst),) + dst.shape[1:])
        dst = np.concatenate([dst, pad])
    dst[s:s + len(src)] += src * gain
    return dst


def silence(dur: float, stereo: bool = True) -> np.ndarray:
    return np.zeros((n_of(dur), 2)) if stereo else np.zeros(n_of(dur))


def normalize(x: np.ndarray, peak_db: float = -1.0) -> np.ndarray:
    pk = np.max(np.abs(x)) + 1e-12
    return x * (10 ** (peak_db / 20) / pk)


def trim_tail(x: np.ndarray, thresh_db: float = -60) -> np.ndarray:
    th = 10 ** (thresh_db / 20)
    a = np.abs(x if x.ndim == 1 else x.max(axis=1))
    idx = np.where(a > th * np.max(a))[0]
    if len(idx) == 0:
        return x
    end = min(len(x), idx[-1] + n_of(0.02))
    return x[:end]


def write_wav(path: Path, x: np.ndarray, peak_db: float = -1.0, norm: bool = True) -> float:
    x = to_stereo(x)
    if norm:
        x = normalize(x, peak_db)
    x = fade(x, 0.001, 0.008)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = (np.clip(x, -1, 1) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())
    return len(x) / SR


def read_wav(path: Path) -> np.ndarray:
    with wave.open(str(path), "rb") as w:
        n = w.getnframes()
        ch = w.getnchannels()
        sw = w.getsampwidth()
        raw = w.readframes(n)
    if sw != 2:
        raise ValueError("only 16-bit wav supported")
    x = np.frombuffer(raw, dtype="<i2").astype(np.float64) / 32768
    return x.reshape(-1, ch)


def midi_hz(m: float) -> float:
    return 440.0 * 2 ** ((m - 69) / 12)


def note_hz(name: str) -> float:
    names = {"C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5, "F#": 6, "Gb": 6,
             "G": 7, "G#": 8, "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11}
    p, o = (name[:-1], int(name[-1]))
    return midi_hz(12 * (o + 1) + names[p])


def karplus(freq: float, dur: float, bright: float = 0.5, decay: float = 0.996) -> np.ndarray:
    """Karplus-Strong plucked string."""
    n = n_of(dur)
    period = max(2, int(SR / freq))
    buf = RNG.uniform(-1, 1, period)
    buf = lowpass(np.concatenate([buf, buf]), 1500 + bright * 9000)[:period]
    out = np.empty(n)
    bl = buf.tolist()
    idx = 0
    prev = 0.0
    for i in range(n):
        v = bl[idx]
        out[i] = v
        nv = decay * (0.5 * (v + prev))
        prev = v
        bl[idx] = nv
        idx = (idx + 1) % period
    return out


def fm_bell(freq: float, dur: float, ratio: float = 3.5, index: float = 2.5, decay: float = 0.6) -> np.ndarray:
    t = t_axis(dur)
    mod_env = np.exp(-t / (decay * 0.4))
    mod = np.sin(2 * np.pi * freq * ratio * t) * index * mod_env
    return np.sin(2 * np.pi * freq * t + mod) * np.exp(-t / decay)


def clamp01(x):
    return max(0.0, min(1.0, x))


def lerp(a, b, t):
    return a + (b - a) * t


def log_sweep(f0: float, f1: float, dur: float, curve: float = 1.0) -> np.ndarray:
    t = np.linspace(0, 1, n_of(dur)) ** curve
    return f0 * (f1 / f0) ** t
