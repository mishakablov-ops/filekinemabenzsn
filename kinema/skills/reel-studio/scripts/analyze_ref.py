"""Deconstruct a reference reel so its style can be matched (or beaten).

    python analyze_ref.py video.mp4 [--out DIR] [--whisper small|medium] [--lang ru]

Writes to DIR (default: <video>_ref/):
  sheet_*.png      contact sheets, 1 frame/s, 6x4 per sheet, in order (read them!)
  transcript.txt   text + word timings (faster-whisper)
  cuts.txt         scene-cut timestamps
  report.md        format, loudness, pace (words/s), pauses, shot lengths, hook timing, dominant colours,
                   caption-band guess, and a checklist of what to copy / improve
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))


# console: always UTF-8 (Windows defaults to cp1251)
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:
        pass

def sh(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.stdout + r.stderr


def frames_at(v: str, times: list[float], w: int = 108, h: int = 192) -> np.ndarray:
    out = []
    for t in times:
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", v, "-frames:v", "1", "-vf", f"scale={w}:{h}", "-f", "rawvideo", "-pix_fmt", "rgb24", "pipe:1"], capture_output=True).stdout
        if len(raw) == w * h * 3:
            out.append(np.frombuffer(raw, dtype=np.uint8).reshape(h, w, 3))
    return np.array(out)


def palette(fr: np.ndarray, k: int = 6) -> list[str]:
    px = fr.reshape(-1, 3).astype(np.float64)
    q = (px // 32).astype(int)
    keys, counts = np.unique(q[:, 0] * 64 + q[:, 1] * 8 + q[:, 2], return_counts=True)
    top = keys[np.argsort(-counts)[:k]]
    cols = []
    for key in top:
        m = (q[:, 0] * 64 + q[:, 1] * 8 + q[:, 2]) == key
        c = px[m].mean(axis=0)
        cols.append("#%02X%02X%02X" % tuple(int(v) for v in c))
    return cols


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--out")
    ap.add_argument("--whisper", default="small")
    ap.add_argument("--lang", default="ru")
    a = ap.parse_args()
    v = str(Path(a.video).resolve())
    out = Path(a.out) if a.out else Path(v).with_name(Path(v).stem + "_ref")
    out.mkdir(parents=True, exist_ok=True)
    info = json.loads(sh(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height,r_frame_rate:format=duration", "-of", "json", v]))
    dur = float(info["format"]["duration"])
    vs = next(s for s in info["streams"] if s["codec_type"] == "video")
    # contact sheets
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", v, "-vf", "fps=1,scale=270:-1,tile=6x4:padding=3", str(out / "sheet_%02d.png")])
    # loudness
    lo = sh(["ffmpeg", "-hide_banner", "-nostats", "-i", v, "-af", "ebur128", "-f", "null", "-"])
    I = re.findall(r"I:\s+(-?[\d.]+) LUFS", lo)
    # cuts
    sc = sh(["ffmpeg", "-hide_banner", "-nostats", "-i", v, "-vf", "select='gt(scene,0.25)',showinfo", "-an", "-f", "null", "-"])
    cuts = [float(x) for x in re.findall(r"pts_time:([\d.]+)", sc)]
    (out / "cuts.txt").write_text("\n".join(f"{c:.2f}" for c in cuts), encoding="utf-8")
    shots = np.diff([0.0] + cuts + [dur])
    # transcript
    from tts import whisper_words
    words = whisper_words(v, lang=a.lang, model=a.whisper)
    (out / "transcript.txt").write_text(" ".join(w[2] for w in words) + "\n\n" + "\n".join(f"{s:6.2f} {e:6.2f} {t}" for s, e, t in words), encoding="utf-8")
    wps = len(words) / max(1e-3, (words[-1][1] - words[0][0])) if words else 0
    gaps = [b[0] - a_[1] for a_, b in zip(words, words[1:])]
    # palette + brightness
    fr = frames_at(v, list(np.linspace(0.5, dur - 0.5, 16)))
    pal = palette(fr) if len(fr) else []
    bright = float(fr.mean() / 255) if len(fr) else 0
    rep = [
        f"# Reference: {Path(v).name}",
        "",
        f"- format {vs['width']}x{vs['height']} @ {vs['r_frame_rate']} · {dur:.1f}s · loudness {I[-1] if I else 'n/a'} LUFS",
        f"- voice: {len(words)} words · {wps:.2f} words/s · first word at {words[0][0]:.2f}s" if words else "- voice: none detected (music promo?)",
        f"- pauses > 0.4 s: {sum(1 for g in gaps if g > 0.4)} · longest {max(gaps) if gaps else 0:.2f}s",
        f"- shots: {len(shots)} · average {shots.mean():.2f}s · median {np.median(shots):.2f}s · longest {shots.max():.2f}s",
        f"- dominant colours: {', '.join(pal)} · mean brightness {bright:.2f} ({'dark' if bright < 0.35 else 'light' if bright > 0.6 else 'mid'})",
        "",
        "## Read next",
        f"- contact sheets: {out}/sheet_*.png (1 frame per second, left→right, top→bottom)",
        f"- transcript with timings: {out}/transcript.txt",
        "",
        "## Fill in after looking at the sheets",
        "- caption system: position band, lead/punch hierarchy, accent treatment (serif italic / colour / box), reveal type",
        "- background families and how often they change",
        "- block types used per beat (UI mockups, counters, 3D, footage)",
        "- transitions and camera moves",
        "- script formula: hook → … → CTA (write the beat list)",
        "- what to beat: weak spots (static shots > 4 s, unreadable text, repeated layouts, generic visuals)",
    ]
    (out / "report.md").write_text("\n".join(rep), encoding="utf-8")
    print("\n".join(rep))


if __name__ == "__main__":
    main()
