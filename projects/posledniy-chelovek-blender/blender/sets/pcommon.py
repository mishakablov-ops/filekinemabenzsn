"""Shared pieces for posledniy-chelovek-blender (real colours, built from code):
daylight / blue-hour / night skies with a Milky Way, realistic facades with windows that can go dark,
the hero (white cap, orange hoodie, jeans), stopped cars with open doors, a grey wolf with a trot cycle.
"""
import bpy, math, random
from mathutils import Vector
import lib
from lib import C
import people2 as P2

FONT = r'C:\Windows\Fonts\arialbd.ttf'
FONT_REG = r'C:\Windows\Fonts\arial.ttf'


# ----------------------------------------------------------------------------- skies and light
def sun(direction, energy=4.0, color='#FFF3E2', angle=1.5, name='Sun', shadow=True):
    d = Vector(direction).normalized()
    s = lib.light('SUN', (0, 0, 0), energy=energy, color=color, size=angle, name=name, volume=1.0)
    s.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    s.data.use_shadow = shadow
    return s


def day_sky(sun_dir, top='#3F72B8', horizon='#C7D9EA', below='#8E8C86', strength=1.0, glow='#FFF0DA', fog=0.0012,
            fog_col='#C9D6E2', glow_size=0.1, glow_strength=1.6):
    return lib.world_sky_view_gradient(top, horizon, below, strength=strength, fog=fog, fog_col=fog_col, aniso=0.4,
                                       glow_dir=sun_dir, glow_col=glow, glow_size=glow_size, glow_strength=glow_strength)


def night_sky(milky=1.0, stars=1.0, horizon='#0F1626', top='#03050A', airglow=0.6, band_n=(-0.729, 0.547, -0.411),
              core=(0.519, 0.833, 0.19)):
    """Dark sky with fine stars and a Milky Way band (great circle normal to band_n, bright bulge towards `core`,
    dust lanes along the middle). Emission only, so it reads in AgX at higher exposure."""
    w, nt, bg = lib.world_color('#000000', 1.0)
    L = nt.links
    tc = nt.nodes.new('ShaderNodeTexCoord')
    D = nt.nodes.new('ShaderNodeVectorMath'); D.operation = 'NORMALIZE'; L.new(tc.outputs['Generated'], D.inputs[0])
    sep = nt.nodes.new('ShaderNodeSeparateXYZ'); L.new(D.outputs[0], sep.inputs[0])

    def m(op, a=None, b=None, v1=None, v2=None):
        n = nt.nodes.new('ShaderNodeMath'); n.operation = op
        if a is not None: L.new(a, n.inputs[0])
        if b is not None: L.new(b, n.inputs[1])
        if v1 is not None: n.inputs[0].default_value = v1
        if v2 is not None: n.inputs[1].default_value = v2
        return n.outputs[0]

    # base gradient by elevation
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position = 0.0; ramp.color_ramp.elements[0].color = C('#05070B')
    ramp.color_ramp.elements[1].position = 0.75; ramp.color_ramp.elements[1].color = C(top)
    e = ramp.color_ramp.elements.new(0.5); e.color = C(horizon)
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = -1; mr.inputs['From Max'].default_value = 1
    L.new(sep.outputs['Z'], mr.inputs['Value']); L.new(mr.outputs['Result'], ramp.inputs['Fac'])
    base = ramp.outputs['Color']
    # band
    N = Vector(band_n).normalized()
    dn = nt.nodes.new('ShaderNodeVectorMath'); dn.operation = 'DOT_PRODUCT'; L.new(D.outputs[0], dn.inputs[0]); dn.inputs[1].default_value = N
    sq = m('MULTIPLY', dn.outputs['Value'], dn.outputs['Value'])
    band = m('EXPONENT', m('MULTIPLY', sq, v2=-1 / 0.018))            # width ~ 0.13 rad
    narrow = m('EXPONENT', m('MULTIPLY', sq, v2=-1 / 0.0016))         # dust lane width
    G = Vector(core).normalized()
    dg = nt.nodes.new('ShaderNodeVectorMath'); dg.operation = 'DOT_PRODUCT'; L.new(D.outputs[0], dg.inputs[0]); dg.inputs[1].default_value = G
    bulge = m('POWER', m('MAXIMUM', dg.outputs['Value'], v2=0.0), v2=3.0)
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 6.0; nz.inputs['Detail'].default_value = 12
    nz.inputs['Roughness'].default_value = 0.7
    L.new(D.outputs[0], nz.inputs['Vector'])
    clump = nt.nodes.new('ShaderNodeMapRange'); clump.inputs['From Min'].default_value = 0.38; clump.inputs['From Max'].default_value = 0.7
    clump.inputs['To Min'].default_value = 0.2; clump.inputs['To Max'].default_value = 1.3
    L.new(nz.outputs['Fac'], clump.inputs['Value'])
    # soft mottling (fine grain read as sand on the first PC proof)
    grain = nt.nodes.new('ShaderNodeTexNoise'); grain.inputs['Scale'].default_value = 38.0; grain.inputs['Detail'].default_value = 4
    L.new(D.outputs[0], grain.inputs['Vector'])
    gr = nt.nodes.new('ShaderNodeMapRange'); gr.inputs['From Min'].default_value = 0.3; gr.inputs['From Max'].default_value = 0.7
    gr.inputs['To Min'].default_value = 0.75; gr.inputs['To Max'].default_value = 1.2
    L.new(grain.outputs['Fac'], gr.inputs['Value'])
    nz2 = nt.nodes.new('ShaderNodeTexNoise'); nz2.inputs['Scale'].default_value = 11.0; nz2.inputs['Detail'].default_value = 10
    nz2.inputs['Roughness'].default_value = 0.65
    L.new(D.outputs[0], nz2.inputs['Vector'])
    dust = nt.nodes.new('ShaderNodeMapRange'); dust.inputs['From Min'].default_value = 0.46; dust.inputs['From Max'].default_value = 0.6
    L.new(nz2.outputs['Fac'], dust.inputs['Value'])
    lane = m('SUBTRACT', v1=1.0, b=m('MULTIPLY', m('MULTIPLY', narrow, dust.outputs['Result']), v2=0.9))
    glow = m('MULTIPLY', m('ADD', band, m('MULTIPLY', m('MULTIPLY', bulge, band), v2=2.5)), clump.outputs['Result'])
    glow = m('MULTIPLY', m('MULTIPLY', glow, gr.outputs['Result']), lane)
    glow = m('MULTIPLY', glow, v2=0.032 * milky)
    tint = nt.nodes.new('ShaderNodeMix'); tint.data_type = 'RGBA'
    L.new(nz.outputs['Fac'], tint.inputs['Factor'])
    tint.inputs['A'].default_value = C('#AFC0E6'); tint.inputs['B'].default_value = C('#F2DEC2')
    comb = nt.nodes.new('ShaderNodeMix'); comb.data_type = 'RGBA'; comb.blend_type = 'MULTIPLY'; comb.inputs['Factor'].default_value = 1
    L.new(tint.outputs['Result'], comb.inputs['A'])
    gx = nt.nodes.new('ShaderNodeCombineXYZ')
    for s in 'XYZ':
        L.new(glow, gx.inputs[s])
    L.new(gx.outputs[0], comb.inputs['B'])
    # stars sized in pixels: ~1 rad is 1000-1300 px in these 9:16 night frames, so a Voronoi scale of S gives cells of
    # ~1100/S px; the star is the cell's point (distance < r cells), gated by the cell colour so only some cells shine
    def layer(scale, r, keep, gain, sharp=3.0, band_keep=0.0):
        v = nt.nodes.new('ShaderNodeTexVoronoi'); v.inputs['Scale'].default_value = scale
        L.new(D.outputs[0], v.inputs['Vector'])
        f = nt.nodes.new('ShaderNodeMapRange'); f.inputs['From Min'].default_value = r; f.inputs['From Max'].default_value = 0.0
        L.new(v.outputs['Distance'], f.inputs['Value'])
        cs = nt.nodes.new('ShaderNodeSeparateColor'); L.new(v.outputs['Color'], cs.inputs[0])
        thr = m('SUBTRACT', v1=1.0 - keep, b=m('MULTIPLY', band, v2=band_keep)) if band_keep else None
        gate = m('GREATER_THAN', cs.outputs[1], thr) if thr is not None else m('GREATER_THAN', cs.outputs[1], v2=1.0 - keep)
        mag = m('ADD', m('POWER', cs.outputs[0], v2=4.0), v2=0.12)          # few bright, many faint
        return m('MULTIPLY', m('MULTIPLY', m('POWER', f.outputs['Result'], v2=sharp), gate), m('MULTIPLY', mag, v2=gain))
    star = layer(62, 0.09, 0.55, 2.2 * stars)                                    # field stars, ~1.5 px
    star = m('ADD', star, layer(19, 0.045, 0.22, 7.0 * stars, sharp=2.0))      # a few bright ones, ~2 px
    dense = layer(170, 0.16, 0.25, 1.6 * milky, band_keep=0.7)                  # star clouds of the band
    star = m('ADD', star, m('MULTIPLY', dense, m('MULTIPLY', band, lane)))
    above = m('GREATER_THAN', sep.outputs['Z'], v2=-0.02)
    star = m('MULTIPLY', star, above)
    glow_above = m('MULTIPLY', above, v2=1.0)
    sx = nt.nodes.new('ShaderNodeCombineXYZ')
    for s in 'XYZ':
        L.new(star, sx.inputs[s])
    add1 = nt.nodes.new('ShaderNodeMix'); add1.data_type = 'RGBA'; add1.blend_type = 'ADD'; add1.inputs['Factor'].default_value = 1
    L.new(base, add1.inputs['A']); L.new(comb.outputs['Result'], add1.inputs['B'])
    add2 = nt.nodes.new('ShaderNodeMix'); add2.data_type = 'RGBA'; add2.blend_type = 'ADD'; add2.inputs['Factor'].default_value = 1
    L.new(add1.outputs['Result'], add2.inputs['A']); L.new(sx.outputs[0], add2.inputs['B'])
    L.new(add2.outputs['Result'], bg.inputs['Color'])
    bg.inputs['Strength'].default_value = 1.0
    return w


# ----------------------------------------------------------------------------- materials
def facade(name, cols=('#D8CCB4', '#C9C4BA', '#B9B2A6'), glass='#34404C', lit=0.0, glow='#FFC98E', px=3.2, pz=3.1,
           win=(0.2, 0.8, 0.24, 0.74), out_key=None, glow_strength=5.0):
    """Realistic facade on axis-aligned boxes: windows from object coords (period px along x+y, pz in height),
    per-building wall tone from Object Info random, glossy glass that reflects the sky, lit windows (fraction `lit`).
    Returns (material, lit Value node, out Value node). Animate `out` 0 -> 1: buildings go dark one after another."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    L = nt.links
    p = nt.nodes['Principled BSDF']
    lit_v = nt.nodes.new('ShaderNodeValue'); lit_v.outputs[0].default_value = lit
    out_v = nt.nodes.new('ShaderNodeValue'); out_v.outputs[0].default_value = 0.0
    tc = nt.nodes.new('ShaderNodeTexCoord')
    oi = nt.nodes.new('ShaderNodeObjectInfo')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ'); L.new(tc.outputs['Object'], sep.inputs[0])

    def mm(op, a=None, b=None, v1=None, v2=None):
        n = nt.nodes.new('ShaderNodeMath'); n.operation = op
        if a is not None: L.new(a, n.inputs[0])
        if b is not None: L.new(b, n.inputs[1])
        if v1 is not None: n.inputs[0].default_value = v1
        if v2 is not None: n.inputs[1].default_value = v2
        return n.outputs[0]

    us = mm('MULTIPLY', mm('ADD', sep.outputs['X'], sep.outputs['Y']), v2=1 / px)
    vs = mm('MULTIPLY', sep.outputs['Z'], v2=1 / pz)
    fu, fv = mm('FRACT', us), mm('FRACT', vs)
    band_u = mm('MULTIPLY', mm('GREATER_THAN', fu, v2=win[0]), mm('LESS_THAN', fu, v2=win[1]))
    band_v = mm('MULTIPLY', mm('GREATER_THAN', fv, v2=win[2]), mm('LESS_THAN', fv, v2=win[3]))
    geo = nt.nodes.new('ShaderNodeNewGeometry')
    sn = nt.nodes.new('ShaderNodeSeparateXYZ'); L.new(geo.outputs['Normal'], sn.inputs[0])
    wall = mm('LESS_THAN', mm('ABSOLUTE', sn.outputs['Z']), v2=0.5)
    winmask = mm('MULTIPLY', mm('MULTIPLY', band_u, band_v), wall)
    cell = nt.nodes.new('ShaderNodeCombineXYZ')
    L.new(mm('FLOOR', us), cell.inputs['X']); L.new(mm('FLOOR', vs), cell.inputs['Y'])
    L.new(mm('MULTIPLY', oi.outputs['Random'], v2=97.0), cell.inputs['Z'])
    wn = nt.nodes.new('ShaderNodeTexWhiteNoise'); wn.noise_dimensions = '3D'
    L.new(cell.outputs[0], wn.inputs['Vector'])
    on = mm('LESS_THAN', wn.outputs['Value'], lit_v.outputs[0])
    alive = mm('GREATER_THAN', oi.outputs['Random'], out_v.outputs[0])        # building still has power
    em = mm('MULTIPLY', mm('MULTIPLY', winmask, on), alive)
    wcol = nt.nodes.new('ShaderNodeMix'); wcol.data_type = 'RGBA'
    L.new(wn.outputs['Color'], wcol.inputs['Factor'])
    wcol.inputs['A'].default_value = C(glow); wcol.inputs['B'].default_value = C('#FFE7C4')
    L.new(wcol.outputs['Result'], p.inputs['Emission Color'])
    L.new(mm('MULTIPLY', em, v2=glow_strength), p.inputs['Emission Strength'])
    tone = nt.nodes.new('ShaderNodeValToRGB')
    cr = tone.color_ramp
    cr.interpolation = 'CONSTANT'
    cr.elements[0].position = 0.0; cr.elements[0].color = C(cols[0])
    cr.elements[1].position = 0.67; cr.elements[1].color = C(cols[2])
    e = cr.elements.new(0.34); e.color = C(cols[1])
    L.new(oi.outputs['Random'], tone.inputs['Fac'])
    # stains / weathering
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 0.35; nz.inputs['Detail'].default_value = 6
    L.new(tc.outputs['Object'], nz.inputs['Vector'])
    vr = nt.nodes.new('ShaderNodeMapRange'); vr.inputs['To Min'].default_value = 0.86; vr.inputs['To Max'].default_value = 1.08
    L.new(nz.outputs['Fac'], vr.inputs['Value'])
    vx = nt.nodes.new('ShaderNodeCombineXYZ')
    for s in 'XYZ':
        L.new(vr.outputs['Result'], vx.inputs[s])
    wallc = nt.nodes.new('ShaderNodeMix'); wallc.data_type = 'RGBA'; wallc.blend_type = 'MULTIPLY'; wallc.inputs['Factor'].default_value = 1
    L.new(tone.outputs['Color'], wallc.inputs['A']); L.new(vx.outputs[0], wallc.inputs['B'])
    bc = nt.nodes.new('ShaderNodeMix'); bc.data_type = 'RGBA'
    L.new(winmask, bc.inputs['Factor']); L.new(wallc.outputs['Result'], bc.inputs['A']); bc.inputs['B'].default_value = C(glass)
    L.new(bc.outputs['Result'], p.inputs['Base Color'])
    rr = nt.nodes.new('ShaderNodeMapRange'); rr.inputs['To Min'].default_value = 0.85; rr.inputs['To Max'].default_value = 0.08
    L.new(winmask, rr.inputs['Value']); L.new(rr.outputs['Result'], p.inputs['Roughness'])
    sp = nt.nodes.new('ShaderNodeMapRange'); sp.inputs['To Min'].default_value = 0.3; sp.inputs['To Max'].default_value = 0.9
    L.new(winmask, sp.inputs['Value']); L.new(sp.outputs['Result'], p.inputs['Specular IOR Level'])
    return m, lit_v, out_v


def glow_mat(name, color, strength):
    """Emission material whose strength can be keyed (returns material, strength socket)."""
    m, em = lib.emission_mat(name, color, strength)
    return m, em.inputs['Strength']


# ----------------------------------------------------------------------------- the hero
def hero(loc, heading=0.0, coll=None, pose='stand', name='Hero', rng=None):
    rng = rng or random.Random(7)
    p = P2.person(loc, heading, height=1.0, rng=rng, coll=coll, name=name)
    hood = lib.mat('HeroHoodie', '#D9682A', rough=0.88, var=0.08, var_scale=7)
    jeans = lib.mat('HeroJeans', '#2D3B54', rough=0.82, var=0.12, var_scale=9)
    cap = lib.mat('HeroCap', '#F2F0EA', rough=0.7)
    shoe = lib.mat('HeroShoe', '#EAE8E2', rough=0.6)
    skin = lib.mat('HeroSkin', '#D8AC8B', rough=0.55)
    for k in ('torso', 'upperL', 'upperR', 'foreL', 'foreR'):
        lib._obj_mat(p[k], hood)
    for k in ('pelvis', 'thighL', 'thighR', 'shinL', 'shinR'):
        lib._obj_mat(p[k], jeans)
    for k in ('shoeL', 'shoeR'):
        lib._obj_mat(p[k], shoe)
    for k in ('head', 'neck', 'handL', 'handR'):
        lib._obj_mat(p[k], skin)
    for suffix, mt in (('_nose', skin), ('_hair', lib.mat('HeroHair', '#3A2A20', rough=0.8))):
        ob = bpy.data.objects.get(name + suffix)
        if ob:
            lib._obj_mat(ob, mt)
    dome = lib.sphere(0.122, (0, 0.006, 0.036), cap, 22, 12, scale=(1.0, 1.05, 0.8), name=name + '_cap', coll=coll)
    dome.parent = p['head']
    visor = lib.box((0.18, 0.1, 0.012), (0, -0.152, 0.042), cap, rot=(math.radians(-10), 0, 0), bevel=0.004,
                    name=name + '_visor', coll=coll)
    visor.parent = p['head']
    hb = lib.sphere(0.11, (0, 0.09, 0.6), hood, 14, 10, scale=(1.3, 0.7, 0.55), name=name + '_hood', coll=coll)
    hb.parent = p['hips']
    if pose == 'stand':
        P2.stand(p, rng)
    elif pose == 'cheer':
        p['upperL'].rotation_euler.y = -2.5
        p['upperR'].rotation_euler.y = 2.5
        p['foreL'].rotation_euler.y = -0.35
        p['foreR'].rotation_euler.y = 0.35
        p['head'].rotation_euler.x = 0.18
    elif pose == 'point':
        p['upperR'].rotation_euler.x = -1.3
        p['upperR'].rotation_euler.y = 0.12
        p['foreR'].rotation_euler.x = -0.08
        p['head'].rotation_euler.z = -0.2
        p['upperL'].rotation_euler.x = 0.1
    elif pose == 'sit':
        P2.sit(p, rng)
        p['head'].rotation_euler.x = 0.25
    return p


# ----------------------------------------------------------------------------- cars
CAR_REAL = ['#E8E8E4', '#B9BDC1', '#25272A', '#1E3557', '#8D1D1F', '#5C6267', '#C7B48E', '#2E4A3A', '#E6E2D6', '#9AA0A6']


def stopped_car(loc, heading, coll, rng, color=None, door=False, kind='sedan', dusty=0.0, flat=False, name='Car'):
    col = color or rng.choice(CAR_REAL)
    if dusty:
        # a year in the open: paint goes dull and dusty
        c = Vector(C(col)[:3]).lerp(Vector(C('#8E8371')[:3]), dusty)
        col_lin = (c.x, c.y, c.z, 1.0)
        paint = lib.mat(f'DustyPaint{col}{dusty}', col_lin, rough=0.75, var=0.25, var_scale=4)
    z = (loc[2] if len(loc) > 2 else 0.0) - (0.06 if flat else 0.0)
    root = lib.car((loc[0], loc[1], z), heading, color=col, coll=coll, kind=kind, lights=False, rng=rng, name=name)
    body = [ch for ch in root.children if ch.name.startswith(name + 'Body') or ch.name.startswith(name + 'Roof')]
    if dusty:
        for ch in body:
            ch.data.materials.clear(); ch.data.materials.append(paint)
    if door:
        hinge = lib.empty(name + 'Hinge', (0.95, 0.9, 0.0), (0, 0, -0.95), coll=coll)
        hinge.parent = root
        pm = body[0].data.materials[0] if body and body[0].data.materials else lib.mat('DoorPaint', col)
        d = lib.box((1.05, 0.06, 0.62), (-0.53, 0.0, 0.66), pm, bevel=0.03, name=name + 'Door', coll=coll)
        d.parent = hinge
        g = lib.box((0.95, 0.03, 0.42), (-0.5, 0.0, 1.17), lib.mat('CarGlass', '#15181B', rough=0.08, spec=0.8), bevel=0.01,
                    name=name + 'DoorGlass', coll=coll)
        g.parent = hinge
        # dark cabin inside the opening
        inner = lib.box((1.0, 0.04, 0.6), (0.4, 0.86, 0.68), lib.mat('CarInner', '#1A1918', rough=0.9), bevel=0,
                        name=name + 'Inner', coll=coll)
        inner.parent = root
    return root


# ----------------------------------------------------------------------------- wolf
WOLF_L = 0.6       # leg length (shoulder joint height)


def wolf(loc, heading, coll, rng, name='Wolf', scale=1.0):
    """Grey wolf, forward = local -Y (like people2), pivot on the ground. Returns dict of parts."""
    tone = rng.uniform(-0.06, 0.06)
    def tint(h, k=1.0):
        c = Vector(C(h)[:3]) * (1 + tone * k)
        return (c.x, c.y, c.z, 1.0)
    fur = lib.mat(f'{name}Fur', tint('#837C72'), rough=0.95, var=0.28, var_scale=7, bump=0.25, bump_scale=70)
    back = lib.mat(f'{name}Back', tint('#4F4942'), rough=0.95, var=0.25, var_scale=6, bump=0.25, bump_scale=70)
    pale = lib.mat(f'{name}Pale', tint('#BDB2A0'), rough=0.95, var=0.2, var_scale=6, bump=0.2, bump_scale=70)
    dark = lib.mat('WolfDark', '#141211', rough=0.4)
    root = lib.empty(name, loc, (0, 0, heading), coll=coll)
    root.scale = (scale, scale, scale)
    body = lib.empty(name + '_body', (0, 0, 0), coll=coll); body.parent = root
    P = dict(root=root, body=body)

    def part(ob):
        ob.parent = body
        return ob
    part(lib.sphere(1.0, (0, 0.04, 0.66), fur, 20, 12, scale=(0.17, 0.46, 0.2), name=name + '_torso', coll=coll))
    part(lib.sphere(1.0, (0, 0.02, 0.74), back, 16, 10, scale=(0.11, 0.4, 0.1), name=name + '_saddle', coll=coll))
    part(lib.sphere(1.0, (0, -0.27, 0.68), fur, 18, 12, scale=(0.18, 0.22, 0.24), name=name + '_chest', coll=coll))
    part(lib.sphere(1.0, (0, -0.33, 0.6), pale, 14, 10, scale=(0.11, 0.12, 0.14), name=name + '_bib', coll=coll))
    part(lib.sphere(1.0, (0, 0.33, 0.67), fur, 16, 10, scale=(0.16, 0.18, 0.18), name=name + '_rump', coll=coll))
    neck = part(lib.sphere(1.0, (0, -0.45, 0.8), fur, 14, 10, scale=(0.125, 0.17, 0.15), name=name + '_neck', coll=coll))
    neck.rotation_euler.x = -0.55
    head = lib.empty(name + '_headJ', (0, -0.52, 0.84), coll=coll); head.parent = body
    P['head'] = head
    def hpart(ob):
        ob.parent = head
        return ob
    # head reads from the side: long tapered muzzle, big upright ears, pale only under the jaw
    # (a pale ring around the snout made the first proof look like a one-eyed owl head-on)
    hpart(lib.sphere(1.0, (0, -0.08, 0.04), fur, 16, 12, scale=(0.1, 0.12, 0.095), name=name + '_skull', coll=coll))
    hpart(lib.sphere(1.0, (0, -0.08, -0.04), pale, 12, 8, scale=(0.08, 0.1, 0.045), name=name + '_jaw', coll=coll))
    hpart(lib.cyl(0.052, 0.21, (0, -0.23, -0.005), fur, rot=(math.pi / 2 + 0.16, 0, 0), verts=12, r2=0.026, name=name + '_snout', coll=coll))
    hpart(lib.sphere(1.0, (0, -0.22, -0.035), pale, 10, 6, scale=(0.034, 0.1, 0.022), name=name + '_chin', coll=coll))
    hpart(lib.sphere(0.024, (0, -0.335, -0.02), dark, 8, 6, name=name + '_nose', coll=coll))
    for sx in (-1, 1):
        hpart(lib.cyl(0.055, 0.13, (sx * 0.06, -0.03, 0.14), back, rot=(0.2, sx * 0.22, 0), verts=3, r2=0.0,
                      name=name + '_ear', coll=coll))
        hpart(lib.sphere(0.013, (sx * 0.055, -0.15, 0.05), lib.mat('WolfEye', '#2A1C0C', rough=0.3), 8, 6, name=name + '_eye', coll=coll))
    tail = lib.empty(name + '_tailJ', (0, 0.47, 0.7), (-2.45, 0, 0), coll=coll); tail.parent = body
    t = lib.cyl(0.07, 0.42, (0, 0, 0.2), fur, verts=12, r2=0.035, name=name + '_tail', coll=coll); t.parent = tail
    lib.sphere(0.045, (0, 0, 0.42), back, 8, 6, name=name + '_tailTip', coll=coll).parent = tail
    P['tail'] = tail
    for key, (x, y, z) in dict(FL=(0.085, -0.28, 0.6), FR=(-0.085, -0.28, 0.6), RL=(0.08, 0.34, 0.6), RR=(-0.08, 0.34, 0.6)).items():
        hip = lib.empty(f'{name}_{key}hip', (x, y, z), coll=coll); hip.parent = body
        up = lib.cyl(0.055 if key[0] == 'R' else 0.05, 0.3, (0, 0, -0.15), fur, verts=10, r2=0.038, name=f'{name}_{key}up', coll=coll)
        up.parent = hip
        knee = lib.empty(f'{name}_{key}knee', (0, 0, -0.3), coll=coll); knee.parent = hip
        lo = lib.cyl(0.034, 0.27, (0, 0, -0.135), pale if key[0] == 'F' else fur, verts=8, r2=0.028, name=f'{name}_{key}lo', coll=coll)
        lo.parent = knee
        paw = lib.sphere(1.0, (0, -0.025, -0.282), back, 10, 6, scale=(0.04, 0.058, 0.026), name=f'{name}_{key}paw', coll=coll)
        paw.parent = knee
        P[key + 'hip'], P[key + 'knee'] = hip, knee
    return P


def trot(P, speed=2.0, phase=0.0, fps=None, samples=24):
    """Looping trot: diagonal leg pairs together, stance feet planted (stride matched to `speed`), body bounce,
    head nod, tail sway. Use lib.move_root(P, path, speed=speed) for the root."""
    fps = fps or lib.FPS
    A = 0.42
    Pd = 4 * WOLF_L * math.sin(A) / max(0.3, speed)        # one full cycle (s)
    f0 = 1 - phase * Pd * fps
    for j in range(samples + 1):
        t = j / samples
        fr = f0 + t * Pd * fps
        th_st = None
        for key, off in (('FL', 0.0), ('RR', 0.0), ('FR', 0.5), ('RL', 0.5)):
            u = (t + off + (0.04 if key[0] == 'R' else 0.0)) % 1.0
            th, k, f = P2._leg(u, A)
            P2._key(P[key + 'hip'], 'rotation_euler', 0, fr, th)
            P2._key(P[key + 'knee'], 'rotation_euler', 0, fr, k * 1.1)
            if u < 0.5 and th_st is None:
                th_st = th
        P2._key(P['body'], 'location', 2, fr, WOLF_L * (math.cos(th_st or 0.0) - 1.0) + 0.012 * math.sin(4 * math.pi * t))
        P2._key(P['head'], 'rotation_euler', 0, fr, 0.06 * math.sin(4 * math.pi * t + 0.6))
        P2._key(P['tail'], 'rotation_euler', 1, fr, 0.18 * math.sin(2 * math.pi * t))
    P2._cycle([P[k] for k in ('FLhip', 'FRhip', 'RLhip', 'RRhip', 'FLknee', 'FRknee', 'RLknee', 'RRknee', 'body', 'head', 'tail')])
    return Pd


# ----------------------------------------------------------------------------- small props
def text(body, size, loc, rot, color='#FFFFFF', strength=0.0, coll=None, bold=True, align='CENTER', name='Text'):
    if strength:
        m, _ = lib.emission_mat(name + 'Mat', color, strength)
    else:
        m = lib.mat(name + 'Mat', color, rough=0.6)
    return lib.text_obj(body, size=size, loc=loc, rot=rot, mat_=m, font=FONT if bold else FONT_REG, align=align, name=name, coll=coll)
