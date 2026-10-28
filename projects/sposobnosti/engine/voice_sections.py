"""Voice for «Каждому по способности» (sposobnosti, two parts): Gemini 3.1 Flash TTS, voice Algenib, one call per
section with its own direction, 2 takes each -> Whisper text check -> best take -> static gain to -16 LUFS ->
glue -> tts.py --engine audio --tighten 0.25 -> voice.wav + words.json (KINEMA project sposobnosti-<part>).

Runs on the PC (Replicate is not reachable from the cloud), with KINEMA's python:
    python -I engine/voice_sections.py 1      (and 2)
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

HERE = Path(__file__).resolve().parents[1]          # the project folder (script-1.md, script-2.md)
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

PARTS = {
    "1": [
        ("s1", "The hook: an amazed, striking opening, as if it really happened last night; 'Навсегда' firm; "
               "the eight billions land clearly.",
         "Этой ночью все получили суперсилу. Каждый человек на Земле. Одну. Навсегда. "
         "Восемь миллиардов людей, восемь миллиардов способностей."),
        ("s2", "Amused wonder, looking out of the window at a crazy morning, listing what he sees, smiling.",
         "Я выглянул в окно. Сосед сверху летит на работу. Бабушка у подъезда поднимает машину взглядом. "
         "А машина весит около полутора тонн. Курьер исчезает и через секунду стоит у двери."),
        ("s3", "Upbeat and quick, like news of a new world; a clear beat on the hundred thousand.",
         "К обеду в городе не осталось пробок. Полгорода летит на работу по воздуху. "
         "Обычно в мире за день около ста тысяч рейсов. А сегодня аэропорты пустые."),
        ("s4", "Self-ironic and funny about his own failures; 'Упал.' short and dry; the mug line deadpan.",
         "А я весь день искал свою силу. Прыгнул с лавочки, чтобы взлететь. Упал. Час смотрел на кружку. Она не сдвинулась."),
        ("s5", "Surprise and then a slow realisation; 'рухнул в кусты' with a laugh in the voice, the last sentence "
               "quieter, amazed.",
         "Вечером сосед пролетал над моей головой. И вдруг рухнул в кусты. Тогда я понял. Рядом со мной чужие силы гаснут."),
        ("s6", "Proud and a little lonely on 'обычный', then a sudden suspense on the knock; the last line short, "
               "straight to the viewer.",
         "Восемь миллиардов суперлюдей. И один обычный. А утром в мою дверь постучали. Вторая часть уже в профиле."),
    ],
    "2": [
        ("s1", "The hook, sudden and tense: they came for him at six in the morning; the quote serious.",
         "В шесть утра за мной пришли. Люди в форме сказали: «Ты нам нужен». За неделю мир сломался."),
        ("s2", "Fast and alarmed, listing the chaos like breaking news; a firm beat on three hundred million.",
         "Невидимки чистят магазины. Парень с молниями оставил район без света. А в одной молнии около трёхсот миллионов вольт."),
        ("s3", "Grave and gripping, a bit lower; the numbers clear and heavy, still brisk.",
         "Но самый опасный человек управляет погодой. Он закрутил над городом ураган. Ветер больше двухсот пятидесяти "
         "километров в час. Такой ураган за сутки выделяет в двести раз больше энергии, чем все электростанции мира."),
        ("s4", "Brave, steady, building up step by step; the last sentence a quiet, satisfied beat of victory.",
         "Меня высадили на краю бури. Я пошёл к центру, и ветер вокруг меня стихал. Я положил руку ему на плечо. И ураган исчез."),
        ("s5", "Warm, light and smiling; the line about being ordinary sincere; then a friendly question to the viewer.",
         "Теперь у моей двери каждое утро очередь. Те, кто не справляется со своей силой. "
         "Самая нужная сила, оказывается, быть обычным. А какую силу выбрал бы ты?"),
        ("s6", "Switch to warm, friendly, smiling and upbeat, a little playful, quick.",
         "Кстати, это видео сделала нейросеть. Хочешь такие же? Тебе в шапку профиля."),
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


def main(part: str):
    P = RS / "engine" / "public" / "projects" / f"sposobnosti-{part}"
    takes = P / "takes"
    takes.mkdir(parents=True, exist_ok=True)
    shutil.copy(HERE / f"script-{part}.md", P / "script.md")
    manifest = []
    for sid, direction, text in PARTS[part]:
        make_takes(takes, sid, direction, text, "ab")
        cands = [score(text, takes / f"{sid}_{t}.wav") for t in "abcd" if (takes / f"{sid}_{t}.wav").exists()]
        if cands and max(c["match"] for c in cands) < 0.9 and not (takes / f"{sid}_c.wav").exists():
            make_takes(takes, sid, direction, text, "cd")
            cands = [score(text, takes / f"{sid}_{t}.wav") for t in "abcd" if (takes / f"{sid}_{t}.wav").exists()]
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
    for part in sys.argv[1:] or ["1", "2"]:
        main(part)
