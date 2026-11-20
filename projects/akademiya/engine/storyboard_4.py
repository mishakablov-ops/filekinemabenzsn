"""Storyboard for «Каждому по способности», season «Академия героев» (akademiya), episode 4 «Пять утра»: every scene is an
animated Blender clip (VideoBG, set akad_e4, shots-4.json). Motion design by the prompt-motion rules (29.10.2026): hard cuts
on the words and the «ring» transition (the hero's radius) at the section starts, name cards for the cast (new viewers may
start here), rule two as a card to save (RuleCard), no glows or particle bursts on top of the picture.
Music: the Классика bed (ambient-air, dark-cinematic rises in the failure, goes down at the turn, rises again for the glove).

    python3 engine/storyboard_4.py [--out DIR]
writes <RS>/engine/public/projects/akademiya-4/spec.json (or DIR/akademiya-4/spec.json);
needs there voice.wav, words.json, music-bed.wav and clips/<shot>.mp4 (d00 … d20).
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RS = ROOT / "KINEMA" / "skills" / "reel-studio"
OUT = Path(sys.argv[sys.argv.index("--out") + 1]) if "--out" in sys.argv else RS / "engine" / "public" / "projects"
PID = "akademiya-4"


def clip(sid, zoom=(1.0, 1.03), **kw):
    return {"block": "VideoBG", "props": {"src": f"projects/{PID}/clips/{sid}.mp4", "zoom": list(zoom), **kw}}


def scene(sid, at, transition="cut", camera="still", zoom=(1.0, 1.03), layers=None, **kw):
    s = {"id": sid, "at": at, "transition": transition, "camera": camera, "bg": clip(sid, zoom)}
    if layers:
        s["layers"] = layers
    s.update(kw)
    return s


def name(at, who, role, until=None):
    d = {"block": "NameCard", "at": at, "pos": "stageLow", "props": {"name": who, "role": role}}
    if until:
        d["until"] = until
    return d


def stat(at, value, unit, label):
    return {"block": "StatSlam", "at": at, "props": {"value": value, "unit": unit, "label": label},
            "pos": {"preset": "stage", "dy": 160}}


def shake(*at):
    return {"move": "still", "shakeAt": list(at)}


scenes = [
    # --- hook: a month in the Academy of heroes, and I hauled garbage; that was the first lesson
    scene("d00", 0, "cut", zoom=(1.0, 1.05)),
    scene("d00b", "@И это", "cut"),
    # --- the beach: thirty years of scrap, the circle is six metres, Emmet's order
    scene("d01", "@Пять утра", "ring"),
    scene("d02", "@30", "push", layers=[stat("@30", "30", "лет", "сюда свозили железо")]),
    scene("d03", "@Холодильники", "whip"),
    scene("d04", "@Мой круг", "ring", layers=[stat("@6", "6", "м", "мой круг сейчас")]),
    scene("d05", "@Эммет сказал", "cut", layers=[name("@Эммет сказал+0.1", "Эммет", "наставник · скорость ветра")]),
    scene("d05b", "@И сожми", "push"),
    # --- the failure: the fridge does not move, CJ laughs, the circle just goes out, asleep on the sand
    scene("d06", "@Первую", "cut", camera=shake("@холодильник")),
    scene("d07", "@Си-Джей бегал", "whip", layers=[name("@Си-Джей бегал+0.1", "Си-Джей", "сила десятерых")]),
    scene("d07b", "@Ноль", "slam"),
    scene("d08", "@Круг не", "cut"),
    scene("d09", "@На 10", "push"),
    # --- the turn: Emmet says nothing and takes the scrap too; a month later the beach is empty, the circle is a palm
    scene("d10", "@Эммет ничего", "ring"),
    scene("d11", "@Он встал", "cut", camera=shake("@железо#2")),
    scene("d12", "@Каждый день", "whip"),
    scene("d13", "@Через месяц", "push"),
    scene("d14", "@А круг", "cut"),
    # --- warmth: Denise stops time for ten more seconds of sleep; Emmet started alone forty years ago
    scene("d15", "@Дениз", "ring", layers=[name("@Дениз+0.1", "Дениз", "останавливает время")]),
    scene("d16", "@Останавливала", "cut"),
    scene("d17", "@Эммет сказал#2", "push"),
    # --- rule two, a card to save
    scene("d18", "@Правило", "cut", captions=False,
          layers=[{"block": "RuleCard", "at": "@Правило", "pos": {"x": 60, "y": 960, "w": 960, "h": 540},
                   "props": {"n": 2, "label": "Правило", "sub": "Эммет", "width": 960, "size": 60,
                             "text": "Повторение // сильнее ==таланта.==",
                             "lineAt": ["@Повторение", "@сильнее"]}}]),
    # --- cliffhanger: CJ throws the glove, tomorrow a training fight; calm ending
    scene("d19", "@Вечером", "ring"),
    scene("d19b", "@Завтра", "whip"),
    scene("d20", "@Следующая", "cut", zoom=(1.0, 1.02)),
]

sfx = [
    ("@мусор", "hit-sub", 0.55, True),
    ("@урок", "hit-soft", 0.45, True),
    ("@железо", "hit-metal", 0.45, True),
    ("@рельсы", "thud", 0.5, True),
    ("@круг", "reveal-glow", 0.4, False),
    ("@6", "stamp", 0.5, True),
    ("@Расчисти", "whoosh-short", 0.4, True),
    ("@холодильник", "error-thud", 0.5, True),
    ("@бегал", "whoosh-pan-lr", 0.5, True),
    ("@Ноль", "hit-sub", 0.5, True),
    ("@гас", "power-off", 0.5, True),
    ("@уснул", "downlifter-short", 0.35, False),
    ("@взял", "hit-metal", 0.4, True),
    ("@Каждый", "tick-clock", 0.35, False),
    ("@пустой", "reveal-glow", 0.4, False),
    ("@сжался", "suck-in", 0.5, True),
    ("@Останавливала", "whoosh-reverse", 0.45, True),
    ("@Правило", "card-slide", 0.4, True),
    ("@кинул", "whoosh-short", 0.45, True),
    ("@перчатку", "thud", 0.45, True),
    ("@бой", "hit-cinematic", 0.55, True),
]

spec = {
    "id": PID, "mode": "explainer", "style": "dusk", "fps": 60,
    "voice": {"src": f"projects/{PID}/voice.wav", "words": f"projects/{PID}/words.json"},
    "music": {"src": f"projects/{PID}/music-bed.wav", "volume": 0.14, "duck": 0.5, "fadeOut": 0.5},
    "tail": 2.6,
    "autoSfx": False,
    "grain": 0.02, "vignette": 0.12,
    "captions": {"mode": "editorial", "pos": "top", "uppercase": True},
    "sfx": [{"at": a, "id": i, "volume": v, "alignPeak": ap} for a, i, v, ap in sfx],
    "scenes": scenes,
}

if __name__ == "__main__":
    d = OUT / PID
    d.mkdir(parents=True, exist_ok=True)
    (d / "spec.json").write_text(json.dumps(spec, ensure_ascii=False, indent=1), encoding="utf-8")
    print(PID, "scenes", len(spec["scenes"]), "sfx", len(spec["sfx"]))
