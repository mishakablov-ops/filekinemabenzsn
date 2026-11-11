"""«Каждые 10 секунд у тебя становится больше тестостерона» v2 — vertical PIXCINE short (1080×1920), 10.11.2026.
mike on v1: timing problems, no background music (keep the sounds), the script was raw — more action, everything on
the street «как в примере» (a wish for this video, not a mandatory rule; street sets stay in use: mike 11.11.2026),
a bit of 3D, a strong TikTok hook. So:
- hook = teaser of the finale (1:20 gigachad stops a speeding car with his palm at night), a phone call from
  «???», then a rewind to the skinny start; the «кроме одного человека» promise pays off at 1:20 (mom, the hat);
- every block is a street gag with real props in motion (cars, a bench with grannies, a lamp post and a blackout,
  coins, a breaking café table, a wall); cameras orbit, crane and dolly through the 3D sets;
- the voice (MiniMax Russian_ReliableMan ×1.35, as «Эскалатор») was tightened: section gaps ≤ 0.9 s
  (tighten_voice.py); the HUD clock is keyed to the sections, so it still reads 0:10, 0:20 … on each level-up;
- no music track: ambience + SFX only.
Arsen Markaryan is a parody nod only: a bearded pixel «mentor» (char `arsen`) labelled «ПАРОДИЯ» and chat messages."""
import json
import math

from common_sh import K, Cut, Ep, H, W, Words, cam, copy_voice, narration, save_loc

KID = "testosteron2"
w = Words(KID)
C = w.cards
SEC = {int(r["id"]): r for r in json.loads((narration(KID) / "sections.json").read_text(encoding="utf-8"))}
S = {k: v["start"] for k, v in SEC.items()}
A = w.at
END_STORY = round(S[10] - 0.05, 3)
END = round(w.duration + 0.9, 3)
T_RW = 6.33                     # rewind from the 1:20 teaser to the skinny start


# ----------------------------------------------------------------- sets
def street(id, night=False, off=None, tod="day", punch=None):
    """main street along z: 8 m road with a zebra at z=0, 3 m sidewalks, facades at x=±7.5 with shop signs,
    lamps, trees, parked cars, a bus stop, a kiosk, pigeons; off = blackout time (lamps/windows/signs);
    punch = time the left lamp at z=6 is hit (it bends and dies first)"""
    P = [{"t": "road", "p": [0, 0], "w": 8, "len": 160, "zebraZ": 0}]
    cols = ["#8a7e72", "#7a8a8e", "#9a7a62", "#7e7a8a", "#9a8a72", "#7a7e86", "#8a6e60", "#888070", "#6e7a72"]
    for side in (-1, 1):
        for i, z in enumerate([-50, -38, -26, -14, -2, 10, 22, 34, 46]):
            b = {"t": "building", "p": [side * 12, z], "r": 90 if side < 0 else -90, "w": 11, "d": 9, "floors": 5 + (i * 3 + (side > 0) * 2) % 6,
                 "seed": i + (side > 0) * 10, "color": cols[(i + (side > 0) * 4) % len(cols)]}
            if night:
                b["lit"] = 0.5
                if off is not None:
                    b["offAt"] = round(off + 0.04 * abs(z), 3)
            else:
                b["day"] = True
            P.append(b)
    signs = [(-1, -26, "АПТЕКА", "#2a8a4a"), (-1, -14, "ПРОДУКТЫ 24", "#2a4a8a"), (-1, -2, "ШАУРМА", "#c84a2a"), (-1, 10, "ЦВЕТЫ", "#8a3a6a"),
             (-1, 22, "РЕМОНТ ОБУВИ", "#5a4a3a"), (1, -26, "ФИТНЕС «БЫК»", "#c83a3a"), (1, -14, "ЛОМБАРД", "#8a7a2a"), (1, -4, "КАФЕ «БАЗА»", "#3a2a1a"),
             (1, 10, "БАРБЕРШОП", "#1a1a1e"), (1, 22, "САЛОН СВЯЗИ", "#3a6aa8")]
    for side, z, txt, bg in signs:
        g = {"t": "shopSign", "p": [side * 7.42, z], "y": 3.3, "r": 90 if side < 0 else -90, "w": min(5.2, 0.55 * len(txt) + 0.8), "h": 0.8,
             "text": txt, "bg": bg, "glow": 1.1 if night else 0.2}
        if night and off is not None:
            g["offAt"] = round(off + 0.03 * abs(z) + 0.1, 3)
        P.append(g)
    for i, z in enumerate([-42, -30, -18, -6, 6, 18, 30, 42]):
        side = 1 if i % 2 else -1
        lp = {"t": "streetLamp", "p": [side * 4.5, z], "r": 0 if side < 0 else 180, "on": night}
        if night and off is not None:
            lp["offAt"] = round(off + 0.05 * abs(z - 6), 3)
        if punch is not None and z == 6:
            lp["offAt"] = round(punch + 0.06, 3)
            lp["anim"] = [{"t": 0, "r": [0, 0, 0]}, {"t": punch, "r": [0, 0, 0]}, {"t": punch + 0.16, "r": [0, 0, -13], "e": "out"}]
        P.append(lp)
    for side in (-1, 1):
        for z in (-24, -12, 12, 24, 36):
            P.append({"t": "tree", "p": [side * 6.3, z + side * 1.5], "s": 0.75})
    for x, z, r, c in [(-3.2, -32, 0, "#3a6ab8"), (-3.2, -22, 0, "#d8d8d8"), (-3.2, 14, 0, "#2a2a30"), (-3.2, 26, 0, "#8a2a2a"),
                       (3.2, -28, 180, "#e0b020"), (3.2, -9, 180, "#4a8a5a"), (3.2, 16, 180, "#c8c8c0"), (3.2, 30, 180, "#5a3a7a")]:
        P.append({"t": "car", "p": [x, z], "r": r, "color": c})
    # bus stop (right sidewalk) and a kiosk
    P += [{"t": "block", "p": [6.4, -19], "y": 2.45, "size": [1.3, 0.08, 3.2], "tex": "metal", "color": "#4a5a6a", "solid": False},
          {"t": "block", "p": [6.95, -19], "size": [0.06, 2.45, 3.2], "color": "#6a8aa0", "solid": False},
          {"t": "bench", "p": [6.5, -19], "r": -90, "w": 2.2},
          {"t": "shopSign", "p": [5.75, -19], "y": 2.75, "r": -90, "w": 1.6, "h": 0.4, "text": "ОСТАНОВКА", "bg": "#2a5aa8", "glow": 1.0 if night else 0.2},
          {"t": "block", "p": [-6.0, 16], "size": [1.6, 2.4, 1.6], "tex": "metal", "color": "#5a7a5a"},
          {"t": "shopSign", "p": [-5.18, 16], "y": 2.0, "r": 90, "w": 1.4, "h": 0.5, "text": "ПЕЧАТЬ", "bg": "#2a6a3a", "glow": 0.9 if night else 0.2},
          {"t": "bench", "p": [-6.6, 9], "r": 90},
          {"t": "block", "p": [-6.9, 3.2], "size": [0.5, 0.8, 0.5], "color": "#2a4a3a"},
          {"t": "block", "p": [6.9, 4.5], "size": [0.5, 0.8, 0.5], "color": "#2a4a3a"},
          {"t": "bush", "p": [-6.8, -8], "s": 0.8}, {"t": "bush", "p": [6.8, 7], "s": 0.8},
          {"t": "crows", "p": [-5.2, 12], "n": 5, "spread": 2.2, "color": "#7a808c"},
          {"t": "crows", "p": [5.4, -12], "n": 4, "spread": 2.0, "color": "#7a808c"},
          {"t": "building", "p": [0, -72], "w": 40, "d": 10, "floors": 12, "seed": 40, **({"lit": 0.5} if night else {"day": True}), "color": "#7a7680"},
          {"t": "building", "p": [0, 72], "r": 180, "w": 40, "d": 10, "floors": 9, "seed": 41, **({"lit": 0.5} if night else {"day": True}), "color": "#867a6e"}]
    L = {"id": id, "tod": tod, "fog": 0.016 if night else 0.010, "ground": {"tex": "paving", "size": [240, 240]}, "props": P,
         "particles": [{"kind": "motes", "n": 90, "box": [-7, 0.3, -10, 7, 5, 10]}]}
    save_loc(L)
    return L


def yard(id, night=False):
    """courtyard of five-storey blocks: entrance door at (0, -7), playground, parked cars, lamps, pigeons"""
    P = [{"t": "building", "p": [0, -12], "w": 30, "d": 10, "floors": 5, "seed": 51, "color": "#9a8a7a", **({"lit": 0.55} if night else {"day": True})},
         {"t": "building", "p": [-15, 6], "r": 90, "w": 26, "d": 10, "floors": 5, "seed": 52, "color": "#8a8a80", **({"lit": 0.5} if night else {"day": True})},
         {"t": "building", "p": [15, 6], "r": -90, "w": 26, "d": 10, "floors": 9, "seed": 53, "color": "#7a7e8a", **({"lit": 0.5} if night else {"day": True})},
         {"t": "shopSign", "p": [0, -6.93], "y": 2.55, "w": 1.0, "h": 0.32, "text": "ПОД. 3", "bg": "#2a3a5a", "glow": 0.9 if night else 0.2},
         {"t": "road", "p": [0, 8], "w": 5, "len": 40, "sidewalk": 1.5},
         {"t": "block", "p": [-4.0, -3.5], "size": [2.2, 0.3, 2.2], "tex": "wood", "color": "#8a6a3a"},           # sandbox
         {"t": "block", "p": [-6.2, -3.0], "y": 0.0, "size": [0.08, 2.2, 0.08], "color": "#c83a2a", "solid": False},  # swing frame
         {"t": "block", "p": [-6.2, -1.2], "size": [0.08, 2.2, 0.08], "color": "#c83a2a", "solid": False},
         {"t": "block", "p": [-6.2, -2.1], "y": 2.2, "size": [0.1, 0.1, 1.9], "color": "#c83a2a", "solid": False},
         {"t": "block", "p": [-6.2, -2.1], "y": 0.45, "size": [0.5, 0.06, 0.3], "tex": "wood", "solid": False},
         {"t": "bench", "p": [-3.6, 1.6], "r": 0},
         {"t": "tree", "p": [-8.0, -5.0], "s": 0.9}, {"t": "tree", "p": [7.5, -4.5], "s": 0.85}, {"t": "tree", "p": [-8.5, 4.0], "s": 0.8},
         {"t": "tree", "p": [8.2, 3.5], "s": 0.9}, {"t": "bush", "p": [5.0, -6.0], "s": 0.8}, {"t": "bush", "p": [-2.5, -6.0], "s": 0.8},
         {"t": "streetLamp", "p": [-5.0, 3.5], "on": night}, {"t": "streetLamp", "p": [6.0, -2.0], "r": 180, "on": night},
         {"t": "block", "p": [8.6, -6.2], "size": [1.2, 1.3, 0.8], "tex": "metal", "color": "#3a5a3a"},          # garbage container
         {"t": "block", "p": [7.2, -6.2], "size": [1.2, 1.3, 0.8], "tex": "metal", "color": "#3a5a3a"},
         {"t": "crows", "p": [2.0, 2.8], "n": 6, "spread": 2.4, "color": "#7a808c"},
         {"t": "clutter", "p": [-3.4, -3.3]}]
    L = {"id": id, "tod": "night" if night else "day", "fog": 0.02 if night else 0.012, "ground": {"tex": "asphalt", "size": [200, 200]}, "props": P,
         "particles": [{"kind": "motes", "n": 60, "box": [-6, 0.3, -6, 6, 4, 6]}]}
    save_loc(L)
    return L


YARD_CARS = [(-6.6, -1.0, 0, "#c83a2a"), (-6.6, 4.6, 0, "#3a6ab8"), (6.8, 1.0, 180, "#e0b020"), (6.8, 6.6, 180, "#d8d8d8"), (2.6, 10.0, 90, "#4a8a5a")]

street("tt2_night", night=True, tod="night")
T_PUNCH = round(A("столбу") - 0.02, 3)
T_OFF = round(A("Гаснет") + 0.02, 3)
street("tt2_black", night=True, off=T_OFF, tod="night", punch=T_PUNCH)
street("tt2_day", tod="day")
yard("tt2_yard_day")
yard("tt2_yard_night", night=True)
save_loc({"id": "tt2_podezd", "interior": True, "tod": "interior",
          "props": [{"t": "room", "p": [0, 0], "w": 3.0, "d": 3.2, "h": 2.8, "wall": "plaster", "wallOpts": {"color": "#4a6a5e"}, "floor": "floor_tiles",
                     "floorOpts": {"a": "#6a5a4a", "b": "#4a3e34"}, "ceiling": False},
                    {"t": "block", "p": [-0.9, -1.55], "y": 1.0, "size": [1.1, 0.7, 0.1], "tex": "metal", "color": "#5a6a7a"},       # mailboxes
                    {"t": "poster", "p": [0.8, -1.58], "y": 1.5, "v": 2}, {"t": "poster", "p": [1.25, -1.58], "y": 1.45, "v": 0, "w": 0.4, "h": 0.55},
                    {"t": "bulb", "p": [0, -0.6], "y": 2.8, "len": 0.4, "i": 1.6, "d": 5, "flicker": 0.3}],
          "fog": 0.03, "hemi": ["#3a4a44", "#0a0806", 0.3]})

# ----------------------------------------------------------------- episode
ep = Ep("shorts", "testo2", fps=30, w=W, h=H)
cut = Cut(ep, w)


def actor(s, id, char, at, face=0, act="idle", eyes=None, mouth=None, **arg):
    a = s.actor(id, char, at=at, face=face)
    a.act(0, act, **arg)
    if eyes or mouth:
        a.expr(0, eyes, mouth)
    return a


Z_DIST, Z_FOV = 1.65, 1.45      # portrait framing (same calibration as common_sh.cam): pull back and widen


def ks(s, keys, focus=None, ap=None, hh=None, zoom=True):
    """explicit camera keys in GLOBAL time: [(t, pos, look, fov[, ease]), …]; t = -1 → end of shot.
    zoom=True pulls every camera back from its look point (×1.65) and widens it (×1.45, ≤ 68°)."""
    out = []
    for i, (t, p, l, f, *rest) in enumerate(keys):
        if zoom:
            p = [l[j] + (p[j] - l[j]) * Z_DIST for j in range(3)]
            f = min(68, f * Z_FOV)
        out.append(K(round(max(0.0, t - s.t0) if t != -1 else s.dur, 3), p, l, f, None if i == 0 else (rest[0] if rest else "inOut")))
    s.cam(out, focus=focus, aperture=ap, **({"handheld": hh} if hh is not None else {}))
    return s


def orbit(s, c, r, h, a0, a1, look_h, fov, t0=None, t1=None, n=6, focus=None, ap=None, r1=None, h1=None, fov1=None, look_h1=None, zoom=True):
    """circular camera move around c=(x, z): angle a (deg) measured from +z towards +x, global times"""
    t0 = s.t0 if t0 is None else t0
    t1 = s.t1 if t1 is None else t1
    keys = []
    for i in range(n):
        f = i / (n - 1)
        a = math.radians(a0 + (a1 - a0) * f)
        rr = r + ((r1 if r1 is not None else r) - r) * f
        hh = h + ((h1 if h1 is not None else h) - h) * f
        lh = look_h + ((look_h1 if look_h1 is not None else look_h) - look_h) * f
        keys.append((t0 + (t1 - t0) * f, [c[0] + math.sin(a) * rr, hh, c[1] + math.cos(a) * rr], [c[0], lh, c[1]],
                     fov + ((fov1 if fov1 is not None else fov) - fov) * f, "linear"))
    return ks(s, keys, focus=focus, ap=ap, zoom=zoom)


def extra(s, *props):
    s.kw.setdefault("extra", []).extend(props)


def flash(t, d=0.14, color="#ffffff"):
    cut.card("black", t - 0.02, t + d, color=color, fi=0.02, fo=d * 0.8)


def debris(t, origin, n, spread, color="#7a6a5a", size=(0.22, 0.14, 0.18), seed=1, up=1.2, dur=0.7, rise=0.0, dz=1.0):
    """n small blocks flying out from origin (x, y, z) at t and landing on the ground (visible from t)"""
    out = []
    for i in range(n):
        h1 = math.sin(seed * 12.9898 + i * 78.233) * 43758.5453
        h2 = math.sin(seed * 39.3468 + i * 11.135) * 24634.6345
        r1, r2 = h1 - math.floor(h1), h2 - math.floor(h2)
        x0, y0, z0 = origin[0] + (r1 - 0.5) * spread[0], origin[1] + (r2 - 0.5) * spread[1], origin[2]
        x1, z1 = x0 + (r2 - 0.5) * 3.2, z0 + dz * (0.8 + r1 * 2.2)
        sz = [round(size[0] * (0.6 + r1 * 0.8), 3), round(size[1] * (0.6 + r2 * 0.8), 3), round(size[2] * (0.6 + r1 * 0.6), 3)]
        k = [{"t": round(t, 3), "p": [round(x0, 3), round(y0, 3), round(z0, 3)], "r": [0, 0, 0]},
             {"t": round(t + dur * 0.45, 3), "p": [round((x0 + x1) / 2, 3), round(y0 + up * (0.5 + r2) + rise, 3), round((z0 + z1) / 2, 3)],
              "r": [round(r1 * 300, 1), round(r2 * 200, 1), round(r1 * 150, 1)], "e": "out"},
             {"t": round(t + dur, 3), "p": [round(x1, 3), 0.0, round(z1, 3)], "r": [round(r1 * 540, 1), round(r2 * 360, 1), round(r2 * 300, 1)], "e": "in"}]
        out.append({"t": "block", "p": [round(x0, 3), round(z0, 3)], "size": sz, "color": color, "solid": False, "showAt": round(t, 3), "anim": k})
    return out


# HUD: clock keyed to the sections (reads 1:20 in the teaser, spins back on the rewind, then 0:10, 0:20 … on level-ups)
clock = [[0.0, 80], [T_RW, 80], [round(T_RW + 0.6, 3), 6]] + [[S[k], (k - 1) * 10] for k in range(2, 10)]
LEVELS = [(0.0, 8, "MAX"), (T_RW, 0, "×1")] + [(S[k], k - 1, f"×{2 ** (k - 1)}") for k in range(2, 9)] + [(S[9], 8, "MAX")]
T_ZERO = A("нуля", after=S[9])
LEVELS.append((T_ZERO, 0, "×0"))
cut.card("meter", 0.0, END_STORY, levels=[{"t": round(t, 3), "n": n, "mult": m} for t, n, m in LEVELS], max=8, clockKeys=clock, y=0.025)


def level_up(k):
    t = S[k]
    flash(t, 0.16)
    gap = t - SEC[k - 1]["end"]
    if gap > 0.5:   # fill the short pause before every level-up with a riser into the boom
        cut.sfx(round(t - min(1.0, gap + 0.1), 3), "riser-short", -15, dur=round(min(1.0, gap + 0.1), 3))
    cut.sfx(t, "usr-bass-drop-low-tail" if k % 2 else "usr-cinema-boom-low-tail-184", -7, dur=2.6)


for k in range(2, 10):
    level_up(k)

# ======================================================== 1. HOOK — 1:20 teaser: the palm stops a speeding car
T_HIT = round(A("тестостерон") - 0.02, 3)
CAR_RED = {"t": "car", "p": [-1.5, 0], "color": "#c83a2a", "lights": True}
s = cut.shot("tt2_night", 2.62)
h = actor(s, "hero", "geroy_t8p", (-1.5, 0.0), face=180, act="idle", eyes="angry", mouth="closed")
h.act(T_HIT - 0.22, "stop")
h.expr(T_HIT - 0.1, "angry", "grit")
extra(s, {**CAR_RED, "anim": [{"t": 0, "p": [-1.5, 0, -34.0]}, {"t": T_HIT, "p": [-1.5, 0, -2.65], "e": "linear"},
                              {"t": T_HIT + 0.12, "p": [-1.5, 0.18, -2.85], "r": [7, 0, 0], "e": "out"},
                              {"t": T_HIT + 0.45, "p": [-1.5, 0, -2.75], "r": [0, 0, 0], "e": "out"}], "hazardAt": round(T_HIT + 0.5, 3)})
for i, (x, z, ch, f) in enumerate([(-5.6, 2.6, "p1", 120), (-5.9, 1.0, "p4", 100), (5.4, 1.8, "p3", -110), (5.8, -0.4, "p2", -100)]):
    a = actor(s, f"c{i}", ch, (x, z), face=f, act="phone_up")
    a.hold(0, B="phone")
    a.act(T_HIT + 0.05 + i * 0.07, "scared")
ks(s, [(0.0, [-0.55, 1.15, 3.4], [-1.6, 1.4, -6.0], 50),
       (T_HIT - 0.05, [3.2, 0.8, 1.9], [-1.5, 1.2, -0.5], 54),
       (-1, [2.7, 0.9, 1.5], [-1.5, 1.3, -0.4], 50)], focus="hero", ap=4, zoom=False)
s.fxk(T_HIT - s.t0, "shake", d=0.55, v=0.09)
flash(T_HIT, 0.1)
cut.sfx(0.05, "usr-whoosh-roar-low-swell-322", -5)
cut.sfx(T_HIT, "usr-metal-crash-low-swell-310", -6)
cut.sfx(T_HIT, "hit-cinematic", -8)
cut.sfx(T_HIT + 0.35, "shorts/car_horn", -14, dur=0.6)
cut.sfx(T_HIT + 0.15, "usr-crowd-gasp-mid-swell-172", -12)

# the crumpled car behind him, the phone buzzes on «Кроме одного человека»
T_CALL = round(A("Кроме") - 0.05, 3)
s = cut.shot("tt2_night", T_RW)
h = actor(s, "hero", "geroy_t8p", (-1.5, 0.2), face=0, act="idle", eyes="angry", mouth="closed")
h.walk(0.05, (-1.5, 2.7), dur=T_CALL - s.t0 - 0.05)
h.act(T_CALL - s.t0, "phone"); h.hold(T_CALL - s.t0, B="phone")
h.expr(A("человека") - s.t0, "wide", "o")
extra(s, {**CAR_RED, "p": [-1.5, -2.75], "hazardAt": 0.0})
for i, (x, z, ch, f) in enumerate([(-5.6, 2.6, "p1", 120), (-5.9, 1.0, "p4", 100), (5.4, 1.8, "p3", -110), (5.8, -0.4, "p2", -100)]):
    a = actor(s, f"c{i}", ch, (x, z), face=f, act="phone_up")
    a.hold(0, B="phone")
ks(s, [(s.t0, [-1.25, 0.75, 7.6], [-1.5, 1.6, 0.6], 42),
       (T_CALL, [-1.3, 1.0, 6.6], [-1.5, 1.55, 2.4], 40),
       (-1, [-1.4, 1.6, 5.6], [-1.5, 1.6, 2.7], 36)], focus="hero", ap=6, zoom=False)
cut.card("notif", T_CALL, T_RW - 0.05, app="ВХОДЯЩИЙ ВЫЗОВ", text="??? ", icon="#3a8a4a", glyph="✆", y=0.16)
cut.sfx(T_CALL, "usr-notify-two-tone-mid-swell-103", -6)
cut.sfx(A("человека"), "usr-suspense-sting", -10)

# rewind to the skinny start
flash(T_RW, 0.18)
cut.card("label", T_RW, T_RW + 1.1, text="◀◀ ПЕРЕМОТКА", sub="К НАЧАЛУ", x=0.06, y=0.15, border="#ff4a2a")
cut.sfx(T_RW - 0.12, "usr-tape-rewind-mid-swell-049", -5, dur=0.9)

# golden street: the skinny guy, twenty push-ups, and that's it
T_ALL = A("всё")
FILL = {"t": "lightPt", "p": [-4.3, 3.4], "y": 1.6, "i": 3.2, "d": 6, "color": "#ffc890"}      # sun bounce on the push-ups
s = cut.shot("tt2_day", S[2], tod="golden")
s.fxk(0.0, "zoomblur", d=0.35, v=0.5)
d = actor(s, "hero", "geroy_d", (-5.4, 2.0), face=90, act="pushup", eyes="normal", mouth="grit", dir=-1, hz=0.85)
d.act(T_ALL - s.t0, "down", dir=-1)
d.expr(T_ALL - s.t0, "closed", "o")
for i, (ch, z0, z1, x) in enumerate([("p2", -6.0, 9.0, -6.9), ("p4", 9.0, -5.0, -6.6)]):
    a = actor(s, f"w{i}", ch, (x, z0), face=0 if z1 > z0 else 180, act="idle")
    a.walk(0.1, (x, z1), dur=3.5)
extra(s, {"t": "crows", "p": [-6.3, 0.4], "n": 3, "spread": 1.0, "color": "#7a808c"})
extra(s, FILL)
ks(s, [(s.t0, [-4.45, 0.6, 5.4], [-4.6, 0.32, 2.0], 52),
       (T_ALL - 0.3, [-4.4, 0.8, 5.5], [-4.6, 0.3, 2.0], 52),
       (-1, [-4.2, 1.9, 5.6], [-4.6, 0.3, 2.0], 56)], focus="hero", ap=5, zoom=False)
cut.card("stat", A("двадцать", after=7.0) - 0.05, T_ALL - 0.05, **{"from": 0, "to": 20, "rollAt": A("двадцать", after=7.0), "rollDur": 1.3},
         label="ОТЖИМАНИЯ", y=0.17, size=170)
cut.card("label", T_ALL - 0.02, S[2] - 0.08, text="ЛИЧНЫЙ РЕКОРД", sub="ДРЫЩ", x=0.06, y=0.15)
cut.sfx(T_ALL, "usr-cartoon-splat-low-swell-046", -8)
cut.sfx(T_ALL - 0.15, "usr-slide-whistle-mid-snap-278", -12)

# ======================================================== 2. 0:10 — the octave, one-arm push-ups, coins
s = cut.shot("tt2_day", round(C[4]["start"] - 0.1, 3))
h = actor(s, "hero", "geroy", (-5.4, 2.0), face=20, act="talk", eyes="normal", mouth="closed")
h.expr(A("октаву") - s.t0, "angry", "grit"); h.act(A("октаву") - s.t0, "fist")
p = actor(s, "w0", "p2", (-6.2, 4.8), face=160, act="idle")
p.face(A("октаву") - s.t0 + 0.1, -150); p.act(A("октаву") - s.t0 + 0.1, "scared")
ks(s, [(s.t0, [-4.75, 1.72, 4.1], [-5.4, 1.5, 2.0], 32), (-1, [-5.55, 1.68, 4.05], [-5.4, 1.52, 2.0], 30)], focus="hero", ap=12)
s.fxk(A("октаву") - s.t0, "shake", d=0.6, v=0.05)
cut.card("stat", A("октаву") - 0.05, s.t1 - 0.05, text="−1 ОКТАВА", label="ГОЛОС", y=0.17, size=120)
cut.sfx(A("октаву"), "usr-bass-drop-low-swell-210", -6)

T_PU = round(C[4]["start"] - 0.1, 3)
s = cut.shot("tt2_day", round(C[5]["start"] - 0.1, 3))
h = actor(s, "hero", "geroy", (-5.4, 2.0), face=90, act="pushup", eyes="angry", mouth="grit", dir=-1, hz=2.6)
extra(s, FILL)
for i, (x, z, ch, f) in enumerate([(-6.6, 3.7, "p1", 150), (-3.2, 3.9, "p3", -140), (-6.5, 0.1, "p5", 30), (-3.4, 0.3, "p4", -40), (-6.9, 1.9, "p6", 90)]):
    a = actor(s, f"c{i}", ch, (x, z), face=f, act="phone_up" if i % 2 == 0 else "arms_crossed")
    if i % 2 == 0:
        a.hold(0, B="phone")
orbit(s, (-4.6, 2.0), 3.4, 0.5, -30, 55, 0.45, 48, h1=1.0, focus="hero", ap=4, zoom=False)
cut.card("stat", A("сто") - 0.05, s.t1 - 0.05, **{"from": 0, "to": 100, "rollAt": A("сто"), "rollDur": 1.6}, label="НА ОДНОЙ РУКЕ", y=0.17, size=170)
cut.sfx(A("сто"), "usr-energy-burst-mid-swell-176", -10)
cut.sfx(A("тротуаре"), "usr-whoosh-light-mid-swell-190", -12)

s = cut.shot("tt2_day", S[3])
h = actor(s, "hero", "geroy", (-5.4, 2.0), face=90, act="pushup", eyes="angry", mouth="grit", dir=-1, hz=2.6)
throwers = [(-6.6, 3.7, "p1", 150), (-3.2, 3.9, "p3", -140), (-6.5, 0.1, "p5", 30), (-3.4, 0.3, "p4", -40), (-6.9, 1.9, "p6", 90)]
extra(s, FILL)
coins = []
for i, (x, z, ch, f) in enumerate(throwers):
    a = actor(s, f"c{i}", ch, (x, z), face=f, act="idle")
    tt = round(A("кидают") + 0.05 + i * 0.18, 3)
    a.act(tt - s.t0, "throw")
    coins.append({"t": "block", "p": [x, z], "size": [0.16, 0.03, 0.16], "color": "#ffd84a", "solid": False, "showAt": tt + 0.12,
                  "anim": [{"t": tt + 0.12, "p": [x, 1.35, z]}, {"t": tt + 0.42, "p": [(x - 5.4) / 2, 1.9, (z + 2.0) / 2], "r": [180, 90, 0], "e": "out"},
                           {"t": tt + 0.75, "p": [-5.4 + (i - 2) * 0.22, 0.02, 2.3 + (i % 2) * 0.3], "r": [360, 180, 0], "e": "in"}]})
    cut.sfx(tt + 0.7, "usr-coin-bell-bright-tail-075" if i % 2 else "usr-coin-bell-bright-swell-083", -12)
extra(s, *coins)
ks(s, [(s.t0, [-3.9, 4.6, 7.0], [-4.7, 0.3, 2.0], 50), (-1, [-4.0, 3.2, 6.6], [-4.7, 0.4, 2.0], 48)], focus="hero", ap=3, zoom=False)
cut.card("stat", A("протеин") - 0.05, S[3] - 0.08, text="+47 ₽", label="НА ПРОТЕИН", y=0.17, size=150, color="#5ad05a")
cut.sfx(A("протеин"), "usr-cash-register-bright-snap-216", -7)

# ======================================================== 3. 0:20 — brows; the bench with the grannies goes up
s = cut.shot("tt2_yard_day", round(C[7]["start"] - 0.06, 3))
h = actor(s, "hero", "geroy_br", (2.6, 1.6), face=-15, act="idle", eyes="angry", mouth="closed")
h.expr(A("гуще") - s.t0, "angry", "grit")
ks(s, [(s.t0, [2.75, 1.7, 3.85], [2.6, 1.55, 1.6], 32), (-1, [2.45, 1.68, 3.3], [2.6, 1.56, 1.6], 30)], focus="hero", ap=12)
cut.card("stat", A("гуще") - 0.05, s.t1 - 0.05, text="+300%", label="БРОВИ", y=0.17, size=150)
cut.sfx(A("гуще"), "usr-cartoon-boing-mid-snap-285", -8)

T_LIFT = round(A("лавочку") - 0.05, 3)
LIFT_Y = 1.75
BENCH = {"t": "bench", "p": [0, 0], "w": 2.0}
BENCH_UP = {**BENCH, "anim": [{"t": 0, "p": [0, 0, 0]}, {"t": T_LIFT, "p": [0, 0, 0]}, {"t": T_LIFT + 0.6, "p": [0, LIFT_Y, 0], "e": "out"}]}


def grannies(s, lift=True, talk=None):
    out = []
    for i, (ch, x) in enumerate([("babka1", -0.45), ("babka2", 0.45)]):
        g = actor(s, ch, ch, (x, 0.05), face=0, act="sit", eyes="normal", mouth="closed", seat=0.46)
        if lift:
            if s.t0 < T_LIFT + 0.6:
                g.walk(max(0.0, T_LIFT - s.t0), (x, LIFT_Y, 0.05), dur=0.6, e="out")
            else:
                g.teleport(0.001, (x, LIFT_Y, 0.05))
        out.append(g)
    return out


s = cut.shot("tt2_yard_day", round(C[8]["start"] - 0.06, 3))
extra(s, BENCH_UP)
for x, z, r, c in YARD_CARS:
    extra(s, {"t": "car", "p": [x, z], "r": r, "color": c})
b1, b2 = grannies(s)
b1.talk(0.0, 1.2); b2.talk(1.3, 2.4)
h = actor(s, "hero", "geroy_br", (2.6, -0.6), face=-90, act="idle", eyes="angry", mouth="closed")
h.walk(0.0, (0.0, -0.58), dur=round(T_LIFT - s.t0 - 0.25, 3))
h.face(round(T_LIFT - s.t0 - 0.25, 3), 0, 0.15)
h.act(T_LIFT - s.t0 - 0.05, "hands_up")
h.expr(T_LIFT - s.t0, "angry", "grit")
kid = actor(s, "kid", "p6", (-4.0, -3.2), face=30, act="idle")
kid.act(T_LIFT - s.t0 + 0.4, "scared")
ks(s, [(s.t0, [1.0, 0.8, 6.8], [0.2, 1.3, 0.0], 50), (T_LIFT, [0.8, 0.85, 6.6], [0.1, 1.35, 0.0], 50),
       (-1, [0.6, 1.4, 6.0], [0.0, 1.9, 0.0], 48)], focus="hero", ap=3, zoom=False)
cut.sfx(T_LIFT - 0.05, "usr-thud-low-low-snap-316", -6)
cut.sfx(T_LIFT + 0.05, "riser-short", -12)
cut.sfx(A("бабушками") + 0.1, "usr-crowd-gasp-mid-swell-172", -12)

s = cut.shot("tt2_yard_day", S[4])
extra(s, BENCH_UP)
b1, b2 = grannies(s)
b1.talk(0.0, A("только") - s.t0 - 0.1)
b2.talk(A("только") - s.t0 - 0.05, A("спрашивает", end=True) - s.t0)
b2.face(A("спрашивает") - s.t0, -35, 0.3)
b2.expr(A("Наркоман") - s.t0, "angry", "o")
b2.talk(A("Наркоман") - s.t0, A("Наркоман", end=True) - s.t0 + 0.1)
h = actor(s, "hero", "geroy_br", (0.0, -0.58), face=0, act="hands_up", eyes="angry", mouth="grit")
orbit(s, (0.0, 0.0), 2.6, 2.45, 25, -20, 2.4, 40, focus="babka2", ap=6, h1=2.6)
cut.card("bubble", A("Наркоман") - 0.03, S[4] - 0.08, who="БАБУШКА", whoColor="#ff8ad0", text="Наркоман?", y=0.16, side="left")
cut.sfx(A("Наркоман") + 0.6, "usr-voice-bruh-mid-swell-226", -10)

# ======================================================== 4. 0:30 — stubble; the lamp post; blackout; the salute
LAMP = (-4.5, 6.0)                       # the punched lamp (in the location list: z=6, left side)
HERO4 = (-5.3, 6.0)
s = cut.shot("tt2_black", C[10]["start"] - 0.04)
h = actor(s, "hero", "geroy_s", HERO4, face=35, act="idle", eyes="wide", mouth="closed")
h.expr(A("щетина") - s.t0, "angry", "closed")
ks(s, [(s.t0, [-4.6, 1.72, 8.2], [-5.3, 1.55, 6.0], 32), (-1, [-4.9, 1.7, 7.7], [-5.3, 1.56, 6.0], 30)], focus="hero", ap=12)
cut.card("label", A("щетина") - 0.08, s.t1 - 0.05, text="ЩЕТИНА: +3 ДНЯ", sub="ЗА 1 СЕКУНДУ", x=0.06, y=0.15)
cut.sfx(A("щетина"), "usr-whoosh-light-bright-swell-200", -10)

s = cut.shot("tt2_black", C[11]["start"] - 0.06)
h = actor(s, "hero", "geroy_s", HERO4, face=90, act="idle", eyes="angry", mouth="grit")
h.act(T_PUNCH - s.t0 - 0.18, "punch")
h.act(T_OFF - s.t0 + 0.3, "idle")
ks(s, [(s.t0, [-4.7, 1.4, 9.6], [-4.9, 1.4, 6.0], 42), (T_OFF - 0.1, [-4.6, 1.5, 9.8], [-4.9, 1.5, 6.0], 42),
       (-1, [0.5, 8.5, 20.0], [-3.0, 1.5, -2.0], 56)], focus="hero", ap=2, zoom=False)
s.fxk(T_PUNCH - s.t0, "shake", d=0.5, v=0.07)
cut.sfx(T_PUNCH - 0.02, "usr-punch-mid-snap-390", -4)
cut.sfx(T_PUNCH, "usr-metal-crash-low-swell-310", -6)
cut.sfx(T_OFF, "shorts/power_down", -6)
cut.card("label", A("квартал") - 0.05, s.t1 - 0.05, text="КВАРТАЛ: ОФФЛАЙН", x=0.06, y=0.15, border="#ff4a2a")

T_LOOK = A("Смотрит")
T_SAL = round(A("отдаёт") - 0.05, 3)
DARK = [{"t": "lightPt", "p": [-3.0, 6.5], "y": 3.5, "i": 4.0, "d": 14, "color": "#6a88d0"},
        {"t": "lightPt", "p": [-3.5, 1.5], "y": 3.0, "i": 3.0, "d": 12, "color": "#7a90c8"}]
s = cut.shot("tt2_black", round(A("молча") - 0.15, 3))
extra(s, *DARK)
h = actor(s, "hero", "geroy_s", HERO4, face=180, act="arms_crossed", eyes="angry")
pol = actor(s, "police", "police", (-5.7, -1.8), face=0, act="idle", eyes="normal", mouth="closed")
pol.walk(0.0, (-5.7, 4.5), dur=round(T_LOOK - s.t0 - 0.05, 3))
pol.face(T_LOOK - s.t0, 0, 0.2)
pol.expr(T_LOOK - s.t0, "wide", "closed")
ks(s, [(s.t0, [-2.4, 1.5, 5.0], [-5.7, 1.3, 0.5], 46), (T_LOOK, [-1.7, 1.5, 8.2], [-5.5, 1.35, 5.0], 46),
       (-1, [-1.6, 1.5, 8.6], [-5.5, 1.35, 5.2], 45)], focus="police", ap=3, zoom=False)

s = cut.shot("tt2_black", S[5])
extra(s, *DARK)
h = actor(s, "hero", "geroy_s", HERO4, face=180, act="arms_crossed", eyes="angry")
pol = actor(s, "police", "police", (-5.7, 4.5), face=0, act="idle", eyes="wide", mouth="closed")
pol.act(T_SAL - s.t0, "salute")
pol.expr(T_SAL - s.t0, "angry", "closed")
ks(s, [(s.t0, [-3.3, 1.8, 7.3], [-5.7, 1.5, 4.5], 40), (-1, [-3.5, 1.78, 7.0], [-5.7, 1.52, 4.5], 38)], focus="police", ap=8, zoom=False)
cut.sfx(T_SAL, "usr-brass-swell-mid-tail-146", -8)

# ======================================================== 5. 0:40 — mewing; the palm stops the car on red; reverse
s = cut.shot("tt2_day", round(C[13]["start"] - 0.03, 3))
h = actor(s, "hero", "geroy_t4", (-4.6, 1.4), face=90, act="idle", eyes="angry", mouth="closed")
ks(s, [(s.t0, [-4.55, 1.68, 3.5], [-4.6, 1.6, 1.4], 30), (-1, [-4.45, 1.66, 3.1], [-4.6, 1.6, 1.4], 28)], focus="hero", ap=14)
cut.card("label", A("мьюинг") - 0.08, s.t1 - 0.03, text="МЬЮИНГ: ВКЛ", sub="ЧЕЛЮСТЬ ×2", x=0.06, y=0.15)
cut.sfx(A("мьюинг"), "usr-bone-crunch-mid-swell-186", -8)

T_HIT2 = round(A("её", after=S[5]) - 0.04, 3)
CAR_BLUE = {"t": "car", "p": [-1.5, 0], "color": "#3a6ab8", "lights": False}
TL = [{"t": "trafficLight", "p": [-4.4, -2.4], "state": "red"}, {"t": "trafficLight", "p": [4.4, -2.4], "state": "red"}]
crowd5 = [(-5.6, 2.4, "p2", 90), (-6.2, 1.0, "p4", 95), (-5.8, -0.4, "p5", 80), (-6.5, 3.4, "p1", 100)]


def crossing(s, scared_at=None):
    extra(s, *TL)
    for i, (x, z, ch, f) in enumerate(crowd5):
        a = actor(s, f"c{i}", ch, (x, z), face=f, act="idle")
        if scared_at is not None:
            a.act(scared_at - s.t0 + i * 0.06, "scared")


T_STEP = round(A("Ты", after=S[5]) - 0.05, 3)
CAR_RUN = {**CAR_BLUE, "anim": [{"t": 0, "p": [-1.5, 0, -48.0]}, {"t": round(C[13]["start"] - 0.03, 3), "p": [-1.5, 0, -48.0]},
                                {"t": T_HIT2, "p": [-1.5, 0, -2.5], "e": "linear"},
                                {"t": T_HIT2 + 0.12, "p": [-1.5, 0.18, -2.7], "r": [7, 0, 0], "e": "out"},
                                {"t": T_HIT2 + 0.45, "p": [-1.5, 0, -2.6], "r": [0, 0, 0], "e": "out"}]}


def hero5(s):
    h = actor(s, "hero", "geroy_t4", (-4.6, 1.4), face=90, act="idle", eyes="angry", mouth="closed")
    h.walk(max(0.0, A("летит") - s.t0 + 0.1), (-1.5, 0.15), dur=0.75)
    h.face(max(0.0, A("летит") - s.t0 + 0.85), 180, 0.2)
    h.act(T_HIT2 - s.t0 - 0.22, "stop")
    h.expr(T_HIT2 - s.t0 - 0.1, "angry", "grit")
    if s.t0 > A("летит") + 0.9:
        h.teleport(0.001, (-1.5, 0.15)); h.face(0.001, 180, 0.001)
    return h


s = cut.shot("tt2_day", T_STEP)
crossing(s)
hero5(s)
extra(s, CAR_RUN)
ks(s, [(s.t0, [-3.3, 2.9, 1.8], [-4.4, 3.25, -2.4], 36), (A("летит") - 0.1, [-3.35, 2.85, 1.9], [-4.4, 3.2, -2.4], 36),
       (A("летит") + 0.55, [-0.9, 1.4, 5.5], [-1.5, 1.0, -12.0], 46), (-1, [-1.0, 1.35, 5.0], [-1.5, 1.0, -12.0], 44)], focus="hero", ap=3, zoom=False)

s = cut.shot("tt2_day", round(C[14]["start"] - 0.04, 3))
crossing(s, scared_at=T_HIT2 + 0.05)
hero5(s)
extra(s, CAR_RUN)
ks(s, [(s.t0, [3.6, 1.0, 1.0], [-1.5, 1.2, -0.4], 52), (T_HIT2, [3.4, 1.0, 1.0], [-1.5, 1.2, -0.4], 52),
       (-1, [2.9, 1.1, 0.8], [-1.5, 1.25, -0.4], 48)], focus="hero", ap=4, zoom=False)
s.fxk(T_HIT2 - s.t0, "shake", d=0.55, v=0.08)
flash(T_HIT2, 0.1)
cut.card("label", C[13]["start"], A("летит") + 0.35, text="КРАСНЫЙ", sub="СВЕТОФОР", x=0.06, y=0.15, border="#ff4a2a")
cut.card("stat", T_HIT2 + 0.1, s.t1 - 0.05, text="СТОП", label="ОДНОЙ РУКОЙ", y=0.17, size=170, color="#ff5a3c")
cut.sfx(A("красный"), "usr-whoosh-roar-mid-swell-388", -6)
cut.sfx(A("машина") + 0.2, "shorts/car_horn", -9, dur=0.9)
cut.sfx(T_HIT2, "usr-metal-crash-low-swell-310", -6)
cut.sfx(T_HIT2, "hit-cinematic", -8)
cut.sfx(T_HIT2 + 0.1, "usr-crowd-gasp-mid-swell-172", -10)

T_BELT = A("пристёгивается")
T_HAZ = A("аварийку")
T_REV = round(A("уезжает") + 0.1, 3)
s = cut.shot("tt2_day", S[6])
crossing(s)
h = actor(s, "hero", "geroy_t4", (-1.5, 0.15), face=180, act="stop", eyes="angry", mouth="grit")
h.act(T_HAZ - s.t0, "arms_crossed")
h.expr(T_HAZ - s.t0, "angry", "closed")
extra(s, {**CAR_BLUE, "hazardAt": T_HAZ, "anim": [{"t": 0, "p": [-1.5, 0, -2.6]}, {"t": T_REV, "p": [-1.5, 0, -2.6]},
                                                  {"t": T_REV + 1.6, "p": [-1.5, 0, -38.0], "e": "in"}]})
ks(s, [(s.t0, [2.6, 1.8, 4.4], [-1.5, 0.95, -1.6], 50), (T_REV, [2.4, 1.75, 4.6], [-1.5, 0.95, -2.0], 48),
       (-1, [0.6, 1.6, 5.4], [-1.5, 1.1, -14.0], 44)], focus="hero", ap=3, zoom=False)
cut.card("label", T_BELT - 0.05, T_HAZ - 0.08, text="РЕМЕНЬ ✓", sub="ВОДИТЕЛЬ", x=0.06, y=0.15, border="#5ad05a")
cut.card("label", T_HAZ - 0.05, T_REV - 0.1, text="АВАРИЙКА", sub="ВОДИТЕЛЬ", x=0.06, y=0.15, border="#ffa020")
cut.card("label", T_REV - 0.05, S[6] - 0.1, text="ЗАДНИЙ ХОД", sub="ВОДИТЕЛЬ", x=0.06, y=0.15, border="#ff4a2a")
cut.sfx(T_BELT + 0.3, "switch-click", -4)
cut.sfx(T_HAZ, "usr-clock-fast-bright-late-072", -12, dur=round(T_REV - T_HAZ, 3))
cut.sfx(T_REV, "usr-digital-beeps-bright-late-271", -12, dur=1.4)
cut.sfx(T_REV + 0.1, "usr-whoosh-roar-low-swell-143", -8)

# ======================================================== 6. 0:50 — the mentor (parody) texts; the café table breaks
s = cut.shot("tt2_day", round(C[16]["start"] - 0.08, 3))
h = actor(s, "hero", "geroy_t4", (-5.5, -16.0), face=0, act="phone", eyes="normal", mouth="closed")
h.hold(0, B="phone")
h.walk(0.0, (-5.5, -11.8), dur=s.dur)
for i, (ch, x, z0, z1) in enumerate([("p1", -6.9, -5.0, -20.0), ("p3", -6.7, -7.5, -19.0), ("p2", -6.8, -22.0, -8.0), ("p5", -7.0, -24.0, -10.0)]):
    a = actor(s, f"w{i}", ch, (x, z0), face=180 if z1 < z0 else 0, act="idle")
    a.walk(0.0, (x, z1), dur=s.dur * 1.1)
s.cam([{"t": 0, "pos": {"a": "hero", "o": [3.3, 1.75, 3.57]}, "look": {"a": "hero", "o": [0.0, 1.42, 0.1]}, "fov": 52},
       {"t": round(s.dur, 3), "pos": {"a": "hero", "o": [2.15, 1.62, 4.39]}, "look": {"a": "hero", "o": [0.0, 1.45, 0.1]}, "fov": 50, "e": "linear"}],
      focus="hero", aperture=6)
cut.card("bubble", A("Пишет") - 0.02, s.t1 - 0.05, who="АРСЕН М. ✓ · ПАРОДИЯ", whoColor="#ff6a4a", text="Брат, давай на руках.", y=0.15, side="left")
cut.sfx(A("Пишет"), "usr-notify-ding-mid-swell-058", -8)

T_BREAK = round(A("ломается") - 0.02, 3)
TABLE = (5.6, -4.0)
HERO6, ARS6 = (4.78, -4.0), (6.42, -4.0)
CAFE = [{"t": "table", "p": [5.6, -6.6], "w": 1.0, "d": 0.8}, {"t": "stool", "p": [5.0, -6.6]}, {"t": "stool", "p": [6.2, -6.6]},
        {"t": "block", "p": [5.6, -1.6], "size": [0.06, 2.3, 0.06], "color": "#5a4a3a", "solid": False},
        {"t": "block", "p": [5.6, -1.6], "y": 2.3, "size": [1.8, 0.08, 1.8], "color": "#c83a2a", "solid": False},
        {"t": "menuBoard", "p": [7.42, -6.3], "y": 1.7, "r": -90, "w": 1.2, "h": 0.8, "items": [["ПРОТЕИН", "300"], ["ЯЙЦА", "90"], ["БАЗА", "0"]], "title": "МЕНЮ"}]
TBL_PARTS = [{"t": "block", "p": [5.3, -4.0], "y": 0.77, "size": [0.6, 0.08, 0.8], "tex": "wood", "color": "#6a4a2a", "solid": False, "showAt": T_BREAK,
              "anim": [{"t": T_BREAK, "p": [5.3, 0.77, -4.0]}, {"t": T_BREAK + 0.35, "p": [5.0, 0.1, -3.7], "r": [10, 20, 38], "e": "in"}]},
             {"t": "block", "p": [5.9, -4.0], "y": 0.77, "size": [0.6, 0.08, 0.8], "tex": "wood", "color": "#6a4a2a", "solid": False, "showAt": T_BREAK,
              "anim": [{"t": T_BREAK, "p": [5.9, 0.77, -4.0]}, {"t": T_BREAK + 0.38, "p": [6.2, 0.1, -4.3], "r": [-12, -15, -35], "e": "in"}]}]
for sx in (-1, 1):
    for sz in (-1, 1):
        x0, z0 = 5.6 + sx * 0.45, -4.0 + sz * 0.3
        TBL_PARTS.append({"t": "block", "p": [x0, z0], "size": [0.07, 0.72, 0.07], "tex": "wood", "color": "#6a4a2a", "solid": False, "showAt": T_BREAK,
                          "anim": [{"t": T_BREAK, "p": [x0, 0.0, z0]}, {"t": T_BREAK + 0.25, "p": [x0 + sx * 0.5, 0.5, z0 + sz * 0.6], "r": [sz * 60, 0, -sx * 70], "e": "out"},
                                   {"t": T_BREAK + 0.55, "p": [x0 + sx * 0.9, 0.03, z0 + sz * 1.0], "r": [sz * 90, 30, -sx * 90], "e": "in"}]})
TBL = {"t": "table", "p": list(TABLE), "w": 1.0, "d": 0.8, "hideAt": T_BREAK}
SPLINTERS = debris(T_BREAK, (5.6, 0.8, -4.0), 8, (0.9, 0.1), color="#7a5a32", size=(0.14, 0.05, 0.1), seed=6, up=0.8, dur=0.6, dz=0.5)


def cafe(s):
    extra(s, *CAFE, TBL, *TBL_PARTS, *SPLINTERS)
    a = actor(s, "sit", "p2", (6.2, -6.6), face=-90, act="sit", seat=0.46)
    a.act(T_BREAK - s.t0 + 0.08, "scared")
    actor(s, "bar", "barista", (7.0, -2.3), face=-120, act="arms_crossed")


s = cut.shot("tt2_day", round(C[17]["start"] - 0.06, 3))
cafe(s)
h = actor(s, "hero", "geroy_t4", HERO6, face=90, act="struggle", eyes="angry", mouth="grit")
h.act(T_BREAK - s.t0 + 0.05, "fist")
ar = actor(s, "arsen", "arsen", ARS6, face=-90, act="struggle", eyes="angry", mouth="grit")
ar.act(T_BREAK - s.t0 + 0.05, "jolt")
ar.expr(T_BREAK - s.t0 + 0.05, "wide", "o")
orbit(s, TABLE, 3.7, 1.3, -38, 14, 1.1, 54, r1=3.3, focus="hero", ap=4, zoom=False)
s.fxk(T_BREAK - s.t0, "shake", d=0.5, v=0.07)
flash(T_BREAK, 0.08)
cut.card("label", s.t0 + 0.05, s.t1 - 0.05, text="НАСТАВНИК", sub="ПАРОДИЯ", x=0.06, y=0.26, border="#ff4a2a")
cut.card("stat", A("секунду", after=S[6]) - 0.05, s.t1 - 0.05, text="0,9 СЕК", label="СТОЛИК: ВСЁ", y=0.15, size=120)
cut.sfx(s.t0 + 0.05, "usr-punch-low-swell-298", -10)
cut.sfx(T_BREAK, "usr-thud-low-low-snap-327", -3)
cut.sfx(T_BREAK + 0.02, "usr-bone-crunch-mid-swell-186", -6)

s = cut.shot("tt2_day", round(A("отвечаешь") - 0.1, 3))
cafe(s)
h = actor(s, "hero", "geroy_t4", HERO6, face=90, act="arms_crossed", eyes="angry", mouth="closed")
ar = actor(s, "arsen", "arsen", ARS6, face=-120, act="phone", eyes="wide", mouth="closed")
ar.hold(0, B="phone")
ks(s, [(s.t0, [4.9, 1.62, -1.6], [6.4, 1.45, -4.0], 36), (-1, [5.15, 1.6, -2.0], [6.4, 1.47, -4.0], 33)], focus="arsen", ap=8)
cut.card("label", s.t0 + 0.05, s.t1 - 0.05, text="НАСТАВНИК", sub="ПАРОДИЯ", x=0.06, y=0.30, border="#ff4a2a")
cut.card("bubble", A("Учить") - 0.02, S[7] - 0.05, who="АРСЕН М. ✓ · ПАРОДИЯ", whoColor="#ff6a4a", text="Учить тебя больше нечему.", y=0.15, side="left")
cut.sfx(A("Учить"), "usr-notify-ding-mid-swell-102", -8)

s = cut.shot("tt2_day", S[7])
cafe(s)
h = actor(s, "hero", "geroy_t4", HERO6, face=55, act="phone", eyes="angry", mouth="closed")
h.hold(0, B="phone")
ks(s, [(s.t0, [3.85, 1.7, -2.15], [4.8, 1.55, -4.0], 34), (-1, [4.0, 1.68, -2.5], [4.8, 1.56, -4.0], 31)], focus="hero", ap=10)
cut.card("bubble", A("Это") + 0.02, S[7] - 0.05, who="ТЫ", whoColor="#7ad0ff", text="Это база.", y=0.27, side="right", bg="#d8f0ff")
cut.sfx(A("база"), "usr-cinema-boom-low-tail-184", -7, dur=1.5)

# ======================================================== 7. 1:00 — the beard; the sneeze sets off every car alarm; pigeons pay rent
HERO7 = (0.0, 2.0)
YCARS = [{"t": "car", "p": [x, z], "r": r, "color": c} for x, z, r, c in YARD_CARS]
s = cut.shot("tt2_yard_night", round(C[19]["start"] - 0.06, 3))
extra(s, *YCARS)
h = actor(s, "hero", "geroy_t6", HERO7, face=0, act="arms_crossed", eyes="angry", mouth="closed")
ks(s, [(s.t0, [0.3, 1.74, 4.25], [0.0, 1.55, 2.0], 32), (-1, [0.15, 1.7, 3.75], [0.0, 1.56, 2.0], 30)], focus="hero", ap=12)
cut.card("stat", A("борода") - 0.05, s.t1 - 0.05, text="БОРОДА", label="+40 СМ ЗА 1 СЕК", y=0.17, size=130)
cut.sfx(A("борода"), "usr-whoosh-down-low-swell-123", -8)

T_SNZ = round(A("чихаешь") + 0.12, 3)
T_ALARM = round(A("срабатывают") - 0.05, 3)
s = cut.shot("tt2_yard_night", round(C[20]["start"] - 0.06, 3))
extra(s, *[{**c, "hazardAt": round(T_ALARM + i * 0.09, 3), "hazardI": 6} for i, c in enumerate(YCARS)])
extra(s, {"t": "crows", "p": [2.0, 2.8], "n": 6, "spread": 2.4, "color": "#7a808c",
          "anim": [{"t": 0, "p": [2.0, 0, 2.8]}, {"t": T_SNZ + 0.05, "p": [2.0, 0, 2.8]}, {"t": T_SNZ + 1.2, "p": [5.0, 7.0, -2.0], "e": "in"}], "hideAt": T_SNZ + 1.25})
h = actor(s, "hero", "geroy_t6", HERO7, face=0, act="idle", eyes="closed", mouth="o")
h.act(T_SNZ - s.t0, "jolt")
h.expr(T_SNZ - s.t0 + 0.25, "angry", "grit")
ks(s, [(s.t0, [0.35, 1.55, 4.6], [0.0, 1.45, 2.0], 38), (T_SNZ + 0.35, [0.35, 1.6, 4.7], [0.0, 1.45, 2.0], 40),
       (T_ALARM + 0.5, [5.0, 6.5, 12.5], [0.0, 0.6, 1.0], 54), (-1, [6.2, 7.0, 13.0], [0.0, 0.5, 1.0], 54)], focus="hero", ap=2)
s.fxk(T_SNZ - s.t0, "shake", d=0.8, v=0.1)
cut.sfx(T_SNZ, "usr-cartoon-splat-mid-snap-337", -5)
cut.sfx(T_SNZ + 0.1, "usr-whoosh-light-bright-swell-200", -10)
cut.sfx(T_ALARM, "siren-far", -9, dur=round(s.t1 - T_ALARM + 0.3, 3))
cut.sfx(T_ALARM + 0.15, "shorts/car_horn", -12, dur=0.5)
cut.sfx(T_ALARM + 0.1, "usr-digital-beeps-bright-late-060", -14, dur=1.2)

T_MOVE = A("бороду")
s = cut.shot("tt2_yard_night", S[8])
extra(s, *[{**c, "hazardAt": round(T_ALARM + i * 0.09, 3), "hazardI": 6} for i, c in enumerate(YCARS)])
for i, (dx, dz) in enumerate([(2.6, 3.4), (-2.4, 3.0)]):
    extra(s, {"t": "crows", "p": [HERO7[0] + dx, HERO7[1] + dz], "n": 1, "spread": 0.01, "color": "#7a808c", "hideAt": T_MOVE,
              "anim": [{"t": 0, "p": [HERO7[0] + dx, 3.2, HERO7[1] + dz]}, {"t": A("голубя") + i * 0.1, "p": [HERO7[0] + dx, 3.2, HERO7[1] + dz]},
                       {"t": T_MOVE, "p": [HERO7[0] + (i - 0.5) * 0.3, 1.88, HERO7[1] + 0.05], "e": "inOut"}]})
notes = []
for i in range(3):
    t0 = A("наличными") + i * 0.12
    notes.append({"t": "block", "p": [0, 2], "size": [0.17, 0.01, 0.08], "color": "#5ab04a", "solid": False, "showAt": round(t0, 3),
                  "anim": [{"t": round(t0, 3), "p": [HERO7[0] + (i - 1) * 0.12, 1.95, HERO7[1] + 0.1]},
                           {"t": round(t0 + 0.9, 3), "p": [HERO7[0] + (i - 1) * 0.35, 0.02, HERO7[1] + 0.6 + i * 0.1], "r": [40, 300, 20], "e": "out"}]})
extra(s, *notes)
h0 = actor(s, "hero0", "geroy_t6", HERO7, face=0, act="arms_crossed", eyes="angry", mouth="closed")
h0.show(T_MOVE - s.t0, False)
h1 = actor(s, "hero", "geroy_t6p", HERO7, face=0, act="arms_crossed", eyes="normal", mouth="smile")
h1.show(0, False); h1.show(T_MOVE - s.t0, True)
ks(s, [(s.t0, [0.2, 1.8, 4.35], [0.0, 1.7, 2.0], 36), (-1, [0.1, 1.76, 3.9], [0.0, 1.66, 2.0], 33)], focus="hero", ap=10)
cut.card("stat", A("платят") - 0.05, S[8] - 0.08, text="+500 ₽", label="АРЕНДА ОТ ГОЛУБЕЙ / МЕС", y=0.17, size=140, color="#5ad05a")
cut.sfx(T_MOVE, "usr-cartoon-bloop-mid-snap-384", -8)
cut.sfx(A("платят"), "usr-coin-bell-bright-swell-083", -12)
cut.sfx(A("наличными"), "usr-cash-register-bright-snap-216", -7)

# ======================================================== 8. 1:10 — glowing eyes; out of the entrance straight through the wall
s = cut.shot("tt2_podezd", round(C[22]["start"] - 0.06, 3))
extra(s, {"t": "lightPt", "p": [0.0, 0.45], "y": 1.62, "i": 2.5, "d": 2.4, "color": "#6ae0ff", "onAt": A("светятся") - 0.05})
h = actor(s, "hero", "geroy_t8p", (0.0, 0.0), face=0, act="idle", eyes="closed", mouth="closed")
h.expr(A("светятся") - s.t0 - 0.05, "angry", "closed")
ks(s, [(s.t0, [0.06, 1.72, 2.0], [0.0, 1.62, 0.0], 30), (-1, [0.03, 1.68, 1.45], [0.0, 1.64, 0.0], 28)], focus="hero", ap=16)
cut.sfx(A("светятся"), "reveal-glow", -6)
cut.sfx(A("светятся"), "usr-energy-burst-mid-swell-376", -10)

T_WALL = round(A("стену") - 0.08, 3)
WALLX, FACE_Z = 3.0, -7.0
WALL = [{"t": "block", "p": [WALLX, FACE_Z + 0.12], "size": [1.6, 2.4, 0.25], "tex": "concrete", "color": "#9a8a7a", "solid": False, "hideAt": T_WALL},
        {"t": "block", "p": [WALLX, FACE_Z + 0.015], "size": [1.5, 2.3, 0.03], "color": "#0a0806", "solid": False, "showAt": T_WALL},
        {"t": "lightPt", "p": [WALLX, FACE_Z + 0.6], "y": 1.2, "i": 3.0, "d": 6, "color": "#ffcf8a", "onAt": T_WALL}]
RUBBLE = debris(T_WALL, (WALLX, 1.2, FACE_Z + 0.2), 14, (1.5, 2.2), color="#9a8a7a", size=(0.32, 0.2, 0.22), seed=3, up=1.0, dur=0.75, dz=1.2)
s = cut.shot("tt2_yard_night", round(C[23]["start"] - 0.05, 3))
extra(s, *WALL, *RUBBLE, *YCARS)
h = actor(s, "hero", "geroy_t8p", (WALLX, FACE_Z - 0.6), face=0, act="idle", eyes="angry", mouth="grit")
h.show(0, False); h.show(T_WALL - s.t0, True)
h.run(T_WALL - s.t0, (WALLX, -4.2), dur=0.55)
h.walk(T_WALL - s.t0 + 0.6, (WALLX, -3.2), dur=0.9)
ks(s, [(s.t0, [6.2, 1.3, 0.3], [2.6, 1.6, -6.6], 48), (T_WALL, [6.0, 1.3, 0.0], [2.8, 1.5, -6.4], 48),
       (-1, [5.0, 1.2, 0.2], [3.0, 1.35, -3.6], 46)], focus="hero", ap=3, zoom=False)
s.fxk(T_WALL - s.t0, "shake", d=0.6, v=0.1)
flash(T_WALL, 0.1)
cut.sfx(T_WALL, "hit-cinematic", -7)
cut.sfx(T_WALL, "usr-metal-crash-low-swell-310", -7)
cut.sfx(T_WALL + 0.05, "usr-thud-low-low-snap-095", -4)
cut.sfx(T_WALL + 0.1, "usr-glass-shatter-bright-swell-099", -12)
cut.card("label", A("Двери") - 0.05, A("Голуби") - 0.1, text="ДВЕРИ", sub="ДЛЯ СЛАБЫХ", x=0.06, y=0.15)

s = cut.shot("tt2_yard_night", round(A("Ты", after=A("аплодируют")) - 0.1, 3))
extra(s, *WALL, *RUBBLE, *YCARS)
h = actor(s, "hero", "geroy_t8p", (WALLX, -3.2), face=0, act="idle", eyes="angry", mouth="smile")
h.walk(0.0, (WALLX, -2.2), dur=s.dur)
ks(s, [(s.t0, [3.45, 1.1, 0.3], [3.0, 1.75, -3.2], 40), (-1, [3.4, 1.15, 0.9], [3.0, 1.75, -2.2], 40)], focus="hero", ap=6, zoom=False)
cut.sfx(A("Голуби") + 0.1, "usr-applause-mid-tail-057", -8, dur=1.9)
cut.card("bubble", A("аплодируют") - 0.05, s.t1 - 0.05, who="ГОЛУБИ", whoColor="#b8c0cc", text="*ХЛОП-ХЛОП-ХЛОП*", y=0.17, side="right")

s = cut.shot("tt2_yard_night", S[9])
extra(s, *WALL, *RUBBLE, *YCARS)
h = actor(s, "hero", "geroy_t8p", (WALLX, -2.2), face=0, act="arms_crossed", eyes="angry", mouth="closed")
orbit(s, (WALLX, -2.2), 3.6, 0.55, -40, 25, 1.4, 46, focus="hero", ap=4, r1=3.2, h1=0.7, zoom=False)
cut.card("stat", A("гигачад", after=S[8]) - 0.05, S[9] - 0.08, text="ГИГАЧАД", label="ОФИЦИАЛЬНО", y=0.17, size=140)
cut.sfx(A("гигачад", after=S[8]), "usr-cinema-boom-low-tail-024", -5, dur=1.4)

# ======================================================== 9. 1:20 — back to the teaser: mom calls; the hat
SNOW = [{"kind": "snow", "n": 500, "box": [-7, 0.2, -10, 4, 6, 1.2]}]
CAR_DONE = {**CAR_RED, "p": [-1.5, -2.75], "hazardAt": 0.0}
s = cut.shot("tt2_night", round(A("Сынок") - 0.08, 3), particles=SNOW)
extra(s, CAR_DONE)
h = actor(s, "hero", "geroy_t8p", (-1.5, 0.2), face=0, act="arms_crossed", eyes="angry", mouth="closed")
h.act(A("Звонит") - s.t0 + 0.2, "phone"); h.hold(A("Звонит") - s.t0 + 0.2, B="phone")
ks(s, [(s.t0, [-1.1, 1.5, 4.9], [-1.5, 1.35, 0.2], 42), (-1, [-1.3, 1.55, 4.3], [-1.5, 1.4, 0.2], 40)], focus="hero", ap=6, zoom=False)
cut.card("notif", A("Звонит") - 0.05, s.t1 - 0.05, app="ВХОДЯЩИЙ ВЫЗОВ", text="МАМА ❤", icon="#3a8a4a", glyph="✆", y=0.16)
cut.sfx(A("Звонит"), "usr-notify-two-tone-mid-swell-103", -6)

s = cut.shot("tt2_night", round(C[25]["start"] - 0.04, 3), particles=SNOW)
extra(s, CAR_DONE)
h = actor(s, "hero", "geroy_t8p", (-1.5, 0.2), face=0, act="phone_ear", eyes="wide", mouth="o")
h.hold(0, B="phone")
ks(s, [(s.t0, [-1.32, 1.68, 2.25], [-1.5, 1.6, 0.2], 32), (-1, [-1.4, 1.66, 1.95], [-1.5, 1.6, 0.2], 30)], focus="hero", ap=12)
cut.card("bubble", A("Сынок") - 0.03, s.t1 - 0.05, who="МАМА ❤", whoColor="#ff8ad0", text="Сынок, ты шапку надел? На улице минус два.", y=0.15, side="left")

s = cut.shot("tt2_night", round(C[26]["start"] - 0.04, 3), particles=SNOW)
extra(s, CAR_DONE)
h = actor(s, "hero", "geroy_t8p", (-1.5, 0.2), face=0, act="phone_ear", eyes="wide", mouth="o")
h.hold(0, B="phone")
h.act(T_ZERO - s.t0 - 0.1, "cower")
ks(s, [(s.t0, [-1.4, 1.62, 2.0], [-1.5, 1.55, 0.2], 30), (-1, [-1.35, 1.5, 4.4], [-1.5, 1.2, 0.2], 46)], focus="hero", ap=6)
s.fxk(T_ZERO - s.t0, "shake", d=0.4, v=0.04)
cut.card("stat", T_ZERO - 0.05, s.t1 - 0.03, text="0", label="ТЕСТОСТЕРОН", y=0.17, size=170, color="#ff5a3c")
cut.sfx(T_ZERO - 0.35, "usr-slide-whistle-bright-swell-088", -6)

T_HAT = A("шапку", after=A("бежит"))
s = cut.shot("tt2_night", END_STORY, particles=SNOW)
extra(s, CAR_DONE)
h0 = actor(s, "hero0", "geroy_t8p", (-1.5, 0.2), face=-90, act="idle", eyes="wide", mouth="o")
h0.run(0.1, (-7.0, 3.0), dur=0.7); h0.show(0.85, False)
h1 = actor(s, "hero", "geroy_t8h", (-7.0, 3.2), face=90, act="idle", eyes="normal", mouth="smile")
h1.show(0, False); h1.show(T_HAT - s.t0 + 0.05, True)
h1.walk(T_HAT - s.t0 + 0.1, (-1.5, 0.6), dur=round(END_STORY - T_HAT - 0.15, 3)); h1.face(END_STORY - s.t0 - 0.05, 0)
ks(s, [(s.t0, [0.2, 1.6, 8.0], [-2.6, 1.2, 0.8], 48), (-1, [-0.2, 1.6, 7.4], [-2.0, 1.2, 0.8], 46)], focus=None, ap=2, zoom=False)
cut.sfx(s.t0 + 0.1, "usr-whoosh-whip-mid-swell-241", -8)
cut.sfx(T_HAT, "usr-voice-bruh-mid-swell-226", -8)

# ======================================================== 10. CTA — same voice, the channel profile, «шапку профиля»
t0 = ep.t
s = ep.shot("tt2_night", round(END - t0, 3), particles=SNOW)
extra(s, CAR_DONE)
a = s.actor("hero", "geroy_t8h", at=(-1.5, 0.6), face=0)
a.act(0, "wave"); a.expr(0, "happy", "smile")
cam(s, [(0, [-1.5, 1.5, 3.4], [-1.5, 1.2, 0.6], 40), (-1, [-1.5, 1.5, 3.0], [-1.5, 1.2, 0.6], 38)], focus="hero", ap=8, zoom=False)
t_hl = A("шапку", after=S[10])
cut.card("black", t0, END, color="rgba(0,0,0,0.55)", fi=0.25, fo=0.01)
cut.card("profile", t0, END, hlAt=t_hl)
ep.sfx(t_hl, "pk-notify-notification-sfx-1", -6)

# ----------------------------------------------------------------- sound: voice + ambience + SFX, NO music (mike 10.11)
ep.voice(0, copy_voice(KID, "testo2"), gain=0)
w.subs(ep, 0.3)
for sub, c in zip(ep.subs[-len(C):], C):
    sub["t1"] = round(min(sub["t1"], c["end"] + 0.8), 3)
ep.amb(0.0, T_RW, "shorts/city_dark", gain=-24, fi=0.05, fo=0.2)
ep.amb(T_RW, S[3], "shorts/street_day", gain=-25, fi=0.1, fo=0.3)
ep.amb(S[3], S[4], "shorts/street_day", gain=-31, fi=0.2, fo=0.3)
ep.amb(S[4], T_OFF, "shorts/city_dark", gain=-25, fi=0.2, fo=0.05)
ep.amb(T_OFF, S[5], "city-hum", gain=-34, fi=0.4, fo=0.3)
ep.amb(S[5], S[7], "shorts/street_day", gain=-25, fi=0.2, fo=0.3)
ep.amb(round(C[17]["start"] - 0.06, 3), S[7], "shorts/cafe", gain=-30, fi=0.3, fo=0.3)
ep.amb(S[7], round(C[22]["start"] - 0.06, 3), "shorts/city_dark", gain=-27, fi=0.2, fo=0.1)
ep.amb(round(C[23]["start"] - 0.05, 3), S[9], "shorts/city_dark", gain=-27, fi=0.1, fo=0.3)
ep.amb(S[9], END, "shorts/city_dark", gain=-27, fi=0.3, fo=1.0)
ep.save()
