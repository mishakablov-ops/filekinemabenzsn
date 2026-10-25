"""Quality gate for a rendered reel. Writes <video>_qa.md / _qa.json and a contact sheet.

    python qa.py <video.mp4> [--project id] [--quick] [--strict]

Checks
  format     1080x1920, h264 yuv420p, 30/60 fps, AAC 48 kHz stereo
  loudness   integrated -14 ±1 LUFS, true peak <= -1 dBTP
  black      black frames >= 0.15 s (dead frames between scenes)
  freeze     picture frozen >= 1.5 s (nothing moves = viewers swipe)
  silence    audio gaps >= 0.8 s (except the last second)
  rhythm     average shot length from scene cuts (explainers 1.2–4 s); any shot < MIN_SHOT (1 s) = error
  captions   pace, cards on screen < 0.35 s, longest card
  layout     overlap / safe-zone / 3D-collision check rendered by the engine (--project, skipped with --quick)
  sheet      contact sheet every 1.5 s for visual review (<video>_sheet.png)
Exit code 1 when an error-level check fails (or any warning with --strict).
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

# console: always UTF-8 (Windows defaults to cp1251)
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:
        pass

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parent / "engine"


MIN_SHOT = 1.0  # seconds; no flash cuts


def sh(cmd: list[str]) -> str:
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.stdout + r.stderr


def probe(v: str) -> dict:
    out = sh(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,codec_name,width,height,r_frame_rate,pix_fmt,sample_rate,channels:format=duration", "-of", "json", v])
    return json.loads(out[out.index("{"):])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--project")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--strict", action="store_true")
    a = ap.parse_args()
    v = str(Path(a.video).resolve())
    base = str(Path(v).with_suffix(""))
    res: list[dict] = []

    def add(check, level, msg):
        res.append(dict(check=check, level=level, msg=msg))

    info = probe(v)
    dur = float(info["format"]["duration"])
    vs = next(s for s in info["streams"] if s["codec_type"] == "video")
    au = next((s for s in info["streams"] if s["codec_type"] == "audio"), None)
    num, den = map(int, vs["r_frame_rate"].split("/"))
    fps = num / den
    if (vs["width"], vs["height"]) != (1080, 1920):
        add("format", "warn" if a.quick else "error", f"{vs['width']}x{vs['height']} (expected 1080x1920)")
    if vs["codec_name"] != "h264" or vs.get("pix_fmt") != "yuv420p":
        add("format", "error", f"{vs['codec_name']} {vs.get('pix_fmt')} (expected h264 yuv420p)")
    if round(fps) not in (30, 60):
        add("format", "warn", f"{fps:.2f} fps")
    if not au:
        add("format", "error", "no audio stream")
    elif int(au["sample_rate"]) != 48000:
        add("format", "warn", f"audio {au['sample_rate']} Hz")

    # loudness
    lo = sh(["ffmpeg", "-hide_banner", "-nostats", "-i", v, "-af", "ebur128=peak=true", "-f", "null", "-"])
    m_i = re.findall(r"I:\s+(-?[\d.]+) LUFS", lo)
    m_tp = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", lo)
    if m_i:
        I = float(m_i[-1])
        TP = float(m_tp[-1]) if m_tp else 0.0
        if abs(I + 14) > 1.0:
            add("loudness", "error", f"integrated {I} LUFS (target -14 ±1)")
        if TP > -0.9:
            add("loudness", "warn", f"true peak {TP} dBTP (> -1)")
        loud = f"{I} LUFS, TP {TP}"
    else:
        loud = "n/a"

    # black / freeze / silence
    bl = sh(["ffmpeg", "-hide_banner", "-nostats", "-i", v, "-vf", "blackdetect=d=0.15:pix_th=0.04", "-an", "-f", "null", "-"])
    for s, e in re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", bl):
        if float(s) > 0.05 and float(e) < dur - 0.3:
            add("black", "error", f"black frames {float(s):.2f}–{float(e):.2f}s")
    fr = sh(["ffmpeg", "-hide_banner", "-nostats", "-i", v, "-vf", "freezedetect=n=0.0008:d=1.5", "-an", "-f", "null", "-"])
    for s, d in re.findall(r"freeze_start: ([\d.]+)[\s\S]*?freeze_duration: ([\d.]+)", fr):
        add("freeze", "warn", f"picture frozen {float(s):.2f}s for {float(d):.1f}s")
    si = sh(["ffmpeg", "-hide_banner", "-nostats", "-i", v, "-af", "silencedetect=noise=-42dB:d=0.8", "-vn", "-f", "null", "-"])
    for s, e in re.findall(r"silence_start: ([\d.]+)[\s\S]*?silence_end: ([\d.]+)", si):
        if float(e) < dur - 1.0:
            add("silence", "warn", f"audio gap {float(s):.2f}–{float(e):.2f}s")

    # rhythm (pixel cuts; replaced by the engine's real scene list when --project QA runs below)
    sc = sh(["ffmpeg", "-hide_banner", "-nostats", "-i", v, "-vf", "select='gt(scene,0.22)',showinfo", "-an", "-f", "null", "-"])
    cuts = [float(x) for x in re.findall(r"pts_time:([\d.]+)", sc)]
    shots = len(cuts) + 1
    asl = dur / shots
    if asl > 4.5:
        add("rhythm", "warn", f"average shot {asl:.1f}s — too static for a reel (aim 1.2–4 s; add scene changes / camera moves)")
    if asl < 0.6:
        add("rhythm", "warn", f"average shot {asl:.2f}s — chaotic")

    # captions (from words.json)
    cap = ""
    if a.project:
        wpath = ENGINE / "public" / "projects" / a.project / "words.json"
        if wpath.exists():
            W = json.loads(wpath.read_text(encoding="utf-8"))
            ws = W["words"]
            if ws:
                span = ws[-1]["end"] - ws[0]["start"]
                wps = len(ws) / max(span, 0.1)
                cards = W["cards"]
                nxt = [c2["start"] for c2 in cards[1:]] + [dur]
                on = [n - c["start"] for c, n in zip(cards, nxt)]
                short = [c["i"] for c, o in zip(cards, on) if o < 0.35]
                cap = f"{len(ws)} words, {wps:.2f} w/s, {len(cards)} cards, longest card {max(on):.1f}s"
                if short:
                    add("captions", "warn", f"cards on screen < 0.35 s: {short}")
                if wps > 3.4:
                    add("captions", "warn", f"pace {wps:.2f} w/s is hard to read")
                if ws[0]["start"] > 0.4:
                    add("captions", "warn", f"first word at {ws[0]['start']:.2f}s — hook should start immediately")

    # layout QA via engine
    layout = "skipped"
    if a.project and not a.quick:
        qdir = ENGINE / "out" / f"{a.project}_qa"
        cmd = ["node", "tools/stills.mjs", "--comp", "Reel", "--props", json.dumps({"project": a.project, "fps": 30}), "--every", "0.5", "--out", str(qdir), "--scale", "0.35", "--qa"]
        out = subprocess.run(cmd, cwd=ENGINE, capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
        qj = qdir / "qa.json"
        if qj.exists():
            qa = json.loads(qj.read_text(encoding="utf-8"))
            n = 0
            scene_starts = None
            for q in qa:
                for it in q.get("issues", []):
                    n += 1
                    if n <= 12:
                        add("layout", "error" if it["kind"] == "overlap" else "warn", f"{q.get('t', '?')}s {it['kind']}: {it['a']}{(' × ' + it['b']) if it.get('b') else ''} @ {it['r']}")
                for c3 in q.get("collisions3d", []):
                    n += 1
                    if n <= 12:
                        add("layout", "error", f"frame {q.get('frame')}: 3D collision {c3}")
                for p in q.get("plan", []):
                    n += 1
                    add("plan", "error", p)
                if q.get("scenes"):
                    scene_starts = q["scenes"]
            layout = f"{n} issue(s)" if n else "clean"
            if scene_starts:
                shots = len(scene_starts)
                asl = dur / shots
                res[:] = [r for r in res if r["check"] != "rhythm"]
                if asl > 4.5:
                    add("rhythm", "warn", f"average scene {asl:.1f}s — too static (aim 1.2–4 s)")
                # the user hates shots that flash by ("дверь на долю секунды"): every shot must be readable
                lens = [b2 - a2 for a2, b2 in zip(scene_starts, scene_starts[1:] + [dur])]
                flash = [f"{scene_starts[i]:.2f}s ({l:.2f}s)" for i, l in enumerate(lens) if l < MIN_SHOT]
                if flash:
                    add("rhythm", "error", f"shots shorter than {MIN_SHOT}s flash by: {flash}")
        else:
            layout = "failed to run: " + out[-300:]
            add("layout", "warn", layout)

    # contact sheet
    sheet = base + "_sheet.png"
    step = 1.5
    n_tiles = max(1, int(dur / step))
    cols = 8
    rows = (n_tiles + cols - 1) // cols
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", v, "-vf", f"fps=1/{step},scale=270:-1,tile={cols}x{rows}:padding=4:color=0x202020", "-frames:v", "1", sheet])

    errs = [r for r in res if r["level"] == "error"]
    warns = [r for r in res if r["level"] == "warn"]
    status = "FAIL" if errs or (a.strict and warns) else "PASS"
    md = [f"# QA {Path(v).name}: {status}", "", f"- duration {dur:.2f}s · {vs['width']}x{vs['height']} @ {fps:.0f} fps · loudness {loud}",
          f"- shots {shots} · average shot length {asl:.2f}s", f"- captions: {cap or 'n/a'}", f"- layout: {layout}", f"- contact sheet: {sheet}", ""]
    for r in res:
        md.append(f"- **{r['level'].upper()}** [{r['check']}] {r['msg']}")
    if not res:
        md.append("- no problems found")
    Path(base + "_qa.md").write_text("\n".join(md), encoding="utf-8")
    Path(base + "_qa.json").write_text(json.dumps(dict(status=status, duration=dur, fps=fps, loudness=loud, asl=asl, results=res), ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n".join(md))
    sys.exit(1 if status == "FAIL" else 0)


if __name__ == "__main__":
    main()
