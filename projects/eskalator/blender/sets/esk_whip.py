"""Переходы как в образце IMG_1924 (разбор 08.11.2026): не цифровые эффекты, а сама камера.

В конце плана камера срывается в резкий поворот (панорама/наклон) или рывок вперёд, разгоняясь, со смазом движения;
следующий план начинается с того же рывка в ту же сторону и мягко тормозит. Склейка встык в момент самого сильного
смаза, поэтому стык не виден, как в монтаже «на свиш-панораме». Изредка простая склейка.

apply(sc, shot, shots, fps) зовёт build_shot.py после сборки плана: запекает мировую матрицу камеры по кадрам
(снимает Track To и родителя) и добавляет поверх рывки. Номера кадров стыка считает cut_frames() — ими же режет
assemble.py, поэтому смаз приходится ровно на склейку.
"""
import math
import bpy
from mathutils import Quaternion, Vector

# стык «предыдущий план -> этот план»: в какую сторону рвётся камера
# R/L - панорама вправо/влево, U/D - наклон вверх/вниз, F - рывок-наезд вперёд, CUT - простая склейка
TRANS = {
    'S02': 'D', 'S03': 'R', 'S04': 'F', 'S05': 'U', 'S06': 'R', 'S07': 'F', 'S08': 'D', 'S09': 'R',
    'S10': 'U', 'S11': 'F', 'S12': 'L', 'S13': 'D', 'S14': 'U', 'S15': 'R', 'S16': 'D', 'S17': 'CUT',
    'S18': 'R', 'S19': 'L', 'S20': 'D', 'S20B': 'U', 'S21': 'F',
}
N_OUT = 6                  # кадров разгона в конце плана
N_IN = 8                   # кадров торможения в начале следующего
ANG = math.radians(42)     # размах поворота за рывок
PUSH = 0.75                # рывок вперёд: доля расстояния до точки взгляда
POW = 2.6                  # крутизна разгона/торможения
BLUR_MAX = 720             # px: потолок длины смаза в Eevee (по умолчанию 32 - рывок выйдет резким)


def cut_frames(shots, fps):
    """id -> число показываемых кадров плана (склейка встык по началу следующего плана)."""
    g = [int(round(s['start'] * fps)) for s in shots]
    out = {}
    for k, s in enumerate(shots):
        if k + 1 < len(shots):
            out[s['id']] = g[k + 1] - g[k]
        else:
            out[s['id']] = int(round(s['dur'] * fps))
    return out


def _amount(f, f_cut, kind_in, kind_out):
    """(рывок на входе, рывок на выходе) в долях 0..>1 для кадра f."""
    a_in = a_out = 0.0
    if kind_in:
        v = (f - 1) / N_IN
        if v < 1.0:
            a_in = (1.0 - v) ** POW          # f=1 -> 1, тормозит к 0; f=0 -> больше 1 (для смаза первого кадра)
    if kind_out:
        u = (f - (f_cut - 1 - N_OUT)) / N_OUT
        if u > 0.0:
            a_out = u ** POW                 # последний показываемый кадр -> 1, дальше разгон продолжается
    return a_in, a_out


def _turn(kind, ang):
    if kind == 'R':
        return Quaternion((0, 1, 0), -ang)
    if kind == 'L':
        return Quaternion((0, 1, 0), ang)
    if kind == 'U':
        return Quaternion((1, 0, 0), ang)
    if kind == 'D':
        return Quaternion((1, 0, 0), -ang)
    return Quaternion()


def apply(sc, shot, shots, fps):
    ids = [s['id'] for s in shots]
    if shot not in ids or sc.camera is None:
        return None
    k = ids.index(shot)
    kind_in = TRANS.get(shot) if k > 0 else None
    kind_out = TRANS.get(ids[k + 1]) if k + 1 < len(ids) else None
    kind_in = None if kind_in == 'CUT' else kind_in
    kind_out = None if kind_out == 'CUT' else kind_out
    if not kind_in and not kind_out:
        return dict(shot=shot, whip=None)
    f_cut = cut_frames(shots, fps)[shot] + 1      # первый кадр, который уже не показывается
    cam = sc.camera
    tgt = None
    for c in cam.constraints:
        if c.type == 'TRACK_TO' and c.target is not None:
            tgt = c.target
    n = sc.frame_end
    frames = list(range(0, n + 2))
    mats, dist = {}, {}
    for f in frames:
        sc.frame_set(f)
        mats[f] = cam.matrix_world.copy()
        dist[f] = (tgt.matrix_world.translation - mats[f].translation).length if tgt else 3.0
    sc.frame_set(1)
    # снять старую анимацию объекта камеры (объектив и фокус остаются на данных камеры)
    cam.constraints.clear()
    cam.parent = None
    if cam.animation_data:
        cam.animation_data.action = None
    cam.rotation_mode = 'QUATERNION'
    for f in frames:
        loc, rot, _ = mats[f].decompose()
        a_in, a_out = _amount(f, f_cut, kind_in, kind_out)
        fwd = rot @ Vector((0, 0, -1))
        if kind_in == 'F':
            loc = loc - fwd * (PUSH * dist[f] * a_in)            # прилетает сзади и тормозит
        elif kind_in:
            rot = rot @ _turn(kind_in, -ANG * a_in)              # стоит развёрнутой «до» и доворачивает на место
        if kind_out == 'F':
            loc = loc + fwd * (PUSH * dist[f] * a_out)           # уносится вперёд
        elif kind_out:
            rot = rot @ _turn(kind_out, ANG * a_out)
        cam.location = loc
        cam.rotation_quaternion = rot
        cam.keyframe_insert('location', frame=f)
        cam.keyframe_insert('rotation_quaternion', frame=f)
    ad = cam.animation_data
    if ad and ad.action:
        try:
            from esk_mech import iter_fcurves
            fcs = iter_fcurves(ad.action)
        except Exception:
            fcs = getattr(ad.action, 'fcurves', [])
        for fc in fcs:
            for kp in fc.keyframe_points:
                kp.interpolation = 'LINEAR'
    sc.render.use_motion_blur = True
    try:
        sc.eevee.motion_blur_max = BLUR_MAX
    except Exception:
        pass
    return dict(shot=shot, whip_in=kind_in, whip_out=kind_out, f_cut=f_cut)
