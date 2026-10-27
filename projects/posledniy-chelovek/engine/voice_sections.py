"""Voice for «Последний человек на Земле» (posledniy-chelovek): Gemini 3.1 Flash TTS, voice Algenib, one call per
section with its own direction, 2 takes each -> Whisper text check -> best take -> static gain to -16 LUFS ->
glue -> tts.py --engine audio --tighten 0.25 -> voice.wav + words.json.

Runs on the PC (Replicate is not reachable from the cloud), from a copy of the repo:
    python -I projects/posledniy-chelovek/engine/voice_sections.py
Token: REPLICATE_API_TOKEN in the environment (the worker job sets it from the PC's .secrets.env, never printed).
Takes are kept, so a re-run only re-picks and re-aligns. Report: <project>/voice_manifest.json
"""
import difflib
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RS = ROOT / "kinema" / "skills" / "reel-studio"
sys.path.insert(0, str(RS / "scripts"))
import fish_tts  # noqa: E402
import loudnorm  # noqa: E402
import replicate_tts as R  # noqa: E402
from tts import write_wav  # noqa: E402

PID = "posledniy-chelovek"
P = RS / "engine" / "public" / "projects" / PID
TAKES = P / "takes"
TAKES.mkdir(parents=True, exist_ok=True)
shutil.copy(ROOT / "projects" / PID / "script.md", P / "script.md")

BASE = ("Read this Russian text as a native Russian male narrator of a gripping short story video, talking straight to "
        "the viewer: the viewer is the last person left on Earth. Warm, lively and engaging, never theatrical, never "
        "whispering. Brisk natural pace, very short pauses between sentences: this is a short social video, not a film. "
        "Perfect native Russian pronunciation, no foreign accent. ")

SECTIONS = [
    ("s1", "Start calm and a little puzzled, as if the viewer just woke up into an eerie quiet morning; "
           "a firm, striking beat on the eight billion; the last words 'И это ты' land slowly and personally.",
     "Ты просыпаешься. Людей нет. Исчезли все восемь миллиардов. Остался один человек. И это ты."),
    ("s2", "Quiet, observant, uneasy: describing an empty city detail by detail. "
           "A touch of sadness on the message to mom that does not go through.",
     "Машины стоят посреди дороги. В кафе на столе кофе ещё тёплый. Пишешь маме. Сообщение не доходит."),
    ("s3", "Serious and ominous, a little lower, but keep it moving.",
     "Через несколько часов гаснет свет. Станциям нужны люди. А их нет."),
    ("s4", "Turn lighter and a bit playful on 'all the shops are yours now', then practical and punchy on the numbers.",
     "Зато все магазины теперь твои. Хлеб покроется плесенью за неделю. А консервы хранятся до пяти лет. "
     "Любая машина тоже твоя. Но бензин портится за полгода."),
    ("s5", "Softer, with quiet awe and wonder looking up at the night sky.",
     "Ночью ни одного фонаря. Город чёрный. А над ним Млечный Путь. Раньше треть людей его не видела."),
    ("s6", "Tense and alert, a hint of danger; clear and punchy on the number seven.",
     "Через год в города приходят волки. В зоне Чернобыля их в семь раз больше, чем в заповедниках."),
    ("s7", "Slow, hushed suspense building up (but not whispering), then a sharp, startled emphasis on the last words "
           "'в дверь стучат'.",
     "Ты последний человек на Земле. Сидишь в пустой комнате. Тишина. И вдруг в дверь стучат."),
    ("s8", "Switch to warm, friendly, smiling and upbeat, a little playful, quick.",
     "Кстати, это видео сделала нейросеть. Хочешь делать такие же в два клика? Тебе в шапку профиля."),
]


def norm_words(s: str) -> list[str]:
    s = s.lower().replace("ё", "е")
    return re.findall(r"[a-zа-я0-9]+", s)


_model = None


def transcribe(path: Path) -> tuple[str, list[tuple[float, float]], float]:
    global _model
    from faster_whisper import WhisperModel
    if _model is None:
        _model = WhisperModel("small", device="cpu", compute_type="int8")
    # decode with ffmpeg ourselves, like tts.py (the PC's PyAV is older than faster-whisper expects)
    import numpy as np
    raw = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", str(path), "-ac", "1", "-ar", "16000", "-f", "f32le", "pipe:1"],
                         capture_output=True, check=True).stdout
    pcm = np.frombuffer(raw, dtype=np.float32)
    segs, info = _model.transcribe(pcm, language="ru", word_timestamps=True, beam_size=5)
    words, text = [], []
    for s in segs:
        text.append(s.text)
        for w in s.words or []:
            words.append((w.start, w.end))
    return " ".join(text).strip(), words, len(pcm) / 16000


def score(sid: str, text: str, f: Path) -> dict:
    hyp, wt, dur = transcribe(f)
    ref_w, hyp_w = norm_words(text), norm_words(hyp)
    ratio = difflib.SequenceMatcher(a=ref_w, b=hyp_w).ratio()
    gaps = [b[0] - a[1] for a, b in zip(wt, wt[1:])]
    span = (wt[-1][1] - wt[0][0]) if wt else dur
    # plain int/float: whisper times can be numpy scalars, which json cannot write
    return dict(file=f.name, match=round(float(ratio), 3), hyp=hyp, dur=round(float(dur), 2),
                wps=round(float(len(ref_w) / max(span, 0.1)), 2), long_pauses=int(sum(bool(g > 0.6) for g in gaps)),
                max_pause=round(float(max(gaps, default=0)), 2))


def make_takes(sid: str, direction: str, text: str, names: str):
    for take in names:
        f = TAKES / f"{sid}_{take}.wav"
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


def main():
    manifest = []
    for sid, direction, text in SECTIONS:
        make_takes(sid, direction, text, "ab")
        cands = [score(sid, text, TAKES / f"{sid}_{t}.wav") for t in "abcd" if (TAKES / f"{sid}_{t}.wav").exists()]
        if cands and max(c["match"] for c in cands) < 0.9 and not (TAKES / f"{sid}_c.wav").exists():
            # both takes misread a word: two more takes ($0.06), then pick from all four
            make_takes(sid, direction, text, "cd")
            cands = [score(sid, text, TAKES / f"{sid}_{t}.wav") for t in "abcd" if (TAKES / f"{sid}_{t}.wav").exists()]
        if not cands:
            raise SystemExit(f"no takes for {sid}")
        # best text match; near-ties go to the take without long pauses, then the brisker one
        best = max(cands, key=lambda c: (round(c["match"] / 0.03), -c["long_pauses"], c["wps"]))
        pick = TAKES / f"{sid}_pick.wav"
        loudnorm.normalize(str(TAKES / best["file"]), str(pick), -16.0, -1.0)
        manifest.append(dict(id=sid, text=text, takes=cands, pick=best["file"]))
        for c in cands:
            print(f"  {sid} {c['file']}: match {c['match']}  {c['dur']}s  {c['wps']} w/s  pauses>0.6s: {c['long_pauses']}"
                  f"{'  <- pick' if c is best else ''}\n     {c['hyp']}", flush=True)
    parts = [TAKES / f"{m['id']}_pick.wav" for m in manifest]
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
