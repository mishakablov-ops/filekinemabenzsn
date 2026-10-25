"""Storyboard for coffee-agent: a coffee-shop owner tells (first person) how an agent took video editing off his hands.
Rules from the user's notes: cozy 3D in nearly every shot, aggressive typography, hero = guy in a white cap,
no shot < 1 s, no airy SFX (autoSfx off, cues mostly from the user's pack), CTA = iPhone flips to the TikTok profile.

    python -I storyboard.py   -> engine/public/projects/coffee-agent/spec.json
"""
import json
from pathlib import Path

RS = Path(__file__).resolve().parents[2]
P = RS / "engine" / "public" / "projects" / "coffee-agent"

HERO = {"hero": True}


def k(t, pos, tgt, fov=None, ease=None):
    d = {"t": t, "pos": pos, "target": tgt}
    if fov:
        d["fov"] = fov
    if ease:
        d["ease"] = ease
    return d


def cafe(cam, people, **kw):
    return {"block": "Room3D", "props": {"preset": "cafe", "lights": "evening", "build": False, "cam": cam, "people": people, **kw}}


TIMELINE = {"block": "EditorTimeline", "props": {"title": "Кофейня_ролик_v12.prproj",
                                                 "adds": [{"track": "V1", "at": 0.3, "n": 6}, {"track": "T1", "at": 1.0, "n": 7}, {"track": "A2", "at": 1.7, "n": 5}]}}
OFFICE_NIGHT = {"preset": "office", "lights": "evening", "build": False}
BARISTA = {"pose": "stand", "pos": [0.6, 0, -2.35], "rotY": 0, "seed": 5, "look": HERO}

TILES = [f"projects/nuclear-survival/tiles/t{i}.jpg" for i in range(1, 13)]
PROFILE = {"block": "TikTokProfile", "props": {"pinned": 1, "highlightAt": "@шапку"}}  # name, bio, link, avatar, tiles: the channel in engine/src/brand.json

sfx = [
    ("@6", "pk-digital-digitasl-burst-sfx", 0.6, True),
    ("@Ради", "pk-pop-ui-menu", 0.7, True),
    ("@40", "pk-click-ui-button", 0.7, True),
    ("@гости", "pk-notify-notification-sfx-1", 0.5, False),
    ("@заказы", "pk-pop-ui-menu", 0.5, True),
    ("@поставки", "pk-click-ui-button", 0.5, True),
    ("@таймлайн", "pk-digital-data-load-sfx-1", 0.5, False),
    ("@субтитры", "pk-click-ui-button", 0.5, True),
    ("@звуки", "pk-pop-ui-menu", 0.5, True),
    ("@растёт", "pk-result-failure", 0.55, True),
    ("@кофейню+0.45", "pk-click-ui-button", 0.6, False),
    ("@кофейню+0.8", "pk-shimmer-ui-dissolvre-sfx", 0.6, False),
    ("@Сценарий", "pk-pop-ui-menu", 0.6, True),
    ("@голос", "pk-click-ui-button", 0.6, True),
    ("@монтаж", "pk-digital-digitasl-burst-sfx", 0.6, True),
    ("@тему", "pk-pop-ui-menu", 0.6, True),
    ("@больше", "pk-notify-notification-sfx-1", 0.55, True),
    ("@Кстати", "pk-shimmer-ui-dissolvre-sfx", 0.6, False),
    ("@агент+1.2", "pk-pop-ui-menu", 0.55, False),
    ("@шапку", "pk-click-ui-button", 0.7, True),
    ("@профиля", "pk-notify-notification-sfx-1", 0.8, True),
]

scenes = [
    # 1. hook: night, editing over the shoulder, clips pile up on the timeline
    {"id": "edit-night", "at": 0, "camera": "still",
     "bg": {"block": "Room3D", "props": {**OFFICE_NIGHT, "cam": [k(0, [1.65, 1.6, 0.05], [0.3, 1.1, -2.02], 38), k(3, [1.45, 1.52, -0.3], [0.3, 1.1, -2.02], 38)],
                                         "people": [{"pose": "type", "pos": [0.3, 0, -1.0], "rotY": 3.14159, "seed": 1, "look": HERO}], "screen": TIMELINE}}},
    # 2. aggressive type: 6 hours for 40 seconds (captions off, BigType carries the words)
    {"id": "six-for-forty", "at": "@Ради", "transition": "zoom", "camera": "punch", "captions": False,
     "bg": {"block": "Room3D", "props": {**OFFICE_NIGHT, "cam": [k(0, [1.2, 1.45, -0.6], [0.3, 1.12, -2.02], 34), k(2.5, [1.0, 1.4, -0.9], [0.3, 1.12, -2.02], 34)],
                                         "people": [], "screen": TIMELINE}, "dim": 0.62},
     "layers": [{"block": "BigType", "pos": "center", "props": {"lines": ["6 часов", "ради", "40 секунд"], "at": [0, "@Ради", "@40"],
                                                                "treatment": ["solid", "serif", "mark"], "enter": "slam", "upper": True}}]},
    # 3. the day job: busy cafe, orders dropping in
    {"id": "cafe-day", "at": "@Днём", "transition": "push", "camera": "still",
     "bg": cafe("counter", [BARISTA,
                            {"pose": "stand", "pos": [0.1, 0, -0.72], "rotY": 3.14159, "seed": 7},
                            {"pose": "phone", "pos": [-0.75, 0, 0.35], "rotY": 2.6, "seed": 9},
                            {"pose": "stand", "pos": [2.3, 0, 0.55], "walkTo": [1.15, 0, -0.62], "walkDur": 2.4, "seed": 6}]),
     "layers": [{"block": "NotificationStack", "pos": "lower", "props": {"items": [
         {"app": "Бронь", "text": "Столик на 4 · 12:30", "at": "@гости"},
         {"app": "Заказ #214", "text": "2 капучино, раф с собой", "at": "@заказы"},
         {"app": "Поставка", "text": "Молоко 12 л · зерно 5 кг", "at": "@поставки"}]}}]},
    # 4. the night job: the editor on the MacBook, track after track
    {"id": "macbook-edit", "at": "@Ночью", "transition": "zoom", "camera": "still",
     "bg": {"block": "MacBook", "props": {"cam": "toScreen", "screen": {"block": "EditorTimeline", "props": {
         "title": "Кофейня_ролик_v13.prproj", "adds": [{"track": "V1", "at": "@таймлайн", "n": 8}, {"track": "T1", "at": "@субтитры", "n": 9},
                                                        {"track": "A2", "at": "@звуки", "n": 7}]}}}}},
    # 5. flat growth (3D bars)
    {"id": "flat", "at": "@Я знал", "transition": "push", "camera": "still",
     "bg": {"block": "Bars3D", "props": {"bars": [{"label": "июнь", "value": 41, "color": "#C9A27A"}, {"label": "июль", "value": 40, "color": "#C9A27A"},
                                                  {"label": "август", "value": 42, "color": "#C9A27A"}, {"label": "сентябрь", "value": 40, "color": "#D9732F"}],
                                         "unit": "", "max": 100, "cam": "orbit"}}},
    # 6. no time left for me: alone at the window at night
    {"id": "alone", "at": "@Но", "transition": "blur", "camera": "still",
     "bg": {"block": "Room3D", "props": {**OFFICE_NIGHT, "cam": [k(0, [0.05, 1.72, 2.35], [-2.3, 1.55, -0.2], 40), k(2.5, [-0.25, 1.7, 2.0], [-2.3, 1.55, -0.2], 40)],
                                         "people": [{"pose": "think", "pos": [-2.05, 0, -0.1], "rotY": -1.5708, "seed": 1, "look": HERO}]}}},
    # 7. the turn: one message to the agent
    {"id": "prompt", "at": "@Однажды", "transition": "zoom", "camera": "still",
     "bg": {**cafe("counter", [BARISTA]), "dim": 0.6},
     "layers": [{"block": "ClaudeChat", "pos": "stage", "props": {
         "greeting": "Доброе утро", "type": "Сделай ролик про мою кофейню ☕", "typeAt": "@Сделай", "cps": 18, "dark": True,
         "sendAt": "@кофейню+0.45", "reply": "Принято. Пишу сценарий, озвучиваю, монтирую…", "replyAt": "@кофейню+0.8"}}]},
    # 8. it builds everything while I make coffee (barista head-cam at the steaming machine)
    {"id": "bar-pov", "at": "@Сценарий", "transition": "whip", "camera": "still",
     "bg": cafe("fpvBar", []),
     "layers": [{"block": "Checklist", "pos": "lower", "props": {"title": "Агент собирает", "items": ["Сценарий", "Голос", "Монтаж"],
                                                                 "checkAt": ["@Сценарий", "@голос", "@монтаж"]}}]},
    # 9. now: the topic over morning coffee
    {"id": "morning", "at": "@Теперь", "transition": "push", "camera": "still",
     "bg": cafe([k(0, [-0.2, 1.58, 3.2], [-1.55, 1.15, 0.0], 42), k(2.6, [-0.35, 1.55, 2.95], [-1.55, 1.15, 0.0], 42)],
                [{"pose": "sit", "pos": [-1.5, 0.05, 0.2], "rotY": 0, "seed": 1, "look": HERO}, BARISTA | {"look": {}, "seed": 4}]),
     "layers": [{"block": "Bubble", "pos": "lower", "at": "@тему", "props": {"text": "Тема на завтра: *осенний раф* 🍂", "side": "right"}}]},
    # 10. the evening is mine again
    {"id": "evening", "at": "@А вечер", "transition": "blur", "camera": "still",
     "bg": {"block": "Room3D", "props": {"preset": "cabin", "cam": "fire", "build": False,
                                         "people": [{"pose": "sit", "pos": [0.2, 0.08, 0.55], "rotY": 3.14159, "seed": 1, "look": HERO}]}}},
    # 11. more guests -> CTA over the last frames: iPhone rises showing its back, flips to the profile
    {"id": "busy-cta", "at": "@И гостей", "transition": "zoom", "camera": "still",
     "bg": {**cafe([k(0, [2.7, 2.35, 4.0], [0.0, 1.05, -0.6], 50), k(9, [2.2, 2.2, 3.4], [0.0, 1.05, -0.6], 50)],
                   [BARISTA,
                    {"pose": "sit", "pos": [-1.5, 0.05, 1.6], "rotY": 3.14159, "seed": 6},
                    {"pose": "sit", "pos": [-1.5, 0.05, 0.2], "rotY": 0, "seed": 9},
                    {"pose": "stand", "pos": [0.1, 0, -0.72], "rotY": 3.14159, "seed": 7},
                    {"pose": "phone", "pos": [-0.9, 0, -0.65], "rotY": 2.8, "seed": 8},
                    {"pose": "stand", "pos": [1.3, 0, -0.8], "rotY": 3.14159, "seed": 11},
                    {"pose": "stand", "pos": [2.7, 0, 0.7], "walkTo": [1.9, 0, -0.62], "walkDur": 2.6, "seed": 10}]),
            "dim": 0.55, "dimAt": "@Кстати"},
     "layers": [{"block": "IPhone17", "pos": "full", "enter": "none", "at": "@Кстати", "props": {
         "enter": "flip", "flipAt": "@агент", "flipDur": 1.2, "float": True, "shadow": 0, "screen": PROFILE,
         "cam": [k(0, [0, 2.3, 10.8], [0, 2.25, 0], 30), k(3.9, [0.35, 2.32, 10.4], [0, 2.25, 0], 30),
                 k(4.9, [0, 2.53, 5.4], [0, 2.53, 0], 30, "inOut"), k(8, [0, 2.5, 5.1], [0, 2.5, 0], 30)]}}]},
]

spec = {
    "id": "coffee-agent", "mode": "explainer", "style": "dusk", "fps": 60,
    "voice": {"src": "projects/coffee-agent/voice.wav", "words": "projects/coffee-agent/words.json"},
    "music": {"src": "music/lofi-warm.m4a", "volume": 0.14, "duck": 0.45},
    "tail": 2.0,
    "autoSfx": False,
    "captions": {"mode": "editorial", "pos": "top", "uppercase": True},
    "sfx": [{"at": a, "id": i, "volume": v, "alignPeak": ap} for a, i, v, ap in sfx],
    "scenes": scenes,
}
(P / "spec.json").write_text(json.dumps(spec, ensure_ascii=False, indent=1), encoding="utf-8")
print("scenes", len(scenes), "sfx", len(sfx))
