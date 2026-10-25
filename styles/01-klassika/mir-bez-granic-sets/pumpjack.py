"""Oil pumpjacks in the desert at sunset (rivers and oil -> new lines)."""
import bpy, bmesh, math, random
from mathutils import Vector
import lib
from lib import C

def dunes(coll, m, size=400, res=200, seed=3):
    rng = random.Random(seed)
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=res, y_segments=res, size=size / 2)
    waves = [(rng.uniform(0.01, 0.05), rng.uniform(0, 6.28), rng.uniform(0.6, 2.2), rng.uniform(-1, 1)) for _ in range(6)]
    for v in bm.verts:
        x, y = v.co.x, v.co.y
        z = 0
        for k, ph, a, ang in waves:
            z += a * math.sin(k * (x * math.cos(ang) + y * math.sin(ang)) + ph)
        fade = min(1.0, (abs(y + 20) / 60.0))   # flatter near the camera / pumps
        dr = math.hypot(x - 22, y - 125)
        fade *= min(1.0, max(0.0, (dr - 95) / 45.0))   # flat pad under the refinery
        fade *= min(1.0, max(0.0, (math.hypot(x - 4, y - 16) - 26) / 16.0))   # flat work site round the pump
        fade *= min(1.0, max(0.0, (abs(y - 48) - 6) / 10.0))                  # flat dirt road
        v.co.z = z * fade
    return lib.mesh_from_bm(bm, 'Dunes', m, smooth=True, coll=coll)

def pumpjack(x, y, rot, coll, m, dark, phase=0.0, scale=1.0, period=4.0):
    root = lib.empty('Pumpjack', (x, y, 0), (0, 0, rot), coll=coll)
    root.scale = (scale, scale, scale)
    parts = []
    parts.append(lib.box((7.5, 1.6, 0.35), (0, 0, 0), dark, bevel=0.03, name='Skid', coll=coll, origin='bottom'))
    # samson post (A-frame)
    for sy in (-0.6, 0.6):
        parts.append(lib.curve_poly('Samson', [[(-0.6, sy, 0.3), (0.0, sy * 0.25, 4.6)], [(0.6, sy, 0.3), (0.0, sy * 0.25, 4.6)]],
                                    bevel=0.09, mat_=m, coll=coll))
    beam_pivot = lib.empty('BeamPivot', (0, 0, 4.7), coll=coll)
    beam_pivot.parent = root
    beam = lib.box((7.6, 0.45, 0.55), (0.6, 0, 0), m, bevel=0.03, name='Beam', coll=coll)
    head = lib.poly_prism([(0, -0.9), (0.55, -0.6), (0.75, 0.0), (0.55, 0.6), (0, 0.9), (-0.25, 0)], 0.5, (0, 0, 0), m,
                          name='HorseHead', bevel=0.02, coll=coll)
    head.rotation_euler = (math.radians(90), 0, 0)
    head.location = (4.4, 0.25, 0)
    for o in (beam, head):
        o.parent = beam_pivot
    # gearbox + rotating cranks with counterweights
    parts.append(lib.box((1.2, 1.0, 1.4), (-2.6, 0, 0.3), dark, bevel=0.05, name='Gearbox', coll=coll, origin='bottom'))
    crank = lib.empty('Crank', (-2.6, 0, 1.4), coll=coll)
    crank.parent = root
    for sy in (-0.65, 0.65):
        arm = lib.box((2.0, 0.12, 0.35), (-0.7, sy, 0), m, bevel=0.02, name='CrankArm', coll=coll)
        cw = lib.box((1.0, 0.25, 1.1), (-1.5, sy, 0), dark, bevel=0.05, name='CW', coll=coll)
        for o in (arm, cw):
            o.parent = crank
    # bridle + polished rod
    rod = lib.cyl(0.04, 4.0, (5.15, 0, 0.35), lib.mat('Rod', '#9A958C', rough=0.25, metal=1.0), verts=10, name='Rod', coll=coll,
                  origin='bottom')
    parts.append(rod)
    parts.append(lib.cyl(0.35, 0.6, (5.15, 0, 0.0), dark, verts=20, name='Wellhead', coll=coll, origin='bottom'))
    for p in parts:
        p.parent = root
    # motion: crank spins, beam rocks in sync
    sc = bpy.context.scene
    for f in range(sc.frame_start, sc.frame_end + 1, 2):
        t = (f - 1) / lib.FPS
        a = 2 * math.pi * t / period + phase
        crank.rotation_euler = (0, -a, 0)
        crank.keyframe_insert('rotation_euler', frame=f)
        beam_pivot.rotation_euler = (0, math.radians(14) * math.sin(a), 0)
        beam_pivot.keyframe_insert('rotation_euler', frame=f)
        rod.location = (5.15, 0, 0.35 - 5.15 * math.sin(math.radians(14) * math.sin(a)))
        rod.keyframe_insert('location', frame=f)
    for ob in (crank, beam_pivot, rod):
        for fc in ob.animation_data.action.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = 'LINEAR'
    return root

def build(shot, fps=60):
    dur = shot['dur']
    coll = lib.collection('Oil')
    # daytime: high sun, clear blue sky, light haze
    sun_dir = Vector((-0.45, 0.35, 0.82))
    lib.world_sky_view_gradient('#4F86C6', '#CADCEB', '#A88E6E', strength=2.0, fog=0.0018, fog_col='#E4ECF2', aniso=0.4,
                                glow_dir=sun_dir, glow_col='#FFF3E0', glow_size=0.12, glow_strength=0.6)
    s = lib.light('SUN', (0, 0, 0), energy=4.6, color='#FFF2E2', size=1.2, name='Sun', volume=1.0)
    s.rotation_euler = (-sun_dir).normalized().to_track_quat('-Z', 'Y').to_euler()
    sand = lib.mat('Sand', '#CDAA7C', rough=0.92, var=0.15, var_scale=0.08, bump=0.3, bump_scale=60)
    dunes(coll, sand)
    steel = lib.mat('PumpSteel', '#3A3633', rough=0.55, metal=0.5, var=0.15, var_scale=3)
    dark = lib.mat('PumpDark', '#22201E', rough=0.7)
    pumpjack(1.5, 14, math.radians(8), coll, steel, dark, phase=0.0, scale=1.0)
    pumpjack(-14, 40, math.radians(-12), coll, steel, dark, phase=1.7, scale=1.0)
    pumpjack(18, 70, math.radians(20), coll, steel, dark, phase=3.1, scale=1.0)
    pumpjack(-62, 82, math.radians(5), coll, steel, dark, phase=4.4, scale=1.0)
    # refinery with a live flare, power line, tanker trucks
    import civ
    civ.refinery((22, 125), coll)
    civ.power_line((-45, -30), (-45, 200), coll, spacing=65)
    civ.truck((-30, 30, 0), math.radians(80), coll, color='#C9C1B2')
    civ.cell_tower((-72, 60, 0), coll)
    # pipeline
    pipe = lib.mat('Pipe', '#5A524A', rough=0.5, metal=0.6)
    lib.cyl(0.25, 260, (14, 60, 0.45), pipe, rot=(math.radians(90), 0, math.radians(-4)), verts=20, name='Pipeline', coll=coll)
    # the work site: a worker in a hi-vis vest, a service pickup, a shed, small tanks, a tanker on the dirt road
    road = lib.mat('DirtTrack', '#9A6E48', rough=0.95, var=0.25, var_scale=0.5, bump=0.4, bump_scale=20)
    lib.plane((420, 9), (0, 48, 0.03), road, name='DirtRoad', coll=coll)
    lib.plane((4.5, 30), (-1.0, 31, 0.025), road, rot=(0, 0, math.radians(8)), name='SiteTrack', coll=coll)
    rw = random.Random(14)
    wk = lib.person((4.4, 9.6, 0), 0, height=1.0, rng=rw, coll=coll, name='Worker')
    vest = lib.pmat('#E8742A')
    for k in ('torso', 'armL', 'armR'):
        wk[k].material_slots[0].material = vest
    wk['legL'].material_slots[0].material = lib.pmat('#2F3B45'); wk['legR'].material_slots[0].material = lib.pmat('#2F3B45')
    hat = lib.sphere(0.13, (0, 0, 1.68), lib.mat('HardHat', '#E9E0D0', rough=0.35), 20, 10, scale=(1.0, 1.1, 0.75), name='HardHat', coll=coll)
    hat.parent = wk['root']
    tab = lib.box((0.22, 0.03, 0.3), (0.0, -0.32, 1.15), lib.mat('Tablet', '#1A1C1E', rough=0.2), rot=(math.radians(-55), 0, 0), bevel=0.01,
                  name='Tablet', coll=coll)
    tab.parent = wk['root']
    lib.walk(wk, period=1.15, phase=0.0, swing=0.35)
    lib.move_root(wk, [(4.4, 9.6, 0), (1.9, 11.0, 0)], t0=0.0, speed=0.85)
    # foreground props: oil drums and a stack of pipes
    for i, (bx, by, c) in enumerate(((-2.3, 5.6, '#2F5A78'), (-1.65, 5.9, '#B4532A'), (-2.05, 6.3, '#2F5A78'), (-1.4, 6.6, '#C9A24A'))):
        lib.cyl(0.29, 0.88, (bx, by, 0), lib.mat('Drum' + c, c, rough=0.5, metal=0.4, var=0.15, var_scale=8), verts=24, bevel=0.02,
                name='Drum', coll=coll, origin='bottom')
    pipe_m = lib.mat('PipeStack', '#6E665C', rough=0.45, metal=0.7)
    for k, (dz, dy) in enumerate(((0.16, 0.0), (0.16, 0.34), (0.16, 0.68), (0.45, 0.17), (0.45, 0.51), (0.74, 0.34))):
        lib.cyl(0.16, 4.2, (1.2, 7.0 + dy, dz), pipe_m, rot=(0, math.radians(90), math.radians(12)), verts=16, name='PipeLying', coll=coll)
    lib.add_sine(wk['head'], 'rotation_euler', 2, 0.3, 2.6, 0.5)
    lib.car((-3.6, 18.5, 0), math.radians(25), '#D8D0C2', coll, kind='van', lights=False, rng=rw, name='ServiceVan')
    shed = lib.mat('Shed', '#B4532A', rough=0.6, var=0.15, var_scale=2)
    lib.box((6.0, 2.5, 2.6), (-7.5, 26.0, 0), shed, rot=(0, 0, math.radians(15)), bevel=0.05, name='Shed', coll=coll, origin='bottom')
    tankm = lib.mat('SmallTank', '#D2C8B8', rough=0.5)
    for ty in (17.5, 21.3):
        lib.cyl(1.6, 4.2, (11.5, ty, 0), tankm, verts=32, name='SiteTank', coll=coll, origin='bottom')
    sign = lib.mat('SignPanel', '#E9C24A', rough=0.5)
    lib.cyl(0.05, 1.6, (3.6, 9.0, 0), lib.mat('SignPost', '#3A3633', rough=0.6), verts=8, name='SignPost', coll=coll, origin='bottom')
    lib.box((0.6, 0.04, 0.5), (3.6, 8.97, 1.6), sign, bevel=0.01, name='SignPanel', coll=coll)
    tanker = civ.truck((-70, 47, 0), 0.0, coll, color='#8A2E25', name='Tanker')
    tank_t = lib.cyl(1.25, 10.5, (-0.8, 0, 2.6), lib.mat('TankerShell', '#C9C1B2', rough=0.3, metal=0.6), rot=(0, math.radians(90), 0),
                     verts=32, name='TankerShell', coll=coll)
    tank_t.parent = tanker
    for ch in tanker.children:
        if ch.name.startswith('TrailerBox'):
            ch.hide_render = True
    lib.drive(tanker, [(-70, 47, 0), (120, 47, 0)], t0=0.0, speed=9.0, accel=50.0)
    cam = lib.camera((-5.9, 0.7, 1.4), (1.5, 14, 3.2), lens=44, dof=15.0, fstop=5.6)
    lib.animate_camera(cam, [(0, (-6.4, 0.1, 1.35)), (dur, (-5.4, 1.6, 1.5))],
                       [(0, (1.8, 14, 3.1)), (dur, (2.2, 14, 2.9))], step=2, focus_keys=[(0, 15), (dur, 14)])
    lib.bloom(strength=0.4, threshold=1.1, size=8)
    return dict(samples=48, fill=0.7, exposure=-0.15)
