"""Re-voice only the iodine warning (no whisper) with Gemini 3.1 Flash TTS · Algenib: 3 candidates + 1 full-section fallback."""
import sys
import time
from pathlib import Path

RS = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RS / "scripts"))
import replicate_tts as R  # noqa: E402

OUT = RS / "engine" / "public" / "projects" / "nuclear-survival" / "takes"
BASE = ("Read this Russian text as a gripping native Russian male narrator of a fast viral survival video. "
        "Brisk pace, very short pauses between sentences, never drag — this is a short social video, not a film. ")
LINE = ("Serious, firm, direct warning in a normal full speaking voice — not a whisper, not quiet. Same energy as the rest of the story. Quick.",
        "Йод из аптечки не пей. Это ожог, а не защита.")
FULL = ("Curious hook on the question, playful on the toilet tank line, then a serious firm warning in a normal full voice "
        "for the iodine line — never whisper. Quick.",
        "Вода? Она у тебя уже есть. В бойлере до двухсот литров чистой воды. И в бачке унитаза. Не в чаше. В бачке. "
        "Консервы безопасны, если протереть банку. Йод из аптечки не пей. Это ожог, а не защита.")

jobs = [(f"iodine_{k}", LINE) for k in "abc"] + [("s4_full_v2", FULL)]
for name, (direction, text) in jobs:
    f = OUT / f"{name}.wav"
    if f.exists():
        continue
    for attempt in range(3):
        t0 = time.time()
        try:
            b = R.run("google/gemini-3.1-flash-tts", dict(text=text, voice="Algenib", language_code="ru-RU", prompt=BASE + direction))
            f.write_bytes(b)
            print(f"OK  {name} {time.time() - t0:5.1f}s", flush=True)
            break
        except SystemExit as e:
            print(f"ERR {name} try {attempt + 1}: {str(e)[:200]}", flush=True)
            time.sleep(4)
