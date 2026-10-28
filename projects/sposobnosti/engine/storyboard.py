"""Storyboard for «Каждому по способности» (sposobnosti), two parts: every scene is an animated Blender clip (VideoBG,
the camera moves inside the clip), numbers are KINEMA counters, part 1 ends on the TikTok profile where «ЧАСТЬ 2»
lands in the grid, part 2 ends on the iPhone flipping to the profile. Since 28.10.2026 both endings are a calm invite
(«Переходи в профиль…»), no ad and no highlighted link; the avatar is the Hermes engraving, the music is minimal-keys.

    python3 projects/sposobnosti/engine/storyboard.py [--out DIR]
writes <RS>/engine/public/projects/sposobnosti-{1,2}/spec.json (or DIR/sposobnosti-{1,2}/spec.json);
needs there voice.wav, words.json and clips/<shot>.mp4 (a01..a20 in part 1, b01..b20 in part 2).
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RS = ROOT / "kinema" / "skills" / "reel-studio"
OUT = Path(sys.argv[sys.argv.index("--out") + 1]) if "--out" in sys.argv else RS / "engine" / "public" / "projects"


def k(t, pos, tgt, fov=None, ease=None):
    d = {"t": round(t, 2), "pos": pos, "target": tgt}
    if fov:
        d["fov"] = fov
    if ease:
        d["ease"] = ease
    return d


def clip(pid, sid, zoom=(1.0, 1.03), **kw):
    return {"block": "VideoBG", "props": {"src": f"projects/{pid}/clips/{sid}.mp4", "zoom": list(zoom), **kw}}


def counter(to, label, size=180, **kw):
    """label: Russian plural forms, shared tail after a space: «рейс|рейса|рейсов в день»"""
    return {"block": "Counter", "props": {"from": 0, "to": to, "label": label, "size": size, "labelSize": 48, "dur": 0.9, **kw}}


def scene(pid, sid, at, transition="push", camera="still", zoom=(1.0, 1.03), layers=None, **kw):
    s = {"id": sid, "at": at, "transition": transition, "camera": camera, "bg": clip(pid, sid, zoom)}
    if layers:
        s["layers"] = layers
    s.update(kw)
    return s


# real covers of the channel's reels only (aipollon-knowledge: no invented tiles); the two parts go first
COVER1, COVER2 = "brand/tiles/cover-sposobnosti-1.jpg", "brand/tiles/cover-sposobnosti-2.jpg"
OTHER = ["brand/tiles/cover-posledniy-chelovek-blender.jpg", "brand/tiles/kosmos-dlya-vseh-v2.jpg", "brand/tiles/mir-bez-granic.jpg",
         "brand/tiles/edinyi-yazyk.jpg", "brand/tiles/fr-gibrid.jpg", "brand/tiles/cover-nuclear.jpg", "brand/tiles/quiet-evenings.jpg",
         "brand/tiles/cover-coffee-agent.jpg"]


def profile(tiles, **kw):
    return {"block": "TikTokProfile", "props": {
        "dark": True, "name": "aipollon", "handle": "videopollon", "badge": "Verified business",
        "bio": "Даем возможность делать самые качественные ролики с ии прямо здесь 👇🏻", "link": "https://t.me/aipollonvideo",
        "avatar": "brand/aipollon-avatar-hermes.png", "tiles": tiles, "pinned": 1, **kw}}


def spec(pid, scenes, sfx, tail):
    return {
        "id": pid, "mode": "explainer", "style": "dusk", "fps": 60,
        "voice": {"src": f"projects/{pid}/voice.wav", "words": f"projects/{pid}/words.json"},
        "music": {"src": "music/minimal-keys.m4a", "volume": 0.13, "duck": 0.5},
        "tail": tail,
        "autoSfx": False,
        "grain": 0.02, "vignette": 0.12,
        "captions": {"mode": "editorial", "pos": "top", "uppercase": True},
        "sfx": [{"at": a, "id": i, "volume": v, "alignPeak": ap} for a, i, v, ap in sfx],
        "scenes": scenes,
    }


# ============================================================================= part 1
P1 = "sposobnosti-1"
s1 = lambda *a, **kw: scene(P1, *a, **kw)  # noqa: E731
scenes1 = [
    # --- hook: the night of the gifts, the Earth, a street full of powers
    s1("a01", 0, "cut", zoom=(1.0, 1.04)),
    s1("a02", "@Каждый", "zoom"),
    s1("a03", "@8", "blur", layers=[{**counter(8000000000, "суперсила|суперсилы|суперсил", size=110), "at": "@8", "pos": "lower"}]),
    # --- the morning at home: the neighbour flies past the window, granny lifts a car, the courier teleports
    s1("a04", "@Я выглянул", "dip"),
    s1("a05", "@Сосед сверху", "whip"),
    s1("a06", "@Бабушка", "push"),
    s1("a07", "@А машина", "zoom",
       layers=[{"block": "StatSlam", "at": "@весит+0.3", "props": {"value": "1,5", "unit": "т", "label": "весит машина"},
                "pos": {"preset": "stage", "dy": 160}}]),
    s1("a08", "@Курьер", "whip"),
    # --- the city at noon: no jams, people fly to work, 100 000 flights a day, the airports are empty
    s1("a09", "@К обеду", "dip"),
    s1("a10", "@Полгорода", "push"),
    s1("a11", "@Обычно", "blur", layers=[{**counter(100000, "рейс|рейса|рейсов в день"), "at": "@мире+0.3", "pos": "lower"}]),
    s1("a12", "@А сегодня", "push"),
    # --- me: looking for my power all day
    s1("a13", "@А я весь", "dip"),
    s1("a14", "@Прыгнул", "whip", camera={"move": "still", "shakeAt": ["@Упал"]}),
    s1("a15", "@Час", "blur"),
    # --- the evening: the neighbour falls into the bushes next to me; powers die around me
    s1("a16", "@Вечером", "dip"),
    s1("a17", "@И вдруг", "cut", camera={"move": "still", "shakeAt": ["@рухнул+0.25"]}),
    s1("a18", "@Тогда", "zoom"),
    s1("a19", "@Восемь миллиардов суперлюдей", "blur"),
    # --- cliffhanger: a knock on the door; a calm invite: part 2 is already in the profile (28.10: no ad)
    s1("a20", "@А утром", "dip", camera={"move": "still", "shakeAt": ["@постучали"]},
       layers=[{"block": "IPhone17", "at": "@Переходи-0.15", "pos": "full", "enter": "none", "props": {
           "enter": "rise", "float": True, "shadow": 0, "color": "#2C3A4F",
           "screen": profile([COVER1] + OTHER, newTile={"src": COVER2, "label": "ЧАСТЬ 2", "at": "@вторая"}),
           "cam": [k(0, [0, 2.3, 10.8], [0, 2.25, 0], 30), k(1.2, [0.3, 2.32, 9.6], [0, 2.3, 0], 30),
                   k(4.5, [0, 2.6, 6.2], [0, 2.75, 0], 30, "inOut")]}}]),
]
sfx1 = [
    ("@суперсилу", "sparkle-rise", 0.6, False),
    ("@Одну", "hit-sub", 0.55, True),
    ("@Навсегда", "reveal-glow", 0.5, False),
    ("@летит", "whoosh-pan-lr", 0.55, True),
    ("@поднимает", "magic-wand", 0.6, True),
    ("@исчезает", "suck-in", 0.55, True),
    ("@стоит", "pop-high", 0.5, True),
    ("@двери", "thud", 0.55, True),
    ("@двери+0.25", "thud", 0.45, True),
    ("@Полгорода", "whoosh-double", 0.45, True),
    ("@пустые", "wind", 0.35, False),
    ("@взлететь", "whoosh-up", 0.5, True),
    ("@Упал", "thud", 0.8, True),
    ("@Час", "tick-clock", 0.45, False),
    ("@сдвинулась", "error-down", 0.4, True),
    ("@пролетал", "whoosh-pan-rl", 0.55, True),
    ("@рухнул", "power-off", 0.45, True),
    ("@кусты", "steps-debris", 0.6, True),
    ("@гаснут", "shockwave-hit", 0.55, True),
    ("@обычный", "hit-sub", 0.65, True),
    ("@постучали", "thud", 0.9, True),
    ("@постучали+0.27", "thud", 0.85, True),
    ("@постучали+0.54", "thud", 0.9, True),
    ("@вторая", "pk-notify-notification-sfx-1", 0.45, True),
]

# ============================================================================= part 2
P2 = "sposobnosti-2"
s2 = lambda *a, **kw: scene(P2, *a, **kw)  # noqa: E731
scenes2 = [
    # --- hook: six in the morning, they came for me
    s2("b01", 0, "cut", captions={"mode": "slam", "pos": "middle"}),
    s2("b02", "@Люди", "push"),
    s2("b03", "@За неделю", "dip"),
    # --- chaos: invisible men in the shops, the lightning guy, 300 million volts
    s2("b04", "@Невидимки", "whip"),
    s2("b05", "@Парень", "push", camera={"move": "still", "shakeAt": ["@света"]}),
    s2("b06", "@А в одной", "cut", camera={"move": "still", "shakeAt": ["@одной+0.2"]},
       layers=[{**counter(300000000, "вольт|вольта|вольт в молнии", size=125), "at": "@молнии+0.3", "pos": "lower"}]),
    # --- the hurricane: the weather man, 250 km/h, x200 the power of all power stations
    s2("b07", "@Но самый", "dip"),
    s2("b08", "@Он закрутил", "zoom"),
    s2("b09", "@Ветер", "whip", layers=[{"block": "StatSlam", "at": "@больше+0.1", "props": {"value": "250", "unit": "",  # «км/ч» beside the number fell under the TikTok buttons
                                                                                          "label": "км/ч, скорость ветра"},
                                          "pos": {"preset": "stage", "dy": 160}}]),
    s2("b10", "@Такой ураган", "blur"),
    s2("b11", "@в 200", "push", layers=[{"block": "StatSlam", "at": "@раз", "props": {"value": "×200", "unit": "",
                                                                                     "label": "энергии всех электростанций мира"},
                                         "pos": {"preset": "stage", "dy": 160, "dx": -20, "scale": 0.9}}]),  # off the right 140 px
    # --- into the storm: the wind dies around me, a hand on his shoulder, the hurricane is gone
    s2("b12", "@Меня высадили", "dip"),
    s2("b13", "@Я пошёл", "push"),
    s2("b14", "@Я положил", "blur"),
    s2("b15", "@И ураган", "cut", captions={"mode": "slam", "pos": "middle"}, camera={"move": "still", "shakeAt": ["@исчез"]}),
    # --- the end: a queue at my door; the most needed power is being ordinary; a calm invite to the profile
    s2("b16", "@Теперь", "dip"),
    s2("b17", "@Те кто", "push"),
    s2("b18", "@Самая нужная", "blur"),
    s2("b19", "@А какую", "zoom"),
    # 28.10: the end is a warm thank-you, no ad: «Если история зацепила, оставь лайк и подпишись. Для меня это настоящая
    # суперсила.» The profile turns to the viewer, a few soft hearts float down on «лайк»
    {"id": "b20", "at": "@Если", "transition": "fade", "camera": "still", "bg": {**clip(P2, "b20", (1.06, 1.12)), "dim": 0.45},
     "layers": [{"block": "IPhone17", "pos": "full", "enter": "none", "props": {
         "enter": "flip", "flipAt": "@Если+0.1", "flipDur": 1.0, "float": True, "shadow": 0, "color": "#2C3A4F",
         "screen": profile([COVER2, COVER1] + OTHER),
         "cam": [k(0, [0, 2.3, 10.8], [0, 2.25, 0], 30), k(1.1, [0.35, 2.32, 10.4], [0, 2.25, 0], 30),
                 k(2.1, [0, 2.53, 5.4], [0, 2.7, 0], 30, "inOut"), k(5, [0, 2.5, 5.1], [0, 2.5, 0], 30),
                 k(8.9, [0, 2.48, 4.8], [0, 2.5, 0], 30, "inOut")]}},
                {"block": "StarRain", "at": "@лайк", "pos": "full", "props": {"kind": "heart", "count": 24, "color": "#FF5C7A", "dur": 3.4}}]},
]
sfx2 = [
    ("@пришли", "door-creak", 0.7, False),
    ("@нужен", "sting-dark", 0.5, True),
    ("@сломался", "glitch-medium", 0.45, True),
    ("@Невидимки", "suck-in", 0.4, True),
    ("@молниями", "hum-on", 0.45, False),
    ("@света", "power-off", 0.75, True),
    ("@одной+0.2", "strike", 0.7, True),
    ("@погодой", "rumble-distant", 0.6, False),
    ("@ураган", "wind-ash", 0.55, False),
    ("@Ветер", "wind", 0.6, False),
    ("@бури", "wind", 0.45, False),
    ("@стихал", "whoosh-down", 0.45, True),
    ("@плечо", "hit-soft", 0.6, True),
    ("@исчез-0.3", "suck-in", 0.5, False),
    ("@исчез", "shockwave-hit", 0.85, True),
    ("@очередь", "steps-concrete", 0.4, False),
    ("@силой", "glitch-short", 0.4, True),
    ("@обычным", "reveal-glow", 0.55, False),
    ("@ты#2", "sparkle", 0.5, True),
    ("@Если+0.1", "pk-pop-ui-menu", 0.45, False),
    ("@лайк", "sparkle-rise", 0.35, False),
    ("@суперсила", "sparkle", 0.4, True),
]

SPECS = {P1: spec(P1, scenes1, sfx1, 2.6), P2: spec(P2, scenes2, sfx2, 2.6)}

if __name__ == "__main__":
    for pid, sp in SPECS.items():
        d = OUT / pid
        d.mkdir(parents=True, exist_ok=True)
        (d / "spec.json").write_text(json.dumps(sp, ensure_ascii=False, indent=1), encoding="utf-8")
        print(pid, "scenes", len(sp["scenes"]), "sfx", len(sp["sfx"]))
