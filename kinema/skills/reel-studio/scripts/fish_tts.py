"""Fish Audio TTS (S2.1-pro): Russian voices from the Fish library, emotion cues in [brackets], one take per script.

    python fish_tts.py --voices                          # shortlist (licensed first) + live search
    python fish_tts.py --search "энергичный" [--all]     # library search (default: licensed voices only)
    python fish_tts.py --voice <model_id> --text "..." --out take.wav [--cues reel|none] [--model s2.1-pro]
    python fish_tts.py --audition --out <folder>         # the audition text with every shortlisted voice
    python fish_tts.py --join voice_raw.wav --parts <url|file>... --texts chunks.json   # glue MCP chunk takes

Two ways to pay: REST API (this script / `tts.py --engine fish`) spends *API credit* (separate balance, fish.audio/app/
developers); the Fish MCP connector (`text_to_speech` tool) spends the account's *package credits* (free plan: ~7.7k,
1 credit per UTF-8 byte incl. tags, 500 bytes per call, licensed PVC voices cost double). MCP workflow for a reel:
    voice_direct.py <project> --max-bytes 480 --json <project>/chunks.json   -> one text_to_speech call per chunk
    fish_tts.py --join <project>/voice_raw.wav --parts <audio_url>... --texts <project>/chunks.json
    tts.py <project> --engine audio --audio <project>/voice_raw.wav          (untouched; --tighten 0.3 only if pauses drag)

Key: FISH_API_KEY from the environment or reel-studio/.secrets.env (never print it). The voice library listing works
without a key. tts.py uses this via `--engine fish --voice <model_id>` (timings via Whisper alignment, auto tempo).

Licensing: prefer voices with `licensed: true` (rights secured from the voice owner). The public library is full of
clones of real people (bloggers, actors, politicians) — never pick those.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:
        pass

RS = Path(__file__).resolve().parent.parent
API = "https://api.fish.audio"
UA = {"User-Agent": "reel-studio/1.0"}

# the user's pick (2026-10-20): public voice, rights NOT confirmed by Fish — fine for tests, a licensed voice is safer for ads
FAVORITE = "7312c38557eb4fb384e3874e8e9cea67"  # «Мужской Профессиональный213»

# pre-screened 2026-10-19 (voice_profile on their public samples); licensed = rights confirmed by Fish
SHORTLIST = [
    ("e2e94a830c6143f3a2ab60e1b0d16aec", "maksim", "Максим (Fish Official, licensed): young, clear, friendly", True),
    ("1a75349b724e4ae48da1ba05ae1a203e", "kinorakurs", "KinoRakurs (licensed): young, soft, social-media narrator", True),
    ("773ed9d827bb4c0d8b7a1b9267a4255e", "samoha", "samoha8989 (licensed): 25–35, fast energetic seller", True),
    ("55ece81d65564775ab448bab3b525599", "igor", "Игорь (Fish Official, licensed): warm, relaxed storyteller", True),
    ("48ec28a45588422b977a86460c11977f", "energetic-narrator", "«Энергичный Рассказчик» (public, NOT licensed)", False),
    ("7312c38557eb4fb384e3874e8e9cea67", "pro-male", "«Мужской Профессиональный» (public, NOT licensed)", False),
]

AUDITION = ("Хотите своё приложение, но боитесь, что выйдет хуже? Этот скилл разбирает чужое приложение по косточкам: "
            "экраны, тексты, отзывы. И за двадцать минут собирает план, как сделать лучше. Сколько стоит? Нисколько! "
            "Ссылка в шапке профиля.")


def key() -> str:
    k = os.environ.get("FISH_API_KEY")
    if not k:
        f = RS / ".secrets.env"
        if f.exists():
            for line in f.read_text(encoding="utf-8").splitlines():
                a, _, b = line.partition("=")
                if a.strip() == "FISH_API_KEY":
                    k = b.strip()
    if not k:
        raise SystemExit("FISH_API_KEY is not set: fish.audio -> API Keys, then add a line FISH_API_KEY=... to reel-studio/.secrets.env")
    return k


def cue(text: str, style: str = "reel") -> str:
    """Sentence-level emotion cues (S2 bracket syntax). 'reel' = the energy of the reference reels."""
    if style == "none":
        return text
    parts = re.findall(r"[^.!?…]+[.!?…]*", text)
    out = []
    for i, s in enumerate(p.strip() for p in parts if p.strip()):
        if i == 0:
            c = "[excited][confident, young energetic narrator]"
        elif s.endswith("?"):
            c = "[curious]"
        elif s.endswith("!"):
            c = "[very excited]"
        else:
            c = "[confident]"
        out.append(f"{c} {s}")
    return " ".join(out)


def synth(text: str, voice: str, model: str = "s2.1-pro", cues: str = "reel", temperature: float = 0.8, top_p: float = 0.8,
          speed: float = 1.0, fmt: str = "wav") -> bytes:
    body = dict(text=cue(text, cues), reference_id=voice, format=fmt, sample_rate=44100 if fmt == "wav" else None,
                latency="normal", normalize=True, language="ru", temperature=temperature, top_p=top_p,
                prosody=dict(speed=speed, volume=0, normalize_loudness=True))
    req = urllib.request.Request(f"{API}/v1/tts", data=json.dumps(body).encode(), method="POST",
                                 headers={**UA, "Authorization": f"Bearer {key()}", "Content-Type": "application/json", "model": model})
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            return r.read()
    except urllib.error.HTTPError as e:
        raise SystemExit(f"Fish {e.code}: {e.read().decode('utf-8', 'replace')[:500]}")


def join_takes(parts: list[bytes | str | Path], texts: list[str] | None = None, sr: int = 48000):
    """Glue chunk takes (files, URLs or bytes) into one mono take. The gap follows the direction at each seam:
    [long pause] 0.65 s · [pause] 0.45 s · next chunk opens with [short pause] 0.28 s · otherwise 0.14 s."""
    import numpy as np
    segs = []
    for p in parts:
        if isinstance(p, (str, Path)) and str(p).startswith("http"):
            with urllib.request.urlopen(urllib.request.Request(str(p), headers=UA), timeout=120) as r:
                p = r.read()
        cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", "pipe:0" if isinstance(p, bytes) else str(p),
               "-ac", "1", "-ar", str(sr), "-f", "f32le", "pipe:1"]
        x = np.frombuffer(subprocess.run(cmd, input=p if isinstance(p, bytes) else None, capture_output=True, check=True).stdout,
                          dtype=np.float32).astype(np.float64)
        k = int(0.01 * sr)
        e = np.sqrt(np.convolve(x ** 2, np.ones(k) / k, mode="same"))
        on = np.where(e > e.max() * 10 ** (-40 / 20))[0]
        if len(on):
            x = x[max(0, on[0] - int(0.03 * sr)): on[-1] + int(0.08 * sr)].copy()
        f = min(len(x) // 4, int(0.008 * sr))  # soft edges: no clicks at the seams
        if f > 0:
            x[:f] *= np.linspace(0, 1, f)
            x[-f:] *= np.linspace(1, 0, f)
        segs.append(x)
    out = [segs[0]]
    for i in range(1, len(segs)):
        prev, nxt = (texts[i - 1], texts[i]) if texts and len(texts) == len(segs) else ("", "")
        gap = 0.65 if re.search(r"\[long pause\]\s*$", prev) else 0.45 if re.search(r"\[pause\]\s*$", prev) else \
            0.28 if nxt.lstrip().startswith("[short pause]") else 0.14
        out += [np.zeros(int(gap * sr)), segs[i]]
    return np.concatenate(out)


def search(query: str | None = None, licensed: bool = True, n: int = 30) -> list[dict]:
    q = dict(page_size=n, language="ru", sort_by="task_count", licensed=str(licensed).lower())
    if query:
        q["title"] = query
    with urllib.request.urlopen(urllib.request.Request(f"{API}/model?{urllib.parse.urlencode(q)}", headers=UA), timeout=60) as r:
        return json.loads(r.read())["items"]


def audition(out: Path, model: str) -> None:
    out.mkdir(parents=True, exist_ok=True)
    for n, (vid, name, desc, lic) in enumerate(SHORTLIST, 1):
        raw = out / f"_raw-{name}.wav"
        raw.write_bytes(synth(AUDITION, vid, model))
        dst = out / f"{n}-fish-{name}{'' if lic else '-unlicensed'}.mp3"
        import loudnorm  # static gain only: no stretching, no dynamic loudness processing
        loudnorm.normalize(str(raw), str(dst), -16.0, 0.0)  # tp 0: gain only, no limiter on auditions
        print(f"  {dst.name}  ({desc})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--voices", action="store_true")
    ap.add_argument("--search", default=None)
    ap.add_argument("--all", action="store_true", help="search: include unlicensed public voices")
    ap.add_argument("--voice", default=None)
    ap.add_argument("--text", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--cues", default="reel", choices=["reel", "none"])
    ap.add_argument("--model", default="s2.1-pro")
    ap.add_argument("--audition", action="store_true")
    ap.add_argument("--join", default=None, help="glue chunk takes (files/URLs given in --parts) into this wav")
    ap.add_argument("--parts", nargs="*", default=[])
    ap.add_argument("--texts", default=None, help="chunks.json from voice_direct.py (pause-aware seams)")
    a = ap.parse_args()
    if a.join:
        import numpy as np
        texts = json.loads(Path(a.texts).read_text(encoding="utf-8")) if a.texts else None
        x = join_takes(a.parts, texts)
        sys.path.insert(0, str(Path(__file__).parent))
        from tts import write_wav
        write_wav(Path(a.join), x / (np.max(np.abs(x)) + 1e-9) * 0.89)
        print(f"{a.join} ({len(x) / 48000:.2f}s from {len(a.parts)} part(s))")
        return
    if a.voices or (a.search is None and not a.voice and not a.audition):
        for vid, name, desc, lic in SHORTLIST:
            print(f"{vid}  {name:20} {desc}")
        return
    if a.search is not None:
        for m in search(a.search or None, licensed=not a.all):
            print(f"{m['_id']}  {m['title'][:40]:40} {'licensed' if m.get('licensed') else '-':8} uses {m.get('task_count', 0):>8}  "
                  f"{','.join(m.get('tags', []))[:90]}")
        return
    if a.audition:
        audition(Path(a.out or "."), a.model)
        return
    data = synth(a.text, a.voice, a.model, a.cues)
    Path(a.out).write_bytes(data)
    print(f"{a.out} ({len(data) // 1024} KB)")


if __name__ == "__main__":
    main()
