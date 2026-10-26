"""The empty city in real colours (posledniy-chelovek-blender).
Variants: wake (empty street, morning), you (the hero alone among stopped cars), car (the hero points at a car),
blackout (aerial at blue hour, the lights die block by block, clip), night (no lights, Milky Way, tilt up, clip),
third (Milky Way over the roofs), wolves (a year later: grass on the road, three wolves trot to camera, clip),
fuel (an empty petrol station), chernobyl (Pripyat: the Ferris wheel, birches, a wolf).
Street along +Y: road |x| < 7, sidewalks 7..11, buildings from |x| = 11.
"""
import bpy, math, random
from mathutils import Vector
import lib
from lib import C
import pcommon as pc

ROAD, SW = 7.0, 4.0
BX = ROAD + SW
CROSS = (64.0, 190.0)
GREENS = ['#4C7436', '#5B8540', '#3E6530', '#6A8F45']
F = lib.sec2f


# ----------------------------------------------------------------------------- vegetation
def tree(x, y, coll, rng, h=8.0, greens=GREENS, wild=1.0, birch=False):
    bark = lib.mat('BirchBark' if birch else 'Bark', '#E6E1D6' if birch else '#58483B', rough=0.9,
                   var=0.45 if birch else 0.2, var_scale=14 if birch else 8)
    lib.cyl(0.17 * h / 8, h * 0.6, (x, y, 0), bark, verts=8, r2=0.1 * h / 8, name='Trunk', coll=coll, origin='bottom')
    for k in range(rng.randint(3, 5)):
        g = rng.choice(greens)
        lm = lib.mat('Leaf' + g, g, rough=0.85, var=0.35, var_scale=2.5, bump=0.5, bump_scale=7)
        r = h * rng.uniform(0.17, 0.25) * wild
        lib.sphere(r, (x + rng.uniform(-0.3, 0.3) * h * 0.28, y + rng.uniform(-0.3, 0.3) * h * 0.28, h * rng.uniform(0.62, 0.86)),
                   lm, 10, 8, scale=(1, 1, rng.uniform(0.75, 1.0)), name='Crown', coll=coll)


def tufts(coll, rng, n, area, h=(0.15, 0.45), cols=('#5F7F35', '#728F3D', '#4E6B2E', '#8A8F48'), name='Tuft'):
    """Grass tufts: clusters of thin cones."""
    (x0, x1), (y0, y1) = area
    for i in range(n):
        x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
        c = rng.choice(cols)
        m = lib.mat('Grass' + c, c, rough=0.9, var=0.25, var_scale=6)
        for k in range(rng.randint(2, 4)):
            hh = rng.uniform(*h)
            lib.cyl(0.022 * hh / 0.3 + 0.008, hh, (x + rng.uniform(-0.12, 0.12), y + rng.uniform(-0.12, 0.12), 0),
                    m, rot=(rng.uniform(-0.25, 0.25), rng.uniform(-0.25, 0.25), 0), verts=5, r2=0.0, name=name, coll=coll,
                    origin='bottom')


# ----------------------------------------------------------------------------- street
def facade_set(lit=0.0, prefix='F'):
    sets = [('#DAD5CA', '#C9C4B9', '#B8BAB6'), ('#A9604A', '#9B5D49', '#B87158'), ('#E2D4A8', '#D9CBB1', '#CBBBA2'),
            ('#CBCED1', '#A1A9B0', '#D8D2C6')]
    out = []
    for i, cols in enumerate(sets):
        out.append(pc.facade(f'{prefix}{i}', cols=cols, lit=lit))
    return out


SIGNS = ['ПРОДУКТЫ', 'АПТЕКА', 'КАФЕ', 'ЦВЕТЫ', 'ХЛЕБ', 'ОПТИКА', 'КНИГИ', 'МАРКЕТ', 'ОБУВЬ', 'СВЯЗЬ']


def street(coll, rng, lit=0.0, y0=-60.0, y1=430.0, shop_glow=0.0, lamp_glow=0.0, overgrown=0.0, signs=True):
    """Builds the street. Returns dict(facades=[(mat, lit, out)], lamps=[strength sockets], shops=[...])."""
    if overgrown:
        ground = overgrown_asphalt(overgrown)
    else:
        ground = lib.mat('Asphalt', '#5A5C5F', rough=0.86, var=0.16, var_scale=0.4, bump=0.12, bump_scale=40)
    lib.plane((3000, 3000), (0, 0, 0), ground, name='Ground', coll=coll)
    walk = lib.mat('Sidewalk', '#A39E95', rough=0.9, var=0.14, var_scale=1.5, bump=0.1, bump_scale=20)
    curb = lib.mat('Curb', '#BDB9B0', rough=0.85, var=0.1, var_scale=3)
    line = lib.mat('RoadLine', '#E7E5DF', rough=0.6, var=0.2 if overgrown else 0.05, var_scale=2)
    gaps = [(c - ROAD - 0.5, c + ROAD + 0.5) for c in CROSS]

    def spans(a, b):
        cur = a
        for g0, g1 in gaps:
            if g1 <= cur or g0 >= b:
                continue
            if g0 > cur:
                yield cur, g0
            cur = max(cur, g1)
        if cur < b:
            yield cur, b

    for sx in (-1, 1):
        for a, b in spans(y0, y1):
            lib.box((SW - 0.25, b - a, 0.15), (sx * (ROAD + 0.25 + (SW - 0.25) / 2), (a + b) / 2, 0), walk, bevel=0,
                    name='Walk', coll=coll, origin='bottom')
            lib.box((0.25, b - a, 0.16), (sx * (ROAD + 0.125), (a + b) / 2, 0), curb, bevel=0.03, name='Curb', coll=coll,
                    origin='bottom')
    # lane markings: dashes between lanes, double line in the middle, zebra at the first crossing
    for y in range(int(y0), int(y1), 12):
        if any(g0 - 2 < y < g1 + 2 for g0, g1 in gaps):
            continue
        for x in (-3.5, 3.5):
            lib.box((0.14, 3.0, 0.012), (x, y, 0.004), line, bevel=0, name='Dash', coll=coll, origin='bottom')
    for a, b in spans(y0, y1):
        for x in (-0.12, 0.12):
            lib.box((0.12, b - a, 0.012), (x, (a + b) / 2, 0.004), line, bevel=0, name='Centre', coll=coll, origin='bottom')
    zc = CROSS[0] - ROAD - 3.0
    for x in range(-6, 7, 1):
        lib.box((0.5, 3.2, 0.012), (x + 0.0, zc, 0.004), line, bevel=0, name='Zebra', coll=coll, origin='bottom')

    facades = facade_set(lit)
    shop_m, shop_s = pc.glow_mat('ShopGlass', '#FFD9A6', shop_glow) if shop_glow else (lib.mat('ShopGlass', '#2B3238', rough=0.08, spec=0.9), None)
    sign_cols = ['#B5272D', '#1F6E43', '#1E4E8C', '#E2A72E', '#5A2E6E', '#D35A1E']
    roof_m = lib.mat('Roof', '#5E5F60', rough=0.8, var=0.2, var_scale=2)
    for sx in (-1, 1):
        for a, b in spans(y0 - 20, y1 + 120):
            y = a
            while y < b - 6:
                L = min(rng.uniform(18, 38), b - y)
                floors = rng.choice([5, 5, 6, 9, 9, 12]) if y < y1 else rng.choice([9, 12, 16, 20])
                h = floors * 3.1 + 0.6
                depth = rng.uniform(13, 17)
                fm = rng.choice(facades)
                bx = sx * (BX + depth / 2)
                bd = lib.box((depth, L - 0.6, h), (bx, y + L / 2, 0), fm[0], bevel=0.1, name='Bld', coll=coll, origin='bottom')
                lib.box((depth + 0.4, L - 0.2, 0.6), (bx, y + L / 2, h), roof_m, bevel=0.05, name='Parapet', coll=coll, origin='bottom')
                if rng.random() < 0.5:
                    lib.box((3, 4, 2.6), (bx + rng.uniform(-3, 3), y + L / 2 + rng.uniform(-L / 4, L / 4), h + 0.6), roof_m,
                            bevel=0.05, name='RoofBox', coll=coll, origin='bottom')
                if y < y1 and L > 10:
                    # shop front + sign on the ground floor
                    fx = sx * (BX - 0.08)
                    lib.box((0.2, L - 3.0, 3.4), (fx, y + L / 2, 0.15), shop_m, bevel=0, name='ShopWin', coll=coll, origin='bottom')
                    if signs and rng.random() < 0.8:
                        sc = rng.choice(sign_cols)
                        sw = min(L - 4.0, rng.uniform(6, 11))
                        lib.box((0.25, sw, 0.9), (fx - sx * 0.1, y + L / 2, 3.75), lib.mat('Sign' + sc, sc, rough=0.5),
                                bevel=0.03, name='SignBox', coll=coll, origin='bottom')
                        rot = (math.pi / 2, 0, -math.pi / 2) if sx > 0 else (math.pi / 2, 0, math.pi / 2)
                        pc.text(rng.choice(SIGNS), 0.62, (fx - sx * 0.25, y + L / 2, 4.2), rot, '#F4F1EA', coll=coll, name='SignText')
                y += L + rng.uniform(0.0, 2.5)
    # lamps and trees on both sidewalks
    pole = lib.mat('LampPole', '#4A4D50', rough=0.5, metal=0.6)
    lamp_m, lamp_s = pc.glow_mat('LampHead', '#FFC58A', lamp_glow) if lamp_glow else (lib.mat('LampHead', '#D9D6CF', rough=0.3), None)
    for sx in (-1, 1):
        for y in range(int(y0) + 8, int(y1), 26):
            if any(g0 - 3 < y < g1 + 3 for g0, g1 in gaps):
                continue
            x = sx * (ROAD + 0.6)
            lib.cyl(0.09, 8.2, (x, y, 0.15), pole, verts=10, r2=0.06, name='Pole', coll=coll, origin='bottom')
            lib.box((1.8, 0.1, 0.1), (x - sx * 0.85, y, 8.2), pole, bevel=0.02, name='Arm', coll=coll)
            lib.box((0.7, 0.28, 0.14), (x - sx * 1.75, y, 8.1), lamp_m, bevel=0.04, name='LampBox', coll=coll)
        for y in range(int(y0) + 21, int(y1), 26):
            if any(g0 - 4 < y < g1 + 4 for g0, g1 in gaps):
                continue
            tree(sx * (ROAD + 2.4), y + rng.uniform(-1, 1), coll, rng, h=rng.uniform(7.5, 9.5) * (1.25 if overgrown else 1.0),
                 wild=1.25 if overgrown else 1.0)
    # traffic lights at the first crossing (dark: no power)
    tl = lib.mat('TLBody', '#2A2C2E', rough=0.5)
    lens_m = lib.mat('TLLens', '#3B3A36', rough=0.2, spec=0.9)
    for sx, yy in ((1, CROSS[0] - ROAD - 1.2), (-1, CROSS[0] + ROAD + 1.2)):
        lib.cyl(0.08, 4.2, (sx * (ROAD + 0.5), yy, 0.15), pole, verts=10, name='TLPole', coll=coll, origin='bottom')
        lib.box((0.36, 0.3, 1.0), (sx * (ROAD + 0.5), yy, 4.6), tl, bevel=0.04, name='TL', coll=coll)
        for k in range(3):
            lib.cyl(0.1, 0.05, (sx * (ROAD + 0.5), yy - sx * 0.16, 4.92 - k * 0.3), lens_m, rot=(math.pi / 2, 0, 0), verts=14,
                    name='TLLens', coll=coll)
    # bus stop on the right
    glass = lib.mat('StopGlass', '#9FB2BF', rough=0.05, alpha=0.35)
    frame = lib.mat('StopFrame', '#3D4246', rough=0.4, metal=0.6)
    lib.box((1.6, 6.0, 0.08), (BX - 1.2, 38, 2.6), frame, bevel=0.02, name='StopRoof', coll=coll)
    lib.box((0.05, 6.0, 2.3), (BX - 0.4, 38, 1.4), glass, bevel=0, name='StopBack', coll=coll)
    lib.box((0.45, 4.0, 0.08), (BX - 0.8, 38, 0.6), lib.mat('Bench', '#7A5A3E', rough=0.7), bevel=0.02, name='Bench', coll=coll)
    for yy in (35.1, 40.9):
        lib.cyl(0.05, 2.5, (BX - 1.9, yy, 0.15), frame, verts=8, name='StopPost', coll=coll, origin='bottom')
    # far end: the city goes on into the haze
    for i in range(30):
        x = rng.uniform(-260, 260)
        y = rng.uniform(y1 + 140, y1 + 600)
        if abs(x) < 30:
            continue
        h = rng.uniform(30, 90)
        lib.box((rng.uniform(20, 40), rng.uniform(16, 30), h), (x, y, 0), rng.choice(facades)[0], bevel=0.2, name='Far', coll=coll,
                origin='bottom')
    return dict(facades=facades, lamps=[lamp_s] if lamp_s else [], shops=[shop_s] if shop_s else [])


def overgrown_asphalt(k=1.0):
    """Asphalt with moss and grass growing out of the cracks (noise mask)."""
    m = bpy.data.materials.new('OvergrownAsphalt')
    m.use_nodes = True
    nt = m.node_tree; L = nt.links
    p = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord')
    n1 = nt.nodes.new('ShaderNodeTexNoise'); n1.inputs['Scale'].default_value = 0.22; n1.inputs['Detail'].default_value = 10
    n1.inputs['Roughness'].default_value = 0.65
    L.new(tc.outputs['Object'], n1.inputs['Vector'])
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = 0.5 - 0.06 * k; mr.inputs['From Max'].default_value = 0.56 - 0.06 * k
    L.new(n1.outputs['Fac'], mr.inputs['Value'])
    n2 = nt.nodes.new('ShaderNodeTexNoise'); n2.inputs['Scale'].default_value = 3.0; n2.inputs['Detail'].default_value = 8
    L.new(tc.outputs['Object'], n2.inputs['Vector'])
    green = nt.nodes.new('ShaderNodeMix'); green.data_type = 'RGBA'
    L.new(n2.outputs['Fac'], green.inputs['Factor'])
    green.inputs['A'].default_value = C('#4D6B2C'); green.inputs['B'].default_value = C('#7C8C3E')
    asph = nt.nodes.new('ShaderNodeMix'); asph.data_type = 'RGBA'
    L.new(n2.outputs['Fac'], asph.inputs['Factor'])
    asph.inputs['A'].default_value = C('#5B5C5C'); asph.inputs['B'].default_value = C('#6E6A62')
    mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'
    L.new(mr.outputs['Result'], mix.inputs['Factor']); L.new(asph.outputs['Result'], mix.inputs['A']); L.new(green.outputs['Result'], mix.inputs['B'])
    L.new(mix.outputs['Result'], p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = 0.92
    b = nt.nodes.new('ShaderNodeBump'); b.inputs['Strength'].default_value = 0.35; b.inputs['Distance'].default_value = 0.03
    L.new(n2.outputs['Fac'], b.inputs['Height']); L.new(b.outputs['Normal'], p.inputs['Normal'])
    return m


def stopped_cars(coll, rng, dusty=0.0, flat=False, ys=(6, 13, 24, 31, 44, 52, 78, 92, 104, 118, 133, 150, 170, 212, 240), avoid=()):
    """Cars left where their drivers vanished: in the lanes, a little askew, some doors open. avoid: [(x, y, r)]."""
    out = []
    lanes = [-5.25, -1.75, 1.75, 5.25]
    for i, y in enumerate(ys):
        x = rng.choice(lanes) + rng.uniform(-0.4, 0.4)
        if any(math.hypot(x - ax, y - ay) < ar for ax, ay, ar in avoid):
            continue
        head = (math.pi / 2 if x > 0 else -math.pi / 2) + rng.uniform(-0.18, 0.18)
        c = pc.stopped_car((x, y + rng.uniform(-2, 2), 0), head, coll, rng, door=rng.random() < 0.45,
                           kind='van' if rng.random() < 0.15 else 'sedan', dusty=dusty, flat=flat and rng.random() < 0.6,
                           name=f'Car{i}')
        out.append(c)
    # parked along the curbs
    for i in range(14):
        sx = rng.choice([-1, 1])
        y = rng.uniform(-30, 260)
        if any(abs(y - c) < 12 for c in CROSS):
            continue
        out.append(pc.stopped_car((sx * 6.1, y, 0), (math.pi / 2 if sx > 0 else -math.pi / 2), coll, rng, dusty=dusty,
                                  flat=flat and rng.random() < 0.5, name=f'Park{i}'))
    return out


def daylight(sun_dir=(0.55, -0.35, 0.55), energy=4.2, col='#FFF2DF', fog=0.0012):
    lib.FOG_BOX = (2400.0, 2400.0, 220.0)
    pc.day_sky(sun_dir, fog=fog)
    pc.sun(sun_dir, energy, col, angle=1.2)


# ----------------------------------------------------------------------------- variants
def v_street_day(shot, variant):
    dur = shot['dur']
    rng = random.Random(11)
    coll = lib.collection('Street')
    morning = variant == 'wake'
    daylight((0.75, -0.45, 0.32) if morning else (0.55, -0.35, 0.6), energy=4.0 if morning else 4.4,
             col='#FFE6C8' if morning else '#FFF3E2')
    street(coll, rng)
    crs = random.Random(5)
    avoid = {'you': [(0.9, 4.0, 5.0)], 'car': [(1.0, 16.0, 7.0)]}.get(variant, [])
    stopped_cars(coll, crs, avoid=avoid)
    if variant == 'wake':
        # a bike dropped on the zebra, a shopping bag on the sidewalk
        cam = lib.camera((1.4, -14, 1.65), (0.2, 80, 4.5), lens=26)
        cam.data.clip_start = 0.1
        lib.animate_camera(cam, [(0, (1.4, -14, 1.65)), (dur, (1.4, -12.5, 1.7))], [(0, (0.2, 80, 4.5)), (dur, (0.3, 80, 4.6))])
        return dict(fill=0.5, exposure=0.15, still_t=0.5)
    if variant == 'you':
        pc.hero((0.9, 4.0, 0), heading=0.25, coll=coll, pose='stand')
        cam = lib.camera((1.75, 0.2, 1.45), (0.7, 8.0, 1.4), lens=50)
        lib.animate_camera(cam, [(0, (1.75, 0.2, 1.45)), (dur, (1.75, 0.3, 1.45))], [(0, (0.7, 8.0, 1.4)), (dur, (0.7, 8.0, 1.4))])
        cam.data.clip_start = 0.1
        return dict(fill=0.6, exposure=0.15, still_t=0.4)
    # car: the hero by an open driver's door (car heading +Y in the right lane, driver side faces -X)
    pc.stopped_car((2.0, 16.0, 0), math.pi / 2 + 0.06, coll, crs, color='#8D1D1F', door=True, name='HeroCar')
    pc.hero((-0.15, 15.2, 0), heading=math.pi / 2 + 0.1, coll=coll, pose='point')
    cam = lib.camera((-3.0, 11.6, 1.5), (1.0, 16.2, 1.1), lens=36)
    lib.animate_camera(cam, [(0, (-3.0, 11.6, 1.5)), (dur, (-2.9, 11.7, 1.5))], [(0, (1.0, 16.2, 1.1)), (dur, (1.0, 16.2, 1.1))])
    cam.data.clip_start = 0.1
    return dict(fill=0.6, exposure=0.15, still_t=0.5)


def v_blackout(shot):
    """Aerial at blue hour; windows and street lamps die building by building after `out`."""
    dur = shot['dur']
    t_out = shot['events'].get('out', 1.8)
    rng = random.Random(21)
    coll = lib.collection('City')
    lib.FOG_BOX = (3000.0, 3000.0, 260.0)
    sun_dir = Vector((-0.25, 1.0, 0.0))
    lib.world_sky_view_gradient('#0D1830', '#56688C', '#1E2026', strength=1.2, fog=0.0011, fog_col='#3E4A66', aniso=0.5,
                                glow_dir=sun_dir, glow_col='#C8775A', glow_size=0.35, glow_strength=0.7)
    pc.sun((-0.25, 1.0, 0.06), 0.25, '#FFA868', angle=4)
    ground = lib.mat('CityAsphalt', '#4A4C50', rough=0.85, var=0.15, var_scale=0.3)
    lib.plane((4000, 4000), (0, 0, 0), ground, name='Ground', coll=coll)
    walk = lib.mat('CityWalk', '#8C8984', rough=0.9)
    facs = [pc.facade(f'BF{i}', cols=cols, lit=0.36, glow='#FFB565', glow_strength=2.4) for i, cols in enumerate(
        [('#D7D2C6', '#C4C0B6', '#B3B5B2'), ('#A9614B', '#9A5C48', '#B6725A'), ('#DED0A6', '#D4C6AC', '#C6B69D'),
         ('#C8CBCE', '#9FA7AE', '#D6D0C4')])]
    block, st = 56.0, 18.0
    n = 6
    for bi in range(-n, n + 1):
        for bj in range(-n, n + 3):
            cx, cy = bi * (block + st), bj * (block + st)
            lib.box((block + 4, block + 4, 0.15), (cx, cy, 0), walk, bevel=0, name='Block', coll=coll, origin='bottom')
            d = math.hypot(cx, cy - 150) / ((block + st) * n)
            hmax = lib.lerp(95, 24, min(1.0, d))
            for (x, y, w, dd) in [(cx - block / 4, cy - block / 4, block / 2 - 4, block / 2 - 4), (cx + block / 4, cy - block / 4, block / 2 - 4, block / 2 - 4),
                                  (cx - block / 4, cy + block / 4, block / 2 - 4, block / 2 - 4), (cx + block / 4, cy + block / 4, block / 2 - 4, block / 2 - 4)]:
                if rng.random() < 0.15:
                    continue
                h = max(12, min(hmax * 1.3, rng.lognormvariate(math.log(hmax * 0.6), 0.4)))
                fm = rng.choice(facs)
                lib.box((w, dd, h), (x, y, 0.15), fm[0], bevel=0.2, name='Bld', coll=coll, origin='bottom')
                lib.box((w + 0.4, dd + 0.4, 0.8), (x, y, 0.15 + h), lib.mat('BRoof', '#55575A', rough=0.8), bevel=0.05, name='BRoof', coll=coll,
                        origin='bottom')
    # street lamps: three groups so they do not all switch off in the same frame
    lamp_groups = [pc.glow_mat(f'AvLamp{k}', '#FFB868', 28.0) for k in range(3)]
    for i in range(-n, n + 1):
        c = i * (block + st) + (block + st) / 2
        for t in range(-n * 2, (n + 3) * 2):
            v = t * (block + st) / 2
            for off in (-7.5, 7.5):
                m = lamp_groups[rng.randint(0, 2)][0]
                lib.sphere(0.7, (c + off, v, 7.5), m, 6, 4, name='Lamp', coll=coll)
                m = lamp_groups[rng.randint(0, 2)][0]
                lib.sphere(0.7, (v, c + off, 7.5), m, 6, 4, name='Lamp', coll=coll)
    # power cut: windows (building by building, ~1.1 s) and lamps (three waves)
    f_out = F(t_out)
    for fm, lit, out in facs:
        lib.key_value(out.outputs[0], 1, 0.0, 'LINEAR')
        lib.key_value(out.outputs[0], f_out, 0.0, 'LINEAR')
        lib.key_value(out.outputs[0], F(t_out + 1.1), 1.0, 'LINEAR')
    for k, (m, s) in enumerate(lamp_groups):
        tk = t_out + 0.15 + 0.3 * k
        lib.key_value(s, 1, 28.0, 'CONSTANT')
        lib.key_value(s, F(tk), 0.0, 'CONSTANT')
    cam = lib.camera((-120, -175, 78), (15, 150, 22), lens=30)
    lib.animate_camera(cam, [(0, (-120, -175, 78)), (dur, (-104, -163, 73))], [(0, (15, 150, 22)), (dur, (24, 156, 20))])
    cam.data.clip_start = 1.0
    lib.bloom(0.35, 1.0, 8)
    return dict(fill=0.15, fill_col='#9FB4E0', exposure=0.25, samples=32)


def v_night(shot, variant):
    dur = shot['dur']
    rng = random.Random(11)
    coll = lib.collection('Street')
    pc.night_sky(milky=1.0)
    # the street was near-black under the reel's grade: twice the moonlight, the sky stays as it is
    pc.sun((-0.5, -0.35, 0.75), 0.16, '#A9BEE6', angle=1.0, name='Moon')
    street(coll, rng, signs=True)
    stopped_cars(coll, random.Random(5))
    if variant == 'night':
        t1 = shot['events'].get('tilt', dur - 2.0)
        t2 = min(dur - 0.05, t1 + 1.9)
        p0, p1, p2 = (0.8, -12.0, 1.7), (0.8, -11.0, 1.7), (0.6, -10.6, 1.6)
        g0, g1 = (0.3, 80, 7.0), (0.3, 80, 8.0)
        V = Vector((-0.085, 0.523, 0.848)).normalized()
        g2 = tuple(Vector(p2) + V * 80)
        cam = lib.camera(p0, g0, lens=26)
        lib.animate_camera(cam, [(0, p0), (t1, p1), (t2, p2), (dur, p2)], [(0, g0), (t1, g1), (t2, g2), (dur, g2)])
        bpy.context.scene.render.use_motion_blur = False      # the tilt smeared the stars into rain
    else:      # third: the sky over the roofs
        p = (0.4, -7.0, 1.6)
        cam = lib.camera(p, (-2.0, 30, 46), lens=24)
        lib.animate_camera(cam, [(0, p), (dur, p)], [(0, (-2.0, 30, 46)), (dur, (-2.0, 30, 46))])
    cam.data.clip_end = 3000
    lib.bloom(0.25, 0.8, 7)
    return dict(fill=0.12, fill_col='#AFC2E8', exposure=1.6, samples=48, still_t=0.5)


def v_wolves(shot):
    dur = shot['dur']
    rng = random.Random(11)
    coll = lib.collection('Street')
    lib.FOG_BOX = (2400.0, 2400.0, 220.0)
    sd = (0.45, -0.3, 0.7)
    pc.day_sky(sd, top='#7E98B6', horizon='#D2DADF', below='#8A8A80', glow='#FFF4E6', glow_size=0.15, glow_strength=0.8, fog=0.0018,
               fog_col='#C9CFCF')
    pc.sun(sd, 2.6, '#FFF4E8', angle=6)
    street(coll, rng, overgrown=1.0, signs=True)
    crs = random.Random(5)
    stopped_cars(coll, crs, dusty=0.55, flat=True, avoid=[(-0.8, 11.0, 5.0), (2.7, 5.0, 3.4)])
    # grass along the curbs and in the cracks, bushes on the sidewalks
    trs = random.Random(3)
    for sx in (-1, 1):
        tufts(coll, trs, 160, ((sx * 6.2, sx * 7.0) if sx > 0 else (-7.0, -6.2), (-10, 60)), h=(0.2, 0.55))
        tufts(coll, trs, 140, ((sx * 7.3, sx * 10.8) if sx > 0 else (-10.8, -7.3), (-10, 60)), h=(0.25, 0.7))
    tufts(coll, trs, 260, ((-6, 6), (-6, 50)), h=(0.12, 0.35))
    bush = [lib.mat('Bush' + g, g, rough=0.85, var=0.35, var_scale=3, bump=0.5, bump_scale=8) for g in GREENS]
    for i in range(40):
        sx = trs.choice([-1, 1])
        lib.sphere(trs.uniform(0.5, 1.1), (sx * trs.uniform(8, 10.8), trs.uniform(-5, 70), 0.3), trs.choice(bush), 10, 8,
                   scale=(1, 1, 0.7), name='Bush', coll=coll)
    for i in range(60):          # ivy on the ground floors
        sx = trs.choice([-1, 1])
        lib.sphere(1.0, (sx * (BX - 0.15), trs.uniform(-5, 90), trs.uniform(0.5, 3.5)), trs.choice(bush), 10, 8,
                   scale=(0.25, trs.uniform(1.0, 2.6), trs.uniform(1.2, 3.0)), name='Ivy', coll=coll)
    # three wolves trot down the street; the camera tracks alongside at 3/4 (head-on they read as owls), spread
    # across the frame so their silhouettes do not merge, low in the frame under the overgrown street
    W = []
    lead = (0.0, 10.4)
    for i, (x, y, sp) in enumerate([(0.0, 10.4, 1.55), (-0.01, 12.03, 1.6), (-2.66, 11.2, 1.57)]):
        w = pc.wolf((x, y, 0), 0.0, coll, random.Random(30 + i), name=f'Wolf{i}', scale=1.05 if i == 0 else 1.0)
        pc.trot(w, speed=sp, phase=0.27 * i)
        lib.move_root(w, [(x, y, 0), (x + 0.1 * (i - 1), y - 14, 0)], t0=0, speed=sp)
        W.append(w)
    ly1 = lead[1] - 1.55 * dur
    cam = lib.camera((2.7, 7.5, 0.55), (-0.2, 10.5, 1.55), lens=45)
    lib.animate_camera(cam, [(0, (2.7, 7.5, 0.55)), (dur, (2.7, 7.5 - 1.3 * dur, 0.55))],
                       [(0, (-0.2, 10.5, 1.55)), (dur, (-0.2, ly1 + 0.1, 1.5))])
    cam.data.clip_start = 0.1
    return dict(fill=0.5, exposure=0.2, samples=32)


def v_fuel(shot):
    dur = shot['dur']
    rng = random.Random(41)
    coll = lib.collection('Fuel')
    daylight((0.6, -0.5, 0.55), energy=4.2)
    lib.plane((3000, 3000), (0, 0, 0), lib.mat('FieldGround', '#7D8B55', rough=0.95, var=0.3, var_scale=0.08), name='Ground', coll=coll)
    conc = lib.mat('Concrete', '#B3AFA6', rough=0.9, var=0.12, var_scale=0.6, bump=0.1, bump_scale=15)
    lib.box((60, 50, 0.06), (0, 4, 0), conc, bevel=0, name='Apron', coll=coll, origin='bottom')
    road = lib.mat('Asphalt', '#57595C', rough=0.86, var=0.16, var_scale=0.4)
    lib.box((600, 12, 0.04), (0, -26, 0), road, bevel=0, name='Road', coll=coll, origin='bottom')
    white = lib.mat('CanopyWhite', '#ECEBE6', rough=0.5)
    blue = lib.mat('CanopyBlue', '#1F5AA6', rough=0.45)
    yel = lib.mat('CanopyYellow', '#F1B73A', rough=0.5)
    lib.box((24, 14, 1.0), (0, 2, 5.6), white, bevel=0.05, name='Canopy', coll=coll, origin='bottom')
    lib.box((24.1, 14.1, 0.35), (0, 2, 6.05), blue, bevel=0.02, name='CanopyBand', coll=coll)
    lib.box((24.12, 14.12, 0.08), (0, 2, 6.3), yel, bevel=0, name='CanopyStripe', coll=coll)
    for x in (-6.0, 6.0):
        lib.box((0.6, 0.6, 5.6), (x, 2, 0.06), white, bevel=0.03, name='Pillar', coll=coll, origin='bottom')
        lib.box((1.4, 6.0, 0.22), (x, 2, 0.06), conc, bevel=0.05, name='Island', coll=coll, origin='bottom')
        for yy in (0.2, 3.8):
            lib.box((0.75, 1.0, 1.9), (x, yy, 0.28), white, bevel=0.05, name='Pump', coll=coll, origin='bottom')
            lib.box((0.77, 1.02, 0.4), (x, yy, 1.85), blue, bevel=0.03, name='PumpTop', coll=coll, origin='bottom')
            for sx in (-1, 1):
                lib.box((0.02, 0.5, 0.32), (x + sx * 0.39, yy, 1.35), lib.mat('PumpScreen', '#1B2228', rough=0.15, spec=0.8), bevel=0,
                        name='PumpScreen', coll=coll)
                for k in range(3):
                    lib.box((0.05, 0.1, 0.22), (x + sx * 0.4, yy - 0.3 + k * 0.3, 0.95), lib.mat('Nozzle', '#2A2B2C', rough=0.4), bevel=0.01,
                            name='Nozzle', coll=coll)
    # shop with a glass front and the price totem
    lib.box((18, 9, 4.2), (0, 20, 0.06), white, bevel=0.05, name='Shop', coll=coll, origin='bottom')
    lib.box((18.1, 9.1, 0.7), (0, 20, 4.25), blue, bevel=0.03, name='ShopBand', coll=coll, origin='bottom')
    lib.box((14, 0.1, 2.6), (0, 15.45, 0.4), lib.mat('ShopGlass', '#2B3540', rough=0.06, spec=0.9), bevel=0, name='ShopGlass', coll=coll,
            origin='bottom')
    pc.text('МАГАЗИН · КАФЕ', 0.6, (0, 15.35, 4.6), (math.pi / 2, 0, 0), '#F4F2EC', coll=coll, name='ShopText')
    tx, ty = -13.0, -12.0
    lib.box((0.5, 0.5, 6.0), (tx, ty, 0), lib.mat('TotemPole', '#5B5F63', rough=0.5, metal=0.5), bevel=0.02, name='TotemPole', coll=coll,
            origin='bottom')
    lib.box((2.6, 0.45, 3.4), (tx, ty, 5.4), blue, bevel=0.05, name='Totem', coll=coll, origin='bottom')
    for k, label in enumerate(['АИ-92', 'АИ-95', 'ДТ']):
        lib.box((2.2, 0.05, 0.62), (tx, ty - 0.24, 7.95 - k * 0.8), lib.mat('TotemRow', '#0E1215', rough=0.3), bevel=0, name='TotemRow', coll=coll)
        pc.text(label, 0.36, (tx - 0.5, ty - 0.28, 7.95 - k * 0.8), (math.pi / 2, 0, 0), '#F4F2EC', coll=coll, name='TotemText')
        pc.text('— —', 0.36, (tx + 0.55, ty - 0.28, 7.95 - k * 0.8), (math.pi / 2, 0, 0), '#E2463A', coll=coll, name='TotemDash')
    pc.text('ТОПЛИВО', 0.42, (tx, ty - 0.24, 8.55), (math.pi / 2, 0, 0), '#F1B73A', coll=coll, name='TotemHead')
    # an abandoned car at the pump, door open; nozzle hose hanging to the tank
    crs = random.Random(8)
    pc.stopped_car((3.6, 1.2, 0.06), math.pi / 2 + 0.05, coll, crs, color='#2E4A6B', door=True, dusty=0.25, name='PumpCar')
    # the nozzle is still in the tank: hose from the pump holster, handle, open filler recess
    hose = lib.mat('Hose', '#1E1F20', rough=0.6)
    lib.curve_poly('Hose', [[(5.58, 0.6, 1.0), (5.3, 0.5, 0.42), (5.0, 0.3, 0.32), (4.78, 0.08, 0.7), (4.72, 0.02, 0.9)]], bevel=0.022,
                   mat_=hose, coll=coll)
    lib.box((0.05, 0.13, 0.13), (4.515, 0.0, 0.83), lib.mat('Filler', '#141516', rough=0.7), bevel=0.01, name='Filler', coll=coll)
    lib.box((0.16, 0.06, 0.1), (4.66, 0.0, 0.92), lib.mat('NozzleGreen', '#2F7A3E', rough=0.45), bevel=0.015, name='NozzleGrip', coll=coll)
    lib.box((0.1, 0.035, 0.035), (4.56, 0.0, 0.86), lib.mat('NozzleSteel', '#9A9C9E', rough=0.3, metal=0.9), bevel=0.005,
            name='NozzleSpout', coll=coll).rotation_euler.y = 0.5
    pc.stopped_car((-3.4, 4.5, 0.06), -math.pi / 2 - 0.08, coll, crs, color='#25272A', name='PumpCar2')
    for i in range(24):
        tree(rng.uniform(-70, 70), rng.uniform(35, 70), coll, rng, h=rng.uniform(8, 13))
    for i in range(10):
        tree(rng.choice([-1, 1]) * rng.uniform(32, 60), rng.uniform(-8, 30), coll, rng, h=rng.uniform(8, 12))
    # dead light panels under the canopy, oil stains and weeds so the apron is not an empty grey plane
    panel = lib.mat('CanopyPanel', '#D6D8D8', rough=0.3)
    for px_ in (-9, -3, 3, 9):
        for py_ in (-2.5, 2, 6.5):
            lib.box((2.2, 0.6, 0.04), (px_, py_, 5.58), panel, bevel=0, name='Panel', coll=coll)
    stain = lib.mat('OilStain', '#A39F97', rough=0.8)
    for i in range(8):
        r_ = rng.uniform(0.25, 0.8)
        lib.cyl(r_, 0.005, (rng.uniform(-9, 9), rng.uniform(-5, 9), 0.062), stain, verts=16, name='Stain', coll=coll).scale = (1.0, rng.uniform(0.5, 1.0), 1.0)
    for x in (-6.0, 6.0):
        tufts(coll, rng, 30, ((x - 0.75, x + 0.75), (-1.1, 5.1)), h=(0.08, 0.22))
    cam = lib.camera((5.6, -4.3, 0.95), (4.7, 0.3, 1.9), lens=34, dof=4.6, fstop=4.0)
    lib.animate_camera(cam, [(0, (5.6, -4.3, 0.95)), (dur, (5.45, -3.95, 0.95))], [(0, (4.7, 0.3, 1.9)), (dur, (4.68, 0.2, 1.9))])
    cam.data.clip_start = 0.05
    return dict(fill=0.5, exposure=0.12, still_t=0.5)


def ferris_wheel(c, coll, R=13.0, n=20):
    """Pripyat-style Ferris wheel: two rims with spokes, A-frame legs, yellow gondolas (faded paint)."""
    x0, y0, z0 = c
    rim = lib.mat('WheelRim', '#C49A35', rough=0.75, var=0.35, var_scale=3)
    steel = lib.mat('WheelSteel', '#7A6A55', rough=0.8, metal=0.3, var=0.35, var_scale=4)
    gond = lib.mat('Gondola', '#D9B13A', rough=0.7, var=0.3, var_scale=4)
    roof = lib.mat('GondolaRoof', '#C8692E', rough=0.7, var=0.3, var_scale=4)
    for sy in (-0.9, 0.9):
        pts = [(x0 + R * math.cos(2 * math.pi * k / 72), y0 + sy, z0 + R * math.sin(2 * math.pi * k / 72)) for k in range(73)]
        lib.curve_poly('Rim', [pts], bevel=0.16, mat_=rim, coll=coll)
        pts2 = [(x0 + R * 0.86 * math.cos(2 * math.pi * k / 72), y0 + sy, z0 + R * 0.86 * math.sin(2 * math.pi * k / 72)) for k in range(73)]
        lib.curve_poly('Rim2', [pts2], bevel=0.09, mat_=rim, coll=coll)
        spokes = [[(x0, y0 + sy, z0), (x0 + R * math.cos(2 * math.pi * k / n), y0 + sy, z0 + R * math.sin(2 * math.pi * k / n))] for k in range(n)]
        lib.curve_poly('Spokes', spokes, bevel=0.05, mat_=steel, coll=coll)
        legs = [[(x0, y0 + sy * 1.4, z0), (x0 - 6.5, y0 + sy * 3.2, 0)], [(x0, y0 + sy * 1.4, z0), (x0 + 6.5, y0 + sy * 3.2, 0)]]
        lib.curve_poly('Legs', legs, bevel=0.32, mat_=steel, coll=coll)
    lib.cyl(0.6, 3.0, (x0, y0, z0), steel, rot=(math.pi / 2, 0, 0), verts=16, name='Hub', coll=coll)
    for k in range(n):
        a = 2 * math.pi * k / n
        gx, gz = x0 + R * math.cos(a), z0 + R * math.sin(a)
        lib.box((1.5, 1.5, 1.05), (gx, y0, gz - 1.45), gond, bevel=0.12, name='Gondola', coll=coll)
        lib.cyl(1.05, 0.35, (gx, y0, gz - 0.68), roof, verts=10, r2=0.35, name='GondolaRoof', coll=coll)
        lib.box((0.06, 0.06, 0.7), (gx, y0, gz - 0.3), steel, bevel=0, name='GondolaHanger', coll=coll)
    lib.box((16, 7, 0.6), (x0, y0, 0), lib.mat('WheelBase', '#8E8A82', rough=0.9, var=0.3, var_scale=2), bevel=0.1, name='WheelBase',
            coll=coll, origin='bottom')


def v_chernobyl(shot):
    dur = shot['dur']
    rng = random.Random(61)
    coll = lib.collection('Pripyat')
    lib.FOG_BOX = (2400.0, 2400.0, 220.0)
    sd = (-0.45, -0.55, 0.6)
    pc.day_sky(sd, top='#6F8DB0', horizon='#D6DDE2', below='#7D8460', glow='#FFF6EA', glow_size=0.12, glow_strength=0.5, fog=0.002,
               fog_col='#CDD3D2')
    pc.sun(sd, 2.8, '#FFF3E4', angle=5)
    meadow = lib.mat('Meadow', '#6E7F3F', rough=0.95, var=0.35, var_scale=0.12, bump=0.3, bump_scale=10)
    lib.plane((3000, 3000), (0, 0, 0), meadow, name='Ground', coll=coll)
    ferris_wheel((2.0, 34.0, 15.5), coll)
    # panel blocks behind, windows dark and empty
    pan = [pc.facade(f'PanelF{i}', cols=cols, glass='#1E2226', lit=0.0) for i, cols in enumerate(
        [('#C9C7BF', '#BDBBB3', '#D2D0C8'), ('#B9B6AC', '#C6C3BA', '#ADAAA1')])]
    for (x, y, w, h) in [(-48, 78, 60, 48), (30, 92, 70, 30), (75, 64, 18, 30), (-12, 120, 40, 52), (-95, 60, 22, 31)]:
        lib.box((w, 14, h), (x, y, 0), rng.choice(pan)[0], bevel=0.15, name='Panel', coll=coll, origin='bottom')
        lib.box((w + 0.4, 14.4, 0.7), (x, y, h), lib.mat('PRoof', '#6B6B68', rough=0.85), bevel=0.05, name='PRoof', coll=coll, origin='bottom')
    # birches and pines everywhere, tall grass in front
    for i in range(70):
        x, y = rng.uniform(-60, 60), rng.uniform(14, 70)
        if abs(x - 2) < 12 and 26 < y < 44:
            continue
        tree(x, y, coll, rng, h=rng.uniform(9, 16), greens=['#7EA04C', '#8DAE58', '#6E9244'], birch=rng.random() < 0.7)
    for i in range(14):
        sx = rng.choice([-1, 1])
        tree(sx * rng.uniform(7, 16), rng.uniform(4, 14), coll, rng, h=rng.uniform(8, 12), greens=['#7EA04C', '#8DAE58', '#6E9244'],
             birch=True)
    tufts(coll, rng, 700, ((-12, 12), (-2, 24)), h=(0.25, 0.7), cols=('#6E7F3A', '#7F8C44', '#5E6E34', '#8E8A52'))
    cam = lib.camera((-1.5, -6.0, 1.25), (2.0, 34, 12.5), lens=35)
    lib.animate_camera(cam, [(0, (-1.5, -6.0, 1.25)), (dur, (-1.2, -5.6, 1.25))], [(0, (2.0, 34, 12.5)), (dur, (2.0, 34, 12.5))])
    return dict(fill=0.6, exposure=0.2, still_t=0.5)


def build(shot, fps=60):
    lib.FPS = fps
    v = shot['variant']
    if v in ('wake', 'you', 'car'):
        return v_street_day(shot, v)
    if v == 'blackout':
        return v_blackout(shot)
    if v in ('night', 'third'):
        return v_night(shot, v)
    if v == 'wolves':
        return v_wolves(shot)
    if v == 'fuel':
        return v_fuel(shot)
    if v == 'chernobyl':
        return v_chernobyl(shot)
    raise SystemExit('unknown variant ' + v)
