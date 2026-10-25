"""Shared helpers for the 'Mir bez granic' Blender scenes (Blender 4.5 LTS, Eevee Next).

Everything is built procedurally with bmesh (no bpy.ops), so scripts run headless with --factory-startup.
"""
import bpy, bmesh, math, random, os
from mathutils import Vector, Matrix, Euler

PROJ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA = os.path.join(PROJ, 'data')
FPS = 60
FOG_BOX = (900.0, 900.0, 120.0)

# ----------------------------------------------------------------------------- palette (dusk / ember)
def hex2lin(h, a=1.0):
    h = h.lstrip('#')
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return (lin[0], lin[1], lin[2], a)

PAL = dict(
    charcoal='#2A2622', beige='#EDE3D4', terracotta='#E08A55', orange='#FF8A2A', sage='#A9B79A',
    sand='#E3D6C1', rust='#B4532A', ink='#1A1714', paper='#D9CBB2', olive='#4E5236', maroon='#5A1E1E',
)

def C(name_or_hex, a=1.0):
    return hex2lin(PAL.get(name_or_hex, name_or_hex), a)

# ----------------------------------------------------------------------------- scene setup
def reset():
    for coll in (bpy.data.objects, bpy.data.meshes, bpy.data.materials, bpy.data.lights, bpy.data.cameras,
                 bpy.data.curves, bpy.data.images, bpy.data.node_groups, bpy.data.worlds, bpy.data.textures):
        for b in list(coll):
            try:
                coll.remove(b)
            except Exception:
                pass
    sc = bpy.context.scene
    for c in list(sc.collection.children):
        sc.collection.children.unlink(c)
    return sc

def setup_render(dur_s, samples=48, scale=1.0, motion_blur=True, fps=FPS, view='AgX', look='AgX - Medium High Contrast',
                 exposure=0.0, volumetrics=True, vol_tile='4', vol_end=120.0):
    sc = bpy.context.scene
    r = sc.render
    try:
        r.engine = 'BLENDER_EEVEE_NEXT'
    except TypeError:
        r.engine = 'BLENDER_EEVEE'
    r.resolution_x, r.resolution_y = 1080, 1920
    r.resolution_percentage = int(round(scale * 100))
    r.fps = fps
    sc.frame_start = 1
    sc.frame_end = max(1, int(round(dur_s * fps)))
    e = sc.eevee
    e.taa_render_samples = samples
    for k, v in dict(use_raytracing=True, use_shadows=True, shadow_ray_count=2, shadow_step_count=8,
                     use_volumetric_shadows=True, volumetric_tile_size=vol_tile, volumetric_samples=96,
                     volumetric_start=0.1, volumetric_end=vol_end, volumetric_shadow_samples=24,
                     use_gtao=True, gtao_distance=0.6, fast_gi_method='GLOBAL_ILLUMINATION').items():
        try:
            setattr(e, k, v)
        except Exception:
            pass
    try:
        e.ray_tracing_options.resolution_scale = '2'
        e.ray_tracing_options.use_denoise = True
    except Exception:
        pass
    try:
        r.use_motion_blur = motion_blur
        r.motion_blur_shutter = 0.45
    except Exception:
        pass
    r.film_transparent = False
    r.filter_size = 1.2
    vs = sc.view_settings
    try:
        vs.view_transform = view
        vs.look = look
    except Exception:
        try:
            vs.look = 'None'
        except Exception:
            pass
    vs.exposure = exposure
    r.image_settings.file_format = 'JPEG'
    r.image_settings.quality = 93
    r.use_overwrite = False
    r.use_placeholder = True
    return sc

def bloom(strength=0.35, threshold=1.0, size=7, glare='BLOOM'):
    sc = bpy.context.scene
    sc.use_nodes = True
    nt = sc.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    rl = nt.nodes.new('CompositorNodeRLayers')
    comp = nt.nodes.new('CompositorNodeComposite')
    g = nt.nodes.new('CompositorNodeGlare')
    try:
        g.glare_type = glare
    except Exception:
        g.glare_type = 'FOG_GLOW'
    for k, v in dict(quality='HIGH', mix=-1 + 2 * strength, threshold=threshold, size=size).items():
        try:
            setattr(g, k, v)
        except Exception:
            pass
    # 4.5 may expose these as sockets
    for k, v in (('Strength', strength), ('Threshold', threshold), ('Size', size / 9.0)):
        if k in g.inputs:
            try:
                g.inputs[k].default_value = v
            except Exception:
                pass
    lens = nt.nodes.new('CompositorNodeLensdist')
    try:
        lens.inputs['Dispersion'].default_value = 0.012
        lens.inputs['Distortion'].default_value = 0.0
    except Exception:
        pass
    nt.links.new(rl.outputs['Image'], g.inputs['Image'])
    nt.links.new(g.outputs['Image'], lens.inputs['Image'])
    nt.links.new(lens.outputs['Image'], comp.inputs['Image'])
    return g

# ----------------------------------------------------------------------------- world
def world_color(col, strength=1.0, fog=0.0, fog_col=None, aniso=0.2):
    w = bpy.data.worlds.new('World')
    bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputWorld')
    bg = nt.nodes.new('ShaderNodeBackground')
    bg.inputs['Color'].default_value = C(col) if isinstance(col, str) else col
    bg.inputs['Strength'].default_value = strength
    nt.links.new(bg.outputs[0], out.inputs['Surface'])
    if fog > 0:
        # NOTE: Eevee Next treats a *world* volume as infinite and it blocks the sun + sky, so fog lives in a mesh box.
        sx, sy, sz = FOG_BOX
        fog_box((sx, sy, sz), (0, 0, sz / 2 - 1.0), density=fog, color=fog_col if isinstance(fog_col, str) else '#cfc2b0',
                aniso=aniso, name='AirFog')
    return w, nt, bg

def world_gradient(top, horizon, bottom=None, strength=1.0, fog=0.0, fog_col=None, aniso=0.3, sun_glow=None):
    """Vertical sky gradient (by view direction z). sun_glow=(dir_vec, color, size, strength)"""
    w, nt, bg = world_color('#000000', strength, fog, fog_col, aniso)
    tc = nt.nodes.new('ShaderNodeTexCoord')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(tc.outputs['Generated'], sep.inputs[0])
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    cr = ramp.color_ramp
    cr.elements[0].position = 0.38
    cr.elements[0].color = C(bottom or horizon)
    cr.elements[1].position = 0.75
    cr.elements[1].color = C(top)
    e = cr.elements.new(0.5)
    e.color = C(horizon)
    # Generated coords for world: z in [0,1] maps -1..1 of view direction
    nt.links.new(sep.outputs['Z'], ramp.inputs['Fac'])
    col_out = ramp.outputs['Color']
    if sun_glow:
        d, gcol, size, gs = sun_glow
        dot = nt.nodes.new('ShaderNodeVectorMath'); dot.operation = 'DOT_PRODUCT'
        nt.links.new(tc.outputs['Generated'], dot.inputs[0])
        dot.inputs[1].default_value = Vector(d).normalized()
        # Generated is 0..1 cube for world? use Object coords fallback: normal of view = generated*2-1
        mapr = nt.nodes.new('ShaderNodeMapRange')
        mapr.inputs['From Min'].default_value = 1 - size
        mapr.inputs['From Max'].default_value = 1.0
        powr = nt.nodes.new('ShaderNodeMath'); powr.operation = 'POWER'; powr.inputs[1].default_value = 3.0
        nt.links.new(dot.outputs['Value'], mapr.inputs['Value'])
        nt.links.new(mapr.outputs['Result'], powr.inputs[0])
        mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'; mix.blend_type = 'ADD'
        nt.links.new(powr.outputs[0], mix.inputs['Factor'])
        nt.links.new(col_out, mix.inputs['A'])
        mix.inputs['B'].default_value = tuple(x * gs for x in C(gcol)[:3]) + (1,)
        col_out = mix.outputs['Result']
    nt.links.new(col_out, bg.inputs['Color'])
    return w, nt, bg

def world_sky_view_gradient(top, horizon, below, strength=1.0, fog=0.0, fog_col=None, aniso=0.3,
                            glow_dir=None, glow_col='#FF8A2A', glow_size=0.25, glow_strength=2.0):
    """Gradient from the *view direction* (Incoming of Light Path is not available; use Geometry Incoming)."""
    w, nt, bg = world_color('#000000', strength, fog, fog_col, aniso)
    geo = nt.nodes.new('ShaderNodeTexCoord')
    inv = nt.nodes.new('ShaderNodeVectorMath'); inv.operation = 'NORMALIZE'
    nt.links.new(geo.outputs['Generated'], inv.inputs[0])
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(inv.outputs[0], sep.inputs[0])
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    cr = ramp.color_ramp
    cr.elements[0].position = 0.0
    cr.elements[0].color = C(below)
    cr.elements[1].position = 1.0
    cr.elements[1].color = C(top)
    e = cr.elements.new(0.52); e.color = C(horizon)
    e2 = cr.elements.new(0.47); e2.color = C(below)
    mr = nt.nodes.new('ShaderNodeMapRange')
    mr.inputs['From Min'].default_value = -1; mr.inputs['From Max'].default_value = 1
    nt.links.new(sep.outputs['Z'], mr.inputs['Value'])
    nt.links.new(mr.outputs['Result'], ramp.inputs['Fac'])
    col = ramp.outputs['Color']
    if glow_dir is not None:
        dot = nt.nodes.new('ShaderNodeVectorMath'); dot.operation = 'DOT_PRODUCT'
        nt.links.new(inv.outputs[0], dot.inputs[0])
        dot.inputs[1].default_value = Vector(glow_dir).normalized()
        m2 = nt.nodes.new('ShaderNodeMapRange')
        m2.inputs['From Min'].default_value = 1 - glow_size; m2.inputs['From Max'].default_value = 1.0
        nt.links.new(dot.outputs['Value'], m2.inputs['Value'])
        pw = nt.nodes.new('ShaderNodeMath'); pw.operation = 'POWER'; pw.inputs[1].default_value = 2.2
        nt.links.new(m2.outputs['Result'], pw.inputs[0])
        sc = nt.nodes.new('ShaderNodeMath'); sc.operation = 'MULTIPLY'; sc.inputs[1].default_value = glow_strength
        nt.links.new(pw.outputs[0], sc.inputs[0])
        mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'; mix.blend_type = 'ADD'
        mix.inputs['Factor'].default_value = 1.0
        cm = nt.nodes.new('ShaderNodeMix'); cm.data_type = 'RGBA'; cm.blend_type = 'MULTIPLY'
        cm.inputs['Factor'].default_value = 1.0
        cm.inputs['A'].default_value = C(glow_col)
        # scalar -> color via combine
        comb = nt.nodes.new('ShaderNodeCombineXYZ')
        for s in ('X', 'Y', 'Z'):
            nt.links.new(sc.outputs[0], comb.inputs[s])
        nt.links.new(comb.outputs[0], cm.inputs['B'])
        nt.links.new(col, mix.inputs['A'])
        nt.links.new(cm.outputs['Result'], mix.inputs['B'])
        col = mix.outputs['Result']
    nt.links.new(col, bg.inputs['Color'])
    return w, nt, bg

def fog_box(size=(200, 200, 60), loc=(0, 0, 20), density=0.02, color='#cfc2b0', aniso=0.35, noise=0.0, noise_scale=0.08,
            name='Fog'):
    ob = box(size, loc, None, bevel=0, name=name)
    m = bpy.data.materials.new(name + 'Mat')
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    v = nt.nodes.new('ShaderNodeVolumePrincipled')
    v.inputs['Color'].default_value = C(color)
    v.inputs['Anisotropy'].default_value = aniso
    if noise > 0:
        tc = nt.nodes.new('ShaderNodeTexCoord')
        nz = nt.nodes.new('ShaderNodeTexNoise')
        nz.inputs['Scale'].default_value = noise_scale
        nz.inputs['Detail'].default_value = 3
        nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
        mr = nt.nodes.new('ShaderNodeMapRange')
        mr.inputs['From Min'].default_value = 0.35; mr.inputs['From Max'].default_value = 0.75
        mr.inputs['To Min'].default_value = density * (1 - noise); mr.inputs['To Max'].default_value = density * (1 + noise)
        nt.links.new(nz.outputs['Fac'], mr.inputs['Value'])
        nt.links.new(mr.outputs['Result'], v.inputs['Density'])
    else:
        v.inputs['Density'].default_value = density
    nt.links.new(v.outputs[0], out.inputs['Volume'])
    ob.data.materials.append(m)
    ob.visible_shadow = False
    return ob, v

# ----------------------------------------------------------------------------- materials
_mat_cache = {}

def mat(name, color, rough=0.65, metal=0.0, emit=None, emit_strength=0.0, spec=0.5, bump=0.0, bump_scale=8.0,
        var=0.0, var_scale=3.0, coat=0.0, alpha=1.0, sss=0.0):
    """Principled material. var = color variation (noise) amount, bump = noise bump strength."""
    key = name
    if key in _mat_cache and _mat_cache[key].name in bpy.data.materials:
        return _mat_cache[key]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    p = nt.nodes['Principled BSDF']
    col = C(color) if isinstance(color, str) else color
    p.inputs['Base Color'].default_value = col
    p.inputs['Roughness'].default_value = rough
    p.inputs['Metallic'].default_value = metal
    try:
        p.inputs['Specular IOR Level'].default_value = spec
    except Exception:
        pass
    if coat:
        p.inputs['Coat Weight'].default_value = coat
    if emit is not None:
        p.inputs['Emission Color'].default_value = C(emit) if isinstance(emit, str) else emit
        p.inputs['Emission Strength'].default_value = emit_strength
    if alpha < 1:
        p.inputs['Alpha'].default_value = alpha
        try:
            m.surface_render_method = 'BLENDED'
        except Exception:
            pass
    if var > 0 or bump > 0:
        tc = nt.nodes.new('ShaderNodeTexCoord')
        nz = nt.nodes.new('ShaderNodeTexNoise')
        nz.inputs['Scale'].default_value = var_scale
        nz.inputs['Detail'].default_value = 8.0
        nz.inputs['Roughness'].default_value = 0.6
        nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
        if var > 0:
            mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'; mix.blend_type = 'MULTIPLY'
            mr = nt.nodes.new('ShaderNodeMapRange')
            mr.inputs['To Min'].default_value = 1 - var
            mr.inputs['To Max'].default_value = 1 + var * 0.6
            nt.links.new(nz.outputs['Fac'], mr.inputs['Value'])
            comb = nt.nodes.new('ShaderNodeCombineXYZ')
            for s in ('X', 'Y', 'Z'):
                nt.links.new(mr.outputs['Result'], comb.inputs[s])
            mix.inputs['Factor'].default_value = 1.0
            mix.inputs['A'].default_value = col
            nt.links.new(comb.outputs[0], mix.inputs['B'])
            nt.links.new(mix.outputs['Result'], p.inputs['Base Color'])
            # roughness variation too
            rr = nt.nodes.new('ShaderNodeMapRange')
            rr.inputs['To Min'].default_value = max(0.0, rough - 0.12)
            rr.inputs['To Max'].default_value = min(1.0, rough + 0.12)
            nt.links.new(nz.outputs['Fac'], rr.inputs['Value'])
            nt.links.new(rr.outputs['Result'], p.inputs['Roughness'])
        if bump > 0:
            nz2 = nt.nodes.new('ShaderNodeTexNoise')
            nz2.inputs['Scale'].default_value = bump_scale
            nz2.inputs['Detail'].default_value = 10.0
            nt.links.new(tc.outputs['Object'], nz2.inputs['Vector'])
            b = nt.nodes.new('ShaderNodeBump')
            b.inputs['Strength'].default_value = bump
            b.inputs['Distance'].default_value = 0.02
            nt.links.new(nz2.outputs['Fac'], b.inputs['Height'])
            nt.links.new(b.outputs['Normal'], p.inputs['Normal'])
    _mat_cache[key] = m
    return m

def emission_mat(name, color, strength=5.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    em = nt.nodes.new('ShaderNodeEmission')
    em.inputs['Color'].default_value = C(color) if isinstance(color, str) else color
    em.inputs['Strength'].default_value = strength
    nt.links.new(em.outputs[0], out.inputs['Surface'])
    return m, em

def key_value(sock, frame, value, interp='BEZIER'):
    sock.default_value = value
    sock.keyframe_insert('default_value', frame=frame)
    _set_interp(sock.id_data, interp)

def _set_interp(idblock, interp):
    ad = getattr(idblock, 'animation_data', None)
    if ad and ad.action:
        for fc in ad.action.fcurves:
            for kp in fc.keyframe_points:
                if interp == 'BEZIER':
                    kp.interpolation = 'BEZIER'
                    kp.easing = 'AUTO'
                    kp.handle_left_type = kp.handle_right_type = 'AUTO_CLAMPED'
                else:
                    kp.interpolation = interp

# ----------------------------------------------------------------------------- geometry
def _link(ob, coll=None):
    (coll or bpy.context.scene.collection).objects.link(ob)
    return ob

def collection(name):
    c = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(c)
    return c

def mesh_from_bm(bm, name, mat_=None, loc=(0, 0, 0), rot=(0, 0, 0), smooth=True, coll=None):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    if smooth:
        me.polygons.foreach_set('use_smooth', [True] * len(me.polygons))
    ob = bpy.data.objects.new(name, me)
    ob.location = loc
    ob.rotation_euler = rot
    if mat_ is not None:
        me.materials.append(mat_)
    return _link(ob, coll)

def add_bevel(ob, width=0.02, segs=3, harden=True, angle=40):
    if width <= 0:
        return ob
    m = ob.modifiers.new('Bevel', 'BEVEL')
    m.width = width
    m.segments = segs
    m.limit_method = 'ANGLE'
    m.angle_limit = math.radians(angle)
    try:
        m.harden_normals = harden
    except Exception:
        pass
    return ob

def box(size=(1, 1, 1), loc=(0, 0, 0), mat_=None, rot=(0, 0, 0), bevel=0.02, name='Box', coll=None, origin='center'):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    sx, sy, sz = size
    oz = 0.5 if origin == 'bottom' else 0.0
    for v in bm.verts:
        v.co = Vector((v.co.x * sx, v.co.y * sy, (v.co.z + oz) * sz))
    ob = mesh_from_bm(bm, name, mat_, loc, rot, smooth=bevel > 0, coll=coll)
    if bevel > 0:
        add_bevel(ob, min(bevel, min(size) * 0.45))
    return ob

def cyl(r=0.5, h=1.0, loc=(0, 0, 0), mat_=None, rot=(0, 0, 0), verts=32, r2=None, bevel=0.0, name='Cyl', coll=None,
        origin='center', cap=True):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=cap, cap_tris=False, segments=verts, radius1=r, radius2=r if r2 is None else r2,
                          depth=h)
    if origin == 'bottom':
        for v in bm.verts:
            v.co.z += h / 2
    ob = mesh_from_bm(bm, name, mat_, loc, rot, smooth=True, coll=coll)
    if bevel > 0:
        add_bevel(ob, bevel, angle=50)
    return ob

def sphere(r=0.5, loc=(0, 0, 0), mat_=None, segs=32, rings=16, scale=(1, 1, 1), name='Sphere', coll=None):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=rings, radius=r)
    for v in bm.verts:
        v.co = Vector((v.co.x * scale[0], v.co.y * scale[1], v.co.z * scale[2]))
    return mesh_from_bm(bm, name, mat_, loc, smooth=True, coll=coll)

def plane(size=(10, 10), loc=(0, 0, 0), mat_=None, rot=(0, 0, 0), name='Plane', subdiv=0, coll=None):
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=max(1, subdiv), y_segments=max(1, subdiv), size=0.5)
    for v in bm.verts:
        v.co.x *= size[0]
        v.co.y *= size[1]
    return mesh_from_bm(bm, name, mat_, loc, rot, smooth=False, coll=coll)

def poly_prism(points2d, h, loc=(0, 0, 0), mat_=None, rot=(0, 0, 0), name='Prism', bevel=0.0, coll=None):
    """Extrude a 2D polygon (x,y) up by h."""
    bm = bmesh.new()
    vs = [bm.verts.new((x, y, 0)) for x, y in points2d]
    f = bm.faces.new(vs)
    ext = bmesh.ops.extrude_face_region(bm, geom=[f])
    for v in [e for e in ext['geom'] if isinstance(e, bmesh.types.BMVert)]:
        v.co.z += h
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = mesh_from_bm(bm, name, mat_, loc, rot, smooth=bevel > 0, coll=coll)
    if bevel:
        add_bevel(ob, bevel)
    return ob

def empty(name='Empty', loc=(0, 0, 0), rot=(0, 0, 0), coll=None):
    ob = bpy.data.objects.new(name, None)
    ob.location = loc
    ob.rotation_euler = rot
    ob.empty_display_size = 0.3
    return _link(ob, coll)

def parent(child, par, keep=True):
    mw = child.matrix_world.copy()
    child.parent = par
    if keep:
        child.matrix_parent_inverse = par.matrix_world.inverted()
    return child

def curve_poly(name, pts_list, bevel=0.01, mat_=None, res=2, coll=None, caps=True):
    cu = bpy.data.curves.new(name, 'CURVE')
    cu.dimensions = '3D'
    cu.bevel_depth = bevel
    cu.bevel_resolution = res
    cu.use_fill_caps = caps
    try:
        cu.bevel_factor_mapping_start = 'SPLINE'
        cu.bevel_factor_mapping_end = 'SPLINE'
    except Exception:
        pass
    for pts in pts_list:
        if len(pts) < 2:
            continue
        sp = cu.splines.new('POLY')
        sp.points.add(len(pts) - 1)
        for i, p in enumerate(pts):
            sp.points[i].co = (p[0], p[1], p[2], 1.0)
    ob = bpy.data.objects.new(name, cu)
    if mat_ is not None:
        cu.materials.append(mat_)
    return _link(ob, coll)

def text_obj(body, size=0.5, loc=(0, 0, 0), rot=(0, 0, 0), mat_=None, font=None, extrude=0.0, align='CENTER',
             name='Text', coll=None):
    cu = bpy.data.curves.new(name, 'FONT')
    cu.body = body
    cu.size = size
    cu.extrude = extrude
    cu.align_x = align
    cu.align_y = 'CENTER'
    if font and os.path.exists(font):
        cu.font = bpy.data.fonts.load(font)
    ob = bpy.data.objects.new(name, cu)
    ob.location = loc
    ob.rotation_euler = rot
    if mat_ is not None:
        cu.materials.append(mat_)
    return _link(ob, coll)

# ----------------------------------------------------------------------------- lights & camera
def light(kind='AREA', loc=(0, 0, 5), rot=(0, 0, 0), energy=500, color='#FFE2C0', size=1.0, spot=45, blend=0.3,
          name=None, shadow=True, volume=1.0, soft=None, coll=None):
    ld = bpy.data.lights.new(name or kind, kind)
    ld.energy = energy
    ld.color = C(color)[:3] if isinstance(color, str) else color[:3]
    ld.use_shadow = shadow
    try:
        ld.volume_factor = volume
    except Exception:
        pass
    if kind == 'AREA':
        ld.shape = 'DISK'
        ld.size = size
    elif kind == 'SPOT':
        ld.spot_size = math.radians(spot)
        ld.spot_blend = blend
        ld.shadow_soft_size = size if soft is None else soft
    elif kind == 'POINT':
        ld.shadow_soft_size = size if soft is None else soft
    elif kind == 'SUN':
        ld.angle = math.radians(size)
    ob = bpy.data.objects.new(ld.name, ld)
    ob.location = loc
    ob.rotation_euler = rot
    return _link(ob, coll)

def look_at(ob, target, roll=0.0):
    d = Vector(target) - ob.location
    q = d.to_track_quat('-Z', 'Y')
    ob.rotation_euler = q.to_euler()
    if roll:
        ob.rotation_euler.rotate_axis('Z', roll)
    return ob

def camera(loc=(0, -10, 2), target=(0, 0, 1), lens=35, dof=None, fstop=2.8, sensor=36.0, shift=(0, 0), name='Cam'):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.sensor_fit = 'HORIZONTAL'
    cd.sensor_width = sensor
    cd.shift_x, cd.shift_y = shift
    cd.clip_start = 0.02
    cd.clip_end = 2000
    if dof is not None:
        cd.dof.use_dof = True
        cd.dof.aperture_fstop = fstop
        if isinstance(dof, (int, float)):
            cd.dof.focus_distance = dof
        else:
            cd.dof.focus_object = dof
    ob = bpy.data.objects.new(name, cd)
    ob.location = loc
    _link(ob)
    look_at(ob, target)
    bpy.context.scene.camera = ob
    return ob

def ease(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)

def ease_io(t, p=2.2):
    t = max(0.0, min(1.0, t))
    return t ** p / (t ** p + (1 - t) ** p) if 0 < t < 1 else t

def lerp(a, b, t):
    return a + (b - a) * t

def vlerp(a, b, t):
    return Vector(a).lerp(Vector(b), t)

def animate_camera(cam, keys, target_keys=None, step=2, lens_keys=None, focus_keys=None):
    """keys: list of (time_s, (x,y,z)); target_keys: list of (time_s, (x,y,z)). Baked every `step` frames with
    smoothstep easing between keys (no overshoot), linear interpolation between baked keys."""
    sc = bpy.context.scene
    f0, f1 = sc.frame_start, sc.frame_end

    def sample(kk, t):
        if t <= kk[0][0]:
            return Vector(kk[0][1])
        for (ta, a), (tb, b) in zip(kk, kk[1:]):
            if ta <= t <= tb:
                u = (t - ta) / max(1e-6, tb - ta)
                return Vector(a).lerp(Vector(b), ease_io(u, 1.8))
        return Vector(kk[-1][1])

    def sample_s(kk, t):
        if t <= kk[0][0]:
            return kk[0][1]
        for (ta, a), (tb, b) in zip(kk, kk[1:]):
            if ta <= t <= tb:
                return lerp(a, b, ease_io((t - ta) / max(1e-6, tb - ta), 1.8))
        return kk[-1][1]

    frames = list(range(f0, f1 + 1, step))
    if frames[-1] != f1:
        frames.append(f1)
    prev = None
    for f in frames:
        t = (f - 1) / FPS
        cam.location = sample(keys, t)
        if target_keys:
            look_at(cam, sample(target_keys, t))
            if prev is not None:  # keep euler continuous
                e = cam.rotation_euler
                for i in range(3):
                    while e[i] - prev[i] > math.pi:
                        e[i] -= 2 * math.pi
                    while e[i] - prev[i] < -math.pi:
                        e[i] += 2 * math.pi
            prev = cam.rotation_euler.copy()
            cam.keyframe_insert('rotation_euler', frame=f)
        cam.keyframe_insert('location', frame=f)
        if lens_keys:
            cam.data.lens = sample_s(lens_keys, t)
            cam.data.keyframe_insert('lens', frame=f)
        if focus_keys:
            cam.data.dof.focus_distance = sample_s(focus_keys, t)
            cam.data.dof.keyframe_insert('focus_distance', frame=f)
    for idb in (cam, cam.data):
        ad = idb.animation_data
        if ad and ad.action:
            for fc in ad.action.fcurves:
                for kp in fc.keyframe_points:
                    kp.interpolation = 'LINEAR'

def key_obj(ob, frame, loc=None, rot=None, scale=None, interp='BEZIER'):
    if loc is not None:
        ob.location = loc
        ob.keyframe_insert('location', frame=frame)
    if rot is not None:
        ob.rotation_euler = rot
        ob.keyframe_insert('rotation_euler', frame=frame)
    if scale is not None:
        ob.scale = scale if hasattr(scale, '__len__') else (scale, scale, scale)
        ob.keyframe_insert('scale', frame=frame)
    if ob.animation_data and ob.animation_data.action:
        for fc in ob.animation_data.action.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = interp
                if interp == 'BEZIER':
                    kp.handle_left_type = kp.handle_right_type = 'AUTO_CLAMPED'

def sec2f(t):
    return 1 + int(round(t * FPS))

def add_sine(ob, path, index, amp, period_s, phase=0.0, offset=0.0):
    """Add a sine F-Modifier to a property channel (keeps evaluating without Python drivers)."""
    if not ob.animation_data:
        ob.animation_data_create()
    if not ob.animation_data.action:
        ob.animation_data.action = bpy.data.actions.new(ob.name + 'Act')
    act = ob.animation_data.action
    fc = act.fcurves.find(path, index=index)
    if fc is None:
        # need a keyframe for the channel to exist
        ob.keyframe_insert(path, index=index, frame=1)
        fc = act.fcurves.find(path, index=index)
    m = fc.modifiers.new('FNGENERATOR')
    m.function_type = 'SIN'
    m.amplitude = amp
    m.phase_multiplier = 2 * math.pi / (period_s * FPS)
    m.phase_offset = phase
    m.value_offset = offset
    m.use_additive = True
    return m

# ----------------------------------------------------------------------------- people
PEOPLE_COLS = ['#6B4E3D', '#3E4A52', '#8C6F55', '#4F5A43', '#5B3F4A', '#7A6A58', '#2F3438', '#9C5B3B', '#C2B49A',
               '#4A3C33', '#6E7B85', '#A0805E']
SKIN = ['#C69C7B', '#A87A5A', '#8A5E43', '#E0B99A', '#6E4A35', '#D4A989']

_person_meshes = {}

def _person_parts():
    if _person_meshes:
        return _person_meshes
    def bm_capsule(r, h, segs=16):
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=12, radius=r)
        for v in bm.verts:
            if v.co.z > 0:
                v.co.z += h / 2
            else:
                v.co.z -= h / 2
        return bm
    def to_mesh(bm, name):
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        bm.free()
        me.polygons.foreach_set('use_smooth', [True] * len(me.polygons))
        return me
    _person_meshes['torso'] = to_mesh(bm_capsule(0.17, 0.32), 'P_torso')
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=20, v_segments=14, radius=0.11)
    _person_meshes['head'] = to_mesh(bm, 'P_head')
    bm = bm_capsule(0.065, 0.62)
    for v in bm.verts:
        v.co.z -= 0.36  # pivot at hip
    _person_meshes['leg'] = to_mesh(bm, 'P_leg')
    bm = bm_capsule(0.045, 0.5)
    for v in bm.verts:
        v.co.z -= 0.27  # pivot at shoulder
    _person_meshes['arm'] = to_mesh(bm, 'P_arm')
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * 0.36, v.co.y * 0.16, v.co.z * 0.5 + 0.25))
    _person_meshes['bag'] = to_mesh(bm, 'P_bag')
    return _person_meshes

def _obj_mat(ob, m):
    ob.data.materials.clear() if False else None
    if len(ob.material_slots) == 0:
        ob.data.materials.append(m) if len(ob.data.materials) == 0 else None
    ob.material_slots[0].link = 'OBJECT'
    ob.material_slots[0].material = m

_pmat = {}

def pmat(col):
    if col not in _pmat:
        _pmat[col] = mat('P_' + col, col, rough=0.8, var=0.08, var_scale=6)
    return _pmat[col]

def person(loc=(0, 0, 0), heading=0.0, height=1.0, rng=None, coll=None, bag=False, name='Person'):
    """Simple stylised person (pivot at feet). Returns dict of parts."""
    rng = rng or random
    parts = _person_parts()
    root = empty(name, loc, (0, 0, heading), coll=coll)
    root.scale = (height, height, height)
    col_top = rng.choice(PEOPLE_COLS)
    col_bot = rng.choice(['#2B2826', '#3A3631', '#4A4540', '#2E3236', '#5A4B3E'])
    skin = rng.choice(SKIN)
    def part(key, l, m):
        ob = bpy.data.objects.new(name + '_' + key, parts[key])
        ob.location = l
        _link(ob, coll)
        _obj_mat(ob, m)
        ob.parent = root
        return ob
    torso = part('torso', (0, 0, 1.18), pmat(col_top))
    torso.scale = (1.0, 0.72, 1.0)
    head = part('head', (0, 0, 1.62), pmat(skin))
    legL = part('leg', (0.085, 0, 0.86), pmat(col_bot))
    legR = part('leg', (-0.085, 0, 0.86), pmat(col_bot))
    armL = part('arm', (0.215, 0, 1.38), pmat(col_top))
    armR = part('arm', (-0.215, 0, 1.38), pmat(col_top))
    out = dict(root=root, torso=torso, head=head, legL=legL, legR=legR, armL=armL, armR=armR)
    if bag:
        b = part('bag', (0.0, 0.17, 0.95), pmat(rng.choice(['#3A3631', '#6B4E3D', '#5D6A72'])))
        b.scale = (0.75, 0.9, 0.62)
        out['bag'] = b
    return out

def walk(p, speed=1.3, period=1.05, phase=0.0, swing=0.5):
    """Leg/arm swing + body bob as F-modifiers (forward = local -Y of root)."""
    for k, sgn in (('legL', 1), ('legR', -1)):
        add_sine(p[k], 'rotation_euler', 0, swing * sgn, period, phase)
    for k, sgn in (('armL', -1), ('armR', 1)):
        add_sine(p[k], 'rotation_euler', 0, swing * 0.8 * sgn, period, phase)
    add_sine(p['torso'], 'location', 2, 0.025, period / 2, phase * 2, 0)
    add_sine(p['head'], 'location', 2, 0.025, period / 2, phase * 2, 0)

def move_root(p, path_pts, t0=0.0, speed=1.3):
    """Animate root along polyline (world xy) at constant speed starting at t0 seconds. Heading follows path."""
    root = p['root']
    sc = bpy.context.scene
    pts = [Vector(x) for x in path_pts]
    segs = [(a, b, (b - a).length) for a, b in zip(pts, pts[1:])]
    total = sum(s[2] for s in segs)
    def at(d):
        for a, b, L in segs:
            if d <= L:
                return a.lerp(b, d / max(L, 1e-6)), (b - a)
            d -= L
        a, b, L = segs[-1]
        return b, (b - a)
    for f in range(sc.frame_start, sc.frame_end + 1, 6):
        t = (f - 1) / FPS - t0
        d = max(0.0, t * speed)
        pos, dirv = at(min(d, total))
        root.location = pos
        root.rotation_euler = (0, 0, math.atan2(dirv.y, dirv.x) + math.pi / 2)
        root.keyframe_insert('location', frame=f)
        root.keyframe_insert('rotation_euler', frame=f)
    if root.animation_data and root.animation_data.action:
        for fc in root.animation_data.action.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = 'LINEAR'

def save_blend(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=path, compress=True)


def camera_fill(energy=0.9, color='#FFEBDD', angle=25.0, up=0.35):
    """Shadowless soft fill from behind the camera (keeps every object readable, user asked for fewer shadows)."""
    sc = bpy.context.scene
    cam = sc.camera
    if cam is None:
        return None
    sc.frame_set(sc.frame_start)
    fwd = cam.matrix_world.to_quaternion() @ Vector((0, 0, -1))
    d = (fwd + Vector((0, 0, -up))).normalized()          # light travels along d (from behind/above the camera)
    ld = bpy.data.lights.new('CamFill', 'SUN')
    ld.energy = energy
    ld.color = C(color)[:3]
    ld.use_shadow = False
    ld.angle = math.radians(angle)
    try:
        ld.volume_factor = 0.0
    except Exception:
        pass
    ob = bpy.data.objects.new('CamFill', ld)
    ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    sc.collection.objects.link(ob)
    return ob


# ----------------------------------------------------------------------------- vehicles
CAR_COLS = ['#8A2E25', '#2F3B45', '#C9C1B2', '#3E4A3A', '#6B6259', '#1F2124', '#A67C45', '#4B5E73']

def car(loc=(0, 0, 0), heading=0.0, color=None, coll=None, kind='sedan', lights=True, rng=None, name='Car'):
    """Simple stylised car, forward = local +X, pivot on the ground. Returns the root empty."""
    rng = rng or random
    col = color or rng.choice(CAR_COLS)
    paint = mat('CarPaint' + col, col, rough=0.32, coat=0.5, var=0.05, var_scale=3)
    glass = mat('CarGlass', '#15181B', rough=0.08, spec=0.8)
    rub = mat('Tyre', '#151414', rough=0.85)
    rim = mat('Rim', '#8C8C8A', rough=0.3, metal=0.9)
    root = empty(name, loc, (0, 0, heading), coll=coll)
    parts = []
    if kind == 'van':
        parts.append(box((4.9, 1.95, 1.75), (0, 0, 0.33), paint, bevel=0.12, name=name + 'Body', coll=coll, origin='bottom'))
        parts.append(box((0.05, 1.7, 0.7), (2.46, 0, 1.45), glass, bevel=0, name=name + 'Wind', coll=coll))
        for sy in (-1, 1):
            parts.append(box((1.6, 0.03, 0.55), (1.4, sy * 0.985, 1.55), glass, bevel=0, name=name + 'SideWin', coll=coll))
    else:
        parts.append(box((4.3, 1.8, 0.62), (0, 0, 0.33), paint, bevel=0.14, name=name + 'Body', coll=coll, origin='bottom'))
        cab = poly_prism([(-1.55, 0), (1.05, 0), (0.45, 0.56), (-1.2, 0.56)], 1.58, (0, 0, 0), glass, name=name + 'Cabin', bevel=0.05, coll=coll)
        cab.rotation_euler = (math.radians(90), 0, 0)
        cab.location = (0, 0.79, 0.93)
        parts.append(cab)
        parts.append(box((1.62, 1.5, 0.05), (-0.37, 0, 1.49), paint, bevel=0.02, name=name + 'Roof', coll=coll))
    L = 4.9 if kind == 'van' else 4.3
    for sx in (-1, 1):
        for sy in (-1, 1):
            w = cyl(0.33, 0.24, (sx * L * 0.31, sy * 0.84, 0.33), rub, rot=(math.radians(90), 0, 0), verts=24, bevel=0.03, name=name + 'Wheel', coll=coll)
            r = cyl(0.19, 0.25, (sx * L * 0.31, sy * 0.85, 0.33), rim, rot=(math.radians(90), 0, 0), verts=16, name=name + 'Rim', coll=coll)
            parts += [w, r]
    if lights:
        hm, _ = emission_mat('HeadLamp', '#FFE9C8', 8.0)
        tm, _ = emission_mat('TailLamp', '#FF2A1A', 6.0)
        for sy in (-0.62, 0.62):
            parts.append(box((0.04, 0.32, 0.12), (L / 2 + 0.01, sy, 0.78), hm, bevel=0, name=name + 'Head', coll=coll))
            parts.append(box((0.04, 0.3, 0.1), (-L / 2 - 0.01, sy, 0.8), tm, bevel=0, name=name + 'Tail', coll=coll))
    for p in parts:
        p.parent = root
    return root

def drive(root, path_pts, t0=0.0, speed=8.0, accel=1.5):
    """Move a car along a straight polyline starting at t0 with a soft start."""
    sc = bpy.context.scene
    pts = [Vector(p) for p in path_pts]
    total = sum((b - a).length for a, b in zip(pts, pts[1:]))
    def at(d):
        for a, b in zip(pts, pts[1:]):
            L = (b - a).length
            if d <= L:
                return a.lerp(b, d / max(L, 1e-6)), (b - a)
            d -= L
        return pts[-1], (pts[-1] - pts[-2])
    for f in range(sc.frame_start, sc.frame_end + 1, 3):
        t = max(0.0, (f - 1) / FPS - t0)
        d = 0.5 * accel * t * t if t < speed / accel else (speed * speed / (2 * accel) + speed * (t - speed / accel))
        p, dv = at(min(d, total))
        root.location = p
        root.rotation_euler = (0, 0, math.atan2(dv.y, dv.x))
        root.keyframe_insert('location', frame=f)
        root.keyframe_insert('rotation_euler', frame=f)
    for fc in root.animation_data.action.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = 'LINEAR'
