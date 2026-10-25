"""Final narration: N takes per section with the chosen Replicate voice -> voice/final/<engine>_<voice>/
python tts_final.py --engine gemini --voice Charon --takes 2
"""
import argparse, json, os, pathlib, subprocess, sys, time
for s in (sys.stdout, sys.stderr):
    try: s.reconfigure(encoding="utf-8")
    except Exception: pass
ROOT = pathlib.Path(__file__).resolve().parents[2]
RS = ROOT.parent / "AIpollon-Reel-Studio" / "skills" / "reel-studio"
FF = str(RS / ".runtime" / "bin" / "ffmpeg.exe")
for line in (ROOT / ".secrets.env").read_text(encoding="utf-8").splitlines():
    if line.startswith("REPLICATE_API_TOKEN="):
        os.environ["REPLICATE_API_TOKEN"] = line.split("=", 1)[1].strip()
sys.path.insert(0, str(RS / "scripts"))
import replicate_tts as rt

BASE = ("Read this Russian script aloud as a native Russian documentary narrator for a popular-science short video: warm, pleasant, "
        "confident and engaging. Brisk natural pace, very short pauses between sentences, clear diction, never whispering, never "
        "theatrical. Perfect native Russian pronunciation, no foreign accent. Mood for this part: ")
MOOD = {"s1": "intriguing, inviting, a touch of wonder", "s2": "confident and factual, weighty on the numbers",
        "s3": "brighter, hopeful, opening up", "s4": "energetic, a sense of movement", "s5": "thoughtful, then concerned",
        "s6": "serious, questioning", "s7": "darker and grave, heavy on the last word", "s8": "calm and sincere, a reflective question at the end",
        "s9": "friendly and casual, a light smile"}
MM_EMO = {"s1": "neutral", "s2": "neutral", "s3": "happy", "s4": "neutral", "s5": "neutral", "s6": "neutral", "s7": "sad", "s8": "neutral", "s9": "happy"}

ap = argparse.ArgumentParser()
ap.add_argument("--engine", required=True)
ap.add_argument("--voice", required=True)
ap.add_argument("--takes", type=int, default=2)
ap.add_argument("--only", default="")
ap.add_argument("--speed", type=float, default=None)
a = ap.parse_args()
secs = json.loads((ROOT / "voice" / "sections.json").read_text(encoding="utf-8"))
out = ROOT / "voice" / "final" / f"{a.engine}_{a.voice}"
out.mkdir(parents=True, exist_ok=True)
only = set(filter(None, a.only.split(",")))
for sec in secs:
    sid = sec["id"]
    if only and sid not in only: continue
    for t in range(1, a.takes + 1):
        dst = out / f"{sid}_t{t}.wav"
        if dst.exists(): continue
        if a.engine == "gemini":
            style = BASE + MOOD.get(sid, "")
        elif a.engine == "minimax":
            style = MM_EMO.get(sid, "neutral")
        elif a.engine == "eleven":
            style = "[calm, confident]"
        else:
            style = None
        for attempt in range(3):
            try:
                data = rt.synth(a.engine, sec["text"], a.voice, style, a.speed)
                raw = out / f"{sid}_t{t}.raw"
                raw.write_bytes(data)
                subprocess.run([FF, "-v", "error", "-y", "-i", str(raw), "-ac", "1", "-ar", "48000", str(dst)], check=True)
                print("ok", dst.name, flush=True)
                break
            except BaseException as e:
                print("retry", sid, t, repr(e)[:300], flush=True)
                time.sleep(5)
manifest = [{"name": f"{p.stem}", "section": p.stem.split("_")[0], "file": p.name, "text": next(s["text"] for s in secs if s["id"] == p.stem.split("_")[0])}
            for p in sorted(out.glob("s*_t*.wav"))]
(out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
print("DONE", len(manifest))
