"""Voice a «every N seconds …» short on a time grid: one TTS call per `# --- N.` section, section k starts exactly at
(k-1)*grid seconds (the hook at 0.15 s), the last section (CTA) right after the one before it.
Word timings come from faster-whisper (word_timestamps) mapped onto the script words; cards = script lines.

    python voice_grid.py <id>                       # real voice (Replicate MiniMax, key from reel-studio/.secrets.env)
    python voice_grid.py <id> --placeholder         # silent track + estimated timings, to stage shots before the voice
    python voice_grid.py <id> --only 3,5            # re-voice some sections (others kept from takes/)

Reads   narration/<id>/script.md
Writes  narration/<id>/takes/sN.wav, voice.wav, words.json {words, cards, duration}, sections.json
Default voice = «Эскалатор» (09.11.2026): MiniMax speech-2.8-hd Russian_ReliableMan, speed 1.35.
"""
from __future__ import annotations

import argparse
import difflib
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]                        # pixcine/
RS = ROOT.parent / "skills" / "reel-studio"
SR = 48000


def spoken(line: str) -> str:
    s = re.sub(r"\{([^|}]*)\|([^}]*)\}", r"\2", line)
    for m in ("==", "~~", "__", "^", "*", "[", "]"):
        s = s.replace(m, "")
    s = s.replace("//", " ")
    return re.sub(r"\s+", " ", s).strip()


def display(line: str) -> str:
    s = re.sub(r"\{([^|}]*)\|[^}]*\}", r"\1", line)
    for m in ("==", "~~", "__", "^", "*", "[", "]"):
        s = s.replace(m, "")
    return re.sub(r"\s+", " ", s.replace("//", " ")).strip()


def sections(script: Path):
    out = []
    for raw in script.read_text(encoding="utf-8").splitlines():
        m = re.match(r"#\s*---\s*(\d+)", raw)
        if m:
            out.append({"id": m.group(1), "lines": []})
        elif raw.strip() and not raw.startswith("#") and out:
            out[-1]["lines"].append(raw)
    return out


def norm(w: str) -> str:
    return re.sub(r"[^a-zа-я0-9]+", "", w.lower().replace("ё", "е"))


def load(path: Path) -> np.ndarray:
    raw = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", str(path), "-ac", "1", "-ar", str(SR), "-f", "f32le", "pipe:1"],
                         capture_output=True, check=True).stdout
    a = np.frombuffer(raw, dtype=np.float32).copy()
    # trim leading/trailing silence (−45 dB) but keep 40 ms
    lvl = np.abs(a) > 10 ** (-45 / 20)
    if lvl.any():
        i0, i1 = np.argmax(lvl), len(a) - np.argmax(lvl[::-1])
        a = a[max(0, i0 - int(0.04 * SR)): min(len(a), i1 + int(0.08 * SR))]
    return a


def estimate(words: list[str], seps: set[int]) -> list[tuple[float, float]]:
    t, out = 0.0, []
    for i, w in enumerate(words):
        d = 0.07 + 0.048 * len(norm(w))
        out.append((t, t + d))
        t += d + (0.22 if i in seps else 0.03)
    return out


def whisper_words(path: Path, model) -> list[tuple[str, float, float]]:
    raw = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", str(path), "-ac", "1", "-ar", "16000", "-f", "f32le", "pipe:1"],
                         capture_output=True, check=True).stdout
    segs, _ = model.transcribe(np.frombuffer(raw, dtype=np.float32), language="ru", beam_size=5, word_timestamps=True)
    return [(w.word.strip(), w.start, w.end) for s in segs for w in s.words]


def align(script_words: list[str], heard: list[tuple[str, float, float]], dur: float) -> list[tuple[float, float]]:
    """map whisper word times onto the script words; unmatched words are interpolated between matched neighbours"""
    a, b = [norm(w) for w in script_words], [norm(h[0]) for h in heard]
    times: list[tuple[float, float] | None] = [None] * len(a)
    for blk in difflib.SequenceMatcher(None, a, b, autojunk=False).get_matching_blocks():
        for j in range(blk.size):
            times[blk.a + j] = (heard[blk.b + j][1], heard[blk.b + j][2])
    # interpolate gaps
    i = 0
    while i < len(a):
        if times[i] is not None:
            i += 1
            continue
        j = i
        while j < len(a) and times[j] is None:
            j += 1
        t0 = times[i - 1][1] if i > 0 else 0.0
        t1 = times[j][0] if j < len(a) else dur
        span = [len(a[k]) + 1 for k in range(i, j)]
        tot, acc = sum(span), t0
        for k, n in zip(range(i, j), span):
            d = (t1 - t0) * n / tot
            times[k] = (acc, acc + d)
            acc += d
        i = j
    return times  # type: ignore[return-value]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("id")
    ap.add_argument("--placeholder", action="store_true")
    ap.add_argument("--grid", type=float, default=10.0)
    ap.add_argument("--voice", default="Russian_ReliableMan")
    ap.add_argument("--speed", type=float, default=1.35)
    ap.add_argument("--emotion", default=None)
    ap.add_argument("--only", default="")
    a = ap.parse_args()
    N = HERE / "narration" / a.id
    T = N / "takes"
    T.mkdir(parents=True, exist_ok=True)
    secs = sections(N / "script.md")
    only = set(filter(None, a.only.split(",")))

    if not a.placeholder:
        sys.path.insert(0, str(RS / "scripts"))
        import replicate_tts as R
        for s in secs:
            f = T / f"s{s['id']}.wav"
            if f.exists() and not (only and s["id"] in only):
                continue
            text = " ".join(spoken(l) for l in s["lines"])
            data = R.synth("minimax", text, a.voice, a.emotion, a.speed)
            tmp = T / f"s{s['id']}.raw"
            tmp.write_bytes(data)
            subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(tmp), "-ac", "1", "-ar", str(SR), str(f)], check=True)
            tmp.unlink()
            print(f"voiced s{s['id']}: {sf.info(str(f)).duration:.2f}s  | {text[:70]}", flush=True)
        from faster_whisper import WhisperModel
        model = WhisperModel("small", compute_type="int8")

    words, cards, rows = [], [], []
    track = np.zeros(int(SR * (len(secs) * a.grid + 15)), dtype=np.float32)
    end_prev = 0.0
    for k, s in enumerate(secs):
        lines = s["lines"]
        sw, line_of, seps = [], [], set()
        for li, l in enumerate(lines):
            toks = display(l).split()
            # word index ending a «//» chunk or a line -> a slightly longer pause in placeholder mode
            chunk_ends = []
            n = 0
            for chunk in l.split("//"):
                n += len(display(chunk).split())
                chunk_ends.append(len(sw) + n - 1)
            seps.update(chunk_ends)
            sw += toks
            line_of += [li] * len(toks)
        if a.placeholder:
            tm = estimate(sw, seps)
            audio = np.zeros(int(SR * (tm[-1][1] + 0.1)), dtype=np.float32)
        else:
            f = T / f"s{s['id']}.wav"
            audio = load(f)
            tmp = T / f"_s{s['id']}_trim.wav"
            sf.write(str(tmp), audio, SR)
            heard = whisper_words(tmp, model)
            tmp.unlink()
            tm = align(sw, heard, len(audio) / SR)
            r = difflib.SequenceMatcher(None, [norm(w) for w in sw], [norm(h[0]) for h in heard]).ratio()
            print(f"s{s['id']} match {r:.2f} dur {len(audio) / SR:.2f}s", flush=True)
        dur = len(audio) / SR
        last = k == len(secs) - 1
        start = 0.15 if k == 0 else (round(end_prev + 0.7, 3) if last else k * a.grid)
        if not last and k > 0 and start < end_prev + 0.25:
            print(f"WARN s{s['id']}: previous section runs to {end_prev:.2f}s, past the {start:.0f}s mark — shorten its text or raise --speed", flush=True)
            start = round(end_prev + 0.25, 3)
        i0 = int(start * SR)
        track[i0:i0 + len(audio)] += audio
        end_prev = start + dur
        rows.append({"id": s["id"], "start": round(start, 3), "end": round(end_prev, 3)})
        base = len(words)
        for li in range(len(lines)):
            idx = [base + j for j, x in enumerate(line_of) if x == li]
            cards.append({"i": len(cards), "start": round(start + tm[idx[0] - base][0], 3), "end": round(start + tm[idx[-1] - base][1], 3), "words": idx})
        for j, w in enumerate(sw):
            words.append({"i": base + j, "text": w, "start": round(start + tm[j][0], 3), "end": round(start + tm[j][1], 3), "card": len(cards) - len(lines) + line_of[j]})
    total = round(end_prev + 0.3, 3)
    sf.write(str(N / "voice.wav"), track[: int(total * SR)], SR)
    (N / "words.json").write_text(json.dumps({"words": words, "cards": cards, "duration": total, "placeholder": a.placeholder}, ensure_ascii=False, indent=1), encoding="utf-8")
    (N / "sections.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{'PLACEHOLDER ' if a.placeholder else ''}voice {total:.2f}s, {len(words)} words, {len(cards)} cards")
    for r in rows:
        print(f"  s{r['id']}: {r['start']:6.2f} – {r['end']:6.2f}")


if __name__ == "__main__":
    main()
