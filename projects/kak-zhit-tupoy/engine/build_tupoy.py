"""«Как жить, если ты тупой» — vertical PIXCINE short (1080×1920), 11.11.2026.
mike: «сделай резче», «юмористичный, а не познавательный», TikTok only in passing, «сделай что нибудь смешное епта,
можешь маты добавить», «делай грязь»; places: home, school, shop, street. Format of the approved «Тестостерон» v2:
hook-teaser of the finale in the first second (Витёк with his tongue frozen to a lamp post, a crowd filming), rewind,
voice MiniMax Russian_ReliableMan ×1.35, section gaps ≤ 0.9 s, no music (ambience + SFX), CTA to the profile header.
«Резче»: a cut every 1.5–2.5 s, whip/zoom hits on every punchline."""
import json
import math

from common_sh import K, Cut, Ep, H, W, Words, cam, copy_voice, narration, save_loc

KID = "tupoy"
w = Words(KID)
C = w.cards
SEC = {int(r["id"]): r for r in json.loads((narration(KID) / "sections.json").read_text(encoding="utf-8"))}
S = {k: v["start"] for k, v in SEC.items()}
A = w.at
END_STORY = round(S[9] - 0.05, 3)
END = round(w.duration + 0.9, 3)
V = "geroy"            # Витёк
VW = "vitek_w"         # Витёк in a winter beanie

# ----------------------------------------------------------------- sets
POLE = (-4.5, 0.0)                     # «тот самый столб»: lamp post on the left sidewalk
TONGUE_AT = (-3.98, 0.0)               # where Витёк stands (facing -x) with his tongue on the pole


def winter(id, tod="dusk"):
    """snowy evening street: road along z, lamps lit, shop signs, parked cars, snowdrifts, other idiots on other poles"""
    P = [{"t": "road", "p": [0, 0], "w": 8, "len": 160, "zebraZ": 9, "color": "#4a4a52"}]
    cols = ["#8a7e72", "#7a8a8e", "#9a7a62", "#7e7a8a", "#9a8a72", "#7a7e86", "#8a6e60", "#888070"]
    for side in (-1, 1):
        for i, z in enumerate([-50, -38, -26, -14, -2, 10, 22, 34]):
            P.append({"t": "building", "p": [side * 12, z], "r": 90 if side < 0 else -90, "w": 11, "d": 9, "floors": 5 + (i * 3 + (side > 0) * 2) % 5,
                      "seed": 60 + i + (side > 0) * 10, "color": cols[(i + (side > 0) * 3) % len(cols)], "lit": 0.55})
    for side, z, txt, bg in [(-1, -14, "ПРОДУКТЫ 24", "#2a4a8a"), (-1, -2, "ШАУРМА", "#c84a2a"), (-1, 10, "АПТЕКА", "#2a8a4a"),
                             (1, -14, "ЛОМБАРД", "#8a7a2a"), (1, -2, "ПИВО", "#c8902a"), (1, 10, "САЛОН СВЯЗИ", "#3a6aa8")]:
        P.append({"t": "shopSign", "p": [side * 7.42, z], "y": 3.3, "r": 90 if side < 0 else -90, "w": min(5.2, 0.55 * len(txt) + 0.8), "h": 0.8,
                  "text": txt, "bg": bg, "glow": 1.1})
    for i, z in enumerate([-36, -24, -12, 0, 12, 24]):
        P.append({"t": "streetLamp", "p": [-4.5, z], "r": 0, "on": True})
        P.append({"t": "streetLamp", "p": [4.5, z + 6], "r": 180, "on": True})
    for x, z, r, c in [(-3.2, -20, 0, "#3a6ab8"), (-3.2, 18, 0, "#d8d8d8"), (3.2, -8, 180, "#e0b020"), (3.2, 14, 180, "#8a2a2a")]:
        P.append({"t": "car", "p": [x, z], "r": r, "color": c})
    for i, z in enumerate([-30, -18, -6, 6, 18, 30]):          # snowdrifts along the curbs
        for side in (-1, 1):
            P.append({"t": "block", "p": [side * (5.6 + (i % 2) * 0.4), z + side * 2], "size": [1.6, 0.35 + (i % 3) * 0.1, 2.6], "color": "#e8eef6", "solid": False})
    P += [{"t": "tree", "p": [-6.4, -9], "s": 0.75}, {"t": "tree", "p": [6.4, 3], "s": 0.75}, {"t": "tree", "p": [-6.4, 15], "s": 0.75},
          {"t": "bench", "p": [6.6, -4], "r": -90}, {"t": "crows", "p": [5.4, 8], "n": 4, "spread": 2.0, "color": "#7a808c"},
          {"t": "building", "p": [0, -72], "w": 40, "d": 10, "floors": 12, "seed": 80, "lit": 0.5, "color": "#7a7680"}]
    save_loc({"id": id, "tod": tod, "fog": 0.02, "ground": {"tex": "concrete", "opts": {"color": "#dfe6ee", "lines": False}, "size": [240, 240]},
              "props": P, "particles": [{"kind": "snow", "n": 420, "box": [-8, 0.2, -16, 8, 7, -1.5]}]})


winter("tp_winter")
save_loc({"id": "tp_bath", "interior": True, "tod": "interior_day",
          "props": [{"t": "room", "p": [0, 0], "w": 3.4, "d": 3.0, "h": 2.6, "wall": "tiles", "wallOpts": {"color": "#b8d0d8"}, "floor": "floor_tiles",
                     "floorOpts": {"a": "#d8dcdc", "b": "#a8b0b4"}, "ceiling": False},
                    {"t": "sink", "p": [0.0, -1.2]},
                    {"t": "block", "p": [0.0, -1.47], "y": 1.15, "size": [0.8, 0.7, 0.04], "tex": "metal", "color": "#c8dce8"},          # mirror
                    {"t": "block", "p": [1.2, -1.2], "size": [0.6, 0.9, 0.5], "tex": "white", "color": "#e8ecec"},                       # washing machine
                    {"t": "block", "p": [-1.35, -0.6], "size": [0.6, 0.45, 1.5], "tex": "white", "color": "#f0f2f2"},                    # bath tub
                    {"t": "block", "p": [0.32, -1.32], "y": 0.86, "size": [0.08, 0.06, 0.18], "color": "#141414"},                     # shoe polish tube
                    {"t": "block", "p": [0.18, -1.3], "y": 0.86, "size": [0.05, 0.14, 0.05], "color": "#e84a4a"},                      # cup
                    {"t": "aptDoor", "p": [1.0, 1.48], "r": 180, "num": "", "color": "#e8e2d4"},
                    {"t": "lightPt", "p": [0, -0.6], "y": 2.4, "i": 3.5, "d": 7, "color": "#f4f8ff"}],
          "fog": 0.01, "hemi": ["#d0dce4", "#3a4044", 0.8]})
MICRO = (1.2, -1.45)
save_loc({"id": "tp_kitchen", "interior": True, "tod": "interior_day",
          "props": [{"t": "room", "p": [0, 0], "w": 4.4, "d": 3.6, "h": 2.7, "wall": "tiles", "wallOpts": {"color": "#c8d4c0"}, "floor": "lino",
                     "floorOpts": {"color": "#6a5a4a"}, "ceiling": False},
                    {"t": "block", "p": [0.6, -1.45], "size": [2.6, 0.9, 0.6], "tex": "wood", "color": "#8a6a4a"},                       # worktop
                    {"t": "sink", "p": [-0.4, -1.45]},
                    {"t": "block", "p": [MICRO[0], MICRO[1]], "y": 0.9, "size": [0.6, 0.36, 0.42], "tex": "white", "color": "#d8dcdc"},   # microwave
                    {"t": "block", "p": [MICRO[0] - 0.06, MICRO[1] + 0.215], "y": 0.97, "size": [0.36, 0.22, 0.01], "color": "#ffd88a"},  # its lit window
                    {"t": "block", "p": [-1.75, -1.4], "size": [0.75, 1.95, 0.7], "tex": "white", "color": "#e8ecec"},                    # fridge
                    {"t": "table", "p": [-1.3, 0.7]}, {"t": "stool", "p": [-1.3, 1.3]},
                    {"t": "windowModern", "p": [0.0, -1.78], "y": 1.75, "w": 0.9, "h": 0.8, "morning": True},
                    {"t": "bulb", "p": [0, 0], "y": 2.7, "len": 0.4, "i": 4, "d": 7}],
          "fog": 0.012, "hemi": ["#d8d0c0", "#3a3028", 0.75]})
DESKS = [(x, z) for z in (0.2, 1.6) for x in (-2.0, 0.0, 2.0)]
VDESK = (0.0, 1.6)                      # Витёк's desk (second row, middle)
save_loc({"id": "tp_school", "interior": True, "tod": "interior_day",
          "props": [{"t": "room", "p": [0, 0], "w": 7.0, "d": 6.0, "h": 3.0, "wall": "plaster", "wallOpts": {"color": "#a8b890"}, "floor": "parquet", "ceiling": False},
                    {"t": "screenBoard", "p": [0.0, -2.96], "y": 1.75, "w": 3.2, "h": 1.3, "title": "МАТЕМАТИКА", "rows": ["7 × 8 = ?"], "color": "#1e3a2a"},
                    {"t": "block", "p": [-1.5, -2.2], "size": [1.2, 0.76, 0.6], "tex": "wood", "color": "#6a4a2a"},                     # teacher's desk
                    *[{"t": "table", "p": [x, z]} for x, z in DESKS],
                    *[{"t": "stool", "p": [x, z + 0.55]} for x, z in DESKS],
                    {"t": "windowModern", "p": [-3.48, 0.0], "y": 1.6, "r": 90, "w": 1.6, "h": 1.2, "morning": True},
                    {"t": "windowModern", "p": [-3.48, 2.2], "y": 1.6, "r": 90, "w": 1.6, "h": 1.2, "morning": True},
                    {"t": "aptDoor", "p": [3.48, -1.8], "r": -90, "num": "5Б", "color": "#7a5a3a"},
                    {"t": "poster", "p": [2.0, -2.98], "y": 1.7, "v": 1}, {"t": "shelf", "p": [3.0, 2.2], "r": -90, "s": 0.8},
                    {"t": "lightPt", "p": [0, 0.5], "y": 2.8, "i": 3.5, "d": 10, "color": "#f4f0dc"}],
          "fog": 0.01, "hemi": ["#d8d0b8", "#3a3428", 0.8]})
DOOR = (0.0, -4.5)                      # shop entrance (glass door) in the facade at z=-5
save_loc({"id": "tp_shop", "tod": "day",
          "props": [{"t": "building", "p": [0, -10], "w": 14, "d": 10, "floors": 4, "seed": 90, "color": "#8a8a7e", "day": True},
                    {"t": "shopSign", "p": [0, -4.93], "y": 3.1, "w": 4.6, "h": 0.9, "text": "ПРОДУКТЫ", "bg": "#2a6a3a", "glow": 0.6},
                    {"t": "block", "p": [0, -4.98], "size": [1.5, 2.3, 0.06], "tex": "metal", "color": "#4a5a6a", "solid": False},             # door frame
                    {"t": "block", "p": [0, -4.94], "y": 0.1, "size": [1.3, 2.05, 0.03], "color": "#a8d4ec", "solid": False},               # glass
                    {"t": "shopSign", "p": [0, -4.9], "y": 1.45, "w": 0.95, "h": 0.32, "text": "ОТ СЕБЯ", "bg": "#c83a2a", "glow": 0.5},
                    {"t": "block", "p": [0.5, -4.88], "y": 0.95, "size": [0.06, 0.4, 0.06], "tex": "metal", "color": "#d8d8d8", "solid": False},  # handle
                    {"t": "block", "p": [-2.6, -4.96], "y": 0.6, "size": [2.6, 1.8, 0.04], "color": "#a8d4ec", "solid": False},               # shop windows
                    {"t": "block", "p": [2.6, -4.96], "y": 0.6, "size": [2.6, 1.8, 0.04], "color": "#a8d4ec", "solid": False},
                    {"t": "shopSign", "p": [-2.6, -4.9], "y": 1.6, "w": 2.0, "h": 0.5, "text": "АКЦИЯ -50%", "bg": "#e0b020", "glow": 0.4},
                    {"t": "road", "p": [0, 6], "r": 90, "w": 7, "len": 80, "color": "#4a4a52"},
                    {"t": "streetLamp", "p": [-4.0, -3.0], "on": False}, {"t": "bench", "p": [3.8, -3.6]},
                    {"t": "block", "p": [-5.5, -3.6], "size": [2.0, 0.4, 1.2], "color": "#e8eef6", "solid": False},
                    {"t": "block", "p": [5.5, -2.0], "size": [1.6, 0.35, 1.4], "color": "#e8eef6", "solid": False},
                    {"t": "car", "p": [-2.4, 4.6], "r": 90, "color": "#3a6ab8"}, {"t": "car", "p": [4.0, 7.6], "r": -90, "color": "#d8d8d8"},
                    {"t": "crows", "p": [3.6, -3.0], "n": 3, "spread": 1.0, "color": "#7a808c"}],
          "fog": 0.012, "ground": {"tex": "concrete", "opts": {"color": "#dfe6ee", "lines": False}, "size": [160, 160]},
          "particles": [{"kind": "snow", "n": 260, "box": [-6, 0.2, -6, 6, 6, 2]}]})

# ----------------------------------------------------------------- episode
ep = Ep("shorts", "tupoy", fps=30, w=W, h=H)
cut = Cut(ep, w)


def actor(s, id, char, at, face=0, act="idle", eyes=None, mouth=None, **arg):
    a = s.actor(id, char, at=at, face=face)
    a.act(0, act, **arg)
    if eyes or mouth:
        a.expr(0, eyes, mouth)
    return a


MIN_D = 3.4


def ks(s, keys, focus=None, ap=None, hh=None):
    """explicit camera keys in GLOBAL time: [(t, pos, look, fov[, ease]), …]; t = -1 → end of shot (no portrait zoom)"""
    out = []
    for i, (t, p, l, f, *rest) in enumerate(keys):
        d = math.dist(p, l)
        if d < MIN_D:                       # pixel dolls are big: a «close-up» needs ≥ 2.6 m (lesson of testosteron v2)
            p = [l[j] + (p[j] - l[j]) * MIN_D / max(d, 0.05) for j in range(3)]
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


def splats(origin, n, spread, seed=1, t=None, color="#f2c418", y=(0.3, 2.2), size=0.22):
    """flat yellow yolk splats stuck on walls / floor (appear at t)"""
    out = []
    for i in range(n):
        h1 = math.sin(seed * 12.9898 + i * 78.233) * 43758.5453
        h2 = math.sin(seed * 39.3468 + i * 11.135) * 24634.6345
        r1, r2 = h1 - math.floor(h1), h2 - math.floor(h2)
        x, z = origin[0] + (r1 - 0.5) * spread[0], origin[1] + (r2 - 0.5) * spread[1]
        sz = size * (0.5 + r2)
        b = {"t": "block", "p": [round(x, 3), round(z, 3)], "y": round(y[0] + (y[1] - y[0]) * r2, 3), "size": [round(sz, 3), round(sz * 0.8, 3), round(sz, 3)],
             "color": color if i % 4 else "#f8f0d8", "solid": False}
        if t is not None:
            b["showAt"] = round(t, 3)
        out.append(b)
    return out


TONGUE = {"t": "block", "p": [-4.3, 0.0], "y": 1.5, "size": [0.36, 0.035, 0.07], "color": "#e86a7a", "solid": False}
FROST = {"t": "lightPt", "p": [-4.4, 0.6], "y": 1.6, "i": 0.7, "d": 2.5, "color": "#a8d8ff"}
CROWD = [(-5.6, 2.6, "p1", 150), (-3.0, 2.8, "p3", -150), (-2.6, 1.0, "p4", -110), (-5.8, -1.8, "p2", 30), (-2.8, -1.6, "p5", -40), (-6.0, 1.0, "p6", 100)]


def stuck(s, char=VW, eyes="wide", mouth="o"):
    """Витёк frozen to the pole: facing the pole (-x), tongue block between his mouth and the lamp post"""
    v = actor(s, "hero", char, TONGUE_AT, face=-90, act="struggle", eyes=eyes, mouth=mouth)
    extra(s, TONGUE, FROST)
    return v


def crowd(s, n=6, film=True, flashes=None):
    for i, (x, z, ch, f) in enumerate(CROWD[:n]):
        a = actor(s, f"c{i}", ch, (x, z), face=f, act="phone_up" if film else "idle")
        if film:
            a.hold(0, B="phone")
    if flashes:
        for k, t in enumerate(flashes):
            extra(s, {"t": "lightPt", "p": [CROWD[k % n][0], CROWD[k % n][1]], "y": 1.6, "i": 6, "d": 4, "color": "#ffffff",
                      "blink": {"t0": round(t - s.t0, 3), "on": 0.06, "off": 9.0}})


# ======================================================== 1. HOOK — teaser: tongue frozen to the lamp post, everybody films
T_TUP = A("тупой")
s = cut.shot("tp_winter", round(A("Спокойно") - 0.05, 3), tod="dusk")
stuck(s)
crowd(s, 6, flashes=[0.4, 0.9, 1.3])
ks(s, [(0.0, [-3.0, 1.7, 5.4], [-4.2, 1.45, 0.0], 44), (T_TUP, [-4.0, 1.55, 3.6], [-4.2, 1.5, 0.0], 42), (-1, [-4.05, 1.55, 3.4], [-4.2, 1.5, 0.0], 42)],
   focus="hero", ap=6)
hit(s, T_TUP, 0.05)
cut.sfx(0.0, "usr-whoosh-roar-low-swell-322", -6)
cut.sfx(T_TUP, "hit-cinematic", -7)
for t in (0.4, 0.9, 1.3):
    cut.sfx(t, "usr-photo-shutter-bright-snap-001", -10)

T_NAS = A("Нас")
s = cut.shot("tp_winter", round(T_NAS - 0.05, 3), tod="dusk")
stuck(s)
crowd(s, 6, flashes=[s.t0 + 0.3, s.t0 + 0.8, s.t0 + 1.2, s.t0 + 1.6])
orbit(s, (-4.2, 0.4), 5.2, 1.4, 40, -20, 1.2, 50, focus="hero", ap=3, h1=2.2)
for t in (0.3, 0.8, 1.2, 1.6):
    cut.sfx(s.t0 + t, "usr-photo-shutter-bright-swell-106", -12)
cut.sfx(A("один"), "usr-crowd-gasp-mid-swell-172", -14)

# «Нас дохуя»: crane up — every lamp post down the street has its own idiot on it
s = cut.shot("tp_winter", round(C[1]["start"] - 0.05, 3), tod="dusk")
stuck(s)
for i, z in enumerate([-12, -24, -36]):
    actor(s, f"d{i}", ["p1", "p3", "p5"][i], (-3.98, z), face=-90, act="struggle", eyes="wide", mouth="o")
    extra(s, {**TONGUE, "p": [-4.3, z]})
for i, z in enumerate([6, -6, -18]):
    actor(s, f"e{i}", ["p4", "p2", "sosed"][i], (3.98, z), face=90, act="struggle", eyes="wide", mouth="o")
    extra(s, {**TONGUE, "p": [4.3, z]})
ks(s, [(s.t0, [-1.0, 1.4, 4.0], [-4.0, 1.4, -4.0], 50), (-1, [0.0, 6.5, 9.5], [0.0, 1.0, -16.0], 54)], focus=None, ap=1)
cut.card("stat", T_NAS - 0.05, s.t1 - 0.03, text="ДОХУЯ", label="НАС", y=0.17, size=160)
cut.sfx(T_NAS, "usr-whoosh-build-hit-mid-late-086", -8)

# «Вот Витёк» — freeze on him
T_VOT = C[1]["start"]
T_LIZ = A("лизнул")
s = cut.shot("tp_winter", round(T_LIZ - 0.08, 3), tod="dusk")
stuck(s, eyes="wide", mouth="o")
ks(s, [(s.t0, [-3.6, 1.6, 3.4], [-4.1, 1.5, 0.0], 42), (-1, [-3.7, 1.58, 3.2], [-4.1, 1.5, 0.0], 42)], focus="hero", ap=12)
cut.card("label", T_VOT - 0.03, s.t1 - 0.03, text="ВИТЁК", sub="IQ: ПРИМЕРНО 12", x=0.06, y=0.15, border="#ffd84a")
cut.sfx(T_VOT, "usr-record-scratch" if False else "usr-whoosh-whip-mid-snap-135", -8)
cut.sfx(T_VOT + 0.05, "usr-voice-bruh-mid-swell-097", -12)

T_M20 = A("минус")
s = cut.shot("tp_winter", round(A("И", after=T_M20) - 0.08, 3), tod="dusk")
stuck(s)
crowd(s, 4)
ks(s, [(s.t0, [-4.1, 3.6, 2.8], [-4.2, 1.2, 0.0], 44), (-1, [-4.0, 2.6, 2.4], [-4.2, 1.3, 0.0], 40)], focus="hero", ap=4)
cut.card("stat", T_M20 - 0.05, s.t1 - 0.03, text="−20°", label="ЛИЗНУЛ СТОЛБ", y=0.17, size=170, color="#7ad0ff")
cut.sfx(T_M20, "usr-whoosh-light-bright-swell-200", -10)

# «И это не самое тупое за сегодня» — slow push in, then the rewind to the morning
s = cut.shot("tp_winter", S[2], tod="dusk")
stuck(s, eyes="sad", mouth="o")
crowd(s, 6)
ks(s, [(s.t0, [-2.6, 1.3, 5.2], [-4.2, 1.45, 0.0], 46), (-1, [-3.6, 1.45, 3.6], [-4.2, 1.5, 0.0], 42)], focus="hero", ap=6)
cut.sfx(A("тупое", after=T_M20), "usr-suspense-sting", -12)
T_RW = S[2]
flash(T_RW, 0.16)
cut.card("label", T_RW, T_RW + 1.2, text="◀◀ ПЕРЕМОТКА", sub="7:30 УТРА", x=0.06, y=0.15, border="#ff4a2a")
cut.sfx(T_RW - 0.12, "usr-tape-rewind-mid-swell-049", -5, dur=0.9)

# ======================================================== 2. Bathroom — shoe polish instead of toothpaste
T_KREM = A("кремом")
s = cut.shot("tp_bath", round(C[3]["start"] - 0.05, 3))
s.fxk(0.0, "zoomblur", d=0.35, v=0.5)
v = actor(s, "hero", V, (0.0, -0.55), face=0, act="idle", eyes="closed", mouth="closed")
v.act(A("чистит") - s.t0, "hammer")
v.expr(A("чистит") - s.t0, "normal", "grit")
ks(s, [(s.t0, [1.2, 1.8, 3.6], [0.0, 1.4, -0.55], 46), (-1, [0.6, 1.65, 3.0], [0.0, 1.45, -0.55], 42)], focus="hero", ap=6)
cut.card("label", T_KREM - 0.05, s.t1 - 0.03, text="КРЕМ ДЛЯ ОБУВИ", sub="ЧЁРНЫЙ", x=0.06, y=0.15)
cut.sfx(A("чистит"), "usr-whoosh-light-mid-snap-221", -12)
cut.sfx(A("чистит") + 0.35, "usr-whoosh-light-mid-snap-223", -12)
cut.sfx(T_KREM, "usr-voice-bruh-mid-swell-178", -12)

T_BL = A("блестят")
s = cut.shot("tp_bath", round(C[4]["start"] - 0.05, 3))
v = actor(s, "hero", V, (0.0, -0.55), face=20, act="idle", eyes="happy", mouth="smile")
extra(s, {"t": "lightPt", "p": [0.1, -0.1], "y": 1.5, "i": 3, "d": 1.6, "color": "#ffffff", "blink": {"t0": round(T_BL - s.t0, 3), "on": 0.2, "off": 0.35}})
ks(s, [(s.t0, [0.15, 1.62, 1.1], [0.0, 1.55, -0.55], 30), (-1, [0.1, 1.6, 0.85], [0.0, 1.56, -0.55], 26)], focus="hero", ap=14)
cut.sfx(T_BL, "usr-notify-ding-bright-snap-105", -8)
cut.card("stat", A("ботинками") - 0.05, s.t1 - 0.03, text="АРОМАТ", label="СТАРЫЙ БОТИНОК", y=0.17, size=130, color="#c89a5a")
cut.sfx(A("ботинками"), "usr-comic-fart-mid-snap-062", -10)

T_DEB = A("дебил")
T_CH = A("Частично")
s = cut.shot("tp_bath", round(T_CH - 0.1, 3))
v = actor(s, "hero", V, (-0.5, -0.55), face=30, act="idle", eyes="normal", mouth="smile")
m = actor(s, "mama", "mama", (0.8, 0.5), face=-30, act="idle", eyes="angry", mouth="closed")
m.act(T_DEB - s.t0 - 0.2, "shout"); m.expr(T_DEB - s.t0 - 0.2, "angry", "shout")
m.talk(A("Ты", after=C[4]["start"]) - s.t0, A("блядь", end=True) - s.t0)
ks(s, [(s.t0, [-0.2, 1.7, 4.2], [0.3, 1.45, 0.0], 48), (-1, [0.0, 1.65, 3.8], [0.5, 1.5, 0.2], 46)], focus="mama", ap=4)
cut.card("bubble", T_DEB - 0.25, s.t1 - 0.03, who="МАМА", whoColor="#ff8ad0", text="Ты дебил, блядь?", y=0.15, side="right")
cut.sfx(T_DEB, "usr-boxing-bell-mid-snap-076", -12)

s = cut.shot("tp_bath", S[3])
v = actor(s, "hero", V, (-0.5, -0.55), face=10, act="shrug", eyes="normal", mouth="smile")
v.talk(T_CH - s.t0, A("Частично", end=True) - s.t0)
ks(s, [(s.t0, [-0.4, 1.62, 2.9], [-0.5, 1.55, -0.55], 42), (-1, [-0.45, 1.6, 2.7], [-0.5, 1.56, -0.55], 42)], focus="hero", ap=12)
cut.card("bubble", T_CH - 0.05, s.t1 - 0.03, who="ВИТЁК", whoColor="#ffd84a", text="Частично.", y=0.15, side="left")
cut.sfx(T_CH + 0.5, "usr-cartoon-bloop-mid-snap-061", -10)

# ======================================================== 3. Kitchen — egg in the microwave
T_EGG = A("микроволновку")
T_BAH = round(A("Бабах") - 0.02, 3)
s = cut.shot("tp_kitchen", round(T_BAH - 0.05, 3))
s.fxk(0.0, "zoomblur", d=0.3, v=0.5)
v = actor(s, "hero", V, (0.45, -0.8), face=90, act="idle", eyes="happy", mouth="smile")
v.act(T_EGG - s.t0 - 0.2, "point")
extra(s, {"t": "block", "p": [MICRO[0] - 0.06, MICRO[1]], "y": 0.98, "size": [0.07, 0.09, 0.07], "color": "#f8f4e8", "solid": False, "hideAt": round(T_EGG + 0.3, 3)})
ks(s, [(s.t0, [0.9, 1.6, 3.2], [0.85, 1.2, -1.1], 46), (-1, [1.0, 1.4, 2.4], [1.0, 1.15, -1.2], 42)], focus="hero", ap=4)
cut.sfx(T_EGG, "usr-click-pop-bright-snap-215", -10)
cut.sfx(T_EGG + 0.2, "terminal-hum", -14, dur=1.0)

YOLK_K = splats((0.2, -0.4), 26, (4.0, 2.6), seed=3) + splats((0.2, -1.75), 14, (4.2, 0.1), seed=5, y=(0.9, 2.4))
s = cut.shot("tp_kitchen", round(A("кот", after=T_BAH) - 0.08, 3))
v = actor(s, "hero", V, (0.45, -0.8), face=90, act="idle", eyes="happy", mouth="smile")
v.act(0.04, "fall")
v.expr(0.04, "wide", "o")
extra(s, *splats((0.2, -0.4), 26, (4.0, 2.6), seed=3, t=T_BAH), *splats((0.2, -1.75), 14, (4.2, 0.1), seed=5, y=(0.9, 2.4), t=T_BAH),
      {"t": "lightPt", "p": [MICRO[0], MICRO[1] + 0.4], "y": 1.1, "i": 9, "d": 5, "color": "#ffd060", "blink": {"t0": 0.0, "on": 0.14, "off": 99}})
ks(s, [(s.t0, [-1.2, 1.9, 1.6], [0.6, 1.0, -0.8], 56), (-1, [-1.0, 1.8, 1.5], [0.4, 1.0, -0.8], 54)], focus=None, ap=1)
hit(s, T_BAH, 0.12, 0.6)
flash(T_BAH, 0.12, "#fff2a0")
cut.sfx(T_BAH, "nuke-boom", -9, dur=1.4)
cut.sfx(T_BAH + 0.05, "usr-cartoon-splat-low-swell-046", -6)
cut.card("label", A("Кухня") - 0.05, s.t1 - 0.03, text="КУХНЯ: В ЖЕЛТКЕ", x=0.06, y=0.15, border="#f2c418")

# the cat (pixel blocks), all yellow
CAT = [{"t": "block", "p": [-1.3, 0.75], "y": 0.78, "size": [0.42, 0.2, 0.2], "color": "#e8b018", "solid": False},
       {"t": "block", "p": [-1.08, 0.75], "y": 0.93, "size": [0.17, 0.16, 0.17], "color": "#e8b018", "solid": False},
       {"t": "block", "p": [-1.04, 0.69], "y": 1.06, "size": [0.04, 0.07, 0.04], "color": "#e8b018", "solid": False},
       {"t": "block", "p": [-1.04, 0.81], "y": 1.06, "size": [0.04, 0.07, 0.04], "color": "#e8b018", "solid": False},
       {"t": "block", "p": [-1.0, 0.71], "y": 0.97, "size": [0.02, 0.03, 0.03], "color": "#101010", "solid": False},
       {"t": "block", "p": [-1.0, 0.79], "y": 0.97, "size": [0.02, 0.03, 0.03], "color": "#101010", "solid": False},
       {"t": "block", "p": [-1.55, 0.75], "y": 0.9, "size": [0.05, 0.28, 0.05], "color": "#e8b018", "solid": False}]
s = cut.shot("tp_kitchen", round(A("мама", after=T_BAH) - 0.08, 3))
extra(s, *YOLK_K, *CAT)
ks(s, [(s.t0, [-0.2, 1.05, 1.0], [-1.15, 0.92, 0.75], 34), (-1, [-0.35, 1.0, 0.95], [-1.15, 0.92, 0.75], 30)], focus=None, ap=10)
cut.card("label", A("кот", after=T_BAH) - 0.05, s.t1 - 0.03, text="КОТ: В ЖЕЛТКЕ", x=0.06, y=0.15, border="#f2c418")
cut.sfx(A("кот", after=T_BAH), "usr-cartoon-bloop-low-swell-284", -8)

s = cut.shot("tp_kitchen", round(C[7]["start"] - 0.05, 3))
extra(s, *YOLK_K, *CAT, *splats((-0.3, 0.6), 7, (0.5, 0.2), seed=9, y=(1.2, 1.85), size=0.16))
m = actor(s, "mama", "mama", (-0.3, 0.55), face=20, act="facepalm", eyes="angry", mouth="grit")
ks(s, [(s.t0, [0.2, 1.6, 2.4], [-0.3, 1.45, 0.55], 34), (-1, [0.1, 1.6, 2.1], [-0.3, 1.5, 0.55], 32)], focus="mama", ap=10)
cut.card("label", A("мама", after=T_BAH) - 0.05, s.t1 - 0.03, text="МАМА: В ЖЕЛТКЕ", x=0.06, y=0.15, border="#f2c418")
cut.sfx(A("мама", after=T_BAH), "usr-voice-bruh-mid-swell-226", -10)

T_ZAM = A("заметки")
s = cut.shot("tp_kitchen", S[4])
extra(s, *YOLK_K)
v = actor(s, "hero", V, (0.3, 0.2), face=20, act="phone_up", eyes="normal", mouth="closed")
v.hold(0, B="phone")
ks(s, [(s.t0, [0.4, 1.6, 1.7], [0.3, 1.5, 0.2], 36), (-1, [0.4, 1.55, 1.5], [0.3, 1.5, 0.2], 34)], focus="hero", ap=10)
cut.card("phone", T_ZAM - 0.4, S[4] - 0.02, app="ЗАМЕТКИ", clock="07:42", signal="LTE", battery="12%",
         msgs=[{"t": round(A("Яйца", after=T_ZAM) - T_ZAM + 0.3, 3), "who": "me", "text": "ЯЙЦА — ОПАСНЫЕ!!!"}])
cut.sfx(T_ZAM, "typing-short", -10)

# ======================================================== 4. School — 7 × 8
s = cut.shot("tp_school", round(C[9]["start"] - 0.05, 3))
s.fxk(0.0, "zoomblur", d=0.3, v=0.5)
v = actor(s, "hero", V, (VDESK[0], VDESK[1] + 0.5), face=180, act="sit", eyes="normal", mouth="smile", seat=0.46)
for i, (x, z) in enumerate([d for d in DESKS if d != VDESK]):
    actor(s, f"k{i}", ["odnokl", "p2", "p4", "p6", "p1"][i], (x, z + 0.5), face=180, act="sit", seat=0.46)
ks(s, [(s.t0, [2.4, 3.6, 4.6], [0.0, 0.9, 0.6], 54), (-1, [1.2, 2.8, 4.4], [0.0, 1.0, 1.4], 48)], focus="hero", ap=3)
cut.card("label", A("легенда") - 0.05, s.t1 - 0.03, text="ЛЕГЕНДА", sub="5 КЛАСС, 3-Й ГОД", x=0.06, y=0.15, border="#ffd84a")
cut.sfx(C[8]["start"], "usr-boxing-bell-mid-tail-109", -14)
cut.sfx(A("легенда"), "usr-brass-swell-mid-tail-146", -10)

T_78 = A("Семь")
T_SED = A("седеет")
s = cut.shot("tp_school", round(A("Витёк", after=T_78) - 0.08, 3))
u = actor(s, "teacher", "uchitel", (1.0, -2.3), face=0, act="point", eyes="normal", mouth="closed")
u.talk(T_78 - s.t0, A("восемь", after=T_78, end=True) - s.t0)
ks(s, [(s.t0, [0.4, 1.6, 0.6], [0.6, 1.6, -2.5], 46), (-1, [0.5, 1.6, 0.2], [0.7, 1.6, -2.5], 42)], focus="teacher", ap=6)
cut.card("bubble", T_78 - 0.05, s.t1 - 0.03, who="УЧИТЕЛЬ", whoColor="#9ad0ff", text="Семь на восемь?", y=0.15, side="left")

s = cut.shot("tp_school", round(T_SED - 0.1, 3))
v = actor(s, "hero", V, (VDESK[0], VDESK[1] + 0.5), face=180, act="think", eyes="normal", mouth="closed", seat=0.46)
ks(s, [(s.t0, [0.0, 1.35, -0.3], [0.0, 1.2, 2.1], 34), (-1, [0.0, 1.3, -0.1], [0.0, 1.2, 2.1], 30)], focus="hero", ap=10)
cut.card("stat", A("думает", after=T_78) - 0.05, s.t1 - 0.03, **{"from": 0, "to": 47, "rollAt": A("думает", after=T_78), "rollDur": 1.4},
         label="МИНУТ ДУМАЕТ", y=0.17, size=160)
cut.sfx(A("думает", after=T_78), "heartbeat", -6, dur=1.6)

s = cut.shot("tp_school", round(C[10]["start"] - 0.05, 3))
u0 = actor(s, "teacher0", "uchitel", (1.0, -2.3), face=0, act="arms_crossed", eyes="normal", mouth="closed")
u0.show(T_SED - s.t0 + 0.15, False)
u1 = actor(s, "teacher", "uchitel_s", (1.0, -2.3), face=0, act="arms_crossed", eyes="sad", mouth="closed")
u1.show(0, False); u1.show(T_SED - s.t0 + 0.15, True)
ks(s, [(s.t0, [1.0, 1.65, -0.5], [1.0, 1.6, -2.3], 32), (-1, [1.0, 1.65, -0.8], [1.0, 1.62, -2.3], 30)], focus="teacher", ap=12)
flash(T_SED + 0.15, 0.1)
cut.card("label", T_SED - 0.05, s.t1 - 0.03, text="БОРОДА: СЕДАЯ", sub="+40 ЛЕТ", x=0.06, y=0.15)
cut.sfx(T_SED + 0.15, "usr-whoosh-light-bright-swell-200", -9)

T_40 = C[10]["start"]
T_PEN = A("пенсию")
s = cut.shot("tp_school", round(A("Учитель", after=T_40) - 0.08, 3))
v = actor(s, "hero", V, (VDESK[0], VDESK[1] + 0.5), face=180, act="think", eyes="normal", mouth="o", seat=0.46)
v.talk(T_40 - s.t0, A("восемь", after=T_40, end=True) - s.t0)
ks(s, [(s.t0, [0.15, 1.3, -0.1], [0.0, 1.22, 2.1], 30), (-1, [0.1, 1.28, 0.1], [0.0, 1.22, 2.1], 26)], focus="hero", ap=12)
cut.card("bubble", T_40 - 0.05, s.t1 - 0.03, who="ВИТЁК", whoColor="#ffd84a", text="Сорок... семь... восемь?", y=0.15, side="left")
cut.sfx(A("семь", after=T_40), "usr-error-alert-mid-snap-078", -12)

s = cut.shot("tp_school", S[5])
u = actor(s, "teacher", "uchitel_s", (1.0, -2.3), face=90, act="idle", eyes="sad", mouth="closed")
u.walk(0.1, (3.1, -1.8), dur=round(s.dur - 0.2, 3))
ks(s, [(s.t0, [-1.5, 1.8, 2.8], [1.8, 1.2, -2.0], 50), (-1, [-1.2, 1.8, 2.6], [2.4, 1.2, -1.9], 48)], focus="teacher", ap=3)
cut.card("label", T_PEN - 0.05, s.t1 - 0.03, text="УШЁЛ НА ПЕНСИЮ", sub="МОЛЧА", x=0.06, y=0.15)
cut.sfx(T_PEN, "door-creak", -10)

# ======================================================== 5. Shop — «От себя»
T_MAG = A("магазин")
T_TYAN = A("тянет")
s = cut.shot("tp_shop", round(T_TYAN - 0.08, 3), tod="day")
s.fxk(0.0, "zoomblur", d=0.3, v=0.5)
v = actor(s, "hero", VW, (1.6, 2.4), face=-150, act="idle", eyes="normal", mouth="smile")
v.walk(0.05, (0.45, -3.85), dur=round(T_TYAN - s.t0 - 0.35, 3))
ks(s, [(s.t0, [3.6, 1.7, 3.4], [0.6, 1.2, -3.4], 48), (A("двери") - 0.1, [1.6, 1.6, -1.0], [0.0, 1.5, -4.9], 38), (-1, [1.0, 1.55, -2.1], [0.0, 1.45, -4.9], 34)],
   focus=None, ap=4)
cut.card("label", A("двери") - 0.05, s.t1 - 0.03, text="«ОТ СЕБЯ»", sub="ДВЕРЬ, ЗАПОМНИ", x=0.06, y=0.15, border="#c83a2a")
cut.sfx(T_MAG, "usr-whoosh-whip-mid-snap-149", -10)

T_10 = A("Десять", after=T_TYAN)
s = cut.shot("tp_shop", round(C[13]["start"] - 0.05, 3), tod="day")
v = actor(s, "hero", VW, (0.45, -3.85), face=180, act="struggle", eyes="angry", mouth="grit")
ks(s, [(s.t0, [2.4, 1.6, -0.4], [0.3, 1.3, -4.4], 46), (-1, [2.1, 1.55, -0.6], [0.3, 1.3, -4.4], 44)], focus="hero", ap=6, hh=1.0)
cut.card("stat", T_10 - 0.05, s.t1 - 0.03, **{"from": 0, "to": 10, "rollAt": T_TYAN, "rollDur": round(T_10 - T_TYAN + 0.4, 3)}, label="МИНУТ ТЯНЕТ", y=0.17, size=170)
for k in range(4):
    cut.sfx(T_TYAN + k * 0.42, "usr-thud-low-low-snap-095", -12)

T_OHR = A("Охранник")
T_NET = A("Нет", after=T_OHR)
s = cut.shot("tp_shop", round(T_NET - 0.08, 3), tod="day")
v = actor(s, "hero", VW, (0.45, -3.85), face=180, act="struggle", eyes="angry", mouth="grit")
g = actor(s, "guard", "ohrannik", (-1.1, -4.3), face=40, act="arms_crossed", eyes="angry", mouth="closed")
g.talk(A("Ты", after=T_OHR) - s.t0, A("ебанутый", end=True) - s.t0)
ks(s, [(s.t0, [0.2, 1.6, -0.6], [-0.4, 1.5, -4.1], 44), (-1, [0.0, 1.6, -0.9], [-0.5, 1.55, -4.1], 42)], focus="guard", ap=6)
cut.card("bubble", T_OHR - 0.05, s.t1 - 0.03, who="ОХРАННИК", whoColor="#9a9aa8", text="Ты чё, ебанутый?", y=0.15, side="right")
cut.sfx(T_OHR, "door-heavy-close", -12, dur=0.6)

s = cut.shot("tp_shop", S[6], tod="day")
v = actor(s, "hero", VW, (0.45, -3.85), face=20, act="idle", eyes="normal", mouth="smile")
v.talk(T_NET - s.t0, A("Витёк", after=T_NET, end=True) - s.t0)
ks(s, [(s.t0, [0.8, 1.62, -0.6], [0.45, 1.55, -3.85], 42), (-1, [0.7, 1.6, -0.8], [0.45, 1.56, -3.85], 42)], focus="hero", ap=12)
cut.card("bubble", T_NET - 0.05, s.t1 - 0.03, who="ВИТЁК", whoColor="#ffd84a", text="Нет, я Витёк.", y=0.15, side="left")
cut.sfx(A("Витёк", after=T_NET) + 0.4, "usr-voice-bruh-mid-swell-098", -10)

# ======================================================== 6. Street — walking in TikTok: pole, puddle, second pole
T_ST1 = A("Столб", after=S[6])
T_LUZ = A("Лужа")
T_ST2 = A("Второй")
PUDDLE = {"t": "block", "p": [-3.9, -6.2], "size": [1.2, 0.02, 1.0], "color": "#5a7a9a", "solid": False}
s = cut.shot("tp_winter", round(T_ST1 - 0.08, 3), tod="dusk")
s.fxk(0.0, "zoomblur", d=0.3, v=0.5)
v = actor(s, "hero", VW, (-4.0, 6.0), face=180, act="phone_up", eyes="normal", mouth="smile")
v.hold(0, B="phone")
v.walk(0.0, (-4.1, 1.0), dur=s.dur + 0.4)
ks(s, [(s.t0, [-1.6, 1.6, -0.6], [-4.0, 1.4, 5.5], 44), (-1, [-1.8, 1.6, -1.6], [-4.0, 1.4, 2.0], 44)], focus="hero", ap=4)

s = cut.shot("tp_winter", round(C[16]["start"] - 0.05, 3), tod="dusk")
extra(s, PUDDLE)
v = actor(s, "hero", VW, (-4.05, 0.55), face=180, act="phone_up", eyes="normal", mouth="smile")
v.hold(0, B="phone")
v.act(T_ST1 - s.t0, "jolt"); v.expr(T_ST1 - s.t0, "wide", "o")
v.walk(T_ST1 - s.t0 + 0.25, (-3.9, -5.9), dur=round(T_LUZ - T_ST1 - 0.25, 3))
v.act(T_LUZ - s.t0, "jolt")
v.walk(T_LUZ - s.t0 + 0.2, (-4.05, -11.45), dur=round(T_ST2 - T_LUZ - 0.2, 3))
v.act(T_ST2 - s.t0, "fall")
ks(s, [(s.t0, [-0.8, 1.9, 1.8], [-4.0, 1.2, -0.6], 50), (T_LUZ, [-0.6, 2.0, -3.6], [-4.0, 1.0, -6.4], 50), (-1, [-0.8, 2.2, -8.8], [-4.0, 1.0, -11.6], 50)],
   focus="hero", ap=3)
for t, name in [(T_ST1, "usr-thud-low-low-snap-305"), (T_LUZ, "usr-cartoon-splat-mid-snap-063"), (T_ST2, "usr-metal-crash-low-swell-310")]:
    hit(s, t, 0.06, 0.3)
    cut.sfx(t, name, -7)
    cut.card("stat", t - 0.03, t + 0.55, text={T_ST1: "БОНК", T_LUZ: "ПЛЮХ", T_ST2: "БОНК ×2"}[t], label="", y=0.2, size=120, color="#ff5a3c")

T_PRO = A("пролистал")
s = cut.shot("tp_winter", S[7], tod="dusk")
v = actor(s, "hero", VW, (-4.05, -12.4), face=0, act="sit_ground", eyes="normal", mouth="smile")
v.act(0.1, "phone_up"); v.hold(0.1, B="phone")
ks(s, [(s.t0, [-3.8, 1.3, -10.6], [-4.05, 0.9, -12.4], 40), (-1, [-3.85, 1.25, -11.0], [-4.05, 0.9, -12.4], 36)], focus="hero", ap=8)
sw0 = round(A("Видео") - 0.25 - s.t0, 3)
cut.card("feed", s.t0 + 0.05, S[7] - 0.03, y=0.42, swipes=[0.25, round(T_PRO - s.t0 - 0.1, 3)],
         clips=[{"title": "КОТ ТАНЦУЕТ", "color": "#8a3a6a", "likes": "4.1M", "author": "kotik"},
                {"title": "КАК НЕ БЫТЬ ТУПЫМ", "sub": "0:09", "color": "#2a4a7a", "likes": "12", "author": "umnik"},
                {"title": "ПАРЕНЬ ЛИЖЕТ СТОЛБ", "color": "#c84a2a", "likes": "9.9M", "author": "lol"}])
cut.sfx(s.t0 + 0.25, "usr-whoosh-light-mid-snap-382", -8)
cut.sfx(T_PRO - 0.1, "usr-whoosh-light-mid-snap-382", -6)
cut.card("label", A("девять") - 0.05, S[7] - 0.03, text="9 СЕКУНД", sub="СЛИШКОМ ДЛИННОЕ", x=0.06, y=0.15, border="#ff4a2a")

# ======================================================== 7. That very pole
T_SAM = A("столб", after=S[7])
s = cut.shot("tp_winter", round(C[18]["start"] - 0.05, 3), tod="dusk")
extra(s, {"t": "lightPt", "p": [-4.3, 0.3], "y": 1.6, "i": 4, "d": 2.5, "color": "#d8f0ff", "blink": {"t0": 0.0, "on": 0.3, "off": 0.3}})
ks(s, [(s.t0, [-3.0, 0.4, 2.2], [-4.5, 2.2, 0.0], 50), (-1, [-3.6, 1.0, 1.0], [-4.5, 1.7, 0.0], 40)], focus=None, ap=6)
cut.sfx(s.t0, "reveal-glow", -6)
cut.sfx(T_SAM, "usr-suspense-sting", -9)
cut.card("label", T_SAM - 0.05, s.t1 - 0.03, text="ТОТ САМЫЙ СТОЛБ", sub="−20°", x=0.06, y=0.15, border="#7ad0ff")

T_SL = A("сладкий")
s = cut.shot("tp_winter", round(C[19]["start"] - 0.05, 3), tod="dusk")
v = actor(s, "hero", VW, (-3.7, 0.3), face=-30, act="think", eyes="happy", mouth="smile")
extra(s, {"t": "lightPt", "p": [-4.3, 0.3], "y": 1.6, "i": 4, "d": 2.5, "color": "#d8f0ff", "blink": {"t0": 0.0, "on": 0.3, "off": 0.3}})
ks(s, [(s.t0, [-3.3, 1.62, 3.8], [-3.9, 1.55, 0.3], 42), (-1, [-3.4, 1.6, 3.6], [-3.95, 1.55, 0.3], 42)], focus="hero", ap=12)
cut.sfx(A("Блестит"), "usr-notify-ding-bright-snap-105", -8)
cut.card("bubble", A("А", after=A("думает", after=S[7])) - 0.05, s.t1 - 0.03, who="ВИТЁК", whoColor="#ffd84a", text="А вдруг он сладкий?", y=0.15, side="left")

T_NE = C[19]["start"]
T_MCS = A("МЧС")
T_MLN = A("миллион")
s = cut.shot("tp_winter", round(T_MCS + 0.35, 3), tod="dusk")
stuck(s, eyes="wide", mouth="o")
ks(s, [(s.t0, [-3.9, 1.6, 3.4], [-4.15, 1.5, 0.0], 42), (-1, [-3.95, 1.58, 3.2], [-4.15, 1.5, 0.0], 40)], focus="hero", ap=12)
hit(s, T_NE + 0.05, 0.08, 0.5)
flash(T_NE + 0.05, 0.1, "#bfe8ff")
cut.sfx(T_NE + 0.05, "usr-glass-shatter-bright-snap-151", -9)
cut.sfx(T_NE + 0.1, "hit-cinematic", -8)
cut.card("stat", T_NE - 0.03, s.t1 - 0.02, text="НЕ СЛАДКИЙ", label="", y=0.17, size=130, color="#7ad0ff")

s = cut.shot("tp_winter", S[8], tod="dusk")
stuck(s)
crowd(s, 6, flashes=[T_MCS + 0.6, T_MCS + 1.0, T_MCS + 1.3, T_MLN, T_MLN + 0.3])
r1 = actor(s, "r1", "resc1", (-1.6, 2.8), face=-120, act="idle", eyes="normal", mouth="closed")
r1.walk(0.05, (-3.4, 0.9), dur=1.3)
r2 = actor(s, "r2", "resc2", (-0.8, 1.6), face=-110, act="idle", eyes="angry", mouth="closed")
r2.walk(0.15, (-3.3, -0.6), dur=1.3)
extra(s, {"t": "car", "p": [-1.6, 4.5], "r": 0, "color": "#d0602a", "lights": True, "hazardAt": 0.0},
      {"t": "lightPt", "p": [-1.6, 4.5], "y": 2.0, "i": 5, "d": 8, "color": "#3a6aff", "blink": {"t0": 0.0, "on": 0.2, "off": 0.2}},
      {"t": "lightPt", "p": [-1.2, 4.5], "y": 2.0, "i": 5, "d": 8, "color": "#ff3a3a", "blink": {"t0": 0.2, "on": 0.2, "off": 0.2}})
orbit(s, (-3.6, 0.6), 6.0, 2.2, 35, -15, 1.2, 52, focus="hero", ap=2, h1=3.2)
cut.sfx(T_MCS - 0.1, "siren-far", -10, dur=2.4)
for t in (0.6, 1.0, 1.3):
    cut.sfx(T_MCS + t, "usr-photo-shutter-bright-snap-163", -12)
cut.card("stat", T_MLN - 0.05, S[8] - 0.03, **{"from": 0, "to": 1000000, "rollAt": T_MLN, "rollDur": 1.2}, label="ПРОСМОТРОВ", y=0.17, size=120, color="#ff4a8a")
cut.sfx(T_MLN, "usr-cash-register-bright-snap-216", -8)

# ======================================================== 8. So how to live — «да заебись»
T_ZAE = A("заебись")
s = cut.shot("tp_kitchen", round(C[21]["start"] - 0.05, 3))
extra(s, *YOLK_K, {"t": "block", "p": [0.3, 0.42], "y": 1.5, "size": [0.12, 0.06, 0.02], "color": "#f0e8d8", "solid": False})   # plaster on the mouth
v = actor(s, "hero", V, (0.3, 0.3), face=10, act="idle", eyes="normal", mouth="closed")
v.act(T_ZAE - s.t0 - 0.1, "fist"); v.expr(T_ZAE - s.t0 - 0.1, "happy", "closed")
m = actor(s, "mama", "mama", (-1.3, 0.9), face=30, act="phone_up", eyes="normal", mouth="smile")
m.hold(0, B="phone")
ks(s, [(s.t0, [1.2, 1.6, 2.4], [-0.2, 1.4, 0.4], 44), (-1, [0.9, 1.6, 2.0], [-0.1, 1.45, 0.4], 40)], focus="hero", ap=4)
cut.card("stat", T_ZAE - 0.05, s.t1 - 0.03, text="ДА ЗАЕБИСЬ", label="КАК ЖИТЬ?", y=0.17, size=120, color="#5ad05a")
cut.card("notif", A("Так", after=S[8]) - 0.05, T_ZAE - 0.1, app="ТИКТОК", text="Мама лайкнула: «Ну и тупой»", icon="#e8306a", glyph="❤", y=0.16)
cut.sfx(A("Так", after=S[8]), "pk-notify-notification-sfx-1", -8)
cut.sfx(T_ZAE, "usr-cinema-boom-low-tail-024", -7, dur=1.4)

T_XOL = A("холодно")
s = cut.shot("tp_winter", round(C[22]["start"] - 0.05, 3), tod="dusk")
v = actor(s, "hero", VW, (-3.7, 0.3), face=-80, act="idle", eyes="happy", mouth="smile")
v.walk(A("бывает", after=A("Тупым", occ=2, after=S[8])) - s.t0, TONGUE_AT, dur=0.5)
v.act(T_XOL - s.t0 - 0.1, "struggle"); v.expr(T_XOL - s.t0 - 0.1, "wide", "o")
extra(s, {**TONGUE, "showAt": round(T_XOL - 0.1, 3)}, FROST)
crowd(s, 4, flashes=[T_XOL + 0.2, T_XOL + 0.5])
ks(s, [(s.t0, [-2.4, 1.5, 4.6], [-4.0, 1.45, 0.1], 46), (-1, [-3.5, 1.5, 3.6], [-4.1, 1.5, 0.0], 42)], focus="hero", ap=4)
cut.card("label", A("стыдно") - 0.05, T_XOL - 0.15, text="СТЫДНО: 0%", x=0.06, y=0.15)
cut.card("label", T_XOL - 0.05, s.t1 - 0.03, text="ОПЯТЬ ЛИЗНУЛ", sub="ВТОРОЙ РАЗ", x=0.06, y=0.15, border="#ff4a2a")
cut.sfx(T_XOL, "usr-glass-shatter-bright-snap-372", -10)
cut.sfx(T_XOL + 0.15, "usr-crowd-aww-mid-swell-156", -12)

T_TY = A("ты", after=A("конца"))
s = cut.shot("tp_winter", END_STORY, tod="dusk")
stuck(s, eyes="normal", mouth="o")
ks(s, [(s.t0, [-2.8, 1.55, 4.4], [-4.1, 1.5, 0.0], 44), (T_TY, [-3.9, 1.5, 3.4], [-4.1, 1.5, 0.0], 42), (-1, [-3.95, 1.5, 3.3], [-4.1, 1.5, 0.0], 42)],
   focus="hero", ap=6)
cut.card("label", T_TY - 0.05, END_STORY - 0.02, text="ТЫ", sub="НЕМНОЖКО ВИТЁК", x=0.06, y=0.15, border="#ffd84a")
cut.sfx(T_TY, "usr-whoosh-whip-mid-snap-169", -9)

# ======================================================== 9. CTA — same voice, profile, «шапку профиля»
t0 = ep.t
s = ep.shot("tp_winter", round(END - t0, 3), tod="dusk")
stuck(s, eyes="happy", mouth="smile")
s.actors["hero"].act(0.0, "wave") if hasattr(s, "actors") and isinstance(getattr(s, "actors"), dict) else None
cam(s, [(0, [-3.4, 1.5, 4.2], [-4.1, 1.4, 0.0], 44), (-1, [-3.2, 1.5, 4.6], [-4.1, 1.4, 0.0], 46)], focus="hero", ap=6, zoom=False)
t_hl = A("шапку", after=S[9])
cut.card("black", t0, END, color="rgba(0,0,0,0.55)", fi=0.25, fo=0.01)
cut.card("profile", t0, END, hlAt=t_hl)
ep.sfx(t_hl, "pk-notify-notification-sfx-1", -6)

# ----------------------------------------------------------------- sound: voice + ambience + SFX, NO music
ep.voice(0, copy_voice(KID, "tupoy"), gain=0)
w.subs(ep, 0.3)
for sub, c in zip(ep.subs[-len(C):], C):
    sub["t1"] = round(min(sub["t1"], c["end"] + 0.8), 3)
ep.amb(0.0, S[2], "city-hum", gain=-34, fi=0.05, fo=0.2)
ep.amb(0.0, S[2], "shorts/city_dark", gain=-28, fi=0.05, fo=0.2)
ep.amb(S[2], S[5], "room-tone", gain=-32, fi=0.1, fo=0.2)
ep.amb(S[5], S[6], "room-tone", gain=-30, fi=0.1, fo=0.2)
ep.amb(S[6], S[7], "shorts/street_day", gain=-27, fi=0.2, fo=0.2)
ep.amb(S[7], C[21]["start"], "city-hum", gain=-34, fi=0.2, fo=0.2)
ep.amb(S[7], C[21]["start"], "shorts/city_dark", gain=-28, fi=0.2, fo=0.2)
ep.amb(C[21]["start"], C[22]["start"], "room-tone", gain=-32, fi=0.1, fo=0.1)
ep.amb(C[22]["start"], END, "city-hum", gain=-34, fi=0.1, fo=1.0)
ep.save()
print(f"tupoy: {ep.t:.2f}s, {len(ep.shots)} shots")
