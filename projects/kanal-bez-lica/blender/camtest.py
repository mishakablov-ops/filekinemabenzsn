"""Camera trials for one shot from ONE build (25.11, mike: «голова гг закрывает основной вид картинки»):
    blender -b --factory-startup --python camtest.py -- --shot k05 --out DIR --cams cams.json [--t 0.5] [--samples 16]

cams.json: {"<shot>": {"<tag>": {"lens": 30, "loc": [[0, [x, y, z]], [1, [x, y, z]]], "tgt": [[0, [x, y, z]], [1, [x, y, z]]]}}}
Times are fractions of the shot, coordinates are room coordinates (the same as in sets/kanal.py, before city_view moves
the room into «Метрополис»). Each tag -> DIR/<shot>_<tag>.jpg; tag "orig" keeps the shot's own camera.
"""
import sys, os, json, time, argparse, importlib, traceback
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, 'sets'))
for _p in (('..', '..', '..', 'blender', 'kit', 'blender'), ('..', '..', '..', 'blender', 'library')):
    sys.path.append(os.path.normpath(os.path.join(HERE, *_p)))
import bpy
import lib


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument('--shot', required=True)
    ap.add_argument('--shots', default=os.path.join(HERE, 'shots.json'))
    ap.add_argument('--cams', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--t', default='0.5')
    ap.add_argument('--samples', type=int, default=16)
    ap.add_argument('--scale', type=float, default=0.5)
    a = ap.parse_args(argv)
    shots = json.load(open(a.shots, encoding='utf-8'))
    shot = next(s for s in shots['shots'] if s['id'] == a.shot)
    cams = json.load(open(a.cams, encoding='utf-8')).get(a.shot, {})
    fps = 30
    lib.FPS = fps
    t0 = time.time()
    lib.reset()
    mod = importlib.import_module(shot['set'])
    lib.setup_render(shot['dur'], samples=16, scale=a.scale, fps=fps, **shot.get('render', {}))
    res = mod.build(shot, fps) or {}
    sc = bpy.context.scene
    sc.view_settings.exposure = shot.get('exposure', res.get('exposure', 0.1))
    sc.eevee.taa_render_samples = a.samples
    sc.frame_end = max(sc.frame_start, int(round(shot['dur'] * fps)))
    if 'sila_hero' in sys.modules:
        sys.modules['sila_hero'].alive_all(sc, seed=sum(map(ord, a.shot)))
    print(f'BUILD {a.shot} in {time.time() - t0:.1f}s', flush=True)
    cam = sc.camera
    orig = dict(lens=cam.data.lens)
    fill = shot.get('fill', res.get('fill', 0.6))
    os.makedirs(a.out, exist_ok=True)
    r = sc.render
    r.image_settings.file_format = 'JPEG'
    r.image_settings.quality = 88
    dur = shot['dur']
    for tag, spec in [('orig', None)] + list(cams.items()):
        if spec:
            cam.animation_data_clear()
            cam.data.lens = spec.get('lens', orig['lens'])
            loc = [(dur * t, tuple(p)) for t, p in spec['loc']]
            tgt = [(dur * t, tuple(p)) for t, p in spec['tgt']]
            cam.location = loc[0][1]
            lib.look_at(cam, tgt[0][1])
            lib.animate_camera(cam, loc, tgt)
        for o in [o for o in bpy.data.objects if o.name.startswith('CamFill')]:
            bpy.data.objects.remove(o, do_unlink=True)
        if fill:
            lib.camera_fill(fill, color=res.get('fill_col', '#FFF4EA'))
        for tt in [float(x) for x in a.t.split(',')]:
            f = min(max(1, int(round(1 + tt * (sc.frame_end - 1)))), sc.frame_end)
            sc.frame_set(f)
            r.filepath = os.path.join(a.out, f'{a.shot}_{tag}_t{int(round(tt * 100)):02d}.jpg')
            t1 = time.time()
            bpy.ops.render.render(write_still=True)
            print(f'CAM {a.shot} {tag} f{f} {time.time() - t1:.1f}s', flush=True)


try:
    main()
except Exception:
    traceback.print_exc()
    sys.stdout.flush()
    os._exit(3)
