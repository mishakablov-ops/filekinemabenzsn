"""Soldiers, tanks and a battle over a freshly drawn line. Variants: march (column of soldiers past tanks), battle."""
import bpy, math, random
from mathutils import Vector
import lib
from lib import C

OLIVE = '#4E5236'

def tank(loc=(0, 0, 0), heading=0.0, coll=None, name='Tank', paint=OLIVE, dust=0.25):
    root = lib.empty(name, loc, (0, 0, heading), coll=coll)
    body = lib.mat(name + 'Paint', paint, rough=0.78, var=dust, var_scale=1.2, bump=0.15, bump_scale=20)
    dark = lib.mat('TrackDark', '#1E1D1B', rough=0.85, var=0.2, var_scale=6, bump=0.4, bump_scale=40)
    metal = lib.mat('GunMetal', '#2C2D2B', rough=0.5, metal=0.7)
    parts = []
    # hull (side profile in XZ, extruded along Y)
    prof = [(-3.4, 0.45), (3.0, 0.45), (3.65, 0.95), (3.2, 1.45), (-3.3, 1.45), (-3.5, 1.0)]
    hull = lib.poly_prism(prof, 2.3, (0, 0, 0), body, name=name + 'Hull', bevel=0.04, coll=coll)
    hull.rotation_euler = (math.radians(90), 0, 0)
    hull.location = (0, 1.15, 0)
    parts.append(hull)
    for sy in (-1, 1):
        tr = lib.box((7.0, 0.62, 0.95), (0, sy * 1.42, 0.0), dark, bevel=0.32, name=name + 'Track', coll=coll, origin='bottom')
        parts.append(tr)
        fen = lib.box((7.3, 0.7, 0.06), (0, sy * 1.42, 1.0), body, bevel=0.02, name=name + 'Fender', coll=coll)
        parts.append(fen)
        for k in range(6):
            w = lib.cyl(0.34, 0.12, (-2.6 + k * 1.04, sy * 1.76, 0.42), metal, rot=(math.radians(90), 0, 0), verts=24,
                        bevel=0.02, name=name + 'Wheel', coll=coll)
            parts.append(w)
    turret = lib.poly_prism([(-1.7, -1.15), (1.0, -1.25), (1.95, -0.6), (1.95, 0.6), (1.0, 1.25), (-1.7, 1.15)], 0.78,
                            (0.0, 0, 1.45), body, name=name + 'Turret', bevel=0.05, coll=coll)
    parts.append(turret)
    mant = lib.box((0.5, 0.7, 0.5), (2.1, 0, 1.84), body, bevel=0.06, name=name + 'Mantlet', coll=coll)
    barrel = lib.cyl(0.085, 4.6, (4.55, 0, 1.86), metal, rot=(0, math.radians(90), 0), verts=20, name=name + 'Barrel', coll=coll)
    brake = lib.cyl(0.13, 0.35, (6.8, 0, 1.86), metal, rot=(0, math.radians(90), 0), verts=20, name=name + 'Brake', coll=coll)
    hatch = lib.cyl(0.38, 0.16, (-0.6, 0.45, 2.23), body, verts=24, bevel=0.03, name=name + 'Hatch', coll=coll)
    box2 = lib.box((0.9, 0.5, 0.4), (-2.1, 0.0, 1.75), body, bevel=0.05, name=name + 'Bustle', coll=coll)
    parts += [mant, barrel, brake, hatch, box2]
    for p in parts:
        p.parent = root
    return root

def soldier(loc, heading, rng, coll, pose='march', name='Soldier'):
    p = lib.person(loc, heading, height=rng.uniform(0.96, 1.04), rng=rng, coll=coll, name=name)
    uni = lib.pmat(rng.choice(['#4E5236', '#55583D', '#4A4D35', '#5C5A44']))
    for k in ('torso', 'legL', 'legR', 'armL', 'armR'):
        p[k].material_slots[0].material = uni
    helmet_m = lib.pmat('#3F4330')
    h = lib.sphere(0.135, (0, 0, 1.655), helmet_m, 20, 12, scale=(1.0, 1.08, 0.82), name=name + '_helmet', coll=coll)
    h.parent = p['root']
    # cut the lower half visually by pushing it up; brim
    brim = lib.cyl(0.15, 0.025, (0, 0, 1.63), helmet_m, verts=24, name=name + '_brim', coll=coll)
    brim.parent = p['root']
    pack = lib.box((0.3, 0.16, 0.4), (0, 0.19, 1.22), helmet_m, bevel=0.04, name=name + '_pack', coll=coll)
    pack.parent = p['root']
    rifle_m = lib.pmat('#1E1E1C')
    if pose == 'march':
        r = lib.box((0.05, 0.05, 0.95), (0.0, 0.2, 1.2), rifle_m, rot=(0, math.radians(35), 0), bevel=0.01, name=name + '_rifle', coll=coll)
        r.parent = p['root']
    else:
        # rifle held forward (aiming): arms forward
        p['armL'].rotation_euler = (math.radians(-75), 0, math.radians(-25))
        p['armR'].rotation_euler = (math.radians(-80), 0, math.radians(20))
        r = lib.box((0.05, 0.95, 0.06), (0.0, -0.42, 1.36), rifle_m, bevel=0.01, name=name + '_rifle', coll=coll)
        r.parent = p['root']
    p['rifle'] = r
    return p

def smoke_column(loc, h=30, r=5, density=0.6, color='#3A3530', coll=None, name='Smoke'):
    ob = lib.cyl(r, h, loc, None, verts=24, r2=r * 2.2, name=name, coll=coll, origin='bottom')
    m = bpy.data.materials.new(name + 'Mat')
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    L = nt.links
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    v = nt.nodes.new('ShaderNodeVolumePrincipled')
    v.inputs['Color'].default_value = C(color)
    tc = nt.nodes.new('ShaderNodeTexCoord')
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 0.35; nz.inputs['Detail'].default_value = 6
    nz.inputs['Roughness'].default_value = 0.65
    try:
        nz.noise_dimensions = '4D'
        val = nt.nodes.new('ShaderNodeValue'); val.name = 'W'
        val.outputs[0].default_value = 0
        L.new(val.outputs[0], nz.inputs['W'])
        holder = val
    except Exception:
        holder = None
    L.new(tc.outputs['Object'], nz.inputs['Vector'])
    # fade toward the cylinder edge + top
    sep = nt.nodes.new('ShaderNodeSeparateXYZ'); L.new(tc.outputs['Object'], sep.inputs[0])
    vm = nt.nodes.new('ShaderNodeVectorMath'); vm.operation = 'LENGTH'
    comb = nt.nodes.new('ShaderNodeCombineXYZ'); L.new(sep.outputs['X'], comb.inputs['X']); L.new(sep.outputs['Y'], comb.inputs['Y'])
    L.new(comb.outputs[0], vm.inputs[0])
    rad = nt.nodes.new('ShaderNodeMapRange')
    rad.inputs['From Min'].default_value = r * 1.6; rad.inputs['From Max'].default_value = r * 0.2
    L.new(vm.outputs['Value'], rad.inputs['Value'])
    mr = nt.nodes.new('ShaderNodeMapRange')
    mr.inputs['From Min'].default_value = 0.42; mr.inputs['From Max'].default_value = 0.72
    mr.inputs['To Max'].default_value = density
    L.new(nz.outputs['Fac'], mr.inputs['Value'])
    mul = nt.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'
    L.new(mr.outputs['Result'], mul.inputs[0]); L.new(rad.outputs['Result'], mul.inputs[1])
    L.new(mul.outputs[0], v.inputs['Density'])
    L.new(v.outputs[0], out.inputs['Volume'])
    ob.data.materials.append(m)
    if holder is not None:
        sc = bpy.context.scene
        holder.outputs[0].default_value = 0.0
        holder.outputs[0].keyframe_insert('default_value', frame=1)
        holder.outputs[0].default_value = sc.frame_end / lib.FPS * 0.25
        holder.outputs[0].keyframe_insert('default_value', frame=sc.frame_end)
        ad = m.node_tree.animation_data
        if ad and ad.action:
            for fc in ad.action.fcurves:
                for kp in fc.keyframe_points:
                    kp.interpolation = 'LINEAR'
    return ob

def fire(loc, coll, strength=1.0, seed=0, name='Fire'):
    rng = random.Random(seed)
    m, em = lib.emission_mat(name + 'Glow', '#FF7A2A', 12 * strength)
    for i in range(5):
        s = lib.sphere(rng.uniform(0.3, 0.7) * strength, (loc[0] + rng.uniform(-0.8, 0.8), loc[1] + rng.uniform(-0.8, 0.8),
                                                        loc[2] + rng.uniform(0.1, 0.9)), m, 12, 8,
                       scale=(1, 1, 1.8), name=name + 'Flame', coll=coll)
        lib.add_sine(s, 'scale', 2, 0.25, rng.uniform(0.18, 0.35), rng.uniform(0, 6))
    l = lib.light('POINT', (loc[0], loc[1], loc[2] + 1.2), energy=9000 * strength, color='#FF8A35', size=1.2, name=name + 'Light',
                  coll=coll)
    l.data.energy = 9000 * strength
    l.data.keyframe_insert('energy', frame=1)
    fc = l.data.animation_data.action.fcurves.find('energy')
    mod = fc.modifiers.new('NOISE')
    mod.scale = 4.0
    mod.strength = 5000 * strength
    mod.phase = rng.uniform(0, 100)
    return l

def flash(loc, t, coll, power=1.0, name='Blast'):
    """Distant explosion: light spike + expanding emissive ball."""
    F = lib.sec2f
    l = lib.light('POINT', loc, energy=0, color='#FFB060', size=3, name=name + 'Light', coll=coll, volume=3.0)
    for tt, e in ((t - 0.02, 0), (t, 900000 * power), (t + 0.12, 400000 * power), (t + 0.9, 0)):
        l.data.energy = e
        l.data.keyframe_insert('energy', frame=max(1, F(tt)))
    m, em = lib.emission_mat(name + 'Ball', '#FFC27A', 0)
    b = lib.sphere(2.5 * power, loc, m, 24, 12, name=name + 'Ball', coll=coll)
    for tt, s, e in ((t - 0.02, 0.05, 0), (t, 0.4, 60), (t + 0.25, 1.0, 25), (t + 0.9, 1.4, 0)):
        lib.key_value(em.inputs['Strength'], max(1, F(tt)), e)
        lib.key_obj(b, max(1, F(tt)), scale=(s, s, s * 0.8))
    return l

def tracer(a, b, t0, coll, m, dur=0.35, name='Tracer'):
    ob = lib.curve_poly(name, [[a, b]], bevel=0.035, mat_=m, res=1, coll=coll)
    ob.visible_shadow = False
    cu = ob.data
    F = lib.sec2f
    cu.bevel_factor_start = 0.0; cu.bevel_factor_end = 0.0
    cu.keyframe_insert('bevel_factor_start', frame=max(1, F(t0))); cu.keyframe_insert('bevel_factor_end', frame=max(1, F(t0)))
    cu.bevel_factor_end = 1.0; cu.keyframe_insert('bevel_factor_end', frame=F(t0 + dur * 0.6))
    cu.bevel_factor_start = 1.0; cu.keyframe_insert('bevel_factor_start', frame=F(t0 + dur))
    for fc in cu.animation_data.action.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = 'LINEAR'
    return ob

def rubble(coll, rng, area, n, m):
    for i in range(n):
        s = rng.uniform(0.2, 1.1)
        lib.box((s * rng.uniform(0.8, 2.2), s * rng.uniform(0.6, 1.4), s * rng.uniform(0.3, 0.9)),
                (rng.uniform(*area[0]), rng.uniform(*area[1]), 0.05), m,
                rot=(rng.uniform(-0.3, 0.3), rng.uniform(-0.3, 0.3), rng.uniform(0, 3.1)), bevel=0.03, name='Rubble', coll=coll)

def build(shot, fps=60):
    ev = shot.get('events', {})
    dur = shot['dur']
    variant = shot.get('variant', 'march')
    rng = random.Random(31)
    coll = lib.collection('Military')
    F = lib.sec2f
    if variant == 'march':
        sun_dir = Vector((-1.0, 0.45, 0.07))
        lib.world_sky_view_gradient('#46536A', '#E89A62', '#2A2520', strength=2.2, fog=0.0025, fog_col='#E8CBA8', aniso=0.6,
                                    glow_dir=sun_dir, glow_col='#FF9A50', glow_size=0.3, glow_strength=2.4)
        s = lib.light('SUN', (0, 0, 0), energy=3.4, color='#FFB27A', size=1.5, name='Sun', volume=1.8)
        s.rotation_euler = (-sun_dir).normalized().to_track_quat('-Z', 'Y').to_euler()
        ground = lib.mat('Steppe', '#5A4D3B', rough=0.96, var=0.3, var_scale=0.3, bump=0.5, bump_scale=4)
        lib.plane((800, 800), (0, 0, 0), ground, name='Ground', coll=coll)
        road = lib.mat('DirtRoad', '#6B5A45', rough=0.95, var=0.25, var_scale=1.2, bump=0.6, bump_scale=25)
        lib.plane((500, 9), (0, 0, 0.01), road, name='Road', coll=coll)
        # tanks parked in a line beside the road
        for i in range(6):
            tank((-34 + i * 11.5, 10.5, 0), math.radians(180 + rng.uniform(-5, 5)), coll, name=f'Tank{i}')
        # column of soldiers marching along the road (-x direction)
        k = 0
        for row in range(14):
            for col in range(4):
                x0 = -1 + row * 1.35 + rng.uniform(-0.08, 0.08)
                y0 = -2.1 + col * 1.25 + rng.uniform(-0.06, 0.06)
                p = soldier((x0, y0, 0), 0, rng, coll, 'march', name=f'S{k}')
                lib.walk(p, period=1.0, phase=0.0 if col % 2 == 0 else 0.05, swing=0.42)
                lib.move_root(p, [(x0, y0, 0), (x0 - 80, y0, 0)], t0=0, speed=1.45)
                k += 1
        # an army base and a town on the horizon, power line across the steppe
        import civ
        civ.power_line((-120, 75), (380, 75), coll, spacing=70)
        hang = lib.mat('Hangar', '#7A7466', rough=0.8, var=0.15, var_scale=0.5)
        for i in range(4):
            lib.cyl(11, 34, (110 + i * 28, 105 + i * 12, 0), hang, rot=(0, math.radians(90), math.radians(-35)), verts=32,
                    name='Hangar', coll=coll)
        lib.box((8, 8, 14), (215, 190, 0), hang, bevel=0.2, name='RadarTower', coll=coll, origin='bottom')
        lib.sphere(6, (215, 190, 19), lib.mat('Radome', '#D9D3C8', rough=0.5), 24, 16, name='Radome', coll=coll)
        civ.cell_tower((95, 70, 0), coll, h=45)
        civ.town((290, 300), coll, n=20, spread=(90, 40), seed=31)
        for i, (x, y) in enumerate(((150, 330), (210, 360), (110, 300))):
            civ.wind_turbine((x, y, 0), coll, rot=math.radians(-120), phase=i)
        civ.tree_line((60, 150), (240, 250), coll, n=22, seed=33)
        # dust in the low sun
        dust, _ = lib.fog_box((160, 60, 4), (0, 0, 2), density=0.006, color='#D8B48A', aniso=0.6, noise=0.8, noise_scale=0.12,
                              name='Dust')
        for i in range(3):
            smoke_column((rng.uniform(-80, 60), rng.uniform(80, 140), 0), h=40, r=6, density=0.25, color='#6A5C4E', coll=coll)
        cam = lib.camera((-6, -4.3, 0.6), (2, 0.5, 1.8), lens=24, dof=6.0, fstop=4.0)
        lib.animate_camera(cam, [(0, (-5.5, -4.4, 0.55)), (dur, (-7.0, -4.6, 0.7))],
                           [(0, (3, 0.5, 2.0)), (dur, (-2, 0.5, 1.9))], step=2, focus_keys=[(0, 6.0), (dur, 5.0)])
    else:  # battle over the new line
        lib.world_sky_view_gradient('#2E3540', '#8A4C2C', '#1C1814', strength=2.4, fog=0.004, fog_col='#C9B29A', aniso=0.5,
                                    glow_dir=(0.0, 1.0, 0.05), glow_col='#FF6A2A', glow_size=0.45, glow_strength=1.2)
        moon = lib.light('SUN', (0, 0, 0), energy=0.9, color='#8EA2BA', size=2.0, name='Moon')
        moon.rotation_euler = (math.radians(60), 0, math.radians(150))
        ground = lib.mat('Mud', '#3A322A', rough=0.9, var=0.35, var_scale=0.5, bump=0.7, bump_scale=3)
        lib.plane((600, 600), (0, 0, 0), ground, name='Ground', coll=coll)
        # the line: glowing red paint across the field (along x)
        line_m, line_em = lib.emission_mat('LineGlow', '#FF4A1E', 6.0)
        line = lib.box((300, 0.22, 0.02), (0, 0, 0.01), line_m, bevel=0, name='TheLine', coll=coll)
        lib.light('AREA', (0, 0, 0.3), (0, 0, 0), energy=0, color='#FF4A1E', size=1, name='LineLight', coll=coll)
        conc = lib.mat('BattleConcrete', '#6E675E', rough=0.92, var=0.2, var_scale=2, bump=0.4, bump_scale=10)
        rubble(coll, rng, ((-30, 30), (-6.5, -3.5)), 25, conc)
        rubble(coll, rng, ((-30, 30), (4, 18)), 40, conc)
        # ruined wall fragments as cover
        for x, y, w, h, r in ((-6, -5.5, 4, 1.6, 0.1), (5, -7, 3, 1.2, -0.2), (-3, 6.5, 5, 1.8, 0.05), (8, 5.5, 3, 1.3, 0.3),
                              (-14, -6, 3, 2.2, 0.0), (14, 7, 4, 2.0, 0.1)):
            lib.box((w, 0.4, h), (x, y, 0), conc, rot=(0, 0, r), bevel=0.04, name='Cover', coll=coll, origin='bottom')
        # two groups facing each other across the line
        k = 0
        for side, y0, head in ((-1, -4.5, math.pi), (1, 5.0, 0.0)):
            for i in range(12):
                x = -12 + i * 2.1 + rng.uniform(-0.5, 0.5)
                y = y0 + side * rng.uniform(0, 2.0)
                p = soldier((x, y, 0), head + rng.uniform(-0.25, 0.25), rng, coll, 'aim', name=f'B{k}')
                if i % 3 == 1:  # some advance slowly
                    lib.walk(p, period=1.3, phase=rng.uniform(0, 6), swing=0.25)
                    lib.move_root(p, [(x, y, 0), (x, y - side * 3.0, 0)], t0=rng.uniform(0, 0.6), speed=0.7)
                else:  # crouch a bit behind cover
                    p['root'].scale = (1.0, 1.0, 0.82)
                    lib.add_sine(p['torso'], 'rotation_euler', 0, 0.03, 2.0, rng.uniform(0, 6))
                k += 1
        # a ruined town behind the line, burned-out cars
        import civ
        civ.ruins((0, 78), coll, n=11, seed=8)
        lib.car((9, 19, 0), math.radians(30), '#2A2724', coll, lights=False, name='BurntCar1')
        lib.car((-13, 24, 0), math.radians(-70), '#2A2724', coll, lights=False, name='BurntCar2')
        civ.power_line((-200, 55), (200, 55), coll, spacing=80, h=22)
        # wrecked tank burning in the background
        wreck = tank((-18, 30, 0), math.radians(25), coll, name='Wreck', paint='#2E2C27', dust=0.4)
        wreck.rotation_euler = (math.radians(6), math.radians(-4), math.radians(25))
        fire((-17, 30, 1.6), coll, 1.3, seed=2, name='WreckFire')
        fire((22, 40, 0.5), coll, 1.0, seed=5, name='FieldFire')
        fire((6, -26, 0.4), coll, 0.6, seed=8, name='NearFire')
        for i, (x, y) in enumerate(((-18, 32), (22, 42), (40, 90), (-50, 80))):
            smoke_column((x, y, 1), h=45, r=4 + i, density=0.55, color='#2E2925', coll=coll, name=f'Smoke{i}')
        # explosions in the distance
        for i, t in enumerate(ev.get('blasts', [0.6, 1.9, 3.1])):
            if t < dur:
                flash((rng.uniform(-40, 40), rng.uniform(55, 110), 3), t, coll, power=rng.uniform(0.7, 1.2), name=f'Blast{i}')
        # tracers across the line
        tm, _ = lib.emission_mat('TracerGlow', '#FFB35A', 40.0)
        tt = 0.25
        i = 0
        while tt < dur:
            a = Vector((rng.uniform(-10, 12), -7 + rng.uniform(-1, 1), 1.3 + rng.uniform(-0.2, 0.3)))
            b = Vector((a.x + rng.uniform(-6, 6), 40, a.z + rng.uniform(-0.5, 2)))
            if i % 2:
                a, b = Vector((a.x, 8, a.z)), Vector((b.x, -40, b.z))
            tracer(a, b, tt, coll, tm, dur=0.4, name=f'Tr{i}')
            tt += rng.uniform(0.12, 0.35)
            i += 1
        cam = lib.camera((-1.0, -10.5, 2.0), (0.5, 4, 0.9), lens=26, dof=9.5, fstop=4.0)
        lib.animate_camera(cam, [(0, (-1.6, -10.8, 1.95)), (dur, (0.4, -9.8, 2.1))],
                           [(0, (0.0, 4, 0.95)), (dur, (1.2, 4, 0.85))], step=2, focus_keys=[(0, 10), (dur, 9.5)])
        # tiny handheld shake on blasts
        for t in ev.get('blasts', [0.6, 1.9, 3.1]):
            pass
    lib.bloom(strength=0.45, threshold=1.0, size=8)
    return dict(samples=56, fill=1.1, exposure=0.5)
