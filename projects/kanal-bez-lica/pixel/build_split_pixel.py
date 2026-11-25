"""Нижняя половина сплит-экрана k5s в нашем пиксельном стиле (PIXCINE), mike 26.11: «по поводу пикселя, сделай прям наш
стиль туда… не просто пиксели вместо хорошего качества».

    python build_split_pixel.py [SHOTS_JSON]        (PIXCINE: env PIXCINE, по умолчанию kinema/pixcine или ../algorithm…)

То же действие, что в 3D-половине (blender/sets/kanal.py, v_split): герой `geroy` стоит в комнате у окна, машет правой
рукой, с 42 % до 66 % плана делает оборот на месте (кукла меняет ракурсы F → Q → S → B), потом снова машет. Кадр
1080×960, 30 к/с, длина = k5s из shots.json; без субтитров и плашек (их ставит KINEMA). Рендер:
    cd $PIXCINE/engine && node tools/stills.mjs --project kanal --ep split --seconds 0.8,2.6,4.6 --scale 0.5
    cd $PIXCINE/engine && node tools/render.mjs --project kanal --ep split   ->  $PIXCINE/projects/kanal/out/split.mp4
(в облаке: PIX_CHROME=<chrome-headless-shell> PIX_GL=swangle). render_clips.py кладёт его под 3D-половину.
"""
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PIX = Path(os.environ.get("PIXCINE") or next(
    (p for p in (HERE.parents[2] / "kinema" / "pixcine", Path("/home/user/algorithm-for-aipollon/pixcine")) if p.exists()),
    HERE.parents[2] / "kinema" / "pixcine"))
sys.path.insert(0, str(PIX / "scripts"))
from sb import Ep  # noqa: E402

shots = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE.parent / "blender" / "shots.json"
dur = next(s for s in json.loads(shots.read_text(encoding="utf-8"))["shots"] if s["id"] == "k5s")["dur"]
t_sp0, t_sp1 = dur * 0.42, dur * 0.66                   # как в v_split: оборот между 42 и 66 % плана

# комната «Тестостерона» (tt_room: окно с утренним светом, стол с монитором, кровать, полки) с потолком — без него над
# стенами в кадре чёрная полоса — и с реже пылью в луче (в тёмной комнате 120 пылинок читались как снег)
loc = json.loads((PIX / "engine" / "public" / "locations" / "tt_room.json").read_text(encoding="utf-8"))
loc["id"] = "kanal_room"
for pr in loc["props"]:
    if pr.get("t") == "room":
        pr["ceiling"] = True
for pa in loc.get("particles", []):
    pa["n"] = 40
# 26.11: над 3D-половиной светлая дневная комната — пиксельную делаем светлее (стены, рассеянный свет, лампа), но в нашей
# гамме: тёмно-синие обои и луч из окна остаются
for pr in loc["props"]:
    if pr.get("t") == "room":
        pr.setdefault("wallOpts", {})["color"] = "#46506a"
hemi = loc.get("hemi") or ["#c8c0b8", "#3a2a20", 0.6]
loc["hemi"] = [hemi[0], "#5a4636", round(hemi[2] * 1.6, 2)]
for li in loc.get("lights", []):
    if li.get("type") == "point":
        li["i"] = round(li["i"] * 1.6, 2)
(PIX / "engine" / "public" / "locations" / "kanal_room.json").write_text(json.dumps(loc, ensure_ascii=False), encoding="utf-8")

ep = Ep("kanal", "split", fps=30, w=1080, h=960)
s = ep.shot("kanal_room", round(dur, 3))
X, Z = -0.3, -0.5                                       # левее окна: окно и стол с монитором видны справа от героя
h = s.actor("hero", "geroy", at=(X, Z), face=0)
h.act(0, "wave")
h.expr(0, "normal", "smile")
h.act(round(t_sp0 - 0.12, 3), "idle", blend=0.15)
for k in range(4):                                      # 0 → 360°: четверть оборота каждые (t_sp1 - t_sp0) / 4
    h.face(round(t_sp0 + (t_sp1 - t_sp0) * k / 4, 3), 90 * (k + 1), d=round((t_sp1 - t_sp0) / 4, 3))
h.act(round(t_sp1 + 0.05, 3), "wave", blend=0.15)
# камера как у 3D-половины: спереди, герой во весь рост в нижних ~60 % кадра, сверху окно и стена; медленный наезд
s.cam([{"t": 0, "pos": [X + 0.25, 1.38, Z + 2.75], "look": [X + 0.35, 1.3, Z], "fov": 55},
       {"t": round(dur, 3), "pos": [X + 0.22, 1.36, Z + 2.55], "look": [X + 0.33, 1.3, Z], "fov": 55, "e": "inOut"}],
      focus="hero", aperture=3)
ep.save()
