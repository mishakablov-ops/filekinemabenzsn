"""Build and render one shot of «Эскалатор».

blender -b --python build_shot.py -- <SHOT> [--dur 3.0] [--pct 100] [--samples 64] [--still 0.5,1.5] [--out DIR]
                                            [--engine CYCLES|EEVEE] [--blend] [--look 0] [--tex DIR] [--whip 0]
Frames -> <out>/<SHOT>/####.jpg (resumable), stills -> <out>/stills/<SHOT>_<t>.jpg
Shot durations come from shots.json next to this file (written from the voice timings) unless --dur is given.
"""
import bpy, sys, os, json, math, importlib, time
T0 = time.time()
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, 'sets'))
import esk_mech as E, esk_studio as S, esk_metro as MT
import esk_shots as SH

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
shot = argv[0]
def opt(name, default=None, cast=str):
    if name in argv:
        return cast(argv[argv.index(name) + 1])
    return default
pct = opt('--pct', 100, int)
samples = opt('--samples', 64, int)
engine = opt('--engine', 'CYCLES')
out = opt('--out', os.path.join(HERE, '..', 'render'))
stills = opt('--still', None)
fps = 30
shots = {}
sj = os.path.join(HERE, 'shots.json')
if os.path.exists(sj):
    shots = {s['id']: s for s in json.load(open(sj, encoding='utf-8'))['shots']}
dur = opt('--dur', shots.get(shot, {}).get('dur', 3.0), float)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.fps = fps
sc.frame_start = 1
sc.frame_end = max(2, int(round(dur * fps)))
info = getattr(SH, shot)(sc, dur, fps, shots.get(shot, {}))
print('ESK_T scene %.1fs' % (time.time() - T0))
S.render_setup(engine, pct=pct, samples=samples, fps=fps)
# живые люди дорого пересчитывать на каждом frame_set: пока считаем камеру, их коллекция выключена
people = sc.view_layers[0].layer_collection.children.get('People')
if os.environ.get('ESK_LOD', '1') != '0':
    print('ESK_LOD', SH.lod_people(sc, people))
if people:
    people.exclude = True
if opt('--whip', '1') != '0' and os.path.exists(sj):   # переходы как в образце: рывок камеры со смазом (sets/esk_whip.py)
    import esk_whip as WH
    print('ESK_WHIP', WH.apply(sc, shot, json.load(open(sj, encoding='utf-8'))['shots'], fps))
if people:
    people.exclude = False
print('ESK_T cam %.1fs' % (time.time() - T0))
if opt('--look', '1') != '0':      # «без пластика»: фото-текстуры, кожа с SSS, фаски (sets/esk_look.py)
    import esk_look as LK
    LK.apply(sc, opt('--tex', LK.TEX_DIR))
    print('ESK_T look %.1fs' % (time.time() - T0))
if engine == 'CYCLES':
    prefs = bpy.context.preferences.addons['cycles'].preferences
    for dt in ('OPTIX', 'CUDA'):
        try:
            prefs.compute_device_type = dt; prefs.get_devices()
            for d in prefs.devices: d.use = d.type == dt
            sc.cycles.device = 'GPU'; break
        except Exception:
            continue
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.max_bounces = 6
    sc.render.use_persistent_data = True
sc.render.use_motion_blur = True
sc.render.motion_blur_shutter = 0.5
sc.render.image_settings.file_format = 'JPEG'
sc.render.image_settings.quality = 92
if '--blend' in argv:
    os.makedirs(os.path.join(out, 'blend'), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out, 'blend', shot + '.blend'), compress=True)
if stills:
    os.makedirs(os.path.join(out, 'stills'), exist_ok=True)
    for t in [float(x) for x in stills.split(',')]:
        f = min(sc.frame_end, 1 + int(round(t * fps)))
        sc.frame_set(f)
        sc.render.filepath = os.path.join(out, 'stills', f'{shot}_{t:.1f}.jpg')
        bpy.ops.render.render(write_still=True)
        print('ESK_T still %.1f %.1fs' % (t, time.time() - T0))
else:
    d = os.path.join(out, 'frames', shot)
    os.makedirs(d, exist_ok=True)
    rg = opt('--range', None)                  # проверка: только кадры a,b
    if rg:
        sc.frame_start, sc.frame_end = [int(x) for x in rg.split(',')]
    sc.render.filepath = os.path.join(d, '####')
    sc.render.use_overwrite = False
    sc.render.use_placeholder = True
    bpy.ops.render.render(animation=True)
    print('ESK_T anim %.1fs' % (time.time() - T0))
print('SHOT_DONE', shot, sc.frame_end)
