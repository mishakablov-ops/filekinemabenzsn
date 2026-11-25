"""Voice for «Канал без лица» (kanal-bez-lica): Gemini 3.1 Flash TTS, voice Algenib, one call per section with its own
direction, 2 takes each -> Whisper text check -> best take -> static gain to -16 LUFS -> glue -> tts.py --engine audio
--tighten 0.25 -> voice.wav + words.json (KINEMA project kanal-bez-lica). Same method as sposobnosti (template).

Runs on the PC (Replicate is not reachable from the cloud), with KINEMA's python:
    python -I engine/voice_sections.py
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

BASE = ("Read this Russian text as a young Russian guy of about 25 who runs faceless video channels and tells a friend "
        "how it works, in a short social video. Confident, friendly, lively and a little ironic, like sharing a useful "
        "trick, never salesy, never pushy, never theatrical, never whispering. Brisk natural pace, very short pauses "
        "between sentences, never stretch words. Perfect native Russian pronunciation, no foreign accent. ")

PID = "kanal-bez-lica"
# 25.11: the first 16 takes made 40.5 s at 2.1 w/s (plan ~35 s, KINEMA wants 2.5–3.0): two faster takes per section,
# the pick is the fastest take among those that read the text right (never time-stretched)
FAST = (" Pace: fast and energetic, like a lively social-video voice-over, about three words per second; "
        "list items flow quickly one after another without pauses.")
TAKES = os.environ.get("KANAL_TAKES", "abef")
PICK = dict(x.split("=") for x in os.environ.get("KANAL_PICK", "").split(",") if "=" in x)   # «s4b=e,s6=a» by ear
SECTIONS = [
    ("s1", "The hook: punchy and intriguing, three short beats; a light stress on 'монтажа'.",
     "Канал без лица, камеры и монтажа."),
    ("s2", "Matter-of-fact insider tone, the three kinds of ads listed briskly with a small smile.",
     "Такие каналы живут на рекламе: баннеры, интеграции, партнёрки."),
    ("s3", "A turn: the first sentence clear and logical; the second with tired irony, 'это часы' short and dry.",
     "Но реклама идёт туда, где ролики выходят каждый день. А монтаж одного это часы."),
    ("s4", "Upbeat and a bit amazed at how simple it is; 'одну фразу' stressed; the four items listed quickly and lightly. "
           "'Кинема' is a product name, read it as one word.",
     "С Кинема пишешь одну фразу, а и-и сам собирает ролик: сценарий, голос, три-дэ сцены, субтитры."),
    ("s4b", "Light and proud, listing styles quickly like a menu; 'скоро' with a little anticipation; 'и другие' easy.",
     "И стиль не один: три-дэ и пиксель уже работают, а скоро добавятся пластилин, аниме, неон, гжель, лоу поли и другие."),
    ("s5", "Satisfied and simple, a short beat on 'на месяц'.",
     "Один вечер, и роликов хватает на месяц."),
    ("s6", "Warm and reassuring: a friendly question, then a calm, confident promise.",
     "Не шаришь в нейросетях? Настроим всё за тебя."),
    ("s7", "Casual, said in passing to a friend, relaxed and quiet-confident, no pressure, no selling; "
           "the word 'канал' slightly marked as a quote.",
     "Кто напишет в комментах «канал», расскажу, с чего начать."),
]


def norm_words(s: str) -> list[str]:
    s = s.lower().replace("ё", "е")
    return re.findall(r"[a-zа-я0-9]+", s)


# Whisper writes «3D», «ИИ», «лоуполи» where the script spells the sounds: compare letters, not words (25.11: «три-дэ»
# against «3D» cost s4/s4b up to 0.2 of the word match and picked the slowest take)
CANON = [("3d", "тридэ"), ("3д", "тридэ"), ("ai", "ии"), ("кинема", "кинема")]


def letters(s: str) -> str:
    s = s.lower().replace("ё", "е")
    for a, b in CANON:
        s = s.replace(a, b)
    return "".join(re.findall(r"[а-я0-9]+", s))


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
    ref_w = norm_words(text)
    ratio = difflib.SequenceMatcher(a=letters(text), b=letters(hyp), autojunk=False).ratio()
    gaps = [b[0] - a[1] for a, b in zip(wt, wt[1:])]
    span = (wt[-1][1] - wt[0][0]) if wt else dur
    return dict(file=f.name, match=round(float(ratio), 3), hyp=hyp, dur=round(float(dur), 2),
                wps=round(float(len(ref_w) / max(span, 0.1)), 2), long_pauses=int(sum(bool(g > 0.6) for g in gaps)),
                max_pause=round(float(max(gaps, default=0)), 2))


def make_takes(takes: Path, sid: str, direction: str, text: str, names: str):
    for take in names:
        if take in "efgh":
            direction_t = direction + FAST
        else:
            direction_t = direction
        f = takes / f"{sid}_{take}.wav"
        if f.exists():
            continue
        for attempt in range(3):
            t0 = time.time()
            try:
                b = R.run("google/gemini-3.1-flash-tts", dict(text=text, voice="Algenib", language_code="ru-RU", prompt=BASE + direction_t))
                f.write_bytes(b)
                print(f"OK  {sid}_{take} {time.time() - t0:5.1f}s", flush=True)
                break
            except SystemExit as e:
                print(f"ERR {sid}_{take} try {attempt + 1}: {str(e)[:200]}", flush=True)
                time.sleep(4)


def main():
    P = RS / "engine" / "public" / "projects" / PID
    takes = P / "takes"
    takes.mkdir(parents=True, exist_ok=True)
    shutil.copy(HERE / "script-voice.md", P / "script.md")
    manifest = []
    for sid, direction, text in SECTIONS:
        make_takes(takes, sid, direction, text, TAKES)
        cands = [score(text, takes / f"{sid}_{t}.wav") for t in "abcdefgh" if (takes / f"{sid}_{t}.wav").exists()]
        if cands and max(c["match"] for c in cands) < 0.92 and not (takes / f"{sid}_g.wav").exists():
            make_takes(takes, sid, direction, text, "gh")
            cands = [score(text, takes / f"{sid}_{t}.wav") for t in "abcdefgh" if (takes / f"{sid}_{t}.wav").exists()]
        if not cands:
            raise SystemExit(f"no takes for {sid}")
        top = max(c["match"] for c in cands)
        good = [c for c in cands if c["match"] >= top - 0.03 and c["long_pauses"] == 0] or cands
        best = max(good, key=lambda c: (c["wps"], c["match"]))
        if sid in PICK:
            best = next(c for c in cands if c["file"] == f"{sid}_{PICK[sid]}.wav")
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
    main()
