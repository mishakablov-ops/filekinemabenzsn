"""Voiceover + word timings for a Reel Studio project.

    python tts.py <project_dir> [--preset energetic|andrew|remy|calm|plain] [--engine edge|eleven|audio|silent]
                  [--voice ID] [--rate +16%] [--pitch +40Hz] [--widen 1.5] [--emph 1.6] [--fx energetic|clean|off]
                  [--audio my_take.wav] [--gap 0.15] [--beats music/x.beats.json --every 2 --offset 0]

Reads <project_dir>/script.md, writes:
    voice.wav    48 kHz mono voiceover (not for --engine silent)
    words.json   {words[], cards[], duration}  -> captions + "@word" anchors in spec.json
    tts_report.json  pace / pauses / warnings

Voice presets (Edge TTS, free) — tuned against the user's reference reels with voice_profile.py:
    energetic  default: young energetic male VO — Dmitry raised to ~150 Hz, melody x1.5, key words lifted, VO mastering
    andrew     same treatment on en-US-AndrewMultilingualNeural reading Russian (warmer, more conversational)
    remy       fr-FR-RemyMultilingualNeural reading Russian (most melodic, lower)
    calm       Dmitry, natural pitch, light processing (serious topics)
    plain      Dmitry as is (the old default)
Explicit --voice/--rate/--pitch/--widen/--fx/--gap override the preset.
Expressive FX (vo_fx.py): pitch melody widened by TD-PSOLA — timing is untouched, so word timings stay exact;
words marked as accents in script.md (*x* [x] ==x== ^x^ __x__ !!x!! ++x++) get a pitch/level lift.

Engines:
    edge    Microsoft neural TTS (free, online). Word timings from the TTS itself.
    eleven  ElevenLabs (needs ELEVENLABS_API_KEY; --voice <voice_id>). Character timings from the API.
    replicate  hosted models via replicate_tts.py (token in .secrets.env): --model gemini|eleven|inworld|minimax|qwen
            --voice <name> [--style "..."]. The whole script is read in one take (best flow), timings via Whisper.
    fish    Fish Audio S2.1-pro via fish_tts.py (FISH_API_KEY in .secrets.env): --voice <model_id> (default: licensed
            "Максим"); sentence emotion cues added automatically. One take, timings via Whisper, auto tempo.
    audio   Your own recording / any external TTS: --audio file; timings via faster-whisper + script alignment.
    silent  No voice (music promos): cards are placed on the beat grid (--beats) every N beats.
"""
from __future__ import annotations

import argparse
import asyncio
import base64
import difflib
import json
import os
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from script_parse import Tok, parse_script, utterances  # noqa: E402

VOICE_PRESETS = {
    "energetic": dict(voice="ru-RU-DmitryNeural", rate="+16%", pitch="+50Hz", widen=1.7, emph=2.0, fx="energetic", gap=0.15),
    "andrew": dict(voice="en-US-AndrewMultilingualNeural", rate="+24%", pitch="+35Hz", widen=1.6, emph=2.0, fx="energetic", gap=0.14),
    "remy": dict(voice="fr-FR-RemyMultilingualNeural", rate="+24%", pitch="+50Hz", widen=1.5, emph=2.0, fx="energetic", gap=0.14),
    "calm": dict(voice="ru-RU-DmitryNeural", rate="+10%", pitch="+0Hz", widen=1.15, emph=1.0, fx="clean", gap=0.24),
    "plain": dict(voice="ru-RU-DmitryNeural", rate="+14%", pitch="+0Hz", widen=1.0, emph=0.0, fx="off", gap=0.18),
}
# hosted engines and the user's own recordings come out finished: leave the sound untouched (no FX, no stretching —
# the user heard rubberband tempo + dynamic loudnorm as "bugs"). Opt in with --fx clean / --tempo / --tighten.
ENGINE_DEFAULTS = {
    "eleven": dict(widen=1.0, emph=0.0, fx="off", gap=0.15),
    "audio": dict(widen=1.0, emph=0.0, fx="off", gap=0.15),
    "replicate": dict(widen=1.0, emph=0.0, fx="off", gap=0.15),
    "fish": dict(widen=1.0, emph=0.0, fx="off", gap=0.15),
}
EMPH_STYLES = {"italic", "accent", "mark", "alt", "outline", "neg", "pos"}

# console: always UTF-8 (Windows defaults to cp1251)
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:
        pass

SR = 48000


def norm(s: str) -> str:
    s = s.lower().replace("ё", "е").replace("́", "").replace("+", "")  # stress marks never reach matching
    s = re.sub(r"[«»\"“”„'’`.,!?…:;()\[\]{}*_=~^|/\\]", "", s)
    return s.strip("-—– ")


def decode_to_float(data: bytes | None = None, path: str | None = None) -> np.ndarray:
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", "pipe:0" if data is not None else path, "-ac", "1", "-ar", str(SR), "-f", "f32le", "pipe:1"]
    out = subprocess.run(cmd, input=data, capture_output=True, check=True).stdout
    return np.frombuffer(out, dtype=np.float32).astype(np.float64)


def write_wav(path: Path, x: np.ndarray) -> None:
    import wave
    x = np.clip(x, -1, 1)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((x * 32767).astype("<i2").tobytes())


def energy_end(x: np.ndarray, after: float, cap: float = 0.4, thresh_db: float = -42) -> float:
    a = int(after * SR)
    b = min(len(x), int((after + cap) * SR))
    if b <= a:
        return after
    seg = np.abs(x[a:b])
    win = int(0.01 * SR)
    th = 10 ** (thresh_db / 20)
    env = np.convolve(seg, np.ones(win) / win, mode="same")
    idx = np.where(env > th)[0]
    return after + ((idx[-1] / SR) if len(idx) else 0.0)


def tighten_pauses(x: np.ndarray, max_pause: float = 0.28, thresh_db: float = -45.0) -> np.ndarray:
    """Shorten silences longer than max_pause by cutting their middle (15 ms crossfade). The voice itself is untouched."""
    k = int(0.01 * SR)
    env = np.sqrt(np.convolve(x ** 2, np.ones(k) / k, mode="same"))
    quiet = env < (env.max() * 10 ** (thresh_db / 20))
    d = np.diff(np.concatenate([[0], quiet.astype(np.int8), [0]]))
    starts, ends = np.where(d == 1)[0], np.where(d == -1)[0]
    keep = int(max_pause * SR)
    xf = int(0.015 * SR)
    out, pos = [], 0
    for a0, b0 in zip(starts, ends):
        if a0 == 0 or b0 >= len(x) or (b0 - a0) <= keep + 2 * xf:
            continue
        cut_a, cut_b = a0 + keep // 2, b0 - keep // 2
        seg = x[pos:cut_a + xf].copy()
        if out:
            seg[:xf] *= np.linspace(0, 1, xf)
            out[-1][-xf:] *= np.linspace(1, 0, xf)
            out[-1][-xf:] += seg[:xf]
            seg = seg[xf:]
        out.append(seg)
        pos = cut_b
    tail = x[pos:].copy()
    if out:
        tail[:xf] *= np.linspace(0, 1, xf)
        out[-1][-xf:] *= np.linspace(1, 0, xf)
        out[-1][-xf:] += tail[:xf]
        tail = tail[xf:]
    out.append(tail)
    return np.concatenate(out)


def time_stretch(x: np.ndarray, tempo: float) -> np.ndarray:
    """Uniform tempo change, pitch and formants kept (rubberband)."""
    pk = np.max(np.abs(x)) + 1e-9
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "pipe:0",
           "-af", f"rubberband=tempo={tempo:.5f}:pitchq=quality:transients=smooth:formant=preserved", "-f", "f32le", "pipe:1"]
    y = subprocess.run(cmd, input=(x / pk * 0.5).astype(np.float32).tobytes(), capture_output=True, check=True).stdout
    return np.frombuffer(y, dtype=np.float32).astype(np.float64) * (pk / 0.5)


# ------------------------------------------------------------------ mapping spoken words -> timings
def map_times(spoken: list[str], hyp: list[tuple[float, float, str]]) -> list[tuple[float, float]]:
    """Align script words to recognised/boundary words. Returns (start, end) per script word."""
    a = [norm(w) for w in spoken]
    b = [norm(h[2]) for h in hyp]
    res: list[tuple[float, float] | None] = [None] * len(a)
    sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            for k in range(i2 - i1):
                h = hyp[j1 + k]
                res[i1 + k] = (h[0], h[1])
        elif op == "replace" and j2 > j1:
            # spread the hyp block over the script block proportionally to character length
            t0, t1 = hyp[j1][0], hyp[j2 - 1][1]
            lens = [max(1, len(a[k])) for k in range(i1, i2)]
            tot = sum(lens)
            acc = 0
            for k, L in zip(range(i1, i2), lens):
                s = t0 + (t1 - t0) * acc / tot
                acc += L
                e = t0 + (t1 - t0) * acc / tot
                res[k] = (s, e)
    # interpolate gaps
    n = len(res)
    for k in range(n):
        if res[k] is None:
            prev = next((res[j] for j in range(k - 1, -1, -1) if res[j]), None)
            nxt_i = next((j for j in range(k + 1, n) if res[j]), None)
            p_end = prev[1] if prev else (hyp[0][0] if hyp else 0.0)
            n_start = res[nxt_i][0] if nxt_i is not None else p_end + 0.3 * (n - k)
            gap_words = (nxt_i - k) if nxt_i is not None else (n - k)
            step = max(0.05, (n_start - p_end) / (gap_words + 0.0001))
            res[k] = (p_end, p_end + step)
    return [r for r in res]  # type: ignore


# ------------------------------------------------------------------ engines
async def _edge(text: str, voice: str, rate: str, pitch: str):
    import edge_tts
    comm = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch, boundary="WordBoundary")
    audio = bytearray()
    bounds = []
    async for ch in comm.stream():
        if ch["type"] == "audio":
            audio += ch["data"]
        elif ch["type"] == "WordBoundary":
            bounds.append((ch["offset"] / 1e7, (ch["offset"] + ch["duration"]) / 1e7, ch["text"]))
    return bytes(audio), bounds


def synth_edge(text: str, voice: str, rate: str, pitch: str):
    import time
    for attempt in range(8):
        try:
            data, bounds = asyncio.run(_edge(text, voice, rate, pitch))
            if not data:
                raise RuntimeError("empty audio")
            return decode_to_float(data), bounds
        except Exception as e:  # the free endpoint drops requests now and then
            if attempt == 7:
                raise
            print(f"  edge-tts retry {attempt + 1} ({type(e).__name__})", file=sys.stderr)
            time.sleep(0.8 + attempt * 0.7)


def synth_eleven(text: str, voice: str, model: str | None = None):
    """ElevenLabs with character timestamps. Energetic VO settings: low stability = livelier delivery.
    Model: ELEVENLABS_MODEL env (default eleven_multilingual_v2; eleven_v3 understands tags like [excited])."""
    model = model or os.environ.get("ELEVENLABS_MODEL", "eleven_multilingual_v2")
    key = os.environ.get("ELEVENLABS_API_KEY")
    if not key:
        raise SystemExit("ELEVENLABS_API_KEY is not set")
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice}/with-timestamps?output_format=mp3_44100_128"
    body = json.dumps({"text": text, "model_id": model, "voice_settings": {"stability": 0.35, "similarity_boost": 0.8, "style": 0.45, "use_speaker_boost": True}}).encode()
    req = urllib.request.Request(url, data=body, headers={"xi-api-key": key, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        js = json.loads(r.read())
    audio = decode_to_float(base64.b64decode(js["audio_base64"]))
    al = js.get("alignment") or js.get("normalized_alignment")
    chars, st, en = al["characters"], al["character_start_times_seconds"], al["character_end_times_seconds"]
    bounds, cur, cs = [], "", None
    for c, s, e in zip(chars, st, en):
        if c.isspace():
            if cur:
                bounds.append((cs, pe, cur))
            cur, cs = "", None
            continue
        if cs is None:
            cs = s
        cur += c
        pe = e
    if cur:
        bounds.append((cs, pe, cur))
    return audio, bounds


def whisper_words(path: str, lang: str = "ru", model: str = "small"):
    from faster_whisper import WhisperModel
    m = WhisperModel(model, device="cpu", compute_type="int8")
    # decode with ffmpeg ourselves (avoids PyAV version issues)
    raw = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", path, "-ac", "1", "-ar", "16000", "-f", "f32le", "pipe:1"],
                         capture_output=True, check=True).stdout
    pcm = np.frombuffer(raw, dtype=np.float32)
    segs, _ = m.transcribe(pcm, language=lang, word_timestamps=True, vad_filter=False)
    out = []
    for s in segs:
        for w in s.words:
            out.append((float(w.start), float(w.end), w.word.strip()))
    return out


# ------------------------------------------------------------------ build words.json
def build_words(cards, tok_times: dict[int, tuple[float, float]], duration: float):
    words, card_out = [], []
    idx = 0
    for c in cards:
        ids = []
        for t in c.toks:
            s, e = tok_times[id(t)]
            disp = t.display
            words.append(dict(i=idx, text=disp, start=round(s, 3), end=round(e, 3), card=c.i, role=t.role,
                              style=t.style or None, line=t.line))
            ids.append(idx)
            idx += 1
        if ids:
            card_out.append(dict(i=c.i, start=words[ids[0]]["start"], end=words[ids[-1]]["end"], words=ids, mode=c.mode, pos=c.pos))
    for w in words:
        if w["style"] is None:
            del w["style"]
    for c in card_out:
        if c["mode"] is None:
            del c["mode"]
        if c["pos"] is None:
            del c["pos"]
    return dict(words=words, cards=card_out, duration=round(duration, 3))


def report(words: dict) -> dict:
    ws = words["words"]
    if not ws:
        return {}
    dur = ws[-1]["end"] - ws[0]["start"]
    gaps = [b["start"] - a["end"] for a, b in zip(ws, ws[1:])]
    warn = []
    wps = len(ws) / max(dur, 0.1)
    if wps < 2.2:
        warn.append(f"slow pace {wps:.2f} w/s (target 2.5–3.0): raise --rate")
    if wps > 3.3:
        warn.append(f"fast pace {wps:.2f} w/s: lower --rate or cut words")
    if ws[0]["start"] > 0.35:
        warn.append(f"voice starts late ({ws[0]['start']:.2f}s): hook must start immediately")
    long_gaps = [round(g, 2) for g in gaps if g > 0.8]
    if long_gaps:
        warn.append(f"{len(long_gaps)} pauses > 0.8 s: {long_gaps}")
    for c in words["cards"]:
        d = c["end"] - c["start"]
        if d < 0.35 and len(c["words"]) > 2:
            warn.append(f"card {c['i']} is on screen only {d:.2f}s")
    return dict(duration=words["duration"], words=len(ws), wps=round(wps, 2), cards=len(words["cards"]),
                max_gap=round(max(gaps) if gaps else 0, 2), warnings=warn)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--engine", default="edge", choices=["edge", "eleven", "replicate", "fish", "audio", "silent"])
    ap.add_argument("--model", default="gemini", help="replicate engine: gemini|eleven|inworld|minimax|qwen")
    ap.add_argument("--direction", default="rich", choices=["rich", "light", "none"], help="fish: automatic voice direction ([tags])")
    ap.add_argument("--style", default=None, help="replicate engine: style prompt / emotion / [tags]")
    ap.add_argument("--tempo", default=None, help="audio/replicate/fish: speed factor or \"auto\" (~2.6 w/s). Off by default: stretching colours the voice")
    ap.add_argument("--tighten", type=float, default=None, help="audio/replicate/fish: shorten pauses longer than this many seconds (clean cuts, no stretching)")
    ap.add_argument("--preset", default="energetic", choices=list(VOICE_PRESETS), help="voice character (Edge engine)")
    ap.add_argument("--voice", default=None)
    ap.add_argument("--rate", default=None, help="Edge speed, e.g. +16%%")
    ap.add_argument("--pitch", default=None, help="Edge pitch, e.g. +40Hz")
    ap.add_argument("--widen", type=float, default=None, help="melody range multiplier (1 = as is)")
    ap.add_argument("--emph", type=float, default=None, help="pitch lift on accent words, semitones (0 = off)")
    ap.add_argument("--fx", default=None, choices=["energetic", "clean", "off"], help="voice-over mastering chain")
    ap.add_argument("--audio", default=None)
    ap.add_argument("--gap", type=float, default=None, help="pause between sentences, s")
    ap.add_argument("--lead-in", type=float, default=0.08, help="silence before first word, s")
    ap.add_argument("--whisper-model", default="small")
    ap.add_argument("--beats", default=None)
    ap.add_argument("--every", type=float, default=2, help="silent mode: beats per card")
    ap.add_argument("--offset", type=float, default=0.0, help="silent mode: first card time, s")
    a = ap.parse_args()

    pdir = Path(a.project)
    cfg = dict(VOICE_PRESETS[a.preset]) if a.engine == "edge" else dict(ENGINE_DEFAULTS.get(a.engine, {}))
    for k in ("voice", "rate", "pitch", "widen", "emph", "fx", "gap"):
        if getattr(a, k) is not None:
            cfg[k] = getattr(a, k)
    for k, v in dict(rate="+14%", pitch="+0Hz", widen=1.0, emph=0.0, fx="off", gap=0.18).items():
        cfg.setdefault(k, v)
    a.rate, a.pitch, a.gap = cfg["rate"], cfg["pitch"], cfg["gap"]
    cards = parse_script((pdir / "script.md").read_text(encoding="utf-8"))
    tok_times: dict[int, tuple[float, float]] = {}

    if a.engine == "silent":
        grid = json.loads(Path(a.beats).read_text(encoding="utf-8")) if a.beats else None
        step = (grid["beatSec"] if grid else 0.5) * a.every
        t = a.offset
        for c in cards:
            n = len(c.toks)
            for k, tok in enumerate(c.toks):
                s = t + k * min(0.14, step / max(n, 1) * 0.5)
                tok_times[id(tok)] = (s, s + 0.12)
            t += step * max(1, round(n / 3 + 0.49))
        total = t + 0.5
        words = build_words(cards, tok_times, total)
        (pdir / "words.json").write_text(json.dumps(words, ensure_ascii=False, indent=1), encoding="utf-8")
        # no voice: pace / pause warnings don't apply
        print(json.dumps(dict(duration=words["duration"], cards=len(words["cards"]), card_starts=[c["start"] for c in words["cards"]]), ensure_ascii=False))
        return

    if a.engine in ("replicate", "fish"):
        text = " ".join(" ".join(w for t in u for w in t.spoken) for u in utterances(cards))
        if a.engine == "fish":
            import fish_tts
            import voice_direct
            fv = cfg.get("voice") or fish_tts.FAVORITE
            chunks = voice_direct.performed((pdir / "script.md").read_text(encoding="utf-8"), a.direction, 1800)
            print(f"  fish s2.1-pro · {fv} · {len(chunks)} directed chunk(s)", file=sys.stderr)
            x = fish_tts.join_takes([fish_tts.synth(c, fv, cues="none") for c in chunks], chunks, SR)
            buf = pdir / "voice_raw.wav"
            write_wav(buf, x / (np.max(np.abs(x)) + 1e-9) * 0.89)
            data = buf.read_bytes()
            src = f"fish:{fv}"
        else:
            import replicate_tts
            print(f"  replicate {a.model} · {cfg.get('voice') or replicate_tts.MODELS[a.model]['default_voice']}", file=sys.stderr)
            data = replicate_tts.synth(a.model, text, cfg.get("voice"), a.style)
            src = f"replicate:{a.model}:{cfg.get('voice') or replicate_tts.MODELS[a.model]['default_voice']}"
        raw = pdir / ("voice_raw.wav" if data[:4] == b"RIFF" else "voice_raw.mp3")
        raw.write_bytes(data)
        a.audio = str(raw)
        a.engine = "audio"
        cfg["source"] = src
    if a.engine == "audio":
        if not a.audio:
            raise SystemExit("--audio file required")
        x = decode_to_float(path=a.audio)
        if a.tighten:
            x = tighten_pauses(x, a.tighten)
            tight = Path(a.audio).with_name("voice_tight.wav")
            write_wav(tight, x / (np.max(np.abs(x)) + 1e-9) * 0.89)
            a.audio = str(tight)
            cfg["tighten"] = a.tighten
        hyp = whisper_words(a.audio, model=a.whisper_model)
        all_toks = [t for c in cards for t in c.toks]
        spoken = [(t, w) for t in all_toks for w in t.spoken]
        times = map_times([w for _, w in spoken], hyp)
        for t in all_toks:
            ts = [tm for (tt, _), tm in zip(spoken, times) if tt is t]
            tok_times[id(t)] = (ts[0][0], ts[-1][1])
        # tempo: hosted models often read slower than a reel needs; stretch uniformly (pitch kept), timings scale exactly
        tempo = None if a.tempo in (None, "auto") else float(a.tempo)
        if tempo is None and a.tempo == "auto":
            span = max(0.1, times[-1][1] - times[0][0])
            wps = len(times) / span
            tempo = min(1.22, 2.62 / wps) if wps < 2.45 else 1.0
        if tempo and abs(tempo - 1) > 0.01:
            x = time_stretch(x, tempo)
            tok_times = {k: (s0 / tempo, e0 / tempo) for k, (s0, e0) in tok_times.items()}
            cfg["tempo"] = round(tempo, 3)
            print(f"  tempo x{tempo:.3f}", file=sys.stderr)
        out = x
    else:
        voice = cfg.get("voice") or ("ru-RU-DmitryNeural" if a.engine == "edge" else "")
        if a.engine == "eleven" and not voice:
            raise SystemExit("--voice <ElevenLabs voice_id> required")
        pieces = []
        pos = a.lead_in
        for u in utterances(cards):
            words_sp = [w for t in u for w in t.spoken]
            text = " ".join(words_sp)
            if a.engine == "edge":
                audio, bounds = synth_edge(text, voice, a.rate, a.pitch)
            else:
                audio, bounds = synth_eleven(text, voice)
            if not bounds:
                raise SystemExit(f"no word timings returned for: {text}")
            head = max(0.0, bounds[0][0] - 0.04)
            tail = energy_end(audio, bounds[-1][1], 0.35)
            seg = audio[int(head * SR): int(tail * SR)]
            # tiny fades to avoid clicks
            f = min(len(seg) // 4, int(0.006 * SR))
            if f > 0:
                seg[:f] *= np.linspace(0, 1, f)
                seg[-f:] *= np.linspace(1, 0, f)
            times = map_times(words_sp, bounds)
            k = 0
            for t in u:
                n = len(t.spoken)
                st = times[k][0] - head + pos
                en = times[k + n - 1][1] - head + pos
                tok_times[id(t)] = (st, en)
                k += n
            pieces.append((pos, seg))
            gap = max(a.gap, u[-1].pause_after) if u[-1].pause_after else a.gap
            pos += len(seg) / SR + gap
            print(f"  ✓ {text[:70]}", file=sys.stderr)
        total = pos
        out = np.zeros(int(total * SR) + SR)
        for p, seg in pieces:
            s = int(p * SR)
            out[s:s + len(seg)] += seg
        out = out[: int((pos - a.gap + 0.05) * SR)]
    if cfg["widen"] != 1.0 or cfg["emph"] > 0 or cfg["fx"] != "off":
        import vo_fx
        if cfg["widen"] != 1.0 or cfg["emph"] > 0:
            emphasis = [tok_times[id(t)] for c in cards for t in c.toks if EMPH_STYLES & set(t.style or [])]
            out = vo_fx.expressive(out, widen=cfg["widen"], emphasis=emphasis if cfg["emph"] > 0 else (), emph_st=cfg["emph"])
        out = vo_fx.master(out, cfg["fx"])
        print(f"  fx: widen {cfg['widen']} · emphasis {cfg['emph']} st on accent words · master {cfg['fx']}", file=sys.stderr)
    pk = np.max(np.abs(out)) + 1e-9
    out = out * (10 ** (-1.5 / 20) / pk)
    write_wav(pdir / "voice.wav", out)
    words = build_words(cards, tok_times, len(out) / SR)
    (pdir / "words.json").write_text(json.dumps(words, ensure_ascii=False, indent=1), encoding="utf-8")
    rep = report(words)
    rep["voice"] = {k: cfg.get(k) for k in ("voice", "rate", "pitch", "widen", "emph", "fx", "gap", "source", "tempo", "tighten") if cfg.get(k) is not None} | {"engine": a.engine, "preset": a.preset if a.engine == "edge" else None}
    (pdir / "tts_report.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(rep, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
