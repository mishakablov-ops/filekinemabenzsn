"""Очередь рендера «Эскалатора» на ПК: по одному фоновому blender.exe на план, лог в render/pc_run.log.
python pc_run.py stills S01,S12 [--pct 50 --samples 32]     стоп-кадры в render/stills
python pc_run.py anim S01,S02,... [--samples 64]             кадры в render/frames/<план> (докачка: готовые кадры пропускаются)
TEMP держим на C: (на FAT32-флешке Chrome/Blender спотыкаются о время файлов)."""
import subprocess, sys, os, json, time

HERE = os.path.dirname(os.path.abspath(__file__))
BLENDER = os.environ.get('ESK_BLENDER', r'C:\Users\Gigabyte\Documents\aipollon claude\blender-mcp\blender-5.2.3-windows-x64\blender.exe')
OUT = os.environ.get('ESK_OUT', os.path.join(HERE, 'render'))
mode, ids = sys.argv[1], sys.argv[2].split(',')
extra = sys.argv[3:]
shots = {s['id']: s for s in json.load(open(os.path.join(HERE, 'shots.json'), encoding='utf-8'))['shots']}
env = dict(os.environ)
env['TEMP'] = env['TMP'] = os.path.join(os.environ.get('LOCALAPPDATA', r'C:\Temp'), 'Temp')
os.makedirs(OUT, exist_ok=True)
log = open(os.path.join(OUT, 'pc_run.log'), 'a', encoding='utf-8')
for sid in ids:
    args = [BLENDER, '-b', '--factory-startup', '--python', os.path.join(HERE, 'build_shot.py'), '--', sid, '--out', OUT] + extra
    if mode == 'stills' and '--still' not in extra:
        d = shots[sid]['dur']
        args += ['--still', '%.1f,%.1f' % (d * 0.25, d * 0.75)]
    t = time.time()
    r = subprocess.run(args, capture_output=True, text=True, encoding='utf-8', errors='replace', env=env, cwd=HERE)
    tail = (r.stdout[-1500:] + r.stderr[-1500:]) if r.returncode else r.stdout[-200:]
    log.write('%s %s rc=%s %.0fs\n%s\n' % (time.strftime('%H:%M:%S'), sid, r.returncode, time.time() - t, tail))
    log.flush()
log.write('QUEUE_DONE %s\n' % ','.join(ids))
log.close()
