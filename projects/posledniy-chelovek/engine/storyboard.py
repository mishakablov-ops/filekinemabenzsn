"""Storyboard for posledniy-chelovek («Последний человек на Земле»), style «Гибрид»: the viewer is the last person on Earth.
Low-poly 3D in nearly every shot, hero = guy in the white cap and orange hoodie, editorial captions on top,
a scene every ~2.5-3.5 s on an anchor word, autoSfx off + hand-placed cues, CTA = iPhone flips to the TikTok profile.

New engine pieces made for this video (2026-10-26): Street3D stopped / lightsOut / stars / wolves, Globe3D look "dusk" +
cities / citiesOut, ChatScreen (messenger with «Не доставлено»), sfx door-knock and wolf-howl.

    python -I projects/posledniy-chelovek/engine/storyboard.py   -> <RS>/engine/public/projects/posledniy-chelovek/spec.json
Camera keys that must land on a word are computed from words.json (run again after a new voice).
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RS = ROOT / "kinema" / "skills" / "reel-studio"
PID = "posledniy-chelovek"
P = RS / "engine" / "public" / "projects" / PID
WORDS = json.loads((P / "words.json").read_text(encoding="utf-8"))["words"]

HERO = {"hero": True}


def norm(s):
    return re.sub(r"[^a-zа-я0-9]", "", s.lower().replace("ё", "е"))


def ws(word, n=1, end=False):
    """start (or end) time of the n-th caption word equal to `word` (punctuation and case ignored)"""
    k = 0
    for w in WORDS:
        if norm(w["text"]) == norm(word):
            k += 1
            if k == n:
                return w["end"] if end else w["start"]
    raise SystemExit(f"word not found: {word}#{n}")


def k(t, pos, tgt, fov=None, ease=None):
    d = {"t": round(t, 2), "pos": pos, "target": tgt}
    if fov:
        d["fov"] = fov
    if ease:
        d["ease"] = ease
    return d


def street(**kw):
    """the city after everyone vanished: nobody on the sidewalks, cars left standing in the lanes"""
    return {"block": "Street3D", "props": {"people": 0, "cars": 6, "stopped": True, **kw}}


def room(preset, cam, people=None, **kw):
    return {"block": "Room3D", "props": {"preset": preset, "cam": cam, "build": False, "people": people or [], **kw}}


def counter(to, label, size=190, **kw):
    """label: Russian plural forms, shared tail after a space: «день|дня|дней до плесени»"""
    return {"block": "Counter", "props": {"from": 0, "to": to, "label": label, "size": size, "labelSize": 50, "dur": 0.9, **kw}}


# scene start times (s) for keys that must hit a word inside a shot
T_YOU = ws("И")                      # «И это ты»
T_CARS = ws("Машины")
T_NIGHT = ws("Ночью")
T_MILKY = ws("Млечный")
T_KNOCK = ws("вдруг")

TILES = ["brand/tiles/cover-posledniy-chelovek.jpg", "brand/tiles/cover-kosmos-dlya-vseh-v2.jpg", "brand/tiles/cover-edinyi-yazyk.jpg",
         "brand/tiles/cover-coffee-agent.jpg", "brand/tiles/cover-nuclear.jpg", "brand/tiles/fr-gibrid.jpg",
         "brand/tiles/cover-mir-bez-granic.jpg", "brand/tiles/quiet-evenings.jpg", "brand/tiles/cover-fr-klassika.jpg"]
PROFILE = {"block": "TikTokProfile", "props": {
    "dark": True, "name": "aipollon", "handle": "videopollon", "badge": "Verified business",
    "bio": "Даем возможность делать самые качественные ролики с ии прямо здесь 👇🏻", "link": "https://t.me/aipollonvideo",
    "avatar": "brand/aipollon-avatar.png", "tiles": TILES, "pinned": 1, "highlightAt": "@шапку"}}

DOOR_CAM = [k(0, [0.75, 1.62, -0.45], [2.2, 1.1, -2.9], 56), k(4.5, [1.2, 1.62, -1.15], [2.2, 1.12, -2.9], 56)]

sfx = [
    # 1. hook: the lights of Earth go out, the counter rolls down to one
    ("@нет", "hit-sub", 0.75, True),
    ("@Исчезли", "dread-rise", 0.35, False),
    ("@8", "pk-digital-data-load-sfx-1", 0.55, False),
    ("@один", "pk-digital-digitasl-burst-sfx", 0.55, False),
    ("@ты", "pk-shimmer-ui-dissolvre-sfx", 0.6, True),
    # 2. empty city
    ("@Машины", "pk-click-ui-button", 0.5, True),
    ("@тёплый", "pk-pop-ui-menu", 0.5, True),
    ("@Пишешь+0.45", "pk-click-ui-button", 0.5, False),
    ("@доходит", "pk-result-failure", 0.7, True),
    # 3. the world switches off
    ("@гаснет+0.2", "switch-click", 0.8, False),
    ("@гаснет+0.3", "hit-sub", 0.55, False),
    ("@Станциям", "pk-notify-system-alert-sfx", 0.45, False),
    ("@нет#2", "hit-soft", 0.6, True),
    # 4. everything is yours
    ("@твои", "pk-notify-notification-sfx-1", 0.6, True),
    ("@неделю", "pk-pop-ui-menu", 0.6, True),
    ("@пяти", "pk-click-ui-button", 0.7, True),
    ("@машина", "pk-shimmer-ui-dissolvre-sfx", 0.5, True),
    ("@бензин", "hit-punch", 0.6, True),
    ("@полгода", "pk-result-failure", 0.55, True),
    # 5. night
    ("@Млечный", "pk-shimmer-ui-dissolvre-sfx", 0.55, False),
    ("@треть", "pk-pop-ui-menu", 0.6, True),
    # 6. wolves
    ("@волки", "wolf-howl", 0.7, False),
    ("@7", "pk-digital-digitasl-burst-sfx", 0.7, True),
    ("@заповедниках", "pk-click-ui-button", 0.5, True),
    # 7. the last one
    ("@Земле", "pk-notify-system-alert-sfx", 0.45, False),
    ("@Тишина", "heartbeat", 0.6, False),
    ("@стучат", "door-knock", 1.0, True),
    # 8. CTA
    ("@Кстати", "pk-shimmer-ui-dissolvre-sfx", 0.7, False),
    ("@нейросеть+1.2", "pk-pop-ui-menu", 0.6, False),
    ("@шапку", "pk-click-ui-button", 0.7, True),
    ("@профиля", "pk-notify-notification-sfx-1", 0.8, True),
]

scenes = [
    # --- 1. hook: an empty morning street, then Earth from space: the lights go out, 8 000 000 000 -> 1
    {"id": "wake", "at": 0, "camera": "still",
     "bg": street(time="day", cam=[k(0, [0.6, 8.5, 27], [0, 1.2, -12], 40), k(3, [0.3, 6.2, 21], [0, 1.0, -14], 40)])},
    {"id": "count", "at": "@Исчезли", "transition": "zoom", "camera": "still",
     "bg": {"block": "Globe3D", "props": {"look": "dusk", "cities": True, "citiesOut": "@8", "spin": 3, "labels": False,
                                         "focus": [{"t": 0, "lat": 32, "lon": 70, "dist": 4.6}, {"t": 4.5, "lat": 42, "lon": 45, "dist": 4.0}]}},
     "layers": [{"block": "Counter", "pos": "lower", "props": {
         "from": 8000000000, "to": 1, "steps": [{"at": "@один", "value": 1}], "dur": 0.6, "size": 128, "labelSize": 48,
         "label": "человек|человека|человек на Земле"}}]},
    # the hero alone among the stopped cars; the camera cranes up on «Машины»
    {"id": "you", "at": "@И это", "transition": "blur", "camera": "still",
     "bg": street(time="day", walkers=[{"x": 0.15, "z": 5.2, "speed": 0, "pose": "stand", "look": HERO, "rotY": 0.25}],
                  cam=[k(0, [0.55, 1.5, 9.4], [0.1, 1.45, 5.2], 38), k(T_CARS - T_YOU, [0.5, 1.6, 8.8], [0.1, 1.45, 5.2], 38),
                       k(T_CARS - T_YOU + 2.4, [-2.5, 9.5, 19], [0, 0.6, -3], 40, "inOut")])},
    {"id": "cafe", "at": "@В кафе", "transition": "push", "camera": "still", "bg": room("cafe", "table", lights="day")},
    {"id": "mom", "at": "@Пишешь", "transition": "whip", "camera": "still",
     "bg": {"block": "IPhone17", "props": {"enter": "rise", "color": "#2C3A4F",
            # close enough to read the chat: the phone fills the lower 3/4 of the frame, under the captions
            "cam": [k(0, [0, 2.0, 7.9], [0, 1.98, 0], 30), k(5, [0.45, 2.05, 7.3], [0, 1.98, 0], 30)],
            "screen": {"block": "ChatScreen", "props": {"name": "Мама", "sub": "была в сети вчера", "time": "8:14", "messages": [
                {"text": "Позвони, как проснёшься", "time": "вчера, 23:40"},
                {"text": "Мам, ты где?", "me": True, "at": "@Пишешь+0.45", "failAt": "@доходит"}]}}}}},
    # --- 3. the evening city goes dark window by window; the power plant has no operator
    {"id": "blackout", "at": "@Через", "transition": "dip", "camera": "still",
     "bg": street(time="evening", lightsOut="@гаснет+0.25", cam=[k(0, [-4, 21, 30], [0, 0, -12], 36), k(4, [3, 17, 25], [0, 0, -14], 36)])},
    {"id": "station", "at": "@Станциям", "transition": "push", "camera": "still",
     # push in on the monitor (screen centre 0.3, 1.12, -2.02; 0.86 m wide) so the console text reads on a phone
     "bg": room("office", [k(0, [1.0, 1.55, 1.0], [0.3, 1.3, -2.02], 40), k(4, [0.6, 1.45, 0.45], [0.3, 1.27, -2.02], 40)], lights="night",
                screen={"block": "Terminal", "props": {
         "title": "ТЭЦ-2 · пульт энергоблока", "welcome": False, "size": 52, "w": 1280, "h": 840, "lines": [
             {"kind": "text", "text": "Энергоблок 2 · 06:40", "at": 0.1},
             {"kind": "status", "text": "Ждём оператора", "at": 0.4, "until": "@нет", "hint": ""},
             {"kind": "tool", "name": "Аварийный останов", "state": "err", "at": "@нет", "sub": ["нагрузка 0 МВт", "город обесточен"]}]}})},
    # --- 4. everything is yours
    {"id": "shops", "at": "@Зато", "transition": "whip", "camera": "still",
     "bg": room("cafe", "counter", [{"pose": "cheer", "pos": [0.6, 0, -2.35], "rotY": 0, "seed": 5, "look": HERO}], lights="day")},
    {"id": "bread", "at": "@Хлеб", "transition": "push", "camera": "still", "bg": room("kitchen", "counter", lights="day"),
     "layers": [{**counter(7, "день|дня|дней до плесени"), "at": "@неделю", "pos": "lower"}]},
    {"id": "cans", "at": "@А консервы", "transition": "zoom", "camera": "still", "bg": room("basement", "fpvShelf"),
     "layers": [{**counter(5, "год|года|лет хранятся консервы"), "at": "@пяти", "pos": "lower"}]},
    {"id": "car", "at": "@Любая", "transition": "whip", "camera": "still",
     # the hero points at the nearest stopped car (x -1.8, z 8.6); camera front-right keeps both in the narrow 9:16 frame
     "bg": street(time="day", walkers=[{"x": 0.35, "z": 7.6, "speed": 0, "pose": "point", "look": HERO, "rotY": -1.15}],
                  cam=[k(0, [2.6, 1.7, 13.6], [-0.3, 1.0, 7.6], 42), k(3, [2.3, 1.62, 12.9], [-0.35, 1.0, 7.6], 42)])},
    {"id": "fuel", "at": "@Но бензин", "transition": "slam", "camera": "punch", "style": "blaze",
     "captions": {"mode": "editorial", "pos": "top"},
     "layers": [{"block": "StatSlam", "props": {"value": "6", "unit": "мес", "label": "и бензин в баке испорчен"}, "pos": {"preset": "stage", "dy": 150}}]},
    # --- 5. a black city under the Milky Way (the camera tilts up on «Млечный»)
    {"id": "night", "at": "@Ночью", "transition": "dip", "camera": "still",
     "bg": street(time="night", lightsOut=-5, stars=True,
                  cam=[k(0, [0.8, 1.7, 17], [0.3, 3.0, -30], 46), k(T_MILKY - T_NIGHT - 0.2, [0.8, 1.7, 15.6], [0.3, 3.2, -30], 46),
                       k(T_MILKY - T_NIGHT + 1.6, [0.6, 1.6, 15.2], [0, 48, -46], 50, "inOut")])},
    {"id": "third", "at": "@Раньше", "transition": "blur", "camera": "still",
     "bg": street(time="night", lightsOut=-5, stars=True, cam=[k(0, [2.2, 1.6, 6], [-14, 70, -40], 52), k(4, [2.0, 1.6, 5], [-6, 72, -46], 52)]),
     "layers": [{**counter(33, "людей не видели его из-за света городов", size=170, suffix=" %"), "at": "@треть", "pos": "lower"}]},
    # --- 6. a year later: wolves walk down the empty street; Chernobyl numbers
    {"id": "wolves", "at": "@Через год", "transition": "dip", "camera": "still",
     "bg": street(abandoned=True, ash=False, wolves=[{"x": 0.1, "z": 3.0, "speed": 1.0, "seed": 0}, {"x": -0.55, "z": 1.2, "speed": 1.0, "seed": 1},
                                                    {"x": 0.65, "z": 0.6, "speed": 1.0, "seed": 2}],
                  cam=[k(0, [0.4, 0.9, 13.5], [0, 0.7, 2], 40), k(4, [0.35, 0.85, 12.8], [0, 0.7, 4], 40)])},
    {"id": "chernobyl", "at": "@В зоне", "transition": "push", "camera": "still",
     "bg": {"block": "Bars3D", "props": {"bars": [{"label": "заповедники", "value": 1, "color": "#C9A27A"},
                                                 {"label": "Чернобыль", "value": 7, "color": "#D9732F"}], "unit": "×",
                                        # orbit from farther and higher: the 7× bar tops out under the captions
                                        "cam": [k(0, [-6.5, 5.4, 17.0], [0, 3.6, 0], 30), k(6, [5.5, 5.1, 17.3], [0, 3.6, 0], 30)]}}},
    # --- 7. the last one: Earth is dark, one marker; a quiet room; a knock on the door
    {"id": "last", "at": "@Ты последний", "transition": "zoom", "camera": "still",
     "bg": {"block": "Globe3D", "props": {"look": "dusk", "cities": True, "citiesOut": -5, "spin": 2,
                                         "markers": [{"lat": 55.75, "lon": 37.62, "label": "ТЫ", "at": "@Земле"}],
                                         "focus": [{"t": 0, "lat": 38, "lon": 70, "dist": 4.6}, {"t": 2.6, "lat": 52, "lon": 42, "dist": 3.4}]}}},
    {"id": "room", "at": "@Сидишь", "transition": "blur", "camera": "still",
     "bg": room("living", [k(0, [3.0, 2.5, 3.6], [0.0, 1.3, -1.7], 40), k(5, [2.3, 2.15, 2.7], [0.0, 1.25, -1.75], 40)],
                [{"pose": "sit", "pos": [0.0, 0.08, -1.85], "rotY": 0, "seed": 2, "look": HERO}], lights="night")},
    {"id": "knock", "at": "@И вдруг", "transition": "cut", "camera": {"move": "still", "shakeAt": ["@стучат"]},
     "bg": room("basement", DOOR_CAM, head=True, lantern=True)},
    # --- 8. CTA over the door: it opens a crack while the iPhone flips onto the TikTok profile
    {"id": "cta", "at": "@Кстати", "transition": "fade", "camera": "still",
     "bg": {**room("basement", [k(0, [1.2, 1.62, -1.15], [2.2, 1.12, -2.9], 56), k(8, [1.35, 1.62, -1.4], [2.2, 1.12, -2.9], 56)],
                   head=True, door=[0.0, 0.14]), "dim": 0.5},
     "layers": [{"block": "IPhone17", "pos": "full", "enter": "none", "props": {
         "enter": "flip", "flipAt": "@нейросеть", "flipDur": 1.2, "float": True, "shadow": 0, "color": "#2C3A4F", "screen": PROFILE,
         "cam": [k(0, [0, 2.3, 10.8], [0, 2.25, 0], 30), k(1.6, [0.35, 2.32, 10.4], [0, 2.25, 0], 30),
                 k(2.6, [0, 2.53, 5.4], [0, 2.53, 0], 30, "inOut"), k(6, [0, 2.5, 5.1], [0, 2.5, 0], 30)]}}]},
]

spec = {
    "id": PID, "mode": "explainer", "style": "dusk", "fps": 60,
    "voice": {"src": f"projects/{PID}/voice.wav", "words": f"projects/{PID}/words.json"},
    "music": {"src": "music/dark-cinematic.m4a", "volume": 0.11, "duck": 0.45},
    "tail": 1.8,
    "autoSfx": False,
    "captions": {"mode": "editorial", "pos": "top", "uppercase": True},
    "sfx": [{"at": a, "id": i, "volume": v, "alignPeak": ap} for a, i, v, ap in sfx],
    "scenes": scenes,
}
(P / "spec.json").write_text(json.dumps(spec, ensure_ascii=False, indent=1), encoding="utf-8")
print("scenes", len(scenes), "sfx", len(sfx), "voice", round(WORDS[-1]["end"], 1), "s")
