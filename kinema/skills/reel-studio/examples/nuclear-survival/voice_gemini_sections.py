"""Voice the survival script with Gemini 3.1 Flash TTS (voice Algenib), one call per section with its own direction."""
import json
import sys
import time
from pathlib import Path

RS = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RS / "scripts"))
import replicate_tts as R  # noqa: E402

OUT = RS / "engine" / "public" / "projects" / "nuclear-survival" / "takes"
OUT.mkdir(parents=True, exist_ok=True)

BASE = ("Read this Russian text as a gripping native Russian male narrator of a fast viral survival video. "
        "Brisk pace, very short pauses between sentences, never drag — this is a short social video, not a film. ")

SECTIONS = [
    ("s1", "Start calm and low on the first two words, then a sudden urgent shout at the flash. Fast, commanding orders. "
           "Shout the single word 'Дверь'. Then breathless relief.",
     "Обычный вечер. И вдруг [shouting] вспышка! Не смотри на неё. Падай лицом вниз. Свет приходит раньше волны, у тебя есть секунды. "
     "Вниз, в подвал, подальше от окон. [shouting] Дверь! Над головой грохот. Но ты жив."),
    ("s2", "Confident, intriguing explainer tone, punchy on the numbers, quick.",
     "Снаружи оседает пыль. Она радиоактивная. Но слабеет она очень быстро. Через семь часов в десять раз. Через два дня в сто. "
     "Поэтому сидишь. Даже когда очень хочется выйти."),
    ("s3", "Serious and direct, then playful and amused on the line about the hair conditioner. Quick.",
     "Первым делом сними верхнюю одежду. В ней до девяноста процентов всей пыли. В пакет и за дверь. Потом душ. Мыло, шампунь. "
     "А вот бальзам нельзя. Он приклеивает пыль к волосам."),
    ("s4", "Curious hook on the question, playful on the toilet tank line, then a tense whisper for the iodine warning. Quick.",
     "Вода? Она у тебя уже есть. В бойлере до двухсот литров чистой воды. И в бачке унитаза. Не в чаше. В бачке. "
     "Консервы безопасны, если протереть банку. [whispering] Йод из аптечки не пей. Это ожог, а не защита."),
    ("s5", "Practical and quick for the instructions, quieter and a little sad on the tally marks, "
           "then rising tense excitement when the radio says you can go out.",
     "Радио на батарейках или с ручкой. Интернета не будет. А инструкции будут. Вентиляцию закрыть. Щели плёнкой и скотчем. "
     "Туалет: ведро с пакетом, подальше от еды. Каждый день чёрточка на стене. Так ты не потеряешь счёт времени. "
     "День пятый. День девятый. И вдруг радио говорит: можно выходить."),
    ("s6", "Fast, focused listing of the gear. Then hushed and slow for the door, a whisper for 'Тишина', "
           "quiet sadness on the empty city — but keep it moving.",
     "Собираешь костюм. Дождевик, перчатки, сапоги, очки, респиратор. Скотч на каждый стык. Дверь открывается. "
     "[whispering] Тишина. Ни машин. Ни людей. Никого. Город просто остановился."),
    ("s7", "Warm, friendly, smiling and upbeat, a little playful, quick.",
     "Кстати, это видео сделала нейросеть. Хочешь делать такие же в два клика? Тебе в шапку профиля."),
]

meta = []
for sid, direction, text in SECTIONS:
    f = OUT / f"{sid}.wav"
    if not f.exists():
        for attempt in range(3):
            t0 = time.time()
            try:
                b = R.run("google/gemini-3.1-flash-tts", dict(text=text, voice="Algenib", language_code="ru-RU", prompt=BASE + direction))
                f.write_bytes(b)
                print(f"OK  {sid} {time.time() - t0:5.1f}s", flush=True)
                break
            except SystemExit as e:
                print(f"ERR {sid} try {attempt + 1}: {str(e)[:200]}", flush=True)
                time.sleep(3)
    meta.append({"id": sid, "text": text, "file": str(f)})
(OUT / "sections.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
