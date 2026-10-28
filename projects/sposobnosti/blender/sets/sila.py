"""Set «sila» for «Каждому по способности» (sposobnosti): every scene of both parts, variant = scene type.

City scenes are filmed in «Метрополис» (metro_build / metro_mats, places from metro_spots, fixed in shots.json);
interiors, the airport and the power plant are small sets of their own (sila_sets.py). The hero is the generated and
rigged model (sila_hero.py), the other people are people2 figures with bigger heads (folk()), the powers are sila_fx.
Scene code: sila_p1.py (part 1, ids a..), sila_p2.py (part 2, ids b..).
"""
import math
import random

import bpy
from mathutils import Vector

import lib
import metro
import metro_build as MB
import metro_mats as MM
import people2 as P2

F = lib.sec2f


# ----------------------------------------------------------------------------- the city
def city(shot, fps, cam=None, target=None, lens=None, preset=None, keep=(), over=None, detail_r=None, cars=True,
         walkers=True, filler=True, cam_keys=None, focus=None):
    """«Метрополис» around a place. cam/target/lens/preset default to the shot's fields (metro_spots).
    cam_keys: [(t, cam, target)] for our own camera move (else 'move' of the shot drifts the camera).
    keep: [((x0, y0), (x1, y1), r)] zones the street furniture and walkers keep clear of (people, the hero)."""
    cam_loc = Vector(cam or shot['cam'])
    tgt = Vector(target or shot['target'])
    lens = lens or shot.get('lens', 35)
    preset = preset or shot.get('preset', 'day')
    over = dict(shot.get('over', {}), **(over or {}))
    dur = shot['dur']
    frames = max(1, int(round(dur * fps)))
    fx, fy = focus or (cam_loc.x, cam_loc.y)
    low = cam_loc.z < 30 or (cam_keys and min(k[1][2] for k in cam_keys) < 30)
    dr = detail_r if detail_r is not None else shot.get('detail_r', 300.0 if low else 0.0)
    MM.set_global('FocusX', fx)
    MM.set_global('FocusY', fy)
    MM.set_global('FocusR', dr)
    night = dict(metro.PRESETS[preset], **over)['night']
    zones = list(keep)
    if low:
        path = [k[1] for k in cam_keys] if cam_keys else [cam_loc, cam_loc + Vector(shot.get('move') or (0, 0, 0))]
        for a, b in zip(path, path[1:]):
            zones.append(((a[0], a[1]), (b[0], b[1]), 1.6))
    st = MB.build_city(focus=(fx, fy), detail_r=dr, filler=shot.get('filler', filler), fps=fps, frames=frames,
                       night=night, keep=zones)
    p = metro.apply_preset(preset, over)
    MM.key_time(fps, frames)
    c = lib.camera(tuple(cam_loc), tuple(tgt), lens)
    c.data.clip_start = 0.1 if low else 1.0
    c.data.clip_end = 20000.0
    if cam_keys:
        lib.animate_camera(c, [(t, Vector(a)) for t, a, _ in cam_keys], [(t, Vector(b)) for t, _, b in cam_keys])
    elif shot.get('move'):
        mv = Vector(shot['move'])
        lib.animate_camera(c, [(0.0, cam_loc), (dur, cam_loc + mv)], [(0.0, tgt), (dur, tgt + mv * 0.3)])
    if cam_loc.y < 900:
        metro.water_probe(cam_loc)
    if p['night'] > 0.5:
        lib.bloom(0.45, 1.0, 7)
    else:
        lib.bloom(0.2, 1.4, 6)
    if not cars:
        for o in [o for o in bpy.data.objects if o.name.startswith('MetroCar')]:
            bpy.data.objects.remove(o, do_unlink=True)
    if not walkers:
        drop_near((fx, fy), 1e9, prefix='MetroWalker')
    print('SILA city', preset, st, flush=True)
    return p, c


def drop_near(xy, r, prefix='MetroWalker'):
    """Remove walkers (people2 roots + parts) whose start is within r of xy."""
    gone = set()
    for o in list(bpy.data.objects):
        if o.name.startswith(prefix) and o.parent is None and math.hypot(o.location.x - xy[0], o.location.y - xy[1]) < r:
            gone.add(o.name.split('_')[0])
    if not gone:
        return 0
    for o in list(bpy.data.objects):
        if o.name.split('_')[0] in gone:
            bpy.data.objects.remove(o, do_unlink=True)
    return len(gone)


def ground(x, y, z0=80.0, default=0.15):
    """Height of whatever is under (x, y): sidewalk, road, grass (ray cast against the built scene)."""
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    hit, loc, n, i, ob, M = bpy.context.scene.ray_cast(dg, Vector((x, y, z0)), Vector((0, 0, -1)))
    return loc.z if hit else default


def ahead(shot, d, side=0.0, cam=None, target=None):
    """Point d metres in front of the shot camera (on the ground plane), side metres to its right."""
    c, t = Vector(cam or shot['cam']), Vector(target or shot['target'])
    f = Vector((t.x - c.x, t.y - c.y, 0)).normalized()
    r = Vector((f.y, -f.x, 0))
    p = c + f * d + r * side
    return Vector((p.x, p.y, 0.0)), f, r


def face(frm, to):
    """Heading (rot z) that makes a figure at `frm` look towards `to` (forward = local -Y)."""
    return math.atan2(to[0] - frm[0], -(to[1] - frm[1]))


def vlerp(a, b, w):
    return Vector(a).lerp(Vector(b), w)


# ----------------------------------------------------------------------------- other people: people2 with chibi heads
LOOKS = {
    'neighbour': dict(top='#3B4A63', pants='#2E3236', hair='#3D2B20', skin='#E0B99A', shoe='#1F1C1A', bag='#5A3E2A'),
    'granny': dict(top='#7E4E7A', pants='#4A4540', hair='#C9C5C0', skin='#E0B99A', shoe='#3A3631', scarf='#B8473B'),
    'courier': dict(top='#E8B92E', pants='#2B2826', hair='#1E1C1B', skin='#C69C7B', shoe='#2E2824', box='#E8B92E'),
    'agent': dict(top='#1B1D21', pants='#1B1D21', hair='#1E1C1B', skin='#D4A989', shoe='#111111', shades=True),
    'storm': dict(top='#2E3A44', pants='#22282E', hair='#B9A38A', skin='#E0B99A', shoe='#1F1C1A', coat='#2E3A44'),
    'girl': dict(top='#C9533E', pants='#3C4652', hair='#5A3E2A', skin='#E0B99A', shoe='#E9E7E1'),
    'sparky': dict(top='#3E5A3A', pants='#2E3236', hair='#8A6A48', skin='#C69C7B', shoe='#E9E7E1'),
    'kid': dict(top='#3E6FA8', pants='#3A3631', hair='#3D2B20', skin='#E0B99A', shoe='#E9E7E1'),
}


def folk(loc, heading, rng, coll=None, look=None, height=0.9, head=1.6, name='Folk'):
    """A people2 person with a bigger head (so the cast matches the chibi hero). look: LOOKS key or dict."""
    lk = LOOKS.get(look, look) if look else None
    p = P2.person(loc, heading, height, rng, coll, name=name)
    if lk:
        for key, parts in (('top', ('torso', 'upperL', 'upperR', 'foreL', 'foreR')), ('pants', ('pelvis', 'thighL', 'thighR', 'shinL', 'shinR')),
                           ('skin', ('neck', 'head', 'handL', 'handR')), ('shoe', ('shoeL', 'shoeR'))):
            m = lib.pmat(lk[key])
            for k in parts:
                lib._obj_mat(p[k], m)
        for o in p['head'].children:
            if o.name.endswith('_hair'):
                lib._obj_mat(o, lib.pmat(lk['hair']))
            if o.name.endswith('_nose'):
                lib._obj_mat(o, lib.pmat(lk['skin']))
    hd = p['head']
    hd.scale = (hd.scale.x * head, hd.scale.y * head, hd.scale.z * head)
    hd.location.z += 0.105 * (head - 1.0) * 0.9
    p['neck'].scale = (1.25, 1.25, 1.0)
    if lk and lk.get('scarf'):                      # babushka headscarf: a cap over the hair and a knot
        sm = lib.pmat(lk['scarf'])
        s = lib.sphere(0.118, (0, 0.012, 0.015), sm, 20, 12, scale=(1.0, 1.02, 1.0), name=name + '_scarf', coll=coll)
        s.parent = hd
        k = lib.sphere(0.03, (0, 0.02, -0.105), sm, 10, 8, name=name + '_knot', coll=coll)
        k.parent = hd
    if lk and lk.get('shades'):
        sh = lib.box((0.17, 0.03, 0.035), (0, -0.1, 0.02), lib.mat('Shades', '#0B0C0E', rough=0.1, spec=0.9), bevel=0.01,
                     name=name + '_shades', coll=coll)
        sh.parent = hd
    if lk and lk.get('coat'):                        # long coat: a cone from the chest to the knees
        cm = lib.pmat(lk['coat'])
        c = lib.cyl(0.2, 0.62, (0, 0, -0.33), cm, verts=20, r2=0.15, name=name + '_coat', coll=coll, origin='bottom')
        c.parent = p['hips']
        c.location = (0, 0, -0.5)
        c.scale = (1.0, 0.75, 1.0)
    if lk and lk.get('box'):                         # courier backpack
        b = lib.box((0.36, 0.3, 0.38), (0, 0.24, 0.42), lib.pmat(lk['box']), bevel=0.03, name=name + '_box', coll=coll)
        b.parent = p['hips']
    if lk and lk.get('bag'):
        b = lib.box((0.34, 0.09, 0.26), (0, 0, 0), lib.pmat(lk['bag']), bevel=0.02, name=name + '_case', coll=coll)
        b.parent = p['handR']
        b.location = (0, 0, -1.2)
        b.scale = (1 / 0.036, 1 / 0.03, 1 / 0.048)
    return p


def fly_pose(p, arms='forward'):
    """people2 figure in the superman pose (call before keying the root); the root then flies face down along -Y."""
    for sd in ('L', 'R'):
        p['thigh' + sd].rotation_euler.x = 0.08
        p['shin' + sd].rotation_euler.x = 0.25
        p['shoe' + sd].rotation_euler.x = 0.6
    if arms == 'forward':
        p['upperL'].rotation_euler = (-math.pi * 0.95, 0, 0.12)
        p['upperR'].rotation_euler = (-math.pi * 0.95, 0, -0.12)
        p['foreL'].rotation_euler.x = 0.0
        p['foreR'].rotation_euler.x = 0.0
    elif arms == 'one':
        p['upperR'].rotation_euler = (-math.pi * 0.95, 0, -0.1)
        p['upperL'].rotation_euler = (0.1, 0, 0.18)
        p['foreL'].rotation_euler.x = -0.2
    p['head'].rotation_euler.x = -0.5


def fly(p, keys, tilt=1.35, bob=0.15):
    """Fly a people2 root through keys [(t, (x, y, z))]: body leans along the path (tilt rad from upright), soft bob."""
    root = p['root']
    for (t0, a), (t1, b) in zip(keys, keys[1:]):
        h = math.atan2(b[0] - a[0], -(b[1] - a[1]))
        for t, q in ((t0, a), (t1, b)):
            root.location = q
            root.rotation_euler = (tilt, 0, h)
            root.keyframe_insert('location', frame=F(t))
            root.keyframe_insert('rotation_euler', frame=F(t))
    if bob:
        lib.add_sine(root, 'location', 2, bob, 1.3, random.random() * 6)
    lib._set_interp(root, 'LINEAR')
    return root


def key_people(p, part, idx, keys, path='rotation_euler'):
    for t, v in keys:
        P2._key(p[part], path, idx, F(t), v)


# ----------------------------------------------------------------------------- dispatcher
def build(shot, fps=30):
    lib.FPS = fps
    v = shot['variant']
    import importlib
    mod = importlib.import_module('sila_p2' if str(shot.get('part', shot['id'][0])) in ('2', 'b') else 'sila_p1')
    fn = getattr(mod, 'v_' + v, None)
    if fn is None:
        raise SystemExit('unknown variant ' + v)
    return fn(shot, fps) or {}
