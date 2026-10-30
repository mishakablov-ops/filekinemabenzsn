"""Storyboard for «Каждому по способности», season «Академия героев» (akademiya), episode 3: every scene is an animated
Blender clip (VideoBG, the camera moves inside the clip). Motion design by the prompt-motion rules (29.10.2026): hard
cuts on the words and the «ring» transition (the hero's radius) instead of dissolves, name cards for the cast
(NameCard), the mentor's rule as a card to save (RuleCard), no glows or particle bursts on top of the picture.
Music: the Классика bed (ambient-air, dark-cinematic rises from the laughter to the golem and goes down after it).

    python3 engine/storyboard.py [--out DIR]
writes <RS>/engine/public/projects/akademiya-3/spec.json (or DIR/akademiya-3/spec.json);
needs there voice.wav, words.json, music-bed.wav and clips/<shot>.mp4 (c00 … c22).
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RS = ROOT / "KINEMA" / "skills" / "reel-studio"
OUT = Path(sys.argv[sys.argv.index("--out") + 1]) if "--out" in sys.argv else RS / "engine" / "public" / "projects"
PID = "akademiya-3"


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


def shake(*at):
    return {"move": "still", "shakeAt": list(at)}


scenes = [
    # --- hook: zero on the board, and yet taken first (a flash-forward)
    scene("c00", 0, "cut", zoom=(1.0, 1.05)),
    scene("c00b", "@И меня", "cut"),
    # --- the letter, the Academy, director Saul
    scene("c01", "@После урагана", "ring"),
    scene("c02", "@Академию открыли", "push"),
    scene("c03", "@для тех", "zoom"),
    scene("c04", "@Директор", "cut", layers=[name("@Директор+0.1", "Сол", "директор · с ним не спорят")]),
    scene("c05", "@С ним", "whip"),
    # --- the exam: CJ and the bus, Cesar's lap, Denise stops time
    scene("c06", "@Экзамен", "ring"),
    scene("c07", "@Си-Джей", "whip", layers=[name("@Си-Джей+0.1", "Си-Джей", "сила десятерых")]),
    scene("c08", "@А это", "cut", camera=shake("@тонн"),
          layers=[{"block": "StatSlam", "at": "@тонн", "props": {"value": "12", "unit": "т", "label": "городской автобус"},
                   "pos": {"preset": "stage", "dy": 160}}]),
    scene("c09", "@Сезар", "whip", layers=[name("@Сезар+0.1", "Сезар", "быстрее звука")]),
    scene("c10", "@Дениз", "cut", layers=[name("@Дениз+0.1", "Дениз", "останавливает время")]),
    # --- «what will you show?» nothing; the zero; everyone laughs
    scene("c11", "@А меня", "push"),
    scene("c12", "@Я показал", "cut"),
    scene("c12b", "@На табло", "slam"),
    scene("c12c", "@Все смеялись", "cut"),
    # --- the golem: everyone runs, I walk towards it, it falls apart
    scene("c13", "@И тут", "cut", camera=shake("@контроля")),
    scene("c14", "@Он пошёл", "whip", camera=shake("@трибуны")),
    scene("c15", "@Я пошёл", "push"),
    scene("c16", "@И голем", "cut", camera=shake("@рассыпался")),
    # --- Emmet: the first hero, forty years without a student, «this one is mine», rule one
    scene("c17", "@На трибуне", "ring", layers=[name("@Эммет", "Эммет", "первый герой · скорость ветра", until="@Сорок-0.1")]),
    scene("c18", "@Сорок лет", "whip"),
    scene("c19", "@А тут", "cut"),
    scene("c19b", "@Почему", "cut"),
    scene("c19c", "@Правило", "cut", captions=False,
          layers=[{"block": "RuleCard", "at": "@Правило", "pos": {"x": 60, "y": 960, "w": 960, "h": 540},
                   "props": {"n": 1, "label": "Правило", "sub": "Эммет", "width": 960, "size": 56,
                             "text": "Сила сейчас есть у ==всех.== // Навстречу идут [единицы.]",
                             "lineAt": ["@Сила сейчас", "@Навстречу идут"]}}]),
    # --- the evening: the cough, the power burns him, next to me he rests; calm ending
    scene("c20", "@Вечером", "ring"),
    scene("c21", "@Моя сила", "cut"),
    scene("c21b", "@А рядом", "push"),
    scene("c22", "@Следующая", "cut", zoom=(1.0, 1.02)),
]

sfx = [
    ("@ноль", "hit-sub", 0.6, True),
    ("@первым", "reveal-glow", 0.45, False),
    ("@письмо", "paper-rustle", 0.5, False),
    ("@поднял", "whoosh-up", 0.5, True),
    ("@тонн", "thud", 0.7, True),
    ("@пробежал", "whoosh-pan-lr", 0.6, True),
    ("@остановила", "suck-in", 0.5, True),
    ("@ничего", "error-down", 0.4, True),
    ("@ноль#2", "hit-sub", 0.6, True),
    ("@голем", "rumble-distant", 0.6, False),
    ("@трибуны", "steps-debris", 0.5, True),
    ("@побежали", "whoosh-double", 0.4, True),
    ("@навстречу", "steps-concrete", 0.4, False),
    ("@рассыпался", "shockwave-hit", 0.85, True),
    ("@рассыпался+0.2", "steps-debris", 0.6, False),
    ("@рассыпался+0.4", "usr-crowd-gasp-mid-swell-172", 0.45, False),
    ("@встал", "reveal-glow", 0.4, False),
    ("@учеников", "whoosh-short", 0.5, True),
    ("@ко мне", "hit-soft", 0.5, True),
    ("@отдыхаю", "reveal-glow", 0.35, False),
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
