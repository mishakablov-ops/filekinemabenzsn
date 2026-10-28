"""«Маленькая планета» for «Каждому по способности» (28.10.2026): a03 «Восемь миллиардов людей, восемь миллиардов
способностей». Not the city: right after the real Earth (a02) a tiny toy planet (R = 6 m) with little houses, trees,
ponds and people standing all over it. On «людей» a few people light up; on «способностей» (event 'second') a wave of
auras runs over the whole planet, someone gets fire in the palm, someone floats up, someone sparks, one flies around.
The camera orbits a little and pushes in. The counter sits in the lower third, over the planet's lower half.
"""
import math
import random

from mathutils import Quaternion, Vector as V

import lib
import pcommon as pc
import people2 as P2
import sila as S
import sila_fx as FX

F = lib.sec2f
R = 6.0
AURA = ['#FFC857', '#7FD8FF', '#FF7AB6', '#9DFF8A', '#C59BFF', '#FF9C5B', '#6FFFE1', '#FFE66B']


def fib(n):
    """n points spread evenly over the unit sphere."""
    g = math.pi * (3 - math.sqrt(5))
    out = []
    for i in range(n):
        z = 1 - 2 * (i + 0.5) / n
        r = math.sqrt(1 - z * z)
        out.append(V((r * math.cos(g * i), r * math.sin(g * i), z)))
    return out


def on_surface(ob, n, heading=0.0, lift=0.0):
    """Stand an object on the planet at normal n (its local +Z along n), turned by heading about n."""
    ob.location = n * (R + lift)
    ob.rotation_mode = 'QUATERNION'
    ob.rotation_quaternion = n.to_track_quat('Z', 'Y') @ Quaternion((0, 0, 1), heading)


def planet(coll, rng):
    grass = lib.mat('TinyGrass', '#77A24E', rough=0.9, var=0.3, var_scale=0.35, bump=0.25, bump_scale=3)
    lib.sphere(R, (0, 0, 0), grass, 128, 64, name='TinyPlanet', coll=coll)
    m, s, a = FX.fresnel_glow('TinyAirMat', '#8CC6FF', 1.6, 0.4)
    lib.sphere(R * 1.1, (0, 0, 0), m, 96, 48, name='TinyAir', coll=coll)


def _house(coll, n, rng, k):
    root = lib.empty(f'House{k}', (0, 0, 0), coll=coll)
    wall = lib.mat('TinyWall' + str(k % 4), ['#EFE3CF', '#F2C9A0', '#D9E4EA', '#F4DDB0'][k % 4], rough=0.8)
    roof = lib.mat('TinyRoof' + str(k % 3), ['#B5482F', '#7A4A35', '#3E5F7A'][k % 3], rough=0.7)
    win, _ = lib.emission_mat('TinyWin', '#FFD58A', 1.2)
    w, d, h = rng.uniform(1.3, 1.9), rng.uniform(1.1, 1.5), rng.uniform(1.1, 1.5)
    parts = [lib.box((w, d, h), (0, 0, -0.1), wall, bevel=0.04, name=f'House{k}W', coll=coll, origin='bottom'),
             lib.poly_prism([(-w / 2 - 0.12, 0), (w / 2 + 0.12, 0), (0, 0.65)], d + 0.2, (0, d / 2 + 0.1, h - 0.1), roof,
                            rot=(math.pi / 2, 0, 0), name=f'House{k}R', coll=coll),
             lib.box((0.3, 0.05, 0.3), (-w / 4, -d / 2 - 0.01, h * 0.55), win, bevel=0, name=f'House{k}Win', coll=coll),
             lib.box((0.3, 0.05, 0.3), (w / 4, -d / 2 - 0.01, h * 0.55), win, bevel=0, name=f'House{k}Win', coll=coll),
             lib.box((0.32, 0.05, 0.55), (0, -d / 2 - 0.01, 0.0), lib.mat('TinyDoor', '#6A4430', rough=0.6), bevel=0,
                     name=f'House{k}D', coll=coll, origin='bottom')]
    for p in parts:
        p.parent = root
    on_surface(root, n, rng.uniform(0, 6.28))
    return root


def _block(coll, n, rng, k):
    """A tiny five-storey block like the hero's."""
    root = lib.empty(f'TBlock{k}', (0, 0, 0), coll=coll)
    wall = lib.mat('TinyPanel', '#E2D8C6', rough=0.85)
    win = lib.mat('TinyBlockWin', '#4A5A6C', rough=0.3)
    L, D, H = 3.2, 1.3, 2.6
    parts = [lib.box((L, D, H), (0, 0, -0.1), wall, bevel=0.03, name=f'TBlock{k}B', coll=coll, origin='bottom')]
    for fl in range(5):
        for c in range(5):
            for sy in (-1, 1):
                parts.append(lib.box((0.28, 0.04, 0.26), (-1.2 + c * 0.6, sy * (D / 2 + 0.01), 0.2 + fl * 0.48), win, bevel=0,
                                     name=f'TBlock{k}Win', coll=coll, origin='bottom'))
    for p in parts:
        p.parent = root
    on_surface(root, n, rng.uniform(0, 6.28))
    return root


def _tree(coll, n, rng, k):
    root = lib.empty(f'TTree{k}', (0, 0, 0), coll=coll)
    bark = lib.mat('TinyBark', '#6B4E3A', rough=0.9)
    h = rng.uniform(1.4, 2.4)
    parts = [lib.cyl(0.08, h * 0.6, (0, 0, -0.05), bark, verts=8, r2=0.05, name=f'TTree{k}T', coll=coll, origin='bottom')]
    g = rng.choice(['#5E9A43', '#7DB04F', '#E0B54A', '#D9822E', '#4F8A3E'])
    lm = lib.mat('TinyLeaf' + g, g, rough=0.85, var=0.25, var_scale=3)
    if rng.random() < 0.35:                                     # a fir
        for j in range(3):
            parts.append(lib.cyl(0.55 - j * 0.14, 0.7, (0, 0, h * 0.3 + j * 0.42), lib.mat('TinyFir', '#3F6E3A', rough=0.85),
                                 verts=10, r2=0.02, name=f'TTree{k}F', coll=coll, origin='bottom'))
    else:
        for j in range(3):
            parts.append(lib.sphere(rng.uniform(0.38, 0.55), (rng.uniform(-0.2, 0.2), rng.uniform(-0.2, 0.2), h * 0.62 + j * 0.2),
                                    lm, 12, 8, name=f'TTree{k}L', coll=coll))
    for p in parts:
        p.parent = root
    on_surface(root, n, rng.uniform(0, 6.28))
    return root


def _pond(coll, n, k):
    water = lib.mat('TinyWater', '#4C93C8', rough=0.08, spec=0.8)
    ob = lib.sphere(1.0, (0, 0, 0), water, 24, 8, scale=(1.3, 1.0, 0.06), name=f'TPond{k}', coll=coll)
    on_surface(ob, n, k * 1.3, lift=-0.02)
    return ob


def v_crowd(shot, fps):
    dur = shot['dur']
    second = shot.get('events', {}).get('second', 2.0)
    rng = random.Random(3)
    coll = lib.collection('Tiny')
    pc.night_sky(milky=0.55, stars=1.0, horizon='#16173A', top='#070914', airglow=0.0)
    sun_dir = V((-0.55, -0.62, 0.56)).normalized()
    pc.sun(tuple(sun_dir), 4.0, '#FFE1B5', 2.0, name='TinySun')
    rim = pc.sun((0.55, 0.75, 0.2), 1.6, '#9CC4FF', 3.0, name='TinyRim')
    rim.data.use_shadow = False
    planet(coll, rng)
    # the camera looks at the planet from -y, a little above the equator; things go on the visible side
    view = V((0.0, -1.0, 0.35)).normalized()
    c_dir = V((-2.5, -14.0, 5.0)).normalized()                  # where the camera is (see below)
    # people stand where the camera sees them from the side, upright in frame: the top of the planet up to its horizon
    # (on the cap facing the lens they would be seen from above and look like lying down)
    top = [p for p in fib(2200) if math.radians(36) < p.angle(c_dir) < math.radians(96) and p.z > 0.62]
    cap = [p for p in fib(1400) if p.dot(view) > 0.3]
    rng.shuffle(top)
    rng.shuffle(cap)
    used = []

    def take(pool, min_ang):
        """The next free spot of pool at least 0.6 * (both sizes) radians away from everything already placed."""
        for p in pool:
            if all(p.angle(q) > 0.6 * (a + min_ang) for q, a in used):
                used.append((p, min_ang))
                pool.remove(p)
                return p
        return None

    folk = []
    for k in range(40):
        n = take(top, 0.12)
        if n is None:
            break
        pp = S.folk((0, 0, 0), 0.0, rng, coll, None, name=f'Tp{k}')
        P2.stand(pp, rng)
        on_surface(pp['root'], n, rng.uniform(0, 6.28))
        folk.append((n, pp))
    for k in range(3):
        n = take(cap, 0.32)
        if n:
            _pond(coll, n, k)
    for k, (mk, size, cnt, pools) in enumerate(((_block, 0.38, 2, (cap,)), (_house, 0.24, 8, (cap, top)),
                                                (_tree, 0.14, 26, (cap, top)))):
        for j in range(cnt):
            n = take(pools[j % len(pools)], size)
            if n:
                mk(coll, n, rng, j + 20 * k)
    folk.sort(key=lambda q: abs(q[0].angle(c_dir) - math.radians(60)))   # the best seen get the special powers
    seed = folk[0][0]
    early = [1, 5, 9]
    for k, (n, pp) in enumerate(folk):
        if k in early:
            t = 0.35 + early.index(k) * 0.45
        else:
            t = second + 0.05 + n.angle(seed) / math.pi * 1.6 + rng.uniform(0, 0.12)
        col = AURA[k % len(AURA)]
        FX.aura(coll, pp['root'], col, r=0.5, z=0.95, t_on=t, strength=3.5, alpha=0.5, name=f'TpAura{k}', scale=(1, 1, 1.9))
        FX.flash(coll, tuple(n * (R + 1.0)), t, col=col, size=0.32, energy=250.0, name=f'TpFlash{k}')
        if k == 0:                                   # fire in the palm
            import sila_p1
            FX.flame(coll, sila_p1.palm(pp, coll, 'TpPalm'), (0, 0, 0.05), t + 0.1, None, scale=0.4, rng=rng, name='TpFlame')
        if k == 2:                                   # floats up off the ground
            on_surface(pp['root'], n, 0.0)
            FX.key_loc(pp['root'], [(0, tuple(n * R)), (t, tuple(n * R)), (dur, tuple(n * (R + 1.3)))])
        if k == 3:                                   # sparks between the hands
            side = n.cross(V((0, 0, 1))).normalized()
            base = n * (R + 1.0)
            FX.bolt(coll, tuple(base - side * 0.3), tuple(base + side * 0.3), [t + 0.1 + 0.18 * i for i in range(int((dur - t) / 0.18))],
                    rng, width=0.012, strength=30, light=200.0, name='TpBolt')
    # one flies around the planet with a golden trail of an aura
    fl = S.folk((0, 0, 0), 0, rng, coll, None, name='TpFlyer')
    S.fly_pose(fl, 'one')
    e1, e2 = V((1, 0, 0)), V((0, -0.45, 0.89)).normalized()
    ro = R + 2.4
    orb = []
    for i in range(9):
        a = math.radians(160 - i * 140 / 8)
        orb.append((dur * i / 8, tuple((e1 * math.cos(a) + e2 * math.sin(a)) * ro)))
    S.fly(fl, orb, tilt=1.4, bob=0.05)
    FX.aura(coll, fl['root'], '#FFC857', r=0.45, z=0.9, t_on=-1.0, strength=3.5, alpha=0.55, name='TpFlyA', scale=(1, 1, 1.9))
    # a few little clouds drifting round it
    puff = lib.mat('TinyCloud', '#FFFFFF', rough=1.0)
    for k in range(5):                               # low at the sides, not over the people on top
        n = (view + V((rng.choice((-1, 1)) * rng.uniform(0.6, 1.1), rng.uniform(-0.3, 0.3), rng.uniform(-0.7, -0.1)))).normalized()
        c = n * (R + rng.uniform(2.2, 3.2))
        for j in range(4):
            lib.sphere(rng.uniform(0.3, 0.5), tuple(c + V((j * 0.45 - 0.7, 0, rng.uniform(-0.1, 0.15)))), puff, 12, 8,
                       scale=(1.3, 1, 0.8), name=f'TCloud{k}', coll=coll)
    # camera: close over the planet, its horizon arcs across the upper middle with people standing on it against the
    # stars; a slow orbit and push-in (framing checked with a pinhole projection of the silhouette)
    c0, c1 = V((-2.5, -14.0, 5.0)), V((2.0, -12.9, 5.4))
    cam = lib.camera(tuple(c0), (0, 0, 4.5), 35)
    lib.animate_camera(cam, [(0, tuple(c0)), (dur, tuple(c1))], [(0, (0, 0, 4.5)), (dur, (0, 0, 4.8))])
    cam.data.clip_start = 0.1
    lib.bloom(0.35, 1.0, 7)
    return dict(fill=0.3, exposure=0.2, samples=32)
