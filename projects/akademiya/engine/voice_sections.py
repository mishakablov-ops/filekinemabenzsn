"""Voice for «Каждому по способности», season «Академия героев» (akademiya): Gemini 3.1 Flash TTS, voice Algenib,
one call per section with its own direction, ONE take per section (mike 28.10.2026); a second take only on a clear
error (Whisper text match < 0.9) -> best take -> static gain to -16 LUFS -> glue -> tts.py --engine audio
--tighten 0.25 -> voice.wav + words.json (KINEMA project akademiya-<episode>).

Runs on the PC (Replicate is not reachable from the cloud), with KINEMA's python:
    python -I engine/voice_sections.py 3
Env: KINEMA_RS = path to KINEMA/skills/reel-studio; REPLICATE_API_TOKEN and REPLICATE_JOB come from the worker job.
Takes are kept, so a re-run only re-picks and re-aligns. Report: <KINEMA project>/voice_manifest.json
"""
import difflib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]          # the project folder (script-3.md, ...)
RS = Path(os.environ.get("KINEMA_RS", r"C:\Users\Gigabyte\Documents\aipollon claude\KINEMA\skills\reel-studio"))
sys.path.insert(0, str(RS / "scripts"))
import fish_tts  # noqa: E402
import loudnorm  # noqa: E402
import replicate_tts as R  # noqa: E402
from tts import write_wav  # noqa: E402

BASE = ("Read this Russian text as its author: a young Russian guy of about 22 telling his own amazing story in first "
        "person to a friend, in a short social video. Lively, warm, a little ironic, genuinely engaged, never theatrical, "
        "never whispering. Brisk natural pace, very short pauses between sentences, never stretch words. "
        "Perfect native Russian pronunciation, no foreign accent. ")

EPISODES = {
    "3": [
        ("s1", "The hook: a striking paradox told with a half-smile, as if he still can't believe it; 'ноль' short and "
               "firm, then 'И меня взяли первым' with a proud little twist.",
         "На экзамене в Академию героев я получил ноль. И меня взяли первым."),
        ("s2", "Quick and curious, setting the scene; a light ironic smile on 'С ним невозможно спорить. Это его сила.'",
         "После урагана мне пришло письмо. Академию открыли за неделю для тех, кто не справляется со своей силой. "
         "Директор Сол. С ним невозможно спорить. Это его сила."),
        ("s3", "Fast and impressed, listing the others like a sports commentator; a clear beat on twelve tonnes; then the "
               "question to him, a short honest pause, and 'Все смеялись' a little bitter but with humour.",
         "Экзамен — на арене. Си-Джей поднял автобус одной рукой. А это около двенадцати тонн. "
         "Сезар пробежал круг за секунду. Дениз остановила время. А меня спросили: «Что покажешь ты?» "
         "Я показал ничего. На табло — ноль. Все смеялись."),
        ("s4", "Sudden tension and danger, faster; 'Все побежали' hurried; 'Я пошёл ему навстречу' calm and steady; "
               "the last sentence a quiet, amazed beat of victory.",
         "И тут каменный голем вышел из-под контроля. Он пошёл прямо на трибуны. Все побежали. "
         "Я пошёл ему навстречу. И голем рассыпался."),
        ("s5", "Respectful and a bit awed about the old hero; the quotes of the old man slower, low, kind and wise; "
               "'Почему я?' genuinely surprised, his own voice.",
         "На трибуне встал старик. Эммет. Первый герой. Сорок лет он не брал учеников. А тут сказал: «Этот — ко мне». "
         "«Почему я?» «Правило первое. Сила сейчас есть у всех. Навстречу идут единицы»."),
        ("s6", "Quiet and warm, a sad secret at sunset; the old man's words tired and sincere; then the last sentence "
               "calm and friendly, a simple invitation, no selling.",
         "Вечером он сел рядом и закашлялся. «Моя сила меня сжигает. А рядом с тобой я впервые за сорок лет отдыхаю». "
         "Следующая серия скоро в профиле."),
    ],
    "4": [
        ("s1", "The hook: a funny paradox told with a crooked smile; 'мусор' plain and a bit embarrassed, then "
               "'И это был мой первый урок' with quiet pride.",
         "Месяц в Академии героев я таскал мусор. И это был мой первый урок."),
        ("s2", "Early morning, fresh and a little sleepy at first, then curious; numbers clear; the mentor's order "
               "slower, low and calm.",
         "Пять утра. Пляж за Академией. Тридцать лет туда свозили старое железо. Холодильники, машины, рельсы. "
         "Мой круг гасит любую силу рядом. Сейчас он шесть метров. Эммет сказал: «Расчисти пляж. И сожми его до ладони»."),
        ("s3", "Honest about failing, self-ironic, faster; CJ's mocking line '«Ноль тренируется!»' teasing and loud-ish; "
               "the last sentence tired and funny.",
         "Первую неделю я не мог сдвинуть холодильник. Си-Джей бегал мимо и смеялся. «Ноль тренируется!» "
         "Круг не сжимался. Он просто гас. На десятый день я уснул прямо на песке."),
        ("s4", "The turn: quiet respect, steady rhythm like work; 'Каждый день. В пять утра.' measured; "
               "the last two sentences a growing, amazed joy.",
         "Эммет ничего не сказал. Он встал рядом и тоже взял железо. Каждый день. В пять утра. "
         "Через месяц пляж был пустой. А круг сжался до ладони."),
        ("s5", "Warm and tender with a smile about Denise; the old man's words slower, kind, a little sad.",
         "Дениз приходила каждое утро. Останавливала время, чтобы я поспал ещё десять секунд. "
         "Эммет сказал: «Я тоже так начинал. Один. Сорок лет назад»."),
        ("s6", "The mentor's rule, slow, low and wise, worth remembering; a clear beat before the last word.",
         "«Правило второе. Повторение сильнее таланта»."),
        ("s7", "Evening, a spark of challenge: CJ's words cocky and short; then the last sentence calm and friendly, "
               "a simple invitation, no selling.",
         "Вечером Си-Джей кинул мне перчатку. «Завтра учебный бой. Ты и я». Следующая серия скоро в профиле."),
    ],
    "5": [
        ("s1", "The hook: a bold paradox with a sly grin; 'с нулём' plain; 'И выиграл за восемь секунд' quick and proud.",
         "Против сильнейшего в Академии я вышел с нулём. И выиграл за восемь секунд."),
        ("s2", "Brisk, setting the rules like before a game; the mentor's one word calm and low.",
         "Учебный бой. Двое на двое. Я и Дениз против Си-Джея и Сезара. Надо сорвать флаг соперника. "
         "Эммет сказал мне одно слово: «Думай»."),
        ("s3", "Fast and painful, losing; CJ's line mocking; the stands laughing again said with a bitter smile.",
         "Сезар забрал наш флаг за секунду. Си-Джей прижал меня к стене. «Где твоя сила, Ноль?» "
         "Первый раунд проигран. Трибуны снова смеялись."),
        ("s4", "The turn: calm and sly, slowing down on the trick, then quick and excited as it works; "
               "'Восемь секунд' a short triumphant beat.",
         "Во втором раунде я ничего не делал. Я просто поднял ладонь. Си-Джей решил, что я погашу его силу. "
         "Он замер. Сезар кинулся его прикрывать. А Дениз остановила время. И взяла их флаг. Восемь секунд."),
        ("s5", "Warm, friends after the fight; CJ's line gruff but respectful; the last sentence touched.",
         "Си-Джей подошёл и протянул руку. «В следующий раз я не поверю». Дениз засмеялась первой. "
         "А Эммет на трибуне впервые улыбнулся."),
        ("s6", "The mentor's rule, slow, low and wise, worth remembering.",
         "«Правило третье. Противник решает за полсекунды. Покажи ему то, что нужно тебе»."),
        ("s7", "Night, sudden unease, quieter and slower; then the last sentence calm and friendly, no selling.",
         "А ночью на стене Академии кто-то выжег «НОЛЬ». Следующая серия скоро в профиле."),
    ],
}


def norm_words(s: str) -> list[str]:
    s = s.lower().replace("ё", "е")
    return re.findall(r"[a-zа-я0-9]+", s)


_model = None


def transcribe(path: Path):
    global _model
    from faster_whisper import WhisperModel
    import numpy as np
    if _model is None:
        _model = WhisperModel("small", device="cpu", compute_type="int8")
    raw = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", str(path), "-ac", "1", "-ar", "16000",
                          "-f", "f32le", "pipe:1"], capture_output=True, check=True).stdout
    pcm = np.frombuffer(raw, dtype=np.float32)
    segs, info = _model.transcribe(pcm, language="ru", word_timestamps=True, beam_size=5)
    words, text = [], []
    for s in segs:
        text.append(s.text)
        for w in s.words or []:
            words.append((w.start, w.end))
    return " ".join(text).strip(), words, len(pcm) / 16000


def score(text: str, f: Path) -> dict:
    hyp, wt, dur = transcribe(f)
    ref_w, hyp_w = norm_words(text), norm_words(hyp)
    ratio = difflib.SequenceMatcher(a=ref_w, b=hyp_w).ratio()
    gaps = [b[0] - a[1] for a, b in zip(wt, wt[1:])]
    span = (wt[-1][1] - wt[0][0]) if wt else dur
    return dict(file=f.name, match=round(float(ratio), 3), hyp=hyp, dur=round(float(dur), 2),
                wps=round(float(len(ref_w) / max(span, 0.1)), 2), long_pauses=int(sum(bool(g > 0.6) for g in gaps)),
                max_pause=round(float(max(gaps, default=0)), 2))


def make_takes(takes: Path, sid: str, direction: str, text: str, names: str):
    for take in names:
        f = takes / f"{sid}_{take}.wav"
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


def main(ep: str):
    P = RS / "engine" / "public" / "projects" / f"akademiya-{ep}"
    takes = P / "takes"
    takes.mkdir(parents=True, exist_ok=True)
    shutil.copy(HERE / f"script-{ep}.md", P / "script.md")
    manifest = []
    for sid, direction, text in EPISODES[ep]:
        make_takes(takes, sid, direction, text, "a")
        cands = [score(text, takes / f"{sid}_{t}.wav") for t in "ab" if (takes / f"{sid}_{t}.wav").exists()]
        if cands and max(c["match"] for c in cands) < 0.9 and not (takes / f"{sid}_b.wav").exists():
            make_takes(takes, sid, direction, text, "b")       # clear error only: a second take
            cands = [score(text, takes / f"{sid}_{t}.wav") for t in "ab" if (takes / f"{sid}_{t}.wav").exists()]
        if not cands:
            raise SystemExit(f"no takes for {sid}")
        best = max(cands, key=lambda c: (round(c["match"] / 0.03), -c["long_pauses"], c["wps"]))
        pick = takes / f"{sid}_pick.wav"
        loudnorm.normalize(str(takes / best["file"]), str(pick), -16.0, -1.0)
        manifest.append(dict(id=sid, text=text, takes=cands, pick=best["file"]))
        for c in cands:
            print(f"  {sid} {c['file']}: match {c['match']}  {c['dur']}s  {c['wps']} w/s  pauses>0.6s: {c['long_pauses']}"
                  f"{'  <- pick' if c is best else ''}\n     {c['hyp']}", flush=True)
    parts = [takes / f"{m['id']}_pick.wav" for m in manifest]
    texts = [""] + ["[short pause] " + m["text"] for m in manifest[1:]]   # 0.28 s between sections
    x = fish_tts.join_takes(parts, texts, 48000)
    write_wav(P / "voice_raw.wav", x / (abs(x).max() + 1e-9) * 0.89)
    (P / "voice_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    r = subprocess.run([sys.executable, "-I", str(RS / "scripts" / "tts.py"), str(P), "--engine", "audio",
                        "--audio", str(P / "voice_raw.wav"), "--tighten", "0.25"])
    if r.returncode:
        raise SystemExit("tts.py failed")
    print((P / "tts_report.json").read_text(encoding="utf-8"))


if __name__ == "__main__":
    for ep in sys.argv[1:] or ["3"]:
        main(ep)
