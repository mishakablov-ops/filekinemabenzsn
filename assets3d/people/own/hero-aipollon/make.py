"""Builds hero-aipollon.glb (and preview renders) from blender/library/hero.py.

    blender -b --factory-startup --python make.py -- [--previews]

The .glb keeps the joint hierarchy (Hero_hips, Hero_thighL, Hero_shinL, Hero_shoeL, Hero_upperL, Hero_foreL, ...),
so three.js / KINEMA can pose it by rotating nodes. Procedural shading is reduced to plain colours for glTF;
the haircut fade goes into vertex colours of the head.
"""
import sys, os, math
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
sys.path[:0] = [os.path.join(REPO, 'blender', 'kit', 'blender'), os.path.join(REPO, 'blender', 'library')]
import bpy, bmesh, mathutils
import lib, hero

args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []


def build():
    lib.reset()
    lib._mat_cache.clear()                       # caches point at data removed by reset()
    hero._meshes.clear()
    return hero.hero((0, 0, 0), 0.0, pose='still', name='Hero')


def bake_for_gltf(p):
    """Curves -> meshes; head gets an RGB colour attribute (skin -> hair) and a material that uses it."""
    for ob in [o for o in bpy.data.objects if o.type == 'CURVE']:
        me = bpy.data.meshes.new_from_object(ob.evaluated_get(bpy.context.evaluated_depsgraph_get()))
        nob = bpy.data.objects.new(ob.name, me)
        for c in ob.users_collection:
            c.objects.link(nob)
        nob.parent = ob.parent
        nob.matrix_parent_inverse = ob.matrix_parent_inverse
        nob.matrix_basis = ob.matrix_basis
        mat = ob.data.materials[0]
        bpy.data.objects.remove(ob)
        nob.name = nob.name.split('.')[0]
        me.materials.clear(); me.materials.append(mat)
    # the pupil lives in the iris shader; glTF keeps only flat colours, so give it a thin black disc
    black = bpy.data.materials.get('HeroPupil')
    for side in 'LR':
        iris = bpy.data.objects['Hero_iris' + side]
        disc = lib.sphere(1.0, segs=24, rings=8, mat_=black, scale=(0.025, 0.0015, 0.029), name='Hero_pupil' + side)
        disc.parent = iris.parent
        disc.location = iris.location + mathutils.Vector((0, -iris.scale.y + 0.0006, 0))
    head = p['head']
    me = head.data
    skin, hair = lib.C(hero.COL['skin']), lib.C(hero.COL['hair'])
    w = me.color_attributes['Col']
    rgb = me.color_attributes.new('HairRGB', 'FLOAT_COLOR', 'CORNER')
    for i, d in enumerate(w.data):
        t = d.color[0]
        rgb.data[i].color = tuple(skin[k] * (1 - t) + hair[k] * t for k in range(3)) + (1.0,)
    me.color_attributes.remove(me.color_attributes['Col'])
    me.color_attributes.active_color = me.color_attributes['HairRGB']
    m = bpy.data.materials.new('HeroHead')
    m.use_nodes = True
    nt = m.node_tree
    a = nt.nodes.new('ShaderNodeVertexColor'); a.layer_name = 'HairRGB'
    bsdf = nt.nodes['Principled BSDF']; bsdf.inputs['Roughness'].default_value = 0.6
    nt.links.new(a.outputs['Color'], bsdf.inputs['Base Color'])
    head.material_slots[0].material = m
    me.materials[0] = m


def export(path):
    kw = dict(filepath=path, export_format='GLB', export_apply=True, export_yup=True, export_animations=False)
    try:
        bpy.ops.export_scene.gltf(export_vertex_color='ACTIVE', **kw)
    except TypeError:
        bpy.ops.export_scene.gltf(**kw)


def previews(p, path, res=720):
    """Turnaround sheet (3/4, front, side, back, face) on a soft studio backdrop, Cycles."""
    from PIL import Image
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.samples = 64
    sc.cycles.use_denoising = True
    sc.render.resolution_x = sc.render.resolution_y = res
    sc.view_settings.view_transform = 'AgX'
    sc.view_settings.look = 'AgX - Medium High Contrast'
    lib.world_gradient('#2E3D52', '#8FA3BA', '#9DB0C4', strength=0.8)
    bm = bmesh.new()
    prof = [(-20, 0.0), (1.5, 0.0)] + [(1.5 + 2.5 * math.sin(a / 24 * math.pi), 2.5 * (1 - math.cos(a / 24 * math.pi)))
                                        for a in range(1, 13)] + [(4.0, 12.0)]
    rows = [[bm.verts.new((x, y, z)) for (y, z) in prof] for x in (-20, 20)]
    for i in range(len(prof) - 1):
        bm.faces.new((rows[0][i], rows[1][i], rows[1][i + 1], rows[0][i + 1]))
    lib.mesh_from_bm(bm, 'Backdrop', lib.mat('Backdrop', '#7F90A6', rough=0.95))
    for loc, e, col, size in (((-2.0, -3.0, 3.2), 900, '#FFF4E8', 3.0), ((2.5, 2.5, 2.8), 500, '#DCE8FF', 2.0),
                              ((3.0, -3.0, 1.5), 250, '#E8F0FF', 3.0)):
        lib.look_at(lib.light('AREA', loc, energy=e, color=col, size=size), (0, 0, 1.0))
    views = [(-30, 6.0, 1.4, 0.9, 95), (0, 6.0, 1.2, 0.9, 95), (90, 6.0, 1.2, 0.9, 95), (180, 6.0, 1.2, 0.9, 95),
             (-25, 3.0, 1.45, 1.36, 85)]
    tiles = []
    for i, (az, dist, cz, tz, lens) in enumerate(views):
        p['root'].rotation_euler.z = math.radians(-az)       # turn the hero, keep the camera in front of the backdrop
        sc.camera = lib.camera((0, -dist, cz), (0, 0, tz), lens=lens)
        sc.render.filepath = path + f'_{i}.png'
        bpy.ops.render.render(write_still=True)
        tiles.append(Image.open(sc.render.filepath).convert('RGB'))
        os.remove(sc.render.filepath)
    sheet = Image.new('RGB', (res * len(tiles), res))
    for i, t in enumerate(tiles):
        sheet.paste(t, (res * i, 0))
    sheet.save(path, quality=88)


p = build()
if '--previews' in args:
    previews(p, os.path.join(HERE, 'preview.jpg'))
    p = build()
bake_for_gltf(p)
export(os.path.join(HERE, 'hero-aipollon.glb'))
print('OK', os.path.getsize(os.path.join(HERE, 'hero-aipollon.glb')))
