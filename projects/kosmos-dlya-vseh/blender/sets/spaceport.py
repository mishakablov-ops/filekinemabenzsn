"""Spaceport at dusk (desert pad, crewed rocket, lattice tower, passengers) and the ascent to 100 km.
Variants: pad, ascent.
"""
import bpy, math, random
from mathutils import Vector, Quaternion, Matrix
import lib
import spacekit as sk
import people2
from lib import C


def tower(x, y, h=52.0, w=5.0, name='Tower'):
    M = sk._mats()
    steel = lib.mat('TowerSteel', '#6E5A4A', rough=0.55, metal=0.6)
    root = lib.empty(name, (x, y, 0))
    P = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            P.append(lib.box((0.35, 0.35, h), (sx * w / 2, sy * w / 2, h / 2), steel, bevel=0.02, name=name + 'Post'))
    k = 0
    for z in range(0, int(h), 4):
        for (a, b) in (((-1, -1), (1, -1)), ((1, -1), (1, 1)), ((1, 1), (-1, 1)), ((-1, 1), (-1, -1))):
            av = Vector((a[0] * w / 2, a[1] * w / 2, z + 0.1))
            bv = Vector((b[0] * w / 2, b[1] * w / 2, z + 0.1))
            P.append(_strut(av, bv, 0.12, steel, name + 'Ring'))
            # diagonal brace, alternating
            bz = Vector((b[0] * w / 2, b[1] * w / 2, z + 4.0)) if k % 2 == 0 else bv
            az = av if k % 2 == 0 else Vector((a[0] * w / 2, a[1] * w / 2, z + 4.0))
            P.append(_strut(az, bz, 0.08, steel, name + 'Brace'))
        k += 1
    # crew access arm and white room at the capsule
    P.append(lib.box((1.9, 1.6, 1.4), (3.4, 0, 43.6), steel, bevel=0.03, name=name + 'Arm'))
    P.append(lib.box((1.4, 2.4, 2.6), (5.1, 0, 44.0), M['white'], bevel=0.05, name=name + 'WhiteRoom'))
    wl, _ = lib.emission_mat('ArmWin', '#FFD9A0', 6.0)
    P.append(lib.box((1.0, 0.05, 0.7), (5.1, -1.21, 44.2), wl, bevel=0, name=name + 'ArmWin'))
    # aviation light on top
    red, _ = lib.emission_mat('AvRed', '#FF2A1A', 30.0)
    P.append(lib.sphere(0.35, (0, 0, h + 0.4), red, 12, 8, name=name + 'Beacon'))
    for ob in P:
        ob.parent = root
    pl = lib.light('POINT', (x, y, h + 0.4), energy=300, color='#FF3A22', size=0.3, name=name + 'BeaconL')
    return root


def _strut(a, b, r, m, name):
    d = b - a
    ob = lib.cyl(r, d.length, (a + b) / 2, m, verts=6, name=name)
    ob.rotation_mode = 'QUATERNION'
    ob.rotation_quaternion = d.to_track_quat('Z', 'Y')
    return ob


def pad(shot, fps):
    dur = shot['dur']
    sun_dir = Vector((-0.92, 0.38, 0.015)).normalized()
    lib.world_sky_view_gradient('#132449', '#C98863', '#221E1C', strength=1.0,
                                glow_dir=sun_dir, glow_col='#FF8E45', glow_size=0.32, glow_strength=1.7)
    lib.fog_box((2400, 2400, 160), (0, 0, 79), density=0.00045, color='#B8C3D6', aniso=0.5, name='Haze')
    s = sk.sun_light(sun_dir, 1.2, '#FFA866', 2.0)
    # desert: near ground with the pad flattened, far mountains on the horizon
    gm = sk.ground_mat('Desert', '#9C8468', '#6F5C49', '#B59C7E', rough=0.95, scale=0.02, bump=0.4)
    sk.terrain(size=1800, n=300, height=1.6, octaves=6, seed=3, flat_center=(0, 0, 90), mat_=gm, name='Desert')
    mm = sk.ground_mat('Mount', '#5D5862', '#3F3C46', '#736B73', rough=0.95, scale=0.0012, bump=0.0)
    mt, _ = sk.terrain(size=16000, n=360, height=900.0, octaves=7, seed=9, ramp=(2600, 7000, 0.0), mat_=mm, name='Mountains',
                       base=5)
    mt.location.z = -0.8
    concrete = lib.mat('Concrete', '#8F8A82', rough=0.85, var=0.18, var_scale=0.15, bump=0.1)
    asphalt = lib.mat('Asphalt', '#2A2724', rough=0.9, var=0.1, var_scale=0.3)
    amber = lib.mat('PadAmber', '#D9932E', rough=0.5)
    lib.cyl(36, 0.6, (0, 0, 0.3), concrete, verts=96, name='Pad')
    lib.cyl(22.5, 0.62, (0, 0, 0.31), amber, verts=96, name='PadRing')
    lib.cyl(21.5, 0.64, (0, 0, 0.32), concrete, verts=96, name='PadInner')
    lib.box((5.0, 70, 0.08), (0, -70, 0.04), asphalt, bevel=0, name='Walkway')
    bol, _ = lib.emission_mat('Bollard', '#FFC27A', 8.0)
    for i in range(14):
        for s_ in (-1, 1):
            lib.cyl(0.08, 0.5, (s_ * 2.9, -100 + i * 5.2, 0.25), bol, verts=10, name='Bollard')
    r = sk.rocket(46.0, 1.9)
    r.location = (0, 0, 0.64)
    tower(-7.2, 0, 52.0)
    # floodlights around the pad
    for a in (-2.2, -0.9, 0.9, 2.2):
        p = Vector((math.sin(a) * 34, -math.cos(a) * 34, 1.0))
        L = lib.light('SPOT', tuple(p), energy=60000, color='#E8EEFF', size=0.6, spot=26, blend=0.5, name='Flood', volume=0.35)
        lib.look_at(L, (0, 0, 26))
        lib.box((1.2, 0.6, 0.9), tuple(p), lib.mat('FloodBox', '#2B2B2B', rough=0.5), bevel=0.05, name='FloodBox')
    for i, y in enumerate((-95, -75, -55)):
        for s_ in (-1, 1):
            lib.cyl(0.09, 6, (s_ * 4.2, y, 3), lib.mat('Pole', '#3A3632', rough=0.6), verts=12, name='Pole')
            lib.light('POINT', (s_ * 4.2, y, 6.2), energy=900, color='#FFB772', size=0.25, name='PoleL')
            lib.sphere(0.25, (s_ * 4.2, y, 6.1), bol, 12, 8, name='PoleBulb')
    # passengers walking to the rocket (only a few hundred people have ever been to space)
    rng = random.Random(7)
    for i in range(6):
        h = rng.uniform(0.92, 1.05)
        p = people2.person((0, 0, 0), 0, h, rng, name=f'Pax{i}')
        x = (-0.9 if i % 2 else 0.9) + rng.uniform(-0.15, 0.15)
        y0 = -80.5 + i * 2.4 + rng.uniform(-0.3, 0.3)
        sp = rng.uniform(1.05, 1.25)
        people2.walk(p, sp, rng.random(), h)
        lib.move_root(p, [(x, y0, 0.08), (x * 0.6, 20, 0.08)], 0.0, sp)
    c = lib.camera((2.2, -86, 1.7), (0, 0, 20), 36)
    c.data.clip_end = 20000
    lib.animate_camera(c, [(0, (2.2, -86, 1.7)), (dur, (1.6, -79, 1.9))], [(0, (0, 0, 19)), (dur, (0, 0, 21))])
    lib.bloom(0.3, 1.2)
    return dict(fill=0.35, exposure=0.2)


def ascent(shot, fps):
    dur = shot['dur']
    RE = 48000.0
    KM = RE / 6371.0
    sk.SUN_SOCKETS.clear()
    w, sky = sk.sky_world('#2C63B9', '#C4DAF2', 1.0)
    sd = Vector((0.12, -0.75, 0.55)).normalized()
    e, cl, shells, spin = sk.earth(sd, night=0.0, r=RE, patch=(-100.0, -50.0, 0.0, 45.0, 'patch_bahamas.jpg'), haze=1.0,
                                   cloud_tex=False, cloud_scale=0.03, cloud_cover=0.46, seg=(512, 256), atmo_top=1.0155)
    csock, ssock = sk.ATMO[-1]
    up, east, north = sk.local_frame(-80.6, 28.6)
    b = math.radians(90.0)
    fwd = (east * math.sin(b) + north * math.cos(b)).normalized()
    left = up.cross(fwd).normalized()
    spin.rotation_mode = 'QUATERNION'
    spin.rotation_quaternion = Matrix((fwd, left, up)).to_quaternion()
    alt0, alt1 = 9.0, 140.0
    top = 0.0155 * 6371.0
    f1 = lib.sec2f(dur) + 2
    for f in range(1, f1 + 1, 3):
        u = (f - 1) / max(1, f1 - 1)
        alt = alt0 + (alt1 - alt0) * u ** 1.5
        spin.location = (0, 0, -(RE + alt * KM))
        spin.keyframe_insert('location', frame=f)
        csock.default_value = spin.location
        csock.keyframe_insert('default_value', frame=f)
        ssock.default_value = 2.6 * max(0.0, min(1.0, (alt - top - 2.0) / 22.0))
        ssock.keyframe_insert('default_value', frame=f)
        sky.outputs[0].default_value = max(0.0, min(1.0, 1.0 - (alt - alt0) / 46.0)) ** 1.4
        sky.outputs[0].keyframe_insert('default_value', frame=f)
    lamp = sk.sun_light(sd, 4.2)
    r = sk.rocket(46.0, 1.9)
    pl, core = sk.plume(30.0, 2.3)
    pl.parent = r
    pl.location = (0, 0, -0.9)
    fl = lib.light('POINT', (0, 0, -4), energy=16000, color='#FFB066', size=2.0, name='PlumeL')
    fl.parent = r
    rng = random.Random(2)
    for f in range(1, f1 + 1, 2):
        core.inputs['Strength'].default_value = rng.uniform(30, 48)
        core.inputs['Strength'].keyframe_insert('default_value', frame=f)
    lib.add_sine(r, 'location', 0, 0.035, 0.07)
    lib.add_sine(r, 'location', 1, 0.03, 0.09, 1.0)
    lib.key_obj(r, 1, loc=(0, 0, -4))
    lib.key_obj(r, lib.sec2f(dur), loc=(0, 0, 4))
    c = lib.camera((-40, -28, 10), (0, 0, 18), 40)
    c.data.clip_start, c.data.clip_end = 0.3, 150000
    lib.animate_camera(c, [(0, (-40, -28, 9)), (dur, (-36, -31, 12))], [(0, (0, 0, 17)), (dur, (0, 0, 19.5))])
    lib.bloom(0.4, 1.1, 8)
    return dict(fill=0.3, exposure=0.0)


def build(shot, fps):
    lib.FPS = fps
    return {'pad': pad, 'ascent': ascent}[shot['variant']](shot, fps)
