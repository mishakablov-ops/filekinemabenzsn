"""Voice the sosed6 horror story (Sosed s shestogo etazha, part 1) with Gemini 3.1 Flash TTS (voice Algenib): one call per section, 2 takes each.

    python -I voice_sections.py [section ...]   -> engine/public/projects/sosed6/takes/<section>_<a|b>.wav (v1 takes were too slow: kept in takes/v1)
Pick the best take per section (whisper check + voice_profile.py), level, glue, then tts.py --engine audio --tighten 0.25.
"""
import concurrent.futures as cf
import sys
import time
from pathlib import Path

RS = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RS / "scripts"))
import replicate_tts as R  # noqa: E402

OUT = RS / "engine" / "public" / "projects" / "sosed6" / "takes"
OUT.mkdir(parents=True, exist_ok=True)

BASE = ("Read this Russian text as its author: a man of about 30 who lives on the top floor of an old five-storey block, telling "
        "a true creepy story that is still happening to him, in first person. Low, calm, slightly hoarse voice with real unease underneath. "
        "Brisk conversational pace, like telling a friend late at night: about three words per second, very short pauses "
        "between sentences, never stretch words. The tension comes from the tone, not from slowness. Never whispering, "
        "no theatrical horror-movie voice, no melodrama. ")

SECTIONS = [
    ("s1", "The hook: grave and steady, every word lands; tired, a little scared.",
     "Я живу на пятом этаже пятиэтажки. Две недели каждую ночь надо мной двигают мебель. Но выше меня никого нет."),
    ("s2", "Listing the sounds, each one creepier; 'детский плач' quieter and colder.",
     "Сначала шаги. Босиком. Потом скрежет. Как будто тащат шкаф. А в ночь на субботу детский плач."),
    ("s3", "Matter-of-fact, then growing unease; 'Изнутри.' short and cold after a beat.",
     "Я позвонил в управляющую. Мне сказали: над вами только крыша. Люк на чердак заварен с девяносто восьмого года. "
     "Я поднялся проверить. Сварка ржавая. А на крышке свежие царапины. Изнутри."),
    ("s4", "The core of the story: tense and precise like reporting evidence; count 'Раз. Два. Три.' evenly; "
           "the last line slow and frozen.",
     "Тогда я поставил камеру. Ночь первая. Три двенадцать. Шаги начались. На видео я в комнате один. А на звуке нас двое. "
     "Шаги повторяют каждый мой шаг. С задержкой в три секунды. Я остановился. Раз. Два. Три. Наверху тоже остановились. "
     "Я поднял руку. Над потолком скрип. Я опустил руку. А он не опустил. Утром на потолке над кроватью проступило пятно. По форме как ладонь."),
    ("s5", "Discovery, quiet dread rising; 'Шесть.' a stunned beat; the quote read flatly like handwriting; "
           "the last line chilling.",
     "Утром в подъезде был открыт почтовый ящик. Номер двадцать четыре. А квартир в доме двадцать. Внутри старая фотография. "
     "Мой дом. Семьдесят четвёртый год. Я посчитал этажи. Шесть. В окне шестого стоит человек. Он похож на меня. "
     "На обороте ручкой: «Не позволяйте жильцу сверху узнать, что этаж исчез». "
     "Соседка снизу посмотрела на фото и сказала, что я здесь не живу."),
    ("s6", "The climax: close and controlled, barely breathing; the last line almost hushed but voiced.",
     "Этой ночью шаги спустились к моей двери. Я посмотрел в глазок. Лестница шла выше пятого. А наверху горел свет."),
    ("s7", "Out of the story, straight to the viewer, short and intriguing.",
     "Продолжение смотри в профиле."),
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
