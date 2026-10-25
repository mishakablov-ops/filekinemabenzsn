# blender -b --factory-startup --disable-autoexec --python export_for_mixamo.py -- <scene.gltf> <out.fbx>
# Static soldier mesh (A-pose, no armature, textures embedded, 2K) for Mixamo's auto-rigger.
import sys

import bpy

src, out = sys.argv[sys.argv.index("--") + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
sc = bpy.context.scene
for o in list(sc.objects):
    if o.type == "MESH" and o.name.startswith("Icosphere"):
        bpy.data.objects.remove(o, do_unlink=True)
meshes = [o for o in sc.objects if o.type == "MESH"]
for o in meshes:
    for m in list(o.modifiers):
        if m.type == "ARMATURE":
            bpy.context.view_layer.objects.active = o
            bpy.ops.object.modifier_apply(modifier=m.name)  # bake the rest (A) pose into the mesh
    o.vertex_groups.clear()
    w = o.matrix_world.copy()
    o.parent = None
    o.matrix_world = w
for o in list(sc.objects):
    if o.type != "MESH":
        bpy.data.objects.remove(o, do_unlink=True)
bpy.ops.object.select_all(action="SELECT")
bpy.context.view_layer.objects.active = meshes[0]
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
for img in bpy.data.images:
    if max(img.size) > 2048:
        img.scale(2048, 2048)
    img.pack()
bpy.ops.export_scene.fbx(filepath=out, use_selection=True, path_mode="COPY", embed_textures=True, apply_unit_scale=True,
                         axis_forward="-Z", axis_up="Y", add_leaf_bones=False, mesh_smooth_type="FACE")
print("FBX", out)
