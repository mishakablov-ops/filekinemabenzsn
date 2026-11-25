"""Storyboard for «Канал без лица» (kanal-bez-lica): every scene is an animated Blender clip (VideoBG), captions on top,
no music (mike lays his own house music), sounds on the events of the 3D picture, the end card «ПОДДЕРЖИ ЛАЙКОМ И
ПОДПИСКОЙ» in the «coins» theme over the profile on the iPhone (no link and no «Телеграм» on screen, promo-funnel.md).

    python storyboard.py [--rs RS] [--shots SHOTS_JSON]

RS = KINEMA/skills/reel-studio (default: env KINEMA_RS). Needs <RS>/engine/public/projects/kanal-bez-lica/words.json
(voice_sections.py) and shots.json filled by tools/build_timeline.py (clip starts and in-shot events), and writes
spec.json there. Sounds are checked against the engine's sfx index (first live id of each candidate list wins), tiles and
the avatar against public/brand; anything missing is dropped with a note, never invented.
"""
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "tools"))
from build_timeline import TIN, TRANS, Words  # noqa: E402


def arg(name, default):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


PID = "kanal-bez-lica"
RS = Path(arg("--rs", os.environ.get("KINEMA_RS", str(HERE.parents[2] / "kinema" / "skills" / "reel-studio"))))
PUB = RS / "engine" / "public"
P = PUB / "projects" / PID
SHOTS = Path(arg("--shots", str(HERE.parent / "blender" / "shots.json")))
TAIL = 3.2

# ----------------------------------------------------------------------------- engine checks
try:
    _IDX = {x["id"]: x for x in json.loads((PUB / "sfx" / "index.json").read_text(encoding="utf-8"))}
except FileNotFoundError:
    _IDX = None
NOTES = []


def live(i, depth=0):
    """the library file an id finally plays (aliases followed), None = silent / unknown"""
    x = _IDX.get(i) if _IDX is not None else None
    if x is None or depth > 6:
        return None
    if x.get("alias"):
        return live(x["alias"], depth + 1)
    return None if x.get("retired") else x


def pick(cands):
    cands = [cands] if isinstance(cands, str) else cands
    if _IDX is None:
        return cands[0], None
    for c in cands:
        x = live(c)
        if x:
            return c, x
    NOTES.append(f"no live sound among {cands}: cue dropped")
    return None, None


def brand(path, fallback=None):
    if (PUB / path).exists() or not PUB.exists():
        return path
    NOTES.append(f"{path} missing in public/: {'using ' + fallback if fallback else 'dropped'}")
    return fallback


# ----------------------------------------------------------------------------- timing
W = Words(P / "words.json")
S = json.loads(SHOTS.read_text(encoding="utf-8"))
SH = {s["id"]: s for s in S["shots"]}
if "start" not in SH["k02"] or not SH["k02"].get("events"):
    raise SystemExit("shots.json has no clip starts/events: run tools/build_timeline.py on words.json first")


def c0(sid):
    return SH[sid]["start"]


def ev(sid, k, d=None):
    return SH[sid]["events"].get(k, d)


# ----------------------------------------------------------------------------- blocks
def k(t, pos, tgt, fov=None, ease=None):
    d = {"t": round(t, 2), "pos": pos, "target": tgt}
    if fov:
        d["fov"] = fov
    if ease:
        d["ease"] = ease
    return d


def clip(sid, zoom=(1.0, 1.03), **kw):
    return {"block": "VideoBG", "props": {"src": f"projects/{PID}/clips/{sid}.mp4", "zoom": list(zoom), **kw}}


def scene(sid, at, zoom=(1.0, 1.03), layers=None, **kw):
    s = {"id": sid, "at": at, "transition": TRANS[sid], "camera": "still", "bg": clip(sid, zoom)}
    if layers:
        s["layers"] = layers
    s.update(kw)
    return s


# real covers of the channel's own reels only (no invented tiles, no «Гибрид», no closed «Академия»)
TILES = [t for t in (brand(f"brand/tiles/{n}.jpg") for n in (
    "cover-sposobnosti-1", "cover-sposobnosti-2", "cover-million-16", "cover-kosmos-dlya-vseh-v2", "cover-mir-bez-granic",
    "cover-posledniy-chelovek-blender", "cover-edinyi-yazyk", "cover-nuclear", "cover-coffee-agent")) if t]


def profile(**kw):
    # promo-funnel.md: no link and no «Телеграм» on screen; the bio without «прямо здесь 👇» (there is nothing to point at)
    return {"block": "TikTokProfile", "props": {
        "dark": True, "name": "aipollon", "handle": "videopollon", "badge": "Verified business",
        "bio": "Делаем ролики с ИИ: 3D, пиксель и новые стили", "link": "",
        "avatar": brand("brand/aipollon-avatar-hermes.png", "brand/avatar.jpg"), "tiles": TILES, "pinned": 2, **kw}}


# ----------------------------------------------------------------------------- scenes
_, end_last = W.find("начать", W.find("Кто напишет")[0])       # the last word of the voice
# the end card cuts in right after the voice (captions end with it, the title takes their place: video-ending-rule);
# 25.11 cloud test: started on «расскажу», the last caption and the title fought over the top band
END_AT = "@начать>+0.2"
END0 = end_last + 0.2 - 0.07                                    # the end scene's cut, seconds
end_from = END0 - TIN["fade"] / 2


def at_end(rel):
    """an absolute anchor rel seconds after the end card's cut"""
    return f"@начать>+{0.13 + rel:.2f}"


def pill(text, at, dy, preset="upper", **kw):
    return {"block": "Pill", "at": at, "pos": {"preset": preset, "dy": dy}, "enter": "pop",
            "props": {"text": text, "size": 40, "dark": True, **kw}}


def chip(text, at, dy, preset="lower", size=48, accent=False):
    """v2: one solid tag (Chips with one item): the dusk theme's Pill is 10 % white glass (dark) or white with light ink
    (light) and is unreadable over the bright day room; the Chips card is solid dark with light ink, the accent one orange"""
    return {"block": "Chips", "at": at, "pos": {"preset": preset, "dy": dy}, "enter": "pop",
            "props": {"items": [text], "size": size, "accentIdx": [0] if accent else []}}


scenes = [
    scene("k01", 0, zoom=(1.0, 1.04)),          # hook: the faceless feed on the phone
    scene("k1b", "@В ТикТоке"),                 # v2: the «Для вас» feed plays our 3D reel, hearts fly, «в рекомендациях»
    scene("k02", "@А где просмотры"),           # the sofa, the phone pings: an ad offer
    scene("k03", "@баннеры"),                   # the phone: banners, integrations, partner programs (no sums)
    scene("k04", "@Но реклама"),                # night editing seen from the front: the face in the monitor light
    scene("k05", "@С KINEMA"),                  # the monitor close: one phrase → checks: script, voice, 3D scenes, captions
    # v2 «Плюсы такого монтажа»: the hero leans back, a pill per plus on its word
    # (lower, under the face: the hero's face sits in the upper middle of this shot; solid tags, see chip())
    scene("k5c", "@Плюсы", layers=[chip("без камеры", "@камеры", -120), chip("без монтажёра", "@монтажёра", 0),
                                     chip("3D выделяется в ленте", "@выделяется", 120, accent=True)]),
    # v2 split screen (mike): the same wave and turn, 3D on top and pixel below; labels on each half
    scene("k5s", "@Одно действие", layers=[
        chip("3D", "@стиля", -75, "center", size=54, accent=True), chip("ПИКСЕЛЬ", "@пиксель", 75, "center", size=54, accent=True)],
          captions={"pos": "bottom"}),          # the top band would sit on the 3D hero's head; below it is the pixel copy
    scene("k06", "@а скоро"),                   # the style menu: the «скоро» tiles
    # the wall calendar fills with covers; «больше мест под баннеры» — ad tags pop low (v2: the hero stands left of the
    # calendar, the tags must not cross his face or the calendar)
    scene("k07", "@Один вечер", layers=[{"block": "Chips", "at": "@больше роликов", "pos": {"preset": "lower", "dy": 0},
                                          "props": {"items": ["баннер", "интеграция", "партнёрка"], "accentIdx": [0]}}]),
    scene("k08", "@Не шаришь"),                 # the call on the monitor, then the camera turns to the hero: thumbs up
    scene("k09", "@Кто напишет"),               # «канал» typed into the comments
    # the end card (video-ending-rule, themed «coins»): the k09 clip goes on dimmed, the profile flips in on the iPhone,
    # «ПОДДЕРЖИ ЛАЙКОМ И ПОДПИСКОЙ» lands where the captions were once the voice is over, coins rain, two jokes
    {"id": "kend", "at": END_AT, "transition": "fade", "camera": "still", "captions": False,
     "bg": {**clip("k09", (1.04, 1.1), startFrom=round(end_from - c0("k09"), 3)), "dim": 0.55},
     "layers": [
         # the phone sits low (its top under the jokes, the grid runs into the TikTok buttons), the header readable
         {"block": "IPhone17", "pos": "full", "enter": "none", "props": {
             "enter": "flip", "flipAt": 0.0, "flipDur": 0.9, "float": True, "shadow": 0, "color": "#2C3A4F",
             "screen": profile(),
             "cam": [k(0, [0, 2.75, 12.4], [0, 2.7, 0], 30), k(1.0, [0.3, 2.77, 11.4], [0, 2.72, 0], 30),
                     k(2.2, [0, 2.75, 9.6], [0, 2.75, 0], 30, "inOut"), k(5.0, [0, 2.75, 9.3], [0, 2.75, 0], 30)]}},
         # the last caption card holds ~2.2 s after the voice (captions/Captions.tsx), so the title sits just under it;
         # words glued with NBSP: the cloud test lost the spaces between Title words («ПОДДЕРЖИЛАЙКОМ»)
         {"block": "Title", "at": 0.3, "pos": {"preset": "top", "dy": 130}, "enter": "none",
          "props": {"text": "ПОДДЕРЖИ\u00a0ЛАЙКОМ / [И\u00a0ПОДПИСКОЙ]", "size": 80, "weight": 900}},
         {"block": "StarRain", "at": 0.35, "pos": "full", "props": {"kind": "coin", "count": 22, "dur": 3.0}},
         {"block": "Pill", "at": 0.85, "pos": {"preset": "upper", "dy": 0}, "enter": "pop",
          "props": {"text": "лайк — бесплатная интеграция", "size": 38, "dark": True}},
         {"block": "Pill", "at": 1.3, "pos": {"preset": "upper", "dy": 95}, "enter": "pop",
          "props": {"text": "подписка дешевле монтажёра", "size": 38, "dark": True}},
     ]},
]

# ----------------------------------------------------------------------------- sounds (no music, no airy noise)
NOTIFY_A = ["usr-notify-ding-mid-swell-102", "pk-notify-notification-sfx-1"]
NOTIFY_B = ["usr-notify-ding-mid-swell-091", "pk-notify-system-alert-sfx"]
SUCCESS = ["usr-success-jingle-mid-late-282", "usr-notify-ding-mid-snap-171", "pk-notify-notification-sfx-1"]
TAP = ["usr-keyboard-typing-bright-snap-179", "pk-click-ui-button"]
POP = ["pk-pop-ui-menu"]
CLICK = ["usr-mouse-click-bright-swell-108", "pk-click-ui-button"]
COINS = ["usr-coin-bell-bright-swell-083", "pk-shimmer-ui-dissolvre-sfx"]
CUES = []


def cue(at, cands, vol, peak=False, dur=None, fade=0.25):
    i, x = pick(cands)
    if not i:
        return
    if dur is not None and x is not None:              # a long library sound played as a trimmed file
        CUES.append({"at": round(at, 3) if not isinstance(at, str) else at, "id": i, "src": x["file"], "from": 0,
                     "dur": round(dur, 2), "fade": fade, "volume": vol})
        return
    CUES.append({"at": round(at, 3) if not isinstance(at, str) else at, "id": i, "volume": vol, "alignPeak": peak})


# k1b: the feed: a like tap when the heart turns red (overlay frame 2 of 12), soft pops as the hearts fly
d1b = SH["k1b"]["dur"]
cue(c0("k1b") + d1b * 2 / 12, ["pk-click-ui-button"] + POP, 0.3)
for j in range(3):
    cue(c0("k1b") + d1b * (0.32 + 0.2 * j), POP, 0.18)
# k02: the ad offer pings on the phone
cue(c0("k02") + ev("k02", "ping"), NOTIFY_A, 0.5)
# k03: the other two notifications drop in on their words (the first is on screen at the cut, k02 just pinged)
for kk, cands in (("n2", NOTIFY_B), ("n3", NOTIFY_A)):
    cue(c0("k03") + ev("k03", kk), cands, 0.42)
# k04: night typing (0 → 45 % of the shot), then the clock races on «А монтаж одного — это часы»
d4 = SH["k04"]["dur"]
cue(c0("k04") + 0.05, ["typing-long"], 0.3, dur=d4 * 0.45 - 0.05)
t_mont = W.find("А монтаж", c0("k04"))[0]
cue(t_mont - 0.05, ["usr-clock-fast-bright-late-072"], 0.32, dur=c0("k05") + 0.4 - t_mont, fade=0.4)
# k05: one phrase typed, then a soft pop on each check; the fourth check (субтитры) makes the reel ready: a small jingle
tt = ev("k05", "typed")
cue(c0("k05") + 0.05, ["typing-medium", "typing-long"], 0.3, dur=max(0.4, tt - 0.1))
for j in range(3):
    cue(c0("k05") + ev("k05", f"s{j}"), POP, 0.32)
cue(c0("k05") + ev("k05", "s3"), SUCCESS, 0.38)
# k5c: a pop per plus pill (on its word)
for j in range(3):
    cue(c0("k5c") + ev("k5c", f"p{j}"), POP, 0.3)
# k5s: a click per style label, a whoosh-free «tick» on the turn is the picture itself
for w in ("стиля", "пиксель"):
    cue(W.find(w, c0("k5s"))[0], CLICK, 0.3)
# k06: «скоро» tiles light up: one pop
cue(W.find("скоро", c0("k06") - 0.3)[0], POP, 0.3)
# k07: covers fill the calendar: three soft pops; the ad tags pop on «больше роликов»
d7 = SH["k07"]["dur"]
for j in range(3):
    cue(c0("k07") + 0.2 + (d7 * 0.5 - 0.2) * (j + 0.5) / 3, POP, 0.22)
cue(W.find("больше роликов", c0("k07"))[0], NOTIFY_B, 0.32)
# k08: the call connects, the helper clicks the setup through, the thumb goes up
d8 = SH["k08"]["dur"]
cue(c0("k08") + 0.1, NOTIFY_B, 0.32)
cue(c0("k08") + d8 * 0.3, CLICK, 0.28)
cue(c0("k08") + ev("k08", "thumb") + 0.3, SUCCESS, 0.4)
# k09: «канал» typed letter by letter (the same frames as kanal.py v_comment), the send button lights up
t0, t1 = 0.3, ev("k09", "typed")
for j in range(1, 6):
    cue(c0("k09") + t0 + (t1 - t0) * j / 5, TAP, 0.35)
cue(c0("k09") + t1 + 0.15, POP, 0.3)
# end card: the flip, coins with the title, a pop per joke
cue(at_end(0.05), ["card-flip", "pk-pop-ui-menu"], 0.35)
cue(at_end(0.3), COINS, 0.38)
cue(at_end(0.85), POP, 0.3)
cue(at_end(1.3), POP, 0.3)

SPEC = {
    "id": PID, "mode": "explainer", "style": "dusk", "fps": 30,
    "voice": {"src": f"projects/{PID}/voice.wav", "words": f"projects/{PID}/words.json"},
    "tail": TAIL,
    "autoSfx": False,
    "grain": 0.02, "vignette": 0.12,
    "captions": {"mode": "editorial", "pos": "top", "uppercase": True},
    "sfx": CUES,
    "scenes": scenes,
}

if __name__ == "__main__":
    P.mkdir(parents=True, exist_ok=True)
    (P / "spec.json").write_text(json.dumps(SPEC, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{PID}: scenes {len(scenes)}, sfx {len(CUES)}, tiles {len(TILES)}, voice {W.dur:.2f} s, last word ends {end_last:.2f} s")
    for n in NOTES:
        print("NOTE", n)
