"""Beat grid for ANY music track (your licensed song, a stock track) -> <track>.beats.json

    python beats.py song.mp3 [--out engine/public/music/song.beats.json] [--bpm 120]

Same schema as the generated beds: {bpm, beatSec, barSec, beats[], bars[], sections[], drops[], duration}.
Onset envelope (spectral flux) -> tempo by autocorrelation (70–180 bpm) -> beat phase by comb scoring
-> bar phase by low-end energy -> sections by energy novelty -> drops = sharp energy rises.
"""
from __future__ import annotations

import sys

import argparse
import json
import subprocess
from pathlib import Path

import numpy as np

# console: always UTF-8 (Windows defaults to cp1251)
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:
        pass

SR = 22050
HOP = 256


def load(path: str) -> np.ndarray:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR), "-f", "f32le", "pipe:1"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).astype(np.float64)


def stft_mag(x: np.ndarray, n: int = 1024) -> np.ndarray:
    w = np.hanning(n)
    frames = 1 + (len(x) - n) // HOP
    idx = np.arange(n)[None, :] + HOP * np.arange(frames)[:, None]
    return np.abs(np.fft.rfft(x[idx] * w, axis=1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("audio")
    ap.add_argument("--out")
    ap.add_argument("--bpm", type=float, help="force tempo")
    a = ap.parse_args()
    x = load(a.audio)
    dur = len(x) / SR
    S = stft_mag(x)
    logS = np.log1p(S * 10)
    flux = np.maximum(0, np.diff(logS, axis=0)).sum(axis=1)
    flux = np.concatenate([[0], flux])
    flux = (flux - flux.mean()) / (flux.std() + 1e-9)
    fr = SR / HOP  # frames per second
    # tempo: autocorrelation peak (parabolic refine) then a fine comb search over the whole track
    if a.bpm:
        bpm = a.bpm
    else:
        ac = np.correlate(flux, flux, mode="full")[len(flux) - 1:]
        lags = np.arange(len(ac))
        bpms = 60 * fr / np.maximum(lags, 1)
        mask = (bpms >= 70) & (bpms <= 180)
        weight = np.exp(-0.5 * (np.log2(bpms / 115) / 0.9) ** 2)  # mild prior around 115
        cand = lags[mask]
        best = int(cand[np.argmax((ac * weight)[mask])])
        y0, y1, y2 = ac[best - 1], ac[best], ac[best + 1]
        off = 0.5 * (y0 - y2) / (y0 - 2 * y1 + y2 + 1e-12)
        bpm = 60 * fr / (best + off)

    def comb(b):
        per = 60 / b * fr
        best_s, best_p = -1e9, 0
        for p0 in np.linspace(0, per, 48, endpoint=False):
            idx = np.round(np.arange(p0, len(flux), per)).astype(int)
            sc = flux[idx[idx < len(flux)]].sum()
            if sc > best_s:
                best_s, best_p = sc, p0
        return best_s, best_p

    if not a.bpm:
        grid_b = np.arange(bpm - 2.0, bpm + 2.0, 0.05)
        sc = [comb(b)[0] for b in grid_b]
        bpm = float(grid_b[int(np.argmax(sc))])
        if abs(bpm - round(bpm)) < 0.35:
            bpm = float(round(bpm))
    period = 60 / bpm * fr
    ph = comb(bpm)[1]
    beats = np.arange(ph, len(flux), period) / fr
    # bar phase: low-frequency energy at every 4th beat
    freqs = np.fft.rfftfreq(1024, 1 / SR)
    low = S[:, freqs < 150].sum(axis=1)
    bscore = [low[np.clip(np.round(beats[k::4] * fr).astype(int), 0, len(low) - 1)].sum() for k in range(4)]
    b0 = int(np.argmax(bscore))
    bars = beats[b0::4]
    # sections & drops: energy per bar, smoothed; a drop = bar where the next 2 bars are much louder than the previous 4
    rms = np.sqrt(np.convolve(x ** 2, np.ones(SR // 4) / (SR // 4), mode="same"))
    bar_e = np.array([rms[int(t * SR):int(min(len(rms), (t + 240 / bpm) * SR))].mean() if int(t * SR) < len(rms) else 0 for t in bars])
    bar_e = bar_e / (bar_e.max() + 1e-9)
    rise = np.array([bar_e[i:i + 2].mean() - bar_e[max(0, i - 4):i].mean() if i >= 2 else 0 for i in range(len(bars))])
    drops_i = [i for i in range(2, len(bars) - 1) if rise[i] > 0.18 and rise[i] >= rise[max(0, i - 2):i + 3].max()]
    drops = [round(float(bars[i]), 3) for i in drops_i]
    cuts = [0] + drops_i + [len(bars)]
    sections = [dict(name=f"s{k}", start=round(float(bars[c0]), 3) if c0 < len(bars) else round(dur, 3), end=round(float(bars[c1]), 3) if c1 < len(bars) else round(dur, 3),
                     energy=round(float(bar_e[c0:c1].mean()) if c1 > c0 else 0, 2)) for k, (c0, c1) in enumerate(zip(cuts, cuts[1:]))]
    grid = dict(bpm=round(float(bpm), 2), beatSec=round(60 / bpm, 5), barSec=round(240 / bpm, 5), beats=[round(float(b), 4) for b in beats], bars=[round(float(b), 4) for b in bars],
                sections=sections, drops=drops, duration=round(dur, 3), source=Path(a.audio).name)
    out = Path(a.out) if a.out else Path(a.audio).with_suffix(".beats.json")
    out.write_text(json.dumps(grid), encoding="utf-8")
    print(f"{Path(a.audio).name}: {bpm:.1f} bpm, {len(beats)} beats, {len(bars)} bars, {len(sections)} sections, drops {drops} -> {out}")


if __name__ == "__main__":
    main()
