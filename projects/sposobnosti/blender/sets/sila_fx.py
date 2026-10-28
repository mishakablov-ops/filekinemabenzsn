"""Effects for «Каждому по способности» (sposobnosti): superpowers drawn with simple emissive shapes, all from code.

Everything is keyed in seconds of the shot (lib.FPS), works in Eevee Next (transparent materials are BLENDED).
    sparks()        golden sparks raining on the city (the night everybody got a power)
    aura()          a soft coloured glow around a person (his power), fades in/out
    flash()         teleport: a white-blue burst + light
    ripple()        the hero's anti-power: an expanding translucent dome and a ring on the ground
    bolt()          lightning between two points (jagged tube, flickers)
    flame()         a small fire in a palm (flickering cones + light)
    float_glow()    telekinesis: a ring of light under a lifted object
    smoke()         a smoke column (stacked translucent puffs that rise and grow)
    rain()          falling streaks; drops near a moving point vanish (the calm around the hero)
    vortex()        a hurricane: rotating cloud rings narrowing to a funnel
    plane_model()   a passenger jet from boxes and cylinders (airport, sky)
"""
import math
import random
import bpy
from mathutils import Vector
import lib

F = lib.sec2f


def _blend(m):
    for attr, v in (('surface_render_method', 'BLENDED'), ('blend_method', 'BLEND')):
        try:
            setattr(m, attr, v)
        except Exception:
            pass
    try:
        m.use_transparency_overlap = True
    except Exception:
        pass
    return m


def glow(name, color, strength=6.0, alpha=1.0):
    """Emission (+ optional transparency) material; returns (material, strength socket, alpha socket or None)."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    em = nt.nodes.new('ShaderNodeEmission')
    em.inputs['Color'].default_value = lib.C(color)
    em.inputs['Strength'].default_value = strength
    if alpha >= 1.0:
        nt.links.new(em.outputs[0], out.inputs['Surface'])
        return m, em.inputs['Strength'], None
    tr = nt.nodes.new('ShaderNodeBsdfTransparent')
    mix = nt.nodes.new('ShaderNodeMixShader')
    mix.inputs['Fac'].default_value = alpha
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(em.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs['Surface'])
    _blend(m)
    return m, em.inputs['Strength'], mix.inputs['Fac']


def fresnel_glow(name, color, strength=4.0, alpha=0.6, power=2.5):
    """Glow that is strong at the rim and clear in the middle (bubbles, auras)."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    em = nt.nodes.new('ShaderNodeEmission')
    em.inputs['Color'].default_value = lib.C(color)
    em.inputs['Strength'].default_value = strength
    lw = nt.nodes.new('ShaderNodeLayerWeight')
    lw.inputs['Blend'].default_value = 0.5
    pw = nt.nodes.new('ShaderNodeMath'); pw.operation = 'POWER'; pw.inputs[1].default_value = 1.0 / power
    nt.links.new(lw.outputs['Facing'], pw.inputs[0])
    k = nt.nodes.new('ShaderNodeMath'); k.operation = 'MULTIPLY'; k.use_clamp = True
    nt.links.new(pw.outputs[0], k.inputs[0]); k.inputs[1].default_value = alpha
    tr = nt.nodes.new('ShaderNodeBsdfTransparent')
    mix = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(k.outputs[0], mix.inputs['Fac'])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(em.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs['Surface'])
    _blend(m)
    return m, em.inputs['Strength'], k.inputs[1]


def key(sock, keys, interp='BEZIER'):
    for t, v in keys:
        lib.key_value(sock, F(t), v, interp)


def key_scale(ob, keys):
    for t, s in keys:
        ob.scale = (s, s, s) if not isinstance(s, (tuple, list)) else s
        ob.keyframe_insert('scale', frame=F(t))


def key_loc(ob, keys, interp=None):
    for t, p in keys:
        ob.location = p
        ob.keyframe_insert('location', frame=F(t))
    if interp and ob.animation_data and ob.animation_data.action:
        for fc in ob.animation_data.action.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = interp


def key_hide(ob, keys):
    """keys: [(t, visible)] — hard switches of render visibility (constant interpolation)."""
    for t, vis in keys:
        ob.hide_render = not vis
        ob.hide_viewport = not vis
        ob.keyframe_insert('hide_render', frame=F(t))
        ob.keyframe_insert('hide_viewport', frame=F(t))


# ----------------------------------------------------------------------------- sparks
def sparks(coll, center, radius, z_top, z_bot, n, t0, t1, rng, col='#FFD27A', size=0.35, speed=(18.0, 32.0),
           strength=14.0, name='Spark'):
    """Glowing sparks falling over an area (golden 'gifts'): each a stretched droplet with a short life."""
    m, _, _ = glow(name + 'Mat', col, strength)
    base = lib.sphere(size, (0, 0, 0), m, 10, 6, scale=(1.0, 1.0, 4.0), name=name + 'Base', coll=coll)
    base.hide_render = True
    base.hide_viewport = True
    out = []
    for i in range(n):
        a, r = rng.uniform(0, 2 * math.pi), radius * math.sqrt(rng.random())
        x, y = center[0] + r * math.cos(a), center[1] + r * math.sin(a)
        v = rng.uniform(*speed)
        ts = rng.uniform(t0 - (z_top - z_bot) / v, t1)
        te = ts + (z_top - z_bot) / v
        ob = bpy.data.objects.new(f'{name}{i}', base.data)
        coll.objects.link(ob)
        ob.scale = (1, 1, 1)
        sc = rng.uniform(0.6, 1.4)
        ob.scale = (sc, sc, sc)
        key_loc(ob, [(ts, (x, y, z_top)), (te, (x, y, z_bot))], 'LINEAR')
        out.append(ob)
    return out


# ----------------------------------------------------------------------------- auras, flashes, ripples
def aura(coll, parent, col, r=0.6, z=0.9, t_on=0.0, t_off=None, strength=3.0, alpha=0.55, name='Aura', scale=(1.0, 1.0, 1.6)):
    m, s_sock, a_sock = fresnel_glow(name + 'Mat', col, strength, alpha)
    ob = lib.sphere(r, (0, 0, z), m, 24, 14, scale=scale, name=name, coll=coll)
    if parent is not None:
        ob.parent = parent
    keys = [(0, 0.0), (t_on, 0.0), (t_on + 0.35, alpha)]
    if t_off is not None:
        keys += [(t_off, alpha), (t_off + 0.3, 0.0)]
    key(a_sock, keys)
    return ob, s_sock


def flash(coll, loc, t, col='#BFE3FF', size=1.2, energy=2500.0, name='Flash'):
    m, s, a = glow(name + 'Mat', col, 12.0, alpha=0.9)
    ob = lib.sphere(1.0, loc, m, 24, 12, name=name, coll=coll)
    key_scale(ob, [(0, 0.001), (t - 0.05, 0.001), (t + 0.08, size), (t + 0.35, size * 1.4), (t + 0.5, 0.001)])
    key(a, [(0, 0.0), (t - 0.05, 0.0), (t + 0.06, 0.9), (t + 0.45, 0.0)])
    L = lib.light('POINT', loc, energy=0.0, color=col, size=0.3, name=name + 'L')
    for tt, e in ((0, 0.0), (t - 0.05, 0.0), (t + 0.06, energy), (t + 0.5, 0.0)):
        L.data.energy = e
        L.data.keyframe_insert('energy', frame=F(tt))
    return ob


def ripple(coll, center, t0, dur=1.2, rmax=9.0, col='#9FD8FF', strength=3.0, name='Ripple'):
    """The anti-power wave: a translucent dome and a thin ring on the ground expand from the hero and fade."""
    m, s, a = fresnel_glow(name + 'Mat', col, strength, 0.7)
    dome = lib.sphere(1.0, center, m, 32, 16, scale=(1, 1, 0.7), name=name + 'Dome', coll=coll)
    key_scale(dome, [(0, (0.01, 0.01, 0.007)), (t0, (0.01, 0.01, 0.007)), (t0 + dur, (rmax, rmax, rmax * 0.7))])
    key(a, [(0, 0.0), (t0, 0.0), (t0 + 0.12, 0.75), (t0 + dur * 0.7, 0.35), (t0 + dur, 0.0)])
    rm, rs, ra = glow(name + 'RingMat', col, 6.0, alpha=0.8)
    bpy.ops.mesh.primitive_torus_add(major_radius=1.0, minor_radius=0.025, major_segments=64, minor_segments=8,
                                     location=(center[0], center[1], center[2] + 0.03))
    ring = bpy.context.active_object
    ring.name = name + 'Ring'
    for c in ring.users_collection:
        c.objects.unlink(ring)
    coll.objects.link(ring)
    ring.data.materials.append(rm)
    key_scale(ring, [(0, 0.01), (t0, 0.01), (t0 + dur, rmax)])
    key(ra, [(0, 0.0), (t0, 0.0), (t0 + 0.1, 0.9), (t0 + dur, 0.0)])
    return dome, ring


# ----------------------------------------------------------------------------- lightning
def bolt_points(p0, p1, rng, segs=14, jag=0.12, branches=2):
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    side = d.cross(Vector((0, 0, 1)))
    if side.length < 1e-4:
        side = Vector((1, 0, 0))
    side.normalize()
    up = d.cross(side).normalized()
    L = d.length
    pts = []
    for i in range(segs + 1):
        t = i / segs
        w = math.sin(math.pi * t)
        pts.append(p0 + d * t + side * rng.uniform(-1, 1) * jag * L * w + up * rng.uniform(-1, 1) * jag * 0.6 * L * w)
    out = [pts]
    for b in range(branches):
        i = rng.randint(2, segs - 3)
        q0 = pts[i]
        q1 = q0 + (d.normalized() * rng.uniform(0.15, 0.3) + side * rng.uniform(-0.25, 0.25)) * L
        sub = []
        for k in range(6):
            t = k / 5
            sub.append(q0.lerp(q1, t) + side * rng.uniform(-1, 1) * 0.05 * L * math.sin(math.pi * t))
        out.append(sub)
    return out


def bolt(coll, p0, p1, times, rng, col='#CFE6FF', width=0.06, strength=40.0, light=8000.0, name='Bolt', seeds=3):
    """Lightning from p0 to p1, visible in short flickers around each time in `times` (a few shapes alternate)."""
    shapes = []
    for k in range(seeds):
        m, s, _ = glow(f'{name}Mat{k}', col, 0.0)
        lines = bolt_points(p0, p1, random.Random(rng.random()), jag=0.1 + 0.03 * k)
        ob = lib.curve_poly(f'{name}{k}', [[tuple(p) for p in l] for l in lines], bevel=width, mat_=m, coll=coll)
        shapes.append((ob, s))
    mid = (Vector(p0) + Vector(p1)) / 2
    L = lib.light('POINT', tuple(mid), energy=0.0, color=col, size=1.0, name=name + 'L')
    for k, (ob, s) in enumerate(shapes):
        keys = [(0, 0.0)]
        for j, t in enumerate(times):
            if j % seeds != k and len(times) > 1:
                continue
            keys += [(t - 0.02, 0.0), (t, strength), (t + 0.06, strength * 0.4), (t + 0.09, strength), (t + 0.16, 0.0)]
        key(s, sorted(keys), 'CONSTANT')
    lk = [(0, 0.0)]
    for t in times:
        lk += [(t - 0.02, 0.0), (t, light), (t + 0.16, 0.0)]
    for t, e in sorted(lk):
        L.data.energy = e
        L.data.keyframe_insert('energy', frame=F(t))
    return shapes, L


# ----------------------------------------------------------------------------- fire, smoke
def flame(coll, parent, loc, t_on, t_off=None, scale=1.0, rng=None, name='Flame'):
    rng = rng or random.Random(3)
    root = lib.empty(name, loc, coll=coll)
    if parent is not None:
        root.parent = parent
    parts = []
    for k, (col, r, h, st) in enumerate((('#FF7A1A', 0.09, 0.32, 9.0), ('#FFB43C', 0.06, 0.24, 14.0), ('#FFF1B0', 0.035, 0.14, 22.0))):
        m, s, _ = glow(f'{name}Mat{k}', col, st)
        c = lib.cyl(r * scale, h * scale, (0, 0, 0), m, verts=12, r2=0.0, name=f'{name}C{k}', coll=coll, origin='bottom')
        c.parent = root
        lib.add_sine(c, 'scale', 2, 0.18, rng.uniform(0.18, 0.3), rng.uniform(0, 6), offset=1.0)
        lib.add_sine(c, 'rotation_euler', 0, 0.12, rng.uniform(0.25, 0.4), rng.uniform(0, 6))
        parts.append((c, s, st))
    L = lib.light('POINT', (0, 0, 0.15 * scale), energy=60.0 * scale, color='#FF9A40', size=0.1, name=name + 'L')
    L.parent = root
    on = [(0, 0.0), (t_on, 0.0), (t_on + 0.2, 1.0)]
    if t_off is not None:
        on += [(t_off, 1.0), (t_off + 0.25, 0.0)]
    for t, v in on:
        root.scale = (max(v, 0.001),) * 3
        root.keyframe_insert('scale', frame=F(t))
        L.data.energy = 60.0 * scale * v
        L.data.keyframe_insert('energy', frame=F(t))
    return root


def smoke(coll, base, h, t0, t1, rng, col='#5E5A57', r0=3.0, n=10, rise=4.0, name='Smoke'):
    """A smoke column: puffs rising from `base` and growing; looks continuous with a few overlapping puffs."""
    m = lib.mat(name + 'Mat', col, rough=1.0)
    nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    bsdf.inputs['Alpha'].default_value = 0.55
    _blend(m)
    life = h / rise
    puffs = []
    for i in range(n):
        ts = t0 - life + i * (t1 - t0 + life) / n
        p = lib.sphere(1.0, base, m, 16, 10, name=f'{name}{i}', coll=coll)
        x, y, z = base
        drift = Vector((rng.uniform(-0.2, 0.2) * h, rng.uniform(-0.2, 0.2) * h, 0))
        key_loc(p, [(ts, (x, y, z)), (ts + life, (x + drift.x, y + drift.y, z + h))], 'LINEAR')
        key_scale(p, [(ts, r0 * 0.5), (ts + life, r0 * 2.2)])
        puffs.append(p)
    return puffs


# ----------------------------------------------------------------------------- telekinesis
def float_glow(coll, obj, t0, t1, lift=3.0, col='#9EE7FF', spin=0.35, name='Lift'):
    """Lift `obj` (root at the ground) from t0 to t1 with a soft wobble; a ring of light stays under it."""
    z0 = obj.location.z
    key_loc(obj, [(0, tuple(obj.location)), (t0, tuple(obj.location))])
    p1 = obj.location.copy()
    p1.z = z0 + lift
    key_loc(obj, [(t1, tuple(p1))])
    r0 = obj.rotation_euler.copy()
    obj.keyframe_insert('rotation_euler', frame=F(t0))
    obj.rotation_euler = (r0.x + 0.12, r0.y - 0.08, r0.z + spin)
    obj.keyframe_insert('rotation_euler', frame=F(t1 + 1.5))
    m, s, a = glow(name + 'Mat', col, 5.0, alpha=0.7)
    bpy.ops.mesh.primitive_torus_add(major_radius=2.4, minor_radius=0.05, major_segments=48, minor_segments=8,
                                     location=(obj.location.x, obj.location.y, z0 + 0.05))
    ring = bpy.context.active_object
    ring.name = name + 'Ring'
    for c in ring.users_collection:
        c.objects.unlink(ring)
    coll.objects.link(ring)
    ring.data.materials.append(m)
    key(a, [(0, 0.0), (t0 - 0.1, 0.0), (t0 + 0.3, 0.7)])
    lib.add_sine(ring, 'scale', 0, 0.06, 0.8, 0.0, offset=1.0)
    lib.add_sine(ring, 'scale', 1, 0.06, 0.8, 0.0, offset=1.0)
    return ring


# ----------------------------------------------------------------------------- rain and the calm around the hero
def rain(coll, x0, x1, y0, y1, z_top, n, rng, speed=14.0, slant=(2.0, 0.0), calm=None, calm_r=4.0, dur=6.0,
         col='#C9D6E2', name='Rain'):
    """Falling streaks over a box. `calm(t) -> (x, y)` is a moving point (the hero): drops within calm_r of it hide."""
    m, _, _ = glow(name + 'Mat', col, 1.6, alpha=0.55)
    base = lib.cyl(0.012, 0.9, (0, 0, 0), m, verts=4, name=name + 'Base', coll=coll)
    base.hide_render = True
    base.hide_viewport = True
    fall = z_top / speed
    sv = Vector((slant[0], slant[1], -speed)).normalized()
    tilt = Vector((0, 0, -1)).rotation_difference(sv).to_euler()
    drops = []
    for i in range(n):
        x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
        ph = rng.uniform(0, fall)
        ob = bpy.data.objects.new(f'{name}{i}', base.data)
        coll.objects.link(ob)
        ob.rotation_euler = tilt
        # one fall, looped (CYCLES), phase shifted
        ob.location = (x, y, z_top)
        ob.keyframe_insert('location', frame=F(-ph))
        ob.location = (x + slant[0] * fall, y + slant[1] * fall, 0.0)
        ob.keyframe_insert('location', frame=F(-ph + fall))
        for fc in ob.animation_data.action.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = 'LINEAR'
            fc.modifiers.new('CYCLES')
        if calm is not None:
            inside_prev = None
            keys = []
            steps = int(dur * 10) + 1
            for s in range(steps):
                t = s / 10
                cx, cy = calm(t)
                inside = math.hypot(x - cx, y - cy) < calm_r
                if inside != inside_prev:
                    keys.append((t, not inside))
                    inside_prev = inside
            if any(not v for _, v in keys):
                key_hide(ob, keys)
        drops.append(ob)
    return drops


# ----------------------------------------------------------------------------- hurricane
def cloud_mat(name, col='#8E959C', alpha=0.85, dark='#4E5560'):
    m = lib.mat(name, col, rough=1.0)
    bsdf = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    bsdf.inputs['Alpha'].default_value = alpha
    _blend(m)
    return m


def vortex(coll, center, z_top, z_bot, r_top, r_bot, rng, rings=9, per=26, period=6.0, col='#8E959C', name='Vortex'):
    """Rotating cloud rings, wide at the top, narrow at the bottom (a funnel). Each ring spins about the centre."""
    m = cloud_mat(name + 'Mat', col)
    pivots = []
    for k in range(rings):
        t = k / max(1, rings - 1)
        z = z_top + (z_bot - z_top) * t
        r = r_top + (r_bot - r_top) * t ** 0.7
        piv = lib.empty(f'{name}Piv{k}', (center[0], center[1], z), coll=coll)
        nn = max(8, int(per * (r / r_top) ** 0.5))
        for j in range(nn):
            a = 2 * math.pi * j / nn + rng.uniform(-0.1, 0.1)
            pr = rng.uniform(0.25, 0.4) * r * 2 * math.pi / nn * 1.6
            p = lib.sphere(1.0, (r * math.cos(a), r * math.sin(a), rng.uniform(-0.1, 0.1) * pr), m, 12, 8,
                           scale=(pr * 1.6, pr, pr * 0.55), name=f'{name}P{k}_{j}', coll=coll)
            p.rotation_euler.z = a + math.pi / 2
            p.parent = piv
        piv.rotation_euler.z = rng.uniform(0, 6.28)
        piv.keyframe_insert('rotation_euler', index=2, frame=F(0))
        piv.rotation_euler.z += 2 * math.pi * (1.0 + 1.5 * t) * 10.0 / period
        piv.keyframe_insert('rotation_euler', index=2, frame=F(10.0))
        for fc in piv.animation_data.action.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = 'LINEAR'
        pivots.append(piv)
    return pivots


def cloud_deck(coll, center, R, rng, n=60, col='#7F8892', alpha=0.9, name='Deck', spin=0.0):
    """A low storm ceiling: flattened puffs scattered over a disc of radius R around center (x, y, z);
    spins slowly if spin != 0 (rad/s)."""
    m = cloud_mat(name + 'Mat', col, alpha)
    piv = lib.empty(name, tuple(center), coll=coll)
    for i in range(n):
        a, r = rng.uniform(0, 2 * math.pi), R * math.sqrt(rng.random())
        s = rng.uniform(0.12, 0.22) * R
        p = lib.sphere(1.0, (r * math.cos(a), r * math.sin(a), rng.uniform(-0.03, 0.03) * R), m, 12, 8,
                       scale=(s * 1.4, s, s * 0.3), name=f'{name}P{i}', coll=coll)
        p.parent = piv
    if spin:
        piv.keyframe_insert('rotation_euler', index=2, frame=F(0))
        piv.rotation_euler.z = spin * 10.0
        piv.keyframe_insert('rotation_euler', index=2, frame=F(10.0))
        for fc in piv.animation_data.action.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = 'LINEAR'
    return piv


# ----------------------------------------------------------------------------- planes
def plane_model(coll, loc, heading=0.0, livery='#F2F2F0', tail='#C8282A', scale=1.0, name='Jet'):
    """A narrow-body jet (~38 m) from primitives; nose towards local -Y, like people2 and lib.car."""
    root = lib.empty(name, loc, (0, 0, heading), coll=coll)
    root.scale = (scale, scale, scale)
    body = lib.mat(name + 'Body', livery, rough=0.35)
    dark = lib.mat(name + 'Dark', '#2B3138', rough=0.3)
    tl = lib.mat(name + 'Tail', tail, rough=0.4)
    eng = lib.mat(name + 'Eng', '#B9BEC4', rough=0.3, metal=0.5)
    parts = []
    parts.append(lib.cyl(1.95, 30.0, (0, 0, 3.6), body, rot=(math.pi / 2, 0, 0), verts=28, name=name + 'Fus', coll=coll))
    parts.append(lib.sphere(1.95, (0, -15.0, 3.6), body, 24, 12, scale=(1, 2.2, 1), name=name + 'Nose', coll=coll))
    parts.append(lib.cyl(1.95, 7.0, (0, 18.4, 4.1), body, rot=(math.pi / 2 - 0.12, 0, 0), verts=28, r2=0.5, name=name + 'Aft', coll=coll))
    parts.append(lib.box((1.6, 0.6, 0.5), (0, -17.6, 4.3), dark, rot=(0.25, 0, 0), bevel=0.15, name=name + 'Cockpit', coll=coll))
    for sx in (1, -1):
        w = lib.box((15.5, 4.2, 0.35), (sx * 9.2, 1.0, 2.6), body, rot=(0, -sx * 0.06, sx * 0.42), bevel=0.1, name=name + 'Wing', coll=coll)
        parts.append(w)
        parts.append(lib.cyl(0.95, 4.2, (sx * 5.6, -2.2, 1.5), eng, rot=(math.pi / 2, 0, 0), verts=20, name=name + 'Engine', coll=coll))
        parts.append(lib.box((5.8, 2.3, 0.22), (sx * 3.4, 19.6, 4.9), body, rot=(0, 0, sx * 0.45), bevel=0.06, name=name + 'Stab', coll=coll))
        # windows: a dark band along the fuselage
        parts.append(lib.box((0.05, 22.0, 0.32), (sx * 1.93, -1.0, 4.35), dark, bevel=0.0, name=name + 'Win', coll=coll))
    parts.append(lib.box((0.35, 5.0, 6.4), (0, 19.8, 7.6), tl, rot=(-0.5, 0, 0), bevel=0.08, name=name + 'Fin', coll=coll))
    for gx, gy in ((0, -12.0), (2.3, 1.6), (-2.3, 1.6)):
        parts.append(lib.cyl(0.42, 0.35, (gx, gy, 0.42), dark, rot=(0, math.pi / 2, 0), verts=16, name=name + 'Wheel', coll=coll))
        parts.append(lib.cyl(0.12, 1.4, (gx, gy, 1.2), eng, verts=8, name=name + 'Strut', coll=coll))
    for p in parts:
        p.parent = root
    return root
