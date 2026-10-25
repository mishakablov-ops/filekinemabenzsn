"""Import 3D models (BlenderKit downloads, any .blend/.fbx/.obj/.glb) into the engine.

    python import_models.py                      # scan ~/blenderkit_data/models (BlenderKit add-on download folder)
    python import_models.py D:/models/macbook    # scan any folder
    python import_models.py file.blend --name macbook

For each model writes engine/public/models/<name>.glb + <name>.json with mesh names, sizes and a guessed
`screenMesh` (the display surface for a LIVE HTML screen in Model3D). Uses Blender headless.
Then in spec.json:  { "block": "Model3D", "props": { "src": "models/<name>.glb", "screenMesh": "<guess>", "screen": {…} } }
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:
        pass

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "engine" / "public" / "models"
CANDIDATES = [
    r"C:\Program Files (x86)\Steam\steamapps\common\Blender\blender.exe",
    *sorted((str(p) for p in Path(r"C:\Program Files\Blender Foundation").glob("*/blender.exe")), reverse=True),
]
SCREEN_HINTS = re.compile(r"screen|display|lcd|monitor|panel|экран|glass_front|retina", re.I)


def blender() -> str:
    exe = shutil.which("blender")
    if exe:
        return exe
    for c in CANDIDATES:
        if Path(c).exists():
            return c
    raise SystemExit("Blender not found — install it or put blender.exe on PATH")


CONVERT = r'''
import bpy, sys, json
argv = sys.argv[sys.argv.index("--") + 1:]
src, out = argv[0], argv[1]
ext = src.lower().rsplit(".", 1)[-1]
if ext != "blend":
    bpy.ops.wm.read_factory_settings(use_empty=True)
    if ext == "fbx": bpy.ops.import_scene.fbx(filepath=src)
    elif ext == "obj": bpy.ops.wm.obj_import(filepath=src)
    elif ext in ("glb", "gltf"): bpy.ops.import_scene.gltf(filepath=src)
    elif ext == "usdz" or ext == "usd": bpy.ops.wm.usd_import(filepath=src)
# drop cameras/lights that come with asset scenes
for o in list(bpy.data.objects):
    if o.type in ("CAMERA", "LIGHT"):
        bpy.data.objects.remove(o, do_unlink=True)
meshes = []
mats_info = {}
for o in bpy.data.objects:
    if o.type == "MESH":
        me = o.data
        mats = [m.name for m in me.materials if m]
        meshes.append({"name": o.name, "polys": len(me.polygons), "dims": [round(v, 4) for v in o.dimensions], "materials": mats})
        for p in me.polygons:
            if not me.materials or p.material_index >= len(me.materials) or not me.materials[p.material_index]:
                continue
            mn = me.materials[p.material_index].name
            d = mats_info.setdefault(mn, {"area": 0.0, "polys": 0, "lo": [1e9] * 3, "hi": [-1e9] * 3})
            d["area"] += p.area
            d["polys"] += 1
            for vi in p.vertices:
                co = o.matrix_world @ me.vertices[vi].co
                for k in range(3):
                    d["lo"][k] = min(d["lo"][k], co[k]); d["hi"][k] = max(d["hi"][k], co[k])
for mn, d in mats_info.items():
    d["size"] = [round(d["hi"][k] - d["lo"][k], 4) for k in range(3)]
    d["area"] = round(d["area"], 6)
    del d["lo"], d["hi"]
bpy.ops.export_scene.gltf(filepath=out, export_format="GLB", export_apply=True, export_yup=True, export_animations=True)
print("@@JSON" + json.dumps({"meshes": meshes, "materials": mats_info}))
'''


def guess_screen_material(mats: dict) -> str | None:
    best = None
    for name, d in mats.items():
        s = sorted(d["size"])
        flat = s[0] <= 0.02 * max(s[2], 1e-6)
        if SCREEN_HINTS.search(name) and flat and s[1] > 0:
            score = d["area"]
            if not best or score > best[0]:
                best = (score, name)
    return best[1] if best else None


def guess_screen(meshes: list[dict]) -> str | None:
    scored = []
    for m in meshes:
        name = m["name"] + " " + " ".join(m.get("materials", []))
        d = sorted(m["dims"])
        flat = d[0] < 0.08 * max(d[1], 1e-6) if d[1] > 0 else False
        score = (3 if SCREEN_HINTS.search(name) else 0) + (1 if flat else 0) + (0.5 if m["polys"] < 400 else 0)
        if score >= 1.5:
            scored.append((score, d[1] * d[2], m["name"]))
    scored.sort(reverse=True)
    return scored[0][2] if scored else None


def convert(src: Path, name: str, exe: str) -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / f"{name}.glb"
    script = OUT / "_convert.py"
    script.write_text(CONVERT, encoding="utf-8")
    # --disable-autoexec: never run Python embedded in downloaded .blend files
    cmd = [exe, "-b", "--disable-autoexec"] + ([str(src)] if src.suffix.lower() == ".blend" else []) + ["--python", str(script), "--", str(src), str(out)]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900)
    script.unlink(missing_ok=True)
    m = re.search(r"@@JSON(.*)", r.stdout)
    if not out.exists() or not m:
        raise RuntimeError(f"conversion failed for {src}:\n{(r.stdout + r.stderr)[-1500:]}")
    data = json.loads(m.group(1))
    meshes, mats = data["meshes"], data["materials"]
    info = {"src": str(src), "glb": f"models/{name}.glb", "screenMaterial": guess_screen_material(mats), "screenMesh": guess_screen(meshes),
            "materials": mats, "meshes": sorted(meshes, key=lambda x: -x["polys"])[:60], "sizeMB": round(out.stat().st_size / 1e6, 2)}
    (OUT / f"{name}.json").write_text(json.dumps(info, ensure_ascii=False, indent=1), encoding="utf-8")
    return info


def slug(p: Path) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", p.stem.lower()).strip("-")
    return s[:40] or "model"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path", nargs="?", default=str(Path.home() / "blenderkit_data" / "models"))
    ap.add_argument("--name")
    a = ap.parse_args()
    p = Path(a.path)
    exe = blender()
    files = [p] if p.is_file() else [f for f in p.rglob("*") if f.suffix.lower() in (".blend", ".fbx", ".obj", ".glb", ".gltf", ".usdz") and not f.name.endswith(".blend1")]
    if not files:
        raise SystemExit(f"no models found in {p}. Download them with the BlenderKit add-on (or put files there) and run again.")
    for f in files:
        name = a.name if a.name and len(files) == 1 else slug(f)
        try:
            info = convert(f, name, exe)
            print(f"✓ {f.name} -> {info['glb']} ({info['sizeMB']} MB) · screenMaterial: {info['screenMaterial']} · screenMesh: {info['screenMesh']}")
        except Exception as e:
            print(f"✗ {f.name}: {e}")


if __name__ == "__main__":
    main()
