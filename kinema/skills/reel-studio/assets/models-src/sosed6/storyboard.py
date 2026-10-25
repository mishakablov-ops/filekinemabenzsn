"""Storyboard for sosed6 — «Сосед с шестого этажа», серия 1 (~1:45). PS1 lowpoly + VHS, VHS captions.
57 short shots (S6Shot / S6Insert in engine/src/three/sosedShots.tsx), every one anchored to the voice; in-shot event
times (`ev`) come from words.json (scenes anchored to a word start 0.07 s early). The camcorder night is one
continuous tape: `walk0` = seconds into the hero's walk at the shot's start, so the REC shots line up across cuts,
and the sounds put his steps on the floor at each step and the steps above exactly 3 s later.

    python -I storyboard.py   -> engine/public/projects/sosed6/spec.json
"""
import json
import re
from pathlib import Path

RS = Path(__file__).resolve().parents[3]
P = RS / "engine" / "public" / "projects" / "sosed6"
SRC = "projects/sosed6/sfx-src/"
LEAD = 0.07
BRAND = json.loads((RS / "engine" / "src" / "brand.json").read_text(encoding="utf-8"))
W = json.loads((P / "words.json").read_text(encoding="utf-8"))
WORDS = W["words"] if isinstance(W, dict) else W
norm = lambda s: re.sub(r"[^а-яёa-z0-9]", "", s.lower().replace("ё", "е"))


def phrase_t(ph, after=0.0):
    toks = [norm(p) for p in ph.split()]
    for i, x in enumerate(WORDS):
        if x["start"] < after - 1e-6:
            continue
        if all(i + k < len(WORDS) and norm(WORDS[i + k]["text"]) == toks[k] for k in range(len(toks))):
            return x["start"]
    raise SystemExit(f"phrase not found: {ph}")


wt = phrase_t
WALK_START_WORD = ("А на звуке", 0.0)  # he starts walking just before «А на звуке нас двое»
WALK_V, WALK_STEP = 0.27, 0.33
WALK_LEN = ((-0.2 - 0.45) ** 2 + (0.35 + 1.15) ** 2) ** 0.5  # WALK_A -> WALK_B in sosedShots.tsx

# (block, props, anchor phrase, events {name: phrase or (phrase, extra)}, transition)
S, I = "S6Shot", "S6Insert"
PLAN = [
    (S, {"shot": "ext_push"}, None, {}, None),
    (S, {"shot": "ext_win"}, "пятиэтажки", {}, "cut"),
    (S, {"shot": "bed_up"}, "Две недели", {}, "hardcut"),
    (S, {"shot": "chand_close"}, "надо мной", {}, "cut"),
    (S, {"shot": "stair_top"}, "Но выше", {}, "glitch"),
    (S, {"shot": "ceil_steps"}, "Сначала", {}, "hardcut"),
    (S, {"shot": "footprints"}, "Босиком", {}, "cut"),
    (S, {"shot": "crack_grow"}, "Потом скрежет", {}, "cut"),
    (S, {"shot": "wardrobe_shake"}, "Как будто", {}, "cut"),
    (S, {"shot": "door_dark"}, "А в ночь", {}, "hardcut"),
    (S, {"shot": "ceil_corner"}, "детский", {}, "cut"),
    (S, {"shot": "phone_dial"}, "Я позвонил", {}, "glitch"),
    (S, {"shot": "phone_talk"}, "Мне сказали", {}, "cut"),
    (S, {"shot": "roof"}, "над вами", {}, "hardcut"),
    (S, {"shot": "hatch_wide"}, "Люк на", {}, "glitch"),
    (S, {"shot": "hatch_1998"}, "1998", {}, "cut"),
    (S, {"shot": "climb"}, "Я поднялся", {}, "cut"),
    (S, {"shot": "weld_close"}, "Сварка", {}, "cut"),
    (S, {"shot": "scratches"}, "А на крышке", {}, "cut"),
    (S, {"shot": "dent"}, "Изнутри", {"bang": ("Изнутри", 0.05)}, "hardcut"),
    (S, {"shot": "setup_cam"}, "Тогда я", {"press": "камеру"}, "glitch"),
    (I, {"kind": "card", "lines": ["НОЧЬ 1", "03:12"]}, "Ночь первая", {}, "glitch"),
    (S, {"shot": "clock_312"}, "Три двенадцать", {"sec": ("Три двенадцать", 0)}, "hardcut"),
    (S, {"shot": "cam_wide"}, "Шаги начались", {}, "glitch"),
    (S, {"shot": "cam_walk1"}, "На видео", {}, "cut"),
    (I, {"kind": "tracks"}, "А на звуке", {}, "glitch"),
    (S, {"shot": "cam_walk2"}, "Шаги повторяют", {}, "glitch"),
    (I, {"kind": "tracks", "delay": True}, "С задержкой", {}, "glitch"),
    (S, {"shot": "cam_stop"}, "Я остановился", {}, "glitch"),
    (S, {"shot": "clock_tick"}, "Раз", {"sec": ("Раз", 0)}, "hardcut"),
    (S, {"shot": "face_up"}, "Два", {}, "hardcut"),
    (S, {"shot": "ceil_wait"}, "Три", {}, "hardcut"),
    (S, {"shot": "raise"}, "Я поднял", {}, "glitch"),
    (S, {"shot": "ceil_creak"}, "Над потолком", {"creak": "скрип"}, "hardcut"),
    (S, {"shot": "lower"}, "Я опустил", {"turn": ("А он", -0.2)}, "glitch"),
    (S, {"shot": "bulge_hold"}, "не опустил", {}, "hardcut"),
    (S, {"shot": "morning_bed"}, "Утром на", {}, "dip"),
    (S, {"shot": "palm_stain"}, "По форме", {}, "cut"),
    (S, {"shot": "lobby_walk"}, "Утром в", {}, "glitch"),
    (S, {"shot": "box_open"}, "почтовый", {}, "cut"),
    (S, {"shot": "num24"}, "Номер", {}, "hardcut"),
    (S, {"shot": "pan_numbers"}, "А квартир", {}, "cut"),
    (S, {"shot": "grab_photo"}, "Внутри", {"grab": "старая"}, "cut"),
    (S, {"shot": "photo_hold"}, "Мой дом", {}, "cut"),
    (I, {"kind": "count"}, "Я посчитал", {"six": "Шесть"}, "glitch"),
    (I, {"kind": "zoom"}, "В окне", {}, "cut"),
    (I, {"kind": "match"}, "Он похож", {}, "hardcut"),
    (S, {"shot": "photo_flip"}, "На обороте", {}, "glitch"),
    (I, {"kind": "back"}, "Не позволяйте", {"l2": "узнать", "end": ("исчез", 0.5)}, "cut"),
    (S, {"shot": "neighbor"}, "Соседка", {}, "glitch"),
    (S, {"shot": "neighbor_close"}, "и сказала", {"shut": "не живу"}, "cut"),
    (S, {"shot": "hall_dark"}, "Этой ночью", {}, "dip"),
    (S, {"shot": "feet_shadow"}, "спустились", {"feet": "двери"}, "hardcut"),
    (S, {"shot": "to_peephole"}, "Я посмотрел", {}, "cut"),
    (S, {"shot": "peep_view"}, "Лестница", {}, "hardcut"),
    (S, {"shot": "peep_up"}, "А наверху", {}, "cut"),
]
TAPE0 = 2 * 3600 + 47 * 60 + 31
walk_abs = phrase_t(*WALK_START_WORD) - 0.25

scenes, starts, prev = [], {}, 0.0
for block, props, anchor, events, trans in PLAN:
    t0 = 0.0 if anchor is None else phrase_t(anchor, prev)
    pic0 = max(0.0, t0 - (LEAD if anchor else 0))
    key = props.get("shot") or props.get("kind") + ("_d" if props.get("delay") else "")
    starts[key] = t0
    ev = {}
    for k, w in events.items():
        ph, extra = (w, 0.0) if isinstance(w, str) else w
        ev[k] = round(phrase_t(ph, t0) + extra - pic0, 3)
    if props.get("shot", "").startswith("cam_") or props.get("shot") in ("raise", "lower", "face_up"):
        ev["walk0"] = round(pic0 - walk_abs, 3)
    p = {**props, "ev": ev, "c0": TAPE0 + pic0}
    sc = {"id": f"{len(scenes):02d}_{key}", "at": 0 if anchor is None else "@" + anchor, "camera": "still", "bg": {"block": block, "props": p}}
    if trans:
        sc["transition"] = {"type": trans, "sfx": False, **({"dur": 0.25} if trans in ("glitch", "dip") else {})}
    scenes.append(sc)
    prev = t0

cta_t = phrase_t("Продолжение")
PROFILE = {"block": "TikTokProfile", "props": {"pinned": 0,
                                               "newTile": {"src": "projects/sosed6/part2_cover.jpg", "label": "ЧАСТЬ 2", "at": "@профиле"}}}
scenes.append({"id": "cta", "at": "@Продолжение", "camera": "still", "captions": False, "transition": {"type": "glitch", "dur": 0.3, "sfx": False},
               "bg": {"block": S, "props": {"shot": "cover", "ev": {}, "c0": TAPE0 + cta_t}}, "dim": 0.6, "dimAt": "@Продолжение",
               "layers": [{"block": "IPhone17", "pos": "full", "enter": "none", "at": "@Продолжение", "props": {
                   "enter": "flip", "flipAt": "@смотри", "flipDur": 0.8, "float": True, "shadow": 0, "screen": PROFILE,
                   "cam": [{"t": 0, "pos": [0, 2.3, 10.8], "target": [0, 2.25, 0], "fov": 30},
                           {"t": 1.4, "pos": [0.2, 2.32, 10.4], "target": [0, 2.25, 0], "fov": 30},
                           {"t": 2.3, "pos": [0, 1.62, 6.2], "target": [0, 1.62, 0], "fov": 30, "ease": "inOut"},
                           {"t": 6, "pos": [0, 1.6, 5.8], "target": [0, 1.6, 0], "fov": 30}]}}]})


def snd(at, name, vol, frm=0.0, dur=None, fade=None):
    d = {"at": round(at, 3), "id": name, "src": SRC + name + ".mp3", "volume": vol, "from": frm}
    if dur:
        d["dur"] = dur
    if fade:
        d["fade"] = fade
    return d


def lib(at, name, vol, peak=True):
    return {"at": at, "id": name, "volume": vol, "alignPeak": peak}


T = phrase_t
END = WORDS[-1]["end"] + 2.6
sfx = []
for a in range(0, int(END) + 1, 26):
    sfx.append(snd(float(a), "drone", 0.5, 0.3, 26.8, 0.8))
# his steps on the parquet and the steps above, 3 s later
n_steps = int(WALK_LEN / WALK_STEP) + 1
for j in range(n_steps):
    ts = walk_abs + j * WALK_STEP / WALK_V
    sfx.append(snd(ts, "floor_creak", 0.35, 0.0, 0.3, 0.1))
    sfx.append(snd(ts + 3.0, "steps_above", 0.95, 0.25, 0.4, 0.1))
sfx += [
    snd(0.0, "vhs_tape", 0.55, 0.4, 1.3, 0.3),
    snd(T("двигают") - 0.2, "furniture_drag_muf", 0.8, 0.0, 2.2, 0.5),
    snd(T("Сначала"), "steps_above", 0.85, 0.2, 1.6, 0.3),
    snd(T("Босиком"), "steps_above", 0.6, 2.0, 1.1, 0.3),
    snd(T("скрежет"), "furniture_drag_muf", 0.95, 0.5, 2.6, 0.5),
    snd(T("детский") - 0.1, "child_cry_muf", 0.6, 4.0, 2.4, 0.6),
    snd(T("Я позвонил") + 0.5, "phone_beeps", 0.45, 0.0, 1.9, 0.1),
    snd(T("Люк"), "lamp_buzz", 0.5, 0.1, 2.6, 0.4),
    snd(T("Я поднялся"), "breath_scared", 0.45, 0.4, 2.8, 0.5),
    snd(T("Я поднялся") + 0.2, "steps_concrete", 0.4, 0.5, 1.4, 0.3),
    lib("@Изнутри+0.06", "hit-metal", 0.85),
    snd(T("Изнутри") + 0.1, "floor_creak", 0.6, 10.4, 1.0, 0.4),
    snd(T("камеру") - 1.9, "vhs_tape", 0.7, 0.0, 2.6, 0.3),
    lib(T("Ночь первая"), "trans-glitch-cut", 0.5),
    snd(T("Три двенадцать"), "clock_tick", 0.6, 1.7, 1.3, 0.2),
    lib("@А на звуке", "trans-glitch-cut", 0.4),
    lib("@С задержкой", "trans-glitch-cut", 0.4),
    snd(T("Раз"), "clock_tick", 0.9, 1.74, 0.35, 0.1),
    snd(T("Два"), "clock_tick", 0.9, 2.72, 0.35, 0.1),
    snd(T("Три", T("Два")), "clock_tick", 0.9, 3.72, 0.35, 0.1),
    snd(T("скрип") - 0.3, "floor_creak", 0.95, 10.4, 1.3, 0.4),
    snd(T("не опустил") + 0.3, "heartbeat", 0.55, 0.45, 2.0, 0.4),
    snd(T("Утром в"), "steps_concrete", 0.5, 0.0, 1.8, 0.3),
    snd(T("почтовый") - 0.48, "mailbox", 0.8, 0.0, 1.7, 0.3),
    snd(T("старая"), "pages", 0.6, 0.3, 0.7, 0.2),
    lib("@Шесть", "hit-sub", 0.7),
    lib(T("меня", T("похож")), "dread-rise", 0.55),
    lib("@похож", "sting-dark", 0.5),
    snd(T("На обороте") + 0.2, "pages", 0.55, 2.55, 0.8, 0.2),
    snd(T("не живу") + 0.15, "door_lock", 0.75, 0.0, 1.0, 0.2),
    snd(T("Этой ночью"), "clock_tick", 0.35, 5.7, 1.6, 0.4),
    snd(T("спустились") - 0.3, "steps_concrete", 0.6, 2.0, 1.4, 0.3),
    snd(T("глазок") - 0.2, "door_lock", 0.45, 0.55, 0.4, 0.1),
    lib("@пятого", "dread-rise", 0.6),
    snd(T("горел"), "lamp_buzz", 0.6, 0.1, 2.0, 0.3),
    snd(cta_t - 0.35, "scream_long", 0.7, 1.6, 1.0, 0.3),
    snd(cta_t - 0.12, "stinger", 0.95, 0.0, 2.4, 0.6),
    lib("@смотри+0.5", "pk-pop-ui-menu", 0.5, False),
    lib("@профиле", "pk-notify-notification-sfx-1", 0.8),
]
for i, c in enumerate([0, 1, 2, 3, 4, 5]):
    sfx.append(lib(f"@посчитал+{0.07 + i * 0.28:.2f}", "pk-click-ui-button", 0.35, False))

spec = {
    "id": "sosed6", "mode": "explainer", "style": "dusk", "fps": 60,
    "voice": {"src": "projects/sosed6/voice.wav", "words": "projects/sosed6/words.json"},
    "music": {"src": "music/dark-cinematic.m4a", "volume": 0.07, "duck": 0.5},
    "tail": 2.6,
    "autoSfx": False,
    "captions": {"mode": "vhs", "pos": "top", "uppercase": True},
    "sfx": sfx,
    "scenes": scenes,
}
(P / "spec.json").write_text(json.dumps(spec, ensure_ascii=False, indent=1), encoding="utf-8")
print("scenes", len(scenes), "sfx", len(sfx), "end", round(END, 2), "walk starts", round(walk_abs, 2))
