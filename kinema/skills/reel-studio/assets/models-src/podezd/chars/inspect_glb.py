# blender -b --factory-startup --disable-autoexec --python inspect_glb.py -- <in.glb> <out.png>
# Stats + a 4-view turnaround render (front, side, back, 3/4) of a generated character.
import math
import sys

import bpy
from mathutils import Vector

src, out = sys.argv[sys.argv.index("--") + 1:][:2]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
meshes = [o for o in bpy.data.objects if o.type == "MESH"]
pts = [o.matrix_world @ v.co for o in meshes for v in o.data.vertices]
lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
print("MESHES", [(o.name, len(o.data.vertices), len(o.data.polygons), [m.name for m in o.data.materials]) for o in meshes])
print("BOUNDS", tuple(round(v, 3) for v in lo), tuple(round(v, 3) for v in hi))
for m in bpy.data.materials:
    imgs = [n.image.name + f" {n.image.size[0]}x{n.image.size[1]}" for n in (m.node_tree.nodes if m.use_nodes else []) if n.type == "TEX_IMAGE" and n.image]
    print("MAT", m.name, imgs)
for o in meshes:
    bpy.context.view_layer.objects.active = o
    o.select_set(True)
    me = o.data
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(me)
    nm = sum(1 for e in bm.edges if not e.is_manifold)
    print("NONMANIFOLD_EDGES", o.name, nm, "loose parts?")
    bm.free()

sc = bpy.context.scene
sc.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items.keys() else "BLENDER_EEVEE"
sc.render.resolution_x, sc.render.resolution_y = 1600, 1000
sc.world = bpy.data.worlds.new("w")
sc.world.color = (0.5, 0.5, 0.52)
ctr = (lo + hi) / 2
H = hi.z - lo.z
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
sun.data.energy = 3
sun.rotation_euler = (0.8, 0.2, 0.6)
sc.collection.objects.link(sun)
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
cam.data.type = "ORTHO"
sc.collection.objects.link(cam)
sc.camera = cam
# four copies side by side (front, right, back, 3/4)
base = meshes
offs = []
for k, rz in enumerate([0, math.pi / 2, math.pi, math.pi / 4]):
    if k == 0:
        grp = base
    else:
        grp = []
        for o in base:
            c = o.copy()
            c.data = o.data
            sc.collection.objects.link(c)
            grp.append(c)
    for o in grp:
        o.rotation_mode = "XYZ"
        o.rotation_euler.z += rz
        o.location.x += (k - 1.5) * (H * 0.55) - ctr.x
cam.data.ortho_scale = max(4 * H * 0.55, H * 1.6) * 1.05
cam.location = (0, -10, ctr.z)
cam.rotation_euler = (math.pi / 2, 0, 0)
sc.render.filepath = out
bpy.ops.render.render(write_still=True)
print("RENDERED", out)
