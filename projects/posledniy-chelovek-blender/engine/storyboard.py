"""Storyboard for posledniy-chelovek-blender: the same story, voice, captions and sounds as the gibrid posledniy-chelovek,
pictures from Blender in real colours. Counters, the chat, the stat slam and the TikTok end card stay KINEMA layers.

v2 (default, full mode): every scene is an animated Blender clip (VideoBG, 60 fps), KINEMA project
posledniy-chelovek-blender-v2. v1 (--quick): 15 stills with camera moves in the edit (PhotoBG zoom/pan) + 4 clips.

    python3 projects/posledniy-chelovek-blender/engine/storyboard.py [--quick]
needs <RS>/engine/public/projects/<PID>/{voice.wav, words.json, clips/*.mp4 (+ stills/*.jpg for --quick)}
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RS = ROOT / "kinema" / "skills" / "reel-studio"
FULL = "--quick" not in sys.argv
PID = "posledniy-chelovek-blender-v2" if FULL else "posledniy-chelovek-blender"
P = RS / "engine" / "public" / "projects" / PID
B = f"projects/{PID}"


def k(t, pos, tgt, fov=None, ease=None):
    d = {"t": round(t, 2), "pos": pos, "target": tgt}
    if fov:
        d["fov"] = fov
    if ease:
        d["ease"] = ease
    return d


def photo(sid, zoom=(1.0, 1.1), pan=(0, 0, 0, 0), **kw):
    if FULL:  # the camera already moves inside the clip: keep only a light push in the edit
        kw.pop("topShade", None)
        return clip(sid, (1.0, 1.03), **kw)
    return {"block": "PhotoBG", "props": {"src": f"{B}/stills/{sid}.jpg", "zoom": list(zoom), "pan": list(pan), "topShade": 0.3, **kw}}


def clip(sid, zoom=(1.0, 1.04), **kw):
    return {"block": "VideoBG", "props": {"src": f"{B}/clips/{sid}.mp4", "zoom": list(zoom), **kw}}


def counter(to, label, size=190, **kw):
    """label: Russian plural forms, shared tail after a space: «день|дня|дней до плесени»"""
    return {"block": "Counter", "props": {"from": 0, "to": to, "label": label, "size": size, "labelSize": 50, "dur": 0.9, **kw}}


TILES = ["brand/tiles/cover-posledniy-chelovek-blender.jpg", "brand/tiles/cover-posledniy-chelovek.jpg",
         "brand/tiles/cover-kosmos-dlya-vseh-v2.jpg", "brand/tiles/cover-edinyi-yazyk.jpg", "brand/tiles/cover-coffee-agent.jpg",
         "brand/tiles/cover-nuclear.jpg", "brand/tiles/fr-gibrid.jpg", "brand/tiles/cover-mir-bez-granic.jpg",
         "brand/tiles/quiet-evenings.jpg"]
PROFILE = {"block": "TikTokProfile", "props": {
    "dark": True, "name": "aipollon", "handle": "videopollon", "badge": "Verified business",
    "bio": "Даем возможность делать самые качественные ролики с ии прямо здесь 👇🏻", "link": "https://t.me/aipollonvideo",
    "avatar": "brand/aipollon-avatar.png", "tiles": TILES, "pinned": 1, "highlightAt": "@шапку"}}
PHONE_CAM = [k(0, [0, 2.0, 7.9], [0, 1.98, 0], 30), k(5, [0.45, 2.05, 7.3], [0, 1.98, 0], 30)]

# same sound design as the gibrid version
sfx = [
    ("@нет", "hit-sub", 0.75, True),
    ("@Исчезли", "dread-rise", 0.35, False),
    ("@8", "pk-digital-data-load-sfx-1", 0.55, False),
    ("@один", "pk-digital-digitasl-burst-sfx", 0.55, False),
    ("@ты", "pk-shimmer-ui-dissolvre-sfx", 0.6, True),
    ("@Машины", "pk-click-ui-button", 0.5, True),
    ("@тёплый", "pk-pop-ui-menu", 0.5, True),
    ("@Пишешь+0.45", "pk-click-ui-button", 0.5, False),
    ("@доходит", "pk-result-failure", 0.7, True),
    ("@гаснет+0.2", "switch-click", 0.8, False),
    ("@гаснет+0.3", "hit-sub", 0.55, False),
    ("@Станциям", "pk-notify-system-alert-sfx", 0.45, False),
    ("@нет#2", "hit-soft", 0.6, True),
    ("@твои", "pk-notify-notification-sfx-1", 0.6, True),
    ("@неделю", "pk-pop-ui-menu", 0.6, True),
    ("@пяти", "pk-click-ui-button", 0.7, True),
    ("@машина", "pk-shimmer-ui-dissolvre-sfx", 0.5, True),
    ("@бензин", "hit-punch", 0.6, True),
    ("@полгода", "pk-result-failure", 0.55, True),
    ("@Млечный", "pk-shimmer-ui-dissolvre-sfx", 0.55, False),
    ("@треть", "pk-pop-ui-menu", 0.6, True),
    ("@волки", "wolf-howl", 0.7, False),
    ("@7", "pk-digital-digitasl-burst-sfx", 0.7, True),
    ("@заповедниках", "pk-click-ui-button", 0.5, True),
    ("@Земле", "pk-notify-system-alert-sfx", 0.45, False),
    ("@Тишина", "heartbeat", 0.6, False),
    ("@стучат", "door-knock", 1.0, True),
    ("@Кстати", "pk-shimmer-ui-dissolvre-sfx", 0.7, False),
    ("@нейросеть+1.2", "pk-pop-ui-menu", 0.6, False),
    ("@шапку", "pk-click-ui-button", 0.7, True),
    ("@профиля", "pk-notify-notification-sfx-1", 0.8, True),
]

scenes = [
    # --- 1. hook: an empty morning street, then the night side of the Earth: the lights die, 8 000 000 000 -> 1
    {"id": "wake", "at": 0, "camera": "still", "bg": photo("wake", (1.0, 1.1), (0, 0, 0, -30))},
    {"id": "count", "at": "@Исчезли", "transition": "zoom", "camera": "still", "bg": clip("count", (1.0, 1.0)),
     "layers": [{"block": "Counter", "pos": "lower", "props": {
         "from": 8000000000, "to": 1, "steps": [{"at": "@один", "value": 1}], "dur": 0.6, "size": 128, "labelSize": 48,
         "label": "человек|человека|человек на Земле"}}]},
    # the hero alone among the stopped cars: the frame pulls back on «Машины»
    {"id": "you", "at": "@И это", "transition": "blur", "camera": "still",
     "bg": clip("you", (1.0, 1.0)) if FULL else photo("you", (1.22, 1.0), (0, 40, 0, 0))},
    {"id": "cafe", "at": "@В кафе", "transition": "push", "camera": "still", "bg": photo("cafe", (1.0, 1.12), (0, 0, 0, 40))},
    {"id": "mom", "at": "@Пишешь", "transition": "whip", "camera": "still",
     # v2: the same cafe clip keeps running behind the phone (startFrom = mom start - cafe start)
     "bg": clip("cafe", (1.08, 1.1), startFrom=2.76, blur=16, darken=0.4) if FULL else photo("cafe", (1.14, 1.2), blur=16, darken=0.4),
     "layers": [{"block": "IPhone17", "pos": "full", "enter": "none", "sfx": False, "props": {
         "enter": "rise", "color": "#2C3A4F", "shadow": 0, "cam": PHONE_CAM,
         "screen": {"block": "ChatScreen", "props": {"name": "Мама", "sub": "была в сети вчера", "time": "8:14", "messages": [
             {"text": "Позвони, как проснёшься", "time": "вчера, 23:40"},
             {"text": "Мам, ты где?", "me": True, "at": "@Пишешь+0.45", "failAt": "@доходит"}]}}}}]},
    # --- 3. the evening city goes dark; the power plant has no operator
    {"id": "blackout", "at": "@Через", "transition": "dip", "camera": "still", "bg": clip("blackout", (1.0, 1.03))},
    {"id": "station", "at": "@Станциям", "transition": "push", "camera": "still", "bg": photo("station", (1.0, 1.16), (0, 0, 0, 60))},
    # --- 4. everything is yours
    {"id": "shops", "at": "@Зато", "transition": "whip", "camera": "still", "bg": photo("shops", (1.14, 1.0))},
    {"id": "bread", "at": "@Хлеб", "transition": "push", "camera": "still", "bg": photo("bread", (1.0, 1.1), (0, 0, -30, 0)),
     "layers": [{**counter(7, "день|дня|дней до плесени"), "at": "@неделю", "pos": "lower"}]},
    {"id": "cans", "at": "@А консервы", "transition": "zoom", "camera": "still", "bg": photo("cans", (1.08, 1.0), (30, 0, 0, 0)),
     "layers": [{**counter(5, "год|года|лет хранятся консервы"), "at": "@пяти", "pos": "lower"}]},
    {"id": "car", "at": "@Любая", "transition": "whip", "camera": "still", "bg": photo("car", (1.0, 1.12), (0, 0, 20, 40))},
    {"id": "fuel", "at": "@Но бензин", "transition": "slam", "camera": "punch", "style": "blaze",
     "captions": {"mode": "editorial", "pos": "top"}, "bg": photo("fuel", (1.06, 1.14), darken=0.5),
     "layers": [{"block": "StatSlam", "props": {"value": "6", "unit": "мес", "label": "и бензин в баке испорчен"}, "pos": {"preset": "stage", "dy": 150}}]},
    # --- 5. a black city under the Milky Way (the clip tilts up on «Млечный»)
    {"id": "night", "at": "@Ночью", "transition": "dip", "camera": "still", "bg": clip("night", (1.0, 1.0))},
    {"id": "third", "at": "@Раньше", "transition": "blur", "camera": "still", "bg": photo("third", (1.0, 1.08)),
     "layers": [{**counter(33, "людей не видели его из-за света городов", size=170, suffix=" %"), "at": "@треть", "pos": "lower"}]},
    # --- 6. a year later: wolves on the overgrown street; Chernobyl numbers over Pripyat
    {"id": "wolves", "at": "@Через год", "transition": "dip", "camera": "still", "bg": clip("wolves", (1.0, 1.02))},
    {"id": "chernobyl", "at": "@В зоне", "transition": "push", "camera": "still", "bg": photo("chernobyl", (1.0, 1.1), (0, 0, 0, 30)),
     "layers": [{"block": "BarChart", "at": "@Чернобыля", "pos": {"preset": "stage", "dy": 430}, "props": {
         "title": "Волков в зоне Чернобыля", "w": 920, "bars": [
             {"label": "в заповедниках", "value": 1, "note": "1×", "dim": True},
             {"label": "в зоне", "value": 7, "note": "7×"}]}}]},
    # --- 7. the last one: the dark Earth with one light (frame centre), a quiet room, a knock on the door
    {"id": "last", "at": "@Ты последний", "transition": "zoom", "camera": "still", "bg": photo("last", (1.0, 1.14), topShade=0),
     "layers": [{"block": "Callout", "at": "@Земле", "pos": "full", "props": {"text": "ТЫ", "x": 540, "y": 960, "lx": 700, "ly": 820}}]},
    {"id": "room", "at": "@Сидишь", "transition": "blur", "camera": "still", "bg": photo("room", (1.12, 1.0), (0, 30, 0, 0))},
    {"id": "knock", "at": "@И вдруг", "transition": "cut", "camera": {"move": "still", "shakeAt": ["@стучат"]},
     "bg": photo("knock", (1.0, 1.1))},
    # --- 8. CTA over the door ajar: the iPhone flips onto the TikTok profile
    {"id": "cta", "at": "@Кстати", "transition": "fade", "camera": "still", "bg": {**photo("cta", (1.1, 1.16)), "dim": 0.5},
     "layers": [{"block": "IPhone17", "pos": "full", "enter": "none", "props": {
         "enter": "flip", "flipAt": "@нейросеть", "flipDur": 1.2, "float": True, "shadow": 0, "color": "#2C3A4F", "screen": PROFILE,
         "cam": [k(0, [0, 2.3, 10.8], [0, 2.25, 0], 30), k(1.6, [0.35, 2.32, 10.4], [0, 2.25, 0], 30),
                 # aim a little higher at the close-up: mid-flip the phone top touched «НЕЙРОСЕТЬ» (QA overlap at 59.3 s)
                 k(2.6, [0, 2.53, 5.4], [0, 2.7, 0], 30, "inOut"), k(6, [0, 2.5, 5.1], [0, 2.5, 0], 30)]}}]},
]

spec = {
    "id": PID, "mode": "explainer", "style": "dusk", "fps": 60,
    "voice": {"src": f"{B}/voice.wav", "words": f"{B}/words.json"},
    "music": {"src": "music/dark-cinematic.m4a", "volume": 0.11, "duck": 0.45},
    "tail": 1.8,
    "autoSfx": False,
    "grain": 0.02, "vignette": 0.12,
    "captions": {"mode": "editorial", "pos": "top", "uppercase": True},
    "sfx": [{"at": a, "id": i, "volume": v, "alignPeak": ap} for a, i, v, ap in sfx],
    "scenes": scenes,
}
if __name__ == "__main__":
    (P / "spec.json").write_text(json.dumps(spec, ensure_ascii=False, indent=1), encoding="utf-8")
    print("scenes", len(scenes), "sfx", len(sfx))
