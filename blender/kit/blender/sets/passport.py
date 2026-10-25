"""Desk close-up: an open passport with stamps on a paper map of Europe. It closes, slides away, Schengen merges."""
import bpy, math, os, random
from mathutils import Vector
import lib
from lib import C

TEX = os.path.join(lib.PROJ, 'blender', 'tex')

def img(name, noncolor=False):
    im = bpy.data.images.load(os.path.join(TEX, name), check_existing=True)
    if noncolor:
        im.colorspace_settings.name = 'Non-Color'
    return im

def planar_mat(name, image, u_scale, v_scale, u_off=0.0, v_off=0.5, flip_u=False, rough=0.75, bump=0.0, extra=None):
    """Object-space planar mapping: u = u_off + x*u_scale (or minus), v = v_off + y*v_scale."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    p = nt.nodes['Principled BSDF']
    L = nt.links
    tc = nt.nodes.new('ShaderNodeTexCoord')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ'); L.new(tc.outputs['Object'], sep.inputs[0])
    u = nt.nodes.new('ShaderNodeMath'); u.operation = 'MULTIPLY_ADD'
    u.inputs[1].default_value = -u_scale if flip_u else u_scale; u.inputs[2].default_value = u_off
    L.new(sep.outputs['X'], u.inputs[0])
    v = nt.nodes.new('ShaderNodeMath'); v.operation = 'MULTIPLY_ADD'
    v.inputs[1].default_value = v_scale; v.inputs[2].default_value = v_off
    L.new(sep.outputs['Y'], v.inputs[0])
    uv = nt.nodes.new('ShaderNodeCombineXYZ'); L.new(u.outputs[0], uv.inputs['X']); L.new(v.outputs[0], uv.inputs['Y'])
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = image; t.extension = 'EXTEND'; t.interpolation = 'Cubic'
    L.new(uv.outputs[0], t.inputs['Vector'])
    L.new(t.outputs['Color'], p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = rough
    p.inputs['Specular IOR Level'].default_value = 0.35
    if bump:
        nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 900; nz.inputs['Detail'].default_value = 6
        L.new(tc.outputs['Object'], nz.inputs['Vector'])
        b = nt.nodes.new('ShaderNodeBump'); b.inputs['Strength'].default_value = bump; b.inputs['Distance'].default_value = 0.0004
        L.new(nz.outputs['Fac'], b.inputs['Height']); L.new(b.outputs['Normal'], p.inputs['Normal'])
    if extra:
        extra(nt, p, t, uv)
    return m

def wood_mat():
    m = bpy.data.materials.new('DeskWood')
    m.use_nodes = True
    nt = m.node_tree
    p = nt.nodes['Principled BSDF']
    L = nt.links
    tc = nt.nodes.new('ShaderNodeTexCoord')
    mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (1.2, 22.0, 1.0)
    L.new(tc.outputs['Object'], mp.inputs['Vector'])
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 3.0; nz.inputs['Detail'].default_value = 3
    L.new(tc.outputs['Object'], nz.inputs['Vector'])
    wv = nt.nodes.new('ShaderNodeTexNoise'); wv.inputs['Scale'].default_value = 6.0; wv.inputs['Detail'].default_value = 6
    wv.inputs['Roughness'].default_value = 0.55
    L.new(mp.outputs[0], wv.inputs['Vector'])
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color = C('#2B1C14'); ramp.color_ramp.elements[1].color = C('#5A3B27')
    L.new(wv.outputs['Fac'], ramp.inputs['Fac'])
    L.new(ramp.outputs['Color'], p.inputs['Base Color'])
    rr = nt.nodes.new('ShaderNodeMapRange'); rr.inputs['To Min'].default_value = 0.38; rr.inputs['To Max'].default_value = 0.6
    L.new(nz.outputs['Fac'], rr.inputs['Value']); L.new(rr.outputs['Result'], p.inputs['Roughness'])
    b = nt.nodes.new('ShaderNodeBump'); b.inputs['Strength'].default_value = 0.15; b.inputs['Distance'].default_value = 0.002
    L.new(wv.outputs['Fac'], b.inputs['Height']); L.new(b.outputs['Normal'], p.inputs['Normal'])
    return m

def map_mat():
    a, b = img('europe_political.jpg'), img('europe_schengen.jpg')
    W, H = 0.62, 0.62 * 2714 / 3000
    holder = {}
    def extra(nt, p, t, uv):
        L = nt.links
        t2 = nt.nodes.new('ShaderNodeTexImage'); t2.image = b; t2.extension = 'EXTEND'; t2.interpolation = 'Cubic'
        L.new(uv.outputs[0], t2.inputs['Vector'])
        val = nt.nodes.new('ShaderNodeValue'); val.name = 'Schengen'; val.outputs[0].default_value = 0.0
        mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'
        L.new(val.outputs[0], mx.inputs['Factor']); L.new(t.outputs['Color'], mx.inputs['A']); L.new(t2.outputs['Color'], mx.inputs['B'])
        L.new(mx.outputs['Result'], p.inputs['Base Color'])
        holder['val'] = val
    m = planar_mat('MapPaper', a, 1 / W, 1 / H, 0.5, 0.5, rough=0.82, bump=0.08, extra=extra)
    return m, holder['val'], W, H

def build(shot, fps=60):
    ev = shot.get('events', {})
    dur = shot['dur']
    F = lib.sec2f
    coll = lib.collection('Desk')
    lib.world_color('#3A322B', 1.0)
    desk = lib.plane((3, 3), (0, 0, 0), wood_mat(), name='Desk', coll=coll)
    mm, schengen, MW, MH = map_mat()
    mp = lib.plane((MW, MH), (-0.02, 0.06, 0.0004), mm, rot=(0, 0, math.radians(-4)), name='Map', coll=coll)
    # passport --------------------------------------------------------------
    PW, PH = 0.088, 0.125
    cov_t, pg_t = 0.0006, 0.0019
    root = lib.empty('Passport', (-0.035, 0.0, 0.0008), (0, 0, math.radians(-9)), coll=coll)
    leather = lib.mat('Leather', '#5A1E20', rough=0.55, var=0.12, var_scale=60, bump=0.25, bump_scale=900)
    pages_img = img('passport_pages.jpg')
    cover_img = img('passport_cover.jpg')
    gold_img = img('passport_cover_gold.png', noncolor=True)
    right_pages = planar_mat('PagesR', pages_img, 0.5 / (PW - 0.002), 1 / (PH - 0.004), 0.5, 0.5, rough=0.85, bump=0.05)
    left_pages = planar_mat('PagesL', pages_img, 0.5 / (PW - 0.002), 1 / (PH - 0.004), 0.5, 0.5, flip_u=True, rough=0.85, bump=0.05)
    def cover_extra(nt, p, t, uv):
        L = nt.links
        g = nt.nodes.new('ShaderNodeTexImage'); g.image = gold_img; g.extension = 'EXTEND'
        L.new(uv.outputs[0], g.inputs['Vector'])
        L.new(g.outputs['Color'], p.inputs['Metallic'])
        r = nt.nodes.new('ShaderNodeMapRange'); r.inputs['To Min'].default_value = 0.6; r.inputs['To Max'].default_value = 0.28
        L.new(g.outputs['Color'], r.inputs['Value']); L.new(r.outputs['Result'], p.inputs['Roughness'])
    cover_m = planar_mat('CoverFront', cover_img, 1 / PW, 1 / PH, 0.0, 0.5, rough=0.55, bump=0.2, extra=cover_extra)
    # back half (static, right side when open)
    bc = lib.box((PW, PH, cov_t), (PW / 2, 0, 0), leather, bevel=0.0012, name='BackCover', coll=coll, origin='bottom')
    bp = lib.box((PW - 0.002, PH - 0.004, pg_t), (0, 0, 0), right_pages, bevel=0.0003, name='PagesBack', coll=coll, origin='bottom')
    bp.location = ((PW - 0.002) / 2 + 0.0004, 0, cov_t)
    for o in (bc, bp):
        o.parent = root
    # hinge (front half rotates around the spine at the top of the back half)
    hinge = lib.empty('Hinge', (0, 0, cov_t + pg_t), (0, -math.pi, 0), coll=coll)
    hinge.parent = root
    fp = lib.box((PW - 0.002, PH - 0.004, pg_t), (0, 0, 0), left_pages, bevel=0.0003, name='PagesFront', coll=coll, origin='bottom')
    fp.location = ((PW - 0.002) / 2 + 0.0004, 0, 0.00005)
    fc = lib.box((PW, PH, cov_t), (PW / 2, 0, pg_t + 0.00005), leather, bevel=0.0012, name='FrontCover', coll=coll, origin='bottom')
    # printed cover face (thin skin on the outside of the front cover)
    skin = lib.plane((PW - 0.0016, PH - 0.0016), (PW / 2, 0, pg_t + cov_t + 0.00007), cover_m, name='CoverPrint', coll=coll)
    for o in (fp, fc, skin):
        o.parent = hinge
    # small spine roll
    spine = lib.cyl(0.0013, PH, (0.0, 0, cov_t + pg_t), leather, rot=(math.radians(90), 0, 0), verts=16, name='Spine', coll=coll)
    spine.parent = root
    # rubber stamp on the map
    st_root = lib.empty('Stamp', (0.17, -0.12, 0.0004), (0, 0, math.radians(28)), coll=coll)
    rub = lib.mat('Rubber', '#1F1B19', rough=0.8)
    wood = lib.mat('StampWood', '#6B4A30', rough=0.5, var=0.15, var_scale=40)
    for o in (lib.box((0.055, 0.032, 0.008), (0, 0, 0), rub, bevel=0.0015, name='StampBase', coll=coll, origin='bottom'),
              lib.box((0.05, 0.028, 0.012), (0, 0, 0.008), wood, bevel=0.003, name='StampBody', coll=coll, origin='bottom'),
              lib.cyl(0.007, 0.05, (0, 0, 0.02), wood, verts=20, name='StampNeck', coll=coll, origin='bottom'),
              lib.sphere(0.014, (0, 0, 0.075), wood, 24, 12, name='StampKnob', coll=coll)):
        o.parent = st_root
    # fountain pen
    pen_m = lib.mat('PenBody', '#1E1C1B', rough=0.25, coat=0.6)
    gold_m = lib.mat('PenGold', '#C9A060', rough=0.3, metal=1.0)
    pen = lib.empty('Pen', (-0.24, -0.15, 0.006), (0, math.radians(90), math.radians(62)), coll=coll)
    for o in (lib.cyl(0.0055, 0.13, (0, 0, 0), pen_m, verts=24, name='PenBarrel', coll=coll),
              lib.cyl(0.0057, 0.004, (0, 0, 0.02), gold_m, verts=24, name='PenRing', coll=coll),
              lib.cyl(0.0055, 0.02, (0, 0, -0.075), gold_m, r2=0.0008, verts=24, name='PenNib', coll=coll)):
        o.parent = pen
    # lights: warm desk lamp + soft cool fill + rim
    lib.light('AREA', (-0.35, -0.25, 0.55), (math.radians(40), math.radians(-30), 0), energy=12, color='#FFD3A1', size=0.35,
              name='DeskLamp', coll=coll)
    look = lib.light('AREA', (0.45, 0.4, 0.5), (math.radians(-40), math.radians(35), 0), energy=5, color='#9FB2C8', size=0.8,
                     name='Fill', coll=coll)
    lib.light('SPOT', (0.0, 0.6, 0.35), (math.radians(-60), 0, math.radians(180)), energy=8, color='#FFB27A', spot=40,
              size=0.1, name='Rim', coll=coll)
    look_at(look)
    # animation -------------------------------------------------------------
    t_close = ev.get('close', 0.9)
    t_slide = ev.get('slide', t_close + 1.1)
    t_sch = ev.get('schengen', dur - 1.6)
    lib.key_obj(hinge, 1, rot=(0, -math.pi, 0))
    lib.key_obj(hinge, F(t_close), rot=(0, -math.pi, 0))
    lib.key_obj(hinge, F(t_close + 0.85), rot=(0, 0, 0))
    lib.key_obj(root, F(t_slide), loc=(-0.035, 0.0, 0.0008), rot=(0, 0, math.radians(-9)))
    lib.key_obj(root, F(t_slide + 1.0), loc=(0.27, -0.2, 0.0008), rot=(0, 0, math.radians(14)))
    lib.key_value(schengen.outputs[0], F(t_sch), 0.0)
    lib.key_value(schengen.outputs[0], F(t_sch + 0.7), 1.0)
    # camera: macro on the stamps -> rises to reveal the map
    cam = lib.camera((0.02, -0.2, 0.26), (0.0, 0.0, 0.0), lens=50, dof=0.3, fstop=2.8)
    cam.data.shift_y = 0.1
    lib.animate_camera(cam,
                       [(0, (0.0, -0.17, 0.25)), (t_close + 0.6, (0.0, -0.18, 0.27)), (t_slide + 1.2, (-0.02, -0.33, 0.62)),
                        (dur, (-0.02, -0.35, 0.7))],
                       [(0, (0.0, 0.005, 0.0)), (t_close + 0.6, (0.005, 0.01, 0.0)), (t_slide + 1.2, (-0.02, 0.07, 0.0)),
                        (dur, (-0.02, 0.07, 0.0))],
                       step=2, focus_keys=[(0, 0.3), (t_close + 0.6, 0.32), (t_slide + 1.2, 0.71), (dur, 0.78)])
    lib.bloom(strength=0.25, threshold=1.5, size=6)
    return dict(samples=64, fill=0.3, exposure=-0.1)

def look_at(ob):
    lib.look_at(ob, (0, 0, 0))
