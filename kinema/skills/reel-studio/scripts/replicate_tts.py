"""Replicate TTS: the strongest hosted voice models behind one call, tuned for an energetic Russian reel voice-over.

    python replicate_tts.py --model minimax --voice Russian_HandsomeChildhoodFriend --text "..." --out take.wav [--style "..."]
    python replicate_tts.py --list                         # models + recommended voices

Token: REPLICATE_API_TOKEN from the environment or reel-studio/.secrets.env (never commit / print it).
tts.py uses this through `--engine replicate --model <key> --voice <voice>` (word timings via Whisper alignment).

Model keys (all official Replicate models):
    eleven   elevenlabs/v3                 most expressive; audio tags like [excited] inside the text
    minimax  minimax/speech-2.8-hd         studio quality, native Russian system voices, emotion presets, pitch in semitones
    gemini   google/gemini-3.1-flash-tts   style steered by a natural-language prompt
    inworld  inworld/realtime-tts-2        bracketed natural-language steering
    qwen     qwen/qwen3-tts                voice_design: a voice built from a text description (no cloning)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:
        pass

RS = Path(__file__).resolve().parent.parent
API = "https://api.replicate.com/v1"

# the brief all prompts share: what the user's reference reels sound like (voice_profile.py: ~155 Hz, ~16 st melody, ~2.7 w/s)
VO_BRIEF_EN = ("Read this Russian script aloud as a young male voice-over artist (about 25) for viral tech Reels: energetic, "
               "confident, smiling, fast pace, punchy emphasis on key words, rising intonation on questions. Natural mid-range "
               "male pitch, not shouting, not cartoonish. Native Russian pronunciation.")

MODELS = {
    "eleven": dict(slug="elevenlabs/v3", voices=["Mark", "Austin", "Gaming", "Roger", "Fin", "Dave", "Drew", "Paul", "James"],
                   default_voice="Mark"),
    "minimax": dict(slug="minimax/speech-2.8-hd",
                    voices=["Russian_HandsomeChildhoodFriend", "Russian_AttractiveGuy", "Russian_ReliableMan", "Russian_Bad-temperedBoy"],
                    default_voice="Russian_HandsomeChildhoodFriend"),
    "gemini": dict(slug="google/gemini-3.1-flash-tts", voices=["Puck", "Fenrir", "Sadachbia", "Achird", "Orus", "Zubenelgenubi", "Charon"],
                   default_voice="Puck"),
    "inworld": dict(slug="inworld/realtime-tts-2", voices=["Dmitry", "Nikolai", "Dennis", "Alex", "Mark"], default_voice="Dmitry"),
    "qwen": dict(slug="qwen/qwen3-tts", voices=["design"], default_voice="design"),
}


def token() -> str:
    t = os.environ.get("REPLICATE_API_TOKEN")
    if not t:
        f = RS / ".secrets.env"
        if f.exists():
            for line in f.read_text(encoding="utf-8").splitlines():
                k, _, v = line.partition("=")
                if k.strip() == "REPLICATE_API_TOKEN":
                    t = v.strip()
    if not t:
        raise SystemExit("REPLICATE_API_TOKEN is not set (env or reel-studio/.secrets.env)")
    return t


def _req(method: str, url: str, body: dict | None = None, wait: bool = False) -> dict:
    h = {"Authorization": f"Bearer {token()}", "Content-Type": "application/json", "User-Agent": "reel-studio/1.0"}
    if wait:
        h["Prefer"] = "wait=60"
    for attempt in range(12):
        r = urllib.request.Request(url, data=json.dumps(body).encode() if body is not None else None, headers=h, method=method)
        try:
            with urllib.request.urlopen(r, timeout=120) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            msg = e.read().decode("utf-8", "replace")
            if e.code == 429 and attempt < 11:  # low-credit accounts: 6 predictions/min, burst 1
                try:
                    wait_s = float(json.loads(msg).get("retry_after", 10))
                except Exception:
                    wait_s = 10.0
                time.sleep(wait_s + 1.0)
                continue
            raise SystemExit(f"Replicate {e.code}: {msg[:600]}")
    raise SystemExit("Replicate: still throttled")


# ------------------------------------------------------------------ spend cap (user rule: at most $3 per job)
# Replicate's API does not report the price of a prediction, so every call is charged here at a deliberately HIGH
# estimate before it is sent; a call that would push the job over the cap is refused. One job = one task / video:
# set REPLICATE_JOB (e.g. the project id); without it the job is the calendar day. Ledger: reel-studio/.replicate_budget.json
SPEND_CAP = float(os.environ.get("REPLICATE_CAP_USD", "3.0"))
PRICE_USD = {  # conservative per-call estimates
    "google/gemini-3.1-flash-tts": 0.03,
    "google/nano-banana-pro": 0.30,
    "hyper3d/rodin": 1.50,
    "firtoz/trellis": 0.10,
}
DEFAULT_PRICE = 0.15
LEDGER = RS / ".replicate_budget.json"


def _job() -> str:
    return os.environ.get("REPLICATE_JOB") or time.strftime("day-%Y-%m-%d")


def charge(slug: str, n: int = 1) -> float:
    """reserve the estimated price of n predictions of `slug` for the current job; refuse past the cap"""
    import threading
    lock = globals().setdefault("_LEDGER_LOCK", threading.Lock())
    with lock:
        led = json.loads(LEDGER.read_text(encoding="utf-8")) if LEDGER.exists() else {}
        job = _job()
        spent = float(led.get(job, 0.0))
        cost = PRICE_USD.get(slug, DEFAULT_PRICE) * n
        if spent + cost > SPEND_CAP + 1e-9:
            raise SystemExit(f"Replicate spend cap: job '{job}' has used ~${spent:.2f} of ${SPEND_CAP:.2f}; "
                             f"{slug} (~${cost:.2f}) refused. Ask the user before raising the cap.")
        led[job] = round(spent + cost, 4)
        LEDGER.write_text(json.dumps(led, indent=1), encoding="utf-8")
        return spent + cost


def refund(slug: str, n: int = 1) -> None:
    """a prediction that never ran (rejected before start) gives its reservation back"""
    import threading
    lock = globals().setdefault("_LEDGER_LOCK", threading.Lock())
    with lock:
        led = json.loads(LEDGER.read_text(encoding="utf-8")) if LEDGER.exists() else {}
        job = _job()
        led[job] = round(max(0.0, float(led.get(job, 0.0)) - PRICE_USD.get(slug, DEFAULT_PRICE) * n), 4)
        LEDGER.write_text(json.dumps(led, indent=1), encoding="utf-8")


def run(slug: str, inp: dict, timeout: float = 600) -> bytes:
    charge(slug)
    try:
        p = _req("POST", f"{API}/models/{slug}/predictions", {"input": inp}, wait=True)
    except SystemExit as e:
        if " 402" in str(e) or " 422" in str(e):
            refund(slug)  # rejected before it ran: nothing was billed
        raise
    t0 = time.time()
    while p.get("status") not in ("succeeded", "failed", "canceled"):
        if time.time() - t0 > timeout:
            raise SystemExit(f"{slug}: timed out ({p.get('status')})")
        time.sleep(1.5)
        p = _req("GET", p["urls"]["get"])
    if p["status"] != "succeeded":
        raise SystemExit(f"{slug}: {p['status']} — {str(p.get('error'))[:500]}")
    out = p["output"]
    if isinstance(out, dict):
        out = out.get("audio") or out.get("audio_out") or next(iter(out.values()))
    if isinstance(out, list):
        out = out[0]
    with urllib.request.urlopen(urllib.request.Request(out, headers={"User-Agent": "reel-studio/1.0"}), timeout=120) as r:
        return r.read()


def build_input(model: str, text: str, voice: str | None, style: str | None = None, speed: float | None = None, pitch: int | None = None) -> dict:
    m = MODELS[model]
    voice = voice or m["default_voice"]
    if model == "eleven":
        tag = style or "[excited]"
        return dict(prompt=f"{tag} {text}", voice=voice, stability=0.0 if style is None else 0.5, similarity_boost=0.75,
                    style=0.6, speed=speed or 1.08, language_code="ru")
    if model == "minimax":
        return dict(text=text, voice_id=voice, speed=speed or 1.12, pitch=pitch or 0, emotion=style or "happy",
                    language_boost="Russian", sample_rate=44100, audio_format="wav")
    if model == "gemini":
        return dict(text=text, voice=voice, language_code="ru-RU",
                    prompt=style or VO_BRIEF_EN)
    if model == "inworld":
        lead = style or "[energetic, excited, confident young male narrator, fast pace]"
        return dict(text=f"{lead} {text}", voice_id=voice, language="ru", temperature=1.1, speaking_rate=speed or 1.1,
                    audio_format="wav", sample_rate=48000)
    if model == "qwen":
        return dict(text=text, mode="voice_design", language="Russian",
                    voice_description=("Young Russian man, about 25, bright energetic voice-over voice, clear diction, "
                                       "confident and friendly, slightly higher pitch, studio quality"),
                    style_instruction=style or "excited, energetic, fast-paced, punchy emphasis on key words, smiling")
    raise SystemExit(f"unknown model {model}")


def synth(model: str, text: str, voice: str | None = None, style: str | None = None, speed: float | None = None, pitch: int | None = None) -> bytes:
    return run(MODELS[model]["slug"], build_input(model, text, voice, style, speed, pitch))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", choices=list(MODELS))
    ap.add_argument("--voice", default=None)
    ap.add_argument("--style", default=None)
    ap.add_argument("--speed", type=float, default=None)
    ap.add_argument("--pitch", type=int, default=None)
    ap.add_argument("--text", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    if a.list or not a.model:
        for k, m in MODELS.items():
            print(f"{k:8} {m['slug']:30} voices: {', '.join(m['voices'])}")
        return
    data = synth(a.model, a.text, a.voice, a.style, a.speed, a.pitch)
    Path(a.out).write_bytes(data)
    print(f"{a.out} ({len(data) // 1024} KB)")


if __name__ == "__main__":
    main()
