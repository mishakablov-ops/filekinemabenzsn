"""Storyboard of «Баронесса-пулемётчица» v2 (29.10.2026, mike: «жёсткий юмор-экшн», «звук не как в классике»):
fast cuts (whip/cut/zoom), camera shakes on the volleys and her orders, slams on the numbers, the war-sound bed
(gunfire, explosions, boots, tank engines from the kit's own sfx) over a driving beat; the calm-free ending is the
TikTok profile with hearts on «лайк» and a frame round the header on «шапке», then «Свободны».

    python -I engine/storyboard_v2.py  -> <RS>/engine/public/projects/baronessa-v2/spec.json
"""
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

ROOT = Path(__file__).resolve().parents[2]
RS = ROOT / "KINEMA" / "skills" / "reel-studio"
PID = "baronessa-v2"
PUB = RS / "engine" / "public" / "projects" / PID
KIT_SFX = ROOT / "baronessa" / "audio" / "sfx"

import storyboard as V1  # noqa: E402  (profile(), k(), OTHER tiles)


def clip(sid, zoom=(1.0, 1.04), **kw):
    return {"block": "VideoBG", "props": {"src": f"projects/{PID}/clips/{sid}.mp4", "zoom": list(zoom), **kw}}


def scene(sid, at, transition="cut", shake=None, zoom=(1.0, 1.04), layers=None, **kw):
    s = {"id": sid, "at": at, "transition": transition,
         "camera": {"move": "still", "shakeAt": shake} if shake else "still", "bg": clip(sid, zoom)}
    if layers:
        s["layers"] = layers
    s.update(kw)
    return s


def slam(value, label, at, dy=160, scale=1.0):
    return {"block": "StatSlam", "at": at, "props": {"value": value, "unit": "", "label": label},
            "pos": {"preset": "stage", "dy": dy, "dx": -20, "scale": scale}}


scenes = [
    scene("d01", 0, "cut", shake=["@кончились"], captions={"mode": "slam", "pos": "middle"}),
    scene("d02", "@За одну ночь", "whip"),
    scene("d03", "@Без единого", "zoom"),
    scene("d04", "@Год сорок", "dip", layers=[slam("194?", "историки спорят", "@Год+0.15")]),
    scene("d05", "@Ставка", "push"),
    scene("d06", "@Товарищи", "cut"),
    scene("d07", "@Один генерал", "whip", shake=["@обморок"]),
    scene("d08", "@Через сутки", "zoom", layers=[slam("100 000", "баронесс", "@Сто+0.1")]),
    scene("d09", "@Все одинаковые", "push"),
    scene("d10", "@Танки", "whip", shake=["@Танки+0.3"]),
    scene("d11", "@Очередь на танк", "cut", layers=[slam("6 ЛЕТ", "очередь на танк", "@шесть+0.05")]),
    scene("d12", "@Пулемёты", "cut", shake=["@купонами"]),
    scene("d13", "@Первый удар", "whip", shake=["@удар"]),
    scene("d13b", "@Стрелка", "zoom"),
    scene("d14", "@Медленно", "cut"),
    scene("d15", "@Огонь", "cut", shake=["@Огонь", "@Огонь+0.4"], captions={"mode": "slam", "pos": "middle"}),
    scene("d16", "@Шесть тысяч", "whip", shake=["@Шесть", "@секунду"], layers=[slam("6000/с", "купонов", "@Шесть+0.1")]),
    scene("d17", "@У врага", "zoom"),
    scene("d18", "@А чек", "cut"),
    scene("d19", "@Графство сдаётся", "push"),
    scene("d20", "@Крепость Эрмес", "dip", layers=[slam("40", "дней осады", "@Сорок+0.1")]),
    scene("d21", "@Враг предлагает", "whip", layers=[slam("−50%", "предлагает враг", "@минус+0.1")]),
    scene("d22", "@Минус пятьдесят#2", "cut"),
    scene("d23", "@На сорок первый", "push"),
    scene("d24", "@Эрмесовка", "whip", shake=["@Эрмесовка", "@битва"]),
    scene("d24b", "@Баронессы идут", "zoom", shake=["@стеной"]),
    scene("d25", "@Стена тоже", "cut"),
    scene("d26", "@С неба", "push"),
    scene("d27", "@Ни шагу", "cut", shake=["@назад", "@касса"], captions={"mode": "slam", "pos": "middle"}),
    scene("d28", "@Город сдаёт", "blur"),
    scene("d29", "@К утру", "dip"),
    scene("d29b", "@Луивиттония", "push"),
    scene("d30", "@Кроме рынка", "cut"),
    scene("d31", "@Запишите", "zoom"),
    scene("d32", "@Так родилась", "whip"),
    scene("d33", "@Строгая", "cut"),
    # d34 «Полная» was 0.96 s after the caption fix (QA: shots under 1 s flash by) -> d33 runs through it
    scene("d35", "@Непобедимая", "cut", shake=["@Непобедимая"]),
    {"id": "d36", "at": "@Если поржал", "transition": "fade", "camera": "still",
     "bg": {**clip("d36", (1.04, 1.1)), "dim": 0.45},
     "layers": [{"block": "IPhone17", "pos": "full", "enter": "none", "props": {
         "enter": "flip", "flipAt": "@Если+0.1", "flipDur": 0.8, "float": True, "shadow": 0, "color": "#2C3A4F",
         "screen": V1.profile(V1.OTHER, highlightAt="@шапке"),
         "cam": [V1.k(0, [0, 2.3, 10.8], [0, 2.25, 0], 30), V1.k(1.0, [0.35, 2.32, 10.4], [0, 2.25, 0], 30),
                 V1.k(1.9, [0, 2.53, 5.4], [0, 2.7, 0], 30, "inOut"), V1.k(5, [0, 2.5, 5.1], [0, 2.5, 0], 30)]}},
                {"block": "StarRain", "at": "@лайк", "pos": "full",
                 "props": {"kind": "heart", "count": 26, "color": "#FF5C7A", "dur": 3.0}}]},
    scene("d37", "@Свободны", "cut", zoom=(1.0, 1.06), captions={"mode": "slam", "pos": "middle"}),
]

# war sounds from the kit (synthesised by sfx_mbg.py, our own) + the engine library
K = lambda n: f"projects/{PID}/sfx/mbg-{n}.wav"  # noqa: E731
war = [
    ("@кончились", "gunfire", "gunfire-far", 0.9, None), ("@кончились+0.1", "boom", "explosion-far", 0.8, None),
    ("@Без единого", "coins", "coins", 0.6, None), ("@Через сутки", "boots", "march-boots", 0.75, 4.5),
    ("@Танки", "tank", "tank-engine", 0.85, 3.2), ("@Первый удар", "boom2", "explosion-far", 0.8, None),
    ("@Медленно", "boots2", "march-boots", 0.6, 2.4), ("@Огонь", "gunfire2", "gunfire-far", 1.0, None),
    ("@Шесть тысяч", "gunfire3", "gunfire-far", 0.85, None), ("@Крепость Эрмес", "boom3", "explosion-far", 0.6, None),
    ("@Эрмесовка", "gunfire4", "gunfire-far", 0.9, None), ("@Эрмесовка+0.6", "boom4", "explosion-far", 0.85, None),
    ("@Баронессы идут", "boots3", "march-boots", 0.8, 4.0), ("@Ни шагу", "boom5", "explosion-far", 0.7, None),
    ("@Город сдаёт", "coins2", "coins", 0.55, None), ("@Так родилась", "crowd", "crowd-dense", 0.5, 3.5),
]
lib_sfx = [
    ("@кончились", "hit-sub", 0.7, True), ("@патрона", "glitch-short", 0.4, True), ("@купоны", "shockwave-hit", 0.6, True),
    ("@спорят", "pk-pop-ui-menu", 0.4, True), ("@чек", "hit-soft", 0.6, True), ("@обморок", "thud", 0.8, True),
    ("@путает", "pk-result-failure", 0.45, True), ("@шесть", "hit-sub", 0.6, True), ("@Каблуки", "pop-high", 0.5, True),
    ("@кошельке", "pk-digital-digitasl-burst-sfx", 0.5, True), ("@сохранили", "pop-high", 0.5, True),
    ("@было", "error-down", 0.5, True), ("@пятьдесят", "whoosh-pan-lr", 0.5, True), ("@оскорбление", "hit-sub", 0.6, True),
    ("@очереди", "pk-notify-notification-sfx-1", 0.45, True), ("@пилотке", "pop-high", 0.5, True),
    ("@два", "pk-pop-ui-menu", 0.45, True), ("@размер", "pk-result-failure", 0.5, True), ("@оранжевая", "reveal-glow", 0.5, False),
    ("@дома", "pk-click-ui-button", 0.5, True), ("@шрифтом", "pk-pop-ui-menu", 0.45, True), ("@Непобедимая", "shockwave-hit", 0.7, True),
    ("@Если+0.1", "pk-shimmer-ui-dissolvre-sfx", 0.4, False), ("@лайк", "sparkle-rise", 0.35, False),
    ("@Свободны", "hit-sub", 0.7, True),
]

spec = {
    "id": PID, "mode": "explainer", "style": "blaze", "fps": 60,
    "voice": {"src": f"projects/{PID}/voice.wav", "words": f"projects/{PID}/words.json"},
    "music": {"src": f"projects/{PID}/music-bed.wav", "volume": 0.16, "duck": 0.55, "fadeOut": 0.5},
    "tail": 2.4, "autoSfx": False, "grain": 0.05, "vignette": 0.22,
    "captions": {"mode": "editorial", "pos": "top", "uppercase": True},
    "sfx": [{"at": a, "id": i, "src": K(f), "volume": v, **({"dur": d, "fade": 0.6} if d else {})} for a, i, f, v, d in war]
           + [{"at": a, "id": i, "volume": v, "alignPeak": ap} for a, i, v, ap in lib_sfx],
    "scenes": scenes,
}

if "--no-music" in sys.argv:   # mike 29.10: the music («Gopher Mambo») goes in on TikTok from its sound library
    spec.pop("music")

if __name__ == "__main__":
    (PUB / "sfx").mkdir(parents=True, exist_ok=True)
    for f in KIT_SFX.glob("mbg-*.wav"):
        shutil.copy(f, PUB / "sfx" / f.name)
    (PUB / "spec.json").write_text(json.dumps(spec, ensure_ascii=False, indent=1), encoding="utf-8")
    print(PID, "scenes", len(scenes), "sfx", len(spec["sfx"]))
