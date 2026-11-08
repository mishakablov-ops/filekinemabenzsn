"""Shot recipes for «Эскалатор». Each function builds the scene for one shot and animates the camera.
Signature: fn(scene, dur_s, fps, shot_info) -> dict
Ведущий и толпа берутся из D:\\aipollon\\eskalator\\assets (hero.blend, crowd.blend; см. esk_hero.py),
путь можно переопределить переменной окружения ESK_ASSETS. Без этих файлов сцены строятся без людей.

Живая толпа (08.11.2026, «добавить побольше жизни людям»): если есть crowd_rig.blend и mocap/mocap.blend,
люди ставятся с костями и мокапом CMU (esk_mocap.py): ждут и переминаются, листают телефон, разговаривают
парами, проходят по залу, едут на ступенях. Без этих файлов - прежние статичные фигуры из crowd.blend.
Ведущий: мокап верха тела и мимика под голос (esk_face.py, assets/voice/words.json + voice.wav)."""
import bpy, math, os, random
from mathutils import Vector
import esk_mech as E, esk_studio as S, esk_metro as MT, esk_hero as H, esk_places as PL
import esk_mocap as MC, esk_face as FC

ASSETS = os.environ.get('ESK_ASSETS', r'D:\aipollon\eskalator\assets')


def ease(u, p=1.8):
    u = max(0.0, min(1.0, u))
    return u ** p / (u ** p + (1 - u) ** p) if 0 < u < 1 else u


def cam_move(sc, dur, fps, a, b, ta, tb, lens=(35, 35), name='Cam', step=1, dof=None, parent=None, p=1.8, focus=None):
    """camera from a->b looking from ta->tb, smooth ease, baked keys (linear between bakes).
    parent: object to ride on (keys are then in its local space)"""
    cam = S.camera(a, ta, lens=lens[0], name=name)
    tgt = bpy.data.objects.new(name + 'Tgt', None); sc.collection.objects.link(tgt)
    con = cam.constraints.new('TRACK_TO'); con.target = tgt; con.track_axis = 'TRACK_NEGATIVE_Z'; con.up_axis = 'UP_Y'
    foc = None
    if focus:      # точка резкости отдельно от точки взгляда (лицо, а не центр тела за ним)
        foc = bpy.data.objects.new(name + 'Foc', None); sc.collection.objects.link(foc)
    if dof:
        cam.data.dof.use_dof = True; cam.data.dof.focus_object = foc or tgt; cam.data.dof.aperture_fstop = dof
    if parent is not None:
        cam.parent = parent; tgt.parent = parent
        if foc:
            foc.parent = parent
    n = sc.frame_end
    for f in range(1, n + 1, step):
        u = ease((f - 1) / max(1, n - 1), p)
        cam.location = Vector(a).lerp(Vector(b), u); cam.keyframe_insert('location', frame=f)
        tgt.location = Vector(ta).lerp(Vector(tb), u); tgt.keyframe_insert('location', frame=f)
        if foc:
            foc.location = Vector(focus[0]).lerp(Vector(focus[1]), u); foc.keyframe_insert('location', frame=f)
        cam.data.lens = lens[0] + (lens[1] - lens[0]) * u; cam.data.keyframe_insert('lens', frame=f)
    for ob in (cam, tgt, cam.data) + ((foc,) if foc else ()):
        ad = ob.animation_data
        if ad and ad.action:
            for fc in E.iter_fcurves(ad.action):
                for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'
    return cam


# ----------------------------------------------------------------------------- люди
_CROWD = {}
_RIGS = {}


def crowd():
    p = os.path.join(ASSETS, 'crowd.blend')
    if not _CROWD and os.path.exists(p):
        _CROWD.update(H.load_crowd(p))
    return list(_CROWD.values())


def crowd_rigs():
    p = os.path.join(ASSETS, 'crowd_rig.blend')
    if not _RIGS and os.path.exists(p):
        _RIGS.update(H.load_crowd_rigs(p))
    return list(_RIGS.values())


def acts():
    return MC.load_actions(os.path.join(ASSETS, 'mocap', 'mocap.blend'))


def voice():
    d = os.path.join(ASSETS, 'voice')
    return os.path.join(d, 'words.json'), os.path.join(d, 'voice.wav')


def live():
    return bool(crowd_rigs()) and bool(acts())


def _people_col(sc):
    col = bpy.data.collections.get('People')
    if col is None:
        col = bpy.data.collections.new('People')
        sc.collection.children.link(col)
    return col


def _pick(kind, n, rng, need=0):
    pool = [a for a in MC.by_kind(kind) if a['esk_frames'] >= need] or MC.by_kind(kind)
    a = rng.choice(pool)
    off = rng.randint(0, max(0, a['esk_frames'] - n - 2))
    return a, off


def person(sc, rng, role, loc, rot_z=0.0, parent=None, src=None, act=None, offset=None):
    """живой человек. role: idle | phone | talk | walk | ride (стоит на ступени).
    Возвращает риг (или статичный меш, если живых людей нет)."""
    n = sc.frame_end
    if not live():
        ppl = crowd()
        if not ppl:
            return None
        ob = H.place_person(sc, rng.choice(ppl), loc, rot_z)
        if parent is not None:
            ob.parent = parent
            ob.location = loc
        return ob
    src = src or rng.choice(crowd_rigs())
    rig = H.clone_person(src, _people_col(sc), phone=(role == 'phone'))
    rig.parent = parent
    rig.location = loc
    rig.rotation_euler = (0, 0, rot_z)
    if act is None:
        kind = {'walk': 'walk', 'talk': 'talk'}.get(role, 'idle')
        act, off = _pick(kind, n, rng, need=(n + 2 if role == 'walk' else 0))
        offset = off if offset is None else offset
    offset = offset or 0
    if role == 'phone':
        for b, q in dict(src.get('esk_phone_pose', {})).items():   # руки с телефоном у груди, голова опущена
            pb = rig.pose.bones.get(b)
            if pb:
                pb.rotation_mode = 'QUATERNION'
                pb.rotation_quaternion = tuple(q)
        MC.play(rig, act, offset, skip=MC.ARM_L + MC.ARM_R + MC.HEAD)
    else:
        MC.play(rig, act, offset)
    rig['esk_role'] = role
    return rig


def lod_people(sc, near=6.0):
    """дальним живым людям - без сглаживания (subdivision): на расстоянии не видно, а считать в разы дольше"""
    col = bpy.data.collections.get('People')
    if col is None or sc.camera is None:
        return 0
    n = sc.frame_end
    cams = []
    for f in sorted({1, max(1, n // 2), n}):
        sc.frame_set(f)
        cams.append(sc.camera.matrix_world.translation.copy())
    k = 0
    for o in col.objects:
        if o.type != 'ARMATURE':
            continue
        p = o.matrix_world.translation
        if min((p - c).length for c in cams) > near:
            for ch in o.children:
                for md in ch.modifiers:
                    if md.type == 'SUBSURF':
                        md.levels = 0
                        md.render_levels = 0
            k += 1
    sc.frame_set(1)
    return k


def hero(sc, parent=None, loc=(0, 0, 0), rot_z=0.0, pose='stand'):
    p = os.path.join(ASSETS, 'hero.blend')
    if not os.path.exists(p):
        return None
    rig, col = H.load_hero(p, sc)
    if parent is not None:
        rig.parent = parent
    rig.location = loc
    rig.rotation_euler = (0, 0, rot_z)
    bpy.context.view_layer.update()
    if pose:
        H.pose(rig, pose)
    return rig


def hero_live(sc, rig, info, fps, kind='idle', clip=None, only=None, skip=(), talk=True, smile=0.0, seed=1):
    """ведущий оживает: мокап (часть костей) + мимика под голос"""
    if rig is None:
        return {}
    n = sc.frame_end
    res = {}
    if acts():
        a = MC._ACTS.get(clip) if clip else None
        rng = random.Random(seed)
        if a is None:
            a, off = _pick(kind, n, rng)
        else:
            off = rng.randint(0, max(0, a['esk_frames'] - n - 2))
        MC.play(rig, a, off, skip=skip, only=only)
        res['mocap'] = (a.name, off)
    w, v = voice()
    res['face'] = FC.animate(rig, info, n, fps, w, v, seed=seed, smile=smile, talk=talk)
    return res


def step_at(e, s0, x_target, v=0.0, t=0.0):
    """index and object of the step whose front axle is nearest x_target at time t (upper run only)"""
    P = e.path
    best = None
    for i, st in enumerate(e.steps):
        p, th = P.at(s0 + i * P.pitch + v * t)
        if th != 0.0:
            continue
        d = abs(p.x - x_target)
        if best is None or d < best[0]:
            best = (d, i, st)
    return best[1], best[2]


def tread(dx=0.0, dy=0.0):
    """centre of the tread in step-local space"""
    return (-E.TREAD_D / 2 + dx, dy, E.TREAD_Z)


def fill_steps(sc, m, dur, rng, density=0.5, skip=(), margin=1.1, live_near=None):
    """passengers on the moving steps: stand on the right, a few on the left; never ride into a comb.
    live_near=(x, r): живые (с мокапом) только ступени в r метрах от x, дальние - статичные (длинный туннель)"""
    ppl = crowd()
    if not ppl and not live():
        return 0
    k_n = 0
    for k, e in enumerate(m['escs']):
        v = m['speeds'][k]
        s0 = k * 0.13
        P = e.path
        for i, st in enumerate(e.steps):
            if (k, i) in skip:
                continue
            p, th = P.at(s0 + i * P.pitch)
            if th != 0.0:
                continue
            x1 = p.x + v * dur
            lo, hi = P.x0 + margin, P.x1 - margin
            if not (lo < p.x < hi and lo < x1 < hi):
                continue
            if rng.random() > density:
                continue
            right = -0.22 if v > 0 else 0.22
            if rng.random() < 0.2:
                right = -right
            loc = tread(rng.uniform(-0.02, 0.02), right + rng.uniform(-0.05, 0.05))
            rz = (math.pi / 2 if v > 0 else -math.pi / 2) + rng.uniform(-0.3, 0.3)
            if live() and (live_near is None or abs(p.x - live_near[0]) < live_near[1]):
                person(sc, rng, 'phone' if rng.random() < 0.3 else 'ride', loc, rz, parent=st)
            elif ppl:
                ob = H.place_person(sc, rng.choice(ppl), (0, 0, 0), 0)
                ob.parent = st
                ob.location = loc
                ob.rotation_euler = (0, 0, rz)
            k_n += 1
    return k_n


def fill_hall(sc, m, rng, n=30, top=True, depth=11.0, avoid=()):
    P = m['path']
    W = m['width'] + 6
    lanes = [e.origin.y for e in m['escs']]
    if top:
        xa, xb, z, xm = P.x1 + 0.8, P.x1 + depth, P.rise + E.TREAD_Z, P.x1
    else:
        xa, xb, z, xm = P.x0 - depth, P.x0 - 0.8, E.TREAD_Z, P.x0
    ya, yb = -W / 2 + 0.7, W / 2 - 0.7

    def free(x, y, r=0.0, taken=()):
        if not (xa - 0.01 <= x <= xb + 0.01 and ya <= y <= yb):
            return False
        if abs(x - xm) < 2.6 and min(abs(y - ly) for ly in lanes) < 0.85:
            return False
        if any((x - ax) ** 2 + (y - ay) ** 2 < ar * ar for (ax, ay, ar) in avoid):
            return False
        return all((x - tx) ** 2 + (y - ty) ** 2 >= (r + tr) ** 2 for (tx, ty, tr) in taken)

    if not live():
        ppl = crowd()
        if not ppl:
            return 0
        c = tries = 0
        while c < n and tries < n * 20:
            tries += 1
            x, y = rng.uniform(xa, xb), rng.uniform(ya, yb)
            if not free(x, y):
                continue
            H.place_person(sc, rng.choice(ppl), (x, y, z), rng.uniform(0, 2 * math.pi))
            c += 1
        return c

    nf = sc.frame_end
    taken = []                                        # (x, y, радиус) стоящих
    c = 0
    # 1) пары разговаривают (18_08 и 19_08 - одна запись, поэтому смотрят друг на друга и жесты в такт)
    pa, pb = MC._ACTS.get('mc_talk_18_08'), MC._ACTS.get('mc_talk_19_08')
    for _ in range(max(0, n // 9)):
        for _t in range(30):
            x, y = rng.uniform(xa, xb), rng.uniform(ya, yb)
            ang = rng.uniform(0, 2 * math.pi)
            d = rng.uniform(1.0, 1.25)
            x2, y2 = x + math.cos(ang) * d, y + math.sin(ang) * d
            if free(x, y, 0.4, taken) and free(x2, y2, 0.4, taken):
                break
        else:
            continue
        off = rng.randint(0, 120)
        if pa and pb:
            person(sc, rng, 'talk', (x, y, z), math.atan2(x2 - x, -(y2 - y)), act=pa, offset=off)
            person(sc, rng, 'talk', (x2, y2, z), math.atan2(x - x2, -(y - y2)), act=pb, offset=off)
        else:
            person(sc, rng, 'talk', (x, y, z), math.atan2(x2 - x, -(y2 - y)))
            person(sc, rng, 'talk', (x2, y2, z), math.atan2(x - x2, -(y - y2)))
        taken += [(x, y, 0.4), (x2, y2, 0.4)]
        c += 2
    # 2) стоят: ждут, переминаются, смотрят в телефон
    n_walk = max(1, n // 4)
    tries = 0
    while c < n - n_walk and tries < n * 25:
        tries += 1
        x, y = rng.uniform(xa, xb), rng.uniform(ya, yb)
        if not free(x, y, 0.35, taken):
            continue
        person(sc, rng, 'phone' if rng.random() < 0.35 else 'idle', (x, y, z), rng.uniform(0, 2 * math.pi))
        taken.append((x, y, 0.35))
        c += 1
    # 3) идут: путь проверяется по кадрам, чтобы не пройти сквозь людей, эскалатор и друг друга
    walkers = []
    tries = 0
    while len(walkers) < n_walk and tries < n_walk * 40:
        tries += 1
        a, off = _pick('walk', nf, rng, need=nf + 2)
        r = rng.random()
        if r < 0.35:                                  # сошёл с эскалатора и уходит / идёт к эскалатору
            hd = 0.0 if top else math.pi
            if rng.random() < 0.4:
                hd += math.pi
        elif r < 0.7:
            hd = rng.choice([math.pi / 2, -math.pi / 2])  # поперёк зала
        else:
            hd = rng.uniform(0, 2 * math.pi)
        hd += rng.uniform(-0.25, 0.25)
        ux, uy = math.cos(hd), math.sin(hd)
        rz = math.atan2(ux, -uy)                      # клип идёт в -Y рига
        cz, sz = math.cos(rz), math.sin(rz)
        x0, y0 = rng.uniform(xa, xb), rng.uniform(ya, yb)
        tr = MC.root_track(crowd_rigs()[0], a, [1 + off + k for k in range(0, nf + 1, 6)])
        bx, by = tr[0]
        path = [(x0 + cz * (tx - bx) - sz * (ty - by), y0 + sz * (tx - bx) + cz * (ty - by)) for (tx, ty) in tr]
        if not all(free(px, py, 0.35, taken) for (px, py) in path):
            continue
        if any(any((p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2 < 0.7 ** 2 for p, q in zip(path, w)) for w in walkers):
            continue
        # риг ставим так, чтобы на первом кадре плана человек был в (x0, y0)
        person(sc, rng, 'walk', (x0 - (cz * bx - sz * by), y0 - (sz * bx + cz * by), z), rz, act=a, offset=off)
        walkers.append(path)
        c += 1
    return c


def metro_light(strength=0.25):
    S.world('#FFE8C8', strength)


def metro(sc, fps, rise=6.0, lanes=3, every=1, seed=1, density=0.55, hall_n=30, skip=(), lamp_every=3.2, speeds=None, avoid=(),
          live_near=None):
    n = sc.frame_end
    m = MT.build(rise=rise, lanes=lanes, animate=(1, n, fps), every=every, lamp_every=lamp_every, speeds=speeds)
    rng = random.Random(seed)
    dur = n / fps
    fill_steps(sc, m, dur, rng, density=density, skip=skip, live_near=live_near)
    if hall_n:
        fill_hall(sc, m, rng, n=hall_n, top=True, avoid=avoid)
        fill_hall(sc, m, rng, n=hall_n // 2, top=False, avoid=avoid)
    metro_light()
    return m


def studio_esk(sc, dur, fps, near_truss=True, s0=0.0, speed=0.75, rise=3.0):
    esk = E.Escalator(rise=rise)
    if not near_truss:
        bpy.data.objects.remove(esk.truss[-1])
    esk.animate(1, sc.frame_end, fps, speed=speed, s0=s0)
    S.world('#F3F1EE', 0.8, cam_col='#B5121B'); S.backdrop(center=(4, 0, 0)); S.lights(center=(4, 0, 1.5))
    return esk


# ============================================================================= 1. Хук
def S01(sc, dur, fps, info):      # «Под твоими ногами прямо сейчас едут ступеньки» - кеды ведущего на ступени
    m = metro(sc, fps, rise=6.0, seed=11, skip={(0, i) for i in range(0)})
    e = m['escs'][0]
    i, st = step_at(e, 0.0, 2.6)
    # освободить соседние ступени от людей (камера стоит на них)
    for ob in list(st.children):
        bpy.data.objects.remove(ob)
    for j in (i - 3, i - 2, i - 1, i + 1):
        if 0 <= j < len(e.steps):
            for ob in list(e.steps[j].children):
                bpy.data.objects.remove(ob)
    rig = hero(sc, parent=st, loc=tread(0.0, 0.05), rot_z=math.pi / 2, pose='stand')
    # камера едет вместе со ступенью: низко сзади, у пяток, и наезжает к щели между ступенями
    cam_move(sc, dur, fps, (-1.05, -0.34, 0.58), (-0.66, -0.20, 0.40), (-0.12, 0.02, 0.42), (-0.22, 0.0, 0.30),
             lens=(24, 26), dof=2.8, parent=st, name='CamS01')
    return {}


def S02(sc, dur, fps, info):      # «Вверх ногами» - обратная ветка: ступени едут перевёрнутыми
    studio_esk(sc, dur, fps, near_truss=False)
    cam_move(sc, dur, fps, (1.4, -1.55, 0.05), (2.3, -1.35, 0.25), (2.6, 0, 0.35), (3.6, 0, 0.75), lens=(26, 28), dof=3.5)
    return {}


# ============================================================================= 2-6. Механика (студия)
def S03(sc, dur, fps, info):      # «Эскалатор это одна длинная петля» - вся петля, 3/4 снизу
    studio_esk(sc, dur, fps)
    # снизу-сбоку вдоль подъёма: петля уходит по диагонали кадра и заполняет вертикаль
    cam_move(sc, dur, fps, (-1.4, -2.3, -0.35), (-0.8, -2.6, 0.05), (3.4, 0, 1.25), (3.9, 0, 1.45), lens=(18, 18))
    return {}


def S04(sc, dur, fps, info):      # «Ступени сцеплены цепью» - цепь на подъёме
    studio_esk(sc, dur, fps, near_truss=False)
    cam_move(sc, dur, fps, (2.2, -1.7, 0.45), (3.3, -1.55, 0.95), (3.0, -0.5, 0.95), (4.0, -0.5, 1.5), lens=(40, 44), dof=4.0)
    return {}


def S05(sc, dur, fps, info):      # «наверху каждая ныряет вниз и едет обратно под тобой» - верхняя звёздочка
    studio_esk(sc, dur, fps, near_truss=False)
    cam_move(sc, dur, fps, (9.6, -2.6, 3.4), (9.2, -2.0, 2.5), (8.2, 0, 2.6), (8.3, 0, 2.3), lens=(30, 32))
    return {}


def S06(sc, dur, fps, info):      # «как наверху они становятся ровным полом?» - верхняя площадка сверху
    studio_esk(sc, dur, fps)
    cam_move(sc, dur, fps, (5.0, -1.5, 5.6), (6.6, -1.1, 5.0), (5.6, 0, 3.1), (7.0, 0, 3.3), lens=(28, 30))
    return {}


def S07(sc, dur, fps, info):      # «У каждой ступени две пары колёс» - одна ступень крупно, колёса светятся
    col = E.coll('Hero')
    Mx = E.materials()
    Mx['wheel_a'] = E.mat('EskWheelGlowA', '#39E46B', rough=0.4, emit=3.0)
    Mx['wheel_b'] = E.mat('EskWheelGlowB', '#FF9A1A', rough=0.4, emit=3.0)
    st = E.step_mesh('HeroStep', col, Mx)
    st.location = (0, 0, 0.6)
    n = sc.frame_end
    for f in range(1, n + 1):
        u = (f - 1) / max(1, n - 1)
        st.rotation_euler = (0, 0, math.radians(20 + 55 * u)); st.keyframe_insert('rotation_euler', frame=f)
    S.world('#F3F1EE', 0.9, cam_col='#B5121B'); S.backdrop(center=(0, 0, 0), wall_y=2.0); S.lights(center=(0, 0, 0.8))
    cam_move(sc, dur, fps, (-1.35, -1.55, 1.70), (-1.20, -1.35, 1.55), (-0.17, 0, 0.72), (-0.17, 0, 0.74), lens=(52, 58), dof=4.0)
    return {}


def S08(sc, dur, fps, info):      # «по двум разным рельсам» - вдоль рельсов под ступенями
    esk = studio_esk(sc, dur, fps, near_truss=False)
    P = esk.path
    a = Vector((1.6, -1.05, P.z_of(1.6) + 0.15)); b = Vector((3.6, -1.05, P.z_of(3.6) + 0.15))
    cam_move(sc, dur, fps, a, b, (2.6, -0.5, P.z_of(2.6) + 0.1), (4.6, -0.5, P.z_of(4.6) + 0.1), lens=(32, 32), dof=1.2)
    return {}


def S09(sc, dur, fps, info):      # «на подъёме рельсы расходятся, ступень встаёт лесенкой» - бок подъёма
    studio_esk(sc, dur, fps, near_truss=False)
    cam_move(sc, dur, fps, (2.4, -3.6, 1.2), (3.4, -3.3, 1.8), (2.6, 0, 1.1), (3.6, 0, 1.6), lens=(42, 46))
    return {}


def S10(sc, dur, fps, info):      # «у выхода они сходятся, ступени складываются в плоскую дорожку»
    studio_esk(sc, dur, fps, near_truss=False)
    cam_move(sc, dur, fps, (5.4, -3.4, 2.9), (6.8, -3.2, 3.3), (5.6, 0, 2.7), (7.0, 0, 3.0), lens=(40, 44))
    return {}


def S11(sc, dur, fps, info):      # «эта гребёнка входит в пазы ступени» - гребёнка макро
    esk = studio_esk(sc, dur, fps)
    P = esk.path; z = P.rise + E.TREAD_Z
    x = P.x1 - 0.55
    cam_move(sc, dur, fps, (x - 0.55, -0.55, z + 0.32), (x - 0.35, -0.42, z + 0.18), (x, -0.1, z), (x + 0.02, -0.15, z), lens=(50, 60), dof=2.0)
    return {}


def S12(sc, dur, fps, info):      # «чтобы в щель не затянуло ни шнурок, ни каблук» - кед подъезжает к гребёнке
    m = metro(sc, fps, rise=6.0, seed=12, density=0.35)
    e = m['escs'][0]
    P = e.path
    xc = P.x1 - 0.55
    v = m['speeds'][0]
    # ступень, у которой в конце плана носок кеда в 12 см от гребёнки
    i, st = step_at(e, 0.0, xc - 0.10, v=v, t=dur)
    for j in (i - 1, i, i + 1, i + 2, i + 3):
        if 0 <= j < len(e.steps):
            for ob in list(e.steps[j].children):
                bpy.data.objects.remove(ob)
    hero(sc, parent=st, loc=tread(0.0, 0.10), rot_z=math.pi / 2, pose='stand')
    y = e.origin.y
    z = P.rise + E.TREAD_Z
    cam_move(sc, dur, fps, (xc + 0.45, y - 0.12, z + 0.16), (xc + 0.32, y - 0.10, z + 0.12),
             (xc - 0.45, y + 0.04, z + 0.06), (xc - 0.22, y + 0.06, z + 0.04), lens=(55, 65), dof=2.8)
    return {}


def S13(sc, dur, fps, info):      # «Поручень тянет тот же мотор» - машинное отделение
    esk = studio_esk(sc, dur, fps, near_truss=False)
    cam_move(sc, dur, fps, (10.6, -2.3, 1.2), (9.9, -1.9, 1.7), (9.0, 0.3, 1.8), (8.8, 0.3, 2.1), lens=(30, 34))
    return {}


def S14(sc, dur, fps, info):      # «поэтому он едет с той же скоростью, что и ты» - рука на поручне
    m = metro(sc, fps, rise=6.0, seed=14, density=0.5)
    e = m['escs'][0]
    i, st = step_at(e, 0.0, 1.9)
    for j in (i - 1, i, i + 1, i + 2, i + 3):
        if 0 <= j < len(e.steps):
            for ob in list(e.steps[j].children):
                bpy.data.objects.remove(ob)
    rig = hero(sc, parent=st, loc=tread(0.0, 0.08), rot_z=math.pi / 2, pose='stand')
    P = e.path
    if rig:
        bpy.context.view_layer.update()
        # левая рука на внутреннем поручне (+Y от оси ленты)
        p, _ = P.at(0.0 + i * P.pitch)
        hx = p.x - 0.02
        hand = Vector((hx, e.origin.y + E.STEP_W / 2 + 0.06 - 0.03, P.z_of(hx) + E.TREAD_Z + 0.92 + 0.06))
        H.reach(rig, 'L', hand, pole=(0, 0.3, -1))
        hero_live(sc, rig, info, fps, kind='idle', only=MC.HEAD + MC.ARM_R, talk=False, seed=14)   # голова и свободная рука живые, левая на поручне
    cam_move(sc, dur, fps, (0.62, 0.20, 1.42), (0.52, 0.26, 1.34), (-0.05, 0.50, 1.15), (-0.08, 0.52, 1.12),
             lens=(32, 35), dof=2.4, parent=st, name='CamS14')
    return {}


# ============================================================================= 7. Москва
def S15(sc, dur, fps, info):      # «В московском метро таких машин 1133» - зал наверху, вниз уходят 3 ленты
    P0 = E.Path(rise=6.0, land_lo=3.0, land_hi=3.0)
    m = metro(sc, fps, rise=6.0, seed=15, density=0.7, hall_n=45, avoid=[(P0.x1 + 5.5, 1.2, 2.6)])
    P = m['path']
    zt = P.rise + E.TREAD_Z
    cam_move(sc, dur, fps, (P.x1 + 6.5, 1.6, zt + 3.4), (P.x1 + 4.6, 0.8, zt + 2.9), (P.x0 + 2, 0, 1.0), (P.x0 + 1, 0, 0.6), lens=(22, 24))
    return {}


def long_tunnel(sc, fps, seed=16, density=0.28, hall_n=20, live_near=None):
    # «Парк Победы»: подъём ~63 м, лента ~126 м; ключи раз в 10 кадров (на прямом подъёме это точно)
    # живые (с мокапом) только пассажиры рядом с камерой: остальные 200+ - статичные фигуры вдали
    return metro(sc, fps, rise=63.0, lanes=3, every=10, seed=seed, density=density, hall_n=hall_n, lamp_every=4.0,
                 live_near=live_near)


def S16(sc, dur, fps, info):      # «Самая длинная на Парке Победы: 126 метров» - туннель сверху вниз
    P0 = E.Path(rise=63.0, land_lo=3.0, land_hi=3.0)
    m = long_tunnel(sc, fps, live_near=(P0.x1 - 10.0, 14.0))
    P = m['path']
    zt = P.rise + E.TREAD_Z
    cam_move(sc, dur, fps, (P.x1 + 1.5, 0.0, zt + 2.6), (P.x1 - 3.0, 0.0, zt + 2.3), (P.x1 - 40, 0, zt - 21), (P.x1 - 45, 0, zt - 25),
             lens=(24, 26))
    return {}


def S17(sc, dur, fps, info):      # «а подъём на 63 метра. Это дом в двадцать этажей» - разрез земли и дом
    g = PL.ground_section(rise=63.0)
    S.world('#CFE3F2', 0.9)
    sd = bpy.data.lights.new('Sun', 'SUN'); sd.energy = 4.0; sd.angle = math.radians(2)
    so = bpy.data.objects.new('Sun', sd); so.rotation_euler = (math.radians(48), 0, math.radians(-35))
    sc.collection.objects.link(so)
    run, zb = g['run'], g['zb']
    # портрет: смотрим на разрез под углом ~58°, чтобы туннель (109 м по горизонтали) сжался и дом с глубиной влезли по высоте
    cam_move(sc, dur, fps, (run - 4, -38, -48), (run - 14, -122, -4), (run - 4, 0, -52), (run - 14, 0, -4), lens=(40, 50), p=1.6)
    return {}


def S18(sc, dur, fps, info):      # «Едешь почти три минуты» - ведущий на бесконечном эскалаторе
    P0 = E.Path(rise=63.0, land_lo=3.0, land_hi=3.0)
    m = long_tunnel(sc, fps, seed=18, density=0.3, live_near=(P0.x1 * 0.45, 12.0))
    e = m['escs'][0]
    P = e.path
    i, st = step_at(e, 0.0, P.x1 * 0.45)
    for j in range(i - 1, i + 6):
        if 0 <= j < len(e.steps):
            for ob in list(e.steps[j].children):
                bpy.data.objects.remove(ob)
    rig = hero(sc, parent=st, loc=tread(0.0, 0.06), rot_z=math.pi / 2, pose='stand')
    if rig:
        bpy.context.view_layer.update()
        p, _ = P.at(i * P.pitch)
        hx = p.x - 0.02
        hand = Vector((hx, e.origin.y + E.STEP_W / 2 + 0.06 - 0.03, P.z_of(hx) + E.TREAD_Z + 0.92 + 0.06))
        H.reach(rig, 'L', hand, pole=(0, 0.3, -1))
        # говорит в камеру: голова и правая рука из мокапа «объясняет жестами», губы под голос, моргает
        hero_live(sc, rig, info, fps, clip='mc_talk_18_08', only=MC.HEAD + MC.ARM_R, seed=18)
    # камера на ступенях выше и смотрит вниз на лицо, за спиной туннель уходит вниз
    cam_move(sc, dur, fps, (1.55, -0.30, 2.25), (1.35, -0.22, 2.15), (-0.15, 0.05, 1.80), (-0.15, 0.05, 1.78),
             lens=(40, 44), dof=2.8, parent=st, name='CamS18')
    k1 = S.area('HostKey', (0.9, -0.9, 2.5), (-0.15, 0.05, 1.85), 60, 1.0, col='#FFE4C8')
    k1.parent = st
    return {}


# ============================================================================= 8. Слово
def S19(sc, dur, fps, info):      # «А «эскалатор» когда-то был названием бренда» - универмаг 1900-х
    d = PL.old_store(rise=4.0)
    d['esk'].animate(1, sc.frame_end, fps, speed=0.5)
    P = d['path']
    rng = random.Random(19)
    for k in range(10):
        x = rng.uniform(-10, -2.5) if k % 2 else rng.uniform(P.x1 + 1, P.x1 + 8)
        z = E.TREAD_Z if x < 0 else P.rise + E.TREAD_Z
        person(sc, rng, 'idle', (x, rng.choice([-1, 1]) * rng.uniform(2.0, 5.5), z), rng.uniform(0, 6.28))
    S.world('#F1D9B0', 0.35)
    S.area('Win', (-6, -14, 9), (2, 0, 2), 9000, 10, col='#FFE3B5')
    cam_move(sc, dur, fps, (-6.5, -6.2, 1.5), (-5.2, -5.0, 2.0), (P.x1 * 0.5, 0.8, P.rise + 2.2), (P.x1 * 0.5, 1.0, P.rise + 3.0),
             lens=(26, 30))
    return {}


def S20(sc, dur, fps, info):      # «В 1950 году его признали обычным словом» - штамп на документе
    n = sc.frame_end
    PL.stamp_doc(sc, f_hit=int(n * 0.38), n=n)
    S.world('#2A2622', 0.4)
    S.area('Desk', (-0.6, -0.8, 1.4), (0, 0, 0), 120, 1.2, col='#FFE3C0')
    S.area('Fill', (0.9, -0.5, 0.8), (0, 0, 0), 30, 1.5, shadow=False)
    cam_move(sc, dur, fps, (0.05, -0.62, 0.78), (0.06, -0.48, 0.62), (0.02, 0.0, 0.0), (0.06, -0.02, 0.0), lens=(40, 42), dof=4.0)
    return {}


def S20B(sc, dur, fps, info):     # «так уже звали любую движущуюся лестницу» - торговый центр
    d = PL.mall()
    for k, e in enumerate(d['escs']):
        e.animate(1, sc.frame_end, fps, speed=0.6, s0=k * 0.1)
    P = d['path']
    rng = random.Random(20)
    for k, e in enumerate(d['escs']):
        for i, st in enumerate(e.steps):
            p, th = e.path.at(k * 0.1 + i * e.path.pitch)
            if th == 0 and P.x0 + 1 < p.x < P.x1 - 1.6 and rng.random() < 0.3:
                person(sc, rng, 'phone' if rng.random() < 0.3 else 'ride', tread(0, -0.2), math.pi / 2, parent=st)
    for lvl in range(3):
        for k in range(14):
            x = rng.uniform(P.x0 - 7, P.x1 + 7); y = rng.choice([-1, 1]) * rng.uniform(7.5, 11.5)
            r = rng.random()
            person(sc, rng, 'phone' if r < 0.3 else 'idle', (x, y, lvl * d['lvl'] + E.TREAD_Z), rng.uniform(0, 6.28))
    S.world('#F4F2EE', 0.12)
    cx = (P.x0 + P.x1) / 2
    S.area('Sky', (cx, 0, 18), (cx, 0, 0), 4000, 14, col='#FFFFFF')
    for lv in range(3):
        for xx in (P.x0 - 4, cx, P.x1 + 4):
            for yy in (-9.5, 9.5):
                S.area('Ceil', (xx, yy, lv * d['lvl'] + 4.3), (xx, yy, lv * d['lvl']), 600, 3.0, col='#FFF4E6', shadow=False)
    cam_move(sc, dur, fps, (P.x0 - 0.6, -4.6, 1.7), (P.x0 + 0.4, -4.4, 8.8), (P.x1 + 1, 0.8, 4.2), (P.x1 + 1, 0.8, 9.2), lens=(20, 20))
    return {}


# ============================================================================= 9. Концовка
def S21(sc, dur, fps, info):      # «Оставь лайк, если узнал что-то новое» - ведущий поворачивается к камере
    P0 = E.Path(rise=6.0, land_lo=3.0, land_hi=3.0)
    hx, hy = P0.x1 + 6.0, -2.6
    cx, cy = hx + 0.84, hy - 0.32                      # камера ~0,9 м, 70 мм: голова и грудь, как в образце
    m = metro(sc, fps, rise=6.0, seed=21, density=0.6, hall_n=40,
              avoid=[(hx, hy, 1.2), (cx, cy, 1.1), ((hx + cx) / 2, (hy + cy) / 2, 0.9), (cx + 1.0, cy - 0.4, 1.0)])
    P = m['path']
    zt = P.rise + E.TREAD_Z
    face = math.atan2(cy - hy, cx - hx) + math.pi / 2   # MakeHuman смотрит в -Y
    rig = hero(sc, loc=(hx, hy, zt), rot_z=face, pose='stand')
    n = sc.frame_end
    if rig:
        a0, a1 = face - math.radians(65), face
        t_turn = int(0.6 * fps)
        for f in range(1, n + 1):
            u = ease(min(1.0, (f - 1) / t_turn))
            rig.rotation_euler = (0, 0, a0 + (a1 - a0) * u)
            rig.keyframe_insert('rotation_euler', frame=f)
        # верх тела жестикулирует (мокап «объясняет жестами»), ноги стоят; губы под голос, улыбка к концу
        # крупный план головы и груди: из мокапа только голова (корпус и плечи на крупном плане дают «вздутую» грудь)
        live = hero_live(sc, rig, info, fps, clip='mc_talk_18_08', only=MC.HEAD, smile=0.3, seed=21)
        if not (live.get('face') or {}).get('visemes'):            # старый hero.blend без мимики: улыбка костями
            for f in range(1, n + 1):
                k = ease(min(1.0, max(0.0, (f - t_turn * 0.6) / (0.5 * fps))))
                for side, sx in (('L', 1), ('R', -1)):
                    for bn, dw in (('risorius03.', (sx * 0.003, 0.002, 0.0035)), ('levator05.', (0, 0, 0.0015))):
                        pb = rig.pose.bones.get(bn + side)
                        if pb:
                            H.nudge(rig, bn + side, dw, k)
                            pb.keyframe_insert('location', frame=f)
    host_light(sc, (hx, hy, zt + 1.66), (cx, cy))
    L = math.hypot(cx - hx, cy - hy)
    eye = (hx + (cx - hx) / L * 0.14, hy + (cy - hy) / L * 0.14, zt + 1.685)   # глаза ~14 см перед осью рига
    cam_move(sc, dur, fps, (cx + 0.10, cy - 0.04, zt + 1.62), (cx, cy, zt + 1.61),
             (hx, hy, zt + 1.52), (hx, hy, zt + 1.53), lens=(68, 72), dof=5.6, focus=(eye, eye))
    return {}


def host_light(sc, head, cam_xy, parent=None):
    """мягкий тёплый ключ на лицо ведущего сбоку от камеры + холодный контровой сзади"""
    hx, hy, hz = head
    cx, cy = cam_xy
    dx, dy = cx - hx, cy - hy
    L = math.hypot(dx, dy) or 1.0
    ux, uy = dx / L, dy / L
    side = (-uy, ux)
    # ключ под ~45° сбоку и выше: светотень лепит лицо (фронтальный свет делает его плоским, «пластиковым»)
    key = S.area('HostKey', (hx + ux * 1.0 + side[0] * 1.0, hy + uy * 1.0 + side[1] * 1.0, hz + 0.6), head, 80, 0.9, col='#FFE4C8')
    fill = S.area('HostFill', (hx + ux * 1.4 - side[0] * 0.9, hy + uy * 1.4 - side[1] * 0.9, hz + 0.1), head, 14, 1.5, col='#FFF4EA', shadow=False)
    rim = S.area('HostRim', (hx - ux * 1.0 - side[0] * 0.5, hy - uy * 1.0 - side[1] * 0.5, hz + 0.6), head, 55, 0.8, col='#DCE8FF', shadow=False)
    for o in (key, fill, rim):
        o.data.use_shadow = o is key
        if parent is not None:
            mw = o.matrix_world.copy(); o.parent = parent; o.matrix_world = mw
    return key, rim
