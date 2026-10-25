"""Storyboard for podezd (part 1): a Khrushchyovka horror told by Dima, PS1 + VHS look, ~1:57.
Every shot is a PzShot (engine/src/three/podezdShots.tsx). Scene starts are anchored to the voice; in-shot event times
(`ev`) are computed here from words.json so the action lands on the word (scenes anchored to a word start 0.07 s early).
Sounds: the user's horror pack in projects/podezd/sfx-src (+ a few library UI cues for the CTA).

    python -I storyboard.py   -> engine/public/projects/podezd/spec.json
"""
import json
import re
from pathlib import Path

RS = Path(__file__).resolve().parents[3]
P = RS / "engine" / "public" / "projects" / "podezd"
SRC = "projects/podezd/sfx-src/"
LEAD = 0.07
BRAND = json.loads((RS / "engine" / "src" / "brand.json").read_text(encoding="utf-8"))
W = json.loads((P / "words.json").read_text(encoding="utf-8"))
WORDS = W["words"] if isinstance(W, dict) else W
norm = lambda s: re.sub(r"[^а-яёa-z0-9]", "", s.lower().replace("ё", "е"))


def wt(word, after=0.0):
    """start time of the first `word` at or after `after`"""
    for x in WORDS:
        if x["start"] >= after - 1e-6 and norm(x["text"]) == norm(word):
            return x["start"]
    raise SystemExit(f"word not found: {word} after {after}")


def phrase_t(ph, after=0.0):
    toks = [norm(p) for p in ph.split()]
    for i, x in enumerate(WORDS):
        if x["start"] < after - 1e-6:
            continue
        if all(i + k < len(WORDS) and norm(WORDS[i + k]["text"]) == toks[k] for k in range(len(toks))):
            return x["start"]
    raise SystemExit(f"phrase not found: {ph}")


# (shot, anchor phrase, events {name: word}, transition)
SHOTS = [
    ("hook", None, {}, None),
    ("moan", "И воют", {}, "hardcut"),
    ("block", "Меня зовут", {}, "glitch"),
    ("upgap", "Лифта нет", {}, "cut"),
    ("landing", "зелёные стены", {}, "cut"),
    ("boothWindow", "Внизу вахта", {}, "cut"),
    ("journal", "Она знает", {"close": "закрывает"}, "cut"),
    ("serega", "Первым был", {}, "glitch"),
    ("ask", "Я спросил", {"up": "Он"}, "cut"),
    ("graffiti", "смотри вниз", {}, "hardcut"),
    ("crane", "Через день", {}, "cut"),
    ("listen", "Они не спят", {"listen": "слушают"}, "cut"),
    ("pipe", "Ночью в", {"k1": "стук.", "k3": "Снизу", "k4": "вверх."}, "glitch"),
    ("upfast", "Этаж за", {}, "hardcut"),
    ("breath", "А лампочки", {}, "cut"),
    ("wake", "В ночь на", {"scream": "крик."}, "dip"),
    ("bed", "Кричала", {}, "cut"),
    ("railing", "Я вышел", {"turn": "Все"}, "cut"),
    ("point", "И молча", {"point": "показали"}, "hardcut"),
    ("boothEnter", "Вахта открыта", {"tea": "Чай"}, "glitch"),
    ("journalFloor", "Журнал на", {"name": "моя"}, "cut"),
    ("door", "А за шкафом", {}, "cut"),
    ("call", "Я позвонил", {"beeps": "Гудки."}, "cut"),
    ("cry", "А потом в", {}, "cut"),
    ("torch", "Я включил", {"on": "включил"}, "cut"),
    ("nosig", "Связь пропала", {}, "glitch"),
    ("count", "Я считал", {"six": "Шесть."}, "cut"),
    ("scratches", "На стенах", {}, "cut"),
    ("doorway", "Внизу кто-то", {}, "cut"),
    ("him", "Он сидел", {"tall": "высокий."}, "cut"),
    ("face", "И закрывал", {}, "cut"),
    ("scarf", "Рядом лежал", {}, "cut"),
    ("step", "Я сделал", {"stop": "оборвался."}, "cut"),
    ("lower", "И он начал", {}, "hardcut"),
]
TAPE0 = 1 * 3600 + 12 * 60 + 9  # the tape counter starts at 1:12:09

scenes, starts, prev = [], {}, 0.0
for shot, anchor, events, trans in SHOTS:
    t0 = 0.0 if anchor is None else phrase_t(anchor, prev)
    starts[shot] = t0
    pic0 = max(0.0, t0 - (LEAD if anchor else 0))
    ev = {k: round(wt(w, t0) - pic0, 3) for k, w in events.items()}
    if shot == "pipe":
        ev["k2"] = round(ev["k1"] + 0.5, 3)
    if shot == "torch":
        ev["on"] = round(ev["on"] + 0.2, 3)
    sc = {"id": shot, "at": 0 if anchor is None else "@" + anchor, "camera": "still",
          "bg": {"block": "PzShot", "props": {"shot": shot, "ev": ev, "c0": TAPE0 + pic0}}}
    if trans:
        sc["transition"] = {"type": trans, "sfx": False, **({"dur": 0.3} if trans in ("glitch", "dip") else {})}
    scenes.append(sc)
    prev = t0

# CTA: the last shot keeps running dimmed; the phone rises, flips to the profile, part 2 lands in the grid
cta_t = phrase_t("Продолжение")
PROFILE = {"block": "TikTokProfile", "props": {"pinned": 0,
                                               "newTile": {"src": "projects/podezd/part2_cover.jpg", "label": "ЧАСТЬ 2", "at": "@профиле"}}}
scenes.append({"id": "cta", "at": "@Продолжение", "camera": "still", "captions": False, "transition": {"type": "glitch", "dur": 0.35, "sfx": False},
               "bg": {"block": "PzShot", "props": {"shot": "lower", "ev": {}, "c0": TAPE0 + cta_t}}, "dim": 0.6, "dimAt": "@Продолжение",
               "layers": [{"block": "IPhone17", "pos": "full", "enter": "none", "at": "@Продолжение", "props": {
                   "enter": "flip", "flipAt": "@смотри", "flipDur": 0.9, "float": True, "shadow": 0, "screen": PROFILE,
                   "cam": [{"t": 0, "pos": [0, 2.3, 10.8], "target": [0, 2.25, 0], "fov": 30},
                           {"t": 1.6, "pos": [0.2, 2.32, 10.4], "target": [0, 2.25, 0], "fov": 30},
                           {"t": 2.6, "pos": [0, 1.62, 6.2], "target": [0, 1.62, 0], "fov": 30, "ease": "inOut"},
                           {"t": 6, "pos": [0, 1.6, 5.8], "target": [0, 1.6, 0], "fov": 30}]}}]})


def snd(at, name, vol, frm=0.0, dur=None, fade=None):
    d = {"at": round(at, 3) if isinstance(at, float) else at, "id": name, "src": SRC + name + ".mp3", "volume": vol, "from": frm}
    if dur:
        d["dur"] = dur
    if fade:
        d["fade"] = fade
    return d


def lib(at, name, vol, peak=True):
    return {"at": at, "id": name, "volume": vol, "alignPeak": peak}


T = lambda w, after=0.0: wt(w, after)
END = WORDS[-1]["end"] + 2.6
sfx = []
# beds: a drone the whole way, stairwell room tone under the stairwell shots
for a in range(0, int(END) + 1, 26):
    sfx.append(snd(float(a), "drone", 0.55, 0.3, 26.8, 0.8))
for a in (0.0, 14.0, 28.0, 42.0, 54.0, 68.0):
    sfx.append(snd(a, "stairwell_tone", 0.9, 0.0, 14.2, 0.6))
s = starts
sfx += [
    snd(0.0, "lamp_buzz", 0.45, 0.1, 2.8, 0.4),
    snd(0.4, "people_moan", 0.45, 4.6, 2.6, 0.5),
    snd(T("воют.") - 0.35, "people_moan", 0.9, 20.2, 3.0, 0.8),
    snd(s["upgap"] + 0.2, "steps_concrete", 0.35, 0.0, 1.9, 0.4),
    snd(T("лампочки") - 0.2, "lamp_buzz", 0.55, 0.15, 2.6, 0.4),
    snd(T("закрывает") - 0.1, "pages", 0.7, 2.55, 0.9, 0.2),
    snd(s["serega"] + 0.3, "people_moan", 0.4, 10.0, 3.6, 0.8),
    snd(s["ask"] + 0.15, "steps_concrete", 0.4, 0.0, 0.45, 0.1),
    lib("@смотри", "sting-dark", 0.5),
    snd(s["crane"], "people_moan", 0.55, 31.0, 3.3, 0.6),
    snd(T("слушают."), "drip", 0.35),
    snd(T("стук.") - 0.16, "pipe_knock", 0.8, 0.0, 0.6, 0.15),
    snd(T("стук.") + 0.34, "pipe_knock", 0.6, 0.0, 0.6, 0.15),
    snd(T("Снизу") - 0.16, "pipe_knock", 0.75, 2.62, 0.6, 0.15),
    snd(T("вверх.") - 0.16, "pipe_knock", 0.7, 3.17, 0.6, 0.15),
    snd(s["upfast"] + 0.25, "pipe_knock", 0.5, 5.25, 0.5, 0.15),
    snd(s["upfast"] + 0.7, "pipe_knock", 0.3, 5.25, 0.5, 0.15),
    snd(T("лампочки", s["breath"]), "lamp_buzz", 0.5, 0.1, 2.8, 0.5),
    snd(T("дышит.") - 0.6, "breath_scared", 0.45, 0.4, 2.6, 0.6),
    snd(T("крик.") - 0.27, "woman_scream", 0.85, 0.0, 2.4, 0.3),
    snd(s["bed"] + 0.1, "breath_scared", 0.4, 1.4, 3.6, 0.6),
    snd(T("Снизу.", s["bed"]) - 0.25, "woman_scream", 0.38, 0.0, 2.3, 0.6),
    snd(T("Долго."), "woman_scream", 0.24, 0.1, 2.4, 1.0),
    snd(s["railing"], "doors_open_close", 0.55, 0.0, 1.1, 0.2),
    snd(s["railing"] + 0.7, "steps_concrete", 0.35, 0.5, 1.0, 0.2),
    snd(T("Все") - 0.1, "bones_crack", 0.7, 0.5, 0.7, 0.2),
    lib("@Все", "hit-sub", 0.6),
    snd(T("показали") + 0.1, "drip", 0.3),
    snd(s["boothEnter"] - 0.25, "door_creak", 0.7, 1.3, 1.9, 0.4),
    snd(s["journalFloor"] + 0.25, "pages", 0.55, 0.3, 1.1, 0.2),
    lib("@моя", "hit-sub", 0.55),
    snd(s["door"] + 0.5, "door_creak", 0.55, 5.0, 2.6, 0.6),
    snd(s["call"] + 0.35, "phone_beeps", 0.25, 30.0, 0.4, 0.05),
    snd(T("Гудки.") - 0.98, "phone_beeps", 0.6, 0.0, 2.3, 0.1),
    snd(T("заплакал.") - 0.75, "child_cry", 0.5, 13.15, 2.4, 0.4),
    lib("@включил", "pk-click-ui-button", 0.45),
    snd(T("вниз.", s["torch"]), "steps_concrete", 0.45, 1.0, 3.2, 0.5),
    snd(T("вниз.", s["torch"]) + 1.3, "drip", 0.3),
    lib("@пролёте", "pk-result-failure", 0.3),
    snd(s["count"], "steps_concrete", 0.4, 4.3, 3.0, 0.5),
    lib("@Шесть", "hit-sub", 0.5),
    snd(s["scratches"] + 0.7, "furniture_drag", 0.18, 0.0, 0.8, 0.3),
    snd(T("плакал.") - 0.4, "child_cry", 0.6, 4.0, 3.3, 0.6),
    snd(s["him"] - 0.1, "child_cry", 0.5, 7.8, 4.6, 0.5),
    snd(s["him"] + 0.4, "breath_scared", 0.35, 4.1, 4.0, 0.6),
    snd(s["face"] - 0.05, "child_cry", 0.45, 13.2, 2.3, 0.4),
    snd(s["scarf"] - 0.05, "child_cry", 0.4, 15.0, 2.6, 0.4),
    snd(s["step"] + 0.3, "steps_concrete", 0.45, 0.0, 0.42, 0.1),
    snd(s["step"], "child_cry", 0.45, 18.0, round(T("оборвался.") + 0.25 - s["step"], 2), 0.03),
    snd(s["lower"] + 0.1, "bones_crack", 0.8, 3.2, 2.8, 0.3),
    snd(s["lower"], "breath_scared", 0.35, 6.3, 2.0, 0.4),
    snd(cta_t - 0.12, "stinger", 0.95, 0.0, 2.4, 0.6),
    lib("@смотри+0.5", "pk-pop-ui-menu", 0.5, False),
    lib("@профиле", "pk-notify-notification-sfx-1", 0.8),
]

spec = {
    "id": "podezd", "mode": "explainer", "style": "dusk", "fps": 60,
    "voice": {"src": "projects/podezd/voice.wav", "words": "projects/podezd/words.json"},
    "music": {"src": "music/dark-cinematic.m4a", "volume": 0.08, "duck": 0.5},
    "tail": 2.6,
    "autoSfx": False,
    "captions": {"mode": "editorial", "pos": "top", "uppercase": True},
    "sfx": sfx,
    "scenes": scenes,
}
(P / "spec.json").write_text(json.dumps(spec, ensure_ascii=False, indent=1), encoding="utf-8")
print("scenes", len(scenes), "sfx", len(sfx), "end", round(END, 2))
for sc in scenes[:3]:
    print(sc["id"], sc["at"], sc["bg"]["props"].get("ev"))
