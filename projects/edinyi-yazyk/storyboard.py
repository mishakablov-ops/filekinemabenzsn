"""Storyboard for edinyi-yazyk: 'what if the whole world spoke one language'. Style 'gibrid' engine, theme `fresh`
(natural colours, white sentence-case captions low in the frame with a yellow pill on the spoken word).
Realistic CC0 Poly Haven models (engine/public/models/ph) + kit people in the `real` palette, Earth globe over a blue sky.

    python -I storyboard.py   -> engine/public/projects/edinyi-yazyk/spec.json
"""
import json
from pathlib import Path

RS = Path(__file__).resolve().parents[1] / "AIpollon-Reel-Studio" / "skills" / "reel-studio"
P = RS / "engine" / "public" / "projects" / "edinyi-yazyk"
HERO = {"hero": True}


def k(t, pos, tgt, fov=None, ease=None):
    d = {"t": t, "pos": pos, "target": tgt}
    if fov:
        d["fov"] = fov
    if ease:
        d["ease"] = ease
    return d


def m(name, pos, rotY=0.0, **kw):
    d = {"type": "model", "src": f"models/ph/{name}/{name}.gltf", "pos": [round(v, 3) for v in pos], "rotY": rotY}
    d.update(kw)
    return d


def box(size, pos, color, rotY=0.0, **kw):
    d = {"type": "box", "size": [round(v, 3) for v in size], "pos": [round(v, 3) for v in pos], "rotY": rotY, "color": color}
    d.update(kw)
    return d


def person(pos, rotY=0.0, pose="stand", seed=1, **look):
    d = {"type": "person", "pos": pos, "rotY": rotY, "pose": pose, "seed": seed}
    if look:
        d["look"] = look
    return d


WALL, WALL2, OAK = "#EEEBE5", "#E3DFD8", "#B48A60"

# ---------------------------------------------------------------- sets
CAFE = [
    box([10, 3.2, 0.15], [0, 0, -2.3], WALL), box([0.15, 3.2, 9], [-2.7, 0, 1.5], WALL2),
    box([1.7, 1.3, 0.04], [0.35, 1.0, -2.2], "#CFE6F7"), box([1.84, 0.08, 0.1], [0.35, 0.96, -2.18], "#FFFFFF"),
    m("hanging_picture_frame_01", [-1.35, 1.75, -2.2]),
    m("round_wooden_table_01", [0, 0, 0], h=0.76),
    m("tea_set_01", [0.12, 0.76, -0.05], s=0.62),
    m("wooden_bowl_01", [-0.33, 0.76, 0.22]), m("croissant", [-0.33, 0.79, 0.22], rotY=0.6),
    m("lemon", [0.42, 0.76, 0.3]),
    m("gallinera_chair", [0.95, 0, 0.05], rotY=-1.5708), m("gallinera_chair", [-0.95, 0, -0.05], rotY=1.5708),
    m("standing_chalkboard_01", [-0.95, 0, -1.2], rotY=0.35),
    m("potted_plant_01", [-1.9, 0, -1.8]), m("potted_plant_02", [2.0, 0, -1.8]),
    m("CoffeeCart_01", [1.35, 0, -1.7], rotY=-0.35),
    m("modern_ceiling_lamp_01", [0, 2.05, 0]),
]

LIVING = [
    box([10, 3.2, 0.15], [0, 0, -1.6], "#E8E2D6"), box([0.15, 3.2, 8], [-2.4, 0, 2], "#DCD5C8"),
    m("Sofa_01", [-0.7, 0, -1.15]), m("throw_pillows_01", [-0.7, 0.42, -1.1], s=0.85),
    m("side_table_01", [0.55, 0, -1.05]),
    m("book_encyclopedia_set_01", [0.5, 0.55, -1.05], rotY=0.15),
    m("desk_lamp_arm_01", [0.72, 0.55, -1.15], rotY=-0.6, s=0.7),
    m("potted_plant_02", [1.45, 0, -1.2]), m("ceramic_vase_01", [0.33, 0.55, -0.95], s=0.6),
    m("fancy_picture_frame_01", [-0.7, 1.6, -1.52]),
    {"type": "rug", "pos": [0, 0, -0.2], "w": 2.6, "d": 1.8, "color": "#7F93A3"},
]

MINT, MINT2 = "#DCEAE5", "#CFE1DB"
DOCTOR = {"shirt": "#F4F4F2", "pants": "#4E9C94", "hairStyle": "short", "skin": "#E3B999", "hair": "#4A3122"}
NURSE = {"shirt": "#6FB1A8", "pants": "#6FB1A8", "hairStyle": "bun", "skin": "#C68E68"}
MOM = {"shirt": "#C2443A", "pants": "#2B3442", "hairStyle": "long", "skin": "#C68E68", "hair": "#231B16"}
PATIENT = {"shirt": "#7FA7C9", "pants": "#7FA7C9", "hairStyle": "short", "skin": "#C68E68", "hair": "#16161A"}
HOSPITAL = [
    box([10, 3.2, 0.15], [0, 0, -2.2], MINT), box([0.15, 3.2, 9], [-2.6, 0, 1.5], MINT2),
    box([1.5, 1.2, 0.04], [1.2, 1.1, -2.1], "#D5EBF8"), box([10, 0.12, 0.06], [0, 0.9, -2.1], "#FFFFFF"),
    {"type": "bed", "pos": [-0.6, 0, -0.9], "rotY": 0},
    person([-0.6, 0.0, -0.55], 0.0, "sit", 7, **PATIENT),
    person([0.75, 0, -0.1], -0.9, "think", 2, **DOCTOR),
    person([-1.5, 0, 0.6], 0.7, "talk", 4, **MOM),
    person([1.15, 0, -1.35], -0.5, "stand", 5, **NURSE),
    m("side_table_01", [0.6, 0, -1.75]), m("potted_plant_04", [0.5, 0.55, -1.75]), m("ceramic_vase_01", [0.72, 0.55, -1.7], s=0.5),
    m("potted_plant_01", [2.2, 0, -1.8]),
    m("modern_ceiling_lamp_01", [-0.3, 2.05, -0.5]),
]

OUTBACK_SOIL = "#B8693E"
OUTBACK = [
    m("quiver_tree_01", [-2.6, 0, -4.5], s=1.4), m("quiver_tree_01", [3.4, 0, -7.5], rotY=1.2, s=1.2),
    m("dead_quiver_trunk", [2.0, 0, -2.6], rotY=0.5),
    m("wild_rooibos_bush", [-1.2, 0, -1.6]), m("wild_rooibos_bush", [2.6, 0, -0.6], rotY=1.0), m("wild_rooibos_bush", [-3.4, 0, -0.4], rotY=2.0),
    m("wild_rooibos_bush", [0.6, 0, -9.0], s=1.3), m("wild_rooibos_bush", [-5.0, 0, -8.0], rotY=0.7, s=1.4),
    person([0, 0, 0], 0.3, "point", 3, skin="#4A2E20", hair="#151313", shirt="#E9E6DF", pants="#3A3A3F", hairStyle="short"),
]

FOREST = [{"type": "tree", "pos": [x, 0, z], "s": s} for x, z, s in (
    (-2.6, -2.0, 1.7), (2.4, -2.6, 1.8), (-1.1, -5.0, 1.9), (1.9, -6.5, 1.7), (-3.4, -7.0, 1.8), (3.6, -7.5, 1.9), (2.0, -11.0, 2.0), (-2.0, -12.0, 1.8))] + [
    {"type": "prim", "shape": "sphere", "pos": [0.5, 4.6, -26], "r": 1.5, "color": "#FFF6D8", "emissive": "#FFF1C4", "ei": 3.0, "shadow": False},
    {"type": "prim", "shape": "sphere", "pos": [0.5, 4.6, -26.8], "r": 3.6, "color": "#FFF0C8", "emissive": "#FFE29A", "ei": 0.9, "shadow": False},
    person([-0.75, 0, 2.6], 3.3, "stand", 6, shirt="#E9E6DF", pants="#56688A", hairStyle="long", hair="#16161A", skin="#F0CFB4"),
]

# spread out so the labels never overlap on the globe
GREET = [(51.5, -0.12, "Hello", 0.2), (55.75, 37.62, "Привет", 0.5), (40.4, -3.7, "Hola", 0.8), (30.0, 31.2, "مرحبا", 1.1),
         (28.6, 77.2, "नमस्ते", 1.4), (-1.3, 36.8, "Jambo", 1.7), (-8.8, 13.2, "Olá", 2.0)]
LANGS = [(28.6, 77.2, "नमस्ते", 0.1), (39.9, 116.4, "你好", 0.3), (30.0, 31.2, "مرحبا", 0.5), (-1.3, 36.8, "Jambo", 0.7),
         (41.0, 29.0, "Merhaba", 0.9), (35.68, 139.69, "こんにちは", 1.9), (19.4, -99.1, "Hola", 1.3), (-15.3, 145.2, "Guugu Yimithirr", 1.6)]

TILES = ["brand/tiles/cover-edinyi-yazyk.jpg", "brand/tiles/cover-coffee-agent.jpg", "brand/tiles/cover-nuclear.jpg",
         "brand/tiles/fr-gibrid.jpg", "projects/mir-bez-granic/cover.jpg", "brand/tiles/quiet-evenings.jpg",
         "brand/tiles/cover-fr-klassika.jpg", "brand/tiles/fr-test-1.jpg", ""]
PROFILE = {"block": "TikTokProfile", "props": {
    "dark": True, "name": "aipollon", "handle": "videopollon", "badge": "Verified business",
    "bio": "Даем возможность делать самые качественные ролики с ии прямо здесь 👇🏻",
    "link": "https://t.me/aipollonvideo", "avatar": "brand/aipollon-avatar.png",
    "tiles": TILES, "pinned": 1, "highlightAt": "@шапку"}}
PHONE = "#2F4560"   # deep blue, matches the globe / sky palette

REAL = {"look": "real", "pop": False, "lights": "studio", "env": 0.8}

sfx = [
    ("@Представь", "pk-digital-digitasl-burst-sfx", 0.5, True),
    ("@языке", "pk-pop-ui-menu", 0.5, True),
    ("@Токио", "pk-click-ui-button", 0.5, True),
    ("@полуслова", "pk-notify-notification-sfx-1", 0.5, True),
    ("@понятно", "pk-pop-ui-menu", 0.5, True),
    ("@не", "pk-result-failure", 0.5, True),
    ("@1980", "sting-dark", 0.4, False),
    ("@интоксикадо", "pk-click-ui-button", 0.5, True),
    ("@передозировка", "pk-pop-ui-menu", 0.5, True),
    ("@кровоизлияние", "heartbeat", 0.45, False),
    ("@71", "pk-digital-data-load-sfx-1", 0.55, False),
    ("@исчезнут", "pk-shimmer-ui-dissolvre-sfx", 0.5, False),
    ("@север", "pk-click-ui-button", 0.45, True),
    ("@юг", "click-soft", 0.45, True),
    ("@запад", "pk-click-ui-button", 0.45, True),
    ("@восток", "click-soft", 0.45, True),
    ("@комореби", "sparkle", 0.4, True),
    ("@удобнее", "pk-pop-ui-menu", 0.5, True),
    ("@Кстати", "pk-shimmer-ui-dissolvre-sfx", 0.6, False),
    ("@нейросеть", "pk-pop-ui-menu", 0.55, True),
    ("@шапку", "pk-click-ui-button", 0.7, True),
    ("@профиля", "pk-notify-notification-sfx-1", 0.8, True),
]

GLOBE = lambda props: {"block": "Globe3D", "pos": "full", "enter": "none", "props": dict({"look": "earth"}, **props)}

scenes = [
    # 1. hook: the real Earth over a daytime sky, greetings in many languages
    {"id": "globe", "at": 0, "camera": "still", "bg": {"block": "Sky"},
     "layers": [GLOBE({"spin": 3, "focus": [{"t": 0, "lat": 30, "lon": 34, "dist": 8.6}, {"t": 3.6, "lat": 38, "lon": 24, "dist": 6.6}],
                       "markers": [{"lat": a, "lon": b, "label": l, "at": t} for a, b, l, t in GREET]})]},
    # 2. Tokyo taxi: a daytime street, the tourist and the driver understand each other
    {"id": "street", "at": "@Таксист", "transition": "push", "camera": "still",
     "bg": {"block": "Street3D", "props": {"look": "real", "time": "day", "cam": "eye", "cars": 7, "people": 12, "seed": "tokyo"}},
     "layers": [
         {"block": "Bubble", "at": "@Токио", "pos": {"x": 70, "y": 330, "w": 760, "h": 200}, "props": {"text": "Мне на Сибую, пожалуйста", "side": "left", "name": "Ты", "size": 46}},
         {"block": "Bubble", "at": "@полуслова-0.2", "pos": {"x": 250, "y": 540, "w": 760, "h": 200}, "props": {"text": "Конечно, садитесь!", "side": "right", "name": "Таксист", "size": 46}}]},
    # 3. a café: menu board, tea and a croissant, everything readable
    {"id": "cafe", "at": "@Меню", "transition": "zoom", "camera": "still",
     "bg": {"block": "Scene3D", "props": dict(REAL, bg="#F2EEE8", ground={"size": 30, "color": OAK},
            cam=[k(0, [0.55, 1.55, 3.7], [0.0, 0.8, -0.8], 46), k(2.9, [0.4, 1.45, 3.15], [0.0, 0.8, -0.8], 46)], objects=CAFE)}},
    # 4. translators and phrasebooks are crossed out: a cosy living room with books
    {"id": "books", "at": "@Переводчики", "transition": "push", "camera": "still",
     "bg": {"block": "Scene3D", "props": dict(REAL, bg="#EFEAE2", ground={"size": 30, "color": OAK},
            cam=[k(0, [0.9, 1.15, 1.5], [0.3, 0.7, -1.1], 40), k(2.8, [0.75, 1.1, 1.25], [0.35, 0.7, -1.1], 40)], objects=LIVING), "dim": 0.25},
     "layers": [{"block": "StrikeList", "pos": "upper", "props": {"items": ["Переводчик", "Разговорник", "Субтитры"],
                                                                 "strikeAt": ["@не", "@не+0.2", "@нужны"]}}]},
    # 5. Florida 1980: a hospital ward
    {"id": "ward", "at": "@В 1980", "transition": "blur", "camera": "still",
     "bg": {"block": "Scene3D", "props": dict(REAL, bg="#EEF3F2", ground={"size": 30, "color": "#C9CDC9"},
            cam=[k(0, [1.1, 2.0, 5.2], [-0.25, 0.85, -0.6], 46), k(4.2, [0.85, 1.85, 4.6], [-0.25, 0.85, -0.6], 46)], objects=HOSPITAL)},
     "layers": [{"block": "Kicker", "pos": "top", "props": {"text": "Флорида · 1980", "size": 46, "solid": True}}]},
    # 6. intoxicado vs overdose: family and doctor
    {"id": "words", "at": "@Семья", "transition": "push", "camera": "still",
     "bg": {"block": "Scene3D", "props": dict(REAL, bg="#EEF3F2", ground={"size": 30, "color": "#C9CDC9"},
            cam=[k(0, [-0.35, 1.6, 3.4], [-0.45, 1.0, -0.3], 46), k(4.6, [-0.15, 1.55, 3.0], [-0.45, 1.0, -0.3], 46)], objects=HOSPITAL)},
     "layers": [
         {"block": "Bubble", "at": "@интоксикадо", "pos": {"x": 70, "y": 330, "w": 760, "h": 200}, "props": {"text": "Он *intoxicado*, ему плохо!", "side": "left", "name": "Семья", "size": 46}},
         {"block": "Bubble", "at": "@передозировка-0.3", "pos": {"x": 250, "y": 540, "w": 760, "h": 200}, "props": {"text": "Передозировка?", "side": "right", "name": "Врач", "size": 46}}]},
    # 7. a brain haemorrhage: slow push on the patient
    {"id": "patient", "at": "@У парня", "transition": "blur", "camera": "still",
     "bg": {"block": "Scene3D", "props": dict(REAL, bg="#EEF3F2", ground={"size": 30, "color": "#C9CDC9"},
            cam=[k(0, [0.9, 1.9, 3.7], [-0.6, 0.95, -0.7], 40), k(2.4, [0.65, 1.8, 3.0], [-0.6, 0.95, -0.7], 40)], objects=HOSPITAL), "dim": 0.15}},
    # 8. paralysis and a $71 million settlement
    {"id": "money", "at": "@Итог", "transition": "zoom", "camera": "still",
     "bg": {"block": "Scene3D", "props": dict(REAL, bg="#EEF3F2", ground={"size": 30, "color": "#C9CDC9"},
            cam=[k(0, [1.6, 2.6, 5.6], [-0.3, 1.9, -0.8], 46), k(4, [1.4, 2.5, 5.2], [-0.3, 1.9, -0.8], 46)], objects=HOSPITAL), "dim": 0.62},
     "layers": [{"block": "Counter", "pos": "center", "at": "@71-0.35", "props": {"from": 0, "to": 71, "prefix": "$", "label": "миллион|миллиона|миллионов", "size": 240, "dur": 1.0, "startAt": "@71"}}]},
    # 9. thousands of ways to see the world: languages all over the globe, flying to Australia
    {"id": "globe-langs", "at": "@Но", "transition": "zoom", "camera": "still", "bg": {"block": "Sky"},
     "layers": [GLOBE({"spin": 0, "focus": [{"t": 0, "lat": 25, "lon": 60, "dist": 8.2}, {"t": 3.6, "lat": -15, "lon": 140, "dist": 5.6}],
                       "markers": [{"lat": a, "lon": b, "label": l, "at": t} for a, b, l, t in LANGS]})]},
    # 10. Guugu Yimithirr: north, south, west, east around a man in the red outback
    {"id": "outback", "at": "@В языке", "transition": "push", "camera": "still",
     "bg": {"block": "Scene3D", "props": dict(REAL, bg="#9FCDEE", ground={"size": 300, "color": OUTBACK_SOIL},
            cam=[k(0, [1.0, 1.7, 5.0], [0, 1.1, -1], 50), k(5.2, [-0.4, 1.75, 5.2], [0, 1.1, -1], 50)], objects=OUTBACK,
            labels=[{"text": "Север", "size": 56, "pos": [0, 3.0, -4.0], "at": "@север"}, {"text": "Юг", "size": 56, "pos": [0.2, 0.25, 1.6], "at": "@юг"},
                    {"text": "Запад", "size": 56, "pos": [-1.0, 1.6, -0.3], "at": "@запад"}, {"text": "Восток", "size": 56, "pos": [1.1, 1.6, -0.3], "at": "@восток"}])}},
    # 11. komorebi: sunlight through the leaves, looking up
    {"id": "komorebi", "at": "@А японское", "transition": "blur", "camera": "still",
     "bg": {"block": "Scene3D", "props": dict(REAL, bg="#CFE8F7", ground={"size": 200, "color": "#5E8F45"},
            cam=[k(0, [0.25, 1.3, 8.2], [0.3, 2.9, -6], 50), k(4.6, [0.2, 1.25, 7.3], [0.3, 3.3, -6], 50)], objects=FOREST)},
     "layers": [{"block": "Kicker", "pos": "top", "at": "@комореби", "props": {"text": "木漏れ日 · комореби", "size": 46, "solid": True}}]},
    # 12. convenient, but more boring: the globe slowly turning, arcs connecting everyone
    {"id": "globe-end", "at": "@Один", "transition": "zoom", "camera": "still", "bg": {"block": "Sky"},
     "layers": [GLOBE({"spin": 6, "labels": False, "focus": [{"t": 0, "lat": 20, "lon": 30, "dist": 6.4}, {"t": 3.4, "lat": 25, "lon": 10, "dist": 8.6}],
                       "arcs": [{"from": [35.7, 139.7], "to": [51.5, -0.12], "at": 0.2, "dur": 1.2}, {"from": [-23.5, -46.6], "to": [48.85, 2.35], "at": 0.5, "dur": 1.2},
                                {"from": [28.6, 77.2], "to": [40.7, -74.0], "at": 0.8, "dur": 1.2}, {"from": [-33.9, 151.2], "to": [55.75, 37.62], "at": 1.1, "dur": 1.2}]})]},
    # 13. CTA over the café: the deep-blue iPhone flips to the profile
    {"id": "cta", "at": "@Кстати", "transition": "fade", "camera": "still",
     "bg": {"block": "Scene3D", "props": dict(REAL, bg="#F2EEE8", ground={"size": 30, "color": OAK},
            cam=[k(0, [0.55, 1.55, 3.7], [0.0, 0.8, -0.8], 46), k(7, [0.35, 1.45, 3.2], [0.0, 0.8, -0.8], 46)], objects=CAFE), "dim": 0.4},
     "captions": {"pos": "top"},
     "layers": [{"block": "IPhone17", "pos": "full", "enter": "none", "props": {
         "enter": "flip", "flipAt": "@нейросеть", "flipDur": 1.2, "float": True, "shadow": 0, "color": PHONE, "screen": PROFILE,
         "cam": [k(0, [0, 2.3, 10.8], [0, 2.25, 0], 30), k(1.6, [0.35, 2.32, 10.4], [0, 2.25, 0], 30),
                 k(2.6, [0, 2.53, 5.4], [0, 2.53, 0], 30, "inOut"), k(6, [0, 2.5, 5.1], [0, 2.5, 0], 30)]}}]},
]

spec = {
    "id": "edinyi-yazyk", "mode": "explainer", "style": "fresh", "fps": 60,
    "voice": {"src": "projects/edinyi-yazyk/voice.wav", "words": "projects/edinyi-yazyk/words.json"},
    "music": {"src": "music/lofi-warm.m4a", "volume": 0.12, "duck": 0.45},
    "tail": 2.0,
    "autoSfx": False,
    "captions": {"mode": "pill", "pos": "lower"},
    "sfx": [{"at": a, "id": i, "volume": v, "alignPeak": ap} for a, i, v, ap in sfx],
    "scenes": scenes,
}
P.mkdir(parents=True, exist_ok=True)
(P / "spec.json").write_text(json.dumps(spec, ensure_ascii=False, indent=1), encoding="utf-8")
print("scenes", len(scenes), "sfx", len(sfx))
