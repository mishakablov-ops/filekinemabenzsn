"""Materials of the permanent city (metro_*.py). Everything reads one node group, MetroGlobals, so a preset changes the
time of day for the whole city at once: Night (0 day .. 1 night), Lit (share of lit windows), Street (street lights),
Neon (signs, screens, shop windows), Traffic (density of car lights), Time (seconds, keyed linearly), Fog (density per
metre, height, colour). Fog is aerial perspective inside every material (MetroFog), so the far city melts into the sky
in Eevee and Cycles alike without a volume.

Facades take their pattern from the mesh: UV u = metres along the footprint, v = height in metres; face attributes
bcol (wall colour), brnd (0..1 per building), fh (floor height), bay (window bay), gf (shop floor height, 0 = none),
crown (1 on floodlit crowns).
"""
import bpy
import lib
from lib import C

G = 'MetroGlobals'
GLOBAL_DEFAULTS = dict(Night=0.0, Lit=0.1, Street=0.0, Neon=0.3, Traffic=0.6, Time=0.0, FogDensity=0.00025,
                       FogHeight=600.0, FocusX=0.0, FocusY=0.0, FocusR=0.0, Signal=1.0)
FOG_COLOR = '#AFC0CC'


# ----------------------------------------------------------------------------- node helpers
class NB:
    """Tiny node builder: numbers or sockets in, sockets out."""

    def __init__(self, nt):
        self.nt, self.L = nt, nt.links

    def node(self, kind, **props):
        n = self.nt.nodes.new(kind)
        for k, v in props.items():
            setattr(n, k, v)
        return n

    def _in(self, sock, v):
        if hasattr(v, 'is_output') or hasattr(v, 'links'):
            self.L.new(v, sock)
        else:
            sock.default_value = v

    def math(self, op, a, b=0.0, clamp=False):
        n = self.node('ShaderNodeMath', operation=op, use_clamp=clamp)
        self._in(n.inputs[0], a)
        self._in(n.inputs[1], b)
        return n.outputs[0]

    def add(self, a, b): return self.math('ADD', a, b)
    def sub(self, a, b): return self.math('SUBTRACT', a, b)
    def mul(self, a, b): return self.math('MULTIPLY', a, b)
    def div(self, a, b): return self.math('DIVIDE', a, b)
    def fract(self, a): return self.math('FRACT', a)
    def floor(self, a): return self.math('FLOOR', a)
    def lt(self, a, b): return self.math('LESS_THAN', a, b)
    def gt(self, a, b): return self.math('GREATER_THAN', a, b)
    def mn(self, a, b): return self.math('MINIMUM', a, b)
    def mx(self, a, b): return self.math('MAXIMUM', a, b)
    def exp(self, a): return self.math('EXPONENT', a)
    def clamp01(self, a): return self.math('ADD', a, 0.0, clamp=True)

    def band(self, x, a, b):
        return self.mul(self.gt(x, a), self.lt(x, b))

    def smooth_band(self, x, a, b, soft=0.02):
        n1 = self.node('ShaderNodeMapRange', interpolation_type='SMOOTHSTEP')
        self._in(n1.inputs['Value'], x)
        n1.inputs['From Min'].default_value = a - soft
        n1.inputs['From Max'].default_value = a + soft
        n2 = self.node('ShaderNodeMapRange', interpolation_type='SMOOTHSTEP')
        self._in(n2.inputs['Value'], x)
        n2.inputs['From Min'].default_value = b + soft
        n2.inputs['From Max'].default_value = b - soft
        return self.mul(n1.outputs['Result'], n2.outputs['Result'])

    def mixc(self, f, a, b):
        n = self.node('ShaderNodeMix', data_type='RGBA')
        self._in(n.inputs['Factor'], f)
        self._in(n.inputs[6], C(a) if isinstance(a, str) else a)
        self._in(n.inputs[7], C(b) if isinstance(b, str) else b)
        return n.outputs[2]

    def scalec(self, col, f):
        n = self.node('ShaderNodeVectorMath', operation='SCALE')
        self._in(n.inputs[0], col)
        self._in(n.inputs['Scale'], f)
        return n.outputs[0]

    def attr(self, name, out='Fac'):
        n = self.node('ShaderNodeAttribute', attribute_type='GEOMETRY', attribute_name=name)
        return n.outputs[out]

    def xyz(self, a, b, c=0.0):
        n = self.node('ShaderNodeCombineXYZ')
        self._in(n.inputs[0], a)
        self._in(n.inputs[1], b)
        self._in(n.inputs[2], c)
        return n.outputs[0]

    def sep(self, v):
        n = self.node('ShaderNodeSeparateXYZ')
        self._in(n.inputs[0], v)
        return n.outputs

    def noise3(self, v):
        n = self.node('ShaderNodeTexWhiteNoise', noise_dimensions='3D')
        self._in(n.inputs['Vector'], v)
        return n.outputs['Value'], n.outputs['Color']

    def glob(self):
        n = self.node('ShaderNodeGroup')
        n.node_tree = globals_group()
        return n.outputs


def _sock(ng, name, kind, io='OUTPUT'):
    return ng.interface.new_socket(name=name, in_out=io, socket_type=kind)


def globals_group():
    ng = bpy.data.node_groups.get(G)
    if ng:
        return ng
    ng = bpy.data.node_groups.new(G, 'ShaderNodeTree')
    out = ng.nodes.new('NodeGroupOutput')
    for k, v in GLOBAL_DEFAULTS.items():
        _sock(ng, k, 'NodeSocketFloat')
        n = ng.nodes.new('ShaderNodeValue')
        n.name = n.label = k
        n.outputs[0].default_value = v
        ng.links.new(n.outputs[0], out.inputs[k])
    _sock(ng, 'FogColor', 'NodeSocketColor')
    n = ng.nodes.new('ShaderNodeRGB')
    n.name = n.label = 'FogColor'
    n.outputs[0].default_value = C(FOG_COLOR)
    ng.links.new(n.outputs[0], out.inputs['FogColor'])
    return ng


def set_global(name, value, frame=None):
    ng = globals_group()
    n = ng.nodes[name]
    if name == 'FogColor':
        n.outputs[0].default_value = C(value) if isinstance(value, str) else value
        if frame is not None:
            n.outputs[0].keyframe_insert('default_value', frame=frame)
        return
    n.outputs[0].default_value = value
    if frame is not None:
        n.outputs[0].keyframe_insert('default_value', frame=frame)


def key_time(fps, frames):
    """Time output runs in seconds through the whole shot (linear)."""
    ng = globals_group()
    s = ng.nodes['Time'].outputs[0]
    s.default_value = 0.0
    s.keyframe_insert('default_value', frame=1)
    s.default_value = (frames - 1) / fps
    s.keyframe_insert('default_value', frame=frames)
    ad = ng.animation_data
    if ad and ad.action:
        for fc in ad.action.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = 'LINEAR'


def fog_group():
    """Shader in -> shader out, mixed towards FogColor by distance from the camera (denser near the ground)."""
    ng = bpy.data.node_groups.get('MetroFog')
    if ng:
        return ng
    ng = bpy.data.node_groups.new('MetroFog', 'ShaderNodeTree')
    _sock(ng, 'Shader', 'NodeSocketShader', 'INPUT')
    _sock(ng, 'Shader', 'NodeSocketShader', 'OUTPUT')
    b = NB(ng)
    gi, go = ng.nodes.new('NodeGroupInput'), ng.nodes.new('NodeGroupOutput')
    g = b.glob()
    cam = b.node('ShaderNodeCameraData')
    geo = b.node('ShaderNodeNewGeometry')
    z = b.mx(b.sep(geo.outputs['Position'])[2], 0.0)
    hf = b.exp(b.div(b.mul(z, -1.0), g['FogHeight']))
    dens = b.mul(g['FogDensity'], b.add(0.3, b.mul(hf, 0.7)))
    f = b.sub(1.0, b.exp(b.mul(b.mul(cam.outputs['View Distance'], dens), -1.0)))
    em = b.node('ShaderNodeEmission')
    b.L.new(g['FogColor'], em.inputs['Color'])
    mix = b.node('ShaderNodeMixShader')
    b.L.new(f, mix.inputs[0])
    b.L.new(gi.outputs['Shader'], mix.inputs[1])
    b.L.new(em.outputs[0], mix.inputs[2])
    b.L.new(mix.outputs[0], go.inputs['Shader'])
    return ng


def finish(m, b, shader_out):
    """Route a shader through MetroFog into the material output."""
    out = b.node('ShaderNodeOutputMaterial')
    fg = b.node('ShaderNodeGroup')
    fg.node_tree = fog_group()
    b.L.new(shader_out, fg.inputs[0])
    b.L.new(fg.outputs[0], out.inputs['Surface'])
    return m


def new_mat(name):
    m = bpy.data.materials.get(name)
    if m:
        return None, m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    m.node_tree.nodes.clear()
    return NB(m.node_tree), m


def principled(b, base, rough, metal=0.0, spec=0.5, emit_col=None, emit=None, normal=None):
    p = b.node('ShaderNodeBsdfPrincipled')
    b._in(p.inputs['Base Color'], base)
    b._in(p.inputs['Roughness'], rough)
    b._in(p.inputs['Metallic'], metal)
    b._in(p.inputs['Specular IOR Level'], spec)
    if emit_col is not None:
        b._in(p.inputs['Emission Color'], emit_col)
        b._in(p.inputs['Emission Strength'], emit)
    if normal is not None:
        b.L.new(normal, p.inputs['Normal'])
    return p.outputs[0]


# ----------------------------------------------------------------------------- facades
# window placement inside one bay x one floor (fractions), glass tint, mullion colour, emission scale, warmth
KINDS = {
    'curtain':      dict(u=(0.035, 0.965), v=(0.13, 0.97), glass='#22303A', glass_mix=0.35, frame='#5A6168', em=2.2, warm=0.35, metal=0.6),
    'curtain_dark': dict(u=(0.04, 0.96), v=(0.14, 0.96), glass='#14181C', glass_mix=0.15, frame='#1A1B1D', em=2.0, warm=0.4, metal=0.7),
    'ribbon':       dict(u=(0.03, 0.97), v=(0.36, 0.88), glass='#1E262C', glass_mix=0.0, frame=None, em=2.2, warm=0.45, metal=0.0),
    'punched':      dict(u=(0.24, 0.76), v=(0.28, 0.82), glass='#1C2328', glass_mix=0.0, frame=None, em=2.8, warm=0.85, metal=0.0),
    'brick':        dict(u=(0.27, 0.73), v=(0.24, 0.80), glass='#1B2024', glass_mix=0.0, frame=None, em=2.8, warm=0.85, metal=0.0),
    'shopfront':    dict(u=(0.24, 0.76), v=(0.28, 0.82), glass='#1C2328', glass_mix=0.0, frame=None, em=2.8, warm=0.8, metal=0.0),
    'industrial':   dict(u=(0.1, 0.9), v=(0.6, 0.86), glass='#2A3034', glass_mix=0.0, frame=None, em=1.8, warm=0.3, metal=0.0),
}


def facade(kind):
    name = 'MF_' + kind
    b, m = new_mat(name)
    if b is None:
        return m
    k = KINDS[kind]
    g = b.glob()
    uv = b.node('ShaderNodeUVMap', uv_map='UVMap').outputs[0]
    u, v, _ = b.sep(uv)
    bcol = b.attr('bcol', 'Color')
    brnd = b.attr('brnd')
    fh, bay, gf, crown = b.attr('fh'), b.attr('bay'), b.attr('gf'), b.attr('crown')
    # shop floor: v below gf is one tall storey of shop windows
    is_gf = b.lt(v, gf)
    vv = b.sub(v, gf)
    U, V = b.div(u, bay), b.div(vv, fh)
    fu, fv = b.fract(U), b.fract(V)
    win = b.mul(b.band(fu, *k['u']), b.band(fv, *k['v']))
    if kind == 'industrial':      # windows only in every other bay
        win = b.mul(win, b.lt(b.fract(b.mul(b.floor(U), 0.5)), 0.25))
    shop = b.mul(b.band(b.fract(b.div(u, b.mul(bay, 2.0))), 0.04, 0.96), b.band(b.div(v, b.mx(gf, 0.01)), 0.06, 0.8))
    win = b.add(b.mul(win, b.sub(1.0, is_gf)), b.mul(shop, is_gf))
    # per-window randomness: lit or not, colour, brightness; whole floors tend to be lit together
    seed = b.mul(brnd, 917.0)
    r1, rc = b.noise3(b.xyz(b.floor(U), b.floor(V), seed))
    rf, _ = b.noise3(b.xyz(seed, b.floor(V), 3.7))
    r2, r3, _ = b.sep(rc)
    bl = b.add(0.1, b.mul(b.fract(b.mul(brnd, 7.31)), 1.8))
    lit = b.lt(b.add(b.mul(r1, 0.62), b.mul(rf, 0.38)), b.mul(g['Lit'], bl))
    warm = b.mixc(b.lt(r2, k['warm']), '#DCE6FA', '#FFC37C')
    warm = b.mixc(b.gt(r3, 0.82), warm, '#FFE6BD')
    em_win = b.mul(b.mul(b.mul(win, lit), g['Night']), b.mul(b.add(0.5, b.mul(r3, 1.2)), k['em']))
    em_win = b.mul(em_win, b.sub(1.0, is_gf))
    # what is inside a lit window: brighter towards the ceiling, curtains half drawn, blinds, furniture below
    u0, u1 = k['u']
    v0, v1 = k['v']
    wu = b.clamp01(b.div(b.sub(fu, u0), u1 - u0))
    wv = b.clamp01(b.div(b.sub(fv, v0), v1 - v0))
    r4, rc2 = b.noise3(b.xyz(b.floor(U), b.floor(V), b.add(seed, 31.7)))
    r5, _, _ = b.sep(rc2)
    c = b.add(0.1, b.mul(r5, 0.3))
    curt = b.mul(b.lt(r4, 0.45), b.clamp01(b.add(b.lt(wu, c), b.gt(wu, b.sub(1.0, c)))))
    blinds = b.mul(b.gt(r4, 0.85), b.lt(b.fract(b.mul(wv, 10.0)), 0.45))
    shade = b.sub(b.sub(1.0, b.mul(curt, 0.65)), b.mul(blinds, 0.45))
    room = b.mul(b.add(0.5, b.mul(wv, 0.7)), b.sub(1.0, b.mul(b.lt(wv, 0.22), 0.35)))
    em_win = b.mul(em_win, b.mul(shade, room))
    # shop windows glow with Neon
    shop_on = b.lt(r1, 0.8)
    inner = b.node('ShaderNodeTexNoise')            # shelves and people inside: uneven glow
    inner.inputs['Scale'].default_value = 0.9
    b.L.new(b.xyz(u, b.mul(v, 2.0), seed), inner.inputs['Vector'])
    em_shop = b.mul(b.mul(b.mul(shop, is_gf), shop_on), b.mul(b.mul(g['Neon'], b.add(0.05, b.mul(g['Night'], 0.95))), 1.4))
    # a shop interior seen from the street: shelves every 0.6 m, coloured goods, a bright ceiling strip
    shelf = b.mul(b.lt(b.fract(b.div(v, 0.6)), 0.14), b.band(v, 0.3, 2.5))
    goods, gcol = b.noise3(b.xyz(b.floor(b.mul(u, 3.0)), b.floor(b.div(v, 0.6)), seed))
    ceil = b.band(b.div(v, b.mx(gf, 0.01)), 0.68, 0.76)
    lum = b.add(b.mul(b.sub(1.0, b.mul(shelf, 0.75)), b.add(0.35, b.mul(inner.outputs['Fac'], 0.6))), b.mul(ceil, 1.6))
    em_shop = b.mul(em_shop, lum)
    shop_col = b.mixc(b.lt(r2, 0.5), '#FFD9A8', '#FFF0DC')
    shop_col = b.mixc(b.mul(b.mul(b.band(v, 0.3, 2.5), b.sub(1.0, ceil)), 0.45), shop_col, gcol)
    # floodlit crowns
    em_crown = b.mul(b.mul(crown, g['Night']), 1.6)
    emit = b.add(b.add(em_win, em_shop), em_crown)
    ecol = b.mixc(b.gt(em_shop, 0.001), b.mixc(b.mul(curt, 0.6), warm, '#E8925A'), shop_col)
    ecol = b.mixc(b.gt(em_crown, 0.001), ecol, '#FFDDA8')
    # surfaces: wall (or mullion) vs glass
    wallc = bcol
    if kind == 'brick':
        br = b.node('ShaderNodeTexBrick', offset=0.5, offset_frequency=2, squash=1.0, squash_frequency=2)
        b.L.new(b.xyz(u, v, 0.0), br.inputs['Vector'])
        br.inputs['Scale'].default_value = 1.0
        br.inputs['Brick Width'].default_value = 0.25
        br.inputs['Row Height'].default_value = 0.075
        br.inputs['Mortar Size'].default_value = 0.008
        b.L.new(b.scalec(bcol, 1.12), br.inputs['Color1'])
        b.L.new(b.scalec(bcol, 0.82), br.inputs['Color2'])
        br.inputs['Mortar'].default_value = C('#8C877E')
        wallc = br.outputs['Color']
    if k['frame']:
        wallc = b.mixc(0.6, bcol, k['frame'])
    # weathering: soft patches and vertical rain streaks, stronger near the ground
    dirt = b.node('ShaderNodeTexNoise')
    dirt.inputs['Scale'].default_value = 1.0
    dirt.inputs['Detail'].default_value = 4.0
    b.L.new(b.xyz(b.mul(u, 0.45), b.mul(v, 0.035), seed), dirt.inputs['Vector'])
    grime = b.add(b.mul(dirt.outputs['Fac'], 0.45), b.mul(b.lt(v, 1.2), 0.15))
    wallc = b.mixc(b.clamp01(b.sub(grime, 0.12)), wallc, b.scalec(wallc, 0.55))
    glass = b.mixc(k['glass_mix'], k['glass'], bcol) if k['glass_mix'] else C(k['glass'])
    # unlit windows at night look a little lit from inside (curtains, TV) only when lit is false
    base = b.mixc(win, wallc, glass)
    rough = b.add(b.mul(win, 0.05 - 0.8), 0.8) if kind != 'curtain' else b.add(b.mul(win, 0.04 - 0.3), 0.3)
    metal = b.mul(b.sub(1.0, win), k['metal'])
    spec = b.add(0.5, b.mul(win, 0.5))
    bump = b.node('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.6
    bump.inputs['Distance'].default_value = 0.08
    b.L.new(b.mul(win, -1.0), bump.inputs['Height'])
    sh = principled(b, base, rough, metal, spec, ecol, emit, bump.outputs['Normal'])
    m['metro'] = kind
    return finish(m, b, sh)


def roof_mat():
    b, m = new_mat('MF_roof')
    if b is None:
        return m
    g = b.glob()
    tc = b.node('ShaderNodeTexCoord')
    nz = b.node('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = 0.08
    b.L.new(tc.outputs['Object'], nz.inputs['Vector'])
    base = b.mixc(nz.outputs['Fac'], '#4A4B4C', '#6E6C68')
    sh = principled(b, base, 0.9)
    return finish(m, b, sh)


def flat_mat(name, color, rough=0.8, metal=0.0, spec=0.5, var=0.0, var_scale=0.2):
    b, m = new_mat(name)
    if b is None:
        return m
    base = C(color)
    if var:
        tc = b.node('ShaderNodeTexCoord')
        nz = b.node('ShaderNodeTexNoise')
        nz.inputs['Scale'].default_value = var_scale
        b.L.new(tc.outputs['Object'], nz.inputs['Vector'])
        base = b.mixc(b.mul(nz.outputs['Fac'], var), color, '#2A2A2A')
    sh = principled(b, base, rough, metal, spec)
    return finish(m, b, sh)


def glow_mat(name, color, strength, gate='Night', blink=0.0):
    """Emissive light source (lamp heads, aviation lights, screens). gate = which global switches it on."""
    b, m = new_mat(name)
    if b is None:
        return m
    g = b.glob()
    s = b.mul(g[gate], strength)
    if blink:
        ph = b.attr('brnd')
        s = b.mul(s, b.lt(b.fract(b.add(b.mul(g['Time'], blink), ph)), 0.5))
    em = b.node('ShaderNodeEmission')
    b._in(em.inputs['Color'], C(color))
    b.L.new(s, em.inputs['Strength'])
    p = principled(b, C('#2A2A2A'), 0.5)
    mix = b.node('ShaderNodeAddShader')
    b.L.new(p, mix.inputs[0])
    b.L.new(em.outputs[0], mix.inputs[1])
    return finish(m, b, mix.outputs[0])


def asphalt_mat():
    """Ground between the blocks = the roads. At night sodium pools of light every 30 m."""
    b, m = new_mat('MF_asphalt')
    if b is None:
        return m
    g = b.glob()
    tc = b.node('ShaderNodeTexCoord')
    x, y, _ = b.sep(tc.outputs['Object'])
    nz = b.node('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = 0.5
    b.L.new(tc.outputs['Object'], nz.inputs['Vector'])
    base = b.mixc(b.mul(nz.outputs['Fac'], 0.6), '#3A3C3F', '#26282A')
    dx, dy = b.sub(b.fract(b.div(x, 30.0)), 0.5), b.sub(b.fract(b.div(y, 30.0)), 0.5)
    pool = b.exp(b.mul(b.add(b.mul(dx, dx), b.mul(dy, dy)), -22.0))
    em = b.mul(b.mul(pool, g['Street']), 0.9)
    sh = principled(b, base, 0.82, 0.0, 0.5, C('#FFA34D'), em)
    return finish(m, b, sh)


def marking_mat():
    """Lane lines: geometry strips with UV u in metres; dashes 3 m on, 9 m off where attribute dash = 1."""
    b, m = new_mat('MF_marking')
    if b is None:
        return m
    uv = b.node('ShaderNodeUVMap', uv_map='UVMap').outputs[0]
    u, _, _ = b.sep(uv)
    dash = b.attr('dash')
    on = b.add(b.sub(1.0, dash), b.mul(dash, b.lt(b.fract(b.div(u, 12.0)), 0.25)))
    base = b.mixc(on, '#2E3033', '#D9D6CE')
    sh = principled(b, base, 0.7)
    return finish(m, b, sh)


def traffic_mat():
    """Painted traffic for the far city: car-sized patches drift along each lane (u in metres, attributes dir +-1,
    lane id, tx/ty = road direction). Day: car colours; night: white headlights on cars coming towards the camera,
    red tail lights on cars driving away. Hidden near FocusX/Y where real cars drive."""
    b, m = new_mat('MF_traffic')
    if b is None:
        return m
    g = b.glob()
    uv = b.node('ShaderNodeUVMap', uv_map='UVMap').outputs[0]
    u, vlat, _ = b.sep(uv)
    dr, lane = b.attr('dir'), b.attr('lane')
    speed = b.add(11.0, b.mul(b.fract(b.mul(lane, 0.731)), 6.0))
    s = b.div(b.sub(u, b.mul(b.mul(dr, speed), g['Time'])), 11.0)
    s = b.add(s, b.mul(lane, 0.379))
    cell = b.floor(s)
    rnd, rc = b.noise3(b.xyz(cell, lane, 1.3))
    present = b.lt(rnd, b.mul(g['Traffic'], 0.7))
    fs = b.fract(s)
    car = b.mul(b.band(fs, 0.1, 0.5), present)
    tc = b.node('ShaderNodeTexCoord')
    px, py, _ = b.sep(tc.outputs['Object'])
    ddx, ddy = b.sub(px, g['FocusX']), b.sub(py, g['FocusY'])
    far = b.gt(b.add(b.mul(ddx, ddx), b.mul(ddy, ddy)), b.mul(g['FocusR'], g['FocusR']))
    car = b.mul(car, far)
    # lights are two dots at each end: white at the leading end, red at the trailing end; the end facing the
    # camera is brighter (Incoming points to the viewer)
    geo = b.node('ShaderNodeNewGeometry')
    dot = b.node('ShaderNodeVectorMath', operation='DOT_PRODUCT')
    b.L.new(b.xyz(b.mul(b.attr('tx'), dr), b.mul(b.attr('ty'), dr), 0.0), dot.inputs[0])
    b.L.new(geo.outputs['Incoming'], dot.inputs[1])
    toward = b.gt(dot.outputs['Value'], 0.0)
    pos = b.gt(dr, 0.0)
    hi, lo = b.band(fs, 0.44, 0.5), b.band(fs, 0.1, 0.16)
    lead = b.add(b.mul(pos, hi), b.mul(b.sub(1.0, pos), lo))
    trail = b.add(b.mul(pos, lo), b.mul(b.sub(1.0, pos), hi))
    dots = b.band(b.math('ABSOLUTE', vlat), 0.3, 0.8)
    e_head = b.mul(lead, b.add(3.0, b.mul(toward, 12.0)))
    e_tail = b.mul(trail, b.add(2.5, b.mul(b.sub(1.0, toward), 7.0)))
    head = b.mixc(b.gt(lead, 0.5), '#FF2412', '#FFF2D6')
    em = b.mul(b.mul(b.mul(car, dots), g['Night']), b.add(e_head, e_tail))
    body = b.mixc(rc, '#20252B', '#B9BDC1')
    base = b.mixc(car, '#34363A', body)
    sh = principled(b, base, b.add(0.8, b.mul(car, -0.5)), 0.0, 0.5, head, em)
    return finish(m, b, sh)


def road_mat():
    """Road surface: UV u = metres along, v = metres across (signed); attributes hw (half width) and led (0 sodium,
    1 white). At night pools of light under the kerb lamps every 30 m, staggered on the two sides."""
    b, m = new_mat('MF_road')
    if b is None:
        return m
    g = b.glob()
    uv = b.node('ShaderNodeUVMap', uv_map='UVMap').outputs[0]
    u, v, _ = b.sep(uv)
    hw, led = b.attr('hw'), b.attr('led')
    tc = b.node('ShaderNodeTexCoord')
    nz = b.node('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = 0.35
    b.L.new(tc.outputs['Object'], nz.inputs['Vector'])
    av = b.math('ABSOLUTE', v)
    # darker wheel tracks in every lane (lanes ~3.3 m)
    tr = b.fract(b.div(av, 3.3))
    track = b.add(b.band(tr, 0.15, 0.32), b.band(tr, 0.62, 0.8))
    base = b.mixc(b.mul(nz.outputs['Fac'], 0.7), '#3D3F42', '#2B2D30')
    base = b.mixc(b.mul(track, 0.35), base, '#1F2022')
    side = b.gt(v, 0.0)
    uu = b.add(u, b.mul(side, 15.0))
    du = b.mul(b.sub(b.fract(b.div(uu, 30.0)), 0.5), 30.0)
    dv = b.sub(av, b.sub(hw, 1.2))
    pool = b.exp(b.mul(b.add(b.mul(du, du), b.mul(dv, dv)), -1.0 / 60.0))
    em = b.mul(b.mul(pool, g['Street']), 0.9)
    col = b.mixc(led, '#FF9A45', '#FFE4C2')
    sh = principled(b, base, b.add(0.62, b.mul(track, -0.2)), 0.0, 0.5, col, em)
    return finish(m, b, sh)


def sidewalk_mat(name='MF_sidewalk', color='#A29E97', tile=1.5):
    """Concrete slabs with joints (object coordinates, metres)."""
    b, m = new_mat(name)
    if b is None:
        return m
    tc = b.node('ShaderNodeTexCoord')
    x, y, _ = b.sep(tc.outputs['Object'])
    jx = b.lt(b.fract(b.div(x, tile)), 0.03)
    jy = b.lt(b.fract(b.div(y, tile)), 0.03)
    joint = b.mx(jx, jy)
    nz = b.node('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = 0.6
    b.L.new(tc.outputs['Object'], nz.inputs['Vector'])
    base = b.mixc(b.mul(nz.outputs['Fac'], 0.45), color, '#6E6B66')
    base = b.mixc(b.mul(joint, 0.6), base, '#4E4C49')
    sh = principled(b, base, 0.85)
    return finish(m, b, sh)


def paint_mat(name, rough=0.3, metal=0.0, spec=0.6, glow=0.0, gate='Neon'):
    """Colour from the corner attribute bcol (cars, awnings, sign boards); glow > 0 makes it shine with a global."""
    b, m = new_mat(name)
    if b is None:
        return m
    col = b.attr('bcol', 'Color')
    if glow:
        g = b.glob()
        sh = principled(b, col, rough, metal, spec, col, b.mul(g[gate], glow))
    else:
        sh = principled(b, col, rough, metal, spec)
    return finish(m, b, sh)


def tree_mat():
    """Tree crowns; colour varies per tree with attribute brnd."""
    b, m = new_mat('MF_tree')
    if b is None:
        return m
    r = b.attr('brnd')
    base = b.mixc(r, '#2F4A22', '#5C7432')
    base = b.mixc(b.gt(r, 0.86), base, '#7A6A2E')
    sh = principled(b, base, 0.9, 0.0, 0.3)
    return finish(m, b, sh)


def water_mat():
    b, m = new_mat('MF_water')
    if b is None:
        return m
    g = b.glob()
    tc = b.node('ShaderNodeTexCoord')
    w = b.node('ShaderNodeTexWave', wave_type='BANDS', bands_direction='X')
    w.inputs['Scale'].default_value = 0.06
    w.inputs['Distortion'].default_value = 6.0
    w.inputs['Detail'].default_value = 3.0
    nz = b.node('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = 0.35
    vm = b.node('ShaderNodeVectorMath', operation='ADD')
    b.L.new(tc.outputs['Object'], vm.inputs[0])
    b.L.new(b.xyz(g['Time'], b.mul(g['Time'], 0.6), 0.0), vm.inputs[1])
    b.L.new(vm.outputs[0], w.inputs['Vector'])
    b.L.new(vm.outputs[0], nz.inputs['Vector'])
    bump = b.node('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.12
    bump.inputs['Distance'].default_value = 0.4
    b.L.new(b.add(b.mul(w.outputs['Fac'], 0.5), nz.outputs['Fac']), bump.inputs['Height'])
    base = b.mixc(g['Night'], '#2B4250', '#0B1216')
    sh = principled(b, base, 0.04, 0.0, 1.0, normal=bump.outputs['Normal'])
    return finish(m, b, sh)


def grass_mat():
    """Lawn: big mown patches, fine clumps, dry spots; fine bump so it is not a flat green."""
    b, m = new_mat('MF_grass')
    if b is None:
        return m
    tc = b.node('ShaderNodeTexCoord')
    nz = b.node('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = 0.05
    b.L.new(tc.outputs['Object'], nz.inputs['Vector'])
    fine = b.node('ShaderNodeTexNoise')
    fine.inputs['Scale'].default_value = 3.0
    fine.inputs['Detail'].default_value = 6.0
    b.L.new(tc.outputs['Object'], fine.inputs['Vector'])
    base = b.mixc(nz.outputs['Fac'], '#33502A', '#5E7A3A')
    base = b.mixc(b.mul(fine.outputs['Fac'], 0.6), base, '#26401F')
    base = b.mixc(b.clamp01(b.mul(b.sub(nz.outputs['Fac'], 0.62), 3.0)), base, '#8A8A4E')
    bump = b.node('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.5
    bump.inputs['Distance'].default_value = 0.05
    b.L.new(fine.outputs['Fac'], bump.inputs['Height'])
    sh = principled(b, base, 0.95, normal=bump.outputs['Normal'])
    return finish(m, b, sh)


def screen_mat(name, a, c, speed=0.3):
    """Billboard screen: two colours drifting in bands, bright at night, still on by day."""
    b, m = new_mat(name)
    if b is None:
        return m
    g = b.glob()
    uv = b.node('ShaderNodeUVMap', uv_map='UVMap').outputs[0]
    u, v, _ = b.sep(uv)
    w = b.node('ShaderNodeTexWave', wave_type='BANDS', bands_direction='DIAGONAL')
    w.inputs['Scale'].default_value = 1.4
    w.inputs['Distortion'].default_value = 3.0
    b.L.new(b.xyz(b.add(u, b.mul(g['Time'], speed)), v, 0.0), w.inputs['Vector'])
    col = b.mixc(w.outputs['Fac'], a, c)
    s = b.add(1.2, b.mul(g['Neon'], 7.0))
    em = b.node('ShaderNodeEmission')
    b.L.new(col, em.inputs['Color'])
    b.L.new(s, em.inputs['Strength'])
    return finish(m, b, em.outputs[0])


def world(sky_top, sky_mid, sun_dir=None, sun_col='#FFE6C4', sun_glow=0.0, strength=1.0):
    """Sky gradient whose horizon is the city fog colour (MetroGlobals.FogColor), so the far city melts into it."""
    w = bpy.data.worlds.new('MetroSky')
    bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    b = NB(nt)
    g = b.glob()
    tc = b.node('ShaderNodeTexCoord')
    n = b.node('ShaderNodeVectorMath', operation='NORMALIZE')
    b.L.new(tc.outputs['Generated'], n.inputs[0])
    _, _, z = b.sep(n.outputs[0])
    t1 = b.clamp01(b.div(z, 0.12))
    t2 = b.clamp01(b.div(b.sub(z, 0.12), 0.6))
    c = b.node('ShaderNodeMix', data_type='RGBA')
    b.L.new(t1, c.inputs['Factor'])
    b.L.new(g['FogColor'], c.inputs[6])
    c.inputs[7].default_value = C(sky_mid)
    col = b.mixc(t2, c.outputs[2], sky_top)
    if sun_dir is not None and sun_glow:
        dv = b.node('ShaderNodeVectorMath', operation='DOT_PRODUCT')
        b.L.new(n.outputs[0], dv.inputs[0])
        dv.inputs[1].default_value = sun_dir
        glow = b.math('POWER', b.mx(dv.outputs['Value'], 0.0), 18.0)
        col = b.mixc(b.mul(glow, sun_glow), col, sun_col)
    bg = b.node('ShaderNodeBackground')
    b.L.new(col, bg.inputs['Color'])
    bg.inputs['Strength'].default_value = strength
    out = b.node('ShaderNodeOutputWorld')
    b.L.new(bg.outputs[0], out.inputs['Surface'])
    return w
