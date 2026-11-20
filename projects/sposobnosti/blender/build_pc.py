"""Entry point for sposobnosti (Каждому по способности), same as posledniy-chelovek-blender:
    blender -b --factory-startup --python build_pc.py -- --shot wake --still DIR [--t 0.5] [--scale 1.25]
    blender -b --factory-startup --python build_pc.py -- --shot count --mp4 FILE [--scale 1.0] [--fps 30 --samples 24]

--still: renders one frame at t (fraction of the shot, default 0.5) into DIR/<shot>.jpg; --ts 0.2,0.8 renders several
         frames of one build into DIR/<shot>_t20.jpg, DIR/<shot>_t80.jpg.
--mp4:   renders the whole shot straight into an H.264 file (no frame sequence on disk), GOP 30, no B-frames
         (what Remotion needs for exact seeking). Nothing is saved as .blend unless --save.
"""
import sys, os, json, time, argparse, importlib, traceback, glob
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, 'sets'))
# in the repository the scene modules live only in blender/library (and lib.py in blender/kit): local copies win
for _p in (('..', '..', '..', 'blender', 'kit', 'blender'), ('..', '..', '..', 'blender', 'library')):
    sys.path.append(os.path.normpath(os.path.join(HERE, *_p)))
import bpy
import lib


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument('--shot', required=True)
    ap.add_argument('--shots', default=os.path.join(HERE, 'shots.json'))
    ap.add_argument('--still', default='')
    ap.add_argument('--t', type=float, default=-1.0)
    ap.add_argument('--ts', default='', help='several stills from one build: "0.2,0.5,0.9" -> <shot>_t20.jpg ...')
    ap.add_argument('--tag', default='', help='suffix for the still file name')
    ap.add_argument('--mp4', default='')
    ap.add_argument('--scale', type=float, default=1.0)
    ap.add_argument('--samples', type=int, default=0)
    ap.add_argument('--save', action='store_true')
    ap.add_argument('--dry', action='store_true', help='build only, no render')
    ap.add_argument('--engine', default='', help='CYCLES for a CPU preview without a GPU')
    ap.add_argument('--fps', type=int, default=0, help='override the timeline fps (clips at 30 halve the render time)')
    ap.add_argument('--hide', default='', help='profiling: hide objects whose names start with these prefixes ("Rain,AveDeck")')
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
    _lighten_shadows(sc, a.hide)
    sc.view_settings.exposure = shot.get('exposure', res.get('exposure', 0.1))
    sc.eevee.taa_render_samples = a.samples or shot.get('samples', res.get('samples', 64 if a.still else 32))
    sc.frame_end = max(sc.frame_start, int(round(shot['dur'] * fps)))
    if 'sila_hero' in sys.modules:               # 28.10.2026: the hero blinks, looks around, breathes
        sys.modules['sila_hero'].alive_all(sc, seed=sum(map(ord, a.shot)))
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
        r.use_overwrite = True
        r.use_placeholder = False
        r.image_settings.file_format = 'JPEG'
        r.image_settings.quality = 92
        if a.ts:
            todo = [(float(x), f'_t{int(round(float(x) * 100)):02d}') for x in a.ts.split(',')]
        else:
            todo = [(a.t if a.t >= 0 else shot.get('still_t', res.get('still_t', 0.5)), a.tag)]
        for t, tag in todo:
            f = min(max(1, int(round(1 + t * (sc.frame_end - 1)))), sc.frame_end)
            sc.frame_set(f)
            r.filepath = os.path.join(d, f'{a.shot}{tag}.jpg')
            t1 = time.time()
            bpy.ops.render.render(write_still=True)
            print(f'STILL {a.shot}{tag} f{f} {time.time() - t1:.1f}s', flush=True)


def _lighten_shadows(sc, hide=''):
    """Rain streaks, cloud puffs, auras and glows (all alpha-blended) cast no shadows: thousands of moving casters made
    Eevee re-render shadow pages every sample. A bigger shadow pool stops the 'Shadow buffer full' thrashing."""
    n = 0
    for o in bpy.data.objects:
        ms = [s.material for s in getattr(o, 'material_slots', []) if s.material]
        if ms and all(getattr(m, 'surface_render_method', '') == 'BLENDED' for m in ms):
            o.visible_shadow = False
            n += 1
    try:
        sc.eevee.shadow_pool_size = '1024'
    except Exception:
        pass
    pre = tuple(p for p in hide.split(',') if p)
    k = 0
    if pre:
        for o in bpy.data.objects:
            if o.name.startswith(pre):
                o.hide_render = True
                k += 1
    print(f'SHADOWS off for {n} blended objects, hidden {k}', flush=True)


try:
    main()
except Exception:
    traceback.print_exc()
    sys.stdout.flush()
    os._exit(3)
