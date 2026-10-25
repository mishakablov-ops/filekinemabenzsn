"""Storyboard for fr-gibrid: a morning in France, 'gibrid' style (Reel Studio only, no Blender).
Street walk -> croissants in the pastry case -> coffee on a terrace -> the Eiffel Tower at the end of a street ->
330 m counter -> CTA (iPhone flips to the TikTok profile). Hero = guy in the white cap and orange hoodie.

    python -I storyboard.py   -> engine/public/projects/fr-gibrid/spec.json
"""
import json
from pathlib import Path

RS = Path(__file__).resolve().parents[1] / "AIpollon-Reel-Studio" / "skills" / "reel-studio"
P = RS / "engine" / "public" / "projects" / "fr-gibrid"

HERO = {"hero": True}
TOWER_COL = "#A9825F"


def k(t, pos, tgt, fov=None, ease=None):
    d = {"t": t, "pos": pos, "target": tgt}
    if fov:
        d["fov"] = fov
    if ease:
        d["ease"] = ease
    return d


def box(size, pos, color, rotY=0.0):
    return {"type": "box", "size": [round(v, 3) for v in size], "pos": [round(v, 3) for v in pos], "rotY": rotY, "color": color}


def eiffel(cx, cz, s=1.0, col=TOWER_COL):
    """Low-poly Eiffel Tower from stacked boxes (Scene3D boxes only turn around Y, so the legs are stepped).
    Proportions of the real one: 1st deck at 17 % of the height, 2nd at 35 %, top deck at 84 %."""
    H = 64 * s
    out = []
    seg = 2.0 * s
    y1, y2, y3 = 0.17 * H, 0.35 * H, 0.84 * H
    B, b2 = 11.0 * s, 3.0 * s

    def half(y):                      # leg / column offset from the axis
        if y <= y2:
            return B - (B - b2) * (y / y2) ** 0.7
        return b2 - (b2 - 0.7 * s) * ((y - y2) / (y3 - y2)) ** 0.9

    y = 0.0
    while y < 0.62 * H:               # four legs, then four corner columns
        u = y / H
        w = max(0.5 * s, (2.8 - 3.2 * u) * s)
        h = half(y + seg / 2)
        for sx in (-1, 1):
            for sz in (-1, 1):
                out.append(box([w, seg * 1.04, w], [cx + sx * h, y, cz + sz * h], col))
        y += seg
    while y < y3:                     # solid upper shaft
        h = half(y + seg / 2)
        out.append(box([2 * h + 0.6 * s, seg * 1.04, 2 * h + 0.6 * s], [cx, y, cz], col))
        y += seg
    for yy, extra, th in ((y1, 3.4, 1.5), (y2, 2.4, 1.2)):
        h = half(yy)
        out.append(box([2 * h + extra * s, th * s, 2 * h + extra * s], [cx, yy, cz], col))
    out.append(box([2.2 * s, 2.4 * s, 2.2 * s], [cx, y3, cz], col))
    out.append(box([0.35 * s, 9 * s, 0.35 * s], [cx, y3 + 2.4 * s, cz], col))
    return out


def paris_street():
    """Pedestrian street of six-storey houses opening onto the tower far away."""
    objs = []
    for side, face in ((-1, 1), (1, -1)):
        z, i = 10.0, 0
        while z > -70:
            d = 9 + (i * 37 % 6)
            objs.append({"type": "building", "pos": [side * 11.5, 0, z - d / 2], "w": 7, "h": 15 + (i * 53 % 6), "d": d - 0.2,
                         "face": face, "lit": 0.35, "seed": i * 7 + (3 if side > 0 else 0)})
            z -= d
            i += 1
        for z in range(6, -70, -10):
            objs.append({"type": "tree", "pos": [side * 6.2, 0, z], "s": 1.0})
        for z in range(1, -70, -10):
            objs.append({"type": "streetlamp", "pos": [side * 5.6, 0, z], "rotY": 0 if side > 0 else 3.14159, "on": True})
    objs += eiffel(0, -170, 0.85)
    return objs


# only real covers in the grid, the rest are empty placeholders (as in mir-bez-granic)
TILES = ["projects/mir-bez-granic/cover.jpg", "brand/tiles/quiet-evenings.jpg", "", "", "", "", "", "", ""]
PROFILE = {"block": "TikTokProfile", "props": {
    "dark": True, "name": "aipollon", "handle": "videopollon", "badge": "Verified business",
    "bio": "Даем возможность делать самые качественные ролики с ии прямо здесь 👇🏻",
    "link": "https://t.me/aipollonvideo", "avatar": "brand/aipollon-avatar.png",
    "tiles": TILES, "pinned": 1, "highlightAt": "@шапку"}}

sfx = [
    ("@Утро", "pk-digital-digitasl-burst-sfx", 0.55, True),
    ("@Франции", "pk-pop-ui-menu", 0.5, True),
    ("@круассаном", "pk-click-ui-button", 0.55, True),
    ("@Кофе", "pk-pop-ui-menu", 0.5, True),
    ("@спешить", "pk-notify-notification-sfx-1", 0.5, True),
    ("@башня", "pk-shimmer-ui-dissolvre-sfx", 0.6, False),
    ("@330", "pk-digital-data-load-sfx-1", 0.55, False),
    ("@Парижем", "pk-click-ui-button", 0.5, True),
    ("@Кстати", "pk-shimmer-ui-dissolvre-sfx", 0.6, False),
    ("@нейросеть", "pk-pop-ui-menu", 0.55, True),
    ("@шапку", "pk-click-ui-button", 0.7, True),
    ("@профиля", "pk-notify-notification-sfx-1", 0.8, True),
]

STREET = paris_street()

scenes = [
    # 1. hook: morning street, we follow the hero (slam card over it)
    {"id": "street", "at": 0, "camera": "still",
     "bg": {"block": "Street3D", "props": {"time": "day", "cam": "follow", "cars": 0, "seed": "fr", "walkers": [
         {"x": 4.6, "z": 13.5, "speed": 1.5, "dir": -1, "seed": 1, "look": HERO},
         {"x": -4.6, "z": 2, "speed": 1.25, "dir": 1, "seed": 3},
         {"x": -5.75, "z": -8, "speed": 1.4, "dir": -1, "seed": 4},
         {"x": 5.75, "z": -6, "speed": 1.4, "dir": -1, "seed": 5},
         {"x": -4.6, "z": -22, "speed": 1.25, "dir": 1, "seed": 6},
         {"x": 5.2, "z": -15, "speed": 0, "pose": "phone", "seed": 7}]}, "dim": 0.2}},
    # 2. croissants in the pastry case, the barista behind
    {"id": "croissants", "at": "@Пахнет", "transition": "zoom", "camera": "still",
     "bg": {"block": "Room3D", "props": {"preset": "cafe", "lights": "day", "build": False,
                                         "cam": [k(0, [0.15, 1.55, 0.75], [-0.2, 1.18, -1.6], 38), k(2.4, [0.0, 1.5, 0.4], [-0.25, 1.16, -1.6], 38)],
                                         "people": [{"pose": "stand", "pos": [0.2, 0, -2.35], "rotY": 0, "seed": 5}]}}},
    # 3. coffee on the terrace, nowhere to hurry
    {"id": "terrace", "at": "@Кофе", "transition": "push", "camera": "still",
     "bg": {"block": "Scene3D", "props": {
         "look": "dusk", "lights": "sunset", "pop": False, "ground": {"size": 60, "color": "#5C5751"},
         "cam": [k(0, [1.1, 1.65, 3.9], [-0.7, 1.05, -0.8], 40), k(3.4, [0.85, 1.6, 3.45], [-0.75, 1.05, -0.8], 40)],
         "objects": [
             {"type": "building", "pos": [0, 0, -7], "rotY": -1.5708, "w": 6, "h": 13, "d": 16, "face": 1, "lit": 0.35, "seed": 3},
             {"type": "table", "pos": [-0.9, 0, 0.1], "r": 0.42, "h": 0.74},
             {"type": "chair", "pos": [-0.9, 0, -0.6]},
             {"type": "person", "pose": "sit", "pos": [-0.9, 0.05, -0.6], "rotY": 0, "seed": 1, "look": HERO},
             {"type": "mug", "pos": [-0.78, 0.765, 0.2]},
             {"type": "table", "pos": [1.4, 0, -1.5], "r": 0.42, "h": 0.74},
             {"type": "chair", "pos": [1.4, 0, -2.2]},
             {"type": "person", "pose": "sit", "pos": [1.4, 0.05, -2.2], "rotY": 0, "seed": 6},
             {"type": "mug", "pos": [1.48, 0.765, -1.42]},
             {"type": "table", "pos": [-3.0, 0, -1.7], "r": 0.42, "h": 0.74},
             {"type": "chair", "pos": [-3.0, 0, -2.4]},
             {"type": "person", "pose": "sit", "pos": [-3.0, 0.05, -2.4], "rotY": 0, "seed": 9},
             box([0.07, 2.3, 0.07], [1.4, 0, -1.5], "#3A3936"), box([2.3, 0.12, 2.3], [1.4, 2.3, -1.5], "#D8C8B0"),
             box([0.07, 2.3, 0.07], [-3.0, 0, -1.7], "#3A3936"), box([2.3, 0.12, 2.3], [-3.0, 2.3, -1.7], "#A15E44"),
             {"type": "person", "pose": "walk", "pos": [-7, 0, -3.1], "walkTo": [7, 0, -3.1], "walkDur": 8, "seed": 11},
             {"type": "person", "pose": "walk", "pos": [6, 0, -2.75], "walkTo": [-8, 0, -2.75], "walkDur": 9, "seed": 12},
         ]}},
     "layers": [{"block": "NotificationStack", "pos": "lower", "props": {"items": [
         {"app": "Календарь", "text": "Сегодня: никаких планов", "at": "@спешить"}]}}]},
    # 4. the tower at the end of the street, the hero walks towards it
    {"id": "tower-street", "at": "@А в конце", "transition": "whip", "camera": "still",
     "bg": {"block": "Scene3D", "props": {
         "look": "dusk", "lights": "sunset", "pop": False, "ground": {"size": 420, "color": "#57514B"},
         "cam": [k(0, [1.4, 1.75, 9.0], [0, 8, -170], 44), k(2.2, [1.3, 1.85, 6.8], [0, 9, -170], 44)],
         "objects": STREET + [
             {"type": "person", "pose": "walk", "pos": [0.9, 0, 4.2], "walkTo": [0.9, 0, -0.2], "walkDur": 3.2, "seed": 1, "look": HERO},
             {"type": "person", "pose": "walk", "pos": [-2.6, 0, -6], "walkTo": [-2.6, 0, 2], "walkDur": 6, "seed": 13},
             {"type": "person", "pose": "walk", "pos": [3.2, 0, -14], "walkTo": [3.2, 0, -22], "walkDur": 6, "seed": 14},
         ]}}},
    # 5. 330 metres: low angle up the tower, counter
    {"id": "tower-up", "at": "@330", "transition": "zoom", "camera": "still",
     "bg": {"block": "Scene3D", "props": {
         "look": "dusk", "lights": "sunset", "pop": False, "ground": {"size": 420, "color": "#57514B"},
         "cam": [k(0, [16, 1.8, -128], [0, 26, -170], 52), k(2.6, [13.5, 2.2, -131], [0, 30, -170], 52)],
         "objects": STREET}, "dim": 0.35},
     "layers": [{"block": "Counter", "props": {"from": 0, "to": 330, "label": "метр|метра|метров", "size": 220, "dur": 1.0}}]},
    # 6. CTA over the tower street: iPhone rises showing its back, flips to the profile
    {"id": "cta", "at": "@Кстати", "transition": "fade", "camera": "still",
     "bg": {"block": "Scene3D", "props": {
         "look": "dusk", "lights": "sunset", "pop": False, "ground": {"size": 420, "color": "#57514B"},
         "cam": [k(0, [1.3, 1.85, 6.8], [0, 9, -170], 44), k(7, [1.2, 1.9, 5.6], [0, 9.5, -170], 44)],
         "objects": STREET}, "dim": 0.5},
     "layers": [{"block": "IPhone17", "pos": "full", "enter": "none", "props": {
         "enter": "flip", "flipAt": "@нейросеть", "flipDur": 1.2, "float": True, "shadow": 0, "screen": PROFILE,
         "cam": [k(0, [0, 2.3, 10.8], [0, 2.25, 0], 30), k(2.9, [0.35, 2.32, 10.4], [0, 2.25, 0], 30),
                 k(3.8, [0, 2.53, 5.4], [0, 2.53, 0], 30, "inOut"), k(7, [0, 2.5, 5.1], [0, 2.5, 0], 30)]}}]},
]

spec = {
    "id": "fr-gibrid", "mode": "explainer", "style": "dusk", "fps": 60,
    "voice": {"src": "projects/fr-gibrid/voice.wav", "words": "projects/fr-gibrid/words.json"},
    "music": {"src": "music/lofi-warm.m4a", "volume": 0.12, "duck": 0.45},
    "tail": 2.0,
    "autoSfx": False,
    "captions": {"mode": "editorial", "pos": "top", "uppercase": True},
    "sfx": [{"at": a, "id": i, "volume": v, "alignPeak": ap} for a, i, v, ap in sfx],
    "scenes": scenes,
}
P.mkdir(parents=True, exist_ok=True)
(P / "spec.json").write_text(json.dumps(spec, ensure_ascii=False, indent=1), encoding="utf-8")
print("scenes", len(scenes), "sfx", len(sfx), "tower boxes", len(eiffel(0, 0, 0.85)), "street objects", len(STREET))
