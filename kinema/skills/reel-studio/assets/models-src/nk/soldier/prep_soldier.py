# blender -b --factory-startup --disable-autoexec --python prep_soldier.py -- <scene.gltf> <out_dir> <work_dir>
# "Forest soldier (outdated)" by buh (CC-BY-4.0) -> soldier_rok.glb (original woodland camo) + soldier_kpa.glb (plain olive-khaki).
# Bones renamed to readable humanoid names, stray icosphere removed, ~45 % lighter mesh, textures 4K/2K JPEG.
# Character faces +Z in three.js (Blender -Y), feet on the ground, 1.86 m to the helmet top.
import sys
from pathlib import Path

import bpy
import numpy as np

src, out, work = sys.argv[sys.argv.index("--") + 1:]
out, work = Path(out), Path(work)
work.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
sc = bpy.context.scene
for o in list(sc.objects):
    if o.type == "MESH" and o.name.startswith("Icosphere"):
        bpy.data.objects.remove(o, do_unlink=True)
arm = [o for o in sc.objects if o.type == "ARMATURE"][0]
arm.name = arm.data.name = "soldier_rig"

NAMES = {"Bone": "Hips", "Bone.001": "Pelvis", "Bone.002": "Spine", "Bone.003": "Chest", "Bone.004": "Neck", "Bone.005": "Head",
         "Bone.007": "LeftUpLeg", "Bone.008": "LeftLeg", "Bone.009": "LeftFoot", "Bone.010": "RightUpLeg", "Bone.011": "RightLeg", "Bone.012": "RightFoot"}
for side, first in (("Left", 6), ("Right", 35)):
    NAMES[f"Bone.{first:03d}"] = f"{side}Shoulder"
    base = 13 if side == "Left" else 36
    NAMES[f"Bone.{base:03d}"] = f"{side}Arm"
    NAMES[f"Bone.{base + 1:03d}"] = f"{side}ForeArm"
    NAMES[f"Bone.{base + 2:03d}"] = f"{side}Hand"
    t0 = 16 if side == "Left" else 39
    for j in range(3):
        NAMES[f"Bone.{t0 + j:03d}"] = f"{side}HandThumb{j + 1}"
    f0 = 19 if side == "Left" else 42
    for k, finger in enumerate(["Index", "Middle", "Ring", "Pinky"]):
        for j in range(4):
            NAMES[f"Bone.{f0 + k + j * 4:03d}"] = f"{side}Hand{finger}{j}"
renamed = 0
for b in arm.data.bones:
    key = b.name.split("_")[0]
    if key in NAMES:
        new = NAMES[key]
    elif b.parent is None:
        new = "Root"
    else:
        continue
    for o in sc.objects:  # vertex groups follow bone names
        if o.type == "MESH" and b.name in o.vertex_groups:
            o.vertex_groups[b.name].name = new
    b.name = new
    renamed += 1
print("RENAMED", renamed, "of", len(arm.data.bones))

# lighter mesh (weights survive the decimate modifier)
for o in [o for o in sc.objects if o.type == "MESH"]:
    if len(o.data.vertices) > 20000:
        d = o.modifiers.new("lighter", "DECIMATE")
        d.ratio = 0.55
        bpy.context.view_layer.objects.active = o
        mods = [m for m in o.modifiers]
        # decimate must run before the armature deform
        while o.modifiers.find("lighter") > 0:
            bpy.ops.object.modifier_move_up(modifier="lighter")
        bpy.ops.object.modifier_apply(modifier="lighter")
tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in sc.objects if o.type == "MESH")
print("TRIS", tris)


def shrink(img, size):
    if max(img.size) > size:
        img.scale(size, size)


imgs = {i.name: i for i in bpy.data.images}
base = next(i for n, i in imgs.items() if "baseColor" in n and "material_1" in n)
shrink(base, 4096)
for n, i in imgs.items():
    if i is not base:
        shrink(i, 2048)
for i in bpy.data.images:
    if i.source == "FILE":
        i.pack()


def export(path):
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.export_scene.gltf(filepath=str(path), export_format="GLB", export_image_format="JPEG", export_jpeg_quality=88,
                              export_apply=False, export_yup=True, export_animations=False, export_skins=True)
    print("EXPORTED", path)


export(out / "soldier_rok.glb")

# KPA: woodland camo -> plain olive-khaki cotton, keeping folds, seams and wear from the luminance
px = np.empty(base.size[0] * base.size[1] * 4, np.float32)
base.pixels.foreach_get(px)
px = px.reshape(base.size[1], base.size[0], 4)
lum = px[..., 0] * 0.299 + px[..., 1] * 0.587 + px[..., 2] * 0.114
ref = float(np.median(lum[lum > 0.03]))
khaki = np.array([0.43, 0.42, 0.29], np.float32)
k = np.clip(lum / max(ref, 1e-3), 0.25, 2.2) ** 0.8
px[..., :3] = np.clip(khaki[None, None, :] * k[..., None], 0, 1)
kpa = bpy.data.images.new("soldier_kpa_basecolor", base.size[0], base.size[1], alpha=True)
kpa.pixels.foreach_set(px.ravel())
kpa.filepath_raw = str(work / "soldier_kpa_basecolor.png")
kpa.file_format = "PNG"
kpa.save()
for mat in bpy.data.materials:
    for node in (mat.node_tree.nodes if mat.use_nodes else []):
        if node.type == "TEX_IMAGE" and node.image is base:
            node.image = kpa
export(out / "soldier_kpa.glb")
