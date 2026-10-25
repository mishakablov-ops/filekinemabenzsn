# blender -b --factory-startup --disable-autoexec --python jeep_build.py -- <scene.gltf> <clean_basecolor.png> <out_dir>
# Willys jeep -> jeep_kpa.glb: glass removed, 3.33 m long, faces -Y in Blender (+Z in three.js), origin on the ground centre,
# separate steering_wheel (pivot = hub; rotates around local Z in Blender = local Y in three.js) and
# wheel_FL/FR/RL/RR (pivot = hub, spin around local X), empties DRIVER_EYE, GRIP_L, GRIP_R.
import json
import math
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

_a = sys.argv[sys.argv.index("--") + 1:]
src, tex, out = _a[:3]
mr_tex = _a[3] if len(_a) > 3 else None  # cleaned metallicRoughness (the star was glossy there)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
for o in [o for o in bpy.context.scene.objects if o.type == "MESH"]:
    if any(s.material and "Glass" in s.material.name for s in o.material_slots):
        bpy.data.objects.remove(o, do_unlink=True)
meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
for o in meshes:
    m = o.matrix_world.copy()
    o.parent = None
    o.matrix_world = m
for o in [o for o in bpy.context.scene.objects if o.type != "MESH"]:
    bpy.data.objects.remove(o, do_unlink=True)
bpy.ops.object.select_all(action="DESELECT")
for o in meshes:
    o.select_set(True)
bpy.context.view_layer.objects.active = meshes[0]
if len(meshes) > 1:
    bpy.ops.object.join()
body = bpy.context.view_layer.objects.active
body.name = "body"
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
me = body.data
xs = [v.co.x for v in me.vertices]
me.transform(Matrix.Scale(3.33 / (max(xs) - min(xs)), 4))
co = [v.co for v in me.vertices]
mn = Vector((min(c.x for c in co), min(c.y for c in co), min(c.z for c in co)))
mx = Vector((max(c.x for c in co), max(c.y for c in co), max(c.z for c in co)))
me.transform(Matrix.Translation(-Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z))))

# ---- in this frame: front = +X, driver (left) = +Y. A part = loose piece fully inside a box.
WX = {"F": 1.12, "R": -0.90}
WY = {"L": (0.38, 0.82), "R": (-0.82, -0.38)}
SW_C = Vector((0.01, 0.26, 1.21))


def box_for(name):
    if name == "steering_wheel":
        return SW_C - Vector((0.2, 0.26, 0.2)), SW_C + Vector((0.2, 0.26, 0.2))
    x = WX[name[6]]
    y0, y1 = WY[name[7]]
    return Vector((x - 0.43, y0, -0.01)), Vector((x + 0.43, y1, 0.82))


def loose_groups(mesh):
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.verts.ensure_lookup_table()
    par = list(range(len(bm.verts)))

    def f(i):
        while par[i] != i:
            par[i] = par[par[i]]
            i = par[i]
        return i
    for e in bm.edges:
        a, b = f(e.verts[0].index), f(e.verts[1].index)
        if a != b:
            par[a] = b
    groups = {}
    for v in bm.verts:
        groups.setdefault(f(v.index), []).append(v.index)
    cos = [v.co.copy() for v in bm.verts]
    bm.free()
    return list(groups.values()), cos


def split(name):
    lo, hi = box_for(name)
    groups, cos = loose_groups(body.data)
    idx = [j for g in groups if all(lo[i] <= cos[j][i] <= hi[i] for j in g for i in range(3)) for j in g]
    print("PART", name, len(idx), "verts")
    bpy.ops.object.select_all(action="DESELECT")
    body.select_set(True)
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="DESELECT")
    bpy.ops.object.mode_set(mode="OBJECT")
    for j in idx:
        body.data.vertices[j].select = True
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.separate(type="SELECTED")
    bpy.ops.object.mode_set(mode="OBJECT")
    new = [o for o in bpy.context.selected_objects if o is not body][0]
    new.name = new.data.name = name
    return new


parts = {n: split(n) for n in ["steering_wheel", "wheel_FL", "wheel_FR", "wheel_RL", "wheel_RR"]}

# ---- turn the jeep: front +X -> -Y (Blender) == +Z (glTF / three.js); driver side ends up at +X
R = Matrix.Rotation(-math.pi / 2, 4, "Z")
for o in [body, *parts.values()]:
    o.data.transform(R)


def set_origin(o, M):  # geometry stays where it is, object matrix becomes M
    o.data.transform(M.inverted())
    o.matrix_world = M


def bbox_center(o):
    c = [v.co for v in o.data.vertices]
    return Vector(tuple((min(p[i] for p in c) + max(p[i] for p in c)) / 2 for i in range(3)))


for n in ["wheel_FL", "wheel_FR", "wheel_RL", "wheel_RR"]:
    set_origin(parts[n], Matrix.Translation(bbox_center(parts[n])))

sw = parts["steering_wheel"]
pts = [v.co.copy() for v in sw.data.vertices]
ctr = bbox_center(sw)
cov = [[0.0] * 3 for _ in range(3)]
for p in pts:
    d = p - ctr
    for i in range(3):
        for j in range(3):
            cov[i][j] += d[i] * d[j]
best, n = None, None
for t in range(0, 181, 2):  # ring normal = direction of least spread
    for u in range(0, 360, 2):
        c = Vector((math.sin(math.radians(t)) * math.cos(math.radians(u)),
                    math.sin(math.radians(t)) * math.sin(math.radians(u)), math.cos(math.radians(t))))
        var = sum(c[i] * cov[i][j] * c[j] for i in range(3) for j in range(3))
        if best is None or var < best:
            best, n = var, c
if n.y > 0:  # driver sits behind the wheel, i.e. towards +Y (the jeep faces -Y)
    n = -n
n = -n if n.y < 0 and False else n
# the normal must point from the wheel to the driver (+Y side, i.e. backwards)
if n.y < 0:
    n = -n
up = (Vector((0, 0, 1)) - n * n.z).normalized()
right = up.cross(n).normalized()
set_origin(sw, Matrix.Translation(ctr) @ Matrix((right, up, n)).transposed().to_4x4())
radius = max(((p - ctr) - n * (p - ctr).dot(n)).length for p in pts)


def empty(name, loc):
    e = bpy.data.objects.new(name, None)
    e.empty_display_size = 0.05
    e.location = loc
    bpy.context.scene.collection.objects.link(e)


grip = lambda deg: ctr + radius * 0.9 * (math.cos(math.radians(deg)) * right + math.sin(math.radians(deg)) * up)
empty("GRIP_L", grip(150))
empty("GRIP_R", grip(30))
eye = ctr + n * 0.6
eye.z = 1.52
empty("DRIVER_EYE", eye)

clean = bpy.data.images.load(tex)
clean.name = "jeep_baseColor_clean"
for mat in bpy.data.materials:
    for node in (mat.node_tree.nodes if mat.use_nodes else []):
        if node.type == "TEX_IMAGE" and node.image and "jeep.001_baseColor" in node.image.name:
            node.image = clean
            print("TEXTURE replaced in", mat.name)
        elif mr_tex and node.type == "TEX_IMAGE" and node.image and "jeep.001_metallicRoughness" in node.image.name:
            mr = bpy.data.images.load(mr_tex)
            mr.colorspace_settings.name = "Non-Color"
            node.image = mr
            print("ROUGHNESS replaced in", mat.name)
# rounder steering wheel: the source ring is octagonal, which shows in close first-person shots
mod = sw.modifiers.new("smooth", "SUBSURF")
mod.levels = mod.render_levels = 2
for p in sw.data.polygons:
    p.use_smooth = True
bpy.ops.wm.save_as_mainfile(filepath=out + "/jeep_kpa.blend")
bpy.ops.file.pack_all()
bpy.ops.wm.save_mainfile()
bpy.ops.export_scene.gltf(filepath=out + "/jeep_kpa.glb", export_format="GLB", export_image_format="JPEG",
                          export_jpeg_quality=90, export_apply=True, export_yup=True, export_cameras=False, export_lights=False)
info = {
    "length_m": 3.33, "front": "+Z in three.js", "driver_side": "+X in three.js",
    "steering_wheel": {"radius_m": round(radius, 3), "axis": "local Y in three.js (column axis, towards the driver)"},
    "wheels": "wheel_FL/FR/RL/RR: pivot = hub, spin around local X, front wheels steer around local Y",
    "empties_blender": {k: [round(v, 3) for v in bpy.data.objects[k].location] for k in ("DRIVER_EYE", "GRIP_L", "GRIP_R")},
    "verts": {o.name: len(o.data.vertices) for o in [body, *parts.values()]},
    "credit": 'This work is based on "Jeep" (https://sketchfab.com/3d-models/jeep-ae6528c1735848a99de368936413fb9b) by rajibkc (https://sketchfab.com/rajibkc) licensed under CC-BY-4.0',
}
json.dump(info, open(out + "/jeep_kpa.json", "w"), indent=1)
print("INFO", json.dumps(info))
