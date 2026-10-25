"""Voice direction: turn script.md into a *performed* text with inline [tags] for expressive TTS engines
(Fish Audio S2, ElevenLabs v3, Inworld) — so the voice rises on the hook, asks the question, takes a beat before
the punchline, hits the accent words and smiles on the CTA, instead of reading flat text.

    python voice_direct.py <project_dir|script.md> [--level rich|light|none] [--max-bytes 480] [--json out.json]

Automatic rules (an explicit ((cue)) in the script always wins at that spot):
    hook — first sentence                      [excited, confident]
    question                                   [curious, rising intonation]
    answer right after a question               [short pause] + [very excited] (punch / "!") or [confident]
    exclamation, %slam card, lone !!x!! word    [very excited]
    accent run *x* [x] ==x== ^x^ __x__ ++x++   [emphasis] before it            (light: punch half of the card only)
    !!x!! inside a sentence                     [emphasis]
    ~~x~~ struck-out cliché                     [dismissive]
    paragraph pause / <0.4>                     [pause] / [short pause]
    last card (CTA)                             [warm, friendly, smiling]
    start of every chunk after the first        [energetic, confident]   (separate calls keep the same energy)
Chunks split at sentence ends and never exceed --max-bytes UTF-8 (Fish free plan: 500 per call incl. tags).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from script_parse import CardSpec, Tok, parse_script, utterances  # noqa: E402

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:
        pass

ACCENT = {"italic", "accent", "mark", "alt", "outline", "pos"}
HOOK = "excited, confident"
QUESTION = "curious, rising intonation"
PUNCH = "very excited"
ANSWER = "confident"
CTA = "warm, friendly, smiling"
CHUNK_START = "energetic, confident"


def _tag(c: str) -> str:
    return f"[{c}]"


def _kind(u: list[Tok], cards: list[CardSpec]) -> str:
    last = u[-1].display.rstrip("»\"”)")
    if last.endswith("?"):
        return "question"
    if last.endswith("!") or cards[u[0].card].mode == "slam":
        return "punch"
    if len(u) <= 2 and any("neg" in t.style or "pos" in t.style for t in u):
        return "punch"  # «!!Нисколько!!» — the markup ate the "!"
    return "statement"


# Stress (ударение). Fish S2 reads "+" as «плюс» — never send it. In script.md mark stress for the voice with
# {display|spoken} and a "+" before the stressed vowel: {по косточкам|по к+осточкам}; frequent offenders live in
# assets/stress_ru.txt (one per line: косточкам=к+осточкам) and are fixed automatically.
# STRESS_STYLE decides how "+V" reaches the engine: "acute" = ко́сточкам (combining U+0301), "upper" = кОсточкам.
STRESS_STYLE = "acute"  # confirmed by ear 2026-10-20: Fish honours ко́сточкам (U+0301); кОсточкам did not work
VOWELS = "аеёиоуыэюяАЕЁИОУЫЭЮЯ"
_STRESS_DICT: dict[str, str] | None = None


def stress_dict() -> dict[str, str]:
    global _STRESS_DICT
    if _STRESS_DICT is None:
        _STRESS_DICT = {}
        f = Path(__file__).resolve().parent.parent / "assets" / "stress_ru.txt"
        if f.exists():
            for line in f.read_text(encoding="utf-8").splitlines():
                k, _, v = line.split("#")[0].partition("=")
                if k.strip() and v.strip():
                    _STRESS_DICT[k.strip().lower()] = v.strip()
    return _STRESS_DICT


def stressed(word: str, style: str | None = None) -> str:
    style = style or STRESS_STYLE
    m = re.match(r"^([«\"(]*)(.*?)([.,!?…:;»\")]*)$", word)
    pre, core, post = m.groups() if m else ("", word, "")
    if "+" not in core:
        fixed = stress_dict().get(core.lower())
        if fixed:
            core = fixed if core[:1].islower() else fixed[:1].upper() + fixed[1:]
    if "+" in core:
        if style == "acute":
            core = re.sub(rf"\+([{VOWELS}])", lambda q: q.group(1) + "́", core)
        else:
            core = re.sub(rf"\+([{VOWELS}])", lambda q: q.group(1).upper(), core)
        core = core.replace("+", "")
    return pre + core + post


def direct_sentences(cards: list[CardSpec], level: str = "rich") -> list[str]:
    """One performed string per utterance."""
    if level == "none":
        return [" ".join(stressed(w) for t in u for w in t.spoken) for u in utterances(cards)]
    utts = utterances(cards)
    last_card = cards[-1].i if cards else -1
    out: list[str] = []
    prev_kind = None
    for ui, u in enumerate(utts):
        kind = _kind(u, cards)
        head: list[str] = []
        if not u[0].cues:
            if ui == 0:
                head = [HOOK]
            elif u[0].card == last_card and len(cards) > 2:
                head = [CTA] if ui == 0 or utts[ui - 1][0].card != last_card else []
            elif kind == "question":
                head = [QUESTION]
            elif prev_kind == "question":
                head = ["short pause", PUNCH if kind == "punch" else ANSWER]
            elif kind == "punch":
                head = [PUNCH]
        parts = [_tag(h) for h in head]
        prev_style: tuple = ()
        for t in u:
            parts += [_tag(c) for c in t.cues]
            st = tuple(t.style)
            if st and st != prev_style and not t.cues:
                if "strike" in st:
                    parts.append(_tag("dismissive"))
                elif ((ACCENT & set(st)) or "neg" in st) and not (kind == "punch" and len(u) <= 2):
                    if level == "rich" or t.role == "punch":
                        parts.append(_tag("emphasis"))
            prev_style = st
            parts += [stressed(w) for w in t.spoken]
            parts += [_tag(c) for c in t.cues_after]
            if t.pause_after >= 0.45:
                parts.append(_tag("pause"))
            elif t.pause_after > 0:
                parts.append(_tag("short pause"))
        s = re.sub(r"(\[[^\]]+\])(\s*\1)+", r"\1", " ".join(parts))  # collapse repeated tags
        # a sentence split at a card edge has no end mark (markup like !!x!! ate it): give the voice one
        m = re.search(r"((?:\s*\[[^\]]+\])*)$", s)
        body, tail = s[: m.start()], m.group(1)
        if not re.search(r"[.!?…:;][»\"”)]*$", body):
            s = body + ("!" if kind == "punch" else ".") + tail
        out.append(s)
        prev_kind = kind
    return out


def chunk(sentences: list[str], max_bytes: int = 480) -> list[str]:
    def nb(x: str) -> int:
        return len(x.encode("utf-8"))
    chunks: list[str] = []
    cur = ""
    pieces: list[str] = []
    for s in sentences:  # an over-long sentence is split at commas
        if nb(s) <= max_bytes - 25:
            pieces.append(s)
            continue
        acc = ""
        for part in re.split(r"(?<=[,;:—])\s+", s):
            if acc and nb(acc + " " + part) > max_bytes - 25:
                pieces.append(acc)
                acc = part
            else:
                acc = f"{acc} {part}".strip()
        if acc:
            pieces.append(acc)
    for s in pieces:
        cand = f"{cur} {s}".strip()
        if cur and nb(cand) > max_bytes:
            chunks.append(cur)
            cur = s if s.startswith("[") else f"{_tag(CHUNK_START)} {s}"
        else:
            cur = cand
    if cur:
        chunks.append(cur)
    return chunks


def performed(src: str, level: str = "rich", max_bytes: int = 480) -> list[str]:
    return chunk(direct_sentences(parse_script(src), level), max_bytes)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("--level", default="rich", choices=["rich", "light", "none"])
    ap.add_argument("--max-bytes", type=int, default=480)
    ap.add_argument("--json", default=None)
    a = ap.parse_args()
    p = Path(a.src)
    if p.is_dir():
        p = p / "script.md"
    chunks = performed(p.read_text(encoding="utf-8"), a.level, a.max_bytes)
    for i, c in enumerate(chunks):
        print(f"--- chunk {i} ({len(c.encode('utf-8'))} bytes)\n{c}")
    if a.json:
        Path(a.json).write_text(json.dumps(chunks, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
