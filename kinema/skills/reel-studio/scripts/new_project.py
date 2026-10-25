"""Create a project skeleton in engine/public/projects/<id>/.

    python new_project.py <id> [--style dusk] [--mode explainer|promo] [--music pulse-tech] [--force]

explainer: script.md (voiceover) + spec.json wired to voice.wav/words.json + music bed
promo:     script.md (on-screen words only, no voice) + spec.json wired to a beat grid
"""
from __future__ import annotations

import sys

import argparse
import json
from pathlib import Path

# console: always UTF-8 (Windows defaults to cp1251)
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent.parent
PROJ = ROOT / "engine" / "public" / "projects"

EXPLAINER_SCRIPT = """# Одна строка = одна карточка субтитров. `подводка // ударная часть`.
# Разметка: *курсив-акцент* [цвет] ==плашка== ~~зачёркнуто~~ {11|одиннадцать} <0.4>=пауза
# Режим карточки в начале строки: %slam %stack %sub %karaoke, позиция %top %middle %lower
# Формула: хук (≤2.5 с) → что это → как работает (3–5 битов с числами) → поворот → цена/доказательство → CTA

Бесит какое-то *приложение?*
Теперь можно собрать // своё ==такое же==
"""

PROMO_SCRIPT = """# Промо под музыку: короткие карточки, без голоса. Каждая строка встаёт на бит.
%slam [Ноль] кода
%slam ==Один== промпт
%slam Готовый *ролик*
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("id")
    ap.add_argument("--style", default="dusk")
    ap.add_argument("--mode", default="explainer", choices=["explainer", "promo"])
    ap.add_argument("--music", default=None)
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    d = PROJ / a.id
    if d.exists() and not a.force:
        raise SystemExit(f"{d} exists (use --force to overwrite the skeleton files)")
    d.mkdir(parents=True, exist_ok=True)
    base = f"projects/{a.id}"
    if a.mode == "explainer":
        (d / "script.md").write_text(EXPLAINER_SCRIPT, encoding="utf-8")
        music = a.music or "pulse-tech"
        spec = {
            "id": a.id, "mode": "explainer", "style": a.style, "fps": 60,
            "voice": {"src": f"{base}/voice.wav", "words": f"{base}/words.json"},
            "music": {"src": f"music/{music}.m4a", "volume": 0.14, "duck": 0.45},
            "scenes": [{"at": 0, "camera": "push", "layers": []}],
        }
    else:
        music = a.music or "drive-promo"
        (d / "script.md").write_text(PROMO_SCRIPT, encoding="utf-8")
        spec = {
            "id": a.id, "mode": "promo", "style": a.style if a.style != "dusk" else "blaze", "fps": 60,
            "words": f"{base}/words.json",
            "music": {"src": f"music/{music}.m4a", "volume": 0.9, "duck": 1, "beats": f"music/{music}.beats.json"},
            "captions": {"mode": "slam"},
            "scenes": [{"at": 0, "camera": "punch", "layers": []}],
        }
    (d / "spec.json").write_text(json.dumps(spec, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"created {d}\n  next: edit script.md -> python scripts/script_lint.py {d} -> python scripts/tts.py {d}"
          + (" --engine silent --beats engine/public/music/" + music + ".beats.json" if a.mode == "promo" else ""))


if __name__ == "__main__":
    main()
