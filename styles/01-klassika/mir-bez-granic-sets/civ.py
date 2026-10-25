"""Background 'civilization' kit: power lines, wind turbines, distant towns, cell towers, water towers, gas station,
trucks, billboards, tree lines, refinery, ruins, church, grain elevator, wooden poles. Placed far away / to the sides
so the scenes feel inhabited without crowding the subject."""
import bpy, math, random
from mathutils import Vector
import lib
from lib import C

def _steel():
    return lib.mat('CivSteel', '#5C5E60', rough=0.55, metal=0.6, var=0.15, var_scale=2)

def _concrete():
    return lib.mat('CivConcrete', '#9A9184', rough=0.9, var=0.15, var_scale=0.5)

def _red_light():
    m, _ = lib.emission_mat('BeaconRed', '#FF2A1A', 25.0)
    return m

# ----------------------------------------------------------------------------- power line
def pylon(x, y, rot, coll, h=26.0, m=None):
    m = m or _steel()
    ca, sa = math.cos(rot), math.sin(rot)
    def P(lx, ly, z):
        return (x + lx * ca - ly * sa, y + lx * sa + ly * ca, z)
    b, t = 3.2, 0.9
    lines = []
    corners = [(-1, -1), (1, -1), (1, 1), (-1, 1)]
    for cx, cy in corners:
        lines.append([P(cx * b, cy * b, 0), P(cx * t, cy * t, h)])
    for k in range(1, 6):
        z = h * k / 6
        w = b + (t - b) * k / 6
        ring = [P(cx * w, cy * w, z) for cx, cy in corners] + [P(-w, -w, z)]
        lines.append(ring)
        if k < 6:
            z2 = h * (k + 1) / 6
            w2 = b + (t - b) * (k + 1) / 6
            for (ax, ay), (bx, by) in zip(corners, corners[1:] + corners[:1]):
                lines.append([P(ax * w, ay * w, z), P(bx * w2, by * w2, z2)])
    # cross arms (wires hang from their tips)
    arms = []
    for za, span in ((h * 0.78, 7.5), (h * 0.95, 5.5)):
        lines.append([P(-span, 0, za), P(span, 0, za)])
        lines.append([P(-span, 0, za), P(0, -t, za + 1.6), P(span, 0, za)])
        arms += [P(-span, 0, za - 1.2), P(span, 0, za - 1.2)]
    ob = lib.curve_poly('Pylon', lines, bevel=0.09, mat_=m, res=0, coll=coll)
    return arms

def power_line(p0, p1, coll, spacing=60.0, h=26.0, sag=3.5):
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    n = max(1, int(d.length / spacing))
    rot = math.atan2(d.y, d.x) + math.pi / 2
    m = _steel()
    tips = []
    for i in range(n + 1):
        q = p0.lerp(p1, i / n)
        tips.append(pylon(q.x, q.y, rot, coll, h, m))
    wm = lib.mat('Wire2', '#2E2F30', rough=0.5, metal=0.5)
    wires = []
    for a, b in zip(tips, tips[1:]):
        for ta, tb in zip(a, b):
            va, vb = Vector(ta), Vector(tb)
            pts = []
            for k in range(13):
                s = k / 12
                v = va.lerp(vb, s)
                v.z -= sag * 4 * s * (1 - s)
                pts.append(tuple(v))
            wires.append(pts)
    lib.curve_poly('Wires', wires, bevel=0.035, mat_=wm, res=0, coll=coll)

# ----------------------------------------------------------------------------- wind turbine
def wind_turbine(loc, coll, h=85.0, rot=0.0, rps=0.18, phase=0.0):
    x, y, z = loc
    white = lib.mat('TurbineWhite', '#D9D3C8', rough=0.45)
    lib.cyl(2.2, h, (x, y, z), white, r2=1.3, verts=24, name='TurbTower', coll=coll, origin='bottom')
    nac = lib.empty('Nacelle', (x, y, z + h), (0, 0, rot), coll=coll)
    body = lib.box((7.0, 3.0, 3.0), (1.5, 0, 0), white, bevel=0.6, name='NacBody', coll=coll)
    body.parent = nac
    hub = lib.empty('Hub', (-2.2, 0, 0), coll=coll)
    hub.parent = nac
    cone = lib.cyl(1.4, 2.0, (0, 0, 0), white, r2=0.2, rot=(0, math.radians(-90), 0), verts=20, name='HubCone', coll=coll)
    cone.parent = hub
    for k in range(3):
        a = 2 * math.pi * k / 3
        bl = lib.poly_prism([(0, -1.1), (h * 0.5, -0.25), (h * 0.5, 0.25), (0, 1.1)], 0.35, (0, 0, 0), white, name='Blade', coll=coll)
        # Y first (blade length X -> Z), then X spins it inside the rotor plane
        bl.rotation_mode = 'YXZ'
        bl.rotation_euler = (a, math.radians(-90), 0)
        bl.parent = hub
    sc = bpy.context.scene
    hub.rotation_euler = (phase, 0, 0)
    hub.keyframe_insert('rotation_euler', index=0, frame=1)
    hub.rotation_euler = (phase + 2 * math.pi * rps * sc.frame_end / lib.FPS, 0, 0)
    hub.keyframe_insert('rotation_euler', index=0, frame=sc.frame_end)
    for fc in hub.animation_data.action.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = 'LINEAR'
    lib.sphere(0.6, (x, y, z + h + 1.8), _red_light(), 8, 6, name='TurbLight', coll=coll)

# ----------------------------------------------------------------------------- towns, towers, buildings
_facades = []

def facade():
    if not _facades:
        import city
        for i, base in enumerate(['#8A8076', '#7A7068', '#9A8E80']):
            m, v = city.facade_mat(f'CivFacade{i}', base)
            v.outputs[0].default_value = 0.45
            _facades.append(m)
    return random.choice(_facades)

def town(center, coll, n=24, spread=(160, 60), hmin=12, hmax=55, seed=1, roofs=True):
    rng = random.Random(seed)
    cx, cy = center
    for i in range(n):
        x = cx + rng.uniform(-spread[0], spread[0]); y = cy + rng.uniform(-spread[1], spread[1])
        w, d = rng.uniform(14, 40), rng.uniform(12, 18)
        hh = rng.uniform(hmin, hmax) * (1.3 if abs(x - cx) < spread[0] * 0.3 else 1.0)
        b = lib.box((w, d, hh), (x, y, 0), facade(), rot=(0, 0, rng.choice([0, math.pi / 2]) + rng.uniform(-0.08, 0.08)),
                    bevel=0.2, name='TownBlock', coll=coll, origin='bottom')
        if roofs and rng.random() < 0.4:
            lib.box((w * 0.2, d * 0.4, 3), (x, y, hh), _concrete(), bevel=0.1, name='RoofBox', coll=coll, origin='bottom')
    # a couple of chimneys / a TV tower give the skyline character
    lib.cyl(2.0, hmax * 1.6, (cx + spread[0] * 0.6, cy, 0), lib.mat('Chimney', '#B9A795', rough=0.8), r2=1.4, verts=20,
            name='Chimney', coll=coll, origin='bottom')
    lib.cyl(1.2, hmax * 2.4, (cx - spread[0] * 0.5, cy + 10, 0), _steel(), r2=0.5, verts=12, name='TVTower', coll=coll, origin='bottom')
    lib.sphere(0.9, (cx - spread[0] * 0.5, cy + 10, hmax * 2.4 + 0.5), _red_light(), 8, 6, name='TVLight', coll=coll)

def cell_tower(loc, coll, h=40.0):
    x, y, z = loc
    m = _steel()
    lib.curve_poly('CellMast', [[(x - 1, y - 1, 0), (x - 0.3, y - 0.3, h)], [(x + 1, y - 1, 0), (x + 0.3, y - 0.3, h)],
                                [(x + 1, y + 1, 0), (x + 0.3, y + 0.3, h)], [(x - 1, y + 1, 0), (x - 0.3, y + 0.3, h)]],
                   bevel=0.08, mat_=m, coll=coll)
    for k in range(3):
        a = 2 * math.pi * k / 3
        lib.box((0.4, 0.9, 2.4), (x + 0.9 * math.cos(a), y + 0.9 * math.sin(a), h - 2), lib.mat('Antenna', '#D9D3C8', rough=0.5),
                rot=(0, 0, a), bevel=0.05, name='Antenna', coll=coll)
    lib.sphere(0.5, (x, y, h + 0.6), _red_light(), 8, 6, name='CellLight', coll=coll)

def water_tower(loc, coll, h=24.0):
    x, y, z = loc
    m = _steel()
    lib.curve_poly('WTLegs', [[(x + 3 * math.cos(a), y + 3 * math.sin(a), 0), (x + 2 * math.cos(a), y + 2 * math.sin(a), h)]
                              for a in (0.8, 2.4, 3.9, 5.5)], bevel=0.25, mat_=m, coll=coll)
    tank = lib.mat('WTTank', '#B8A48A', rough=0.6, var=0.2, var_scale=2)
    lib.cyl(5.0, 6.0, (x, y, h), tank, verts=32, name='WTTank', coll=coll, origin='bottom')
    lib.cyl(5.2, 3.0, (x, y, h + 6), tank, r2=0.3, verts=32, name='WTRoof', coll=coll, origin='bottom')

def tree(x, y, coll, h=9.0, rng=None, kind=None):
    rng = rng or random
    bark = lib.mat('CivBark', '#4A3C30', rough=0.95)
    leaf = lib.mat('Leaf' + str(rng.randint(0, 2)), rng.choice(['#5A6340', '#6B6A3E', '#4E5A3A']), rough=0.9, var=0.25, var_scale=1.5)
    lib.cyl(0.25 * h / 9, h * 0.45, (x, y, 0), bark, verts=8, name='Trunk', coll=coll, origin='bottom')
    if (kind or rng.choice(['round', 'cone'])) == 'cone':
        lib.cyl(h * 0.22, h * 0.75, (x, y, h * 0.3), leaf, r2=0.0, verts=10, name='Crown', coll=coll, origin='bottom')
    else:
        lib.sphere(h * 0.28, (x, y, h * 0.7), leaf, 10, 8, scale=(1, 1, 1.2), name='Crown', coll=coll)

def tree_line(p0, p1, coll, n=20, h=(7, 12), jitter=2.5, seed=4):
    rng = random.Random(seed)
    p0, p1 = Vector(p0), Vector(p1)
    for i in range(n):
        q = p0.lerp(p1, (i + rng.uniform(-0.3, 0.3)) / max(1, n - 1))
        tree(q.x + rng.uniform(-jitter, jitter), q.y + rng.uniform(-jitter, jitter), coll, rng.uniform(*h), rng)

def truck(loc, heading, coll, color='#B4532A', name='Truck'):
    root = lib.empty(name, loc, (0, 0, heading), coll=coll)
    paint = lib.mat('TruckCab' + color, color, rough=0.4, coat=0.3)
    trailer = lib.mat('Trailer', '#D2C8B8', rough=0.6, var=0.1, var_scale=1)
    rub = lib.mat('Tyre', '#151414', rough=0.85)
    parts = [lib.box((2.4, 2.5, 2.9), (6.6, 0, 0.5), paint, bevel=0.15, name='Cab', coll=coll, origin='bottom'),
             lib.box((12.0, 2.55, 3.9), (-0.8, 0, 1.0), trailer, bevel=0.06, name='TrailerBox', coll=coll, origin='bottom'),
             lib.box((0.05, 2.2, 1.0), (7.81, 0, 2.6), lib.mat('CarGlass', '#15181B', rough=0.08), bevel=0, name='CabGlass', coll=coll)]
    for x in (6.5, 3.2, -4.5, -5.9):
        for sy in (-1.1, 1.1):
            parts.append(lib.cyl(0.52, 0.4, (x, sy, 0.52), rub, rot=(math.radians(90), 0, 0), verts=16, name='TWheel', coll=coll))
    hm, _ = lib.emission_mat('TruckHead', '#FFE9C8', 6.0)
    for sy in (-0.9, 0.9):
        parts.append(lib.box((0.05, 0.35, 0.18), (7.82, sy, 1.0), hm, bevel=0, name='TruckLamp', coll=coll))
    for p in parts:
        p.parent = root
    return root

def billboard(loc, heading, coll, color='#E08A55'):
    x, y, z = loc
    root = lib.empty('Billboard', loc, (0, 0, heading), coll=coll)
    m = _steel()
    panel = lib.mat('BBPanel', color, rough=0.6)
    stripe = lib.mat('BBStripe', '#EDE3D4', rough=0.6)
    parts = [lib.cyl(0.25, 7.0, (-3, 0, 0), m, verts=10, name='BBPost', coll=coll, origin='bottom'),
             lib.cyl(0.25, 7.0, (3, 0, 0), m, verts=10, name='BBPost', coll=coll, origin='bottom'),
             lib.box((12, 0.3, 5), (0, 0, 9.0), panel, bevel=0.05, name='BBPanel', coll=coll),
             lib.box((8, 0.32, 0.8), (-1.0, 0, 9.8), stripe, bevel=0, name='BBStripe1', coll=coll),
             lib.box((5, 0.32, 0.5), (-2.5, 0, 8.6), stripe, bevel=0, name='BBStripe2', coll=coll)]
    for p in parts:
        p.parent = root
    l = lib.light('SPOT', (0, -2.5, 12.5), (math.radians(35), 0, 0), energy=900, color='#FFE2B8', spot=80, blend=0.6, size=0.3,
                  name='BBLight', coll=coll)
    l.parent = root

def gas_station(loc, heading, coll):
    root = lib.empty('GasStation', loc, (0, 0, heading), coll=coll)
    m = lib.mat('GSWhite', '#D8D0C2', rough=0.6)
    acc = lib.mat('GSAccent', '#B8432A', rough=0.5)
    under, _ = lib.emission_mat('GSUnder', '#FFF0D8', 4.0)
    win, _ = lib.emission_mat('GSWin', '#FFD39A', 3.0)
    parts = [lib.box((16, 9, 0.9), (0, 0, 5.2), m, bevel=0.05, name='GSRoof', coll=coll, origin='bottom'),
             lib.box((16.1, 9.1, 0.35), (0, 0, 5.8), acc, bevel=0, name='GSBand', coll=coll),
             lib.box((15, 8, 0.03), (0, 0, 5.18), under, bevel=0, name='GSLights', coll=coll)]
    for sx in (-5, 5):
        parts.append(lib.box((0.5, 0.5, 5.2), (sx, 0, 0), m, bevel=0.02, name='GSCol', coll=coll, origin='bottom'))
        parts.append(lib.box((0.8, 1.5, 1.8), (sx, 2, 0), acc, bevel=0.05, name='Pump', coll=coll, origin='bottom'))
    parts += [lib.box((12, 8, 4), (0, 14, 0), m, bevel=0.05, name='Shop', coll=coll, origin='bottom'),
              lib.box((10, 0.1, 2.2), (0, 9.95, 1.2), win, bevel=0, name='ShopWin', coll=coll, origin='bottom'),
              lib.cyl(0.3, 11, (11, -2, 0), m, verts=10, name='SignPole', coll=coll, origin='bottom'),
              lib.box((3.2, 0.5, 4.0), (11, -2, 11), acc, bevel=0.05, name='SignBox', coll=coll)]
    for p in parts:
        p.parent = root
    lib.light('AREA', (loc[0], loc[1], 5.0), (0, 0, 0), energy=4000, color='#FFF0D8', size=10, name='GSLight', coll=coll)

def refinery(center, coll, seed=6):
    rng = random.Random(seed)
    cx, cy = center
    tankm = lib.mat('RefTank', '#D2C8B8', rough=0.5, var=0.1, var_scale=0.2)
    steel = _steel()
    for i in range(9):
        lib.cyl(rng.uniform(7, 13), rng.uniform(9, 14), (cx + rng.uniform(-70, 70), cy + rng.uniform(-30, 30), 0), tankm, verts=40,
                name='StorageTank', coll=coll, origin='bottom')
    for i in range(5):
        x, y = cx + rng.uniform(-30, 30), cy + rng.uniform(25, 55)
        hh = rng.uniform(30, 55)
        lib.cyl(rng.uniform(1.5, 2.6), hh, (x, y, 0), steel, verts=16, name='Column', coll=coll, origin='bottom')
        for k in range(int(hh // 10)):
            lib.cyl(3.4, 0.25, (x, y, 8 + k * 10), steel, verts=16, name='Platform', coll=coll)
    for k in range(4):
        lib.box((150, 2.0, 0.6), (cx, cy + 15 + k * 3, 6 + k * 1.5), steel, bevel=0, name='PipeRack', coll=coll)
    # flare stack with a live flame
    fx, fy = cx + 80, cy + 50
    lib.cyl(1.0, 70, (fx, fy, 0), steel, r2=0.7, verts=12, name='Flare', coll=coll, origin='bottom')
    fm, fem = lib.emission_mat('FlareFlame', '#FFA040', 30.0)
    fl = lib.sphere(2.2, (fx, fy, 73), fm, 12, 8, scale=(1, 1, 2.0), name='FlareFlame', coll=coll)
    lib.add_sine(fl, 'scale', 2, 0.35, 0.25, 0.0)
    lib.add_sine(fl, 'scale', 0, 0.15, 0.31, 1.0)
    lib.light('POINT', (fx, fy, 74), energy=200000, color='#FF9A40', size=3, name='FlareLight', coll=coll)

def ruins(center, coll, n=10, seed=8):
    rng = random.Random(seed)
    cx, cy = center
    dark = lib.mat('RuinConcrete', '#6E675E', rough=0.95, var=0.25, var_scale=0.6, bump=0.4, bump_scale=3)
    holes = lib.mat('RuinHoles', '#1A1816', rough=1.0)
    for i in range(n):
        x, y = cx + rng.uniform(-90, 90), cy + rng.uniform(-25, 25)
        w, d, hh = rng.uniform(16, 30), rng.uniform(10, 16), rng.uniform(12, 32)
        r = rng.uniform(-0.1, 0.1)
        lib.box((w, d, hh), (x, y, 0), dark, rot=(0, 0, r), bevel=0.2, name='RuinBlock', coll=coll, origin='bottom')
        # broken top: jagged chunks
        for k in range(5):
            lib.box((rng.uniform(3, 8), d * 0.9, rng.uniform(2, 9)), (x + rng.uniform(-w / 2.5, w / 2.5), y, hh - 1), dark,
                    rot=(rng.uniform(-0.2, 0.2), rng.uniform(-0.3, 0.3), r), bevel=0.1, name='RuinChunk', coll=coll, origin='bottom')
        # window holes on the facade facing -y
        rows, cols = int(hh // 3.4) - 1, int(w // 3.2)
        for a in range(rows):
            for b in range(cols):
                if rng.random() < 0.75:
                    lib.box((1.4, 0.3, 1.5), (x - w / 2 + 1.8 + b * 3.2, y - d / 2 - 0.05, 2 + a * 3.4), holes, rot=(0, 0, r), bevel=0,
                            name='Hole', coll=coll)

def church(loc, coll, s=1.0):
    x, y, z = loc
    wall = lib.mat('ChurchWall', '#E3D6C1', rough=0.8)
    gold = lib.mat('Gold', '#D4A55A', rough=0.25, metal=1.0)
    lib.box((14 * s, 10 * s, 9 * s), (x, y, 0), wall, bevel=0.1, name='Nave', coll=coll, origin='bottom')
    lib.cyl(3.0 * s, 8 * s, (x, y, 9 * s), wall, verts=24, name='Drum', coll=coll, origin='bottom')
    lib.sphere(3.4 * s, (x, y, 18.5 * s), gold, 24, 16, scale=(1, 1, 1.25), name='Dome', coll=coll)
    lib.cyl(1.2 * s, 3.5 * s, (x, y, 21.5 * s), gold, r2=0.05, verts=16, name='DomeTip', coll=coll, origin='bottom')
    lib.box((0.25 * s, 0.25 * s, 3 * s), (x, y, 25.5 * s), gold, bevel=0, name='Cross', coll=coll, origin='bottom')
    lib.box((1.6 * s, 0.25 * s, 0.25 * s), (x, y, 27.3 * s), gold, bevel=0, name='CrossBar', coll=coll)
    # bell tower
    lib.box((4 * s, 4 * s, 18 * s), (x, y - 9 * s, 0), wall, bevel=0.08, name='BellTower', coll=coll, origin='bottom')
    lib.cyl(2.6 * s, 6 * s, (x, y - 9 * s, 18 * s), lib.mat('Spire', '#5E6B5A', rough=0.5, metal=0.4), r2=0.1, verts=8,
            name='Spire', coll=coll, origin='bottom')

def grain_elevator(loc, coll):
    x, y, z = loc
    m = lib.mat('Silo', '#C8BBA6', rough=0.85, var=0.2, var_scale=0.6)
    for i in range(4):
        for j in range(2):
            lib.cyl(3.0, 26, (x + i * 6.2, y + j * 6.2, 0), m, verts=24, name='Silo', coll=coll, origin='bottom')
    lib.box((10, 7, 12), (x - 7, y + 3, 0), m, bevel=0.1, name='HeadHouse', coll=coll, origin='bottom')
    lib.box((5, 5, 10), (x - 7, y + 3, 26), m, bevel=0.1, name='HeadTop', coll=coll, origin='bottom')

def wooden_poles(p0, p1, coll, spacing=28.0, h=8.5, sag=1.0, seed=2):
    rng = random.Random(seed)
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    n = max(1, int(d.length / spacing))
    wood = lib.mat('PoleWood', '#5A4838', rough=0.9, var=0.2, var_scale=5)
    rot = math.atan2(d.y, d.x) + math.pi / 2
    tips = []
    for i in range(n + 1):
        q = p0.lerp(p1, i / n)
        tilt = rng.uniform(-0.03, 0.03)
        lib.cyl(0.14, h, (q.x, q.y, 0), wood, rot=(tilt, 0, 0), verts=10, name='WoodPole', coll=coll, origin='bottom')
        lib.box((1.8, 0.14, 0.14), (q.x, q.y, h - 0.4), wood, rot=(0, 0, rot), bevel=0, name='PoleArm', coll=coll)
        tips.append([(q.x + 0.8 * math.cos(rot), q.y + 0.8 * math.sin(rot), h - 0.3), (q.x - 0.8 * math.cos(rot), q.y - 0.8 * math.sin(rot), h - 0.3)])
    wm = lib.mat('Wire2', '#2E2F30', rough=0.5, metal=0.5)
    wires = []
    for a, b in zip(tips, tips[1:]):
        for ta, tb in zip(a, b):
            va, vb = Vector(ta), Vector(tb)
            wires.append([tuple(va.lerp(vb, k / 10) - Vector((0, 0, sag * 4 * (k / 10) * (1 - k / 10)))) for k in range(11)])
    lib.curve_poly('PoleWires', wires, bevel=0.02, mat_=wm, res=0, coll=coll)

def hay_bales(center, coll, n=14, spread=(60, 40), seed=9):
    rng = random.Random(seed)
    m = lib.mat('Hay', '#C9A86A', rough=0.95, var=0.2, var_scale=3, bump=0.3, bump_scale=20)
    for i in range(n):
        lib.cyl(0.8, 1.2, (center[0] + rng.uniform(-spread[0], spread[0]), center[1] + rng.uniform(-spread[1], spread[1]), 0.8), m,
                rot=(math.radians(90), 0, rng.uniform(0, 3.1)), verts=20, name='Bale', coll=coll)
