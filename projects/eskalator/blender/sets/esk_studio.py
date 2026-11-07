"""Bright explainer studio (like the reference cutaways): white floor, red backdrop curve, soft big lights."""
import bpy, bmesh, math
from mathutils import Vector
import esk_mech as E

def world(col='#F3F1EE', strength=0.9):
    w = bpy.data.worlds.new('EskWorld'); bpy.context.scene.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes['Background']
    bg.inputs['Color'].default_value = E.srgb(col); bg.inputs['Strength'].default_value = strength
    return w

def backdrop(center=(4, 0, 0), size=40, col_floor='#F2F2F2', col_wall='#D8262C', wall_y=3.2):
    c = E.coll('Studio')
    bm = bmesh.new(); E.bm_box(bm, (-size / 2, -size / 2, -2.1), (size / 2, size / 2, -2.0), 0)
    fl = E.obj_from_bm(bm, 'StudioFloor', [E.mat('StudioFloor', col_floor, rough=0.4)], c, loc=center)
    # curved red cyclorama behind the escalator (+Y side)
    bm = bmesh.new()
    R = 3.0; n = 16
    prof = [(wall_y + R - R * math.cos(math.pi / 2 * k / n), -2.0 + R - R * math.sin(math.pi / 2 * k / n)) for k in range(n + 1)]
    prof = [(wall_y - 6, -2.0)] + prof + [(wall_y + R, 30)]
    rows = []
    for x in (-size / 2, size / 2):
        rows.append([bm.verts.new((x, y, z)) for (y, z) in prof])
    for k in range(len(prof) - 1):
        bm.faces.new([rows[0][k], rows[1][k], rows[1][k + 1], rows[0][k + 1]])
    wall = E.obj_from_bm(bm, 'StudioWall', [E.mat('StudioWall', col_wall, rough=0.6)], c, loc=(center[0], 0, center[2]), smooth=True)
    return fl, wall

def area(name, loc, target, energy, size, col='#FFFFFF', shadow=True):
    ld = bpy.data.lights.new(name, 'AREA'); ld.energy = energy; ld.size = size; ld.color = E.srgb(col)[:3]
    ld.use_shadow = shadow
    ob = bpy.data.objects.new(name, ld); ob.location = loc
    ob.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    bpy.context.scene.collection.objects.link(ob)
    return ob

def lights(center=(4, 0, 2)):
    cx, cy, cz = center
    area('Key', (cx - 4, cy - 7, cz + 7), center, 2600, 6)
    area('Fill', (cx + 6, cy - 6, cz + 2), center, 900, 8, shadow=False)
    area('Top', (cx, cy, cz + 9), center, 1500, 10)
    area('Rim', (cx + 2, cy + 6, cz + 5), center, 800, 5, col='#FFE7E0')

def camera(loc, target, lens=35, name='Cam'):
    cd = bpy.data.cameras.new(name); cd.lens = lens; cd.sensor_fit = 'HORIZONTAL'; cd.sensor_width = 36
    cd.clip_start = 0.05; cd.clip_end = 500
    ob = bpy.data.objects.new(name, cd); ob.location = loc
    ob.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    bpy.context.scene.collection.objects.link(ob); bpy.context.scene.camera = ob
    return ob

def render_setup(engine='CYCLES', w=1080, h=1920, pct=100, samples=64, fps=30):
    sc = bpy.context.scene
    r = sc.render; r.engine = engine
    r.resolution_x, r.resolution_y, r.resolution_percentage = w, h, pct
    r.fps = fps
    if engine == 'CYCLES':
        sc.cycles.samples = samples; sc.cycles.use_denoising = True
        try: sc.cycles.denoiser = 'OPENIMAGEDENOISE'
        except Exception: pass
    else:
        sc.eevee.taa_render_samples = samples
        for k, v in dict(use_raytracing=True, use_shadows=True, use_gtao=True).items():
            try: setattr(sc.eevee, k, v)
            except Exception: pass
    sc.view_settings.view_transform = 'AgX'
    try: sc.view_settings.look = 'AgX - Medium High Contrast'
    except Exception: pass
    return sc
