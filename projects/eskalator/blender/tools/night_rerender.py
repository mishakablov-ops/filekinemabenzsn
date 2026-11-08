"""Ночной перерендер планов с людьми и сборка ролика, без участия человека (питоном Blender, из папки кода).

Правка mike 08.11.2026 на v2: «персонажей очень дергает, исправь», «сделай это часа в 2 ночи».
  1) пересобрать мокап (tools/build_mocap.py, сглаживание в esk_mocap.retarget): старый mocap.blend -> mocap_v2.blend
  2) кадры планов без людей скопировать из прошлого рендера (--base), планы с людьми рендерить заново двумя очередями
  3) проверить число кадров, собрать assemble.py, замерить длительность и громкость, лист кадров для проверки
Всё пишется в <out>/night.log, итог - строка NIGHT_DONE или NIGHT_FAIL.

PY tools/night_rerender.py --base D:\\aipollon\\eskalator\\render_v2 --out D:\\aipollon\\eskalator\\render_v3
       --video D:\\aipollon\\output\\eskalator-v3.mp4 [--qa S15,S16,S21,S12 --qb S01,S20B,S19,S14,S18] [--no-mocap]"""
import argparse, json, os, re, shutil, subprocess, sys, time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))     # папка кода (pc_run.py, build_shot.py)
BL = os.environ.get('ESK_BLENDER', r'C:\Users\Gigabyte\Documents\aipollon claude\blender-mcp\blender-5.2.3-windows-x64\blender.exe')
KIN = r'D:\aipollon\KINEMA\skills\reel-studio'
ap = argparse.ArgumentParser()
ap.add_argument('--base', required=True)
ap.add_argument('--out', required=True)
ap.add_argument('--video', required=True)
ap.add_argument('--qa', default='S15,S16,S21,S12')
ap.add_argument('--qb', default='S01,S20B,S19,S14,S18')
ap.add_argument('--assets', default=os.environ.get('ESK_ASSETS', r'D:\aipollon\eskalator\assets'))
ap.add_argument('--voice', default=os.path.join(KIN, 'engine', 'public', 'projects', 'eskalator', 'voice.wav'))
ap.add_argument('--words', default=os.path.join(KIN, 'engine', 'public', 'projects', 'eskalator', 'words.json'))
ap.add_argument('--ffmpeg', default=os.path.join(KIN, '.runtime', 'bin', 'ffmpeg.exe'))
ap.add_argument('--no-mocap', action='store_true')
a = ap.parse_args()
os.makedirs(a.out, exist_ok=True)
LOG = open(os.path.join(a.out, 'night.log'), 'a', encoding='utf-8')
ENV = dict(os.environ)
ENV['TEMP'] = ENV['TMP'] = os.path.join(os.environ.get('LOCALAPPDATA', r'C:\Temp'), 'Temp')   # не на FAT32-флешке
NOWIN = 0x08000000 if os.name == 'nt' else 0


def log(*m):
    LOG.write(time.strftime('%Y-%m-%d %H:%M:%S ') + ' '.join(str(x) for x in m) + '\n'); LOG.flush()


def fail(msg):
    log('NIGHT_FAIL', msg); sys.exit(1)


def run(args, **kw):
    r = subprocess.run(args, capture_output=True, text=True, encoding='utf-8', errors='replace', env=ENV,
                       creationflags=NOWIN, **kw)
    return r


log('start', ' '.join(sys.argv[1:]))
shots = json.load(open(os.path.join(HERE, 'shots.json'), encoding='utf-8'))['shots']
ids = [s['id'] for s in shots]
live = [x for x in (a.qa + ',' + a.qb).split(',') if x]

# ---------------------------------------------------------------- 1. мокап
mc = os.path.join(a.assets, 'mocap')
if not a.no_mocap:
    new = os.path.join(mc, 'mocap_new.blend')
    r = run([BL, '-b', '--factory-startup', '--python', os.path.join(HERE, 'tools', 'build_mocap.py'), '--',
             os.path.join(a.assets, 'hero.blend'), os.path.join(mc, 'cmu'), os.path.join(mc, 'default_tpose.json'), new],
            cwd=HERE)
    m = re.search(r'MOCAP_DONE (\d+)', r.stdout)
    if r.returncode or not m or not os.path.exists(new):
        fail('build_mocap rc=%s\n%s\n%s' % (r.returncode, r.stdout[-1500:], r.stderr[-1500:]))
    log('mocap', m.group(0), ' '.join(re.findall(r'^MISSING .*$', r.stdout, re.M)))
    cur = os.path.join(mc, 'mocap.blend')
    keep = os.path.join(mc, 'mocap_v2.blend')
    if os.path.exists(cur):
        if not os.path.exists(keep):
            os.replace(cur, keep)
        else:
            os.remove(cur)          # копия v2 уже сохранена
    os.replace(new, cur)

# ---------------------------------------------------------------- 2. кадры
fr_out = os.path.join(a.out, 'frames')
os.makedirs(fr_out, exist_ok=True)
need = {}
for sid in ids:
    src = os.path.join(a.base, 'frames', sid)
    n = len([f for f in os.listdir(src) if f.endswith('.jpg')]) if os.path.isdir(src) else 0
    need[sid] = n
    if sid not in live and not os.path.isdir(os.path.join(fr_out, sid)):
        shutil.copytree(src, os.path.join(fr_out, sid))
log('copied', ','.join(s for s in ids if s not in live))

procs = []
for q in (a.qa, a.qb):
    if not q:
        continue
    env = dict(ENV); env['ESK_OUT'] = a.out
    procs.append(subprocess.Popen([sys.executable, os.path.join(HERE, 'pc_run.py'), 'anim', q, '--engine', 'EEVEE',
                                   '--samples', '32'], cwd=HERE, env=env, creationflags=NOWIN,
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
    log('queue', q)
for p in procs:
    p.wait()
log('render done')

bad = []
for sid in ids:
    d = os.path.join(fr_out, sid)
    fs = [f for f in os.listdir(d) if f.endswith('.jpg')] if os.path.isdir(d) else []
    small = [f for f in fs if os.path.getsize(os.path.join(d, f)) < 10000]
    if len(fs) < need[sid] or small:
        bad.append('%s %d/%d small=%s' % (sid, len(fs), need[sid], small[:3]))
if bad:
    fail('frames: ' + '; '.join(bad))

# ---------------------------------------------------------------- 3. сборка и проверка
r = run([sys.executable, os.path.join(HERE, 'assemble.py'), '--voice', a.voice, '--words', a.words, '--out', a.video,
         '--frames', fr_out, '--work', os.path.join(a.out, 'asm'), '--ffmpeg', a.ffmpeg], cwd=HERE)
if r.returncode or not os.path.exists(a.video):
    fail('assemble rc=%s\n%s\n%s' % (r.returncode, r.stdout[-1500:], r.stderr[-1500:]))
fp = a.ffmpeg.replace('ffmpeg.exe', 'ffprobe.exe')
r = run([fp, '-v', 'error', '-show_entries', 'format=duration:stream=codec_type,width,height', '-of', 'json', a.video])
log('probe', r.stdout.replace('\n', ' '))
r = run([a.ffmpeg, '-hide_banner', '-nostats', '-i', a.video, '-af', 'ebur128', '-f', 'null', '-'])
m = re.findall(r'I:\s+(-?[\d.]+) LUFS', r.stderr)
log('loudness', m[-1] if m else '?')
qa = os.path.join(a.out, 'qa')
os.makedirs(qa, exist_ok=True)
run([a.ffmpeg, '-y', '-v', 'error', '-i', a.video, '-vf', 'fps=1/2,scale=180:-1,tile=9x3', '-frames:v', '1',
     os.path.join(qa, 'sheet.jpg')])
log('NIGHT_DONE', a.video, '%.1f MB' % (os.path.getsize(a.video) / 1e6))
