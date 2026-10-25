"""Storyboard for nk-escape: the 2017 Panmunjom defector tells his story in first person (~51 s).
Custom 3D scenes from engine/src/three/nkReel.tsx (+ RescueTest from nk.tsx); every scene, BigType line and sound
is anchored to the voice. Sounds are the user's pack (projects/nk-escape/sfx-src) plus a few UI/cinematic cues.

    python -I storyboard.py   -> engine/public/projects/nk-escape/spec.json
"""
import json
from pathlib import Path

RS = Path(__file__).resolve().parents[3]
P = RS / "engine" / "public" / "projects" / "nk-escape"
SRC = "projects/nk-escape/sfx-src/"
BRAND = json.loads((RS / "engine" / "src" / "brand.json").read_text(encoding="utf-8"))


def k(t, pos, tgt, fov=None, ease=None):
    d = {"t": t, "pos": pos, "target": tgt}
    if fov:
        d["fov"] = fov
    if ease:
        d["ease"] = ease
    return d


def bg(block, **props):
    return {"block": block, "props": props}


def tr(kind, dur=None):
    d = {"type": kind, "sfx": False}
    if dur:
        d["dur"] = dur
    return d


def big(lines, at, treatment, enter="slam"):
    return {"block": "BigType", "pos": "center", "props": {"lines": lines, "at": at, "treatment": treatment, "enter": enter, "upper": True}}


PROFILE = {"block": "TikTokProfile", "props": {**{key: BRAND[key] for key in ("name", "handle", "badge", "bio", "link", "avatar", "tiles")}, "pinned": 1, "highlightAt": "@шапку"}}

# scenes anchored to a word start PICTURE_LEAD = 0.07 s early: in-scene event times below include it
scenes = [
    # 1. hook: running, looking back over the shoulder: the squad raises rifles and opens fire
    {"id": "hook-look", "at": 0, "camera": "still",
     "bg": bg("NkChase", tau0=3.36, look=[3.1, 2.0])},
    # 2. hit on «Пять» (flash-forward of the fall), giant type carries the line
    {"id": "hook-hit", "at": "@Пять", "transition": tr("hardcut"), "camera": "still", "captions": False,
     "bg": bg("NkFall", tau0=4.49),
     "layers": [big(["5 пуль", "и я их", "не виню"], ["@Пять", "@их", "@виню"], ["solid", "outline", "mark"])]},
    # 3. November 2017, the barracks: a drink from the aluminium cup
    {"id": "barracks-drink", "at": "@Ноябрь", "transition": tr("dip", 0.4), "camera": "still",
     "bg": bg("NkBarracks", mode="drink")},
    # 4. the fight: fist on the table on «поругался», the friend yells, then the dread on «расстреляют»
    {"id": "barracks-slam", "at": "@Выпил", "transition": tr("cut"), "camera": "still",
     "bg": bg("NkBarracks", mode="slam", slamAt=0.97, lookAt=2.27, dreadAt=4.27)},
    # 5. into the jeep: key, both hands on the wheel, «погнал»
    {"id": "drive-start", "at": "@Сел", "transition": tr("whip", 0.35), "camera": "still",
     "bg": bg("NkDrive", mode="start")},
    # 6. the checkpoint flies past, the sentry yells
    {"id": "checkpoint", "at": "@Пост", "transition": tr("cut"), "camera": "still",
     "bg": bg("NkDrive", mode="checkpoint")},
    # 7. drone over the 72-hour bridge, type carries the line
    {"id": "bridge", "at": "@Дальше", "transition": tr("zoom", 0.4), "camera": "still", "captions": False,
     "bg": bg("NkBridge"),
     "layers": [big(["мост", "за 72", "часа"], ["@мост", "@72", "@часа"], ["outline", "solid", "mark"])]},
    # 8. Panmunjom ahead
    {"id": "approach", "at": "@За ним", "transition": tr("whip", 0.3), "camera": "still",
     "bg": bg("NkDitch", mode="approach")},
    # 9. the wheel drops into the ditch, forward, back
    {"id": "ditch", "at": "@И тут", "transition": tr("cut"), "camera": "still",
     "bg": bg("NkDitch", mode="ditch", dropAt=0.77, revAt=[2.17, 2.83])},
    # 10. UN camera: stuck (the caption card «Вперёд, назад. Застрял.» carries the word)
    {"id": "cctv-stuck", "at": "@Застрял", "transition": tr("glitch", 0.3), "camera": "punch",
     "bg": bg("NkCctv", tau0=-1.28, jeepSpin=True, label="UNC CAM 04 · JSA", clock0=8)},
    # 11. out of the jeep and run; looks back on «Сзади»
    {"id": "run", "at": "@Я бегу", "transition": tr("glitch", 0.3), "camera": "still",
     "bg": bg("NkChase", tau0=-0.4, exit=True, look=[0.54, 0.9])},
    # 12. UN camera, tighter: one of them runs over the line and back
    {"id": "cctv-cross", "at": "@Один", "transition": tr("glitch", 0.3), "camera": "still",
     "bg": bg("NkCctv", tau0=2.14, label="UNC CAM 07 · MDL", clock0=13,
              cam=[k(0, [-6, 5.5, 12], [-13.5, 0.6, -3], 38), k(3, [-6.2, 5.5, 12], [-13.2, 0.6, -2.5], 36)])},
    # 13. hit on «Удар», hit on «Ещё», down into the leaves on «Падаю»
    {"id": "fall", "at": "@Удар", "transition": tr("hardcut"), "camera": "still",
     "bg": bg("NkFall", tau0=4.49)},
    # 14. three ROK soldiers crawl in and drag him behind the wall
    {"id": "rescue", "at": "@Трое", "transition": tr("blur", 0.5), "camera": "still",
     "bg": bg("RescueTest", offset=2.6, rate=1.3)},
    # 15. the helicopter (cut a beat before the word, sound leads)
    {"id": "heli", "at": "@тащат+0.85", "transition": tr("cut"), "camera": "still",
     "bg": bg("NkHeli")},
    # 16. the operating table; white-out on «И выжил»
    {"id": "surgery", "at": "@Операция", "transition": tr("blur", 0.4), "camera": "still",
     "bg": bg("NkSurgery", whiteAt=3.03)},
    # 17. the line today: guards facing each other between the blue huts
    {"id": "line", "at": "@А тех", "transition": tr("fade", 0.5), "camera": "still",
     "bg": bg("NkOutro", view="line")},
    # 18. drone over the line -> CTA: iPhone rises, flips to the profile
    {"id": "wide-cta", "at": "@На их", "transition": tr("blur", 0.4), "camera": "still",
     "bg": {**bg("NkOutro", view="wide"), "dim": 0.55, "dimAt": "@Кстати"},
     "layers": [{"block": "IPhone17", "pos": "full", "enter": "none", "at": "@Кстати", "props": {
         "enter": "flip", "flipAt": "@агент", "flipDur": 1.2, "float": True, "shadow": 0, "screen": PROFILE,
         "cam": [k(0, [0, 2.3, 10.8], [0, 2.25, 0], 30), k(3.9, [0.35, 2.32, 10.4], [0, 2.25, 0], 30),
                 k(4.9, [0, 2.53, 5.4], [0, 2.53, 0], 30, "inOut"), k(8, [0, 2.5, 5.1], [0, 2.5, 0], 30)]}}]},
]


def snd(at, name, vol, frm=0.0, dur=None, fade=None):
    d = {"at": at, "id": name, "src": SRC + name + ".mp3", "volume": vol, "from": frm}
    if dur:
        d["dur"] = dur
    if fade:
        d["fade"] = fade
    return d


def lib(at, name, vol, peak=True):
    return {"at": at, "id": name, "volume": vol, "alignPeak": peak}


sfx = [
    # hook: running, the squad opens fire, two hits, ringing
    snd(0.0, "run_gravel", 0.55, 0.0, 1.25, 0.15),
    snd(0.0, "breathing_run", 0.5, 0.1, 1.3, 0.2),
    snd(0.28, "ak_burst", 0.55, 0.15, 1.0, 0.15),
    snd(0.85, "bullet_whiz", 0.6),
    snd(1.18, "bullet_impact-singlebullet", 0.95),
    snd(1.3, "gunshots_distant", 0.35, 1.5, 1.9, 0.4),
    snd(2.18, "bullet_impact-singlebullet", 0.95),
    snd(1.25, "ear_ringing", 0.3, 0.0, 2.1, 0.5),
    lib("@виню", "hit-sub", 0.55),
    # barracks: the cup, the fist, the dread
    snd(3.9, "cup_table", 0.35),
    snd(6.32, "cup_table", 0.6),
    snd("@поругался-0.1", "4times-fist_table", 0.9, 0.55, 0.9, 0.2),
    lib("@расстреляют", "dread-rise", 0.55),
    snd("@расстреляют-0.4", "heartbeat", 0.65, 0.45, 1.5, 0.4),
    # the jeep: starter, gear, engine all the way to the ditch (these files are hot: keep them ~7 dB under the voice)
    snd(12.8, "engine_start", 0.32, 0.0, 1.3, 0.3),
    snd(13.3, "gear_shift", 0.25, 0.1, 0.6, 0.15),
    snd(13.39, "engine_drive", 0.13, 0.0, 8.4, 0.4),
    lib("@72", "hit-sub", 0.5),
    # the ditch, the wheels spinning, the UN camera
    snd("@проваливается-0.24", "ditch_crash", 0.5, 4.2, 2.0, 0.5),
    snd("@Вперёд", "wheel_stuck", 0.2, 0.0, 2.24, 0.3),
    lib("@Застрял", "trans-glitch-cut", 0.5),
    lib("@Застрял", "hit-sub", 0.5),
    # the run
    lib("@Я бегу", "trans-glitch-cut", 0.45),
    snd(26.25, "run_gravel", 0.6, 0.0, 2.4, 0.2),
    snd(26.12, "breathing_run", 0.55, 0.0, 2.55, 0.25),
    snd(27.9, "ak_single", 0.35),
    lib("@Один", "trans-glitch-cut", 0.45),
    snd(29.9, "gunshots_distant", 0.45, 1.5, 1.2, 0.2),
    # hits and the fall
    snd(30.95, "ak_burst", 0.6, 0.15, 1.4, 0.2),
    snd("@Удар-0.02", "bullet_impact-singlebullet", 1.0),
    snd(31.5, "bullet_whiz", 0.55),
    snd("@Ещё-0.02", "bullet_impact-singlebullet", 1.0),
    snd(31.2, "ear_ringing", 0.38, 0.0, 3.4, 0.6),
    snd(33.41, "body_fall_leaves", 0.85),
    snd(32.3, "heartbeat", 0.5, 0.5, 5.4, 0.6),
    # rescue -> helicopter -> surgery
    snd(35.99, "drag_body", 0.6, 2.5, 1.9, 0.3),
    snd(36.9, "helicopter", 0.6, 1.4, 2.25, 0.4),
    snd(38.06, "hospital_beep", 0.42, 0.0, 3.9, 0.3),
    lib("@выжил", "hit-cinematic", 0.55),
    # the line today
    snd(42.84, "wind_leaves", 1.0, 2.0, 8.2, 1.0),
    # CTA
    lib("@Кстати", "pk-shimmer-ui-dissolvre-sfx", 0.6, False),
    lib("@агент+1.2", "pk-pop-ui-menu", 0.55, False),
    lib("@шапку", "pk-click-ui-button", 0.7),
    lib("@профиля", "pk-notify-notification-sfx-1", 0.8),
]

spec = {
    "id": "nk-escape", "mode": "explainer", "style": "dusk", "fps": 60,
    "voice": {"src": "projects/nk-escape/voice.wav", "words": "projects/nk-escape/words.json"},
    "music": {"src": "music/dark-cinematic.m4a", "volume": 0.12, "duck": 0.45},
    "tail": 1.6,
    "autoSfx": False,
    "captions": {"mode": "editorial", "pos": "top", "uppercase": True},
    "sfx": sfx,
    "scenes": scenes,
}
(P / "spec.json").write_text(json.dumps(spec, ensure_ascii=False, indent=1), encoding="utf-8")
print("scenes", len(scenes), "sfx", len(sfx))
