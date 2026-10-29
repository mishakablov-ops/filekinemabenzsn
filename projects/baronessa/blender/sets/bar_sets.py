"""All scenes of «Баронесса-пулемётчица» (style «Мемы»): build(shot, fps) dispatches on shot['variant'].

Realistic look: PBR props (bar_props), the realistic baroness (baroness.py), lenses 40-85 mm, depth of field on close
shots, warm key + cool rim + sky, light fog; two camera keys per shot. Events (seconds inside the shot) come from the
voice through tools/build_timeline.py: shot['events'][name].
"""
import math
import os
import random

import bpy
from mathutils import Vector

import lib
import sila_hero as SH
import baroness as B
import bar_props as P

F = lib.sec2f
HERE = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.join(HERE, '..', 'tex')


def ev(shot, k, default):
    return float(shot.get('events', {}).get(k, default))


# ----------------------------------------------------------------------------- camera, sky, light
def cam(shot, p0, p1, t0=(0, 0, 1), t1=None, lens=50, dof=None, fstop=2.8, lens1=None):
    c = lib.camera(p0, t0, lens=lens)
    c.data.clip_start = 0.1
    d = shot['dur']
    lib.animate_camera(c, [(0, p0), (d, p1)], [(0, t0), (d, t1 or t0)],
                       lens_keys=[(0, lens), (d, lens1)] if lens1 else None)
    if dof is not None:
        c.data.dof.use_dof = True
        c.data.dof.aperture_fstop = fstop
        if isinstance(dof, (int, float)):
            c.data.dof.focus_distance = dof
        elif isinstance(dof, bpy.types.Object):
            c.data.dof.focus_object = dof
        else:
            e = lib.empty('Focus', loc=dof)
            c.data.dof.focus_object = e
    return c


def sky(kind='gold'):
    if kind == 'gold':        # warm golden hour (v2: the photographic HDRI sky when it is there)
        if not P.hdri_world(1.1, rot=math.radians(160)):
            lib.world_gradient('#7FA3C8', '#F3C894', '#E6B98A', strength=1.0)
        sun = lib.light('SUN', rot=(math.radians(68), 0, math.radians(-35)), energy=3.2, color='#FFD9A8', size=2.5)
    elif kind == 'morning':
        lib.world_gradient('#8FB4D9', '#EBDCC6', '#D8C7AE', strength=1.0)
        sun = lib.light('SUN', rot=(math.radians(55), 0, math.radians(30)), energy=3.5, color='#FFE8C8', size=2.0)
    elif kind == 'dusk':       # warm evening, still light
        lib.world_gradient('#4F6A93', '#F0A877', '#C98D6E', strength=0.9)
        sun = lib.light('SUN', rot=(math.radians(80), 0, math.radians(-60)), energy=2.2, color='#FFB27A', size=3.0)
    elif kind == 'snow':       # soft winter dusk with warm windows
        lib.world_gradient('#6F86A8', '#D6C3B6', '#B9B2B0', strength=0.95)
        sun = lib.light('SUN', rot=(math.radians(75), 0, math.radians(40)), energy=1.4, color='#FFD3B0', size=6.0)
    else:                      # interior: soft neutral world
        lib.world_color('#CDBCA6', 0.55)
        sun = None
    return sun


def interior_lights(key=(2.5, -3, 3.2), rim=(-2.2, 2.5, 2.6), k=600, r=380, kc='#FFE6C8', rc='#D8E2FF', size=2.5):
    lib.light('AREA', key, energy=k, size=size, color=kc)
    lib.light('AREA', rim, energy=r, size=size * 0.8, color=rc)
    for o in bpy.data.objects:
        if o.type == 'LIGHT' and o.data.type == 'AREA' and o.name.startswith('AREA'):
            lib.look_at(o, (0, 0, 1.0))


def room(w=6, d=6, h=3.2, wall='#CDBBA0', floor='wood', paper_wall=True):
    if floor == 'wood':
        fl = lib.plane((w, d), (0, 0, 0), P.wood('#7A5232', 'Parquet'), name='Floor')
    elif floor == 'marble':
        fl = lib.plane((w, d), (0, 0, 0), P.marble(), name='Floor')
    else:
        fl = lib.plane((w, d), (0, 0, 0), P.M('FloorMat', floor, rough=0.7), name='Floor')
    wm = P.M('Wallpaper' + wall, wall, rough=0.85, var=0.1, bump=0.15, bs=60, vs=40 if paper_wall else 6)
    lib.box((w, 0.1, h), (0, d / 2, h / 2), wm, bevel=0, name='WallBack')
    lib.box((0.1, d, h), (-w / 2, 0, h / 2), wm, bevel=0, name='WallL')
    lib.box((0.1, d, h), (w / 2, 0, h / 2), wm, bevel=0, name='WallR')
    lib.box((w, 0.06, 0.14), (0, d / 2 - 0.06, 0.07), P.wood('#4A2E1A', 'Skirting'), bevel=0.01, name='Skirting')
    return fl


def baroness(loc=(0, 0, 0), heading=0.0, pose='stand', name='Baroness', **kw):
    b = B.load(loc=loc, heading=heading, name=name)
    SH.key_pose(b, 0, B.P(pose, **kw))
    return b


def poses(b, keys):
    """keys: [(t, pose_name or dict)]"""
    for t, p in keys:
        SH.key_pose(b, t, B.P(p) if isinstance(p, str) else p)


def fog(d=0.01, col='#E6D5C0', size=(120, 120, 40), z=15):
    lib.fog_box(size=size, loc=(0, 0, z), density=d, color=col)


# ----------------------------------------------------------------------------- scenes
def s_album(shot, gone=False):
    sky('interior')
    lib.plane((4, 4), (0, 0, 0), P.wood('#5B3A22', 'Table'), name='Table')
    pm = P.paper('#E8DCC3', 'AlbumPage')
    cover = P.leather('#3E2416', 'AlbumCover')
    lib.box((0.62, 0.42, 0.03), (0, 0, 0.015), cover, bevel=0.008, name='AlbumCover')
    for sx in (-1, 1):
        pg = lib.box((0.29, 0.4, 0.012), (sx * 0.152, 0, 0.036), pm, bevel=0.003, name='Page')
        pg.rotation_euler.y = -sx * 0.035
    ph = P.uv_plane((0.16, 0.2133), (0.15, 0.0, 0.0445), m=P.sepia_image(os.path.join(TEX, 'portrait.jpg'), 'PhotoMat',
                                                                          fade='gone'), name='Photo')
    ph['gone'] = 0.0
    if gone:
        t = ev(shot, 'gone', shot['dur'] * 0.45)
        ph.keyframe_insert('["gone"]', frame=F(t - 0.1))
        ph['gone'] = 1.0
        ph.keyframe_insert('["gone"]', frame=F(t + 1.0))
    bk = P.M('PhotoCorner', '#1A1310', rough=0.5)
    for cx, cy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        c = lib.box((0.025, 0.025, 0.002), (0.15 + cx * 0.078, cy * 0.108, 0.0455), bk, bevel=0, name='Corner')
        c.rotation_euler.z = math.radians(45)
    # second photo on the left page: a street of the old town (warm blur of a hand-tinted photo)
    lib.box((0.17, 0.12, 0.002), (-0.15, 0.06, 0.0445), P.M('OldPhoto2', '#8F7A5E', rough=0.6, var=0.25, vs=30),
            bevel=0, name='Photo2')
    lib.box((0.12, 0.15, 0.002), (-0.16, -0.1, 0.0445), P.M('OldPhoto3', '#9C8566', rough=0.6, var=0.25, vs=24),
            bevel=0, name='Photo3')
    # props: reading glasses, a cup of tea, lace
    g = P.gold()
    for sx in (-1, 1):
        lib.cyl(0.028, 0.004, (0.43 + sx * 0.035, -0.12, 0.004), lib.mat('Lens', '#D8E4EA', rough=0.05, alpha=0.3),
                name='GlassLens')
        lib.cyl(0.03, 0.004, (0.43 + sx * 0.035, -0.12, 0.004), g, name='GlassRim')
    cup = lib.cyl(0.045, 0.07, (-0.45, -0.14, 0.035), P.M('China', '#F2EEE6', rough=0.2, coat=0.6), name='Cup')
    lib.cyl(0.04, 0.003, (-0.45, -0.14, 0.066), P.M('Tea', '#6B3A1A', rough=0.05), name='Tea')
    lib.cyl(0.075, 0.008, (-0.45, -0.14, 0.004), P.M('China', '#F2EEE6'), name='Saucer')
    lib.light('AREA', (0.6, -0.5, 1.1), energy=60, size=0.8, color='#FFD9A8')
    lib.light('AREA', (-0.8, 0.6, 0.9), energy=18, size=0.8, color='#C9D6FF')
    for o in bpy.data.objects:
        if o.type == 'LIGHT':
            lib.look_at(o, (0.1, 0, 0))
    if gone:
        cam(shot, (0.2, -0.32, 0.42), (0.17, -0.2, 0.3), (0.15, 0, 0.04), lens=50, dof=(0.15, 0, 0.045), fstop=4)
    else:
        cam(shot, (0.05, -0.55, 0.62), (0.16, -0.22, 0.3), (0.1, 0, 0.04), (0.15, 0, 0.045), lens=50,
            dof=(0.15, 0, 0.045), fstop=4)
    return dict(fill=0.25, exposure=0.15)


def s_studio(shot):
    sky('interior')
    room(8, 8, 4.0, wall='#8C7B68')
    bd = lib.plane((4.0, 3.4), (0, 1.2, 1.7), P.M('Backdrop', '#6F6658', rough=0.95, var=0.25, vs=1.5, bump=0.1),
                   rot=(math.radians(90), 0, 0), name='Backdrop')
    b = baroness((0, 0.4, 0), 0.0, 'strict', head=(0, 6, 0))
    poses(b, [(shot['dur'], B.P('strict', head=(-3, 4, 0)))])
    # a big wooden view camera on a tripod, foreground left; a flash pan
    wd, br = P.wood('#4B2E1A', 'CamWood'), P.brass()
    cx, cy = -0.95, -1.5
    lib.box((0.34, 0.42, 0.34), (cx, cy, 1.45), wd, bevel=0.02, name='CamBox')
    lib.box((0.3, 0.3, 0.3), (cx, cy - 0.32, 1.45), P.leather('#151210', 'Bellows'), bevel=0.04, name='Bellows')
    lib.cyl(0.075, 0.14, (cx, cy - 0.52, 1.45), br, rot=(math.radians(90), 0, 0), name='Lens')
    lib.cyl(0.06, 0.02, (cx, cy - 0.6, 1.45), lib.mat('LensGlass', '#1E2630', rough=0.02), rot=(math.radians(90), 0, 0),
            name='LensGlass')
    for a in (0, 2.1, 4.2):
        leg = lib.cyl(0.02, 1.35, (cx + 0.25 * math.sin(a), cy + 0.25 * math.cos(a), 0.65), wd,
                      rot=(0.2 * math.cos(a), -0.2 * math.sin(a), 0), name='Tripod')
    fl = lib.light('POINT', (0.9, -0.9, 2.2), energy=0, size=0.1, color='#FFF6E8')
    pan = lib.box((0.3, 0.06, 0.04), (0.9, -0.9, 2.2), P.steel(), bevel=0.005, name='FlashPan')
    flash_m = lib.mat('FlashGlow', '#FFFFFF', emit='#FFF4E0', emit_strength=0.0)
    glow = lib.sphere(0.06, (0.9, -0.9, 2.25), flash_m, name='Flash')
    t = ev(shot, 'flash', shot['dur'] * 0.6)
    for tt, e, g in ((t - 0.05, 0, 0), (t, 1500, 120), (t + 0.25, 0, 0)):
        fl.data.energy = e
        fl.data.keyframe_insert('energy', frame=F(tt))
        lib.key_value(flash_m.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'], F(tt), g)
    interior_lights((2, -2.5, 3), (-2.5, 2, 3), k=500, r=260)
    cam(shot, (-0.35, -2.7, 1.45), (-0.1, -2.0, 1.48), (0, 0.4, 1.15), (0, 0.4, 1.3), lens=44, dof=(0, 0.3, 1.4),
        fstop=3.2)
    return dict(fill=0.3, exposure=0.25)


def _town(rnd, rows=((-1, 6), (1, 6)), street_w=9.0, start=-6, snow=False, lit=0.35, shop=None, shop_at=(1, 1),
          lamps=True, extra_far=True):
    """Two rows of houses along +Y, the street between them."""
    houses = []
    for side, n in rows:
        y = start
        for i in range(n):
            w = rnd.uniform(6.5, 9.0)
            fl = rnd.choice((3, 3, 4, 4, 5))
            sh = shop if (side, i) == shop_at else (rnd.choice((None, None, 'ЛАВКА', 'АТЕЛЬЕ')) if not snow else None)
            houses.append(P.house(side * (street_w / 2 + 5), y + w / 2, w, 10, fl, rnd,
                                  heading=-side * math.pi / 2, win_lit=lit, shop=sh, snow=snow))
            y += w + rnd.uniform(0.1, 0.4)
    if lamps:
        for k in range(6):
            for side in (-1, 1):
                P.street_lamp((side * (street_w / 2 - 0.4), start + 3 + k * 9, 0), lit=snow)
    if extra_far:
        P.house(0, start + 62, 22, 10, 5, rnd, heading=0, win_lit=lit)
    return houses


def s_street1918(shot):
    rnd = random.Random(1918)
    sky('snow')
    P.cobbles((40, 120), (0, 30, 0))
    snowm = P.M('SnowGround', '#EEF1F4', rough=0.8, var=0.06, bump=0.4, bs=8)
    for side in (-1, 1):
        lib.box((3.0, 120, 0.12), (side * 6.0, 30, 0.06), snowm, bevel=0.03, name='Pavement')
    _town(rnd, snow=True, lit=0.45, shop='БУТИКЪ', shop_at=(1, 1))
    # the boutique window: three bags on stands, lit
    for k, c in enumerate(('#8B3A1E', '#C08A3E', '#2B2B2B')):
        P.handbag((9.4 - 0.2, 6.5 + k * 1.6, 0.9), rot=math.pi / 2, col=c, name=f'WinBag{k}')
    P.drifting_paper(0, (0, 0, 0), (1, 1, 1), 0, 1)
    _snowfall(shot, (-8, -6, 0), (8, 30, 9))
    fog(0.012, '#D9D2CF')
    cam(shot, (-1.2, -9, 1.7), (-0.6, -4.5, 1.9), (2.0, 10, 2.6), (3.2, 10, 3.0), lens=40)
    return dict(fill=0.35, exposure=0.35)


def _snowfall(shot, lo, hi, n=700, seed=7):
    """Snow as keyed small spheres falling slowly (deterministic for stills and clips)."""
    rnd = random.Random(seed)
    me = bpy.data.meshes.new('Flake')
    import bmesh
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.018)
    bm.to_mesh(me)
    me.materials.append(lib.mat('FlakeMat', '#FFFFFF', rough=0.6, emit='#FFFFFF', emit_strength=0.3))
    d = shot['dur'] + 0.5
    for i in range(n):
        ob = bpy.data.objects.new('Snow', me)
        bpy.context.scene.collection.objects.link(ob)
        x, y = rnd.uniform(lo[0], hi[0]), rnd.uniform(lo[1], hi[1])
        z0 = rnd.uniform(lo[2], hi[2] + 3)
        v = rnd.uniform(0.5, 0.9)
        ph = rnd.uniform(0, 6.28)
        for k in range(4):
            t = d * k / 3
            ob.location = (x + 0.2 * math.sin(t + ph), y, z0 - v * t)
            ob.keyframe_insert('location', frame=F(t))
        lib._set_interp(ob, 'LINEAR')
        ob.visible_shadow = False


def s_crib(shot):
    sky('interior')
    room(6, 6, 3.4, wall='#C9B79C')
    # shelves of bags on the back wall
    sh = P.wood('#3F2717', 'Shelf')
    rnd = random.Random(4)
    cols = ['#8B3A1E', '#C08A3E', '#2B2B2B', '#7A1424', '#D9C7A6', '#4F5B3A']
    for z in (1.0, 1.75, 2.5):
        lib.box((4.6, 0.4, 0.05), (0, 2.75, z), sh, bevel=0.01, name='Shelf')
        for k in range(6):
            P.handbag((-1.9 + k * 0.76, 2.7, z + 0.025), rot=rnd.uniform(-0.2, 0.2), w=0.3, h=0.22, d=0.14,
                      col=cols[(k + int(z * 3)) % len(cols)], name='ShelfBag')
    # the crib: dark wood with spindles, lace canopy
    wd = P.wood('#5A3620', 'Crib')
    lace = P.cloth('#F3EDE2', 'Lace')
    cx, cy = 0, 0.6
    lib.box((1.25, 0.7, 0.05), (cx, cy, 0.45), wd, bevel=0.01, name='CribBed')
    lib.box((1.2, 0.65, 0.14), (cx, cy, 0.53), lace, bevel=0.05, name='Mattress')
    for sx in (-1, 1):
        lib.box((0.05, 0.72, 0.95), (cx + sx * 0.64, cy, 0.48), wd, bevel=0.01, name='CribEnd')
        for k in range(12):
            lib.cyl(0.012, 0.42, (cx - 0.55 + k * 0.1, cy + sx * 0.34, 0.78), wd, name='Spindle')
        lib.box((1.3, 0.04, 0.04), (cx, cy + sx * 0.34, 1.0), wd, bevel=0.01, name='Rail')
    # the baby: a lace bundle, a small round face turned away, a tiny pilotka
    bundle = lib.sphere(0.2, (cx, cy, 0.68), lace, scale=(1.6, 0.9, 0.7), name='Bundle')
    face = lib.sphere(0.08, (cx - 0.25, cy - 0.02, 0.72), P.M('BabySkin', '#E8B89A', rough=0.55, sss=0.0), name='Face')
    cap = lib.sphere(0.07, (cx - 0.27, cy, 0.79), P.M('Khaki', '#6F6A3A', rough=0.9, bump=0.3, bs=200),
                     scale=(1.2, 0.55, 0.45), name='TinyCap')
    # a mobile of tiny handbags turning above
    mob = lib.empty('Mobile', loc=(cx, cy, 1.38))
    for k in range(4):
        a = k * math.pi / 2
        hb = P.handbag((0.25 * math.cos(a), 0.25 * math.sin(a), -0.25), w=0.09, h=0.07, d=0.04,
                       col=cols[k], name='MobBag', lock=False)
        hb.parent = mob
        thr = P.tube([(0.25 * math.cos(a), 0.25 * math.sin(a), -0.15), (0.25 * math.cos(a), 0.25 * math.sin(a), 0)],
                     0.0015, P.M('Thread', '#CFC6B6'), 'Thread')
        thr.parent = mob
    lib.key_obj(mob, F(0), rot=(0, 0, 0), interp='LINEAR')
    lib.key_obj(mob, F(shot['dur']), rot=(0, 0, 1.2), interp='LINEAR')
    lib.light('AREA', (1.6, -1.4, 2.6), energy=420, size=1.5, color='#FFE3C0')
    lib.light('AREA', (-1.8, 1.5, 2.4), energy=180, size=1.5, color='#E6ECFF')
    lib.light('POINT', (-1.5, 2.2, 1.6), energy=40, color='#FFC27A')
    for o in bpy.data.objects:
        if o.type == 'LIGHT' and o.data.type == 'AREA':
            lib.look_at(o, (0, 0.6, 0.8))
    cam(shot, (0.9, -1.6, 1.45), (0.6, -1.1, 1.3), (0, 0.6, 0.85), (-0.1, 0.6, 0.8), lens=40, dof=(cx - 0.2, cy, 0.72),
        fstop=3.5)
    return dict(fill=0.3, exposure=0.25)


def s_dustbag(shot):
    sky('interior')
    lib.world_color('#2C2621', 0.5)
    lib.plane((6, 6), (0, 0, 0), P.cloth('#5C1622', 'VelvetFloor'), name='Velvet')
    pil = lib.sphere(0.4, (0, 0, 0.08), P.M('Satin', '#C9A76A', rough=0.3, coat=0.5), scale=(1.0, 0.8, 0.22),
                     name='Pillow')
    db = P.dust_bag((0, 0, 1.2), w=0.42, h=0.5, name='Pyl')
    t = ev(shot, 'word', shot['dur'] * 0.4)
    lib.key_obj(db, F(0), loc=(0, 0, 1.4))
    lib.key_obj(db, F(t + 0.15), loc=(0, 0, 0.15))
    sp = lib.light('SPOT', (0, -0.5, 3.0), energy=900, spot=34, blend=0.5, size=0.4, color='#FFE1B8')
    lib.look_at(sp, (0, 0, 0.2))
    lib.light('AREA', (-1.2, 1.0, 1.2), energy=60, size=1, color='#C9D6FF')
    fog(0.02, '#7C6B5A', size=(8, 8, 6), z=2)
    cam(shot, (0, -1.9, 0.75), (0, -1.6, 0.6), (0, 0, 0.35), (0, 0, 0.3), lens=55, dof=(0, 0, 0.35), fstop=4)
    return dict(fill=0.15, exposure=0.2)


def s_zipper(shot):
    sky('interior')
    lib.world_color('#3A3029', 0.4)
    lib.plane((4, 4), (0, 0, 0), P.wood('#4E321D', 'Counter'), name='Counter')
    lm = P.leather('#8A4A22', 'BagMacro')
    top = lib.box((0.8, 0.3, 0.12), (0, 0, 0.06), lm, bevel=0.04, name='BagTop')
    g = P.gold()
    teeth = []
    for k in range(70):
        x = -0.36 + k * 0.0105
        for sy in (-1, 1):
            teeth.append(lib.box((0.006, 0.008, 0.004), (x, sy * 0.005, 0.122), g, bevel=0.001, name='Tooth'))
    tape = lib.box((0.76, 0.04, 0.003), (0, 0, 0.1205), P.cloth('#2A1A10', 'ZipTape'), bevel=0, name='Tape')
    pull = lib.box((0.03, 0.022, 0.014), (-0.3, 0, 0.13), g, bevel=0.004, name='Slider')
    tab = lib.box((0.018, 0.05, 0.004), (-0.3, -0.035, 0.128), g, bevel=0.002, name='PullTab')
    tab.parent = pull
    tab.location = (0, -0.035, -0.002)
    t = ev(shot, 'zip', shot['dur'] * 0.45)
    lib.key_obj(pull, F(0), loc=(-0.3, 0, 0.13))
    lib.key_obj(pull, F(t - 0.1), loc=(-0.3, 0, 0.13))
    lib.key_obj(pull, F(t + 0.7), loc=(0.2, 0, 0.13))
    # a stitched seam and an embossed crest
    for k in range(40):
        lib.box((0.008, 0.002, 0.002), (-0.38 + k * 0.019, -0.15, 0.1), P.M('Stitch', '#E4D2B0'), bevel=0, name='St')
    lib.light('AREA', (0.4, -0.5, 0.6), energy=40, size=0.4, color='#FFE3C0')
    lib.light('AREA', (-0.5, 0.5, 0.4), energy=20, size=0.4, color='#D0DCFF')
    for o in bpy.data.objects:
        if o.type == 'LIGHT':
            lib.look_at(o, (0, 0, 0.12))
    cam(shot, (-0.5, -0.16, 0.2), (-0.42, -0.14, 0.19), (-0.15, 0, 0.122), (0.05, 0, 0.122), lens=70, dof=pull,
        fstop=4)
    return dict(fill=0.2, exposure=0.15)


def s_queue(shot):
    sky('interior')
    fl = room(16, 22, 5.0, wall='#D8CBB5', floor='marble')
    rnd = random.Random(10)
    # store front with glass doors at the end, a big sale sign
    gl = lib.mat('ShopGlass', '#A9BDC6', rough=0.05, alpha=0.35)
    lib.box((4, 0.1, 3.2), (0, 10.9, 1.6), gl, bevel=0, name='Doors')
    for x in (-2.05, 0, 2.05):
        lib.box((0.12, 0.16, 3.3), (x, 10.85, 1.65), P.gold(), bevel=0.01, name='DoorFrame')
    s = P.sign('РАСПРОДАЖА', (0, 10.75, 3.95), size=0.42, board=(5.6, 0.9), col='#5B1420', txt='gold', name='Sale')
    # the queue between brass stanchions: mannequins with handbags
    cols = ['#8B3A1E', '#C08A3E', '#2B2B2B', '#7A1424', '#D9C7A6', '#4F5B3A', None]
    posts = []
    for k in range(9):
        y = 9.5 - k * 1.25
        for x in (-0.9, 0.9):
            P.stanchion((x, y))
            posts.append((x, y))
        if k:
            for x in (-0.9, 0.9):
                P.rope((x, y + 1.25, 0), (x, y, 0))
        if k < 8:
            P.mannequin((rnd.uniform(-0.15, 0.15), y - 0.4, 0), heading=math.pi + rnd.uniform(-0.2, 0.2),
                        bag_col=cols[k % len(cols)], rnd=rnd, name=f'Man{k}')
    # at the head of the queue: a small podium with a brass megaphone and a child's garrison cap
    lib.box((0.6, 0.6, 0.5), (1.7, 8.2, 0.25), P.wood('#5A3620', 'Podium'), bevel=0.02, name='Podium')
    meg = lib.cyl(0.13, 0.4, (1.7, 8.15, 0.6), P.brass(), r2=0.04, rot=(math.radians(80), 0, math.radians(20)),
                  name='Megaphone')
    lib.sphere(0.09, (1.62, 8.32, 0.55), P.M('Khaki', '#6F6A3A', rough=0.9, bump=0.3, bs=200), scale=(1.3, 0.5, 0.45),
               name='KidCap')
    for k in range(4):
        lib.light('AREA', (0, 8 - k * 5, 4.8), rot=(0, 0, 0), energy=500, size=3, color='#FFE8CC')
    lib.light('AREA', (0, 11.5, 2.5), rot=(math.radians(90), 0, 0), energy=300, size=4, color='#FFF3E0')
    cam(shot, (2.6, -1.0, 1.7), (2.0, 2.5, 1.65), (0, 6, 1.2), (0, 9, 1.4), lens=40, dof=(0.5, 5.5, 1.2), fstop=4)
    return dict(fill=0.3, exposure=0.3)


def s_crate(shot):
    sky('interior')
    lib.world_color('#2F2822', 0.45)
    room(8, 8, 4, wall='#6B5D4E', floor='#5D5247')
    wd = P.wood('#8A6A44', 'CrateWood')
    W, D, H = 1.4, 0.7, 0.5
    for sy in (-1, 1):
        lib.box((W, 0.04, H), (0, sy * D / 2, H / 2), wd, bevel=0.008, name='CrateSide')
    for sx in (-1, 1):
        lib.box((0.04, D, H), (sx * W / 2, 0, H / 2), wd, bevel=0.008, name='CrateEnd')
    lib.box((W, D, 0.04), (0, 0, 0.02), wd, bevel=0.008, name='CrateBottom')
    straw = P.M('Straw', '#C9A55A', rough=0.95, var=0.3, bump=0.6, bs=90, vs=50)
    lib.box((W - 0.06, D - 0.06, 0.2), (0, 0, 0.14), straw, bevel=0.06, name='Straw')
    g = P.coupon_gun((-0.3, 0, 0.32), rot=math.pi / 2, name='Gun')     # barrel along +X, muzzle inside the crate
    g.scale = (0.95, 0.95, 0.95)
    lid = lib.empty('LidHinge', loc=(0, D / 2, H))
    lb = lib.box((W + 0.04, D + 0.04, 0.04), (0, -D / 2, 0.02), wd, bevel=0.008, name='Lid')
    lb.parent = lid
    stencil = P.text('ОСТОРОЖНО: СКИДКИ', 0.06, (0, -D / 2 - 0.0, 0.045), rot=(0, 0, 0),
                     m=P.M('Stencil', '#2A1E14', rough=0.9), font=P.SANS, extrude=0.0005)
    stencil.parent = lid
    t = ev(shot, 'open', 0.5)
    lib.key_obj(lid, F(0), rot=(0, 0, 0))
    lib.key_obj(lid, F(t), rot=(0, 0, 0))
    lib.key_obj(lid, F(t + 1.1), rot=(math.radians(-105), 0, 0))
    glow = lib.light('AREA', (0, 0, 0.42), energy=0, size=1.0, color='#FFCF8A')
    glow.rotation_euler = (math.radians(180), 0, 0)
    glow2 = lib.light('POINT', (0, 0, 0.6), energy=0, size=0.4, color='#FFCF8A')
    for L, e in ((glow, 50), (glow2, 40)):
        L.data.energy = 0
        L.data.keyframe_insert('energy', frame=F(t))
        L.data.energy = e
        L.data.keyframe_insert('energy', frame=F(t + 1.0))
    lib.light('AREA', (1.5, -1.5, 2.2), energy=140, size=2, color='#FFE0B8')
    lib.light('AREA', (-1.8, 1.5, 2.0), energy=90, size=2, color='#C8D4FF')
    for o in bpy.data.objects:
        if o.type == 'LIGHT' and o.data.type == 'AREA' and o not in (glow,):
            lib.look_at(o, (0, 0, 0.4))
    fog(0.03, '#8A735C', size=(8, 8, 4), z=2)
    cam(shot, (0.2, -1.1, 1.55), (0.15, -0.8, 1.3), (0.1, 0, 0.3), (0.1, 0, 0.3), lens=35, dof=(0.1, 0, 0.33),
        fstop=5)
    return dict(fill=0.2, exposure=0.3)


def _hall(rows=5, w=14, d=30, h=7):
    """A marble department-store hall with columns and a gallery (Biркинштат's grand store)."""
    lib.plane((w, d), (0, d / 2 - 6, 0), P.marble(), name='Floor')
    wm = P.M('HallWall', '#E3D7C4', rough=0.7, var=0.06, bump=0.1)
    lib.box((w, 0.2, h), (0, d - 6, h / 2), wm, bevel=0, name='HallBack')
    for sx in (-1, 1):
        lib.box((0.2, d, h), (sx * w / 2, d / 2 - 6, h / 2), wm, bevel=0, name='HallSide')
        for k in range(rows):
            y = -2 + k * (d - 6) / rows
            lib.cyl(0.35, h, (sx * (w / 2 - 1.6), y, h / 2), P.marble('#F0EBE2', '#B5ACA0', 'ColMarble'), verts=40,
                    name='Column')
            lib.cyl(0.48, 0.3, (sx * (w / 2 - 1.6), y, h - 0.15), P.gold(), verts=40, name='Capital')
            lib.cyl(0.48, 0.3, (sx * (w / 2 - 1.6), y, 0.15), P.marble('#F0EBE2', '#B5ACA0', 'ColMarble'), verts=40,
                    name='Base')
    lib.box((w, d, 0.3), (0, d / 2 - 6, h + 0.15), wm, bevel=0, name='Ceiling')
    for k in range(4):
        lib.light('AREA', (0, -1 + k * 6, h - 0.3), energy=900, size=4, color='#FFE9D0')
        ch = lib.sphere(0.35, (0, -1 + k * 6, h - 1.0), lib.mat('Chandelier', '#FFE4B0', rough=0.2, emit='#FFD28A',
                                                                  emit_strength=6.0), name='Chandelier')
    # shop counters with bags along the sides
    rnd = random.Random(9)
    cols = ['#8B3A1E', '#C08A3E', '#2B2B2B', '#7A1424', '#D9C7A6']
    for sx in (-1, 1):
        for k in range(4):
            y = 3 + k * 4
            lib.box((1.0, 2.4, 1.0), (sx * (w / 2 - 3.2), y, 0.5), P.wood('#3F2717', 'CounterWood'), bevel=0.02,
                    name='Counter')
            lib.box((1.02, 2.42, 0.03), (sx * (w / 2 - 3.2), y, 1.015), lib.mat('CounterGlass', '#B8C8CF', rough=0.03,
                                                                                alpha=0.3), bevel=0, name='CGlass')
            for j in range(3):
                P.handbag((sx * (w / 2 - 3.2), y - 0.7 + j * 0.7, 1.03), rot=sx * math.pi / 2,
                          col=cols[rnd.randrange(len(cols))], w=0.3, h=0.22, d=0.14, name='CBag')


def s_gun(shot):
    sky('interior')
    _hall()
    b = baroness((0, 0.35, 0), 0.0, 'hold_gun')
    g = P.coupon_gun((0, -0.25, 0.98), rot=0.0, name='Gun', carriage=True)
    g.scale = (1.1, 1.1, 1.1)
    t0 = ev(shot, 'fire', 0.6)
    # recoil: a small shiver of the gun while firing
    for k in range(int((shot['dur'] - t0) / 0.08)):
        t = t0 + k * 0.08
        lib.key_obj(g, F(t), loc=(0, -0.25 + (0.012 if k % 2 else 0), 0.98), interp='LINEAR')
    bpy.context.scene.frame_set(1)
    mz = P.muzzle_world(g)
    P.flying_paper(140, mz, (0, -9.0, 1.2), t0, shot['dur'] - 0.2, spread=0.22, life=1.5, seed=11)
    flash = lib.light('POINT', tuple(mz), energy=0, size=0.1, color='#FFD9A0')
    for k in range(int((shot['dur'] - t0) / 0.1)):
        t = t0 + k * 0.1
        flash.data.energy = 300 if k % 2 == 0 else 20
        flash.data.keyframe_insert('energy', frame=F(t))
    P.drifting_paper(60, (-5, -6, 0.1), (5, 4, 5), 0, shot['dur'], seed=2, fall=0.4)
    cam(shot, (1.6, -3.4, 1.35), (1.1, -2.6, 1.3), (0, 0.2, 1.25), (0, 0.2, 1.3), lens=40, dof=(0, 0.3, 1.4), fstop=3.5)
    return dict(fill=0.35, exposure=0.3)


def s_tags(shot):
    sky('interior')
    _hall()
    g = P.coupon_gun((0, 0, 1.0), rot=math.radians(20), name='Gun', carriage=True)      # barrel along (+0.34, -0.94)
    bpy.context.scene.frame_set(1)
    mz = P.muzzle_world(g)
    d = Vector((math.sin(math.radians(20)), -math.cos(math.radians(20)), 0.05))
    P.flying_paper(160, mz, tuple(d * 8), 0.05, shot['dur'] - 0.1, spread=0.2, life=1.4, kind='tag', seed=21)
    fl = lib.light('POINT', tuple(mz), energy=0, size=0.1, color='#FFD9A0')
    for k in range(int(shot['dur'] / 0.1)):
        fl.data.energy = 260 if k % 2 == 0 else 15
        fl.data.keyframe_insert('energy', frame=F(k * 0.1))
    # beside the gun, looking along the barrel: the jacket and the muzzle in front, the tags streaming away
    c = cam(shot, (0.75, 0.55, 1.25), (0.85, 0.2, 1.2), (0.2, -0.8, 1.02), (0.45, -1.6, 1.0), lens=40,
            dof=(0.25, -0.75, 1.0), fstop=4)
    return dict(fill=0.3, exposure=0.3)


def s_sale(shot):
    sky('morning')
    rnd = random.Random(3)
    P.cobbles((30, 40), (0, 5, 0))
    # a row of shop windows with sale posters
    for k, txt in enumerate(('−30%', '−50%', '−70%', '−90%')):
        x = -6 + k * 4
        lib.box((3.8, 0.4, 5), (x, 3.0, 2.5), P.M('Facade', '#E3D5BF', rough=0.85, var=0.1, bump=0.2), bevel=0.02,
                name='Facade')
        lib.box((3.0, 0.1, 2.4), (x, 2.78, 1.5), lib.mat('ShopWinLit', '#FFE7C4', rough=0.2, emit='#FFD9A8',
                                                           emit_strength=1.6), bevel=0, name='ShopWin')
        post = lib.box((1.8, 0.02, 1.2), (x, 2.7, 1.6), P.paper('#F6F1E8', 'Poster'), bevel=0, name='Poster')
        tx = P.text(txt, 0.55, (x, 2.68, 1.58), m=P.M('PosterRed', '#C8202A', rough=0.6), font=P.SANS, extrude=0.002)
        # the posters slap on one after another
        t = 0.3 + k * 0.45
        for o in (post, tx):
            lib.key_obj(o, F(0), scale=(0.001, 1, 0.001))
            lib.key_obj(o, F(t), scale=(0.001, 1, 0.001))
            lib.key_obj(o, F(t + 0.18), scale=(1.08, 1, 1.08))
            lib.key_obj(o, F(t + 0.3), scale=(1, 1, 1))
        P.sign('ЛАВКА', (x, 2.7, 3.3), size=0.24, board=(2.6, 0.5), name='ShopSign')
    P.ad_column((-4.2, -1.0, 0), name='AdColS', seed=1)
    P.truck40((6.5, 0.2, 0), heading=math.radians(90), name='Lorry')
    P.drifting_paper(160, (-8, -4, 0.2), (8, 2.6, 6), 0, shot['dur'], seed=8, fall=0.55)
    for k in range(40):
        c = bpy.data.objects.new('FloorCoupon', P.coupon_mesh())
        bpy.context.scene.collection.objects.link(c)
        c.location = (rnd.uniform(-7, 7), rnd.uniform(-3, 2.5), 0.002)
        c.rotation_euler = (math.radians(90), 0, rnd.uniform(0, 6.3))
        c.material_slots[0].link = 'OBJECT'
        c.material_slots[0].material = P.tag_mats()[rnd.randrange(4)]
    cam(shot, (-1.5, -7.5, 1.6), (1.5, -7.0, 1.7), (-0.5, 2.7, 1.6), (1.5, 2.7, 1.7), lens=40)
    return dict(fill=0.3, exposure=0.3)


def _castle(loc=(0, 30, 0), flag_cols=('#111111', '#F4F1EA'), white_flag=None):
    """Château of the county KokoChanel: white stone walls, black slate cone roofs, a string of pearls along the wall."""
    x0, y0, z0 = loc
    st = P.M('WhiteStone', '#ECE6DA', rough=0.8, var=0.08, bump=0.3, bs=10)
    sl = P.M('BlackSlate', '#1B1C1F', rough=0.45, var=0.08, bump=0.2)
    hill = lib.sphere(40, (x0, y0 + 4, z0 - 38.5), P.M('Grass', '#7F8F4E', rough=0.9, var=0.25, bump=0.4, vs=0.3),
                      scale=(1.6, 1.0, 1.0), name='Hill')
    lib.box((22, 8, 9), (x0, y0, z0 + 4.5), st, bevel=0.1, name='Keep')
    lib.box((22.4, 8.4, 0.5), (x0, y0, z0 + 9.2), sl, bevel=0.05, name='KeepRoof')
    towers = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            tx, ty = x0 + sx * 11, y0 + sy * 4
            lib.cyl(2.2, 13, (tx, ty, z0 + 6.5), st, verts=48, name='Tower')
            lib.cyl(2.6, 5.5, (tx, ty, z0 + 15.75), sl, r2=0.05, verts=48, name='Cone')
            towers.append((tx, ty))
    lib.cyl(3.2, 18, (x0, y0 + 2, z0 + 9), st, verts=48, name='Donjon')
    lib.cyl(3.6, 7, (x0, y0 + 2, z0 + 21.5), sl, r2=0.05, verts=48, name='DonjonCone')
    # windows: tall, black frames
    gl = lib.mat('CastleGlass', '#2A3036', rough=0.05)
    for k in range(8):
        lib.box((1.0, 0.2, 2.2), (x0 - 7.7 + k * 2.2, y0 - 4.05, z0 + 5.5), gl, bevel=0, name='CWin')
        lib.box((1.2, 0.22, 0.18), (x0 - 7.7 + k * 2.2, y0 - 4.08, z0 + 6.7), sl, bevel=0, name='CWinTop')
    # a string of pearls along the wall top
    pearl = P.M('Pearl', '#F3EEE6', rough=0.15, coat=0.8)
    for k in range(60):
        u = k / 59
        x = x0 - 10 + 20 * u
        lib.sphere(0.22, (x, y0 - 4.3, z0 + 8.2 - 1.2 * math.sin(math.pi * (u * 4 % 1))), pearl, segs=16, rings=8,
                   name='Pearl')
    # the gate: a white arch with black doors
    lib.box((5, 1.0, 6.2), (x0, y0 - 4.3, z0 + 3.1), st, bevel=0.08, name='GateArch')
    doors = []
    for sx in (-1, 1):
        hinge = lib.empty('DoorHinge', loc=(x0 + sx * 1.5, y0 - 4.85, z0))
        dd = lib.box((1.5, 0.15, 4.2), (-sx * 0.75, 0, 2.1), P.wood('#141210', 'BlackDoor'), bevel=0.03, name='Door')
        dd.parent = hinge
        doors.append(hinge)
    fl = P.flag((x0, y0 + 2, z0 + 25), size=(3.2, 2.0), stripes=flag_cols, pole=4.5, name='CastleFlag')
    return doors, towers


def s_castle(shot):
    sky('gold')
    lib.plane((400, 400), (0, 0, -0.01), P.M('Meadow', '#8A9A55', rough=0.9, var=0.3, bump=0.3, vs=0.2), name='Meadow')
    _castle()
    rnd = random.Random(2)
    for k in range(60):                        # poplar rows and a road
        x = rnd.choice((-1, 1)) * rnd.uniform(16, 60)
        y = rnd.uniform(-10, 80)
        h = rnd.uniform(6, 11)
        lib.cyl(0.25, h * 0.4, (x, y, h * 0.2), P.wood('#4A3424', 'Trunk'), name='Trunk')
        lib.sphere(1.2, (x, y, h * 0.65), P.M('Leaves', '#5E7A3A', rough=0.9, var=0.3, bump=0.5, vs=2),
                   scale=(1, 1, h / 3.5), name='Crown')
    lib.plane((6, 40), (0, 6, 0.01), P.M('Road', '#B7A88E', rough=0.95, var=0.2, bump=0.3), name='Road')
    P.truck40((-1.2, -2.0, 0), heading=math.radians(180), name='Lorry')        # the baroness's column arrives
    P.truck40((1.4, -9.0, 0), heading=math.radians(180), name='Lorry2', col='#5A6244')
    fog(0.006, '#EED9BD', size=(300, 300, 60), z=25)
    cam(shot, (-24, -32, 9), (-14, -28, 7), (0, 30, 9), (0, 30, 10), lens=44)
    return dict(fill=0.35, exposure=0.25)


def s_gates(shot):
    sky('gold')
    lib.plane((400, 400), (0, 0, -0.01), P.M('Meadow', '#8A9A55', rough=0.9, var=0.3, bump=0.3, vs=0.2), name='Meadow')
    lib.plane((6, 40), (0, 6, 0.01), P.M('Road', '#B7A88E', rough=0.95, var=0.2, bump=0.3), name='Road')
    _castle((0, 14, 0))
    b = baroness((0.4, 3.0, 0), math.pi, 'stand')       # facing the gate (+Y)
    poses(b, [(shot['dur'], B.P('strict'))])
    g = P.coupon_gun((-0.6, 3.3, 0.6), rot=math.pi + 0.3, name='Gun', carriage=True)
    fog(0.006, '#EED9BD', size=(300, 300, 60), z=25)
    cam(shot, (2.6, -3.2, 1.5), (1.9, -1.6, 1.45), (0.2, 6, 2.2), (0.2, 8, 2.8), lens=40, dof=(0.4, 3.0, 1.4), fstop=5)
    return dict(fill=0.35, exposure=0.25)


def s_face(shot, bg='castle', line='check'):
    """Close-up of the baroness speaking a line: slow push-in, shallow depth of field, a blurred place behind."""
    if bg == 'castle':
        sky('gold')
        lib.plane((400, 400), (0, 0, -0.01), P.M('Meadow', '#8A9A55', rough=0.9, var=0.3, bump=0.3, vs=0.2))
        _castle((0, 22, 0))
    elif bg == 'fortress':
        sky('dusk')
        lib.plane((400, 400), (0, 0, -0.01), P.M('Plain', '#A79B72', rough=0.9, var=0.3, bump=0.3, vs=0.2))
        _fortress((0, 12, -4.0))
    elif bg == 'fitting':
        sky('interior')
        room(6, 6, 3.2, wall='#7A2E35')
    elif bg == 'palace':
        sky('interior')
        _hall()
    b = baroness((0, 0, 0), 0.0, 'strict')
    d = shot['dur']
    if line == 'check':        # a cool polite question: the head tilts a little, then holds
        poses(b, [(0.6, B.P('strict', head=(0, 2, -4))), (d, B.P('strict', head=(4, 0, -6)))])
    elif line == 'refuse':     # chin up
        poses(b, [(0.5, B.P('strict', head=(0, -6, 0))), (d, B.P('strict', head=(-3, -8, 2)))])
    elif line == 'promise':
        poses(b, [(0.5, B.P('strict', head=(-10, 2, 0))), (d, B.P('strict', head=(-4, 4, 0)))])
    elif line == 'approve':    # one slow nod
        t = ev(shot, 'nod', d * 0.45)
        poses(b, [(t - 0.2, B.P('strict', head=(0, 0, 0))), (t + 0.25, B.P('strict', head=(0, 14, 0))),
                  (t + 0.75, B.P('strict', head=(0, 2, 0)))])
    # soft key from the side (shape on the round face), cool rim behind; the face must not burn out
    lib.light('AREA', (1.0, -1.0, 1.85), energy=60, size=1.4, color='#FFE3C4')
    lib.light('AREA', (-0.9, 0.8, 1.8), energy=70, size=0.8, color='#D6E0FF')
    for o in bpy.data.objects:
        if o.type == 'LIGHT' and o.data.type == 'AREA':
            lib.look_at(o, (0, 0, 1.5))
    cam(shot, (0.18, -1.3, 1.55), (0.12, -1.0, 1.55), (0, 0, 1.5), (0, 0, 1.51), lens=70, dof=(0, -0.08, 1.52),
        fstop=2.2)
    return dict(fill=0.12, exposure=-0.15)


def s_surrender(shot):
    sky('gold')
    lib.plane((400, 400), (0, 0, -0.01), P.M('Meadow', '#8A9A55', rough=0.9, var=0.3, bump=0.3, vs=0.2))
    doors, towers = _castle((0, 18, 0))
    t = ev(shot, 'give', 0.4)
    P.flag((towers[0][0], towers[0][1] - 2.3, 9.0), size=(3.0, 2.0), stripes=('#FAF8F4',), pole=5.5, name='WhiteFlag',
           t_up=(t, t + 1.4), up=(0.05, 1))
    for i, hg in enumerate(doors):
        s = -1 if i == 0 else 1
        lib.key_obj(hg, F(0), rot=(0, 0, 0))
        lib.key_obj(hg, F(t + 0.6), rot=(0, 0, 0))
        lib.key_obj(hg, F(t + 2.2), rot=(0, 0, s * math.radians(-80)))
    fog(0.006, '#EED9BD', size=(300, 300, 60), z=25)
    cam(shot, (-7, -14, 4.5), (-5, -12, 5.0), (-4, 14, 8), (-4, 14, 9), lens=40)
    return dict(fill=0.35, exposure=0.25)


def _fortress(loc=(0, 20, 0), banner=True):
    """Fortress «Эрмес»: walls and towers stacked from huge orange gift boxes with brown ribbons."""
    x0, y0, z0 = loc
    rnd = random.Random(44)
    for k in range(9):                      # the front wall: two layers of boxes
        for layer in range(2):
            s = rnd.uniform(2.6, 3.2)
            P.gift_box((s, 3.0, 2.6), (x0 - 12 + k * 3.0, y0, z0 + layer * 2.6), bow=layer == 1, name='WallBox')
    for sx in (-1, 1):                      # towers: three boxes high, a bow on top
        for layer in range(4):
            P.gift_box((4.2, 4.2, 3.0), (x0 + sx * 14, y0, z0 + layer * 3.0), bow=layer == 3, name='TowerBox')
    P.gift_box((6, 6, 3.5), (x0, y0 + 8, z0), bow=False, name='KeepBox')
    P.gift_box((5, 5, 3.5), (x0, y0 + 8, z0 + 3.5), bow=False, name='KeepBox')
    P.gift_box((4, 4, 3.5), (x0, y0 + 8, z0 + 7.0), bow=True, name='KeepBox')
    if banner:
        P.text('ЭРМЕС', 1.1, (x0, y0 - 1.62, z0 + 3.4), m=P.M('BrownInk', '#4A2A14', rough=0.6), font=P.SERIF,
               extrude=0.02)
        P.flag((x0, y0 + 8, z0 + 10.6), size=(3.2, 2.0), stripes=('#E8701E', '#F3EEE4', '#6B4226'), pole=4.0,
               name='FortFlag')


def s_fortress(shot):
    sky('dusk')
    lib.plane((500, 500), (0, 0, -0.01), P.M('Plain', '#A79B72', rough=0.9, var=0.3, bump=0.3, vs=0.2), name='Plain')
    _fortress()
    rnd = random.Random(5)
    for k in range(25):                    # the besiegers' tents far off: striped sale tents
        x = rnd.uniform(-60, 60)
        y = rnd.uniform(-40, -15)
        lib.cyl(1.8, 2.4, (x, y, 1.2), P.cloth('#E9E1D2' if k % 2 else '#C8402F', 'Tent' + str(k % 2)), r2=0.05,
                verts=12, name='Tent')
    fog(0.008, '#E5B993', size=(300, 300, 60), z=25)
    cam(shot, (-18, -22, 4), (-12, -20, 8), (0, 20, 4), (0, 20, 6), lens=40)
    return dict(fill=0.35, exposure=0.3)


def s_calendar(shot):
    sky('interior')
    lib.world_color('#E8C39A', 0.6)
    # the inside of the fortress: an orange cardboard wall with a brown ribbon off to the side
    lib.box((4, 1, 3.2), (0, 0.6, 1.6), P.M('Orange#E8701E', '#E8701E', rough=0.55, var=0.05, bump=0.06), bevel=0.02,
            name='WallBox')
    lib.box((0.3, 1.05, 3.2), (-1.1, 0.6, 1.6), P.M('Ribbon#5B3A1E', '#5B3A1E', rough=0.35, coat=0.4), bevel=0,
            name='Ribbon')
    pm = P.paper('#F4EEE2', 'CalPage')
    ink = P.M('CalInk', '#2A1C14', rough=0.7)
    red = P.M('CalRed', '#B8322A', rough=0.7)
    lib.box((0.5, 0.02, 0.12), (0, 0.08, 2.1), red, bevel=0.005, name='CalHeader')
    P.text('ОСАДА', 0.06, (0, 0.065, 2.1), m=P.M('White', '#F4EEE2'), font=P.SANS, extrude=0.001)
    d = shot['dur']
    n = 40
    for i in range(1, n + 1):          # pages 1..40; each flips up and away in turn
        hinge = lib.empty('PageHinge', loc=(0, 0.09 - i * 0.0004, 2.04))
        pg = lib.box((0.48, 0.002, 0.56), (0, 0, -0.28), pm, bevel=0, name='Page')
        pg.parent = hinge
        num = P.text(str(n - i + 1), 0.24, (0, -0.002, -0.3), rot=(math.radians(90), 0, 0),
                     m=red if (n - i + 1) % 7 == 0 else ink, font=P.SERIF, extrude=0.0005)
        num.parent = hinge
        lab = P.text('ДЕНЬ', 0.05, (0, -0.002, -0.08), m=ink, font=P.SANS, extrude=0.0003)
        lab.parent = hinge
        k = n - i                       # page "1" is on top and flips first
        t = 0.25 + (d - 0.9) * (k / (n - 1)) ** 1.6
        if i == 1:
            continue
        lib.key_obj(hinge, F(0), rot=(0, 0, 0))
        lib.key_obj(hinge, F(t), rot=(0, 0, 0))
        lib.key_obj(hinge, F(t + 0.12), rot=(math.radians(-170), 0, 0))
    lib.light('AREA', (0.8, -1.2, 2.6), energy=90, size=1.0, color='#FFE0B8')
    lib.light('AREA', (-0.9, -0.8, 2.0), energy=40, size=1.0, color='#D6E0FF')
    for o in bpy.data.objects:
        if o.type == 'LIGHT':
            lib.look_at(o, (0, 0, 1.8))
    cam(shot, (0.15, -1.25, 1.85), (0.05, -1.0, 1.82), (0, 0.08, 1.8), lens=55, dof=(0, 0.08, 1.8), fstop=4)
    return dict(fill=0.3, exposure=0.2)


def s_balloon(shot):
    sky('dusk')
    lib.plane((500, 500), (0, 0, -0.01), P.M('Plain', '#A79B72', rough=0.9, var=0.3, bump=0.3, vs=0.2))
    _fortress((0, 30, 0))
    bl = lib.empty('Balloon', loc=(-30, 0, 18))
    env = lib.sphere(5, (0, 0, 6), P.cloth('#C8202A', 'BalloonRed'), scale=(1, 1, 1.2), segs=48, rings=24,
                     name='Envelope')
    env.parent = bl
    band = lib.cyl(5.05, 2.2, (0, 0, 5.4), P.cloth('#F6F1E8', 'BalloonBand'), verts=48, name='Band')
    band.parent = bl
    tx = P.text('−50%', 1.5, (0, -5.1, 5.1), m=P.M('PosterRed', '#C8202A', rough=0.6), font=P.SANS, extrude=0.05)
    tx.parent = bl
    bas = lib.box((1.6, 1.6, 1.2), (0, 0, -0.6), P.M('Wicker', '#8A6A3A', rough=0.9, var=0.3, bump=0.8, bs=60),
                  bevel=0.1, name='Basket')
    bas.parent = bl
    for sx in (-1, 1):
        for sy in (-1, 1):
            r = P.tube([(sx * 0.7, sy * 0.7, 0), (sx * 2.8, sy * 2.8, 2.6)], 0.02, P.M('RopeTan', '#8C7B5E'), 'BRope')
            r.parent = bl
    lib.key_obj(bl, F(0), loc=(-22, 2, 14))
    lib.key_obj(bl, F(shot['dur']), loc=(-8, 10, 15.5))
    fog(0.008, '#E5B993', size=(300, 300, 60), z=25)
    cam(shot, (6, -24, 5), (4, -22, 7), (-12, 10, 12), (-6, 14, 13), lens=44)
    return dict(fill=0.35, exposure=0.3)


def s_wall(shot):
    sky('dusk')
    lib.plane((500, 500), (0, 0, -6), P.M('Plain', '#A79B72', rough=0.9, var=0.3, bump=0.3, vs=0.2))
    _fortress((0, 0.8, -5.2), banner=False)          # she stands on the top of the wall boxes
    b = baroness((0, 0.2, 0), 0.0, 'strict')
    poses(b, [(shot['dur'], B.P('strict', head=(-6, -6, 0)))])
    P.flag((1.4, 0.6, 0), size=(1.6, 1.0), stripes=('#E8701E', '#F3EEE4', '#6B4226'), pole=2.6, name='WallFlag', amp=0.1)
    lib.light('AREA', (1.5, -2.0, 2.5), energy=260, size=1.5, color='#FFD3A8')
    lib.light('AREA', (-1.5, 2.0, 2.2), energy=220, size=1.5, color='#BFD0FF')
    for o in bpy.data.objects:
        if o.type == 'LIGHT' and o.data.type == 'AREA':
            lib.look_at(o, (0, 0, 1.3))
    fog(0.008, '#E5B993', size=(300, 300, 60), z=25)
    cam(shot, (0.6, -3.4, 0.9), (0.4, -2.6, 1.0), (0, 0, 1.35), (0, 0, 1.45), lens=44, dof=(0, 0.1, 1.4), fstop=3.2)
    return dict(fill=0.3, exposure=0.25)


def s_list(shot):
    sky('dusk')
    _fortress((0, 1.5, -5.2), banner=False)
    lib.plane((500, 500), (0, 0, -5.21), P.M('Plain', '#A79B72', rough=0.9, var=0.3, bump=0.3, vs=0.2))
    pm = P.paper('#F1E6CC', 'Scroll')
    ink = P.M('Ink', '#3A2414', rough=0.7)
    roll = lib.empty('ScrollTop', loc=(0, -0.05, 0.4))
    lib.cyl(0.07, 1.4, (0, 0, 0), P.wood('#5A3620', 'ScrollRod'), rot=(0, math.radians(90), 0), name='Rod').parent = roll
    sheet = lib.empty('Sheet', loc=(0, -0.08, 0.4))
    pg = lib.box((1.2, 0.004, 1.0), (0, 0, -0.5), pm, bevel=0, name='Paper')
    pg.parent = sheet
    lines = [P.text('ЛИСТ ОЖИДАНИЯ', 0.075, (0, -0.004, -0.1), m=ink, font=P.SERIF, extrude=0.0005)]
    for k in range(18):
        lines.append(lib.box((0.9 - 0.25 * ((k * 7) % 3) / 2, 0.001, 0.012), (-0.02, -0.004, -0.22 - k * 0.04), ink,
                             bevel=0, name='Line'))
    for o in lines:
        o.parent = sheet
    t = ev(shot, 'unroll', 0.3)
    # unrolls downward: the sheet grows from 0 to 5 m long (scale in z), the lines with it
    lib.key_obj(sheet, F(0), scale=(1, 1, 0.02))
    lib.key_obj(sheet, F(t), scale=(1, 1, 0.02))
    lib.key_obj(sheet, F(t + 1.6), scale=(1, 1, 5.0))
    lib.light('AREA', (1.2, -2.0, 1.0), energy=220, size=1.5, color='#FFD3A8')
    for o in bpy.data.objects:
        if o.type == 'LIGHT' and o.data.type == 'AREA':
            lib.look_at(o, (0, 0, -1))
    fog(0.008, '#E5B993', size=(300, 300, 60), z=25)
    cam(shot, (0.4, -3.2, 0.6), (0.3, -3.6, -0.8), (0, 0, 0.0), (0, 0, -1.4), lens=40, dof=(0, -0.1, -0.5), fstop=5)
    return dict(fill=0.35, exposure=0.3)


def _ermesovka(rnd, garlands=True, lit=0.2):
    P.cobbles((40, 120), (0, 30, 0), col='#8C8174')
    _town(rnd, lit=lit, start=-8, rows=((-1, 7), (1, 7)), lamps=True)
    # the 1940s (mike 28.10: «добавь про 40-ые годы»): poster columns and an olive lorry loaded with orange boxes
    P.ad_column((-3.0, 12.0, 0), name='AdColA', seed=0)
    P.ad_column((3.2, 26.0, 0), name='AdColB', seed=2)
    P.truck40((3.0, 18.0, 0), heading=math.radians(180), name='Lorry')
    for k in range(3):
        P.gift_box((0.7, 0.7, 0.5), (3.0 + (k - 1) * 0.75, 18.6, 1.0), bow=k == 1, name='LorryBox')
    if garlands:                        # bunting across the street: orange, white, brown flags
        cols = [P.cloth('#E8701E', 'BuntO'), P.cloth('#F3EEE4', 'BuntW'), P.cloth('#6B4226', 'BuntB')]
        for k in range(6):
            y = -2 + k * 8
            pts = [(-9 + 18 * u / 10, y, 7.2 - 1.3 * math.sin(math.pi * u / 10)) for u in range(11)]
            P.tube(pts, 0.012, P.M('String', '#D8D0C2'), 'Bunting')
            for j in range(20):
                u = j / 19
                x = -9 + 18 * u
                z = 7.2 - 1.3 * math.sin(math.pi * u) - 0.25
                tri = lib.poly_prism([(-0.22, 0), (0.22, 0), (0, -0.45)], 0.01, (x, y, z + 0.22), cols[j % 3],
                                     rot=(math.radians(90), 0, 0), name='Pennant')
        # banners «ВЕЛИКАЯ РАСПРОДАЖА» across the street
        for y in (6, 22):
            lib.box((10, 0.05, 1.1), (0, y, 5.2), P.cloth('#F3EEE4', 'BannerCloth'), bevel=0, name='Banner')
            P.text('ВЕЛИКАЯ РАСПРОДАЖА', 0.55, (0, y - 0.04, 5.2), m=P.M('BannerInk', '#C24E16', rough=0.7),
                   font=P.SERIF, extrude=0.002)


def s_salecity(shot):
    rnd = random.Random(21)
    sky('gold')
    _ermesovka(rnd)
    P.drifting_paper(220, (-8, -6, 0.5), (8, 26, 9), 0, shot['dur'], seed=12, fall=0.5)
    fog(0.006, '#EED9BD')
    cam(shot, (0, -12, 2.0), (0.8, -8, 3.4), (0, 14, 5), (0, 16, 5.6), lens=40)
    return dict(fill=0.35, exposure=0.3)


def s_enter(shot):
    rnd = random.Random(22)
    sky('gold')
    _ermesovka(rnd)
    b = B.load(loc=(0, 8, 0), heading=math.pi, name='Baroness')     # walks toward the camera (-Y)
    d = shot['dur']
    SH.walk(b, 0.0, d, [(0, 8), (0, 8 - 0.85 * d)], speed=0.85, A=15.0, base=B.P('stand'))
    g = P.coupon_gun((1.3, 6.5, 0.6), rot=math.pi, name='Gun', carriage=True)    # rolled along beside her
    lib.key_obj(g, F(0), loc=(1.3, 8.5, 0.6), interp='LINEAR')
    lib.key_obj(g, F(d), loc=(1.3, 8.5 - 0.85 * d, 0.6), interp='LINEAR')
    P.drifting_paper(120, (-6, -4, 0.5), (6, 14, 7), 0, d, seed=13, fall=0.45)
    fog(0.006, '#EED9BD')
    # the camera backs away in front of her at her speed: she stays a medium-full figure in the street
    cam(shot, (-0.7, 4.6, 1.35), (-0.7, 4.6 - 0.85 * d, 1.35), (0, 8, 1.25), (0, 8 - 0.85 * d, 1.25), lens=44,
        dof=(0, 8 - 0.85 * d * 0.5, 1.3), fstop=4)
    return dict(fill=0.3, exposure=0.25)


def s_keys(shot):
    sky('interior')
    lib.world_color('#3A2D24', 0.45)
    lib.plane((4, 4), (0, 0, 0), P.cloth('#5C1622', 'VelvetCloth'), name='Velvet')
    g, wd = P.gold(), P.wood('#3F2717', 'Register')
    # a big gold key on a pillow
    pil = lib.sphere(0.22, (-0.42, 0.05, 0.04), P.M('Satin', '#C9A76A', rough=0.3, coat=0.5), scale=(1.0, 0.75, 0.25),
                     name='Pillow')
    key = lib.empty('Key', loc=(-0.42, 0.05, 0.1))
    lib.cyl(0.018, 0.36, (0, 0, 0), g, rot=(0, math.radians(90), 0), name='KeyShaft').parent = key
    lib.cyl(0.07, 0.025, (-0.2, 0, 0), g, rot=(math.radians(90), 0, 0), name='KeyBow').parent = key
    lib.box((0.05, 0.02, 0.07), (0.15, 0, -0.03), g, bevel=0.004, name='KeyBit').parent = key
    # a vintage cash register
    reg = lib.empty('Register', loc=(0.05, 0.25, 0))
    lib.box((0.36, 0.32, 0.22), (0, 0, 0.11), P.brass(), bevel=0.02, name='RegBody').parent = reg
    lib.box((0.36, 0.2, 0.14), (0, 0.06, 0.29), P.brass(), bevel=0.02, name='RegTop').parent = reg
    lib.box((0.2, 0.02, 0.07), (0, -0.04, 0.38), lib.mat('RegDisp', '#F4EEE2', emit='#FFF2D8', emit_strength=0.6),
            bevel=0, name='RegDisplay').parent = reg
    for i in range(4):
        for j in range(3):
            lib.cyl(0.012, 0.03, (-0.12 + i * 0.08, -0.12 + j * 0.05, 0.24), P.M('KeyCap', '#F2ECE0', rough=0.4),
                    name='RegKey').parent = reg
    P.radio40((-0.05, 0.62, 0.0), rot_z=math.radians(-8), name='Radio')        # the 1940s on the table
    # a pile of dust bags
    bags =[P.dust_bag((0.5 + dx, 0.1 + dy, dz), w=0.24, h=0.28, flat=0.4, seed=s, name='PileBag')
            for s, (dx, dy, dz) in enumerate(((0, 0, 0), (0.15, 0.1, 0), (-0.05, 0.18, 0.0), (0.06, 0.08, 0.12)))]
    for obj, k in ((key, 'keys'), (reg, 'cash')):
        t = ev(shot, k, 0.5)
        lib.key_obj(obj, F(0), scale=(0.001,) * 3)
        lib.key_obj(obj, F(t - 0.05), scale=(0.001,) * 3)
        lib.key_obj(obj, F(t + 0.2), scale=(1.08,) * 3)
        lib.key_obj(obj, F(t + 0.32), scale=(1,) * 3)
    t = ev(shot, 'bags', 2.0)
    for i, bg in enumerate(bags):           # the bags drop one after another
        z = bg.location.z
        lib.key_obj(bg, F(0), loc=(bg.location.x, bg.location.y, 1.5))
        lib.key_obj(bg, F(t - 0.1 + i * 0.12), loc=(bg.location.x, bg.location.y, 1.5))
        lib.key_obj(bg, F(t + 0.25 + i * 0.12), loc=(bg.location.x, bg.location.y, z))
    sp = lib.light('SPOT', (0.0, -0.8, 1.8), energy=500, spot=50, blend=0.6, size=0.5, color='#FFE1B8')
    lib.look_at(sp, (0.05, 0.1, 0.1))
    lib.light('AREA', (-1.0, 1.0, 0.8), energy=40, size=1, color='#C9D6FF')
    cam(shot, (0.05, -1.75, 0.85), (0.05, -1.45, 0.7), (0.05, 0.12, 0.15), lens=40, dof=(0.05, 0.15, 0.15), fstop=6)
    return dict(fill=0.2, exposure=0.25)


def s_townhall(shot, close=False):
    rnd = random.Random(24)
    sky('gold')
    P.cobbles((60, 60), (0, 0, 0), col='#8C8174')
    st = P.M('HallStone', '#D9C7A8', rough=0.8, var=0.1, bump=0.25, bs=10)
    lib.box((16, 8, 10), (0, 14, 5), st, bevel=0.1, name='TownHall')
    lib.box((5, 5, 12), (0, 14, 16), st, bevel=0.08, name='HallTower')
    lib.cyl(3.6, 5, (0, 14, 24.5), P.M('Copper', '#5E8F7E', rough=0.6, metal=0.4, var=0.2), r2=0.1, verts=4,
            rot=(0, 0, math.radians(45)), name='Spire')
    clock = lib.cyl(1.3, 0.2, (0, 11.4, 18.5), P.M('ClockFace', '#F2ECDF', rough=0.5), rot=(math.radians(90), 0, 0),
                    name='Clock')
    for k in range(10):
        lib.box((1.2, 0.2, 2.4), (-6.5 + k * 1.45, 9.9, 4.0), lib.mat('HallWin', '#2E3438', rough=0.05), bevel=0,
                name='HWin')
        lib.box((1.2, 0.2, 2.4), (-6.5 + k * 1.45, 9.9, 7.6), lib.mat('HallWin', '#2E3438', rough=0.05), bevel=0,
                name='HWin')
    t = ev(shot, 'raise', 0.4)
    if close:
        P.flag((0, 14, 26.8), size=(3.0, 2.0), stripes=('#E8701E', '#F3EEE4', '#6B4226'), pole=4.5, name='HallFlag',
               amp=0.12)
        cam(shot, (-1.8, 7.2, 29.4), (-1.2, 7.8, 30.0), (1.4, 14, 29.9), (1.6, 14, 30.2), lens=44)
    else:
        cl, pole, knob = P.flag((0, 14, 27), size=(3.0, 2.0), stripes=('#E8701E', '#F3EEE4', '#6B4226'), pole=4.5,
                                name='HallFlag', t_up=(t, t + 1.8), up=(0.05, 1))
        for k in range(8):                     # the square: lamps and a few market stalls
            P.street_lamp((-12 + k * 3.4, -2, 0), lit=False)
        cam(shot, (-6, -16, 3), (-5, -13, 5), (0, 14, 18), (0, 14, 24), lens=40)
    fog(0.005, '#EED9BD')
    return dict(fill=0.35, exposure=0.25)


def _palace(loc=(0, 0, 0), s=1.0):
    """The President's palace of Birkinstadt, shaped like a giant handbag: a trapezoid hall in orange stone, a gilded
    arch for the handle, a flap with a lock-shaped balcony."""
    x0, y0, z0 = loc
    st = P.M('PalaceStone', '#D9894A', rough=0.6, var=0.1, bump=0.2, bs=8)
    import bmesh
    w, d, h, tw = 40 * s, 22 * s, 24 * s, 33 * s
    bm = bmesh.new()
    pts = [(-w / 2, -d / 2, 0), (w / 2, -d / 2, 0), (w / 2, d / 2, 0), (-w / 2, d / 2, 0),
           (-tw / 2, -d / 2 * 0.9, h), (tw / 2, -d / 2 * 0.9, h), (tw / 2, d / 2 * 0.9, h), (-tw / 2, d / 2 * 0.9, h)]
    vs = [bm.verts.new(p) for p in pts]
    for f in ((0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)):
        bm.faces.new([vs[i] for i in f])
    body = lib.mesh_from_bm(bm, 'Palace', st, loc=loc)
    lib.add_bevel(body, 0.8 * s, segs=4)
    flap = lib.box((tw * 1.02, 0.6 * s, h * 0.42), (x0, y0 - d / 2 * 0.9 - 0.4 * s, z0 + h * 0.79),
                   P.M('PalaceFlap', '#B96A32', rough=0.55, var=0.08), bevel=0.3 * s, name='Flap')
    g = P.gold()
    lock = lib.box((3.6 * s, 1.2 * s, 2.6 * s), (x0, y0 - d / 2 * 0.9 - 1.0 * s, z0 + h * 0.6), g, bevel=0.3 * s,
                   name='LockBalcony')
    pts_h = [(x0 - tw * 0.3 + tw * 0.6 * k / 16, y0, z0 + h + 0.5 + 16 * s * math.sin(math.pi * k / 16))
             for k in range(17)]
    P.tube(pts_h, 1.0 * s, g, 'Handle')
    gl = lib.mat('PalaceGlass', '#3A4C5A', rough=0.05)
    for row in range(3):
        for k in range(9):
            x = x0 - 16 * s + k * 4 * s
            lib.box((1.6 * s, 0.4 * s, 3.2 * s), (x, y0 - d / 2 - 0.1 * s + row * 0.0, z0 + 3 + row * 4.6 * s), gl,
                    bevel=0, name='PWin')
    lib.box((8 * s, 1.0 * s, 6 * s), (x0, y0 - d / 2 - 0.4 * s, z0 + 3 * s), P.wood('#3F2717', 'PalaceDoor'),
            bevel=0.2, name='PalaceDoor')
    P.flag((x0, y0, z0 + h + 17 * s), size=(4 * s, 2.6 * s), stripes=('#E8701E', '#F3EEE4', '#6B4226'), pole=5 * s,
           name='PalaceFlag')
    return body


def s_capital(shot):
    rnd = random.Random(26)
    sky('gold')
    lib.plane((800, 800), (0, 0, -0.01), P.M('Land', '#8B925E', rough=0.9, var=0.3, bump=0.2, vs=0.05), name='Land')
    lib.plane((30, 800), (-90, 0, 0.02), lib.mat('River', '#5D7F8F', rough=0.05, spec=0.8), name='River')
    _palace((0, 0, 0))
    lib.plane((70, 70), (0, 0, 0.01), P.cobbles((1, 1), (0, 0, -5)).active_material, name='Square')
    for i in range(-5, 6):                 # city blocks around the square
        for j in range(-5, 6):
            if abs(i) < 2 and abs(j) < 2:
                continue
            x, y = i * 24, j * 24
            for k in range(4):
                hh = rnd.uniform(9, 18)
                lib.box((9, 9, hh), (x + (k % 2) * 10 - 5, y + (k // 2) * 10 - 5, hh / 2),
                        P.M('Block' + str(rnd.randrange(5)), P.WALLS[rnd.randrange(len(P.WALLS))], rough=0.85,
                            var=0.12, bump=0.2), bevel=0.2, name='Block')
                lib.box((9.4, 9.4, 0.8), (x + (k % 2) * 10 - 5, y + (k // 2) * 10 - 5, hh + 0.4),
                        P.M('Roof#6E4A3A', '#6E4A3A', rough=0.7, var=0.12), bevel=0.1, name='BlockRoof')
    fog(0.004, '#EED9BD', size=(800, 800, 120), z=50)
    cam(shot, (-90, -150, 70), (-60, -120, 55), (0, 0, 10), (0, 0, 12), lens=40)
    return dict(fill=0.35, exposure=0.25)


def s_palace(shot):
    sky('gold')
    lib.plane((800, 800), (0, 0, -0.01), P.M('Land', '#8B925E', rough=0.9, var=0.3, bump=0.2, vs=0.05))
    P.cobbles((90, 90), (0, -20, 0.005), col='#9A8F80')
    _palace((0, 10, 0))
    # a fountain with a gilded handbag on top
    lib.cyl(5, 0.8, (0, -22, 0.4), P.marble(), verts=48, name='Fountain')
    lib.cyl(4.6, 0.1, (0, -22, 0.75), lib.mat('Water', '#7FA6B5', rough=0.02, spec=0.9), verts=48, name='Water')
    lib.cyl(0.6, 3, (0, -22, 2.3), P.marble(), verts=24, name='FountainPost')
    P.handbag((0, -22, 3.8), w=1.6, h=1.2, d=0.8, col='#C99A3E', name='GoldBag')
    for k in range(12):
        a = k * math.pi / 6
        P.street_lamp((9 * math.cos(a), -22 + 9 * math.sin(a), 0), lit=False)
    fog(0.004, '#EED9BD', size=(400, 400, 80), z=30)
    cam(shot, (-14, -52, 4), (-6, -46, 7), (0, 0, 14), (0, 4, 16), lens=40)
    return dict(fill=0.35, exposure=0.25)


def s_shrine(shot):
    sky('interior')
    lib.world_color('#2E2620', 0.4)
    lib.plane((20, 30), (0, 6, 0), P.marble('#E8E0D2', '#8C8478', 'ShrineMarble'), name='Floor')
    for sx in (-1, 1):
        for k in range(5):
            lib.cyl(0.5, 9, (sx * 4, k * 3.2 - 2, 4.5), P.marble('#F0EBE2', '#B5ACA0', 'ColMarble'), verts=40,
                    name='Column')
    lib.box((20, 0.3, 10), (0, 14, 5), P.M('ShrineWall', '#6E5A47', rough=0.8, var=0.1), bevel=0, name='Back')
    # three steps and a pedestal, the Holy Handbag under a glass dome
    for k in range(3):
        lib.box((5 - k * 1.2, 4 - k * 0.9, 0.25), (0, 8, 0.125 + k * 0.25), P.marble(), bevel=0.02, name='Step')
    lib.cyl(0.8, 1.4, (0, 8, 1.45), P.marble('#F0EBE2', '#B5ACA0', 'ColMarble'), verts=40, name='Pedestal')
    P.handbag((0, 8, 2.15), w=0.7, h=0.52, d=0.32, col='#E07A2E', name='HolyBag')
    lib.sphere(0.85, (0, 8, 2.15), lib.mat('Dome', '#DDE6EA', rough=0.02, alpha=0.15), segs=48, rings=24,
               name='Dome').scale = (1, 1, 0.9)
    sp = lib.light('SPOT', (0, 6.5, 9), energy=4000, spot=18, blend=0.4, size=0.3, color='#FFE2B0')
    lib.look_at(sp, (0, 8, 2.2))
    for sx in (-1, 1):
        lib.light('POINT', (sx * 2.4, 7, 1.2), energy=60, color='#FFB86A')
        lib.cyl(0.05, 0.9, (sx * 2.4, 7, 0.45), P.gold(), name='Candle')
    lib.fog_box(size=(18, 26, 12), loc=(0, 6, 6), density=0.05, color='#C7B49A')
    t = ev(shot, 'reveal', 0.5)
    sp.data.energy = 0
    sp.data.keyframe_insert('energy', frame=F(max(0, t - 0.3)))
    sp.data.energy = 4000
    sp.data.keyframe_insert('energy', frame=F(t + 0.4))
    cam(shot, (0.0, -3.5, 1.5), (0.0, 1.8, 1.9), (0, 8, 1.9), (0, 8, 2.1), lens=40, dof=(0, 8, 2.1), fstop=4)
    return dict(fill=0.15, exposure=0.3)


def s_motto(shot):
    sky('interior')
    lib.world_color('#D9C2A0', 0.6)
    mm = P.marble('#EFE9DF', '#A69C8E', 'FriezeMarble')
    lib.box((9, 0.6, 2.4), (0, 0.3, 2.5), mm, bevel=0.03, name='Frieze')
    lib.box((9.4, 0.8, 0.25), (0, 0.3, 3.8), mm, bevel=0.03, name='Cornice')
    lib.box((9.4, 0.8, 0.25), (0, 0.3, 1.2), mm, bevel=0.03, name='Base')
    txt = P.text('БЕРЕГИ ПЫЛЬНИК СМОЛОДУ', 0.36, (0, -0.0, 2.55), m=P.M('Gilt', '#B88A3A', rough=0.3, metal=1.0),
                 font=P.SERIF, extrude=0.012)
    # gilt letters are cut into the stone: they appear left to right (a reveal plane slides away)
    cover = lib.box((9.2, 0.05, 0.6), (0, -0.03, 2.55), mm, bevel=0, name='Cover')
    t = ev(shot, 'motto', 0.3)
    lib.key_obj(cover, F(0), loc=(0, -0.03, 2.55))
    lib.key_obj(cover, F(t), loc=(0, -0.03, 2.55))
    lib.key_obj(cover, F(t + 1.6), loc=(9.4, -0.03, 2.55))
    cover.scale = (1, 1, 1)
    lib.light('AREA', (2.5, -2.5, 4.5), energy=420, size=2.5, color='#FFE2C0')
    lib.light('AREA', (-3, -2, 1.5), energy=120, size=2.0, color='#D6E0FF')
    for o in bpy.data.objects:
        if o.type == 'LIGHT':
            lib.look_at(o, (0, 0, 2.5))
    cam(shot, (-2.4, -3.2, 2.3), (2.4, -3.0, 2.5), (-1.2, 0, 2.55), (1.4, 0, 2.55), lens=44, dof=(0, 0, 2.55),
        fstop=5)
    return dict(fill=0.3, exposure=0.2)


def _passport(loc=(0, 0, 0), name='Passport'):
    lm = P.leather('#5A2E16', 'PassCover')
    g = P.gold()
    e = lib.empty(name, loc=loc)
    lib.box((0.125, 0.088, 0.008), (0, 0, 0.004), lm, bevel=0.003, name=name + 'Cover').parent = e
    lib.box((0.12, 0.084, 0.006), (0.001, 0, 0.004), P.paper('#EFE6D2', 'PassPages'), bevel=0.001,
            name=name + 'Pages').parent = e
    for body, z, sz in (('РЕСПУБЛИКА', 0.03, 0.009), ('БИРКИН', 0.018, 0.012), ('ПАСПОРТ', -0.032, 0.01)):
        tx = P.text(body, sz, (0, z, 0.0085), rot=(0, 0, 0), m=g, font=P.SERIF, extrude=0.0003)
        tx.parent = e
    # the emblem: a tiny gold handbag under a laurel ring
    hb = P.handbag((0, -0.02, 0.0085), w=0.022, h=0.016, d=0.003, col='#C99A3E', name=name + 'Emblem', lock=False)
    hb.parent = e
    hb.location = (0, -0.02, 0.0085)
    hb.rotation_euler = (math.radians(-90), 0, 0)         # lying flat on the cover, front up, top towards +Y
    ring = bpy.data.objects.new('Laurel', bpy.data.meshes.new('Laurel'))
    import bmesh
    bm = bmesh.new()
    bmesh.ops.create_circle(bm, segments=48, radius=0.017)
    bm.to_mesh(ring.data)
    bpy.context.scene.collection.objects.link(ring)
    ring.location = (0, -0.006, 0.0088)
    sk = ring.modifiers.new('Skin', 'SKIN')
    for v in ring.data.skin_vertices[0].data:
        v.radius = (0.0007, 0.0007)
    ring.data.materials.append(g)
    ring.parent = e
    return e


def s_passport(shot):
    sky('interior')
    lib.world_color('#3B3029', 0.45)
    lib.plane((2, 2), (0, 0, 0), P.wood('#4A2E1A', 'Desk'), name='Desk')
    ps = _passport((0, 0, 0.001))
    ps.rotation_euler.z = math.radians(8)
    stamp = lib.cyl(0.02, 0.05, (0.12, 0.06, 0.025), P.wood('#3A2516', 'StampWood'), name='Stamp')
    lib.cyl(0.024, 0.012, (0.12, 0.06, 0.006), P.M('StampInk', '#7A1424', rough=0.7), name='StampFoot')
    pen = lib.cyl(0.006, 0.15, (-0.11, -0.05, 0.006), P.M('PenBlack', '#141414', rough=0.3, coat=0.6),
                  rot=(0, math.radians(90), math.radians(30)), name='Pen')
    lib.light('AREA', (0.25, -0.3, 0.5), energy=20, size=0.4, color='#FFE2C0')
    lib.light('AREA', (-0.3, 0.3, 0.3), energy=8, size=0.4, color='#D6E0FF')
    for o in bpy.data.objects:
        if o.type == 'LIGHT':
            lib.look_at(o, (0, 0, 0))
    cam(shot, (0.05, -0.26, 0.22), (0.02, -0.17, 0.17), (0, 0, 0.005), lens=55, dof=(0, 0, 0.008), fstop=3.5)
    return dict(fill=0.25, exposure=0.15)


def s_passbag(shot):
    sky('interior')
    lib.world_color('#3B3029', 0.45)
    lib.plane((2, 2), (0, 0, 0), P.wood('#4A2E1A', 'Desk'), name='Desk')
    db = P.dust_bag((0.04, 0.02, 0.0), w=0.2, h=0.17, flat=0.18, name='TinyBag')
    db.rotation_euler = (math.radians(-90), 0, math.radians(90))
    db.location = (0.06, 0.0, 0.035)
    ps = _passport((-0.12, 0, 0.001))
    t = ev(shot, 'in', 0.6)
    lib.key_obj(ps, F(0), loc=(-0.14, 0, 0.002))
    lib.key_obj(ps, F(t), loc=(-0.14, 0, 0.002))
    lib.key_obj(ps, F(t + 0.9), loc=(0.07, 0, 0.02))
    lib.light('AREA', (0.25, -0.3, 0.5), energy=20, size=0.4, color='#FFE2C0')
    lib.light('AREA', (-0.3, 0.3, 0.3), energy=8, size=0.4, color='#D6E0FF')
    for o in bpy.data.objects:
        if o.type == 'LIGHT':
            lib.look_at(o, (0, 0, 0))
    cam(shot, (-0.05, -0.33, 0.2), (-0.02, -0.28, 0.17), (0, 0, 0.02), lens=50, dof=(0, 0, 0.02), fstop=4)
    return dict(fill=0.25, exposure=0.15)


def s_swamp(shot):
    sky('morning')
    lib.plane((300, 300), (0, 0, -0.02), lib.mat('Water', '#6F8A86', rough=0.04, spec=0.8), name='Water')
    bank = P.M('Bank', '#6E6A45', rough=0.95, var=0.3, bump=0.5, vs=0.6)
    lib.sphere(10, (0, -8, -9.4), bank, scale=(2.5, 1, 1), name='Bank')
    rnd = random.Random(32)
    reed = P.M('Reed', '#8E8A4E', rough=0.9, var=0.3)
    for k in range(260):
        x = rnd.uniform(-12, 12)
        y = rnd.uniform(-6, 2)
        h = rnd.uniform(0.8, 1.8)
        r = lib.cyl(0.012, h, (x, y, h / 2 - 0.1), reed, verts=6, rot=(rnd.uniform(-0.15, 0.15), rnd.uniform(-0.15, 0.15),
                                                                         0), name='Reed')
        r.visible_shadow = False
    # the signpost «БИРКИН 2 км»
    post = lib.cyl(0.06, 2.0, (0.8, -3.2, 1.0), P.wood('#5A4632', 'OldWood'), name='SignPost')
    P.sign('БИРКИН 2 км', (1.45, -3.25, 1.75), size=0.13, board=(1.2, 0.26), col='#7A6448', txt='#F1E6CC', font=P.SERIF,
           name='Pointer', rot_z=0.0, depth=0.03)
    for k in range(20):                    # birches on the far bank
        x = rnd.uniform(-30, 30)
        lib.cyl(0.12, 9, (x, 22 + rnd.uniform(-3, 3), 4.5), P.M('Birch', '#E8E4DA', rough=0.8, var=0.3), name='Birch')
        lib.sphere(2.0, (x, 22, 8.5), P.M('BirchLeaves', '#B49A4A', rough=0.9, var=0.3, bump=0.5), scale=(1, 1, 1.5),
                   name='BirchCrown')
    lib.fog_box(size=(200, 200, 8), loc=(0, 0, 2), density=0.09, color='#E2DDD2')
    cam(shot, (-0.5, -7.5, 1.4), (0.3, -6.6, 1.5), (1.0, -2.5, 1.5), (1.4, -2.5, 1.7), lens=40, dof=(1.3, -3.2, 1.6),
        fstop=4)
    return dict(fill=0.35, exposure=0.35)


def s_fitting(shot):
    sky('interior')
    room(7, 7, 3.4, wall='#D4C2A8')
    # a fitting booth: carved frame, a heavy curtain that closes and opens
    wd = P.wood('#3F2717', 'BoothWood')
    lib.box((1.6, 1.4, 0.08), (0, 1.0, 2.6), wd, bevel=0.01, name='BoothTop')
    for sx in (-1, 1):
        lib.box((0.08, 1.4, 2.6), (sx * 0.8, 1.0, 1.3), wd, bevel=0.01, name='BoothSide')
    lib.box((1.6, 0.06, 2.6), (0, 1.7, 1.3), P.M('BoothBack', '#E8D9C0', rough=0.8), bevel=0, name='BoothBack')
    mir = lib.box((0.6, 0.02, 1.6), (0, 1.66, 1.3), lib.mat('Mirror', '#C9D2D8', rough=0.02, metal=1.0), bevel=0,
                  name='Mirror')
    hook = lib.cyl(0.015, 0.12, (0.5, 1.64, 1.9), P.brass(), rot=(math.radians(90), 0, 0), name='Hook')
    cap = lib.sphere(0.12, (0.5, 1.56, 1.86), P.M('Khaki', '#6F6A3A', rough=0.9, bump=0.3, bs=200),
                     scale=(1.3, 0.5, 0.45), name='PilotkaOnHook')
    b = baroness((0, 1.0, 0), 0.0, 'strict')
    t_in, t_out = ev(shot, 'in', 0.6), ev(shot, 'out', shot['dur'] - 1.2)
    # she is inside, the curtain closes; when it opens she is gone, only her cap on the hook
    for o in (b['rig'], b['body']):
        o.hide_render = False
        o.keyframe_insert('hide_render', frame=F(0))
        o.hide_render = True
        o.keyframe_insert('hide_render', frame=F(t_in + 0.6))
    cap.hide_render = True
    cap.keyframe_insert('hide_render', frame=F(0))
    cap.hide_render = False
    cap.keyframe_insert('hide_render', frame=F(t_in + 0.6))
    import bmesh
    me = bpy.data.meshes.new('Curtain')
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=40, y_segments=10, size=0.5)
    for v in bm.verts:
        x = v.co.x + 0.5
        v.co = Vector((x * 1.55 - 0.775, 0.05 * math.sin(x * 40), (v.co.y + 0.5) * 2.45))
    bm.to_mesh(me)
    cur = bpy.data.objects.new('Curtain', me)
    bpy.context.scene.collection.objects.link(cur)
    me.materials.append(P.cloth('#7A1424', 'CurtainVelvet'))
    P.solidify(cur, 0.01)
    cur.location = (0, 0.28, 0.1)
    # closed = full width; open = bunched to the left (scale x)
    for t, sc in ((0, 0.12), (t_in, 0.12), (t_in + 0.55, 1.0), (t_out, 1.0), (t_out + 0.55, 0.12)):
        cur.scale = (sc, 1, 1)
        cur.location.x = -0.775 * (1 - sc)
        cur.keyframe_insert('scale', frame=F(t))
        cur.keyframe_insert('location', frame=F(t))
    lib.box((1.7, 0.04, 0.04), (0, 0.28, 2.58), P.brass(), bevel=0.01, name='CurtainRod')
    interior_lights((2, -2.5, 3), (-2.5, 2, 3), k=420, r=200)
    lib.light('POINT', (0, 1.0, 2.4), energy=60, color='#FFD8A8')
    cam(shot, (0.9, -2.6, 1.5), (0.6, -2.1, 1.45), (0, 1.0, 1.25), lens=40, dof=(0, 0.4, 1.3), fstop=4)
    return dict(fill=0.3, exposure=0.25)


def s_monitor(shot):
    sky('interior')
    lib.world_color('#4A4038', 0.5)
    room(5, 5, 3, wall='#B9AE9C')
    desk = lib.box((1.6, 0.8, 0.04), (0, 0.6, 0.74), P.wood('#6B4A2E', 'DeskTop'), bevel=0.01, name='Desk')
    lib.box((0.62, 0.035, 0.37), (0, 0.85, 1.12), P.M('MonFrame', '#16171A', rough=0.4), bevel=0.01, name='Monitor')
    lib.box((0.06, 0.06, 0.2), (0, 0.88, 0.86), P.M('MonFrame', '#16171A'), bevel=0.01, name='MonStand')
    scr = P.uv_plane((0.255, 0.34), (0, 0.8305, 1.12), rot=(math.radians(90), 0, 0),
                     m=P.screen_image(os.path.join(TEX, 'portrait.jpg'), 'ScreenMat', 1.4, reveal='reveal'), name='Screen')
    lib.box((0.6, 0.004, 0.35), (0, 0.832, 1.12), P.M('ScreenBg', '#0E0F12', rough=0.2), bevel=0, name='ScreenBg')
    scr['reveal'] = 0.0
    t = ev(shot, 'draw', 0.5)
    scr.keyframe_insert('["reveal"]', frame=F(t))
    scr['reveal'] = 1.0
    scr.keyframe_insert('["reveal"]', frame=F(t + 1.6))
    lib.box((0.44, 0.15, 0.02), (0, 0.45, 0.77), P.M('Keyboard', '#2A2B2E', rough=0.5), bevel=0.005, name='Keyboard')
    mug = lib.cyl(0.04, 0.1, (0.5, 0.5, 0.81), P.M('China', '#F2EEE6', rough=0.2, coat=0.6), name='Mug')
    # a desk calendar «АВГУСТ»
    lib.box((0.16, 0.01, 0.12), (-0.55, 0.7, 0.82), P.paper('#F4EEE2', 'CalPage'), bevel=0, name='DeskCal')
    P.text('АВГУСТ', 0.025, (-0.55, 0.693, 0.86), m=P.M('CalRed', '#B8322A'), font=P.SANS, extrude=0.0003)
    P.text('28', 0.05, (-0.55, 0.693, 0.805), m=P.M('CalInk', '#2A1C14'), font=P.SERIF, extrude=0.0003)
    lib.light('AREA', (1.0, -0.5, 1.8), energy=90, size=1, color='#FFE0B8')
    lib.light('POINT', (0, 0.6, 1.1), energy=8, color='#BFD0FF')
    cam(shot, (0.35, -0.55, 1.2), (0.12, -0.2, 1.15), (0, 0.83, 1.1), (0, 0.83, 1.12), lens=44, dof=(0, 0.83, 1.12),
        fstop=3.2)
    return dict(fill=0.25, exposure=0.25)


COMMENTS = ['баронесса взяла Эрмесовку', 'береги пыльник смолоду', 'она потерялась под Биркином',
            'герой ЛуиВиттона', 'маршал бронетанковых войск', 'покажу маме, она узнала', 'бабушка из альбома',
            'графство КокоШанель пало', 'гражданин республики Биркин', 'где купить мерч баронессы']


def s_comments(shot):
    sky('interior')
    lib.world_color('#4A4038', 0.5)
    lib.plane((2, 2), (0, 0, 0), P.wood('#6B4A2E', 'DeskTop'), name='Desk')
    ph = lib.box((0.075, 0.155, 0.008), (0, 0, 0.004), P.M('PhoneBody', '#1A1B1E', rough=0.3, metal=0.5), bevel=0.006,
                 name='Phone')
    scr = lib.box((0.069, 0.149, 0.001), (0, 0, 0.0085), P.M('PhoneScreen', '#101114', rough=0.1, emit='#0E0F12',
                                                               emit_strength=0.5), bevel=0, name='Screen')
    feed = lib.empty('Feed', loc=(0, 0, 0.0092))
    white = lib.mat('UiText', '#F2F2F2', emit='#F2F2F2', emit_strength=1.4)
    grey = lib.mat('UiGrey', '#9A9A9A', emit='#9A9A9A', emit_strength=1.0)
    rnd = random.Random(7)
    for i, c in enumerate(COMMENTS * 2):
        y = 0.06 - i * 0.026
        av = lib.cyl(0.0055, 0.0004, (-0.027, y, 0), P.M('Av' + str(i % 5), ['#C08A3E', '#7A1424', '#4F5B3A', '#3D4A5C',
                                                                            '#8B3A1E'][i % 5]), name='Avatar')
        av.parent = feed
        nm = P.text('user' + str(rnd.randint(100, 9999)), 0.0035, (-0.019, y + 0.004, 0), rot=(0, 0, 0), m=grey,
                    font=P.SANS, extrude=0.0, align='LEFT')
        nm.parent = feed
        tx = P.text(c, 0.0042, (-0.019, y - 0.002, 0), rot=(0, 0, 0), m=white, font=P.SANS, extrude=0.0, align='LEFT')
        tx.parent = feed
    # the feed scrolls up; items outside the screen are hidden by a mask ring (the phone body above the glass)
    lib.key_obj(feed, F(0), loc=(0, 0, 0.0092), interp='LINEAR')
    lib.key_obj(feed, F(shot['dur']), loc=(0, 0.16, 0.0092), interp='LINEAR')
    mask = P.M('PhoneBody', '#1A1B1E')
    lib.box((0.09, 0.12, 0.003), (0, 0.1355, 0.0095), mask, bevel=0, name='MaskTop')
    lib.box((0.09, 0.12, 0.003), (0, -0.1355, 0.0095), mask, bevel=0, name='MaskBot')
    lib.light('AREA', (0.2, -0.3, 0.5), energy=10, size=0.5, color='#FFE0B8')
    cam(shot, (0.0, -0.025, 0.17), (0.0, -0.02, 0.15), (0, 0.0, 0.0), lens=55, dof=(0, 0, 0.009), fstop=16)
    return dict(fill=0.15, exposure=0.1)


def s_portrait(shot):
    """The «old family photo» itself (rendered once to tex/portrait.jpg): frontal, studio light, plain backdrop."""
    lib.world_color('#8C8378', 0.8)
    lib.plane((4, 3), (0, 0.8, 1.5), P.M('Backdrop', '#8C8378', rough=0.95, var=0.25, vs=1.5),
              rot=(math.radians(90), 0, 0), name='Backdrop')
    baroness((0, 0, 0), 0.0, 'strict', head=(0, 4, 0))
    lib.light('AREA', (0.9, -1.4, 2.0), energy=90, size=1.2, color='#FFFFFF')
    lib.light('AREA', (-1.0, -1.0, 1.8), energy=40, size=1.2, color='#FFFFFF')
    for o in bpy.data.objects:
        if o.type == 'LIGHT':
            lib.look_at(o, (0, 0, 1.4))
    c = lib.camera((0, -1.75, 1.42), (0, 0, 1.33), lens=70)
    c.data.clip_start = 0.1
    r = bpy.context.scene.render              # a 3:4 print for the album and the monitor
    r.resolution_x, r.resolution_y = 1080, 1440
    return dict(fill=0.2, exposure=0.1)


def s_cta(shot):
    """Background for the calm ending (under the TikTok profile): the baroness in the marble hall."""
    sky('interior')
    _hall()
    b = baroness((0, 3, 0), 0.0, 'strict')
    cam(shot, (0.6, -2.5, 1.6), (0.4, -1.8, 1.6), (0, 3, 1.4), lens=44, dof=(0, 3, 1.4), fstop=3)
    return dict(fill=0.3, exposure=0.25)


SCENES = {
    'album': lambda s: s_album(s), 'album_gone': lambda s: s_album(s, gone=True), 'studio': s_studio,
    'street1918': s_street1918, 'crib': s_crib, 'dustbag': s_dustbag, 'zipper': s_zipper, 'queue': s_queue,
    'crate': s_crate, 'gun': s_gun, 'tags': s_tags, 'sale': s_sale, 'castle': s_castle, 'gates': s_gates,
    'check': lambda s: s_face(s, 'castle', 'check'), 'surrender': s_surrender, 'fortress': s_fortress,
    'calendar': s_calendar, 'balloon': s_balloon, 'wall': s_wall, 'refuse': lambda s: s_face(s, 'fortress', 'refuse'),
    'list': s_list, 'salecity': s_salecity, 'enter': s_enter, 'keys': s_keys, 'hall': lambda s: s_townhall(s),
    'flag': lambda s: s_townhall(s, close=True), 'capital': s_capital, 'palace': s_palace, 'shrine': s_shrine,
    'motto': s_motto, 'passport': s_passport, 'passbag': s_passbag, 'swamp': s_swamp, 'fitting': s_fitting,
    'promise': lambda s: s_face(s, 'fitting', 'promise'), 'monitor': s_monitor, 'comments': s_comments,
    'cta': s_cta, 'approve': lambda s: s_face(s, 'palace', 'approve'), 'portrait': s_portrait,
}


def build(shot, fps):
    lib.FPS = fps
    return SCENES[shot['variant']](shot)
