"""Quick look at single shots of a reel: copies the chosen scenes (same props/ev as the reel) into a scratch project,
renders a few frames of each and glues them into one sheet (columns = shots, rows = moments).

    python -I lab.py footprints crack_grow ... [--project sosed6] [--at 0.15,0.5,0.9] [--scale 0.45]   -> engine/out/s6lab_sheet.png
A shot is found by its `shot` (or insert `kind`) prop; a name that is not in the reel is rendered with empty `ev`.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image

RS = Path(__file__).resolve().parents[3]
ENG = RS / "engine"
ap = argparse.ArgumentParser()
ap.add_argument("shots", nargs="+")
ap.add_argument("--project", default="sosed6")
ap.add_argument("--at", default="0.12,0.5,0.88", help="moments as fractions of each shot")
ap.add_argument("--scale", type=float, default=0.42)
ap.add_argument("--dur", type=float, default=None, help="override shot length (s)")
a = ap.parse_args()
sys.stdout.reconfigure(encoding="utf-8")
SPEC = ENG / "public" / "projects" / a.project / "spec.json"
LAB = ENG / "public" / "projects" / "s6-lab" / "spec.json"
LAB.parent.mkdir(parents=True, exist_ok=True)
W = json.loads((ENG / "public" / "projects" / a.project / "words.json").read_text(encoding="utf-8"))

spec = json.loads(SPEC.read_text(encoding="utf-8"))
scenes = spec["scenes"]


def key(sc):
    p = sc["bg"].get("props", {})
    return p.get("shot") or p.get("kind")


# scene lengths in the reel: next scene start - this start, from the words (approximate: ignores the 0.07 lead)
def start_of(sc, prev):
    at = sc["at"]
    if at == 0:
        return 0.0
    ph = at[1:].split("+")[0]
    toks = [t.lower().strip(".,:;!?«»\"") for t in ph.split()]
    ws = W["words"] if isinstance(W, dict) else W
    for i, x in enumerate(ws):
        if x["start"] < prev - 0.05:
            continue
        if all(i + k < len(ws) and ws[i + k]["text"].lower().strip(".,:;!?«»\"/").startswith(toks[k]) for k in range(len(toks))):
            return x["start"]
    return prev + 2


starts, prev = [], 0.0
for sc in scenes:
    prev = start_of(sc, prev)
    starts.append(prev)
lens = {key(sc): (starts[i + 1] if i + 1 < len(starts) else starts[i] + 4) - starts[i] for i, sc in enumerate(scenes)}

chosen = []
for name in a.shots:
    sc = next((s for s in scenes if key(s) == name), None)
    if sc is None:
        block = next((s["bg"]["block"] for s in scenes if s["bg"]["block"] != "S6Insert"), "S6Shot")
        sc = {"bg": {"block": block, "props": {"shot": name, "ev": {}}}}
    chosen.append((name, sc, a.dur or lens.get(name, 2.0)))

lab_scenes, t0, secs = [], 0.0, []
fr = [float(x) for x in a.at.split(",")]
for name, sc, d in chosen:
    lab_scenes.append({"id": name, "at": round(t0, 3), "camera": "still", "transition": "cut", "bg": sc["bg"]})
    secs.append([round(t0 + max(0.03, min(d - 0.03, f * d)), 3) for f in fr])
    t0 += d
LAB.write_text(json.dumps({"id": "s6-lab", "mode": "promo", "style": "dusk", "fps": 30, "duration": round(t0 + 0.1, 3), "captions": {"mode": "none"}, "scenes": lab_scenes}, ensure_ascii=False, indent=1), encoding="utf-8")

flat = [s for row in secs for s in row]
out = ENG / "out" / "s6lab"
for f in out.glob("*.png") if out.exists() else []:
    f.unlink()
cmd = ["node", "tools/stills.mjs", "--props", json.dumps({"project": "s6-lab"}), "--seconds", ",".join(str(x) for x in flat), "--scale", str(a.scale), "--out", "out/s6lab"]
r = subprocess.run(cmd, cwd=ENG, capture_output=True, text=True, encoding="utf-8", errors="replace", shell=(sys.platform == "win32"))
if r.returncode:
    print(r.stdout[-2000:], r.stderr[-3000:])
    raise SystemExit("stills failed")
files = sorted(out.glob("f*.png"))
ims = [Image.open(f).convert("RGB") for f in files]
w, h = ims[0].size
cols, rows = len(chosen), len(fr)
sheet = Image.new("RGB", (w * cols, h * rows))
for i, im in enumerate(ims):
    shot_i, mom = divmod(i, rows)
    sheet.paste(im, (shot_i * w, mom * h))
sheet.save(ENG / "out" / "s6lab_sheet.png")
print("sheet", ENG / "out" / "s6lab_sheet.png", f"{cols}x{rows}", [(n, round(d, 2)) for n, _, d in chosen])
