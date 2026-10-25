"""Audition of accent-free Russian narrators on Replicate (same text), + Chatterbox cloned from a native Russian reference."""
import os, sys, json, pathlib, subprocess, base64, time
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

TEXT = "Представь: завтра утром все границы исчезли. Сто девяносто пять стран. Двести пятьдесят тысяч километров линий на карте. И больше семидесяти стен, которые их охраняют."
STYLE = ("Read this Russian script aloud as a native Russian documentary narrator: warm, pleasant, confident and intriguing, "
         "like a popular science YouTube channel. Moderately brisk pace, very short pauses, clear diction, never whispering, "
         "never theatrical. Perfect native Russian pronunciation with no foreign accent.")
OUT = ROOT / "voice" / "aud2"; OUT.mkdir(parents=True, exist_ok=True)
jobs = [
    ("1_gemini_algenib", "gemini", "Algenib", STYLE, None),
    ("2_gemini_charon", "gemini", "Charon", STYLE, None),
    ("3_gemini_orus", "gemini", "Orus", STYLE, None),
    ("4_minimax_reliableman", "minimax", "Russian_ReliableMan", "neutral", 1.05),
    ("5_minimax_attractiveguy", "minimax", "Russian_AttractiveGuy", "neutral", 1.05),
    ("6_gemini_sulafat_female", "gemini", "Sulafat", STYLE.replace("narrator", "female narrator"), None),
    ("7_eleven_mark", "eleven", "Mark", "[calm, confident]", 1.0),
]
for name, model, voice, style, speed in jobs:
    dst = OUT / f"{name}.wav"
    if dst.exists(): continue
    try:
        data = rt.synth(model, TEXT, voice, style, speed)
        raw = OUT / f"{name}.raw"
        raw.write_bytes(data)
        subprocess.run([FF, "-v", "error", "-y", "-i", str(raw), "-ac", "1", "-ar", "48000", str(dst)], check=True)
        print("ok", name)
    except SystemExit as e:
        print("FAILED", name, e)
    except Exception as e:
        print("FAILED", name, repr(e))
# Chatterbox with a native Russian reference (Charon sample) -> less accent
ref = OUT / "2_gemini_charon.wav"
if ref.exists():
    mp3 = OUT / "ref_charon.mp3"
    subprocess.run([FF, "-v", "error", "-y", "-i", str(ref), "-t", "9.5", "-ac", "1", "-ar", "24000", "-b:a", "128k", str(mp3)], check=True)
    secs = ROOT / "voice" / "aud2" / "sections.json"
    secs.write_text(json.dumps([{"id": "s1", "text": TEXT[:44]}, {"id": "s2", "text": TEXT[45:]}], ensure_ascii=False), encoding="utf-8")
    py = sys.executable
    subprocess.run([py, "-I", str(ROOT / "tools" / "py" / "tts_chatterbox.py"), "--sections", str(secs), "--out", str(OUT / "cb"),
                    "--ref", str(mp3), "--variants", "clone", "--takes", "1", "--cfg", "0.5", "--exaggeration", "0.45",
                    "--temperature", "0.6"], check=False)
print("DONE")
