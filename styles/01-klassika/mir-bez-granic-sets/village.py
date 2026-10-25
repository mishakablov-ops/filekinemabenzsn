"""Empty village at overcast dusk: wooden houses with dark windows, fences, bare trees, a swing still moving."""
import bpy, math, random
from mathutils import Vector
import lib
from lib import C

def gable_house(x, y, w, d, h, rot, coll, wall_m, roof_m, trim_m, win_m, rng):
    root = lib.empty('House', (x, y, 0), (0, 0, rot), coll=coll)
    body = lib.box((w, d, h), (0, 0, 0), wall_m, bevel=0.04, name='HouseBody', coll=coll, origin='bottom')
    rh = w * 0.42
    # roof prism: triangle profile in XZ extruded along Y
    roof = lib.poly_prism([(-w / 2 - 0.35, 0), (w / 2 + 0.35, 0), (0, rh)], d + 0.7, (0, 0, 0), roof_m, name='Roof', bevel=0.03, coll=coll)
    roof.rotation_euler = (math.radians(90), 0, 0)
    roof.location = (0, (d + 0.7) / 2, h - 0.05)
    gable = lib.poly_prism([(-w / 2, 0), (w / 2, 0), (0, rh - 0.1)], d, (0, 0, 0), wall_m, name='Gable', coll=coll)
    gable.rotation_euler = (math.radians(90), 0, 0)
    gable.location = (0, d / 2, h - 0.05)
    chim = lib.box((0.5, 0.5, 1.4), (w * 0.22, d * 0.2, h + rh * 0.45), lib.mat('Brick', '#6E4A3A', rough=0.9, var=0.2, var_scale=8),
                   bevel=0.02, name='Chimney', coll=coll, origin='bottom')
    parts = [body, roof, gable, chim]
    for k in range(3):
        wx = -w / 2 + w * (k + 1) / 4
        parts.append(lib.box((0.9, 0.06, 1.1), (wx, -d / 2 - 0.02, h * 0.52), win_m, bevel=0, name='Win', coll=coll))
        parts.append(lib.box((1.05, 0.08, 0.08), (wx, -d / 2 - 0.04, h * 0.52 - 0.6), trim_m, bevel=0.01, name='Sill', coll=coll))
        parts.append(lib.box((1.05, 0.08, 0.08), (wx, -d / 2 - 0.04, h * 0.52 + 0.6), trim_m, bevel=0.01, name='Lintel', coll=coll))
    door = lib.box((1.0, 0.08, 2.0), (-w / 2 + 0.9, -d / 2 - 0.03, 0), trim_m, bevel=0.01, name='Door', coll=coll, origin='bottom')
    parts.append(door)
    for p in parts:
        p.parent = root
    return root

def bare_tree(x, y, h, coll, m, rng, depth=3):
    root = lib.empty('Tree', (x, y, 0), (0, 0, rng.uniform(0, 6.28)), coll=coll)
    def branch(base, direction, length, radius, lvl):
        end = base + direction.normalized() * length
        ob = lib.curve_poly('Branch', [[tuple(base), tuple(end)]], bevel=radius, mat_=m, res=2, coll=coll)
        ob.parent = root
        if lvl <= 0:
            return
        for k in range(rng.randint(2, 3)):
            d = direction.normalized() + Vector((rng.uniform(-0.9, 0.9), rng.uniform(-0.9, 0.9), rng.uniform(0.1, 0.7)))
            branch(end, d, length * rng.uniform(0.5, 0.7), radius * 0.6, lvl - 1)
    branch(Vector((0, 0, 0)), Vector((rng.uniform(-0.1, 0.1), rng.uniform(-0.1, 0.1), 1)), h * 0.45, 0.16 * h / 7, depth)
    return root

def build(shot, fps=60):
    dur = shot['dur']
    rng = random.Random(51)
    coll = lib.collection('Village')
    F = lib.sec2f
    lib.world_sky_view_gradient('#8C8A86', '#C9B9A2', '#4A4338', strength=1.9, fog=0.02, fog_col='#CFC4B4', aniso=0.3,
                                glow_dir=(-0.5, 1.0, 0.15), glow_col='#F2B887', glow_size=0.5, glow_strength=0.6)
    s = lib.light('SUN', (0, 0, 0), energy=1.6, color='#FFD8B0', size=8.0, name='Overcast')
    s.rotation_euler = (math.radians(50), 0, math.radians(200))
    grass = lib.mat('Grass', '#5C5A3E', rough=0.97, var=0.35, var_scale=0.6, bump=0.5, bump_scale=8)
    lib.plane((600, 600), (0, 0, 0), grass, name='Ground', coll=coll)
    road = lib.mat('VillageRoad', '#6B5D4A', rough=0.96, var=0.3, var_scale=1.0, bump=0.7, bump_scale=10)
    lib.plane((5.0, 300), (0, 60, 0.01), road, name='Road', coll=coll)
    walls = [lib.mat('WoodA', '#7A6650', rough=0.9, var=0.25, var_scale=4, bump=0.2, bump_scale=30),
             lib.mat('WoodB', '#6B5E52', rough=0.9, var=0.25, var_scale=4, bump=0.2, bump_scale=30),
             lib.mat('WoodC', '#8C7B62', rough=0.9, var=0.25, var_scale=4, bump=0.2, bump_scale=30)]
    roof_m = lib.mat('Tin', '#5A4E46', rough=0.6, metal=0.4, var=0.3, var_scale=2)
    trim_m = lib.mat('Trim', '#C9BBA5', rough=0.7, var=0.2, var_scale=10)
    win_m = lib.mat('DarkGlass', '#141618', rough=0.15)
    fence_m = lib.mat('FenceWood', '#6E6253', rough=0.95, var=0.3, var_scale=6)
    tree_m = lib.mat('Bark', '#3E3730', rough=0.95, var=0.2, var_scale=10)
    LIT, _ = lib.emission_mat('LitWindow', '#FFB868', 3.0)
    LIVED = {}
    for k in range(7):
        for side in (-1, 1):
            y = 8 + k * 16 + rng.uniform(-2, 2)
            x = side * rng.uniform(9, 12)
            w, d, h = rng.uniform(6, 8), rng.uniform(5, 6.5), rng.uniform(2.8, 3.3)
            lived = (k == 1 and side < 0)
            gable_house(x, y, w, d, h, math.radians(90 if side < 0 else -90) + (0 if lived else rng.uniform(-0.05, 0.05)), coll,
                        rng.choice(walls), roof_m, trim_m, LIT if lived else win_m, rng)
            if lived:
                LIVED.update(x=x, y=y, w=w, d=d, h=h)
            # picket fence along the road
            for j in range(12):
                fy = y - 7 + j * 1.2
                if rng.random() < 0.12:
                    continue  # missing pickets
                tilt = rng.uniform(-0.06, 0.06) if rng.random() < 0.8 else rng.uniform(-0.4, 0.4)
                lib.box((0.09, 0.09, 1.1), (side * 3.4, fy, 0), fence_m, rot=(tilt, 0, 0), bevel=0.01, name='Picket', coll=coll,
                        origin='bottom')
            lib.box((0.06, 14.0, 0.1), (side * 3.4, y - 0.4, 0.75), fence_m, bevel=0.01, name='Rail', coll=coll)
            if rng.random() < 0.7:
                bare_tree(side * rng.uniform(5, 7), y + rng.uniform(4, 7), rng.uniform(6, 9), coll, tree_m, rng)
    # the swing, still moving in the empty yard
    swing_root = lib.empty('SwingFrame', (-5.6, 22.0, 0), (0, 0, math.radians(90)), coll=coll)
    metal = lib.mat('SwingMetal', '#4A4440', rough=0.5, metal=0.6)
    for sx in (-1.0, 1.0):
        lib.cyl(0.05, 2.5, (sx, 0, 0), metal, verts=10, name='SwingPost', coll=coll, origin='bottom').parent = swing_root
    bar = lib.cyl(0.05, 2.1, (0, 0, 2.5), metal, rot=(0, math.radians(90), 0), verts=10, name='SwingBar', coll=coll)
    bar.parent = swing_root
    pivot = lib.empty('SwingPivot', (0, 0, 2.5), coll=coll)
    pivot.parent = swing_root
    seat = lib.box((0.6, 0.25, 0.05), (0, 0, -1.9), fence_m, bevel=0.01, name='Seat', coll=coll)
    seat.parent = pivot
    for sx in (-0.27, 0.27):
        r = lib.cyl(0.01, 1.9, (sx, 0, -0.95), metal, verts=6, name='Rope', coll=coll)
        r.parent = pivot
    lib.key_obj(pivot, 1, rot=(0, 0, 0))
    lib.add_sine(pivot, 'rotation_euler', 0, 0.22, 3.2, 0.4)
    # signs of life in a half-empty village: one lit window with smoke from the chimney, an old car,
    # a woman on a bench, laundry drying, firewood
    import military
    hx, hy, hw, hd, hh = LIVED['x'], LIVED['y'], LIVED['w'], LIVED['d'], LIVED['h']
    lib.light('POINT', (hx + hd / 2 - 0.8, hy, 1.7), energy=150, color='#FFB060', size=0.5, name='HomeLight', coll=coll)
    rh = hw * 0.42
    military.smoke_column((hx - 0.2 * hd, hy + 0.22 * hw, hh - 0.05 + rh * 0.45 + 1.45), h=14, r=0.45, density=0.3,
                          color='#B8B2AA', coll=coll, name='ChimneySmoke')
    old = lib.car((-1.55, 9.5, 0), math.radians(91), '#6B6259', coll, lights=False, name='OldCar')
    old.rotation_euler = (0, math.radians(1.2), math.radians(91))
    # bench + an old woman sitting
    bm = lib.mat('BenchWood', '#7A6650', rough=0.9, var=0.2, var_scale=6)
    bench = lib.empty('Bench', (-2.95, 16.0, 0), (0, 0, math.radians(90)), coll=coll)
    for o in (lib.box((1.6, 0.42, 0.06), (0, 0, 0.42), bm, bevel=0.01, name='Seat', coll=coll),
              lib.box((1.6, 0.06, 0.42), (0, 0.2, 0.62), bm, bevel=0.01, name='Back', coll=coll),
              lib.box((0.08, 0.4, 0.42), (-0.7, 0, 0.0), bm, bevel=0.01, name='BLeg', coll=coll, origin='bottom'),
              lib.box((0.08, 0.4, 0.42), (0.7, 0, 0.0), bm, bevel=0.01, name='BLeg', coll=coll, origin='bottom')):
        o.parent = bench
    rw = random.Random(3)
    gran = lib.person((-2.95, 16.25, -0.42), math.radians(90), height=0.95, rng=rw, coll=coll, name='Granny')
    for k in ('legL', 'legR'):
        gran[k].rotation_euler = (math.radians(-57), 0, 0)
    for k, z in (('armL', -0.25), ('armR', 0.25)):
        gran[k].rotation_euler = (math.radians(-35), 0, z)
    gran['torso'].material_slots[0].material = lib.pmat('#5B4A5E')
    lib.add_sine(gran['head'], 'rotation_euler', 2, 0.25, 4.0, 0.0)
    scarf = lib.sphere(0.125, (0, 0, 1.64), lib.pmat('#8C5A3C'), 16, 10, scale=(1.0, 1.05, 0.95), name='Scarf', coll=coll)
    scarf.parent = gran['root']
    # laundry line in a yard
    rope = lib.mat('Rope', '#CFC4B4', rough=0.9)
    lib.curve_poly('Line', [[(-5.0, 30.0, 1.9), (-5.0, 35.0, 1.9)]], bevel=0.008, mat_=rope, coll=coll)
    for i, c in enumerate(('#C9BBA5', '#8C5A3C', '#6E7A5B', '#E3D6C1')):
        pv = lib.empty('ClothPivot', (-5.0, 30.8 + i * 1.2, 1.9), coll=coll)
        cl = lib.box((0.02, 0.8, 0.7), (0, 0, -0.36), lib.mat('Cloth' + c, c, rough=0.95), bevel=0, name='Cloth', coll=coll)
        cl.parent = pv
        lib.add_sine(pv, 'rotation_euler', 1, 0.12, 2.2 + i * 0.3, i)
    for i in range(14):
        lib.cyl(0.11, 0.9, (-4.4, 12.0 + i * 0.24, 0.12 + (i % 3) * 0.22), lib.mat('Firewood', '#8A6A4E', rough=0.9, var=0.2, var_scale=20),
                rot=(0, math.radians(90), 0), verts=10, name='Log', coll=coll)
    # the wider world: church, water tower, grain elevator, power poles along the road, a tree line
    import civ
    civ.church((-26, 178, 0), coll)
    civ.water_tower((32, 152, 0), coll)
    civ.grain_elevator((70, 215, 0), coll)
    civ.wooden_poles((2.95, -20), (2.95, 150), coll, spacing=28)
    civ.tree_line((-80, 140), (80, 150), coll, n=24, seed=41)
    # a door slowly creaking open
    cam = lib.camera((0.6, -10, 1.6), (0, 40, 2.0), lens=35, dof=18.0, fstop=4.0)
    lib.animate_camera(cam, [(0, (0.8, -12, 1.6)), (dur, (0.4, -6, 1.7))],
                       [(0, (-1.0, 40, 2.2)), (dur, (-1.5, 40, 2.0))], step=2, focus_keys=[(0, 30), (dur, 26)])
    lib.bloom(strength=0.2, threshold=1.5, size=7)
    return dict(samples=48, fill=1.0, exposure=0.35)
