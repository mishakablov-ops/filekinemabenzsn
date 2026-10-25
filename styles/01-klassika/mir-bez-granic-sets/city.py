"""Megacity at dusk. Variants: grow (aerial, buildings rise + windows light up + cranes), crush (packed street)."""
import bpy, math, random
from mathutils import Vector
import lib
from lib import C

def facade_mat(name, base, glow='#FFC58A'):
    """Procedural windows on axis-aligned boxes. Returns (material, Value node = fraction of lit windows, animatable)."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    lit_val = nt.nodes.new('ShaderNodeValue'); lit_val.name = 'Lit'; lit_val.outputs[0].default_value = 0.35
    p = nt.nodes['Principled BSDF']
    L = nt.links
    tc = nt.nodes.new('ShaderNodeTexCoord')
    oi = nt.nodes.new('ShaderNodeObjectInfo')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ'); L.new(tc.outputs['Object'], sep.inputs[0])
    uu = nt.nodes.new('ShaderNodeMath'); uu.operation = 'ADD'
    L.new(sep.outputs['X'], uu.inputs[0]); L.new(sep.outputs['Y'], uu.inputs[1])
    def scaled(sock, k):
        n = nt.nodes.new('ShaderNodeMath'); n.operation = 'MULTIPLY'; n.inputs[1].default_value = k
        L.new(sock, n.inputs[0]); return n.outputs[0]
    us, vs = scaled(uu.outputs[0], 1 / 3.2), scaled(sep.outputs['Z'], 1 / 3.4)
    def fract(sock):
        n = nt.nodes.new('ShaderNodeMath'); n.operation = 'FRACT'; L.new(sock, n.inputs[0]); return n.outputs[0]
    def floor(sock):
        n = nt.nodes.new('ShaderNodeMath'); n.operation = 'FLOOR'; L.new(sock, n.inputs[0]); return n.outputs[0]
    def band(sock, a, b):
        g1 = nt.nodes.new('ShaderNodeMath'); g1.operation = 'GREATER_THAN'; g1.inputs[1].default_value = a; L.new(sock, g1.inputs[0])
        g2 = nt.nodes.new('ShaderNodeMath'); g2.operation = 'LESS_THAN'; g2.inputs[1].default_value = b; L.new(sock, g2.inputs[0])
        mm = nt.nodes.new('ShaderNodeMath'); mm.operation = 'MULTIPLY'; L.new(g1.outputs[0], mm.inputs[0]); L.new(g2.outputs[0], mm.inputs[1])
        return mm.outputs[0]
    win = nt.nodes.new('ShaderNodeMath'); win.operation = 'MULTIPLY'
    L.new(band(fract(us), 0.16, 0.84), win.inputs[0]); L.new(band(fract(vs), 0.22, 0.78), win.inputs[1])
    # no windows on roofs
    geo = nt.nodes.new('ShaderNodeNewGeometry')
    sn = nt.nodes.new('ShaderNodeSeparateXYZ'); L.new(geo.outputs['Normal'], sn.inputs[0])
    wall = nt.nodes.new('ShaderNodeMath'); wall.operation = 'LESS_THAN'; wall.inputs[1].default_value = 0.5
    L.new(sn.outputs['Z'], wall.inputs[0])
    winw = nt.nodes.new('ShaderNodeMath'); winw.operation = 'MULTIPLY'
    L.new(win.outputs[0], winw.inputs[0]); L.new(wall.outputs[0], winw.inputs[1])
    cell = nt.nodes.new('ShaderNodeCombineXYZ')
    L.new(floor(us), cell.inputs['X']); L.new(floor(vs), cell.inputs['Y'])
    rs = nt.nodes.new('ShaderNodeMath'); rs.operation = 'MULTIPLY'; rs.inputs[1].default_value = 97.0
    L.new(oi.outputs['Random'], rs.inputs[0]); L.new(rs.outputs[0], cell.inputs['Z'])
    wn = nt.nodes.new('ShaderNodeTexWhiteNoise'); wn.noise_dimensions = '3D'
    L.new(cell.outputs[0], wn.inputs['Vector'])
    lit = nt.nodes.new('ShaderNodeMath'); lit.operation = 'LESS_THAN'
    L.new(wn.outputs['Value'], lit.inputs[0]); L.new(lit_val.outputs[0], lit.inputs[1])
    em = nt.nodes.new('ShaderNodeMath'); em.operation = 'MULTIPLY'
    L.new(winw.outputs[0], em.inputs[0]); L.new(lit.outputs[0], em.inputs[1])
    # warm/cool variation of lit windows
    wcol = nt.nodes.new('ShaderNodeMix'); wcol.data_type = 'RGBA'
    L.new(wn.outputs['Color'], wcol.inputs['Factor'])
    wcol.inputs['A'].default_value = C(glow); wcol.inputs['B'].default_value = C('#FFE2B8')
    L.new(wcol.outputs['Result'], p.inputs['Emission Color'])
    es = nt.nodes.new('ShaderNodeMath'); es.operation = 'MULTIPLY'; es.inputs[1].default_value = 4.0
    L.new(em.outputs[0], es.inputs[0]); L.new(es.outputs[0], p.inputs['Emission Strength'])
    # base: concrete tone per building, dark glass in windows
    tone = nt.nodes.new('ShaderNodeValToRGB')
    tone.color_ramp.elements[0].color = C(base); tone.color_ramp.elements[1].color = C('#8A8076')
    e = tone.color_ramp.elements.new(0.5); e.color = C('#5E5750')
    L.new(oi.outputs['Random'], tone.inputs['Fac'])
    bc = nt.nodes.new('ShaderNodeMix'); bc.data_type = 'RGBA'
    L.new(winw.outputs[0], bc.inputs['Factor']); L.new(tone.outputs['Color'], bc.inputs['A']); bc.inputs['B'].default_value = C('#1C1E21')
    L.new(bc.outputs['Result'], p.inputs['Base Color'])
    rr = nt.nodes.new('ShaderNodeMapRange'); rr.inputs['To Min'].default_value = 0.85; rr.inputs['To Max'].default_value = 0.18
    L.new(winw.outputs[0], rr.inputs['Value']); L.new(rr.outputs['Result'], p.inputs['Roughness'])
    return m, lit_val

def crane(x, y, h, coll, m, rng):
    root = lib.empty('Crane', (x, y, 0), (0, 0, rng.uniform(0, 6.28)), coll=coll)
    mast = lib.box((1.6, 1.6, h), (0, 0, 0), m, bevel=0, name='Mast', coll=coll, origin='bottom'); mast.parent = root
    jib = lib.empty('Jib', (0, 0, h), coll=coll); jib.parent = root
    for o in (lib.box((34, 1.2, 1.2), (10, 0, 0.6), m, bevel=0, name='JibArm', coll=coll),
              lib.box((4, 3, 2.5), (-7, 0, 1.0), m, bevel=0, name='Counter', coll=coll),
              lib.box((2.2, 2.2, 3), (0, 0, 1.5), m, bevel=0, name='Cab', coll=coll)):
        o.parent = jib
    lmp, _ = lib.emission_mat('CraneLamp', '#FF3A2A', 20)
    tip = lib.sphere(0.5, (27, 0, 1.4), lmp, 8, 6, name='CraneTip', coll=coll); tip.parent = jib
    lib.add_sine(jib, 'rotation_euler', 2, 0.35, 9.0, rng.uniform(0, 6))
    return root

def build(shot, fps=60):
    ev = shot.get('events', {})
    dur = shot['dur']
    variant = shot.get('variant', 'grow')
    rng = random.Random(41)
    coll = lib.collection('City')
    lib.FOG_BOX = (2200.0, 2200.0, 160.0)
    F = lib.sec2f
    sun_dir = Vector((-0.6, 1.0, 0.1))
    lib.world_sky_view_gradient('#3E4656', '#EE9C66', '#2A2622', strength=2.2, fog=0.0025 if variant == 'grow' else 0.008,
                                fog_col='#E6CDB2', aniso=0.5, glow_dir=sun_dir, glow_col='#FF9A55', glow_size=0.35, glow_strength=2.2)
    s = lib.light('SUN', (0, 0, 0), energy=3.6, color='#FFC08A', size=1.0, name='Sun', volume=1.0)
    s.rotation_euler = (-sun_dir).normalized().to_track_quat('-Z', 'Y').to_euler()
    lit = None
    ground_m = lib.mat('CityGround', '#3A3734', rough=0.85, var=0.15, var_scale=0.2)
    lib.plane((2000, 2000), (0, 0, 0), ground_m, name='Ground', coll=coll)
    side_m = lib.mat('Sidewalk', '#6E665C', rough=0.9, var=0.1, var_scale=3)
    mats, lit_vals = [], []
    for i, base in enumerate(['#5A5550', '#6A625A', '#4E4B48']):
        m, v = facade_mat(f'Facade{i}', base)
        mats.append(m); lit_vals.append(v)
    block, street = 44.0, 16.0
    n = 6
    blds = []
    for bi in range(-n, n + 1):
        for bj in range(-n, n + 1):
            cx, cy = bi * (block + street), bj * (block + street)
            lib.box((block + 3, block + 3, 0.18), (cx, cy, 0), side_m, bevel=0, name='Block', coll=coll, origin='bottom')
            dc = math.hypot(cx, cy) / ((block + street) * n)
            hmax = lib.lerp(150, 26, min(1, dc))
            parts = rng.choice([1, 2, 2, 4])
            if parts == 1:
                rects = [(cx, cy, block - 4, block - 4)]
            elif parts == 2:
                rects = [(cx - block / 4, cy, block / 2 - 3, block - 4), (cx + block / 4, cy, block / 2 - 3, block - 4)]
            else:
                q = block / 4
                rects = [(cx + sx * q, cy + sy * q, block / 2 - 3, block / 2 - 3) for sx in (-1, 1) for sy in (-1, 1)]
            for (x, y, w, d) in rects:
                h = max(10, rng.lognormvariate(math.log(hmax * 0.55), 0.45))
                h = min(h, hmax * 1.3)
                m = rng.choice(mats)
                b = lib.box((w, d, h), (x, y, 0.18), m, bevel=0.3, name='Bld', coll=coll, origin='bottom')
                blds.append((b, h))
                if h > 70 and rng.random() < 0.5:
                    lib.box((w * 0.6, d * 0.6, h * 0.25), (x, y, 0.18 + h), m, bevel=0.3, name='BldTop', coll=coll, origin='bottom')
    steel = lib.mat('CraneSteel', '#C88A3A', rough=0.6, metal=0.3)
    if variant == 'grow':
        # new towers rise from the ground (economy doubles), windows switch on over time
        t0 = ev.get('grow', 0.4)
        rising = rng.sample(blds, min(70, len(blds)))
        for k, (b, h) in enumerate(rising):
            st = t0 + rng.uniform(0, max(0.5, dur - 2.2))
            lib.key_obj(b, 1, loc=(b.location.x, b.location.y, -h - 1))
            lib.key_obj(b, F(st), loc=(b.location.x, b.location.y, -h - 1))
            lib.key_obj(b, F(st + 1.6), loc=(b.location.x, b.location.y, 0.18))
        for v in lit_vals:
            lib.key_value(v.outputs[0], 1, 0.15)
            lib.key_value(v.outputs[0], F(dur), 0.7)
        for i in range(7):
            crane(rng.uniform(-200, 200), rng.uniform(-200, 200), rng.uniform(70, 120), coll, steel, rng)
        # traffic light trails on the avenues
        head_m, _ = lib.emission_mat('Head', '#FFE6C0', 16)
        tail_m, _ = lib.emission_mat('Tail', '#FF3A22', 12)
        for i in range(240):
            lane = rng.randint(-n, n - 1)
            y = lane * (block + street) + (block + street) / 2 + rng.choice([-3, 3])
            x0 = rng.uniform(-400, 400)
            sp = rng.uniform(14, 22) * rng.choice([-1, 1])
            if i % 2:
                car = lib.box((4.2, 1.8, 1.4), (x0, y, 0.8), head_m if sp > 0 else tail_m, bevel=0, name='Car', coll=coll)
                lib.key_obj(car, 1, loc=(x0, y, 0.8), interp='LINEAR')
                lib.key_obj(car, F(dur), loc=(x0 + sp * dur, y, 0.8), interp='LINEAR')
            else:
                car = lib.box((1.8, 4.2, 1.4), (y, x0, 0.8), head_m if sp > 0 else tail_m, bevel=0, name='Car', coll=coll)
                lib.key_obj(car, 1, loc=(y, x0, 0.8), interp='LINEAR')
                lib.key_obj(car, F(dur), loc=(y, x0 + sp * dur, 0.8), interp='LINEAR')
        lampm, _ = lib.emission_mat('AvenueLamp', '#FFD7A0', 14)
        for lane in range(-n, n):
            yy = lane * (block + street) + (block + street) / 2
            for x in range(-380, 381, 26):
                for sy in (-1, 1):
                    lib.sphere(0.5, (x, yy + sy * 7.2, 8.0), lampm, 8, 6, name='AvLamp', coll=coll)
                    lib.sphere(0.5, (yy + sy * 7.2, x, 8.0), lampm, 8, 6, name='AvLamp', coll=coll)
        cam = lib.camera((-260, -300, 210), (0, 0, 30), lens=40, dof=None)
        lib.animate_camera(cam, [(0, (-250, -310, 200)), (dur, (-170, -330, 170))],
                           [(0, (0, 0, 40)), (dur, (20, 0, 50))], step=2)
        cam.data.shift_y = 0.1
    else:  # crush: dense crowd in a street canyon
        for v in lit_vals:
            v.outputs[0].default_value = 0.6
        shop_m, _ = lib.emission_mat('Shop', '#FFC07A', 3.0)
        y_st = (block + street) / 2  # street centre between rows of blocks
        for x in range(-60, 61, 9):
            for sy in (-1, 1):
                lib.box((6.5, 0.1, 3.0), (x, y_st + sy * (street / 2 + 1.55), 1.8), shop_m, bevel=0, name='ShopWin', coll=coll)
        prs = random.Random(9)
        for i in range(shot.get('people', 170)):
            x = prs.uniform(-40, 40)
            yy = y_st + prs.uniform(-6.0, 6.0)
            dirx = prs.choice([-1, 1])
            p = lib.person((x, yy, 0.0), 0, height=prs.uniform(0.92, 1.08), rng=prs, coll=coll, bag=prs.random() < 0.3, name=f'C{i}')
            lib.walk(p, period=prs.uniform(0.95, 1.2), phase=prs.uniform(0, 6.28), swing=0.4)
            lib.move_root(p, [(x, yy, 0), (x + dirx * 40, yy + prs.uniform(-1.5, 1.5), 0)], t0=0, speed=prs.uniform(0.9, 1.4))
        # street lights
        lamp_m, _ = lib.emission_mat('StreetLamp', '#FFD9A8', 20)
        for x in range(-60, 61, 15):
            for sy in (-1, 1):
                lib.cyl(0.1, 6, (x, y_st + sy * 7.8, 0), lib.mat('LampPole', '#2B2A28', rough=0.5, metal=0.5), verts=10,
                        name='LampPole', coll=coll, origin='bottom')
                lib.sphere(0.3, (x, y_st + sy * 7.4, 6.0), lamp_m, 12, 8, name='LampBall', coll=coll)
                lib.light('POINT', (x, y_st + sy * 7.4, 5.8), energy=900, color='#FFC890', size=0.4, name='StreetL', coll=coll)
        cam = lib.camera((-30, y_st - 2.0, 1.75), (10, y_st, 1.4), lens=70, dof=24.0, fstop=3.2)
        lib.animate_camera(cam, [(0, (-32, y_st - 2.2, 1.75)), (dur, (-29, y_st - 1.8, 1.8))],
                           [(0, (10, y_st + 0.5, 1.4)), (dur, (10, y_st - 0.5, 1.5))], step=2, focus_keys=[(0, 22), (dur, 21)])
    lib.bloom(strength=0.35, threshold=1.2, size=8)
    return dict(samples=48, fill=1.0, exposure=0.45)
