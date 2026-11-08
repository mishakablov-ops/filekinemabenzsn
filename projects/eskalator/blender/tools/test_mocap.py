"""Проверка мокапа: ведущий проигрывает клип, стоп-кадры спереди.
blender -b --python tools/test_mocap.py -- <assets dir> <action name> <out dir> [t1,t2,...]"""
import bpy, sys, os, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'sets'))
import esk_hero as H, esk_mocap as MC, esk_studio as S
argv = sys.argv[sys.argv.index('--') + 1:]
assets, act_name, out = argv[:3]
times = [float(x) for x in (argv[3] if len(argv) > 3 else '0.2,1.0,2.0,3.0').split(',')]
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.fps = 30; sc.frame_start = 1; sc.frame_end = 400
rig, col = H.load_hero(os.path.join(assets, 'hero.blend'), sc)
MC.load_actions(os.path.join(assets, 'mocap', 'mocap.blend'))
act = MC._ACTS[act_name]
H.relax_hands(rig)
MC.play(rig, act, offset=0)
S.render_setup('EEVEE', w=1080, h=1920, pct=40, samples=16)
S.world('#DDE3EA', 1.0)
fl = bpy.data.meshes.new('floor'); import bmesh
bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=6); bm.to_mesh(fl); bm.free()
fo = bpy.data.objects.new('floor', fl); sc.collection.objects.link(fo)
cam = S.camera((1.2, -3.6, 1.2), (0, 0, 0.9), lens=35, name='Cam')
sc.camera = cam
sun = bpy.data.lights.new('sun', 'SUN'); sun.energy = 3
so = bpy.data.objects.new('sun', sun); so.rotation_euler = (0.8, 0.2, 0.6); sc.collection.objects.link(so)
os.makedirs(out, exist_ok=True)
for t in times:
    f = 1 + int(round(t * 30))
    sc.frame_set(f)
    sc.render.filepath = os.path.join(out, '%s_%04d.jpg' % (act_name, f))
    sc.render.image_settings.file_format = 'JPEG'
    bpy.ops.render.render(write_still=True)
print('TEST_DONE')
