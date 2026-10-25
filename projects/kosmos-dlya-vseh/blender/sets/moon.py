"""On the Moon: grey regolith with craters, a gold-foil lander, astronauts on a 'weekend trip', the real Earth in the sky."""
import bpy, math, random
from mathutils import Vector
import lib
import spacekit as sk
from lib import C


def lander(name='Lander'):
    M = sk._mats()
    root = lib.empty(name)
    P = [lib.cyl(2.1, 1.7, (0, 0, 1.75), M['gold'], verts=8, name=name + 'Descent')]
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        top = Vector((math.cos(a) * 1.9, math.sin(a) * 1.9, 1.9))
        foot = Vector((math.cos(a) * 3.3, math.sin(a) * 3.3, 0.12))
        d = foot - top
        leg = lib.cyl(0.09, d.length, (top + foot) / 2, M['grey'], verts=10, name=name + 'Leg')
        leg.rotation_mode = 'QUATERNION'
        leg.rotation_quaternion = d.to_track_quat('Z', 'Y')
        P.append(leg)
        P.append(lib.cyl(0.42, 0.12, tuple(foot), M['grey'], verts=24, r2=0.3, name=name + 'Pad'))
    P.append(lib.box((2.6, 2.5, 1.9), (0, 0, 3.55), M['white'], bevel=0.25, name=name + 'Cabin'))
    P.append(lib.box((0.6, 0.06, 0.45), (0.6, -1.26, 3.85), M['win'], bevel=0.06, name=name + 'Window'))
    P.append(lib.box((0.6, 0.06, 0.45), (-0.4, -1.26, 3.85), M['win'], bevel=0.06, name=name + 'Window'))
    P.append(lib.box((0.9, 0.08, 1.1), (0.1, -1.26, 3.3), M['dark'], bevel=0.05, name=name + 'Hatch'))
    P.append(lib.cyl(0.04, 1.4, (0.9, 0.4, 5.1), M['grey'], verts=8, name=name + 'Mast'))
    P.append(lib.cyl(0.55, 0.2, (0.9, 0.4, 5.85), M['white'], verts=24, r2=0.08, rot=(0.6, 0, 0), name=name + 'Dish'))
    P.append(lib.box((2.62, 2.52, 0.18), (0, 0, 2.7), M['amber'], bevel=0.04, name=name + 'Band'))
    # ladder down the front leg
    for i in range(6):
        P.append(lib.box((0.6, 0.05, 0.05), (0, -1.75 - i * 0.18, 1.6 - i * 0.27), M['grey'], bevel=0, name=name + 'Rung'))
    for ob in P:
        ob.parent = root
    return root


def umbrella(loc, name='Umbrella'):
    root = lib.empty(name, loc)
    stripe = lib.mat('UmbAmber', '#E59A32', rough=0.6)
    white = lib.mat('UmbWhite', '#EEE8DC', rough=0.6)
    P = [lib.cyl(0.03, 2.2, (0, 0, 1.1), lib.mat('UmbPole', '#B9B4AA', metal=0.6, rough=0.4), verts=8, name=name + 'Pole')]
    for k in range(8):
        a0 = k * math.pi / 4
        pts = [(0, 0), (math.cos(a0) * 1.35, math.sin(a0) * 1.35), (math.cos(a0 + math.pi / 4) * 1.35, math.sin(a0 + math.pi / 4) * 1.35)]
        tri = lib.poly_prism(pts, 0.02, (0, 0, 2.05), stripe if k % 2 else white, name=name + 'Panel')
        # droop the outer edge
        for v in tri.data.vertices:
            rr = math.hypot(v.co.x, v.co.y)
            v.co.z -= 0.28 * (rr / 1.35) ** 1.5
        P.append(tri)
    for ob in P:
        ob.parent = root
    return root


def chair(loc, rot=0.0, name='Chair'):
    root = lib.empty(name, loc, (0, 0, rot))
    fr = lib.mat('ChairFrame', '#C8C2B6', metal=0.7, rough=0.35)
    cloth = lib.mat('ChairCloth', '#D98A2B', rough=0.8)
    P = [lib.box((0.55, 0.5, 0.04), (0, 0, 0.38), cloth, bevel=0.01, name=name + 'Seat'),
         lib.box((0.55, 0.04, 0.55), (0, 0.27, 0.66), cloth, rot=(-0.25, 0, 0), bevel=0.01, name=name + 'Back')]
    for sx in (-1, 1):
        P.append(lib.cyl(0.015, 0.6, (sx * 0.27, 0, 0.2), fr, rot=(0.6, 0, 0), verts=6, name=name + 'Leg'))
        P.append(lib.cyl(0.015, 0.6, (sx * 0.27, 0, 0.2), fr, rot=(-0.6, 0, 0), verts=6, name=name + 'Leg'))
    for ob in P:
        ob.parent = root
    return root


def hop(ob, base, dur, period=1.25, height=0.75, dx=(0.0, 0.0), phase=0.0):
    f1 = lib.sec2f(dur) + 2
    for f in range(1, f1 + 1, 2):
        t = (f - 1) / lib.FPS + phase
        u = (t % period) / period
        n = t / period
        z = height * 4 * u * (1 - u)
        ob.location = (base[0] + dx[0] * n, base[1] + dx[1] * n, base[2] + z)
        ob.keyframe_insert('location', frame=f)
        ob.rotation_euler = (0.12 * math.sin(2 * math.pi * u), 0, ob.rotation_euler.z)
        ob.keyframe_insert('rotation_euler', frame=f)


def build(shot, fps):
    lib.FPS = fps
    dur = shot['dur']
    sk.SUN_SOCKETS.clear()
    sk.stars(1.0, 0.35)
    cam0 = Vector((-8.5, -10.8, 1.45))
    view = Vector((8.5, 10.8, 0.0)).normalized()
    sun = (Vector((math.cos(math.radians(-62)), math.sin(math.radians(-62)), 0)) * math.cos(math.radians(11))
           + Vector((0, 0, math.sin(math.radians(11))))).normalized()
    sk.sun_light(sun, 5.0, '#FFF9F2', 0.53)
    gm = sk.ground_mat('Regolith', '#7C7871', '#55524D', '#A39E96', rough=0.98, scale=0.06, bump=0.9)
    g, field = sk.terrain(size=700, n=440, height=1.1, octaves=7, craters=190, crater_r=(0.7, 42.0), seed=21,
                          flat_center=(-3, -4, 15), mat_=gm, name='MoonGround')
    sk.rocks(field, 180, 60, 0.05, 0.55, lib.mat('MoonRock', '#6A6660', rough=0.95, var=0.2, var_scale=3.0),
             seed=8, avoid=[(0, 0, 4.5), (cam0.x, cam0.y, 3)])
    ld = lander()
    ld.location = (0, 0, sk.height_at(field, 0, 0))
    ld.rotation_euler = (0, 0, 0.5)
    # the weekend corner: umbrella, chairs, a cooler
    gz = sk.height_at(field, -5.5, -3.0)
    umbrella((-5.5, -3.0, gz))
    chair((-5.9, -3.6, gz), 0.5)
    chair((-4.9, -3.9, gz), -0.2)
    lib.box((0.55, 0.38, 0.4), (-6.6, -4.4, gz + 0.2), lib.mat('Cooler', '#2F6FA8', rough=0.5), bevel=0.05, name='Cooler')
    a1 = sk.astronaut('#ECEBE6', 'A1', pose='wave')
    a1.location = (-4.4, -4.7, gz)
    a1.rotation_euler = (0, 0, -0.75)
    a2 = sk.astronaut('#E8E4DA', 'A2')
    a2.rotation_euler = (0, 0, 2.4)
    hop(a2, (3.8, -5.5, sk.height_at(field, 3.8, -5.5)), dur, dx=(-1.1, -0.2))
    a3 = sk.astronaut('#EDE9E0', 'A3')
    a3.location = (1.6, -2.6, sk.height_at(field, 1.6, -2.6))
    a3.rotation_euler = (0, 0, -0.4)
    # footprints trail
    fp = lib.mat('Footprint', '#4C4945', rough=1.0)
    for i in range(16):
        x, y = -3.7 + i * 0.42, -4.9 + math.sin(i * 0.5) * 0.25 + (i % 2) * 0.25
        lib.box((0.3, 0.15, 0.01), (x, y, sk.height_at(field, x, y) + 0.005), fp, rot=(0, 0, 0.1), bevel=0, name='Step')
    # the Earth hanging in the black sky (real colours, a bit larger than life)
    edir = (view * math.cos(math.radians(30)) + Vector((0, 0, math.sin(math.radians(30))))).normalized()
    epos = cam0 + edir * 800.0
    e, cl, shells, spin = sk.earth(sun, night=2.0, r=40.0, loc=tuple(epos), seg=(256, 128), atmo=0.9)
    sk.face_point(spin, 15.0, 15.0, -edir)
    c = lib.camera(tuple(cam0), (-0.6, -1.0, 2.3), 30)
    c.data.clip_end = 5000
    lib.animate_camera(c, [(0, tuple(cam0)), (dur, (-7.2, -11.6, 1.5))], [(0, (-0.6, -1.0, 2.3)), (dur, (-0.2, -1.2, 2.4))])
    lib.bloom(0.15, 1.6)
    return dict(fill=0.35, exposure=0.0)
