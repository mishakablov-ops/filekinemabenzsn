"""Render the Blender clips of «Канал без лица» on the PC, one background Blender per shot, after the voice is done.

    python -I tools/render_clips.py --blender BLENDER_EXE [--rs RS] [--only k01,k05] [--samples 24]

1. tools/build_timeline.py on <RS>/engine/public/projects/kanal-bez-lica/words.json -> blender/shots.json (clip starts,
   lengths and in-shot events from the voice);
2. each shot -> JPEG frames in <seq-root>/<shot>_<hash>/ (default clips/_seq; the hash covers the shot's timing and the
   set code, so stale frames are never reused; resumable: finished frames are kept, empty placeholders are removed) -> ffmpeg H.264 clips/<shot>.mp4 (1080x1920, 30 fps, CRF 14, GOP 30, no B-frames for exact
   seeking); a middle frame -> clips/_check/<shot>.jpg and a contact sheet clips/_check/sheet.jpg for review;
   Blender's own log of each shot (frame times) -> clips/_check/<shot>.log
3. progress in clips/_check/progress.json (shot, frames, seconds), so a broken run can go on with --only.
Keep TEMP on C: (the flash drive is FAT32): the caller sets it.
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJ = HERE.parent
PID = "kanal-bez-lica"


# v2 (mike 25.11: «разделение на 2 экрана… вот такие уже есть стили»): the 1080×960 render on top as 3D, the same frames
# below as pixel art (1/6 size, 7 levels per channel, nearest-neighbour back up), a thin light line between them
PIXEL = ("scale=180:160:flags=area,lutrgb=r='trunc(val/36)*36+18':g='trunc(val/36)*36+18':b='trunc(val/36)*36+18',"
         "scale=1080:960:flags=neighbor")


def split_screen(ff, clip):
    tmp = clip.with_name(clip.stem + "_half.mp4")
    clip.replace(tmp)
    fc = f"[0:v]split[a][b];[b]{PIXEL}[p];[a][p]vstack,drawbox=x=0:y=956:w=1080:h=8:color=0xF2EFE8@0.95:t=fill[v]"
    e = subprocess.run([ff, "-y", "-loglevel", "error", "-i", str(tmp), "-filter_complex", fc, "-map", "[v]", "-c:v", "libx264",
                        "-crf", "14", "-preset", "medium", "-g", "30", "-bf", "0", "-pix_fmt", "yuv420p", "-movflags",
                        "+faststart", str(clip)], capture_output=True, text=True)
    if e.returncode:
        print("SPLIT FAILED", e.stderr[-1500:], flush=True)
        return False
    tmp.unlink()
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--blender", required=True)
    ap.add_argument("--rs", default=os.environ.get("KINEMA_RS", ""))
    ap.add_argument("--only", default="")
    ap.add_argument("--samples", type=int, default=24)
    ap.add_argument("--scale", type=float, default=1.0)
    ap.add_argument("--seq-root", default=os.environ.get("KANAL_SEQ", ""),
                    help="folder for the JPEG frames, best outside public/ (the KINEMA bundle copies all of public)")
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
    seq_root = Path(a.seq_root) if a.seq_root else clips / "_seq"
    set_md5 = {}
    prog_f = chk / "progress.json"
    prog = json.loads(prog_f.read_text(encoding="utf-8")) if prog_f.exists() else {}
    for s in S["shots"]:
        sid = s["id"]
        if only and sid not in only:
            continue
        out = clips / f"{sid}.mp4"
        # v2 (25.11): the frames folder is named by a hash of the shot (timing, events, camera code), so frames of an
        # older version of the shot are never mixed into a new clip; a broken run of the same shot still resumes
        if s["set"] not in set_md5:
            src = PROJ / "blender" / "sets" / f"{s['set']}.py"
            set_md5[s["set"]] = hashlib.md5(src.read_bytes()).hexdigest() if src.exists() else ""
        key = hashlib.md5((json.dumps(s, sort_keys=True, ensure_ascii=False) + set_md5[s["set"]] +
                           f"{a.samples}/{a.scale}").encode("utf-8")).hexdigest()[:8]
        seq = seq_root / f"{sid}_{key}"
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
        if ok and s.get("variant") == "split":
            ok = split_screen(ff, out)
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
