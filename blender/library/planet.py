"""Whole-Earth shots (R = 100 units, real colours): the fragile planet, the debris swarm, the final with city lights.
Variants: earth, debris, final.
"""
import bpy, math, random
from mathutils import Vector, Quaternion
import lib
import spacekit as sk
from lib import C


def facing(spin, lon, lat, tilt=0.0, spin_deg=0.0, dur=1.0):
    """Turn the globe so (lon, lat) faces the camera on -Y; spin_deg of rotation about the poles over the shot."""
    spin.rotation_mode = 'QUATERNION'
    q_face = Quaternion((0, 0, 1), math.radians(-90.0 - lon))
    q_lat = Quaternion((1, 0, 0), math.radians(lat))       # bring the latitude down to the line of sight
    f1 = lib.sec2f(dur) + 2
    for f in (1, f1):
        u = (f - 1) / max(1, f1 - 1)
        q_spin = Quaternion((0, 0, 1), math.radians(spin_deg * u))
        spin.rotation_quaternion = Quaternion((0, 1, 0), tilt) @ q_lat @ q_face @ q_spin
        spin.keyframe_insert('rotation_quaternion', frame=f)
    for fc in spin.animation_data.action.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = 'LINEAR'


def base(sun, night=2.2, stars=1.0, seg=(512, 256)):
    sk.SUN_SOCKETS.clear()
    sk.stars(1.0, stars)
    sd = Vector(sun).normalized()
    e, cl, shells, spin = sk.earth(sd, night=night, r=sk.R, seg=seg)
    lamp = sk.sun_light(sd, 4.5)
    lamp.data.use_shadow = False
    return e, cl, shells, spin, lamp


def earth(shot, fps):
    dur = shot['dur']
    e, cl, shells, spin, lamp = base((-0.55, -0.8, 0.22))
    facing(spin, 22.0, 18.0, 0.0, 9.0, dur)
    c = lib.camera((0, -150, 8), (0, 0, 2), 36)
    c.data.clip_end = 5000
    lib.animate_camera(c, [(0, (8, -142, 10)), (dur, (0, -330, 22))], [(0, (2, 0, 6)), (dur, (0, 0, 2))])
    lib.bloom(0.15, 1.6)
    return dict(fill=0.0, exposure=0.1)


def debris(shot, fps):
    dur = shot['dur']
    e, cl, shells, spin, lamp = base((-0.7, -0.6, 0.35))
    facing(spin, -40.0, 20.0, 0.0, 6.0, dur)
    n = shot.get('rings', 70)
    sk.debris_shell(n_rings=n, per_ring=80, size=0.32, dur_f=lib.sec2f(dur) + 2)
    c = lib.camera((0, -175, 30), (0, 0, 0), 36)
    c.data.clip_end = 5000
    lib.animate_camera(c, [(0, (14, -150, 34)), (dur, (0, -360, 70))], [(0, (8, 0, 18)), (dur, (0, 0, 4))])
    lib.bloom(0.4, 1.0, 8)
    return dict(fill=0.0, exposure=0.1)


def final(shot, fps):
    dur = shot['dur']
    e, cl, shells, spin, lamp = base((0.95, 0.12, 0.25), night=3.2)
    facing(spin, 30.0, 25.0, 0.0, 5.0, dur)
    c = lib.camera((0, -260, 40), (0, 0, 0), 36)
    c.data.clip_end = 5000
    lib.animate_camera(c, [(0, (0, -262, 46)), (dur, (-10, -245, 40))], [(0, (6, 0, 8)), (dur, (4, 0, 6))])
    lib.bloom(0.3, 1.0, 8)
    return dict(fill=0.0, exposure=0.1)


def build(shot, fps):
    lib.FPS = fps
    return {'earth': earth, 'debris': debris, 'final': final}[shot['variant']](shot, fps)
