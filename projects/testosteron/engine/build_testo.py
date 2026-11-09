"""«Каждые 10 секунд у тебя становится больше тестостерона» — vertical PIXCINE short (1080×1920), 09.11.2026.
Trend format «every 10 seconds …»: narration sections sit on a 10 s grid (voice_grid.py), a HUD shows the timer and a
testosterone bar; every mark = level-up (bass drop + white flash + shake) and the hero sprite grows a stage:
geroy → geroy_s (stubble) → geroy_t4 (big) → geroy_t6/_t6p (beard, pigeons) → geroy_t8 (glowing eyes) → geroy_t8h (beanie).
Arsen Markaryan is a parody nod only: a bearded pixel «mentor» (char `arsen`) and a chat message; no likeness, no voice.
Voice: MiniMax Russian_ReliableMan ×1.35 (as «Эскалатор»); the CTA is the narration's last section (same voice)."""
import json

from common_sh import Cut, Ep, H, W, Words, cam, copy_voice, narration, save_loc

KID = "testosteron"
w = Words(KID)
C = w.cards
SEC = {int(r["id"]): r for r in json.loads((narration(KID) / "sections.json").read_text(encoding="utf-8"))}
S = {k: v["start"] for k, v in SEC.items()}
cs = lambda i, d=0.07: round(C[i]["start"] - d, 3)  # noqa: E731
A = w.at
END_STORY = round(S[10] - 0.05, 3)
END = round(w.duration + 0.9, 3)

# ----------------------------------------------------------------- locations (own ids: zlye/bunker sets bake their own event times)
ROOM = {"id": "tt_room", "interior": True, "tod": "interior_day",
        "props": [{"t": "room", "p": [0, 0], "w": 4.4, "d": 4.6, "h": 2.7, "wall": "wallpaper", "wallOpts": {"color": "#2a3042"}, "floor": "parquet", "floorOpts": {}, "ceiling": False},
                  {"t": "bed", "modern": True, "p": [-1.2, -1.0], "sheet": "#2a3a5a"}, {"t": "nightstand", "p": [-0.3, -1.85], "lamp": True},
                  {"t": "desk", "p": [1.25, -1.9], "on": True}, {"t": "windowModern", "p": [0.55, -2.28], "y": 1.55, "w": 1.3, "h": 1.1, "morning": True},
                  {"t": "poster", "p": [-2.17, 0.6], "y": 1.6, "r": 90, "v": 0}, {"t": "poster", "p": [2.17, -0.4], "y": 1.55, "r": -90, "v": 1},
                  {"t": "shelf", "p": [1.9, 1.2], "r": -90, "s": 0.8}, {"t": "carpet", "p": [0.2, 0.2], "w": 1.8, "len": 2.2, "color": "#3a3448"},
                  {"t": "crate", "p": [1.7, 0.2]},
                  {"t": "shaft", "p": [0.55, -1.9], "top": 2.1, "w": 1.1, "h": 3, "tilt": -28, "color": "#ffe0b0", "opacity": 0.14}],
        "lights": [{"type": "spot", "p": [0.55, 2.2, -2.0], "target": [-0.2, 0.5, -0.4], "i": 7, "d": 9, "angle": 50, "color": "#ffe0b0", "shadow": True},
                   {"type": "point", "p": [1.0, 2.3, 1.5], "i": 1.2, "d": 7, "color": "#ffd8b0"}],
        "particles": [{"kind": "dust", "n": 120, "box": [-0.6, 0.4, -2.1, 1.4, 2.4, -0.2]}], "fog": 0.015, "hemi": ["#c8c0b8", "#3a2a20", 0.6]}
NIGHT = {**ROOM, "id": "tt_room_night", "tod": "interior",
         "props": [p if p["t"] != "windowModern" else {**p, "morning": False} for p in ROOM["props"] if p["t"] != "shaft"],
         "lights": [{"type": "point", "p": [-0.3, 0.9, -1.8], "i": 2.2, "d": 4, "color": "#ffb870"}, {"type": "point", "p": [0.6, 1.8, -2.0], "i": 1.2, "d": 6, "color": "#6a88ff"}],
         "hemi": ["#4a5a8a", "#0a0a12", 0.35], "fog": 0.02}
CAFE = {"id": "tt_cafe", "interior": True, "tod": "interior_day",
        "props": [{"t": "room", "p": [0, 0], "w": 6.0, "d": 4.6, "h": 3.0, "wall": "tiles", "wallOpts": {"color": "#d8cfc0"}, "floor": "floor_tiles", "floorOpts": {"a": "#6a5040", "b": "#4a3a30"}, "ceiling": False},
                  {"t": "counter", "p": [0.8, -1.4], "w": 3.0, "color": "#5a3a26"}, {"t": "coffeeMachine", "p": [1.6, -1.55], "y": 1.06},
                  {"t": "menuBoard", "p": [-1.4, -2.25], "y": 2.0, "w": 1.7, "h": 1.05, "items": [["ЛАТТЕ", "250"], ["ПРОТЕИН", "300"], ["СЫРЫЕ ЯЙЦА", "90"]], "hl": 0, "title": "МЕНЮ"},
                  {"t": "table", "p": [-1.8, 1.0]}, {"t": "stool", "p": [-1.8, 1.7]}, {"t": "bush", "p": [2.6, 1.6], "s": 0.7},
                  {"t": "windowModern", "p": [-2.98, 0.2], "y": 1.6, "r": 90, "w": 1.6, "h": 1.2, "morning": True},
                  {"t": "bulb", "p": [-0.6, 0.0], "y": 3.0, "len": 0.7, "i": 4, "d": 7}, {"t": "bulb", "p": [1.4, -0.6], "y": 3.0, "len": 0.7, "i": 4, "d": 7}],
        "fog": 0.012, "hemi": ["#d8c8b0", "#4a3828", 0.75]}
KITCHEN = {"id": "tt_kitchen", "interior": True, "tod": "interior_day",
           "props": [{"t": "room", "p": [0, 0], "w": 4.2, "d": 3.6, "h": 2.7, "wall": "tiles", "wallOpts": {"color": "#c8d4c0"}, "floor": "lino", "floorOpts": {"color": "#6a5a4a"}, "ceiling": False},
                     {"t": "sink", "p": [-0.2, -1.45]}, {"t": "block", "p": [1.4, -1.4], "size": [0.75, 1.95, 0.7], "tex": "white", "color": "#e8ecec"},
                     {"t": "table", "p": [0.6, 0.2]}, {"t": "stool", "p": [1.2, 0.6]},
                     {"t": "windowModern", "p": [-1.6, -1.78], "y": 1.6, "w": 0.9, "h": 0.9, "morning": True},
                     {"t": "bulb", "p": [0, 0], "y": 2.7, "len": 0.4, "i": 4, "d": 7}],
           "fog": 0.012, "hemi": ["#d8d0c0", "#3a3028", 0.75]}
BATH = {"id": "tt_bath", "interior": True, "tod": "interior_day",
        "props": [{"t": "room", "p": [0, 0], "w": 3.4, "d": 3.0, "h": 2.6, "wall": "tiles", "wallOpts": {"color": "#b8d0d8"}, "floor": "floor_tiles", "floorOpts": {"a": "#d8dcdc", "b": "#a8b0b4"}, "ceiling": False},
                  {"t": "sink", "p": [0.0, -1.2]}, {"t": "block", "p": [0.0, -1.47], "y": 1.15, "size": [0.8, 0.7, 0.04], "tex": "metal", "color": "#c8dce8"},
                  {"t": "block", "p": [1.2, -1.2], "size": [0.6, 0.9, 0.5], "tex": "white", "color": "#e8ecec"},
                  {"t": "lightPt", "p": [0, -0.6], "y": 2.4, "i": 3.5, "d": 7, "color": "#f4f8ff"}],
        "fog": 0.01, "hemi": ["#d0dce4", "#3a4044", 0.8]}
STREET = {"id": "tt_street", "tod": "day", "fog": 0.012, "ground": {"tex": "paving", "size": [200, 200]},
          "props": [{"t": "road", "p": [0, 0], "w": 7, "len": 90, "zebraZ": 0}, {"t": "trafficLight", "p": [-4.1, 1.9], "state": "green"},
                    {"t": "streetLamp", "p": [4.4, -8], "r": 180}, {"t": "streetLamp", "p": [-4.4, -16]}, {"t": "streetLamp", "p": [4.4, 8], "r": 180},
                    *[{"t": "building", "p": [x, z], "r": (90 if x < 0 else -90), "w": 11, "d": 9, "floors": f, "seed": i, "day": True, "color": c}
                      for i, (x, z, f, c) in enumerate([(-12, -18, 7, "#8a7e72"), (-12, -5, 5, "#7a8a8e"), (-12, 8, 6, "#9a7a62"), (-12, 21, 7, "#7e7a8a"),
                                                        (12, -20, 6, "#9a8a72"), (12, -7, 8, "#7a7e86"), (12, 6, 5, "#8a6e60"), (12, 19, 6, "#888070")])],
                    {"t": "bush", "p": [-5.5, -2]}, {"t": "bush", "p": [5.6, 3]}, {"t": "bench", "p": [-6.2, 5], "r": 90}],
          "particles": [{"kind": "motes", "n": 80, "box": [-6, 0.3, -6, 6, 4, 6]}]}
YARD = {"id": "tt_yard", "tod": "night", "fog": 0.018, "ground": {"tex": "asphalt", "size": [300, 300]},
        "props": [{"t": "road", "p": [0, 0], "w": 8, "len": 160},
                  *[{"t": "streetLamp", "p": [s * 4.6, z], "r": (180 if s > 0 else 0)} for s, z in [(1, -6), (-1, -14), (1, -22), (-1, 6), (1, 14)]],
                  *[{"t": "building", "p": [x, z], "r": (90 if x < 0 else -90), "w": 12, "d": 10, "floors": f, "seed": 20 + i, "lit": 0.45, "color": "#5a5660"}
                    for i, (x, z, f) in enumerate([(-13, -8, 9), (-13, 7, 6), (-13, 22, 8), (13, -10, 7), (13, 6, 10), (13, 20, 6), (-13, -48, 12), (13, -50, 9)])]],
        "particles": [{"kind": "motes", "n": 60, "box": [-6, 0.3, -6, 6, 4, 6]}]}
ELEV = {"id": "tt_elev", "interior": True, "tod": "interior", "props": [{"t": "elevator", "p": [0, 0], "allAt": 999, "i": 3.5}], "fog": 0.01, "hemi": ["#b8bcc4", "#3a3a40", 0.6]}
COACH = {"id": "tt_coach", "interior": True, "tod": "interior",
         "props": [{"t": "room", "p": [0, 0], "w": 5.0, "d": 4.0, "h": 3.0, "wall": "plaster", "wallOpts": {"color": "#2a2a30"}, "floor": "parquet", "floorOpts": {}, "ceiling": False},
                   {"t": "screenBoard", "p": [0.0, -1.96], "y": 1.9, "w": 2.4, "h": 1.0, "title": "МАРАФОН «БРАТ»", "rows": ["ДЕНЬ 1: ХОЛОДНЫЙ ДУШ", "ДЕНЬ 2: БОРОДА", "ДЕНЬ 3: ЭТО БАЗА"], "hl": 2},
                   {"t": "sandbags", "p": [-1.8, -1.4]}, {"t": "shelf", "p": [2.2, -0.6], "r": -90, "s": 0.8},
                   {"t": "bulb", "p": [0, 0.2], "y": 3.0, "len": 0.5, "i": 5, "d": 8},
                   {"t": "lightPt", "p": [1.2, 1.0], "y": 2.0, "i": 2.2, "d": 6, "color": "#ff9a4a"}],
         "fog": 0.025, "hemi": ["#8a7a6a", "#120e0c", 0.45]}
for L in (ROOM, NIGHT, CAFE, KITCHEN, BATH, STREET, YARD, ELEV, COACH):
    save_loc(L)

# ----------------------------------------------------------------- episode
ep = Ep("shorts", "testo", fps=30, w=W, h=H)
cut = Cut(ep, w)


def actor(s, id, char, at, face=0, act="idle", eyes=None, mouth=None):
    a = s.actor(id, char, at=at, face=face)
    a.act(0, act)
    if eyes or mouth:
        a.expr(0, eyes, mouth)
    return a


def med(s, x, z, y=1.25, d=2.6, side=0.35, fov=40, ap=6, focus="hero"):
    """medium shot of an actor at (x, z) facing the camera (+z), slow push-in (portrait zoom of common_sh.cam)"""
    cam(s, [(0, [x + side, y + 0.25, z + d], [x, y, z], fov), (-1, [x + side * 0.6, y + 0.22, z + d * 0.88], [x, y, z], fov - 2)], focus=focus, ap=ap)


def cu(s, x, z, y=1.45, d=1.5, fov=32, ap=16, focus="hero"):
    """close-up like zlye #42: head and shoulders"""
    d, fov = max(d, 1.35), max(fov, 30)
    cam(s, [(0, [x + 0.08, y + 0.14, z + d], [x, y, z], fov), (-1, [x + 0.04, y + 0.12, z + d * 0.86], [x, y, z], fov - 2)], focus=focus, ap=ap)


# levels: (time, filled segments of 9, multiplier text)
LEVELS = [(0.0, 0, "×1")] + [(S[k], k - 1, f"×{2 ** (k - 1)}") for k in range(2, 9)] + [(S[9], 9, "MAX")]
t_heels = A("пятки", after=S[9])
LEVELS.append((t_heels, 1, "×1"))
cut.card("meter", 0.25, END_STORY, levels=[{"t": round(t, 3), "n": n, "mult": m} for t, n, m in LEVELS], max=9, start=0.0, y=0.025)


def level_up(k):
    t = S[k]
    cut.card("black", t - 0.02, t + 0.16, color="#ffffff", fi=0.02, fo=0.12)
    cut.sfx(t, "usr-bass-drop-low-tail" if k % 2 else "usr-cinema-boom-low-tail-184", -4)


for k in range(2, 10):
    level_up(k)

# ---- 1. hook: in the room, the hero wakes up, the timer starts
s = cut.shot("tt_room", cs(1))
h = actor(s, "hero", "geroy", (-0.2, 0.2), face=10, act="idle", eyes="normal")
h.act(A("тестостерона") - s.t0, "fist"); h.expr(A("тестостерона") - s.t0, "angry", "grit")
cam(s, [(0, [0.6, 1.7, 3.4], [-0.2, 1.1, 0.0], 48), (-1, [0.3, 1.55, 2.4], [-0.2, 1.2, 0.1], 42)], focus="hero", ap=6, zoom=False)
cut.sfx(A("тестостерона"), "usr-cinema-boom-low-tail-184", -5)

s = cut.shot("tt_room", S[2] - 0.02)
h = actor(s, "hero", "geroy", (-0.2, 0.2), face=0, act="arms_crossed", eyes="normal", mouth="smile")
cu(s, -0.2, 0.2)
cut.card("label", cs(1) + 0.05, S[2] - 0.1, text="ЭКСПЕРИМЕНТ", sub="1:30 · 9 УРОВНЕЙ", x=0.06, y=0.15)
cut.sfx(cs(1) + 0.1, "usr-clock-steady-bright-late", -14)

# ---- 2. 0:10 — voice drops an octave
s = cut.shot("tt_room", cs(3))
h = actor(s, "hero", "geroy", (-0.2, 0.2), face=0, act="talk", eyes="normal", mouth="closed")
cu(s, -0.2, 0.2, fov=30)
s.fxk(S[2] - s.t0, "shake", d=0.5, v=0.04)
cut.card("compare", A("октаву") - 0.1, cs(3), left={"title": "ГОЛОС", "value": "ЛЯ"}, right={"title": "ТЕПЕРЬ", "value": "ЛЯ −8"}, y=0.17)

s = cut.shot("tt_cafe", cs(4))
b = actor(s, "bar", "barista", (1.0, -0.95), face=0, act="idle", eyes="normal", mouth="smile")
b.act(A("стойке") - s.t0 - 0.3, "stand_guard"); b.expr(A("стойке") - s.t0 - 0.3, "wide", "closed")
actor(s, "hero", "geroy", (0.4, 0.7), face=180, act="talk")
cam(s, [(0, [-0.8, 1.6, 2.6], [0.8, 1.2, -0.6], 44), (-1, [-0.6, 1.55, 2.2], [0.9, 1.25, -0.8], 40)], focus="bar", ap=5, zoom=False)
cut.sfx(A("стойке") - 0.3, "usr-boxing-bell-mid-snap", -10)

s = cut.shot("tt_cafe", S[3] - 0.02)
h = actor(s, "hero", "geroy", (0.4, 0.5), face=-20, act="phone", eyes="normal")
h.hold(0, B="phone")
med(s, 0.4, 0.5, fov=38)
cut.card("notif", A("Сири") - 0.05, S[3] - 0.1, app="SIRI", text="Да, сэр. Слушаю, сэр.", icon="#2a2a40", glyph="◉", y=0.16)
cut.sfx(A("Сири"), "usr-notify-two-tone-mid-snap", -8)

# ---- 3. 0:20 — brows, mom's pickle jar
s = cut.shot("tt_room", cs(6))
h = actor(s, "hero", "geroy", (-0.2, 0.2), face=0, act="idle", eyes="angry", mouth="closed")
cu(s, -0.2, 0.2, y=1.5, d=1.05, fov=28)
cut.card("stat", A("гуще") - 0.05, cs(6), text="+300%", label="БРОВИ", y=0.17, size=140)

s = cut.shot("tt_kitchen", cs(7))
m = actor(s, "mama", "mama", (-0.5, -0.4), face=30, act="idle", eyes="normal", mouth="smile")
m.hold(0, B="jar")
hh = actor(s, "hero", "geroy", (0.6, -0.1), face=-60, act="arms_crossed", eyes="angry")
t_pop = A("сама", after=S[3])
m.expr(t_pop - s.t0, "wide", "o"); m.act(t_pop - s.t0, "jolt")
cam(s, [(0, [0.3, 1.75, 3.8], [0.05, 1.15, -0.3], 50), (-1, [0.2, 1.7, 3.3], [0.05, 1.15, -0.3], 47)], focus="mama", ap=4, zoom=False)
cut.card("bubble", t_pop - 0.02, cs(7), text="*ЧПОК*", y=0.2, side="left")
cut.sfx(t_pop, "usr-cork-pop-mid-snap", -4)

s = cut.shot("tt_kitchen", S[4] - 0.02)
hh = actor(s, "hero", "geroy", (0.6, -0.1), face=0, act="arms_crossed", eyes="angry")
cu(s, 0.6, -0.1)
cut.card("stat", A("уважения") - 0.05, S[4] - 0.1, text="+100", label="УВАЖЕНИЕ", y=0.17, size=140, color="#5ad05a")

# ---- 4. 0:30 — stubble, the razor quits, polite mosquitoes
s = cut.shot("tt_bath", cs(9))
h = actor(s, "hero", "geroy_s", (0.0, -0.55), face=0, act="idle", eyes="wide")
cu(s, 0.0, -0.55, y=1.45, d=1.2)
cut.card("label", A("щетина") - 0.1, cs(9), text="ЩЕТИНА: ЗА 1 СЕК", x=0.06, y=0.15)

s = cut.shot("tt_bath", cs(10))
h = actor(s, "hero", "geroy_s", (0.0, -0.55), face=0, act="phone", eyes="normal")
h.hold(0, B="razor")
med(s, 0.0, -0.55, fov=40, d=2.0)
cut.card("notif", A("заявление") - 0.05, cs(10), app="БРИТВА", text="Заявление по собственному. Не ищите.", icon="#3a5a8a", glyph="✎", y=0.16)
cut.sfx(A("заявление"), "usr-paper-rip-bright-snap", -8)

s = cut.shot("tt_room_night", S[5] - 0.02)
h = actor(s, "hero", "geroy_s", (-0.2, 0.2), face=0, act="arms_crossed", eyes="normal", mouth="smile")
cu(s, -0.2, 0.2, fov=30)
cut.card("bubble", A("извиняются") - 0.05, S[5] - 0.1, who="КОМАР", text="Простите, ошибся дверью", y=0.17, side="left")
cut.sfx(A("кусают"), "usr-slide-whistle-mid-swell", -12)

# ---- 5. 0:40 — mewing, bread, phonk, the elevator
s = cut.shot("tt_street", cs(12), tod="day")
h = actor(s, "hero", "geroy_t4", (-4.0, 2.0), face=0, act="idle", eyes="angry", mouth="closed")
h.walk(0.2, (-4.0, 4.0), dur=3.0)
cam(s, [(0, [-3.4, 1.6, 6.8], [-4.0, 1.3, 2.4], 42), (-1, [-3.6, 1.6, 7.4], [-4.0, 1.3, 4.0], 40)], focus="hero", ap=5, zoom=False)
cut.card("label", A("мьюинг") - 0.1, cs(12), text="МЬЮИНГ: ВКЛ", sub="ПРИЧИНА: НЕТ", x=0.06, y=0.15)

s = cut.shot("tt_room", cs(13))
h = actor(s, "hero", "geroy_t4", (-0.2, 0.2), face=0, act="idle", eyes="angry", mouth="grit")
cu(s, -0.2, 0.2, y=1.48)
cut.card("stat", A("хлеб") - 0.1, cs(13), text="ОСТРАЯ", label="ЧЕЛЮСТЬ · 1 ШТ.", y=0.17, size=130)
cut.sfx(A("резать"), "usr-bone-crunch-mid-swell", -8)

s = cut.shot("tt_street", cs(14), tod="day")
h = actor(s, "hero", "geroy_t4", (-4.0, 4.0), face=0, act="fist", eyes="angry", mouth="grit")
cam(s, [(0, [-3.2, 0.7, 6.4], [-4.0, 1.5, 4.0], 46), (-1, [-3.0, 0.6, 5.8], [-4.0, 1.6, 4.0], 44)], focus="hero", ap=4, zoom=False)
s.fxk(A("фонк") - s.t0, "shake", d=1.4, v=0.03)
cut.card("notif", A("фонк") - 0.1, cs(14), app="МУЗЫКА", text="PHONK включён автоматически", icon="#7a2a9a", glyph="♪", y=0.16)

s = cut.shot("tt_elev", S[6] - 0.02)
h = actor(s, "hero", "geroy_t4", (-0.2, 0.0), face=30, act="arms_crossed", eyes="angry")
cam(s, [(0, [0.0, 1.6, 2.4], [0.0, 1.3, -0.1], 42), (-1, [0.1, 1.55, 2.0], [0.0, 1.3, 0.0], 40)], focus="hero", ap=6)
s.fxk(0.2, "shake", d=2.0, v=0.02)
cut.card("label", A("Лифт") - 0.1, S[6] - 0.1, text="ЛИФТ: СКОРОСТЬ ×3", sub="ПРИЧИНА: СТРАХ", x=0.06, y=0.15)
cut.sfx(A("Боится"), "usr-voice-bruh", -10)

# ---- 6. 0:50 — the mentor writes (parody), «Это база»
s = cut.shot("tt_coach", cs(16))
a_ = actor(s, "arsen", "arsen", (0.0, -0.6), face=0, act="phone", eyes="angry", mouth="closed")
a_.hold(0, B="phone")
cam(s, [(0, [0.5, 1.7, 2.6], [0.0, 1.35, -0.6], 44), (-1, [0.35, 1.65, 2.2], [0.0, 1.38, -0.6], 40)], focus="arsen", ap=6, zoom=False)
cut.card("label", cs(15) + 0.4, cs(16), text="НАСТАВНИК", sub="ПАРОДИЯ", x=0.06, y=0.26, border="#ff4a2a")
cut.sfx(cs(15) + 0.4, "usr-suspense-sting", -12)

s = cut.shot("tt_room_night", S[7] - 0.02)
h = actor(s, "hero", "geroy_t4", (-0.2, 0.2), face=0, act="phone", eyes="normal")
h.hold(0, B="phone")
med(s, -0.2, 0.2, fov=40)
tp = cs(16)
t_me = A("отвечаешь") + 0.3
cut.card("bubble", tp + 0.1, S[7] - 0.05, who="АРСЕН М. ✓", whoColor="#ff6a4a", text="Брат, учить тебя больше нечему.", y=0.15, side="left")
cut.card("bubble", t_me, S[7] - 0.05, who="ТЫ", whoColor="#7ad0ff", text="Это база.", y=0.27, side="right", bg="#d8f0ff")
cut.sfx(tp + 0.15, "usr-notify-ding-mid-snap", -8)
cut.sfx(A("отвечаешь") + 0.3, "usr-cinema-boom-low-tail-184", -6)

# ---- 7. 1:00 — the beard, two pigeons paying rent, the shadow
s = cut.shot("tt_street", cs(19), tod="day")
h = actor(s, "hero", "geroy_t6", (-4.0, 3.0), face=0, act="arms_crossed", eyes="angry")
cu(s, -4.0, 3.0, y=1.5, d=1.3)
cut.card("stat", A("борода") - 0.05, cs(19), text="БОРОДА", label="+40 СМ ЗА 1 СЕК", y=0.17, size=130)

s = cut.shot("tt_street", cs(21), tod="day")
h = actor(s, "hero", "geroy_t6p", (-4.0, 3.0), face=0, act="idle", eyes="normal", mouth="closed")
cu(s, -4.0, 3.0, y=1.55, d=1.4, fov=34)
cut.card("stat", A("Платят") - 0.05, cs(21), text="+500 ₽", label="АРЕНДА ОТ ГОЛУБЕЙ / МЕС", y=0.17, size=130, color="#5ad05a")
cut.sfx(A("голубя"), "usr-cartoon-bloop-mid-snap", -10)
cut.sfx(A("Платят"), "usr-cash-register-bright-snap", -8)

s = cut.shot("tt_street", S[8] - 0.02, tod="day")
h = actor(s, "hero", "geroy_t6p", (-4.0, 3.0), face=0, act="arms_crossed", eyes="angry")
cam(s, [(0, [-3.0, 3.0, 9.0], [-4.0, 1.4, 3.0], 46), (-1, [-1.0, 9.0, 16.0], [-4.0, 1.0, 1.0], 52)], ap=2, zoom=False)
cut.card("label", A("соседний") - 0.1, S[8] - 0.1, text="СОСЕДНИЙ РАЙОН", sub="ПОГОДА: ТЕНЬ ОТ БОРОДЫ", x=0.06, y=0.15)

# ---- 8. 1:10 — sneeze → car alarms, the alarm clock, glowing eyes
s = cut.shot("tt_yard", cs(23), tod="night")
h = actor(s, "hero", "geroy_t8", (-3.6, 2.0), face=60, act="idle", eyes="closed", mouth="o")
t_sneeze = A("чихнул")
h.act(t_sneeze - s.t0, "jolt"); h.expr(t_sneeze - s.t0 + 0.2, "angry", "grit")
for i, (x, z) in enumerate([(1.8, -4), (-1.8, -9), (1.8, -14), (-1.8, 4)]):
    s.kw.setdefault("extra", []).append({"t": "car", "p": [x, z], "color": ["#c83a2a", "#3a6ab8", "#e0b020", "#d8d8d8"][i], "lights": True})
cam(s, [(0, [-6.0, 2.0, 7.0], [-1.0, 1.0, -4.0], 50), (-1, [-6.4, 2.4, 8.0], [-1.0, 1.0, -4.0], 52)], ap=2, zoom=False)
s.fxk(t_sneeze - s.t0, "shake", d=0.8, v=0.06)
cut.sfx(t_sneeze, "usr-cartoon-splat-mid-snap", -8)
cut.sfx(A("сигнализации") - 0.2, "siren-far", -10, dur=2.5)

s = cut.shot("tt_room_night", cs(24))
h = actor(s, "hero", "geroy_t8", (-1.2, -0.45), face=15, act="sit", eyes="angry")
h.act(0, "sit", seat=0.62)
cam(s, [(0, [-0.2, 1.55, 2.9], [-1.15, 1.0, -0.45], 50), (-1, [-0.35, 1.5, 2.5], [-1.15, 1.0, -0.45], 47)], focus="hero", ap=6, zoom=False)
cut.card("notif", A("Будильник") - 0.05, cs(24), app="БУДИЛЬНИК 07:00", text="Выключен. Простите, пожалуйста.", icon="#c83a3a", glyph="⏰", y=0.16)
cut.sfx(A("Будильник"), "usr-digital-beeps-bright-late", -14, dur=0.6)

s = cut.shot("tt_room_night", S[9] - 0.02)
h = actor(s, "hero", "geroy_t8", (-0.2, 0.2), face=0, act="arms_crossed", eyes="angry")
cu(s, -0.2, 0.2, y=1.5, d=1.05, fov=28)
cut.card("stat", A("гигачад") - 0.05, S[9] - 0.1, text="ГИГАЧАД", label="УРОВЕНЬ 8 ИЗ 8", y=0.17, size=130)
cut.sfx(A("Глаза"), "reveal-glow", -8)
cut.sfx(A("гигачад"), "usr-cinema-boom-low-tail-184", -3)

# ---- 9. 1:20 — mom calls; testosterone drops to the heels; the beanie
s = cut.shot("tt_room", cs(26))
h = actor(s, "hero", "geroy_t8", (-0.2, 0.2), face=0, act="phone", eyes="angry")
h.hold(0, B="phone")
med(s, -0.2, 0.2, fov=40)
cut.card("notif", A("мама", after=S[9]) - 0.1, cs(27), app="ВХОДЯЩИЙ ВЫЗОВ", text="МАМА ❤", icon="#3a8a4a", glyph="✆", y=0.16)
cut.sfx(A("Звонит"), "usr-notify-two-tone-mid-swell", -6)

s = cut.shot("tt_room", cs(27))
h = actor(s, "hero", "geroy_t8", (-0.2, 0.2), face=0, act="phone_ear", eyes="wide", mouth="o")
h.hold(0, B="phone")
cu(s, -0.2, 0.2, fov=30)
cut.card("bubble", cs(26) + 0.05, cs(27), who="МАМА", text="Сынок, ты шапку надел?", y=0.25, side="left")

s = cut.shot("tt_room", cs(28))
h = actor(s, "hero", "geroy_t8", (-0.2, 0.2), face=0, act="cower", eyes="wide", mouth="o")
med(s, -0.2, 0.2, fov=42)
cut.sfx(t_heels - 0.2, "usr-slide-whistle-bright-swell", -6)

s = cut.shot("tt_room", END_STORY)
h0 = actor(s, "hero0", "geroy_t8", (-0.2, 0.2), face=90, act="idle", eyes="normal", mouth="closed")
h1 = actor(s, "hero", "geroy_t8h", (-0.2, 0.2), face=0, act="idle", eyes="normal", mouth="closed")
t_hat = A("шапку", after=S[9] + 4.0)
h0.walk(0.1, (1.6, 0.4), dur=1.2); h0.show(t_hat - s.t0, False)
h1.show(0, False); h1.show(t_hat - s.t0, True)
med(s, -0.2, 0.2, fov=44, side=0.6, focus=None, ap=2)
cut.sfx(t_hat, "usr-voice-bruh", -8)

# ---- 10. CTA: same narrator, the channel profile rises; bio + link light up on «шапку»
t0 = ep.t
s = ep.shot("tt_room", round(END - t0, 3))
a = s.actor("hero", "geroy_t8h", at=(-0.2, 0.2), face=0)
a.act(0, "wave"); a.expr(0, "happy", "smile")
cam(s, [(0, [-0.2, 1.5, 2.6], [-0.2, 1.2, 0.2], 40), (-1, [-0.2, 1.5, 2.2], [-0.2, 1.2, 0.2], 38)], focus="hero", ap=8, zoom=False)
t_hl = A("шапку", after=S[10])
cut.card("black", t0, END, color="rgba(0,0,0,0.55)", fi=0.25, fo=0.01)
cut.card("profile", t0, END, hlAt=t_hl)
ep.sfx(t_hl, "pk-notify-notification-sfx-1", -6)

# ----------------------------------------------------------------- sound
ep.voice(0, copy_voice(KID, "testo"), gain=0)
w.subs(ep, 0.3)
ep.music(0, S[5] - 0.3, "shorts/t_trap", gain=-22, fi=0.3, fo=0.4)
ep.music(S[5] + 2.5, S[7], "shorts/t_trap", gain=-15, fi=0.2, fo=0.6, offset=8.0)   # «фонк» kicks in louder
ep.music(S[7], S[9] + 1.0, "shorts/t_trap", gain=-21, fi=0.4, fo=0.4, offset=20.0)
ep.music(S[9] + 1.0, END, "shorts/z_comedy", gain=-22, fi=0.6, fo=1.2)
ep.amb(cs(3), S[3], "shorts/cafe", gain=-28)
ep.amb(cs(11), S[6] - 2.0, "shorts/street_day", gain=-28)
ep.amb(S[7], S[8], "shorts/street_day", gain=-28)
ep.amb(S[8], cs(23), "city-hum", gain=-30, fo=0.4)
ep.save()
