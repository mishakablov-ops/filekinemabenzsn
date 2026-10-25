"""Voice-over FX: make a TTS take sound like an energetic young voice actor.

    expressive(x, ...)  TD-PSOLA re-contouring of the pitch: raise the median, widen the melody,
                        lift the key words (accents from the script). Formants and timing stay —
                        so word timings for captions do not change and the voice does not get "chipmunky".
    master(x, preset)   VO chain via ffmpeg: high-pass, mud cut, presence, air, de-esser, compressor, limiter.

CLI (try settings on any file):
    python vo_fx.py in.wav out.wav [--widen 1.4] [--target 145] [--preset energetic|clean|off]
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import voice_profile as vp  # noqa: E402

SR = 48000
HOP = 0.005  # f0 analysis hop, s

PRESETS = {
    # young energetic VO: tight low end, forward presence, crisp top, firm compression
    "energetic": ("highpass=f=85:poles=2,"
                  "equalizer=f=240:t=q:w=1.1:g=-2.5,"
                  "equalizer=f=3100:t=q:w=0.9:g=2,"
                  "equalizer=f=150:t=q:w=1:g=1,"
                  "aexciter=amount=0.4:drive=4:blend=0:freq=7000:ceil=16000,"
                  "deesser=i=0.35:m=0.5:f=0.55,"
                  "acompressor=threshold=0.1:ratio=2.5:attack=6:release=80:knee=3:makeup=1.9,"
                  "alimiter=limit=0.89:attack=1.5:release=35:level=disabled"),
    # gentle: only cleanup + light compression
    "clean": ("highpass=f=75:poles=2,equalizer=f=250:t=q:w=1:g=-1.5,equalizer=f=3000:t=q:w=1:g=1.5,"
              "acompressor=threshold=0.12:ratio=2:attack=8:release=100:knee=4:makeup=1.3,"
              "alimiter=limit=0.89:level=disabled"),
}


# ------------------------------------------------------------------ helpers
def fft_resample(x: np.ndarray, sr_in: int, sr_out: int) -> np.ndarray:
    n_out = int(round(len(x) * sr_out / sr_in))
    X = np.fft.rfft(x)
    keep = min(len(X), n_out // 2 + 1)
    Y = np.zeros(n_out // 2 + 1, dtype=complex)
    Y[:keep] = X[:keep]
    return np.fft.irfft(Y, n_out) * (n_out / len(x))


def lowpass_fft(x: np.ndarray, sr: int, fc: float) -> np.ndarray:
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / sr)
    X *= 1 / (1 + (f / fc) ** 8)
    return np.fft.irfft(X, len(x))


def runs(mask: np.ndarray):
    """[(start, end)] of True runs."""
    d = np.diff(np.concatenate([[0], mask.astype(np.int8), [0]]))
    return list(zip(np.where(d == 1)[0], np.where(d == -1)[0]))


# ------------------------------------------------------------------ pitch track
def f0_track(x: np.ndarray, sr: int = SR):
    x16 = fft_resample(x, sr, vp.SR)
    x16 = x16 / (np.max(np.abs(x16)) + 1e-9)
    f0, ap = vp.yin(x16, fmin=60, fmax=420, win_s=0.03, hop_s=HOP, th=0.15)
    f0_track.aper = ap
    n = len(f0)
    t = np.arange(n) * HOP + 0.015
    # loudness gate
    fr = vp.frames(x16, int(0.03 * vp.SR), int(HOP * vp.SR))[:n]
    rms = 20 * np.log10(np.sqrt((fr ** 2).mean(axis=1)) + 1e-9)
    f0[rms < np.percentile(rms, 95) - 35] = np.nan
    v = ~np.isnan(f0)
    if v.sum() < 10:
        return t, f0
    # octave errors: compare to a running median of voiced frames
    med = np.nanmedian(f0)
    st = 12 * np.log2(np.where(v, f0, med) / med)
    for i in np.where(v)[0]:
        lo, hi = max(0, i - 20), min(n, i + 21)
        loc = st[lo:hi][v[lo:hi]]
        ref = np.median(loc)
        if st[i] - ref > 9:
            f0[i] /= 2
        elif ref - st[i] > 9:
            f0[i] *= 2
    # median smoothing inside voiced runs, drop islands < 30 ms, bridge gaps <= 20 ms
    out = np.full(n, np.nan)
    for a, b in runs(~np.isnan(f0)):
        if b - a < 6:
            continue
        seg = f0[a:b].copy()
        k = 2
        out[a:b] = [np.median(seg[max(0, i - k): i + k + 1]) for i in range(len(seg))]
    v = ~np.isnan(out)
    rr = runs(v)
    for (a1, b1), (a2, b2) in zip(rr, rr[1:]):
        if a2 - b1 <= 4:
            out[b1:a2] = np.exp(np.interp(np.arange(b1, a2), [b1 - 1, a2], [np.log(out[b1 - 1]), np.log(out[a2])]))
    return t, out


# ------------------------------------------------------------------ TD-PSOLA
def psola(x: np.ndarray, t_f0: np.ndarray, f0: np.ndarray, shift_st: np.ndarray, sr: int = SR) -> np.ndarray:
    """Re-pitch voiced parts: new f0(t) = f0(t) * 2^(shift_st(t)/12). Unvoiced parts pass through."""
    N = len(x)
    fi = np.clip(((np.arange(N) / sr - 0.015) / HOP).round().astype(int), 0, len(f0) - 1)
    f0_s = f0[fi]
    voiced = ~np.isnan(f0_s)
    sh_s = shift_st[fi]
    lp = lowpass_fft(x, sr, 900)
    out = np.zeros(N + 4096)
    wsum = np.zeros(N + 4096)

    def add(center_out: int, center_in: int, half: int, right: int | None = None):
        """Hann grain around center_in (rising over `half`, falling over `right`), added at center_out."""
        L, R = half, (half if right is None else right)
        a, b = center_in - L, center_in + R
        if a < 0 or b > N or min(L, R) < 8 or center_out - L < 0:
            return
        w = np.concatenate([0.5 - 0.5 * np.cos(np.pi * np.arange(L) / L), 0.5 + 0.5 * np.cos(np.pi * np.arange(R) / R)])
        o = center_out - L
        out[o:o + L + R] += x[a:b] * w
        wsum[o:o + L + R] += w

    # unvoiced: identity overlap-add (Hann, 50 %)
    U = 240
    for a, b in runs(~voiced):
        for c in range(max(U, a), min(b + U, N - U), U):
            add(c, c, U)
    # voiced: pitch marks on the low-passed waveform, then re-spaced synthesis marks
    interior = np.zeros(N, dtype=bool)
    for a, b in runs(voiced):
        if b - a < int(0.02 * sr):
            for c in range(a, b, U):
                add(c, c, U)
            continue
        P0 = sr / f0_s[a]
        first = a + int(np.argmax(lp[a: a + int(P0)]))
        marks = [first]
        while True:
            m = marks[-1]
            P = sr / f0_s[min(m, N - 1)] if voiced[min(m, N - 1)] else P0
            pred = int(m + P)
            if pred >= b:
                break
            r = int(P * 0.25)
            lo, hi = max(m + int(P * 0.5), pred - r), min(N, pred + r)
            if hi <= lo:
                break
            marks.append(lo + int(np.argmax(lp[lo:hi])))
        marks = np.array(marks)
        if len(marks) < 2:
            continue
        interior[marks[0]:marks[-1]] = True
        periods = np.diff(marks).astype(float)
        left = np.concatenate([[periods[0]], periods]).astype(int)    # distance to the previous mark
        right = np.concatenate([periods, [periods[-1]]]).astype(int)  # distance to the next mark
        idx = np.arange(len(marks), dtype=float)
        ts = float(marks[0])
        # synthesis marks follow the analysis marks' own spacing divided by the pitch ratio:
        # ratio 1 -> marks land exactly on the analysis marks (identity)
        while ts <= marks[-1]:
            u = float(np.interp(ts, marks, idx))
            k = int(round(u))
            add(int(round(ts)), int(marks[k]), int(left[k]), int(right[k]))
            u0 = min(int(u), len(marks) - 2)
            local = periods[u0]
            ts += local / 2 ** (sh_s[min(int(ts), N - 1)] / 12)
    o, w = out[:N], wsum[:N]
    # inside re-pitched runs: normalise by the window sum; around them: fill any coverage gap with the original
    edge = (o + x * np.clip(1 - w, 0, 1)) / np.maximum(w, 1)
    return np.where(interior, o / np.maximum(w, 0.55), edge)


def base_shift(x: np.ndarray, st: float, sr: int = SR) -> np.ndarray:
    """Constant pitch shift with preserved formants (rubberband) — for engines without a pitch control."""
    if abs(st) < 0.05:
        return x
    pk = np.max(np.abs(x)) + 1e-9
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-f", "f32le", "-ar", str(sr), "-ac", "1", "-i", "pipe:0",
           "-af", f"rubberband=pitch={2 ** (st / 12):.6f}:formant=preserved:pitchq=quality:transients=smooth",
           "-f", "f32le", "pipe:1"]
    y = np.frombuffer(subprocess.run(cmd, input=(x / pk * 0.5).astype(np.float32).tobytes(), capture_output=True, check=True).stdout,
                      dtype=np.float32).astype(np.float64) * (pk / 0.5)
    out = np.zeros(len(x))
    out[: min(len(x), len(y))] = y[: len(x)]
    return out


def expressive(x: np.ndarray, widen: float = 1.4, emphasis=(), emph_st: float = 1.6, emph_db: float = 2.5,
               target: float | None = None, sr: int = SR):
    """Livelier melody without touching timing.
    widen     multiply pitch movement around the speaker's median (1 = as is, 1.4 = lively VO)
    emphasis  [(start_s, end_s)] key words: lifted by emph_st semitones and emph_db dB
    target    optional median pitch, Hz: the constant part of the shift goes through rubberband (clean),
              PSOLA only moves the melody around it. With Edge TTS raise pitch in the engine instead (--pitch)."""
    t, f0 = f0_track(x, sr)
    ap = f0_track.aper[: len(f0)]
    v = ~np.isnan(f0)
    if v.sum() < 20:
        return x
    med = float(np.median(f0[v]))
    if target:
        x = base_shift(x, 12 * np.log2(target / med), sr)
        t, f0 = f0_track(x, sr)
        ap = f0_track.aper[: len(f0)]
        v = ~np.isnan(f0)
        med = float(np.median(f0[v]))
    st = 12 * np.log2(np.where(v, f0, med) / med)
    st = np.convolve(st, np.ones(9) / 9, mode="same")  # follow the melody, not the jitter
    conf = np.clip((0.32 - ap) / 0.14, 0, 1)            # breathy / transitional frames stay untouched
    conf = np.convolve(conf, np.ones(7) / 7, mode="same")
    dev = (widen - 1) * np.clip(st, -8, 8)
    gain_db = np.zeros(len(f0))
    for s, e in emphasis:
        # smooth bump: rises 40 ms before the word, holds, falls by its end
        bump = np.clip(np.minimum((t - (s - 0.04)) / 0.06, ((e + 0.03) - t) / 0.08), 0, 1)
        dev = dev + emph_st * bump
        gain_db = np.maximum(gain_db, emph_db * bump)
    shift = np.clip(dev * conf, -4.5, 5.5)
    y = psola(x, t, f0, shift, sr)
    g = np.interp(np.arange(len(y)) / sr, t, 10 ** (gain_db / 20))
    return y * g


def master(x: np.ndarray, preset: str = "energetic", sr: int = SR) -> np.ndarray:
    if preset in ("off", None):
        return x
    chain = PRESETS[preset]
    pk = np.max(np.abs(x)) + 1e-9
    data = (x / pk * 0.5).astype(np.float32).tobytes()  # fixed input level so thresholds mean the same thing
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-f", "f32le", "-ar", str(sr), "-ac", "1", "-i", "pipe:0",
           "-af", chain, "-f", "f32le", "-ar", str(sr), "-ac", "1", "pipe:1"]
    y = np.frombuffer(subprocess.run(cmd, input=data, capture_output=True, check=True).stdout, dtype=np.float32).astype(np.float64)
    n = min(len(y), len(x))
    out = np.zeros(len(x))
    out[:n] = y[:n]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inp")
    ap.add_argument("out")
    ap.add_argument("--target", type=float, default=0, help="median pitch, Hz (0 = keep)")
    ap.add_argument("--widen", type=float, default=1.4, help="melody range multiplier")
    ap.add_argument("--preset", default="energetic", choices=[*PRESETS, "off"])
    a = ap.parse_args()
    sys.path.insert(0, str(Path(__file__).parent))
    from tts import decode_to_float, write_wav
    x = decode_to_float(path=a.inp)
    if a.target > 0 or a.widen != 1:
        x = expressive(x, a.widen, target=a.target or None)
    x = master(x, a.preset)
    write_wav(Path(a.out), x / (np.max(np.abs(x)) + 1e-9) * 0.89)


if __name__ == "__main__":
    main()
