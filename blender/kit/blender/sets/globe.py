"""Globe with real country borders (world-atlas 50m) — hook / arcs / redraw variants."""
import bpy, math, json, os, random
from mathutils import Vector
import lib
from lib import C

R = 1.0

def ll2v(lon, lat, r=R):
    lo, la = math.radians(lon), math.radians(lat)
    return Vector((r * math.cos(la) * math.cos(lo), r * math.cos(la) * math.sin(lo), r * math.sin(la)))

def globe_material(unify_start=0.0):
    m = bpy.data.materials.new('Earth')
    m.use_nodes = True
    nt = m.node_tree
    p = nt.nodes['Principled BSDF']
    L = nt.links
    tc = nt.nodes.new('ShaderNodeTexCoord')
    nrm = nt.nodes.new('ShaderNodeVectorMath'); nrm.operation = 'NORMALIZE'
    L.new(tc.outputs['Object'], nrm.inputs[0])
    sep = nt.nodes.new('ShaderNodeSeparateXYZ'); L.new(nrm.outputs[0], sep.inputs[0])
    at = nt.nodes.new('ShaderNodeMath'); at.operation = 'ARCTAN2'
    L.new(sep.outputs['Y'], at.inputs[0]); L.new(sep.outputs['X'], at.inputs[1])
    u = nt.nodes.new('ShaderNodeMath'); u.operation = 'MULTIPLY_ADD'
    u.inputs[1].default_value = 1 / (2 * math.pi); u.inputs[2].default_value = 0.5
    L.new(at.outputs[0], u.inputs[0])
    asn = nt.nodes.new('ShaderNodeMath'); asn.operation = 'ARCSINE'; L.new(sep.outputs['Z'], asn.inputs[0])
    v = nt.nodes.new('ShaderNodeMath'); v.operation = 'MULTIPLY_ADD'
    v.inputs[1].default_value = 1 / math.pi; v.inputs[2].default_value = 0.5
    L.new(asn.outputs[0], v.inputs[0])
    uv = nt.nodes.new('ShaderNodeCombineXYZ'); L.new(u.outputs[0], uv.inputs['X']); L.new(v.outputs[0], uv.inputs['Y'])
    pol_img = bpy.data.images.load(os.path.join(lib.DATA, 'land_political.png'))
    msk_img = bpy.data.images.load(os.path.join(lib.DATA, 'land_mask.png'))
    msk_img.colorspace_settings.name = 'Non-Color'
    tpol = nt.nodes.new('ShaderNodeTexImage'); tpol.image = pol_img; tpol.extension = 'EXTEND'; tpol.interpolation = 'Cubic'
    tmsk = nt.nodes.new('ShaderNodeTexImage'); tmsk.image = msk_img; tmsk.extension = 'EXTEND'; tmsk.interpolation = 'Cubic'
    L.new(uv.outputs[0], tpol.inputs['Vector']); L.new(uv.outputs[0], tmsk.inputs['Vector'])
    # unify factor (animated): political colours -> one land
    unify = nt.nodes.new('ShaderNodeValue'); unify.name = 'Unify'; unify.outputs[0].default_value = unify_start
    land = nt.nodes.new('ShaderNodeMix'); land.data_type = 'RGBA'; land.name = 'LandMix'
    L.new(unify.outputs[0], land.inputs['Factor'])
    L.new(tpol.outputs['Color'], land.inputs['A'])
    land.inputs['B'].default_value = C('#7A6754')
    # relief noise on land
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 18; nz.inputs['Detail'].default_value = 12
    nz.inputs['Roughness'].default_value = 0.62
    L.new(nrm.outputs[0], nz.inputs['Vector'])
    shade = nt.nodes.new('ShaderNodeMapRange')
    shade.inputs['To Min'].default_value = 0.78; shade.inputs['To Max'].default_value = 1.12
    L.new(nz.outputs['Fac'], shade.inputs['Value'])
    landv = nt.nodes.new('ShaderNodeMix'); landv.data_type = 'RGBA'; landv.blend_type = 'MULTIPLY'
    landv.inputs['Factor'].default_value = 1.0
    comb = nt.nodes.new('ShaderNodeCombineXYZ')
    for s in 'XYZ':
        L.new(shade.outputs['Result'], comb.inputs[s])
    L.new(land.outputs['Result'], landv.inputs['A']); L.new(comb.outputs[0], landv.inputs['B'])
    # ocean with depth-like variation
    nzo = nt.nodes.new('ShaderNodeTexNoise'); nzo.inputs['Scale'].default_value = 4; nzo.inputs['Detail'].default_value = 4
    L.new(nrm.outputs[0], nzo.inputs['Vector'])
    ocean = nt.nodes.new('ShaderNodeMix'); ocean.data_type = 'RGBA'
    L.new(nzo.outputs['Fac'], ocean.inputs['Factor'])
    ocean.inputs['A'].default_value = C('#0E1215'); ocean.inputs['B'].default_value = C('#1A1C1D')
    base = nt.nodes.new('ShaderNodeMix'); base.data_type = 'RGBA'
    L.new(tmsk.outputs['Color'], base.inputs['Factor'])
    L.new(ocean.outputs['Result'], base.inputs['A']); L.new(landv.outputs['Result'], base.inputs['B'])
    L.new(base.outputs['Result'], p.inputs['Base Color'])
    rough = nt.nodes.new('ShaderNodeMapRange')
    rough.inputs['To Min'].default_value = 0.62; rough.inputs['To Max'].default_value = 0.9
    L.new(tmsk.outputs['Color'], rough.inputs['Value'])
    L.new(rough.outputs['Result'], p.inputs['Roughness'])
    p.inputs['Specular IOR Level'].default_value = 0.25
    bump = nt.nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = 0.35; bump.inputs['Distance'].default_value = 0.004
    hm = nt.nodes.new('ShaderNodeMath'); hm.operation = 'MULTIPLY'
    L.new(nz.outputs['Fac'], hm.inputs[0]); L.new(tmsk.outputs['Color'], hm.inputs[1])
    L.new(hm.outputs[0], bump.inputs['Height']); L.new(bump.outputs['Normal'], p.inputs['Normal'])
    return m, unify

def atmosphere(r=1.03, color='#E7A47C', strength=1.6, sun_dir=(1, -0.5, 0.35)):
    ob = lib.sphere(r, (0, 0, 0), None, 128, 64, name='Atmosphere')
    m = bpy.data.materials.new('Atmo')
    m.use_nodes = True
    try:
        m.surface_render_method = 'BLENDED'
    except Exception:
        m.blend_method = 'BLEND'
    m.use_backface_culling = True
    nt = m.node_tree
    nt.nodes.clear()
    L = nt.links
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.5
    pw = nt.nodes.new('ShaderNodeMath'); pw.operation = 'POWER'; pw.inputs[1].default_value = 5.0
    L.new(lw.outputs['Facing'], pw.inputs[0])
    # brighter on the day side
    geo = nt.nodes.new('ShaderNodeNewGeometry')
    dot = nt.nodes.new('ShaderNodeVectorMath'); dot.operation = 'DOT_PRODUCT'
    L.new(geo.outputs['Normal'], dot.inputs[0]); dot.inputs[1].default_value = Vector(sun_dir).normalized()
    day = nt.nodes.new('ShaderNodeMapRange')
    day.inputs['From Min'].default_value = -0.45; day.inputs['From Max'].default_value = 0.6
    day.inputs['To Min'].default_value = 0.08; day.inputs['To Max'].default_value = 1.0
    L.new(dot.outputs['Value'], day.inputs['Value'])
    mul = nt.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'
    L.new(pw.outputs[0], mul.inputs[0]); L.new(day.outputs['Result'], mul.inputs[1])
    em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = C(color)
    sm = nt.nodes.new('ShaderNodeMath'); sm.operation = 'MULTIPLY'; sm.inputs[1].default_value = strength
    L.new(mul.outputs[0], sm.inputs[0]); L.new(sm.outputs[0], em.inputs['Strength'])
    tr = nt.nodes.new('ShaderNodeBsdfTransparent')
    add = nt.nodes.new('ShaderNodeAddShader')
    L.new(tr.outputs[0], add.inputs[0]); L.new(em.outputs[0], add.inputs[1])
    L.new(add.outputs[0], out.inputs['Surface'])
    ob.data.materials.append(m)
    ob.visible_shadow = False
    return ob

def stars_world():
    w, nt, bg = lib.world_color('#000000', 1.0)
    L = nt.links
    geo = nt.nodes.new('ShaderNodeTexCoord')
    vor = nt.nodes.new('ShaderNodeTexVoronoi'); vor.inputs['Scale'].default_value = 160
    try:
        vor.inputs['Randomness'].default_value = 1.0
    except Exception:
        pass
    L.new(geo.outputs['Generated'], vor.inputs['Vector'])
    mr = nt.nodes.new('ShaderNodeMapRange')
    mr.inputs['From Min'].default_value = 0.075; mr.inputs['From Max'].default_value = 0.0
    L.new(vor.outputs['Distance'], mr.inputs['Value'])
    pw = nt.nodes.new('ShaderNodeMath'); pw.operation = 'POWER'; pw.inputs[1].default_value = 6
    L.new(mr.outputs['Result'], pw.inputs[0])
    # random brightness per star
    sep = nt.nodes.new('ShaderNodeSeparateColor')
    L.new(vor.outputs['Color'], sep.inputs[0])
    mul = nt.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'
    L.new(pw.outputs[0], mul.inputs[0]); L.new(sep.outputs[0], mul.inputs[1])
    gate = nt.nodes.new('ShaderNodeMath'); gate.operation = 'GREATER_THAN'; gate.inputs[1].default_value = 0.55
    L.new(sep.outputs[1], gate.inputs[0])
    mul2 = nt.nodes.new('ShaderNodeMath'); mul2.operation = 'MULTIPLY'
    L.new(mul.outputs[0], mul2.inputs[0]); L.new(gate.outputs[0], mul2.inputs[1])
    s3 = nt.nodes.new('ShaderNodeMath'); s3.operation = 'MULTIPLY'; s3.inputs[1].default_value = 2.5
    L.new(mul2.outputs[0], s3.inputs[0])
    col = nt.nodes.new('ShaderNodeMix'); col.data_type = 'RGBA'
    L.new(s3.outputs[0], col.inputs['Factor'])
    col.inputs['A'].default_value = C('#07080A'); col.inputs['B'].default_value = C('#FFE9D2')
    L.new(col.outputs['Result'], bg.inputs['Color'])
    return w

def border_curves(src='borders_50m.json', r=1.0016, bevel=0.0017, color='#FF8A2A', strength=7.0, name='Borders',
                  jitter=0.0, groups=1, seed=3):
    polys = json.load(open(os.path.join(lib.DATA, src)))
    rnd = random.Random(seed)
    rnd.shuffle(polys)
    objs = []
    m, em = lib.emission_mat(name + 'Glow', color, strength)
    for g in range(groups):
        part = polys[g::groups]
        pts_list = []
        for poly in part:
            pts = []
            for lon, lat in poly:
                if jitter:
                    lon += rnd.uniform(-jitter, jitter); lat += rnd.uniform(-jitter, jitter)
                pts.append(ll2v(lon, lat, r))
            pts_list.append(pts)
        ob = lib.curve_poly(f'{name}{g}', pts_list, bevel=bevel, mat_=m, res=1)
        ob.visible_shadow = False
        objs.append(ob)
    return objs, em

def coast_curves(r=1.0011, color='#EDE3D4', strength=0.5):
    polys = json.load(open(os.path.join(lib.DATA, 'coast_50m.json')))
    m, em = lib.emission_mat('CoastGlow', color, strength)
    ob = lib.curve_poly('Coast', [[ll2v(lo, la, r) for lo, la in p] for p in polys], bevel=0.0007, mat_=m, res=0)
    ob.visible_shadow = False
    return ob, em

def arc_points(a, b, h=0.22, n=64, r=1.004):
    va, vb = ll2v(*a).normalized(), ll2v(*b).normalized()
    ang = va.angle(vb)
    pts = []
    for i in range(n + 1):
        t = i / n
        # slerp
        if ang < 1e-6:
            d = va
        else:
            d = (va * math.sin((1 - t) * ang) + vb * math.sin(t * ang)) / math.sin(ang)
        rr = r + h * ang / math.pi * 2.2 * math.sin(math.pi * t)
        pts.append(d.normalized() * rr)
    return pts

def cam_on(lon, lat, dist, shift_y=0.16, lens=50, roll=0.0):
    cam = lib.camera(tuple(ll2v(lon, lat, dist)), (0, 0, 0), lens=lens, shift=(0, shift_y))
    return cam

def build(shot, fps=60):
    ev = shot.get('events', {})
    dur = shot['dur']
    variant = shot.get('variant', 'hook')
    stars_world()
    sun_dir = ll2v(-64, 18).normalized()
    sun = lib.light('SUN', (0, 0, 0), energy=4.6, color='#FFE2C4', size=0.6)
    fill = lib.light('SUN', (0, 0, 0), energy=0.12, color='#8FA2B8', size=5.0, name='Fill')
    fill.rotation_euler = (sun_dir).to_track_quat('-Z', 'Y').to_euler()
    sun.rotation_euler = (-sun_dir).to_track_quat('-Z', 'Y').to_euler()
    earth = lib.sphere(R, (0, 0, 0), None, 256, 128, name='Earth')
    gm, unify = globe_material(0.0 if variant == 'hook' else 1.0)
    earth.data.materials.append(gm)
    atmo = atmosphere(sun_dir=sun_dir)
    spin = lib.empty('Spin')  # everything on the globe rotates together
    earth.parent = spin
    coast, coast_em = coast_curves()
    coast.parent = spin
    lib.bloom(strength=0.42, threshold=0.9, size=8)
    F = lambda t: lib.sec2f(t)
    f_end = int(round(dur * fps))

    if variant == 'hook':
        borders, bem = border_curves()
        for b in borders:
            b.parent = spin
        # slow spin of the globe (+12 deg)
        lib.key_obj(spin, 1, rot=(0, 0, math.radians(-6)), interp='LINEAR')
        lib.key_obj(spin, f_end, rot=(0, 0, math.radians(8)), interp='LINEAR')
        t_d = ev.get('dissolve', 2.4)       # 'исчезли'
        t_r = ev.get('redraw', dur + 10)    # 'Сто девяносто пять' -> borders return
        t_r2 = ev.get('redraw_end', t_r + 2.6)
        # dissolve
        lib.key_value(bem.inputs['Strength'], 1, 6.0)
        lib.key_value(bem.inputs['Strength'], F(t_d - 0.05), 6.0)
        lib.key_value(bem.inputs['Strength'], F(t_d + 0.12), 16.0)
        lib.key_value(bem.inputs['Strength'], F(t_d + 0.75), 0.0)
        lib.key_value(unify.outputs[0], 1, 0.0)
        lib.key_value(unify.outputs[0], F(t_d), 0.0)
        lib.key_value(unify.outputs[0], F(t_d + 0.9), 1.0)
        for b in borders:
            cu = b.data
            cu.bevel_factor_end = 1.0
            cu.keyframe_insert('bevel_factor_end', frame=1)
            cu.keyframe_insert('bevel_factor_end', frame=F(t_d + 0.8))
            cu.bevel_depth = 0.0017
            cu.keyframe_insert('bevel_depth', frame=1)
            cu.keyframe_insert('bevel_depth', frame=F(t_d))
            cu.bevel_depth = 0.0
            cu.keyframe_insert('bevel_depth', frame=F(t_d + 0.75))
        if t_r < dur:
            # borders are drawn again: 195 countries, 250 000 km of lines
            for b in borders:
                cu = b.data
                cu.bevel_depth = 0.0
                cu.keyframe_insert('bevel_depth', frame=F(t_r - 0.12))
                cu.bevel_factor_end = 0.0
                cu.keyframe_insert('bevel_factor_end', frame=F(t_r - 0.12))
                cu.keyframe_insert('bevel_factor_end', frame=F(t_r))
                cu.bevel_depth = 0.0017
                cu.keyframe_insert('bevel_depth', frame=F(t_r - 0.04))
                cu.bevel_factor_end = 1.0
                cu.keyframe_insert('bevel_factor_end', frame=F(t_r2))
            lib.key_value(bem.inputs['Strength'], F(t_r - 0.05), 0.0)
            lib.key_value(bem.inputs['Strength'], F(t_r + 0.2), 7.0)
            lib.key_value(unify.outputs[0], F(t_r), 1.0)
            lib.key_value(unify.outputs[0], F(t_r2), 0.0)
        cam = cam_on(18, 32, 3.35, shift_y=0.16, lens=50)
        keys = [(0, tuple(ll2v(18, 32, 3.35))), (min(t_r, dur), tuple(ll2v(16, 34, 2.95)))]
        if t_r < dur:
            keys.append((dur, tuple(ll2v(40, 30, 3.25))))
        lib.animate_camera(cam, keys, [(0, (0, 0, 0)), (dur, (0, 0, 0))], step=2)

    elif variant == 'arcs':
        lib.key_obj(spin, 1, rot=(0, 0, math.radians(-4)), interp='LINEAR')
        lib.key_obj(spin, f_end, rot=(0, 0, math.radians(5)), interp='LINEAR')
        routes = [((3.4, 6.5), (-0.1, 51.5)), ((90.4, 23.8), (55.3, 25.2)), ((67.0, 24.9), (55.3, 25.2)),
                  ((31.2, 30.0), (13.4, 52.5)), ((15.3, -4.3), (2.35, 48.85)), ((77.2, 28.6), (-0.1, 51.5)),
                  ((36.8, -1.3), (-3.7, 40.4)), ((-74.1, 4.7), (-3.7, 40.4)), ((121.0, 14.6), (55.3, 25.2)),
                  ((44.4, 33.3), (13.4, 52.5)), ((-17.4, 14.7), (2.35, 48.85)), ((72.9, 19.1), (-79.4, 43.7)),
                  ((106.8, -6.2), (139.7, 35.7)), ((28.0, -26.2), (-0.1, 51.5)), ((38.7, 9.0), (46.7, 24.7)),
                  ((85.3, 27.7), (51.5, 25.3)), ((-0.2, 5.6), (12.5, 41.9)), ((69.2, 41.3), (37.6, 55.75))]
        rnd = random.Random(11)
        m_trail, em_trail = lib.emission_mat('ArcTrail', '#E08A55', 1.6)
        m_head, em_head = lib.emission_mat('ArcHead', '#FFD9A8', 14.0)
        t0 = ev.get('start', 0.15)
        for i, (a, b) in enumerate(routes):
            pts = arc_points(a, b, h=0.2)
            trail = lib.curve_poly(f'Trail{i}', [pts], bevel=0.0018, mat_=m_trail, res=1)
            head = lib.curve_poly(f'Pulse{i}', [pts], bevel=0.0042, mat_=m_head, res=2)
            for ob in (trail, head):
                ob.parent = spin
                ob.visible_shadow = False
            st = t0 + (i % 9) * 0.22 + rnd.uniform(0, 0.15)
            cu = trail.data
            cu.bevel_factor_end = 0.0; cu.keyframe_insert('bevel_factor_end', frame=F(st))
            cu.bevel_factor_end = 1.0; cu.keyframe_insert('bevel_factor_end', frame=F(st + 1.4))
            # repeating pulses
            hc = head.data
            per = 1.6 + rnd.uniform(-0.2, 0.3)
            k = 0
            t = st
            while t < dur + 1:
                hc.bevel_factor_start = 0.0; hc.bevel_factor_end = 0.0
                hc.keyframe_insert('bevel_factor_start', frame=F(t)); hc.keyframe_insert('bevel_factor_end', frame=F(t))
                hc.bevel_factor_end = 1.0; hc.keyframe_insert('bevel_factor_end', frame=F(t + per * 0.8))
                hc.bevel_factor_start = 1.0; hc.keyframe_insert('bevel_factor_start', frame=F(t + per))
                t += per
                k += 1
            if hc.animation_data and hc.animation_data.action:
                for fc in hc.animation_data.action.fcurves:
                    for kp in fc.keyframe_points:
                        kp.interpolation = 'LINEAR'
        # glowing dots at destinations
        mdot, _ = lib.emission_mat('CityDot', '#FFB980', 9.0)
        for d in {r[1] for r in routes}:
            s = lib.sphere(0.0085, tuple(ll2v(d[0], d[1], 1.003)), mdot, 12, 8, name='Dest')
            s.parent = spin
        cam = cam_on(32, 30, 3.3, shift_y=0.16, lens=50)
        lib.animate_camera(cam, [(0, tuple(ll2v(30, 30, 3.45))), (dur, tuple(ll2v(36, 32, 3.05)))],
                           [(0, (0, 0, 0)), (dur, (0, 0, 0))], step=2)

    elif variant == 'redraw':
        lib.key_obj(spin, 1, rot=(0, 0, math.radians(-8)), interp='LINEAR')
        lib.key_obj(spin, f_end, rot=(0, 0, math.radians(6)), interp='LINEAR')
        borders, bem = border_curves('borders_110m.json', r=1.002, bevel=0.0021, color='#FF5A24', strength=9.0,
                                     name='NewLines', jitter=0.35, groups=8, seed=5)
        t0 = ev.get('start', 0.3)
        span = ev.get('span', dur - 1.0)
        for i, b in enumerate(borders):
            b.parent = spin
            cu = b.data
            st = t0 + span * i / len(borders) * 0.85
            cu.bevel_factor_end = 0.0; cu.keyframe_insert('bevel_factor_end', frame=F(st))
            cu.bevel_factor_end = 1.0; cu.keyframe_insert('bevel_factor_end', frame=F(st + 1.3))
        cam = cam_on(20, 38, 3.2, shift_y=0.16, lens=50)
        lib.animate_camera(cam, [(0, tuple(ll2v(10, 38, 3.2))), (dur, tuple(ll2v(45, 33, 2.95)))],
                           [(0, (0, 0, 0)), (dur, (0, 0, 0))], step=2)
    return dict(samples=48, fill=0.22, exposure=0.25)
