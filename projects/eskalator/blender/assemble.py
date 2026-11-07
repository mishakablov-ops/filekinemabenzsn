"""Сборка «Эскалатора» на ПК: кадры планов -> клипы -> переходы-смазы -> титры как в образце -> голос + музыка.
python assemble.py --voice <voice.wav> --words <words.json> --out <mp4> [--music pulse-tech] [--frames render/frames]

Титры (по разбору образца): 1–3 слова, без анимации, белый жирный гротеск (Montserrat ExtraBold), мягкая тёмная
тень без обводки, по центру на ~73 % высоты. Крупные красные цифры сверху на статистике.
Переход: смаз/наезд 0,3 с с центром на моменте смены фразы. Голос впереди, тихая подложка, мастер −14 LUFS."""
import argparse, json, os, re, subprocess, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser()
ap.add_argument('--voice', required=True)
ap.add_argument('--words', required=True)
ap.add_argument('--out', required=True)
ap.add_argument('--frames', default=os.path.join(HERE, 'render', 'frames'))
ap.add_argument('--work', default=os.path.join(HERE, 'render', 'asm'))
ap.add_argument('--ffmpeg', default=r'D:\aipollon\KINEMA\skills\reel-studio\.runtime\bin\ffmpeg.exe')
ap.add_argument('--music', default=r'D:\aipollon\KINEMA\skills\reel-studio\engine\public\music\pulse-tech.m4a')
ap.add_argument('--music-vol', type=float, default=0.12)
ap.add_argument('--fps', type=int, default=30)
ap.add_argument('--xf', type=float, default=0.3)
ap.add_argument('--only-clips', action='store_true')
ap.add_argument('--grain', type=float, default=2.5)   # лёгкое плёночное зерно: убирает «стерильность» CG и полосы в градиентах
a = ap.parse_args()
FF = a.ffmpeg
os.makedirs(a.work, exist_ok=True)
shots = json.load(open(os.path.join(HERE, 'shots.json'), encoding='utf-8'))
S = shots['shots']
W = json.load(open(a.words, encoding='utf-8'))
END = shots['duration']


def run(args):
    r = subprocess.run(args, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if r.returncode:
        print(' '.join(args)[:400]); print(r.stderr[-2000:]); sys.exit(1)
    return r


# ----------------------------------------------------------------------------- шрифт
FONTS = os.path.join(a.work, 'fonts')
os.makedirs(FONTS, exist_ok=True)
for fn in ('Montserrat-ExtraBold.ttf', 'Montserrat-Black.ttf'):
    p = os.path.join(FONTS, fn)
    if not os.path.exists(p):
        url = 'https://raw.githubusercontent.com/JulietaUla/Montserrat/master/fonts/ttf/' + fn
        data = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'aipollon'}), timeout=60).read()
        open(p, 'wb').write(data)

# ----------------------------------------------------------------------------- клипы планов
GRADE = {
    'default': 'eq=contrast=1.04:saturation=1.06,colorbalance=rs=0.02:gs=0.0:bs=-0.02',
    'S19': 'colorchannelmixer=.393:.769:.189:0:.349:.686:.168:0:.272:.534:.131,eq=contrast=1.05,vignette=PI/4.5',
}
XF = a.xf
clips = []
for k, s in enumerate(S):
    t0 = s['start'] - (XF / 2 if k else 0.0)
    t1 = (S[k + 1]['start'] + XF / 2) if k + 1 < len(S) else END
    L = t1 - t0
    src = os.path.join(a.frames, s['id'], '%04d.jpg')
    out = os.path.join(a.work, s['id'] + '.mp4')
    vf = GRADE.get(s['id'], GRADE['default']) + ',scale=1080:1920:flags=lanczos,setsar=1,fps=%d' % a.fps
    run([FF, '-y', '-v', 'error', '-framerate', str(a.fps), '-start_number', '1', '-i', src, '-t', '%.3f' % L,
         '-vf', vf + ',tpad=stop_mode=clone:stop_duration=1', '-t', '%.3f' % L,
         '-c:v', 'libx264', '-crf', '14', '-preset', 'medium', '-pix_fmt', 'yuv420p', '-r', str(a.fps), out])
    clips.append((out, t0, L))
if a.only_clips:
    sys.exit(0)

# ----------------------------------------------------------------------------- переходы (xfade цепочкой)
TRANS = {'S02': 'zoomin', 'S12': 'zoomin', 'S16': 'smoothup', 'S17': 'smoothdown', 'S19': 'fadewhite', 'S21': 'hblur'}
args = [FF, '-y', '-v', 'error']
for (p, t0, L) in clips:
    args += ['-i', p]
fc = []
prev = '[0:v]'
for k in range(1, len(clips)):
    off = S[k]['start'] - XF / 2
    tr = TRANS.get(S[k]['id'], 'hblur')
    lab = '[v%d]' % k
    fc.append('%s[%d:v]xfade=transition=%s:duration=%.3f:offset=%.3f%s' % (prev, k, tr, XF, off, lab))
    prev = lab
video = os.path.join(a.work, 'video.mp4')
args += ['-filter_complex', ';'.join(fc), '-map', prev, '-c:v', 'libx264', '-crf', '14', '-preset', 'medium',
         '-pix_fmt', 'yuv420p', '-r', str(a.fps), video]
run(args)

# ----------------------------------------------------------------------------- титры
def ass_time(t):
    t = max(0.0, t)
    h = int(t // 3600); m = int(t % 3600 // 60); s_ = t % 60
    return '%d:%02d:%05.2f' % (h, m, s_)


words = W['words']
chunks = []
cur = []
for i, w in enumerate(words):
    txt = w['text']
    cur.append(w)
    clean = ' '.join(re.sub(r'[«»"“”/]', '', x['text']).strip(' ,.:;!?—-') for x in cur)
    nxt = words[i + 1] if i + 1 < len(words) else None
    brk = (len(cur) >= 3 or len(clean) >= 15 or re.search(r'[,.:;!?]$', txt) or nxt is None
           or (nxt and nxt['card'] != w['card']) or (nxt and nxt['start'] - w['end'] > 0.35)
           or (nxt and len(clean) + 1 + len(nxt['text']) > 17))
    if brk:
        chunks.append(dict(text=clean, start=cur[0]['start'], end=cur[-1]['end']))
        cur = []
for k in range(len(chunks) - 1):
    gap = chunks[k + 1]['start'] - chunks[k]['end']
    chunks[k]['end'] = chunks[k + 1]['start'] if gap < 0.5 else chunks[k]['end'] + 0.2

STATS = [  # (текст, начало, конец): большие красные цифры сверху, как «7/15» в образце
    ('1133', 32.9, 34.75), ('126 м', 36.3, 37.98), ('63 м', 38.1, 41.15), ('≈ 2:48', 41.3, 42.58)]
CY = 1400
ass = ['[Script Info]', 'ScriptType: v4.00+', 'PlayResX: 1080', 'PlayResY: 1920', 'WrapStyle: 2', '',
       '[V4+ Styles]',
       'Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, '
       'Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding',
       'Style: Cap,Montserrat ExtraBold,100,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,5,60,60,0,1',
       'Style: Sh,Montserrat ExtraBold,100,&H70000000,&H70000000,&H70000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,5,60,60,0,1',
       'Style: Stat,Montserrat Black,210,&H00231BE2,&H00231BE2,&H00100A60,&H64000000,0,0,0,0,100,100,0,0,1,7,4,8,40,40,0,1',
       '', '[Events]', 'Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text']
for c in chunks:
    t = c['text']
    ass.append('Dialogue: 0,%s,%s,Sh,,0,0,0,,{\\an5\\pos(544,%d)\\blur9}%s' % (ass_time(c['start']), ass_time(c['end']), CY + 7, t))
    ass.append('Dialogue: 1,%s,%s,Cap,,0,0,0,,{\\an5\\pos(540,%d)}%s' % (ass_time(c['start']), ass_time(c['end']), CY, t))
for (t, b, e) in STATS:
    ass.append('Dialogue: 2,%s,%s,Stat,,0,0,0,,{\\an8\\pos(540,230)\\fscx135\\fscy135\\t(0,140,\\fscx100\\fscy100)\\fad(60,120)}%s'
               % (ass_time(b), ass_time(e), t))
assp = os.path.join(a.work, 'captions.ass')
open(assp, 'w', encoding='utf-8-sig').write('\n'.join(ass) + '\n')

# ----------------------------------------------------------------------------- звук
mix = os.path.join(a.work, 'mix.wav')
run([FF, '-y', '-v', 'error', '-i', a.voice, '-stream_loop', '-1', '-i', a.music, '-filter_complex',
     '[0:a]aresample=48000,loudnorm=I=-16:TP=-1.5:LRA=11,apad=pad_dur=2,asplit=2[v1][v2];'
     '[1:a]aresample=48000,volume=%.3f,afade=t=in:d=0.6,afade=t=out:st=%.2f:d=0.8[m];'
     '[m][v1]sidechaincompress=threshold=0.05:ratio=4:attack=20:release=300[md];'
     '[v2][md]amix=inputs=2:duration=first:normalize=0,atrim=0:%.3f,loudnorm=I=-14:TP=-1:LRA=11' % (a.music_vol, END - 0.8, END),
     '-ar', '48000', mix])

# ----------------------------------------------------------------------------- финал
fontsdir = FONTS.replace('\\', '/').replace(':', '\\:')
assf = assp.replace('\\', '/').replace(':', '\\:')
vf = ("noise=alls=%.1f:allf=t," % a.grain if a.grain > 0 else '') + "ass='%s':fontsdir='%s'" % (assf, fontsdir)
run([FF, '-y', '-v', 'error', '-i', video, '-i', mix, '-vf', vf,
     '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-crf', '16', '-preset', 'slow', '-pix_fmt', 'yuv420p',
     '-r', str(a.fps), '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-movflags', '+faststart', '-t', '%.3f' % END, a.out])
print('ASSEMBLED', a.out)
