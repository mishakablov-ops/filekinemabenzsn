# blender -b --factory-startup --disable-autoexec --python analyze_islands.py -- <source/scene.gltf>
# Prints UV islands of the source arms (metres, Codex frame: hands towards +Y) with position along the arm and texture colour.
import sys

import bmesh
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
for v in o.data.vertices:
    v.co *= 0.01
    v.co.x *= -1
    v.co.y *= -1
img = [n.image for n in o.active_material.node_tree.nodes if n.type == "TEX_IMAGE" and "baseColor" in n.image.name][0]
W, H = img.size
px = list(img.pixels)


def sample(uv):
    x = min(W - 1, max(0, int(uv.x * W)))
    y = min(H - 1, max(0, int(uv.y * H)))
    i = (y * W + x) * 4
    return px[i:i + 3]


bm = bmesh.new()
bm.from_mesh(o.data)
uv = bm.loops.layers.uv.active
bm.faces.ensure_lookup_table()
# UV islands: faces connected through edges whose UVs match on both sides
seen, islands = set(), []
for f in bm.faces:
    if f.index in seen:
        continue
    stack, isl = [f], []
    seen.add(f.index)
    while stack:
        g = stack.pop()
        isl.append(g)
        for e in g.edges:
            for h in e.link_faces:
                if h.index in seen:
                    continue
                ok = True
                for v in e.verts:
                    a = [l[uv].uv for l in g.loops if l.vert == v][0]
                    b = [l[uv].uv for l in h.loops if l.vert == v][0]
                    if (a - b).length > 1e-4:
                        ok = False
                if ok:
                    seen.add(h.index)
                    stack.append(h)
    islands.append(isl)
print("ISLANDS", len(islands), "faces", len(bm.faces))
rows = []
for k, isl in enumerate(islands):
    ys = [v.co.y for f in isl for v in f.verts]
    xs = [v.co.x for f in isl for v in f.verts]
    cols = [sample(sum((l[uv].uv for l in f.loops), Vector((0, 0))) / len(f.loops)) for f in isl]
    c = [sum(cc[i] for cc in cols) / len(cols) for i in range(3)]
    uvs = [l[uv].uv for f in isl for l in f.loops]
    rows.append((min(ys), max(ys), len(isl), "L" if sum(xs) < 0 else "R", c,
                 (min(u.x for u in uvs), min(u.y for u in uvs), max(u.x for u in uvs), max(u.y for u in uvs))))
for r in sorted(rows, key=lambda r: (r[3], r[0])):
    print(f"{r[3]} y {r[0]:+.3f}..{r[1]:+.3f} faces {r[2]:4d} rgb {r[4][0]:.2f} {r[4][1]:.2f} {r[4][2]:.2f} uv {r[5][0]:.2f},{r[5][1]:.2f}-{r[5][2]:.2f},{r[5][3]:.2f}")
