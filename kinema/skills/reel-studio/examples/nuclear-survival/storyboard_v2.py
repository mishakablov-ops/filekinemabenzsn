"""Storyboard v2 for nuclear-survival — after the user's notes (2026-10-20):
no hands in first person (head-cam, wider fov), hero = guy in a white cap, no flash cuts (every shot >= 1 s),
no airy/noise sounds (autoSfx off, hand-placed cues mostly from the user's pack), CTA = iPhone flips from its back
to the real TikTok profile over the last street frames."""
import json
from pathlib import Path

RS = Path(__file__).resolve().parents[2]
P = RS / "engine" / "public" / "projects" / "nuclear-survival"

HERO = {"hero": True}
SUIT_HERO = {"hero": True, "suit": True}


def room(cam, **kw):
    return {"block": "Room3D", "props": {"preset": "basement", "cam": cam, "build": False, **kw}}


def head(keys, **kw):
    """first-person head-cam with custom keys (fov comes from FPV_FOV)"""
    return room(keys, head=True, **kw)


def k(t, pos, tgt, fov=None):
    d = {"t": t, "pos": pos, "target": tgt}
    if fov:
        d["fov"] = fov
    return d


HERO_AT = [0.2, 0, 1.0]

sfx = [
    # catastrophe
    ("@вспышка", "nuke-boom", 1.0, True),
    ("@Не", "siren-air-raid", 0.38, False),
    ("@Свет", "pk-notify-system-alert-sfx", 0.5, False),
    ("@Дверь", "door-heavy-close", 1.0, True),
    ("@грохот", "shockwave-hit", 0.85, True),
    # first day
    ("@Снаружи", "pk-shimmer-ui-dissolvre-sfx", 0.6, False),
    ("@радиоактивная", "geiger-low", 0.45, False),
    ("@слабеет", "pk-digital-data-load-sfx-1", 0.7, False),
    ("@десять", "pk-pop-ui-menu", 0.7, True),
    ("@сто", "pk-click-ui-button", 0.8, True),
    # clothes, shower
    ("@сними", "pk-pop-ui-menu", 0.6, True),
    ("@В ней", "pk-digital-digitasl-burst-sfx", 0.8, True),
    ("@пакет", "pk-click-ui-button", 0.6, True),
    ("@Мыло", "pk-pop-ui-menu", 0.6, True),
    ("@нельзя", "pk-result-failure", 0.7, True),
    # water, food
    ("@бойлере", "pk-digital-data-load-sfx-1", 0.7, False),
    ("@чаше", "pk-click-ui-button", 0.6, True),
    ("@бачке#2", "pk-pop-ui-menu", 0.7, True),
    ("@протереть", "pk-shimmer-ui-dissolvre-sfx", 0.6, True),
    ("@Йод", "pk-notify-system-alert-sfx", 0.5, False),
    # shelter
    ("@Радио", "pk-click-ui-button", 0.6, True),
    ("@Интернета", "pk-notify-notification-sfx-1", 0.6, False),
    ("@будут", "pk-pop-ui-menu", 0.6, True),
    ("@Щели", "pk-click-ui-button", 0.5, True),
    ("@ведро", "pk-pop-ui-menu", 0.55, True),
    ("@чёрточка", "pk-click-ui-button", 0.7, True),
    ("@5", "pk-click-ui-button", 0.7, True),
    ("@9", "pk-digital-digitasl-burst-sfx", 0.6, True),
    ("@можно", "pk-notify-system-alert-sfx", 0.65, False),
    ("@выходить", "dread-rise", 0.45, False),
    # suit
    ("@Дождевик", "pk-pop-ui-menu", 0.6, True),
    ("@перчатки", "pk-click-ui-button", 0.6, True),
    ("@сапоги", "pk-pop-ui-menu", 0.6, True),
    ("@очки", "pk-click-ui-button", 0.6, True),
    ("@респиратор", "pk-digital-digitasl-burst-sfx", 0.7, True),
    ("@Скотч", "pk-shimmer-ui-dissolvre-sfx", 0.6, True),
    ("@Дверь открывается", "pk-click-ui-button", 0.5, True),
    # CTA
    ("@Кстати", "pk-shimmer-ui-dissolvre-sfx", 0.7, False),
    ("@нейросеть+1.2", "pk-pop-ui-menu", 0.6, False),
    ("@шапку", "pk-click-ui-button", 0.7, True),
    ("@профиля", "pk-notify-notification-sfx-1", 0.8, True),
]

TILES = [f"projects/nuclear-survival/tiles/t{i}.jpg" for i in range(1, 13)]
PROFILE = {"block": "TikTokProfile", "props": {"pinned": 1, "highlightAt": "@шапку"}}  # name, bio, link, avatar, tiles: the channel in engine/src/brand.json

scenes = [
    # --- 1. catastrophe (~15 s)
    {"id": "evening", "at": 0, "camera": "still", "bg": {"block": "Street3D", "props": {"time": "evening", "cam": "eye", "people": 12, "cars": 6}}},
    {"id": "flash", "at": "@вспышка", "transition": "flash", "camera": "still", "style": "blaze",
     "bg": {"block": "Blast3D", "props": {"cam": "hill", "flashAt": 0.05, "waveAt": 30}}},
    {"id": "dont-look", "at": "@Не", "transition": "cut", "camera": {"move": "push", "shakeAt": ["@Падай"]},
     "bg": {"block": "Blast3D", "props": {"cam": "street", "flashAt": -1.2, "waveAt": 30}}},
    {"id": "seconds", "at": "@Свет", "transition": "whip", "camera": "still",
     "bg": {"block": "Blast3D", "props": {"cam": "wide", "flashAt": -3.3, "waveAt": 30}},
     "layers": [{"block": "Counter", "props": {"from": 9, "to": 0, "label": "секунда|секунды|секунд до волны", "size": 230, "dur": 2.4}}]},
    # running down into the basement: head-cam walks fast (bob), then the door slams exactly on «Дверь»
    {"id": "down", "at": "@Вниз", "transition": "zoom", "camera": "still",
     "bg": head([k(0, [2.3, 1.74, 2.3], [-1.6, 0.95, -2.4]), k(1.7, [1.2, 1.66, 1.0], [-1.7, 0.9, -2.5])])},
    {"id": "door-slam", "at": "@окон", "transition": "cut", "camera": {"move": "still", "shakeAt": ["@Дверь"]},
     "bg": head([k(0, [0.95, 1.64, -0.75], [2.2, 1.1, -2.9]), k(1.6, [1.1, 1.62, -1.0], [2.2, 1.1, -2.9])],
                door=[0.8, 0.0], doorAt="@Дверь", doorDur=0.45)},
    {"id": "rumble", "at": "@головой", "transition": "fade", "camera": {"move": "still", "shakeAt": ["@грохот"]},
     "bg": room("corner", people=[{"pose": "think", "pos": HERO_AT, "rotY": -0.7, "seed": 12, "look": HERO}])},
    # --- 2. first day
    {"id": "fallout", "at": "@Снаружи", "transition": "dip", "camera": "still", "bg": {"block": "Street3D", "props": {"abandoned": True, "cam": "eye"}}},
    {"id": "decay", "at": "@Но слабеет", "transition": "push", "camera": "still",
     "bg": {"block": "Bars3D", "props": {"bars": [{"label": "1 час", "value": 100, "color": "#D9732F"}, {"label": "7 часов", "value": 10, "color": "#C9A27A"}, {"label": "2 дня", "value": 1, "color": "#E8D9C2"}], "unit": "%", "cam": "orbit"}}},
    {"id": "stay", "at": "@Поэтому", "transition": "blur", "camera": "still", "bg": room("fpvDoor")},
    # --- 3. clothes, shower
    {"id": "undress", "at": "@Первым", "transition": "zoom", "camera": "still",
     "bg": room("corner", people=[{"pose": "stand", "pos": HERO_AT, "rotY": -0.5, "seed": 12, "look": HERO}])},
    {"id": "ninety", "at": "@В ней", "transition": "slam", "camera": "punch", "style": "blaze",
     "layers": [{"block": "StatSlam", "props": {"value": "90", "unit": "%", "label": "пыли на верхней одежде"}, "pos": {"preset": "stage", "dy": 150}}],
     "captions": {"mode": "editorial", "pos": "top"}},
    {"id": "shower", "at": "@Потом", "transition": "push", "camera": "still", "bg": {"block": "Room3D", "props": {"preset": "kitchen", "cam": "counter", "people": []}},
     "layers": [{"block": "StrikeList", "props": {"items": ["Мыло", "Шампунь", "Бальзам"], "strikeAt": [99, 99, "@нельзя"], "size": 80}}]},
    # --- 4. water, food
    {"id": "water", "at": "@Вода", "transition": "whip", "camera": "still",
     "bg": head([k(0, [-0.7, 1.62, -0.5], [-2.5, 0.95, -2.5]), k(4, [-1.2, 1.6, -1.1], [-2.55, 0.9, -2.55])]),
     "layers": [{"block": "Counter", "props": {"from": 0, "to": 200, "label": "литр|литра|литров в бойлере", "size": 220, "dur": 0.9}, "at": "@бойлере"}]},
    {"id": "tank", "at": "@И в бачке", "transition": "push", "camera": "still",
     "layers": [{"block": "StrikeList", "props": {"items": ["В чаше", "В бачке"], "strikeAt": ["@чаше", 99], "size": 110}}],
     "bg": {"block": "Room3D", "props": {"preset": "kitchen", "cam": "table", "people": []}}},
    {"id": "cans", "at": "@Консервы", "transition": "zoom", "camera": "still", "bg": room("fpvShelf")},
    {"id": "iodine", "at": "@Йод", "transition": "blur", "camera": "still",
     "bg": head([k(0, [-0.05, 1.6, -0.4], [1.2, 0.85, -0.05]), k(3.4, [0.3, 1.55, -0.3], [1.22, 0.83, -0.05])])},
    # --- 5. shelter routine
    {"id": "radio", "at": "@Радио", "transition": "whip", "camera": "still", "bg": room("fpvRadio")},
    {"id": "no-net", "at": "@Интернета", "transition": "push", "camera": "still",
     "bg": {"block": "IPhone17", "props": {"enter": "rise", "cam": [{"t": 0, "pos": [0, 2.62, 12.2], "target": [0, 2.62, 0]}, {"t": 6, "pos": [0.9, 2.7, 11.6], "target": [0, 2.62, 0]}],
            "screen": {"block": "LockScreen", "props": {"notes": [{"app": "Сеть", "text": "Нет подключения", "at": 0.2}, {"app": "Радио · 104.2", "text": "Слушайте инструкции", "at": "@будут"}]}}}}},
    {"id": "vent", "at": "@Вентиляцию", "transition": "zoom", "camera": "still",
     "bg": head([k(0, [0.45, 1.62, -0.9], [0.6, 2.35, -3.0]), k(2.6, [0.5, 1.64, -1.5], [0.6, 2.5, -3.0])])},
    {"id": "bucket", "at": "@Туалет", "transition": "push", "camera": "still",
     "bg": head([k(0, [1.05, 1.62, 2.35], [2.6, 0.35, 1.62]), k(2.8, [1.4, 1.6, 2.25], [2.6, 0.32, 1.66])])},
    # one continuous shot: marks appear on «чёрточка», «5», «9» (was three flash cuts)
    {"id": "tally", "at": "@Каждый", "transition": "blur", "camera": "still",
     "bg": room("fpvTally", days=[[0, 2], ["@чёрточка", 3], ["@5", 5], ["@9", 9]]),
     "layers": [{"block": "Counter", "props": {"from": 1, "to": 5, "label": "день|дня|дней в подвале", "size": 190, "dur": 0.5}, "at": "@День#2", "until": "@День#3", "pos": "lower"},
                {"block": "Counter", "props": {"from": 5, "to": 9, "label": "день|дня|дней в подвале", "size": 190, "dur": 0.45}, "at": "@День#3", "pos": "lower", "enter": "none"}]},
    {"id": "all-clear", "at": "@И вдруг радио", "transition": "zoom", "camera": "still",
     "bg": {"block": "IPhone17", "props": {"enter": "spin", "cam": [{"t": 0, "pos": [0, 2.62, 12.2], "target": [0, 2.62, 0]}, {"t": 6, "pos": [-0.9, 2.7, 11.6], "target": [0, 2.62, 0]}],
            "screen": {"block": "EmergencyAlert", "props": {"source": "Радио · МЧС", "level": "ОТБОЙ", "title": "Можно выходить",
                                                             "text": "Уровень радиации снизился. Выходите ненадолго и только в защитной одежде."}}}}},
    # --- 6. going out: the hero puts the suit on piece by piece as the checklist ticks
    {"id": "suit-up", "at": "@Собираешь", "transition": "push", "camera": "still",
     "bg": room([k(0, [-1.24, 1.5, 4.94], [-0.185, 1.36, 0.86], 46), k(5, [-1.08, 1.49, 4.55], [-0.17, 1.33, 0.86], 46)],
                people=[{"pose": "stand", "pos": HERO_AT, "rotY": -0.35, "seed": 12, "look": HERO,
                         "suitAt": {"coat": "@Дождевик", "gloves": "@перчатки", "boots": "@сапоги", "goggles": "@очки", "mask": "@респиратор"}}]),
     "layers": [{"block": "Checklist", "props": {"title": "Костюм", "items": ["Дождевик", "Перчатки", "Сапоги", "Очки", "Респиратор"],
                                                 "checkAt": ["@Дождевик", "@перчатки", "@сапоги", "@очки", "@респиратор"]}, "pos": "left"}]},
    {"id": "suit-reveal", "at": "@Скотч", "transition": "zoom", "camera": "still",
     "bg": room([k(0, [0.2, 1.6, 3.8], [0.2, 1.5, 1.0], 38), k(2.2, [-1.6, 1.55, 3.14], [0.2, 1.48, 1.0], 38)],
                people=[{"pose": "stand", "pos": HERO_AT, "rotY": -0.35, "seed": 12, "look": SUIT_HERO}])},
    {"id": "door-open", "at": "@Дверь открывается", "transition": "fade", "camera": "still",
     "bg": head([k(0, [1.0, 1.64, -0.8], [2.2, 1.1, -2.9]), k(1.6, [1.35, 1.62, -1.3], [2.2, 1.1, -2.9])], door=[0.0, 0.85])},
    {"id": "silence", "at": "@Тишина", "transition": "dip", "camera": "still", "bg": {"block": "Street3D", "props": {"abandoned": True, "cam": "eye"}}},
    {"id": "empty-high", "at": "@Ни людей", "transition": "blur", "camera": "still", "bg": {"block": "Street3D", "props": {"abandoned": True, "cam": "high"}}},
    {"id": "city-stopped", "at": "@Город", "transition": "blur", "camera": "still",
     "bg": {"block": "Street3D", "props": {"abandoned": True, "cam": "drone", "walkers": [{"x": 0.6, "z": 6, "speed": 0, "pose": "stand", "look": SUIT_HERO}]}}},
    # --- 7. CTA over the last frames: iPhone rises showing its back, flips onto the real TikTok profile
    {"id": "cta", "at": "@Кстати", "transition": "fade", "camera": "still",
     "bg": {"block": "Street3D", "props": {"abandoned": True, "cam": "eye", "walkers": [{"x": 4.6, "z": 10, "speed": 0.8, "dir": -1, "look": SUIT_HERO}]}, "dim": 0.5},
     "layers": [{"block": "IPhone17", "pos": "full", "enter": "none", "props": {
         "enter": "flip", "flipAt": "@нейросеть", "flipDur": 1.3, "float": True, "shadow": 0, "screen": PROFILE,
         "cam": [{"t": 0, "pos": [0, 2.3, 10.8], "target": [0, 2.25, 0], "fov": 30}, {"t": 4.6, "pos": [0.35, 2.32, 10.4], "target": [0, 2.25, 0], "fov": 30},
                 {"t": 5.7, "pos": [0, 2.53, 5.4], "target": [0, 2.53, 0], "fov": 30, "ease": "inOut"}, {"t": 8, "pos": [0, 2.5, 5.1], "target": [0, 2.5, 0], "fov": 30}]}}]},
]

spec = {
    "id": "nuclear-survival", "mode": "explainer", "style": "dusk", "fps": 60,
    "voice": {"src": "projects/nuclear-survival/voice.wav", "words": "projects/nuclear-survival/words.json"},
    "music": {"src": "music/dark-cinematic.m4a", "volume": 0.1, "duck": 0.45},
    "tail": 1.8,
    "autoSfx": False,
    "captions": {"mode": "editorial", "pos": "top", "uppercase": True},
    "sfx": [{"at": a, "id": i, "volume": v, "alignPeak": ap} for a, i, v, ap in sfx],
    "scenes": scenes,
}
(P / "spec.json").write_text(json.dumps(spec, ensure_ascii=False, indent=1), encoding="utf-8")
print("scenes", len(scenes), "sfx", len(sfx))
