"""Test reel: a holiday walk in a small French town (styles 2 and 3).
shot: {"style": "toy"|"lowpoly", "variant": "walk"|"cafe"|"reveal"}
Narrow street along +Y (road |x| < 3.5, sidewalks to |x| = 9.5), café terraces with parasols, flags, flowers,
the Eiffel Tower at the end of the street (built here, no model in the packs).
"""
import math, random
import bmesh
from mathutils import Vector
import lib
import assets as A
from street_test import STYLE, KC, KR, KV, KP, QB, QS, QC, QT, QN, QP

KF = 'interior/kenney/furniture-kit/Models/GLTF format/'
KN = 'nature/kenney/nature-kit/Models/GLTF format/'
QF = 'interior/quaternius/furniture-low-poly/Furniture Pack by @Quaternius/Furniture Pack by @Quaternius/Blends/'

EXTRA = {
    'toy': dict(table=KF + 'tableRound.glb', chair=KF + 'chair.glb', table_h=0.75, chair_h=0.9,
                flowers=[KN + f'flower_{c}{v}.glb' for c in ('red', 'yellow', 'purple') for v in 'AB'],
                pot=KN + 'pot_large.glb', parasol=('#EFE6D6', '#C9BBA4'), awning='#D8CBB6',
                tower='#8C8174', sit=['sit'], sky=('#8DBBE6', '#FFD7AE', '#C9D9A8'), paving='#BCAE9B', road='#77736F'),
    'lowpoly': dict(table=QF + 'Table.blend', chair=QF + 'Chair.blend', table_h=0.75, chair_h=0.95,
                    flowers=[QN + n for n in ('Flower_3_Group.gltf', 'Flower_4_Group.gltf', 'Bush_Common_Flowers.gltf')],
                    pot=None, parasol=('#F1E7D6', '#B5654A'), awning='#B5654A',
                    tower='#6F604F', sit=['sitdown'], sky=('#8DB8DE', '#FFCF9E', '#C4D49E'), paving='#B7A992', road='#6E6A66'),
}


def _flat(name, col, rough=0.85):
    return lib.mat(name, col, rough=rough, var=0.05, var_scale=0.5)


# ----------------------------------------------------------------------------- Eiffel Tower (lattice via Wireframe)
def _tube(bm, centers, halves, sides=3):
    """Square tube through rings (center xyz, half-size). Each side split in `sides` segments -> lattice cells."""
    rings = []
    for c, h in zip(centers, halves):
        ring = []
        corners = [(-h, -h), (h, -h), (h, h), (-h, h)]
        for k in range(4):
            (x0, y0), (x1, y1) = corners[k], corners[(k + 1) % 4]
            for s in range(sides):
                t = s / sides
                ring.append(bm.verts.new((c[0] + x0 + (x1 - x0) * t, c[1] + y0 + (y1 - y0) * t, c[2])))
        rings.append(ring)
    n = len(rings[0])
    for a, b in zip(rings, rings[1:]):
        for i in range(n):
            bm.faces.new((a[i], a[(i + 1) % n], b[(i + 1) % n], b[i]))


def eiffel(loc, height=300.0, col='#8C8174', coll=None):
    s = height / 300.0
    m = lib.mat('Eiffel', col, rough=0.75, metal=0.15)
    bm = bmesh.new()
    # four legs: from the corners to the first platform (57 m)
    for sx in (-1, 1):
        for sy in (-1, 1):
            cs, hs = [], []
            for i in range(9):
                t = i / 8
                d = lib.lerp(58, 21, t ** 0.8)
                cs.append((sx * d * s, sy * d * s, 57 * t * s))
                hs.append(lib.lerp(9, 5, t) * s)
            _tube(bm, cs, hs, 2)
    # middle section 57 -> 115 m, upper shaft 115 -> 276 m
    cs, hs = [], []
    for i in range(7):
        t = i / 6
        cs.append((0, 0, (57 + 58 * t) * s)); hs.append(lib.lerp(27, 13, t) * s)
    _tube(bm, cs, hs, 4)
    cs, hs = [], []
    for i in range(13):
        t = i / 12
        cs.append((0, 0, (115 + 161 * t) * s)); hs.append(lib.lerp(11, 2.2, t ** 0.75) * s)
    _tube(bm, cs, hs, 3)
    tw = lib.mesh_from_bm(bm, 'EiffelLattice', m, loc=loc, smooth=False, coll=coll)
    w = tw.modifiers.new('Lattice', 'WIREFRAME')
    w.thickness = 0.9 * s
    w.use_even_offset = True
    x, y, z = loc
    # platforms, arch, antenna
    for zz, half, th in ((57, 36, 4.5), (115, 17, 3.5), (276, 4.5, 4.0)):
        lib.box((2 * half * s, 2 * half * s, th * s), (x, y, z + zz * s), m, bevel=0.2 * s, name='EiffelDeck', coll=coll, origin='bottom')
    lib.cyl(0.9 * s, 24 * s, (x, y, z + 292 * s), m, name='EiffelTop', coll=coll)
    for rot in (0, math.pi / 2):
        arch = lib.cyl(40 * s, 3 * s, (x, y, z + 18 * s), m, rot=(math.pi / 2, 0, rot), verts=48, name='EiffelArch', coll=coll)
        sol = arch.modifiers.new('Ring', 'SOLIDIFY'); sol.thickness = 2.5 * s
    return tw


# ----------------------------------------------------------------------------- small props
def parasol(loc, cols, coll):
    pole = lib.cyl(0.04, 2.3, (loc[0], loc[1], 1.15), _flat('ParasolPole', '#5E5850'), name='ParasolPole', coll=coll)
    canopy = lib.cyl(1.4, 0.45, (loc[0], loc[1], 2.35), _flat('Parasol', cols[0], 0.9), verts=8, r2=0.05, name='Parasol', coll=coll)
    rim = lib.cyl(1.42, 0.12, (loc[0], loc[1], 2.14), _flat('ParasolRim', cols[1], 0.9), verts=8, name='ParasolRim', coll=coll)
    return canopy


def flag(loc, facing, coll):
    """Small French tricolore on a short pole sticking out of a facade."""
    x, y, z = loc
    d = Vector((facing, 0, 0))
    lib.cyl(0.03, 1.8, (x + d.x * 0.8, y, z + 0.4), _flat('FlagPole', '#4A4540'), rot=(0, math.radians(60) * -facing, 0), name='FlagPole', coll=coll)
    for i, c in enumerate(('#2A4D8F', '#F2EEE6', '#C8473F')):
        lib.box((0.02, 0.36, 0.8), (x + d.x * (1.35), y - 0.36 + i * 0.36, z + 0.4), _flat(f'Flag{i}', c, 0.9), bevel=0, name='Flag', coll=coll)


def shop_sign(text, loc, facing, col, coll):
    fm = _flat('SignText', '#F3EDE2', 0.6)
    t = lib.text_obj(text, size=0.55, loc=(loc[0] + facing * 0.08, loc[1], loc[2]), rot=(math.pi / 2, 0, facing * math.pi / 2), mat_=fm, coll=coll)
    lib.box((0.1, len(text) * 0.36 + 0.6, 0.85), (loc[0], loc[1], loc[2] + 0.18), _flat('Sign', col), bevel=0.02, name='SignBoard', coll=coll)
    return t


def build(shot, fps=60):
    style = shot.get('style', 'toy')
    st, ex = STYLE[style], EXTRA[style]
    variant = shot.get('variant', 'walk')
    dur = shot['dur']
    rng = random.Random(11)
    coll = lib.collection('Town')
    lib.FOG_BOX = (2200.0, 2200.0, 260.0)

    # warm holiday light: golden hour, bright, soft shadows
    sun_dir = Vector((-0.35, 1.0, 0.42))
    top, hor, below = ex['sky']
    lib.world_sky_view_gradient(top, hor, below, strength=1.7, fog=0.0016, fog_col='#F6E3CC', aniso=0.5,
                                glow_dir=sun_dir, glow_col='#FFB46E', glow_size=0.32, glow_strength=1.8)
    s = lib.light('SUN', (0, 0, 0), energy=3.2, color='#FFE2BE', size=1.0, name='Sun', volume=1.0)
    s.rotation_euler = (-sun_dir).normalized().to_track_quat('-Z', 'Y').to_euler()
    s.data.angle = math.radians(10)

    L0, L1 = -60, 360
    TOWER = (0.0, 480.0, 0.0)   # at the end of the street, big in frame
    Ly, cy = L1 - L0, (L0 + L1) / 2
    lib.plane((3000, 3000), (0, 0, -0.02), _flat('Ground', st['ground'], 0.95), name='Ground', coll=coll)
    lib.box((7, Ly, 0.05), (0, cy, 0), _flat('Road', ex['road']), bevel=0, name='Road', coll=coll, origin='bottom')
    for sx in (-1, 1):
        lib.box((6.0, Ly, 0.16), (sx * 6.5, cy, 0), _flat('Paving', ex['paving'], 0.9), bevel=0.02, name='Side', coll=coll, origin='bottom')
        lib.box((0.25, Ly, 0.18), (sx * 3.6, cy, 0), _flat('Curb', st['curb'], 0.9), bevel=0.02, name='Curb', coll=coll, origin='bottom')
    line_m = _flat('Line', st['line'], 0.6)
    for y in range(L0, L1, 8):
        lib.box((0.15, 3.0, 0.02), (0, y, 0.05), line_m, bevel=0, name='Dash', coll=coll, origin='bottom')

    # facades, shop fronts with awnings, signs and flags
    signs = ['BOULANGERIE', 'CAFÉ', 'FLEURS', 'BISTRO', 'PÂTISSERIE', 'FROMAGERIE', 'LIBRAIRIE']
    for sx in (-1, 1):
        y = L0
        while y < L1:
            src = rng.choice(st['front'])
            sz = A.size(src)
            k = st['front_scale'] * rng.uniform(0.95, 1.05) if st.get('front_scale') else 7.2 / A.size(st['ref']).z
            w, d = sz.x * k, sz.y * k
            A.place(src, (sx * (9.8 + d / 2), y + w / 2, 0.16), rot=-sx * math.pi / 2, scale=k, coll=coll)
            if -10 < y < 170 and rng.random() < 0.75:
                aw = lib.box((1.6, min(w - 1.0, 7.0), 0.12), (sx * 9.0, y + w / 2, 3.05), _flat('Awning', ex['awning'], 0.9),
                             rot=(0, -sx * math.radians(14), 0), bevel=0.03, name='Awning', coll=coll)
                shop_sign(rng.choice(signs), (sx * 9.72, y + w / 2, 3.9), -sx, '#3A3633', coll)
                if rng.random() < 0.6:
                    flag((sx * 9.7, y + 1.0, 6.5), -sx, coll)
            y += w + rng.uniform(0.2, 1.2)
    # skyline beyond the street
    for i in range(70):
        src = rng.choice(st['far'])
        x = rng.choice([-1, 1]) * rng.uniform(40, 300); yy = rng.uniform(-50, 900)
        if abs(x) < 110 and 360 < yy < 620:
            continue   # keep the view to the tower clear
        if st.get('far_scale'):
            A.place(src, (x, yy, 0), rot=rng.choice([0, math.pi / 2, math.pi]), scale=st['far_scale'] * rng.uniform(0.7, 1.0), coll=coll)
        else:
            A.place(src, (x, yy, 0), rot=rng.choice([0, math.pi / 2, math.pi]), height=rng.uniform(12, 22), coll=coll)
    for i in range(40):
        tx, ty = rng.choice([-1, 1]) * rng.uniform(30, 260), rng.uniform(0, 900)
        if abs(tx) < 90 and 380 < ty < 580:
            continue
        A.place(rng.choice(st['trees']), (tx, ty, 0), rot=rng.uniform(0, 6.28), height=rng.uniform(7, 12), coll=coll)
    eiffel(TOWER, 300, ex['tower'], coll)
    # park (Champ de Mars) in front of the tower: rows of trees on both sides of the axis
    for ty in range(375, 450, 12):
        for tx in (-34, -22, 22, 34):
            A.place(rng.choice(st['trees']), (tx, ty, 0), rot=rng.uniform(0, 6.28), height=rng.uniform(8, 10), coll=coll)

    # street furniture
    for y in range(L0 + 4, L1, 18):
        for sx in (-1, 1):
            if sx > 0 and -6 < y < 30:
                continue   # first terrace: keep the café shot clear
            A.place(st['lamp'], (sx * 4.1, y, 0.16), rot=sx * math.pi / 2, height=5.5, coll=coll)
            A.place(rng.choice(st['trees']), (sx * 4.3, y + 9, 0.16), rot=rng.uniform(0, 6.28), height=rng.uniform(5.5, 7.5), coll=coll)
    for y in range(L0 + 2, 200, 5):
        for sx in (-1, 1):
            if rng.random() < 0.55:
                if ex['pot']:
                    A.place(ex['pot'], (sx * 9.2, y, 0.16), height=0.5, coll=coll)
                A.place(rng.choice(ex['flowers']), (sx * 9.2, y, 0.16 + (0.45 if ex['pot'] else 0)), rot=rng.uniform(0, 6.28),
                        height=rng.uniform(0.5, 0.8), coll=coll)

    # café terraces: tables, chairs, parasols, people sitting
    sit_i = 0
    terraces = [(1, 6, 26), (-1, 34, 50), (1, 70, 84)]
    for sx, ya, yb in terraces:
        for y in range(ya, yb, 4):
            tx = sx * 7.0
            A.place(ex['table'], (tx, y, 0.16), height=ex['table_h'], coll=coll)
            parasol((tx, y), ex['parasol'], coll)
            for side in (-1, 1):
                cx, cyy = tx + side * 0.85, y
                A.place(ex['chair'], (cx, cyy, 0.16), rot=(math.pi / 2 if side < 0 else -math.pi / 2), height=ex['chair_h'], coll=coll)
                if rng.random() < 0.7:
                    src = st['people'][sit_i % len(st['people'])]; sit_i += 1
                    # Kenney 'sit' is posed with the hips at the root (legs hang below): lift onto the seat
                    seat = 0.16 + (0.46 if style == 'toy' else 0.0)
                    A.character(src, (cx, cyy, seat), rot=(-math.pi / 2 if side < 0 else math.pi / 2), height=st['person_h'],
                                anim=ex['sit'], hold=(style == 'lowpoly'), coll=coll, name=f'Sit{sit_i}')

    # strollers (both directions) and a few slow cars
    for i in range(26):
        src = st['people'][(i * 5) % len(st['people'])]
        sx = rng.choice([-1, 1])
        x = sx * rng.uniform(4.9, 5.7) if rng.random() < 0.7 else sx * rng.uniform(8.0, 8.6)
        y0 = rng.uniform(4, 120)   # nobody starts next to the walk camera
        dirn = rng.choice([-1, 1])
        p = A.character(src, (x, y0, 0.16), height=st['person_h'] * rng.uniform(0.92, 1.05), anim='walk', phase=rng.random(),
                        coll=coll, name=f'Walk{i}')
        A.walk_path(p, [(x, y0), (x, y0 + dirn * 20)], t0=0, speed=rng.uniform(0.9, 1.3))
    if variant == 'walk':   # a couple and a passer-by strolling ahead of the camera, same direction
        for j, (x, y0, sp) in enumerate(((5.7, -7.6, 1.25), (6.4, -7.3, 1.25), (7.7, -3.0, 1.1))):
            p = A.character(st['people'][(j * 3 + 1) % len(st['people'])], (x, y0, 0.16), height=st['person_h'] * (0.95 + 0.04 * j),
                            anim='walk', phase=0.3 * j, coll=coll, name=f'Lead{j}')
            A.walk_path(p, [(x, y0), (x, y0 + 30)], t0=0, speed=sp)
    for i in range(5):
        src = rng.choice(st['cars'])
        key = src.split('/')[-1].split('.')[0]
        lane = rng.choice([-1, 1]); y0 = rng.uniform(10, 160)
        csz = A.size(src)
        yaw = math.pi / 2 if csz.x > csz.y else 0.0
        car = A.place(src, (lane * 1.75, y0, 0.05), rot=(math.pi if lane > 0 else 0.0) + yaw, length=min(st['car_len'].get(key, 4.3), 5.0),
                      coll=coll, tint=st.get('tints', {}).get(key))
        A.drive_line(car, (lane * 1.75, y0), (lane * 1.75, y0 + lane * 50), rng.uniform(3.5, 5.5))

    # cameras (9:16)
    if variant == 'walk':      # stroll along the right sidewalk towards the tower, gentle step bob
        keys, tk = [], []
        for i in range(int(dur * 4) + 1):
            t = i / 4
            keys.append((t, (6.2, -12 + 1.35 * t, 1.65 + 0.025 * math.sin(t * 2 * math.pi * 1.8))))
            tk.append((t, (2.5, 60 + 1.35 * t, 6.0)))
        cam = lib.camera(keys[0][1], tk[0][1], lens=32)
        lib.animate_camera(cam, keys, tk)
    elif variant == 'cafe':    # slow dolly past the first terrace
        cam = lib.camera((1.6, 2, 2.0), (7.5, 14, 1.0), lens=30)
        lib.animate_camera(cam, [(0, (1.6, 2, 2.0)), (dur, (1.8, 7, 2.1))], [(0, (7.5, 14, 1.0)), (dur, (7.5, 20, 1.1))])
    else:                      # reveal: rise over the roofs, the tower appears in the haze
        cam = lib.camera((0, -10, 3.0), (0, 80, 10), lens=28)
        lib.animate_camera(cam, [(0, (0, -10, 3.0)), (dur, (-3, -24, 34))], [(0, (0, 80, 10)), (dur, (0, 480, 110))])
    return dict(exposure=0.5, fill=0.9)
