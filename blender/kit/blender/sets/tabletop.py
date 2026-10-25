"""Who collects taxes, fixes roads and settles disputes? Three still lifes on a dark table, camera trucks past them."""
import bpy, math, random, os
from mathutils import Vector
import lib
from lib import C
from passport import wood_mat

def coins(x0, y0, coll, rng):
    gold = lib.mat('Coin', '#C9A25E', rough=0.28, metal=1.0, var=0.12, var_scale=200)
    silver = lib.mat('CoinS', '#B8B2A8', rough=0.3, metal=1.0, var=0.12, var_scale=200)
    for s in range(6):
        cx, cy = x0 + rng.uniform(-0.07, 0.07), y0 + rng.uniform(-0.05, 0.05)
        n = rng.randint(4, 14)
        m = gold if rng.random() < 0.6 else silver
        for k in range(n):
            lib.cyl(0.0125, 0.0022, (cx + rng.uniform(-0.0012, 0.0012), cy + rng.uniform(-0.0012, 0.0012), 0.0011 + k * 0.00225),
                    m, verts=32, bevel=0.0004, name='Coin', coll=coll)
    for i in range(7):
        lib.cyl(0.0125, 0.0022, (x0 + rng.uniform(-0.12, 0.12), y0 + rng.uniform(-0.09, 0.08), 0.0011), gold, verts=32,
                rot=(0, 0, 0), bevel=0.0004, name='CoinLoose', coll=coll)
    # paper form under the coins
    form = lib.mat('TaxForm', '#E2D6C0', rough=0.85, var=0.08, var_scale=40)
    lib.box((0.21, 0.297, 0.0004), (x0 - 0.04, y0 + 0.03, 0.0002), form, rot=(0, 0, math.radians(12)), bevel=0, name='Form', coll=coll)
    ink = lib.mat('Ink', '#5A4E44', rough=0.9)
    for k in range(9):
        lib.box((0.15, 0.0025, 0.0003), (x0 - 0.04, y0 + 0.13 - k * 0.022, 0.00045), ink, rot=(0, 0, math.radians(12)), bevel=0,
                name='FormLine', coll=coll)

def road_piece(x0, y0, coll, rng):
    asp = lib.mat('AsphaltChunk', '#3A3631', rough=0.9, var=0.3, var_scale=60, bump=0.8, bump_scale=300)
    slab = lib.box((0.26, 0.17, 0.035), (x0, y0, 0), asp, rot=(0, 0, math.radians(-8)), bevel=0.004, name='Slab', coll=coll, origin='bottom')
    crack = lib.mat('Crack', '#0E0D0C', rough=1.0)
    pts = [(x0 - 0.12, y0 - 0.02, 0.0352)]
    for k in range(10):
        pts.append((pts[-1][0] + 0.024, pts[-1][1] + rng.uniform(-0.012, 0.012), 0.0352))
    lib.curve_poly('CrackLine', [pts], bevel=0.0018, mat_=crack, coll=coll)
    paint = lib.mat('RoadPaint', '#D8CCB6', rough=0.6)
    lib.box((0.03, 0.12, 0.0006), (x0 + 0.07, y0, 0.0353), paint, rot=(0, 0, math.radians(-8)), bevel=0, name='Paint', coll=coll)
    cone_m = lib.mat('Cone', '#E0622E', rough=0.45)
    band_m = lib.mat('ConeBand', '#E9E0D0', rough=0.4)
    cx, cy = x0 - 0.06, y0 + 0.11
    lib.box((0.075, 0.075, 0.006), (cx, cy, 0), lib.mat('ConeBase', '#2B2724', rough=0.7), bevel=0.003, name='ConeBase', coll=coll, origin='bottom')
    lib.cyl(0.03, 0.11, (cx, cy, 0.006), cone_m, r2=0.006, verts=40, name='ConeBody', coll=coll, origin='bottom')
    lib.cyl(0.0206, 0.018, (cx, cy, 0.046), band_m, r2=0.0174, verts=40, name='ConeBand', coll=coll, origin='bottom')
    grav = lib.mat('Gravel2', '#6E665C', rough=0.9, var=0.3, var_scale=100)
    for i in range(26):
        lib.sphere(rng.uniform(0.002, 0.006), (x0 + rng.uniform(-0.16, 0.16), y0 + rng.uniform(-0.12, 0.12), 0.002), grav, 8, 6,
                   scale=(1, 0.8, 0.6), name='Pebble', coll=coll)

def gavel(x0, y0, coll):
    wood = lib.mat('GavelWood', '#5A3622', rough=0.35, var=0.12, var_scale=80, coat=0.4)
    brass = lib.mat('Brass', '#C29A55', rough=0.25, metal=1.0)
    block = lib.cyl(0.055, 0.02, (x0, y0, 0), wood, verts=48, bevel=0.003, name='SoundBlock', coll=coll, origin='bottom')
    # pivot at the far end of the handle, so the head swings down onto the block
    pivot = lib.empty('GavelPivot', (x0 + 0.21, y0 + 0.02, 0.05), coll=coll)
    parts = [lib.cyl(0.0075, 0.19, (-0.095, 0, 0), wood, rot=(0, math.radians(90), 0), verts=24, name='Handle', coll=coll),
             lib.cyl(0.022, 0.09, (-0.2, 0, 0), wood, rot=(math.radians(90), 0, 0), verts=40, bevel=0.003, name='Head', coll=coll),
             lib.cyl(0.0225, 0.008, (-0.2, 0.03, 0), brass, rot=(math.radians(90), 0, 0), verts=40, name='Band1', coll=coll),
             lib.cyl(0.0225, 0.008, (-0.2, -0.03, 0), brass, rot=(math.radians(90), 0, 0), verts=40, name='Band2', coll=coll)]
    for p in parts:
        p.parent = pivot
    return pivot

def build(shot, fps=60):
    ev = shot.get('events', {})
    dur = shot['dur']
    F = lib.sec2f
    rng = random.Random(61)
    coll = lib.collection('Table')
    lib.world_color('#6A584A', 1.0)
    lib.plane((4, 3), (0.5, 0.3, 0), wood_mat(), name='Table', coll=coll)
    X = [0.0, 0.55, 1.1]
    coins(X[0], 0.0, coll, rng)
    road_piece(X[1], 0.0, coll, rng)
    pv = gavel(X[2] - 0.03, 0.0, coll)
    # gavel strike on the anchor word
    t_g = ev.get('gavel', dur - 1.2)
    up = math.radians(34)          # +Y rotation lifts the head (it sits on the -X side of the pivot)
    rest = math.radians(-2.3)      # head resting on the sound block
    lib.key_obj(pv, 1, rot=(0, rest, 0))
    lib.key_obj(pv, F(max(0.1, t_g - 0.75)), rot=(0, rest, 0))
    lib.key_obj(pv, F(t_g - 0.3), rot=(0, up, 0))
    lib.key_obj(pv, F(t_g), rot=(0, rest, 0), interp='LINEAR')
    lib.key_obj(pv, F(t_g + 0.07), rot=(0, math.radians(3.5), 0))
    lib.key_obj(pv, F(t_g + 0.18), rot=(0, rest, 0))
    # pools of warm light on each still life + bokeh lights far behind
    for x in X:
        lib.light('SPOT', (x - 0.1, -0.25, 0.7), (math.radians(20), 0, 0), energy=28, color='#FFD2A0', spot=38, blend=0.6, size=0.15,
                  name='Pool', coll=coll)
        lib.look_at(bpy.data.objects[-1] if False else coll.objects[-1], (x, 0.0, 0.0))
    lib.light('AREA', (0.55, -0.2, 1.4), (0, 0, 0), energy=60, color='#FFE6CC', size=2.5, name='SoftTop', coll=coll)
    bok, _ = lib.emission_mat('Bokeh', '#FFB46A', 8)
    for i in range(24):
        lib.sphere(0.012, (rng.uniform(-0.6, 1.8), rng.uniform(1.6, 2.6), rng.uniform(0.15, 0.6)), bok, 10, 6, name='Bokeh', coll=coll)
    t1, t2 = ev.get('roads', dur * 0.38), ev.get('judge', dur * 0.7)
    cam = lib.camera((X[0] - 0.05, -0.42, 0.24), (X[0], 0.0, 0.02), lens=50, dof=0.45, fstop=2.2)
    cam.data.shift_y = 0.12
    lib.animate_camera(cam,
                       [(0, (X[0] - 0.08, -0.43, 0.24)), (max(0.3, t1 - 0.5), (X[0] + 0.02, -0.42, 0.25)), (t1 + 0.1, (X[1] - 0.02, -0.42, 0.25)),
                        (t2 - 0.5, (X[1] + 0.03, -0.41, 0.25)), (t2 + 0.1, (X[2] - 0.03, -0.40, 0.24)), (dur, (X[2] + 0.0, -0.38, 0.23))],
                       [(0, (X[0] - 0.03, 0.0, 0.02)), (max(0.3, t1 - 0.5), (X[0] + 0.02, 0.0, 0.02)), (t1 + 0.1, (X[1], 0.0, 0.02)),
                        (t2 - 0.5, (X[1] + 0.03, 0.0, 0.02)), (t2 + 0.1, (X[2] - 0.02, 0.0, 0.03)), (dur, (X[2] - 0.01, 0.0, 0.03))],
                       step=1, focus_keys=[(0, 0.48), (dur, 0.45)])
    lib.bloom(strength=0.3, threshold=1.3, size=6)
    return dict(samples=64, fill=0.7, exposure=0.2)
