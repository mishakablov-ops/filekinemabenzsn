# blender -b --factory-startup --disable-autoexec --python rig_chars.py -- <name> <height_m> <in.glb> <out.glb> [test.png] [tris=1800] [tex=256]
# Rig a generated A-pose character from scratch:
#  * normalise: one mesh, feet on z=0, centred, facing -Y, scaled to the given height; seams welded (UVs stay per-loop)
#  * joints found from the mesh itself (horizontal slices: torso / arm / leg clusters), Mixamo-style bone names
#  * weights: Blender bone heat, then bleeding removed (a vertex only keeps bones near it) and normalised
#  * textures: diffuse 2048, normal + ORM 1024; exported as GLB (armature + skinned mesh, no animation)
# Optional test render: the rig posed (arm raised, knee bent, spine bent) to check the weights.
import math
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Vector

args = sys.argv[sys.argv.index("--") + 1:]
NAME, TARGET_H, SRC, DST = args[0], float(args[1]), args[2], args[3]
TEST = args[4] if len(args) > 4 and not args[4].startswith(("tris=", "tex=")) else None
HAND = {"him": 0.15}.get(NAME, 0.108)  # hand length / height
DRESS = NAME in ("valya", "lyuda")

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
body.name = NAME
for o in [o for o in bpy.data.objects if o.type == "EMPTY"]:
    bpy.data.objects.remove(o)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

# weld seams, clean
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.mesh.remove_doubles(threshold=0.0004)
bpy.ops.object.mode_set(mode="OBJECT")
me = body.data
V = np.array([v.co[:] for v in me.vertices], np.float64)
lo, hi = V.min(0), V.max(0)
H0 = hi[2] - lo[2]
s = TARGET_H / H0
V = (V - np.array([(lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, lo[2]])) * s
me.vertices.foreach_set("co", V.astype(np.float32).ravel())
me.update()
H = TARGET_H
print("NORMALISED", NAME, "verts", len(V), "scale", round(s, 4))


def slab(z, tol=0.006):
    return V[np.abs(V[:, 2] - z) < tol * H]


def clusters(x, gap):
    """1-D clusters of sorted values split at gaps larger than `gap`"""
    xs = np.sort(x)
    cut = np.where(np.diff(xs) > gap)[0]
    parts = np.split(xs, cut + 1)
    return [(p.min(), p.max()) for p in parts if len(p) > 3]


def side_pts(pts, sign, xmin, xmax):
    return pts[(pts[:, 0] * sign >= xmin) & (pts[:, 0] * sign <= xmax)]


# ---------------------------------------------------------------- joints from the mesh
mid = lambda a: float((a.min() + a.max()) / 2)


def torso_y(z, half):
    q = slab(z, 0.006)
    q = q[np.abs(q[:, 0]) < half]
    return mid(q[:, 1]) if len(q) else 0.0


def torso_half(z):
    q = slab(z, 0.006)
    c = [k for k in clusters(q[:, 0], 0.01 * H) if k[0] <= 0 <= k[1]]
    return max(-c[0][0], c[0][1]) if c else 0.12 * H


# T-pose: arms horizontal at shoulder height; joints from slices across the arm
sh_x = torso_half(0.74 * H) - 0.02 * H
sh_x = min(max(sh_x, 0.085 * H), 0.13 * H)


def arm_section(x, sign, w=0.004):
    q = V[(np.abs(V[:, 0] * sign - x) < w * H) & (V[:, 2] > 0.62 * H)]
    if len(q) < 4:
        return None
    c = clusters(q[:, 2], 0.02 * H)
    k = max(c, key=lambda r: r[1])  # the arm is the highest cluster in this slice
    q = q[(q[:, 2] >= k[0]) & (q[:, 2] <= k[1])]
    return mid(q[:, 1]), mid(q[:, 2]), k


joints, SHZ = {}, {}
for sign, nm in ((1, "Left"), (-1, "Right")):
    tip_x = float((V[:, 0] * sign).max())
    wrist_x = tip_x - HAND * H
    sec = lambda x: arm_section(x, sign) or (0.0, 0.81 * H, None)
    y0, z0, _ = sec(sh_x + 0.05 * H)
    shoulder = Vector((sign * sh_x, y0, z0))
    el_x = sh_x + 0.56 * (wrist_x - sh_x)
    ye, ze, _ = sec(el_x)
    yw, zw, _ = sec(wrist_x)
    yt, zt, _ = sec(tip_x - 0.02 * H)
    joints[nm + "Arm"] = shoulder
    joints[nm + "ForeArm"] = Vector((sign * el_x, ye + 0.004 * H, ze))
    joints[nm + "Hand"] = Vector((sign * wrist_x, yw, zw))
    joints[nm + "HandEnd"] = Vector((sign * (tip_x - 0.01 * H), yt, zt))
    joints[nm + "Shoulder"] = Vector((sign * 0.025 * H, y0 + 0.01 * H, z0 - 0.01 * H))
    SHZ[sign] = z0
ARMPIT = {k: v - 0.06 * H for k, v in SHZ.items()}
print("SHOULDER_X", round(sh_x, 3), "SHZ", {k: round(v, 3) for k, v in SHZ.items()})


def leg_centre(z, sign):
    q = slab(z, 0.006)
    q = q[(q[:, 0] * sign > 0.005 * H) & (np.abs(q[:, 0]) < sh_x * 0.95)]
    cl = clusters(q[:, 0] * sign, 0.01 * H) if len(q) else []
    if cl:
        c = cl[0]
        q = q[(q[:, 0] * sign >= c[0]) & (q[:, 0] * sign <= c[1])]
        return sign * mid(np.abs(q[:, 0])), mid(q[:, 1])
    if len(q):
        return sign * mid(np.abs(q[:, 0])), mid(q[:, 1])
    return sign * 0.055 * H, 0.0


for sign, nm in ((1, "Left"), (-1, "Right")):
    x2, y2 = leg_centre(0.20 * H, sign)
    xk, yk = leg_centre(0.285 * H, sign) if not DRESS else (x2, y2 - 0.004 * H)
    hx = sign * min(max(abs(x2), 0.045 * H), 0.065 * H)
    joints[nm + "UpLeg"] = Vector((hx, torso_y(0.5 * H, sh_x * 0.7), 0.505 * H))
    joints[nm + "Leg"] = Vector((xk, yk - 0.004 * H, 0.285 * H))
    xa, ya = leg_centre(0.07 * H, sign)
    ankle = Vector((xa, ya + 0.012 * H, 0.045 * H))
    foot = V[(V[:, 2] < 0.05 * H) & (V[:, 0] * sign > 0)]
    toe = foot[np.argmin(foot[:, 1])]  # most forward (-Y)
    joints[nm + "Foot"] = ankle
    joints[nm + "ToeBase"] = Vector((ankle.x * 0.6 + toe[0] * 0.4, ankle.y + (toe[1] - ankle.y) * 0.72, 0.022 * H))
    joints[nm + "ToeEnd"] = Vector((toe[0], toe[1], 0.02 * H))

ty = lambda f: torso_y(f * H, sh_x * 0.7)
joints["Hips"] = Vector((0, ty(0.525), 0.525 * H))
for nm, f in (("Spine", 0.585), ("Spine1", 0.655), ("Spine2", 0.725)):
    joints[nm] = Vector((0, ty(f) + 0.01 * H, f * H))  # spine sits behind the body centre
for nm, f in (("Neck", 0.835), ("Head", 0.885)):
    joints[nm] = Vector((0, ty(f) + 0.004 * H, f * H))
joints["HeadEnd"] = Vector((0, joints["Head"].y, H))
print("JOINTS", {k: tuple(round(c, 3) for c in v) for k, v in joints.items()})

# ---------------------------------------------------------------- low poly (PS1): decimate after the joints were found on the dense mesh
TRIS = int(next((a.split("=")[1] for a in args if a.startswith("tris=")), "1800"))
TEXPX = int(next((a.split("=")[1] for a in args if a.startswith("tex=")), "256"))
bpy.ops.object.select_all(action="DESELECT")
body.select_set(True)
bpy.context.view_layer.objects.active = body
tris = sum(len(pl.vertices) - 2 for pl in body.data.polygons)
if tris > TRIS:
    dm = body.modifiers.new("dec", "DECIMATE")
    dm.decimate_type = "COLLAPSE"
    dm.ratio = TRIS / tris
    dm.use_collapse_triangulate = True
    bpy.ops.object.modifier_apply(modifier="dec")
for pl in body.data.polygons:
    pl.use_smooth = False  # faceted
me = body.data
V = np.array([v.co[:] for v in me.vertices], np.float64)
print("DECIMATED", tris, "->", len(body.data.polygons), "tris; verts", len(V))

# ---------------------------------------------------------------- armature
arm_data = bpy.data.armatures.new(NAME + "_rig")
rig = bpy.data.objects.new(NAME + "_rig", arm_data)
bpy.context.scene.collection.objects.link(rig)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode="EDIT")
eb = arm_data.edit_bones
CHAIN = [
    ("Hips", "Hips", "Spine", None), ("Spine", "Spine", "Spine1", "Hips"), ("Spine1", "Spine1", "Spine2", "Spine"),
    ("Spine2", "Spine2", "Neck", "Spine1"), ("Neck", "Neck", "Head", "Spine2"), ("Head", "Head", "HeadEnd", "Neck"),
]
for side in ("Left", "Right"):
    CHAIN += [
        (side + "Shoulder", side + "Shoulder", side + "Arm", "Spine2"), (side + "Arm", side + "Arm", side + "ForeArm", side + "Shoulder"),
        (side + "ForeArm", side + "ForeArm", side + "Hand", side + "Arm"), (side + "Hand", side + "Hand", side + "HandEnd", side + "ForeArm"),
        (side + "UpLeg", side + "UpLeg", side + "Leg", "Hips"), (side + "Leg", side + "Leg", side + "Foot", side + "UpLeg"),
        (side + "Foot", side + "Foot", side + "ToeBase", side + "Leg"), (side + "ToeBase", side + "ToeBase", side + "ToeEnd", side + "Foot"),
    ]
for name, h, t, parent in CHAIN:
    b = eb.new(name)
    b.head, b.tail = joints[h], joints[t]
    if parent:
        b.parent = eb[parent]
        b.use_connect = (eb[parent].tail - b.head).length < 1e-4
    # roll: bone Z toward the character's front (-Y) for limbs/spine; feet: Z up
    b.align_roll(Vector((0, 0, 1)) if "Foot" in name or "Toe" in name else Vector((0, -1, 0)))
bpy.ops.object.mode_set(mode="OBJECT")

# ---------------------------------------------------------------- weights
bpy.ops.object.select_all(action="DESELECT")
body.select_set(True)
rig.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.parent_set(type="ARMATURE_AUTO")
groups = {g.index: g.name for g in body.vertex_groups}
bones = {b.name: (np.array(b.head_local), np.array(b.tail_local)) for b in arm_data.bones}
names = list(bones)
W = np.zeros((len(V), len(names)))
gi = {g.name: i for i, g in enumerate(body.vertex_groups)}
col = {n: names.index(n) for n in names if n in gi}
for v in me.vertices:
    for g in v.groups:
        n = groups[g.group]
        if n in col:
            W[v.index, col[n]] = g.weight
zero = int((W.sum(1) < 1e-4).sum())


def seg_dist(P, a, b):
    ab = b - a
    t = np.clip(((P - a) @ ab) / max(ab @ ab, 1e-9), 0, 1)
    return np.linalg.norm(P - (a + t[:, None] * ab), axis=1)


D = np.stack([seg_dist(V, *bones[n]) for n in names], 1)
# which vertices belong to an arm (T-pose: everything outside the torso above the hips)
is_arm = {1: (V[:, 0] > sh_x + 0.03 * H) & (V[:, 2] > 0.62 * H), -1: (V[:, 0] < -sh_x - 0.03 * H) & (V[:, 2] > 0.62 * H)}
B = {n: i for i, n in enumerate(names)}
allow = np.ones_like(W, bool)
for sign, side in ((1, "Left"), (-1, "Right")):
    other = "Right" if side == "Left" else "Left"
    chain = [side + x for x in ("Shoulder", "Arm", "ForeArm", "Hand")]
    am = is_arm[sign]
    for n in names:
        if n not in chain and not (n == "Spine2"):
            allow[am, B[n]] = False  # arm vertices follow the arm only (and the chest at the top)
    allow[am & (np.abs(V[:, 0]) > sh_x + 0.10 * H), B["Spine2"]] = False
    non = ~(is_arm[1] | is_arm[-1])
    for n in (side + "ForeArm", side + "Hand"):
        allow[non, B[n]] = False
    allow[non & ((V[:, 2] < ARMPIT[sign] - 0.02 * H) | (np.abs(V[:, 0]) < sh_x - 0.05 * H)), B[side + "Arm"]] = False
    if not DRESS:  # trousers: each leg follows its own leg bones
        for n in (other + "UpLeg", other + "Leg", other + "Foot", other + "ToeBase"):
            allow[non & (V[:, 2] < 0.47 * H) & (V[:, 0] * sign > 0.012 * H), B[n]] = False
low = V[:, 2] < 0.40 * H
for n in names:
    if not any(k in n for k in ("UpLeg", "Leg", "Foot", "Toe", "Hand", "ForeArm")):
        allow[low, B[n]] = False
near_ok = D <= D.min(1, keepdims=True) * 2.0 + 0.04 * H / 1.75
allow &= near_ok | (W > 0.5)
W = np.where(allow, W, 0)
empty = W.sum(1) < 1e-4
Dm = np.where(allow, D, 1e9)
W[empty, Dm[empty].argmin(1)] = 1.0
# smooth over the mesh (neighbours), keeping the masks
E = np.array([e.vertices[:] for e in me.edges])
for it in range(3):
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
print("ARMVERTS", int(is_arm[1].sum()), int(is_arm[-1].sum()))
for g in list(body.vertex_groups):
    body.vertex_groups.remove(g)
for i, n in enumerate(names):
    g = body.vertex_groups.new(name=n)
    nz = np.nonzero(W[:, i] > 0.002)[0]
    for vi in nz:
        g.add([int(vi)], float(W[vi, i]), "REPLACE")
print("WEIGHTS heat-missed", zero, "of", len(V))

# ---------------------------------------------------------------- textures: PS1 look = small diffuse, no normal / ORM maps
for mat in body.data.materials:
    if not mat or not mat.use_nodes:
        continue
    nt = mat.node_tree
    bsdf = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None)
    for n in list(nt.nodes):
        if n.type == "TEX_IMAGE" and n.image and ("normal" in n.image.name or "metal" in n.image.name or "rough" in n.image.name):
            nt.nodes.remove(n)
    for n in list(nt.nodes):
        if n.type in ("NORMAL_MAP", "SEPARATE_COLOR", "SEPRGB"):
            nt.nodes.remove(n)
    if bsdf:
        bsdf.inputs["Roughness"].default_value = 0.85
        bsdf.inputs["Metallic"].default_value = 0.0
for img in bpy.data.images:
    if img.size[0] > TEXPX:
        img.scale(TEXPX, TEXPX)

bpy.ops.object.select_all(action="SELECT")
bpy.ops.export_scene.gltf(filepath=DST, export_format="GLB", use_selection=True, export_animations=False, export_skins=True,
                          export_yup=True, export_image_format="JPEG", export_jpeg_quality=88)
print("EXPORTED", DST)

# ---------------------------------------------------------------- optional test pose render
if TEST:
    pb = rig.pose.bones
    rig.rotation_mode = "XYZ"
    def rot(n, ax, deg):
        b = pb[n]
        b.rotation_mode = "XYZ"
        e = list(b.rotation_euler)
        e["XYZ".index(ax)] += math.radians(deg)
        b.rotation_euler = e
    rot("LeftArm", "Z", 70)
    rot("LeftForeArm", "X", 60)
    rot("RightArm", "X", -50)
    rot("RightForeArm", "X", 90)
    rot("RightUpLeg", "X", 60)
    rot("RightLeg", "X", -80)
    rot("Spine1", "X", 20)
    rot("Head", "Y", 30)
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items.keys() else "BLENDER_EEVEE"
    sc.render.resolution_x, sc.render.resolution_y = 1200, 1000
    sc.world = bpy.data.worlds.new("w")
    sc.world.color = (0.45, 0.45, 0.47)
    sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
    sun.data.energy = 3
    sun.rotation_euler = (0.9, 0.1, -0.5)
    sc.collection.objects.link(sun)
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = H * 1.25
    sc.collection.objects.link(cam)
    sc.camera = cam
    for k, (cx, cy, rz) in enumerate([(0.0, -5.0, 0.0), (3.2, -5.0, math.radians(32))]):
        cam.location = (cx, cy, H * 0.55)
        cam.rotation_euler = (math.pi / 2, 0, rz)
        sc.render.filepath = TEST.replace(".png", f"_{k}.png")
        bpy.ops.render.render(write_still=True)
    print("TEST", TEST)
