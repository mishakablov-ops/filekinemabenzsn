"""Entry point for the permanent city «Метрополис» (projects/metro-city): renders the named spots of the city.
    blender -b --factory-startup --python build_pc.py -- --shot skyline_dusk --still DIR [--scale 1.0]
    blender -b --factory-startup --python build_pc.py -- --shot avenue --mp4 FILE [--fps 30 --samples 24]

Modules: on the PC they are copied flat into sets/ (metro.py, metro_plan.py, metro_mats.py, metro_build.py,
metro_detail.py from blender/library, lib.py from blender/kit/blender); inside the repo they are found in place.
"""
import sys, os, json, time, argparse, importlib, traceback, glob
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
for _p in (os.path.join(HERE, '..', '..', '..', 'blender', 'kit', 'blender'),
           os.path.join(HERE, '..', '..', '..', 'blender', 'library'), os.path.join(HERE, 'sets')):
    if os.path.isdir(_p):
        sys.path.insert(0, os.path.abspath(_p))
import bpy
import lib


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument('--shot', required=True)
    ap.add_argument('--shots', default=os.path.join(HERE, 'shots.json'))
    ap.add_argument('--still', default='')
    ap.add_argument('--t', type=float, default=-1.0)
    ap.add_argument('--tag', default='', help='suffix for the still file name')
    ap.add_argument('--mp4', default='')
    ap.add_argument('--scale', type=float, default=1.0)
    ap.add_argument('--samples', type=int, default=0)
    ap.add_argument('--save', action='store_true')
    ap.add_argument('--dry', action='store_true', help='build only, no render')
    ap.add_argument('--engine', default='', help='CYCLES for a CPU preview without a GPU')
    ap.add_argument('--fps', type=int, default=0, help='override the timeline fps (clips at 30 halve the render time)')
    a = ap.parse_args(argv)
    shots = json.load(open(a.shots, encoding='utf-8'))
    shot = next(s for s in shots['shots'] if s['id'] == a.shot)
    fps = a.fps or shots.get('fps', 60)
    lib.FPS = fps
    t0 = time.time()
    lib.reset()
    mod = importlib.import_module(shot['set'])
    lib.setup_render(shot['dur'], samples=48, scale=a.scale, fps=fps, **shot.get('render', {}))
    res = mod.build(shot, fps) or {}
    fill = shot.get('fill', res.get('fill', 0.6))
    if fill:
        lib.camera_fill(fill, color=res.get('fill_col', '#FFF4EA'))
    sc = bpy.context.scene
    sc.view_settings.exposure = shot.get('exposure', res.get('exposure', 0.1))
    sc.eevee.taa_render_samples = a.samples or shot.get('samples', res.get('samples', 64 if a.still else 32))
    sc.frame_end = max(sc.frame_start, int(round(shot['dur'] * fps)))
    print(f'BUILD {a.shot} set={shot["set"]}/{shot.get("variant")} frames={sc.frame_end} built in {time.time() - t0:.1f}s', flush=True)
    if a.dry:
        print(f'DRY {a.shot} objects={len(bpy.data.objects)}', flush=True)
        return
    if a.engine:
        sc.render.engine = a.engine
        if a.engine == 'CYCLES':
            sc.cycles.samples = a.samples or 24
            sc.cycles.use_denoising = True
            sc.cycles.device = 'CPU'
    if a.save:
        lib.save_blend(os.path.join(lib.PROJ, 'blender', 'files', a.shot + '.blend'))
    r = sc.render
    if a.mp4:
        tmp = os.path.join(os.path.dirname(a.mp4), '_tmp_' + a.shot)
        os.makedirs(tmp, exist_ok=True)
        if hasattr(r.image_settings, 'media_type'):          # Blender 5.x: video is a media type, then FFMPEG
            r.image_settings.media_type = 'VIDEO'
        r.image_settings.file_format = 'FFMPEG'
        ff = r.ffmpeg
        ff.format = 'MPEG4'
        ff.codec = 'H264'
        ff.constant_rate_factor = 'PERC_LOSSLESS'
        ff.ffmpeg_preset = 'GOOD'
        ff.gopsize = 30
        try:
            ff.use_max_b_frames = True
            ff.max_b_frames = 0
        except Exception:
            pass
        ff.audio_codec = 'NONE'
        r.use_overwrite = True
        r.use_placeholder = False
        r.filepath = os.path.join(tmp, 'clip_')
        t1 = time.time()
        bpy.ops.render.render(animation=True)
        made = sorted(glob.glob(os.path.join(tmp, 'clip_*')), key=os.path.getmtime)
        if not made:
            raise SystemExit('no movie written')
        os.replace(made[-1], a.mp4)
        n = sc.frame_end - sc.frame_start + 1
        print(f'CLIP {a.shot} {n} frames in {time.time() - t1:.1f}s -> {a.mp4}', flush=True)
    else:
        d = a.still or os.path.join(lib.PROJ, 'renders', 'stills')
        os.makedirs(d, exist_ok=True)
        t = a.t if a.t >= 0 else shot.get('still_t', res.get('still_t', 0.5))
        f = min(max(1, int(round(1 + t * (sc.frame_end - 1)))), sc.frame_end)
        sc.frame_set(f)
        r.use_overwrite = True
        r.use_placeholder = False
        r.image_settings.file_format = 'JPEG'
        r.image_settings.quality = 92
        r.filepath = os.path.join(d, f'{a.shot}{a.tag}.jpg')
        t1 = time.time()
        bpy.ops.render.render(write_still=True)
        print(f'STILL {a.shot} f{f} {time.time() - t1:.1f}s', flush=True)


try:
    main()
except Exception:
    traceback.print_exc()
    sys.stdout.flush()
    os._exit(3)
