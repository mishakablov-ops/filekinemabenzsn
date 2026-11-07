"""Escalator mechanism built from code (Blender 5.2): steps on a chain loop, two wheel tracks per side,
drive sprockets, comb plates, balustrade with moving handrail, truss and machine room.

Coordinates: escalator runs along +X (up), width along Y, Z up. Bottom landing step line starts at x=0, z=0.
All animation is baked as keyframes (no Python handlers), so the .blend renders anywhere.
"""
import bpy, bmesh, math
from mathutils import Vector, Matrix, Euler

PITCH = 0.40           # chain pitch between step axles (m)
ANG = math.radians(30)
TREAD_D = PITCH * math.cos(ANG) - 0.004   # tread depth = horizontal pitch on the incline
RISE = PITCH * math.sin(ANG)
TREAD_Z = 0.30         # tread top above the step axle
REAR = Vector((-0.30, 0.0, 0.055))       # trailer wheel offset in step-local XZ (x, -, z)
WHEEL_R = 0.05
CHAIN_Y = 0.50
TRAIL_Y = 0.60
STEP_W = 1.00

# ----------------------------------------------------------------------------- tiny helpers
def srgb(h):
    h = h.lstrip('#'); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple((x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4) for x in c) + (1.0,)

_MATS = {}
def mat(name, col, rough=0.5, metal=0.0, alpha=1.0, emit=0.0, coat=0.0, transm=0.0):
    if name in _MATS and _MATS[name].name in bpy.data.materials:
        return _MATS[name]
    m = bpy.data.materials.new(name); m.use_nodes = True
    p = m.node_tree.nodes['Principled BSDF']
    c = srgb(col) if isinstance(col, str) else col
    p.inputs['Base Color'].default_value = c
    p.inputs['Roughness'].default_value = rough
    p.inputs['Metallic'].default_value = metal
    if coat: p.inputs['Coat Weight'].default_value = coat
    if transm:
        p.inputs['Transmission Weight'].default_value = transm
    if emit:
        p.inputs['Emission Color'].default_value = c
        p.inputs['Emission Strength'].default_value = emit
    if alpha < 1:
        p.inputs['Alpha'].default_value = alpha
        try: m.surface_render_method = 'BLENDED'
        except Exception: pass
        m.use_transparency_overlap = False if hasattr(m, 'use_transparency_overlap') else None
    m.diffuse_color = c
    _MATS[name] = m
    return m

def coll(name, parent=None):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    par = parent or bpy.context.scene.collection
    if c.name not in [x.name for x in par.children]:
        par.children.link(c)
    return c

def obj_from_bm(bm, name, mats, col, loc=(0, 0, 0), smooth=False):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for m in mats: me.materials.append(m)
    if smooth:
        for p in me.polygons: p.use_smooth = True
    ob = bpy.data.objects.new(name, me); ob.location = loc
    col.objects.link(ob)
    return ob

def bm_box(bm, c0, c1, mi=0):
    """axis-aligned box from corner c0 to c1, material index mi"""
    x0, y0, z0 = c0; x1, y1, z1 = c1
    vs = [bm.verts.new(v) for v in [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
                                     (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]]
    for f in [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]:
        bm.faces.new([vs[i] for i in f]).material_index = mi

def bm_cyl(bm, center, r, h, axis='Y', segs=20, mi=0):
    res = bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r, radius2=r, depth=h)
    rot = {'Y': Matrix.Rotation(math.pi / 2, 4, 'X'), 'X': Matrix.Rotation(math.pi / 2, 4, 'Y'), 'Z': Matrix()}[axis]
    bmesh.ops.transform(bm, matrix=Matrix.Translation(center) @ rot, verts=res['verts'])
    for f in {f for v in res['verts'] for f in v.link_faces}: f.material_index = mi

def bm_tube(bm, pts, prof_w, prof_h, mi=0, normal_up=True, side=(0, 1, 0)):
    """rectangular tube along a 3D polyline; `side` is the profile's width axis (kept perpendicular to the path)"""
    rings = []
    S = Vector(side).normalized()
    for i, p in enumerate(pts):
        a = pts[max(0, i - 1)]; b = pts[min(len(pts) - 1, i + 1)]
        t = (Vector(b) - Vector(a)).normalized()
        sd = (S - t * S.dot(t)).normalized()
        up = t.cross(sd).normalized() * -1
        if S.y != 0 and up.z < 0: up = -up
        p = Vector(p)
        ring = [bm.verts.new(p + sd * sx * prof_w / 2 + up * sz * prof_h / 2) for sx, sz in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        rings.append(ring)
    for r0, r1 in zip(rings, rings[1:]):
        for k in range(4):
            bm.faces.new([r0[k], r0[(k + 1) % 4], r1[(k + 1) % 4], r1[k]]).material_index = mi

# ----------------------------------------------------------------------------- the path of the step axles
class Path:
    """Closed loop of the step-chain axle, in the XZ plane.
    upper run: flat bottom landing -> concave arc -> 30 deg incline -> convex arc -> flat top landing,
    then a half circle down at the top, the return run below, a half circle up at the bottom."""
    def __init__(self, rise=3.0, land_lo=2.0, land_hi=2.4, r_lo=1.2, r_hi=1.8, drop=0.9, step=0.01):
        self.rise = rise; self.drop = drop
        pts = []
        # upper run sampled densely by x
        a = ANG
        x_lo_arc_end = r_lo * math.sin(a)
        z_lo_arc_end = r_lo * (1 - math.cos(a))
        z_hi_arc_start = rise - r_hi * (1 - math.cos(a))
        inc_len = (z_hi_arc_start - z_lo_arc_end) / math.sin(a)
        x_hi_arc_start = x_lo_arc_end + inc_len * math.cos(a)
        x_top = x_hi_arc_start + r_hi * math.sin(a)
        self.x0 = -land_lo; self.x1 = x_top + land_hi
        self.x_top = x_top
        def z_of(x):
            if x <= 0: return 0.0
            if x <= x_lo_arc_end: return r_lo - math.sqrt(max(0, r_lo * r_lo - x * x))
            if x <= x_hi_arc_start: return z_lo_arc_end + (x - x_lo_arc_end) * math.tan(a)
            if x <= x_top:
                dx = x_top - x
                return rise - (r_hi - math.sqrt(max(0, r_hi * r_hi - dx * dx)))
            return rise
        self.z_of = z_of
        n = int((self.x1 - self.x0) / step)
        upper = [Vector((self.x0 + i * (self.x1 - self.x0) / n, 0, z_of(self.x0 + i * (self.x1 - self.x0) / n))) for i in range(n + 1)]
        R = drop / 2
        top = [Vector((self.x1 + R * math.sin(math.pi * k / 60), 0, rise - R + R * math.cos(math.pi * k / 60))) for k in range(1, 60)]
        lower = [Vector((p.x, 0, p.z - drop)) for p in reversed(upper)]
        bot = [Vector((self.x0 - R * math.sin(math.pi * k / 60), 0, -R - R * math.cos(math.pi * k / 60))) for k in range(1, 60)]
        self.segs = [('up', upper), ('top', top), ('low', lower), ('bot', bot)]
        P = []; tags = []
        for tag, seg in self.segs:
            for i, p in enumerate(seg):
                u = i / max(1, len(seg) - 1)
                P.append(p); tags.append((tag, u))
        self.P = P; self.tags = tags
        S = [0.0]
        for i in range(1, len(P)):
            S.append(S[-1] + (P[i] - P[i - 1]).length)
        self.L = S[-1] + (P[0] - P[-1]).length
        self.S = S
        self.n_steps = int(self.L // PITCH)
        self.pitch = self.L / self.n_steps   # make the loop close exactly

    def at(self, s):
        """position and step rotation (about +Y) at arclength s"""
        s = s % self.L
        import bisect
        i = bisect.bisect_right(self.S, s) - 1
        i = max(0, min(i, len(self.P) - 1))
        j = (i + 1) % len(self.P)
        s0 = self.S[i]; s1 = self.S[i + 1] if i + 1 < len(self.S) else self.L
        t = (s - s0) / max(1e-9, s1 - s0)
        p = self.P[i].lerp(self.P[j], t)
        tag, u = self.tags[i]
        if tag == 'up': th = 0.0
        elif tag == 'top': th = math.pi * (u + t / 59.0)
        elif tag == 'low': th = math.pi
        else: th = math.pi + math.pi * (u + t / 59.0)
        return p, th

# ----------------------------------------------------------------------------- one step (local: origin = front axle)
def step_mesh(name, col, M):
    bm = bmesh.new()
    d = TREAD_D; w = STEP_W
    # tread plate
    bm_box(bm, (-d, -w / 2, TREAD_Z - 0.035), (-0.004, w / 2, TREAD_Z - 0.012), 0)
    # cleats (ribs along X)
    n = 46
    for k in range(n):
        y = -w / 2 + 0.03 + k * (w - 0.06) / (n - 1)
        bm_box(bm, (-d + 0.002, y - 0.004, TREAD_Z - 0.012), (-0.006, y + 0.004, TREAD_Z), 0)
    # yellow demarcation: side bands + front band
    bm_box(bm, (-d, -w / 2, TREAD_Z - 0.011), (-0.004, -w / 2 + 0.035, TREAD_Z + 0.001), 1)
    bm_box(bm, (-d, w / 2 - 0.035, TREAD_Z - 0.011), (-0.004, w / 2, TREAD_Z + 0.001), 1)
    bm_box(bm, (-0.045, -w / 2, TREAD_Z - 0.011), (-0.004, w / 2, TREAD_Z + 0.0015), 1)
    # riser: cleated plate hanging from the rear edge, slightly curved
    seg = 6
    for k in range(seg):
        z0 = TREAD_Z - 0.035 - (RISE + 0.01) * k / seg
        z1 = TREAD_Z - 0.035 - (RISE + 0.01) * (k + 1) / seg
        x0 = -d + 0.012 * math.sin(math.pi * k / seg)
        x1 = -d + 0.012 * math.sin(math.pi * (k + 1) / seg)
        bm_box(bm, (min(x0, x1) - 0.006, -w / 2 + 0.01, z1), (max(x0, x1) + 0.006, w / 2 - 0.01, z0), 0)
    for k in range(30):
        y = -w / 2 + 0.04 + k * (w - 0.08) / 29
        bm_box(bm, (-d - 0.012, y - 0.004, TREAD_Z - RISE - 0.03), (-d - 0.004, y + 0.004, TREAD_Z - 0.04), 0)
    # side brackets (frame) from tread to both axles
    for sy in (-1, 1):
        y0 = sy * (w / 2 - 0.02)
        bm_box(bm, (-d + 0.02, min(y0, y0 - sy * 0.02), 0.02), (-0.03, max(y0, y0 - sy * 0.02), TREAD_Z - 0.035), 2)
        # axle stubs and wheels
        bm_cyl(bm, Vector((0, sy * (CHAIN_Y - 0.03), 0)), 0.018, 0.08, 'Y', 12, 2)
        bm_cyl(bm, Vector((0, sy * CHAIN_Y, 0)), WHEEL_R, 0.035, 'Y', 24, 3)
        bm_cyl(bm, Vector((REAR.x, sy * (TRAIL_Y - 0.06), REAR.z)), 0.016, 0.14, 'Y', 12, 2)
        bm_cyl(bm, Vector((REAR.x, sy * TRAIL_Y, REAR.z)), WHEEL_R, 0.035, 'Y', 24, 4)
    # main axle across
    bm_cyl(bm, Vector((0, 0, 0)), 0.02, CHAIN_Y * 2 - 0.08, 'Y', 12, 2)
    ob = obj_from_bm(bm, name, [M['alu'], M['yellow'], M['steel'], M['wheel_a'], M['wheel_b']], col)
    return ob

def chain_link_mesh(col, M):
    bm = bmesh.new()
    L = 1.0  # scaled per link along X later
    bm_box(bm, (-0.5, -0.008, -0.022), (0.5, 0.008, 0.022), 0)
    ob = obj_from_bm(bm, 'ChainLinkProto', [M['chain']], col)
    return ob.data

# ----------------------------------------------------------------------------- build
def materials():
    return dict(
        alu=mat('EskAlu', '#B9BEC3', rough=0.32, metal=0.85),
        yellow=mat('EskYellow', '#F2C200', rough=0.45),
        steel=mat('EskSteel', '#5A6068', rough=0.4, metal=0.7),
        wheel_a=mat('EskWheelChain', '#2BB24C', rough=0.45),     # chain wheels: green (highlight colour)
        wheel_b=mat('EskWheelTrail', '#FF8A00', rough=0.45),     # trailer wheels: orange
        rail_a=mat('EskRailChain', '#1E8F3C', rough=0.35, metal=0.4),
        rail_b=mat('EskRailTrail', '#E07000', rough=0.35, metal=0.4),
        chain=mat('EskChain', '#3A3F46', rough=0.35, metal=0.8),
        truss=mat('EskTruss', '#2E3238', rough=0.5, metal=0.6),
        cut=mat('EskCut', '#D8262C', rough=0.55),
        glass=mat('EskGlass', '#DDEFF5', rough=0.05, alpha=0.18),
        handrail=mat('EskHandrail', '#111214', rough=0.35),
        print=mat('EskHandrailPrint', '#F4F4F4', rough=0.4),
        comb=mat('EskComb', '#F2C200', rough=0.4, metal=0.2),
        plate=mat('EskPlate', '#9EA4AA', rough=0.35, metal=0.8),
        motor=mat('EskMotor', '#1F57C8', rough=0.35, coat=0.6),
        gear=mat('EskGear', '#C9CDD2', rough=0.25, metal=0.9),
        skirt=mat('EskSkirt', '#C5CACF', rough=0.25, metal=0.9),
    )

class Escalator:
    def __init__(self, origin=(0, 0, 0), rise=3.0, name='Esk', cutaway=True, glass_truss=True, machine=True,
                 balustrade=True, land_lo=2.0, land_hi=2.4, truss=True, chain=True, rails=True, sprockets=True,
                 glass=True, prints=True):
        self.origin = Vector(origin)
        self.name = name
        self.col = coll(name)
        self.M = materials()
        self.path = Path(rise=rise, land_lo=land_lo, land_hi=land_hi)
        self.root = bpy.data.objects.new(name + 'Root', None)
        self.root.location = self.origin
        self.col.objects.link(self.root)
        self.opt = dict(glass=glass, prints=prints)
        self.links = []; self.sprockets = []; self.prints = []
        self._build_steps()
        if chain: self._build_chain()
        if rails: self._build_rails()
        if sprockets: self._build_sprockets()
        self._build_landings()
        if balustrade: self._build_balustrade()
        if truss: self._build_truss(cutaway, glass_truss)
        if machine: self._build_machine()

    def _parent(self, ob):
        ob.parent = self.root
        return ob

    def _build_steps(self):
        proto = step_mesh(self.name + 'StepProto', self.col, self.M)
        self.steps = [proto]
        self._parent(proto)
        for i in range(1, self.path.n_steps):
            ob = proto.copy()   # linked mesh
            ob.name = f'{self.name}Step{i:03d}'
            self.col.objects.link(ob); self._parent(ob)
            self.steps.append(ob)

    def _build_chain(self):
        me = chain_link_mesh(self.col, self.M)
        bpy.data.objects.remove(bpy.data.objects['ChainLinkProto'])
        self.links = []
        for i in range(self.path.n_steps):
            for sy in (-1, 1):
                ob = bpy.data.objects.new(f'{self.name}Link{i:03d}{"L" if sy < 0 else "R"}', me)
                ob['side'] = sy
                self.col.objects.link(ob); self._parent(ob)
                self.links.append((i, sy, ob))

    def _build_rails(self):
        P = self.path
        bm = bmesh.new()
        # chain track: follows the axle path on the working (up) and return (low) runs, under the wheel
        for tag, seg in P.segs:
            if tag not in ('up', 'low'): continue
            pts = seg[::6]
            for sy in (-1, 1):
                rp = [Vector((p.x, sy * CHAIN_Y, p.z - WHEEL_R - 0.012)) if tag == 'up' else
                      Vector((p.x, sy * CHAIN_Y, p.z + WHEEL_R + 0.012)) for p in pts]
                bm_tube(bm, rp, 0.05, 0.022, 0)
        # trailer track: trajectory of the rear wheel
        for tag, seg in P.segs:
            if tag not in ('up', 'low'): continue
            th = 0.0 if tag == 'up' else math.pi
            rot = Matrix.Rotation(th, 3, 'Y')
            off = rot @ Vector((REAR.x, 0, REAR.z))
            pts = [p + off for p in seg[::6]]
            # trim ends so the track stops before the sprockets
            pts = [p for p in pts if P.x0 + 0.25 < p.x < P.x1 - 0.25]
            for sy in (-1, 1):
                rp = [Vector((p.x, sy * TRAIL_Y, p.z - WHEEL_R - 0.012)) if tag == 'up' else
                      Vector((p.x, sy * TRAIL_Y, p.z + WHEEL_R + 0.012)) for p in pts]
                bm_tube(bm, rp, 0.05, 0.022, 1)
        self.rails = self._parent(obj_from_bm(bm, self.name + 'Rails', [self.M['rail_a'], self.M['rail_b']], self.col))

    def _gear(self, name, r, teeth, width, m):
        bm = bmesh.new()
        bm_cyl(bm, Vector((0, 0, 0)), r * 0.92, width, 'Y', 48, 0)
        for k in range(teeth):
            a = 2 * math.pi * k / teeth
            c = Vector((math.cos(a) * r * 0.96, 0, math.sin(a) * r * 0.96))
            res = bmesh.ops.create_cube(bm, size=1.0)
            bmesh.ops.transform(bm, matrix=Matrix.Translation(c) @ Matrix.Rotation(-a, 4, 'Y') @
                                Matrix.Diagonal((r * 0.16, width, r * 0.09, 1)), verts=res['verts'])
        # spokes / hub holes look
        bm_cyl(bm, Vector((0, 0, 0)), r * 0.25, width * 1.6, 'Y', 24, 0)
        return obj_from_bm(bm, name, [m], self.col, smooth=False)

    def _build_sprockets(self):
        P = self.path; R = P.drop / 2
        self.sprockets = []
        for (cx, cz, nm) in ((P.x1, P.rise - R, 'Top'), (P.x0, -R, 'Bot')):
            for sy in (-1, 1):
                g = self._gear(f'{self.name}Sprocket{nm}{sy}', R, 16, 0.05, self.M['gear'])
                g.location = (cx, sy * CHAIN_Y, cz)
                self._parent(g)
                self.sprockets.append(g)
            shaft = bmesh.new(); bm_cyl(shaft, Vector((cx, 0, cz)), 0.06, CHAIN_Y * 2 + 0.3, 'Y', 24, 0)
            self._parent(obj_from_bm(shaft, f'{self.name}Shaft{nm}', [self.M['steel']], self.col))

    def _build_landings(self):
        P = self.path; M = self.M
        bm = bmesh.new()
        w = STEP_W / 2 + 0.25
        tz = TREAD_Z
        # floor plates beyond the comb, bottom and top
        bm_box(bm, (P.x0 - 1.6, -w, tz - 0.03), (P.x0 + 0.55, w, tz + 0.012), 0)
        bm_box(bm, (P.x1 - 0.55, -w, P.rise + tz - 0.03), (P.x1 + 1.6, w, P.rise + tz + 0.012), 0)
        self._parent(obj_from_bm(bm, self.name + 'Landings', [M['plate']], self.col))
        # comb plates with teeth that enter the cleat grooves
        bm = bmesh.new()
        for (x, z, d) in ((P.x0 + 0.55, tz, 1), (P.x1 - 0.55, P.rise + tz, -1)):
            bm_box(bm, (x - (0.10 if d > 0 else 0.0), -STEP_W / 2, z - 0.02), (x + (0.0 if d > 0 else 0.10), STEP_W / 2, z + 0.03), 0)
            n = 46
            for k in range(n):
                y = -STEP_W / 2 + 0.03 + k * (STEP_W - 0.06) / (n - 1)
                tip = x + d * 0.09
                bm_box(bm, (min(x, tip), y - 0.003, z - 0.004), (max(x, tip), y + 0.003, z + 0.012), 0)
        self.combs = self._parent(obj_from_bm(bm, self.name + 'Combs', [M['comb']], self.col))

    def _rail_line(self, h, y):
        """handrail line along the escalator at height h above the tread line"""
        P = self.path
        pts = []
        xs = [P.x0 - 0.6 + i * 0.05 for i in range(int((P.x1 - P.x0 + 1.2) / 0.05) + 1)]
        for x in xs:
            pts.append(Vector((x, y, P.z_of(min(max(x, P.x0), P.x1)) + TREAD_Z + h)))
        return pts

    def _build_balustrade(self):
        P = self.path; M = self.M
        self.handrail_pts = {}
        for sy in (-1, 1):
            y = sy * (STEP_W / 2 + 0.06)
            # skirt panel (shiny, low)
            bm = bmesh.new()
            pts = self._rail_line(0.0, y)
            for a, b in zip(pts[::4], pts[4::4]):
                v = [bm.verts.new((a.x, y, a.z - 0.25)), bm.verts.new((b.x, y, b.z - 0.25)),
                     bm.verts.new((b.x, y, b.z + 0.12)), bm.verts.new((a.x, y, a.z + 0.12))]
                bm.faces.new(v)
            self._parent(obj_from_bm(bm, f'{self.name}Skirt{sy}', [M['skirt']], self.col))
            # glass panel
            bm = bmesh.new()
            for a, b in zip(pts[::4], pts[4::4]):
                v = [bm.verts.new((a.x, y, a.z + 0.12)), bm.verts.new((b.x, y, b.z + 0.12)),
                     bm.verts.new((b.x, y, b.z + 0.86)), bm.verts.new((a.x, y, a.z + 0.86))]
                bm.faces.new(v)
            if self.opt['glass']:
                g = self._parent(obj_from_bm(bm, f'{self.name}Glass{sy}', [M['glass']], self.col))
                g.visible_shadow = False
            else:
                bm.free()
            # handrail (top run) as tube
            top = [Vector((p.x, y, p.z + 0.92)) for p in pts]
            bm = bmesh.new(); bm_tube(bm, top, 0.08, 0.045, 0)
            # return run of the handrail below the steps (inside truss)
            ret = [Vector((p.x, y, p.z - 0.55)) for p in reversed(pts)]
            bm_tube(bm, ret, 0.08, 0.045, 0)
            # round newel ends
            for p0, p1, cx in ((top[0], ret[-1], P.x0 - 0.6), (top[-1], ret[0], P.x1 + 0.6)):
                R = (p0.z - p1.z) / 2
                cz = (p0.z + p1.z) / 2
                sgn = -1 if cx < P.x0 else 1
                arc = [Vector((cx + sgn * R * math.sin(math.pi * k / 24) * 0.35, y, cz + R * math.cos(math.pi * k / 24))) for k in range(25)]
                bm_tube(bm, arc, 0.08, 0.045, 0)
            self._parent(obj_from_bm(bm, f'{self.name}Handrail{sy}', [M['handrail']], self.col))
            self.handrail_pts[sy] = top
        # moving prints on the handrail (white marks) -> show it moves with the steps
        self.prints = []
        if not self.opt['prints']:
            return
        bmp = bmesh.new(); bm_box(bmp, (-0.06, -0.035, -0.002), (0.06, 0.035, 0.002), 0)
        pme = bpy.data.meshes.new(self.name + 'PrintMesh'); bmp.to_mesh(pme); bmp.free(); pme.materials.append(M['print'])
        for sy in (-1, 1):
            for k in range(60):
                ob = bpy.data.objects.new(f'{self.name}Print{sy}_{k:02d}', pme)
                self.col.objects.link(ob); self._parent(ob)
                self.prints.append((sy, k, ob))

    def _build_truss(self, cutaway, glass):
        """side truss: lattice of beams under the steps; the camera-side (-Y) panel is cut away with red cut faces"""
        P = self.path; M = self.M
        bm = bmesh.new()
        for sy in (-1, 1):
            y = sy * (STEP_W / 2 + 0.32)
            top = [Vector((x, y, P.z_of(x) - 0.25)) for x in [P.x0 - 1.4 + i * 0.1 for i in range(int((P.x1 - P.x0 + 2.8) / 0.1))]]
            bot = [Vector((p.x, y, p.z - P.drop - 0.75)) for p in top]
            bm_tube(bm, top, 0.08, 0.10, 0)
            bm_tube(bm, bot, 0.08, 0.10, 0)
            for i in range(0, len(top), 8):
                a, b = top[i], bot[i]
                bm_tube(bm, [a, b], 0.06, 0.06, 0)
                if i + 8 < len(top):
                    bm_tube(bm, [a, bot[i + 8]], 0.04, 0.04, 0)
        self._parent(obj_from_bm(bm, self.name + 'Truss', [M['truss']], self.col))
        # bottom cover (far side panel only, so the camera on -Y sees inside)
        bm = bmesh.new()
        y = STEP_W / 2 + 0.36
        xs = [P.x0 - 1.4 + i * 0.2 for i in range(int((P.x1 - P.x0 + 2.8) / 0.2) + 1)]
        for a, b in zip(xs, xs[1:]):
            za, zb = P.z_of(a), P.z_of(b)
            v = [bm.verts.new((a, y, za - P.drop - 0.8)), bm.verts.new((b, y, zb - P.drop - 0.8)),
                 bm.verts.new((b, y, zb + 0.05)), bm.verts.new((a, y, za + 0.05))]
            bm.faces.new(v)
        self._parent(obj_from_bm(bm, self.name + 'FarPanel', [mat('EskPanel', '#E9ECEF', rough=0.6)], self.col))
        if cutaway:
            # red cut edge along the near side (like a sliced model)
            bm = bmesh.new()
            y = -(STEP_W / 2 + 0.36)
            top = [Vector((x, y, P.z_of(x) + 0.12)) for x in xs]
            bot = [Vector((p.x, y, p.z - P.drop - 0.92)) for p in top]
            bm_tube(bm, top, 0.03, 0.06, 0)
            bm_tube(bm, bot, 0.03, 0.06, 0)
            self._parent(obj_from_bm(bm, self.name + 'CutEdge', [M['cut']], self.col))

    def _build_machine(self):
        """machine room under the top landing: motor -> gearbox -> drive chain -> main shaft; handrail drive wheel"""
        P = self.path; M = self.M; R = P.drop / 2
        cx, cz = P.x1, P.rise - R
        bm = bmesh.new()
        mx, mz = cx + 0.95, cz - 0.55
        bm_cyl(bm, Vector((mx, 0.0, mz)), 0.22, 0.55, 'Y', 32, 0)               # motor body
        for k in range(10):                                                     # cooling fins
            bm_cyl(bm, Vector((mx, -0.25 + k * 0.055, mz)), 0.245, 0.012, 'Y', 32, 0)
        bm_box(bm, (mx - 0.25, 0.30, mz - 0.25), (mx + 0.25, 0.62, mz + 0.22), 1)  # gearbox
        bm_box(bm, (mx - 0.35, -0.4, mz - 0.32), (mx + 0.35, 0.7, mz - 0.24), 2)  # base
        self.motor = self._parent(obj_from_bm(bm, self.name + 'Motor', [M['motor'], mat('EskGearbox', '#2B2F35', rough=0.4, metal=0.5), M['steel']], self.col, smooth=True))
        # drive chain loop between motor sprocket and main shaft
        g1 = self._gear(self.name + 'MotorSprocket', 0.12, 12, 0.04, M['gear']); g1.location = (mx, 0.68, mz); self._parent(g1)
        g2 = self._gear(self.name + 'DriveSprocket', 0.30, 24, 0.04, M['gear']); g2.location = (cx, 0.68, cz); self._parent(g2)
        self.drive = (g1, g2)
        bm = bmesh.new()
        a = Vector((mx, 0.68, mz)); b = Vector((cx, 0.68, cz))
        d = (b - a); n = Vector((-d.z, 0, d.x)).normalized()
        bm_tube(bm, [a + n * 0.12, b + n * 0.30], 0.03, 0.02, 0)
        bm_tube(bm, [a - n * 0.12, b - n * 0.30], 0.03, 0.02, 0)
        self._parent(obj_from_bm(bm, self.name + 'DriveChain', [M['chain']], self.col))
        # handrail drive wheels (friction wheels pressing the handrail return run)
        self.hr_wheels = []
        for sy in (-1, 1):
            y = sy * (STEP_W / 2 + 0.06)
            hw = self._gear(f'{self.name}HRWheel{sy}', 0.16, 20, 0.06, mat('EskRubber', '#202224', rough=0.7))
            x = P.x1 - 1.2
            hw.location = (x, y, P.z_of(x) + TREAD_Z - 0.55 - 0.18)
            self._parent(hw); self.hr_wheels.append(hw)

    # ------------------------------------------------------------------------- animation
    def pose(self, s=0.0):
        """place the steps once (no keyframes): for far / still shots"""
        P = self.path
        for i, ob in enumerate(self.steps):
            p, th = P.at(s + i * P.pitch)
            ob.location = p; ob.rotation_euler = (0, th, 0)

    def animate(self, f0, f1, fps, speed=0.75, s0=0.0, every=1):
        """bake positions for frames f0..f1; speed in m/s along the chain"""
        P = self.path
        pitch = P.pitch
        R = P.drop / 2
        for f in list(range(f0, f1 + 1, every)) + ([f1] if (f1 - f0) % every else []):
            t = (f - f0) / fps
            s = s0 + speed * t
            for i, ob in enumerate(self.steps):
                p, th = P.at(s + i * pitch)
                ob.location = p
                ob.rotation_euler = (0, th, 0)
                ob.keyframe_insert('location', frame=f)
                ob.keyframe_insert('rotation_euler', frame=f)
            for (i, sy, ob) in self.links:
                a, _ = P.at(s + i * pitch); b, _ = P.at(s + (i + 1) * pitch)
                d = b - a
                ob.location = (a + b) / 2 + Vector((0, sy * (CHAIN_Y - 0.035), 0))
                ob.rotation_euler = (0, -math.atan2(d.z, d.x), 0)
                ob.scale = (d.length, 1, 1)
                ob.keyframe_insert('location', frame=f); ob.keyframe_insert('rotation_euler', frame=f)
                ob.keyframe_insert('scale', frame=f)
            ang = -(s / R)
            for g in self.sprockets:
                g.rotation_euler = (0, ang, 0); g.keyframe_insert('rotation_euler', frame=f)
            if hasattr(self, 'drive'):
                g1, g2 = self.drive
                g2.rotation_euler = (0, ang, 0); g2.keyframe_insert('rotation_euler', frame=f)
                g1.rotation_euler = (0, ang * 0.30 / 0.12, 0); g1.keyframe_insert('rotation_euler', frame=f)
                for hw in self.hr_wheels:
                    hw.rotation_euler = (0, s / 0.16, 0); hw.keyframe_insert('rotation_euler', frame=f)
            if self.prints:
                for (sy, k, ob) in self.prints:
                    pts = self.handrail_pts[sy]
                    Ltop = sum((b - a).length for a, b in zip(pts, pts[1:]))
                    u = (s + k * Ltop / 30.0) % (2 * Ltop)
                    if u < Ltop:
                        acc = 0.0
                        for a, b in zip(pts, pts[1:]):
                            seg = (b - a).length
                            if acc + seg >= u:
                                q = a.lerp(b, (u - acc) / seg); dd = b - a; break
                            acc += seg
                        ob.location = q + Vector((0, 0, 0.024)); ob.rotation_euler = (0, -math.atan2(dd.z, dd.x), 0)
                        ob.scale = (1, 1, 1)
                    else:
                        ob.scale = (0, 0, 0)
                    ob.keyframe_insert('location', frame=f); ob.keyframe_insert('rotation_euler', frame=f)
                    ob.keyframe_insert('scale', frame=f)
        linear_all(self.col)

def linear_all(col):
    """set every keyframe in the collection to LINEAR (works with 4.x and 5.x layered actions)"""
    for ob in col.all_objects:
        ad = ob.animation_data
        if not ad or not ad.action: continue
        for fc in iter_fcurves(ad.action):
            for kp in fc.keyframe_points:
                kp.interpolation = 'LINEAR'

def iter_fcurves(action):
    if hasattr(action, 'layers') and len(action.layers):
        for lay in action.layers:
            for st in lay.strips:
                for cb in getattr(st, 'channelbags', []):
                    for fc in cb.fcurves:
                        yield fc
    elif hasattr(action, 'fcurves'):
        for fc in action.fcurves:
            yield fc
