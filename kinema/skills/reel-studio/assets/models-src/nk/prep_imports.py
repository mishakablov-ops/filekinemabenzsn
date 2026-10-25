# blender -b --factory-startup --disable-autoexec --python prep_imports.py -- <asset> <src.gltf> <out.glb>
# Normalises downloaded Sketchfab models for the nk-escape reel: metres, origin on the ground, textures <= 4096 JPEG,
# fewer draw calls, moving parts separated. asset: road | checkpoint | heli
import math
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

asset, src, out = sys.argv[sys.argv.index("--") + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
sc = bpy.context.scene


def bake_parents():
    for o in [o for o in sc.objects if o.type == "MESH"]:
        m = o.matrix_world.copy()
        o.parent = None
        o.matrix_world = m
    for o in [o for o in sc.objects if o.type != "MESH"]:
        bpy.data.objects.remove(o, do_unlink=True)
    bpy.ops.object.select_all(action="SELECT")
    bpy.context.view_layer.objects.active = [o for o in sc.objects][0]
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)


def join_all(name):
    objs = [o for o in sc.objects if o.type == "MESH"]
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    if len(objs) > 1:
        bpy.ops.object.join()
    o = bpy.context.view_layer.objects.active
    o.name = o.data.name = name
    return o


def scale_all(k):
    for o in [o for o in sc.objects if o.type == "MESH"]:
        o.data.transform(Matrix.Scale(k, 4))


def bounds(objs):
    """from the vertices themselves (bound_box is stale right after mesh.transform)"""
    lo = Vector((1e18, 1e18, 1e18))
    hi = Vector((-1e18, -1e18, -1e18))
    for o in objs:
        mw = o.matrix_world
        for v in o.data.vertices:
            p = mw @ v.co
            for i in range(3):
                lo[i] = min(lo[i], p[i])
                hi[i] = max(hi[i], p[i])
    return lo, hi


def to_ground_centre(objs, centre=True):
    mn, mx = bounds(objs)
    off = Vector(((mn.x + mx.x) / 2 if centre else 0, (mn.y + mx.y) / 2 if centre else 0, mn.z))
    for o in objs:
        o.data.transform(Matrix.Translation(-off))


def shrink_images(limit=4096):
    for img in bpy.data.images:
        if img.size[0] > limit or img.size[1] > limit:
            k = limit / max(img.size)
            img.scale(int(img.size[0] * k), int(img.size[1] * k))
            print("SHRUNK", img.name, tuple(img.size))


bake_parents()
if asset == "road":
    o = join_all("road_scan")
    to_ground_centre([o], centre=False)
    shrink_images(4096)
elif asset == "checkpoint":
    scale_all(100.0)
    keep = []
    for o in [o for o in sc.objects if o.type == "MESH"]:
        mn, mx = bounds([o])
        if (mn.x + mx.x) / 2 < 21.5:  # the first (intact) of three copies; the others are the same post abandoned
            keep.append(o)
        else:
            bpy.data.objects.remove(o, do_unlink=True)
    o = join_all("checkpoint")
    to_ground_centre([o])
    print("CHECKPOINT parts", len(keep))
elif asset == "heli":
    mn, mx = bounds([o for o in sc.objects if o.type == "MESH"])
    scale_all(19.76 / (mx.x - mn.x))
    objs = [o for o in sc.objects if o.type == "MESH"]
    to_ground_centre(objs)
    # every mesh -> loose parts; main rotor = long pieces at the very top; tail rotor = blade pieces at the tail end (-X)
    hmn, hmx = bounds(objs)
    parts = []
    for o in objs:
        bpy.ops.object.select_all(action="DESELECT")
        o.select_set(True)
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.mesh.separate(type="LOOSE")
        bpy.ops.object.mode_set(mode="OBJECT")
        parts += [p for p in bpy.context.selected_objects if p.type == "MESH"]
    top, tail = [], []
    for p in parts:
        if not any(s.material and "RotBlade" in s.material.name for s in p.material_slots):
            continue
        lo, hi = bounds([p])
        (tail if (lo.x + hi.x) / 2 < hmn.x + (hmx.x - hmn.x) * 0.15 else top).append(p)  # the tail rotor sits at -X
    print("ROTOR PARTS main", len(top), "tail", len(tail), "of", len(parts))
    body = [p for p in parts if p not in top and p not in tail]
    rotors = {}
    if True:
        for name, group in (("main_rotor", top), ("tail_rotor", tail)):
            if not group:
                continue
            bpy.ops.object.select_all(action="DESELECT")
            for p in group:
                p.select_set(True)
            bpy.context.view_layer.objects.active = group[0]
            if len(group) > 1:
                bpy.ops.object.join()
            r = bpy.context.view_layer.objects.active
            r.name = r.data.name = name
            gmn, gmx = bounds([r])
            c = (gmn + gmx) / 2
            r.data.transform(Matrix.Translation(-c))
            r.location = c
            rotors[name] = [round(v, 3) for v in c]
    bpy.ops.object.select_all(action="DESELECT")
    for o in body:
        o.select_set(True)
    bpy.context.view_layer.objects.active = body[0]
    bpy.ops.object.join()
    bpy.context.view_layer.objects.active.name = "heli_body"
    print("ROTORS", rotors)
    shrink_images(2048)
mn, mx = bounds([o for o in sc.objects if o.type == "MESH"])
tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in sc.objects if o.type == "MESH")
print("RESULT", asset, "size", [round(v, 2) for v in (mx - mn)], "tris", tris, "objects", [o.name for o in sc.objects][:8])
bpy.ops.export_scene.gltf(filepath=out, export_format="GLB", export_image_format="JPEG", export_jpeg_quality=88, export_apply=True, export_yup=True)
