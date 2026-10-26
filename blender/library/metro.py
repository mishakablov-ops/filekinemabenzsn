"""Set «metro»: the permanent city «Метрополис» for every reel of style «блендер» (26.10.2026).

The whole city is built from code (metro_plan -> metro_build -> metro_mats) and filmed from named spots of the plan.
A shot in shots.json:

    {"id": "s1", "set": "metro", "variant": "skyline_dusk", "dur": 4.0}
    optional: "preset": "day|golden|dusk|night", "cam": [x,y,z], "target": [x,y,z], "lens": 30,
              "move": [dx,dy,dz] (camera drift over the shot, metres), "over": {preset overrides},
              "detail_r": metres of street furniture around the camera, "filler": false (no city beyond the plan)

Spots (metro_plan.py): skyline_dusk, aerial_night, avenue, plaza, embankment, bridge, park, rooftop.
"""
import math
import bpy
from mathutils import Vector
import lib
import metro_mats as MM
import metro_build as MB

# time of day: sun (elevation, azimuth from east counter-clockwise), sky, fog = aerial perspective, city lights
PRESETS = {
    'day': dict(sun_el=55.0, sun_az=-80.0, sun='#FFF4E5', sun_E=4.5, zen='#4A78B0', mid='#9CB4C9', fog='#B4C3CD',
                dens=0.00022, fogh=700.0, night=0.0, lit=0.06, street=0.0, neon=0.25, traffic=0.75, exposure=0.3,
                glow=0.25, moon_E=0.0, sky=1.6),
    'golden': dict(sun_el=7.0, sun_az=200.0, sun='#FFB46A', sun_E=3.5, zen='#5C78A8', mid='#C9A88E', fog='#D8AE8A',
                   dens=0.0003, fogh=500.0, night=0.25, lit=0.12, street=0.3, neon=0.5, traffic=0.75, exposure=0.1,
                   glow=0.9, moon_E=0.0),
    'dusk': dict(sun_el=-4.0, sun_az=190.0, sun='#FF9A70', sun_E=0.0, zen='#2F2C55', mid='#7C6FA0', fog='#A08AB0',
                 dens=0.0005, fogh=350.0, night=0.9, lit=0.22, street=0.85, neon=1.0, traffic=0.85, exposure=0.2,
                 glow=0.6, moon_E=0.0),
    'night': dict(sun_el=-30.0, sun_az=190.0, sun='#FFFFFF', sun_E=0.0, zen='#1A1716', mid='#33292A', fog='#45362D',
                  dens=0.00038, fogh=450.0, night=1.0, lit=0.26, street=1.0, neon=1.0, traffic=0.9, exposure=0.6,
                  glow=0.0, moon_E=0.08),
}


def sun_vec(el, az):
    e, a = math.radians(el), math.radians(az)
    return (math.cos(e) * math.cos(a), math.cos(e) * math.sin(a), math.sin(e))


def apply_preset(name, over=None):
    p = dict(PRESETS[name])
    p.update(over or {})
    for k, gk in (('night', 'Night'), ('lit', 'Lit'), ('street', 'Street'), ('neon', 'Neon'), ('traffic', 'Traffic'),
                  ('dens', 'FogDensity'), ('fogh', 'FogHeight')):
        MM.set_global(gk, p[k])
    MM.set_global('FogColor', p['fog'])
    sd = sun_vec(p['sun_el'], p['sun_az'])
    MM.world(p['zen'], p['mid'], sd, p['sun'], p['glow'], p.get('sky', 1.0))
    if p['sun_E'] > 0:
        s = lib.light('SUN', (0, 0, 300), energy=p['sun_E'], color=p['sun'], size=0.6, name='MetroSun')
        s.rotation_euler = (-Vector(sd)).to_track_quat('-Z', 'Y').to_euler()
    if p['moon_E'] > 0:
        md = sun_vec(35.0, 120.0)
        s = lib.light('SUN', (0, 0, 300), energy=p['moon_E'], color='#9FB3D9', size=1.0, name='MetroMoon', shadow=False)
        s.rotation_euler = (-Vector(md)).to_track_quat('-Z', 'Y').to_euler()
        s.data.specular_factor = 0.0           # no moon disc mirrored in the river
    return p


def water_probe(cam_loc):
    """Planar reflection over the river near the camera (Eevee); ignored by Cycles."""
    for kind in ('PLANE', 'PLANAR'):
        try:
            pr = bpy.data.lightprobes.new('MetroWaterProbe', kind)
            break
        except Exception:
            pr = None
    if pr is None:
        return None
    ob = bpy.data.objects.new('MetroWaterProbe', pr)
    ob.location = (cam_loc[0], MB.MP.RIVER_S / 2, -1.19)
    ob.scale = (5000.0, -MB.MP.RIVER_S / 2 + 20, 1.0)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def build(shot, fps):
    plan = MB.get_plan()
    spot = dict(plan['spots'][shot.get('variant', 'skyline_dusk')])
    for k in ('cam', 'target', 'lens', 'preset', 'move'):
        if k in shot:
            spot[k] = shot[k]
    frames = max(1, int(round(shot['dur'] * fps)))
    cam_loc, tgt = Vector(spot['cam']), Vector(spot['target'])
    detail_r = shot.get('detail_r', 300.0 if cam_loc.z < 30 else 0.0)
    MM.set_global('FocusX', cam_loc.x)
    MM.set_global('FocusY', cam_loc.y)
    MM.set_global('FocusR', detail_r)
    night = dict(PRESETS[spot['preset']], **shot.get('over', {}))['night']
    st = MB.build_city(focus=(cam_loc.x, cam_loc.y), detail_r=detail_r, filler=shot.get('filler', True), fps=fps,
                       frames=frames, night=night)
    p = apply_preset(spot['preset'], shot.get('over'))
    MM.key_time(fps, frames)
    cam = lib.camera(tuple(cam_loc), tuple(tgt), spot['lens'])
    cam.data.clip_start = 0.1 if cam_loc.z < 30 else 1.0
    cam.data.clip_end = 20000.0
    move = spot.get('move')
    if move:
        mv = Vector(move)
        lib.animate_camera(cam, [(0.0, cam_loc), (shot['dur'], cam_loc + mv)],
                           [(0.0, tgt), (shot['dur'], tgt + mv * 0.3)])
    if cam_loc.y < 900:
        water_probe(cam_loc)
    if p['night'] > 0.5:
        lib.bloom(0.45, 1.0, 7)
    else:
        lib.bloom(0.2, 1.4, 6)
    print('METRO', spot.get('preset'), st, flush=True)
    return dict(fill=0, exposure=p['exposure'], still_t=0.5, samples=shot.get('samples', 32))
