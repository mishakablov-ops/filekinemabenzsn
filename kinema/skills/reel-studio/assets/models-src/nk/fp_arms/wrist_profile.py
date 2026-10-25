# blender -b --factory-startup --disable-autoexec --python wrist_profile.py -- <source/scene.gltf>
# Radius of the left arm around the forearm axis, sliced along the arm (Codex frame), to see the glove-cuff bulge.
import sys

import bpy
from mathutils import Vector

src = sys.argv[sys.argv.index("--") + 1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
o = [x for x in bpy.context.scene.objects if x.type == "MESH"][0]
w = o.matrix_world.copy()
o.parent = None
o.matrix_world = w
bpy.context.view_layer.objects.active = o
o.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
A = Vector((-.212, -.005, .045))
B = Vector((-.201, .319, -.022))  # elbow -> end of the hand bone
d = (B - A).normalized()
rows = {}
for v in o.data.vertices:
    p = v.co * 0.01
    p.x *= -1
    p.y *= -1
    if p.x > 0:
        continue
    t = (p - A).dot(d)
    r = ((p - A) - d * t).length
    y = round(p.y, 3)
    if 0.15 <= p.y <= 0.30:
        k = round(p.y / 0.005) * 0.005
        rows.setdefault(k, []).append(r)
for k in sorted(rows):
    rs = sorted(rows[k])
    print(f"y {k:.3f} n {len(rs):3d} r_med {rs[len(rs)//2]*1000:5.1f} mm  r_max {rs[-1]*1000:5.1f} mm")
