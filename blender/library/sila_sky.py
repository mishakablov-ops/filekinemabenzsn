"""«Над облаками» for «Каждому по способности» (28.10.2026): a11 «Обычно в мире за день около 100 000 рейсов».
Not the city: a golden morning above a sea of cumulus. Jets cross at every height and distance with long soft
contrails, and faint old trails criss-cross the high sky, so the air looks busy. The counter sits in the lower third,
so the near jet crosses the upper middle of the frame.

Camera at z ~ 60 above the cloud tops (z = 0), looking along +y and a little up.
"""
import math
import random

from mathutils import Vector as V

import lib
import pcommon as pc
import sila_fx as FX

F = lib.sec2f
TAILS = ['#C8282A', '#2B4A9A', '#1F7A5A', '#D98A1E', '#5A2B7A', '#1E8FB0', '#B0302A', '#3A3F8F']


def cloud_sea(coll, rng, cam, half=0.7, d0=70.0, d1=4500.0):
    """Cumulus tops: clusters of flattened warm-white puffs, some piled into towers, in rows getting wider and bigger
    with distance (about the same size on screen) with gaps; a blue-grey lower deck under them gives the gaps depth."""
    floor = lib.mat('SkyFloor', '#DAD8DE', rough=1.0, var=0.3, var_scale=0.004, bump=0.8, bump_scale=0.03)
    lib.plane((40000, 40000), (0, 0, -4.0), floor, name='CloudFloor', coll=coll)
    puff = lib.mat('SkyPuff', '#FFF5EA', rough=1.0, sss=0.1)
    shade = lib.mat('SkyPuffShade', '#E6E0E2', rough=1.0)
    d, n = d0, 0
    while d < d1:
        size = d * 0.14
        width = d * half * 2
        k = max(2, int(width / (size * 2.2)))
        for i in range(k):
            if rng.random() < 0.1:
                continue
            x = cam.x - d * half + (i + rng.uniform(0.1, 0.9)) * width / k
            y = cam.y + d + rng.uniform(-0.4, 0.4) * size
            sz = size * rng.uniform(0.7, 1.5)
            tower = rng.random() < 0.22
            for j in range(rng.randint(10, 16)):
                a, r = rng.uniform(0, 2 * math.pi), sz * rng.uniform(0.0, 0.85)
                s = sz * rng.uniform(0.28, 0.5) * (1.0 - 0.4 * r / sz)
                zt = s * rng.uniform(-0.3, 0.25) + (sz * 0.9 * (1 - r / sz) * rng.uniform(0.3, 1.0) if tower else 0.0)
                loc = (x + r * math.cos(a), y + r * math.sin(a) * 0.8, zt)
                lib.sphere(1.0, loc, puff if rng.random() < 0.75 else shade, 14, 9, scale=(s * 1.3, s * 1.1, s * 0.8),
                           name='Puff', coll=coll)
                n += 1
        d *= 1.16
    return n


def contrail(coll, jet, length, name, r0=0.5, r1=4.5, gap=26.0, spread=6.5, alpha=0.75):
    """Two soft trails from the engines, parented to the jet (its tail is local +Y), widening behind it."""
    m = FX.cloud_mat(name + 'Mat', '#FFFFFF', alpha, dark='#C9CDD6', soft=1.0, noise=0.03)
    for sx in (-spread, spread):
        tr = lib.cyl(r0, length, (sx, gap + length / 2, 3.2), m, rot=(-math.pi / 2, 0, 0), verts=12, r2=r1,      # wide end behind
                     name=name + ('L' if sx < 0 else 'R'), coll=coll)
        tr.parent = jet


def v_planes(shot, fps):
    dur = shot['dur']
    rng = random.Random(11)
    coll = lib.collection('Sky')
    sun_dir = V((-0.88, 0.42, 0.2)).normalized()
    pc.day_sky(tuple(sun_dir), top='#3F78C4', horizon='#F4D9B4', below='#DCD6D2', strength=1.05, glow='#FFD49A', fog=0.00045,
               fog_col='#EADDCB', glow_size=0.16, glow_strength=2.6)
    pc.sun(tuple(sun_dir), 4.2, '#FFE2B8', 1.5, name='SkySun')
    c0, c1 = V((0.0, 0.0, 42.0)), V((8.0, 28.0, 44.0))
    t0, t1 = V((0.0, 1400.0, 115.0)), V((60.0, 1400.0, 135.0))
    cloud_sea(coll, rng, c0)
    # jets placed in screen space of the first frame: (depth m, x0 -> x1 across the half width, y in the half height,
    # tail colour, bank). The near one crosses just above the horizon, near eye level (higher up, its near wing would
    # look stuck up in this wide lens), left to right; the counter is in the lower third
    f = (t0 - c0).normalized()
    r = f.cross(V((0, 0, 1))).normalized()
    u = r.cross(f)
    tx, ty = 10.125 / 28, 18.0 / 28
    jets = [(85.0, -1.5, 0.9, 0.1, 0, 0.1), (330.0, 1.15, -0.25, 0.62, 1, -0.06), (560.0, -1.1, 0.05, 0.12, 2, 0.05),
            (820.0, 0.75, -0.2, -0.04, 3, 0.0), (430.0, 0.15, 0.6, -0.16, 5, -0.12), (1250.0, -0.45, 0.2, 0.78, 6, 0.0),
            (1700.0, 1.05, 0.55, 0.36, 7, 0.0), (2300.0, -0.9, -0.4, 0.5, 4, 0.0)]
    for k, (d, x0, x1, y, tail, bank) in enumerate(jets):
        p = c0 + f * d + r * (x0 * d * tx) + u * (y * d * ty)
        q = c0 + f * d * (1.0 + 0.05 * (k % 3 - 1)) + r * (x1 * d * tx) + u * (y * d * ty)
        v = (q - p) / dur
        hd = math.atan2(v.x, -v.y)
        jet = FX.plane_model(coll, tuple(p), heading=hd, livery='#F4F4F2', tail=TAILS[tail], name=f'Jet{k}')
        jet.rotation_euler.x = -math.atan2(v.z, math.hypot(v.x, v.y))
        jet.rotation_euler.y = bank
        FX.key_loc(jet, [(0, tuple(p)), (dur, tuple(q))], 'LINEAR')
        contrail(coll, jet, 420.0 if k == 0 else 1400.0, f'Trail{k}', alpha=0.8 if k == 0 else 0.65)
    # old trails high up, spreading and fading: the sky is a busy road
    old = FX.cloud_mat('OldTrailMat', '#FFFFFF', 0.35, dark='#D8DCE4', soft=1.0, noise=0.01)
    for k in range(11):
        d = rng.uniform(1500, 5000)
        q = V((rng.uniform(-0.9, 0.9) * d * 0.5, d, rng.uniform(380, 1400)))
        a = rng.uniform(0, math.pi)
        lib.cyl(rng.uniform(5, 12), rng.uniform(2500, 6000), tuple(q), old, rot=(math.pi / 2, 0, a), verts=10,
                     name=f'OldTrail{k}', coll=coll)
    cam = lib.camera(tuple(c0), tuple(t0), 28)
    lib.animate_camera(cam, [(0, tuple(c0)), (dur, tuple(c1))], [(0, tuple(t0)), (dur, tuple(t1))])
    cam.data.clip_start = 0.5
    cam.data.clip_end = 40000
    lib.bloom(0.25, 1.1, 7)
    return dict(fill=0.0, exposure=-0.1, samples=32)
