"""Служебное: выписать кости рига ведущего (hero.blend) и скелета CMU BVH в JSON для настройки ретаргета.
blender -b --python tools/dump_rigs.py -- <hero.blend> <file.bvh> <out.json>"""
import bpy, sys, json
argv = sys.argv[sys.argv.index('--') + 1:]
hero, bvh, out = argv
bpy.ops.wm.read_factory_settings(use_empty=True)
res = {}
with bpy.data.libraries.load(hero, link=False) as (src, dst):
    dst.collections = ['HeroChar']
col = dst.collections[0]
bpy.context.scene.collection.children.link(col)
rig = [o for o in col.objects if o.type == 'ARMATURE'][0]
def dump(arm):
    bl = []
    for b in arm.data.bones:
        bl.append(dict(n=b.name, p=b.parent.name if b.parent else None, h=[round(x, 4) for x in (arm.matrix_world @ b.head_local)],
                       t=[round(x, 4) for x in (arm.matrix_world @ b.tail_local)]))
    return bl
res['hero'] = dump(rig)
res['hero_mw'] = [list(r) for r in rig.matrix_world]
bpy.ops.import_anim.bvh(filepath=bvh, global_scale=1.0, rotate_mode='NATIVE', axis_forward='-Z', axis_up='Y')
b = bpy.context.active_object
res['bvh'] = dump(b)
res['bvh_frames'] = [bpy.context.scene.frame_start, bpy.context.scene.frame_end]
res['bvh_fps'] = bpy.context.scene.render.fps
json.dump(res, open(out, 'w'), indent=0)
print('DUMP_OK', len(res['hero']), len(res['bvh']))
