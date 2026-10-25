"""SFX library manager: retire the synthetic "8-bit" sounds, import a real sound pack, map every id onto it.

    python sfx_library.py status                       what is playable / retired / mapped to the pack
    python sfx_library.py retire                       apply RETIRED (files move to assets/sfx-retired, ids become aliases)
    python sfx_library.py import <dir|zip> [--dry] [--map "substring=category" ...] [--category whoosh] [--keep-generated]
    python sfx_library.py reset-pack                   remove the imported pack, restore the previous aliases
    python sfx_library.py docs                         regenerate the SFX part of references/sound.md

Index entries (engine/public/sfx/index.json):
    {id, file, category, desc, tags, dur, peak, source}       playable ("gen" = synthesized, "pack" = imported)
    {..., alias: "<id>" | null}                              plays another sound instead (null = silence, no error)
The engine (core/plan.ts) follows alias chains, so blocks and transitions keep asking for "pop-soft", "tick-roll" etc.
and get the pack's sound once it is imported — no code changes.

Import: wav / mp3 / ogg / flac / aif / m4a. Category from file + folder names (EN/RU keywords), else from the sound
itself (length, attack, brightness). Every file is trimmed, faded, converted to 48 kHz stereo and levelled to the
loudness the mixer expects for its category; the peak moment is measured for cut alignment.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import wave
import zipfile
from pathlib import Path

import numpy as np

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:
        pass

RS = Path(__file__).resolve().parent.parent
SFX = RS / "engine" / "public" / "sfx"
INDEX = SFX / "index.json"
RETIRED_DIR = RS / "assets" / "sfx-retired"
PACKS_DIR = RS / "assets" / "sfx-packs"
SR = 48000

# Synthetic tonal blips that read as 8-bit / toy sounds -> replacement id, or None = silence until a pack provides one.
RETIRED: dict[str, str | None] = {
    **{k: None for k in ["click-crisp", "click-soft", "click-mouse", "click-trackpad", "click-button", "click-glass", "click-wood",
                         "click-tiny", "click-double", "click-select", "click-crisp-low", "click-crisp-high"]},
    **{k: None for k in ["pop-soft", "pop-high", "pop-low", "pop-bubble", "pop-bubble-high", "pop-cork", "pop-triple", "pop-plop",
                         "pop-soft-low", "pop-soft-high"]},
    **{k: None for k in ["tick-digital", "tick-soft", "tick-wood", "tick-clock", "tick-meter", "tick-roll", "tick-digital-low",
                         "tick-digital-high"]},
    **{k: None for k in ["key-single", "key-space", "key-enter"]},
    **{k: None for k in ["ding-soft", "ding-bright", "chime-two-up", "chime-two-down", "chime-triad", "chime-glass", "chime-message",
                         "chime-calm", "ping", "ping-sonar", "ding-soft-low", "ding-soft-high"]},
    **{k: None for k in ["success-pluck", "success-chime", "success-check", "success-soft", "success-level", "success-coin",
                         "error-buzz", "error-down", "deny-tap"]},
    "error-thud": "thud",
    **{k: None for k in ["glitch-short", "glitch-medium", "glitch-long", "data-blips", "scan-beep", "hum-on", "power-off", "modem-chirp"]},
    **{k: None for k in ["sparkle", "sparkle-rise", "shimmer-pad", "star", "magic-wand"]},
    **{k: None for k in ["shutter", "toggle-on", "toggle-off", "scroll", "lock", "unlock", "cash", "drop-in", "hover"]},
    **{k: None for k in ["sting-logo", "sting-soft", "sting-dark", "sting-bright"]},
    "hit-metal": "hit-punch",
    "hit-glitch": "hit-punch",
    "trans-air-sparkle": "whoosh-airy",
    "trans-glitch-cut": "trans-whoosh-hit",
    # 2026-10-20: the user heard the synthesized air/noise sounds as a loud, unclear "blizzard" (transition whooshes,
    # wind, mask breathing, tape rips, radio static). Silence them; transitions cut clean, cues come from the pack.
    **{k: None for k in ["whoosh-short", "whoosh-medium", "whoosh-long", "whoosh-up", "whoosh-down", "whoosh-airy", "whoosh-deep",
                         "whoosh-pan-lr", "whoosh-pan-rl", "whoosh-double", "whoosh-reverse", "whoosh-cloud", "whoosh-short-low",
                         "whoosh-short-high"]},
    **{k: None for k in ["swipe-fast", "swipe-soft", "swipe-up", "swipe-down", "swipe-paper", "swipe-tiny", "swipe-fast-low", "swipe-fast-high"]},
    **{k: None for k in ["zoom-in", "zoom-out", "cursor-move", "riser-noise", "suck-in", "air-high", "wind", "trans-whoosh-hit", "trans-zoom-through", "trans-swish-pop"]},
    **{k: None for k in ["wind-ash", "breath-mask", "tape-rip", "radio-static", "radio-voice", "radio-tune", "steps-debris", "steps-concrete",
                         "water-pour", "can-open"]},
}

CATEGORIES = ["whoosh", "swipe", "click", "pop", "tick", "type", "notify", "result", "impact", "riser", "digital", "shimmer", "foley", "alarm",
              "ui", "sting", "ambience", "transition"]
# keyword -> category (checked in order; file name first, then folder names)
KEYWORDS: list[tuple[str, str]] = [
    (r"transition|трансл|переход", "transition"),
    (r"whoosh|woosh|swoosh|swish|whip|swing|\bpass|fly.?by|вжух|свуш|свист", "whoosh"),
    (r"swipe|slide|flick|свайп|слайд", "swipe"),
    (r"riser|rise|uplift|build|tension|reverse|downlift|suck|nарастан|подъ[её]м|райзер", "riser"),
    (r"impact|hit|boom|punch|thud|slam|kick|bass.?drop|sub.?drop|braam|удар|бум|хит", "impact"),
    (r"typing|typewriter|keyboard|keystroke|\bkeys?\b|клав|печат", "type"),
    (r"click|tap|button|mouse|press|клик|щелч|кнопк|тап", "click"),
    (r"pop|bubble|blip|bloop|поп|пузыр", "pop"),
    (r"tick|counter|clock|тик|счетчик|счётчик", "tick"),
    (r"notif|ding|chime|bell|message|alert|ping|уведом|звон|сообщ", "notify"),
    (r"success|correct|complete|done|win|confirm|error|fail|wrong|deny|успех|ошиб|готово", "result"),
    (r"glitch|digital|data|scan|beep|computer|tech|глитч|цифр|данн|скан", "digital"),
    (r"sparkle|shimmer|magic|twinkle|glow|блеск|магия|искр", "shimmer"),
    (r"sting|logo|intro|outro|reveal|стинг|лого", "sting"),
    (r"ambien|room|drone|atmos|city|wind|hum|tone|амбиент|атмосф|гул|город|ветер", "ambience"),
    (r"paper|card|camera|shutter|cash|coin|lock|toggle|switch|zoom|scroll|stamp|marker|pen|page|бумаг|камер|монет|замок", "ui"),
]
_NEG = re.compile(r"error|fail|deny|denied|wrong|reject|nope|ошиб|отказ|провал", re.I)
_POS = re.compile(r"success|correct|complete|done|confirm|win|coin|level|unlock|check|успех|готово|верно", re.I)


def polarity(text: str) -> int:
    """-1 = error / bad, +1 = success / good, 0 = neutral."""
    return -1 if _NEG.search(text) else 1 if _POS.search(text) else 0


CAT_MAX_SEC = {"ambience": 20.0, "riser": 8.0, "sting": 6.0, "transition": 4.0}


# ------------------------------------------------------------------ io
def load_index() -> list[dict]:
    return json.loads(INDEX.read_text(encoding="utf-8"))


def save_index(ix: list[dict]) -> None:
    INDEX.write_text(json.dumps(ix, ensure_ascii=False, indent=1), encoding="utf-8")


def decode(path: Path) -> np.ndarray:
    raw = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", str(path), "-vn", "-ac", "2", "-ar", str(SR),
                          "-f", "f32le", "pipe:1"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).astype(np.float64).reshape(-1, 2)


def read_wav(path: Path) -> np.ndarray:
    with wave.open(str(path)) as w:
        ch = w.getnchannels()
        x = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(np.float64).reshape(-1, ch) / 32768
    return x if ch == 2 else np.repeat(x, 2, axis=1)


def write_wav(path: Path, x: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype("<i2").tobytes())


# ------------------------------------------------------------------ analysis
def env_db(x: np.ndarray, win_s: float = 0.02) -> np.ndarray:
    m = np.abs(x).max(axis=1)
    k = max(1, int(win_s * SR))
    e = np.sqrt(np.convolve(m ** 2, np.ones(k) / k, mode="same"))
    return 20 * np.log10(e + 1e-9)


def punch_db(x: np.ndarray) -> float:
    """Loudest 50 ms RMS, dBFS — what the ear compares between short effects."""
    m = x.mean(axis=1)
    k = int(0.05 * SR)
    if len(m) < k:
        return float(20 * np.log10(np.sqrt((m ** 2).mean()) + 1e-9))
    e = np.convolve(m ** 2, np.ones(k) / k, mode="valid")
    return float(10 * np.log10(e.max() + 1e-12))


def peak_time(x: np.ndarray) -> float:
    return float(np.argmax(env_db(x, 0.02)) / SR)


def features(x: np.ndarray) -> dict:
    m = x.mean(axis=1)
    e = env_db(x, 0.01)
    pk = int(np.argmax(e))
    X = np.abs(np.fft.rfft(m * np.hanning(len(m)))) ** 2
    f = np.fft.rfftfreq(len(m), 1 / SR)
    cent = float((X * f).sum() / (X.sum() + 1e-12))
    low = float(X[f < 150].sum() / (X.sum() + 1e-12))
    return dict(dur=len(m) / SR, attack=pk / SR, cent=cent, low=low, rise=(e[pk] - e[0]) if pk > 0 else 0.0)


def classify(path: Path, rel_parts: list[str], x: np.ndarray, maps: list[tuple[str, str]], force: str | None) -> tuple[str, str]:
    if force:
        return force, "forced"
    name = path.stem.lower()
    for sub, cat in maps:
        if sub.lower() in path.name.lower():
            return cat, "map"
    for text, how in [(name, "name")] + [(p.lower(), "folder") for p in reversed(rel_parts)]:
        for rx, cat in KEYWORDS:
            if re.search(rx, text):
                return cat, how
    ft = features(x)
    if ft["dur"] > 6:
        return "ambience", "audio"
    if ft["dur"] > 1.6 and ft["attack"] > ft["dur"] * 0.6:
        return "riser", "audio"
    if ft["low"] > 0.25 and ft["attack"] < 0.05:
        return "impact", "audio"
    if ft["dur"] < 0.18:
        return ("click" if ft["cent"] > 1800 else "pop"), "audio"
    if ft["attack"] > 0.08:
        return "whoosh", "audio"
    return "ui", "audio"


def slug(s: str) -> str:
    tr = dict(zip("абвгдеёжзийклмнопрстуфхцчшщъыьэюя", ["a", "b", "v", "g", "d", "e", "e", "zh", "z", "i", "y", "k", "l", "m", "n", "o",
                                                       "p", "r", "s", "t", "u", "f", "h", "c", "ch", "sh", "sch", "", "y", "", "e", "yu", "ya"]))
    s = "".join(tr.get(c, c) for c in s.lower())
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:40] or "sound"


# ------------------------------------------------------------------ commands
def apply_retired(ix: list[dict] | None = None, quiet: bool = False) -> list[dict]:
    ix = ix if ix is not None else load_index()
    moved = 0
    for e in ix:
        if e["id"] not in RETIRED or e.get("retired"):
            continue
        src = SFX.parent / e["file"] if e.get("file") else None
        if src and src.exists():
            dst = RETIRED_DIR / Path(e["file"]).relative_to("sfx")
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
            moved += 1
        e["retired"] = True
        e["retiredFile"] = e.pop("file", e.get("retiredFile"))
        e["alias"] = RETIRED[e["id"]]
        e["alias0"] = RETIRED[e["id"]]
    for d in sorted(SFX.glob("*/"), reverse=True):
        if d.is_dir() and not any(d.iterdir()):
            d.rmdir()
    save_index(ix)
    if not quiet:
        print(f"retired {sum(1 for e in ix if e.get('retired'))} synthetic sounds ({moved} files moved to {RETIRED_DIR})")
    return ix


def gen_levels(ix: list[dict]) -> dict[str, float]:
    """Median punch loudness per category of the synthesized library (active + retired files)."""
    lv: dict[str, list[float]] = {}
    for e in ix:
        if e.get("source") == "pack":
            continue
        f = SFX.parent / e["file"] if e.get("file") else (RETIRED_DIR / Path(e["retiredFile"]).relative_to("sfx") if e.get("retiredFile") else None)
        if f and f.exists():
            lv.setdefault(e["category"], []).append(punch_db(read_wav(f)))
    return {k: float(np.median(v)) for k, v in lv.items()}


def safe_extract(zp: Path) -> Path:
    dst = PACKS_DIR / slug(zp.stem)
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True)
    with zipfile.ZipFile(zp) as z:
        for m in z.infolist():
            p = Path(m.filename)
            if m.is_dir() or p.is_absolute() or ".." in p.parts:
                continue
            if p.suffix.lower() not in AUDIO_EXT:
                continue
            out = dst / p
            out.parent.mkdir(parents=True, exist_ok=True)
            with z.open(m) as fi, open(out, "wb") as fo:
                shutil.copyfileobj(fi, fo)
    return dst


AUDIO_EXT = {".wav", ".mp3", ".ogg", ".flac", ".aif", ".aiff", ".m4a", ".opus", ".wma"}


def import_pack(src: Path, dry: bool, maps: list[tuple[str, str]], force: str | None, keep_generated: bool) -> None:
    ix = load_index()
    if not any(e.get("retired") for e in ix):
        ix = apply_retired(ix, quiet=True)
    if src.suffix.lower() == ".zip":
        src = safe_extract(src)
        print(f"unpacked to {src}")
    files = sorted(p for p in src.rglob("*") if p.suffix.lower() in AUDIO_EXT and p.is_file())
    if not files:
        raise SystemExit(f"no audio files in {src}")
    levels = gen_levels(ix)
    existing = {e["id"] for e in ix}
    new: list[dict] = []
    rows = []
    for f in files:
        try:
            x = decode(f)
        except subprocess.CalledProcessError:
            rows.append((f.name, "-", "unreadable", ""))
            continue
        if len(x) < SR * 0.02:
            rows.append((f.name, "-", "too short", ""))
            continue
        cat, how = classify(f, list(f.relative_to(src).parts[:-1]), x, maps, force)
        # trim silence, cap length, fade
        e = env_db(x, 0.005)
        top = e.max()
        on = np.where(e > top - 45)[0]
        a = max(0, on[0] - int(0.004 * SR))
        b = min(len(x), np.where(e > top - 60)[0][-1] + int(0.05 * SR))
        x = x[a:b]
        cap = CAT_MAX_SEC.get(cat, 3.0)
        if len(x) > cap * SR:
            x = x[: int(cap * SR)]
        fo = min(len(x) // 3, int(0.015 * SR))
        x[:int(0.002 * SR)] *= np.linspace(0, 1, int(0.002 * SR))[:, None][: len(x)]
        if fo > 0:
            x[-fo:] *= np.linspace(1, 0, fo)[:, None]
        # level to what the mixer expects for this category, never above -1 dBFS peak
        target = levels.get(cat, -14.0)
        g = 10 ** ((target - punch_db(x)) / 20)
        g = min(g, 10 ** (-1 / 20) / (np.abs(x).max() + 1e-9))
        x = x * g
        sid = f"pk-{cat}-{slug(f.stem)}"
        n = 2
        while sid in existing:
            sid = f"pk-{cat}-{slug(f.stem)}-{n}"
            n += 1
        existing.add(sid)
        rel = f"sfx/pack/{cat}/{sid}.wav"
        if not dry:
            write_wav(SFX.parent / rel, x)
        new.append(dict(id=sid, file=rel, category=cat, desc=f"pack: {f.relative_to(src).as_posix()}", tags=["pack", cat],
                        dur=round(len(x) / SR, 3), peak=round(peak_time(x), 3), source="pack"))
        rows.append((f.name, cat, how, f"{len(x) / SR:.2f}s"))
    w = max(len(r[0]) for r in rows)
    for r in rows:
        print(f"  {r[0]:<{w}}  {r[1]:<10} ({r[2]}) {r[3]}")
    by_cat: dict[str, list[dict]] = {}
    for e in new:
        by_cat.setdefault(e["category"], []).append(e)
    # packs file whooshes under "transitions" and vice versa
    if "transition" not in by_cat and "whoosh" in by_cat:
        by_cat["transition"] = by_cat["whoosh"]
    elif "whoosh" not in by_cat and "transition" in by_cat:
        by_cat["whoosh"] = by_cat["transition"]
    # map library ids onto the pack: closest length, spread over the 3 closest for variety
    mapped = 0
    for e in ix:
        if e.get("source") == "pack":
            continue
        pool = by_cat.get(e["category"])
        if not pool:
            continue
        if not e.get("retired") and keep_generated:
            continue
        # meaning first: an error sound never stands in for a success id (and vice versa)
        pe = polarity(e["id"] + " " + e.get("desc", ""))
        pool = [p for p in pool if pe == 0 or polarity(p["desc"]) in (0, pe)] if pe else pool
        if pe and not any(polarity(p["desc"]) == pe for p in pool):
            pool = []
        if not pool:
            continue
        dur = e.get("dur", 0.5)
        near = sorted(pool, key=lambda p: abs(np.log(max(p["dur"], 0.02) / max(dur, 0.02))))[:3]
        pick = near[int(hashlib.md5(e["id"].encode()).hexdigest(), 16) % len(near)]
        if "alias0" not in e:
            e["alias0"] = e.get("alias", "__none__") if "alias" in e else "__none__"
        e["alias"] = pick["id"]
        mapped += 1
    print(f"\n{len(new)} pack sounds in {len(by_cat)} categories: " + ", ".join(f"{k} {len(v)}" for k, v in sorted(by_cat.items())))
    print(f"{mapped} library ids now play pack sounds" + (" (dry run, nothing written)" if dry else ""))
    if not dry:
        ix = [e for e in ix if e.get("source") != "pack"] + new
        save_index(ix)
        write_docs(ix)


def reset_pack() -> None:
    ix = load_index()
    for e in ix:
        if "alias0" in e:
            if e["alias0"] == "__none__":
                e.pop("alias", None)
                e.pop("alias0")
            else:
                e["alias"] = e["alias0"]
    ix = [e for e in ix if e.get("source") != "pack"]
    shutil.rmtree(SFX / "pack", ignore_errors=True)
    save_index(ix)
    write_docs(ix)
    print("pack removed; aliases restored")


def status() -> None:
    ix = load_index()
    play = [e for e in ix if "alias" not in e]
    ali = [e for e in ix if e.get("alias")]
    mute = [e for e in ix if "alias" in e and e["alias"] is None]
    pack = [e for e in ix if e.get("source") == "pack"]
    print(f"playable {len(play)} (pack {len(pack)}) · aliased {len(ali)} · silent {len(mute)}")
    for cat in CATEGORIES:
        p = [e["id"] for e in play if e["category"] == cat]
        s = [e["id"] for e in mute if e["category"] == cat]
        a = [f"{e['id']}→{e['alias']}" for e in ali if e["category"] == cat]
        if p or s or a:
            print(f"\n{cat}: plays {len(p)}" + (f" · silent {len(s)}" if s else "") + (f" · aliased {len(a)}" if a else ""))
            if p:
                print("  " + " ".join(p))


def write_docs(ix: list[dict] | None = None) -> None:
    ix = ix if ix is not None else load_index()
    doc = RS / "references" / "sound.md"
    txt = doc.read_text(encoding="utf-8")
    head = txt[: txt.index("## SFX by category")] if "## SFX by category" in txt else txt
    play = [e for e in ix if "alias" not in e]
    pack = [e for e in play if e.get("source") == "pack"]
    lines = ["## SFX by category", "",
             f"{len(play)} playable sounds ({len(pack)} from the imported pack). Synthetic tonal blips (clicks, pops, ticks, chimes, "
             "coins, beeps, glitches) are retired: their ids still work in specs and blocks but play the pack's sound of the same "
             "category, or nothing until a pack is imported (`scripts/sfx_library.py import <folder|zip>`). "
             "`sfx_library.py status` shows the current mapping.", ""]
    for cat in CATEGORIES:
        items = [e for e in play if e["category"] == cat]
        ali = [e for e in ix if e["category"] == cat and "alias" in e]
        if not items and not ali:
            continue
        lines.append(f"### {cat} ({len(items)})")
        for e in items:
            lines.append(f"- `{e['id']}` — {e['desc']} ({e['dur']}s, peak {e['peak']}s)")
        if ali:
            lines.append("- also accepted: " + ", ".join(f"`{e['id']}`" + (f"→`{e['alias']}`" if e["alias"] else " (silent)") for e in ali))
        lines.append("")
    n_total = len(play)
    head = re.sub(r"^# Sound library \(.*?\)", f"# Sound library ({n_total} SFX + 8 music beds)", head, flags=re.M)
    doc.write_text(head + "\n".join(lines), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status")
    sub.add_parser("retire")
    sub.add_parser("reset-pack")
    sub.add_parser("docs")
    im = sub.add_parser("import")
    im.add_argument("src")
    im.add_argument("--dry", action="store_true")
    im.add_argument("--map", action="append", default=[], help='"substring=category" override, repeatable')
    im.add_argument("--category", choices=CATEGORIES, default=None, help="force one category for every file")
    im.add_argument("--keep-generated", action="store_true", help="only replace retired ids, keep synthesized whooshes etc.")
    a = ap.parse_args()
    if a.cmd == "status":
        status()
    elif a.cmd == "retire":
        write_docs(apply_retired())
    elif a.cmd == "reset-pack":
        reset_pack()
    elif a.cmd == "docs":
        write_docs()
    else:
        maps = []
        for m in a.map:
            k, _, v = m.partition("=")
            if v not in CATEGORIES:
                raise SystemExit(f"--map {m}: unknown category {v}")
            maps.append((k, v))
        import_pack(Path(a.src), a.dry, maps, a.category, a.keep_generated)


if __name__ == "__main__":
    main()
