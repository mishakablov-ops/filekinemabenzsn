"""Convert a .blend (e.g. a BlenderKit download) to .glb for the Model3D block.

    "C:/Program Files (x86)/Steam/steamapps/common/Blender/blender.exe" -b model.blend --python blend2glb.py -- out.glb [--decimate 0.5]

Also writes out.json with mesh names (pick the display mesh for `screenMesh`) and sizes.
Applies modifiers, keeps materials (Principled BSDF -> glTF PBR). Procedural node textures that glTF
cannot express are lost: bake them in Blender first if the model looks flat.
"""
import json
import sys

import bpy

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
out = argv[0] if argv else bpy.data.filepath.replace(".blend", ".glb")
dec = float(argv[argv.index("--decimate") + 1]) if "--decimate" in argv else 1.0

if dec < 1.0:
    for o in bpy.data.objects:
        if o.type == "MESH" and len(o.data.polygons) > 20000:
            m = o.modifiers.new("decimate", "DECIMATE")
            m.ratio = dec

meshes = [{"name": o.name, "polys": len(o.data.polygons), "dims": [round(v, 3) for v in o.dimensions]}
          for o in bpy.data.objects if o.type == "MESH"]
bpy.ops.export_scene.gltf(filepath=out, export_format="GLB", export_apply=True, export_yup=True, export_animations=True)
with open(out.rsplit(".", 1)[0] + ".json", "w", encoding="utf-8") as f:
    json.dump({"file": out, "meshes": sorted(meshes, key=lambda m: -m["polys"])}, f, ensure_ascii=False, indent=1)
print("exported", out, "meshes:", len(meshes))
