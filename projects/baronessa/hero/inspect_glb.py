"""blender -b --factory-startup --python inspect_glb.py -- <glb> <out.jpg>: prints bounds and renders front/side views."""
import sys, math
import bpy
from mathutils import Vector

glb, out = sys.argv[sys.argv.index('--') + 1:][:2]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
for o in bpy.context.scene.objects:
    print('OBJ', o.name, o.type, tuple(round(v, 3) for v in o.location), tuple(round(v, 3) for v in o.rotation_euler),
          tuple(round(v, 3) for v in o.scale), 'parent', o.parent.name if o.parent else None)
pts = [o.matrix_world @ v.co for o in meshes for v in o.data.vertices]
lo = Vector([min(p[i] for p in pts) for i in range(3)])
hi = Vector([max(p[i] for p in pts) for i in range(3)])
print('VERTS', len(pts), 'LO', tuple(round(v, 3) for v in lo), 'HI', tuple(round(v, 3) for v in hi))
for o in meshes:
    print('MATS', o.name, [m.name for m in o.data.materials], 'uv', len(o.data.uv_layers))
# horizontal slices: width in x per height band
H = hi.z - lo.z
for k in range(20):
    z0 = lo.z + H * k / 20
    band = [p for p in pts if z0 <= p.z < z0 + H / 20]
    if band:
        print(f'BAND {k/20:.2f} x[{min(p.x for p in band):.3f},{max(p.x for p in band):.3f}] '
              f'y[{min(p.y for p in band):.3f},{max(p.y for p in band):.3f}] n={len(band)}')
sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE_NEXT'
sc.render.resolution_x, sc.render.resolution_y = 900, 900
w = bpy.data.worlds.new('W'); sc.world = w; w.color = (0.6, 0.6, 0.6)
ctr = (lo + hi) / 2
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = max(hi.x - lo.x, H) * 1.1
sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sc.collection.objects.link(sun)
sun.data.energy = 3; sun.rotation_euler = (math.radians(50), 0, math.radians(20))
for tag, loc, rot in (('front', (ctr.x, lo.y - 5, ctr.z), (math.radians(90), 0, 0)),
                      ('side', (hi.x + 5, ctr.y, ctr.z), (math.radians(90), 0, math.radians(90)))):
    cam.location, cam.rotation_euler = loc, rot
    sc.render.filepath = out.replace('.jpg', f'_{tag}.jpg')
    sc.render.image_settings.file_format = 'JPEG'
    bpy.ops.render.render(write_still=True)
