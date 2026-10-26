"""Render a project to a finished, loudness-mastered MP4 and run QA.

    python render.py <project_id> [--preview] [--out FILE] [--concurrency 6] [--no-qa] [--frames 0-299]

  --preview   30 fps, half resolution, CRF 24 — fast check of timing and motion
  default     spec fps (60), 1080x1920, CRF 16, AAC 320k, then EBU R128 -14 LUFS / -1 dBTP
Outputs go to engine/out/<id>.mp4 (or --out). QA report: engine/out/<id>_qa.md
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

# console: always UTF-8 (Windows defaults to cp1251)
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:
        pass

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parent / "engine"
sys.path.insert(0, str(HERE))
from loudnorm import normalize  # noqa: E402

NPX = "npx.cmd" if os.name == "nt" else "npx"


def run_render(pid: str, out: Path, preview: bool, concurrency: int, frames: str | None) -> None:
    props = {"project": pid}
    if preview:
        props["fps"] = 30
    cmd = [NPX, "remotion", "render", "src/index.ts", "Reel", str(out), f"--props={json.dumps(props)}", f"--concurrency={concurrency}", "--log=warn"]
    if os.environ.get("REMOTION_GL"):  # GPU-less machines: REMOTION_GL=swangle
        cmd += [f"--gl={os.environ['REMOTION_GL']}"]
    if preview:
        cmd += ["--scale=0.5", "--crf=24"]
    if frames:
        cmd += [f"--frames={frames}"]
    t0 = time.time()
    print("render:", " ".join(cmd[:6]), "…", flush=True)
    r = subprocess.run(cmd, cwd=ENGINE)
    if r.returncode:
        raise SystemExit(f"remotion render failed ({r.returncode})")
    print(f"rendered in {time.time() - t0:.0f}s -> {out}", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--out")
    ap.add_argument("--concurrency", type=int, default=6)
    ap.add_argument("--no-qa", action="store_true")
    ap.add_argument("--frames")
    a = ap.parse_args()
    outdir = ENGINE / "out"
    outdir.mkdir(exist_ok=True)
    final = Path(a.out).resolve() if a.out else outdir / f"{a.project}{'_preview' if a.preview else ''}.mp4"
    raw = outdir / f"{a.project}_raw.mp4"
    run_render(a.project, raw, a.preview, a.concurrency, a.frames)
    m = normalize(str(raw), str(final), -14.0, -1.0)
    print(f"loudness {m['input_i']} LUFS -> -14 LUFS, true peak target -1 dBTP -> {final}")
    raw.unlink(missing_ok=True)
    if not a.preview and not a.frames:
        add_cover(a.project, final)
    if not a.no_qa:
        subprocess.run([sys.executable, "-I", str(HERE / "qa.py"), str(final), "--project", a.project] + (["--quick"] if a.preview else []))


def add_cover(pid: str, video: Path) -> None:
    """Put a cover of the finished reel at the front of the channel's video grid (TikTokProfile tiles in brand.json)."""
    brand_path = ENGINE / "src" / "brand.json"
    if not brand_path.exists():
        return
    tiles_dir = ENGINE / "public" / "brand" / "tiles"
    tiles_dir.mkdir(parents=True, exist_ok=True)
    cover = tiles_dir / f"{pid}.jpg"
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(video)],
                               capture_output=True, text=True).stdout.strip() or 4)
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{dur * 0.3:.2f}", "-i", str(video), "-frames:v", "1",
                    "-vf", "crop=1080:1440:0:240,scale=270:360", "-q:v", "3", str(cover)])
    if not cover.exists():
        return
    brand = json.loads(brand_path.read_text(encoding="utf-8"))
    rel = f"brand/tiles/{pid}.jpg"
    brand["tiles"] = ([rel] + [t for t in brand.get("tiles", []) if t != rel])[:12]
    brand_path.write_text(json.dumps(brand, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
