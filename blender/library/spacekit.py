"""Real-colour space kit for 'kosmos-dlya-vseh' (Blender 4.5, Eevee Next), everything built from code.

Earth uses NASA public-domain imagery in blender/tex/nasa (Blue Marble NG July 2004, Blue Marble clouds, Black Marble 2016),
the Moon in the sky uses the LRO colour map. Ground (Moon, Mars) is a numpy heightfield. Scale: Earth radius R = 100 units
(1 unit = 63.7 km), so low Earth orbit (400 km) is ~6.3 units above the surface.
"""
import bpy, bmesh, math, os, random
import numpy as np
from mathutils import Vector, Matrix
import lib
from lib import C

TEX = os.path.join(lib.PROJ, 'blender', 'tex', 'nasa')
R = 100.0


# ----------------------------------------------------------------------------- helpers
def img(name, noncolor=False):
    im = bpy.data.images.load(os.path.join(TEX, name), check_existing=True)
    if noncolor:
        im.colorspace_settings.name = 'Non-Color'
    return im


def ll2v(lon, lat, r=R):
    lo, la = math.radians(lon), math.radians(lat)
    return Vector((r * math.cos(la) * math.cos(lo), r * math.cos(la) * math.sin(lo), r * math.sin(la)))


def local_frame(lon, lat):
    """(up, east, north) unit vectors at a point on the globe."""
    up = ll2v(lon, lat, 1.0).normalized()
    lo = math.radians(lon)
    east = Vector((-math.sin(lo), math.cos(lo), 0.0))
    north = up.cross(east).normalized()
    return up, east, north


def at_ll(lon, lat, alt, de=0.0, dn=0.0):
    """Point `alt` units above (lon, lat), shifted de east / dn north (units)."""
    up, east, north = local_frame(lon, lat)
    return up * (R + alt) + east * de + north * dn


def sun_light(direction_to_sun, energy=4.5, color='#FFF4E6', size=0.53, name='Sun'):
    d = Vector(direction_to_sun).normalized()
    s = lib.light('SUN', (0, 0, 0), energy=energy, color=color, size=size, name=name)
    s.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    return s


def stars(density=1.0, strength=1.0):
    """Black sky with fine stars (world shader, Generated coordinates)."""
    w, nt, bg = lib.world_color('#000000', strength)
    L = nt.links
    tc = nt.nodes.new('ShaderNodeTexCoord')
    vor = nt.nodes.new('ShaderNodeTexVoronoi'); vor.inputs['Scale'].default_value = 260 * density
    L.new(tc.outputs['Generated'], vor.inputs['Vector'])
    mr = nt.nodes.new('ShaderNodeMapRange')
    mr.inputs['From Min'].default_value = 0.06; mr.inputs['From Max'].default_value = 0.0
    L.new(vor.outputs['Distance'], mr.inputs['Value'])
    pw = nt.nodes.new('ShaderNodeMath'); pw.operation = 'POWER'; pw.inputs[1].default_value = 7
    L.new(mr.outputs['Result'], pw.inputs[0])
    sep = nt.nodes.new('ShaderNodeSeparateColor'); L.new(vor.outputs['Color'], sep.inputs[0])
    gate = nt.nodes.new('ShaderNodeMath'); gate.operation = 'GREATER_THAN'; gate.inputs[1].default_value = 0.62
    L.new(sep.outputs[1], gate.inputs[0])
    m1 = nt.nodes.new('ShaderNodeMath'); m1.operation = 'MULTIPLY'
    L.new(pw.outputs[0], m1.inputs[0]); L.new(gate.outputs[0], m1.inputs[1])
    m2 = nt.nodes.new('ShaderNodeMath'); m2.operation = 'MULTIPLY'
    L.new(m1.outputs[0], m2.inputs[0]); L.new(sep.outputs[0], m2.inputs[1])
    m3 = nt.nodes.new('ShaderNodeMath'); m3.operation = 'MULTIPLY'; m3.inputs[1].default_value = 1.6
    L.new(m2.outputs[0], m3.inputs[0])
    col = nt.nodes.new('ShaderNodeMix'); col.data_type = 'RGBA'
    L.new(m3.outputs[0], col.inputs['Factor'])
    col.inputs['A'].default_value = C('#000000'); col.inputs['B'].default_value = C('#F2F4FF')
    L.new(col.outputs['Result'], bg.inputs['Color'])
    return w


def _equirect(nt, vec):
    """Object-space position -> equirectangular (u, v) for a sphere centred on its origin; returns (uv, normalized)."""
    L = nt.links
    nrm = nt.nodes.new('ShaderNodeVectorMath'); nrm.operation = 'NORMALIZE'; L.new(vec, nrm.inputs[0])
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
    return uv.outputs[0], nrm.outputs[0]


def _tex(nt, image, vec, interp='Cubic'):
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = image; t.interpolation = interp; t.extension = 'REPEAT'
    nt.links.new(vec, t.inputs['Vector'])
    return t


# ----------------------------------------------------------------------------- Earth
SUN_SOCKETS = []     # vector sockets that hold the sun direction (animate_sun keys them all)


def _sun_dot(nt, normal_out, sun_dir):
    dot = nt.nodes.new('ShaderNodeVectorMath'); dot.operation = 'DOT_PRODUCT'
    nt.links.new(normal_out, dot.inputs[0]); dot.inputs[1].default_value = Vector(sun_dir).normalized()
    SUN_SOCKETS.append(dot.inputs[1])
    return dot


def _smin(nt, a, b):
    m = nt.nodes.new('ShaderNodeMath'); m.operation = 'MINIMUM'
    nt.links.new(a, m.inputs[0]); nt.links.new(b, m.inputs[1])
    return m.outputs[0]


def earth(sun_dir, night=2.2, clouds=True, day='earth_day_8k.jpg', seg=(384, 192), r=R, loc=(0, 0, 0), name='Earth',
          atmo=1.0, sat=1.08, patch=None, detail=0.07, haze=0.0, cloud_tex=True, cloud_scale=0.0, cloud_cover=0.5,
          atmo_top=None):
    """Real-colour Earth (+ clouds shell + atmosphere shells). Returns (earth, clouds, atmo list, spin empty).
    patch=(lon0, lon1, lat0, lat1, file): sharper crop of the 21600 map blended in over that box.
    cloud_tex=False + cloud_scale>0: procedural cloud deck (feature size ~1/cloud_scale units) instead of the 2k map."""
    spin = lib.empty(name + 'Spin', loc)
    e = lib.sphere(r, (0, 0, 0), None, seg[0], seg[1], name=name)
    e.parent = spin
    e.visible_shadow = False
    m = bpy.data.materials.new(name + 'Mat'); m.use_nodes = True
    nt = m.node_tree; L = nt.links; p = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord')
    uv, nrm = _equirect(nt, tc.outputs['Object'])
    tday = _tex(nt, img(day), uv)
    col = tday.outputs['Color']
    if patch:
        lon0, lon1, lat0, lat1, fn = patch
        sep = nt.nodes.new('ShaderNodeSeparateXYZ'); L.new(uv, sep.inputs[0])
        pu = nt.nodes.new('ShaderNodeMath'); pu.operation = 'MULTIPLY_ADD'
        pu.inputs[1].default_value = 360.0 / (lon1 - lon0); pu.inputs[2].default_value = -(lon0 / 360.0 + 0.5) * 360.0 / (lon1 - lon0)
        L.new(sep.outputs['X'], pu.inputs[0])
        pv = nt.nodes.new('ShaderNodeMath'); pv.operation = 'MULTIPLY_ADD'
        pv.inputs[1].default_value = 180.0 / (lat1 - lat0); pv.inputs[2].default_value = -(lat0 / 180.0 + 0.5) * 180.0 / (lat1 - lat0)
        L.new(sep.outputs['Y'], pv.inputs[0])
        puv = nt.nodes.new('ShaderNodeCombineXYZ'); L.new(pu.outputs[0], puv.inputs['X']); L.new(pv.outputs[0], puv.inputs['Y'])
        tp = _tex(nt, img(fn), puv.outputs[0]); tp.extension = 'EXTEND'
        inv_u = nt.nodes.new('ShaderNodeMath'); inv_u.operation = 'SUBTRACT'; inv_u.inputs[0].default_value = 1.0
        L.new(pu.outputs[0], inv_u.inputs[1])
        inv_v = nt.nodes.new('ShaderNodeMath'); inv_v.operation = 'SUBTRACT'; inv_v.inputs[0].default_value = 1.0
        L.new(pv.outputs[0], inv_v.inputs[1])
        mn = _smin(nt, _smin(nt, pu.outputs[0], inv_u.outputs[0]), _smin(nt, pv.outputs[0], inv_v.outputs[0]))
        mk = nt.nodes.new('ShaderNodeMapRange'); mk.interpolation_type = 'SMOOTHSTEP'
        mk.inputs['From Min'].default_value = 0.0; mk.inputs['From Max'].default_value = 0.06
        L.new(mn, mk.inputs['Value'])
        mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'
        L.new(mk.outputs['Result'], mx.inputs['Factor']); L.new(col, mx.inputs['A']); L.new(tp.outputs['Color'], mx.inputs['B'])
        col = mx.outputs['Result']
    hsv = nt.nodes.new('ShaderNodeHueSaturation'); hsv.inputs['Saturation'].default_value = sat
    hsv.inputs['Value'].default_value = 1.05
    L.new(col, hsv.inputs['Color'])
    base = hsv.outputs['Color']
    if detail:
        nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 900.0; nz.inputs['Detail'].default_value = 8.0
        L.new(nrm, nz.inputs['Vector'])
        mr = nt.nodes.new('ShaderNodeMapRange')
        mr.inputs['To Min'].default_value = 1 - detail; mr.inputs['To Max'].default_value = 1 + detail
        L.new(nz.outputs['Fac'], mr.inputs['Value'])
        mul = nt.nodes.new('ShaderNodeMix'); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'; mul.inputs['Factor'].default_value = 1.0
        comb = nt.nodes.new('ShaderNodeCombineXYZ')
        for s in 'XYZ':
            L.new(mr.outputs['Result'], comb.inputs[s])
        L.new(base, mul.inputs['A']); L.new(comb.outputs[0], mul.inputs['B'])
        base = mul.outputs['Result']
    L.new(base, p.inputs['Base Color'])
    # oceans: glossy, land: matte (blue minus red of the photo)
    sc = nt.nodes.new('ShaderNodeSeparateColor'); L.new(col, sc.inputs[0])
    sub = nt.nodes.new('ShaderNodeMath'); sub.operation = 'SUBTRACT'
    L.new(sc.outputs[2], sub.inputs[0]); L.new(sc.outputs[0], sub.inputs[1])
    rough = nt.nodes.new('ShaderNodeMapRange')
    rough.inputs['From Min'].default_value = 0.0; rough.inputs['From Max'].default_value = 0.06
    rough.inputs['To Min'].default_value = 0.88; rough.inputs['To Max'].default_value = 0.34
    L.new(sub.outputs[0], rough.inputs['Value']); L.new(rough.outputs['Result'], p.inputs['Roughness'])
    p.inputs['Specular IOR Level'].default_value = 0.45
    geo = nt.nodes.new('ShaderNodeNewGeometry')
    dot = _sun_dot(nt, geo.outputs['Normal'], sun_dir)
    # city lights on the night side (Black Marble)
    if night > 0:
        tn = _tex(nt, img('night_8k.jpg', True), uv)
        dark = nt.nodes.new('ShaderNodeMapRange')
        dark.inputs['From Min'].default_value = 0.04; dark.inputs['From Max'].default_value = -0.14
        L.new(dot.outputs['Value'], dark.inputs['Value'])
        bw = nt.nodes.new('ShaderNodeRGBToBW'); L.new(tn.outputs['Color'], bw.inputs[0])
        curve = nt.nodes.new('ShaderNodeMath'); curve.operation = 'POWER'; curve.inputs[1].default_value = 1.6
        L.new(bw.outputs[0], curve.inputs[0])
        st = nt.nodes.new('ShaderNodeMath'); st.operation = 'MULTIPLY'
        L.new(curve.outputs[0], st.inputs[0]); L.new(dark.outputs['Result'], st.inputs[1])
        st2 = nt.nodes.new('ShaderNodeMath'); st2.operation = 'MULTIPLY'; st2.inputs[1].default_value = night
        L.new(st.outputs[0], st2.inputs[0])
        p.inputs['Emission Color'].default_value = C('#FFB85C')
        L.new(st2.outputs[0], p.inputs['Emission Strength'])
    if haze:
        # in-scattered sky light over the surface at grazing angles (day side only)
        out = [n for n in nt.nodes if n.bl_idname == 'ShaderNodeOutputMaterial'][0]
        lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.5
        pw = nt.nodes.new('ShaderNodeMath'); pw.operation = 'POWER'; pw.inputs[1].default_value = 2.4
        L.new(lw.outputs['Facing'], pw.inputs[0])
        dm = nt.nodes.new('ShaderNodeMapRange')
        dm.inputs['From Min'].default_value = -0.12; dm.inputs['From Max'].default_value = 0.3
        L.new(dot.outputs['Value'], dm.inputs['Value'])
        hm = nt.nodes.new('ShaderNodeMath'); hm.operation = 'MULTIPLY'
        L.new(pw.outputs[0], hm.inputs[0]); L.new(dm.outputs['Result'], hm.inputs[1])
        hs = nt.nodes.new('ShaderNodeMath'); hs.operation = 'MULTIPLY'; hs.inputs[1].default_value = haze
        L.new(hm.outputs[0], hs.inputs[0])
        em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = C('#A9C8FF')
        L.new(hs.outputs[0], em.inputs['Strength'])
        add = nt.nodes.new('ShaderNodeAddShader')
        L.new(p.outputs[0], add.inputs[0]); L.new(em.outputs[0], add.inputs[1]); L.new(add.outputs[0], out.inputs['Surface'])
    e.data.materials.append(m)
    cl = None
    if clouds:
        cl = lib.sphere(r * (1.006 if cloud_tex else 1.0004), (0, 0, 0), None, seg[0], seg[1], name=name + 'Clouds')
        cl.parent = spin
        cm = bpy.data.materials.new(name + 'CloudMat'); cm.use_nodes = True
        try:
            cm.surface_render_method = 'BLENDED'
        except Exception:
            pass
        nt = cm.node_tree; L = nt.links
        nt.nodes.clear()
        out = nt.nodes.new('ShaderNodeOutputMaterial')
        tc = nt.nodes.new('ShaderNodeTexCoord')
        uv, nrm = _equirect(nt, tc.outputs['Object'])
        mul = nt.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'
        if cloud_tex:
            tcl = _tex(nt, img('clouds_2048.jpg', True), uv)
            bw = nt.nodes.new('ShaderNodeRGBToBW'); L.new(tcl.outputs['Color'], bw.inputs[0])
            L.new(bw.outputs[0], mul.inputs[0])
            # fine fractal breakup so the 2k map holds up close to the camera
            nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 140; nz.inputs['Detail'].default_value = 12
            nz.inputs['Roughness'].default_value = 0.62
            L.new(nrm, nz.inputs['Vector'])
            nzr = nt.nodes.new('ShaderNodeMapRange'); nzr.inputs['To Min'].default_value = 0.55; nzr.inputs['To Max'].default_value = 1.35
            L.new(nz.outputs['Fac'], nzr.inputs['Value']); L.new(nzr.outputs['Result'], mul.inputs[1])
            lo, hi = 0.14, 0.72
        else:
            nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = cloud_scale; nz.inputs['Detail'].default_value = 12
            nz.inputs['Roughness'].default_value = 0.6
            L.new(tc.outputs['Object'], nz.inputs['Vector'])
            nc = nt.nodes.new('ShaderNodeTexNoise'); nc.inputs['Scale'].default_value = cloud_scale / 9.0; nc.inputs['Detail'].default_value = 3
            L.new(tc.outputs['Object'], nc.inputs['Vector'])
            ncr = nt.nodes.new('ShaderNodeMapRange'); ncr.inputs['From Min'].default_value = 0.35; ncr.inputs['From Max'].default_value = 0.65
            ncr.inputs['To Min'].default_value = 0.55; ncr.inputs['To Max'].default_value = 1.25
            L.new(nc.outputs['Fac'], ncr.inputs['Value'])
            L.new(nz.outputs['Fac'], mul.inputs[0]); L.new(ncr.outputs['Result'], mul.inputs[1])
            lo, hi = 1.0 - cloud_cover, 1.0 - cloud_cover + 0.16
        a = nt.nodes.new('ShaderNodeMapRange')
        a.inputs['From Min'].default_value = lo; a.inputs['From Max'].default_value = hi
        L.new(mul.outputs[0], a.inputs['Value'])
        dif = nt.nodes.new('ShaderNodeBsdfDiffuse'); dif.inputs['Color'].default_value = C('#F4F6F8')
        tr = nt.nodes.new('ShaderNodeBsdfTransparent')
        mix = nt.nodes.new('ShaderNodeMixShader')
        L.new(a.outputs['Result'], mix.inputs['Fac']); L.new(tr.outputs[0], mix.inputs[1]); L.new(dif.outputs[0], mix.inputs[2])
        L.new(mix.outputs[0], out.inputs['Surface'])
        cl.data.materials.append(cm)
        cl.visible_shadow = False
    shells = atmosphere(r, sun_dir, center=loc, strength=atmo, top=atmo_top) if atmo else []
    for s in shells:
        s.parent = spin
    return e, cl, shells, spin


ATMO = []      # (centre socket, strength socket) of every atmosphere shell, for animated globes


def atmosphere(r, sun_dir, center=(0, 0, 0), strength=1.0, H=0.0045, top=None, color='#4F93FF', edge='#FF8A3D',
               forward=1.0, name='Atmo'):
    """One shell whose glow is computed per view ray: the ray's closest approach to the planet centre gives the
    altitude it grazes (exp(-h/H) for rays that miss the planet, the slant path for rays that hit it), so the limb
    is brightest just above the surface and fades smoothly upwards. Blue on the day side, warm at the terminator,
    brighter towards the sun. Needs the camera outside the shell (backfaces are culled)."""
    rr = r * (top or (1.0 + 7.0 * H))
    ob = lib.sphere(rr, (0, 0, 0), None, 256, 128, name=name)
    m = bpy.data.materials.new(name + 'Mat'); m.use_nodes = True
    try:
        m.surface_render_method = 'BLENDED'
    except Exception:
        m.blend_method = 'BLEND'
    m.use_backface_culling = True
    nt = m.node_tree; nt.nodes.clear(); L = nt.links
    def vm(op, a=None, b=None):
        n = nt.nodes.new('ShaderNodeVectorMath'); n.operation = op
        if a is not None:
            L.new(a, n.inputs[0]) if not isinstance(a, (tuple, Vector)) else setattr(n.inputs[0], 'default_value', a)
        if b is not None:
            L.new(b, n.inputs[1]) if not isinstance(b, (tuple, Vector)) else setattr(n.inputs[1], 'default_value', b)
        return n
    def fm(op, a=None, b=None, clamp=False):
        n = nt.nodes.new('ShaderNodeMath'); n.operation = op; n.use_clamp = clamp
        for i, x in enumerate((a, b)):
            if x is None:
                continue
            if isinstance(x, (int, float)):
                n.inputs[i].default_value = x
            else:
                L.new(x, n.inputs[i])
        return n.outputs[0]
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    geo = nt.nodes.new('ShaderNodeNewGeometry')
    v = vm('SUBTRACT', geo.outputs['Position'], Vector(center))
    csock = v.inputs[1]
    d = vm('DOT_PRODUCT', v.outputs[0], geo.outputs['Incoming'])
    sc = nt.nodes.new('ShaderNodeVectorMath'); sc.operation = 'SCALE'
    L.new(geo.outputs['Incoming'], sc.inputs[0]); L.new(d.outputs['Value'], sc.inputs['Scale'])
    w = vm('SUBTRACT', v.outputs[0], sc.outputs[0])
    b = vm('LENGTH', w.outputs[0])
    x = fm('DIVIDE', b.outputs['Value'], r)
    # rays that miss the planet: exp(-(b - R) / H)
    hm = fm('MULTIPLY', fm('SUBTRACT', x, 1.0), -1.0 / H)
    g_miss = fm('EXPONENT', fm('MINIMUM', hm, 0.0))
    # rays that hit it: slant path through the bottom of the atmosphere, relative to the grazing path
    k = math.sqrt(H / (2 * math.pi))
    cosz = fm('SQRT', fm('MAXIMUM', fm('SUBTRACT', 1.0, fm('MULTIPLY', x, x)), 1e-5))
    g_hit = fm('MINIMUM', fm('DIVIDE', k, cosz), 1.0)
    miss = fm('GREATER_THAN', x, 1.0)
    g = fm('ADD', fm('MULTIPLY', miss, g_miss), fm('MULTIPLY', fm('SUBTRACT', 1.0, miss), g_hit))
    # light at the grazing point
    nq = vm('NORMALIZE', w.outputs[0])
    dot = nt.nodes.new('ShaderNodeVectorMath'); dot.operation = 'DOT_PRODUCT'
    L.new(nq.outputs[0], dot.inputs[0]); dot.inputs[1].default_value = Vector(sun_dir).normalized()
    SUN_SOCKETS.append(dot.inputs[1])
    day = nt.nodes.new('ShaderNodeMapRange')
    day.inputs['From Min'].default_value = -0.18; day.inputs['From Max'].default_value = 0.35
    L.new(dot.outputs['Value'], day.inputs['Value'])
    term = nt.nodes.new('ShaderNodeMapRange'); term.interpolation_type = 'SMOOTHSTEP'
    term.inputs['From Min'].default_value = 0.0; term.inputs['From Max'].default_value = 0.26
    term.inputs['To Min'].default_value = 1.0; term.inputs['To Max'].default_value = 0.0
    L.new(fm('ABSOLUTE', dot.outputs['Value']), term.inputs['Value'])
    vd = nt.nodes.new('ShaderNodeVectorMath'); vd.operation = 'DOT_PRODUCT'
    L.new(geo.outputs['Incoming'], vd.inputs[0]); vd.inputs[1].default_value = Vector(sun_dir).normalized()
    SUN_SOCKETS.append(vd.inputs[1])
    fw = fm('POWER', fm('MULTIPLY', vd.outputs['Value'], -1.0, clamp=True), 10.0)
    lvl_miss = fm('ADD', fm('MAXIMUM', day.outputs['Result'], fm('MULTIPLY', term.outputs['Result'], 0.55)),
                  fm('MULTIPLY', fm('MULTIPLY', fw, 3.0 * forward), fm('ADD', day.outputs['Result'], term.outputs['Result'])))
    # over the disc only the sunlit air scatters (no warm band smeared over the night side)
    lvl_hit = fm('ADD', day.outputs['Result'], fm('MULTIPLY', fm('MULTIPLY', fw, 1.5 * forward), day.outputs['Result']))
    lvl = fm('ADD', fm('MULTIPLY', miss, lvl_miss), fm('MULTIPLY', fm('SUBTRACT', 1.0, miss), lvl_hit))
    cf = fm('MAXIMUM', term.outputs['Result'], fm('MULTIPLY', fw, 0.6, clamp=True))
    colmix = nt.nodes.new('ShaderNodeMix'); colmix.data_type = 'RGBA'
    L.new(cf, colmix.inputs['Factor'])
    colmix.inputs['A'].default_value = C(color); colmix.inputs['B'].default_value = C(edge)
    st = nt.nodes.new('ShaderNodeValue'); st.outputs[0].default_value = 2.6 * strength
    em = nt.nodes.new('ShaderNodeEmission')
    L.new(colmix.outputs['Result'], em.inputs['Color'])
    L.new(fm('MULTIPLY', fm('MULTIPLY', g, lvl), st.outputs[0]), em.inputs['Strength'])
    tr = nt.nodes.new('ShaderNodeBsdfTransparent')
    add = nt.nodes.new('ShaderNodeAddShader')
    L.new(tr.outputs[0], add.inputs[0]); L.new(em.outputs[0], add.inputs[1])
    L.new(add.outputs[0], out.inputs['Surface'])
    ob.data.materials.append(m)
    ob.visible_shadow = False
    ATMO.append((csock, st.outputs[0]))
    return [ob]


def animate_sun(keys, lamp=None, disk=None, disk_dist=None, origin=(0, 0, 0)):
    """keys: [(t_s, direction_to_sun)] -> keys every shader sun socket, the sun lamp and the sun disk position."""
    for t, d in keys:
        f = lib.sec2f(t)
        d = Vector(d).normalized()
        for s in SUN_SOCKETS:
            s.default_value = d
            s.keyframe_insert('default_value', frame=f)
        if lamp is not None:
            lamp.rotation_mode = 'QUATERNION'
            lamp.rotation_quaternion = (-d).to_track_quat('-Z', 'Y')
            lamp.keyframe_insert('rotation_quaternion', frame=f)
        if disk is not None:
            for ob in disk:
                ob.location = Vector(origin) + d * disk_dist
                ob.keyframe_insert('location', frame=f)


def earthshine(dir_to_earth, energy=0.5, color='#9DB8E8'):
    s = sun_light(dir_to_earth, energy, color, 30.0, name='EarthShine')
    s.data.use_shadow = False
    return s


def sky_world(top='#2F5FA8', horizon='#B9D4F0', star_strength=1.0, density=1.0):
    """Daytime sky gradient (by view z) mixed with the star field; returns the Value node whose output (1=day, 0=space)
    can be keyed: v.outputs[0].keyframe_insert('default_value', frame=f)."""
    w = stars(density, star_strength)
    nt = w.node_tree; L = nt.links
    bg = [n for n in nt.nodes if n.bl_idname == 'ShaderNodeBackground'][0]
    star_col = bg.inputs['Color'].links[0].from_socket
    tc = nt.nodes.new('ShaderNodeTexCoord')
    nrm = nt.nodes.new('ShaderNodeVectorMath'); nrm.operation = 'NORMALIZE'; L.new(tc.outputs['Generated'], nrm.inputs[0])
    sep = nt.nodes.new('ShaderNodeSeparateXYZ'); L.new(nrm.outputs[0], sep.inputs[0])
    ramp = nt.nodes.new('ShaderNodeValToRGB'); cr = ramp.color_ramp
    cr.elements[0].position = 0.0; cr.elements[0].color = C(horizon)
    cr.elements[1].position = 0.55; cr.elements[1].color = C(top)
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = -0.05; mr.inputs['From Max'].default_value = 1.0
    L.new(sep.outputs['Z'], mr.inputs['Value']); L.new(mr.outputs['Result'], ramp.inputs['Fac'])
    v = nt.nodes.new('ShaderNodeValue'); v.outputs[0].default_value = 1.0
    mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'
    L.new(v.outputs[0], mix.inputs['Factor']); L.new(star_col, mix.inputs['A']); L.new(ramp.outputs['Color'], mix.inputs['B'])
    L.new(mix.outputs['Result'], bg.inputs['Color'])
    return w, v


def moon_body(r, loc, name='MoonBody'):
    """The Moon as seen in the sky (LRO colour map)."""
    ob = lib.sphere(r, loc, None, 128, 64, name=name)
    m = bpy.data.materials.new(name + 'Mat'); m.use_nodes = True
    nt = m.node_tree; p = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord')
    uv, nrm = _equirect(nt, tc.outputs['Object'])
    t = _tex(nt, img('moon_color_4k.jpg'), uv)
    nt.links.new(t.outputs['Color'], p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = 0.95
    p.inputs['Specular IOR Level'].default_value = 0.1
    ob.data.materials.append(m)
    return ob


def sun_disk(direction, dist=900.0, r=6.0, strength=60.0, glow=True):
    d = Vector(direction).normalized()
    m, em = lib.emission_mat('SunDisk', '#FFF6E8', strength)
    s = lib.sphere(r, d * dist, m, 48, 24, name='SunDisk')
    s.visible_shadow = False
    if glow:
        gm, gem = lib.emission_mat('SunHalo', '#FFE2B0', 1.0)
        try:
            gm.surface_render_method = 'BLENDED'
        except Exception:
            pass
        nt = gm.node_tree; L = nt.links
        lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.5
        pw = nt.nodes.new('ShaderNodeMath'); pw.operation = 'POWER'; pw.inputs[1].default_value = 4.0
        inv = nt.nodes.new('ShaderNodeMath'); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0
        L.new(lw.outputs['Facing'], inv.inputs[1]); L.new(inv.outputs[0], pw.inputs[0])
        sm = nt.nodes.new('ShaderNodeMath'); sm.operation = 'MULTIPLY'; sm.inputs[1].default_value = 6.0
        L.new(pw.outputs[0], sm.inputs[0]); L.new(sm.outputs[0], gem.inputs['Strength'])
        out = [n for n in nt.nodes if n.bl_idname == 'ShaderNodeOutputMaterial'][0]
        tr = nt.nodes.new('ShaderNodeBsdfTransparent'); add = nt.nodes.new('ShaderNodeAddShader')
        L.new(tr.outputs[0], add.inputs[0]); L.new(gem.outputs[0], add.inputs[1]); L.new(add.outputs[0], out.inputs['Surface'])
        h = lib.sphere(r * 5.0, d * dist, gm, 48, 24, name='SunGlow')
        h.visible_shadow = False
        return s, h
    return s, None


# ----------------------------------------------------------------------------- vehicles
def _mats():
    return dict(
        white=lib.mat('HullWhite', '#ECEDEF', rough=0.32, spec=0.6),
        grey=lib.mat('HullGrey', '#9DA3AA', rough=0.4, metal=0.6),
        dark=lib.mat('HullDark', '#1B1E23', rough=0.35),
        glass=lib.mat('CockpitGlass', '#0B1724', rough=0.05, spec=1.0, coat=1.0),
        amber=lib.mat('HullAmber', '#E9A23B', rough=0.35),
        win=lib.mat('WinLit', '#2A2118', rough=0.3, emit='#FFD49A', emit_strength=4.0),
        engine=lib.emission_mat('EngineGlow', '#9CC8FF', 18.0)[0],
        gold=lib.mat('GoldFoil', '#C99A3E', rough=0.32, metal=0.95, var=0.25, var_scale=9.0, bump=0.35, bump_scale=30.0),
        panel=lib.mat('SolarPanel', '#8B5A2C', rough=0.28, metal=0.55, var=0.12, var_scale=6.0),
        visor=lib.mat('Visor', '#C8962F', rough=0.08, metal=1.0, coat=1.0),
        suit=lib.mat('Suit', '#ECEBE6', rough=0.75, var=0.08, bump=0.15, bump_scale=14.0),
    )


def spaceplane(name='Spaceplane'):
    """Passenger spaceplane ~13 m long, forward = +X, lit cabin windows. Root at the fuselage centre."""
    M = _mats()
    root = lib.empty(name)
    parts = []
    parts.append(lib.cyl(0.62, 7.0, (0, 0, 0), M['white'], rot=(0, math.pi / 2, 0), verts=48, name=name + 'Body'))
    parts.append(lib.cyl(0.62, 2.4, (4.7, 0, 0), M['white'], rot=(0, math.pi / 2, 0), verts=48, r2=0.06, name=name + 'Nose'))
    parts.append(lib.cyl(0.66, 0.5, (-3.75, 0, 0), M['dark'], rot=(0, math.pi / 2, 0), verts=48, r2=0.6, name=name + 'Aft'))
    # cockpit glass
    parts.append(lib.sphere(0.5, (4.2, 0, 0.3), M['glass'], 32, 16, scale=(1.6, 0.9, 0.45), name=name + 'Cockpit'))
    # wings (delta) and fin
    for s in (1, -1):
        pts = [(1.6, 0.4 * s), (-2.9, 3.9 * s), (-3.6, 3.9 * s), (-3.3, 0.4 * s)]
        if s < 0:
            pts = pts[::-1]
        w = lib.poly_prism(pts, 0.16, (0, 0, -0.38), M['white'], name=name + 'Wing', bevel=0.03)
        parts.append(w)
        tip = lib.box((0.8, 0.1, 0.5), (-3.25, 3.88 * s, -0.12), M['amber'], bevel=0.03, name=name + 'Winglet')
        parts.append(tip)
    fin = lib.poly_prism([(-3.7, 0), (-2.4, 0), (-3.1, 1.9), (-3.75, 1.9)], 0.14, (0, 0.07, 0.42), M['amber'],
                         rot=(math.pi / 2, 0, 0), name=name + 'Fin', bevel=0.03)
    parts.append(fin)
    # cabin windows (both sides)
    for s in (1, -1):
        for i in range(11):
            x = 2.6 - i * 0.5
            parts.append(lib.box((0.2, 0.06, 0.26), (x, 0.6 * s, 0.14), M['win'], bevel=0.04, name=name + 'Win'))
    # engines
    for y, z in ((0.0, 0.22), (0.3, -0.2), (-0.3, -0.2)):
        parts.append(lib.cyl(0.19, 0.3, (-4.1, y, z), M['grey'], rot=(0, math.pi / 2, 0), verts=24, r2=0.15, name=name + 'Bell'))
        g = lib.cyl(0.14, 0.04, (-4.27, y, z), M['engine'], rot=(0, math.pi / 2, 0), verts=24, name=name + 'Glow')
        g.visible_shadow = False
        parts.append(g)
    for ob in parts:
        ob.parent = root
    return root


def station(name='Station'):
    """ISS-like station ~70 m wide: truss, bronze solar wings, white pressurised modules, radiators. Root at centre."""
    M = _mats()
    root = lib.empty(name)
    parts = [lib.box((44, 1.1, 1.1), (0, 0, 0), M['grey'], bevel=0.05, name=name + 'Truss')]
    for x in (-19, -13, 13, 19):
        for s in (1, -1):
            arm = lib.box((0.25, 4.5, 0.25), (x, 2.4 * s, 0), M['grey'], bevel=0.02, name=name + 'Mast')
            wing = lib.box((3.6, 16.0, 0.06), (x, 11.0 * s, 0), M['panel'], bevel=0.0, name=name + 'Array')
            parts += [arm, wing]
            for k in range(1, 8):   # panel seams
                parts.append(lib.box((3.62, 0.08, 0.07), (x, (3.0 + k * 2.0) * s, 0), M['dark'], bevel=0, name=name + 'Seam'))
    for y, ln in ((0, 18), ):
        parts.append(lib.cyl(2.1, ln, (0, 0, -2.4), M['white'], rot=(math.pi / 2, 0, 0), verts=48, bevel=0.1, name=name + 'Core'))
    parts.append(lib.cyl(2.1, 7, (4.0, -6.5, -2.4), M['white'], rot=(0, math.pi / 2, 0), verts=48, bevel=0.1, name=name + 'Lab'))
    parts.append(lib.cyl(2.1, 7, (-4.0, 6.5, -2.4), M['white'], rot=(0, math.pi / 2, 0), verts=48, bevel=0.1, name=name + 'Node'))
    for s in (1, -1):
        parts.append(lib.box((7.0, 0.08, 3.2), (6.5 * s, 0, 3.0), M['white'], bevel=0.02, name=name + 'Radiator'))
    for ob in parts:
        ob.parent = root
    return root


def rocket(h=46.0, r=1.9, name='Rocket'):
    """Two-stage crewed rocket standing on z=0, white with a black interstage, crew capsule on top. Root at the base."""
    M = _mats()
    root = lib.empty(name)
    parts = [lib.cyl(r, h * 0.62, (0, 0, h * 0.31), M['white'], verts=64, name=name + 'S1')]
    parts.append(lib.cyl(r * 1.002, h * 0.05, (0, 0, h * 0.645), M['dark'], verts=64, name=name + 'Inter'))
    parts.append(lib.cyl(r, h * 0.2, (0, 0, h * 0.77), M['white'], verts=64, name=name + 'S2'))
    parts.append(lib.cyl(r, h * 0.06, (0, 0, h * 0.9), M['dark'], verts=64, r2=r * 0.7, name=name + 'Adapter'))
    parts.append(lib.cyl(r * 0.7, h * 0.06, (0, 0, h * 0.96), M['white'], verts=64, r2=r * 0.25, name=name + 'Capsule'))
    parts.append(lib.cyl(r * 0.08, h * 0.06, (0, 0, h * 1.02), M['grey'], verts=16, r2=0.02, name=name + 'Tower'))
    # amber band (the operator's livery)
    parts.append(lib.cyl(r * 1.004, h * 0.025, (0, 0, h * 0.55), M['amber'], verts=64, name=name + 'Band'))
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        fin = lib.poly_prism([(0, 0), (2.4, 0), (2.4, 1.2), (0, 4.6)], 0.22, (0, 0, 0), M['dark'],
                             rot=(math.pi / 2, 0, a), name=name + 'Fin')
        fin.location = (math.cos(a) * r * 0.95, math.sin(a) * r * 0.95, 0.4)
        parts.append(fin)
    parts.append(lib.cyl(r * 0.85, 1.4, (0, 0, -0.4), M['grey'], verts=48, r2=r * 0.6, name=name + 'Engines'))
    for ob in parts:
        ob.parent = root
    return root


def plume(length=26.0, r=2.2, name='Plume'):
    """Exhaust: bright core cone + soft outer cone, pointing down from z=0 (parent to the rocket base)."""
    m, em = lib.emission_mat(name + 'Core', '#FFE6B8', 40.0)
    core = lib.cyl(r * 0.55, length * 0.45, (0, 0, -length * 0.225 - 0.8), m, verts=32, r2=r * 0.45, name=name + 'Core')
    om = bpy.data.materials.new(name + 'Outer'); om.use_nodes = True
    try:
        om.surface_render_method = 'BLENDED'
    except Exception:
        pass
    nt = om.node_tree; nt.nodes.clear(); L = nt.links
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.6
    tc = nt.nodes.new('ShaderNodeTexCoord'); sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    L.new(tc.outputs['Generated'], sep.inputs[0])
    mul = nt.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'
    L.new(lw.outputs['Facing'], mul.inputs[0])
    inv = nt.nodes.new('ShaderNodeMath'); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0
    L.new(sep.outputs['Z'], inv.inputs[1])   # fade towards the tail (Generated z: 0 at the tail end)
    mul2 = nt.nodes.new('ShaderNodeMath'); mul2.operation = 'MULTIPLY'
    L.new(mul.outputs[0], mul2.inputs[0]); L.new(sep.outputs['Z'], mul2.inputs[1])
    sm = nt.nodes.new('ShaderNodeMath'); sm.operation = 'MULTIPLY'; sm.inputs[1].default_value = 14.0
    L.new(mul2.outputs[0], sm.inputs[0])
    e = nt.nodes.new('ShaderNodeEmission'); e.inputs['Color'].default_value = C('#FF9A3C')
    L.new(sm.outputs[0], e.inputs['Strength'])
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); add = nt.nodes.new('ShaderNodeAddShader')
    L.new(tr.outputs[0], add.inputs[0]); L.new(e.outputs[0], add.inputs[1]); L.new(add.outputs[0], out.inputs['Surface'])
    outer = lib.cyl(r, length, (0, 0, -length / 2 - 0.6), om, verts=32, r2=r * 0.7, name=name + 'Outer')
    for o in (core, outer):
        o.visible_shadow = False
    root = lib.empty(name)
    core.parent = root; outer.parent = root
    return root, em


def astronaut(suit='#ECEBE6', name='Astro', pose='stand'):
    """Bulky suit figure ~1.85 m: torso, backpack, helmet with a gold visor, limbs. Root at the feet, faces -Y."""
    M = _mats()
    sm = lib.mat('Suit' + suit, suit, rough=0.75, var=0.08, bump=0.15, bump_scale=14.0)
    root = lib.empty(name)
    P = []
    P.append(lib.box((0.56, 0.36, 0.62), (0, 0, 1.18), sm, bevel=0.12, name=name + 'Torso'))
    P.append(lib.box((0.5, 0.3, 0.62), (0, 0.32, 1.2), M['white'], bevel=0.06, name=name + 'Pack'))
    P.append(lib.sphere(0.21, (0, -0.02, 1.68), sm, 32, 16, name=name + 'Helmet'))
    P.append(lib.sphere(0.2, (0, -0.07, 1.68), M['visor'], 32, 16, scale=(0.92, 0.8, 0.82), name=name + 'Visor'))
    P.append(lib.box((0.44, 0.3, 0.28), (0, 0, 0.82), sm, bevel=0.1, name=name + 'Hips'))
    for s in (1, -1):
        P.append(lib.cyl(0.11, 0.78, (0.14 * s, 0, 0.42), sm, verts=16, bevel=0.03, name=name + 'Leg'))
        P.append(lib.box((0.17, 0.3, 0.12), (0.14 * s, -0.05, 0.06), M['grey'], bevel=0.04, name=name + 'Boot'))
        if pose == 'wave' and s > 0:
            arm = lib.cyl(0.09, 0.6, (0.42, 0, 1.55), sm, verts=16, rot=(0, -0.35, 0), bevel=0.03, name=name + 'Arm')
        else:
            arm = lib.cyl(0.09, 0.62, (0.36 * s, -0.02, 1.08), sm, verts=16, rot=(0, 0.12 * s, 0), bevel=0.03, name=name + 'Arm')
        P.append(arm)
        P.append(lib.sphere(0.08, (arm.location.x + (0.02 * s if pose != 'wave' or s < 0 else 0.1), arm.location.y,
                                   arm.location.z + (-0.33 if pose != 'wave' or s < 0 else 0.3)), M['white'], 12, 8, name=name + 'Glove'))
    for o in P:
        o.parent = root
    return root


# ----------------------------------------------------------------------------- terrain (numpy heightfield)
def _noise2(n, octaves, seed, base=4):
    rng = np.random.default_rng(seed)
    h = np.zeros((n, n))
    amp, cells = 1.0, base
    for _ in range(octaves):
        g = rng.standard_normal((cells + 1, cells + 1))
        xs = np.linspace(0, cells, n)
        i0 = np.floor(xs).astype(int).clip(0, cells - 1); f = xs - i0
        f = f * f * (3 - 2 * f)
        a = g[i0][:, i0]; b = g[i0][:, i0 + 1]; c = g[i0 + 1][:, i0]; d = g[i0 + 1][:, i0 + 1]
        fx = f[None, :]; fy = f[:, None]
        h += amp * ((a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy)
        amp *= 0.5; cells *= 2
    return h


def terrain(size=240.0, n=320, height=1.0, octaves=6, craters=0, crater_r=(1.5, 14.0), seed=1, curve=0.0,
            flat_center=None, mat_=None, name='Ground', ramp=None, base=4, center=(0.0, 0.0)):
    """Square heightfield centred at the origin. craters: count of bowl craters with raised rims.
    curve: planet curvature drop (z -= curve * r^2) so the horizon bends a little. flat_center=(x, y, radius) flattens a pad."""
    h = _noise2(n, octaves, seed, base) * height
    xs = np.linspace(-size / 2, size / 2, n)
    X, Y = np.meshgrid(xs + center[0], xs + center[1])
    if ramp:
        r0, r1, b0 = ramp
        d = np.sqrt(X ** 2 + Y ** 2)
        w = np.clip((d - r0) / (r1 - r0), 0, 1)
        h = h * (b0 + (1 - b0) * w * w * (3 - 2 * w))
    rng = np.random.default_rng(seed + 7)
    for _ in range(craters):
        cx, cy = rng.uniform(-size / 2, size / 2, 2)
        r = crater_r[0] * (crater_r[1] / crater_r[0]) ** (rng.random() ** 2.2)
        d = np.sqrt((X - cx) ** 2 + (Y - cy) ** 2) / r
        depth = 0.22 * r
        bowl = np.where(d < 1, -depth * (1 - d ** 2), 0.0)
        rim = 0.09 * r * np.exp(-((d - 1.0) / 0.28) ** 2)
        h += bowl + rim
    if flat_center:
        fx, fy, fr = flat_center
        d = np.sqrt((X - fx) ** 2 + (Y - fy) ** 2)
        w = np.clip((d - fr) / (fr * 0.8), 0, 1)
        w = w * w * (3 - 2 * w)
        h = h * w
    if curve:
        h -= curve * (X ** 2 + Y ** 2)
    verts = np.stack([X.ravel(), Y.ravel(), h.ravel()], axis=1)
    ys = xs + center[1]
    xs = xs + center[0]
    idx = np.arange(n * n).reshape(n, n)
    faces = np.stack([idx[:-1, :-1].ravel(), idx[:-1, 1:].ravel(), idx[1:, 1:].ravel(), idx[1:, :-1].ravel()], axis=1)
    me = bpy.data.meshes.new(name)
    me.vertices.add(n * n)
    me.vertices.foreach_set('co', verts.astype(np.float32).ravel())
    me.loops.add(faces.size)
    me.loops.foreach_set('vertex_index', faces.astype(np.int32).ravel())
    me.polygons.add(len(faces))
    me.polygons.foreach_set('loop_start', (np.arange(len(faces)) * 4).astype(np.int32))
    me.polygons.foreach_set('loop_total', np.full(len(faces), 4, dtype=np.int32))
    me.update(calc_edges=True)
    me.validate()
    me.polygons.foreach_set('use_smooth', [True] * len(me.polygons))
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    if mat_ is not None:
        me.materials.append(mat_)
    return ob, (xs, h, ys)


def height_at(field, x, y):
    xs, h, ys = field
    i = int(np.clip(np.searchsorted(ys, y), 0, len(ys) - 1))
    j = int(np.clip(np.searchsorted(xs, x), 0, len(xs) - 1))
    return float(h[i, j])


def ground_mat(name, base, dark, light, rough=0.95, scale=0.08, bump=0.6):
    """Regolith / dust: two-scale colour variation from noise + fine bump (object space)."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; p = nt.nodes['Principled BSDF']; L = nt.links
    tc = nt.nodes.new('ShaderNodeTexCoord')
    n1 = nt.nodes.new('ShaderNodeTexNoise'); n1.inputs['Scale'].default_value = scale; n1.inputs['Detail'].default_value = 8
    n2 = nt.nodes.new('ShaderNodeTexNoise'); n2.inputs['Scale'].default_value = scale * 18; n2.inputs['Detail'].default_value = 10
    L.new(tc.outputs['Object'], n1.inputs['Vector']); L.new(tc.outputs['Object'], n2.inputs['Vector'])
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    cr = ramp.color_ramp
    cr.elements[0].position = 0.32; cr.elements[0].color = C(dark)
    cr.elements[1].position = 0.7; cr.elements[1].color = C(light)
    e = cr.elements.new(0.5); e.color = C(base)
    L.new(n1.outputs['Fac'], ramp.inputs['Fac'])
    mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'; mix.blend_type = 'MULTIPLY'
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['To Min'].default_value = 0.82; mr.inputs['To Max'].default_value = 1.12
    L.new(n2.outputs['Fac'], mr.inputs['Value'])
    comb = nt.nodes.new('ShaderNodeCombineXYZ')
    for s in 'XYZ':
        L.new(mr.outputs['Result'], comb.inputs[s])
    mix.inputs['Factor'].default_value = 1.0
    L.new(ramp.outputs['Color'], mix.inputs['A']); L.new(comb.outputs[0], mix.inputs['B'])
    L.new(mix.outputs['Result'], p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = rough
    p.inputs['Specular IOR Level'].default_value = 0.2
    if bump:
        n3 = nt.nodes.new('ShaderNodeTexNoise'); n3.inputs['Scale'].default_value = 6.0; n3.inputs['Detail'].default_value = 12
        L.new(tc.outputs['Object'], n3.inputs['Vector'])
        b = nt.nodes.new('ShaderNodeBump'); b.inputs['Strength'].default_value = bump; b.inputs['Distance'].default_value = 0.05
        L.new(n3.outputs['Fac'], b.inputs['Height']); L.new(b.outputs['Normal'], p.inputs['Normal'])
    return m


def rocks(field, count, area, rmin, rmax, mat_, seed=3, avoid=None, name='Rock', center=(0.0, 0.0)):
    """Scattered faceted rocks (distorted icospheres) sitting on the heightfield."""
    rng = random.Random(seed)
    out = []
    for i in range(count):
        x = center[0] + rng.uniform(-area, area); y = center[1] + rng.uniform(-area, area)
        if avoid and any((x - ax) ** 2 + (y - ay) ** 2 < ar ** 2 for ax, ay, ar in avoid):
            continue
        r = rmin * (rmax / rmin) ** (rng.random() ** 2.5)
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=2, radius=r)
        for v in bm.verts:
            v.co *= rng.uniform(0.75, 1.2)
            v.co.z *= 0.6
        z = height_at(field, x, y)
        ob = lib.mesh_from_bm(bm, f'{name}{i}', mat_, (x, y, z), (rng.random(), rng.random(), rng.random() * 6), smooth=False)
        out.append(ob)
    return out


# ----------------------------------------------------------------------------- debris
def debris_shell(n_rings=60, per_ring=70, r_min=R * 1.04, r_max=R * 1.3, size=0.35, seed=5, spin_deg=(10, 26), dur_f=600,
                 name='Debris'):
    """Thousands of small fragments on many inclined orbits (vertex instancing, each ring rotates on its own axis)."""
    rng = random.Random(seed)
    frag_m = lib.mat('DebrisMat', '#C9CCD1', rough=0.5, metal=0.6, emit='#D7E2F2', emit_strength=0.6)
    sat_m = lib.mat('SatMat', '#E6E2D8', rough=0.4, metal=0.3, emit='#FFE9C8', emit_strength=0.8)
    protos = []
    for k, (m, s) in enumerate(((frag_m, size), (frag_m, size * 0.55), (sat_m, size * 1.6))):
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=1, radius=s)
        for v in bm.verts:
            v.co *= rng.uniform(0.6, 1.3)
        pr = lib.mesh_from_bm(bm, f'{name}Proto{k}', m, (0, 0, -9999), smooth=False)
        pr.hide_render = False
        protos.append(pr)
    rings = []
    for i in range(n_rings):
        rr = rng.uniform(r_min, r_max) if rng.random() < 0.75 else rng.uniform(R * 1.05, R * 1.12)
        bm = bmesh.new()
        for j in range(per_ring):
            a = rng.uniform(0, 2 * math.pi)
            jr = rr * rng.uniform(0.995, 1.005)
            bm.verts.new((jr * math.cos(a), jr * math.sin(a), rng.uniform(-0.4, 0.4)))
        holder = lib.mesh_from_bm(bm, f'{name}Ring{i}', None, (0, 0, 0),
                                  (rng.uniform(-1.4, 1.4), rng.uniform(-1.4, 1.4), rng.uniform(0, 6.28)), smooth=False)
        holder.instance_type = 'VERTS'
        child = protos[i % 3 if i % 9 == 0 else i % 2].copy()
        child.data = protos[i % 3 if i % 9 == 0 else i % 2].data
        bpy.context.scene.collection.objects.link(child)
        child.location = (0, 0, 0)
        child.parent = holder
        # spin around the ring's own axis
        spin = math.radians(rng.uniform(*spin_deg)) * (1 if rng.random() < 0.8 else -1)
        e0 = holder.rotation_euler.copy()
        holder.rotation_mode = 'QUATERNION'
        q0 = e0.to_quaternion()
        axis = q0 @ Vector((0, 0, 1))
        from mathutils import Quaternion
        for f, ang in ((1, 0.0), (dur_f, spin * dur_f / 60.0)):
            holder.rotation_quaternion = Quaternion(axis, ang) @ q0
            holder.keyframe_insert('rotation_quaternion', frame=f)
        for fc in holder.animation_data.action.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = 'LINEAR'
        rings.append(holder)
    for pr in protos:
        pr.hide_render = True
        pr.hide_viewport = True
    return rings


def face_point(spin, lon, lat, view_dir):
    """Rotate a globe so the point (lon, lat) looks along view_dir (from the globe centre towards the viewer)."""
    spin.rotation_mode = 'QUATERNION'
    q = ll2v(lon, lat, 1.0).normalized().rotation_difference(Vector(view_dir).normalized())
    spin.rotation_quaternion = q
    return q


def space_shadows(lamp, scale=0.5, pool='1024'):
    """Huge depth ranges (an Earth thousands of units away) overflow Eevee's shadow pool: coarser sun shadows, bigger pool."""
    for ob, attr, val in ((lamp.data, 'shadow_resolution_scale', scale), (bpy.context.scene.eevee, 'shadow_pool_size', pool)):
        try:
            setattr(ob, attr, val)
        except Exception:
            pass
