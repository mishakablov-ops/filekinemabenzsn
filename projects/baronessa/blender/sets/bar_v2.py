"""Scenes of «Баронесса-пулемётчица» v2 (29.10.2026, mike: «жёсткий юмор-экшн… армия… как Сталин… отслеживалось как на
картах»): the war room with the brand map of Europe, an army of identical baronesses, «Биркин-34» tanks, coupon volleys,
sieges. Harder light than v1: smoke, searchlights, fire glow, contrast. build(shot, fps) dispatches on shot['variant'].
Reuses the places of v1 (bar_sets) where the story goes back to them.
"""
import math
import os
import random

import bmesh
import bpy
from mathutils import Vector

import lib
import sila_hero as SH
import baroness as B
import bar_props as P
import bar_sets as S

F = lib.sec2f
TEX = S.TEX
ev = S.ev

# brand map of Europe on europe_political.jpg: (u, v) of the image, v from the bottom
MAP_W, MAP_H = 3.0, 2.714
PLACES = {'Биркинштат': (0.85, 0.61), 'Эрмесовка': (0.65, 0.47), 'Эрмес': (0.475, 0.375),
          'КокоШанель': (0.40, 0.44), 'Луивиттония': (0.50, 0.50), 'Гучийск': (0.54, 0.25),
          'Прада-на-Дону': (0.875, 0.40)}


def mxy(name, z=0.0, c=(0, 0)):
    u, v = PLACES[name]
    return Vector((c[0] + (u - 0.5) * MAP_W, c[1] + (v - 0.5) * MAP_H, z))


# ----------------------------------------------------------------------------- army
_ARMY = {}


def army_mesh(pose='strict', **kw):
    """The baroness in one pose as a static mesh (no rig) to instance by the hundred."""
    key = pose + str(sorted(kw.items()))
    if key in _ARMY:
        return _ARMY[key]
    b = B.load(name='ArmySrc')
    B.SH.apply(b, B.P(pose, **kw))
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(b['body'].evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)
    me.name = 'Army_' + pose
    for o in (b['body'], b['rig']):
        bpy.data.objects.remove(o)
    _ARMY[key] = me
    return me


def soldier(me, loc, heading=0.0, scale=1.0, name='Soldier'):
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    ob.location, ob.rotation_euler, ob.scale = loc, (0, 0, heading), (scale,) * 3
    return ob


def march_block(me, origin, rows, cols, dx=1.05, dy=1.3, heading=math.pi, t0=0.0, t1=5.0, speed=1.2, seed=1,
                bob=0.035, jitter=0.12):
    """A block of baronesses marching along -Y (before heading): each bobs on the step, the block moves forward."""
    rnd = random.Random(seed)
    out = []
    # the model faces -Y at heading 0: front = (sin h, -cos h); ranks stand behind the first one, files across
    fwd = Vector((math.sin(heading), -math.cos(heading), 0))
    right = Vector((math.cos(heading), math.sin(heading), 0))
    for r in range(rows):
        for c in range(cols):
            p0 = Vector(origin) + right * ((c - (cols - 1) / 2) * dx + rnd.uniform(-jitter, jitter)) \
                - fwd * (r * dy + rnd.uniform(-jitter, jitter))
            ob = soldier(me, p0, heading + rnd.uniform(-0.04, 0.04))
            for t, k in ((t0, 0), (t1, 1)):
                ob.location = p0 + fwd * speed * (t - t0)
                ob.keyframe_insert('location', frame=F(t))
            lib._set_interp(ob, 'LINEAR')
            lib.add_sine(ob, 'location', 2, bob, 0.55, phase=(r % 2) * math.pi)
            out.append(ob)
    return out


# ----------------------------------------------------------------------------- tank «Биркин-34»
def tank(loc, heading=0.0, name='Tank', gun_up=0.05):
    """A WWII-style medium tank whose turret is a giant leather handbag with a handle and a gold lock; the gun is
    brass. Front (gun) along -Y before heading."""
    hull_m = P.M('TankOlive', '#4F5634', rough=0.6, var=0.18, bump=0.25, bs=12, coat=0.1)
    track_m = P.M('TankTrack', '#1C1C1A', rough=0.8, var=0.1, bump=0.5, bs=40)
    objs = []
    bm = bmesh.new()
    pts = [(-1.5, -3.2, 0.55), (1.5, -3.2, 0.55), (1.5, 3.0, 0.55), (-1.5, 3.0, 0.55),
           (-1.35, -2.2, 1.45), (1.35, -2.2, 1.45), (1.35, 2.6, 1.45), (-1.35, 2.6, 1.45)]
    vs = [bm.verts.new(p) for p in pts]
    for f in ((0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)):
        bm.faces.new([vs[i] for i in f])
    hull = lib.mesh_from_bm(bm, name + 'Hull', hull_m)
    lib.add_bevel(hull, 0.08)
    objs.append(hull)
    for sx in (-1, 1):
        objs.append(lib.box((0.75, 6.8, 0.95), (sx * 1.65, -0.1, 0.5), track_m, bevel=0.3, name=name + 'Track'))
        for k in range(6):
            objs.append(lib.cyl(0.36, 0.2, (sx * 2.03, -2.6 + k * 1.0, 0.48), P.steel(), rot=(0, math.radians(90), 0),
                                verts=24, name=name + 'Wheel'))
    tur = P.handbag((0, 0.2, 1.42), w=2.3, h=1.25, d=1.9, col='#6B3A1E', name=name + 'Turret')
    objs.append(tur)
    gun = lib.empty(name + 'Gun', loc=(0, -0.75, 2.0))
    lib.cyl(0.11, 3.2, (0, -1.6, 0), P.brass(), rot=(math.radians(90), 0, 0), verts=24, name=name + 'Barrel').parent = gun
    lib.cyl(0.17, 0.5, (0, -3.1, 0), P.brass(), rot=(math.radians(90), 0, 0), verts=24, name=name + 'Brake').parent = gun
    gun.rotation_euler.x = gun_up
    objs.append(gun)
    tx = P.text('БИРКИН-34', 0.32, (1.36, 0.0, 1.0), rot=(math.radians(90), 0, math.radians(90)),
                m=P.M('StencilWhite', '#E9E3D4', rough=0.8), font=P.SANS, extrude=0.002)
    objs.append(tx)
    e = P.group(name, objs, loc)
    e.rotation_euler.z = heading
    e['gun'] = gun.name
    return e


# ----------------------------------------------------------------------------- effects
def smoke_puffs(center, n=10, r=4.0, h=3.0, t0=0.0, t1=5.0, col='#8D8478', seed=3, grow=1.6, alpha=0.55):
    """Soft rising smoke: alpha-blended noisy spheres growing and drifting (no volumes, cheap in Eevee)."""
    rnd = random.Random(seed)
    m = bpy.data.materials.get('Smoke' + col)
    if not m:
        m = bpy.data.materials.new('Smoke' + col)
        m.use_nodes = True
        nt = m.node_tree
        p = nt.nodes['Principled BSDF']
        p.inputs['Base Color'].default_value = lib.C(col)
        p.inputs['Roughness'].default_value = 1.0
        nz = nt.nodes.new('ShaderNodeTexNoise')
        nz.inputs['Scale'].default_value = 2.5
        nz.inputs['Detail'].default_value = 6.0
        ramp = nt.nodes.new('ShaderNodeValToRGB')
        ramp.color_ramp.elements[0].position = 0.45
        ramp.color_ramp.elements[0].color = (0, 0, 0, 1)
        ramp.color_ramp.elements[1].position = 0.75
        ramp.color_ramp.elements[1].color = (alpha, alpha, alpha, 1)
        nt.links.new(nz.outputs['Fac'], ramp.inputs['Fac'])
        nt.links.new(ramp.outputs['Color'], p.inputs['Alpha'])
        m.surface_render_method = 'BLENDED'
    out = []
    for i in range(n):
        p0 = Vector(center) + Vector((rnd.uniform(-r, r), rnd.uniform(-r, r), rnd.uniform(0, h * 0.4)))
        ob = lib.sphere(rnd.uniform(0.8, 1.6), tuple(p0), m, segs=16, rings=8, name='Smoke')
        ob.visible_shadow = False
        lib.key_obj(ob, F(t0), loc=tuple(p0), scale=1.0, interp='LINEAR')
        lib.key_obj(ob, F(t1), loc=tuple(p0 + Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), h))), scale=grow,
                    interp='LINEAR')
        out.append(ob)
    return out


def flashes(loc, t0, t1, every=0.12, energy=900, col='#FFD39A', seed=0):
    rnd = random.Random(seed)
    L = lib.light('POINT', loc, energy=0, size=0.3, color=col)
    t = t0
    while t < t1:
        L.data.energy = energy * rnd.uniform(0.6, 1.0)
        L.data.keyframe_insert('energy', frame=F(t))
        L.data.energy = 0
        L.data.keyframe_insert('energy', frame=F(t + every * 0.5))
        t += every * rnd.uniform(0.8, 1.3)
    return L


def searchlights(n=4, z=0, spread=40, seed=2, y=30):
    rnd = random.Random(seed)
    for k in range(n):
        x = -spread / 2 + spread * k / max(1, n - 1)
        sp = lib.light('SPOT', (x, y, z + 1), energy=60000, spot=4, blend=0.3, size=0.3, color='#E8F0FF')
        a = rnd.uniform(-0.5, 0.5)
        sp.rotation_euler = (math.radians(rnd.uniform(15, 35)), 0, a)
        lib.key_obj(sp, F(0), rot=(sp.rotation_euler.x, 0, a), interp='LINEAR')
        lib.key_obj(sp, F(8), rot=(sp.rotation_euler.x, 0, a + rnd.uniform(-0.4, 0.4)), interp='LINEAR')


def war_sky():
    """Aggressive evening: deep blue-grey sky, a burning orange horizon, strong warm rim light."""
    if not P.hdri_world(0.9, rot=math.radians(200)):        # photographic sunset sky (Poly Haven CC0)
        lib.world_gradient('#2F3B52', '#D9763A', '#5A4436', strength=0.8)
    lib.light('SUN', rot=(math.radians(82), 0, math.radians(-30)), energy=2.6, color='#FFB070', size=1.5)


# ----------------------------------------------------------------------------- the enemy: boutique armies
# mike 29.10: «и добавь врагов на сцене». The enemy are shop mannequins in their brand's colours (no faces, no blood):
# KokoChanel — black and white with pearls, Hermès — orange with brown, the rest mixed. They hold handbags like
# shields; when they give up they wave white flags.
FACTIONS = {'chanel': ('#151515', '#F2EFE8'), 'hermes': ('#E8701E', '#5B3A1E'), 'mixed': ('#3D4A5C', '#7A2E2E')}


def enemy_squad(center, rows=3, cols=6, faction='chanel', heading=0.0, dx=0.9, dy=1.1, surrender_at=None, seed=1,
                flee=None):
    """Mannequin soldiers in ranks facing `heading` (front -Y at 0). surrender_at: time they raise white flags;
    flee=(t0, t1, dist): they run backwards (comic retreat)."""
    rnd = random.Random(seed)
    c1, c2 = FACTIONS[faction]
    m1 = P.M('Enemy' + faction + '1', c1, rough=0.7, var=0.08, bump=0.3, bs=200)
    m2 = P.M('Enemy' + faction + '2', c2, rough=0.6, var=0.05, bump=0.2, bs=200)
    pearl = P.M('Pearl', '#F3EEE6', rough=0.15, coat=0.8)
    fwd = Vector((math.sin(heading), -math.cos(heading), 0))
    right = Vector((math.cos(heading), math.sin(heading), 0))
    out = []
    for r in range(rows):
        for cc in range(cols):
            p = Vector(center) + right * ((cc - (cols - 1) / 2) * dx + rnd.uniform(-0.1, 0.1)) - fwd * (r * dy)
            e = P.mannequin(tuple(p), heading=heading, bag_col=c2 if rnd.random() < 0.6 else None, rnd=rnd,
                            name='Enemy')
            for ch in e.children:
                if ch.type == 'MESH' and ('Torso' in ch.name or 'Skirt' in ch.name):
                    ch.data.materials.clear()
                    ch.data.materials.append(m1 if ('Torso' in ch.name) == (cc % 2 == 0) else m2)
            cap = lib.cyl(0.13, 0.05, (0, 0, 1.75), m1, r2=0.14, name='EnemyCap')     # a pillbox hat
            cap.parent = e
            cap.location = (0, 0, 1.75)
            if faction == 'chanel':
                for k in range(8):
                    a = k * math.pi / 4
                    pr = lib.sphere(0.018, (0.12 * math.cos(a), 0.12 * math.sin(a) - 0.02, 1.42), pearl, segs=8, rings=4,
                                    name='EnemyPearl')
                    pr.parent = e
                    pr.location = (0.12 * math.cos(a), 0.12 * math.sin(a) - 0.02, 1.42)
            if surrender_at is not None:
                fl = lib.empty('WhiteFlagE', loc=(0, 0, 0))
                fl.parent = e
                fl.location = (0.25, -0.1, 1.2)
                lib.cyl(0.01, 0.9, (0, 0, 0.45), P.wood('#8A6A44', 'FlagStick'), name='Stick').parent = fl
                cl = lib.box((0.35, 0.005, 0.24), (0.18, 0, 0.78), P.cloth('#FAF8F4', 'WhiteCloth'), bevel=0, name='WCloth')
                cl.parent = fl
                t = surrender_at + rnd.uniform(0, 0.4)
                lib.key_obj(fl, F(0), scale=(0.001,) * 3)
                lib.key_obj(fl, F(t), scale=(0.001,) * 3)
                lib.key_obj(fl, F(t + 0.2), scale=(1, 1, 1))
                lib.add_sine(fl, 'rotation_euler', 1, 0.35, 0.5, phase=rnd.uniform(0, 6))
            if flee:
                t0, t1, dist = flee
                lib.key_obj(e, F(t0), loc=tuple(p))
                lib.key_obj(e, F(t1), loc=tuple(p - fwd * dist), interp='LINEAR')
                lib.add_sine(e, 'location', 2, 0.06, 0.3, phase=rnd.uniform(0, 6))
            out.append(e)
    return out


# ----------------------------------------------------------------------------- gag props (mike 29.10: «моментами пусто
# на сцене, добавь объекты, танки, дома разрушенные, пончики и там по угару что-нибудь»)
def donut(loc, r=1.2, rot=0.0, name='Donut'):
    dough = P.M('Dough', '#C98A4A', rough=0.6, var=0.12, bump=0.3, bs=20)
    glaze = P.M('Glaze', '#F07AAE', rough=0.25, coat=0.6, var=0.05)
    bpy.ops.mesh.primitive_torus_add(major_radius=r, minor_radius=r * 0.45, location=loc, major_segments=40,
                                     minor_segments=20)
    d = bpy.context.active_object
    d.name = name
    d.data.materials.append(dough)
    bpy.ops.object.shade_smooth()
    bpy.ops.mesh.primitive_torus_add(major_radius=r, minor_radius=r * 0.47, location=(loc[0], loc[1], loc[2] + r * 0.06),
                                     major_segments=40, minor_segments=20)
    g = bpy.context.active_object
    g.name = name + 'Glaze'
    g.data.materials.append(glaze)
    bpy.ops.object.shade_smooth()
    g.scale = (1, 1, 0.75)
    rnd = random.Random(int(loc[0] * 7 + loc[1] * 13))
    sp = [P.M('Sprinkle' + c, c, rough=0.4) for c in ('#F2E04B', '#5BC0EB', '#FFFFFF', '#7AD36B')]
    for k in range(40):
        a = rnd.uniform(0, 6.28)
        rr = r + rnd.uniform(-0.35, 0.35) * r
        s = lib.cyl(r * 0.03, r * 0.16, (loc[0] + rr * math.cos(a), loc[1] + rr * math.sin(a), loc[2] + r * 0.42),
                    sp[k % 4], rot=(math.radians(90), 0, rnd.uniform(0, 6)), verts=6, name='Sprinkle')
    d.rotation_euler = g.rotation_euler = (rot, 0, 0)
    return d


def giant_bag(loc, s=2.0, rot=0.0, col='#E8701E'):
    hb = P.handbag(loc, rot=rot, w=0.34 * s * 3, h=0.25 * s * 3, d=0.16 * s * 3, col=col, name='GiantBag')
    return hb


def perfume(loc, s=1.0):
    gl = lib.mat('PerfumeGlass', '#F4C7D8', rough=0.03, alpha=0.45)
    b = lib.box((0.9 * s, 0.5 * s, 1.1 * s), (loc[0], loc[1], loc[2] + 0.55 * s), gl, bevel=0.08 * s, name='Perfume')
    lib.box((0.75 * s, 0.38 * s, 0.7 * s), (loc[0], loc[1], loc[2] + 0.42 * s), P.M('PerfumeJuice', '#E8A23A', rough=0.1,
                                                                                    alpha=0.8), bevel=0.06 * s, name='Juice')
    lib.cyl(0.22 * s, 0.4 * s, (loc[0], loc[1], loc[2] + 1.3 * s), P.gold(), verts=24, name='PerfumeCap')
    return b


def shoe_boxes(loc, s=1.0, seed=0):
    rnd = random.Random(seed)
    for k in range(rnd.randint(3, 6)):
        c = rnd.choice(('#E9E1D2', '#151515', '#E8701E', '#F07AAE'))
        lib.box((1.2 * s, 0.7 * s, 0.45 * s), (loc[0] + rnd.uniform(-0.15, 0.15), loc[1] + rnd.uniform(-0.15, 0.15),
                                               loc[2] + 0.225 * s + k * 0.46 * s),
                P.M('ShoeBox' + c, c, rough=0.6, var=0.05), rot=(0, 0, rnd.uniform(-0.3, 0.3)), bevel=0.02, name='ShoeBox')


def lipstick(loc, s=1.0, tilt=0.0):
    e = lib.empty('Lipstick', loc=loc)
    lib.cyl(0.35 * s, 1.4 * s, (0, 0, 0.7 * s), P.gold(), verts=32, name='LipCase').parent = e
    lib.cyl(0.28 * s, 0.9 * s, (0, 0, 1.85 * s), P.M('LipRed', '#B3121F', rough=0.3, coat=0.5), verts=32,
            name='LipStick').parent = e
    e.rotation_euler = (tilt, 0, 0)
    return e


def ruin(loc, rnd, w=7, h=7):
    """A shelled house: walls with window holes, broken top, rubble heap, a burnt roof beam."""
    wall = P.M('Ruin', '#6E6256', rough=0.9, var=0.25, bump=0.4)
    x, y = loc[0], loc[1]
    for sx in (-1, 1):
        hh = h * rnd.uniform(0.5, 1.0)
        lib.box((0.4, 5, hh), (x + sx * w / 2, y, hh / 2), wall, bevel=0.05, name='RuinWall')
    hh = h * rnd.uniform(0.6, 1.0)
    lib.box((w, 0.4, hh), (x, y + 2.5, hh / 2), wall, bevel=0.05, name='RuinBack')
    lib.box((w * 0.6, 0.4, h * 0.45), (x - w * 0.2, y - 2.5, h * 0.225), wall, bevel=0.05, name='RuinFront')
    for k in range(3):
        lib.box((0.9, 0.5, 1.2), (x - w * 0.35 + k * 1.4, y - 2.5, h * 0.25), P.M('CraterDark', '#2A241E'), bevel=0,
                name='RuinHole')
    for k in range(12):
        lib.box((rnd.uniform(0.3, 0.9),) * 3, (x + rnd.uniform(-w / 2, w / 2), y + rnd.uniform(-3, 2), 0.2), wall,
                rot=(rnd.uniform(0, 3), rnd.uniform(0, 3), rnd.uniform(0, 3)), bevel=0.05, name='Rubble')
    lib.box((w * 0.9, 0.25, 0.25), (x, y, hh * 0.8), P.wood('#2A1C12', 'BurntBeam'), rot=(0, 0.35, 0), bevel=0,
            name='Beam')


def gag_scatter(center=(0, 20, 0), radius=30, n=18, keep=(0, 0, 6), seed=1, ruins=4, wrecks=2, sale=True, avoid=()):
    """Fill the empty middle ground: ruined houses, wrecked tanks and, for the laughs, giant donuts, handbags,
    perfume bottles, shoe-box stacks, lipsticks and «−90%» signs. Nothing inside `keep` (x, y, r)."""
    rnd = random.Random(seed)
    cx, cy, _ = center
    kx, ky, kr = keep

    def spot():
        for _ in range(40):
            x, y = cx + rnd.uniform(-radius, radius), cy + rnd.uniform(-radius * 0.5, radius)
            if (x - kx) ** 2 + (y - ky) ** 2 > kr ** 2 and all((x - ax) ** 2 + (y - ay) ** 2 > ar ** 2 for ax, ay, ar in avoid):
                return x, y
        return cx + radius, cy + radius
    for k in range(ruins):
        x, y = spot()
        ruin((x, y, 0), rnd, w=rnd.uniform(5, 8), h=rnd.uniform(5, 9))
    for k in range(wrecks):
        x, y = spot()
        t = tank((x, y, 0), heading=rnd.uniform(0, 6.28), name='Wreck%d' % k, gun_up=-0.25)
        t.rotation_euler.x = rnd.uniform(-0.15, 0.15)
        smoke_puffs((x, y, 2), n=4, r=1.0, h=8, t1=8, col='#3E3832', grow=2.0, seed=k + seed)
    kinds = ['donut', 'donut', 'bag', 'perfume', 'shoes', 'lipstick', 'sale']
    for k in range(n):
        x, y = spot()
        kind = kinds[k % len(kinds)] if sale or kinds[k % len(kinds)] != 'sale' else 'donut'
        if kind == 'donut':
            donut((x, y, rnd.choice((0.55, 1.2))), r=rnd.uniform(0.8, 1.5), rot=rnd.choice((0.0, math.radians(80))))
        elif kind == 'bag':
            giant_bag((x, y, 0), s=rnd.uniform(1.5, 2.6), rot=rnd.uniform(0, 6.28),
                      col=rnd.choice(('#E8701E', '#151515', '#8B3A1E', '#C99A3E')))
        elif kind == 'perfume':
            perfume((x, y, 0), s=rnd.uniform(1.0, 1.8))
        elif kind == 'shoes':
            shoe_boxes((x, y, 0), s=rnd.uniform(1.0, 1.6), seed=k)
        elif kind == 'lipstick':
            lipstick((x, y, 0), s=rnd.uniform(1.0, 1.6), tilt=rnd.choice((0.0, math.radians(75))))
        else:
            lib.cyl(0.06, 2.4, (x, y, 1.2), P.wood('#5A4632', 'OldWood'), name='SignStick')
            lib.box((1.6, 0.06, 0.9), (x, y - 0.05, 2.6), P.paper('#F6F1E8', 'Poster'), bevel=0, name='SaleBoard')
            P.text('−90%', 0.42, (x, y - 0.09, 2.6), m=P.M('PosterRed', '#C8202A', rough=0.6), font=P.SANS,
                   extrude=0.002)


def street_gags(seed=0, y0=0, y1=40):
    """Along both pavements of the Ermesovka street: small donuts, shoe-box stacks, perfume bottles, lipsticks."""
    rnd = random.Random(seed)
    for k in range(10):
        x = rnd.choice((-1, 1)) * 3.7
        y = rnd.uniform(y0, y1)
        r = rnd.random()
        if r < 0.4:
            donut((x, y, 0.33), r=0.5, rot=math.radians(80))
        elif r < 0.65:
            shoe_boxes((x, y, 0), s=0.7, seed=k + seed)
        elif r < 0.85:
            perfume((x, y, 0), s=0.6)
        else:
            lipstick((x, y, 0), s=0.6, tilt=math.radians(75))


def dress_battlefield(center=(0, 20, 0), radius=40, seed=5, keep=(0, 0, 6), dur=8.0, far=True, avoid=()):
    """mike 29.10: «и в целом на сцене тоже» (no empty feeling): craters, sandbag walls, barbed wire, burning houses
    and smoke columns on the horizon, telegraph poles, parked lorries and tank silhouettes. Nothing within `keep`
    (x, y, r) so the action stays clear."""
    rnd = random.Random(seed)
    cx, cy, _ = center
    kx, ky, kr = keep
    mud = P.M('Mud', '#4A4032')
    sand = P.M('Sandbag', '#9C8A64', rough=0.95, var=0.2, bump=0.5, bs=30)
    wire = P.M('Wire', '#3A3632', rough=0.6, metal=0.7)

    def free(x, y):
        return (x - kx) ** 2 + (y - ky) ** 2 > kr ** 2 and all((x - ax) ** 2 + (y - ay) ** 2 > ar ** 2 for ax, ay, ar in avoid)
    for k in range(18):                                  # craters
        x, y = cx + rnd.uniform(-radius, radius), cy + rnd.uniform(-radius * 0.6, radius)
        if not free(x, y):
            continue
        r = rnd.uniform(0.8, 2.2)
        lib.cyl(r, 0.12, (x, y, 0.03), mud, r2=r * 0.75, verts=24, name='CraterRim')
        lib.cyl(r * 0.72, 0.02, (x, y, 0.07), P.M('CraterDark', '#2A241E', rough=0.9), verts=24, name='CraterHole')
    for k in range(7):                                   # sandbag walls
        x, y = cx + rnd.uniform(-radius * 0.7, radius * 0.7), cy + rnd.uniform(-radius * 0.3, radius * 0.6)
        if not free(x, y):
            continue
        a = rnd.uniform(0, math.pi)
        for i in range(8):
            for j in range(2):
                bx = x + math.cos(a) * (i - 4) * 0.55 + (0.27 if j else 0) * math.cos(a)
                by = y + math.sin(a) * (i - 4) * 0.55 + (0.27 if j else 0) * math.sin(a)
                o = lib.sphere(0.3, (bx, by, 0.15 + j * 0.24), sand, scale=(1, 0.55, 0.45), segs=12, rings=6, name='Sandbag')
                o.rotation_euler.z = a
    for k in range(5):                                   # barbed wire on X-posts
        x, y = cx + rnd.uniform(-radius * 0.8, radius * 0.8), cy + rnd.uniform(-radius * 0.2, radius * 0.7)
        if not free(x, y):
            continue
        pts = []
        for i in range(9):
            px = x - 4 + i
            lib.box((0.06, 0.06, 1.2), (px, y, 0.5), P.wood('#4A3A2A', 'PostWood'), rot=(0.4, 0, 0), bevel=0, name='WirePost')
            pts += [(px, y, 0.9), (px + 0.5, y, 0.55)]
        P.tube(pts, 0.008, wire, 'Wire')
    for k in range(10):                                  # telegraph poles along a line
        x = cx - radius + k * radius / 5
        lib.cyl(0.1, 7, (x, cy + radius * 0.8, 3.5), P.wood('#4A3A2A', 'PostWood'), name='Pole')
        lib.box((1.6, 0.08, 0.08), (x, cy + radius * 0.8, 6.6), P.wood('#4A3A2A', 'PostWood'), bevel=0, name='PoleArm')
    if far:                                              # burning houses and smoke columns on the horizon
        for k in range(8):
            x = cx + rnd.uniform(-radius * 1.5, radius * 1.5)
            y = cy + radius * rnd.uniform(1.4, 2.0)
            w, h = rnd.uniform(5, 9), rnd.uniform(5, 11)
            lib.box((w, 6, h), (x, y, h / 2), P.M('Ruin', '#6E6256', rough=0.9, var=0.25, bump=0.4), bevel=0.1, name='Ruin')
            if k % 2 == 0:
                lib.light('POINT', (x, y - 3.5, h * 0.6), energy=6000, size=2.0, color='#FF8A3A')
                smoke_puffs((x, y, h), n=6, r=2.5, h=14, t1=dur, col='#3E3832', grow=2.4, seed=k + seed)
        for k in range(4):
            tk = tank((cx + rnd.uniform(-radius, radius), cy + radius * rnd.uniform(1.0, 1.3), 0),
                      heading=rnd.uniform(-0.4, 0.4), name='FarTank%d' % k)
        for k in range(3):
            P.truck40((cx + rnd.uniform(-radius, radius), cy + radius * rnd.uniform(0.6, 0.9), 0),
                      heading=rnd.uniform(0, 6.28), name='FarLorry%d' % k)
    # the middle ground is never empty (mike 29.10): ruins, wrecks and the gag props
    gag_scatter(center, radius * 0.75, n=16, keep=keep, seed=seed + 100, ruins=4 if far else 2, wrecks=2, avoid=avoid)


# ----------------------------------------------------------------------------- the war room (Ставка)
def map_table(center=(0, 0, 0.9), conq=None, arrows=(), labels=True, tokens=True):
    """The brand map of Europe on a big oak table; an orange conquest layer that spreads from Biркинштат when the
    object property 'conq' goes 0..1; arrows (from, to, t0, t1) that draw themselves; tiny baroness figurines."""
    c = Vector(center)
    lib.box((MAP_W + 0.6, MAP_H + 0.6, 0.12), (c.x, c.y, c.z - 0.07), P.wood('#4A2C17', 'OakTable'), bevel=0.03,
            name='Table')
    for sx in (-1, 1):
        for sy in (-1, 1):
            lib.box((0.16, 0.16, c.z - 0.13), (c.x + sx * (MAP_W / 2 + 0.1), c.y + sy * (MAP_H / 2 + 0.1), (c.z - 0.13) / 2),
                    P.wood('#4A2C17', 'OakTable'), bevel=0.02, name='Leg')
    m = bpy.data.materials.new('MapPaper')
    m.use_nodes = True
    nt = m.node_tree
    p = nt.nodes['Principled BSDF']
    img = nt.nodes.new('ShaderNodeTexImage')
    img.image = bpy.data.images.load(os.path.join(TEX, 'europe_political.jpg'), check_existing=True)
    col = img.outputs['Color']
    if conq is not None:     # orange conquest: distance from the capital (noise-distorted) under the 'conq' radius
        tc = nt.nodes.new('ShaderNodeTexCoord')
        u0, v0 = PLACES['Биркинштат']
        sep = nt.nodes.new('ShaderNodeSeparateXYZ')
        nt.links.new(tc.outputs['UV'], sep.inputs['Vector'])
        dx = nt.nodes.new('ShaderNodeMath'); dx.operation = 'SUBTRACT'
        nt.links.new(sep.outputs['X'], dx.inputs[0]); dx.inputs[1].default_value = u0
        dy = nt.nodes.new('ShaderNodeMath'); dy.operation = 'SUBTRACT'
        nt.links.new(sep.outputs['Y'], dy.inputs[0]); dy.inputs[1].default_value = v0
        cmb = nt.nodes.new('ShaderNodeCombineXYZ')
        nt.links.new(dx.outputs[0], cmb.inputs['X'])
        dy2 = nt.nodes.new('ShaderNodeMath'); dy2.operation = 'MULTIPLY'
        nt.links.new(dy.outputs[0], dy2.inputs[0]); dy2.inputs[1].default_value = MAP_H / MAP_W
        nt.links.new(dy2.outputs[0], cmb.inputs['Y'])
        ln = nt.nodes.new('ShaderNodeVectorMath'); ln.operation = 'LENGTH'
        nt.links.new(cmb.outputs[0], ln.inputs[0])
        nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 6.0
        nt.links.new(tc.outputs['UV'], nz.inputs['Vector'])
        wob = nt.nodes.new('ShaderNodeMath'); wob.operation = 'MULTIPLY_ADD'
        nt.links.new(nz.outputs['Fac'], wob.inputs[0]); wob.inputs[1].default_value = 0.12
        nt.links.new(ln.outputs['Value'], wob.inputs[2])
        at = nt.nodes.new('ShaderNodeAttribute'); at.attribute_type = 'OBJECT'; at.attribute_name = 'conq'
        rad = nt.nodes.new('ShaderNodeMath'); rad.operation = 'MULTIPLY'
        nt.links.new(at.outputs['Fac'], rad.inputs[0]); rad.inputs[1].default_value = 1.05
        lt = nt.nodes.new('ShaderNodeMath'); lt.operation = 'LESS_THAN'
        nt.links.new(wob.outputs[0], lt.inputs[0]); nt.links.new(rad.outputs[0], lt.inputs[1])
        mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'; mix.blend_type = 'MULTIPLY'
        fac = nt.nodes.new('ShaderNodeMath'); fac.operation = 'MULTIPLY'
        nt.links.new(lt.outputs[0], fac.inputs[0]); fac.inputs[1].default_value = 1.0
        nt.links.new(fac.outputs[0], mix.inputs['Factor'])
        nt.links.new(col, mix.inputs[6]); mix.inputs[7].default_value = lib.C('#E8650F')
        col = mix.outputs[2]
    nt.links.new(col, p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = 0.85
    mp = P.uv_plane((MAP_W, MAP_H), (c.x, c.y, c.z + 0.001), m=m, name='Map')
    mp['conq'] = 0.0
    if conq is not None:
        for t, v in conq:
            mp['conq'] = v
            mp.keyframe_insert('["conq"]', frame=F(t))
    ink = P.M('MapInk', '#2A1A10', rough=0.8)
    if labels:
        for nm in PLACES:
            p3 = mxy(nm, c.z + 0.004, (c.x, c.y))
            P.text(nm.upper(), 0.07, tuple(p3 + Vector((0, 0.07, 0))), rot=(0, 0, 0), m=ink, font=P.SERIF, extrude=0.0008)
            lib.cyl(0.025, 0.01, tuple(p3), P.M('MapPin', '#9E1B1B', rough=0.4), name='Pin')
    red = P.M('ArrowRed', '#B3261E', rough=0.5, emit='#B3261E', emit_strength=0.3)
    for k, (a, b, t0, t1) in enumerate(arrows):
        pa, pb = mxy(a, c.z + 0.012, (c.x, c.y)), mxy(b, c.z + 0.012, (c.x, c.y))
        mid = (pa + pb) / 2 + Vector((0, 0.18, 0))
        pts = [tuple(pa.lerp(mid, s / 6)) if s <= 6 else None for s in range(7)] + \
              [tuple(mid.lerp(pb, s / 6)) for s in range(1, 7)]
        pts = [q for q in pts if q]
        cu = lib.curve_poly('Arrow%d' % k, [pts], bevel=0.025, mat_=red, res=6)
        cu.data.bevel_factor_end = 0.0
        cu.data.keyframe_insert('bevel_factor_end', frame=F(t0))
        cu.data.bevel_factor_end = 1.0
        cu.data.keyframe_insert('bevel_factor_end', frame=F(t1))
        head = lib.cyl(0.07, 0.12, tuple(pb), red, r2=0.0, verts=3, rot=(0, math.radians(90), 0), name='ArrowHead')
        d = pb - Vector(pts[-2])
        head.rotation_euler = (0, math.radians(90), 0)
        head.rotation_euler.z = math.atan2(d.y, d.x)
        head.scale = (0.001,) * 3
        head.keyframe_insert('scale', frame=F(t1 - 0.05))
        head.scale = (1, 1, 1)
        head.keyframe_insert('scale', frame=F(t1 + 0.1))
    if tokens:   # mike 29.10: «чтобы не было ощущения пустоты на карте» -> fronts of figurines, tank tokens, flags
        rnd = random.Random(7)
        me = army_mesh('strict')
        fronts = [('Биркинштат', 14), ('Эрмесовка', 18), ('Прада-на-Дону', 10), ('Луивиттония', 12), ('Гучийск', 8),
                  ('Эрмес', 8), ('КокоШанель', 8)]
        for nm, n in fronts:
            p0 = mxy(nm, c.z + 0.003, (c.x, c.y))
            for i in range(n):           # a little formation round each place, facing west
                off = Vector(((i % 5) * 0.045 - 0.09, -0.06 - (i // 5) * 0.05, 0))
                soldier(me, tuple(p0 + off + Vector((rnd.uniform(-0.01, 0.01), rnd.uniform(-0.01, 0.01), 0))),
                        math.radians(-90) + rnd.uniform(-0.2, 0.2), 0.045, name='Figurine')
            tk = tank(tuple(p0 + Vector((0.16, 0.02, 0))), heading=math.radians(-90), name='TankToken')
            tk.scale = (0.022,) * 3
            pin = lib.cyl(0.004, 0.14, tuple(p0 + Vector((-0.05, 0.05, 0.07))), P.steel(), name='FlagPin')
            fl = lib.box((0.07, 0.002, 0.045), tuple(p0 + Vector((-0.015, 0.05, 0.12))),
                         P.cloth('#E8701E', 'MapFlag'), bevel=0, name='MapFlag')
        # the enemy on the map too: black-and-white and blue tokens west of each brand-land, a few already knocked over
        for nm, col in (('КокоШанель', '#151515'), ('Эрмес', '#E8EDF2'), ('Луивиттония', '#2F3E5C'), ('Гучийск', '#2F5C3A')):
            p0 = mxy(nm, c.z + 0.003, (c.x, c.y))
            for i in range(6):
                tk = lib.cyl(0.012, 0.05, tuple(p0 + Vector((-0.12 - (i % 3) * 0.035, 0.03 - (i // 3) * 0.04, 0.025))),
                             P.M('EnemyToken' + col, col, rough=0.4, coat=0.4), name='EnemyToken')
                lib.sphere(0.014, (0, 0, 0.032), P.M('EnemyToken' + col, col), segs=10, rings=6, name='EnemyHead').parent = tk
                if i == 5:
                    tk.rotation_euler = (math.radians(90), 0, rnd.uniform(0, 6))
        cme = P.coupon_mesh()
        if not cme.materials:
            cme.materials.append(P.tag_mats()[0])
        for k in range(70):              # coupons and price tags spilled over the map
            cp = bpy.data.objects.new('MapCoupon', cme)
            bpy.context.scene.collection.objects.link(cp)
            cp.location = (c.x + rnd.uniform(-MAP_W / 2, MAP_W / 2) * 0.95, c.y + rnd.uniform(-MAP_H / 2, MAP_H / 2) * 0.95,
                           c.z + 0.003)
            cp.rotation_euler = (math.radians(90), 0, rnd.uniform(0, 6.3))
            cp.scale = (0.7,) * 3
            cp.material_slots[0].link = 'OBJECT'
            cp.material_slots[0].material = P.tag_mats()[k % 4]
        # the table edge: field telephone, binoculars, compasses, folders, a glass of tea, a pencil, dust bags
        e = c + Vector((MAP_W / 2 + 0.05, 0, 0))
        lib.box((0.22, 0.16, 0.1), (c.x - MAP_W / 2 + 0.2, c.y - MAP_H / 2 + 0.15, c.z + 0.05), P.leather('#3A2A1E', 'PhoneBox'),
                bevel=0.02, name='FieldPhone')
        lib.cyl(0.02, 0.2, (c.x - MAP_W / 2 + 0.2, c.y - MAP_H / 2 + 0.15, c.z + 0.12), P.M('Bakelite', '#141210', rough=0.3),
                rot=(0, math.radians(90), 0), name='Receiver')
        for sx in (-1, 1):
            lib.cyl(0.035, 0.12, (c.x + MAP_W / 2 - 0.3 + sx * 0.04, c.y - MAP_H / 2 + 0.12, c.z + 0.035),
                    P.M('Bakelite', '#141210'), rot=(math.radians(90), 0, 0), name='Binocular')
        for k in range(3):
            lib.box((0.3, 0.22, 0.012 + k * 0.004), (c.x + 1.0 - k * 0.05, c.y + MAP_H / 2 - 0.12, c.z + 0.01 + k * 0.012),
                    P.paper(['#C9B48A', '#D8CFB8', '#B9A27A'][k], 'Folder%d' % k), bevel=0.003, name='Folder')
        lib.cyl(0.03, 0.09, (c.x - 1.2, c.y + MAP_H / 2 - 0.1, c.z + 0.045), lib.mat('TeaGlass', '#C9D6DA', rough=0.03, alpha=0.4),
                name='TeaGlass')
        lib.cyl(0.026, 0.06, (c.x - 1.2, c.y + MAP_H / 2 - 0.1, c.z + 0.03), P.M('Tea', '#6B3A1A', rough=0.05), name='Tea')
        lib.cyl(0.004, 0.18, (c.x + 0.2, c.y - 0.6, c.z + 0.004), P.M('PencilRed', '#B3261E', rough=0.5),
                rot=(0, math.radians(90), 0.4), name='Pencil')
        for k in range(2):
            lib.cyl(0.003, 0.16, (c.x - 0.6 + k * 0.03, c.y + 0.4, c.z + 0.02), P.steel(),
                    rot=(0, math.radians(84), 0.3 + k * 0.4), name='Compass')
        for k in range(3):
            P.dust_bag((c.x + MAP_W / 2 - 0.25, c.y + 0.6 - k * 0.3, c.z), w=0.12, h=0.14, flat=0.4, seed=k, name='MiniBag')
    return mp


def hq_room():
    """The Ставка: dark panelled walls, a big map on the wall, green lamps over the table, red drapes."""
    wall = P.M('HQPanel', '#3B2A1E', rough=0.6, var=0.12, bump=0.15)
    lib.plane((14, 14), (0, 0, 0), P.wood('#3A2414', 'HQFloor'), name='Floor')
    lib.box((14, 0.2, 5), (0, 5, 2.5), wall, bevel=0, name='Back')
    for sx in (-1, 1):
        lib.box((0.2, 14, 5), (sx * 7, 0, 2.5), wall, bevel=0, name='Side')
        lib.box((1.4, 0.15, 4.2), (sx * 4.6, 4.85, 2.4), P.cloth('#6E1416', 'Drape'), bevel=0.2, name='Drape')
    wm = bpy.data.materials.new('WallMap')
    wm.use_nodes = True
    im = wm.node_tree.nodes.new('ShaderNodeTexImage')
    im.image = bpy.data.images.load(os.path.join(TEX, 'europe_political.jpg'), check_existing=True)
    wm.node_tree.links.new(im.outputs['Color'], wm.node_tree.nodes['Principled BSDF'].inputs['Base Color'])
    P.uv_plane((5.5, 5.0), (0, 4.88, 2.6), rot=(math.radians(90), 0, 0), m=wm, name='WallMap')
    for x in (-1.0, 1.0):
        lamp = lib.cyl(0.35, 0.25, (x, 0, 2.6), P.M('LampGreen', '#1F4A2C', rough=0.3, coat=0.6), r2=0.12,
                       name='Lamp')
        lib.light('SPOT', (x, 0, 2.45), rot=(0, 0, 0), energy=160, spot=80, blend=0.9, size=0.6, color='#FFD9A0')
    # soft overall light: the map and the generals must read (v2 test: the room was a black hole with two hot spots)
    lib.light('AREA', (0, -1.0, 3.6), energy=420, size=5.0, color='#FFE2C0')
    lib.light('AREA', (0, 4.0, 3.0), rot=(math.radians(-60), 0, 0), energy=220, size=5.0, color='#C9D6FF')


def generals(n=6, table_c=(0, 0, 0.9), faint=None):
    """Baroness-generals round the map table (all the same face — the joke); one may faint (falls back)."""
    me = army_mesh('stand')
    out = []
    for k in range(n):
        side = -1 if k < n // 2 else 1
        y = -0.9 + (k % (n // 2)) * 0.9
        ob = soldier(me, (table_c[0] + side * (MAP_W / 2 + 0.75), table_c[1] + y, 0), side * math.pi / 2,
                     name='General%d' % k)
        out.append(ob)
    if faint is not None and out:
        g = out[1]
        t = faint
        lib.key_obj(g, F(t), rot=(0, 0, g.rotation_euler.z))
        lib.key_obj(g, F(t + 0.5), rot=(0, math.radians(-85), g.rotation_euler.z), loc=(g.location.x - 0.4, g.location.y, 0.25))
        lib.key_obj(g, F(t + 0.65), rot=(0, math.radians(-90), g.rotation_euler.z), loc=(g.location.x - 0.9, g.location.y, 0.25))
    return out


# ----------------------------------------------------------------------------- scenes
def s_hook(shot):
    """«Скидки кончились!» — she shouts on a hill at dusk, a line of coupon guns fires behind her, the army below."""
    war_sky()
    lib.plane((400, 400), (0, 0, 0), P.M('Mud', '#4A4032', rough=0.95, var=0.3, bump=0.6, vs=0.4), name='Ground')
    b = S.baroness((0, 0, 0), 0.0, 'hand_up')
    S.poses(b, [(0.0, B.P('hand_up', head=(0, -12, 0))), (0.6, B.P('point', head=(0, -6, 0))),
                (shot['dur'], B.P('point', head=(4, -4, 0)))])
    rnd = random.Random(1)
    for k in range(5):
        g = P.coupon_gun((-6 + k * 3, 6, 0.6), rot=math.pi + rnd.uniform(-0.2, 0.2), name='Gun%d' % k, carriage=True)
        bpy.context.scene.frame_set(1)
        mz = P.muzzle_world(g)
        P.flying_paper(50, mz, (0, 9, 6), 0.3 + k * 0.05, shot['dur'], spread=0.25, life=1.6, seed=k)
        flashes(tuple(mz), 0.3, shot['dur'], seed=k)
    me = army_mesh('strict')
    march_block(me, (-8, 30, 0), 6, 14, heading=0.0, t0=0, t1=shot['dur'], speed=0.0, seed=4)
    smoke_puffs((0, 14, 0), n=14, r=10, h=4, t1=shot['dur'], col='#6E655B')
    dress_battlefield((0, 24, 0), 40, seed=11, keep=(0, 0, 5), dur=shot['dur'])
    enemy_squad((0, 26, 0), 3, 14, 'mixed', heading=0.0, dx=1.0, seed=61)
    S.fog(0.012, '#B98A66', size=(200, 200, 40), z=15)
    lib.light('AREA', (1.2, -1.8, 2.4), energy=180, size=1.2, color='#FFC890')
    S.cam(shot, (0.3, -1.6, 1.4), (0.2, -1.25, 1.45), (0, 0, 1.5), (0, 0, 1.52), lens=40, dof=(0, -0.05, 1.5), fstop=2.8)
    return dict(fill=0.2, exposure=0.1)


def s_conquest_night(shot):
    """«За одну ночь она захватила пол-Европы» — top-down map, orange spreads west over the night."""
    lib.world_color('#1E1A16', 0.4)
    map_table(conq=[(0.2, 0.0), (shot['dur'] - 0.4, 0.62)],
              arrows=[('Биркинштат', 'Эрмесовка', 0.5, 1.6), ('Эрмесовка', 'Луивиттония', 1.5, 2.6),
                      ('Луивиттония', 'КокоШанель', 2.4, 3.4)], tokens=True)
    lib.light('AREA', (0, 0, 4.2), energy=380, size=4.0, color='#FFE0B0')
    S.cam(shot, (0.6, -0.6, 3.9), (0.3, -0.3, 3.3), (0.3, 0.1, 0.9), (0.1, 0.15, 0.9), lens=35)
    return dict(fill=0.15, exposure=0.2)


def s_coupon_rain(shot):
    """«Без единого патрона. Только купоны.» — night town, coupons pour down like a blizzard."""
    war_sky()
    rnd = random.Random(5)
    S._ermesovka(rnd, garlands=False, lit=0.4)
    street_gags(1, 0, 30)
    P.drifting_paper(380, (-8, -6, 0.5), (8, 30, 12), 0, shot['dur'], seed=21, fall=1.6)
    searchlights(4, y=40, spread=30)
    S.fog(0.01, '#C08A60')
    S.cam(shot, (0, -10, 1.6), (0, -7, 2.6), (0, 14, 6), (0, 16, 7), lens=35)
    return dict(fill=0.25, exposure=0.15)


def s_hq_exterior(shot):
    """«Год сорок какой-то» — the Ставка building at dusk, lorries, sentries (baronesses), flags."""
    war_sky()
    P.cobbles((80, 80), (0, 0, 0), col='#6E665C')
    st = P.M('HQStone', '#B9A890', rough=0.8, var=0.1, bump=0.25, bs=10)
    lib.box((26, 10, 12), (0, 16, 6), st, bevel=0.1, name='HQ')
    for k in range(8):
        lib.cyl(0.55, 9, (-10.5 + k * 3, 10.6, 4.5), st, verts=24, name='Column')
    lib.box((27, 11, 1.2), (0, 16, 12.6), st, bevel=0.1, name='Cornice')
    P.text('СТАВКА', 1.0, (0, 10.4, 10.5), m=P.gold(), font=P.SERIF, extrude=0.05)
    for x in (-8, 8):
        P.flag((x, 9.8, 0), size=(2.4, 1.6), stripes=('#E8701E', '#F3EEE4', '#6B4226'), pole=8, name='HQFlag')
    P.truck40((-6, 2, 0), heading=math.radians(90), name='Lorry')
    P.truck40((7, -1, 0), heading=math.radians(-80), name='Lorry2', col='#5A6244')
    me = army_mesh('strict')
    for x in (-2.2, 2.2):
        soldier(me, (x, 9.8, 0), math.pi, name='Sentry')
    # the square is full: two standing blocks of baronesses, a third marching past, more lorries and a tank
    march_block(me, (-7, 5, 0), 4, 6, heading=math.pi, t0=0, t1=shot['dur'], speed=0.0, seed=51)
    march_block(me, (7, 5, 0), 4, 6, heading=math.pi, t0=0, t1=shot['dur'], speed=0.0, seed=52)
    march_block(me, (-14, -2, 0), 3, 4, heading=math.radians(-90), t0=0, t1=shot['dur'], speed=1.2, seed=53)
    P.truck40((12, 3, 0), heading=math.radians(100), name='Lorry3')
    tank((-13, 8, 0), heading=math.radians(150), name='HQTank')
    for x in (-12, 12):
        P.street_lamp((x, 0, 0), lit=True)
    searchlights(3, y=24, spread=20)
    gag_scatter((0, 0, 0), 22, n=10, keep=(0, 4, 13), seed=82, ruins=2, wrecks=1)
    S.fog(0.008, '#C08A60')
    S.cam(shot, (-6, -14, 1.8), (-3, -11, 3.4), (0, 12, 6), (0, 12, 7), lens=35)
    return dict(fill=0.3, exposure=0.15)


def s_hq_map(shot, conq=0.1, arrows=(), cam_close=False, faint=None):
    hq_room()
    mp = map_table(conq=[(0, conq), (shot['dur'], conq)], arrows=arrows)
    generals(6, faint=faint)
    if cam_close:
        S.cam(shot, (-0.3, -1.3, 1.9), (0.1, -1.0, 1.6), (0.0, 0.1, 0.9), (0.3, 0.2, 0.9), lens=40, dof=(0.1, 0.1, 0.9),
              fstop=4)
    else:
        S.cam(shot, (2.8, -4.2, 2.6), (2.0, -3.6, 2.4), (0, 0, 0.9), (0, 0.2, 0.9), lens=32)
    return dict(fill=0.2, exposure=0.15)


def s_hq_line(shot, line='chek'):
    """The baroness speaking at the head of the table: close, hard side light, generals blurred behind."""
    hq_room()
    map_table(conq=[(0, 0.1), (shot['dur'], 0.1)], labels=False, tokens=False)
    generals(6)
    b = S.baroness((0, -MAP_H / 2 - 0.7, 0), 0.0, 'strict')
    d = shot['dur']
    if line == 'chek':
        S.poses(b, [(0.3, B.P('strict', head=(-10, 4, 0))), (d, B.P('strict', head=(8, 2, 0)))])
    elif line == 'order':
        S.poses(b, [(0.2, B.P('point', head=(0, -6, 0))), (d, B.P('point', head=(4, -4, 0)))])
    else:
        S.poses(b, [(0.2, B.P('hand_up', head=(0, -10, 0))), (d, B.P('hand_up', head=(0, -6, 0)))])
    lib.light('AREA', (1.1, -2.2, 1.9), energy=90, size=1.0, color='#FFD3A0')
    lib.light('AREA', (-1.0, -0.8, 2.0), energy=70, size=0.8, color='#9FB6FF')
    for o in bpy.data.objects:
        if o.type == 'LIGHT' and o.data.type == 'AREA':
            lib.look_at(o, (0, -MAP_H / 2 - 0.7, 1.5))
    y0 = -MAP_H / 2 - 0.7
    S.cam(shot, (0.25, y0 - 1.3, 1.55), (0.15, y0 - 1.0, 1.55), (0, y0, 1.5), (0, y0, 1.51), lens=60,
          dof=(0, y0 - 0.08, 1.52), fstop=2.2)
    return dict(fill=0.1, exposure=-0.05)


def s_army(shot):
    """«Через сутки у неё армия. Сто тысяч баронесс.» — crane over endless marching blocks, tanks, flags, smoke."""
    war_sky()
    lib.plane((600, 600), (0, 0, 0), P.M('Field', '#5C5638', rough=0.95, var=0.3, bump=0.5, vs=0.2), name='Ground')
    lib.plane((14, 400), (0, 100, 0.01), P.M('Road', '#6E6252', rough=0.95, var=0.25, bump=0.4), name='Road')
    me = army_mesh('strict')
    d = shot['dur']
    for k in range(4):
        march_block(me, (-3.5 if k % 2 else 3.5, 4 + (k // 2) * 22, 0), 12, 6, heading=0.0, t0=0, t1=d, speed=1.1, seed=k)
    for k in range(3):
        tank((-11, 6 + k * 14, 0), heading=0.0, name='Tank%d' % k)
    for k in range(6):
        P.flag((7.5, 3 + k * 9, 0), size=(1.8, 1.2), stripes=('#E8701E', '#F3EEE4', '#6B4226'), pole=4, name='ArmyFlag%d' % k)
    smoke_puffs((0, 60, 0), n=12, r=30, h=8, t1=d, col='#6E655B')
    for sx in (-1, 1):            # both roadsides: ruins, wrecks, donuts, giant bags
        gag_scatter((sx * 26, 40, 0), 14, n=10, keep=(0, 40, 0.1), seed=70 + sx, ruins=3, wrecks=1)
    S.fog(0.008, '#B98A66', size=(400, 400, 60), z=25)
    S.cam(shot, (12, -14, 7), (9, -9, 4.5), (0, 20, 1.5), (0, 22, 1.4), lens=32)
    return dict(fill=0.25, exposure=0.15)


def s_identical(shot):
    """«Все одинаковые. Даже мама путает.» — dolly along a front rank of identical faces."""
    war_sky()
    lib.plane((200, 200), (0, 0, 0), P.cobbles((1, 1), (0, 0, -5)).active_material, name='Square')
    me = army_mesh('strict')
    for k in range(14):
        soldier(me, (-7 + k * 0.95, 0, 0), 0.0, name='Rank')
    for r in range(1, 5):
        for k in range(14):
            soldier(me, (-7 + k * 0.95 + (r % 2) * 0.3, r * 1.1, 0), 0.0, name='Rank')
    lib.light('AREA', (0, -4, 4), energy=600, size=6, color='#FFD3A0')
    S.cam(shot, (-5.5, -1.6, 1.55), (1.5, -1.6, 1.55), (-4.5, 0, 1.5), (2.5, 0, 1.5), lens=50, dof=1.6, fstop=2.8)
    return dict(fill=0.2, exposure=0.05)


def s_tank(shot):
    """«Танки „Биркин-34“» — low angle, the handbag-turret tank rolls at the camera through smoke."""
    war_sky()
    lib.plane((400, 400), (0, 0, 0), P.M('Mud', '#4A4032', rough=0.95, var=0.3, bump=0.6, vs=0.4), name='Ground')
    t = tank((0, 9, 0), heading=0.0, name='Tank')
    d = shot['dur']
    lib.key_obj(t, F(0), loc=(0, 9, 0), interp='LINEAR')
    lib.key_obj(t, F(d), loc=(0, 9 - 1.4 * d, 0), interp='LINEAR')
    for k in range(2):
        t2 = tank((-9 + k * 18, 26, 0), heading=0.0, name='TankB%d' % k)
        lib.key_obj(t2, F(0), loc=t2.location.copy(), interp='LINEAR')
        lib.key_obj(t2, F(d), loc=(t2.location.x, 26 - 2.0 * d, 0), interp='LINEAR')
    smoke_puffs((0, 18, 0), n=14, r=10, h=4, t1=d, col='#5C554D')
    dress_battlefield((0, 22, 0), 36, seed=12, keep=(0, 6, 7), dur=d)
    S.fog(0.012, '#B98A66', size=(200, 200, 40), z=15)
    S.cam(shot, (3.2, -1.5, 0.6), (2.6, -0.8, 0.7), (0, 7, 1.8), (0, 5, 1.7), lens=24)
    return dict(fill=0.2, exposure=0.1)


def s_tank_queue(shot):
    """«Очередь на танк — шесть лет.» — a tank showroom; baronesses queue round the block under a sign."""
    war_sky()
    P.cobbles((80, 80), (0, 0, 0), col='#6E665C')
    lib.box((16, 10, 7), (0, 12, 3.5), P.M('Showroom', '#D9C7A8', rough=0.8, var=0.1), bevel=0.05, name='Showroom')
    lib.box((10, 0.1, 4.5), (0, 6.95, 2.4), lib.mat('ShowGlass', '#FFE7C4', emit='#FFD9A8', emit_strength=1.4), bevel=0,
            name='ShowWindow')
    tank((0, 9.5, 0), heading=math.radians(200), name='DisplayTank')
    lib.box((11, 0.3, 1.3), (0, 6.8, 6.0), P.wood('#3A2516', 'SignWood'), bevel=0.03, name='Sign')
    P.text('ОЧЕРЕДЬ НА ТАНК: 6 ЛЕТ', 0.55, (0, 6.62, 6.0), m=P.gold(), font=P.SANS, extrude=0.01)
    me = army_mesh('stand')
    rnd = random.Random(8)
    for k in range(40):
        a = k * 0.42
        x, y = -6 + k * 0.7, 4.5 - 0.35 * math.sin(a)
        if x > 7:
            x, y = 7 + (x - 7) * 0.2, 4.5 - (k - 18) * 0.7
        soldier(me, (x, y, 0), math.radians(90) + rnd.uniform(-0.2, 0.2), name='Q')
    gag_scatter((0, 0, 0), 18, n=8, keep=(0, 6, 9), seed=84, ruins=1, wrecks=1)
    S.cam(shot, (-9, -6, 2.2), (-6, -5, 2.6), (2, 7, 3), (3, 7, 3.4), lens=32)
    return dict(fill=0.3, exposure=0.15)


def s_load(shot):
    """«Пулемёты зарядить купонами!» — her order, close; then baroness-gunners feed coupon belts (cut in v2 storyboard)."""
    return s_hq_line(shot, 'order')


def s_heels(shot):
    """«Медленно. Каблуки.» — close on marching legs: army boots... with high heels, slow-motion through the mud."""
    war_sky()
    lib.plane((60, 60), (0, 0, 0), P.M('Mud', '#4A4032', rough=0.95, var=0.3, bump=0.6, vs=0.4), name='Ground')
    me = army_mesh('stand')
    march_block(me, (0, 3, 0), 3, 5, dx=0.9, dy=1.2, heading=0.0, t0=0, t1=shot['dur'], speed=0.35, seed=3, bob=0.02)
    leather = P.leather('#3B1E0E', 'HeelLeather')
    for o in [o for o in bpy.data.objects if o.name.startswith('Soldier')]:
        for sx in (-0.1, 0.1):          # a slim heel under each boot (the joke)
            h = lib.cyl(0.018, 0.11, (sx, 0.08, 0.055), leather, name='Heel')
            h.parent = o
    S.cam(shot, (0.6, -0.6, 0.25), (0.5, -0.5, 0.22), (0, 2.6, 0.18), (0, 2.2, 0.18), lens=85, dof=(0, 2.5, 0.15),
          fstop=2.8)
    return dict(fill=0.25, exposure=0.15)


def s_volley(shot):
    """«Огонь!» / «шесть тысяч купонов в секунду» — a battery of coupon guns fires at the castle, coupon storm."""
    war_sky()
    lib.plane((400, 400), (0, 0, -0.01), P.M('Meadow', '#6F7A45', rough=0.9, var=0.3, bump=0.3, vs=0.2), name='Meadow')
    S._castle((0, 46, 0))
    d = shot['dur']
    rnd = random.Random(2)
    me = army_mesh('hold_gun')
    for k in range(7):
        x = -9 + k * 3
        g = P.coupon_gun((x, 0, 0.6), rot=math.pi + rnd.uniform(-0.1, 0.1), name='VGun%d' % k, carriage=True)
        soldier(me, (x, 0.85, 0), math.pi, name='Gunner')
        bpy.context.scene.frame_set(1)
        mz = P.muzzle_world(g)
        P.flying_paper(40, mz, (rnd.uniform(-1, 1), 16, 4), 0.1, d, spread=0.25, life=1.8, seed=k + 10)
        flashes(tuple(mz), 0.1, d, seed=k)
    smoke_puffs((0, 3, 0), n=16, r=9, h=3, t1=d, col='#C9BFAF', alpha=0.4)
    dress_battlefield((0, 22, 0), 40, seed=13, keep=(0, 6, 14), dur=d, far=False)
    enemy_squad((0, 17, 0), 3, 14, 'chanel', heading=0.0, seed=62, flee=(0.8, d, 7.0))
    S.fog(0.008, '#C08A60', size=(300, 300, 60), z=25)
    S.cam(shot, (-12, -6, 1.6), (-10, -4, 2.2), (0, 12, 2), (0, 16, 3), lens=32)
    return dict(fill=0.25, exposure=0.15)


def s_wallet(shot):
    """«У врага кончилось место в кошельке.» — a giant enemy wallet bursting with coupons, zip popping."""
    lib.world_color('#2A2420', 0.5)
    lib.plane((10, 10), (0, 0, 0), P.cloth('#3E2A20', 'Tablecloth'), name='Cloth')
    lm = P.leather('#1F1F22', 'WalletLeather')
    lib.box((1.6, 0.35, 1.0), (0, 0, 0.5), lm, bevel=0.12, name='Wallet')
    lib.box((1.62, 0.37, 0.05), (0, 0, 1.0), P.gold(), bevel=0.01, name='Zip')
    P.drifting_paper(0, (0, 0, 0), (1, 1, 1), 0, 1)
    P.flying_paper(120, (0, 0, 1.05), (0, 0, 3.0), 0.2, shot['dur'], spread=0.9, life=1.8, seed=4, grav=3.0)
    for k in range(60):
        c = bpy.data.objects.new('Stuck', P.coupon_mesh())
        bpy.context.scene.collection.objects.link(c)
        c.location = (random.uniform(-0.7, 0.7), random.uniform(-0.1, 0.1), 1.0 + random.uniform(0, 0.15))
        c.rotation_euler = (random.uniform(1.2, 1.9), random.uniform(-0.6, 0.6), random.uniform(-0.5, 0.5))
        c.material_slots[0].link = 'OBJECT'
        c.material_slots[0].material = P.tag_mats()[k % 4]
    sp = lib.light('SPOT', (0.5, -2.0, 3.0), energy=1600, spot=40, blend=0.5, size=0.4, color='#FFE0B8')
    lib.look_at(sp, (0, 0, 0.8))
    S.cam(shot, (0.3, -2.9, 1.3), (0.2, -2.4, 1.2), (0, 0, 0.9), (0, 0, 1.0), lens=44, dof=(0, 0, 0.9), fstop=4)
    return dict(fill=0.2, exposure=0.15)


def s_siege(shot):
    """«Крепость Эрмес. Сорок дней осады.» — the orange-box fortress surrounded by the army and searchlights at night."""
    war_sky()
    lib.plane((500, 500), (0, 0, -0.01), P.M('Plain', '#6F6548', rough=0.9, var=0.3, bump=0.3, vs=0.2), name='Plain')
    S._fortress((0, 26, 0))
    me = army_mesh('strict')
    for k in range(5):
        march_block(me, (-16 + k * 8, 6, 0), 5, 6, heading=math.pi, t0=0, t1=shot['dur'], speed=0.0, seed=k + 20)
    for k in range(2):
        tank((-20 + k * 40, 10, 0), heading=math.pi, name='SiegeTank%d' % k)
    searchlights(5, y=4, spread=40)
    smoke_puffs((0, 18, 0), n=10, r=18, h=6, t1=shot['dur'], col='#5C554D')
    dress_battlefield((0, 0, 0), 30, seed=14, keep=(0, 20, 18), dur=shot['dur'], far=False, avoid=((-12, -15, 12),))
    enemy_squad((0, 25.0, 5.2), 1, 12, 'hermes', heading=0.0, dx=1.4, seed=63)
    S.fog(0.01, '#B98A66', size=(300, 300, 60), z=25)
    S.cam(shot, (-14, -16, 9), (-9, -13, 6.5), (0, 22, 3), (0, 24, 4), lens=32)
    return dict(fill=0.25, exposure=0.15)


def s_boutique(shot):
    """«Крепость открывает бутик. Баронесса без очереди.» — the box doors open, a red carpet, she walks in past the queue."""
    S.sky('gold')
    lib.plane((300, 300), (0, 0, -0.01), P.M('Plain', '#A79B72', rough=0.9, var=0.3, bump=0.3, vs=0.2), name='Plain')
    S._fortress((0, 8, 0), banner=False)
    lib.box((2.2, 12, 0.02), (0, 0, 0.011), P.cloth('#8E1A1E', 'RedCarpet'), bevel=0, name='Carpet')
    P.sign('БУТИК ОТКРЫТ', (0, 6.3, 3.4), size=0.32, board=(4.0, 0.7), col='#2A1A10', txt='gold', name='Open')
    me = army_mesh('stand')
    for k in range(18):
        soldier(me, (2.2 + (k % 2) * 0.6, 5 - k * 0.8, 0), math.radians(90), name='Queue')
    b = B.load(loc=(0, -4, 0), heading=0.0, name='Baroness')
    SH.walk(b, 0.2, shot['dur'], [(0, -4), (0, 5)], speed=1.0, A=15.0, base=B.P('stand'))
    gag_scatter((0, 0, 0), 16, n=10, keep=(0, 0, 4.5), seed=83, ruins=0, wrecks=0, avoid=((-2.3, -7.0, 5.0),))
    S.cam(shot, (-2.6, -8, 1.6), (-2.0, -6, 1.7), (0, -2, 1.3), (0, 2, 1.5), lens=35)
    return dict(fill=0.3, exposure=0.2)


def s_wall_cap(shot):
    """«Стена тоже в пилотке.» — a literal brick wall advancing… wearing a giant garrison cap."""
    war_sky()
    rnd = random.Random(23)
    S._ermesovka(rnd, garlands=False)
    street_gags(3, 0, 20)
    wall = lib.empty('WallBlock', loc=(0, 12, 0))
    lib.box((8, 1.0, 3.2), (0, 0, 1.6), P.M('Brick', '#8A4A36', rough=0.85, var=0.25, bump=0.5, bs=6), bevel=0.02,
            name='BrickWall').parent = wall
    cap = lib.sphere(1.0, (0, 0, 3.4), P.M('Khaki', '#6F6A3A', rough=0.9, bump=0.3, bs=200), scale=(4.6, 0.9, 0.9),
                     name='GiantCap')
    cap.parent = wall
    lib.key_obj(wall, F(0), loc=(0, 12, 0), interp='LINEAR')
    lib.key_obj(wall, F(shot['dur']), loc=(0, 12 - 0.9 * shot['dur'], 0), interp='LINEAR')
    lib.add_sine(wall, 'location', 2, 0.04, 0.55)
    S.cam(shot, (-1.2, -2.5, 1.5), (-0.8, -1.8, 1.6), (0, 10, 2.2), (0, 9, 2.4), lens=35)
    return dict(fill=0.25, exposure=0.15)


def s_parachutes(shot):
    """«С неба падают пыльники. Местные берут по два.» — dust bags on little parachutes over Ermesovka."""
    S.sky('gold')
    rnd = random.Random(27)
    S._ermesovka(rnd, garlands=True)
    street_gags(4, 0, 30)
    canopy_m = P.cloth('#E9E1D2', 'Canopy')
    for k in range(26):
        e = lib.empty('Chute', loc=(rnd.uniform(-6, 6), rnd.uniform(0, 30), rnd.uniform(9, 20)))
        db = P.dust_bag((0, 0, -1.3), w=0.42, h=0.5, seed=k, name='ChuteBag')
        db.parent = e
        can = lib.sphere(0.9, (0, 0, 0.4), canopy_m, scale=(1, 1, 0.45), segs=24, rings=12, name='CanopyDome')
        can.parent = e
        for sx in (-1, 1):
            P.tube([(sx * 0.8, 0, 0.3), (sx * 0.1, 0, -0.85)], 0.006, P.M('Thread', '#CFC6B6'), 'Line').parent = e
        z0 = e.location.z
        lib.key_obj(e, F(0), loc=e.location.copy(), interp='LINEAR')
        lib.key_obj(e, F(shot['dur']), loc=(e.location.x, e.location.y, z0 - 1.6 * shot['dur']), interp='LINEAR')
        lib.add_sine(e, 'rotation_euler', 1, 0.12, 2.2, phase=k)
    S.cam(shot, (0, -6, 1.6), (0, -4, 2.2), (0, 12, 8), (0, 12, 9), lens=32)
    return dict(fill=0.3, exposure=0.2)


def s_assault(shot):
    """«Эрмесовка. Главная битва.» — the army storms down the main street, smoke, flashes, coupons."""
    war_sky()
    rnd = random.Random(29)
    S._ermesovka(rnd, garlands=False, lit=0.5)
    street_gags(2, 0, 30)
    me = army_mesh('hold_gun')
    d = shot['dur']
    march_block(me, (0, -4, 0), 8, 6, dx=1.1, dy=1.3, heading=math.pi, t0=0, t1=d, speed=2.0, seed=31, bob=0.05)
    for k in range(6):
        flashes((rnd.uniform(-4, 4), rnd.uniform(10, 30), 2), 0.1, d, every=0.2, energy=2500, seed=k)
    smoke_puffs((0, 20, 0), n=16, r=6, h=6, t1=d, col='#5C554D')
    for k in range(10):           # the enemy's barricade of shopping bags and sandbags at the end of the street
        lib.sphere(0.32, (-4.5 + k, 29.2, 0.16), P.M('Sandbag', '#9C8A64'), scale=(1.4, 0.6, 0.5), segs=12, rings=6, name='Barricade')
    enemy_squad((0, 31, 0), 2, 9, 'mixed', heading=0.0, seed=64, flee=(1.2, d, 9.0))
    P.drifting_paper(160, (-7, 0, 0.5), (7, 30, 9), 0, d, seed=33, fall=0.8)
    S.fog(0.012, '#B98A66')
    S.cam(shot, (2.0, -9, 1.0), (1.4, -7, 1.3), (0, 8, 1.6), (0, 12, 1.8), lens=28)
    return dict(fill=0.2, exposure=0.1)


def s_surrender_city(shot):
    """«Город сдаёт кассы, ключи и последний размер S.» — tabletop: key, register, and a tiny dress on a hanger."""
    S.s_keys(shot)
    hang = lib.empty('Hanger', loc=(-0.05, -0.15, 0.55))
    P.tube([(-0.12, 0, 0), (0, 0, 0.05), (0.12, 0, 0)], 0.004, P.gold(), 'HangerBar').parent = hang
    dress = lib.cyl(0.07, 0.22, (0, 0, -0.12), P.cloth('#1F1F1F', 'LittleDress'), r2=0.03, name='SizeS')
    dress.parent = hang
    P.text('S', 0.05, (0, -0.075, -0.1), m=P.M('White', '#F2F2F2'), font=P.SANS, extrude=0.001).parent = hang
    t = ev(shot, 'size', shot['dur'] - 0.8)
    lib.key_obj(hang, F(0), loc=(-0.05, -0.15, 1.6))
    lib.key_obj(hang, F(t), loc=(-0.05, -0.15, 1.6))
    lib.key_obj(hang, F(t + 0.4), loc=(-0.05, -0.15, 0.55))
    return dict(fill=0.2, exposure=0.25)


def s_map_orange(shot):
    """«К утру карта оранжевая.» — the whole map goes orange; labels of the conquered brand-lands."""
    hq_room()
    map_table(conq=[(0.0, 0.6), (shot['dur'] * 0.6, 1.3), (shot['dur'], 1.3)],
              arrows=[('Эрмесовка', 'Гучийск', 0.4, 1.4), ('Эрмесовка', 'Прада-на-Дону', 0.8, 1.8)])
    generals(6)
    S.cam(shot, (0.2, -1.6, 3.0), (0.0, -1.1, 2.4), (0.0, 0.1, 0.9), (0.0, 0.1, 0.9), lens=32)
    return dict(fill=0.2, exposure=0.15)


def s_market(shot):
    """«Кроме рынка у дома.» — one tiny market stall with apples and a sign, untouched, in an orange-flagged square."""
    S.sky('gold')
    P.cobbles((60, 60), (0, 0, 0), col='#8C8174')
    for k in range(10):
        a = k * math.pi / 5
        P.flag((9 * math.cos(a), 10 + 9 * math.sin(a), 0), size=(1.6, 1.0), stripes=('#E8701E', '#F3EEE4', '#6B4226'),
               pole=4, name='SqFlag%d' % k)
    lib.box((2.2, 1.0, 0.9), (0, 10, 0.45), P.wood('#7A5A3A', 'Stall'), bevel=0.02, name='Stall')
    for k in range(4):
        lib.cyl(0.04, 2.2, (-1.0 + (k % 2) * 2.0, 9.6 + (k // 2) * 0.8, 1.1), P.wood('#5A4632', 'StallPost'), name='Post')
    lib.box((2.6, 1.4, 0.06), (0, 10, 2.2), P.cloth('#2F6B3A', 'Awning'), bevel=0.02, name='Awning')
    for k in range(30):
        lib.sphere(0.07, (-0.9 + (k % 10) * 0.2, 9.75 + (k // 10) * 0.2, 0.95), P.M('Apple', '#B3261E', rough=0.35),
                   segs=12, rings=6, name='Apple')
    P.sign('РЫНОК У ДОМА', (0, 9.45, 1.65), size=0.14, board=(1.8, 0.3), col='#F1E6CC', txt='#2A1A10', font=P.SANS,
           name='MarketSign')
    # round the untouched stall: the conquered square full of the army, a tank, orange banners (the stall stays alone)
    me = army_mesh('strict')
    for k in range(28):
        a = k * 2 * math.pi / 28
        soldier(me, (6.5 * math.cos(a), 10 + 6.5 * math.sin(a), 0), a + math.pi / 2 + math.pi, name='Ring')
    tank((-8, 18, 0), heading=math.radians(200), name='MarketTank')
    for k in range(3):
        P.house(-14 + k * 14, 26, 12, 8, 4, random.Random(k), heading=0.0, win_lit=0.2)
    S.cam(shot, (-3, 3, 1.7), (-1.5, 6.0, 1.5), (0, 10, 1.2), (0, 10, 1.2), lens=40, dof=(0, 10, 1.2), fstop=3.2)
    return dict(fill=0.3, exposure=0.2)


def s_textbook(shot):
    """«Запишите в учебники. Мелким шрифтом.» — a history textbook opens; one line about her in microscopic print."""
    lib.world_color('#3B3029', 0.45)
    lib.plane((3, 3), (0, 0, 0), P.wood('#4A2E1A', 'Desk'), name='Desk')
    pm = P.paper('#EFE6D2', 'BookPage')
    for sx in (-1, 1):
        pg = lib.box((0.21, 0.29, 0.02), (sx * 0.107, 0, 0.012), pm, bevel=0.003, name='Page')
        pg.rotation_euler.y = -sx * 0.06
    P.text('ИСТОРИЯ', 0.03, (-0.107, 0.11, 0.024), rot=(0, 0, 0), m=P.M('Ink', '#2A1C14'), font=P.SERIF, extrude=0.0002)
    for k in range(14):
        lib.box((0.16 - 0.03 * (k % 3) / 2, 0.0005, 0.004), (-0.107, 0.07 - k * 0.012, 0.024),
                P.M('Ink', '#2A1C14'), bevel=0, rot=(math.radians(90), 0, 0), name='Line')
    P.text('баронесса взяла всё', 0.0035, (0.107, -0.12, 0.024), rot=(0, 0, 0), m=P.M('Ink', '#2A1C14'), font=P.SANS,
           extrude=0.0001)
    lens_m = lib.mat('Magnifier', '#DDE6EA', rough=0.02, alpha=0.2)
    mag = lib.empty('Magnifier', loc=(0.107, -0.12, 0.08))
    lib.cyl(0.05, 0.004, (0, 0, 0), lens_m, name='MagGlass').parent = mag
    lib.cyl(0.054, 0.006, (0, 0, 0), P.brass(), name='MagRim').parent = mag
    lib.key_obj(mag, F(0), loc=(0.3, -0.3, 0.12))
    lib.key_obj(mag, F(shot['dur'] * 0.5), loc=(0.107, -0.12, 0.06))
    sp = lib.light('SPOT', (0.2, -0.4, 0.8), energy=60, spot=40, blend=0.5, size=0.2, color='#FFE0B8')
    lib.look_at(sp, (0, 0, 0))
    S.cam(shot, (0.05, -0.42, 0.42), (0.1, -0.24, 0.2), (0.0, 0.0, 0.02), (0.107, -0.12, 0.024), lens=50,
          dof=(0.107, -0.12, 0.024), fstop=4)
    return dict(fill=0.2, exposure=0.15)


def s_parade(shot):
    """«Так родилась республика Биркин.» — victory parade before the handbag palace: army, tanks, flags, coupons."""
    S.sky('gold')
    lib.plane((800, 800), (0, 0, -0.01), P.M('Land', '#8B925E', rough=0.9, var=0.3, bump=0.2, vs=0.05))
    P.cobbles((90, 90), (0, -20, 0.005), col='#9A8F80')
    S._palace((0, 14, 0), s=0.8)
    me = army_mesh('strict')
    d = shot['dur']
    march_block(me, (-6, -12, 0), 6, 8, heading=math.radians(90), t0=0, t1=d, speed=1.2, seed=40)
    for k in range(2):
        tk = tank((-14, -22 - k * 9, 0), heading=math.radians(90), name='ParadeTank%d' % k)
        lib.key_obj(tk, F(0), loc=tk.location.copy(), interp='LINEAR')
        lib.key_obj(tk, F(d), loc=(-14 + 2.0 * d, tk.location.y, 0), interp='LINEAR')
    P.drifting_paper(200, (-15, -30, 1), (15, 0, 14), 0, d, seed=44, fall=0.7)
    gag_scatter((0, -18, 0), 30, n=14, keep=(-2, -18, 14), seed=81, ruins=0, wrecks=0)
    S.cam(shot, (-22, -40, 6), (-14, -36, 9), (0, -10, 3), (0, 0, 8), lens=32)
    return dict(fill=0.3, exposure=0.2)


def s_triple(shot, which=0):
    """«Строгая. Полная. Непобедимая.» — three hard close-ups (front / profile / low hero angle)."""
    war_sky()
    lib.world_color('#2A2420', 0.35)
    b = S.baroness((0, 0, 0), 0.0, 'strict')
    S.poses(b, [(0, B.P('strict', head=(0, -4 if which == 2 else 2, 0))), (shot['dur'], B.P('strict', head=(3, 0, 0)))])
    lib.light('AREA', (1.4, -0.8, 1.9), energy=110, size=0.8, color='#FFB070')
    lib.light('AREA', (-1.2, 0.6, 2.0), energy=140, size=0.6, color='#8FA8FF')
    for o in bpy.data.objects:
        if o.type == 'LIGHT' and o.data.type == 'AREA':
            lib.look_at(o, (0, 0, 1.5))
    if which == 0:
        S.cam(shot, (0.0, -1.2, 1.55), (0.0, -1.0, 1.55), (0, 0, 1.52), lens=70, dof=(0, -0.08, 1.52), fstop=2.0)
    elif which == 1:
        S.cam(shot, (1.2, -0.2, 1.5), (1.0, -0.2, 1.5), (0, 0, 1.45), lens=60, dof=(0.1, 0, 1.45), fstop=2.0)
    else:
        S.cam(shot, (0.3, -1.4, 0.7), (0.2, -1.1, 0.75), (0, 0, 1.5), (0, 0, 1.55), lens=32, dof=(0, -0.08, 1.4), fstop=2.8)
    return dict(fill=0.08, exposure=-0.1)


def s_shout(shot):
    """Her short orders («Огонь!», «Ни шагу назад!», «Свободны.») on the battlefield: hard rim light, smoke, flashes."""
    war_sky()
    lib.plane((200, 200), (0, 0, 0), P.M('Mud', '#4A4032', rough=0.95, var=0.3, bump=0.6, vs=0.4), name='Ground')
    b = S.baroness((0, 0, 0), 0.0, 'point')
    S.poses(b, [(0, B.P('point', head=(0, -8, 0))), (shot['dur'], B.P('point', head=(6, -6, 0)))])
    smoke_puffs((0, 8, 0), n=12, r=8, h=4, t1=shot['dur'], col='#5C554D')
    dress_battlefield((0, 22, 0), 36, seed=15, keep=(0, 0, 5), dur=shot['dur'])
    enemy_squad((0, 16, 0), 2, 10, 'mixed', heading=0.0, seed=65, flee=(0.3, shot['dur'], 10.0))
    for k in range(3):
        flashes((-6 + k * 6, 14, 2), 0.1, shot['dur'], every=0.25, energy=3000, seed=k)
    lib.light('AREA', (-1.2, 1.0, 2.2), energy=220, size=0.8, color='#FFB070')
    lib.light('AREA', (1.0, -1.2, 1.8), energy=60, size=1.0, color='#9FB6FF')
    for o in bpy.data.objects:
        if o.type == 'LIGHT' and o.data.type == 'AREA':
            lib.look_at(o, (0, 0, 1.5))
    S.fog(0.012, '#B98A66', size=(200, 200, 40), z=15)
    S.cam(shot, (0.35, -1.25, 1.45), (0.25, -1.0, 1.5), (0, 0, 1.5), (0, 0, 1.52), lens=50, dof=(0, -0.08, 1.52),
          fstop=2.2)
    return dict(fill=0.1, exposure=0.0)


SCENES = {
    'hook': s_hook, 'night_map': s_conquest_night, 'coupon_rain': s_coupon_rain, 'hq_ext': s_hq_exterior,
    'hq_map': lambda s: s_hq_map(s, 0.1), 'hq_chek': lambda s: s_hq_line(s, 'chek'),
    'hq_faint': lambda s: s_hq_map(s, 0.1, cam_close=False, faint=S.ev(s, 'faint', 0.6)),
    'army': s_army, 'identical': s_identical, 'tank': s_tank, 'tank_queue': s_tank_queue, 'load': s_load,
    'strike_map': lambda s: s_hq_map(s, 0.25, arrows=[('Эрмесовка', 'КокоШанель', 0.3, s['dur'] - 0.3)], cam_close=True),
    'heels': s_heels, 'fire': s_shout, 'volley': s_volley, 'wallet': s_wallet,
    'siege': s_siege,
    'boutique': s_boutique,
    'assault': s_assault, 'wall_cap': s_wall_cap, 'parachutes': s_parachutes, 'no_retreat': s_shout,
    'city_gives': s_surrender_city, 'map_orange': s_map_orange, 'market': s_market, 'textbook': s_textbook,
    'parade': s_parade, 'strict1': lambda s: s_triple(s, 0), 'strict2': lambda s: s_triple(s, 1),
    'strict3': lambda s: s_triple(s, 2), 'cta': S.s_cta, 'dismiss': s_shout,
    'castle': lambda s: (S.s_castle(s), dress_battlefield((0, 4, 0), 30, seed=16, keep=(0, 30, 16), dur=s['dur'], avoid=((-12, -6, 14),)),
                         enemy_squad((0, 8, 0), 3, 14, 'chanel', heading=0.0, seed=66))[0],
    'chek_gate': lambda s: (S.s_face(s, 'castle', 'check'), enemy_squad((0, 15, 0), 2, 8, 'chanel', heading=math.pi * 0, seed=67))[0],
    'surrender': lambda s: (S.s_surrender(s), enemy_squad((-4, 11, 0), 3, 8, 'chanel', heading=0.0, seed=68,
                                                         surrender_at=S.ev(s, 'give', 0.6)))[0],
    'insult': lambda s: (S.s_face(s, 'fortress', 'refuse'), enemy_squad((0, 11.5, 1.2), 1, 10, 'hermes', heading=0.0, dx=1.3, seed=69))[0],
    'balloon': lambda s: (S.s_balloon(s), dress_battlefield((0, 6, 0), 34, seed=17, keep=(0, 30, 14), dur=s['dur']))[0],
    'map_all': lambda s: s_hq_map(s, 1.3, cam_close=True),
}


def build(shot, fps):
    lib.FPS = fps
    return SCENES[shot['variant']](shot)
