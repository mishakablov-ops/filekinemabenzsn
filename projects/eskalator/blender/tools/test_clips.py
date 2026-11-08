"""Смотр всех клипов одного вида на ведущем: по кадру на клип (спереди-сбоку), чтобы отсеять странные позы.
blender -b --python tools/test_clips.py -- <assets dir> <out dir> <kind> [секунда=2.0]"""
import bpy, sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'sets'))
import esk_hero as H, esk_mocap as MC, esk_studio as S
argv = sys.argv[sys.argv.index('--') + 1:]
assets, out, kind = argv[:3]
t = float(argv[3]) if len(argv) > 3 else 2.0
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.fps = 30; sc.frame_start = 1; sc.frame_end = 400
rig, col = H.load_hero(os.path.join(assets, 'hero.blend'), sc)
MC.load_actions(os.path.join(assets, 'mocap', 'mocap.blend'))
H.relax_hands(rig)
S.render_setup('EEVEE', w=1080, h=1920, pct=30, samples=8)
S.world('#DDE3EA', 1.0)
cam = S.camera((1.6, -3.4, 1.0), (0, 0, 0.85), lens=45, name='Cam')
sun = bpy.data.lights.new('sun', 'SUN'); sun.energy = 3
so = bpy.data.objects.new('sun', sun); so.rotation_euler = (0.8, 0.2, 0.6); sc.collection.objects.link(so)
os.makedirs(out, exist_ok=True)
sc.render.image_settings.file_format = 'JPEG'
for act in MC.by_kind(kind):
    ad = rig.animation_data_create()
    for tr in list(ad.nla_tracks):
        ad.nla_tracks.remove(tr)
    MC.play(rig, act, offset=0)
    sc.frame_set(1 + int(round(t * 30)))
    if kind == 'walk':                                   # прохожий уходит: камера за тазом
        hip = rig.matrix_world @ rig.pose.bones['root'].head
        cam.location = (hip.x + 1.6, hip.y - 3.4, 1.0)
    sc.render.filepath = os.path.join(out, act.name + '.jpg')
    bpy.ops.render.render(write_still=True)
print('CLIPS_DONE')
