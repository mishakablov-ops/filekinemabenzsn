"""Low-orbit shots over the real-colour Earth (NASA Blue Marble / Black Marble).

Craft and people are in metres near the origin. The Earth is a sphere of RE units placed below, so that its angular
size and horizon dip match a 400 km orbit; the camera moves only metres, so the Earth parallax stays tiny.
World frame after placing the Earth: +X = flight direction, +Y = left, +Z = local up.
Variants: hook, sunrise, eva, jam, dream, dump.
"""
import bpy, math, random
from mathutils import Vector, Matrix, Quaternion
import lib
import spacekit as sk
from lib import C

RE = 48000.0
KM = RE / 6371.0
OMEGA = 7.66 / 6771.0          # orbital angular rate, rad/s

# sharper crops of the 21600 px Blue Marble (cut by the job with ffmpeg): (lon0, lon1, lat0, lat1, file)
PATCH = {
    'bahamas': (-100.0, -50.0, 0.0, 45.0, 'patch_bahamas.jpg'),
    'egypt': (10.0, 60.0, 0.0, 45.0, 'patch_egypt.jpg'),
    'usa': (-125.0, -65.0, 15.0, 55.0, 'patch_usa.jpg'),
    'iberia': (-30.0, 30.0, 20.0, 60.0, 'patch_iberia.jpg'),
}


def sdir(az, el):
    """Direction from azimuth (deg, from +X towards +Y = left) and elevation (deg)."""
    a, e = math.radians(az), math.radians(el)
    return Vector((math.cos(e) * math.cos(a), math.cos(e) * math.sin(a), math.sin(e)))


def dip(alt_km=400.0):
    return math.degrees(math.acos(6371.0 / (6371.0 + alt_km)))


def globe_below(lon, lat, bearing, dur, sun, alt_km=400.0, speed=1.0, patch=None, night=2.2, atmo=1.0, sat=1.1,
                stars=0.7, sun_energy=4.5, shine=0.45, **kw):
    """Earth under the camera: (lon, lat) straight below, flying towards `bearing` (deg from north, clockwise)."""
    alt = alt_km * KM
    sk.SUN_SOCKETS.clear()
    sk.stars(1.0, stars)
    sd = Vector(sun).normalized()
    e, cl, shells, spin = sk.earth(sd, night=night, r=RE, loc=(0, 0, -(RE + alt)), patch=PATCH.get(patch), atmo=atmo,
                                   sat=sat, seg=(512, 256), **kw)
    up, east, north = sk.local_frame(lon, lat)
    b = math.radians(bearing)
    fwd = (east * math.sin(b) + north * math.cos(b)).normalized()
    left = up.cross(fwd).normalized()
    M = Matrix((fwd, left, up))
    q0 = M.to_quaternion()
    spin.rotation_mode = 'QUATERNION'
    f1 = lib.sec2f(dur) + 2
    for f in (1, f1):
        t = (f - 1) / lib.FPS
        spin.rotation_quaternion = Quaternion((0, 1, 0), -OMEGA * speed * t) @ q0
        spin.keyframe_insert('rotation_quaternion', frame=f)
    for fc in spin.animation_data.action.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = 'LINEAR'
    lamp = sk.sun_light(sd, energy=sun_energy)
    lamp.data.use_shadow = False          # Earth thousands of units away overflows Eevee's shadow pool
    if shine:
        sk.earthshine(Vector((0, 0, -1)), shine)
    return dict(earth=e, clouds=cl, shells=shells, spin=spin, sun=lamp, sun_dir=sd, alt=alt)


def cam(loc, target, lens=32, clip=(0.3, 150000.0)):
    c = lib.camera(loc, target, lens)
    c.data.clip_start, c.data.clip_end = clip
    return c


def hide_casting(*obs):
    for ob in obs:
        if ob is None:
            continue
        for o in [ob] + list(ob.children_recursive):
            o.visible_shadow = False


def roll_bob(ob, roll=0.04, bob=0.15, period=4.5, phase=0.0):
    lib.add_sine(ob, 'rotation_euler', 0, roll, period, phase)
    lib.add_sine(ob, 'location', 2, bob, period * 1.3, phase + 1.0)


def tail_lights(root, col='#FF2A1A', strength=6.0, name='Tail'):
    m, em = lib.emission_mat(name + 'Mat', col, strength)
    for s in (1, -1):
        b = lib.box((0.16, 0.5, 0.18), (-3.7, 3.9 * s, -0.12), m, bevel=0.03, name=name + 'L')
        b.parent = root
        b.visible_shadow = False
    b = lib.box((0.1, 0.1, 0.22), (-3.86, 0, 2.2), m, bevel=0.02, name=name + 'Fin')
    b.parent = root
    return em


# ----------------------------------------------------------------------------- variants
def hook(shot, fps):
    dur = shot['dur']
    g = globe_below(-78.0, 23.5, -35.0, dur, sdir(-65, 38), patch='bahamas', night=0.0, speed=1.6)
    p = sk.spaceplane('Plane')
    roll_bob(p, 0.035, 0.12, 5.0)
    # other flights further along the lane
    for i, (x, y, z, h) in enumerate(((95, -22, -9, 0.08), (210, 36, -20, -0.05), (330, -60, -30, 0.02))):
        o = sk.spaceplane(f'Far{i}')
        o.location = (x, y, z)
        o.rotation_euler = (0, 0, h)
        lib.key_obj(o, 1, loc=(x, y, z))
        lib.key_obj(o, lib.sec2f(dur), loc=(x + 4.0 * dur, y, z), interp='LINEAR')
    c = cam((-9.5, 5.6, 8.6), (2.0, -0.6, -1.2), 32)
    lib.animate_camera(c, [(0, (-9.5, 5.6, 8.6)), (dur, (-6.2, 7.6, 7.2))],
                       [(0, (2.0, -0.6, -1.2)), (dur, (2.6, -0.2, -1.4))])
    lib.bloom(0.22, 1.4)
    return dict(fill=0.25, exposure=0.15)


def sunrise(shot, fps):
    dur = shot['dur']
    d = dip()
    tr = shot.get('events', {}).get('rise', 1.0)       # the sun centre crosses the horizon here
    s0, s1 = sdir(6, -d - 2.2 * tr), sdir(6, -d + 2.2 * (dur - tr))
    g = globe_below(10.0, 47.0, 80.0, dur, s0, night=2.6, speed=3.0, shine=0.06)
    st = sk.station('ISS')
    st.location = (53.3, 11.3, -7.7)
    st.rotation_euler = (0.35, 0.0, 1.75)
    lib.add_sine(st, 'rotation_euler', 2, 0.02, 9.0)
    disk, glow = sk.sun_disk(s0, dist=60000.0, r=330.0, strength=80.0)
    # sun climbs over the limb; the station leaves the Earth's shadow when the disk clears the horizon
    keys = [(0, s0), (dur, s1)]
    sk.animate_sun(keys, lamp=g['sun'], disk=[o for o in (disk, glow) if o], disk_dist=60000.0)
    lamp = g['sun'].data
    for t, en in ((0, 0.0), (max(0.0, tr - 0.25), 0.0), (tr + 0.45, 5.0), (dur, 5.0)):
        lamp.energy = en
        lamp.keyframe_insert('energy', frame=lib.sec2f(t))
    c = cam((0, 0, 0), (60, 3, -15), 34)
    lib.animate_camera(c, [(0, (0, 0, 0)), (dur, (3.0, -1.5, -0.3))], [(0, (60, 3, -15.2)), (dur, (60, 3, -14.6))])
    lib.bloom(0.55, 1.0, 9)
    return dict(fill=0.0, exposure=0.0)


def eva(shot, fps):
    dur = shot['dur']
    g = globe_below(35.4, 26.1, -18.0, dur, sdir(150, 42), patch='egypt', night=0.0, speed=1.4)
    M = sk._mats()
    # truss segment with a yellow handrail
    truss = lib.empty('Truss')
    for y in (-0.55, 0.55):
        for z in (-0.55, 0.55):
            b = lib.cyl(0.06, 22, (4, y, z), M['grey'], rot=(0, math.pi / 2, 0), verts=12, name='Chord')
            b.parent = truss
    for i in range(12):
        x = -7 + i * 2.0
        for a, bb in (((x, -0.55, -0.55), (x + 2, -0.55, 0.55)), ((x, 0.55, 0.55), (x + 2, 0.55, -0.55)),
                      ((x, -0.55, 0.55), (x, 0.55, 0.55)), ((x, -0.55, -0.55), (x, 0.55, -0.55))):
            av, bv = Vector(a), Vector(bb)
            mid = (av + bv) / 2
            dvec = bv - av
            ob = lib.cyl(0.035, dvec.length, mid, M['grey'], verts=8, name='Brace')
            ob.rotation_mode = 'QUATERNION'
            ob.rotation_quaternion = dvec.to_track_quat('Z', 'Y')
            ob.parent = truss
    rail_m = lib.mat('Rail', '#D9A43A', rough=0.4, metal=0.5)
    rail = lib.cyl(0.03, 6.0, (1.5, -0.75, 0.62), rail_m, rot=(0, math.pi / 2, 0), verts=10, name='Rail')
    rail.parent = truss
    for x in (-1.2, 1.5, 4.2):
        ob = lib.cyl(0.025, 0.2, (x, -0.75, 0.55), rail_m, verts=8, name='RailPost')
        ob.parent = truss
    truss.location = (-2.0, 1.3, -2.2)
    truss.rotation_euler = (0.0, 0.0, 0.08)
    a = sk.astronaut('#EEEDE8', 'Astro')
    a.location = (0.6, 0.2, -1.55)
    a.rotation_euler = (0.3, 0.0, math.pi / 2 - 0.75)
    lib.add_sine(a, 'rotation_euler', 0, 0.05, 6.0)
    lib.add_sine(a, 'location', 2, 0.06, 5.0)
    lib.key_obj(a, 1, loc=(0.6, 0.2, -1.55))
    lib.key_obj(a, lib.sec2f(dur), loc=(0.85, 0.35, -1.5))
    # tether
    lib.curve_poly('Tether', [[(0.3, 0.45, -0.75), (-0.6, 0.2, -1.9), (-1.6, 0.6, -1.7)]], 0.012,
                   lib.mat('TetherM', '#D8D2C2', rough=0.7))
    # low, close camera: the astronaut sits mid-frame on the limb, the top stays free for the captions
    c = cam((0.5, -4.2, 0.3), (0.5, 2.1, -0.62), 32)
    lib.animate_camera(c, [(0, (0.5, -4.2, 0.3)), (dur, (0.95, -3.8, 0.2))], [(0, (0.5, 2.1, -0.62)), (dur, (0.8, 2.2, -0.71))])
    lib.bloom(0.2, 1.4)
    return dict(fill=0.3, exposure=0.1)


def jam(shot, fps):
    dur = shot['dur']
    g = globe_below(-96.0, 37.0, 62.0, dur, sdir(140, 44), patch='usa', night=0.0, speed=0.0)
    rng = random.Random(4)
    ems = []
    lanes = [(0.0, 0.0, 12), (-15.0, 3.0, 9)]
    for li, (y0, z0, n) in enumerate(lanes):
        for i in range(n):
            p = sk.spaceplane(f'Q{li}_{i}')
            x = 10 + i * 19.5 + (li * 8) + rng.uniform(-2, 2)
            p.location = (x, y0 + rng.uniform(-1.2, 1.2), z0 - i * 0.6 + rng.uniform(-0.6, 0.6))
            p.rotation_euler = (rng.uniform(-0.04, 0.04), 0, rng.uniform(-0.05, 0.05))
            for o in p.children:
                if o.name.startswith(f'Q{li}_{i}Glow'):
                    o.hide_render = True
            em = tail_lights(p, name=f'T{li}_{i}')
            ems.append((em, rng.uniform(0, 1.0)))
            # creeping forward a metre now and then
            lib.key_obj(p, 1, loc=tuple(p.location))
            lib.key_obj(p, lib.sec2f(dur), loc=(p.location.x + rng.uniform(0.5, 2.0), p.location.y, p.location.z))
            roll_bob(p, 0.012, 0.05, 5.0 + rng.random(), rng.random() * 6)
    for em, ph in ems:
        f = 1
        on = True
        t = ph
        em.inputs['Strength'].default_value = 14.0
        em.inputs['Strength'].keyframe_insert('default_value', frame=1)
        while t < dur:
            em.inputs['Strength'].default_value = 14.0 if on else 2.0
            em.inputs['Strength'].keyframe_insert('default_value', frame=lib.sec2f(t))
            em.inputs['Strength'].keyframe_insert('default_value', frame=lib.sec2f(t) + 3)
            on = not on
            t += 0.55 if on else 0.75
    c = cam((-12, 6.5, 6.5), (60, -6, -10), 40)
    lib.animate_camera(c, [(0, (-12, 6.5, 6.5)), (dur, (-8, 5.0, 5.6))], [(0, (60, -6, -10)), (dur, (64, -6, -10.5))])
    lib.bloom(0.35, 1.2)
    return dict(fill=0.25, exposure=0.15)


def dream(shot, fps):
    dur = shot['dur']
    d = dip()
    sun = sdir(-7, -d + 1.0)
    g = globe_below(52.0, 21.0, 78.0, dur, sun, night=3.0, speed=2.0, shine=0.12)
    disk, glow = sk.sun_disk(sun, dist=60000.0, r=300.0, strength=90.0)
    p = sk.spaceplane('Plane')
    for t in (0.0, dur * 0.5, dur):
        u = t / dur
        lib.key_obj(p, lib.sec2f(t), loc=(9 + 12 * u + 14 * u * u, -0.6 + 0.4 * u, -0.4 + 0.9 * u))
    roll_bob(p, 0.03, 0.05, 4.0)
    c = cam((-2.5, 1.6, 1.7), (40, -2.5, -9.0), 34)
    lib.animate_camera(c, [(0, (-2.5, 1.6, 1.7)), (dur, (-1.2, 1.2, 1.5))], [(0, (40, -2.5, -9.0)), (dur, (44, -2.5, -8.6))])
    lib.bloom(0.6, 1.0, 9)
    return dict(fill=0.2, exposure=0.05)


def dump(shot, fps):
    dur = shot['dur']
    g = globe_below(-8.0, 41.0, 95.0, dur, sdir(150, 32), patch='iberia', night=0.0, speed=1.0)
    M = sk._mats()
    rng = random.Random(11)
    junk = []
    can_m = lib.mat('CanRed', '#B3241E', rough=0.3, metal=0.8)
    bag_m = lib.mat('Bag', '#E9E6DE', rough=0.5, alpha=0.85)
    rust_m = lib.mat('StageWhite', '#D9D5CC', rough=0.6, var=0.3, var_scale=4.0, bump=0.2)
    # a dead satellite with a broken array
    sat = lib.empty('DeadSat')
    lib.box((1.4, 1.4, 1.8), (0, 0, 0), M['gold'], bevel=0.05, name='SatBody').parent = sat
    lib.box((0.2, 4.2, 1.0), (0, 2.9, 0), M['panel'], bevel=0.01, name='SatWing').parent = sat
    w2 = lib.box((0.2, 2.2, 1.0), (0, -2.0, 0.4), M['panel'], rot=(0.5, 0, 0.3), bevel=0.01, name='SatWingBroken')
    w2.parent = sat
    lib.cyl(0.5, 0.5, (0, 0, 1.15), M['grey'], verts=24, r2=0.15, name='SatDish').parent = sat
    sat.location = (16, -3.0, -1.0)
    junk.append(sat)
    # spent upper stage
    stage = lib.cyl(1.6, 7.5, (40, 6, -4), rust_m, rot=(0.3, 1.2, 0.2), verts=48, name='Stage')
    lib.cyl(1.1, 1.2, (0, 0, -4.3), M['grey'], verts=32, r2=0.8, name='StageBell').parent = stage
    junk.append(stage)
    # fragments, a can, a bag, bolts
    for i in range(70):
        kind = rng.random()
        loc = (rng.uniform(3, 70), rng.uniform(-14, 14), rng.uniform(-9, 5))
        if Vector(loc).length < 4:
            continue
        if kind < 0.45:
            ob = lib.box((rng.uniform(0.1, 0.9), rng.uniform(0.05, 0.6), rng.uniform(0.02, 0.1)), loc,
                         M['panel'] if rng.random() < 0.4 else M['grey'], bevel=0.0, name='Shard')
        elif kind < 0.8:
            ob = lib.box((rng.uniform(0.08, 0.4),) * 3, loc, M['gold'] if rng.random() < 0.5 else M['white'], bevel=0.02, name='Chunk')
        elif kind < 0.9:
            ob = lib.cyl(0.04, 0.12, loc, M['grey'], verts=8, name='Bolt')
        else:
            ob = lib.cyl(0.033, 0.12, loc, can_m, verts=16, name='Can') if rng.random() < 0.6 else \
                lib.sphere(0.25, loc, bag_m, 12, 8, scale=(1.4, 0.4, 0.9), name='Bag')
        junk.append(ob)
    # a can very close to the lens to sell the clutter
    can = lib.cyl(0.033, 0.122, (2.1, -0.35, 0.05), can_m, verts=32, name='CanNear')
    junk.append(can)
    for ob in junk:
        r0 = Vector((rng.uniform(0, 6), rng.uniform(0, 6), rng.uniform(0, 6)))
        w = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1))) * rng.uniform(0.2, 0.9)
        v = Vector((rng.uniform(-0.6, 0.2), rng.uniform(-0.3, 0.3), rng.uniform(-0.2, 0.2)))
        l0 = ob.location.copy()
        lib.key_obj(ob, 1, loc=tuple(l0), rot=tuple(r0), interp='LINEAR')
        lib.key_obj(ob, lib.sec2f(dur), loc=tuple(l0 + v * dur), rot=tuple(r0 + w * dur), interp='LINEAR')
    c = cam((0, 0, 0), (20, -2, -4), 30)
    lib.animate_camera(c, [(0, (0, 0, 0)), (dur, (2.6, 0.3, -0.1))], [(0, (20, -2, -4)), (dur, (22, -1, -4.5))])
    lib.bloom(0.2, 1.4)
    return dict(fill=0.3, exposure=0.1)


def build(shot, fps):
    lib.FPS = fps
    return {'hook': hook, 'sunrise': sunrise, 'eva': eva, 'jam': jam, 'dream': dream, 'dump': dump}[shot['variant']](shot, fps)
