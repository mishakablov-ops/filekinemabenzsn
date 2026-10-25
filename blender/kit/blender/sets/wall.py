"""Border wall at night: concrete T-wall panels, concertina wire, watchtower with sweeping searchlight, sodium lamps, fog."""
import bpy, math, random
from mathutils import Vector
import lib
from lib import C

def concrete(name, col, var=0.18):
    return lib.mat(name, col, rough=0.92, var=var, var_scale=2.2, bump=0.25, bump_scale=14)

def t_wall_panel(x, mats, rnd, coll):
    m = rnd.choice(mats)
    h = 4.1 + rnd.uniform(-0.04, 0.04)
    lean = rnd.uniform(-0.006, 0.006)
    slab = lib.box((1.18, 0.26, h), (x, 0, 0), m, rot=(lean, 0, 0), bevel=0.025, name='Panel', coll=coll, origin='bottom')
    foot = lib.box((1.18, 1.25, 0.42), (x, -0.35, 0), m, bevel=0.03, name='Foot', coll=coll, origin='bottom')
    # lifting hole hint
    return slab, foot

def concertina(x0, x1, z, y=0.0, r=0.32, pitch=0.42, mat_=None, coll=None):
    pts = []
    n = int((x1 - x0) / pitch * 22)
    for i in range(n + 1):
        t = i / n
        x = x0 + (x1 - x0) * t
        a = 2 * math.pi * (x - x0) / pitch
        pts.append((x + 0.06 * math.sin(a * 0.5), y + r * math.cos(a), z + r * math.sin(a)))
    ob = lib.curve_poly('Concertina', [pts], bevel=0.006, mat_=mat_, res=1, coll=coll)
    return ob

def watchtower(loc, mats, coll):
    x, y = loc
    steel, roof, glass_lit, conc = mats
    legs = []
    for dx in (-1.3, 1.3):
        for dy in (-1.3, 1.3):
            leg = lib.box((0.18, 0.18, 9.0), (x + dx, y + dy, 0), steel, bevel=0.01, name='Leg', coll=coll, origin='bottom')
            legs.append(leg)
    # cross braces
    for z0 in (1.0, 4.0, 7.0):
        for (ax, ay, bx, by) in ((-1.3, -1.3, 1.3, -1.3), (-1.3, 1.3, 1.3, 1.3), (-1.3, -1.3, -1.3, 1.3), (1.3, -1.3, 1.3, 1.3)):
            a = Vector((x + ax, y + ay, z0)); b = Vector((x + bx, y + by, z0 + 2.6))
            lib.curve_poly('Brace', [[a, b]], bevel=0.04, mat_=steel, coll=coll)
    lib.box((3.6, 3.6, 0.25), (x, y, 9.0), conc, bevel=0.02, name='Deck', coll=coll, origin='bottom')
    cabin = lib.box((3.0, 3.0, 2.3), (x, y, 9.25), steel, bevel=0.03, name='Cabin', coll=coll, origin='bottom')
    # windows (lit dim)
    for side in range(4):
        ang = side * math.pi / 2
        cx, cy = x + 1.52 * math.cos(ang), y + 1.52 * math.sin(ang)
        lib.box((0.04 if side % 2 == 0 else 2.2, 2.2 if side % 2 == 0 else 0.04, 0.8), (cx, cy, 10.55), glass_lit,
                bevel=0, name='Win', coll=coll)
    lib.box((3.8, 3.8, 0.18), (x, y, 11.55), roof, bevel=0.03, name='Roof', coll=coll, origin='bottom')
    # searchlight on the roof
    pivot = lib.empty('SearchPivot', (x, y - 0.4, 12.15), coll=coll)
    housing = lib.cyl(0.32, 0.6, (0, 0, 0), steel, rot=(math.radians(90), 0, 0), name='Lamp', coll=coll)
    housing.parent = pivot
    lens_m, lens_em = lib.emission_mat('LensGlow', '#FFE7C4', 40.0)
    lens = lib.cyl(0.27, 0.02, (0, 0.31, 0), lens_m, rot=(math.radians(90), 0, 0), name='Lens', coll=coll)
    lens.parent = pivot
    spot = lib.light('SPOT', (0, 0.36, 0), (math.radians(90), 0, 0), energy=60000, color='#FFF0DC', spot=9,
                     blend=0.25, size=0.12, name='Searchlight', volume=2.5, coll=coll)
    spot.parent = pivot
    return pivot, lens_em, spot

def sodium_lamp(x, y, h, coll, pole_m, bulb_m):
    lib.cyl(0.07, h, (x, y, 0), pole_m, verts=12, name='Pole', coll=coll, origin='bottom')
    arm = lib.box((0.08, 1.4, 0.08), (x, y + 0.65, h - 0.05), pole_m, bevel=0, name='Arm', coll=coll)
    head = lib.box((0.36, 0.6, 0.12), (x, y + 1.35, h - 0.12), pole_m, bevel=0.02, name='Head', coll=coll)
    lib.box((0.28, 0.46, 0.02), (x, y + 1.35, h - 0.19), bulb_m, bevel=0, name='Bulb', coll=coll)
    l = lib.light('SPOT', (x, y + 1.35, h - 0.25), (0, 0, 0), energy=5200, color='#FF9840', spot=115, blend=0.9,
                  size=0.25, name='Sodium', volume=1.4, coll=coll)
    return l

def build(shot, fps=60):
    ev = shot.get('events', {})
    dur = shot['dur']
    rnd = random.Random(21)
    coll = lib.collection('Wall')
    lib.world_sky_view_gradient('#1A1E26', '#5A4030', '#1A1714', strength=2.2, fog=0.006, fog_col='#BDB2A4', aniso=0.55,
                                glow_dir=(0.15, 1.0, 0.0), glow_col='#FF8A3A', glow_size=0.5, glow_strength=0.7)
    ground_m = lib.mat('Dirt', '#3A332B', rough=0.95, var=0.25, var_scale=0.6, bump=0.4, bump_scale=3)
    lib.plane((1200, 1200), (0, 0, 0), ground_m, name='Ground', subdiv=1, coll=coll)
    road_m = lib.mat('Patrol', '#4A433A', rough=0.9, var=0.2, var_scale=1.5, bump=0.5, bump_scale=30)
    lib.plane((420, 5), (0, -4.2, 0.01), road_m, name='PatrolRoad', coll=coll)
    mats = [concrete('ConcA', '#8E857A'), concrete('ConcB', '#7F776D'), concrete('ConcC', '#9A9184', 0.22)]
    for i in range(-40, 90):
        t_wall_panel(i * 1.2, mats, rnd, coll)
    wire_m = lib.mat('Wire', '#77736D', rough=0.3, metal=1.0)
    concertina(-50, 110, 4.42, y=0.0, r=0.3, mat_=wire_m, coll=coll)
    steel = lib.mat('Steel', '#3B3D3E', rough=0.55, metal=0.6, var=0.2, var_scale=4)
    roof = lib.mat('Roof', '#2C2C2B', rough=0.7)
    glass_lit, _ = lib.emission_mat('CabinWin', '#FFB46A', 0.6)
    conc = mats[1]
    pivot, lens_em, spot = watchtower((26.0, -8.5), (steel, roof, glass_lit, conc), coll)
    spot.data.energy = 30000
    spot.data.volume_factor = 5.0
    watchtower((92.0, -8.5), (steel, roof, glass_lit, conc), coll)
    # sodium lamps on the far side of the patrol road, angled at the wall
    pole_m = lib.mat('PoleM', '#2E2F30', rough=0.6, metal=0.5)
    bulb_m, _ = lib.emission_mat('SodiumBulb', '#FFB15A', 18.0)
    for x in range(-24, 110, 13):
        h = 7.0
        X = x + 2
        lib.cyl(0.07, h, (X, -7.0, 0), pole_m, verts=12, name='Pole', coll=coll, origin='bottom')
        lib.box((0.08, 1.6, 0.08), (X, -6.25, h - 0.05), pole_m, bevel=0, name='Arm', coll=coll)
        lib.box((0.36, 0.6, 0.12), (X, -5.4, h - 0.12), pole_m, bevel=0.02, name='Head', coll=coll)
        lib.box((0.28, 0.46, 0.02), (X, -5.4, h - 0.19), bulb_m, bevel=0, name='Bulb', coll=coll)
        lib.light('SPOT', (X, -5.3, h - 0.25), (math.radians(38), 0, 0), energy=2600, color='#FF9A45', spot=95, blend=0.85,
                  size=0.25, name='Sodium', volume=0.7, coll=coll)
    # warning plates on the wall
    plate_m = lib.mat('Plate', '#B8432A', rough=0.5)
    plate2 = lib.mat('Plate2', '#E3D6C1', rough=0.6)
    for x in range(-30, 110, 18):
        lib.box((0.9, 0.03, 0.6), (x + 0.6, -0.15, 2.3), plate_m, bevel=0.01, name='Warn', coll=coll)
        lib.box((0.7, 0.035, 0.12), (x + 0.6, -0.16, 2.3), plate2, bevel=0, name='WarnBar', coll=coll)
    hill_m = lib.mat('Hills', '#14120F', rough=1.0)
    for i in range(14):
        lib.sphere(rnd.uniform(25, 45), (rnd.uniform(-220, 260), rnd.uniform(130, 190), -rnd.uniform(12, 22)), hill_m, 32, 16,
                   scale=(2.4, 1.0, 0.55), name='Hill', coll=coll)
    F = lib.sec2f
    for t, yaw in ((0.0, math.radians(38)), (dur * 0.6, math.radians(72)), (dur, math.radians(62))):
        lib.key_obj(pivot, F(t), rot=(math.radians(-14), 0, yaw))
    import civ
    civ.power_line((-60, -48), (300, -48), coll, spacing=60)
    civ.town((270, -95), coll, n=22, spread=(80, 45), seed=21)
    civ.cell_tower((42, -24, 0), coll)
    civ.water_tower((95, -32, 0), coll)
    for i, (x, y) in enumerate(((130, -170), (180, -195), (235, -160))):
        civ.wind_turbine((x, y, 0), coll, rot=math.radians(180), phase=i * 1.1)
    civ.tree_line((10, -62), (170, -75), coll, n=16, seed=23)
    # patrol: a parked SUV with headlights on and a guard walking along the wall
    lib.car((15.0, -4.6, 0), 0.0, '#C9C1B2', coll, kind='van', rng=rnd, name='Patrol')
    import military
    g = military.soldier((7.0, -3.3, 0), 0, rnd, coll, 'march', name='Guard')
    lib.walk(g, period=1.15, phase=0.3, swing=0.35)
    lib.move_root(g, [(7.0, -3.3, 0), (-3.0, -3.3, 0)], t0=0, speed=1.0)
    moon = lib.light('SUN', (0, 0, 0), energy=0.7, color='#A4B4C8', size=1.5, name='Moon')
    moon.rotation_euler = (math.radians(55), 0, math.radians(210))
    cam = lib.camera((-14, -3.4, 1.1), (10, 0.5, 2.6), lens=24, dof=9.0, fstop=4.0)
    lib.animate_camera(cam, [(0, (-15.0, -3.3, 1.05)), (dur, (-10.5, -3.0, 1.3))],
                       [(0, (8.0, 0.6, 3.4)), (dur, (13.0, 0.4, 3.0))], step=2, focus_keys=[(0, 8.0), (dur, 8.0)])
    cam.data.shift_y = 0.05
    lib.bloom(strength=0.4, threshold=1.2, size=8)
    return dict(samples=56, fill=1.1, exposure=0.6)
