"""Props and materials of «Баронесса-пулемётчица» (style «Мемы»: realistic PBR, no toy look).

Everything is built from code: handbags, dust bags, the coupon machine gun, price tags, orange boxes, flags, signs,
old-town houses. Materials carry colour/roughness variation and fine bump so nothing reads as plastic.
"""
import math
import os
import random

import bmesh
import bpy
from mathutils import Matrix, Vector

import lib

F = lib.sec2f
SERIF = r'C:\Windows\Fonts\georgiab.ttf'
SERIF_R = r'C:\Windows\Fonts\georgia.ttf'
SANS = r'C:\Windows\Fonts\arialbd.ttf'


# ----------------------------------------------------------------------------- materials
# v2 (29.10.2026, mike: «качественные ресурсы, не пластик»): CC0 photo textures from Poly Haven (tools/get_polyhaven.py)
PH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'assets_ph')
PBR_BY_NAME = [('Mud', 'brown_mud_leaves_01', 3.0), ('Field', 'aerial_grass_rock', 8.0), ('Plain', 'aerial_grass_rock', 8.0),
               ('Meadow', 'aerial_grass_rock', 8.0), ('Land', 'aerial_grass_rock', 10.0), ('Grass', 'aerial_grass_rock', 8.0),
               ('Brick', 'brick_4', 1.6), ('Wall', 'painted_plaster_wall', 3.0), ('Facade', 'painted_plaster_wall', 3.0),
               ('HallWall', 'painted_plaster_wall', 3.0), ('HQStone', 'painted_plaster_wall', 3.0),
               ('PalaceStone', 'painted_plaster_wall', 4.0), ('WhiteStone', 'painted_plaster_wall', 4.0),
               ('Road', 'brown_mud_leaves_01', 4.0), ('Showroom', 'painted_plaster_wall', 3.0)]


def pbr(name, asset, scale=2.0, tint=None, rough_mul=1.0, bump=1.0):
    """Photo-textured material (diffuse/normal/roughness, box-projected in object space, `scale` metres per tile);
    tint multiplies the photo colour so one texture serves many colours."""
    key = f'PBR_{name}_{asset}'
    m = bpy.data.materials.get(key)
    if m:
        return m
    d = os.path.join(PH, asset)
    if not os.path.exists(os.path.join(d, 'diff.jpg')):
        return None
    m = bpy.data.materials.new(key)
    m.use_nodes = True
    nt = m.node_tree
    p = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord')
    mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (1 / scale,) * 3
    nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])

    def img(fn, data):
        n = nt.nodes.new('ShaderNodeTexImage')
        n.image = bpy.data.images.load(os.path.join(d, fn), check_existing=True)
        if not data:
            pass
        else:
            n.image.colorspace_settings.name = 'Non-Color'
        n.projection = 'BOX'
        n.projection_blend = 0.25
        nt.links.new(mp.outputs['Vector'], n.inputs['Vector'])
        return n
    dif = img('diff.jpg', False)
    col = dif.outputs['Color']
    if tint:
        mix = nt.nodes.new('ShaderNodeMix')
        mix.data_type = 'RGBA'
        mix.blend_type = 'MULTIPLY'
        mix.inputs['Factor'].default_value = 1.0
        c = lib.C(tint)
        mix.inputs[7].default_value = tuple(min(1.0, v * 2.2) for v in c[:3]) + (1,)
        nt.links.new(col, mix.inputs[6])
        col = mix.outputs[2]
    nt.links.new(col, p.inputs['Base Color'])
    if os.path.exists(os.path.join(d, 'rough.jpg')):
        r = img('rough.jpg', True)
        mm = nt.nodes.new('ShaderNodeMath')
        mm.operation = 'MULTIPLY'
        mm.inputs[1].default_value = rough_mul
        nt.links.new(r.outputs['Color'], mm.inputs[0])
        nt.links.new(mm.outputs[0], p.inputs['Roughness'])
    if os.path.exists(os.path.join(d, 'nor.jpg')):
        nimg = img('nor.jpg', True)
        nm = nt.nodes.new('ShaderNodeNormalMap')
        nm.inputs['Strength'].default_value = bump
        nt.links.new(nimg.outputs['Color'], nm.inputs['Color'])
        nt.links.new(nm.outputs['Normal'], p.inputs['Normal'])
    return m


def M(name, col, rough=0.6, metal=0.0, var=0.08, bump=0.15, bs=40.0, **kw):
    for pre, asset, sc in PBR_BY_NAME:
        if name.startswith(pre):
            m = pbr(name, asset, sc, tint=col if asset in ('painted_plaster_wall',) else None)
            if m:
                return m
    return lib.mat(name, col, rough=rough, metal=metal, var=var, var_scale=kw.pop('vs', 6.0), bump=bump,
                   bump_scale=bs, **kw)


def hdri_world(strength=1.0, rot=0.0, asset='belfast_sunset_puresky'):
    """Photographic evening sky (Poly Haven HDRI) as the world; returns False if it is missing."""
    f = os.path.join(PH, asset, 'sky.hdr')
    if not os.path.exists(f):
        return False
    w = bpy.context.scene.world or bpy.data.worlds.new('World')
    bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputWorld')
    bg = nt.nodes.new('ShaderNodeBackground')
    env = nt.nodes.new('ShaderNodeTexEnvironment')
    env.image = bpy.data.images.load(f, check_existing=True)
    tc = nt.nodes.new('ShaderNodeTexCoord')
    mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Rotation'].default_value = (0, 0, rot)
    nt.links.new(tc.outputs['Generated'], mp.inputs['Vector'])
    nt.links.new(mp.outputs['Vector'], env.inputs['Vector'])
    nt.links.new(env.outputs['Color'], bg.inputs['Color'])
    bg.inputs['Strength'].default_value = strength
    nt.links.new(bg.outputs['Background'], out.inputs['Surface'])
    return True


def gold():
    return M('Gold', '#C99A3E', rough=0.28, metal=1.0, var=0.05, bump=0.04, bs=90)


def brass():
    return M('Brass', '#A8803A', rough=0.38, metal=1.0, var=0.12, bump=0.08, bs=60)


def steel():
    return M('Steel', '#4A4C50', rough=0.42, metal=1.0, var=0.1, bump=0.05)


def leather(col='#7A3E1E', name=None):
    m = pbr(name or 'Leather' + col, 'brown_leather', 0.6, tint=col)
    if m:
        return m
    return M(name or 'Leather' + col, col, rough=0.48, var=0.12, bump=0.35, bs=180, coat=0.15)


def paper(col='#EDE3CF', name=None):
    return M(name or 'Paper' + col, col, rough=0.92, var=0.05, bump=0.06, bs=120, spec=0.2)


def cloth(col='#E9E1D2', name=None):
    return M(name or 'Cloth' + col, col, rough=0.95, var=0.07, bump=0.3, bs=260, spec=0.15, sss=0.0)


def wood(col='#6B4426', name=None):
    m = pbr(name or 'Wood' + col, 'wood_table_worn', 1.5, tint=col)
    if m:
        return m
    m = bpy.data.materials.get(name or 'Wood' + col)
    if m:
        return m
    m = bpy.data.materials.new(name or 'Wood' + col)
    m.use_nodes = True
    nt = m.node_tree
    p = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord')
    mp = nt.nodes.new('ShaderNodeMapping')               # long grain along X: stretch the noise along X
    mp.inputs['Scale'].default_value = (0.25, 4.0, 4.0)
    wv = nt.nodes.new('ShaderNodeTexWave')
    wv.wave_type = 'BANDS'
    wv.bands_direction = 'Y'
    wv.inputs['Scale'].default_value = 2.0
    wv.inputs['Distortion'].default_value = 9.0
    wv.inputs['Detail'].default_value = 5.0
    wv.inputs['Detail Scale'].default_value = 2.5
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    c = lib.C(col)
    ramp.color_ramp.elements[0].color = tuple(v * 0.62 for v in c[:3]) + (1,)
    ramp.color_ramp.elements[1].color = tuple(min(1, v * 1.18) for v in c[:3]) + (1,)
    nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
    nt.links.new(mp.outputs['Vector'], wv.inputs['Vector'])
    nt.links.new(wv.outputs['Fac'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = 0.5
    p.inputs['Coat Weight'].default_value = 0.25
    bmp = nt.nodes.new('ShaderNodeBump')
    bmp.inputs['Strength'].default_value = 0.08
    nt.links.new(wv.outputs['Fac'], bmp.inputs['Height'])
    nt.links.new(bmp.outputs['Normal'], p.inputs['Normal'])
    return m


def marble(col='#ECE7DF', vein='#9C948A', name='Marble'):
    m = pbr(name, 'marble_01', 2.5)
    if m:
        return m
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    p = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord')
    nz = nt.nodes.new('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = 1.6
    nz.inputs['Detail'].default_value = 12.0
    nz.inputs['Distortion'].default_value = 2.5
    wv = nt.nodes.new('ShaderNodeTexWave')
    wv.inputs['Scale'].default_value = 1.3
    wv.inputs['Distortion'].default_value = 14.0
    wv.inputs['Detail'].default_value = 6.0
    nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
    nt.links.new(nz.outputs['Color'], wv.inputs['Vector'])
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = lib.C(vein)
    ramp.color_ramp.elements[1].position = 0.12
    ramp.color_ramp.elements[1].color = lib.C(col)
    nt.links.new(wv.outputs['Fac'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = 0.18
    p.inputs['Coat Weight'].default_value = 0.3
    return m


def sepia_image(path, name='Photo', tone=1.0, fade=None):
    """Image material with a sepia/aged look; fade: object property name 0..1 that dissolves the picture to paper."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    p = nt.nodes['Principled BSDF']
    img = nt.nodes.new('ShaderNodeTexImage')
    img.image = bpy.data.images.load(path, check_existing=True)
    bw = nt.nodes.new('ShaderNodeRGBToBW')
    nt.links.new(img.outputs['Color'], bw.inputs['Color'])
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color = lib.C('#2A1A0E')
    ramp.color_ramp.elements[1].color = lib.C('#F1DDB4')
    nt.links.new(bw.outputs['Val'], ramp.inputs['Fac'])
    out = ramp.outputs['Color']
    if fade:
        at = nt.nodes.new('ShaderNodeAttribute')
        at.attribute_type, at.attribute_name = 'OBJECT', fade
        nz = nt.nodes.new('ShaderNodeTexNoise')
        nz.inputs['Scale'].default_value = 9.0
        nz.inputs['Detail'].default_value = 6.0
        ge = nt.nodes.new('ShaderNodeMath')
        ge.operation = 'LESS_THAN'
        nt.links.new(nz.outputs['Fac'], ge.inputs[0])
        mr = nt.nodes.new('ShaderNodeMapRange')
        mr.inputs['To Min'].default_value = 0.25
        mr.inputs['To Max'].default_value = 0.8
        nt.links.new(at.outputs['Fac'], mr.inputs['Value'])
        nt.links.new(mr.outputs['Result'], ge.inputs[1])
        mix = nt.nodes.new('ShaderNodeMix')
        mix.data_type = 'RGBA'
        nt.links.new(ge.outputs[0], mix.inputs['Factor'])
        nt.links.new(out, mix.inputs[6])
        mix.inputs[7].default_value = lib.C('#EADCC0')
        out = mix.outputs[2]
    nt.links.new(out, p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = 0.55
    return m


def screen_image(path, name='Screen', strength=1.6, reveal=None):
    """Emissive picture for a monitor; reveal: object property 0..1 that turns noise into the picture."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    p = nt.nodes['Principled BSDF']
    img = nt.nodes.new('ShaderNodeTexImage')
    img.image = bpy.data.images.load(path, check_existing=True)
    col = img.outputs['Color']
    if reveal:
        at = nt.nodes.new('ShaderNodeAttribute')
        at.attribute_type, at.attribute_name = 'OBJECT', reveal
        tc = nt.nodes.new('ShaderNodeTexCoord')
        nz = nt.nodes.new('ShaderNodeTexNoise')
        nz.inputs['Scale'].default_value = 140.0
        nz.inputs['Detail'].default_value = 1.0
        nt.links.new(tc.outputs['UV'], nz.inputs['Vector'])
        vor = nt.nodes.new('ShaderNodeTexVoronoi')         # blocky "diffusion" noise that settles
        vor.inputs['Scale'].default_value = 40.0
        nt.links.new(tc.outputs['UV'], vor.inputs['Vector'])
        mix = nt.nodes.new('ShaderNodeMix')
        mix.data_type = 'RGBA'
        nt.links.new(at.outputs['Fac'], mix.inputs['Factor'])
        mix2 = nt.nodes.new('ShaderNodeMix')
        mix2.data_type = 'RGBA'
        mix2.inputs['Factor'].default_value = 0.5
        nt.links.new(nz.outputs['Color'], mix2.inputs[6])
        nt.links.new(vor.outputs['Color'], mix2.inputs[7])
        nt.links.new(mix2.outputs[2], mix.inputs[6])
        nt.links.new(col, mix.inputs[7])
        col = mix.outputs[2]
    nt.links.new(col, p.inputs['Base Color'])
    nt.links.new(col, p.inputs['Emission Color'])
    p.inputs['Emission Strength'].default_value = strength
    p.inputs['Roughness'].default_value = 0.15
    return m


# ----------------------------------------------------------------------------- small helpers
def uv_plane(size, loc=(0, 0, 0), rot=(0, 0, 0), m=None, name='Pic'):
    """A plane with UVs 0..1 (lib.plane has none, an image on it shows one pixel)."""
    bm = bmesh.new()
    bm.loops.layers.uv.new('UVMap')                 # calc_uvs fills an existing layer only
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.5, calc_uvs=True)
    for v in bm.verts:
        v.co.x *= size[0]
        v.co.y *= size[1]
    ob = lib.mesh_from_bm(bm, name, m, loc, rot, smooth=False)
    return ob



def ob_mat(ob, m):
    ob.data.materials.clear()
    ob.data.materials.append(m)
    return ob


def sub(ob, levels=2):
    md = ob.modifiers.new('Sub', 'SUBSURF')
    md.levels = md.render_levels = levels
    return ob


def solidify(ob, t=0.004):
    md = ob.modifiers.new('Sol', 'SOLIDIFY')
    md.thickness = t
    return ob


def text(body, size, loc, rot=(math.radians(90), 0, 0), m=None, font=SERIF, extrude=0.004, align='CENTER', name='Txt'):
    ob = lib.text_obj(body, size=size, loc=loc, rot=rot, mat_=m, font=font, extrude=extrude, align=align, name=name)
    return ob


def group(name, objs, loc=(0, 0, 0)):
    e = lib.empty(name, loc=(0, 0, 0))
    for o in objs:
        o.parent = e
    e.location = loc
    return e


def tube(pts, r, m, name='Tube', res=3):
    return lib.curve_poly(name, [pts], bevel=r, mat_=m, res=res)


# ----------------------------------------------------------------------------- handbag & dust bag
def handbag(loc=(0, 0, 0), rot=0.0, w=0.34, h=0.25, d=0.16, col='#B5651D', name='Bag', lock=True):
    """A structured top-handle bag (trapezoid body, flap with straps, two rolled handles, gold lock). Origin: bottom."""
    s = w / 0.34                                    # details scale with the bag
    lm = leather(col)
    dark = leather('#3B1E0E', 'LeatherEdge')
    tw = w * 0.86                                  # top is narrower
    bm = bmesh.new()
    pts = [(-w / 2, -d / 2, 0), (w / 2, -d / 2, 0), (w / 2, d / 2, 0), (-w / 2, d / 2, 0),
           (-tw / 2, -d / 2 * 0.9, h), (tw / 2, -d / 2 * 0.9, h), (tw / 2, d / 2 * 0.9, h), (-tw / 2, d / 2 * 0.9, h)]
    vs = [bm.verts.new(p) for p in pts]
    for f in ((0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)):
        bm.faces.new([vs[i] for i in f])
    body = lib.mesh_from_bm(bm, name + 'Body', lm)
    lib.add_bevel(body, 0.018 * s, segs=4)
    # flap over the front
    fy = -d / 2 * 0.9
    flap = lib.box((tw * 1.02, 0.012 * s, h * 0.42), (0, fy - 0.006 * s, h * 0.79), lm, bevel=0.006 * s, name=name + 'Flap')
    top = lib.box((tw * 1.02, d * 0.92, 0.012 * s), (0, 0, h + 0.004 * s), lm, bevel=0.005 * s, name=name + 'Top')
    straps = [lib.box((0.026 * s, 0.006 * s, h * 0.5), (sx * tw * 0.3, fy - 0.013 * s, h * 0.74), dark, bevel=0.002 * s,
                      name=name + 'Strap') for sx in (-1, 1)]
    objs = [body, flap, top] + straps
    for sy in (-1, 1):                              # two rolled handles, front and back
        pts_h = [(-tw * 0.27 + tw * 0.54 * k / 8, sy * d * 0.18, h + 0.012 * s + 0.12 * s * math.sin(math.pi * k / 8))
                 for k in range(9)]
        objs.append(tube(pts_h, 0.009 * s, dark, name + 'Handle'))
    if lock:
        g = gold()
        objs.append(lib.box((0.05 * s, 0.012 * s, 0.035 * s), (0, fy - 0.016 * s, h * 0.6), g, bevel=0.004 * s,
                            name=name + 'Lock'))
        objs.append(lib.cyl(0.006 * s, 0.02 * s, (0, fy - 0.024 * s, h * 0.6), g, rot=(math.radians(90), 0, 0),
                            name=name + 'Pad'))
        for sx in (-1, 1):
            objs.append(lib.sphere(0.006 * s, (sx * w * 0.42, -d * 0.35, 0.004 * s), g, segs=12, rings=6,
                                   name=name + 'Foot'))
    e = group(name, objs, loc)
    e.rotation_euler.z = rot
    return e


def dust_bag(loc=(0, 0, 0), w=0.42, h=0.5, col='#E6DED0', name='DustBag', flat=0.35, seed=1):
    """A soft cotton dust bag with a drawstring: squashed, lumpy sphere with a gathered neck. Origin: bottom."""
    rnd = random.Random(seed)
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=40, v_segments=24, radius=0.5)
    for v in bm.verts:
        z = v.co.z + 0.5                                  # 0..1
        neck = 1.0 - 0.72 * max(0.0, (z - 0.78) / 0.22) ** 0.7
        v.co.x *= w * neck * (1 + 0.04 * math.sin(v.co.z * 23 + seed))
        v.co.y *= w * flat * neck
        v.co.z = z * h
        v.co.x += 0.006 * math.sin(v.co.z * 40 + rnd.random())
    ob = lib.mesh_from_bm(bm, name, cloth(col), smooth=True)
    disp = ob.modifiers.new('Wrinkle', 'DISPLACE')
    tx = bpy.data.textures.new(name + 'Tx', 'CLOUDS')
    tx.noise_scale = 0.05
    disp.texture, disp.strength, disp.mid_level = tx, 0.006, 0.5
    cord = tube([(-w * 0.14, -w * flat * 0.15, h * 0.92), (-w * 0.05, -w * flat * 0.2, h * 0.86),
                 (-w * 0.02, -w * flat * 0.25, h * 0.6), (-w * 0.04, -w * flat * 0.22, h * 0.45)], 0.004,
                cloth('#B7AA92', 'Cord'), name + 'Cord')
    # a printed crest: a small handbag silhouette (text-free)
    crest = lib.box((w * 0.16, 0.002, w * 0.11), (0, -w * flat * 0.5 - 0.002, h * 0.48), cloth('#8C6A3E', 'Crest'),
                    bevel=0.0, name=name + 'Crest')
    e = group(name, [ob, cord, crest], loc)
    return e


# ----------------------------------------------------------------------------- price tag & coupon
def tag_mesh():
    me = bpy.data.meshes.get('TagMesh')
    if me:
        return me
    bm = bmesh.new()
    w, h, c = 0.05, 0.028, 0.008
    pts = [(-w / 2, -h / 2), (w / 2 - c, -h / 2), (w / 2, 0), (w / 2 - c, h / 2), (-w / 2, h / 2)]
    vs = [bm.verts.new((x, 0, y)) for x, y in pts]
    bm.faces.new(vs)
    me = bpy.data.meshes.new('TagMesh')
    bm.to_mesh(me)
    return me


def coupon_mesh():
    me = bpy.data.meshes.get('CouponMesh')
    if me:
        return me
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.5)
    for v in bm.verts:
        v.co = Vector((v.co.x * 0.07, 0, v.co.y * 0.035))
    me = bpy.data.meshes.new('CouponMesh')
    bm.to_mesh(me)
    return me


def tag_mats():
    return [paper('#F2E9D6', 'TagCream'), paper('#E9C46A', 'TagYellow'), paper('#E76F51', 'TagRed'),
            paper('#F4F1EA', 'TagWhite')]


def flying_paper(n, src, vel, t0, t1, spread=0.35, life=1.6, kind='coupon', seed=3, grav=2.2, coll=None):
    """n pieces of paper shot from `src` along `vel` (m/s) between t0 and t1, tumbling and falling. Keyed objects
    (deterministic, renders the same in stills and clips)."""
    rnd = random.Random(seed)
    me = coupon_mesh() if kind == 'coupon' else tag_mesh()
    mats = tag_mats()
    src, vel = Vector(src), Vector(vel)
    out = []
    for i in range(n):
        ts = t0 + (t1 - t0) * i / max(1, n - 1) + rnd.uniform(-0.02, 0.02)
        if not me.materials:
            me.materials.append(mats[0])
        ob = bpy.data.objects.new(f'Paper{i}', me)
        (coll or bpy.context.scene.collection).objects.link(ob)
        md = ob.modifiers.new('Sol', 'SOLIDIFY')
        md.thickness = 0.0008
        ob.material_slots[0].link = 'OBJECT'
        ob.material_slots[0].material = mats[rnd.randrange(len(mats))]
        v = vel + Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-0.6, 1))) * spread * vel.length
        spin = Vector((rnd.uniform(-12, 12), rnd.uniform(-12, 12), rnd.uniform(-12, 12)))
        ob.scale = (0, 0, 0)
        ob.keyframe_insert('scale', frame=max(1, F(ts) - 1))
        steps = 8
        for k in range(steps + 1):
            dt = life * k / steps
            drag = 1 - math.exp(-dt * 2.4)
            p = src + v * (drag / 2.4) + Vector((0, 0, -grav * dt * dt * 0.5 * 0.6))
            ob.location = p
            ob.rotation_euler = tuple(spin * dt)
            ob.scale = (1, 1, 1)
            ob.keyframe_insert('location', frame=F(ts + dt))
            ob.keyframe_insert('rotation_euler', frame=F(ts + dt))
            if k == 0:
                ob.keyframe_insert('scale', frame=F(ts))
        out.append(ob)
    return out


def drifting_paper(n, box_lo, box_hi, t0, t1, seed=5, kind='coupon', coll=None, fall=0.6):
    """Paper slowly drifting down through a box volume during [t0, t1] (confetti of coupons)."""
    rnd = random.Random(seed)
    me = coupon_mesh() if kind == 'coupon' else tag_mesh()
    mats = tag_mats()
    lo, hi = Vector(box_lo), Vector(box_hi)
    out = []
    for i in range(n):
        if not me.materials:
            me.materials.append(mats[0])
        ob = bpy.data.objects.new(f'Drift{i}', me)
        (coll or bpy.context.scene.collection).objects.link(ob)
        ob.material_slots[0].link = 'OBJECT'
        ob.material_slots[0].material = mats[rnd.randrange(len(mats))]
        md = ob.modifiers.new('Sol', 'SOLIDIFY')
        md.thickness = 0.0008
        x, y = rnd.uniform(lo.x, hi.x), rnd.uniform(lo.y, hi.y)
        z0 = rnd.uniform(lo.z, hi.z)
        sp = Vector((rnd.uniform(-3, 3), rnd.uniform(-3, 3), rnd.uniform(-3, 3)))
        ph = rnd.uniform(0, 6.28)
        for k in range(7):
            t = t0 + (t1 - t0) * k / 6
            z = z0 - fall * (t - t0)
            if z < lo.z - 2:
                z += (hi.z - lo.z) + 2
            ob.location = (x + 0.15 * math.sin(t * 1.7 + ph), y + 0.1 * math.cos(t * 1.3 + ph), z)
            ob.rotation_euler = tuple(sp * t)
            ob.keyframe_insert('location', frame=F(t))
            ob.keyframe_insert('rotation_euler', frame=F(t))
        lib._set_interp(ob, 'LINEAR')
        out.append(ob)
    return out


# ----------------------------------------------------------------------------- the coupon machine gun
def coupon_gun(loc=(0, 0, 0), rot=0.0, name='Gun', carriage=False):
    """A heavy vintage water-cooled machine gun, polished brass and dark steel, fed by a belt of paper coupons
    instead of cartridges. Barrel along -Y. Origin: the grips' middle."""
    b, s, wd = brass(), steel(), wood('#5A3820', 'GunWood')
    objs = []
    objs.append(lib.cyl(0.055, 0.62, (0, -0.48, 0.0), b, rot=(math.radians(90), 0, 0), verts=40, bevel=0.006,
                        name=name + 'Jacket'))
    for y in (-0.2, -0.78):
        objs.append(lib.cyl(0.062, 0.035, (0, y, 0), s, rot=(math.radians(90), 0, 0), verts=40, name=name + 'Ring'))
    objs.append(lib.cyl(0.016, 0.16, (0, -0.86, 0), s, rot=(math.radians(90), 0, 0), name=name + 'Muzzle'))
    objs.append(lib.cyl(0.03, 0.05, (0, -0.95, 0), b, rot=(math.radians(90), 0, 0), r2=0.04, name=name + 'Flash'))
    objs.append(lib.box((0.11, 0.3, 0.12), (0, -0.05, 0.0), s, bevel=0.012, name=name + 'Receiver'))
    objs.append(lib.box((0.115, 0.22, 0.02), (0, -0.07, 0.07), b, bevel=0.006, name=name + 'Lid'))
    objs.append(lib.cyl(0.02, 0.05, (0, -0.68, 0.07), b, name=name + 'Cap'))
    for sx in (-1, 1):                                   # spade grips
        objs.append(lib.cyl(0.016, 0.1, (sx * 0.045, 0.14, 0.0), wd, name=name + 'Grip'))
    objs.append(lib.box((0.12, 0.03, 0.03), (0, 0.11, 0.0), s, bevel=0.006, name=name + 'Back'))
    objs.append(lib.box((0.02, 0.02, 0.05), (0, 0.11, -0.05), b, bevel=0.004, name=name + 'Trigger'))
    # the coupon belt: a canvas strip with paper coupons where cartridges would be, hanging off the left side
    belt_pts = [(0.06, -0.06, 0.0), (0.16, -0.05, -0.04), (0.22, -0.02, -0.16), (0.24, 0.02, -0.32), (0.2, 0.06, -0.45)]
    belt = tube(belt_pts, 0.004, cloth('#8A7B5E', 'Canvas'), name + 'Belt')
    belt.data.bevel_mode = 'ROUND'
    objs.append(belt)
    sp = bpy.data.curves[belt.data.name].splines[0]
    pm = paper('#F2E9D6', 'TagCream')
    for k in range(10):
        u = k / 9
        i = min(len(belt_pts) - 2, int(u * (len(belt_pts) - 1)))
        w = u * (len(belt_pts) - 1) - i
        p = Vector(belt_pts[i]).lerp(Vector(belt_pts[i + 1]), w)
        c = lib.box((0.006, 0.05, 0.026), tuple(p), pm, bevel=0.0, name=name + 'BeltCoupon')
        c.rotation_euler = (0, math.radians(-60 * u), 0)
        objs.append(c)
    if carriage:
        for sx in (-1, 1):
            objs.append(lib.cyl(0.16, 0.04, (sx * 0.22, 0.05, -0.42), s, rot=(0, math.radians(90), 0), verts=40,
                                name=name + 'Wheel'))
        objs.append(lib.box((0.5, 0.06, 0.05), (0, 0.05, -0.42), s, bevel=0.01, name=name + 'Axle'))
        objs.append(lib.box((0.08, 0.5, 0.06), (0, 0.32, -0.42), s, bevel=0.01, name=name + 'Trail'))
        objs.append(lib.box((0.06, 0.06, 0.4), (0, 0.0, -0.2), s, bevel=0.01, name=name + 'Post'))
    e = group(name, objs, loc)
    e.rotation_euler.z = rot
    e['muzzle'] = (0.0, -0.98, 0.0)
    return e


def muzzle_world(gun):
    return gun.matrix_world @ Vector(gun['muzzle'])


def attach(ob, rig, bone, offset=(0, 0, 0), rot=(0, 0, 0)):
    """Parent a prop to a bone (follows the pose)."""
    ob.parent = rig
    ob.parent_type = 'BONE'
    ob.parent_bone = bone
    pb = rig.data.bones[bone]
    ob.matrix_parent_inverse = Matrix()
    # bone parenting puts the child at the bone's tail; move it back by the bone length along Y
    ob.location = Vector(offset) + Vector((0, -pb.length, 0))
    ob.rotation_euler = rot
    return ob


# ----------------------------------------------------------------------------- boxes, flags, signs
def gift_box(size=(1, 1, 0.6), loc=(0, 0, 0), col='#E8701E', ribbon='#5B3A1E', name='Box', bow=True):
    bx = lib.box(size, (loc[0], loc[1], loc[2] + size[2] / 2), M('Orange' + col, col, rough=0.55, var=0.05, bump=0.06),
                 bevel=min(size) * 0.02, name=name)
    lid = lib.box((size[0] * 1.03, size[1] * 1.03, size[2] * 0.16), (loc[0], loc[1], loc[2] + size[2] * 0.93),
                  M('Orange' + col, col), bevel=min(size) * 0.02, name=name + 'Lid')
    rm = M('Ribbon' + ribbon, ribbon, rough=0.35, var=0.04, bump=0.02, coat=0.4)
    r1 = lib.box((size[0] * 1.05, size[1] * 0.08, size[2] * 1.02), (loc[0], loc[1], loc[2] + size[2] / 2), rm, bevel=0,
                 name=name + 'R1')
    r2 = lib.box((size[0] * 0.08, size[1] * 1.05, size[2] * 1.02), (loc[0], loc[1], loc[2] + size[2] / 2), rm, bevel=0,
                 name=name + 'R2')
    objs = [bx, lid, r1, r2]
    if bow:
        for a in (-1, 1):
            o = lib.sphere(min(size) * 0.12, (loc[0] + a * min(size) * 0.1, loc[1], loc[2] + size[2] * 1.03), rm,
                           scale=(1.2, 0.5, 0.45), name=name + 'Bow')
            o.rotation_euler.y = a * 0.4
            objs.append(o)
    return objs


def flag(loc, size=(1.5, 1.0), stripes=('#E8701E', '#F3EEE4', '#6B4226'), pole=4.0, name='Flag', t_up=None, up=(0, 1),
         amp=0.06):
    """A cloth flag with horizontal stripes on a pole, waving (wave modifier); t_up=(t0, t1) raises it along the pole."""
    w, h = size
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=40, y_segments=20, size=0.5)
    for v in bm.verts:
        v.co = Vector(((v.co.x + 0.5) * w, 0, (v.co.y + 0.5) * h))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    cloth_ = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(cloth_)
    n = len(stripes)
    for i, c in enumerate(stripes):
        me.materials.append(cloth(c, f'{name}Stripe{i}'))
    for poly in me.polygons:
        z = poly.center.z / h
        poly.material_index = min(n - 1, int((1 - z) * n))
    wv = cloth_.modifiers.new('Wave', 'WAVE')
    wv.use_normal = False
    wv.use_x, wv.use_y = True, False
    wv.height, wv.width, wv.narrowness, wv.speed = amp, 0.6, 1.2, 0.18
    wv.start_position_x = -0.3
    wv.falloff_radius = 0
    # pin the side at the pole: vertex group weights rising from the pole
    vg = cloth_.vertex_groups.new(name='Free')
    for v in me.vertices:
        vg.add([v.index], min(1.0, v.co.x / (w * 0.35)), 'REPLACE')
    wv.vertex_group = 'Free'
    sol = cloth_.modifiers.new('Sol', 'SOLIDIFY')
    sol.thickness = 0.004
    p = lib.cyl(0.03, pole, (loc[0], loc[1], loc[2] + pole / 2), M('PoleWhite', '#E4DED4', rough=0.4, metal=0.3),
                name=name + 'Pole')
    knob = lib.sphere(0.06, (loc[0], loc[1], loc[2] + pole + 0.04), gold(), name=name + 'Knob')
    cloth_.location = (loc[0] + 0.03, loc[1], loc[2] + pole - h - 0.05)
    if t_up:
        z_top = loc[2] + pole - h - 0.05
        cloth_.location.z = loc[2] + up[0] * (pole - h)
        cloth_.keyframe_insert('location', frame=F(t_up[0]))
        cloth_.location.z = z_top
        cloth_.keyframe_insert('location', frame=F(t_up[1]))
    return cloth_, p, knob


def sign(body, loc, size=0.3, board=None, rot_z=0.0, col='#2A2118', txt='#D9B36A', font=SERIF, name='Sign', depth=0.04):
    """A painted wooden sign board with gold letters. board=(w, h) or auto."""
    n = max(1, len(body))
    bw, bh = board or (n * size * 0.62 + size * 1.2, size * 1.9)
    bd = lib.box((bw, depth, bh), (0, 0, 0), wood(col, 'SignWood' + col), bevel=0.01, name=name + 'Board')
    t = text(body, size, (0, -depth / 2 - 0.004, 0), m=gold() if txt == 'gold' else M('SignTxt' + txt, txt, rough=0.35,
                                                                                         metal=0.6), font=font,
             extrude=0.003, name=name + 'Txt')
    e = group(name, [bd, t], loc)
    e.rotation_euler.z = rot_z
    return e


# ----------------------------------------------------------------------------- old-town houses (realistic proportions)
WALLS = ['#D8C3A5', '#C9A27E', '#E3D5BF', '#B9876A', '#D6B48C', '#CDBBA0', '#A9AE97']


def house(x, y, w, d, floors, rnd, heading=0.0, win_lit=0.3, shop=None, coll=None, roof='#6E4A3A', snow=False):
    """A 19th-century town house: plaster walls with cornices, tall windows with frames, a pitched roof, chimney;
    optional shop front (shop = sign text). Front faces -Y (before heading)."""
    fh = 3.2
    H = floors * fh + 0.6
    wall = M('Wall' + str(rnd.randrange(len(WALLS))), WALLS[rnd.randrange(len(WALLS))], rough=0.85, var=0.12, bump=0.25,
             bs=14)
    trim = M('Trim', '#EFE8DC', rough=0.7, var=0.05, bump=0.1)
    glass_dark = lib.mat('GlassDark', '#1E2A33', rough=0.08, metal=0.0, spec=0.8)
    glass_lit = lib.mat('GlassLit', '#FFD9A0', rough=0.2, emit='#FFC27A', emit_strength=4.0)
    objs = [lib.box((w, d, H), (0, 0, H / 2), wall, bevel=0.03, name='Wall')]
    for k in range(1, floors + 1):
        objs.append(lib.box((w + 0.12, d + 0.12, 0.16), (0, 0, k * fh), trim, bevel=0.02, name='Cornice'))
    nwin = max(2, int(w / 1.6))
    for f in range(1 if shop else 0, floors):
        for i in range(nwin):
            wx = -w / 2 + w * (i + 0.5) / nwin
            z = f * fh + 1.0
            lit = rnd.random() < win_lit
            objs.append(lib.box((0.82, 0.08, 1.55), (wx, -d / 2 - 0.02, z + 0.78), trim, bevel=0.01, name='Frame'))
            objs.append(lib.box((0.68, 0.06, 1.4), (wx, -d / 2 - 0.05, z + 0.78), glass_lit if lit else glass_dark,
                                bevel=0.0, name='Win'))
            objs.append(lib.box((0.04, 0.07, 1.4), (wx, -d / 2 - 0.07, z + 0.78), trim, bevel=0.0, name='Mullion'))
            objs.append(lib.box((0.95, 0.18, 0.08), (wx, -d / 2 - 0.08, z - 0.02), trim, bevel=0.01, name='Sill'))
    if shop:
        objs.append(lib.box((w * 0.86, 0.1, 2.4), (0, -d / 2 - 0.04, 1.45), glass_lit, bevel=0.0, name='ShopWin'))
        objs.append(lib.box((w * 0.9, 0.16, 0.1), (0, -d / 2 - 0.07, 2.7), wood('#3A2516'), bevel=0.01, name='ShopTop'))
        objs.append(lib.box((w * 0.9, 0.16, 0.25), (0, -d / 2 - 0.07, 0.12), wood('#3A2516'), bevel=0.01, name='ShopBase'))
        s = sign(shop, (0, -d / 2 - 0.14, 3.05), size=0.36, board=(w * 0.8, 0.62), name='ShopSign')
        objs.append(s)
    rm = M('Roof' + roof, roof, rough=0.7, var=0.12, bump=0.3, bs=30)
    bm = bmesh.new()
    rh = d * 0.45
    pts = [(-w / 2 - 0.15, -d / 2 - 0.25, 0), (w / 2 + 0.15, -d / 2 - 0.25, 0), (w / 2 + 0.15, d / 2 + 0.25, 0),
           (-w / 2 - 0.15, d / 2 + 0.25, 0), (-w / 2 - 0.15, 0, rh), (w / 2 + 0.15, 0, rh)]
    vs = [bm.verts.new(p) for p in pts]
    for f in ((0, 1, 5, 4), (2, 3, 4, 5), (0, 4, 3), (1, 2, 5)):
        bm.faces.new([vs[i] for i in f])
    roof_o = lib.mesh_from_bm(bm, 'Roof', rm, loc=(0, 0, H), smooth=False)
    objs.append(roof_o)
    if snow:
        sm = M('Snow', '#F4F6F8', rough=0.75, var=0.03, bump=0.2, sss=0.0)
        sn = lib.mesh_from_bm(_roof_bm(w, d, rh, 0.08), 'Snow', sm, loc=(0, 0, H + 0.02), smooth=False)
        objs.append(sn)
    objs.append(lib.box((0.5, 0.5, 1.4), (w * 0.28, d * 0.12, H + rh * 0.7), M('Brick', '#7A4433', rough=0.85, var=0.2,
                                                                              bump=0.3), bevel=0.02, name='Chimney'))
    e = group('House', objs)
    e.location = (x, y, 0)
    e.rotation_euler.z = heading
    return e


def _roof_bm(w, d, rh, t):
    bm = bmesh.new()
    pts = [(-w / 2 - 0.15, -d / 2 - 0.25, t), (w / 2 + 0.15, -d / 2 - 0.25, t), (w / 2 + 0.15, d / 2 + 0.25, t),
           (-w / 2 - 0.15, d / 2 + 0.25, t), (-w / 2 - 0.15, 0, rh + t), (w / 2 + 0.15, 0, rh + t)]
    vs = [bm.verts.new(p) for p in pts]
    for f in ((0, 1, 5, 4), (2, 3, 4, 5)):
        bm.faces.new([vs[i] for i in f])
    return bm


def street_lamp(loc, lit=True):
    pm = M('LampIron', '#22201E', rough=0.45, metal=0.8)
    objs = [lib.cyl(0.06, 3.6, (0, 0, 1.8), pm, name='LampPost'),
            lib.cyl(0.14, 0.3, (0, 0, 0.15), pm, name='LampBase'),
            lib.box((0.3, 0.3, 0.42), (0, 0, 3.85), lib.mat('LampGlass', '#FFE2B0', rough=0.2, emit='#FFC67A',
                                                            emit_strength=8.0 if lit else 0.0), bevel=0.02,
                    name='LampHead'),
            lib.cyl(0.2, 0.08, (0, 0, 4.1), pm, r2=0.05, name='LampCap')]
    e = group('Lamp', objs, loc)
    if lit:
        lib.light('POINT', (loc[0], loc[1], loc[2] + 3.85), energy=60, color='#FFC47A', size=0.2)
    return e


def cobbles(size=(40, 40), loc=(0, 0, 0), col='#7B7268', name='Cobbles'):
    m = pbr(name, 'cobblestone_floor_001', 2.0)
    if m:
        return lib.plane(size, loc, m, name=name)
    m = bpy.data.materials.get(name + 'Mat')
    if not m:
        m = bpy.data.materials.new(name + 'Mat')
        m.use_nodes = True
        nt = m.node_tree
        p = nt.nodes['Principled BSDF']
        tc = nt.nodes.new('ShaderNodeTexCoord')
        vor = nt.nodes.new('ShaderNodeTexVoronoi')
        vor.feature = 'DISTANCE_TO_EDGE'
        vor.inputs['Scale'].default_value = 5.0
        nt.links.new(tc.outputs['Object'], vor.inputs['Vector'])
        vc = nt.nodes.new('ShaderNodeTexVoronoi')
        vc.inputs['Scale'].default_value = 5.0
        nt.links.new(tc.outputs['Object'], vc.inputs['Vector'])
        ramp = nt.nodes.new('ShaderNodeValToRGB')
        c = lib.C(col)
        ramp.color_ramp.elements[0].color = tuple(v * 0.35 for v in c[:3]) + (1,)
        ramp.color_ramp.elements[0].position = 0.0
        ramp.color_ramp.elements[1].position = 0.08
        ramp.color_ramp.elements[1].color = c
        nt.links.new(vor.outputs['Distance'], ramp.inputs['Fac'])
        mix = nt.nodes.new('ShaderNodeMix')                 # each stone a little lighter or darker, no colour cast
        mix.data_type = 'RGBA'
        mix.blend_type = 'MULTIPLY'
        mix.inputs['Factor'].default_value = 1.0
        bw = nt.nodes.new('ShaderNodeRGBToBW')
        nt.links.new(vc.outputs['Color'], bw.inputs['Color'])
        mr = nt.nodes.new('ShaderNodeMapRange')
        mr.inputs['To Min'].default_value = 0.7
        mr.inputs['To Max'].default_value = 1.15
        nt.links.new(bw.outputs['Val'], mr.inputs['Value'])
        nt.links.new(ramp.outputs['Color'], mix.inputs[6])
        nt.links.new(mr.outputs['Result'], mix.inputs[7])
        nt.links.new(mix.outputs[2], p.inputs['Base Color'])
        bmp = nt.nodes.new('ShaderNodeBump')
        bmp.inputs['Strength'].default_value = 0.6
        bmp.inputs['Distance'].default_value = 0.05
        nt.links.new(vor.outputs['Distance'], bmp.inputs['Height'])
        nt.links.new(bmp.outputs['Normal'], p.inputs['Normal'])
        p.inputs['Roughness'].default_value = 0.75
    return lib.plane(size, loc, m, name=name)


def mannequin(loc, heading=0.0, bag_col=None, name='Mannequin', rnd=None):
    """A faceless display mannequin (smooth, satin), standing in a queue; optional handbag on the forearm."""
    rnd = rnd or random.Random(1)
    sk = M('Mannequin', '#E9E2D8', rough=0.35, var=0.02, bump=0.0, coat=0.3)
    dress = M('Dress' + str(rnd.randrange(5)), ['#3D4A5C', '#7A2E2E', '#2F4F3A', '#5C4A3D', '#202020'][rnd.randrange(5)],
              rough=0.8, var=0.08, bump=0.3, bs=200)
    objs = [lib.sphere(0.11, (0, 0, 1.62), sk, scale=(0.85, 0.95, 1.15), name=name + 'Head'),
            lib.cyl(0.04, 0.12, (0, 0, 1.47), sk, name=name + 'Neck'),
            lib.cyl(0.17, 0.62, (0, 0, 1.12), dress, r2=0.19, name=name + 'Torso'),
            lib.cyl(0.29, 0.62, (0, 0, 0.55), dress, r2=0.16, name=name + 'Skirt'),
            lib.cyl(0.035, 0.42, (-0.07, 0, 0.21), sk, name=name + 'LegL'),
            lib.cyl(0.035, 0.42, (0.07, 0, 0.21), sk, name=name + 'LegR'),
            lib.cyl(0.03, 0.6, (-0.21, 0, 1.12), sk, rot=(0, 0.12, 0), name=name + 'ArmL'),
            lib.cyl(0.03, 0.34, (0.22, -0.12, 1.06), sk, rot=(math.radians(70), 0, 0), name=name + 'ArmR')]
    for o in objs:
        sub(o, 1) if 'Head' in o.name else None
    e = group(name, objs)
    if bag_col:
        hb = handbag((0.22, -0.26, 0.86), w=0.26, h=0.19, d=0.12, col=bag_col, name=name + 'Bag')
        hb.parent = e
    e.location = loc
    e.rotation_euler.z = heading
    return e


def truck40(loc, heading=0.0, col='#4E5A3A', name='Truck'):
    """A 1940s cab-over-engine lorry (rounded bonnet, separate fenders, round headlamps, canvas-covered bed),
    olive paint; the bed is loaded with orange gift boxes. Front faces -Y before heading."""
    paint = M('TruckPaint' + col, col, rough=0.55, var=0.1, bump=0.08, coat=0.2)
    dark = M('TruckDark', '#1E1F1C', rough=0.6)
    canvas = cloth('#8C8460', 'TruckCanvas')
    objs = [lib.box((1.9, 1.6, 0.9), (0, -1.6, 1.15), paint, bevel=0.18, name=name + 'Bonnet'),
            lib.box((2.0, 1.3, 1.3), (0, -0.4, 1.55), paint, bevel=0.14, name=name + 'Cab'),
            lib.box((1.6, 0.05, 0.6), (0, -1.06, 1.85), lib.mat('TruckGlass', '#2C343A', rough=0.05), bevel=0,
                    name=name + 'Windscreen'),
            lib.box((0.9, 0.06, 0.5), (0, -2.42, 1.1), M('Grille', '#2A2A26', rough=0.4, metal=0.7), bevel=0.03,
                    name=name + 'Grille'),
            lib.box((2.2, 3.6, 0.15), (0, 1.6, 0.85), wood('#5A4632', 'TruckBed'), bevel=0.02, name=name + 'Bed'),
            lib.box((2.2, 3.4, 1.4), (0, 1.65, 1.65), canvas, bevel=0.35, name=name + 'Tilt')]
    for sx in (-1, 1):
        objs.append(lib.sphere(0.5, (sx * 0.95, -1.75, 0.75), paint, scale=(0.55, 1.2, 0.6), name=name + 'Fender'))
        objs.append(lib.cyl(0.14, 0.12, (sx * 0.7, -2.45, 1.35), M('Chrome', '#C9CCCF', rough=0.15, metal=1.0),
                            rot=(math.radians(90), 0, 0), name=name + 'Lamp'))
        for y in (-1.6, 1.0, 2.4):
            objs.append(lib.cyl(0.48, 0.32, (sx * 1.0, y, 0.48), dark, rot=(0, math.radians(90), 0), verts=32,
                                name=name + 'Wheel'))
            objs.append(lib.cyl(0.22, 0.34, (sx * 1.0, y, 0.48), paint, rot=(0, math.radians(90), 0), verts=24,
                                name=name + 'Hub'))
    e = group(name, objs, loc)
    e.rotation_euler.z = heading
    return e


def poster40(loc, text1, text2='', rot_z=0.0, w=1.2, h=1.7, bg='#E9DCC0', ink='#B3261E', name='Poster'):
    """A 1940s-style printed poster: cream paper, a big red slogan, a black rule, a smaller second line."""
    pm = paper(bg, 'Poster' + bg)
    objs = [lib.box((w, 0.01, h), (0, 0, 0), pm, bevel=0, name=name + 'Paper'),
            lib.box((w * 0.86, 0.012, 0.06), (0, -0.006, h * 0.1), M('PosterBlack', '#1E1A16', rough=0.8), bevel=0,
                    name=name + 'Rule')]
    objs.append(text(text1, w * 0.14, (0, -0.008, h * 0.28), m=M('PosterInk' + ink, ink, rough=0.8), font=SANS,
                     extrude=0.0005, name=name + 'T1'))
    if text2:
        objs.append(text(text2, w * 0.075, (0, -0.008, -h * 0.05), m=M('PosterBlack', '#1E1A16'), font=SANS,
                         extrude=0.0005, name=name + 'T2'))
    # a stylised gilt handbag emblem in the lower half
    hb = handbag((0, -0.02, -h * 0.42), w=w * 0.34, h=w * 0.25, d=0.02, col='#C99A3E', name=name + 'Bag', lock=False)
    hb.rotation_euler = (0, 0, 0)
    objs.append(hb)
    e = group(name, objs, loc)
    e.rotation_euler.z = rot_z
    return e


POSTERS = [('ВСЕ НА\nРАСПРОДАЖУ!', 'ЭРМЕСОВКА ЖДЁТ'), ('БЕРЕГИ\nПЫЛЬНИК!', 'СМОЛОДУ'),
           ('СКИДКА —\nНЕ ПОВОД!', 'ЛИСТ ОЖИДАНИЯ'), ('ВПЕРЁД,\nЗА СУМКОЙ!', 'РЕСПУБЛИКА БИРКИН')]


def ad_column(loc, name='AdColumn', seed=0):
    """A 1940s advertising column (Litfass) with four posters round it and a little dome on top."""
    st = M('ColumnStone', '#CFC5B4', rough=0.85, var=0.1, bump=0.2)
    objs = [lib.cyl(0.55, 2.7, (0, 0, 1.35), st, verts=40, name=name + 'Body'),
            lib.cyl(0.66, 0.16, (0, 0, 2.78), M('ColumnTrim', '#3C4A3A', rough=0.5, metal=0.4), verts=40, name=name + 'Rim'),
            lib.sphere(0.5, (0, 0, 2.86), M('ColumnTrim', '#3C4A3A'), scale=(1, 1, 0.55), name=name + 'Dome'),
            lib.cyl(0.62, 0.3, (0, 0, 0.15), st, verts=40, name=name + 'Base')]
    for k in range(4):
        a = k * math.pi / 2 + seed
        t1, t2 = POSTERS[(k + seed) % len(POSTERS)]
        p = poster40((0.56 * math.sin(a), -0.56 * math.cos(a), 1.55), t1, t2, rot_z=a, w=0.72, h=1.05,
                     name=f'{name}P{k}')
        objs.append(p)
    return group(name, objs, loc)


def radio40(loc, rot_z=0.0, name='Radio'):
    """A wooden 1940s table radio with a fabric grille and a glowing dial."""
    objs = [lib.box((0.42, 0.22, 0.3), (0, 0, 0.15), wood('#6B3E1E', 'RadioWood'), bevel=0.04, name=name + 'Case'),
            lib.box((0.26, 0.01, 0.15), (-0.03, -0.11, 0.19), cloth('#B9A27A', 'RadioCloth'), bevel=0, name=name + 'Grill'),
            lib.cyl(0.04, 0.012, (0.14, -0.11, 0.2), lib.mat('RadioDial', '#F3D9A0', emit='#FFC67A', emit_strength=2.0),
                    rot=(math.radians(90), 0, 0), name=name + 'Dial')]
    for x in (0.09, 0.17):
        objs.append(lib.cyl(0.018, 0.02, (x, -0.115, 0.08), gold(), rot=(math.radians(90), 0, 0), name=name + 'Knob'))
    e = group(name, objs, loc)
    e.rotation_euler.z = rot_z
    return e


def stanchion(loc, h=0.95):
    g = gold()
    return [lib.cyl(0.025, h, (loc[0], loc[1], h / 2), g, name='StanPost'),
            lib.cyl(0.16, 0.03, (loc[0], loc[1], 0.015), g, name='StanBase'),
            lib.sphere(0.04, (loc[0], loc[1], h + 0.02), g, name='StanTop')]


def rope(a, b, h=0.9, sag=0.18):
    rm = M('Velvet', '#7A1424', rough=0.9, var=0.06, bump=0.2, sss=0.0)
    pts = [tuple(Vector(a).lerp(Vector(b), k / 10) + Vector((0, 0, h - sag * math.sin(math.pi * k / 10))))
           for k in range(11)]
    return tube(pts, 0.018, rm, 'Rope')
