"""Мимика ведущего: губы под голос, моргание, взгляд, брови, улыбка.

Правка mike 08.11.2026: «сделай более качественнее мимику и анимации».
Формы лица - шейп-ключи MPFB (паки MakeHuman CC0: visemes01 - 22 формы рта Microsoft, faceunits01 - 52 ARKit),
их добавляет esk_hero.add_face_keys() в hero.blend (на тело, брови, ресницы, зубы, язык).

Губы: буквы слова (тайминги слов из words.json озвучки) -> визема, гласные длиннее согласных; раскрытие рта
умножается на громкость голоса в этот момент (voice.wav), поэтому рот не шевелится в паузах, даже если
тайминги слов где-то съехали. Моргание раз в 2-5 с (быстро закрыть, медленнее открыть), мелкие движения глаз,
брови чуть вверх на ударных словах.

Правка mike 08.11.2026 на v2 «персонажей очень дергает»: огибающая голоса сглажена сильнее (5 кадров), кривые рта
дополнительно сглажены Гауссом (рот не «трепещет» от кадра к кадру), взгляд перескакивает реже и мягче.
"""
import bpy, json, math, os, random, wave, array

VIS = ['sil_00', 'aa_ah_ax_01', 'aa_02', 'ao_03', 'ey_eh_uh_04', 'er_05', 'y_iy_ih_ix_06', 'w_uw_07', 'ow_08',
       'aw_09', 'oy_10', 'ay_11', 'h_12', 'r_13', 'l_14', 's_z_15', 'sh_ch_jh_zh_16', 'th_dh_17', 'f_v_18',
       'd_t_n_19', 'k_g_ng_20', 'p_b_m_21']
# русская буква -> (визема, сила, гласная?)
LET = {
    'а': ('aa_02', 0.85, 1), 'я': ('aa_ah_ax_01', 0.8, 1), 'о': ('ow_08', 0.8, 1), 'ё': ('ow_08', 0.8, 1),
    'у': ('w_uw_07', 0.85, 1), 'ю': ('w_uw_07', 0.8, 1), 'э': ('ey_eh_uh_04', 0.8, 1), 'е': ('ey_eh_uh_04', 0.75, 1),
    'и': ('y_iy_ih_ix_06', 0.75, 1), 'ы': ('y_iy_ih_ix_06', 0.7, 1), 'й': ('y_iy_ih_ix_06', 0.4, 0),
    'б': ('p_b_m_21', 1.0, 0), 'п': ('p_b_m_21', 1.0, 0), 'м': ('p_b_m_21', 1.0, 0),
    'ф': ('f_v_18', 0.9, 0), 'в': ('f_v_18', 0.8, 0),
    'т': ('d_t_n_19', 0.7, 0), 'д': ('d_t_n_19', 0.7, 0), 'н': ('d_t_n_19', 0.65, 0),
    'с': ('s_z_15', 0.75, 0), 'з': ('s_z_15', 0.7, 0), 'ц': ('s_z_15', 0.75, 0),
    'ш': ('sh_ch_jh_zh_16', 0.85, 0), 'щ': ('sh_ch_jh_zh_16', 0.85, 0), 'ж': ('sh_ch_jh_zh_16', 0.8, 0),
    'ч': ('sh_ch_jh_zh_16', 0.8, 0), 'к': ('k_g_ng_20', 0.6, 0), 'г': ('k_g_ng_20', 0.6, 0), 'х': ('h_12', 0.5, 0),
    'л': ('l_14', 0.7, 0), 'р': ('r_13', 0.7, 0),
}
DIGITS = {'0': 'ноль', '1': 'один', '2': 'два', '3': 'три', '4': 'четыре', '5': 'пять', '6': 'шесть', '7': 'семь',
          '8': 'восемь', '9': 'девять'}


def face_objects(rig):
    """тело и все дети рига, у которых есть формы рта/лица"""
    out = []
    for c in rig.children:
        sk = c.data.shape_keys if c.type == 'MESH' else None
        if sk and ('aa_02' in sk.key_blocks or 'eyeBlinkLeft' in sk.key_blocks):
            out.append(c)
    return out


def envelope(wav_path, t0, t1, fps):
    """громкость голоса по кадрам [t0, t1), 0..1 (95-й перцентиль всего окна = 1)"""
    try:
        w = wave.open(wav_path)
    except Exception:
        return None
    sr, ch, sw = w.getframerate(), w.getnchannels(), w.getsampwidth()
    if sw != 2:
        return None
    a0 = max(0, int(t0 * sr))
    w.setpos(min(a0, w.getnframes()))
    n = max(0, int((t1 - t0) * sr))
    data = array.array('h', w.readframes(n))
    hop = sr / fps
    out = []
    k = 0
    while True:
        s, e = int(k * hop) * ch, int((k + 1) * hop) * ch
        if e > len(data):
            break
        seg = data[s:e:ch * 4]                          # каждая 4-я выборка: для огибающей хватает
        out.append(math.sqrt(sum(x * x for x in seg) / max(1, len(seg))) if seg else 0.0)
        k += 1
    if not out:
        return None
    ref = sorted(out)[int(len(out) * 0.95)] or 1.0
    sm = []
    for i in range(len(out)):                            # сглаживание 5 кадров
        w = out[max(0, i - 2):i + 3]
        sm.append(sum(w) / len(w))
    return [min(1.0, v / ref) for v in sm]


def _gauss(xs, sig):
    r = int(math.ceil(3 * sig))
    w = [math.exp(-0.5 * (k / sig) ** 2) for k in range(-r, r + 1)]
    n = len(xs)
    out = []
    for i in range(n):
        s = ws = 0.0
        for k in range(-r, r + 1):
            if 0 <= i + k < n:
                s += w[k + r] * xs[i + k]; ws += w[k + r]
        out.append(s / ws)
    return out


def _segments(words, t0, t1):
    segs = []
    for wd in words:
        if wd['end'] < t0 - 0.3 or wd['start'] > t1 + 0.3:
            continue
        txt = ''.join(DIGITS.get(c, c) for c in wd['text'].lower())
        ls = [LET[c] for c in txt if c in LET]
        if not ls:
            continue
        ws = [1.7 if v else 1.0 for (_, _, v) in ls]
        tot = sum(ws)
        t = wd['start']
        span = max(0.05, wd['end'] - wd['start'])
        for (vis, k, _), wt in zip(ls, ws):
            d = span * wt / tot
            segs.append((t, t + d, vis, k))
            t += d
    return segs


def _key_series(objs, name, frames, vals):
    for ob in objs:
        kb = ob.data.shape_keys.key_blocks.get(name)
        if kb is None:
            continue
        for f, v in zip(frames, vals):
            kb.value = v
            kb.keyframe_insert('value', frame=f)


def lipsync(rig, words, t_start, n, fps, wav=None, gain=1.0):
    """губы на кадрах 1..n; кадр 1 = время t_start в озвучке"""
    objs = face_objects(rig)
    if not objs:
        return 0
    t1 = t_start + n / fps
    segs = _segments(words, t_start, t1)
    env = envelope(wav, t_start, t1 + 0.1, fps) if wav else None
    frames = list(range(1, n + 1))
    cur = {v: [0.0] * n for v in VIS}
    for i, f in enumerate(frames):
        t = t_start + (f - 1) / fps
        a = 1.0
        if env is not None:
            a = env[min(i, len(env) - 1)]
            a = 0.0 if a < 0.06 else min(1.0, (a - 0.06) / 0.6)
        for (ts, te, vis, k) in segs:
            c = (ts + te) / 2
            hw = (te - ts) / 2 + 0.035                  # соседние звуки перекрываются (коартикуляция)
            u = 1.0 - abs(t - c) / hw
            if u <= 0:
                continue
            u = u * u * (3 - 2 * u)
            amp = k * u * gain * (1.0 if vis == 'p_b_m_21' else (0.35 + 0.65 * a))
            if amp > cur[vis][i]:
                cur[vis][i] = amp
    used = 0
    for v in VIS:
        vals = [min(1.0, x) for x in _gauss(cur[v], 0.6 if v == 'p_b_m_21' else 1.1)]   # смыкание губ на п/б/м резче
        if max(vals) < 0.02:
            continue
        _key_series(objs, v, frames, vals)
        used += 1
    return used


def blinks(rig, n, fps, rng, first=None):
    objs = face_objects(rig)
    if not objs:
        return 0
    t = first if first is not None else rng.uniform(0.3, 1.2)
    k = 0
    keys = {}
    while t * fps < n + 4:
        f0 = 1 + int(t * fps)
        for df, v in ((-1, 0.0), (0, 0.0), (1, 0.65), (2, 1.0), (3, 0.75), (4, 0.3), (5, 0.0)):
            keys[f0 + df] = max(keys.get(f0 + df, 0.0), v)
        k += 1
        t += rng.uniform(2.0, 4.5) if rng.random() > 0.15 else rng.uniform(0.25, 0.45)   # иногда двойное
    fr = sorted(f for f in keys if f >= 0)
    for side in ('Left', 'Right'):
        _key_series(objs, 'eyeBlink' + side, fr, [keys[f] for f in fr])
    return k


def accent(rig, names_vals, frames_vals):
    """плавная форма (улыбка, брови): names_vals {key: weight}, frames_vals [(кадр, 0..1)]"""
    objs = face_objects(rig)
    for nm, w in names_vals.items():
        _key_series(objs, nm, [f for f, _ in frames_vals], [w * v for _, v in frames_vals])


def brows_on_words(rig, words, t_start, n, fps, rng, k=0.35):
    """брови вверх на длинных (ударных) словах"""
    pts = [(1, 0.0)]
    for wd in words:
        if not (t_start <= wd['start'] < t_start + n / fps):
            continue
        if len(wd['text']) >= 7 and rng.random() < 0.7:
            f = 1 + int((wd['start'] - t_start) * fps)
            pts += [(max(1, f - 3), 0.0), (f + 2, 1.0), (f + 9, 0.6), (f + 16, 0.0)]
    pts.sort()
    clean = []
    for f, v in pts:
        if clean and f <= clean[-1][0]:
            continue
        clean.append((f, v))
    accent(rig, {'browInnerUp': k, 'browOuterUpLeft': k * 0.6, 'browOuterUpRight': k * 0.6}, clean)


def eye_darts(rig, n, fps, rng, amp=1.3):
    """мелкие движения глаз (саккады): глаза никогда не застывают у живого человека"""
    from mathutils import Euler
    pbs = [rig.pose.bones.get(b) for b in ('eye.L', 'eye.R')]
    pbs = [p for p in pbs if p]
    if not pbs:
        return 0
    for p in pbs:
        p.rotation_mode = 'XYZ'
    t, cur = 0.0, (0.0, 0.0)
    while t * fps < n + 2:
        f = 1 + int(t * fps)
        for p in pbs:
            p.rotation_euler = Euler((math.radians(cur[0]), 0, math.radians(cur[1])))
            p.keyframe_insert('rotation_euler', frame=f)
        nxt = (rng.uniform(-amp, amp) * 0.6, rng.uniform(-amp, amp))
        for p in pbs:                                   # перескок за 3 кадра
            p.rotation_euler = Euler((math.radians(nxt[0]), 0, math.radians(nxt[1])))
            p.keyframe_insert('rotation_euler', frame=f + 3)
        cur = nxt
        t += rng.uniform(1.0, 2.8)
    return 1


def animate(rig, info, n, fps, words_path, wav_path, seed=1, smile=0.0, talk=True):
    """всё вместе для плана ведущего; info - запись плана из shots.json (start)"""
    rng = random.Random(seed)
    words = []
    if words_path and os.path.exists(words_path):
        w = json.load(open(words_path, encoding='utf-8'))
        words = w['words'] if isinstance(w, dict) else w
    g0 = round(info.get('start', 0.0) * fps) / fps      # кадр 1 плана = этот момент озвучки (как режет assemble.py)
    res = {}
    if talk:
        res['visemes'] = lipsync(rig, words, g0, n, fps, wav=wav_path if wav_path and os.path.exists(wav_path) else None)
        brows_on_words(rig, words, g0, n, fps, rng)
    res['blinks'] = blinks(rig, n, fps, rng)
    res['eyes'] = eye_darts(rig, n, fps, rng)
    if smile:
        t_on = int(0.45 * fps)
        accent(rig, {'mouthSmileLeft': smile, 'mouthSmileRight': smile, 'cheekSquintLeft': smile * 0.2,
                     'cheekSquintRight': smile * 0.2}, [(1, 0.15), (t_on, 0.3), (t_on + 12, 1.0), (n, 1.0)])
    return res
