"""Entry point:  blender -b --factory-startup --python build.py -- --shot sh01 [--frames 1,90] [--anim] [--scale 0.5]

Builds the shot's set from scratch, saves blender/files/<shot>.blend, renders stills or the animation (JPEG sequence).
"""
import sys, os, json, time, argparse, importlib, traceback
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, 'sets'))
import bpy
import lib

def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument('--shot', required=True)
    ap.add_argument('--shots', default=os.path.join(HERE, 'shots.json'))
    ap.add_argument('--frames', default='')
    ap.add_argument('--times', default='', help='comma list of seconds (stills)')
    ap.add_argument('--anim', action='store_true')
    ap.add_argument('--scale', type=float, default=1.0)
    ap.add_argument('--samples', type=int, default=0)
    ap.add_argument('--out', default=os.path.join(lib.PROJ, 'renders'))
    ap.add_argument('--nosave', action='store_true')
    a = ap.parse_args(argv)
    shots = json.load(open(a.shots, encoding='utf-8'))
    shot = next(s for s in shots['shots'] if s['id'] == a.shot)
    fps = shots.get('fps', 60)
    lib.FPS = fps
    t0 = time.time()
    lib.reset()
    mod = importlib.import_module(shot['set'])
    opts = dict(samples=48)
    lib.setup_render(shot['dur'], samples=48, scale=a.scale, fps=fps, **shot.get('render', {}))
    res = mod.build(shot, fps) or {}
    opts.update(res)
    fill = shot.get('fill', opts.get('fill', 0.9))
    if fill:
        lib.camera_fill(fill)
    bpy.context.scene.view_settings.exposure = shot.get('exposure', opts.get('exposure', 0.35))
    sc = bpy.context.scene
    sc.eevee.taa_render_samples = a.samples or shot.get('samples', opts.get('samples', 48))
    if 'vol_samples' in shot:
        sc.eevee.volumetric_samples = shot['vol_samples']
    sc.frame_end = max(sc.frame_start, int(round(shot['dur'] * fps)))
    print(f'BUILD {a.shot} set={shot["set"]} frames={sc.frame_end} built in {time.time() - t0:.1f}s', flush=True)
    if not a.nosave:
        lib.save_blend(os.path.join(lib.PROJ, 'blender', 'files', a.shot + '.blend'))
    if a.anim:
        d = os.path.join(a.out, a.shot)
        os.makedirs(d, exist_ok=True)
        sc.render.filepath = os.path.join(d, '')
        sc.render.image_settings.file_format = 'JPEG'
        t1 = time.time()
        bpy.ops.render.render(animation=True)
        n = sc.frame_end - sc.frame_start + 1
        print(f'ANIM {a.shot} {n} frames in {time.time() - t1:.1f}s', flush=True)
    else:
        frames = [int(x) for x in a.frames.split(',') if x.strip()]
        frames += [lib.sec2f(float(x)) for x in a.times.split(',') if x.strip()]
        if not frames:
            frames = [1, (sc.frame_end + 1) // 2, sc.frame_end]
        d = os.path.join(a.out, 'stills')
        os.makedirs(d, exist_ok=True)
        sc.render.use_overwrite = True
        sc.render.use_placeholder = False
        for f in frames:
            f = min(max(1, f), sc.frame_end)
            sc.frame_set(f)
            sc.render.filepath = os.path.join(d, f'{a.shot}_{f:04d}.jpg')
            t1 = time.time()
            bpy.ops.render.render(write_still=True)
            print(f'STILL {a.shot} f{f} {time.time() - t1:.1f}s', flush=True)

try:
    main()
except Exception:
    traceback.print_exc()
    sys.stdout.flush()
    os._exit(3)
