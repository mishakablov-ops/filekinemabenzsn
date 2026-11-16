"""«Как познакомиться с девушкой» — vertical PIXCINE short (1080×1920), 16.11.2026.
mike: «сделай мне ролик в пиксельном стиле, как правильно знакомиться с девушками, видео юморное».
Kind humour: we laugh at Витёк (the channel's hero of «Как жить, если ты тупой»), never at the girl. No swearing, no music.
Витёк tries five «methods from the guides» on Лиза: Wi-Fi pick-up line (cafe), mystery in dark glasses (night street),
push-ups at the bus stop, texting «Ты ела?», flowers from the city-hall flowerbed (date with a policeman). Then on a park
bench Лиза recognises him as the guy who licked the lamp post, and they talk for two hours. Rule: just say «привет».
Hook-teaser = the policeman moment, ◀◀ rewind. Ending: soft «переходи в профиль» + support card theme «love»."""
import json
import math

from common_sh import K, Cut, Ep, H, W, Words, cam, copy_voice, narration, save_loc, LOCS

KID = "znakomstva"
w = Words(KID)
C = w.cards
SEC = {int(r["id"]): r for r in json.loads((narration(KID) / "sections.json").read_text(encoding="utf-8"))}
S = {k: v["start"] for k, v in SEC.items()}
A = w.at
END_STORY = round(S[9] - 0.05, 3)
END = round(w.duration + 2.5, 3)        # like/subscribe block after the voice CTA
V, VG, L = "geroy", "vitek_g", "liza"    # Витёк, Витёк in dark glasses, Лиза


# ----------------------------------------------------------------- sets
def street(id, night=False, tod="day", extra_props=()):
    """main street along z (as testosteron v2): 8 m road, 3 m sidewalks, facades at x=±12 with shop signs, lamps,
    trees, parked cars, a bus stop on the right at z=-19, a kiosk, pigeons"""
    P = [{"t": "road", "p": [0, 0], "w": 8, "len": 160, "zebraZ": 0}]
    cols = ["#8a7e72", "#7a8a8e", "#9a7a62", "#7e7a8a", "#9a8a72", "#7a7e86", "#8a6e60", "#888070", "#6e7a72"]
    for side in (-1, 1):
        for i, z in enumerate([-50, -38, -26, -14, -2, 10, 22, 34, 46]):
            b = {"t": "building", "p": [side * 12, z], "r": 90 if side < 0 else -90, "w": 11, "d": 9, "floors": 5 + (i * 3 + (side > 0) * 2) % 6,
                 "seed": 20 + i + (side > 0) * 10, "color": cols[(i + (side > 0) * 4) % len(cols)]}
            if night:
                b["lit"] = 0.45
            else:
                b["day"] = True
            P.append(b)
    for side, z, txt, bg in [(-1, -26, "АПТЕКА", "#2a8a4a"), (-1, -14, "ПРОДУКТЫ 24", "#2a4a8a"), (-1, -2, "ШАУРМА", "#c84a2a"), (-1, 10, "ЦВЕТЫ", "#8a3a6a"),
                             (-1, 22, "КИНО", "#5a2a6a"), (1, -26, "ФИТНЕС «БЫК»", "#c83a3a"), (1, -14, "ЛОМБАРД", "#8a7a2a"), (1, -4, "КАФЕ «ВАЙ-ФАЙ»", "#3a2a1a"),
                             (1, 10, "БАРБЕРШОП", "#1a1a1e"), (1, 22, "САЛОН СВЯЗИ", "#3a6aa8")]:
        P.append({"t": "shopSign", "p": [side * 7.42, z], "y": 3.3, "r": 90 if side < 0 else -90, "w": min(5.2, 0.55 * len(txt) + 0.8), "h": 0.8,
                  "text": txt, "bg": bg, "glow": 1.1 if night else 0.2})
    for i, z in enumerate([-42, -30, -18, -6, 6, 18, 30, 42]):
        side = 1 if i % 2 else -1
        P.append({"t": "streetLamp", "p": [side * 4.5, z], "r": 0 if side < 0 else 180, "on": night})
    for side in (-1, 1):
        for z in (-24, -12, 12, 24, 36):
            P.append({"t": "tree", "p": [side * 6.3, z + side * 1.5], "s": 0.75})
    for x, z, r, c in [(-3.2, -32, 0, "#3a6ab8"), (-3.2, -22, 0, "#d8d8d8"), (-3.2, 14, 0, "#2a2a30"), (-3.2, 26, 0, "#8a2a2a"),
                       (3.2, -30, 180, "#4a8a5a"), (3.2, -9, 180, "#c8c8c0"), (3.2, 16, 180, "#5a3a7a"), (3.2, 30, 180, "#e0b020")]:
        P.append({"t": "car", "p": [x, z], "r": r, "color": c})
    P += [{"t": "block", "p": [6.4, -19], "y": 2.45, "size": [1.3, 0.08, 3.2], "tex": "metal", "color": "#4a5a6a", "solid": False},   # bus stop roof
          {"t": "block", "p": [6.95, -19], "size": [0.06, 2.45, 3.2], "color": "#6a8aa0", "solid": False},
          {"t": "bench", "p": [6.5, -19], "r": -90, "w": 2.2},
          {"t": "shopSign", "p": [5.75, -19], "y": 2.75, "r": -90, "w": 1.6, "h": 0.4, "text": "ОСТАНОВКА", "bg": "#2a5aa8", "glow": 1.0 if night else 0.2},
          {"t": "poster", "p": [6.9, -18.0], "y": 1.4, "r": -90, "v": 2},
          {"t": "block", "p": [-6.0, 16], "size": [1.6, 2.4, 1.6], "tex": "metal", "color": "#5a7a5a"},
          {"t": "shopSign", "p": [-5.18, 16], "y": 2.0, "r": 90, "w": 1.4, "h": 0.5, "text": "ПЕЧАТЬ", "bg": "#2a6a3a", "glow": 0.9 if night else 0.2},
          {"t": "bench", "p": [-6.6, 9], "r": 90},
          {"t": "block", "p": [-6.9, 3.2], "size": [0.5, 0.8, 0.5], "color": "#2a4a3a"},
          {"t": "block", "p": [6.9, 4.5], "size": [0.5, 0.8, 0.5], "color": "#2a4a3a"},
          {"t": "bush", "p": [-6.8, -8], "s": 0.8}, {"t": "bush", "p": [6.8, 7], "s": 0.8},
          {"t": "crows", "p": [-5.2, 12], "n": 5, "spread": 2.2, "color": "#7a808c"},
          {"t": "building", "p": [0, -72], "w": 40, "d": 10, "floors": 12, "seed": 40, **({"lit": 0.45} if night else {"day": True}), "color": "#7a7680"},
          {"t": "building", "p": [0, 72], "r": 180, "w": 40, "d": 10, "floors": 9, "seed": 41, **({"lit": 0.45} if night else {"day": True}), "color": "#867a6e"},
          *extra_props]
    save_loc({"id": id, "tod": tod, "fog": 0.018 if night else 0.010, "ground": {"tex": "paving", "size": [240, 240]}, "props": P,
              "particles": [{"kind": "motes", "n": 90, "box": [-7, 0.3, -10, 7, 5, 10]}]})


street("zn_day", tod="day", extra_props=[{"t": "crows", "p": [6.5, -14.4], "n": 7, "spread": 1.2, "color": "#7a808c"}])
street("zn_night", night=True, tod="night")

# cafe «Вай-фай»: Лиза's table by the window, a free table on the right, a laptop guy, the barista
T1, T2, T3 = (-1.6, 0.9), (1.7, 1.3), (-0.1, -0.2)
save_loc({"id": "zn_cafe", "interior": True, "tod": "interior_day",
          "props": [{"t": "room", "p": [0, 0], "w": 6.4, "d": 5.0, "h": 3.0, "wall": "tiles", "wallOpts": {"color": "#d8c8b8"}, "floor": "floor_tiles",
                     "floorOpts": {"a": "#6a5040", "b": "#4a3a30"}, "ceiling": False},
                    {"t": "counter", "p": [1.2, -1.75], "w": 3.0, "color": "#5a3a26"},
                    {"t": "coffeeMachine", "p": [2.0, -1.9], "y": 1.06},
                    {"t": "menuBoard", "p": [-1.2, -2.45], "y": 2.0, "w": 1.9, "h": 1.1, "items": [["ЛАТТЕ", "250"], ["КАПУЧИНО", "220"], ["ПАРОЛЬ WI-FI", "У БАРИСТЫ"]],
                     "hl": 2, "title": "МЕНЮ"},
                    {"t": "shopSign", "p": [1.2, -2.45], "y": 2.35, "w": 1.6, "h": 0.42, "text": "Wi-Fi FREE", "bg": "#3a6aa8", "glow": 0.7},
                    *[{"t": "table", "p": list(p)} for p in (T1, T2, T3)],
                    {"t": "stool", "p": [T1[0], T1[1] + 0.6]}, {"t": "stool", "p": [T1[0], T1[1] - 0.6]},
                    {"t": "stool", "p": [T2[0], T2[1] + 0.6]}, {"t": "stool", "p": [T3[0] + 0.6, T3[1]]},
                    {"t": "block", "p": [T1[0] + 0.12, T1[1] + 0.12], "y": 0.76, "size": [0.08, 0.1, 0.08], "color": "#f0ece4", "solid": False},     # her cup
                    {"t": "block", "p": [T3[0], T3[1]], "y": 0.76, "size": [0.34, 0.02, 0.24], "color": "#2a2c34", "solid": False},                 # laptop base
                    {"t": "block", "p": [T3[0] - 0.12, T3[1]], "y": 0.77, "size": [0.02, 0.22, 0.24], "emissive": "#5ac8ff", "ei": 0.6, "solid": False},
                    {"t": "bush", "p": [2.8, 2.0], "s": 0.7}, {"t": "bush", "p": [-2.9, -2.0], "s": 0.6},
                    {"t": "windowModern", "p": [-3.18, 0.6], "y": 1.6, "r": 90, "w": 1.8, "h": 1.3, "morning": True},
                    {"t": "poster", "p": [3.18, 0.4], "y": 1.6, "r": -90, "v": 1},
                    {"t": "bulb", "p": [-1.2, 0.6], "y": 3.0, "len": 0.7, "i": 4, "d": 7}, {"t": "bulb", "p": [1.4, -0.4], "y": 3.0, "len": 0.7, "i": 4, "d": 7}],
          "fog": 0.012, "hemi": ["#d8c8b0", "#4a3828", 0.75]})

# Витёк's room at night (texting): the testosteron room, lamp only
room = json.loads((LOCS / "tt_room.json").read_text(encoding="utf-8"))
room.update({"id": "zn_room", "tod": "interior", "hemi": ["#5a5a78", "#1a1420", 0.35], "particles": []})
room["props"] = [p for p in room["props"] if p["t"] not in ("shaft", "windowModern")] + [
    {"t": "windowModern", "p": [0.55, -2.28], "y": 1.55, "w": 1.3, "h": 1.1, "morning": False},
    {"t": "lightPt", "p": [-0.3, -1.7], "y": 1.0, "i": 2.5, "d": 4, "color": "#ffc888"}]
room["lights"] = [{"type": "point", "p": [-0.4, 1.2, -1.6], "i": 2.0, "d": 5, "color": "#ffc080"},
                  {"type": "point", "p": [1.0, 2.3, 1.5], "i": 0.5, "d": 7, "color": "#8aa0ff"}]
save_loc(room)

# square at the city hall: the flowerbed Витёк robs, a police car, pigeons, passers-by
BED = (0.0, -6.0)
FLOWER_COLS = ["#e8304a", "#ffd23a", "#ff8ab0", "#f4f0e6", "#c83aa8"]


def flowers(cx, cz, w, d, seed=0, hide=None, step=0.28):
    """flower heads on stems in a bed; the ones inside `hide` (x0, x1, t) vanish at t (picked)"""
    out = []
    i = 0
    x = cx - w / 2 + 0.15
    while x < cx + w / 2 - 0.1:
        z = cz - d / 2 + 0.15
        while z < cz + d / 2 - 0.1:
            h = math.sin((x * 7.1 + z * 3.3 + seed) * 12.9898) * 43758.5453
            r = h - math.floor(h)
            st = {"t": "block", "p": [round(x, 3), round(z, 3)], "y": 0.3, "size": [0.03, 0.22, 0.03], "color": "#3a8a3a", "solid": False}
            fl = {"t": "block", "p": [round(x, 3), round(z, 3)], "y": 0.5, "size": [0.12, 0.1, 0.12], "color": FLOWER_COLS[int(r * 5) % 5], "solid": False}
            if hide and hide[0] <= x <= hide[1]:
                st["hideAt"] = fl["hideAt"] = round(hide[2] + r * 0.6, 3)
            out += [st, fl]
            z += step
            i += 1
        x += step
    return out


def city_hall(id, pick=None):
    P = [{"t": "building", "p": [0, -16], "w": 22, "d": 10, "floors": 4, "seed": 70, "color": "#b8a890", "day": True},
         {"t": "shopSign", "p": [0, -10.93], "y": 4.4, "w": 4.4, "h": 1.0, "text": "МЭРИЯ", "bg": "#2a3a6a", "glow": 0.3},
         *[{"t": "pillar", "p": [x, -10.4], "s": 0.9} for x in (-3.0, -1.0, 1.0, 3.0)],
         {"t": "block", "p": [-7.0, -10.6], "y": 3.2, "size": [0.06, 1.2, 0.8], "color": "#e8e8ee", "solid": False},       # flag
         {"t": "block", "p": [BED[0], BED[1]], "size": [6.2, 0.3, 2.6], "tex": "concrete", "color": "#9a968c"},             # flowerbed border
         {"t": "block", "p": [BED[0], BED[1]], "y": 0.3, "size": [5.9, 0.02, 2.3], "color": "#4a3424", "solid": False},     # soil
         *flowers(BED[0], BED[1], 5.8, 2.2, hide=pick),
         {"t": "block", "p": [3.6, -4.55], "size": [0.06, 1.0, 0.06], "color": "#5a5a60", "solid": False},
         {"t": "shopSign", "p": [3.6, -4.52], "y": 0.95, "w": 1.5, "h": 0.42, "text": "ЦВЕТЫ НЕ РВАТЬ", "bg": "#c83a2a", "glow": 0.2},
         {"t": "road", "p": [0, 7], "r": 90, "w": 7, "len": 80},
         {"t": "car", "p": [-6.0, 2.6], "r": 90, "color": "#e8eef6", "lights": True},
         {"t": "block", "p": [-6.0, 2.6], "y": 1.45, "size": [0.9, 0.12, 0.3], "emissive": "#3a6aff", "ei": 1.0, "solid": False},
         {"t": "car", "p": [5.0, 9.6], "r": -90, "color": "#3a6ab8"}, {"t": "car", "p": [-9.0, 9.6], "r": -90, "color": "#c8c8c0"},
         {"t": "streetLamp", "p": [-5.0, -3.0], "on": False}, {"t": "streetLamp", "p": [5.0, -3.0], "r": 180, "on": False},
         {"t": "bench", "p": [-6.0, -6.0], "r": 90}, {"t": "bench", "p": [6.0, -6.0], "r": -90},
         {"t": "tree", "p": [-9.0, -7.0], "s": 0.9}, {"t": "tree", "p": [9.0, -7.5], "s": 0.9}, {"t": "tree", "p": [-11.0, -1.0], "s": 0.8},
         {"t": "tree", "p": [11.0, -1.5], "s": 0.8},
         {"t": "building", "p": [-22, -4], "r": 90, "w": 20, "d": 10, "floors": 6, "seed": 71, "day": True, "color": "#8a7e72"},
         {"t": "building", "p": [22, -4], "r": -90, "w": 20, "d": 10, "floors": 7, "seed": 72, "day": True, "color": "#7a8a8e"},
         {"t": "building", "p": [0, 24], "r": 180, "w": 40, "d": 10, "floors": 8, "seed": 73, "day": True, "color": "#867a6e"},
         {"t": "crows", "p": [2.5, -2.0], "n": 6, "spread": 2.0, "color": "#7a808c"}]
    save_loc({"id": id, "tod": "day", "fog": 0.01, "ground": {"tex": "paving", "size": [200, 200]}, "props": P,
              "particles": [{"kind": "motes", "n": 60, "box": [-6, 0.3, -8, 6, 4, 4]}]})


PICK_X = (-2.95, -1.7)                  # the corner of the bed Витёк picks clean


# park: a lane along z, benches, lamps, trees, a pond; golden hour and the same park two hours later (night)
BENCH = (-2.2, 0.0)                     # the bench (faces +x, towards the lane)


def park(id, tod, night=False):
    P = [{"t": "block", "p": [0, 0], "size": [3.0, 0.02, 120], "tex": "paving", "color": "#b8a890", "solid": False},       # lane
         {"t": "bench", "p": list(BENCH), "r": 90, "w": 2.0},
         {"t": "bench", "p": [-2.2, -12.0], "r": 90}, {"t": "bench", "p": [2.2, -7.0], "r": -90}, {"t": "bench", "p": [2.2, 9.0], "r": -90},
         *[{"t": "streetLamp", "p": [(-1 if i % 2 else 1) * 2.0, z], "r": 0 if i % 2 else 180, "on": night} for i, z in enumerate([-18, -9, 2.5, 12, 22])],
         *[{"t": "tree", "p": [x, z], "s": 0.8 + 0.1 * (i % 3)} for i, (x, z) in enumerate(
             [(-4.5, -3.5), (-5.5, 4.0), (-4.2, 9.5), (-6.0, -10.0), (4.5, -2.0), (5.5, 5.0), (4.2, -11.0), (6.5, 12.0), (-7.5, 15.0), (-9, 0), (9, 0), (-8, -18), (8, -18)])],
         *[{"t": "bush", "p": [x, z], "s": 0.7} for x, z in [(-3.2, 2.2), (-3.2, -2.4), (3.4, 3.4), (3.3, -5.0), (-3.4, 6.5)]],
         {"t": "block", "p": [7.5, -5.0], "size": [5.0, 0.03, 4.0], "color": "#3a6a8a", "emissive": "#2a4a6a", "ei": 0.2, "solid": False},     # pond
         {"t": "crows", "p": [1.0, -4.0], "n": 5, "spread": 1.6, "color": "#7a808c"},
         {"t": "lightPt", "p": [0.8, 0.3], "y": 2.2, "i": 2.2 if not night else 1.2, "d": 7, "color": "#ffd8b0"},
         {"t": "building", "p": [-30, 0], "r": 90, "w": 60, "d": 10, "floors": 9, "seed": 81, **({"lit": 0.5} if night else {"day": True}), "color": "#7a7680"},
         {"t": "building", "p": [32, 0], "r": -90, "w": 60, "d": 10, "floors": 12, "seed": 82, **({"lit": 0.5} if night else {"day": True}), "color": "#867a6e"}]
    save_loc({"id": id, "tod": tod, "fog": 0.014, "ground": {"tex": "grass", "size": [200, 200]}, "props": P,
              "particles": [{"kind": "motes", "n": 70, "box": [-5, 0.3, -6, 5, 4, 6]}]})


park("zn_park", "golden")
park("zn_park_n", "night", night=True)

# ----------------------------------------------------------------- episode
ep = Ep("shorts", "znak", fps=30, w=W, h=H)
cut = Cut(ep, w)


def actor(s, id, char, at, face=0, act="idle", eyes=None, mouth=None, **arg):
    a = s.actor(id, char, at=at, face=face)
    a.act(0, act, **arg)
    if eyes or mouth:
        a.expr(0, eyes, mouth)
    return a


MIN_D = 3.4


def ks(s, keys, focus=None, ap=None, hh=None, md=None):
    """explicit camera keys in GLOBAL time: [(t, pos, look, fov[, ease]), …]; t = -1 → end of shot. Dolls are big: closer
    than MIN_D the camera is pushed back along its line (testosteron v2 / tupoy lesson)"""
    out = []
    for i, (t, p, l, f, *rest) in enumerate(keys):
        d = math.dist(p, l)
        lim = MIN_D if md is None else md
        if d < lim:
            p = [l[j] + (p[j] - l[j]) * lim / max(d, 0.05) for j in range(3)]
            f = max(f, 42)
        out.append(K(round(max(0.0, t - s.t0) if t != -1 else s.dur, 3), p, l, f, None if i == 0 else (rest[0] if rest else "inOut")))
    s.cam(out, focus=focus, aperture=ap, **({"handheld": hh} if hh is not None else {}))
    return s


def orbit(s, c, r, h, a0, a1, look_h, fov, n=6, focus=None, ap=None, r1=None, h1=None):
    keys = []
    for i in range(n):
        f = i / (n - 1)
        a = math.radians(a0 + (a1 - a0) * f)
        rr = r + ((r1 if r1 is not None else r) - r) * f
        hh = h + ((h1 if h1 is not None else h) - h) * f
        keys.append((s.t0 + s.dur * f, [c[0] + math.sin(a) * rr, hh, c[1] + math.cos(a) * rr], [c[0], look_h, c[1]], fov, "linear"))
    return ks(s, keys, focus=focus, ap=ap)


def extra(s, *props):
    s.kw.setdefault("extra", []).extend(props)


def flash(t, d=0.12, color="#ffffff"):
    cut.card("black", t - 0.02, t + d, color=color, fi=0.02, fo=d * 0.8)


def hit(s, t, v=0.06, d=0.4):
    s.fxk(t - s.t0, "shake", d=d, v=v)


def method(n, name, t0, t1, color="#ffd84a"):
    cut.card("stat", t0, t1, text=f"СПОСОБ №{n}", label=name, y=0.15, size=110, color=color)


def blink_lights(s, x, z, y=1.5):
    """police car roof lights: blue/red alternate (lightPt.blink takes Hz + absolute onAt)"""
    extra(s, {"t": "lightPt", "p": [x - 0.3, z], "y": y, "i": 4, "d": 7, "color": "#3a6aff", "onAt": round(s.t0, 3), "blink": 2.5},
          {"t": "lightPt", "p": [x + 0.3, z], "y": y, "i": 4, "d": 7, "color": "#ff3a3a", "onAt": round(s.t0 + 0.2, 3), "blink": 2.5})


# ======================================================== 1. HOOK — teaser: the «date» at the city hall (with a policeman)
city_hall("zn_hall", pick=(PICK_X[0], PICK_X[1], -10.0))     # bed already picked in the teaser and after
city_hall("zn_hall_pick", pick=(PICK_X[0], PICK_X[1], round(A("Нарвал") + 0.2, 3)))
KNEEL = (0.4, -1.4)                                          # Витёк kneels here, facing +z
COP = (0.4, -0.2)
T_DEV = A("девушкой")
s = cut.shot("zn_hall", round(A("Витёк") - 0.05, 3))
v = actor(s, "hero", V, KNEEL, face=0, act="kneel", eyes="happy", mouth="smile")
v.hold(0, B="flowers")
p = actor(s, "cop", "police", COP, face=180, act="arms_crossed", eyes="angry", mouth="closed")
actor(s, "liza", L, (2.6, 0.6), face=-120, act="idle", eyes="wide", mouth="o")
actor(s, "x1", "p1", (-3.4, 1.2), face=60, act="phone_up").hold(0, B="phone")
actor(s, "x2", "babka2", (-4.2, -0.2), face=80, act="idle", eyes="wide", mouth="o")
blink_lights(s, -6.0, 2.6)
ks(s, [(0.0, [5.2, 1.5, -2.2], [0.6, 1.0, -0.6], 50), (T_DEV, [4.2, 1.35, -1.9], [0.5, 1.0, -0.7], 46), (-1, [4.0, 1.3, -1.8], [0.5, 1.0, -0.7], 44)],
   focus="hero", ap=4)
hit(s, T_DEV, 0.05)
cut.sfx(0.0, "usr-whoosh-roar-low-swell-322", -7)
cut.sfx(T_DEV, "hit-cinematic", -8)
cut.sfx(0.2, "siren-far", -16, dur=1.6)

# rewind → Витёк's room: forty guides on the phone
T_VIT = A("Витёк")
T_RW = T_VIT
T_SEY = A("Сейчас")
s = cut.shot("zn_room", round(T_SEY - 0.05, 3))
v = actor(s, "hero", V, (-1.2, -0.6), face=20, act="sit", eyes="normal", mouth="closed", seat=0.5)
v.hold(0, B="phone")
ks(s, [(s.t0, [0.6, 1.5, 2.4], [-1.1, 1.35, -0.6], 48), (-1, [0.2, 1.4, 1.9], [-1.15, 1.4, -0.6], 44)], focus="hero", ap=6)
flash(T_RW, 0.16)
cut.card("label", T_RW, T_RW + 1.1, text="◀◀ ПЕРЕМОТКА", sub="УТРО", x=0.06, y=0.15, border="#ff4a2a")
cut.sfx(T_RW - 0.12, "usr-tape-rewind-mid-swell-049", -6, dur=0.9)
T_40 = A("сорок", after=T_VIT)
cut.card("stat", T_40 - 0.05, s.t1 - 0.03, **{"from": 0, "to": 40, "rollAt": T_40, "rollDur": 0.8}, label="ГАЙДОВ «КАК ПОКОРИТЬ»", y=0.3, size=150)
cut.sfx(T_40, "usr-whoosh-light-mid-snap-382", -9)

T_NADO = A("надо")
s = cut.shot("zn_room", S[2])
v = actor(s, "hero", V, (-0.2, 0.3), face=10, act="idle", eyes="happy", mouth="smile")
v.act(T_SEY - s.t0 + 0.2, "fist"); v.expr(T_SEY - s.t0 + 0.2, "happy", "smile")
ks(s, [(s.t0, [0.4, 0.7, 2.6], [-0.2, 1.3, 0.3], 52), (-1, [0.3, 0.65, 2.3], [-0.2, 1.35, 0.3], 48)], focus="hero", ap=6)       # low angle: «the master»
cut.card("label", T_SEY, s.t1 - 0.03, text="ВИТЁК", sub="ТОТ САМЫЙ, СО СТОЛБА", x=0.06, y=0.15, border="#7ad0ff")
cut.card("stat", T_NADO - 0.3, s.t1 - 0.03, text="КАК НЕ НАДО", label="", y=0.3, size=110, color="#ff5a3c")
cut.sfx(T_SEY + 0.2, "usr-whoosh-whip-mid-snap-135", -9)
cut.sfx(T_NADO, "usr-voice-bruh-mid-swell-097", -12)

# ======================================================== 2. Method 1: the pick-up line (cafe «Вай-фай»)
LZ_SEAT = (T1[0], T1[1] + 0.6)          # Лиза sits facing -z towards the window-side table
VK_SEAT = (T1[0], T1[1] - 0.6)          # Витёк sits down opposite her, facing +z


def cafe_people(s, liza=True):
    actor(s, "bar", "barista", (1.4, -2.15), face=10, act="idle")
    actor(s, "lap", "p1", (T3[0] + 0.6, T3[1]), face=-90, act="sit", seat=0.46)
    actor(s, "c2", "p4", (T2[0] + 0.5, T2[1] - 0.3), face=-60, act="phone_up").hold(0, B="phone")
    if liza:
        lz = actor(s, "liza", L, LZ_SEAT, face=180, act="sit", eyes="normal", mouth="closed", seat=0.46)
        lz.hold(0, B="cup")
        return lz


T_TY2 = A("Ты", after=S[2])
T_VF = A("вай-фай")
T_SVZ = A("связь")
s = cut.shot("zn_cafe", round(T_TY2 - 0.05, 3))
s.fxk(0.0, "zoomblur", d=0.3, v=0.5)
cafe_people(s)
v = actor(s, "hero", V, (1.4, 2.0), face=-120, act="idle", eyes="happy", mouth="smile")
WALK = round(max(1.0, s.dur - 0.45), 3)
v.walk(0.1, VK_SEAT, dur=WALK)                       # ~3.3 m in ~2 s
v.face(WALK + 0.1, 0)
v.act(WALK + 0.2, "sit", seat=0.46)
ks(s, [(s.t0, [-0.2, 1.8, -1.0], [-1.0, 1.0, 1.4], 56), (-1, [-0.4, 1.7, -1.1], [-1.3, 1.0, 1.0], 52)], focus="hero", ap=3)
method(1, "ПОДКАТ", S[2], A("Витёк", after=S[2]) + 0.6)
cut.card("label", A("кафе") - 0.05, s.t1 - 0.03, text="КАФЕ «ВАЙ-ФАЙ»", x=0.06, y=0.15, border="#3a6aa8")
cut.sfx(S[2], "usr-whoosh-whip-mid-snap-149", -9)

s = cut.shot("zn_cafe", round(A("Лиза", after=S[2]) - 0.05, 3))
cafe_people(s)
v = actor(s, "hero", V, VK_SEAT, face=0, act="sit", eyes="happy", mouth="smile", seat=0.46)
v.act(T_VF - s.t0, "point")
v.talk(0.0, A("связь", end=True) - s.t0)
ks(s, [(s.t0, [-1.2, 1.35, 4.0], [-1.6, 1.05, 0.3], 44), (-1, [-1.15, 1.3, 3.8], [-1.6, 1.05, 0.3], 42)], focus="hero", ap=8)   # over Лиза, onto him
cut.card("bubble", T_TY2 - 0.05, s.t1 - 0.03, who="ВИТЁК", whoColor="#ffd84a", text="Ты случайно не вай-фай?\nЧувствую связь.", y=0.15, side="left")
cut.card("label", T_SVZ, s.t1 - 0.03, text="▮▮▮▯ СВЯЗЬ", sub="СЛАБАЯ", x=0.55, y=0.3, border="#3a6aa8")
cut.sfx(T_VF, "usr-notify-ding-bright-snap-105", -10)

T_PAR = A("Пароль")
T_PERE = A("пересаживается")
s = cut.shot("zn_cafe", round(A("И", after=T_PAR) - 0.05, 3))
cafe_people(s, liza=False)
lz = actor(s, "liza", L, LZ_SEAT, face=180, act="sit", eyes="narrow", mouth="closed", seat=0.46)
lz.hold(0, B="cup")
lz.talk(T_PAR - s.t0, A("нет", after=T_PAR, end=True) - s.t0)
ks(s, [(s.t0, [-1.6, 1.3, -1.6], [-1.6, 1.15, 1.5], 42), (-1, [-1.6, 1.28, -1.4], [-1.6, 1.15, 1.5], 40)], focus="liza", ap=10)
cut.card("bubble", T_PAR - 0.05, s.t1 - 0.03, who="ЛИЗА", whoColor="#ff8ad0", text="Пароль: нет.", y=0.15, side="right")
cut.sfx(A("нет", after=T_PAR), "usr-error-alert-mid-snap-078", -11)

s = cut.shot("zn_cafe", S[3])
cafe_people(s, liza=False)
lz = actor(s, "liza", L, LZ_SEAT, face=180, act="sit", seat=0.46)
lz.act(0.05, "idle"); lz.hold(0, B="cup")
lz.walk(0.25, (T2[0], T2[1] + 0.6), dur=round(min(2.6, s.dur - 0.5), 3))    # 3.3 m in ~2.5 s
lz.face(round(min(2.6, s.dur - 0.5) + 0.25, 3), 180)
lz.act(round(min(2.6, s.dur - 0.5) + 0.35, 3), "sit", seat=0.46)
v = actor(s, "hero", V, VK_SEAT, face=0, act="sit", eyes="sad", mouth="o", seat=0.46)
ks(s, [(s.t0, [0.0, 2.0, -2.0], [0.0, 1.0, 1.0], 56), (-1, [0.1, 2.0, -2.1], [0.4, 1.0, 1.2], 56)], focus="hero", ap=2)
cut.card("label", T_PERE - 0.05, s.t1 - 0.03, text="ПОДКАТ: МИМО", x=0.06, y=0.15, border="#ff4a2a")
cut.sfx(T_PERE, "usr-cartoon-bloop-low-swell-284", -10)

# ======================================================== 3. Method 2: mystery (dark glasses, lamp, night, three hours)
LAMP = (-4.5, 6.0)
SPOT = (-5.0, 6.6)                       # under the lamp, facing the road (+x)
T_TEM = A("Тёмные")
s = cut.shot("zn_night", round(T_TEM - 0.05, 3))
v = actor(s, "hero", VG, (-5.4, 2.8), face=10, act="idle", eyes="normal", mouth="closed")
v.walk(0.0, SPOT, dur=round(max(1.0, s.dur - 0.3), 3))
v.face(round(max(1.0, s.dur - 0.3), 3), 90)
ks(s, [(s.t0, [-1.2, 1.5, 9.0], [-5.1, 1.2, 5.0], 52), (-1, [-1.6, 1.5, 9.2], [-5.0, 1.25, 6.2], 50)], focus="hero", ap=4)
method(2, "ЗАГАДОЧНОСТЬ", S[3], s.t1 - 0.03, color="#9ad0ff")
cut.sfx(S[3], "usr-whoosh-whip-mid-snap-149", -9)

T_FON = A("фонарь")
T_NOCH = A("ночь", after=S[3])
s = cut.shot("zn_night", round(A("Витёк", after=S[3]) - 0.05, 3))
actor(s, "hero", VG, SPOT, face=90, act="arms_crossed", eyes="normal", mouth="closed")
ks(s, [(s.t0, [-2.2, 1.7, 7.6], [-5.0, 1.6, 6.6], 30), (T_FON - 0.05, [-2.25, 1.75, 7.5], [-5.0, 1.65, 6.6], 30),          # the glasses
       (T_FON + 0.3, [-2.4, 1.0, 7.9], [-4.5, 3.4, 6.0], 46, "out"),                                                            # tilt up to the lamp
       (T_NOCH + 0.3, [-2.2, 1.1, 10.0], [-5.6, 6.5, -4.0], 56, "out"), (-1, [-2.1, 1.15, 10.2], [-5.7, 6.8, -4.5], 56)],       # the night sky
   focus="hero", ap=6, md=2.6)
for t in (A("Тёмные"), T_FON, T_NOCH):
    cut.sfx(t, "usr-whoosh-light-mid-snap-221", -10)
cut.card("label", A("Тёмные") - 0.05, T_FON - 0.08, text="ОЧКИ: ТЁМНЫЕ", sub="НОЧЬЮ", x=0.06, y=0.15, border="#9ad0ff")

T_3H = A("три", after=S[3])
s = cut.shot("zn_night", round(C[4]["start"] - 0.05, 3))
actor(s, "hero", VG, SPOT, face=90, act="arms_crossed", eyes="normal", mouth="closed")
extra(s, {"t": "crows", "p": [-5.6, 8.6], "n": 2, "spread": 0.6, "color": "#5a5e68"})
orbit(s, SPOT, 4.6, 1.5, 70, 135, 1.3, 50, focus="hero", ap=4)
cut.card("stat", T_3H - 0.05, s.t1 - 0.03, **{"from": 0, "to": 3, "rollAt": T_3H, "rollDur": 0.6}, label="ЧАСА СТОИТ", y=0.15, size=150, color="#9ad0ff")
cut.sfx(T_3H, "usr-whoosh-light-bright-swell-200", -10)

T_BAB = A("бабушка")
T_SYN = A("Сынок")
s = cut.shot("zn_night", S[4])
v = actor(s, "hero", VG, SPOT, face=90, act="arms_crossed", eyes="normal", mouth="closed")
v.face(T_SYN - s.t0, 160)
v.act(T_SYN - s.t0 + 0.1, "shrug")
b = actor(s, "babka", "babka1", (-4.9, 10.0), face=180, act="idle", eyes="normal", mouth="closed")
b.walk(0.0, (-5.1, 7.6), dur=round(max(0.8, T_SYN - s.t0 - 0.2), 3))   # 2.4 m, grandma pace
b.talk(T_SYN - s.t0, s.dur - 0.1)
ks(s, [(s.t0, [-1.6, 1.5, 9.4], [-5.0, 1.3, 7.6], 48), (-1, [-1.9, 1.5, 9.0], [-5.05, 1.35, 7.2], 46)], focus="babka", ap=5)
cut.card("bubble", T_SYN - 0.05, s.t1 - 0.03, who="БАБУШКА", whoColor="#c8b8ff", text="Сынок, ты потерялся?", y=0.15, side="right")
cut.card("label", T_BAB - 0.05, T_SYN - 0.1, text="ПОДОШЛА: 1", sub="БАБУШКА", x=0.06, y=0.28, border="#c8b8ff")
cut.sfx(T_BAB, "usr-cartoon-bloop-mid-snap-061", -12)

# ======================================================== 4. Method 3: show strength (100 push-ups at the bus stop)
STOP_BENCH = (6.35, -19.0)
PUSH = (5.0, -16.6)                      # on the sidewalk in front of the stop, side view from +z
SW = 0.16                                # sidewalk top for keyframed props
T_STO = A("Сто", after=S[4])
s = cut.shot("zn_day", round(T_STO - 0.05, 3))
lz = actor(s, "liza", L, STOP_BENCH, face=-90, act="sit", eyes="normal", mouth="closed", seat=0.46)
lz.hold(0, B="phone")
v = actor(s, "hero", V, (5.2, -12.6), face=180, act="idle", eyes="happy", mouth="smile")
v.walk(0.0, (5.1, -15.6), dur=round(max(1.0, s.dur - 0.3), 3))
v.act(round(max(1.0, s.dur - 0.3), 3), "fist")
actor(s, "x1", "p3", (6.6, -21.0), face=-80, act="idle")
ks(s, [(s.t0, [1.2, 1.6, -11.0], [5.6, 1.2, -17.0], 52), (-1, [1.5, 1.6, -11.6], [5.8, 1.2, -17.6], 50)], focus="hero", ap=4)
method(3, "ПОКАЗАТЬ СИЛУ", S[5] if 5 in S and False else S[4] + 0.0, s.t1 - 0.03, color="#ff8a3a")
cut.sfx(S[4], "usr-whoosh-whip-mid-snap-149", -9)

T_NA = A("На", after=T_STO)
T_TAX = A("такси")
T_DOS = A("Досчитал")
TAXI_STOP = [3.2, 0.0, -19.4]


def taxi(t_arrive, t_leave):
    k = [{"t": round(t_arrive - 1.6, 3), "p": [3.2, 0.0, 10.0]}, {"t": round(t_arrive, 3), "p": TAXI_STOP, "e": "out"},
         {"t": round(t_leave, 3), "p": TAXI_STOP}, {"t": round(t_leave + 1.8, 3), "p": [3.2, 0.0, -48.0], "e": "in"}]
    return {"t": "car", "p": [3.2, 10.0], "r": 180, "color": "#f0c020", "taxi": True, "lights": True, "anim": k}


TAXI = taxi(T_NA + 0.3, T_TAX + 0.55)
s = cut.shot("zn_day", round(T_NA - 0.05, 3))
lz = actor(s, "liza", L, STOP_BENCH, face=-90, act="sit", seat=0.46)
lz.hold(0, B="phone")
v = actor(s, "hero", V, PUSH, face=-90, act="pushup", eyes="angry", mouth="grit")
ks(s, [(s.t0, [4.5, 1.1, -12.4], [4.5, 0.45, -16.6], 50), (-1, [4.3, 1.1, -12.3], [4.5, 0.45, -16.6], 48)], focus="hero", ap=5)
cut.card("stat", T_STO - 0.05, s.t1 - 0.03, **{"from": 0, "to": 41, "rollAt": T_STO, "rollDur": round(max(0.6, s.t1 - T_STO - 0.2), 3)}, label="ОТЖИМАНИЙ", y=0.15, size=150)
for k in range(int((s.t1 - T_STO) / 0.45)):
    cut.sfx(T_STO + k * 0.45, "usr-thud-low-low-snap-095", -16)

s = cut.shot("zn_day", round(T_DOS - 0.05, 3))
extra(s, TAXI)
lz = actor(s, "liza", L, STOP_BENCH, face=-90, act="sit", seat=0.46)
lz.hold(0, B="phone")
lz.act(T_NA + 0.35 - s.t0, "idle"); lz.hold(T_NA + 0.35 - s.t0, B=None)
lz.walk(T_NA + 0.4 - s.t0, (4.35, -19.4), dur=1.4)
lz.show(T_NA + 1.9 - s.t0, False)
v = actor(s, "hero", V, PUSH, face=-90, act="pushup", eyes="angry", mouth="grit")
ks(s, [(s.t0, [1.0, 1.6, -12.4], [5.0, 0.8, -18.2], 54), (-1, [0.8, 1.7, -12.2], [4.6, 0.8, -19.0], 56)], focus=None, ap=2)
cut.card("stat", s.t0, s.t1 - 0.03, **{"from": 42, "to": 87, "rollAt": s.t0 + 0.2, "rollDur": round(s.dur - 0.4, 3)}, label="ОТЖИМАНИЙ", y=0.15, size=150)
cut.card("label", T_TAX - 0.05, s.t1 - 0.03, text="ЛИЗА: УЕХАЛА", sub="НА 42-М", x=0.06, y=0.3, border="#ff8ad0")
cut.sfx(T_NA - 0.6, "usr-whoosh-roar-low-swell-322", -18, dur=1.2)   # taxi rolls in (no car-pass in the library)
cut.sfx(T_TAX + 0.4, "door-heavy-close", -14, dur=0.5)
for k in range(int(s.dur / 0.45)):
    cut.sfx(s.t0 + k * 0.45, "usr-thud-low-low-snap-095", -17)

T_GOL = A("Голуби")
s = cut.shot("zn_day", S[5])
v = actor(s, "hero", V, PUSH, face=-90, act="pushup", eyes="angry", mouth="grit")
v.act(0.35, "fist"); v.expr(0.35, "happy", "shout"); v.face(0.3, 0)
ks(s, [(s.t0, [5.6, 0.35, -13.2], [5.2, 1.0, -16.4], 52), (-1, [5.7, 0.35, -13.0], [5.2, 1.1, -16.4], 50)], focus="hero", ap=3)   # pigeons' eye level
cut.card("stat", s.t0, round(T_GOL - 0.1, 3), text="100!", label="", y=0.15, size=170, color="#5ad05a")
cut.card("label", T_GOL - 0.05, s.t1 - 0.03, text="ГОЛУБИ: В ВОСТОРГЕ", sub="ЛИЗА: В ТАКСИ", x=0.06, y=0.15, border="#5ad05a")
cut.sfx(s.t0 + 0.35, "usr-brass-swell-mid-tail-146", -12)
cut.sfx(T_GOL, "usr-crowd-aww-mid-swell-156", -16)

# ======================================================== 5. Method 4: texting
T_PRV = A("Привет", after=S[5])
T_HAI = A("Хай")
T_CHR = A("Через", after=S[5])
T_ELA = A("ела")
T_DA = A("Да", after=T_ELA)
T_DLG = A("Диалог")
s = cut.shot("zn_room", round(T_CHR - 0.05, 3))
v = actor(s, "hero", V, (-1.2, -0.6), face=20, act="sit", eyes="normal", mouth="closed", seat=0.5)
v.hold(0, B="phone")
ks(s, [(s.t0, [0.3, 1.4, 1.7], [-1.15, 1.4, -0.6], 46), (-1, [0.2, 1.35, 1.5], [-1.15, 1.4, -0.6], 44)], focus="hero", ap=6)
method(4, "НАПИСАТЬ", S[5], T_PRV - 0.1, color="#7ad0ff")
cut.card("strike", T_PRV - 0.1, s.t1 - 0.03, items=["ПРИВЕТ", "ХАЙ"], at=[round(A("стёр", after=T_PRV), 3), round(A("стёр", after=T_HAI), 3)], y=0.15, size=90)
for t in (A("стёр", after=T_PRV), A("стёр", after=T_HAI)):
    cut.sfx(t, "usr-click-pop-bright-snap-215", -10)
cut.sfx(T_PRV - 0.1, "typing-short", -12)

s = cut.shot("zn_room", round(A("Диалог") - 0.05, 3))
v = actor(s, "hero", V, (-1.2, -0.6), face=20, act="sit", eyes="normal", mouth="closed", seat=0.5)
v.hold(0, B="phone")
v.expr(T_DA - s.t0 + 0.1, "wide", "o")
ks(s, [(s.t0, [0.1, 1.3, 1.3], [-1.15, 1.1, -0.6], 42), (-1, [0.0, 1.3, 1.2], [-1.15, 1.1, -0.6], 40)], focus="hero", ap=10)
t0p = s.t0
cut.card("phone", t0p, S[6] - 0.02, app="ЛИЗА", clock="03:12", signal="LTE", battery="4%",
         msgs=[{"t": round(A("Ты", after=T_CHR) - t0p, 3), "who": "me", "text": "Ты ела?"},
               {"t": round(T_DA - t0p + 0.05, 3), "who": "ai", "from": "Лиза", "text": "Да"}])
cut.card("label", T_CHR - 0.05, A("отправил") + 0.6, text="+3 ЧАСА", sub="ДУМАЛ", x=0.06, y=0.12, border="#7ad0ff")
cut.sfx(A("Ты", after=T_CHR), "typing-short", -12)
cut.sfx(T_DA, "pk-notify-notification-sfx-1", -8)

s = cut.shot("zn_room", S[6])
v = actor(s, "hero", V, (-1.2, -0.6), face=20, act="sit", eyes="wide", mouth="o", seat=0.5)
v.act(0.05, "facepalm")
ks(s, [(s.t0, [-0.6, 2.6, 1.2], [-1.2, 0.9, -0.6], 50), (-1, [-0.7, 2.8, 1.4], [-1.2, 0.9, -0.6], 52)], focus="hero", ap=4)
cut.card("stat", T_DLG - 0.05, s.t1 - 0.03, text="ДИАЛОГ: ВСЁ", label="", y=0.15, size=110, color="#ff5a3c")
cut.sfx(T_DLG, "usr-boxing-bell-mid-tail-109", -12)

# ======================================================== 6. Method 5: flowers from the city-hall bed → a date with a policeman
T_NAR = A("Нарвал")
T_SVI = A("Свидание")
T_POL = A("полицейским")
s = cut.shot("zn_hall_pick", round(T_NAR - 0.05, 3))
v = actor(s, "hero", V, (-2.3, -4.35), face=180, act="kneel", eyes="happy", mouth="smile")
actor(s, "x1", "p3", (6.4, -6.0), face=-90, act="sit", seat=0.46)
ks(s, [(s.t0, [1.4, 1.4, -3.2], [-2.3, 0.7, -4.8], 50), (-1, [1.1, 1.35, -3.4], [-2.3, 0.7, -4.8], 46)], focus="hero", ap=4)
method(5, "ЦВЕТЫ", S[6], s.t1 - 0.03, color="#ff8ab0")
cut.sfx(S[6], "usr-whoosh-whip-mid-snap-149", -9)

s = cut.shot("zn_hall_pick", round(T_SVI - 0.05, 3))
v = actor(s, "hero", V, (-2.3, -4.35), face=180, act="kneel", eyes="happy", mouth="smile")
v.act(T_NAR - s.t0 + 0.4, "idle"); v.hold(T_NAR - s.t0 + 0.4, B="flowers")
v.face(T_NAR - s.t0 + 0.45, 0)
ks(s, [(s.t0, [0.2, 1.3, -1.6], [-2.3, 0.8, -4.6], 46), (-1, [0.0, 1.35, -1.4], [-2.3, 0.9, -4.5], 46)], focus="hero", ap=6)
cut.card("label", A("клумбе") - 0.05, s.t1 - 0.03, text="КЛУМБА МЭРИИ", sub="БЫЛА", x=0.06, y=0.15, border="#ff8ab0")
for k in range(4):
    cut.sfx(T_NAR + 0.2 + k * 0.16, "usr-whoosh-light-mid-snap-223", -15)

s = cut.shot("zn_hall", round(T_POL - 0.1, 3))
v = actor(s, "hero", V, (-0.6, -3.4), face=10, act="idle", eyes="happy", mouth="smile")
v.hold(0, B="flowers")
v.walk(0.0, KNEEL, dur=1.6)
v.act(1.65, "kneel")
cop = actor(s, "cop", "police", (-4.6, 0.6), face=90, act="idle", eyes="angry", mouth="closed")
cop.walk(0.2, COP, dur=round(min(3.6, max(1.5, s.dur - 0.4)), 3))
cop.face(round(min(3.6, max(1.5, s.dur - 0.4)) + 0.2, 3), 180)
lz = actor(s, "liza", L, (2.6, 1.4), face=-90, act="idle")
lz.walk(0.0, (6.0, 2.2), dur=2.8)
blink_lights(s, -6.0, 2.6)
ks(s, [(s.t0, [3.4, 1.7, -5.6], [0.0, 1.0, -1.6], 52), (-1, [2.8, 1.5, -5.0], [0.4, 1.0, -1.0], 48)], focus="hero", ap=4)
cut.sfx(T_SVI, "usr-brass-swell-mid-tail-146", -12)

s = cut.shot("zn_hall", S[7])
v = actor(s, "hero", V, KNEEL, face=0, act="kneel", eyes="wide", mouth="o")
v.hold(0, B="flowers")
actor(s, "cop", "police", COP, face=180, act="arms_crossed", eyes="angry", mouth="closed")
blink_lights(s, -6.0, 2.6)
ks(s, [(s.t0, [4.0, 1.3, -0.6], [0.4, 1.05, -0.8], 46), (-1, [3.8, 1.3, -0.7], [0.4, 1.05, -0.8], 44)], focus="hero", ap=6)
cut.card("stat", T_POL - 0.05, s.t1 - 0.03, text="С ПОЛИЦЕЙСКИМ", label="СВИДАНИЕ", y=0.15, size=100, color="#7ad0ff")
cut.sfx(T_POL - 0.1, "siren-far", -11, dur=1.6)
hit(s, T_POL, 0.05, 0.3)

# ======================================================== 7. The turn: the bench in the park
LZ_B = (BENCH[0], BENCH[1] - 0.45)
VK_B = (BENCH[0], BENCH[1] + 0.45)
T_LZ7 = A("Лиза", after=S[7])
T_LIZN = A("лизнул")
T_NU = C[11]["start"]
T_DVA = A("проболтали")
T_BEZ = A("Без", after=T_DVA)
s = cut.shot("zn_park", round(T_LZ7 - 0.05, 3))
v = actor(s, "hero", V, (0.3, 3.0), face=-150, act="idle", eyes="sad", mouth="closed")
v.walk(0.0, (VK_B[0] + 0.5, VK_B[1]), dur=round(min(2.4, s.dur - 0.7), 3))
v.face(round(min(2.4, s.dur - 0.7), 3), 90)
v.act(round(min(2.4, s.dur - 0.7) + 0.25, 3), "sit", seat=0.46)
v.walk(round(min(2.4, s.dur - 0.7) + 0.15, 3), VK_B, dur=0.25)
ks(s, [(s.t0, [-3.6, 1.5, 4.0], [-0.6, 1.0, 1.4], 52), (-1, [-3.4, 1.45, 3.6], [-1.2, 1.0, 0.8], 48)], focus="hero", ap=4)
cut.card("label", S[7] + 0.05, s.t1 - 0.03, text="ВИТЁК СДАЛСЯ", sub="0 ИЗ 5", x=0.06, y=0.15, border="#9a9aa8")
cut.sfx(A("сел"), "usr-thud-low-low-snap-305", -16)

s = cut.shot("zn_park", round(T_LIZN - 0.3, 3))
v = actor(s, "hero", V, VK_B, face=90, act="sit", eyes="sad", mouth="closed", seat=0.46)
lz = actor(s, "liza", L, (1.0, -2.6), face=-30, act="idle", eyes="normal", mouth="smile")
lz.walk(0.0, (LZ_B[0] + 0.5, LZ_B[1]), dur=round(min(2.2, s.dur - 0.6), 3))
lz.face(round(min(2.2, s.dur - 0.6), 3), 90)
lz.act(round(min(2.2, s.dur - 0.6) + 0.25, 3), "sit", seat=0.46)
lz.walk(round(min(2.2, s.dur - 0.6) + 0.15, 3), LZ_B, dur=0.25)
lz.talk(A("Ты", after=T_LZ7) - s.t0, s.dur)
ks(s, [(s.t0, [1.6, 1.4, 2.0], [-1.4, 1.0, -0.6], 52), (-1, [1.4, 1.35, 1.8], [-1.6, 1.0, -0.4], 48)], focus="liza", ap=4)
cut.card("bubble", A("Ты", after=T_LZ7) - 0.05, s.t1 - 0.03, who="ЛИЗА", whoColor="#ff8ad0", text="Ты же тот, кто лизнул столб?", y=0.15, side="right")
BUB_END = T_NU

s = cut.shot("zn_park", round(T_NU - 0.05, 3))
v = actor(s, "hero", V, VK_B, face=90, act="sit", eyes="wide", mouth="o", seat=0.46)
lz = actor(s, "liza", L, LZ_B, face=60, act="sit", eyes="happy", mouth="smile", seat=0.46)
lz.hold(0, B="phone")
ks(s, [(s.t0, [1.2, 1.3, 0.0], [-2.2, 1.05, 0.0], 44), (-1, [1.1, 1.3, 0.1], [-2.2, 1.05, 0.0], 42)], focus="hero", ap=8)
cut.card("feed", s.t0 + 0.02, T_NU - 0.08, y=0.5, swipes=[],
         clips=[{"title": "ПАРЕНЬ ЛИЖЕТ СТОЛБ", "color": "#c84a2a", "likes": "9.9M", "author": "lol"}])
cut.sfx(T_LIZN, "usr-glass-shatter-bright-snap-151", -16)
cut.sfx(T_LIZN + 0.1, "usr-suspense-sting", -14)

s = cut.shot("zn_park", round(T_DVA - 0.05, 3))
v = actor(s, "hero", V, VK_B, face=60, act="shrug", eyes="happy", mouth="smile", seat=0.46)
v.act(0.0, "sit", seat=0.46)
v.talk(0.0, A("да", after=T_NU, end=True) - s.t0)
lz = actor(s, "liza", L, LZ_B, face=120, act="sit", eyes="happy", mouth="smile", seat=0.46)
ks(s, [(s.t0, [1.6, 1.25, -0.2], [-2.2, 1.05, 0.0], 46), (-1, [1.5, 1.25, -0.1], [-2.2, 1.05, 0.0], 44)], focus="hero", ap=6)
cut.card("bubble", T_NU - 0.05, s.t1 - 0.03, who="ВИТЁК", whoColor="#ffd84a", text="Ну... да.", y=0.15, side="left")

s = cut.shot("zn_park_n", S[8])
v = actor(s, "hero", V, VK_B, face=60, act="sit", eyes="happy", mouth="smile", seat=0.46)
v.talk(0.0, s.dur * 0.4)
lz = actor(s, "liza", L, LZ_B, face=120, act="sit", eyes="happy", mouth="smile", seat=0.46)
lz.talk(s.dur * 0.45, s.dur - 0.1)
ks(s, [(s.t0, [2.2, 1.5, 2.2], [-2.2, 1.0, 0.0], 50), (-1, [3.6, 4.6, 4.8], [-2.2, 1.0, 0.0], 54)], focus=None, ap=2)      # crane up
cut.card("label", T_DVA - 0.05, s.t1 - 0.03, text="+2 ЧАСА", sub="БОЛТАЮТ", x=0.06, y=0.15, border="#ff8ad0")
cut.card("stat", T_BEZ - 0.05, s.t1 - 0.03, text="0", label="ПОДКАТОВ", y=0.24, size=160, color="#5ad05a")
cut.sfx(T_DVA, "usr-whoosh-light-bright-swell-200", -10)

# ======================================================== 8. The rule: just say «привет»
T_PRO = A("Просто")
T_BEZ8 = A("Без", after=S[8])
T_SME = A("Смелость")
s = cut.shot("zn_park", round(T_BEZ8 - 0.05, 3))
v = actor(s, "hero", V, (0.5, 2.0), face=0, act="idle", eyes="happy", mouth="smile")
v.act(T_PRO - s.t0, "wave")
ks(s, [(s.t0, [0.6, 1.5, 6.0], [0.5, 1.3, 2.0], 46), (-1, [0.55, 1.5, 5.6], [0.5, 1.35, 2.0], 44)], focus="hero", ap=6)
cut.card("stat", T_PRO - 0.05, s.t1 - 0.03, text="«ПРИВЕТ»", label="ПРОСТО СКАЖИ", y=0.15, size=150, color="#ffd84a")
cut.sfx(T_PRO, "usr-notify-ding-mid-swell-102", -10)

s = cut.shot("zn_park", round(T_SME - 0.05, 3))
v = actor(s, "hero", V, (0.5, 2.0), face=0, act="idle", eyes="happy", mouth="smile")
v.act(0.1, "shrug")
ks(s, [(s.t0, [2.2, 2.6, 6.0], [0.4, 1.2, 1.0], 54), (-1, [2.0, 2.5, 5.6], [0.4, 1.2, 1.0], 52)], focus="hero", ap=3)
cut.card("strike", s.t0, s.t1 - 0.03, items=["ПОДКАТЫ", "ОЧКИ НОЧЬЮ", "КЛУМБА МЭРИИ"],
         at=[round(A("подкатов", after=T_BEZ8), 3), round(A("очков", after=T_BEZ8), 3), round(A("клумбы", after=T_BEZ8), 3)], y=0.13, size=80)
for wd in ("подкатов", "очков", "клумбы"):
    cut.sfx(A(wd, after=T_BEZ8), "usr-error-alert-mid-snap-078", -14)

T_GAID = A("гайд", after=T_SME)
s = cut.shot("zn_park", END_STORY)
v = actor(s, "hero", V, (-0.5, 4.0), face=180, act="idle", eyes="happy", mouth="smile")
lz = actor(s, "liza", L, (0.3, 4.0), face=180, act="idle", eyes="happy", mouth="smile")
v.walk(0.0, (-0.5, 4.0 - 1.3 * s.dur), dur=s.dur, e="linear")
lz.walk(0.0, (0.3, 4.0 - 1.3 * s.dur), dur=s.dur, e="linear")
zc = 4.0 - 0.65 * s.dur
ks(s, [(s.t0, [1.2, 1.5, 4.0 - 3.6], [-0.1, 1.2, 4.0], 50, "linear"), (-1, [1.2, 1.5, 4.0 - 1.3 * s.dur - 3.6], [-0.1, 1.2, 4.0 - 1.3 * s.dur], 50, "linear")],
   focus="hero", ap=4)
cut.card("stat", T_SME - 0.05, s.t1 - 0.03, text="СМЕЛОСТЬ + УЛЫБКА", label="ВЕСЬ ГАЙД", y=0.15, size=78, color="#ff8ab0")
cut.sfx(T_GAID, "usr-cinema-boom-low-tail-024", -10, dur=1.4)

# ======================================================== 9. CTA — soft «переходи в профиль», profile + support card (theme love)
t0 = ep.t
s = ep.shot("zn_park_n", round(END - t0, 3), tod="night")
actor(s, "hero", V, VK_B, face=60, act="sit", eyes="happy", mouth="smile", seat=0.46).act(0.3, "wave")
actor(s, "liza", L, LZ_B, face=120, act="sit", eyes="happy", mouth="smile", seat=0.46)
cam(s, [(0, [2.2, 1.5, 2.6], [-2.2, 1.0, 0.0], 48), (-1, [2.6, 1.6, 3.0], [-2.2, 1.0, 0.0], 50)], focus="hero", ap=4, zoom=False)
t_hl = A("профиль", after=S[9])
cut.card("black", t0, END, color="rgba(0,0,0,0.55)", fi=0.25, fo=0.01)
cut.card("profile", t0, END, hlAt=t_hl, theme="love")
ep.sfx(t_hl, "pk-notify-notification-sfx-1", -6)
# 15.11 rule: «поддержи лайком и подпиской», themed for this video and different from the last one (tupoy = frost):
# a broken heart heals on the like, the subscribe button is a valentine.
T_SUP = round(SEC[9]["end"] + 0.05, 3)
T_LIKE, T_SUB = round(T_SUP + 0.45, 3), round(T_SUP + 1.35, 3)
cut.card("support", T_SUP - 0.1, END, theme="love", title="ПОДДЕРЖИ ЛАЙКОМ И ПОДПИСКОЙ",
         likeCap="ВИТЬКУ НА ЦВЕТЫ\nНЕ С КЛУМБЫ", subCap="ЭТО ТОЖЕ ПОДКАТ,\nНО РАБОЧИЙ", likeAt=T_LIKE, subAt=T_SUB, y=0.625)
ep.sfx(T_LIKE, "usr-suction-pop-mid-snap-087", -9)
ep.sfx(T_LIKE + 0.05, "usr-notify-ding-bright-snap-105", -12)
ep.sfx(T_SUB - 0.03, "usr-mouse-double-bright-snap-069", -8)
ep.sfx(T_SUB + 0.12, "usr-notify-ding-mid-swell-102", -10)

# ----------------------------------------------------------------- sound: voice + ambience + SFX, NO music
ep.voice(0, copy_voice(KID, "znakomstva"), gain=0)
w.subs(ep, 0.3)
for sub, c in zip(ep.subs[-len(C):], C):
    sub["t1"] = round(min(sub["t1"], c["end"] + 0.8), 3)
ep.subs[-1]["t1"] = round(min(ep.subs[-1]["t1"], T_SUP - 0.12), 3)    # the like/subscribe block takes the caption place
ep.amb(0.0, T_RW, "shorts/street_day", gain=-28, fi=0.05, fo=0.2)
ep.amb(T_RW, S[2], "room-tone", gain=-32, fi=0.1, fo=0.2)
ep.amb(S[2], S[3], "room-tone", gain=-30, fi=0.1, fo=0.2)
ep.amb(S[3], S[4] + 0.0 if False else S[4], "city-hum", gain=-32, fi=0.2, fo=0.2)
ep.amb(S[4], S[5], "shorts/street_day", gain=-27, fi=0.2, fo=0.2)
ep.amb(S[5], S[6], "room-tone", gain=-32, fi=0.1, fo=0.2)
ep.amb(S[6], S[7], "shorts/street_day", gain=-28, fi=0.2, fo=0.2)
ep.amb(S[7], END, "city-hum", gain=-36, fi=0.2, fo=1.0)
ep.save()
print(f"znak: {ep.t:.2f}s, {len(ep.shots)} shots")
