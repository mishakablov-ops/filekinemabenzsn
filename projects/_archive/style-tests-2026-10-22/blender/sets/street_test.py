"""Style test: a lively street from ready-made models.  shot: {"style": "toy"|"lowpoly", "variant": "street"|"aerial"|"close"}
Style 2 "Игрушечный город" = Kenney, style 3 "Low-poly мульт" = Quaternius (see styles/*/README.md).
Street runs along +Y; road x in [-5, 5], sidewalks to |x| = 9, facades at |x| = 9.5.
"""
import math, random
from mathutils import Vector
import lib
import assets as A

KC = 'city/kenney/city-kit-commercial/Models/GLB format/'
KS = 'city/kenney/city-kit-suburban/Models/GLB format/'
KR = 'city/kenney/city-kit-roads/Models/GLB format/'
KI = 'city/kenney/city-kit-industrial/Models/GLB format/'
KV = 'vehicles/kenney/car-kit/Models/GLB format/'
KP = 'people/kenney/mini-characters/Models/GLB format/'
QB = 'city/quaternius/lowpoly-buildings-pack/ultimate_textured_building_pack_by_quaternius/Ultimate Textured Building Pack - Dec 2019/Models with Materials/Blends/'
QS = 'city/quaternius/lowpoly-modular-street-pack/Street Pack by @Quaternius/Street Pack by @Quaternius/Blends/'
QC = 'vehicles/quaternius/lowpoly-cars/Car Pack/Car Pack/Blends/'
QT = 'vehicles/quaternius/lowpoly-public-transport/Public Transport_0/Public Transport/Blends/'
QN = 'nature/quaternius/stylized-nature-megakit/stylized_nature_megakitstandard/glTF/'
QP = 'people/quaternius/animated-characters-pack/ultimate_animated_character_pack_by_quaternius/Ultimate Animated Character Pack - Nov 2019/Blends/'

STYLE = {
    'toy': dict(
        front=[KC + f'building-{c}.glb' for c in 'abcdefghijklmn'], front_scale=10.0,
        far=[KC + f'building-skyscraper-{c}.glb' for c in 'abcde'], far_scale=14.0,
        civ=[KI + 'chimney-large.glb', KI + 'water-tower.glb', KI + 'windmill.glb', KI + 'detail-tank-large.glb'], civ_scale=14.0,
        lamp=KR + 'light-curved.glb', lamp_h=7.5,
        trees=[KS + 'tree-large.glb', KS + 'tree-small.glb'], tree_h=(5.5, 8.0),
        cars=[KV + n + '.glb' for n in ('sedan', 'taxi', 'suv', 'van', 'hatchback-sports', 'delivery', 'sedan-sports', 'suv-luxury')],
        car_len={'van': 5.0, 'delivery': 5.6}, car_rot=0.0,
        people=[KP + f'character-{g}-{c}.glb' for g in ('male', 'female') for c in 'abcdef'],
        person_h=1.75,
        road='#4A4F5C', line='#F2E9D8', side='#C9C2D6', curb='#9C95AE', ground='#8DBF6A',
        sky=('#7FB2E5', '#FFD3A8', '#BFD7A0'), sun='#FFE4C4', glow='#FFB874',
    ),
    'lowpoly': dict(
        front=[QB + n + '_Mat.blend' for n in ('2Story', '2Story_2', '2Story_Balcony', '2Story_Center', '2Story_Columns', '2Story_Sign',
                                              '2Story_Wide', '3Story_Balcony', '3Story_Slim', '3Story_Small', '4Story', '4Story_Center',
                                              '1Story_Sign', '2Story_Slim', '4Story_Wide_2Doors')],
        front_height=None, front_scale=None, ref=QB + '2Story_Mat.blend',
        far=[QB + n + '_Mat.blend' for n in ('6Story_Stack', '4Story_Wide_2Doors_Roof', '4Story')], far_scale=None,
        civ=[], civ_scale=None,
        lamp=QS + 'Streetlight_Single.blend', lamp_h=7.0,
        trees=[QN + f'CommonTree_{i}.gltf' for i in range(1, 6)], tree_h=(6.0, 9.0),
        cars=[QC + n + '.blend' for n in ('BasicCar', 'Taxi', 'SimpleCarHigh', 'SimpleCarShort')] + [QT + 'Bus.blend'],
        car_len={'Bus': 11.0}, car_rot=0.0,
        tints={'BasicCar': '#C8553D', 'SimpleCarHigh': '#4F7CAC', 'SimpleCarShort': '#E0B040', 'Bus': '#D9A23A'},
        people=[QP + n + '.blend' for n in ('Casual_Male', 'Casual_Female', 'Casual2_Male', 'Casual2_Female', 'Casual3_Male',
                                          'Casual3_Female', 'Suit_Male', 'Suit_Female', 'Worker_Male', 'OldClassy_Female', 'Chef_Female', 'Doctor_Male_Young')],
        person_h=1.75,
        road='#56545A', line='#EFE6D2', side='#BDB2A4', curb='#8E8478', ground='#9BBF6E',
        sky=('#86B6E0', '#FFD0A0', '#B9CF95'), sun='#FFE0BC', glow='#FFAE6A',
    ),
}


def _flat(name, col, rough=0.8):
    return lib.mat(name, col, rough=rough, var=0.05, var_scale=0.5)


def build(shot, fps=60):
    st = STYLE[shot.get('style', 'toy')]
    variant = shot.get('variant', 'street')
    dur = shot['dur']
    rng = random.Random(7)
    coll = lib.collection('Street')
    lib.FOG_BOX = (1600.0, 1600.0, 120.0)

    # sky & light: bright, warm evening, few shadows (style rules 22.10)
    sun_dir = Vector((0.5, 1.0, 0.35))
    top, hor, below = st['sky']
    lib.world_sky_view_gradient(top, hor, below, strength=1.6, fog=0.0012, fog_col='#F3E2CF', aniso=0.45,
                                glow_dir=sun_dir, glow_col=st['glow'], glow_size=0.3, glow_strength=1.6)
    s = lib.light('SUN', (0, 0, 0), energy=3.0, color=st['sun'], size=1.0, name='Sun', volume=1.0)
    s.rotation_euler = (-sun_dir).normalized().to_track_quat('-Z', 'Y').to_euler()
    s.data.angle = math.radians(8)

    # ground, road, sidewalks (own simple geometry in the style's palette)
    L0, L1 = -60, 420
    Ly, cy = L1 - L0, (L0 + L1) / 2
    lib.plane((2400, 2400), (0, 0, -0.02), _flat('Ground', st['ground'], 0.95), name='Ground', coll=coll)
    lib.box((10, Ly, 0.05), (0, cy, 0), _flat('Road', st['road'], 0.85), bevel=0, name='Road', coll=coll, origin='bottom')
    line_m = _flat('Line', st['line'], 0.6)
    for y in range(L0, L1, 9):
        lib.box((0.22, 4.0, 0.02), (0, y, 0.05), line_m, bevel=0, name='Dash', coll=coll, origin='bottom')
    for sx in (-1, 1):
        lib.box((4.0, Ly, 0.18), (sx * 7.0, cy, 0), _flat('Side', st['side'], 0.9), bevel=0.02, name='Side', coll=coll, origin='bottom')
        lib.box((0.3, Ly, 0.2), (sx * 5.15, cy, 0), _flat('Curb', st['curb'], 0.9), bevel=0.02, name='Curb', coll=coll, origin='bottom')

    # facades on both sides, front faces the road
    for sx in (-1, 1):
        y = L0
        while y < L1:
            src = rng.choice(st['front'])
            sz = A.size(src)
            if st.get('front_scale'):
                k = st['front_scale'] * rng.uniform(0.95, 1.1)
            else:
                k = 7.2 / A.size(st['ref']).z  # lowpoly: one scale for the whole pack, 2-storey house = 7.2 m
            w, d = sz.x * k, sz.y * k
            A.place(src, (sx * (9.6 + d / 2), y + w / 2, 0.06), rot=-sx * math.pi / 2, scale=k, coll=coll)
            y += w + rng.uniform(0.3, 2.0)
    # far skyline + civilisation on the horizon
    for i in range(60):
        src = rng.choice(st['far'])
        x = rng.choice([-1, 1]) * rng.uniform(55, 260)
        y = rng.uniform(80, 900)
        if st.get('far_scale'):
            A.place(src, (x, y, 0), rot=rng.uniform(0, 6.28), scale=st['far_scale'] * rng.uniform(0.9, 1.5), coll=coll)
        else:
            A.place(src, (x, y, 0), rot=rng.uniform(0, 6.28), height=rng.uniform(18, 40), coll=coll)
    for i, src in enumerate(st['civ'] * 3):
        A.place(src, (rng.choice([-1, 1]) * rng.uniform(90, 300), rng.uniform(300, 900), 0), rot=rng.uniform(0, 6.28),
                scale=st['civ_scale'] * rng.uniform(1.0, 2.0), coll=coll)

    # street furniture: lamps and trees along the curb
    for y in range(L0 + 6, L1, 22):
        for sx in (-1, 1):
            A.place(st['lamp'], (sx * 5.7, y, 0.18), rot=(sx * math.pi / 2), height=st['lamp_h'], coll=coll)
            A.place(rng.choice(st['trees']), (sx * 5.75, y + 11, 0.18), rot=rng.uniform(0, 6.28),
                    height=rng.uniform(*st['tree_h']), coll=coll)

    # traffic: lanes x = +-2.5, right-hand traffic
    for i in range(14):
        src = rng.choice(st['cars'])
        key = src.split('/')[-1].split('.')[0]
        lane = rng.choice([-1, 1])
        y0 = rng.uniform(-10, 260)
        csz = A.size(src)
        yaw = math.pi / 2 if csz.x > csz.y else 0.0   # long side along the road
        car = A.place(src, (lane * 2.5, y0, 0.05), rot=(math.pi if lane > 0 else 0.0) + st['car_rot'] + yaw,
                      length=st['car_len'].get(key, 4.5), coll=coll, tint=st.get('tints', {}).get(key))
        sp = rng.uniform(6, 11)
        A.drive_line(car, (lane * 2.5, y0), (lane * 2.5, y0 + lane * 100), sp)

    # people on the sidewalks with real walk cycles
    n_people = 18 if variant != 'aerial' else 24
    for i in range(n_people):
        src = st['people'][i % len(st['people'])]
        sx = rng.choice([-1, 1])
        x = sx * rng.uniform(6.6, 8.6)
        y0 = rng.uniform(-4, 70 if variant != 'aerial' else 160)
        dirn = rng.choice([-1, 1])
        walking = rng.random() < 0.8
        p = A.character(src, (x, y0, 0.18), height=st['person_h'] * rng.uniform(0.92, 1.05),
                        anim='walk' if walking else 'idle', phase=rng.random(), coll=coll, name=f'P{i}')
        if walking:
            A.walk_path(p, [(x, y0), (x, y0 + dirn * 30)], t0=0, speed=rng.uniform(1.1, 1.5))
        else:
            p.rotation_euler.z = rng.choice([0.0, math.pi / 2, -math.pi / 2])

    # cameras
    if variant == 'street':
        cam = lib.camera((2.0, -18, 4.2), (0, 40, 3.0), lens=30)
        lib.animate_camera(cam, [(0, (2.0, -18, 4.2)), (dur, (1.4, -6, 4.0))], [(0, (0, 40, 3.0)), (dur, (0, 52, 3.2))])
    elif variant == 'aerial':
        cam = lib.camera((-38, -40, 46), (0, 60, 0), lens=32)
        lib.animate_camera(cam, [(0, (-38, -40, 46)), (dur, (-30, -20, 42))], [(0, (0, 60, 0)), (dur, (0, 75, 0))])
    else:  # close: people and passing cars at the curb
        # on the left sidewalk next to the facades, above head height (nobody walks through the lens)
        cam = lib.camera((-8.7, 2, 2.4), (5.0, 22, 1.2), lens=32)
        lib.animate_camera(cam, [(0, (-8.7, 2, 2.4)), (dur, (-8.6, 6, 2.5))], [(0, (5.0, 22, 1.2)), (dur, (5.0, 26, 1.2))])
    return dict(exposure=0.45, fill=0.9)
