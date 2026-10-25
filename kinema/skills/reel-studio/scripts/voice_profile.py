"""Voice profile: how lively a voiceover sounds, in numbers — compare TTS takes to reference reels.

    python voice_profile.py take1.wav take2.wav ... [--ref ref1.mp4 ref2.mp4 ...] [--json out.json]

Per file:
    f0       median pitch, Hz (young energetic male VO ≈ 115–150 Hz)
    range    pitch range p5–p95, semitones (monotone TTS ≈ 5–7, lively VO ≈ 9–13)
    move     mean pitch movement inside phrases, semitones/s (melody, not just range)
    dyn      loudness variation across syllables, dB (punch / emphasis)
    syl      syllable rate, 1/s (Russian VO in the references ≈ 6–7)
    talk     share of time speaking (rest = pauses)
    bright   spectral centroid of voiced frames, Hz
With --ref, every take also gets a distance to the reference average (lower = closer).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:
        pass

SR = 16000
FLOOR = 30.0  # dB below the loud parts that still counts as speech


def load(path: str) -> np.ndarray:
    raw = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", path, "-vn", "-ac", "1", "-ar", str(SR), "-f", "f32le", "pipe:1"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).astype(np.float64)


def frames(x: np.ndarray, win: int, hop: int) -> np.ndarray:
    n = max(0, 1 + (len(x) - win) // hop)
    idx = np.arange(win)[None, :] + hop * np.arange(n)[:, None]
    return x[idx]


def yin(x: np.ndarray, fmin=65.0, fmax=420.0, win_s=0.04, hop_s=0.01, th=0.15):
    """Vectorised YIN. Returns f0 per hop (nan = unvoiced) and the CMND minimum (aperiodicity)."""
    W, H = int(win_s * SR), int(hop_s * SR)
    tmin, tmax = int(SR / fmax), int(SR / fmin)
    out_f, out_a = [], []
    chunk = 4000  # frames per batch (memory)
    n_all = max(0, 1 + (len(x) - W - tmax) // H)
    for b0 in range(0, n_all, chunk):
        n = min(chunk, n_all - b0)
        idx = np.arange(W + tmax)[None, :] + H * (b0 + np.arange(n))[:, None]
        fr = x[idx]
        N = 1 << int(np.ceil(np.log2(2 * W + tmax)))
        acf = np.fft.irfft(np.conj(np.fft.rfft(fr[:, :W], N)) * np.fft.rfft(fr, N), N)[:, : tmax + 1]
        cs = np.concatenate([np.zeros((n, 1)), np.cumsum(fr ** 2, axis=1)], axis=1)
        taus = np.arange(tmax + 1)
        eb = cs[:, taus + W] - cs[:, taus]
        d = eb[:, :1] + eb - 2 * acf
        d = np.maximum(d, 0)
        cm = np.ones_like(d)
        cum = np.cumsum(d[:, 1:], axis=1)
        cm[:, 1:] = d[:, 1:] * np.arange(1, tmax + 1) / np.maximum(cum, 1e-12)
        sub = cm[:, tmin:]
        below = sub < th
        has = below.any(axis=1)
        t = np.where(has, np.argmax(below, axis=1), np.argmin(sub, axis=1)) + tmin
        for _ in range(40):  # walk down to the local minimum
            nxt = np.minimum(t + 1, tmax)
            step = cm[np.arange(n), nxt] < cm[np.arange(n), t]
            if not step.any():
                break
            t = np.where(step, nxt, t)
        r = np.arange(n)
        a = cm[r, t]
        tl, tr = np.maximum(t - 1, 1), np.minimum(t + 1, tmax)
        y0, y1, y2 = cm[r, tl], cm[r, t], cm[r, tr]
        den = y0 - 2 * y1 + y2
        with np.errstate(divide="ignore", invalid="ignore"):
            shift = np.where(np.abs(den) > 1e-12, 0.5 * (y0 - y2) / den, 0)
        f = SR / (t + np.clip(np.nan_to_num(shift), -1, 1))
        f[a > 0.35] = np.nan
        out_f.append(f)
        out_a.append(a)
    if not out_f:
        return np.array([]), np.array([])
    return np.concatenate(out_f), np.concatenate(out_a)


def bandpass_fft(x: np.ndarray, lo: float, hi: float) -> np.ndarray:
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    X[(f < lo) | (f > hi)] = 0
    return np.fft.irfft(X, len(x))


def profile(path: str) -> dict:
    x = load(path)
    x = x / (np.max(np.abs(x)) + 1e-9)
    hop = int(0.01 * SR)
    f0, aper = yin(x)
    fr = frames(x, int(0.04 * SR), hop)[: len(f0)]
    rms = 20 * np.log10(np.sqrt((fr ** 2).mean(axis=1)) + 1e-9)
    loud = rms > (np.percentile(rms, 95) - FLOOR)
    voiced = loud & ~np.isnan(f0)
    fv = f0[voiced]
    med = float(np.median(fv))
    st = 12 * np.log2(f0 / med)
    # octave-error guard: drop frames more than 10 st from the median
    ok = voiced & (np.abs(np.nan_to_num(st, nan=99)) < 10)
    stv = st[ok]
    p5, p95 = np.percentile(stv, [5, 95])
    # movement: |d st| between consecutive voiced frames inside a run, smoothed over 50 ms
    mv = []
    run = np.where(ok)[0]
    if len(run) > 3:
        seg_breaks = np.where(np.diff(run) > 1)[0]
        for seg in np.split(run, seg_breaks + 1):
            if len(seg) >= 8:
                s = np.convolve(st[seg], np.ones(5) / 5, mode="valid")
                mv.append(np.abs(np.diff(s)).sum() / (len(s) * 0.01))
    move = float(np.median(mv)) if mv else 0.0
    # syllable nuclei: peaks of the 300–2500 Hz envelope
    env = np.abs(bandpass_fft(x, 300, 2500))
    k = int(0.03 * SR)
    env = np.convolve(env, np.ones(k) / k, mode="same")[::hop][: len(rms)]
    env_db = 20 * np.log10(env + 1e-9)
    peaks = []
    floor = np.percentile(env_db, 95) - 25
    last = -99
    for i in range(1, len(env_db) - 1):
        if env_db[i] > floor and env_db[i] >= env_db[i - 1] and env_db[i] > env_db[i + 1]:
            lo = env_db[max(0, i - 8): i + 9].min()
            if env_db[i] - lo > 3 and i - last >= 9:  # ≥ 90 ms apart, 3 dB prominence
                peaks.append(i)
                last = i
    speech = loud.sum() * 0.01
    talk = float(speech / (len(x) / SR))
    syl = len(peaks) / max(speech, 0.1)
    dyn = float(np.std(env_db[peaks])) if peaks else 0.0
    # brightness of voiced frames
    win = np.hanning(fr.shape[1])
    spec = np.abs(np.fft.rfft(fr[ok] * win, axis=1))
    freqs = np.fft.rfftfreq(fr.shape[1], 1 / SR)
    cent = float(np.median((spec * freqs).sum(axis=1) / (spec.sum(axis=1) + 1e-12))) if ok.any() else 0.0
    return dict(file=Path(path).name, sec=round(len(x) / SR, 1), f0=round(med, 1), range=round(float(p95 - p5), 2),
                move=round(move, 1), dyn=round(dyn, 2), syl=round(float(syl), 2), talk=round(talk, 2), bright=round(cent))


KEYS = [("f0", 20.0), ("range", 2.0), ("move", 8.0), ("dyn", 1.5), ("syl", 0.6)]  # scale of "one unit of difference"


def distance(p: dict, ref: dict) -> float:
    return round(float(np.sqrt(sum(((p[k] - ref[k]) / s) ** 2 for k, s in KEYS) / len(KEYS))), 2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="*")
    ap.add_argument("--ref", nargs="*", default=[])
    ap.add_argument("--json", default=None)
    a = ap.parse_args()
    refs = [profile(f) for f in a.ref]
    takes = [profile(f) for f in a.files]
    ref_avg = {k: float(np.mean([r[k] for r in refs])) for k, _ in KEYS} if refs else None
    cols = ["file", "sec", "f0", "range", "move", "dyn", "syl", "talk", "bright"] + (["dist"] if ref_avg else [])
    rows = []
    for tag, group in (("ref", refs), ("take", takes)):
        for p in group:
            if ref_avg:
                p["dist"] = distance(p, ref_avg)
            rows.append((tag, p))
    w = max(len(p["file"]) for _, p in rows) if rows else 10
    print(f"{'':5}" + f"{'file':<{w}} " + " ".join(f"{c:>7}" for c in cols[1:]))
    for tag, p in rows:
        print(f"{tag:5}" + f"{p['file']:<{w}} " + " ".join(f"{p[c]:>7}" for c in cols[1:]))
    if ref_avg:
        print("ref avg " + "  ".join(f"{k} {v:.2f}" for k, v in ref_avg.items()))
    if a.json:
        Path(a.json).write_text(json.dumps(dict(ref=refs, takes=takes, ref_avg=ref_avg), ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
