"""Storyboard for «Баронесса-пулемётчица» (style «Мемы»): every scene is an animated Blender clip (VideoBG), numbers are
KINEMA counters/slams, the calm ending is the TikTok profile on the iPhone over the marble hall with soft hearts on
«лайк», then the baroness's nod. Music: ambient-air bed + dark-cinematic rising in the battles (music_bed.py).

    python -I engine/storyboard.py   -> <RS>/engine/public/projects/baronessa/spec.json
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RS = ROOT / "KINEMA" / "skills" / "reel-studio"
PID = "baronessa"


def k(t, pos, tgt, fov=None, ease=None):
    d = {"t": round(t, 2), "pos": pos, "target": tgt}
    if fov:
        d["fov"] = fov
    if ease:
        d["ease"] = ease
    return d


def clip(sid, zoom=(1.0, 1.03), **kw):
    return {"block": "VideoBG", "props": {"src": f"projects/{PID}/clips/{sid}.mp4", "zoom": list(zoom), **kw}}


def scene(sid, at, transition="push", camera="still", zoom=(1.0, 1.03), layers=None, **kw):
    s = {"id": sid, "at": at, "transition": transition, "camera": camera, "bg": clip(sid, zoom)}
    if layers:
        s["layers"] = layers
    s.update(kw)
    return s


def slam(value, label, at, unit="", dy=160, scale=1.0):
    return {"block": "StatSlam", "at": at, "props": {"value": value, "unit": unit, "label": label},
            "pos": {"preset": "stage", "dy": dy, "dx": -20, "scale": scale}}


def counter(to, label, at, size=170):
    return {"block": "Counter", "at": at, "pos": "lower",
            "props": {"from": 0, "to": to, "label": label, "size": size, "labelSize": 48, "dur": 0.9}}


OTHER = ["brand/tiles/cover-sposobnosti-1.jpg", "brand/tiles/cover-sposobnosti-2.jpg",
         "brand/tiles/cover-posledniy-chelovek-blender.jpg", "brand/tiles/kosmos-dlya-vseh-v2.jpg",
         "brand/tiles/mir-bez-granic.jpg", "brand/tiles/edinyi-yazyk.jpg", "brand/tiles/fr-gibrid.jpg",
         "brand/tiles/cover-nuclear.jpg", "brand/tiles/quiet-evenings.jpg"]


def profile(tiles, **kw):
    return {"block": "TikTokProfile", "props": {
        "dark": True, "name": "aipollon", "handle": "videopollon", "badge": "Verified business",
        "bio": "Даем возможность делать самые качественные ролики с ии прямо здесь 👇🏻", "link": "https://t.me/aipollonvideo",
        "avatar": "brand/aipollon-avatar-hermes.png", "tiles": tiles, "pinned": 1, **kw}}


scenes = [
    # --- hook: the old photo; she was real
    scene("c01", 0, "cut", zoom=(1.0, 1.04)),
    scene("c02", "@А теперь", "dip"),
    # --- birth in a boutique family, 1918
    scene("c03", "@1918", "dip", layers=[slam("1918", "год рождения", "@1918+0.2")]),
    scene("c04", "@Её первое слово", "push"),
    scene("c05", "@Её первое слово#2", "zoom"),
    # --- childhood
    scene("c06", "@В 5", "blur"),
    scene("c07", "@В 10", "push"),
    # --- the coupon machine gun
    # mike 28.10: «добавь про 40-ые годы» -> a retro title as the 1940s battles begin (newsreel grade c08..c25)
    scene("c08", "@Взрослой", "dip", layers=[slam("1940-е", "эпоха великих распродаж", "@Взрослой+0.2")]),
    scene("c09", "@Пулемёт", "whip", camera={"move": "still", "shakeAt": ["@стреляет"]}),
    scene("c10", "@600", "cut", layers=[counter(600, "ценник|ценника|ценников в минуту", "@600+0.1")]),
    scene("c11", "@Ни одной", "push"),
    # --- the county KokoChanel
    scene("c12", "@Первым", "dip"),
    scene("c13", "@Баронесса не", "push"),
    scene("c14", "@А чек", "blur"),
    scene("c15", "@Графство сдалось", "cut"),
    # --- the fortress Hermès
    scene("c16", "@Потом", "dip"),
    scene("c17", "@40", "cut", layers=[counter(40, "день|дня|дней осады", "@40+0.1")]),
    scene("c18", "@Скидку в", "whip", layers=[slam("−50%", "скидка от врага", "@50+0.1")]),
    scene("c19", "@Мы не", "push"),
    scene("c20", "@Только лист", "cut"),
    # --- Ermesovka
    scene("c21", "@А в год", "dip"),
    scene("c22", "@она взяла", "push"),
    scene("c23", "@Город", "blur"),
    scene("c24", "@Над ратушей", "push"),
    scene("c25", "@Оранжевый", "cut"),
    # --- the Republic of Birkin
    scene("c26", "@Так родилась", "dip"),
    scene("c27", "@Столица", "push"),
    scene("c28", "@Святыня", "blur"),
    scene("c29", "@Девиз", "push"),
    scene("c30", "@У каждого", "cut"),
    scene("c31", "@А у каждого", "push"),
    # --- the legend: lost near Birkin
    scene("c32", "@Говорят", "dip"),
    scene("c33", "@Зашла", "push"),
    scene("c34", "@Я вернусь", "blur"),
    # ending (28.10 mike: no «truth», like + profile header): the profile turns to the viewer, hearts on «лайк»,
    # a soft frame round bio+link on «шапке профиля»
    {"id": "c38", "at": "@Если", "transition": "fade", "camera": "still", "bg": {**clip("c38", (1.04, 1.1)), "dim": 0.45},
     "layers": [{"block": "IPhone17", "pos": "full", "enter": "none", "props": {
         "enter": "flip", "flipAt": "@Если+0.1", "flipDur": 1.0, "float": True, "shadow": 0, "color": "#2C3A4F",
         "screen": profile(OTHER, highlightAt="@шапке"),
         "cam": [k(0, [0, 2.3, 10.8], [0, 2.25, 0], 30), k(1.1, [0.35, 2.32, 10.4], [0, 2.25, 0], 30),
                 k(2.1, [0, 2.53, 5.4], [0, 2.7, 0], 30, "inOut"), k(5, [0, 2.5, 5.1], [0, 2.5, 0], 30)]}},
                {"block": "StarRain", "at": "@лайк", "pos": "full",
                 "props": {"kind": "heart", "count": 22, "color": "#FF5C7A", "dur": 3.2}}]},
    scene("c39", "@Баронесса одобряет", "fade", zoom=(1.0, 1.05)),
]

sfx = [
    ("@ленте", "pk-pop-ui-menu", 0.4, True),
    ("@настоящей-0.1", "hit-soft", 0.6, True),
    ("@1918", "hit-sub", 0.55, True),
    ("@пыльник", "reveal-glow", 0.5, False),
    ("@молнии", "glitch-short", 0.35, True),
    ("@распродажу", "pop-high", 0.45, True),
    ("@оружие", "door-creak", 0.5, False),
    ("@стреляет", "strike", 0.55, True),
    ("@минуту", "tick-clock", 0.35, False),
    ("@скидки", "sparkle", 0.45, True),
    ("@КокоШанель", "hit-sub", 0.5, True),
    ("@сохранили", "pop-high", 0.4, True),
    ("@сдалось", "error-down", 0.45, True),
    ("@Эрмес", "rumble-distant", 0.55, False),
    ("@осады", "tick-clock", 0.4, False),
    ("@процентов", "whoosh-pan-lr", 0.45, True),
    ("@ожидания", "steps-debris", 0.35, False),
    ("@Эрмесовку", "shockwave-hit", 0.55, True),
    ("@пыльники", "thud", 0.5, True),
    ("@флаг", "whoosh-up", 0.45, True),
    ("@Биркин", "reveal-glow", 0.5, False),
    ("@сумка", "sparkle-rise", 0.5, False),
    ("@смолоду", "hit-soft", 0.5, True),
    ("@паспорт", "pk-pop-ui-menu", 0.4, True),
    ("@вышла", "suck-in", 0.45, True),
    ("@коллекцию", "sparkle", 0.4, True),
    ("@Если+0.1", "pk-shimmer-ui-dissolvre-sfx", 0.4, False),
    ("@лайк", "sparkle-rise", 0.35, False),
    ("@одобряет", "hit-soft", 0.5, True),
]

spec = {
    "id": PID, "mode": "explainer", "style": "dusk", "fps": 60,
    "voice": {"src": f"projects/{PID}/voice.wav", "words": f"projects/{PID}/words.json"},
    "music": {"src": f"projects/{PID}/music-bed.wav", "volume": 0.14, "duck": 0.5, "fadeOut": 0.5},
    "tail": 2.4,
    "autoSfx": False,
    "grain": 0.04, "vignette": 0.18,
    "captions": {"mode": "editorial", "pos": "top", "uppercase": True},
    "sfx": [{"at": a, "id": i, "volume": v, "alignPeak": ap} for a, i, v, ap in sfx],
    "scenes": scenes,
}

if __name__ == "__main__":
    d = RS / "engine" / "public" / "projects" / PID
    d.mkdir(parents=True, exist_ok=True)
    (d / "spec.json").write_text(json.dumps(spec, ensure_ascii=False, indent=1), encoding="utf-8")
    print(PID, "scenes", len(scenes), "sfx", len(sfx))
