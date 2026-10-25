"""Voice the nk-escape story with Gemini 3.1 Flash TTS (voice Algenib): one call per section, 2 takes each.

    python -I voice_sections.py [section ...]   -> engine/public/projects/nk-escape/takes/<section>_<a|b>.wav
Pick the best take per section (whisper check + voice_profile.py), level, glue, then tts.py --engine audio --tighten 0.25.
"""
import concurrent.futures as cf
import sys
import time
from pathlib import Path

RS = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RS / "scripts"))
import replicate_tts as R  # noqa: E402

OUT = RS / "engine" / "public" / "projects" / "nk-escape" / "takes"
OUT.mkdir(parents=True, exist_ok=True)

BASE = ("Read this Russian text as its author: a young man of 24, a former North Korean soldier, telling his own true story "
        "in first person. Calm, low and slightly hoarse voice, serious and honest, with quiet tension underneath — never "
        "theatrical, never whispering, no melodrama. Brisk pace with very short pauses: this is a short social video, not a film. ")

SECTIONS = [
    ("s1", "The opening hook: steady and grave, every short sentence lands; say the last sentence simply, almost calmly.",
     "В меня стреляли свои. Пять пуль. И я их не виню."),
    ("s2", "Matter-of-fact remembering, a bit quicker; the last line darker, with real dread.",
     "Ноябрь две тысячи семнадцатого. Я солдат Северной Кореи. Выпил, поругался с друзьями. И понял: за такое меня расстреляют."),
    ("s3", "Urgent and faster, adrenaline, short clipped phrases; a beat of determination on 'Только на юг'.",
     "Сел в джип и погнал. Пост пролетел на газу. Назад нельзя. Только на юг. Дальше мост, построенный за семьдесят два часа. За ним — граница."),
    ("s4", "Breathless urgency: the wheel drops — shock; 'Застрял' lands hard and short; the running lines fast and tense.",
     "И тут колесо проваливается в канаву. Вперёд, назад. Застрял. Я бегу. Сзади четверо с автоматами. Один даже заскочил за линию и назад."),
    ("s5", "Pain and haze on the first two words, then fading; relief when he is pulled out; 'И выжил' quiet and firm.",
     "Удар. Ещё. Падаю в листья. Трое южнокорейских солдат ползком тащат меня. Вертолёт. Операция. Я потерял половину крови. И выжил."),
    ("s6", "Calm, reflective and sincere, no drama.",
     "А тех, кто стрелял, не виню. На их месте я бы тоже стрелял."),
    ("s7", "Friendlier and warmer, talking straight to the viewer, a little upbeat.",
     "Кстати, этот ролик собрал агент. Хочешь так же? Тебе в шапку профиля."),
]


def take(job):
    sid, direction, text, t = job
    f = OUT / f"{sid}_{t}.wav"
    if f.exists():
        return f"skip {f.name}"
    for attempt in range(3):
        t0 = time.time()
        try:
            f.write_bytes(R.run("google/gemini-3.1-flash-tts", dict(text=text, voice="Algenib", language_code="ru-RU", prompt=BASE + direction)))
            return f"OK  {f.name} {time.time() - t0:5.1f}s"
        except (SystemExit, ValueError) as e:
            time.sleep(4)
            err = str(e)[:160]
    return f"ERR {f.name} {err}"


if __name__ == "__main__":
    want = set(sys.argv[1:])
    jobs = [(s, d, x, t) for s, d, x in SECTIONS if not want or s in want for t in "ab"]
    with cf.ThreadPoolExecutor(4) as ex:
        for r in ex.map(take, jobs):
            print(r, flush=True)
