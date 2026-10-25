"""Border checkpoint: road, barrier gate, booth, canopy with sign, fence. Variants: lift (dawn), crowd, final."""
import bpy, math, random, os
from mathutils import Vector
import lib
from lib import C

FONTS = [r'C:\Windows\Fonts\arialbd.ttf', r'C:\Windows\Fonts\segoeuib.ttf']

def font_path():
    for f in FONTS:
        if os.path.exists(f):
            return f
    return None

def stripe_mat():
    m = bpy.data.materials.new('BarrierStripes')
    m.use_nodes = True
    nt = m.node_tree
    p = nt.nodes['Principled BSDF']
    L = nt.links
    tc = nt.nodes.new('ShaderNodeTexCoord')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ'); L.new(tc.outputs['Object'], sep.inputs[0])
    mul = nt.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'; mul.inputs[1].default_value = 1 / 0.9
    L.new(sep.outputs['X'], mul.inputs[0])
    fr = nt.nodes.new('ShaderNodeMath'); fr.operation = 'FRACT'; L.new(mul.outputs[0], fr.inputs[0])
    st = nt.nodes.new('ShaderNodeMath'); st.operation = 'GREATER_THAN'; st.inputs[1].default_value = 0.5
    L.new(fr.outputs[0], st.inputs[0])
    mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'
    L.new(st.outputs[0], mix.inputs['Factor'])
    mix.inputs['A'].default_value = C('#B8432A'); mix.inputs['B'].default_value = C('#E6DAC6')
    L.new(mix.outputs['Result'], p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = 0.42
    p.inputs['Coat Weight'].default_value = 0.25
    return m

def chainlink_mat():
    m = bpy.data.materials.new('ChainLink')
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    L = nt.links
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    pr = nt.nodes.new('ShaderNodeBsdfPrincipled')
    pr.inputs['Base Color'].default_value = C('#6E6C68'); pr.inputs['Metallic'].default_value = 0.9
    pr.inputs['Roughness'].default_value = 0.45
    tr = nt.nodes.new('ShaderNodeBsdfTransparent')
    mx = nt.nodes.new('ShaderNodeMixShader')
    tc = nt.nodes.new('ShaderNodeTexCoord')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ'); L.new(tc.outputs['Object'], sep.inputs[0])
    def band(sign):
        a = nt.nodes.new('ShaderNodeMath'); a.operation = 'MULTIPLY_ADD'; a.inputs[1].default_value = sign
        L.new(sep.outputs['X'], a.inputs[0]); L.new(sep.outputs['Z'], a.inputs[2])
        s = nt.nodes.new('ShaderNodeMath'); s.operation = 'MULTIPLY'; s.inputs[1].default_value = 1 / 0.06
        L.new(a.outputs[0], s.inputs[0])
        f = nt.nodes.new('ShaderNodeMath'); f.operation = 'PINGPONG'; f.inputs[1].default_value = 0.5
        L.new(s.outputs[0], f.inputs[0])
        g = nt.nodes.new('ShaderNodeMath'); g.operation = 'LESS_THAN'; g.inputs[1].default_value = 0.07
        L.new(f.outputs[0], g.inputs[0])
        return g
    b1, b2 = band(1.0), band(-1.0)
    mxm = nt.nodes.new('ShaderNodeMath'); mxm.operation = 'MAXIMUM'
    L.new(b1.outputs[0], mxm.inputs[0]); L.new(b2.outputs[0], mxm.inputs[1])
    L.new(mxm.outputs[0], mx.inputs['Fac'])
    L.new(tr.outputs[0], mx.inputs[1]); L.new(pr.outputs[0], mx.inputs[2])
    L.new(mx.outputs[0], out.inputs['Surface'])
    return m

def jersey(x, y, rot, m, coll):
    prof = [(-0.3, 0), (0.3, 0), (0.3, 0.08), (0.12, 0.3), (0.09, 0.81), (-0.09, 0.81), (-0.12, 0.3), (-0.3, 0.08)]
    bm_pts = prof
    ob = lib.poly_prism([(p[0], p[1]) for p in bm_pts], 3.0, (0, 0, 0), m, name='Jersey', bevel=0.015, coll=coll)
    # prism is extruded along z; rotate so length runs along y
    ob.rotation_euler = (math.radians(90), 0, rot)
    ob.location = (x, y + 1.5, 0)
    return ob

def build_set(rnd, coll, arm_angle=0.0, sign=True):
    road_m = lib.mat('Asphalt', '#2F2C29', rough=0.82, var=0.18, var_scale=0.9, bump=0.35, bump_scale=60)
    gravel_m = lib.mat('Gravel', '#4C463E', rough=0.95, var=0.25, var_scale=2, bump=0.6, bump_scale=40)
    grass_m = lib.mat('DryGround', '#4E4734', rough=0.97, var=0.3, var_scale=0.4, bump=0.4, bump_scale=6)
    paint_m = lib.mat('Paint', '#D8CCB6', rough=0.55, var=0.12, var_scale=8)
    lib.plane((600, 700), (0, 150, -0.02), grass_m, name='Ground', coll=coll)
    lib.plane((9.0, 520), (0, 200, 0.0), road_m, name='Road', coll=coll)
    for sx in (-1, 1):
        lib.plane((2.6, 520), (sx * 5.8, 200, -0.005), gravel_m, name='Shoulder', coll=coll)
        lib.box((0.14, 520, 0.004), (sx * 4.2, 200, 0.004), paint_m, bevel=0, name='EdgeLine', coll=coll)
    for k in range(-6, 50):
        y = k * 9.0
        if -6 < y < 6:
            continue
        lib.box((0.14, 3.0, 0.004), (0, y, 0.004), paint_m, bevel=0, name='Dash', coll=coll)
    lib.box((8.4, 0.45, 0.004), (0, -3.2, 0.004), paint_m, bevel=0, name='StopLine', coll=coll)
    conc = lib.mat('CpConcrete', '#A49B8D', rough=0.9, var=0.15, var_scale=2.5, bump=0.25, bump_scale=12)
    steel = lib.mat('CpSteel', '#4A4C4D', rough=0.5, metal=0.7, var=0.15, var_scale=5)
    panel = lib.mat('BoothPanel', '#CFC4B2', rough=0.6, var=0.06, var_scale=3)
    dark = lib.mat('Trim', '#262422', rough=0.6)
    # canopy
    for x in (-6.4, 6.4):
        for y in (-4.2, 4.2):
            lib.box((0.55, 0.55, 5.6), (x, y, 0), conc, bevel=0.03, name='Column', coll=coll, origin='bottom')
    lib.box((14.6, 10.4, 0.7), (0, 0, 5.6), panel, bevel=0.04, name='CanopyRoof', coll=coll, origin='bottom')
    lib.box((14.8, 0.35, 1.0), (0, -5.25, 5.45), dark, bevel=0.02, name='Fascia', coll=coll, origin='bottom')
    down_m, down_em = lib.emission_mat('Downlight', '#FFE2B8', 6.0)
    for x in (-4, 0, 4):
        for y in (-2.6, 2.6):
            lib.box((1.6, 0.4, 0.03), (x, y, 5.585), down_m, bevel=0, name='Panel', coll=coll)
            lib.light('AREA', (x, y, 5.5), (0, 0, 0), energy=650, color='#FFE0B5', size=1.2, name='CanopyLight', coll=coll)
    if sign:
        sign_m, sign_em = lib.emission_mat('SignGlow', '#FFC07A', 3.2)
        t = lib.text_obj('ПАСПОРТНЫЙ КОНТРОЛЬ', size=0.58, loc=(0, -5.44, 5.95), rot=(math.radians(90), 0, 0),
                         mat_=sign_m, font=font_path(), extrude=0.01, name='Sign', coll=coll)
    # booth
    bx, by = 7.6, -1.0
    lib.box((2.8, 3.4, 0.25), (bx, by, 0), conc, bevel=0.03, name='BoothBase', coll=coll, origin='bottom')
    lib.box((2.6, 3.2, 2.7), (bx, by, 0.25), panel, bevel=0.04, name='Booth', coll=coll, origin='bottom')
    win_m, win_em = lib.emission_mat('BoothWindow', '#FFB868', 2.6)
    lib.box((0.03, 2.4, 1.1), (bx - 1.31, by, 1.75), win_m, bevel=0, name='BoothWin', coll=coll)
    lib.box((2.0, 0.03, 1.1), (bx, by - 1.61, 1.75), win_m, bevel=0, name='BoothWin2', coll=coll)
    lib.box((3.0, 3.6, 0.18), (bx, by, 2.95), dark, bevel=0.02, name='BoothRoof', coll=coll, origin='bottom')
    lib.light('POINT', (bx - 0.4, by, 2.3), energy=180, color='#FFB060', size=0.4, name='BoothLamp', coll=coll)
    # barrier gate (pivot on the left side)
    post = lib.box((0.42, 0.42, 1.15), (-5.3, 0, 0), dark, bevel=0.03, name='GatePost', coll=coll, origin='bottom')
    pivot = lib.empty('GatePivot', (-5.3, 0, 1.08), (0, -arm_angle, 0), coll=coll)
    arm = lib.box((9.4, 0.13, 0.13), (4.95, 0, 0), stripe_mat(), bevel=0.03, name='GateArm', coll=coll)
    arm.parent = pivot
    cw = lib.box((0.55, 0.26, 0.34), (-0.55, 0, 0), dark, bevel=0.03, name='Counterweight', coll=coll)
    cw.parent = pivot
    lamp_m, lamp_em = lib.emission_mat('GateLamp', '#FF5A2A', 4.0)
    lmp = lib.sphere(0.06, (9.3, 0, 0.1), lamp_m, 12, 8, name='ArmLamp', coll=coll)
    lmp.parent = pivot
    lib.box((0.3, 0.3, 0.9), (4.7, 0, 0), dark, bevel=0.02, name='ArmRest', coll=coll, origin='bottom')
    # jersey barriers lining the approach
    for sx in (-1, 1):
        for k in range(5):
            jersey(sx * 4.9, -38 + k * 3.2, 0, conc, coll)
    # fence with wire on both sides
    fence_m = chainlink_mat()
    for sx in (-1, 1):
        x0, x1 = sx * 9.0, sx * 140.0
        cx = (x0 + x1) / 2
        f = lib.plane((abs(x1 - x0), 3.0), (cx, 0.0, 1.5), fence_m, rot=(math.radians(90), 0, 0), name='Fence', coll=coll)
        f.visible_shadow = True
        for x in range(9, 141, 3):
            lib.cyl(0.04, 3.4, (sx * x, 0, 0), steel, verts=10, name='FPost', coll=coll, origin='bottom')
        for z in (3.25, 3.45, 3.65):
            lib.curve_poly('Barb', [[(x0, 0, z), (x1, 0, z)]], bevel=0.008, mat_=steel, coll=coll)
    # floodlight masts
    fl_m, _ = lib.emission_mat('Flood', '#FFE9C8', 12.0)
    for sx in (-1, 1):
        x, y = sx * 10.5, -9.0
        lib.cyl(0.13, 11, (x, y, 0), steel, verts=12, name='Mast', coll=coll, origin='bottom')
        lib.box((1.4, 0.3, 0.5), (x, y, 11.0), steel, bevel=0.02, name='FloodHead', coll=coll)
        lib.box((1.2, 0.02, 0.36), (x, y + 0.16, 11.0), fl_m, bevel=0, name='FloodLens', coll=coll)
    # distant tree line / hills
    # signs of civilisation behind the checkpoint: town skyline, power line, turbines, roadside life
    import civ
    civ.town((0, 330), coll, n=26, spread=(170, 40), seed=3)
    civ.town((-250, 270), coll, n=10, spread=(60, 30), hmax=30, seed=5)
    civ.power_line((-280, 140), (280, 140), coll, spacing=70)
    for i, (x, y) in enumerate(((-150, 420), (-95, 445), (150, 430), (205, 470))):
        civ.wind_turbine((x, y, 0), coll, rot=math.radians(-90), phase=i * 1.3)
    civ.cell_tower((-30, 60, 0), coll)
    civ.water_tower((62, 165, 0), coll)
    civ.gas_station((28, 72, 0), math.radians(-90), coll)
    civ.truck((-17, 46, 0), math.radians(90), coll)
    civ.truck((-17, 64, 0), math.radians(90), coll, color='#2F3B45', name='Truck2')
    civ.billboard((-15, 28, 0), 0.0, coll)
    civ.tree_line((-11.5, 95), (-11.5, 250), coll, n=18, seed=11)
    civ.tree_line((12.5, 105), (12.5, 260), coll, n=18, seed=12)
    hill_m = lib.mat('FarHills', '#2A2520', rough=1.0)
    for i in range(22):
        lib.sphere(rnd.uniform(18, 40), (rnd.uniform(-260, 260), rnd.uniform(220, 320), -rnd.uniform(10, 20)), hill_m, 32, 16,
                   scale=(2.6, 1.0, 0.5), name='Hill', coll=coll)
    return pivot, down_em, win_em

def sky_dawn(sun_dir, fog=0.016):
    lib.world_sky_view_gradient('#46536A', '#F0A874', '#2A2622', strength=2.4, fog=fog * 0.22, fog_col='#D8D2CA', aniso=0.55,
                                glow_dir=sun_dir, glow_col='#FF9A50', glow_size=0.22, glow_strength=3.0)

def sun_light(sun_dir, energy=4.5, color='#FFB27A', angle=1.2):
    s = lib.light('SUN', (0, 0, 0), energy=energy, color=color, size=angle, name='Sun', volume=1.6)
    s.rotation_euler = (-Vector(sun_dir)).normalized().to_track_quat('-Z', 'Y').to_euler()
    # sun disc
    m, _ = lib.emission_mat('SunDisc', '#FFB878', 14.0)
    d = Vector(sun_dir).normalized() * 600
    lib.sphere(9, tuple(d), m, 32, 16, name='SunDisc')
    return s

def build(shot, fps=60):
    ev = shot.get('events', {})
    dur = shot['dur']
    variant = shot.get('variant', 'lift')
    rnd = random.Random(5)
    coll = lib.collection('Checkpoint')
    F = lib.sec2f
    f_end = int(round(dur * fps))
    if variant == 'lift':
        sun_dir = Vector((0.22, 1.0, 0.075))
        sky_dawn(sun_dir, fog=0.018)
        sun_light(sun_dir, energy=3.0)
        pivot, down_em, win_em = build_set(rnd, coll, 0.0)
        t = ev.get('lift', 0.6)
        rc = random.Random(77)
        # cars waiting on the far side of the gate; the first one rolls out once the arm is up
        c1 = lib.car((-2.0, 6.5, 0), -math.pi / 2, '#8A2E25', coll, rng=rc, name='CarA')
        lib.car((-2.0, 13.0, 0), -math.pi / 2, '#C9C1B2', coll, kind='van', rng=rc, name='CarB')
        lib.car((-2.1, 19.5, 0), -math.pi / 2, '#2F3B45', coll, rng=rc, name='CarC')
        lib.drive(c1, [(-2.0, 6.5, 0), (-2.0, -40, 0)], t0=t + 1.25, speed=5.0, accel=2.2)
        # a few travellers with bags waiting by the booth
        for i, (x, y) in enumerate(((4.7, -3.6), (5.3, -2.7), (4.4, -5.0))):
            p = lib.person((x, y, 0), -math.pi / 2 + rc.uniform(-0.3, 0.3), height=rc.uniform(0.94, 1.05), rng=rc, coll=coll,
                           bag=True, name=f'Trav{i}')
            lib.add_sine(p['torso'], 'rotation_euler', 1, 0.03, 2.4, rc.uniform(0, 6))
            lib.add_sine(p['head'], 'rotation_euler', 2, 0.15, 3.1, rc.uniform(0, 6))
        lib.key_obj(pivot, 1, rot=(0, 0, 0))
        lib.key_obj(pivot, F(t), rot=(0, 0, 0))
        lib.key_obj(pivot, F(t + 1.7), rot=(0, -math.radians(84), 0))
        # ease-out with tiny settle
        cam = lib.camera((1.6, -16, 1.25), (0, 0, 1.3), lens=32, dof=15.0, fstop=3.2)
        lib.animate_camera(cam, [(0, (1.8, -16.5, 1.15)), (dur, (1.2, -12.5, 1.35))],
                           [(0, (-0.4, 0, 1.9)), (dur, (0.0, 0, 2.6))], step=2, focus_keys=[(0, 16.5), (dur, 12.6)])
        cam.data.shift_y = 0.04
    elif variant == 'crowd':
        sun_dir = Vector((-0.25, 1.0, 0.07))
        sky_dawn(sun_dir, fog=0.014)
        sun_light(sun_dir, energy=3.6, color='#FFC08A')
        pivot, down_em, win_em = build_set(rnd, coll, math.radians(84))
        n = shot.get('people', 70)
        prs = random.Random(17)
        for i in range(n):
            lane_x = prs.uniform(-3.6, 3.6)
            y0 = prs.uniform(-34, -6)
            speed = prs.uniform(1.05, 1.5)
            p = lib.person((lane_x, y0, 0), 0, height=prs.uniform(0.92, 1.08), rng=prs, coll=coll, bag=prs.random() < 0.55,
                           name=f'P{i}')
            lib.walk(p, period=prs.uniform(0.95, 1.15), phase=prs.uniform(0, 6.28), swing=0.45)
            lib.move_root(p, [(lane_x, y0, 0), (lane_x + prs.uniform(-1, 1), y0 + 80, 0)], t0=-prs.uniform(0, 0.5), speed=speed)
        cam = lib.camera((2.5, -46, 6.5), (0, 0, 1.2), lens=35, dof=30.0, fstop=5.6)
        lib.animate_camera(cam, [(0, (3.0, -47, 6.8)), (dur, (1.2, -40, 5.6))],
                           [(0, (0, -6, 1.0)), (dur, (0, 2, 1.4))], step=2, focus_keys=[(0, 34), (dur, 32)])
        cam.data.shift_y = 0.0
    else:  # final
        sun_dir = Vector((0.1, 1.0, 0.09))
        sky_dawn(sun_dir, fog=0.02)
        sun_light(sun_dir, energy=3.4, color='#FFC490')
        pivot, down_em, win_em = build_set(rnd, coll, math.radians(48))
        lib.key_value(down_em.inputs['Strength'], 1, 2.0)
        rc = random.Random(88)
        # an open border at sunrise: a few people walk through, one car drives away
        for i in range(6):
            x0 = rc.uniform(-3.2, 3.2); y0 = rc.uniform(-8.5, -2.5)
            p = lib.person((x0, y0, 0), 0, height=rc.uniform(0.93, 1.06), rng=rc, coll=coll, bag=rc.random() < 0.7, name=f'Walker{i}')
            lib.walk(p, period=rc.uniform(1.0, 1.2), phase=rc.uniform(0, 6.28), swing=0.42)
            lib.move_root(p, [(x0, y0, 0), (x0 + rc.uniform(-0.8, 0.8), y0 + 40, 0)], t0=rc.uniform(0, 1.5), speed=rc.uniform(1.0, 1.3))
        cr = lib.car((2.2, -9.0, 0), math.pi / 2, '#2F3B45', coll, rng=rc, name='CarOut')
        lib.drive(cr, [(2.2, -9.0, 0), (2.2, 120, 0)], t0=2.0, speed=6.0, accel=1.6)
        cam = lib.camera((0.8, -15, 1.3), (0, 30, 2.0), lens=30, dof=16.0, fstop=4.0)
        lib.animate_camera(cam, [(0, (1.0, -16, 1.3)), (dur, (0.4, -12, 5.2))],
                           [(0, (0, 0, 2.2)), (dur, (0, 40, 1.2))], step=2, focus_keys=[(0, 16), (dur, 13)])
    lib.bloom(strength=0.38, threshold=1.0, size=8)
    return dict(samples=56, fill=1.2, exposure=0.45)
