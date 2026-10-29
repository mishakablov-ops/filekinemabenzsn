"""Voice for «Баронесса-пулемётчица» (style «Мемы»): two Gemini 3.1 Flash TTS voices, the narrator (newsreel manner)
and the baroness (her own stern voice, not a clone of anyone). Segments in script order, 2 takes each -> Whisper text
check -> best take -> -16 LUFS -> glue -> tts.py --engine audio --tighten 0.25 -> voice.wav + words.json.

    python -I engine/voice_sections.py [--narrator Algenib] [--baroness Gacrux]
Takes are kept per voice (takes/<voice>/), so a re-run with the same voices only re-picks and re-aligns.
"""
import argparse
import difflib
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
RS = Path(os.environ.get("KINEMA_RS", r"C:\Users\Gigabyte\Documents\aipollon claude\KINEMA\skills\reel-studio"))
sys.path.insert(0, str(RS / "scripts"))
for line in (HERE / ".secrets.env").read_text(encoding="utf-8").splitlines():
    if line.startswith("REPLICATE_API_TOKEN="):
        os.environ["REPLICATE_API_TOKEN"] = line.split("=", 1)[1].strip()
os.environ.setdefault("REPLICATE_JOB", "baronessa-voice")
import fish_tts  # noqa: E402
import loudnorm  # noqa: E402
import replicate_tts as R  # noqa: E402
from tts import write_wav  # noqa: E402

NARR = ("Read this Russian text aloud as a native Russian narrator of an old solemn newsreel, played for comedy with a "
        "straight face: grand, ceremonious, confident, a resonant announcer voice, a BRISK lively newsreel pace (old "
        "newsreels are fast), very short pauses between sentences and almost none inside them, clear diction, weighty "
        "emphasis on the key words, never whispering, never stretch words, never slow down. "
        "Perfect native Russian pronunciation, no foreign accent. Mood for this part: ")
# mike 28.10: «нарратора менее выразительным… сделай обычный голос, который мы всегда используем algenib» -> the
# channel's usual direction (tts_final.py BASE), the moods only as light hints
USUAL = ("Read this Russian script aloud as a native Russian documentary narrator for a popular-science short video: "
         "warm, pleasant, confident and engaging. Brisk natural pace, very short pauses between sentences, clear "
         "diction, even and natural intonation, never whispering, never theatrical, no dramatic dips or rises. Perfect "
         "native Russian pronunciation, no foreign accent. A light hint of the mood: ")
BAR = ("Read this Russian line in a comedy sketch as a strict, elegant Russian lady of about fifty: calm, haughty, "
       "unhurried, dry humour, every word final, a low firm voice. Never shouting, never whispering. Perfect native "
       "Russian pronunciation, no foreign accent. Mood: ")

MOOD = {
    "s1": "an intriguing hook, inviting the viewer into a legend",
    "s2": "a grand chronicle opening; the last word 'пыльник' as a solemn punchline",
    "s3": "proud and admiring, listing childhood exploits",
    "s4": "heroic, presenting a legendary weapon; numbers weighty",
    "s5": "a battle report, then a dry beat on 'сдалось'",
    "s6": "an epic siege, tension rising",
    "s7": "a triumphant victory report",
    "s8": "a solemn state anthem feeling, proud",
    "s9": "a mysterious legend, softer",
    "s10": "warm and light, a friendly personal invitation, gentle, no selling",
}
B_MOOD = {"s5": "a cold polite question", "s6": "proud and icy refusal", "s9": "a calm promise",
          "s10": "a short dry approval with a hint of a smile"}


def spoken(s):
    s = re.sub(r"\{[^|}]*\|([^}]*)\}", r"\1", s)
    s = re.sub(r"[=~\[\]*]|//", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def segments():
    """[(seg_id, section, role, text)] from script.md; consecutive narrator lines of a section are one segment"""
    out, sec, buf = [], None, []

    def flush():
        if buf:
            out.append((f"{sec}n{len(out)}", sec, "n", " ".join(buf)))
            buf.clear()
    for line in (HERE / "script.md").read_text(encoding="utf-8").splitlines():
        m = re.match(r"#\s*---\s*(\d+)\.", line)
        if m:
            flush()
            sec = f"s{m.group(1)}"
            continue
        if not line.strip() or line.startswith("#"):
            continue
        if line.startswith("Б:"):
            flush()
            out.append((f"{sec}b{len(out)}", sec, "b", spoken(line[2:])))
        else:
            buf.append(spoken(line))
    flush()
    return out


def norm_words(s):
    return re.findall(r"[a-zа-я0-9]+", s.lower().replace("ё", "е"))


_model = None


def transcribe(path):
    global _model
    from faster_whisper import WhisperModel
    import numpy as np
    if _model is None:
        _model = WhisperModel("small", device="cpu", compute_type="int8")
    raw = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", str(path), "-ac", "1", "-ar", "16000",
                          "-f", "f32le", "pipe:1"], capture_output=True, check=True).stdout
    pcm = np.frombuffer(raw, dtype=np.float32)
    segs, _ = _model.transcribe(pcm, language="ru", word_timestamps=True, beam_size=5)
    words, text = [], []
    for s in segs:
        text.append(s.text)
        words += [(w.start, w.end) for w in s.words or []]
    return " ".join(text).strip(), words, len(pcm) / 16000


def score(text, f):
    hyp, wt, dur = transcribe(f)
    ratio = difflib.SequenceMatcher(a=norm_words(text), b=norm_words(hyp)).ratio()
    gaps = [b[0] - a[1] for a, b in zip(wt, wt[1:])]
    return dict(file=f.name, match=round(float(ratio), 3), hyp=hyp, dur=round(float(dur), 2),
                long_pauses=int(sum(g > 0.6 for g in gaps)), max_pause=round(float(max(gaps, default=0)), 2))


def take(dst, text, voice, prompt):
    if dst.exists():
        return
    for attempt in range(3):
        try:
            dst.write_bytes(R.run("google/gemini-3.1-flash-tts", dict(text=text, voice=voice, language_code="ru-RU",
                                                                      prompt=prompt)))
            print("OK ", dst.name, flush=True)
            return
        except SystemExit as e:
            print("ERR", dst.name, str(e)[:200], flush=True)
            time.sleep(4)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--narrator", default="Algenib")
    ap.add_argument("--baroness", default="Gacrux")
    ap.add_argument("--takes", default="ab", help="take names per line; 'a' = one take (budget)")
    ap.add_argument("--retry", type=float, default=0.95, help="re-take below this text match (0 = never)")
    ap.add_argument("--clone", default="", help="the baroness's lines from takes/<this> (clone_baroness.py), e.g. clone_calm")
    ap.add_argument("--usual", action="store_true", help="the channel's usual narrator direction instead of the newsreel")
    a = ap.parse_args()
    P = RS / "engine" / "public" / "projects" / "baronessa"
    P.mkdir(parents=True, exist_ok=True)
    # the engine's script has no role marks (captions follow the words); roles go to roles.json
    txt = (HERE / "script.md").read_text(encoding="utf-8")
    (P / "script.md").write_text(re.sub(r"(?m)^Б:\s*", "", txt), encoding="utf-8")
    manifest = []
    for sid, sec, role, text in segments():
        voice, prompt = (a.narrator, (USUAL if a.usual else NARR) + MOOD.get(sec, "")) if role == "n" else \
            (a.baroness, BAR + B_MOOD.get(sec, ""))
        cl = P / "takes" / (a.clone or "clone") / f"{sec}b{hashlib.md5(text.encode()).hexdigest()[:6]}.wav"
        if role == "b" and a.clone and cl.exists():          # Igor's own voice (mike 28.10), no TTS call
            pick = cl.parent / f"{cl.stem}_pick.wav"
            loudnorm.normalize(str(cl), str(pick), -16.0, -1.0)
            manifest.append(dict(id=sid, sec=sec, role=role, voice="clone:igor", text=text, pick=str(pick), takes=[]))
            print(f"  {sid} [b] clone {cl.name}", flush=True)
            continue
        d = P / "takes" / voice
        d.mkdir(parents=True, exist_ok=True)
        key = sec + role + hashlib.md5((text + prompt).encode()).hexdigest()[:6]   # changed line/direction: new takes
        if not any((d / f"{key}_{t}.wav").exists() for t in "abcd"):
            for t in a.takes:
                take(d / f"{key}_{t}.wav", text, voice, prompt)
        cands = [score(text, d / f"{key}_{t}.wav") for t in "abcd" if (d / f"{key}_{t}.wav").exists()]
        if cands and max(c["match"] for c in cands) < a.retry:
            for t in "cd":
                take(d / f"{key}_{t}.wav", text, voice, prompt)
            cands = [score(text, d / f"{key}_{t}.wav") for t in "abcd" if (d / f"{key}_{t}.wav").exists()]
        best = max(cands, key=lambda c: (round(c["match"] / 0.03), -c["long_pauses"], -c["dur"]))
        pick = d / f"{key}_pick.wav"
        loudnorm.normalize(str(d / best["file"]), str(pick), -16.0, -1.0)
        manifest.append(dict(id=sid, sec=sec, role=role, voice=voice, text=text, pick=str(pick), takes=cands))
        print(f"  {sid} [{role}] {best['file']} match {best['match']} {best['dur']}s :: {best['hyp']}", flush=True)
    parts = [Path(m["pick"]) for m in manifest]
    texts = [""] + ["[short pause] " + m["text"] for m in manifest[1:]]
    x = fish_tts.join_takes(parts, texts, 48000)
    write_wav(P / "voice_raw.wav", x / (abs(x).max() + 1e-9) * 0.89)
    (P / "voice_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    r = subprocess.run([sys.executable, "-I", str(RS / "scripts" / "tts.py"), str(P), "--engine", "audio",
                        "--audio", str(P / "voice_raw.wav"), "--tighten", "0.25"])
    if r.returncode:
        raise SystemExit("tts.py failed")
    print((P / "tts_report.json").read_text(encoding="utf-8")[:1500])


if __name__ == "__main__":
    main()
