"""Render the 9 Blender clips of «Канал без лица» on the PC, one background Blender per shot, after the voice is done.

    python -I tools/render_clips.py --blender BLENDER_EXE [--rs RS] [--only k01,k05] [--samples 24]

1. tools/build_timeline.py on <RS>/engine/public/projects/kanal-bez-lica/words.json -> blender/shots.json (clip starts,
   lengths and in-shot events from the voice);
2. each shot -> JPEG frames in clips/_seq/<shot>/ (resumable: finished frames are kept, empty placeholders of a broken
   run are removed) -> ffmpeg H.264 clips/<shot>.mp4 (1080x1920, 30 fps, CRF 14, GOP 30, no B-frames for exact
   seeking); a middle frame -> clips/_check/<shot>.jpg and a contact sheet clips/_check/sheet.jpg for review;
   Blender's own log of each shot (frame times) -> clips/_check/<shot>.log
3. progress in clips/_check/progress.json (shot, frames, seconds), so a broken run can go on with --only.
Keep TEMP on C: (the flash drive is FAT32): the caller sets it.
"""
import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJ = HERE.parent
PID = "kanal-bez-lica"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--blender", required=True)
    ap.add_argument("--rs", default=os.environ.get("KINEMA_RS", ""))
    ap.add_argument("--only", default="")
    ap.add_argument("--samples", type=int, default=24)
    ap.add_argument("--scale", type=float, default=1.0)
    a = ap.parse_args()
    rs = Path(a.rs)
    kp = rs / "engine" / "public" / "projects" / PID
    clips = kp / "clips"
    chk = clips / "_check"
    chk.mkdir(parents=True, exist_ok=True)
    ff = rs / ".runtime" / "bin" / ("ffmpeg.exe" if os.name == "nt" else "ffmpeg")
    ff = str(ff) if ff.exists() else "ffmpeg"
    shots_json = PROJ / "blender" / "shots.json"
    r = subprocess.run([sys.executable, "-I", str(HERE / "build_timeline.py"), str(kp / "words.json"), str(shots_json)],
                       capture_output=True, text=True, encoding="utf-8")
    print(r.stdout, r.stderr, flush=True)
    if r.returncode:
        raise SystemExit("build_timeline failed")
    S = json.loads(shots_json.read_text(encoding="utf-8"))
    only = [x for x in a.only.split(",") if x]
    prog_f = chk / "progress.json"
    prog = json.loads(prog_f.read_text(encoding="utf-8")) if prog_f.exists() else {}
    for s in S["shots"]:
        sid = s["id"]
        if only and sid not in only:
            continue
        out = clips / f"{sid}.mp4"
        seq = clips / "_seq" / sid
        seq.mkdir(parents=True, exist_ok=True)
        for f in seq.glob("f_*.jpg"):
            if f.stat().st_size == 0:                # a placeholder of a frame that was never finished
                f.unlink()
        n = round(s["dur"] * 30)
        t0 = time.time()
        print(f"=== {sid} dur {s['dur']} s, {n} frames, {len(list(seq.glob('f_*.jpg')))} already there", flush=True)
        blog = chk / f"{sid}.log"
        with open(blog, "w", encoding="utf-8", errors="replace") as lf:
            r = subprocess.run([a.blender, "-b", "--factory-startup", "--python", str(PROJ / "blender" / "build_pc.py"), "--",
                                "--shot", sid, "--seq", str(seq), "--scale", str(a.scale), "--fps", "30",
                                "--samples", str(a.samples)], stdout=lf, stderr=subprocess.STDOUT)
        text = blog.read_text(encoding="utf-8", errors="replace")
        tail = [ln for ln in text.splitlines() if any(k in ln for k in ("BUILD", "SEQ", "Error", "rror:", "Traceback"))]
        print("\n".join(tail[-8:]), flush=True)
        frames = sorted(f for f in seq.glob("f_*.jpg") if f.stat().st_size > 0)
        ok = r.returncode == 0 and len(frames) >= n
        if ok:
            e = subprocess.run([ff, "-y", "-loglevel", "error", "-framerate", "30", "-start_number", "1",
                                "-i", str(seq / "f_%04d.jpg"), "-frames:v", str(n), "-c:v", "libx264", "-crf", "14",
                                "-preset", "medium", "-g", "30", "-bf", "0", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
                                str(out)], capture_output=True, text=True)
            ok = e.returncode == 0 and out.exists()
            if not ok:
                print("ENCODE FAILED", e.stderr[-1500:], flush=True)
        if ok:
            subprocess.run([ff, "-y", "-loglevel", "error", "-ss", f"{s['dur'] * 0.6:.2f}", "-i", str(out), "-frames:v", "1",
                            "-q:v", "3", str(chk / f"{sid}.jpg")])
        prog[sid] = dict(ok=ok, sec=round(time.time() - t0, 1), frames=round(s["dur"] * 30), at=time.strftime("%H:%M:%S"))
        prog_f.write_text(json.dumps(prog, indent=1), encoding="utf-8")
        if not ok:
            print(f"FAILED {sid}: exit {r.returncode}, frames {len(frames)}/{n}\n" + text[-3000:], flush=True)
    jpgs = [chk / f"{s['id']}.jpg" for s in S["shots"] if (chk / f"{s['id']}.jpg").exists()]
    if jpgs:
        ins = sum([["-i", str(j)] for j in jpgs], [])
        n = len(jpgs)
        fc = "".join(f"[{i}]scale=360:-1[v{i}];" for i in range(n)) + "".join(f"[v{i}]" for i in range(n)) + f"hstack={n}"
        subprocess.run([ff, "-y", "-loglevel", "error", *ins, "-filter_complex", fc, "-q:v", "3", str(chk / "sheet.jpg")])
    print("ALL CLIPS DONE", json.dumps(prog), flush=True)


if __name__ == "__main__":
    main()
