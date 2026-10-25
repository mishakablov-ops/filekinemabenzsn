"""On Mars: rusty ground and rocks under the real butterscotch sky, a habitat dome, a rover, a dish sending a slow
message home to the tiny blue dot of the Earth."""
import bpy, math, random
from mathutils import Vector
import lib
import spacekit as sk
from lib import C


def dome(loc, r=6.0, name='Dome'):
    M = sk._mats()
    root = lib.empty(name, loc)
    shell = lib.mat('DomeShell', '#E6E1D8', rough=0.55, var=0.06)
    P = [lib.sphere(r, (0, 0, 0), shell, 64, 32, scale=(1, 1, 0.72), name=name + 'Shell')]
    rib = lib.mat('DomeRib', '#A9A39A', rough=0.5, metal=0.4)
    for k in range(10):
        a = k * math.pi / 10
        ob = lib.cyl(r * 1.012, 0.12, (0, 0, 0), rib, rot=(math.pi / 2, 0, a), verts=64, cap=False, name=name + 'Rib')
        ob.scale = (1, 0.72, 1)
        P.append(ob)
    win, _ = lib.emission_mat(name + 'Win', '#FFC77A', 5.0)
    for k in range(9):
        a = -1.9 + k * 0.32
        x, y = math.cos(a) * r * 0.985, math.sin(a) * r * 0.985
        ob = lib.box((0.12, 0.9, 0.5), (x, y, 1.1), win, rot=(0, -0.25, a), bevel=0.02, name=name + 'Window')
        P.append(ob)
    P.append(lib.box((1.6, 1.4, 2.2), (math.cos(-1.2) * r, math.sin(-1.2) * r, 1.1), M['white'], rot=(0, 0, -1.2), bevel=0.1,
                     name=name + 'Airlock'))
    for ob in P:
        ob.parent = root
    return root


def rover(loc, rot, name='Rover'):
    M = sk._mats()
    root = lib.empty(name, loc, (0, 0, rot))
    body = lib.mat('RoverBody', '#E9E5DC', rough=0.45)
    P = [lib.box((3.0, 1.9, 0.8), (0, 0, 1.15), body, bevel=0.12, name=name + 'Body'),
         lib.box((3.1, 2.1, 0.06), (0, 0, 1.6), M['panel'], bevel=0.01, name=name + 'Deck'),
         lib.box((1.0, 1.7, 0.7), (1.1, 0, 1.75), M['glass'], bevel=0.18, name=name + 'Cab'),
         lib.cyl(0.05, 1.3, (-1.1, 0.7, 2.25), M['grey'], verts=8, name=name + 'Mast'),
         lib.box((0.3, 0.45, 0.25), (-1.1, 0.7, 2.95), M['white'], bevel=0.05, name=name + 'Head')]
    tire = lib.mat('Tire', '#2A2522', rough=0.9)
    for x in (-1.15, 0, 1.15):
        for s in (-1, 1):
            P.append(lib.cyl(0.42, 0.34, (x, s * 1.12, 0.42), tire, rot=(math.pi / 2, 0, 0), verts=24, bevel=0.04, name=name + 'Wheel'))
    P.append(lib.box((0.06, 0.6, 0.25), (1.52, 0, 1.1), M['win'], bevel=0.02, name=name + 'Lamp'))
    for ob in P:
        ob.parent = root
    return root


def dish(loc, aim, name='Dish'):
    M = sk._mats()
    root = lib.empty(name, loc)
    P = [lib.cyl(0.25, 2.2, (0, 0, 1.1), M['grey'], verts=16, name=name + 'Pedestal')]
    head = lib.empty(name + 'Head', (0, 0, 2.4))
    head.parent = root
    bowl = lib.cyl(2.3, 0.9, (0, 0, 0.45), M['white'], verts=48, r2=0.35, cap=False, name=name + 'Bowl')
    bowl.rotation_euler = (math.pi, 0, 0)
    bowl.parent = head
    feed = lib.cyl(0.04, 1.6, (0, 0, 0.9), M['grey'], verts=8, name=name + 'Feed')
    feed.parent = head
    tip = lib.sphere(0.12, (0, 0, 1.7), lib.emission_mat(name + 'Tip', '#9FD3FF', 12.0)[0], 12, 8, name=name + 'Tip')
    tip.parent = head
    head.rotation_mode = 'QUATERNION'
    head.rotation_quaternion = Vector(aim).normalized().to_track_quat('Z', 'Y')
    for ob in P:
        ob.parent = root
    return root, head


def build(shot, fps):
    lib.FPS = fps
    dur = shot['dur']
    ev = shot.get('events', {})
    sk.SUN_SOCKETS.clear()
    sun = (Vector((math.cos(math.radians(-150)), math.sin(math.radians(-150)), 0)) * math.cos(math.radians(24))
           + Vector((0, 0, math.sin(math.radians(24))))).normalized()
    lib.world_sky_view_gradient('#A88264', '#D8B086', '#6A4A35', strength=1.0,
                                glow_dir=sun, glow_col='#DDE3EE', glow_size=0.12, glow_strength=1.2)
    lib.fog_box((6000, 6000, 420), (0, 0, 205), density=0.0011, color='#C99A6E', aniso=0.5, name='Dust')
    sk.sun_light(sun, 2.3, '#FFF0DC', 0.35)
    gm = sk.ground_mat('MarsGround', '#8E5233', '#5C321F', '#B3734B', rough=0.95, scale=0.05, bump=0.8)
    g, field = sk.terrain(size=900, n=420, height=4.0, octaves=7, craters=28, crater_r=(2.0, 55.0), seed=33,
                          flat_center=(0, 0, 18), mat_=gm, name='MarsGround')
    mm = sk.ground_mat('MarsHills', '#94583A', '#6A3C27', '#B07650', rough=0.95, scale=0.004, bump=0.0)
    hills, _ = sk.terrain(size=9000, n=300, height=320.0, octaves=6, seed=12, ramp=(700, 2600, 0.0), mat_=mm, name='Hills', base=5)
    hills.location.z = -1.2
    cam0 = Vector((-9.5, -12.5, 1.6))
    sk.rocks(field, 260, 70, 0.06, 0.95, lib.mat('MarsRock', '#5A3423', rough=0.9, var=0.25, var_scale=2.0, bump=0.3),
             seed=4, avoid=[(-4, 4, 8), (5.5, -1.0, 3.5), (7.0, 6.0, 3.5), (cam0.x, cam0.y, 3)])
    sk.rocks(field, 160, 9, 0.03, 0.32, lib.mat('MarsPebble', '#4E2D1E', rough=0.9, var=0.3, var_scale=3.0),
             seed=9, avoid=[(cam0.x, cam0.y, 1.5), (-4, 4, 7), (5.5, -1.0, 3.0)], name='Pebble', center=(-5.0, -5.0))
    dome((-4.0, 4.0, sk.height_at(field, -4, 4) - 0.2), 6.0)
    dome((-12.5, 8.5, sk.height_at(field, -12.5, 8.5) - 0.2), 3.6, name='DomeS')
    tun = lib.cyl(1.0, 6.2, (-9.1, 6.6, 0.8), lib.mat('Tunnel', '#D7D1C6', rough=0.55), rot=(0, math.pi / 2, math.radians(-28)),
                  verts=32, name='Tunnel')
    rover((5.5, -1.0, sk.height_at(field, 5.5, -1.0)), 2.6)
    # the tiny blue Earth in the sky, the dish aims at it
    view = Vector((15.0, 19.0, 0)).normalized()
    side = Vector((-view.y, view.x, 0))
    edir = (view * math.cos(math.radians(27)) + Vector((0, 0, math.sin(math.radians(27)))) - side * 0.28).normalized()
    dpos = Vector((7.0, 6.0, sk.height_at(field, 7.0, 6.0)))
    epos = dpos + edir * 900.0
    em, _ = lib.emission_mat('EarthDot', '#7FB2FF', 40.0)
    lib.sphere(1.4, tuple(epos), em, 16, 8, name='EarthDot')
    halo, hem = lib.emission_mat('EarthHalo', '#9EC5FF', 1.0)
    try:
        halo.surface_render_method = 'BLENDED'
    except Exception:
        pass
    nt = halo.node_tree
    lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.5
    inv = nt.nodes.new('ShaderNodeMath'); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0
    nt.links.new(lw.outputs['Facing'], inv.inputs[1])
    pw = nt.nodes.new('ShaderNodeMath'); pw.operation = 'POWER'; pw.inputs[1].default_value = 5.0
    nt.links.new(inv.outputs[0], pw.inputs[0])
    sm = nt.nodes.new('ShaderNodeMath'); sm.operation = 'MULTIPLY'; sm.inputs[1].default_value = 4.0
    nt.links.new(pw.outputs[0], sm.inputs[0]); nt.links.new(sm.outputs[0], hem.inputs['Strength'])
    out = [n for n in nt.nodes if n.bl_idname == 'ShaderNodeOutputMaterial'][0]
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); add = nt.nodes.new('ShaderNodeAddShader')
    nt.links.new(tr.outputs[0], add.inputs[0]); nt.links.new(hem.outputs[0], add.inputs[1]); nt.links.new(add.outputs[0], out.inputs['Surface'])
    hb = lib.sphere(9.0, tuple(epos), halo, 24, 12, name='EarthHaloS')
    hb.visible_shadow = False
    droot, head = dish(tuple(dpos), edir)
    # message pulses: rings leaving the dish slowly towards the Earth
    pm, pem = lib.emission_mat('Pulse', '#9FD3FF', 9.0)
    t0 = ev.get('pulse', dur * 0.35)
    q = edir.to_track_quat('Z', 'Y')
    for k in range(3):
        ring = lib.cyl(1.0, 0.06, (0, 0, 0), pm, verts=64, cap=False, name=f'Pulse{k}')
        ring.rotation_mode = 'QUATERNION'
        ring.rotation_quaternion = q
        ring.visible_shadow = False
        ts = t0 + k * 0.55
        p0 = dpos + Vector((0, 0, 2.4)) + edir * 1.8
        for t, dist, sc in ((max(0.0, ts - 0.02), 0.0, 0.01), (ts, 0.0, 0.6), (ts + 3.0, 22.0, 2.4), (ts + 6.0, 40.0, 3.6)):
            ring.location = p0 + edir * dist
            ring.scale = (sc, sc, 1)
            ring.keyframe_insert('location', frame=lib.sec2f(t))
            ring.keyframe_insert('scale', frame=lib.sec2f(t))
        for fc in ring.animation_data.action.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = 'LINEAR'
    a = sk.astronaut('#E9E3D6', 'MarsAstro', pose='wave')
    a.location = (4.4, 3.3, sk.height_at(field, 4.4, 3.3))
    tc = cam0 - a.location
    a.rotation_euler = (0, 0, math.atan2(tc.y, tc.x) + math.pi / 2)
    c = lib.camera(tuple(cam0), (1.0, 2.5, 3.4), 30)
    c.data.clip_end = 20000
    lib.animate_camera(c, [(0, tuple(cam0)), (dur, (-8.0, -11.2, 1.7))], [(0, (1.0, 2.5, 3.4)), (dur, (1.6, 2.8, 3.8))])
    lib.bloom(0.2, 1.4)
    return dict(fill=0.4, exposure=0.15)
