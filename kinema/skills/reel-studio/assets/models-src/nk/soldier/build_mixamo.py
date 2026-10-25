# blender -b --factory-startup --disable-autoexec --python build_mixamo.py -- <mixamo_dir> <soldier_textures_dir> <out_models_dir> <work_dir>
# Mixamo clips (made on our soldier) -> soldier_mx_rok.glb / soldier_mx_kpa.glb + soldier_mx_clips.json
#  * every clip on one armature (the skinned one from "Rifle Run.fbx")
#  * "pull_low": Pull Heavy Object with the pelvis 0.22 m lower and the torso leaning in; feet kept on their original spots by leg IK
#  * root motion: the horizontal travel of the hips is taken out of every clip and stored as a track (three.js metres),
#    so the engine moves the soldier exactly along it (no foot sliding, clean blends)
import json
import math
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix, Quaternion, Vector

mdir, texdir, outdir, work = [Path(p) for p in sys.argv[sys.argv.index("--") + 1:]]
work.mkdir(parents=True, exist_ok=True)
CLIPS = {  # file -> clip name, loops?
    "Rifle Run": ("rifle_run", True), "Run To Stop": ("run_to_stop", False), "Running To Turn": ("run_turn", False),
    "Firing Rifle": ("fire", True), "Rifle Aiming Idle": ("aim_idle", True), "Rifle Idle": ("rifle_idle", True),
    "Yelling": ("yell", True), "Prone Forward": ("crawl", True), "Pull Heavy Object": ("pull", True), "Kneeling": ("kneel", True),
}
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.fps = 30


def import_fbx(name):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=str(mdir / f"{name}.fbx"), automatic_bone_orientation=False)
    return [o for o in bpy.data.objects if o not in before]


objs = import_fbx("Rifle Run")
arm = next(o for o in objs if o.type == "ARMATURE")
arm.name = "soldier"
meshes = [o for o in objs if o.type == "MESH"]
arm.animation_data.action.name = "rifle_run"
for fname, (clip, _) in CLIPS.items():
    if fname == "Rifle Run":
        continue
    new = import_fbx(fname)
    a = next(o for o in new if o.type == "ARMATURE")
    act = a.animation_data.action
    act.name = clip
    act.use_fake_user = True
    for o in new:
        bpy.data.objects.remove(o, do_unlink=True)
for a in bpy.data.actions:
    a.use_fake_user = True
print("ACTIONS", sorted(a.name for a in bpy.data.actions))
PB = arm.pose.bones
HIPS = PB["mixamorig:Hips"]
for b in PB:
    b.rotation_mode = "QUATERNION"


def frames(act):
    s, e = (int(round(x)) for x in act.frame_range)
    return list(range(s, e + 1))


def use(act):
    arm.animation_data.action = act
    # Blender 4.4+/5.x slotted actions: pick the slot that animates this armature
    if hasattr(act, "slots") and len(act.slots) and hasattr(arm.animation_data, "action_slot"):
        arm.animation_data.action_slot = act.slots[0]


def key_pose(bones, f):
    for b in bones:
        b.keyframe_insert("location", frame=f)
        b.keyframe_insert("rotation_quaternion", frame=f)


# ------------------------------------------------------------------ pull_low: deeper crouch while dragging
pull = bpy.data.actions["pull"]
low = pull.copy()
low.name = "pull_low"
low.use_fake_user = True
use(low)
fr = frames(low)
feet = {}
for f in fr:
    sc.frame_set(f)
    feet[f] = {s: (arm.matrix_world @ PB[f"mixamorig:{s}Foot"].matrix).copy() for s in ("Left", "Right")}
tg = {}
for s in ("Left", "Right"):
    e = bpy.data.objects.new(f"{s}FootTarget", None)
    sc.collection.objects.link(e)
    tg[s] = e
    for f in fr:
        e.matrix_world = feet[f][s]
        e.keyframe_insert("location", frame=f)
        e.keyframe_insert("rotation_euler", frame=f)
DROP = 0.22  # metres
inv_arm = arm.matrix_world.inverted()
right_axis = None
for f in fr:
    sc.frame_set(f)
    # lower the pelvis (armature space; the armature is in centimetres at scale 0.01)
    m = HIPS.matrix.copy()
    m.translation = m.translation + (inv_arm.to_3x3() @ Vector((0, 0, -DROP)))
    HIPS.matrix = m
    bpy.context.view_layer.update()
    # lean the torso forward around the character's side axis
    for bn, deg in (("mixamorig:Spine", 16), ("mixamorig:Spine1", 9), ("mixamorig:Spine2", 5)):
        b = PB[bn]
        side = (arm.matrix_world.to_3x3() @ HIPS.matrix.to_3x3() @ Vector((1, 0, 0))).normalized()
        q = Quaternion(inv_arm.to_3x3() @ side, math.radians(deg))
        bm = b.matrix.copy()
        rot = (q.to_matrix().to_4x4() @ Matrix.Translation(-bm.translation)) if False else None
        new = q.to_matrix().to_4x4() @ bm.to_3x3().to_4x4()
        new.translation = bm.translation
        b.matrix = new
        bpy.context.view_layer.update()
    key_pose([HIPS, PB["mixamorig:Spine"], PB["mixamorig:Spine1"], PB["mixamorig:Spine2"]], f)
# legs: IK back onto the original foot spots, feet keep their original orientation
for s in ("Left", "Right"):
    ik = PB[f"mixamorig:{s}Leg"].constraints.new("IK")
    ik.target = tg[s]
    ik.chain_count = 2
    ik.use_tail = True
    cr = PB[f"mixamorig:{s}Foot"].constraints.new("COPY_ROTATION")
    cr.target = tg[s]
bpy.context.view_layer.objects.active = arm
arm.select_set(True)
bpy.ops.object.mode_set(mode="POSE")
bpy.ops.pose.select_all(action="SELECT")
bpy.ops.nla.bake(frame_start=fr[0], frame_end=fr[-1], only_selected=False, visual_keying=True, clear_constraints=True, use_current_action=True, bake_types={"POSE"})
bpy.ops.object.mode_set(mode="OBJECT")
for s in ("Left", "Right"):
    bpy.data.objects.remove(tg[s], do_unlink=True)
sc.frame_set(fr[0])
print("PULL_LOW hips z", round((arm.matrix_world @ HIPS.head).z, 3), "foot z", round((arm.matrix_world @ PB["mixamorig:LeftFoot"].head).z, 3))

# ------------------------------------------------------------------ root motion out of every clip
meta = {}
for act in list(bpy.data.actions):
    if act.name not in [c for c, _ in CLIPS.values()] + ["pull_low"]:
        continue
    use(act)
    fr = frames(act)
    track, heads = [], []
    for f in fr:
        sc.frame_set(f)
        w = arm.matrix_world @ HIPS.head
        heads.append(w.copy())
    x0, y0 = heads[0].x, heads[0].y
    # facing from the hips' forward axis (yaw change over the clip, e.g. the 180 turn)
    for f, w in zip(fr, heads):
        track.append([round(w.x - x0, 4), round(-(w.y - y0), 4)])  # three.js: x, z  (Blender -Y forward -> three +Z)
    yaws = []
    for f in fr:
        sc.frame_set(f)
        fwd = arm.matrix_world.to_3x3() @ HIPS.matrix.to_3x3() @ Vector((0, 0, 1))
        yaws.append(math.atan2(fwd.x, -fwd.y))
    # strip the horizontal travel: keep each frame's hips over the clip's start point (height and rotation untouched)
    for f, w in zip(fr, heads):
        sc.frame_set(f)
        target = Vector((x0, y0, w.z))
        m = HIPS.matrix.copy()
        m.translation = inv_arm @ target
        HIPS.matrix = m
        bpy.context.view_layer.update()
        HIPS.keyframe_insert("location", frame=f)
    loops = dict(CLIPS.values()).get(act.name, True)
    meta[act.name] = {"frames": len(fr), "fps": 30, "duration": (len(fr) - 1) / 30, "loop": loops, "track": track,
                      "yaw0": round(yaws[0], 4), "yaw1": round(yaws[-1], 4), "hipsY0": round(heads[0].z, 4)}
    print("ROOT", act.name, "travel", track[-1], "yaw change", round(math.degrees(yaws[-1] - yaws[0]), 1))
(outdir / "soldier_mx_clips.json").write_text(json.dumps(meta), encoding="utf-8")

# ------------------------------------------------------------------ lighter mesh
for o in meshes:
    if len(o.data.vertices) > 20000:
        bpy.context.view_layer.objects.active = o
        d = o.modifiers.new("lighter", "DECIMATE")
        d.ratio = 0.55
        while o.modifiers.find("lighter") > 0:
            bpy.ops.object.modifier_move_up(modifier="lighter")
        bpy.ops.object.modifier_apply(modifier="lighter")
print("TRIS", sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in meshes))


# ------------------------------------------------------------------ skins
def load(path, srgb=True):
    im = bpy.data.images.load(str(path), check_existing=True)
    if not srgb:
        im.colorspace_settings.name = "Non-Color"
    return im


src_base = Path(texdir) / "material_1_baseColor.png"
src_nrm = Path(texdir) / "material_1_normal.png"
src_mr = Path(texdir) / "material_1_metallicRoughness.png"
small = {}
for key, p, size, srgb in (("base", src_base, 4096, True), ("nrm", src_nrm, 2048, False), ("mr", src_mr, 2048, False)):
    im = load(p, srgb)
    if max(im.size) > size:
        im.scale(size, size)
    small[key] = im
# KPA: plain olive-khaki — divide out the camo blotches (large-scale luminance), keep folds/seams (small scale)
b = small["base"]
W, H = b.size
px = np.empty(W * H * 4, np.float32)
b.pixels.foreach_get(px)
px = px.reshape(H, W, 4)
lum = px[..., 0] * 0.299 + px[..., 1] * 0.587 + px[..., 2] * 0.114


def box_blur(a, r):
    c = np.cumsum(np.cumsum(np.pad(a, ((r + 1, r), (r + 1, r)), mode="edge"), 0), 1)
    return (c[2 * r + 1:, 2 * r + 1:] - c[:-2 * r - 1, 2 * r + 1:] - c[2 * r + 1:, :-2 * r - 1] + c[:-2 * r - 1, :-2 * r - 1]) / (2 * r + 1) ** 2


# woodland blotches are 80-160 px here, too big to divide out cleanly -> flat khaki cloth:
#  only the finest structure (seams, stitching, weave; radius 3 px) survives, capped so blotch edges cannot reappear;
#  folds and volume come from the normal map; a soft procedural mottling keeps it from looking printed
fine = np.clip(lum / np.maximum(box_blur(lum, 3), 1e-3), 0.9, 1.1)
rng = np.random.default_rng(7)
noise = box_blur(box_blur(rng.random((H, W)).astype(np.float32), 40), 40)
noise = 0.96 + (noise - noise.mean()) / max(float(noise.std()), 1e-6) * 0.025
khaki = np.array([0.42, 0.40, 0.27], np.float32)
kp = px.copy()
kp[..., :3] = np.clip(khaki[None, None, :] * (fine * noise)[..., None], 0, 1)
kpa = bpy.data.images.new("soldier_kpa_base", W, H, alpha=True)
kpa.pixels.foreach_set(kp.ravel())
kpa.filepath_raw = str(work / "soldier_kpa_base.png")
kpa.file_format = "PNG"
kpa.save()


def set_skin(base_img):
    for o in meshes:
        for slot in o.material_slots:
            mat = slot.material
            if not mat or not mat.use_nodes:
                continue
            nt = mat.node_tree
            bsdf = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None)
            if not bsdf or "material_1" not in mat.name and len(o.data.vertices) < 500:
                continue
            for inp, img, nonc in (("Base Color", base_img, False), ("Normal", small["nrm"], True)):
                tex = nt.nodes.new("ShaderNodeTexImage")
                tex.image = img
                if inp == "Normal":
                    nm = nt.nodes.new("ShaderNodeNormalMap")
                    nt.links.new(tex.outputs["Color"], nm.inputs["Color"])
                    nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
                else:
                    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
            bsdf.inputs["Roughness"].default_value = 0.8
            bsdf.inputs["Metallic"].default_value = 0.0


def export(path):
    use(bpy.data.actions["rifle_idle"])
    bpy.ops.object.select_all(action="DESELECT")
    arm.select_set(True)
    for o in meshes:
        o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(path), export_format="GLB", use_selection=True, export_animations=True,
                              export_animation_mode="ACTIONS", export_force_sampling=True, export_frame_range=False,
                              export_image_format="JPEG", export_jpeg_quality=88, export_yup=True, export_apply=False)
    print("EXPORTED", path)


set_skin(small["base"])
export(outdir / "soldier_mx_rok.glb")
set_skin(kpa)
export(outdir / "soldier_mx_kpa.glb")
