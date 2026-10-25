"""Voice the podezd horror story with Gemini 3.1 Flash TTS (voice Algenib): one call per section, 2 takes each.

    python -I voice_sections.py [section ...]   -> engine/public/projects/podezd/takes/<section>_<a|b>.wav (v1 takes were too slow: kept in takes/v1)
Pick the best take per section (whisper check + voice_profile.py), level, glue, then tts.py --engine audio --tighten 0.25.
"""
import concurrent.futures as cf
import sys
import time
from pathlib import Path

RS = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RS / "scripts"))
import replicate_tts as R  # noqa: E402

OUT = RS / "engine" / "public" / "projects" / "podezd" / "takes"
OUT.mkdir(parents=True, exist_ok=True)

BASE = ("Read this Russian text as its author: Dima, a man of about 30, telling a true creepy story that happened in his own "
        "apartment block, in first person. Low, calm, slightly hoarse voice with real unease underneath; he is still shaken. "
        "Brisk conversational pace, like telling a friend late at night: about three words per second, very short pauses "
        "between sentences, never stretch words. The tension comes from the tone, not from slowness. Never whispering, "
        "no theatrical horror-movie voice, no melodrama. ")

SECTIONS = [
    ("s1", "The hook: quiet and grave, every word lands; a short pause before the last two words.",
     "Третью ночь соседи стоят лицом в угол. И воют."),
    ("s2", "Plain and matter-of-fact, setting the scene, a little faster; slight unease on the last line.",
     "Меня зовут Дима. Хрущёвка, четвёртый этаж. Лифта нет. Только лестница, зелёные стены и лампочки по сорок ватт. "
     "Внизу вахта. Там сорок лет сидит Валентина Петровна. Она знает всех. И при мне всегда закрывает журнал."),
    ("s3", "Growing dread; the quoted words 'Не смотри вниз' lower and slower but still voiced, not whispered; "
           "'Этаж за этажом' slow; the last line uneasy.",
     "Первым был Серёга со второго. Сидел на ступеньках и держался за голову. Я спросил, что случилось. Он прошептал: "
     "«Не смотри вниз». Через день их было трое. Каждый в своём углу. Они не спят. Не едят. Они слушают. "
     "Ночью в стояке — стук. Снизу вверх. Этаж за этажом. А лампочки мигают в одном ритме. Как будто кто-то дышит."),
    ("s4", "Sudden tension: the scream line sharper; 'Все разом' cold and slow; the last line quiet.",
     "В ночь на пятницу меня разбудил крик. Кричала Валентина Петровна. Снизу. Долго. Я вышел на площадку. "
     "Соседи повернулись ко мне. Все разом. И молча показали вниз."),
    ("s5", "Short clipped observations, tense; 'моя фамилия' hits hard; the last sentence slower, chilling.",
     "Вахта открыта. Стул опрокинут. Чай ещё тёплый. Журнал на полу. На последней странице — моя фамилия. "
     "А за шкафом — дверь, которой здесь никогда не было. Я позвонил в полицию. Гудки. А потом в трубке кто-то заплакал."),
    ("s6", "Descending into darkness: steady, tight breathing between phrases, rising fear; 'Шесть. В пятиэтажке.' disbelief.",
     "Я включил фонарик. Ступени вели вниз. Ниже подвала. Связь пропала на первом же пролёте. Я считал пролёты. "
     "Шесть. В пятиэтажке. На стенах — царапины. На уровне моего лица. Внизу кто-то плакал. Тихо. Как ребёнок."),
    ("s7", "The climax: very controlled, barely holding together; the last line slow and frozen.",
     "Он сидел ко мне спиной. Очень высокий. Очень худой. И закрывал лицо руками. Рядом лежал платок Валентины Петровны. "
     "Я сделал шаг. Плач оборвался. И он начал медленно опускать руки."),
    ("s8", "Out of the story, straight to the viewer, short and intriguing, a hint of a smile.",
     "Продолжение — смотри в профиле."),
]


def take(job):
    sid, direction, text, t = job
    f = OUT / f"{sid}_{t}.wav"
    if f.exists():
        return f"skip {f.name}"
    err = ""
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
