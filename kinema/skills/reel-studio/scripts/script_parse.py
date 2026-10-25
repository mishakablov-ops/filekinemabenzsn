"""Parse a Reel Studio voiceover script (script.md) into caption cards + spoken text.

FORMAT (one caption card per line):
    %slam %lower  Это // *бесплатно*        <- optional directives, lead // punch
    Бесит какое-то *приложение?*
    Это умеют {11|одиннадцать} бесплатных [скиллов]
    <0.4>                                     <- explicit pause (seconds), own line or inline
    (blank line)                              <- paragraph pause (0.45 s)
    # comment lines are ignored

Inline markup (mirrors engine/src/core/markup.ts):
    *x* serif italic   [x] accent   ==x== highlight box   ~~x~~ strike   ^x^ 2nd accent
    __x__ outline      !!x!! red     ++x++ green           /  forced line break
    {display|spoken}   caption shows `display`, voice says `spoken`
    ((cue))            voice direction before the next word, e.g. ((excited)) ((rising intonation)) ((pause)) ((whispering)):
                       never shown or spoken; becomes an inline [tag] for Fish / ElevenLabs v3 / Inworld / Gemini
                       (voice_direct.py also adds automatic cues: hook, questions, beat before punchlines, accents, CTA)
Directives: %editorial %sub %slam %stack %karaoke %none  and  %top %upper %middle %lower %bottom
"""
from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field

# console: always UTF-8 (Windows defaults to cp1251)
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:
        pass

MODES = {"editorial": "editorial", "edit": "editorial", "sub": "subtitle", "subtitle": "subtitle", "slam": "slam",
         "stack": "stack", "karaoke": "karaoke", "none": "none"}
POSES = {"top", "upper", "middle", "lower", "bottom"}
STYLE_RE = [
    (re.compile(r"==(.+?)=="), "mark"),
    (re.compile(r"~~(.+?)~~"), "strike"),
    (re.compile(r"__(.+?)__"), "outline"),
    (re.compile(r"!!(.+?)!!"), "neg"),
    (re.compile(r"\+\+(.+?)\+\+"), "pos"),
    (re.compile(r"\*(.+?)\*"), "italic"),
    (re.compile(r"\[(.+?)\]"), "accent"),
    (re.compile(r"\^(.+?)\^"), "alt"),
]


@dataclass
class Tok:
    display: str
    spoken: list[str]
    style: list[str]
    role: str  # lead | punch
    line: int
    card: int
    pause_after: float = 0.0
    cues: list[str] = field(default_factory=list)  # voice direction placed before this word
    cues_after: list[str] = field(default_factory=list)  # direction written after the last word of a line, e.g. ((pause))


@dataclass
class CardSpec:
    i: int
    mode: str | None
    pos: str | None
    toks: list[Tok] = field(default_factory=list)


def _split_spoken(s: str) -> list[str]:
    return [w for w in re.split(r"\s+", s.strip()) if w]


def parse_line(text: str, card_i: int, role: str, line0: int = 0) -> list[Tok]:
    # protect {display|spoken} groups: turn into single placeholder tokens
    groups: list[tuple[str, str]] = []

    def grp(m):
        groups.append((m.group(1), m.group(2)))
        return f"\u0004{len(groups) - 1}\u0005"
    s = re.sub(r"\{([^|}]*)\|([^}]*)\}", grp, text)
    # protect ((cue)) voice directions
    cues_found: list[str] = []

    def cue_grp(m):
        cues_found.append(m.group(1).strip())
        return f" {len(cues_found) - 1} "
    s = re.sub(r"\(\(([^()]+)\)\)", cue_grp, s)
    for rx, st in STYLE_RE:
        s = rx.sub(lambda m, st=st: f"\u0001{st}\u0002{m.group(1)}\u0003", s)
    toks: list[Tok] = []
    stack: list[str] = []
    line = line0
    buf = ""
    pending_pause = 0.0
    pending_cues: list[str] = []

    def flush():
        nonlocal buf
        w = buf.strip()
        buf = ""
        if not w:
            return
        m = re.fullmatch(r"(.*?)\u0004(\d+)\u0005(.*)", w)
        if m:
            disp, spk = groups[int(m.group(2))]
            disp = m.group(1) + disp + m.group(3)
            spoken = _split_spoken(spk)
            # punctuation glued to the group ({…|…}: or «{…|…}») belongs to the voice too — it shapes the intonation
            if spoken and re.fullmatch(r"[.,!?…:;»\"”)]*", m.group(3)):
                spoken[-1] += m.group(3)
            if spoken and re.fullmatch(r"[«\"“(]*", m.group(1)):
                spoken[0] = m.group(1) + spoken[0]
        else:
            disp = w
            spoken = [w]
        toks.append(Tok(disp, spoken, list(stack), role, line, card_i, cues=list(pending_cues)))
        pending_cues.clear()

    i = 0
    while i < len(s):
        c = s[i]
        if c == "\u0001":
            flush()
            j = s.index("\u0002", i)
            stack.append(s[i + 1:j])
            i = j + 1
            continue
        if c == "\u0003":
            flush()
            if stack:
                stack.pop()
            i += 1
            continue
        if c == "":
            flush()
            j = s.index("", i)
            pending_cues.append(cues_found[int(s[i + 1:j])])
            i = j + 1
            continue
        if c == "<":
            m = re.match(r"<(\d+(?:\.\d+)?)>", s[i:])
            if m:
                flush()
                if toks:
                    toks[-1].pause_after += float(m.group(1))
                else:
                    pending_pause += float(m.group(1))
                i += len(m.group(0))
                continue
        if c == "/" and s[i + 1:i + 2] != "/":
            flush()
            line += 1
            i += 1
            continue
        if c.isspace():
            flush()
            i += 1
            continue
        buf += c
        i += 1
    flush()
    if pending_cues and toks:  # a cue at the very end of a line: it follows the last word
        toks[-1].cues_after += pending_cues
    # a group placeholder may have been split by spaces inside display text: re-join
    return toks


def parse_script(src: str) -> list[CardSpec]:
    cards: list[CardSpec] = []
    para_pause = 0.0
    for raw in src.splitlines():
        line = raw.strip()
        if line.startswith("#"):
            continue
        if not line:
            if cards and cards[-1].toks:
                cards[-1].toks[-1].pause_after = max(cards[-1].toks[-1].pause_after, 0.45)
            continue
        m = re.fullmatch(r"<(\d+(?:\.\d+)?)>", line)
        if m:
            if cards and cards[-1].toks:
                cards[-1].toks[-1].pause_after += float(m.group(1))
            continue
        mode = pos = None
        while True:
            m = re.match(r"%(\w+)\s*", line)
            if not m:
                break
            key = m.group(1).lower()
            if key in MODES:
                mode = MODES[key]
            elif key in POSES:
                pos = key
            else:
                break
            line = line[m.end():]
        ci = len(cards)
        card = CardSpec(ci, mode, pos)
        if "//" in line:
            lead, punch = line.split("//", 1)
            card.toks += parse_line(lead, ci, "lead")
            card.toks += parse_line(punch, ci, "punch")
        else:
            card.toks += parse_line(line, ci, "punch")
        if card.toks:
            cards.append(card)
    return cards


SENT_END = re.compile(r"[.!?…]+[»\"”)]*$")


def utterances(cards: list[CardSpec]) -> list[list[Tok]]:
    """Group tokens into utterances (synthesised separately). Break at sentence ends and explicit pauses."""
    utts: list[list[Tok]] = []
    cur: list[Tok] = []
    for ci, c in enumerate(cards):
        for t in c.toks:
            cur.append(t)
            if SENT_END.search(t.display) or t.pause_after > 0:
                utts.append(cur)
                cur = []
        # a card that ends without punctuation (markup like !!Нисколько!! eats the "!") before a capitalised card
        nxt = cards[ci + 1].toks[0].display.lstrip("«\"(") if ci + 1 < len(cards) and cards[ci + 1].toks else ""
        if cur and nxt[:1].isupper():
            utts.append(cur)
            cur = []
    if cur:
        utts.append(cur)
    return utts


def spoken_text(toks: list[Tok]) -> str:
    out = []
    for t in toks:
        out.extend(t.spoken)
    s = " ".join(out)
    s = s.replace(" ", " ")
    return s


def plain_text(cards: list[CardSpec]) -> str:
    return " ".join(spoken_text(c.toks) for c in cards)


if __name__ == "__main__":
    src = open(sys.argv[1], encoding="utf-8").read()
    cs = parse_script(src)
    for c in cs:
        print(c.i, c.mode, c.pos, [(t.display, t.spoken, t.style, t.role, t.line, t.pause_after, t.cues) for t in c.toks])
    print("UTTERANCES:")
    for u in utterances(cs):
        print(" -", spoken_text(u))
    json.dump([], sys.stdout)
