# blender -b --factory-startup --disable-autoexec --python build_fp_arms.py -- <source/scene.gltf> <out.glb> <work_dir> [previews]
# First-person arms for KINEMA: "Fps arms" by DJMaesen (CC-BY-4.0), re-skinned as bare hands + olive KPA sleeves.
# Skeleton + weights adapted from the Codex build (fitted to this exact mesh). Frame (Blender): eye at the origin,
# looking +Y, up +Z, +X right  ->  glTF/three.js: camera space (+X right, +Y up, -Z forward). Units: metres.
# Runtime posing is done in the engine (src/three/fphands.ts): two-bone IK + finger curls. No baked clips.
import math
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Matrix, Quaternion, Vector

def clamp(x, a=0.0, b=1.0):
    return min(b, max(a, x))


def smooth(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


args = sys.argv[sys.argv.index("--") + 1:]
SRC, OUT_GLB, WORK = args[0], args[1], Path(args[2])
PREVIEWS = len(args) > 3
WORK.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------------ import, metres, Codex frame
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)
mesh = [o for o in bpy.context.scene.objects if o.type == "MESH"][0]
w = mesh.matrix_world.copy()
mesh.parent = None
mesh.matrix_world = w
for o in list(bpy.context.scene.objects):
    if o is not mesh:
        bpy.data.objects.remove(o, do_unlink=True)
bpy.context.view_layer.objects.active = mesh
mesh.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
for v in mesh.data.vertices:
    v.co *= 0.01
bm = bmesh.new()
bm.from_mesh(mesh.data)
bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=1e-5)
bm.to_mesh(mesh.data)
bm.free()
OFFSET = Vector((0, 0.25, -0.40))  # shoulders below / slightly in front of the eye
raw = []
for v in mesh.data.vertices:
    v.co.x *= -1
    v.co.y *= -1
    raw.append(v.co.copy())
    v.co += OFFSET
mesh.name = mesh.data.name = "fp_arms_mesh"
while len(mesh.data.uv_layers) > 1:
    mesh.data.uv_layers.remove(mesh.data.uv_layers[-1])
mesh.data.uv_layers[0].name = "uv0"

# ------------------------------------------------------------------ sleeve vs skin: by UV island position along the arm
bm = bmesh.new()
bm.from_mesh(mesh.data)
uvl = bm.loops.layers.uv.active
bm.faces.ensure_lookup_table()
seen, islands = set(), []
for f in bm.faces:
    if f.index in seen:
        continue
    stack, isl = [f], []
    seen.add(f.index)
    while stack:
        g = stack.pop()
        isl.append(g.index)
        for e in g.edges:
            for h in e.link_faces:
                if h.index in seen:
                    continue
                same = all(([l[uvl].uv for l in g.loops if l.vert == v][0] - [l[uvl].uv for l in h.loops if l.vert == v][0]).length < 1e-4 for v in e.verts)
                if same:
                    seen.add(h.index)
                    stack.append(h)
    islands.append(isl)
skin_faces = set()
for isl in islands:
    ymax = max(raw[v.index].y for i in isl for v in bm.faces[i].verts)
    if ymax > 0.225:  # sleeve islands end at y = 0.220; the wrist strip and the glove go further
        skin_faces.update(isl)
bm.free()
print("SKIN_FACES", len(skin_faces), "of", len(mesh.data.polygons))

# ---- slim the wrist: the source glove cuff is ~44 mm in radius; a real wrist is ~27 mm. Squeeze skin-only vertices
# (never the ones shared with the sleeve) towards the slice centre, fading back to the original hand at y = 0.265.
skin_verts, sleeve_verts = set(), set()
for p in mesh.data.polygons:
    (skin_verts if p.index in skin_faces else sleeve_verts).update(p.vertices)
AX = (Vector((-.201, .319, -.022)) - Vector((-.212, -.005, .045))).normalized()  # forearm/hand axis (left frame)
slices = {}
for i in skin_verts:
    q = raw[i].copy()
    q.x = -abs(q.x)
    if 0.19 <= q.y <= 0.27:
        slices.setdefault((raw[i].x < 0, round(q.y / 0.005)), []).append(i)
moved = 0
for (is_left, k), ids in slices.items():
    pts = [Vector((-abs(raw[i].x), raw[i].y, raw[i].z)) for i in ids]
    c = sum(pts, Vector()) / len(pts)
    rad = [((p - c) - AX * (p - c).dot(AX)).length for p in pts]
    rmax = max(rad) if rad else 0
    y = k * 0.005
    if rmax < 1e-4:
        continue
    f = 1.0 + (min(1.0, 0.030 / rmax) - 1.0) * (1 - smooth((y - 0.240) / 0.025))
    for i, p in zip(ids, pts):
        if i in sleeve_verts:
            continue
        off = (p - c) - AX * (p - c).dot(AX)
        np_ = p - off * (1 - f)
        np_.x = np_.x if is_left else -np_.x
        mesh.data.vertices[i].co = np_ + OFFSET
        raw[i] = np_
        moved += 1
print("WRIST_SLIMMED", moved)

# ------------------------------------------------------------------ sleeve texture -> olive-khaki KPA cotton (fabric detail kept)
src_mat = mesh.data.materials[0]
src_mat.name = "kpa_sleeve"
base_node = [n for n in src_mat.node_tree.nodes if n.type == "TEX_IMAGE" and "baseColor" in n.image.name][0]
img = bpy.data.images.load(str(Path(SRC).parent / "textures" / "material_baseColor.png"))  # read pixels from the file itself
W_, H_ = img.size
import numpy as np  # noqa: E402  (bundled with Blender)

px = np.empty(W_ * H_ * 4, np.float32)
img.pixels.foreach_get(px)
px = px.reshape(H_, W_, 4)
lum = px[..., 0] * 0.299 + px[..., 1] * 0.587 + px[..., 2] * 0.114
u0, v0, u1, v1 = 0.26, 0.26, 0.82, 0.84  # main sleeve island in UV
ref = float(np.median(lum[int(v0 * H_):int(v1 * H_), int(u0 * W_):int(u1 * W_)]))
OLIVE = np.array([0.405, 0.392, 0.262], np.float32)  # sRGB-ish khaki-olive mid tone
ratio = np.clip(lum / max(ref, 1e-3), 0.35, 1.9) ** 0.85
px[..., :3] = np.clip(OLIVE[None, None, :] * ratio[..., None], 0, 1)
olive = bpy.data.images.new("kpa_sleeve_basecolor", W_, H_, alpha=True)
olive.pixels.foreach_set(px.ravel())
olive.filepath_raw = str(WORK / "kpa_sleeve_basecolor.png")
olive.file_format = "PNG"
olive.save()  # attached to the sleeve only after the skin bake (bake writes into every material's active image)

# ------------------------------------------------------------------ skeleton (Codex fit, left-hand frame x<0; right = mirror)
L = {
    "Shoulder": [(-.105, -.226, .131), (-.205, -.226, .131)],
    "Arm": [(-.205, -.226, .131), (-.212, -.005, .045)],
    "ForeArm": [(-.212, -.005, .045), (-.203, .227, -.007)],
    "Hand": [(-.203, .227, -.007), (-.201, .319, -.022)],
    "Thumb": [(-.203, .246, .005), (-.187, .274, .022), (-.157, .305, .034), (-.130, .327, .040), (-.108, .344, .040)],
    "Index": [(-.203, .253, .000), (-.201, .339, .013), (-.178, .387, .005), (-.151, .418, -.004), (-.132, .431, -.014)],
    "Middle": [(-.207, .252, -.013), (-.211, .329, -.018), (-.188, .380, -.036), (-.159, .414, -.049), (-.135, .428, -.056)],
    "Ring": [(-.209, .250, -.028), (-.211, .311, -.045), (-.190, .356, -.064), (-.161, .388, -.076), (-.136, .400, -.080)],
    "Pinky": [(-.211, .246, -.039), (-.208, .288, -.069), (-.185, .328, -.085), (-.159, .352, -.092), (-.141, .367, -.094)],
}
FINGERS = ["Thumb", "Index", "Middle", "Ring", "Pinky"]


def clamp(x, a=0.0, b=1.0):
    return min(b, max(a, x))


def smooth(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def projection(p, a, b):
    a, b = Vector(a), Vector(b)
    d = b - a
    t = clamp((p - a).dot(d) / d.length_squared)
    return (p - (a + t * d)).length, t


# ------------------------------------------------------------------ skin: new unwrap + baked texture (tone variation, knuckles, nails)
mesh.data.polygons.foreach_set("select", [i in skin_faces for i in range(len(mesh.data.polygons))])
skin_mat = bpy.data.materials.new("skin")
skin_mat.use_nodes = True
mesh.data.materials.append(skin_mat)
for p in mesh.data.polygons:
    if p.index in skin_faces:
        p.material_index = 1
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_mode(type="FACE")
bpy.ops.object.mode_set(mode="OBJECT")
mesh.data.polygons.foreach_set("select", [i in skin_faces for i in range(len(mesh.data.polygons))])
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.006, scale_to_bounds=True)
bpy.ops.object.mode_set(mode="OBJECT")

# per-vertex masks in the left-hand frame: R = nail, G = flush (knuckles, fingertips)
DORSAL = {f: Vector((-1, 0, 0)) for f in FINGERS}  # palms face inwards in the rest pose -> backs of the fingers face outwards
DORSAL["Thumb"] = Vector((-0.45, 0.0, 0.89)).normalized()
col = mesh.data.color_attributes.new("mask", "FLOAT_COLOR", "POINT")
for i, q in enumerate(raw):
    p = q.copy()
    p.x = -abs(p.x)
    nail = flush = 0.0
    if p.y > 0.24:
        for fn in FINGERS:
            pts = [Vector(x) for x in L[fn]]
            d, t = projection(p, pts[3], pts[4])
            seg = pts[4] - pts[3]
            axis_pt = pts[3] + seg * t
            out = (p - axis_pt)
            if out.length < 1e-6:
                continue
            facing = out.normalized().dot(DORSAL[fn])
            r = 0.0085 if fn != "Thumb" else 0.0095
            if d < 0.016:
                # nail: last ~55 % of the distal phalanx, on the back of the finger
                along = (p - pts[3]).dot(seg.normalized()) / seg.length
                n = smooth((facing - 0.55) / 0.25) * smooth((along - 0.42) / 0.12) * smooth((1.08 - along) / 0.1)
                nail = max(nail, n)
                flush = max(flush, 0.6 * smooth((along - 0.7) / 0.3) * (1 - smooth((facing + 0.2) / 0.6)))  # pink fingertip pads
            for j in (1, 2, 3):  # knuckles on the back of the hand / fingers
                kd = (p - pts[j]).length
                if kd < 0.016:
                    flush = max(flush, (1 - kd / 0.016) * 0.75 * smooth((facing + 0.1) / 0.5))
    col.data[i].color = (nail, flush, 0.0, 1.0)

nt = skin_mat.node_tree
for n in list(nt.nodes):
    nt.nodes.remove(n)
outn = nt.nodes.new("ShaderNodeOutputMaterial")
emit = nt.nodes.new("ShaderNodeEmission")
attr = nt.nodes.new("ShaderNodeAttribute")
attr.attribute_name = "mask"
sep = nt.nodes.new("ShaderNodeSeparateColor")
noise = nt.nodes.new("ShaderNodeTexNoise")
noise.inputs["Scale"].default_value = 18.0
noise.inputs["Detail"].default_value = 6.0
fine = nt.nodes.new("ShaderNodeTexNoise")
fine.inputs["Scale"].default_value = 260.0
fine.inputs["Detail"].default_value = 2.0
geo = nt.nodes.new("ShaderNodeNewGeometry")
ramp = nt.nodes.new("ShaderNodeValToRGB")  # large-scale tone: slightly darker / warmer patches
ramp.color_ramp.elements[0].color = (0.47, 0.245, 0.14, 1)
ramp.color_ramp.elements[1].color = (0.60, 0.33, 0.20, 1)
mix_fine = nt.nodes.new("ShaderNodeMix")
mix_fine.data_type = "RGBA"
mix_fine.blend_type = "MULTIPLY"
mix_fine.inputs[0].default_value = 0.10
flush_mix = nt.nodes.new("ShaderNodeMix")
flush_mix.data_type = "RGBA"
flush_mix.inputs[7].default_value = (0.56, 0.20, 0.13, 1)
nail_mix = nt.nodes.new("ShaderNodeMix")
nail_mix.data_type = "RGBA"
nail_mix.inputs[7].default_value = (0.70, 0.45, 0.37, 1)
nt.links.new(geo.outputs["Position"], noise.inputs["Vector"])
nt.links.new(geo.outputs["Position"], fine.inputs["Vector"])
nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
nt.links.new(ramp.outputs["Color"], mix_fine.inputs[6])
nt.links.new(fine.outputs["Color"], mix_fine.inputs[7])
nt.links.new(attr.outputs["Color"], sep.inputs["Color"])
nt.links.new(sep.outputs["Green"], flush_mix.inputs[0])
nt.links.new(mix_fine.outputs[2], flush_mix.inputs[6])
nt.links.new(sep.outputs["Red"], nail_mix.inputs[0])
nt.links.new(flush_mix.outputs[2], nail_mix.inputs[6])
nt.links.new(nail_mix.outputs[2], emit.inputs["Color"])
nt.links.new(emit.outputs["Emission"], outn.inputs["Surface"])
skin_img = bpy.data.images.new("skin_basecolor", 2048, 2048, alpha=False)
tex = nt.nodes.new("ShaderNodeTexImage")
tex.image = skin_img
nt.nodes.active = tex
sc = bpy.context.scene
sc.render.engine = "CYCLES"
sc.cycles.samples = 4
sc.cycles.device = "CPU"
sc.render.bake.margin = 8
for p in mesh.data.polygons:  # bake only reads the skin material; sleeve faces keep their texture
    pass
mesh.select_set(True)
bpy.context.view_layer.objects.active = mesh
bpy.ops.object.bake(type="EMIT")
skin_img.filepath_raw = str(WORK / "skin_basecolor.png")
skin_img.file_format = "PNG"
skin_img.save()
print("BAKED skin")
olive = bpy.data.images.load(str(WORK / "kpa_sleeve_basecolor.png"), check_existing=False)
olive.name = "kpa_sleeve_basecolor"
base_node.image = olive

# final skin material: Principled with the baked colour (what glTF exports)
for n in list(nt.nodes):
    nt.nodes.remove(n)
outn = nt.nodes.new("ShaderNodeOutputMaterial")
bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
tex = nt.nodes.new("ShaderNodeTexImage")
tex.image = skin_img
bsdf.inputs["Roughness"].default_value = 0.52
bsdf.inputs["Specular IOR Level"].default_value = 0.35
nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
nt.links.new(bsdf.outputs["BSDF"], outn.inputs["Surface"])
mesh.data.color_attributes.remove(mesh.data.color_attributes["mask"])

# ------------------------------------------------------------------ armature
bpy.ops.object.armature_add(enter_editmode=True, location=(0, 0, 0))
rig = bpy.context.object
rig.name = "fp_arms_rig"
rig.data.name = "fp_arms_skeleton"
eb = rig.data.edit_bones
eb.remove(eb[0])
root = eb.new("Root")
root.head = (0, 0, 0)
root.tail = (0, 0.08, 0)
specs = {}
for side, prefix, sign in [("L", "Left", 1), ("R", "Right", -1)]:
    def p_(co, sign=sign):
        return Vector((co[0] * sign, co[1], co[2])) + OFFSET

    def bone(name, a, b, parent, sign=sign):
        ob = eb.new(name)
        ob.head = p_(a)
        ob.tail = p_(b)
        ob.parent = eb[parent]
        ob.use_deform = True
        ob.align_roll(Vector((sign, 0, 0)))
        specs[name] = parent
        return ob
    for part, parent in [("Shoulder", "Root"), ("Arm", prefix + "Shoulder"), ("ForeArm", prefix + "Arm"), ("Hand", prefix + "ForeArm")]:
        bone(prefix + part, *L[part], parent)
    bone(prefix + "ForeArmTwist", *L["ForeArm"], prefix + "ForeArm")
    for fn in FINGERS:
        pts = L[fn]
        for j in range(4):
            bone(prefix + "Hand" + fn + str(j), pts[j], pts[j + 1], prefix + "Hand" if j == 0 else prefix + "Hand" + fn + str(j - 1))
bpy.ops.object.mode_set(mode="OBJECT")


def digit_weights(p, finger):
    pts = [Vector(x) for x in L[finger][1:]]
    distances = [projection(p, pts[j], pts[j + 1]) for j in range(3)]
    idx = min(range(3), key=lambda j: distances[j][0])
    d, t = distances[idx]
    lengths = [(pts[j + 1] - pts[j]).length for j in range(3)]
    s = sum(lengths[:idx]) + lengths[idx] * t
    weights = {idx + 1: 1.0}
    width = .010 if finger != "Thumb" else .009
    for joint in [1, 2]:
        boundary = sum(lengths[:joint])
        q = (s - boundary) / width
        if abs(q) < 1:
            ww = smooth((q + 1) / 2)
            weights = {joint: 1 - ww, joint + 1: ww}
            break
    if s < .012:
        bend = smooth((s + .007) / .019)
        weights = {0: 1 - bend, 1: bend}
    return d, weights


groups = {name: mesh.vertex_groups.new(name=name) for name in specs}
for i, point in enumerate(raw):
    prefix = "Left" if point.x < 0 else "Right"
    p = point.copy()
    p.x = -abs(p.x)
    y = p.y
    weights = {}
    if y < .205:
        arm = smooth((y + .045) / .080)
        twist = smooth((y - .055) / .145) * .8
        weights = {prefix + "Arm": 1 - arm, prefix + "ForeArm": arm * (1 - twist), prefix + "ForeArmTwist": arm * twist}
        if y > .190:
            hand = smooth((y - .190) / .055)
            weights = {k: v * (1 - hand) for k, v in weights.items()}
            weights[prefix + "Hand"] = hand
    else:
        cands = []
        for fn in FINGERS:
            mcp = Vector(L[fn][1])
            direction = (Vector(L[fn][2]) - mcp).normalized()
            d, ww = digit_weights(p, fn)
            gate = (p - mcp).dot(direction) > -.012
            if fn == "Thumb":
                gate = gate and p.x > -.19 and p.z > -.001
            if gate:
                cands.append((d, fn, ww))
        if cands and min(cands)[0] < .028:
            d, fn, ww = min(cands)
            weights = {prefix + "Hand" + fn + str(k): value for k, value in ww.items()}
        else:
            hand = smooth((y - .190) / .055)
            weights = {prefix + "ForeArmTwist": 1 - hand, prefix + "Hand": hand}
            if y > .263:
                closest = min(FINGERS, key=lambda f_: projection(p, *L[f_][:2])[0])
                d, t = projection(p, *L[closest][:2])
                ww = .45 * smooth((t - .30) / .65)
                weights = {k: v * (1 - ww) for k, v in weights.items()}
                weights[prefix + "Hand" + closest + "0"] = ww
    weights = {k: v for k, v in weights.items() if v > 1e-5}
    weights = dict(sorted(weights.items(), key=lambda kv: -kv[1])[:4])
    total = sum(weights.values())
    for name, ww in weights.items():
        groups[name].add([i], ww / total, "REPLACE")

# smoother silhouettes: one subdivision level before skinning (weights are interpolated)
sub = mesh.modifiers.new("smooth", "SUBSURF")
sub.levels = sub.render_levels = 1
for p in mesh.data.polygons:
    p.use_smooth = True
arm_mod = mesh.modifiers.new("skin", "ARMATURE")
arm_mod.object = rig
mesh.parent = rig
for b in rig.pose.bones:
    b.rotation_mode = "QUATERNION"

# palm sockets (props held in a hand attach here): +Y along the fingers, +Z into the grip
for side, prefix in [("L", "Left"), ("R", "Right")]:
    e = bpy.data.objects.new("SOCKET_hand_" + side, None)
    bpy.context.collection.objects.link(e)
    e.empty_display_type = "ARROWS"
    e.empty_display_size = .035
    e.parent = rig
    e.parent_type = "BONE"
    e.parent_bone = prefix + "Hand"
    e.location = (0, -rig.data.bones[prefix + "Hand"].length * .48, .010)

# ------------------------------------------------------------------ export (rest pose, no clips: posing happens in the engine)
rig["credit"] = 'Based on "Fps arms" by DJMaesen (sketchfab.com/3d-models/fps-arms-9452ce4cddde4110a4fd73e555a8e412), CC-BY-4.0'
bpy.ops.object.select_all(action="DESELECT")
for o in [rig, mesh, *[o for o in sc.objects if o.name.startswith("SOCKET_")]]:
    o.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.export_scene.gltf(filepath=OUT_GLB, export_format="GLB", use_selection=True, export_yup=True, export_apply=True,
                          export_animations=False, export_def_bones=True, export_all_influences=False,
                          export_image_format="JPEG", export_jpeg_quality=90, export_extras=True)
print("EXPORTED", OUT_GLB)
bpy.ops.wm.save_as_mainfile(filepath=str(WORK / "fp_arms_kinema.blend"))

# ------------------------------------------------------------------ previews in the reel's portrait camera
if PREVIEWS:
    REST = {b.name: b.matrix.copy() for b in rig.pose.bones}

    def reset_pose():
        for b in rig.pose.bones:
            b.matrix_basis = Matrix.Identity(4)
        bpy.context.view_layer.update()

    def set_world_delta(bone, direction):
        q = (bone.tail - bone.head).normalized().rotation_difference(direction.normalized())
        m = bone.matrix.copy()
        head = m.translation.copy()
        bone.matrix = Matrix.Translation(head) @ q.to_matrix().to_4x4() @ Matrix.Translation(-head) @ m
        bpy.context.view_layer.update()

    def ik(side, target, rotation=(0, 0, 0)):
        prefix = "Left" if side == "L" else "Right"
        arm, fore, hand = (rig.pose.bones[prefix + n] for n in ("Arm", "ForeArm", "Hand"))
        shoulder = arm.head.copy()
        target = Vector(target)
        pole = Vector(((-.45 if side == "L" else .45), .20, -.60))
        l1, l2 = rig.data.bones[prefix + "Arm"].length, rig.data.bones[prefix + "ForeArm"].length
        delta = target - shoulder
        dist = clamp(delta.length, abs(l1 - l2) + 1e-5, l1 + l2 - 1e-5)
        axis = delta.normalized()
        sv = pole - shoulder
        sv -= axis * sv.dot(axis)
        sv.normalize()
        along = (l1 * l1 - l2 * l2 + dist * dist) / (2 * dist)
        height = math.sqrt(max(0, l1 * l1 - along * along))
        elbow = shoulder + axis * along + sv * height
        set_world_delta(arm, elbow - shoulder)
        set_world_delta(fore, shoulder + axis * dist - fore.head)
        q = REST[prefix + "Hand"].to_quaternion()
        for ax, angle in zip([(1, 0, 0), (0, 1, 0), (0, 0, 1)], rotation):
            q = q @ Quaternion(ax, math.radians(angle))
        m = q.to_matrix().to_4x4()
        m.translation = hand.head
        hand.matrix = m
        bpy.context.view_layer.update()

    POSES = {
        "relaxed": [[4, 8, 6], [12, 14, 8], [14, 16, 10], [16, 18, 10], [18, 20, 10]],
        "grip": [[6, 12, 14], [30, 38, 24], [36, 42, 27], [40, 45, 28], [44, 48, 28]],
        "fist": [[12, 15, 20], [55, 65, 40], [57, 65, 42], [60, 65, 40], [63, 65, 40]],
        "point": [[6, 10, 12], [-6, -8, -4], [50, 60, 38], [55, 60, 38], [58, 60, 38]],
        "open": [[-8, -8, -4], [-8, -10, -6], [-8, -12, -8], [-8, -12, -8], [-8, -12, -8]],
    }

    def fingers(side, pose):
        prefix = "Left" if side == "L" else "Right"
        for fn, angles in zip(FINGERS, POSES[pose]):
            for j, a in enumerate(angles, 1):
                rig.pose.bones[prefix + "Hand" + fn + str(j)].rotation_quaternion = Quaternion((1, 0, 0), math.radians(a))

    sc.render.engine = "BLENDER_EEVEE" if "BLENDER_EEVEE" in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items] else "BLENDER_EEVEE_NEXT"
    sc.world = bpy.data.worlds.new("w")
    sc.world.use_nodes = True
    sc.world.node_tree.nodes["Background"].inputs[0].default_value = (.32, .34, .36, 1)
    sc.world.node_tree.nodes["Background"].inputs[1].default_value = 0.6
    sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
    sun.data.energy = 3.2
    sun.rotation_euler = (math.radians(55), math.radians(-20), math.radians(30))
    sc.collection.objects.link(sun)
    cam = bpy.data.objects.new("FP_Camera", bpy.data.cameras.new("FP_Camera"))
    sc.collection.objects.link(cam)
    cam.rotation_euler = (math.pi / 2, 0, 0)
    cam.data.sensor_fit = "VERTICAL"
    cam.data.angle = math.radians(70)
    cam.data.clip_start = 0.03
    sc.camera = cam
    sc.render.resolution_x, sc.render.resolution_y = 540, 960
    shots = {
        "one_hand_relaxed": [("R", (0.07, 0.40, -0.24), (0, 0, -10), "relaxed")],
        "wheel_grip": [("L", (-0.15, 0.42, -0.20), (0, 0, 0), "grip"), ("R", (0.15, 0.42, -0.20), (0, 0, 0), "grip")],
        "fist": [("R", (0.05, 0.40, -0.20), (0, 0, 0), "fist")],
        "point": [("R", (0.06, 0.42, -0.16), (0, 0, 0), "point")],
        "reach_up_open": [("L", (-0.04, 0.42, 0.02), (0, 0, 0), "open")],
    }
    for name, hands in shots.items():
        reset_pose()
        for side, target, rot, pose in hands:
            ik(side, target, rot)
            fingers(side, pose)
        bpy.context.view_layer.update()
        sc.render.filepath = str(WORK / f"preview_{name}.png")
        bpy.ops.render.render(write_still=True)
        print("PREVIEW", name)
