"""Voice the coffee-agent story with Gemini 3.1 Flash TTS (voice Algenib): one call per section, 2 takes each.

    python -I voice_sections.py            -> engine/public/projects/coffee-agent/takes/<section>_<a|b>.wav
Pick the best take per section (whisper check + listen), then:
    fish_tts.py --join voice_raw.wav --parts takes/s1_x.wav ...  ->  tts.py <project> --engine audio --tighten 0.25
"""
import sys
import time
from pathlib import Path

RS = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RS / "scripts"))
import replicate_tts as R  # noqa: E402

OUT = RS / "engine" / "public" / "projects" / "coffee-agent" / "takes"
OUT.mkdir(parents=True, exist_ok=True)

BASE = ("Read this Russian text as its author telling his own true story to a friend: a young Russian guy who owns a small "
        "coffee shop. Warm, sincere, natural first-person storytelling with a smile in the voice — lively and engaging, "
        "never theatrical, never whispering. Brisk pace, very short pauses between sentences: this is a short social video, not a film. ")

SECTIONS = [
    ("s1", "Honest and a little tired, self-ironic about the six hours; a quick list for the coffee shop routine; "
           "a slower, sincere beat on the last line.",
     "Я монтировал один ролик шесть часов. Ради сорока секунд. Днём у меня кофейня: гости, заказы, поставки. "
     "Ночью — таймлайн, субтитры, звуки. Я знал: без видео дело не растёт. Но на видео не оставалось меня."),
    ("s2", "Lighter, curious, then genuinely surprised and pleased — the turning point of the story.",
     "Однажды я просто написал агенту: «Сделай ролик про мою кофейню». Сценарий, голос, монтаж — он собрал всё сам, "
     "пока я варил кофе."),
    ("s3", "Warm, calm happiness, smiling; proud but humble on the last line.",
     "Теперь тему я пишу за утренним кофе. А вечер снова мой. И гостей стало больше."),
    ("s4", "Friendly, upbeat and a little playful, talking straight to the viewer.",
     "Кстати, этот ролик тоже собрал агент. Хочешь так же? Тебе в шапку профиля."),
]

for sid, direction, text in SECTIONS:
    for take in "ab":
        f = OUT / f"{sid}_{take}.wav"
        if f.exists():
            continue
        for attempt in range(3):
            t0 = time.time()
            try:
                b = R.run("google/gemini-3.1-flash-tts", dict(text=text, voice="Algenib", language_code="ru-RU", prompt=BASE + direction))
                f.write_bytes(b)
                print(f"OK  {sid}_{take} {time.time() - t0:5.1f}s", flush=True)
                break
            except SystemExit as e:
                print(f"ERR {sid}_{take} try {attempt + 1}: {str(e)[:200]}", flush=True)
                time.sleep(4)
