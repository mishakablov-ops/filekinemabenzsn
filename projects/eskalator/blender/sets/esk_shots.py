"""Shot recipes for «Эскалатор». Each function builds the scene for one shot and animates the camera.
Signature: fn(scene, dur_s, fps, shot_info) -> dict
Ведущий и толпа берутся из D:\\aipollon\\eskalator\\assets (hero.blend, crowd.blend; см. esk_hero.py),
путь можно переопределить переменной окружения ESK_ASSETS. Без этих файлов сцены строятся без людей."""
import bpy, math, os, random
from mathutils import Vector
import esk_mech as E, esk_studio as S, esk_metro as MT, esk_hero as H, esk_places as PL

ASSETS = os.environ.get('ESK_ASSETS', r'D:\aipollon\eskalator\assets')


def ease(u, p=1.8):
    u = max(0.0, min(1.0, u))
    return u ** p / (u ** p + (1 - u) ** p) if 0 < u < 1 else u


def cam_move(sc, dur, fps, a, b, ta, tb, lens=(35, 35), name='Cam', step=1, dof=None, parent=None, p=1.8):
    """camera from a->b looking from ta->tb, smooth ease, baked keys (linear between bakes).
    parent: object to ride on (keys are then in its local space)"""
    cam = S.camera(a, ta, lens=lens[0], name=name)
    tgt = bpy.data.objects.new(name + 'Tgt', None); sc.collection.objects.link(tgt)
    con = cam.constraints.new('TRACK_TO'); con.target = tgt; con.track_axis = 'TRACK_NEGATIVE_Z'; con.up_axis = 'UP_Y'
    if dof:
        cam.data.dof.use_dof = True; cam.data.dof.focus_object = tgt; cam.data.dof.aperture_fstop = dof
    if parent is not None:
        cam.parent = parent; tgt.parent = parent
    n = sc.frame_end
    for f in range(1, n + 1, step):
        u = ease((f - 1) / max(1, n - 1), p)
        cam.location = Vector(a).lerp(Vector(b), u); cam.keyframe_insert('location', frame=f)
        tgt.location = Vector(ta).lerp(Vector(tb), u); tgt.keyframe_insert('location', frame=f)
        cam.data.lens = lens[0] + (lens[1] - lens[0]) * u; cam.data.keyframe_insert('lens', frame=f)
    for ob in (cam, tgt, cam.data):
        ad = ob.animation_data
        if ad and ad.action:
            for fc in E.iter_fcurves(ad.action):
                for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'
    return cam


# ----------------------------------------------------------------------------- люди
_CROWD = {}


def crowd():
    p = os.path.join(ASSETS, 'crowd.blend')
    if not _CROWD and os.path.exists(p):
        _CROWD.update(H.load_crowd(p))
    return list(_CROWD.values())


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


def fill_steps(sc, m, dur, rng, density=0.5, skip=(), margin=1.1):
    """passengers on the moving steps: stand on the right, a few on the left; never ride into a comb"""
    ppl = crowd()
    if not ppl:
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
            ob = H.place_person(sc, rng.choice(ppl), (0, 0, 0), 0)
            ob.parent = st
            right = -0.22 if v > 0 else 0.22
            if rng.random() < 0.2:
                right = -right
            ob.location = tread(rng.uniform(-0.02, 0.02), right + rng.uniform(-0.05, 0.05))
            ob.rotation_euler = (0, 0, (math.pi / 2 if v > 0 else -math.pi / 2) + rng.uniform(-0.3, 0.3))
            k_n += 1
    return k_n


def fill_hall(sc, m, rng, n=30, top=True, depth=11.0):
    ppl = crowd()
    if not ppl:
        return 0
    P = m['path']
    W = m['width'] + 6
    lanes = [e.origin.y for e in m['escs']]
    c = 0
    tries = 0
    while c < n and tries < n * 20:
        tries += 1
        if top:
            x = rng.uniform(P.x1 + 0.8, P.x1 + depth); z = P.rise + E.TREAD_Z
            near = x < P.x1 + 2.6
        else:
            x = rng.uniform(P.x0 - depth, P.x0 - 0.8); z = E.TREAD_Z
            near = x > P.x0 - 2.6
        y = rng.uniform(-W / 2 + 0.7, W / 2 - 0.7)
        if near and min(abs(y - ly) for ly in lanes) < 0.85:
            continue
        H.place_person(sc, rng.choice(ppl), (x, y, z), rng.uniform(0, 2 * math.pi))
        c += 1
    return c


def metro_light(strength=0.25):
    S.world('#FFE8C8', strength)


def metro(sc, fps, rise=6.0, lanes=3, every=1, seed=1, density=0.55, hall_n=30, skip=(), lamp_every=3.2, speeds=None):
    n = sc.frame_end
    m = MT.build(rise=rise, lanes=lanes, animate=(1, n, fps), every=every, lamp_every=lamp_every, speeds=speeds)
    rng = random.Random(seed)
    dur = n / fps
    fill_steps(sc, m, dur, rng, density=density, skip=skip)
    if hall_n:
        fill_hall(sc, m, rng, n=hall_n, top=True)
        fill_hall(sc, m, rng, n=hall_n // 2, top=False)
    metro_light()
    return m


def studio_esk(sc, dur, fps, near_truss=True, s0=0.0, speed=0.75, rise=3.0):
    esk = E.Escalator(rise=rise)
    if not near_truss:
        bpy.data.objects.remove(esk.truss[-1])
    esk.animate(1, sc.frame_end, fps, speed=speed, s0=s0)
    S.world('#F3F1EE', 0.8); S.backdrop(center=(4, 0, 0)); S.lights(center=(4, 0, 1.5))
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
    cam_move(sc, dur, fps, (-3.6, -3.4, -0.9), (-2.6, -3.9, -0.4), (4.2, 0, 1.4), (4.6, 0, 1.6), lens=(22, 22))
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
        st.rotation_euler = (0, 0, math.radians(-35 + 70 * u)); st.keyframe_insert('rotation_euler', frame=f)
    S.world('#F3F1EE', 0.9); S.backdrop(center=(0, 0, 0), wall_y=2.0); S.lights(center=(0, 0, 0.8))
    cam_move(sc, dur, fps, (-1.05, -1.25, 1.55), (-0.95, -1.05, 1.40), (-0.17, 0, 0.72), (-0.17, 0, 0.74), lens=(45, 50), dof=4.0)
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
             (xc - 0.45, y + 0.04, z + 0.02), (xc - 0.25, y + 0.05, z + 0.01), lens=(28, 32), dof=4.0)
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
    cam_move(sc, dur, fps, (0.62, 0.20, 1.42), (0.52, 0.26, 1.34), (-0.05, 0.50, 1.15), (-0.08, 0.52, 1.12),
             lens=(32, 35), dof=2.4, parent=st, name='CamS14')
    return {}


# ============================================================================= 7. Москва
def S15(sc, dur, fps, info):      # «В московском метро таких машин 1133» - зал наверху, вниз уходят 3 ленты
    m = metro(sc, fps, rise=6.0, seed=15, density=0.7, hall_n=45)
    P = m['path']
    zt = P.rise + E.TREAD_Z
    cam_move(sc, dur, fps, (P.x1 + 6.5, 1.6, zt + 3.4), (P.x1 + 4.6, 0.8, zt + 2.9), (P.x0 + 2, 0, 1.0), (P.x0 + 1, 0, 0.6), lens=(22, 24))
    return {}


def long_tunnel(sc, fps, seed=16, density=0.28, hall_n=20):
    # «Парк Победы»: подъём ~63 м, лента ~126 м; ключи раз в 10 кадров (на прямом подъёме это точно)
    return metro(sc, fps, rise=63.0, lanes=3, every=10, seed=seed, density=density, hall_n=hall_n, lamp_every=4.0)


def S16(sc, dur, fps, info):      # «Самая длинная на Парке Победы: 126 метров» - туннель сверху вниз
    m = long_tunnel(sc, fps)
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
    cam_move(sc, dur, fps, (70, -30, -40), (-43, -39, 5), (100, 2, -58), (22, 0, -4), lens=(28, 30), p=1.6)
    return {}


def S18(sc, dur, fps, info):      # «Едешь почти три минуты» - ведущий на бесконечном эскалаторе
    m = long_tunnel(sc, fps, seed=18, density=0.3)
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
    # камера на ступенях выше и смотрит вниз на лицо, за спиной туннель уходит вниз
    cam_move(sc, dur, fps, (1.55, -0.30, 2.25), (1.35, -0.22, 2.15), (-0.15, 0.05, 1.80), (-0.15, 0.05, 1.78),
             lens=(40, 44), dof=2.8, parent=st, name='CamS18')
    return {}


# ============================================================================= 8. Слово
def S19(sc, dur, fps, info):      # «А «эскалатор» когда-то был названием бренда» - универмаг 1900-х
    d = PL.old_store(rise=4.0)
    d['esk'].animate(1, sc.frame_end, fps, speed=0.5)
    P = d['path']
    rng = random.Random(19)
    ppl = crowd()
    if ppl:
        for k in range(10):
            x = rng.uniform(-10, -2.5) if k % 2 else rng.uniform(P.x1 + 1, P.x1 + 8)
            z = E.TREAD_Z if x < 0 else P.rise + E.TREAD_Z
            H.place_person(sc, rng.choice(ppl), (x, rng.choice([-1, 1]) * rng.uniform(2.0, 5.5), z), rng.uniform(0, 6.28))
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
    ppl = crowd()
    if ppl:
        for k, e in enumerate(d['escs']):
            for i, st in enumerate(e.steps):
                p, th = e.path.at(k * 0.1 + i * e.path.pitch)
                if th == 0 and P.x0 + 1 < p.x < P.x1 - 1.6 and rng.random() < 0.3:
                    ob = H.place_person(sc, rng.choice(ppl), (0, 0, 0), 0)
                    ob.parent = st
                    ob.location = tread(0, -0.2)
                    ob.rotation_euler = (0, 0, math.pi / 2)
        for lvl in range(3):
            for k in range(14):
                x = rng.uniform(P.x0 - 7, P.x1 + 7); y = rng.choice([-1, 1]) * rng.uniform(7.5, 11.5)
                H.place_person(sc, rng.choice(ppl), (x, y, lvl * d['lvl'] + E.TREAD_Z), rng.uniform(0, 6.28))
    S.world('#F4F2EE', 0.25)
    S.area('Sky', ((P.x0 + P.x1) / 2, 0, 18), ((P.x0 + P.x1) / 2, 0, 0), 9000, 14, col='#FFFFFF')
    cx = (P.x0 + P.x1) / 2
    cam_move(sc, dur, fps, (cx - 1, -10.5, 1.8), (cx + 0.5, -10.0, 8.5), (cx, 0, 4.0), (cx, 0, 8.0), lens=(22, 22))
    return {}


# ============================================================================= 9. Концовка
def S21(sc, dur, fps, info):      # «Оставь лайк, если узнал что-то новое» - ведущий поворачивается к камере
    m = metro(sc, fps, rise=6.0, seed=21, density=0.6, hall_n=40)
    P = m['path']
    zt = P.rise + E.TREAD_Z
    hx, hy = P.x1 + 3.2, -3.9
    rig = hero(sc, loc=(hx, hy, zt), rot_z=0.0, pose='stand')
    n = sc.frame_end
    if rig:
        # поворот к камере за первые ~0.6 с + улыбка
        a0, a1 = math.radians(-30), math.radians(40)
        t_turn = int(0.65 * fps)
        for f in range(1, n + 1):
            u = ease(min(1.0, (f - 1) / t_turn))
            rig.rotation_euler = (0, 0, a0 + (a1 - a0) * u)
            rig.keyframe_insert('rotation_euler', frame=f)
            for side, sx in (('L', 1), ('R', -1)):
                k = ease(min(1.0, max(0.0, (f - t_turn * 0.6) / (0.5 * fps))))
                for bn, dw in (('risorius03.', (sx * 0.003, 0.002, 0.0035)), ('levator05.', (0, 0, 0.0015))):
                    pb = rig.pose.bones.get(bn + side)
                    if pb:
                        H.nudge(rig, bn + side, dw, k)
                        pb.keyframe_insert('location', frame=f)
    # камера: средний план на уровне глаз, ведущий слева, за ним выходы эскалаторов и люди
    cam_move(sc, dur, fps, (hx + 1.30, hy - 1.55, zt + 1.55), (hx + 1.10, hy - 1.30, zt + 1.55),
             (hx, hy, zt + 1.42), (hx, hy, zt + 1.45), lens=(45, 48), dof=2.0)
    return {}
