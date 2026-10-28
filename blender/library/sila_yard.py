"""«Двор» for «Каждому по способности» (28.10.2026): the courtyard of the hero's five-storey block on a golden autumn
morning. Not the city street (the user wants more variety and creativity than one city).

Plan (metres): the hero's block runs along y = YB (its front faces -y), the entrance (подъезд) at x = 0 with a concrete
canopy, two benches and a flower bed; a driveway with parked cars along it, then the lawn with birches and maples,
a playground (swings with a kid, slide, sandbox, carousel), a washing line with bright laundry, two more blocks closing
the yard. Low warm sun from the left behind the camera, long shadows, birds.

yard(coll, rng) builds it; the scenes (a06 granny lifts the car, a07 the car in the air, a14 the bench jump) are below.
"""
import math
import random

import bpy

from mathutils import Vector as V

import lib
import pcity
import pcommon as pc
import people2 as P2
import sila as S
import sila_fx as FX
import sila_hero as H
import sila_sets as SS

F = lib.sec2f
YB = 12.0                       # the front of the hero's block
FLOOR = 3.1                     # floor height of the facade shader
AURA = ['#FFC857', '#7FD8FF', '#FF7AB6', '#9DFF8A', '#C59BFF', '#FF9C5B', '#6FFFE1', '#FFE66B']
PAINTS = ['#C8553D', '#F2B134', '#3E7CB1', '#5BA35B', '#E8E1D0']


def _block(coll, x0, x1, y_face, depth, floors, facing, fmat, rng, name, balconies=True):
    """A five-storey panel block: facade shader windows, flat roof with a parapet, balconies with pastel fronts.
    facing: -1 the front looks to -y, +1 to +y."""
    L, h = x1 - x0, floors * FLOOR + 0.4
    yc = y_face - facing * depth / 2
    b = lib.box((L, depth, h), ((x0 + x1) / 2, yc, 0.0), fmat, bevel=0.05, name=name, coll=coll, origin='bottom')
    lib.box((L + 0.2, depth + 0.2, 0.35), ((x0 + x1) / 2, yc, h), lib.mat('RoofEdge', '#8C857A', rough=0.85), bevel=0.03,
            name=name + 'Roof', coll=coll, origin='bottom')
    if not balconies:
        return b
    slab = lib.mat('BalSlab', '#C9C2B5', rough=0.85)
    # window columns of the shader: (x + y) / 3.2 = k + 0.5 in object coords (origin at the bottom centre)
    yl = facing * depth / 2
    k0 = math.ceil((-L / 2 + yl) / 3.2 - 0.5)
    cols = []
    k = k0
    while True:
        xl = (k + 0.5) * 3.2 - yl
        if xl > L / 2 - 1.0:
            break
        if xl > -L / 2 + 1.0:
            cols.append(xl)
        k += 1
    for i, xl in enumerate(cols):
        if i % 3 != 1:
            continue
        col = rng.choice(['#D9C7A0', '#C9D3C4', '#E2C2B0', '#CBD5DE'])
        front = lib.mat('BalFront' + col, col, rough=0.8, var=0.06, var_scale=3)
        for fl in range(1, floors):
            z = fl * FLOOR + 0.02
            xw = (x0 + x1) / 2 + xl
            yo = y_face + facing * 0.55
            lib.box((1.5, 1.1, 0.12), (xw, yo, z), slab, bevel=0.01, name=name + 'Bal', coll=coll, origin='bottom')
            lib.box((1.5, 0.06, 1.0), (xw, y_face + facing * 1.08, z + 0.12), front, bevel=0.01, name=name + 'BalFront', coll=coll,
                    origin='bottom')
            if rng.random() < 0.35:                 # a plant or a box on some balconies
                lib.sphere(0.25, (xw + rng.uniform(-0.5, 0.5), yo, z + 1.2), lib.mat('BalPlant', '#5E8A3C', rough=0.85), 8, 6,
                           name=name + 'BalPlant', coll=coll)
    return b


def _swing(coll, loc, t_dur, phase=0.0, kid=None):
    """Red A-frame swing; the seat swings on a pivot (with a kid on it when given)."""
    x, y, z = loc
    red = lib.mat('PlayRed', '#C8553D', rough=0.4)
    yel = lib.mat('PlayYellow', '#F2B134', rough=0.4)
    for sx in (-1.1, 1.1):
        for sy in (-0.7, 0.7):
            lib.cyl(0.05, 2.45, (x + sx, y + sy * 0.5, z), red, rot=(sy * 0.28, 0, 0), verts=10, name='SwingPost', coll=coll,
                    origin='bottom')
    lib.cyl(0.055, 2.4, (x, y, z + 2.3), yel, rot=(0, math.pi / 2, 0), verts=12, name='SwingBar', coll=coll)
    piv = lib.empty('SwingPivot', (x, y, z + 2.3), coll=coll)
    chain = lib.mat('Chain', '#9A9A96', rough=0.3, metal=0.9)
    for sx in (-0.25, 0.25):
        c = lib.cyl(0.012, 1.85, (sx, 0, -1.85), chain, verts=6, name='SwingChain', coll=coll, origin='bottom')
        c.parent = piv
    seat = lib.box((0.6, 0.3, 0.05), (0, 0, -1.87), yel, bevel=0.01, name='SwingSeat', coll=coll)
    seat.parent = piv
    for k in range(int(t_dur * 4) + 2):
        t = k * 0.25
        piv.rotation_euler.x = 0.55 * math.sin(2 * math.pi * t / 2.3 + phase)
        piv.keyframe_insert('rotation_euler', index=0, frame=F(t))
    if kid is not None:
        kid['root'].parent = piv
        kid['root'].location = (0, 0.05, -1.85)
        kid['root'].rotation_euler = (0, 0, 0)
    return piv


def _slide(coll, loc):
    x, y, z = loc
    blue = lib.mat('PlayBlue', '#3E7CB1', rough=0.35)
    steel = lib.mat('SlideSteel', '#D7DADC', rough=0.15, metal=1.0)
    for sx in (-0.4, 0.4):
        for sy in (0.0, 0.8):
            lib.cyl(0.04, 1.6, (x + sx, y + sy, z), blue, verts=8, name='SlidePost', coll=coll, origin='bottom')
    lib.box((0.9, 0.9, 0.06), (x, y + 0.4, z + 1.5), lib.mat('PlayYellow', '#F2B134', rough=0.4), bevel=0.01, name='SlideTop', coll=coll)
    for k in range(5):
        lib.box((0.8, 0.05, 0.04), (x, y + 0.95, z + 0.3 + k * 0.28), blue, bevel=0.005, name='SlideRung', coll=coll)
    L = 2.6
    a = math.atan2(1.5, 2.1)
    lib.box((0.6, L, 0.04), (x, y - 1.05, z + 0.78), steel, rot=(-a, 0, 0), bevel=0.01, name='SlideBed', coll=coll)
    for sx in (-0.32, 0.32):
        lib.box((0.04, L, 0.16), (x + sx, y - 1.05, z + 0.85), blue, rot=(-a, 0, 0), bevel=0.01, name='SlideSide', coll=coll)


def _carousel(coll, loc, dur):
    x, y, z = loc
    root = lib.empty('Carousel', (x, y, z), coll=coll)
    disc = lib.cyl(1.0, 0.08, (0, 0, 0.25), lib.mat('PlayGreen', '#5BA35B', rough=0.4), verts=32, name='CarDisc', coll=coll)
    disc.parent = root
    red = lib.mat('PlayRed', '#C8553D', rough=0.4)
    for k in range(4):
        a = k * math.pi / 2
        r = lib.cyl(0.03, 0.6, (0.75 * math.cos(a), 0.75 * math.sin(a), 0.3), red, verts=8, name='CarRail', coll=coll, origin='bottom')
        r.parent = root
    lib.cyl(0.06, 0.9, (x, y, z), lib.mat('PlayYellow', '#F2B134', rough=0.4), verts=12, name='CarAxle', coll=coll, origin='bottom')
    for t, v in ((0, 0.0), (dur + 1, 0.9 * (dur + 1))):
        root.rotation_euler.z = v
        root.keyframe_insert('rotation_euler', index=2, frame=F(t))
    lib._set_interp(root, 'LINEAR')
    return root


def _sandbox(coll, loc, rng):
    x, y, z = loc
    wood = lib.mat('SandWood', '#B07A4A', rough=0.6, var=0.2, var_scale=8)
    for (dx, dy, sx, sy) in ((0, -1, 2.2, 0.12), (0, 1, 2.2, 0.12), (-1, 0, 0.12, 2.2), (1, 0, 0.12, 2.2)):
        lib.box((sx, sy, 0.25), (x + dx * 1.05, y + dy * 1.05, z), wood, bevel=0.02, name='SandFrame', coll=coll, origin='bottom')
    lib.box((2.0, 2.0, 0.16), (x, y, z), lib.mat('Sand', '#E3CC94', rough=0.95, bump=0.3, bump_scale=30), bevel=0.05, name='Sand',
            coll=coll, origin='bottom')
    lib.cyl(0.08, 0.14, (x + 0.4, y - 0.3, z + 0.16), lib.mat('PlayRed', '#C8553D', rough=0.4), verts=14, r2=0.1, name='Bucket',
            coll=coll, origin='bottom')
    lib.box((0.07, 0.25, 0.02), (x + 0.6, y - 0.2, z + 0.17), lib.mat('PlayBlue', '#3E7CB1', rough=0.35), rot=(0, 0, 0.6), bevel=0.005,
            name='Spade', coll=coll, origin='bottom')


def _laundry(coll, p0, p1, rng, dur):
    """Two T-posts and three lines of bright laundry swaying in the breeze."""
    p0, p1 = V(p0), V(p1)
    post = lib.mat('LinePost', '#6E7A84', rough=0.4, metal=0.5)
    d = (p1 - p0).normalized()
    n = V((-d.y, d.x, 0))
    for p in (p0, p1):
        lib.cyl(0.05, 2.1, tuple(p), post, verts=8, name='LinePost', coll=coll, origin='bottom')
        lib.box((0.06, 1.2, 0.06), (p.x, p.y, p.z + 2.05), post, rot=(0, 0, math.atan2(d.y, d.x)), bevel=0, name='LineBar', coll=coll)
    cols = ['#F4F1EA', '#E8A0A8', '#9CC7E6', '#F2D16B', '#B7DDB0', '#F4F1EA', '#D9B6E8']
    for row in (-0.45, 0.0, 0.45):
        a, b = p0 + n * row + V((0, 0, 2.02)), p1 + n * row + V((0, 0, 2.02))
        lib.curve_poly('Line', [[tuple(a), tuple(a.lerp(b, 0.5) - V((0, 0, 0.08))), tuple(b)]], bevel=0.004,
                       mat_=lib.mat('LineRope', '#E9E6DE', rough=0.6), coll=coll)
        x = 0.4
        L = (b - a).length
        while x < L - 0.6:
            w = rng.uniform(0.5, 1.1)
            c = rng.choice(cols)
            q = a.lerp(b, (x + w / 2) / L) - V((0, 0, 0.05 + 0.08 * (1 - abs((x + w / 2) / L - 0.5) * 2)))
            piv = lib.empty('ClothPiv', tuple(q), (0, 0, math.atan2(d.y, d.x)), coll=coll)
            cl = lib.box((w, 0.01, rng.uniform(0.5, 0.9)), (0, 0, 0), lib.mat('Cloth' + c, c, rough=0.9, var=0.05), bevel=0.003,
                         name='Cloth', coll=coll, origin='bottom')
            cl.rotation_euler.x = math.pi
            cl.parent = piv
            lib.add_sine(piv, 'rotation_euler', 0, 0.12, rng.uniform(1.8, 2.6), rng.uniform(0, 6))
            x += w + rng.uniform(0.1, 0.3)


def _lawn_mat():
    """Autumn lawn: green grass with drifts of fallen leaves (big noise patches broken up by a fine leaf speckle)."""
    m = bpy.data.materials.get('YardLawnLeaves')
    if m:
        return m
    m = bpy.data.materials.new('YardLawnLeaves')
    m.use_nodes = True
    nt = m.node_tree
    p = nt.nodes['Principled BSDF']
    p.inputs['Roughness'].default_value = 0.95
    tc = nt.nodes.new('ShaderNodeTexCoord')
    big, fine = nt.nodes.new('ShaderNodeTexNoise'), nt.nodes.new('ShaderNodeTexNoise')
    for nz, sc, det in ((big, 0.09, 3.0), (fine, 10.0, 2.0)):
        nz.inputs['Scale'].default_value = sc
        nz.inputs['Detail'].default_value = det
        nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
    add = nt.nodes.new('ShaderNodeMath')
    add.operation = 'MULTIPLY_ADD'
    nt.links.new(fine.outputs['Fac'], add.inputs[0])
    add.inputs[1].default_value = 0.9
    big_w = nt.nodes.new('ShaderNodeMath')
    big_w.operation = 'MULTIPLY'
    big_w.inputs[1].default_value = 0.8
    nt.links.new(big.outputs['Fac'], big_w.inputs[0])
    nt.links.new(big_w.outputs[0], add.inputs[2])
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    nt.links.new(add.outputs[0], ramp.inputs['Fac'])
    els = ramp.color_ramp.elements
    # crisp leaf speckles (constant ramp) on plain grass, dense only where the big noise piles them into drifts
    ramp.color_ramp.interpolation = 'CONSTANT'
    stops = ((0.0, '#6E8B42'), (0.935, '#C99A3E'), (0.975, '#B8682F'), (1.0, '#D6AE4C'))
    els[0].position, els[0].color = stops[0][0], lib.C(stops[0][1])
    els[1].position, els[1].color = stops[-1][0], lib.C(stops[-1][1])
    for pos, col in stops[1:-1]:
        e = els.new(pos)
        e.color = lib.C(col)
    nt.links.new(ramp.outputs['Color'], p.inputs['Base Color'])
    bump = nt.nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.25
    nt.links.new(fine.outputs['Fac'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], p.inputs['Normal'])
    return m


def yard(coll, rng, dur=4.0, sun_dir=(-0.55, -0.62, 0.33), dusk=False):
    """dusk: the evening of part 1 (a16-a19): a low orange sun, lit windows, the lamps on."""
    lib.world_color('#000000', 0.0)
    if dusk:
        pc.day_sky(sun_dir, top='#2A3C66', horizon='#F3A46A', below='#3E3842', strength=0.8, glow='#FF8C4A', fog=0.0022,
                   fog_col='#8F7C86', glow_size=0.2, glow_strength=2.6)
        sun = pc.sun(sun_dir, 1.8, '#FF9A5C', 1.5, name='YardSun')
    else:
        pc.day_sky(sun_dir, top='#6FA3D8', horizon='#F5E2C2', below='#9C9484', strength=1.1, glow='#FFE2B5', fog=0.0016,
                   fog_col='#EADCC4', glow_size=0.1, glow_strength=2.0)
        sun = pc.sun(sun_dir, 4.6, '#FFDDAE', 1.0, name='YardSun')
    facs = pcity.facade_set(0.4 if dusk else 0.0, prefix='Yd')
    # the hero's block along y = YB, the one across the yard, the end block on the left
    _block(coll, -36, 36, YB, 12, 5, -1, facs[2][0], rng, 'HomeBlock')
    _block(coll, -36, 30, -26, 12, 5, 1, facs[0][0], rng, 'OppBlock')
    _block(coll, -46, -34, 6, 30, 5, -1, facs[3][0], rng, 'EndBlock', balconies=False)
    # ground: asphalt drive, kerbs, the walk along the block, the lawn
    asph = lib.mat('YardAsphalt', '#6B6A66', rough=0.85, var=0.12, var_scale=0.6, bump=0.08, bump_scale=40)
    walk = lib.mat('YardWalk', '#A8A196', rough=0.85, var=0.1, var_scale=1.5)
    lib.plane((400, 400), (0, 0, -0.01), _lawn_mat(), name='Lawn', coll=coll)
    lib.box((90, 4.2, 0.04), (0, YB - 4.6, 0.0), asph, bevel=0, name='Drive', coll=coll, origin='bottom')
    lib.box((90, 2.4, 0.12), (0, YB - 1.2, 0.0), walk, bevel=0.02, name='Walk', coll=coll, origin='bottom')
    lib.box((2.2, 7.5, 0.06), (14.0, YB - 10.0, 0.0), walk, bevel=0.02, name='Path', coll=coll, origin='bottom')
    lib.box((90, 0.15, 0.15), (0, YB - 6.8, 0.0), walk, bevel=0.02, name='Kerb', coll=coll, origin='bottom')
    # the entrance: door, canopy on brackets, two steps, benches, a flower bed, the lamp over the door
    door = lib.mat('EntranceDoor', '#5A3B2A', rough=0.5)
    lib.box((1.5, 0.12, 2.25), (0.0, YB - 0.02, 0.12), door, bevel=0.02, name='EntDoor', coll=coll, origin='bottom')
    lib.box((0.05, 0.14, 2.0), (0.0, YB - 0.1, 0.2), lib.mat('DoorGap', '#2A1D14', rough=0.6), bevel=0, name='EntGap', coll=coll,
            origin='bottom')
    canopy = lib.mat('Canopy', '#B9B3A8', rough=0.85)
    lib.box((2.6, 1.6, 0.14), (0.0, YB - 0.8, 2.75), canopy, bevel=0.02, name='EntCanopy', coll=coll, origin='bottom')
    for sx in (-1.15, 1.15):
        lib.box((0.08, 1.4, 0.08), (sx, YB - 0.7, 2.6), canopy, rot=(0.6, 0, 0), bevel=0.01, name='EntBracket', coll=coll)
    for k in range(2):
        lib.box((2.0, 1.0 - k * 0.35, 0.14), (0.0, YB - 0.5 + k * 0.17, 0.12 + k * 0.14), walk, bevel=0.02, name='EntStep', coll=coll,
                origin='bottom')
    lamp, _ = lib.emission_mat('EntLamp', '#FFE0A8', 9.0 if dusk else 3.0)
    lib.sphere(0.12, (0.0, YB - 0.2, 2.5), lamp, 16, 10, name='EntLampGlobe', coll=coll)
    for sx in (-2.3, 2.3):
        SS.bench(coll, (sx, YB - 1.9, 0.12), math.pi, name='EntBench')
    for sx in (-4.8, 4.8):
        lib.box((3.0, 1.4, 0.3), (sx, YB - 1.4, 0.12), lib.mat('BedEdge', '#E9E4D8', rough=0.8), bevel=0.04, name='FlowerBed',
                coll=coll, origin='bottom')
        for k in range(14):
            c = rng.choice(['#F2A33A', '#E85D2A', '#F7D046', '#C2362F'])
            lib.sphere(0.09, (sx + rng.uniform(-1.3, 1.3), YB - 1.4 + rng.uniform(-0.5, 0.5), 0.5), lib.mat('Flower' + c, c, rough=0.7),
                       8, 6, name='Flower', coll=coll)
        for k in range(8):
            lib.sphere(0.16, (sx + rng.uniform(-1.3, 1.3), YB - 1.4 + rng.uniform(-0.5, 0.5), 0.4), lib.mat('BedLeaf', '#557A35',
                       rough=0.85), 8, 6, scale=(1, 1, 0.6), name='BedLeaf', coll=coll)
    # trees: birches and maples in autumn, a few bushes
    autumn = ('#D9A13A', '#E0B54A', '#C9732E', '#9DB04A', '#B8842F')
    for (x, y, hgt, birch) in ((-12, 0.5, 13, True), (-17, -6, 11, False), (9, 1.5, 12, False), (18, -3, 14, True), (24, 3.5, 11, True),
                               (-25, -10, 12, False), (4, -12, 13, True), (-6, -16, 11, False), (28, -12, 12, False)):
        pcity.tree(x, y, coll, rng, h=hgt, greens=autumn, birch=birch)
    SS.hedge(coll, rng, (-30, YB - 7.6, 0), (-8, YB - 7.6, 0), h=0.9, w=0.8, name='YardHedge')
    SS.hedge(coll, rng, (8, YB - 7.6, 0), (12.7, YB - 7.6, 0), h=0.9, w=0.8, name='YardHedge')      # a gap for the lawn path
    SS.hedge(coll, rng, (15.3, YB - 7.6, 0), (30, YB - 7.6, 0), h=0.9, w=0.8, name='YardHedge')
    # parked cars on the drive (the red Lada is the scene's own)
    for x, c in ((-13.5, '#E9E6DF'), (-8.2, '#3E5A73'), (11.5, '#2F3B45'), (17.0, '#C9B48A')):
        lib.car((x, YB - 4.3, 0.04), 0.0, color=c, coll=coll, lights=False, rng=rng, name='YdCar')
    # playground and laundry
    _sandbox(coll, (-6.0, -6.0, 0.0), rng)
    _slide(coll, (-1.5, -8.5, 0.0))
    _carousel(coll, (-10.5, -9.0, 0.0), dur)
    _laundry(coll, (8.0, -4.0, 0.0), (15.0, -6.5, 0.0), rng, dur)
    for x, y, a in ((-8.5, -3.0, 0.0), (1.0, -4.5, math.pi)):
        SS.bench(coll, (x, y, 0.0), a, name='PlayBench')
    head = lib.emission_mat('YdLampHead', '#FFD08A', 8.0)[0] if dusk else lib.mat('YdLampHead', '#EDE8DD', rough=0.4)
    for k, x in enumerate((-20.0, 6.0, 22.0)):
        lib.cyl(0.06, 4.2, (x, YB - 7.2, 0.0), lib.mat('LampPost', '#3A3F44', rough=0.4, metal=0.5), verts=10, name='YdLampPost',
                coll=coll, origin='bottom')
        lib.sphere(0.2, (x, YB - 7.2, 4.3), head, 16, 10, name='YdLampHead', coll=coll)
        if dusk:
            lib.light('POINT', (x, YB - 7.2, 4.0), energy=420.0, color='#FFC27A', size=0.2, name='YdLampLight')
    if dusk:
        lib.light('POINT', (0.0, YB - 0.6, 2.3), energy=160.0, color='#FFD9A0', size=0.15, name='EntLampLight')
    pc.birds(coll, rng, 7, (-40.0, -10.0, 24.0), (9.0, 2.0, 0.6), dur + 1.0, spread=(6, 4, 2), size=0.3, name='YdBird')
    return dict(sun=sun)


# ============================================================================= a06 / a07 granny at the entrance lifts the car with her look
def _granny_car(shot, fps, mode):
    dur = shot['dur']
    rng = random.Random(6)
    coll = lib.collection('Yard')
    yard(coll, rng, dur)
    # kids on the playground: one on the swing, one floating over the sandbox
    k1 = S.folk((0, 0, 0), 0.0, rng, coll, 'kid', height=0.8, name='SwingKid')
    P2.sit(k1, rng)
    _swing(coll, (-12.0, -2.0, 0.0), dur, 0.4, k1)
    k2 = S.folk((-6.0, -6.0, 0.6), 0.6, rng, coll, 'girl', height=0.8, name='FloatKid')
    P2.stand(k2, rng)
    lib.add_sine(k2['root'], 'location', 2, 0.12, 1.7, 0.0)
    FX.aura(coll, k2['root'], '#FF7AB6', r=0.4, z=0.8, t_on=-1.0, strength=3.0, alpha=0.4, name='KidAura', scale=(1, 1, 1.8))
    # granny stands on the walk by the door; the red Lada is parked on the drive to her left
    car_xy = V((-2.6, YB - 3.6, 0.04))
    g_xy = V((0.6, YB - 2.0, 0.12))
    car = lib.car(tuple(car_xy), math.pi, color='#8A2E25', coll=coll, lights=False, rng=rng, name='Lada')
    g = S.folk(tuple(g_xy), S.face(g_xy, car_xy), rng, coll, 'granny', height=0.82, name='Granny')
    P2.stand(g, rng)
    lift = shot.get('events', {}).get('lift', 0.9)
    gaze = (car_xy - g_xy).normalized()
    if mode == 'granny':
        S.key_people(g, 'upperR', 0, [(0, 0.0), (lift - 0.25, 0.0), (lift + 0.1, -1.25), (dur, -1.3)])
        FX.float_glow(coll, car, lift, dur + 0.8, lift=3.4, col='#B48CFF', spin=0.25, name='CarLift', ring=1.3)
        FX.aura(coll, g['root'], '#B48CFF', r=0.5, z=0.9, t_on=lift - 0.2, strength=3.0, alpha=0.5, name='GrAura', scale=(1, 1, 1.8))
        # from along the walk: granny big on the right, the car on the ground on the left; on the lift the camera pulls
        # back and tilts up, the car hangs in the upper middle (framing checked with a pinhole projection)
        ca, cb = V((3.0, YB - 4.2, 1.0)), V((4.5, YB - 5.0, 1.1))
        ta, tb = V((-0.4, YB - 2.5, 1.2)), V((-1.0, YB - 2.8, 2.4))
        cam = lib.camera(tuple(ca), tuple(ta), 24)
        lib.animate_camera(cam, [(0, tuple(ca)), (lift, tuple(ca.lerp(cb, 0.12))), (dur, tuple(cb))],
                           [(0, tuple(ta)), (lift, tuple(ta.lerp(tb, 0.1))), (dur, tuple(tb))], lens_keys=[(0, 24), (lift, 24), (dur, 22)])
    else:
        car.location.z = 2.9
        FX.float_glow(coll, car, 0.0, dur + 0.5, lift=0.9, col='#B48CFF', spin=0.18, name='CarLift', ring=0)
        S.key_people(g, 'upperR', 0, [(0, -1.3), (dur, -1.35)])
        FX.aura(coll, g['root'], '#B48CFF', r=0.5, z=0.9, t_on=-1.0, strength=3.0, alpha=0.5, name='GrAura', scale=(1, 1, 1.8))
        # low, from behind granny (the camera stands where the right entrance bench is, so that bench is taken out of this
        # shot; it is behind the camera in a06 anyway): she is a silhouette on the right, the car floats against the trees
        for ob in coll.objects:
            if ob.name.startswith('EntBench') and ob.type == 'EMPTY' and ob.location.x > 0:
                for ch in ob.children:
                    ch.hide_render = ch.hide_viewport = True
        left = V((-gaze.y, gaze.x, 0))
        c0 = g_xy - gaze * 1.7 + left * 0.35 + V((0, 0, 0.8))
        cam = lib.camera(tuple(c0), tuple(car_xy + V((0, 0, 3.4))), 26)
        lib.animate_camera(cam, [(0, tuple(c0)), (dur, tuple(c0 - gaze * 0.3 + V((0, 0, -0.1))))],
                           [(0, tuple(car_xy + V((0, 0, 3.4)))), (dur, tuple(car_xy + V((0, 0, 4.0))))])
    cam.data.clip_start = 0.05
    lib.bloom(0.3, 1.0, 7)
    return dict(fill=0.35, exposure=0.3, samples=32)


def v_granny(shot, fps):
    return _granny_car(shot, fps, 'granny')


def v_car(shot, fps):
    return _granny_car(shot, fps, 'car')


# ============================================================================= a14 he jumps off a playground bench to fly - and falls
def v_bench(shot, fps):
    dur = shot['dur']
    jump, fall = shot.get('events', {}).get('jump', 1.15), shot.get('events', {}).get('fall', 2.1)
    rng = random.Random(14)
    coll = lib.collection('Yard')
    yard(coll, rng, dur)
    k1 = S.folk((0, 0, 0), 0.0, rng, coll, 'kid', height=0.8, name='SwingKid')
    P2.sit(k1, rng)
    _swing(coll, (-12.0, -2.0, 0.0), dur, 1.3, k1)
    bp = V((-8.5, -3.0, 0.0))                       # the playground bench (faces +y... he stands on the seat)
    j = V((1.0, -0.25, 0)).normalized()             # he jumps to the right across the frame, onto the grass
    hd = S.face(bp, bp + j)
    seat = 0.485
    land = bp + j * 1.8
    h = H.load(coll, (bp.x, bp.y, seat), hd)
    H.key_root(h, 0, (bp.x, bp.y, seat), hd)
    H.key_pose(h, 0, H.pose('stand', head=(0, -18, 0)))
    H.key_pose(h, jump - 0.6, H.pose('arms_up', head=(0, -25, 0)))
    H.key_pose(h, jump - 0.22, H.pose('crouch', head=(0, -10, 0)))
    H.key_root(h, jump - 0.22, (bp.x, bp.y, seat))
    H.key_pose(h, jump + 0.05, H.pose('superman', thigh=-10.0, shin=-25.0, foot=-30.0))
    apex = bp + j * 0.9
    H.key_root(h, jump + 0.35, (apex.x, apex.y, seat + 0.7))
    H.key_pose(h, fall - 0.12, H.pose('superman', thigh=-12.0, shin=-30.0, foot=-30.0, head=(0, -30, 0)))
    H.key_pose(h, fall, H.pose('flat'))
    H.key_root(h, fall, (land.x, land.y, 0.16))
    rig = h['rig']
    rig.rotation_euler.x = 0.0
    rig.keyframe_insert('rotation_euler', index=0, frame=F(jump + 0.05))
    rig.rotation_euler.x = math.radians(35)
    rig.keyframe_insert('rotation_euler', index=0, frame=F(jump + 0.4))
    rig.rotation_euler.x = math.radians(90)
    rig.keyframe_insert('rotation_euler', index=0, frame=F(fall))
    H.key_pose(h, fall + 0.25, H.pose('flat', arm=(40, 150), fore=(40, 160)))
    H.key_pose(h, dur, H.pose('flat', arm=(40, 150), fore=(40, 160), head=(0, -10, 0)))
    H.key_root(h, dur, (land.x, land.y, 0.16))
    FX.smoke(coll, (land.x + j.x * 0.6, land.y + j.y * 0.6, 0.0), 0.6, fall, fall + 0.6, random.Random(14), col='#C9A15A', r0=0.25,
             n=5, rise=0.9, name='LeafDust')
    # leaves fly up where he lands
    SS.leaves_burst(coll, (land.x + j.x * 0.5, land.y + j.y * 0.5, 0.1), fall, rng, n=30, col=('#D9A13A', '#E0B54A', '#C9732E'))
    # a pigeon-eye view from the lawn, the block and the entrance behind him
    r = V((j.y, -j.x, 0))
    c0 = bp + j * 0.9 - r * 3.6 + V((0, 0, 0.75))
    tgt0 = bp + j * 0.5 + V((0, 0, 0.95))
    cam = lib.camera(tuple(c0), tuple(tgt0), 30)
    lib.animate_camera(cam, [(0, tuple(c0)), (dur, tuple(c0 + j * 0.6))], [(0, tuple(tgt0)), (dur, tuple(bp + j * 1.6 + V((0, 0, 0.4))))])
    cam.data.clip_start = 0.05
    lib.bloom(0.3, 1.0, 7)
    return dict(fill=0.45, exposure=0.3, samples=32)


# ============================================================================= a13 on the roof of his block: looking for his power
ROOF_Z = 5 * FLOOR + 0.4 + 0.35                  # the top of the home block (facade + roof slab)


def roof(coll, rng):
    """Props on the home block's roof: tar, parapets, the exit hut, brick vents, TV aerials, a dish; two taller blocks
    and the far towers of the city behind it."""
    z = ROOF_Z
    tar = lib.mat('RoofTar', '#4C4B4A', rough=0.9, var=0.25, var_scale=0.6, bump=0.15, bump_scale=12)
    lib.box((72, 12, 0.03), (0, YB + 6, z), tar, bevel=0, name='RoofTar', coll=coll, origin='bottom')
    edge = lib.mat('Parapet', '#9C958A', rough=0.85)
    for y in (YB + 0.12, YB + 11.88):
        lib.box((72, 0.24, 0.45), (0, y, z), edge, bevel=0.02, name='Parapet', coll=coll, origin='bottom')
    hut = lib.mat('RoofHut', '#B4AC9E', rough=0.85)
    lib.box((2.6, 2.4, 2.4), (-3.5, YB + 6.5, z), hut, bevel=0.03, name='RoofHut', coll=coll, origin='bottom')
    lib.box((2.9, 2.7, 0.15), (-3.5, YB + 6.5, z + 2.4), edge, bevel=0.02, name='RoofHutTop', coll=coll, origin='bottom')
    lib.box((0.9, 0.06, 1.9), (-3.5, YB + 5.28, z), lib.mat('RoofDoor', '#5E6B73', rough=0.4, metal=0.4), bevel=0.01,
            name='RoofDoor', coll=coll, origin='bottom')
    brick = lib.mat('VentBrick', '#9A5A44', rough=0.85, var=0.2, var_scale=6)
    for x, y in ((-9.0, YB + 3.0), (6.5, YB + 8.0), (12.0, YB + 3.5), (-15.0, YB + 8.5)):
        lib.box((0.9, 0.9, 1.1), (x, y, z), brick, bevel=0.02, name='Vent', coll=coll, origin='bottom')
        lib.box((1.1, 1.1, 0.08), (x, y, z + 1.1), edge, bevel=0.01, name='VentCap', coll=coll, origin='bottom')
    iron = lib.mat('Aerial', '#3A3D40', rough=0.4, metal=0.6)
    for x, y, h in ((-0.5, YB + 8.5, 3.2), (4.5, YB + 5.5, 2.6), (9.5, YB + 9.0, 3.6), (-7.5, YB + 6.0, 2.9)):
        lib.cyl(0.03, h, (x, y, z), iron, verts=6, name='AerialPole', coll=coll, origin='bottom')
        for j in range(3):
            w = 1.2 - j * 0.3
            lib.box((w, 0.03, 0.03), (x, y, z + h - 0.25 - j * 0.32), iron, rot=(0, 0, rng.uniform(-0.2, 0.2)), bevel=0,
                    name='AerialBar', coll=coll)
    lib.sphere(0.45, (-6.0, YB + 1.2, z + 1.0), lib.mat('Dish', '#E8E6E1', rough=0.4), 16, 8, scale=(1, 0.35, 1), name='Dish',
               coll=coll)
    lib.cyl(0.03, 1.0, (-6.0, YB + 1.4, z), iron, verts=6, name='DishPole', coll=coll, origin='bottom')
    # behind the block: two nine-storey blocks, then the city far away in the haze
    facs = pcity.facade_set(0.0, prefix='Yr')
    _block(coll, -30, 0, YB + 40, 12, 9, -1, facs[1][0], rng, 'BackBlockA', balconies=False)
    _block(coll, 8, 40, YB + 46, 12, 9, -1, facs[3][0], rng, 'BackBlockB', balconies=False)
    tower = facs[0][0]
    for k in range(16):
        x, y = rng.uniform(-420, 420), rng.uniform(420, 800)
        w, h = rng.uniform(25, 50), rng.uniform(70, 190)
        lib.box((w, w * rng.uniform(0.7, 1.2), h), (x, y, 0), tower, bevel=0.5, name='FarTower', coll=coll, origin='bottom')


def v_search(shot, fps):
    import sila_p1
    dur = shot['dur']
    rng = random.Random(13)
    coll = lib.collection('Yard')
    yard(coll, rng, dur, sun_dir=(-0.6, -0.45, 0.42))
    roof(coll, rng)
    z = ROOF_Z + 0.03
    hp = V((1.5, YB + 1.7, z))
    h = H.load(coll, tuple(hp), S.face(hp, hp + V((-0.35, -1.0, 0))))
    # he tries: looks up, calls the sky with both arms, pushes at it hard, then nothing - a shrug
    H.key_pose(h, 0, H.pose('stand', head=(0, -20, 0)))
    H.key_pose(h, 0.25, H.pose('stand', head=(0, -22, 0)))
    H.key_pose(h, 0.6, H.pose('arms_up', head=(0, -24, 0)))
    H.key_pose(h, 1.0, H.pose('arms_up', lean=-4.0, head=(0, -26, 0)))
    H.key_pose(h, 1.35, H.pose('hands_front', arm=(22, 88), fore=(16, 94), lean=12.0, head=(0, -8, 0)))
    H.key_pose(h, 1.85, H.pose('hands_front', arm=(22, 86), fore=(16, 92), lean=14.0, head=(0, -6, 4)))
    H.key_pose(h, min(dur, 2.25), H.pose('shrug', head=(-8, -4, 6)))
    H.key_pose(h, dur, H.pose('shrug', head=(-10, -6, 8)))
    h['body']['eye_look'], h['body']['eye_spread'] = (0.0, 0.55), 0.2           # looking up at the sky
    # pigeons scatter off the parapet
    pc.birds(coll, rng, 6, (hp.x - 1.5, YB + 0.3, z + 0.5), (-3.5, -2.5, 2.2), dur + 0.5, spread=(1.5, 0.4, 0.3), size=0.35,
             col='#6E7178', name='Pigeon')
    # low on the roof in front of him (the parapet behind the camera): his face, the aerials, the hut and the sky
    # where everybody else flies
    c0, c1 = V((2.4, YB + 0.45, z + 0.6)), V((2.25, YB + 0.62, z + 0.58))
    t0, t1 = hp + V((-0.05, 0, 0.85)), hp + V((-0.1, 0, 0.9))
    cam = lib.camera(tuple(c0), tuple(t0), 24)
    lib.animate_camera(cam, [(0, tuple(c0)), (dur, tuple(c1))], [(0, tuple(t0)), (dur, tuple(t1))])
    cam.data.clip_start = 0.05
    cam.data.clip_end = 3000
    f = (t0 - c0).normalized()
    sila_p1._sky_flyers(lib.collection('RoofFlyers'), rng, c0, f, dur, n=6, dmin=12, dmax=45, scale=1.3, view=(c0, t0, 24))
    lib.bloom(0.3, 1.0, 7)
    return dict(fill=0.45, exposure=0.3, samples=32)


# ============================================================================= a16-a19 the evening in the courtyard
EVE_SUN = (-0.78, -0.58, 0.07)                   # low orange sun behind the opposite block
EVE_HERO = V((14.0, 2.9, 0.06))                  # where he stops on the lawn path, in front of the hedge gap
EVE_BUSH = V((11.7, 0.2, 0.0))                   # the bush on the lawn the neighbour falls into


def _ev(shot, k, d):
    return shot.get('events', {}).get(k, d)


def _eve(rng, dur, name):
    coll = lib.collection(name)
    yard(coll, rng, dur, sun_dir=EVE_SUN, dusk=True)
    SS.hedge(coll, random.Random(170), (EVE_BUSH.x - 1.5, EVE_BUSH.y, 0), (EVE_BUSH.x + 1.5, EVE_BUSH.y, 0), h=1.0, w=1.1,
             name='EveBush')
    return coll


def v_evening(shot, fps):
    """a16: he walks home along the lawn path; the neighbour comes over the block, over his head, off across the yard."""
    dur = shot['dur']
    over = _ev(shot, 'over', 2.35)
    rng = random.Random(16)
    coll = _eve(rng, dur, 'Evening')
    a, b = V((14.0, -0.7, 0.06)), EVE_HERO
    h = H.load(coll, tuple(a), S.face(a, b))
    H.walk(h, 0.0, dur, [(a.x, a.y), (b.x, b.y)], speed=(b - a).length / dur * 0.98)
    h['body']['eye_spread'] = 0.3
    h['body']['eye_looks'] = [(over - 0.9, over + 0.4, 0.0, 0.75)]           # looks up at the neighbour going over
    hp = a.lerp(b, over / dur)
    nb = S.folk((0, 0, 0), 0, rng, coll, 'neighbour', name='NbEve')
    S.fly_pose(nb, 'one')
    p0, p1, p2 = V((14.8, 11.0, 5.2)), hp + V((0.15, 0.0, 2.5)), hp + V((-2.5, -26.0, 7.5))
    t0 = over - (p1 - p0).length / 6.0
    S.fly(nb, [(t0, tuple(p0)), (over, tuple(p1)), (dur + 0.5, tuple(p2))], tilt=1.3, bob=0.05)
    FX.aura(coll, nb['root'], '#FFC857', r=0.45, z=0.9, t_on=-1.0, strength=3.5, alpha=0.55, name='NbEveAura', scale=(1, 1, 1.9))
    # low in the hedge gap, pulling back as he comes; the lawn, the lamps and the lit block across behind him
    c0, c1 = V((14.3, 4.6, 1.1)), V((14.3, 5.6, 1.15))
    cam = lib.camera(tuple(c0), tuple(a + V((0, 0, 1.4))), 30)
    lib.animate_camera(cam, [(0, tuple(c0)), (dur, tuple(c1))],
                       [(0, tuple(a + V((0, 0, 1.4)))), (over, tuple(hp + V((0, 0, 1.7)))), (dur, tuple(b + V((0, 0, 1.6))))])
    cam.data.clip_start = 0.05
    lib.bloom(0.4, 1.0, 7)
    return dict(fill=0.5, fill_col='#FFD9B0', exposure=0.25, samples=32)


def v_crash(shot, fps):
    """a17: flying off over the lawn, the neighbour's glow goes out next to me and he drops head first into a bush."""
    dur = shot['dur']
    crash = _ev(shot, 'crash', 0.6)
    rng = random.Random(17)
    coll = _eve(rng, dur, 'Crash')
    hp = EVE_HERO
    h = H.load(coll, tuple(hp), S.face(hp, V((13.6, -5.0, 0))))
    H.key_pose(h, 0, H.pose('stand', head=(0, -22, 0)))
    H.key_pose(h, crash - 0.1, H.pose('stand', head=(0, -12, 0)))
    H.key_pose(h, crash + 0.25, H.pose('stand', head=(-30, 6, 0)))                  # turns to the bush
    H.key_pose(h, crash + 0.7, H.pose('shrug', head=(-26, 4, 6)))
    H.key_pose(h, dur, H.pose('shrug', arm=(30, 20), head=(-24, 6, 8)))
    h['body']['eye_looks'] = [(0.0, crash, 0.0, 0.7), (crash + 0.15, dur + 1, -0.6, -0.2)]
    q = EVE_BUSH + V((0.5, 0.0, 0.0))
    d = V((0.0, -1.0, 0.0))
    nb = S.folk((0, 0, 0), 0, rng, coll, 'neighbour', name='NbCrash')
    S.fly_pose(nb, 'forward')
    root = nb['root']
    hd = S.face(q, q + d)
    for t, loc, tilt in ((0, hp + V((-0.5, -0.8, 3.4)), 1.4), (crash - 0.25, q - d * 1.2 + V((0, 0, 2.6)), 1.9),
                         (crash, q + V((0, 0, 2.3)), 2.6), (crash + 0.25, q + V((0, 0, 1.95)), 2.9),
                         (dur, q + V((0, 0, 1.9)), 2.95)):     # root at his feet: head in the bush, legs up
        root.location = loc
        root.rotation_euler = (tilt, 0, hd)
        root.keyframe_insert('location', frame=F(t))
        root.keyframe_insert('rotation_euler', frame=F(t))
    S.key_people(nb, 'thighL', 0, [(crash + 0.3, 0.1), (crash + 0.6, 0.6), (crash + 0.9, 0.1), (dur, 0.5)])
    FX.aura(coll, root, '#FFC857', r=0.45, z=0.9, t_on=-1.0, t_off=crash - 0.3, strength=3.5, alpha=0.55, name='NbCrAura',
            scale=(1, 1, 1.9))
    SS.leaves_burst(coll, (q.x, q.y, 1.0), crash, rng)
    # from the lawn: the bush, him behind it, the lit block and the entrance lamp
    c0, c1 = V((13.5, -3.3, 1.25)), V((13.5, -3.0, 1.25))
    tg0, tg1 = V((13.2, 1.5, 1.35)), V((13.1, 1.5, 1.2))
    cam = lib.camera(tuple(c0), tuple(tg0), 30)
    lib.animate_camera(cam, [(0, tuple(c0)), (dur, tuple(c1))], [(0, tuple(tg0)), (dur, tuple(tg1))])
    cam.data.clip_start = 0.05
    lib.bloom(0.4, 1.0, 7)
    return dict(fill=0.5, fill_col='#FFD9B0', exposure=0.25, samples=32)


def v_realize(shot, fps):
    """a18: close on him; behind, a girl with fire in her palm and a guy floating; a wave from him puts both out."""
    import sila_p1
    dur = shot['dur']
    wave, others = _ev(shot, 'wave', 3.4), _ev(shot, 'others', 2.3)
    rng = random.Random(18)
    coll = _eve(rng, dur, 'Realize')
    hp = EVE_HERO
    cam_p = V((14.9, -0.6, 1.25))
    h = H.load(coll, tuple(hp), S.face(hp, cam_p) + math.radians(18))
    H.key_pose(h, 0, H.pose('hands_front', head=(0, 24, 0)))
    H.key_pose(h, others - 0.4, H.pose('hands_front', head=(0, 20, 0)))
    H.key_pose(h, others, H.pose('stand', head=(-30, 0, 0)))
    H.key_pose(h, wave - 0.2, H.pose('stand', head=(-26, -2, 0)))
    H.key_pose(h, wave + 0.6, H.pose('shrug', head=(0, -4, 6)))
    H.key_pose(h, dur, H.pose('shrug', head=(4, -6, 8)))
    # behind him on the drive, beyond the hedge gap
    gp, bp = V((12.8, 6.2, 0.04)), V((15.4, 6.5, 0.04))
    g = S.folk(tuple(gp), S.face(gp, hp), rng, coll, 'girl', name='GirlF')
    P2.stand(g, rng)
    S.key_people(g, 'upperR', 0, [(0, -1.1), (wave + 0.4, -1.1), (wave + 0.8, -0.2)])
    S.key_people(g, 'foreR', 0, [(0, -0.6), (wave + 0.4, -0.6), (wave + 0.8, -0.2)])
    FX.flame(coll, sila_p1.palm(g, coll, 'GirlPalm'), (0, 0, 0.05), -1.0, wave + 0.2, scale=0.45, rng=rng, name='GirlFlame')
    b = S.folk((bp.x, bp.y, bp.z + 0.8), S.face(bp, hp), rng, coll, 'sparky', name='FloatGuy')
    P2.stand(b, rng)
    FX.key_loc(b['root'], [(0, (bp.x, bp.y, bp.z + 0.75)), (wave + 0.25, (bp.x, bp.y, bp.z + 0.82)), (wave + 0.5, tuple(bp))])
    lib.add_sine(b['root'], 'location', 2, 0.04, 1.4)
    FX.aura(coll, b['root'], '#7FD8FF', r=0.5, z=0.9, t_on=-1.0, t_off=wave + 0.2, strength=3.5, alpha=0.5, name='FgAura',
            scale=(1, 1, 1.9))
    FX.aura(coll, g['root'], '#FF9C5B', r=0.5, z=0.9, t_on=-1.0, t_off=wave + 0.2, strength=3.0, alpha=0.4, name='GfAura',
            scale=(1, 1, 1.9))
    FX.ripple(coll, (hp.x, hp.y, hp.z + 0.05), wave, 1.1, 10.0)
    c1 = cam_p + (hp - cam_p).normalized() * 0.9
    cam = lib.camera(tuple(cam_p), tuple(hp + V((0, 0, 1.0))), 40)
    lib.animate_camera(cam, [(0, tuple(cam_p)), (dur, tuple(c1))], [(0, tuple(hp + V((0, 0, 1.0)))), (dur, tuple(hp + V((0, 0, 1.05))))])
    cam.data.clip_start = 0.05
    lib.bloom(0.4, 1.0, 7)
    return dict(fill=0.5, fill_col='#FFD9B0', exposure=0.25, samples=32)


def v_ordinary(shot, fps):
    """a19: the camera cranes up from him over the evening yard full of glowing people: eight billion superhumans,
    and one ordinary man in a plain white ring."""
    import sila_p1
    dur = shot['dur']
    one = _ev(shot, 'one', 2.3)
    rng = random.Random(19)
    coll = _eve(rng, dur, 'Ordinary')
    hp = EVE_HERO
    f, r = V((0, 1, 0)), V((1, 0, 0))
    c0 = hp - f * 3.0 + r * 0.5 + V((0, 0, 1.4))
    c1 = hp - f * 7.0 - r * 1.5 + V((0, 0, 6.0))
    h = H.load(coll, tuple(hp), S.face(hp, c0))
    H.key_pose(h, 0, H.pose('stand', head=(0, -30, 0)))
    H.key_pose(h, dur, H.pose('stand', head=(10, -38, 0)))
    h['body']['eye_look'] = (0.0, 0.6)
    # people with powers all over the yard: on the lawn, the drive and the playground, three on the roof edge
    spots = []
    while len(spots) < 22:
        q = V((rng.uniform(7.0, 21.0), rng.uniform(-6.0, 8.8), 0.0))
        if (q - hp).length < 2.6 or (q - EVE_BUSH).length < 2.0 or abs(q.y - (YB - 7.6)) < 0.8 or abs(q.y - (YB - 4.3)) < 1.2:
            continue
        if any((q - p).length < 1.3 for p in spots):
            continue
        spots.append(q)
    for k, q in enumerate(spots):
        z = 0.04 if q.y > YB - 6.8 else 0.0
        pp = S.folk((q.x, q.y, z), rng.uniform(0, 6.28), rng, coll, None, name=f'Ord{k}')
        P2.stand(pp, rng)
        if k % 5 == 2:                                    # a few float
            FX.key_loc(pp['root'], [(0, (q.x, q.y, z + 0.5)), (dur, (q.x, q.y, z + 0.9))])
        FX.aura(coll, pp['root'], AURA[k % len(AURA)], r=0.5, z=0.9, t_on=-1, strength=7.0, alpha=0.6, name=f'OrdA{k}',
                scale=(1, 1, 1.9))                    # bright: they read as glowing from the crane height
    for k, x in enumerate((8.0, 14.5, 21.0)):
        pp = S.folk((x, YB + 0.6, ROOF_Z + 0.03), 0.0, rng, coll, None, name=f'RoofP{k}')
        P2.stand(pp, rng)
        FX.aura(coll, pp['root'], AURA[(k + 3) % len(AURA)], r=0.5, z=0.9, t_on=-1, strength=7.0, alpha=0.6, name=f'RoofA{k}',
                scale=(1, 1, 1.9))
    sila_p1._sky_flyers(coll, rng, hp - f * 10, f, dur, n=10, view=(c1, hp + f * 1.5, 28), dmin=10, dmax=35)
    sila_p1._sky_flyers(coll, rng, hp - f * 10, f, dur, n=6, view=(c0, hp + V((0, 0, 1.0)), 28), dmin=8, dmax=30)
    # one ordinary man: a plain white ring around him lights up, a soft spot from above
    m, s, a = FX.glow('PlainRing', '#FFFFFF', 3.0, alpha=0.8)
    bpy.ops.mesh.primitive_torus_add(major_radius=1.1, minor_radius=0.03, major_segments=64, minor_segments=8,
                                     location=(hp.x, hp.y, hp.z + 0.04))
    ring = bpy.context.active_object
    for cc in ring.users_collection:
        cc.objects.unlink(ring)
    coll.objects.link(ring)
    ring.data.materials.append(m)
    FX.key(a, [(0, 0.0), (one - 0.1, 0.0), (one + 0.3, 0.85), (dur, 0.85)])
    spot = lib.light('SPOT', (hp.x, hp.y, hp.z + 7.0), (0, 0, 0), energy=0.0, color='#FFF4E6', size=0.3, name='PlainSpot')
    spot.data.spot_size = math.radians(28)
    for t, e in ((0, 0.0), (one - 0.1, 0.0), (one + 0.3, 900.0), (dur, 900.0)):
        spot.data.energy = e
        spot.data.keyframe_insert('energy', frame=F(t))
    cam = lib.camera(tuple(c0), tuple(hp + V((0, 0, 1.0))), 28)
    lib.animate_camera(cam, [(0, tuple(c0)), (one, tuple(c0.lerp(c1, 0.55))), (dur, tuple(c1))],
                       [(0, tuple(hp + V((0, 0, 1.0)))), (one, tuple(hp + V((0, 0, 0.8)))), (dur, tuple(hp + f * 1.5 + V((0, 0, 0.6))))])
    cam.data.clip_start = 0.05
    lib.bloom(0.4, 1.0, 7)
    return dict(fill=0.45, fill_col='#FFD9B0', exposure=0.25, samples=32)
