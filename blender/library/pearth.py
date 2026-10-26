"""Earth from space in real colours (NASA Blue/Black Marble, see spacekit.py). Variants:
count: the night side of Eurasia, city lights die patch by patch between events 'out' and 'done', one light stays (clip);
last:  the night side with no lights at all and one tiny light in the middle of the frame: you (still, the dot is at
       frame centre so KINEMA can point a Callout at 540, 960).
"""
import bpy, math, os
from mathutils import Vector
import lib
import spacekit as sk
import planet

if not os.path.isdir(sk.TEX):
    # the textures already live in the kosmos project on this PC; no second copy
    sk.TEX = os.path.join(os.path.dirname(lib.PROJ), 'kosmos-dlya-vseh', 'blender', 'tex', 'nasa')

MOSCOW = (37.62, 55.75)


def blackout_mask(e, scale=0.045):
    """Multiply the city lights by a noise mask that closes as the returned Value goes 0.3 -> 0.7."""
    m = e.data.materials[0]
    nt = m.node_tree
    L = nt.links
    p = nt.nodes['Principled BSDF']
    lk = p.inputs['Emission Strength'].links[0]
    src = lk.from_socket
    L.remove(lk)
    val = nt.nodes.new('ShaderNodeValue'); val.outputs[0].default_value = 0.0
    tc = nt.nodes.new('ShaderNodeTexCoord')
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = scale; nz.inputs['Detail'].default_value = 4
    L.new(tc.outputs['Object'], nz.inputs['Vector'])
    ma = nt.nodes.new('ShaderNodeMath'); ma.operation = 'MULTIPLY_ADD'
    L.new(val.outputs[0], ma.inputs[0]); ma.inputs[1].default_value = -1.5; ma.inputs[2].default_value = 0.25
    add = nt.nodes.new('ShaderNodeMath'); add.operation = 'ADD'
    L.new(nz.outputs['Fac'], add.inputs[0]); L.new(ma.outputs[0], add.inputs[1])
    k = nt.nodes.new('ShaderNodeMath'); k.operation = 'MULTIPLY'; k.use_clamp = True; k.inputs[1].default_value = 8.0
    L.new(add.outputs[0], k.inputs[0])
    out = nt.nodes.new('ShaderNodeMath'); out.operation = 'MULTIPLY'
    L.new(src, out.inputs[0]); L.new(k.outputs[0], out.inputs[1])
    L.new(out.outputs[0], p.inputs['Emission Strength'])
    return val.outputs[0]


def backlit(e, shells, sd, moon=0.05):
    """Fixes for a globe lit from behind (first PC proof): over the disc only air whose entry point is sunlit may glow
    (spacekit's hit-ray branch lit half the night disc purple), no specular (grazing reflections drew a broken white
    ring on the dark limb), and a faint moonlight from the camera side so the continents still read."""
    for sh in shells:
        nt = sh.data.materials[0].node_tree
        L = nt.links
        em = next(n for n in nt.nodes if n.bl_idname == 'ShaderNodeEmission')
        miss = next(n for n in nt.nodes if n.bl_idname == 'ShaderNodeMath' and n.operation == 'GREATER_THAN').outputs[0]
        lk = em.inputs['Strength'].links[0]
        src = lk.from_socket
        L.remove(lk)
        geo = nt.nodes.new('ShaderNodeNewGeometry')
        nn = nt.nodes.new('ShaderNodeVectorMath'); nn.operation = 'NORMALIZE'; L.new(geo.outputs['Position'], nn.inputs[0])
        dt = nt.nodes.new('ShaderNodeVectorMath'); dt.operation = 'DOT_PRODUCT'
        L.new(nn.outputs[0], dt.inputs[0]); dt.inputs[1].default_value = Vector(sd).normalized()
        mk = nt.nodes.new('ShaderNodeMapRange'); mk.interpolation_type = 'SMOOTHSTEP'
        mk.inputs['From Min'].default_value = -0.04; mk.inputs['From Max'].default_value = 0.22
        L.new(dt.outputs['Value'], mk.inputs['Value'])
        inv = nt.nodes.new('ShaderNodeMath'); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0
        L.new(miss, inv.inputs[1])
        hm = nt.nodes.new('ShaderNodeMath'); hm.operation = 'MULTIPLY'
        L.new(inv.outputs[0], hm.inputs[0]); L.new(mk.outputs['Result'], hm.inputs[1])
        f = nt.nodes.new('ShaderNodeMath'); f.operation = 'ADD'
        L.new(miss, f.inputs[0]); L.new(hm.outputs[0], f.inputs[1])
        out = nt.nodes.new('ShaderNodeMath'); out.operation = 'MULTIPLY'
        L.new(src, out.inputs[0]); L.new(f.outputs[0], out.inputs[1])
        L.new(out.outputs[0], em.inputs['Strength'])
    e.data.materials[0].node_tree.nodes['Principled BSDF'].inputs['Specular IOR Level'].default_value = 0.0
    if moon:
        lm = sk.sun_light(Vector((0.0, -1.0, 0.12)).normalized(), moon, color='#A9BEDF', name='Moonlight')
        lm.data.use_shadow = False


def last_light(spin, strength=60.0, r=0.35):
    m, _ = lib.emission_mat('LastLight', '#FFD9A0', strength)
    d = lib.sphere(r, tuple(sk.at_ll(MOSCOW[0], MOSCOW[1], 0.2)), m, 12, 8, name='LastLight')
    d.parent = spin
    return d


def count(shot):
    dur = shot['dur']
    ev = shot.get('events', {})
    sk.SUN_SOCKETS.clear()
    sk.stars(1.0, 0.8)
    sd = Vector((0.45, 0.88, 0.15)).normalized()
    e, cl, shells, spin = sk.earth(sd, night=3.2, r=sk.R, seg=(512, 256))
    lamp = sk.sun_light(sd, 4.5)
    lamp.data.use_shadow = False
    planet.facing(spin, 48.0, 42.0, 0.0, 5.0, dur)
    backlit(e, shells, sd, moon=0.03)
    prog = blackout_mask(e)
    t_out, t_done = ev.get('out', 1.2), ev.get('done', 3.2)
    lib.key_value(prog, 1, 0.3, 'LINEAR')
    lib.key_value(prog, lib.sec2f(t_out), 0.3, 'LINEAR')
    lib.key_value(prog, lib.sec2f(t_done), 0.7, 'LINEAR')
    last_light(spin)
    c = lib.camera((0, -250, 34), (0, 0, 4), 36)
    c.data.clip_end = 5000
    c.data.clip_start = 1.0
    lib.animate_camera(c, [(0, (0, -250, 34)), (dur, (0, -228, 28))], [(0, (0, 0, 4)), (dur, (0, 0, 6))])
    lib.bloom(0.3, 1.0, 8)
    return dict(fill=0.0, exposure=0.1, samples=32)


def last(shot):
    dur = shot['dur']
    sk.SUN_SOCKETS.clear()
    sk.stars(1.0, 0.8)
    sd = Vector((0.5, 0.85, 0.2)).normalized()
    e, cl, shells, spin = sk.earth(sd, night=0.0, r=sk.R, seg=(512, 256))
    lamp = sk.sun_light(sd, 4.5)
    lamp.data.use_shadow = False
    planet.facing(spin, MOSCOW[0], MOSCOW[1] - 15.0, 0.0, 0.0, dur)
    backlit(e, shells, sd, moon=0.05)
    dot = last_light(spin, strength=80.0, r=0.4)
    sc = bpy.context.scene
    sc.frame_set(1)
    bpy.context.view_layer.update()
    p = dot.matrix_world.translation.copy()
    c = lib.camera((0, -272, 6), tuple(p), 40)
    c.data.clip_end = 5000
    c.data.clip_start = 1.0
    print('LAST dot world', tuple(round(x, 2) for x in p), flush=True)
    lib.bloom(0.45, 0.9, 8)
    return dict(fill=0.0, exposure=0.15, still_t=0.5)


def build(shot, fps=60):
    lib.FPS = fps
    return {'count': count, 'last': last}[shot['variant']](shot)
