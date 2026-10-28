"""Rig the generated hero (mesh/hero_a.glb from gen_hero.py) for the scenes of «Каждому по способности».
Same approach as KINEMA assets/models-src/podezd/chars/rig_chars.py, tuned for chibi proportions (head = 40 % of the
height): joints found from slices of the mesh, Blender bone heat, bleeding removed by region masks, then smoothed.

    blender -b --factory-startup --python rig_hero.py -- mesh/hero_a.glb hero_rig.blend [test.png]
    (or the bpy module: python rig_hero.py -- ...)

Output: one .blend with the armature 'HeroRig' (Mixamo-like bone names, root at the feet, facing -Y, 1.55 m) and the
skinned mesh 'Hero' (textures packed: diffuse 2048, normal and roughness 1024). Scenes load it with sila_hero.load().
"""
import math
import sys

import bpy
import numpy as np
from mathutils import Vector

args = sys.argv[sys.argv.index("--") + 1:]
SRC, DST = args[0], args[1]
TEST = args[2] if len(args) > 2 else None
H = 1.55                       # hero height, m (people2 adults are 1.75 m, the big head makes him read as a toy figure)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)
meshes = [o for o in bpy.data.objects if o.type == "MESH"]
for o in bpy.data.objects:
    o.select_set(o in meshes)
bpy.context.view_layer.objects.active = meshes[0]
for o in meshes:
    mw = o.matrix_world.copy()
    o.parent = None
    o.matrix_world = mw
if len(meshes) > 1:
    bpy.ops.object.join()
body = bpy.context.view_layer.objects.active
body.name = "Hero"
body.data.name = "HeroMesh"
for o in [o for o in bpy.data.objects if o.type == "EMPTY"]:
    bpy.data.objects.remove(o)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.mesh.remove_doubles(threshold=0.0004)
bpy.ops.object.mode_set(mode="OBJECT")

me = body.data
V = np.array([v.co[:] for v in me.vertices], np.float64)
lo, hi = V.min(0), V.max(0)
s = H / (hi[2] - lo[2])
V = (V - np.array([(lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, lo[2]])) * s
me.vertices.foreach_set("co", V.astype(np.float32).ravel())
me.update()
print("NORMALISED verts", len(V), "scale", round(s, 4))


def slab(z, tol=0.004):
    return V[np.abs(V[:, 2] - z) < tol * H]


mid = lambda a: float((a.min() + a.max()) / 2)

# ---------------------------------------------------------------- joints (fractions measured on hero_a: arms at 0.45-0.56 H,
# hands from |x| = 0.34 H, neck 0.585 H, legs below the hoodie hem at 0.30 H)
ARM_Z0, ARM_Z1 = 0.42 * H, 0.585 * H
TIP = float(np.abs(V[:, 0]).max())
SH_X = 0.11 * H
WR_X = TIP - 0.072 * H
EL_X = SH_X + 0.52 * (WR_X - SH_X)


def arm_at(x, sign):
    q = V[(np.abs(V[:, 0] * sign - x) < 0.006 * H) & (V[:, 2] > ARM_Z0) & (V[:, 2] < ARM_Z1)]
    return (mid(q[:, 1]), mid(q[:, 2])) if len(q) > 3 else (0.0, 0.5 * H)


def leg_at(z, sign):
    q = slab(z)
    q = q[(q[:, 0] * sign > 0.004 * H) & (np.abs(q[:, 0]) < 0.2 * H)]
    return (sign * mid(np.abs(q[:, 0])), mid(q[:, 1])) if len(q) > 3 else (sign * 0.067 * H, 0.05 * H)


def torso_y(z):
    q = slab(z)
    q = q[np.abs(q[:, 0]) < 0.08 * H]
    return mid(q[:, 1]) if len(q) else 0.0


J = {}
for sign, nm in ((1, "Left"), (-1, "Right")):
    ys, zs = arm_at(SH_X + 0.04 * H, sign)
    ye, ze = arm_at(EL_X, sign)
    yw, zw = arm_at(WR_X, sign)
    yt, zt = arm_at(TIP - 0.012 * H, sign)
    J[nm + "Shoulder"] = Vector((sign * 0.03 * H, ys + 0.005 * H, zs + 0.012 * H))
    J[nm + "Arm"] = Vector((sign * SH_X, ys, zs))
    J[nm + "ForeArm"] = Vector((sign * EL_X, ye + 0.004 * H, ze))
    J[nm + "Hand"] = Vector((sign * WR_X, yw, zw))
    J[nm + "HandEnd"] = Vector((sign * (TIP - 0.008 * H), yt, zt))
    xh, yh = leg_at(0.24 * H, sign)
    xk, yk = leg_at(0.16 * H, sign)
    xa, ya = leg_at(0.085 * H, sign)
    J[nm + "UpLeg"] = Vector((sign * 0.064 * H, yh, 0.30 * H))
    J[nm + "Leg"] = Vector((xk, yk - 0.006 * H, 0.165 * H))
    ankle = Vector((xa, ya + 0.004 * H, 0.055 * H))
    foot = V[(V[:, 2] < 0.04 * H) & (V[:, 0] * sign > 0)]
    toe = foot[np.argmin(foot[:, 1])]
    J[nm + "Foot"] = ankle
    J[nm + "ToeBase"] = Vector((ankle.x * 0.6 + toe[0] * 0.4, ankle.y + (toe[1] - ankle.y) * 0.62, 0.025 * H))
    J[nm + "ToeEnd"] = Vector((ankle.x * 0.6 + toe[0] * 0.4, toe[1], 0.022 * H))
for nm, f in (("Hips", 0.30), ("Spine", 0.36), ("Spine1", 0.42), ("Spine2", 0.48), ("Neck", 0.565), ("Head", 0.605)):
    J[nm] = Vector((0, torso_y(min(f, 0.55) * H) + (0.012 * H if nm.startswith("Spine") else 0.0), f * H))
J["HeadEnd"] = Vector((0, J["Head"].y, H))
print("JOINTS", {k: tuple(round(c, 3) for c in v) for k, v in J.items()})

# ---------------------------------------------------------------- armature
arm_data = bpy.data.armatures.new("HeroRig")
rig = bpy.data.objects.new("HeroRig", arm_data)
bpy.context.scene.collection.objects.link(rig)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode="EDIT")
eb = arm_data.edit_bones
CHAIN = [("Hips", "Hips", "Spine", None), ("Spine", "Spine", "Spine1", "Hips"), ("Spine1", "Spine1", "Spine2", "Spine"),
         ("Spine2", "Spine2", "Neck", "Spine1"), ("Neck", "Neck", "Head", "Spine2"), ("Head", "Head", "HeadEnd", "Neck")]
for sd in ("Left", "Right"):
    CHAIN += [(sd + "Shoulder", sd + "Shoulder", sd + "Arm", "Spine2"), (sd + "Arm", sd + "Arm", sd + "ForeArm", sd + "Shoulder"),
              (sd + "ForeArm", sd + "ForeArm", sd + "Hand", sd + "Arm"), (sd + "Hand", sd + "Hand", sd + "HandEnd", sd + "ForeArm"),
              (sd + "UpLeg", sd + "UpLeg", sd + "Leg", "Hips"), (sd + "Leg", sd + "Leg", sd + "Foot", sd + "UpLeg"),
              (sd + "Foot", sd + "Foot", sd + "ToeBase", sd + "Leg"), (sd + "ToeBase", sd + "ToeBase", sd + "ToeEnd", sd + "Foot")]
for name, h, t, parent in CHAIN:
    b = eb.new(name)
    b.head, b.tail = J[h], J[t]
    if parent:
        b.parent = eb[parent]
        b.use_connect = (eb[parent].tail - b.head).length < 1e-4
    b.align_roll(Vector((0, 0, 1)) if ("Foot" in name or "Toe" in name) else Vector((0, -1, 0)))
bpy.ops.object.mode_set(mode="OBJECT")

# ---------------------------------------------------------------- weights: bone heat, then masks and smoothing
bpy.ops.object.select_all(action="DESELECT")
body.select_set(True)
rig.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.parent_set(type="ARMATURE_AUTO")
names = [b.name for b in arm_data.bones]
B = {n: i for i, n in enumerate(names)}
gi = {g.index: g.name for g in body.vertex_groups}
W = np.zeros((len(V), len(names)))
for v in me.vertices:
    for g in v.groups:
        n = gi[g.group]
        if n in B:
            W[v.index, B[n]] = g.weight
missed = int((W.sum(1) < 1e-4).sum())
bones = {b.name: (np.array(b.head_local), np.array(b.tail_local)) for b in arm_data.bones}


def seg_dist(P, a, b):
    ab = b - a
    t = np.clip(((P - a) @ ab) / max(ab @ ab, 1e-9), 0, 1)
    return np.linalg.norm(P - (a + t[:, None] * ab), axis=1)


D = np.stack([seg_dist(V, *bones[n]) for n in names], 1)
X, Z = V[:, 0], V[:, 2]
is_arm = {1: (X > 0.15 * H) & (Z > ARM_Z0) & (Z < ARM_Z1), -1: (X < -0.15 * H) & (Z > ARM_Z0) & (Z < ARM_Z1)}
arms = is_arm[1] | is_arm[-1]
allow = np.ones_like(W, bool)
LEGB = ("UpLeg", "Leg", "Foot", "ToeBase")
for sign, sd in ((1, "Left"), (-1, "Right")):
    other = "Right" if sd == "Left" else "Left"
    chain = [sd + k for k in ("Shoulder", "Arm", "ForeArm", "Hand")]
    am = is_arm[sign]
    for n in names:
        if n not in chain and n != "Spine2":
            allow[am, B[n]] = False
    allow[am & (np.abs(X) > 0.2 * H), B["Spine2"]] = False
    allow[~am, B[sd + "ForeArm"]] = False
    allow[~am, B[sd + "Hand"]] = False
    allow[~am & ((Z < ARM_Z0 - 0.03 * H) | (X * sign < 0.06 * H)), B[sd + "Arm"]] = False
    allow[~am & (X * sign < 0.0), B[sd + "Shoulder"]] = False
    allow[np.ix_(np.nonzero(X * sign > 0.012 * H)[0], [B[other + k] for k in LEGB])] = False   # trousers: own leg only
head = (Z > 0.625 * H) & ~arms
allow[head, :] = False
allow[head, B["Head"]] = True                                               # the big head is rigid
legs_only = Z < 0.26 * H
for n in names:
    if not any(k in n for k in LEGB):
        allow[legs_only, B[n]] = False
for n in LEGB:
    for sd in ("Left", "Right"):
        allow[Z > 0.37 * H, B[sd + n]] = False
for sd in ("Left", "Right"):
    allow[Z > 0.12 * H, B[sd + "ToeBase"]] = False
    allow[Z > 0.2 * H, B[sd + "Foot"]] = False
near_ok = D <= D.min(1, keepdims=True) * 2.0 + 0.03 * H
allow &= near_ok | (W > 0.5) | head[:, None]
W = np.where(allow, W, 0)
empty = W.sum(1) < 1e-4
Dm = np.where(allow, D, 1e9)
W[empty, Dm[empty].argmin(1)] = 1.0
E = np.array([e.vertices[:] for e in me.edges])
for it in range(4):
    acc = np.zeros_like(W)
    cnt = np.zeros(len(V))
    np.add.at(acc, E[:, 0], W[E[:, 1]])
    np.add.at(acc, E[:, 1], W[E[:, 0]])
    np.add.at(cnt, E[:, 0], 1)
    np.add.at(cnt, E[:, 1], 1)
    W = 0.5 * W + 0.5 * acc / np.maximum(cnt, 1)[:, None]
    W = np.where(allow, W, 0)
    W /= np.maximum(W.sum(1, keepdims=True), 1e-9)
idx = np.argsort(-W, 1)[:, 4:]
np.put_along_axis(W, idx, 0, 1)
W /= np.maximum(W.sum(1, keepdims=True), 1e-9)
for g in list(body.vertex_groups):
    body.vertex_groups.remove(g)
for i, n in enumerate(names):
    g = body.vertex_groups.new(name=n)
    for vi in np.nonzero(W[:, i] > 0.002)[0]:
        g.add([int(vi)], float(W[vi, i]), "REPLACE")
print("WEIGHTS heat-missed", missed, "of", len(V), "arm verts", int(is_arm[1].sum()), int(is_arm[-1].sum()))

# ---------------------------------------------------------------- material: matte, no metal; smaller maps
for mat in body.data.materials:
    if not mat or not mat.use_nodes:
        continue
    mat.name = "HeroSkin"
    nt = mat.node_tree
    bsdf = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None)
    if bsdf:
        for l in list(bsdf.inputs["Metallic"].links):
            nt.links.remove(l)
        bsdf.inputs["Metallic"].default_value = 0.0
        for k, v in (("Specular IOR Level", 0.35), ("Coat Weight", 0.0)):
            if k in bsdf.inputs:
                bsdf.inputs[k].default_value = v
for img in bpy.data.images:
    if img.size[0] > 1024 and "diffuse" not in img.name:
        img.scale(1024, 1024)
        img.pack()                     # the scaled pixels replace the embedded file
    elif not img.packed_file:
        img.pack()
for pl in me.polygons:
    pl.use_smooth = True
body.data.update()

rig.show_in_front = True
rig.data.display_type = "STICK"
bpy.ops.object.select_all(action="DESELECT")
bpy.ops.wm.save_as_mainfile(filepath=DST, compress=True)
print("SAVED", DST)

# ---------------------------------------------------------------- optional test render of a few poses (needs sila_hero.py)
if TEST:
    import os
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, os.path.join(here, "..", "blender", "sets"))
    sys.path.insert(0, os.path.join(here, "..", "blender"))
    sys.path.append(os.path.join(here, "..", "..", "..", "blender", "kit", "blender"))
    import sila_hero as SH
    SH.test_sheet(rig, body, TEST)
