"""Shorten the silences between voice sections (mike 10.11.2026: «траблы с таймингом»).

voice_grid.py puts every section on a 10-second grid, which leaves up to 2+ s of dead air
after a short section. This tool cuts every gap between sections down to --max-gap seconds,
shifts words, cards and sections to match, and keeps the grid version as voice_grid.wav.

    python3 tighten_voice.py testosteron2 --max-gap 0.9
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
SR = 48000


def load(path: Path) -> np.ndarray:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", str(SR),
                          "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).copy()


def save(path: Path, a: np.ndarray) -> None:
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-",
                    "-c:a", "pcm_s16le", str(path)], input=a.astype(np.float32).tobytes(), check=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("id")
    ap.add_argument("--max-gap", type=float, default=0.9)
    ap.add_argument("--tail", type=float, default=0.12, help="audio kept after a section's last word")
    args = ap.parse_args()
    d = HERE / "narration" / args.id
    grid = d / "voice_grid.wav"
    if not grid.exists():
        shutil.copy2(d / "voice.wav", grid)
    a = load(grid)
    secs = json.loads((d / "sections.json").read_text(encoding="utf-8"))
    words = json.loads((d / "words.json").read_text(encoding="utf-8"))

    # offset applied to everything from each section on
    shift, off = [], 0.0
    for i, s in enumerate(secs):
        if i:
            gap = s["start"] - secs[i - 1]["end"]
            off += max(0.0, gap - args.max_gap)
        shift.append(off)

    out = []
    for i, s in enumerate(secs):
        t1 = s["end"] + args.tail if i < len(secs) - 1 else len(a) / SR
        if i:
            # piece = [prev end + tail + cut, this end + tail]: the cut part of the gap is dropped
            t0 = secs[i - 1]["end"] + args.tail + (shift[i] - shift[i - 1])
        else:
            t0 = 0.0
        out.append(a[int(round(t0 * SR)):int(round(t1 * SR))])
    voice = np.concatenate(out)
    save(d / "voice.wav", voice)

    sec_of = []
    for w in words["words"]:
        k = max(i for i, s in enumerate(secs) if w["start"] >= s["start"] - 0.05)
        sec_of.append(k)
        w["start"] = round(w["start"] - shift[k], 3)
        w["end"] = round(w["end"] - shift[k], 3)
    for c in words["cards"]:
        k = sec_of[c["words"][0]]
        c["start"] = round(c["start"] - shift[k], 3)
        c["end"] = round(c["end"] - shift[k], 3)
    words["duration"] = round(len(voice) / SR, 3)
    words["tightened"] = {"max_gap": args.max_gap, "cut_s": round(shift[-1], 3)}
    for i, s in enumerate(secs):
        s["start"] = round(s["start"] - shift[i], 3)
        s["end"] = round(s["end"] - shift[i], 3)
    (d / "words.json").write_text(json.dumps(words, ensure_ascii=False, indent=1), encoding="utf-8")
    (d / "sections.json").write_text(json.dumps(secs, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"duration": words["duration"], "cut_s": round(shift[-1], 3),
                      "sections": [(s["id"], s["start"], s["end"]) for s in secs]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
