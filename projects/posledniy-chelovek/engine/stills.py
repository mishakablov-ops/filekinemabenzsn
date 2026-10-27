"""QA stills + contact sheet for posledniy-chelovek: by default the start (+0.5 s) and the end (-0.4 s) of every scene.
    python -I stills.py [--seconds 1.0,3.2,...] [--out DIR] [--scale 0.4]
On a machine without a GPU set REMOTION_GL=swangle (WebGL on the CPU).
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ENG = ROOT / "kinema" / "skills" / "reel-studio" / "engine"
PID = "posledniy-chelovek"
P = ENG / "public" / "projects" / PID


def scene_starts():
    words = json.loads((P / "words.json").read_text(encoding="utf-8"))["words"]
    spec = json.loads((P / "spec.json").read_text(encoding="utf-8"))
    norm = lambda s: re.sub(r"[^a-zа-я0-9 ]", "", s.lower().replace("ё", "е"))
    toks = [norm(w["text"]) for w in words]
    out = []
    pos = 0
    for sc in spec["scenes"]:
        a = sc["at"]
        if isinstance(a, (int, float)):
            out.append((sc["id"], float(a)))
            continue
        phrase = norm(a.lstrip("@").split("+")[0].split("#")[0]).split()
        for i in range(pos, len(toks)):
            if toks[i:i + len(phrase)] == phrase:
                out.append((sc["id"], words[i]["start"]))
                pos = i
                break
        else:
            raise SystemExit(f"anchor not found: {a}")
    return out, words[-1]["end"] + spec.get("tail", 1.5)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seconds")
    ap.add_argument("--out", default=str(ENG / "out" / f"{PID}_st"))
    ap.add_argument("--scale", default="0.4")
    ap.add_argument("--cols", default="8")
    a = ap.parse_args()
    if a.seconds:
        secs = a.seconds
    else:
        st, total = scene_starts()
        ts = []
        for i, (sid, t0) in enumerate(st):
            t1 = st[i + 1][1] if i + 1 < len(st) else total
            ts += [t0 + 0.5, max(t0 + 0.6, t1 - 0.4)]
            print(f"{sid:10} {t0:6.2f} - {t1:6.2f}  ({t1 - t0:4.1f} s)")
        secs = ",".join(f"{t:.2f}" for t in ts)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    cmd = ["node", "tools/stills.mjs", "--comp", "Reel", "--props", json.dumps({"project": PID}), "--seconds", secs,
           "--out", str(out), "--scale", a.scale, "--sheet", str(out / "sheet.png"), "--cols", a.cols, "--qa"]
    r = subprocess.run(cmd, cwd=ENG, capture_output=True, text=True, encoding="utf-8", errors="replace")
    log = (r.stdout or "") + "\n---stderr---\n" + (r.stderr or "")
    (out / "log.txt").write_text(log, encoding="utf-8")
    keep = [ln for ln in log.splitlines() if ln.strip() and not ln.strip().startswith(("at ", "columnNumber", "fileName", "functionName", "lineNumber", "{", "}", "},", "Detected differing", "Memory reported", "You might", "Using the lower"))]
    print("\n".join(keep[-40:]))
    print("stills exit", r.returncode)
    sys.exit(r.returncode)


if __name__ == "__main__":
    main()
