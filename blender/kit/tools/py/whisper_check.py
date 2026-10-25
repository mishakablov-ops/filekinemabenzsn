"""Transcribe every take with faster-whisper and score it against the expected text -> voice/takes/check.json"""
import json, pathlib, re, sys, difflib, wave, subprocess
for s in (sys.stdout, sys.stderr):
    try: s.reconfigure(encoding="utf-8")
    except Exception: pass
ROOT = pathlib.Path(__file__).resolve().parents[2]
from faster_whisper import WhisperModel
import numpy as np
FF = str(ROOT.parent / "AIpollon-Reel-Studio" / "skills" / "reel-studio" / ".runtime" / "bin" / "ffmpeg.exe")
def load16k(path):
    raw = subprocess.run([FF, "-v", "error", "-i", str(path), "-ac", "1", "-ar", "16000", "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).copy()

def norm(s):
    s = s.lower().replace("ё", "е")
    return [w for w in re.sub(r"[^a-zа-я0-9 ]+", " ", s).split() if not w.isdigit()]
NUMW = set("сто девяносто пять двести пятьдесят тысяч семидесяти двадцатью девятью пятнадцать процентов девятьсот миллионов три триллиона".split())

model_name = sys.argv[1] if len(sys.argv) > 1 else "small"
takes = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "voice" / "takes"
man = json.loads((takes / "manifest.json").read_text(encoding="utf-8"))
chk_path = takes / f"check_{model_name}.json"
res = json.loads(chk_path.read_text(encoding="utf-8")) if chk_path.exists() else {}
m = WhisperModel(model_name, device="cpu", compute_type="int8")
for e in man:
    if e["name"] in res: continue
    f = str(takes / e["file"])
    segs, info = m.transcribe(load16k(f), language="ru", word_timestamps=True, beam_size=5, vad_filter=False)
    words = [dict(w=w.word.strip(), s=round(w.start, 3), e=round(w.end, 3), p=round(w.probability, 3)) for sg in segs for w in sg.words]
    hyp = " ".join(w["w"] for w in words)
    a, b = [w for w in norm(e["text"]) if w not in NUMW], [w for w in norm(hyp) if w not in NUMW]
    ratio = difflib.SequenceMatcher(None, a, b).ratio()
    gaps = [round(words[i + 1]["s"] - words[i]["e"], 2) for i in range(len(words) - 1)]
    res[e["name"]] = dict(file=e["file"], dur=round(info.duration, 2), hyp=hyp, match=round(ratio, 3),
                          first=words[0]["s"] if words else None, last=words[-1]["e"] if words else None,
                          wps=round(len(a) / max(0.1, (words[-1]["e"] - words[0]["s"]) if words else 1), 2),
                          max_gap=max(gaps) if gaps else 0, minp=min((w["p"] for w in words), default=0), words=words)
    chk_path.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(e["name"], res[e["name"]]["match"], res[e["name"]]["dur"], hyp)
print("DONE")
