"""«Канал без лица» (рекламный ролик воронки, 24.11.2026): комната героя, телефон и монитор с экранами-картинками
из tools/ui_textures.py (папка ui/: KANAL_UI, <проект>/ui, project-files). Одна функция на план, время внутри плана —
shot['events'] (после озвучки их проставит build_timeline.py), без них берутся доли длительности.

Планы: feed (POV, лента канала), sofa (герой на кровати с телефоном), notes (POV, уведомления о рекламе), night (ручной
монтаж ночью), build (одна фраза → ролик), styles (меню стилей), calendar (месяц роликов), call (созвон «настроим за
тебя»), comment (POV, поле комментария «канал»).
"""
import math
import os
import random

import bpy
from mathutils import Matrix, Vector

import lib
import pcommon as pc
import prooms as PR
import sila_fx as FX
import sila_hero as H
import sila_sets as SS

F = lib.sec2f
HERE = os.path.dirname(os.path.abspath(__file__))
UI_DIRS = [os.environ.get('KANAL_UI', ''), os.path.join(HERE, '..', 'ui'), os.path.join(HERE, '..', '..', 'ui'),
           '/mnt/project-files/aipollon/kanal-bez-lica/ui']
DESK = Vector((-1.4, 1.05, 0.78))           # верх стола (room() в sila_sets)
CHAIR = Vector((-1.4, 0.32, 0.0))
MON = Vector((-1.4, 1.27, 0.78))            # низ подставки монитора
# v2 (25.11): лицо героя за столом спереди-справа (камера перед линией головы — голова не закрывает экран): старт, конец, цель
# v2: лицо героя спереди-справа, с полутора метров (с 0,85 м голова заполняла кадр); лампа и книги на столе не перед лицом
FACE_R = ((-0.2, 1.2, 1.42), (-0.26, 1.14, 1.4))
FACE_T = (-1.42, 0.45, 1.08)
MON_W, MON_H = 0.64, 0.36
SCR_Z = 0.78 + 0.14 + MON_H / 2             # центр экрана монитора
BED_SEAT = (1.4, -0.42, 0.115)              # на кровати, ноги вдоль неё к -y, спиной к подушкам (замер: попа 0.34 над корнем)
BED_LEGS = dict(thigh=88.0, shin=80.0, lean=-6.0)   # икры на 1–2 см в мягком матрасе, не висят


def ui(name):
    for d in UI_DIRS:
        p = os.path.join(d, name + '.png') if d else ''
        if p and os.path.exists(p):
            return os.path.abspath(p)
    raise SystemExit('UI texture not found: %s (python tools/ui_textures.py <dir>, или KANAL_UI)' % name)


def media(name):
    """Видео для экранов (v2): KANAL_MEDIA, затем папки UI."""
    for d in [os.environ.get('KANAL_MEDIA', '')] + UI_DIRS:
        p = os.path.join(d, name) if d else ''
        if p and os.path.exists(p):
            return os.path.abspath(p)
    raise SystemExit('media not found: %s (KANAL_MEDIA)' % name)


def _ev(shot, k, d):
    return shot.get('events', {}).get(k, d)


# ----------------------------------------------------------------------------- экраны
def screen_mat(name, png, strength=1.3, scroll=None):
    """Светящийся экран: картинка по Generated-координатам плоскости (верх картинки = +Y плоскости), лёгкий блик стекла.
    scroll = [(t, dy)] прокручивает картинку вверх (dy в долях её высоты)."""
    m = bpy.data.materials.new('Scr' + name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    tc = nt.nodes.new('ShaderNodeTexCoord')
    mp = nt.nodes.new('ShaderNodeMapping')
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(png, check_existing=True)
    tex.extension = 'EXTEND'
    tex.interpolation = 'Cubic'
    em = nt.nodes.new('ShaderNodeEmission')
    em.inputs['Strength'].default_value = strength
    gl = nt.nodes.new('ShaderNodeBsdfGlossy')
    gl.inputs['Roughness'].default_value = 0.08
    gl.inputs['Color'].default_value = (1, 1, 1, 1)
    mix = nt.nodes.new('ShaderNodeMixShader')
    mix.inputs['Fac'].default_value = 0.06
    L = nt.links
    L.new(tc.outputs['Generated'], mp.inputs['Vector'])
    L.new(mp.outputs['Vector'], tex.inputs['Vector'])
    L.new(tex.outputs['Color'], em.inputs['Color'])
    L.new(em.outputs[0], mix.inputs[1])
    L.new(gl.outputs[0], mix.inputs[2])
    L.new(mix.outputs[0], out.inputs['Surface'])
    if scroll:
        sk = mp.inputs['Scale']
        if scroll[0][0] is not None:
            sk.default_value = (1.0, 0.5, 1.0)              # видна половина высоты картинки
        loc = mp.inputs['Location']
        for t, dy in scroll:
            loc.default_value = (0.0, 0.5 - dy, 0.0)
            loc.keyframe_insert('default_value', frame=F(t))
    return m


def screen(coll, name, png, w, h, loc, rot, strength=1.3, scroll=None):
    ob = lib.plane((w, h), loc, screen_mat(name, png, strength, scroll), rot=rot, name='Scr' + name, coll=coll)
    ob.visible_shadow = False
    return ob


def video_mat(name, movie, overlay, frames, strength=1.3, aspect=(720 / 1560) / (1080 / 1920)):
    """Экран-видео (v2): наш ролик (MOVIE, кадр сцены = кадр видео) под прозрачным слоем интерфейса overlay (PNG RGBA).
    Видео 9:16 обрезается по ширине под экран телефона (aspect)."""
    m = screen_mat(name, overlay, strength)
    nt = m.node_tree
    ov = next(n for n in nt.nodes if n.type == 'TEX_IMAGE')
    em = next(n for n in nt.nodes if n.type == 'EMISSION')
    tc = next(n for n in nt.nodes if n.type == 'TEX_COORD')
    img = bpy.data.images.load(movie, check_existing=True)
    img.source = 'MOVIE'
    mv = nt.nodes.new('ShaderNodeTexImage')
    mv.image = img
    mv.extension = 'EXTEND'
    iu = mv.image_user
    iu.frame_duration = frames
    iu.frame_start = 1
    iu.frame_offset = 0
    iu.use_auto_refresh = True
    mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (aspect, 1.0, 1.0)
    mp.inputs['Location'].default_value = ((1 - aspect) / 2, 0.0, 0.0)
    mix = nt.nodes.new('ShaderNodeMix')
    mix.data_type = 'RGBA'
    pin = {i.identifier: i for i in mix.inputs}
    pout = {o.identifier: o for o in mix.outputs}
    L = nt.links
    L.new(tc.outputs['Generated'], mp.inputs['Vector'])
    L.new(mp.outputs['Vector'], mv.inputs['Vector'])
    L.new(ov.outputs['Alpha'], pin['Factor_Float'])
    L.new(mv.outputs['Color'], pin['A_Color'])
    L.new(ov.outputs['Color'], pin['B_Color'])
    L.new(pout['Result_Color'], em.inputs['Color'])
    return m


def video_stack(coll, name, movie, frames, items, w, h, loc, rot, strength=1.3):
    """Как stack(), но под каждым слоем интерфейса играет одно и то же видео."""
    obs = []
    for i, (nm, t0) in enumerate(items):
        ob = lib.plane((w, h), loc, video_mat('%s%02d' % (name, i), movie, ui(nm), frames, strength), rot=rot,
                       name='Scr%s%02d' % (name, i), coll=coll)
        ob.visible_shadow = False
        t1 = items[i + 1][1] if i + 1 < len(items) else None
        keys = [(0, t0 <= 0)]
        if t0 > 0:
            keys.append((t0, True))
        if t1 is not None:
            keys.append((t1, False))
        FX.key_hide(ob, keys)
        obs.append(ob)
    return obs


def stack(coll, name, items, w, h, loc, rot, strength=1.3):
    """Экраны по очереди: items = [(png_name, t_on)], каждый виден до включения следующего."""
    obs = []
    for i, (nm, t0) in enumerate(items):
        ob = screen(coll, '%s%02d' % (name, i), ui(nm), w, h, loc, rot, strength)
        t1 = items[i + 1][1] if i + 1 < len(items) else None
        keys = [(0, t0 <= 0)]
        if t0 > 0:
            keys.append((t0, True))
        if t1 is not None:
            keys.append((t1, False))
        FX.key_hide(ob, keys)
        obs.append(ob)
    return obs


# ----------------------------------------------------------------------------- предметы
def monitor(coll):
    dark = lib.mat('MonBody', '#1C1D21', rough=0.35, spec=0.6)
    metal = lib.mat('MonStand', '#8D9096', rough=0.3, metal=1.0)
    lib.box((0.24, 0.18, 0.012), (MON.x, MON.y + 0.02, 0.78), metal, bevel=0.004, name='MonFoot', coll=coll, origin='bottom')
    lib.box((0.05, 0.03, 0.2), (MON.x, MON.y + 0.06, 0.79), metal, bevel=0.006, name='MonNeck', coll=coll, origin='bottom')
    lib.box((MON_W + 0.024, 0.028, MON_H + 0.024), (MON.x, MON.y + 0.01, SCR_Z), dark, bevel=0.006, name='MonBezel', coll=coll)
    return (MON.x, MON.y - 0.0045, SCR_Z), (math.pi / 2, 0, 0)


def desk_stuff(coll, rng, night=False, mugs=1):
    """Клавиатура, мышь, кружки, наушники, книги, стикеры, лампа: задний план не пустой."""
    kb = lib.mat('Keyb', '#2A2C31', rough=0.5)
    lib.box((0.42, 0.14, 0.02), (DESK.x, DESK.y - 0.22, 0.78), kb, bevel=0.004, name='Keyboard', coll=coll, origin='bottom')
    keys = lib.mat('Keys', '#3A3D44', rough=0.45)
    for r in range(4):
        lib.box((0.38, 0.022, 0.006), (DESK.x, DESK.y - 0.27 + r * 0.032, 0.80), keys, bevel=0.002, name='KeyRow', coll=coll,
                origin='bottom')
    lib.box((0.24, 0.2, 0.003), (DESK.x + 0.38, DESK.y - 0.2, 0.78), lib.mat('Pad', '#3B4A5C', rough=0.9), bevel=0.0,
            name='MousePad', coll=coll, origin='bottom')
    mouse = lib.sphere(0.034, (DESK.x + 0.38, DESK.y - 0.2, 0.795), lib.mat('Mouse', '#E8E8EA', rough=0.3), 16, 10,
                       scale=(0.8, 1.25, 0.5), name='Mouse', coll=coll)
    out = [mouse]
    cups = []
    for k in range(4):
        c = PR.cup(DESK.x - 0.52 + k * 0.1, DESK.y - 0.08 - 0.06 * (k % 2), 0.78, coll, steam=False,
                   coffee='#3E2414' if k else '#4A2A16', name='Mug%d' % k)
        cups.append([o for o in bpy.data.objects if o.name.startswith('Mug%d' % k)])
    for k, grp in enumerate(cups):                       # видны только первые `mugs`; остальные включает сцена
        if k >= mugs:
            for o in grp:
                o.hide_render = o.hide_viewport = True
    book = [('#8C2F2F', 0.04), ('#2F5E8C', 0.035), ('#D6A93A', 0.03), ('#3B7A57', 0.045)]
    x = DESK.x + 0.48
    for col, th in book:
        lib.box((th, 0.17, 0.24), (x, DESK.y + 0.25, 0.78), lib.mat('Book' + col, col, rough=0.7), bevel=0.003, name='Book', coll=coll,
                origin='bottom')
        x += th + 0.004
    for k, col in enumerate(()):                                     # стикеры убраны: висели у края рамки
        lib.box((0.05, 0.002, 0.05), (MON.x - MON_W / 2 - 0.01 + k * 0.004, MON.y - 0.006, SCR_Z + 0.12 - k * 0.06),
                lib.mat('Sticky' + col, col, rough=0.9), rot=(0, 0, 0), bevel=0.0, name='Sticky', coll=coll)
    hp = lib.mat('Phones', '#26282D', rough=0.4)
    lib.curve_poly('Headphones', [[(DESK.x - 0.62 + 0.09 * math.cos(a), DESK.y + 0.2, 0.8 + 0.1 * math.sin(a))
                                   for a in [i * math.pi / 10 for i in range(11)]]], bevel=0.012, mat_=hp, coll=coll)
    for sx in (-1, 1):
        lib.cyl(0.04, 0.03, (DESK.x - 0.62 + sx * 0.09, DESK.y + 0.2, 0.8), hp, rot=(0, math.pi / 2, 0), verts=20, name='Cup',
                coll=coll)
    # лампа на кронштейне
    lm = lib.mat('Lamp', '#E9E4D8', rough=0.4)
    lib.cyl(0.07, 0.02, (DESK.x + 0.6, DESK.y + 0.2, 0.78), lm, verts=24, name='LampFoot', coll=coll, origin='bottom')
    lib.curve_poly('LampArm', [[(DESK.x + 0.6, DESK.y + 0.2, 0.8), (DESK.x + 0.55, DESK.y + 0.12, 1.15),
                                (DESK.x + 0.4, DESK.y + 0.02, 1.2)]], bevel=0.008, mat_=lm, coll=coll)
    lib.cyl(0.06, 0.09, (DESK.x + 0.4, DESK.y + 0.02, 1.12), lm, verts=24, r2=0.03, name='LampHead', coll=coll, origin='bottom')
    if night:
        lib.light('POINT', (DESK.x + 0.4, DESK.y + 0.0, 1.08), energy=22, color='#FFC98A', size=0.05, name='DeskLamp', coll=coll)
    return out, cups


def wall_clock(coll, loc=(2.18, 0.75, 2.2), turns=(0.0, 0.0), dur=1.0):
    """Часы на правой стене (смотрят в -x); стрелки делают `turns` оборотов за план."""
    lib.cyl(0.17, 0.03, loc, lib.mat('ClockFace', '#F7F5EE', rough=0.5), rot=(0, math.pi / 2, 0), verts=40, name='Clock', coll=coll)
    lib.cyl(0.185, 0.025, (loc[0] + 0.006, loc[1], loc[2]), lib.mat('ClockRim', '#2B2D30', rough=0.4), rot=(0, math.pi / 2, 0),
            verts=40, name='ClockRim', coll=coll)
    dark = lib.mat('ClockHand', '#1B1C1E', rough=0.4)
    for k in range(12):
        a = k * math.pi / 6
        lib.box((0.01, 0.01, 0.03), (loc[0] - 0.018, loc[1] + 0.14 * math.sin(a), loc[2] + 0.14 * math.cos(a)), dark, rot=(-a, 0, 0),
                bevel=0, name='Tick', coll=coll)
    for nm, Ln, w, tr in (('Min', 0.13, 0.01, turns[0]), ('Hour', 0.085, 0.016, turns[1])):
        piv = lib.empty('Clock' + nm, (loc[0] - 0.022, loc[1], loc[2]), coll=coll)
        hb = lib.box((0.006, w, Ln), (0, 0, Ln / 2 - 0.012), dark, bevel=0, name='Hand' + nm, coll=coll)
        hb.parent = piv
        piv.rotation_euler.x = -0.7 if nm == 'Min' else -2.1
        piv.keyframe_insert('rotation_euler', index=0, frame=F(0))
        piv.rotation_euler.x += -2 * math.pi * tr
        piv.keyframe_insert('rotation_euler', index=0, frame=F(dur))
        lib._set_interp(piv, 'LINEAR')


def calendar(coll, rng, loc=(2.19, 0.75, 1.45), fill=None):
    """Календарь на правой стене: 5 недель × 7 дней; fill=(t0, t1) — клетки заполняются превью роликов по очереди."""
    paper = lib.mat('CalPaper', '#FAF8F2', rough=0.8)
    lib.box((0.012, 0.62, 0.62), loc, paper, bevel=0.003, name='Calendar', coll=coll)
    lib.box((0.014, 0.62, 0.1), (loc[0] - 0.001, loc[1], loc[2] + 0.26), lib.mat('CalHead', '#C8402F', rough=0.6), bevel=0.0,
            name='CalHead', coll=coll)
    lib.text_obj('ДЕКАБРЬ', 0.05, (loc[0] - 0.009, loc[1], loc[2] + 0.26), (math.pi / 2, 0, -math.pi / 2),
                 lib.mat('CalTitle', '#FFFFFF', rough=0.6), name='CalTitle', coll=coll)
    grid = lib.mat('CalGrid', '#D8D4CA', rough=0.8)
    cells = []
    tints = ['#FFA860', '#78B0FF', '#C48CFF', '#FF788C', '#6EDCC8', '#FFD25C']
    for r in range(5):
        for c in range(7):
            y = loc[1] - 0.27 + c * 0.09
            z = loc[2] + 0.15 - r * 0.085
            lib.box((0.003, 0.082, 0.077), (loc[0] - 0.007, y, z), grid, bevel=0.0, name='CalCell', coll=coll)
            th = lib.box((0.003, 0.07, 0.066), (loc[0] - 0.01, y, z), lib.mat('Th' + tints[(r * 7 + c) % 6], tints[(r * 7 + c) % 6],
                                                                              rough=0.6, emit=tints[(r * 7 + c) % 6], emit_strength=0.25),
                         bevel=0.0, name='CalThumb', coll=coll)
            cells.append(th)
    if fill:
        t0, t1 = fill
        for i, th in enumerate(cells):
            ti = t0 + (t1 - t0) * i / len(cells)
            FX.key_hide(th, [(0, False), (ti, True)])
    return cells


def room_detail(coll, rng):
    """Шкаф с полками, гитара, плакат, коврик, гирлянда: комната живая (правило 05.11 про насыщенный задний план)."""
    wood = lib.mat('ShelfWood', '#8A6748', rough=0.55, var=0.2, var_scale=8)
    for z in (0.0, 0.45, 0.9, 1.35, 1.8):
        lib.box((0.32, 0.9, 0.025), (-2.05, -1.0, z + 0.02), wood, bevel=0.004, name='Shelf', coll=coll, origin='bottom')
    for sy in (-1.44, -0.56):
        lib.box((0.32, 0.025, 1.83), (-2.05, sy, 0.0), wood, bevel=0.004, name='ShelfSide', coll=coll, origin='bottom')
    cols = ['#8C2F2F', '#2F5E8C', '#D6A93A', '#3B7A57', '#6B4E8C', '#C46A3A', '#E3DCCB']
    for z in (0.045, 0.495, 0.945, 1.395):
        y = -1.4
        while y < -0.62:
            th = rng.uniform(0.025, 0.05)
            hgt = rng.uniform(0.2, 0.32)
            if rng.random() < 0.12:
                lib.sphere(0.06, (-2.05, y + 0.06, z + 0.06), lib.mat('Ball', rng.choice(cols), rough=0.5), 12, 8, name='Toy', coll=coll)
                y += 0.14
                continue
            lib.box((0.2, th, hgt), (-2.05, y + th / 2, z), lib.mat('Bk' + rng.choice(cols), rng.choice(cols), rough=0.7), bevel=0.003,
                    name='ShelfBook', coll=coll, origin='bottom')
            y += th + 0.003
    pot = lib.cyl(0.1, 0.22, (-1.95, -1.9, 0.0), lib.mat('BigPot', '#D9D2C3', rough=0.6), verts=20, r2=0.08, name='BigPot', coll=coll,
                  origin='bottom')
    for k in range(9):
        a = k * 2.4
        lib.sphere(0.12, (-1.95 + 0.12 * math.cos(a), -1.9 + 0.12 * math.sin(a), 0.4 + k * 0.07),
                   lib.mat('BigLeaf', '#4E7A3A', rough=0.8, var=0.3, var_scale=10), 10, 8, scale=(1.3, 0.6, 0.35),
                   name='BigLeaf', coll=coll).rotation_euler = (0.3, 0.2, a)
    lib.box((1.6, 1.1, 0.012), (0.4, -0.7, 0.0), lib.mat('Rug', '#B8A68C', rough=0.95, var=0.15, var_scale=30), bevel=0.0, name='Rug',
            coll=coll, origin='bottom')
    lib.box((0.6, 0.02, 0.85), (2.19, -1.6, 1.2), lib.mat('Poster2', '#E0B45A', rough=0.7), rot=(0, 0, math.pi / 2), bevel=0.0,
            name='Poster2', coll=coll, origin='bottom')
    bulbs = lib.mat('Bulb', '#FFE3A8', emit='#FFD58A', emit_strength=3.0)
    for k in range(18):
        x = -2.0 + k * 0.24
        lib.sphere(0.018, (x, 1.62, 2.42 - 0.05 * math.sin(k / 17 * math.pi)), bulbs, 8, 6, name='Garland', coll=coll)
    return pot


def base(night=False, rng=None):
    rng = rng or random.Random(24)
    coll = lib.collection('Room')
    out, sun = SS.room(coll, rng, morning=True)
    for nm in ('Laptop', 'Screen'):
        for o in [o for o in bpy.data.objects if o.name.startswith(nm)]:
            bpy.data.objects.remove(o, do_unlink=True)
    scr = monitor(coll)
    PR.chair(CHAIR.x, CHAIR.y, math.pi, coll, wood='#2E3036')
    room_detail(coll, rng)
    soft = lib.mat('Pillow', '#EDE7DC', rough=0.95, var=0.05, var_scale=20)
    for px in (1.05, 1.75):
        lib.box((0.6, 0.22, 0.38), (px, -0.12, 0.45), soft, rot=(0.35, 0, 0), bevel=0.08, name='Pillow', coll=coll, origin='bottom')
    lib.box((1.5, 1.1, 0.04), (1.4, -1.35, 0.45), lib.mat('Plaid', '#C9785A', rough=0.95, var=0.1, var_scale=25), bevel=0.02,
            name='Plaid', coll=coll, origin='bottom')
    if night:
        sun.data.energy = 0.0                       # небо и огни города — пресет 'night' «Метрополиса» (city_view)
        wf = bpy.data.objects.get('WinFill')
        if wf:
            wf.data.energy = 25
            wf.data.color = (0.45, 0.55, 0.9)
        lib.light('AREA', (0.0, -0.6, 2.55), (0, 0, 0), energy=4, color='#AFC3FF', size=3.0, name='NightFill', coll=coll)
    return coll, out, scr


def seated(coll, typing=False):
    h = H.load(coll, (CHAIR.x, CHAIR.y, 0.075), math.pi)
    return h


def type_pose(**kw):
    p = H.pose('sit', arm=(14, 52), fore=(10, 95), head=(0, 4, 0), lean=8.0)
    p.update(kw)
    return p


def typing(h, t0, t1, base=None, rate=6.0):
    """Руки над клавиатурой чуть ходят: ключ каждые 1/rate с."""
    base = base or type_pose()
    n = max(2, int((t1 - t0) * rate))
    for i in range(n + 1):
        t = t0 + (t1 - t0) * i / n
        a = 3.0 * (1 if i % 2 else -1)
        H.key_pose(h, t, dict(base, fore=((10, 95 + a), (10, 95 - a))))


# ----------------------------------------------------------------------------- телефон в руке
PH_W, PH_D, PH_H = 0.11, 0.012, 0.23       # под чиби-кисти (кулак ~8 см): обычные 7,6 × 15,8 см тонули в кулаках
SCR_W, SCR_H = 0.102, 0.22                  # экран 720×1560 (0.4636)


def phone(coll, name='Phone'):
    """Телефон: корпус + экран, экран смотрит в -Y корня (верх = +Z корня)."""
    root = lib.empty(name, (0, 0, 0), coll=coll)
    body = lib.box((PH_W, PH_D, PH_H), (0, 0, 0), lib.mat('PhoneBody', '#E2614E', rough=0.35, spec=0.6), bevel=0.006,
                   name=name + 'Body', coll=coll)
    body.parent = root
    return root


HOLD = dict(arm=(4, 52), fore=(-30, 112))          # ладони перед грудью, 16 см друг от друга (под ширину телефона)


def hold_phone(h, ph, t=0.0, side='Right', tilt=55.0, out=(0.0, -0.035, 0.0), lift=0.06):
    """Посадить телефон в кисть (родитель — кость кисти), экран к лицу. Вызывать после ключа позы на t."""
    sc = bpy.context.scene
    sc.frame_set(F(t))
    bpy.context.view_layer.update()
    rig = h['rig']
    pb = rig.pose.bones[side + 'Hand']
    tips = [rig.matrix_world @ rig.pose.bones[s + 'Hand'].matrix @ Vector((0, pb.length * 0.6, 0)) for s in ('Left', 'Right')]
    tip = (tips[0] + tips[1]) / 2 + Vector((0, 0, 0.03))           # между ладонями: держит двумя руками
    # out: телефон на 4,5 см ближе к лицу, чем центры кулаков, — кулаки за корпусом, видны по бокам, экран не закрывают
    head = rig.matrix_world @ rig.pose.bones['Head'].matrix @ Vector((0, 0.25, 0))
    d = (head - tip).normalized()                       # от телефона к лицу
    q = d.to_track_quat('-Y', 'Z')                      # -Y корня (экран) смотрит на лицо
    M = Matrix.Translation(tip + q @ Vector(out)) @ q.to_matrix().to_4x4()
    M = M @ Matrix.Rotation(math.radians(tilt - 55.0), 4, 'X')       # +Z корня = верх экрана: вперёд-вверх, как герой видит
    M = M @ Matrix.Translation((0, 0, lift))            # кулаки держат низ, верх экрана свободен
    ph.parent = rig
    ph.parent_type = 'BONE'
    ph.parent_bone = side + 'Hand'
    bone_tail = rig.matrix_world @ pb.matrix @ Matrix.Translation((0, pb.length, 0))
    ph.matrix_parent_inverse = bone_tail.inverted()
    ph.matrix_basis = M
    return ph


EYE_REST = Vector((0.0, -0.17, 1.14))       # между глаз, внутри головы (модель: лицо у y = -0.32, глаза z = 1.14)


def eye_point(h, t=0.0):
    sc = bpy.context.scene
    sc.frame_set(F(t))
    bpy.context.view_layer.update()
    rig = h['rig']
    pb = rig.pose.bones['Head']
    return rig.matrix_world @ pb.matrix @ pb.bone.matrix_local.inverted() @ EYE_REST


def pov_mats(h):
    """Взгляд из глаз героя: камера стоит внутри головы, изнанка его модели для камеры прозрачна (видны руки и телефон)."""
    for m in h['body'].data.materials:
        nt = m.node_tree
        out = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL' and n.is_active_output)
        src = out.inputs['Surface'].links[0].from_socket
        geo = nt.nodes.new('ShaderNodeNewGeometry')
        lp = nt.nodes.new('ShaderNodeLightPath')
        mul = nt.nodes.new('ShaderNodeMath')
        mul.operation = 'MULTIPLY'
        tr = nt.nodes.new('ShaderNodeBsdfTransparent')
        mix = nt.nodes.new('ShaderNodeMixShader')
        nt.links.new(geo.outputs['Backfacing'], mul.inputs[0])
        nt.links.new(lp.outputs['Is Camera Ray'], mul.inputs[1])
        nt.links.new(mul.outputs[0], mix.inputs['Fac'])
        nt.links.new(src, mix.inputs[1])
        nt.links.new(tr.outputs[0], mix.inputs[2])
        nt.links.new(mix.outputs[0], out.inputs['Surface'])


def hide_head_for_camera(h, group='Head'):
    """25.11 (EEVEE на ПК): голова героя между камерой и телефоном прозрачна только для лучей камеры — по весу её группы
    вершин, а не отсечением clip_start. Отсечение резало и предплечья с кулаками (они в 1–7 см перед экраном, голова
    подходит к тому же расстоянию), и кулаки превращались в белые «крылья». Тень от головы остаётся."""
    for m in h['body'].data.materials:
        nt = m.node_tree
        out = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL' and n.is_active_output)
        src = out.inputs['Surface'].links[0].from_socket
        at = nt.nodes.new('ShaderNodeAttribute')
        at.attribute_type = 'GEOMETRY'
        at.attribute_name = group
        gt = nt.nodes.new('ShaderNodeMath')
        gt.operation = 'GREATER_THAN'
        gt.inputs[1].default_value = 0.5
        lp = nt.nodes.new('ShaderNodeLightPath')
        mul = nt.nodes.new('ShaderNodeMath')
        mul.operation = 'MULTIPLY'
        tr = nt.nodes.new('ShaderNodeBsdfTransparent')
        mix = nt.nodes.new('ShaderNodeMixShader')
        nt.links.new(at.outputs['Fac'], gt.inputs[0])
        nt.links.new(gt.outputs[0], mul.inputs[0])
        nt.links.new(lp.outputs['Is Camera Ray'], mul.inputs[1])
        nt.links.new(mul.outputs[0], mix.inputs['Fac'])
        nt.links.new(src, mix.inputs[1])
        nt.links.new(tr.outputs[0], mix.inputs[2])
        nt.links.new(mix.outputs[0], out.inputs['Surface'])
        try:
            m.surface_render_method = 'DITHERED'          # EEVEE: прозрачность через дизеринг, тени как у непрозрачного
        except Exception:
            pass


def pov_camera(h, ph, dur, lens=30, push=0.0):
    """Камера из глаз героя на телефон; push — на сколько метров подъехать к телефону за план."""
    pov_mats(h)
    e0, e1 = eye_point(h, 0.0), eye_point(h, dur)
    bpy.context.scene.frame_set(1)
    c = ph.matrix_world.translation.copy()
    d0 = (c - e0).normalized()
    cam = lib.camera(tuple(e0), tuple(c), lens)
    lib.animate_camera(cam, [(0, tuple(e0)), (dur, tuple(e1 + d0 * push))], [(0, tuple(c)), (dur, tuple(c))])
    cam.data.clip_start = 0.01
    cam.data.dof.use_dof = True
    cam.data.dof.focus_object = ph
    cam.data.dof.aperture_fstop = 2.2
    return cam


def phone_cam(h, ph, dur, dist=0.39, lens=54, push=0.03, fstop=4.0, up=0.023):
    # 25.11: телефон ~50 % высоты кадра и ниже центра — сверху место для титров (полоса 13–33 %), низ экрана выше 80 %
    """Крупно экран телефона со стороны лица героя: камера на нормали экрана, верх кадра = верх экрана,
    кулаки по краям. Голова героя для камеры прозрачна (hide_head_for_camera), руки и кулаки целиком в кадре."""
    pov_mats(h)
    hide_head_for_camera(h)
    sc = bpy.context.scene
    sc.frame_set(1)
    bpy.context.view_layer.update()
    W = ph.matrix_world
    c = W.translation.copy()
    n = (W.to_3x3() @ Vector((0, -1, 0))).normalized()          # нормаль экрана (к лицу)
    u = (W.to_3x3() @ Vector((0, 0, 1))).normalized()           # верх картинки
    tgt = c + u * up
    cd = bpy.data.cameras.new('Cam')
    cd.lens = lens
    cd.sensor_fit = 'HORIZONTAL'
    cd.sensor_width = 36.0
    cd.clip_end = 200
    cd.dof.use_dof = True
    cd.dof.focus_object = ph
    cd.dof.aperture_fstop = fstop
    cam = bpy.data.objects.new('Cam', cd)
    lib._link(cam)
    sc.camera = cam
    for t, dd in ((0.0, dist), (dur, dist - push)):
        pos = c + n * dd
        z = (pos - tgt).normalized()
        x = u.cross(z).normalized()
        y = z.cross(x)
        cam.matrix_world = Matrix.Translation(pos) @ Matrix((x, y, z)).transposed().to_4x4()
        cam.keyframe_insert('location', frame=F(t))
        cam.keyframe_insert('rotation_euler', frame=F(t))
    cd.clip_start = 0.05                                # голову прячет материал; clip_start резал кулаки (25.11)
    return cam


def phone_screen_on(ph, coll, items=None, png=None, scroll=None, strength=1.2, movie=None, frames=0):
    """Экран(ы) телефона детьми корня: items=[(png, t)] по очереди или один png (scroll — прокрутка ленты);
    movie — под слоями items играет видео (v2, лента «Для вас»)."""
    rot = (math.pi / 2, 0, 0)
    loc = (0, -(PH_D / 2 + 0.0007), 0)
    if movie:
        obs = video_stack(coll, ph.name + 'S', movie, frames, items, SCR_W, SCR_H, loc, rot, strength)
    else:
        obs = stack(coll, ph.name + 'S', items, SCR_W, SCR_H, loc, rot, strength) if items else \
            [screen(coll, ph.name + 'S', png, SCR_W, SCR_H, loc, rot, strength, scroll)]
    for o in obs:
        o.parent = ph
        for m in o.data.materials:                      # блик слабее и мягче: чёткое отражение подбородка читалось как дуга
            for n in m.node_tree.nodes:
                if n.type == 'BSDF_GLOSSY':
                    n.inputs['Roughness'].default_value = 0.4
                elif n.type == 'MIX_SHADER':
                    n.inputs['Fac'].default_value = 0.025
    return obs


# ============================================================================= планы
def v_feed(shot, fps):
    """POV: экран телефона крупно, лента безликого канала листается, камера отходит и видно руку и колени."""
    dur = shot['dur']
    coll, out, scr = base()
    h = H.load(coll, BED_SEAT, 0.0)
    sp = H.pose('sit', head=(0, 26, 0), **BED_LEGS, **HOLD)
    H.key_pose(h, 0, sp)
    H.key_pose(h, dur, H.pose(sp, head=(0, 24, 3)))
    ph = hold_phone(h, phone(coll), 0.0, 'Right', tilt=60)
    phone_screen_on(ph, coll, png=ui('phone_feed'), scroll=[(0.0, 0.0), (dur * 0.45, 0.0), (dur * 0.7, 0.5), (dur, 0.5)])
    phone_cam(h, ph, dur)
    return dict(fill=0.25, exposure=0.3, samples=32)


def v_tiktok(shot, fps):
    """v2, mike 25.11: «пример с тиктоком, что щас такое залетает». POV: в телефоне лента «Для вас», играет наш 3D-ролик
    (feed_hero.mp4: план v1 с героем, листается на следующий), сердечки всплывают, «в рекомендациях». Без цифр."""
    dur = shot['dur']
    coll, out, scr = base()
    h = H.load(coll, BED_SEAT, 0.0)
    sp = H.pose('sit', head=(0, 26, 0), **BED_LEGS, **HOLD)
    H.key_pose(h, 0, sp)
    H.key_pose(h, dur, H.pose(sp, head=(0, 23, -3)))
    ph = hold_phone(h, phone(coll), 0.0, 'Right', tilt=60)
    n = 12
    items = [('phone_tt%02d' % k, dur * k / n) for k in range(n)]
    phone_screen_on(ph, coll, items=items, strength=1.25, movie=media('feed_hero.mp4'), frames=int(round(dur * fps)) + 2)
    phone_cam(h, ph, dur)
    return dict(fill=0.25, exposure=0.3, samples=32, still_t=0.5)


def _bed_hero(coll, dur, notes_t=()):
    h = H.load(coll, BED_SEAT, 0.0)
    sp = H.pose('sit', head=(0, 24, 0), **BED_LEGS, **HOLD)
    H.key_pose(h, 0, sp)
    for k, t in enumerate(notes_t):                 # на каждое уведомление голова чуть приподнимается, брови вверх
        H.key_pose(h, t + 0.15, H.pose(sp, head=(0, 18 - 2 * k, 4 * (-1) ** k)))
    H.key_pose(h, dur, H.pose(sp, head=(0, 16, -3)))
    ph = hold_phone(h, phone(coll), 0.0, 'Right', tilt=60)
    return h, ph


def v_sofa(shot, fps):
    """Герой на кровати, лицо подсвечено телефоном; телефон звякает (экран вспыхивает)."""
    dur = shot['dur']
    coll, out, scr = base()
    t1 = _ev(shot, 'ping', dur * 0.45)
    h, ph = _bed_hero(coll, dur, (t1,))
    phone_screen_on(ph, coll, items=[('phone_notes0', 0.0), ('phone_notes1', t1)], strength=1.6)
    glow = lib.light('POINT', (0, 0, 0), energy=0.6, color='#CFE0FF', size=0.05, name='PhoneGlow', coll=coll)
    glow.parent = ph
    glow.location = (0, -0.12, 0)
    pc.key_light(glow, [(0, 0.6), (t1, 0.6), (t1 + 0.05, 2.2), (t1 + 0.5, 0.9), (dur, 0.9)])
    cam = lib.camera((0.6, -2.0, 1.12), (1.36, -0.5, 0.86), 42)
    lib.animate_camera(cam, [(0, (0.6, -2.0, 1.12)), (dur, (0.72, -1.82, 1.1))], [(0, (1.36, -0.5, 0.88)), (dur, (1.36, -0.5, 0.86))])
    cam.data.clip_start = 0.05
    return dict(fill=0.35, exposure=0.4, samples=32, still_t=0.6)


def v_notes(shot, fps):
    """POV: экран блокировки, уведомления о рекламе приходят одно за другим (без сумм)."""
    dur = shot['dur']
    coll, out, scr = base()
    ts = [_ev(shot, 'n1', 0.15), _ev(shot, 'n2', dur * 0.38), _ev(shot, 'n3', dur * 0.66)]
    h, ph = _bed_hero(coll, dur, ts)
    phone_screen_on(ph, coll, items=[('phone_notes1', 0.0), ('phone_notes2', ts[1]), ('phone_notes3', ts[2])], strength=1.4)
    phone_cam(h, ph, dur)
    return dict(fill=0.25, exposure=0.3, samples=32, still_t=0.8)


def v_night(shot, fps):
    """Ночь, ручной монтаж: на мониторе дорожки и «осталось 2 ч 40 мин», часы бегут, кружки копятся, герой клюёт носом."""
    dur = shot['dur']
    rng = random.Random(5)
    coll, out, scr = base(night=True, rng=rng)
    screen(coll, 'Edit', ui('mon_edit'), MON_W, MON_H, scr[0], scr[1], strength=1.5)
    lib.light('AREA', (MON.x, MON.y - 0.25, SCR_Z), (math.radians(90), 0, 0), energy=6, color='#9DB8FF', size=0.6, name='MonGlow',
              coll=coll)
    _, cups = desk_stuff(coll, rng, night=True, mugs=1)
    for k, grp in enumerate(cups[1:], 1):
        for o in grp:
            FX.key_hide(o, [(0, False), (dur * (0.2 + 0.22 * k), True)])
    wall_clock(coll, turns=(5.0, 5.0 / 12), dur=dur)
    h = seated(coll)
    tp = type_pose()
    typing(h, 0, dur * 0.45, tp)
    H.key_pose(h, dur * 0.62, H.pose(tp, head=(0, 30, 6), lean=14.0))         # клюёт носом
    H.key_pose(h, dur * 0.72, H.pose(tp, head=(0, -4, 0), lean=6.0))          # вздрогнул
    H.key_pose(h, dur, H.pose(tp, head=(0, 22, -4), lean=12.0))
    # v2 (mike 25.11: «голова гг закрывает основной вид картинки»): сзади-справа и выше, голова слева, монитор с дорожками
    # справа от неё целиком, окно с ночным городом; медленный наезд
    c0, c1 = (-0.3, -0.2, 1.75), (-0.4, -0.05, 1.7)
    cam = lib.camera(c0, (-1.4, 1.0, 1.05), 30)
    lib.animate_camera(cam, [(0, c0), (dur, c1)], [(0, (-1.4, 1.0, 1.05)), (dur, (-1.4, 1.0, 1.03))])
    cam.data.clip_start = 0.05
    return dict(fill=0.04, exposure=0.1, samples=32, fill_col='#9DB0E0')


def v_build(shot, fps):
    """День: пишет одну фразу, откидывается на спинку; на мониторе галочки «Сценарий, Голос, 3D-сцены, Субтитры» → готово."""
    dur = shot['dur']
    rng = random.Random(6)
    coll, out, scr = base(rng=rng)
    desk_stuff(coll, rng, mugs=1)
    wall_clock(coll, turns=(0.02, 0.0), dur=dur)
    tt = _ev(shot, 'typed', dur * 0.22)
    st = [_ev(shot, 's%d' % k, tt + (dur - tt) * (0.12 + 0.17 * k)) for k in range(5)]
    items = [('mon_type0', 0.0), ('mon_type35', tt * 0.3), ('mon_type70', tt * 0.6), ('mon_type100', tt * 0.85),
             ('mon_build0', tt)] + [('mon_build%d' % (k + 1), st[k]) for k in range(4)]
    stack(coll, 'Build', items, MON_W, MON_H, scr[0], scr[1], strength=1.3)
    h = seated(coll)
    tp = type_pose()
    typing(h, 0, tt, tp)
    lean_back = H.pose('sit', arm=(18, 22), fore=(24, 62), lean=-9.0, head=(0, -4, 8))     # откинулся, руки на коленях
    H.key_pose(h, tt + 0.6, lean_back)
    H.key_pose(h, dur, H.pose(lean_back, head=(0, -2, -6)))
    # v2: монитор крупно, камера между героем и экраном (голова позади камеры)
    c = Vector(scr[0])
    cam = lib.camera((c.x - 0.2, c.y - 0.68, c.z + 0.05), tuple(c), 30)
    lib.animate_camera(cam, [(0, (c.x - 0.2, c.y - 0.68, c.z + 0.05)), (dur, (c.x - 0.15, c.y - 0.57, c.z + 0.03))],
                       [(0, tuple(c)), (dur, tuple(c))])
    cam.data.clip_start = 0.02
    return dict(fill=0.35, exposure=0.4, samples=32, still_t=0.8)


def v_styles(shot, fps):
    """Монитор ближе: меню стилей, подсветка бежит по плиткам (3D и Пиксель есть, у остальных «скоро»)."""
    dur = shot['dur']
    rng = random.Random(7)
    coll, out, scr = base(rng=rng)
    desk_stuff(coll, rng, mugs=1)
    n = 12
    items = [('mon_styles%02d' % k, dur * k / n) for k in range(n)]
    stack(coll, 'Sty', items, MON_W, MON_H, scr[0], scr[1], strength=1.3)
    h = seated(coll)
    mp = H.pose('sit', arm=((14, 52), (20, 40)), fore=((10, 95), (12, 70)), head=(0, 4, 0), lean=8.0)
    H.key_pose(h, 0, mp)
    H.key_pose(h, dur, H.pose(mp, head=(0, 2, 6)))
    c = Vector(scr[0])
    cam = lib.camera((c.x + 0.28, c.y - 0.62, c.z + 0.02), tuple(c), 30)
    lib.animate_camera(cam, [(0, (c.x + 0.28, c.y - 0.62, c.z + 0.02)), (dur, (c.x + 0.18, c.y - 0.5, c.z + 0.01))],
                       [(0, tuple(c)), (dur, tuple(c))])
    cam.data.clip_start = 0.02
    return dict(fill=0.3, exposure=0.35, samples=32)


def v_plus(shot, fps):
    """v2 «Плюсы такого монтажа»: день, ролик собран (на мониторе «готово»), герой откинулся на спинку и довольно кивает
    на каждом плюсе (пункты — плашками KINEMA). Камера спереди-справа (FACE_R), лицо в 3/4, монитор не заслонён."""
    dur = shot['dur']
    rng = random.Random(11)
    coll, out, scr = base(rng=rng)
    desk_stuff(coll, rng, mugs=1)
    screen(coll, 'Done', ui('mon_build4'), MON_W, MON_H, scr[0], scr[1], strength=1.2)
    wall_clock(coll, turns=(0.02, 0.0), dur=dur)
    h = seated(coll)
    lb = H.pose('sit', arm=(18, 22), fore=(24, 62), lean=-9.0, head=(0, -4, 8))
    H.key_pose(h, 0, lb)
    for k in range(3):
        t = _ev(shot, 'p%d' % k, dur * (0.15 + 0.27 * k))
        H.key_pose(h, t, H.pose(lb, head=(0, -4, 8 - 6 * k)))
        H.key_pose(h, t + 0.18, H.pose(lb, head=(0, 8, 6 - 6 * k)))        # кивок
        H.key_pose(h, t + 0.42, H.pose(lb, head=(0, -2, 4 - 6 * k)))
    H.key_pose(h, dur, H.pose(lb, head=(0, -6, -10)))
    c0, c1 = FACE_R
    tg = FACE_T
    cam = lib.camera(c0, tg, 36)
    lib.animate_camera(cam, [(0, c0), (dur, c1)], [(0, tg), (dur, tg)])
    cam.data.clip_start = 0.05
    return dict(fill=0.4, exposure=0.4, samples=32, still_t=0.6)


SPLIT_AT = (-0.1, 0.75, 0.0)


def v_split(shot, fps):
    """v2, mike 25.11: «разделение на 2 экрана в каком-либо действии и объяснить, что вот такие уже есть стили».
    Герой стоит у окна («Метрополис» за ним), машет и делает оборот на месте. Кадр 1080×960: render_clips.py ставит
    его сверху как 3D, а снизу то же движение в нашем пиксельном стиле (PIXCINE, pixel/build_split_pixel.py; mike 26.11:
    «не просто пиксели вместо хорошего качества»), подписи стилей — плашки KINEMA."""
    dur = shot['dur']
    rng = random.Random(12)
    coll, out, scr = base(rng=rng)
    desk_stuff(coll, rng, mugs=1)
    sc = bpy.context.scene
    sc.render.resolution_y = int(round(sc.render.resolution_x * 960 / 1080))
    h = H.load(coll, SPLIT_AT, 0.0)
    st = H.pose('stand', head=(0, -6, 0))
    up = ((24, 4), (78, 22))
    t_sp0, t_sp1 = dur * 0.42, dur * 0.66
    t = 0.0
    k = 0
    while t < dur + 0.01:                           # машет правой рукой, кроме оборота
        if t_sp0 - 0.1 < t < t_sp1 + 0.1:
            H.key_pose(h, t, H.pose(st, arm=((26, 8), (30, 10)), fore=((20, 20), (24, 30)), side=0.0))
        else:
            a = 8 if k % 2 else 38
            H.key_pose(h, t, H.pose(st, arm=up, fore=((18, 16), (a, 158 - a * 0.3)), side=3.0 if k % 2 else -3.0,
                                    head=(0, -6, 6 if k % 2 else -6)))
        t += 0.26
        k += 1
    rig = h['rig']
    z0 = rig.rotation_euler.z
    for tt, z in ((0.0, z0), (t_sp0, z0), (t_sp1, z0 + 2 * math.pi), (dur, z0 + 2 * math.pi)):
        rig.rotation_euler.z = z
        rig.keyframe_insert('rotation_euler', index=2, frame=F(tt))
    # 26.11: герой во весь рост в нижних ~55 % половины, сверху окно и «Метрополис» — там встают титры KINEMA, они больше
    # не ложатся на голову; камера на высоте 1,6 м без наклона (без завала вертикалей), объектив 28 мм
    c0, c1 = (SPLIT_AT[0], SPLIT_AT[1] - 2.87, 1.62), (SPLIT_AT[0], SPLIT_AT[1] - 2.72, 1.6)
    tg0, tg1 = (SPLIT_AT[0], SPLIT_AT[1], 1.62), (SPLIT_AT[0], SPLIT_AT[1], 1.6)
    cam = lib.camera(c0, tg0, 28)
    lib.animate_camera(cam, [(0, c0), (dur, c1)], [(0, tg0), (dur, tg1)])
    cam.data.clip_start = 0.05
    return dict(fill=0.4, exposure=0.4, samples=32, still_t=0.3)


def v_calendar(shot, fps):
    """Календарь на стене заполняется превью роликов, клетка за клеткой; герой смотрит на него со стула."""
    dur = shot['dur']
    rng = random.Random(8)
    coll, out, scr = base(rng=rng)
    desk_stuff(coll, rng, mugs=1)
    calendar(coll, rng, fill=(0.2, dur * 0.85))
    # v2 (mike 25.11: «голова гг закрывает основной вид»): герой по другую сторону календаря (ближе к окну), в кадре слева от
    # него, а не перед ним; почти лицом к камере, левой рукой показывает на календарь
    h = H.load(coll, (1.85, 1.33, 0.0), -math.pi / 2 + 0.698)
    p = H.pose('stand', head=(0, -10, 6), arm=((55, 25), (24, 4)), fore=((30, 70), (18, 16)))   # левой рукой «смотри»
    H.key_pose(h, 0, p)
    H.key_pose(h, dur, H.pose(p, head=(0, -8, 10)))
    wall_clock(coll, turns=(0.0, 0.0), dur=dur)
    c0, c1 = (0.35, 0.32, 1.32), (0.45, 0.36, 1.33)
    cam = lib.camera(c0, (2.1, 0.85, 1.3), 32)
    lib.animate_camera(cam, [(0, c0), (dur, c1)], [(0, (2.1, 0.85, 1.3)), (dur, (2.1, 0.86, 1.31))])
    cam.data.clip_start = 0.05
    return dict(fill=0.35, exposure=0.4, samples=32, still_t=0.8)


def v_call(shot, fps):
    """Созвон «настроим за тебя»: на мониторе установка с галочками и помощник на связи, герой показывает «класс»."""
    dur = shot['dur']
    rng = random.Random(9)
    coll, out, scr = base(rng=rng)
    desk_stuff(coll, rng, mugs=1)
    items = [('mon_call0', 0.0), ('mon_call1', dur * 0.3), ('mon_call2', dur * 0.55)]
    stack(coll, 'Call', items, MON_W, MON_H, scr[0], scr[1], strength=1.3)
    h = seated(coll)
    p0 = H.pose('sit', arm=(16, 30), fore=(12, 70), head=(0, 2, 0))
    thumbs = H.pose('sit', arm=((16, 30), (22, 60)), fore=((12, 70), (14, 150)), head=(0, -4, -14))   # правая рука вверх, к камере
    H.key_pose(h, 0, p0)
    H.key_pose(h, _ev(shot, 'thumb', dur * 0.6), p0)
    H.key_pose(h, _ev(shot, 'thumb', dur * 0.6) + 0.35, thumbs)
    H.key_pose(h, dur, H.pose(thumbs, head=(0, -6, -18)))
    # v2: сначала экран созвона крупно, к «за тебя» камера уходит к лицу героя (большой палец); через плечо не снимаем
    c = Vector(scr[0])
    th = _ev(shot, 'thumb', dur * 0.6)
    s0, s1 = (c.x + 0.18, c.y - 0.64, c.z + 0.03), (c.x + 0.13, c.y - 0.55, c.z + 0.02)
    cam = lib.camera(s0, tuple(c), 32)
    lib.animate_camera(cam, [(0, s0), (max(0.2, th - 0.45), s1), (th + 0.12, FACE_R[0]), (dur, FACE_R[1])],
                       [(0, tuple(c)), (max(0.2, th - 0.45), tuple(c)), (th + 0.12, FACE_T), (dur, FACE_T)])
    cam.data.clip_start = 0.02
    return dict(fill=0.4, exposure=0.4, samples=32, still_t=0.9)


def v_comment(shot, fps):
    """POV: телефон в руках над столом, в поле комментария печатается «канал» и загорается кнопка отправки."""
    dur = shot['dur']
    rng = random.Random(10)
    coll, out, scr = base(rng=rng)
    desk_stuff(coll, rng, mugs=2)
    screen(coll, 'Idle', ui('mon_build4'), MON_W, MON_H, scr[0], scr[1], strength=1.1)
    h = seated(coll)
    p = H.pose('sit', head=(0, 16, 0), lean=4.0, **HOLD)          # не нависает над телефоном: лицо дальше от экрана
    H.key_pose(h, 0, p)
    H.key_pose(h, dur, H.pose(p, head=(0, 14, 2)))
    ph = hold_phone(h, phone(coll), 0.0, 'Right', tilt=60)
    t0, t1 = 0.3, _ev(shot, 'typed', dur * 0.55)            # «канал» допечатано к концу слова в голосе
    items = [('phone_comment0', 0.0)] + [('phone_comment%d' % k, t0 + (t1 - t0) * k / 5) for k in range(1, 6)]
    phone_screen_on(ph, coll, items=items, strength=1.3)
    phone_cam(h, ph, dur)
    return dict(fill=0.25, exposure=0.3, samples=32, still_t=0.8)


# ============================================================================= за окном — «Метрополис»
CITY_AT = Vector((0.0, 18.0, 24.0))         # пол комнаты: 8-й этаж над набережной, окно (+y) вдоль проспекта x = 0 в Даунтаун
CITY_DETAIL = 250.0                          # фасады вблизи с подоконниками, вывесками, балконами (metro_detail)
CITY_OVER = {}
WINDOW_PLANS = ('feed', 'tiktok', 'sofa', 'notes', 'night', 'build', 'plus', 'split', 'styles', 'calendar', 'call',
                'comment')


def city_view(shot, fps, preset='day'):
    """mike 25.11: «поменяй на улице вид на наш город новый». Комнату со всем содержимым (герой, камера, свет)
    переносим в «Метрополис» (blender/library/metro*.py), улицу-заглушку sila_sets.room() убираем. Солнце комнаты
    светит только комнату, солнце города — только город (light linking): иначе оно бьёт в открытую стену комнаты."""
    import metro
    import metro_build as MB
    import metro_mats as MM
    out = bpy.data.collections.get('RoomOutside')
    if out:
        for o in list(out.objects):
            bpy.data.objects.remove(o, do_unlink=True)
    room_objs = list(bpy.data.objects)
    room_suns = [o for o in room_objs if o.type == 'LIGHT' and o.data.type == 'SUN']
    root = lib.empty('RoomRoot', tuple(CITY_AT))
    for o in room_objs:
        if o.parent is None:
            o.parent = root
    frames = max(1, int(round(shot['dur'] * fps)))
    MM.set_global('FocusX', CITY_AT.x)
    MM.set_global('FocusY', CITY_AT.y)
    MM.set_global('FocusR', CITY_DETAIL)
    MB.build_city(focus=(CITY_AT.x, CITY_AT.y), detail_r=CITY_DETAIL, filler=True, fps=fps, frames=frames,
                  night=metro.PRESETS[preset]['night'], keep=[])
    metro.apply_preset(preset, CITY_OVER.get(preset))
    g = bpy.data.materials.get('WinGlass')                 # стекло почти без отражения комнаты: город за ним не в молоке
    if g and g.node_tree:
        for n in g.node_tree.nodes:
            if n.type == 'BSDF_PRINCIPLED':
                n.inputs['Alpha'].default_value = 0.04
                n.inputs['Specular IOR Level'].default_value = 0.25
    MM.key_time(fps, frames)
    lit = bpy.data.collections.new('RoomLit')                  # не в сцене: только список приёмников света
    for o in room_objs:
        if o.type in ('MESH', 'CURVE', 'FONT') and o.name in bpy.data.objects:
            lit.objects.link(o)
    for o in room_suns:
        o.light_linking.receiver_collection = lit
    metro_coll = bpy.data.collections.get('Metro')
    for nm in ('MetroSun', 'MetroMoon'):
        o = bpy.data.objects.get(nm)
        if o and metro_coll:
            o.light_linking.receiver_collection = metro_coll
    return root


def hero_tone(value=0.5, sat=1.12):
    """mike 26.11: «гг слишком яркий» — в белой дневной комнате кожа и кроссовки героя светились почти белым. Цвет всех
    материалов героя (и рук в POV) темнее и чуть насыщеннее: HSV после текстуры и масок глаз, до Base Color. Кожа в текстуре
    ~0.85 линейной яркости; пробы 26.11: 0.74 почти не видно, 0.5 — живой тон кожи."""
    done = set()
    for o in bpy.data.objects:
        if o.type != 'MESH' or not o.name.startswith('Hero'):
            continue
        for m in o.data.materials:
            if m is None or not m.use_nodes or m.name in done or m.get('kanal_tone'):
                continue
            done.add(m.name)
            N, L = m.node_tree.nodes, m.node_tree.links
            for b in [n for n in N if n.type == 'BSDF_PRINCIPLED']:
                inp = b.inputs['Base Color']
                if inp.links:
                    hsv = N.new('ShaderNodeHueSaturation')
                    hsv.inputs['Saturation'].default_value = sat
                    hsv.inputs['Value'].default_value = value
                    L.new(inp.links[0].from_socket, hsv.inputs['Color'])
                    L.new(hsv.outputs['Color'], inp)
                else:
                    inp.default_value = [c * value for c in inp.default_value[:3]] + [inp.default_value[3]]
            m['kanal_tone'] = 1
    return len(done)


def build(shot, fps=30):
    res = globals()['v_' + shot['variant']](shot, fps) or {}
    if shot['variant'] in WINDOW_PLANS and not shot.get('old_street'):
        city_view(shot, fps, 'night' if shot['variant'] == 'night' else 'day')
    hero_tone(shot.get('hero_value', 0.5))
    if shot['variant'] != 'night':          # 26.11: днём вся картинка на ~1/4 ступени темнее, заливка от камеры слабее
        res['exposure'] = round(res.get('exposure', 0.1) - 0.25, 3)
        res['fill'] = round(res.get('fill', 0.6) * 0.6, 3)
    return res
