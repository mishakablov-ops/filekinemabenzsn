"""EBU R128 loudness normalisation: measure, then one static gain (+ peak limiter only when needed).

python loudnorm.py in.(wav|mp4) out.(wav|mp4) [--lufs -14] [--tp -1.0]
For video input the video stream is copied untouched and only audio is re-encoded (AAC 320k).
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys


# console: always UTF-8 (Windows defaults to cp1251)
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:
        pass

def measure(path: str, lufs: float, tp: float) -> dict:
    cmd = ["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af",
           f"loudnorm=I={lufs}:TP={tp}:LRA=11:print_format=json", "-f", "null", "-"]
    err = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace").stderr
    m = re.findall(r"\{[^{}]*\"input_i\"[^{}]*\}", err, re.S)
    if not m:
        raise RuntimeError("loudnorm measure failed:\n" + err[-2000:])
    return json.loads(m[-1])


def normalize(src: str, dst: str, lufs: float = -14.0, tp: float = -1.0) -> dict:
    """Static gain to the target loudness — never ffmpeg's dynamic loudnorm mode (it pumps and colours voices).
    Only if the gained peaks would pass the ceiling does a look-ahead limiter shave those peaks."""
    m = measure(src, lufs, tp)
    gain = lufs - float(m["input_i"])
    af = f"volume={gain:.2f}dB"
    if float(m["input_tp"]) + gain > tp:
        # sample-peak limiter a little under the ceiling: inter-sample peaks overshoot by up to ~1 dB
        af += f",alimiter=limit={10 ** ((tp - 1.6) / 20):.4f}:attack=2:release=60:level=disabled"
    af += ",aresample=48000"
    m["gain_db"] = round(gain, 2)
    is_video = dst.lower().endswith((".mp4", ".mov", ".mkv"))
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", src, "-af", af]
    if is_video:
        cmd += ["-c:v", "copy", "-c:a", "aac", "-b:a", "320k", "-movflags", "+faststart"]
    elif dst.lower().endswith(".mp3"):
        cmd += ["-c:a", "libmp3lame", "-b:a", "192k"]
    else:
        cmd += ["-c:a", "pcm_s16le"]
    cmd.append(dst)
    subprocess.run(cmd, check=True)
    return m


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--lufs", type=float, default=-14.0)
    ap.add_argument("--tp", type=float, default=-1.0)
    a = ap.parse_args()
    m = normalize(a.src, a.dst, a.lufs, a.tp)
    print(f"{a.src}: {m['input_i']} LUFS -> {a.lufs} LUFS", file=sys.stderr)
