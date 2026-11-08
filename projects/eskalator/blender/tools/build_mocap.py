"""Перенести мокап CMU на риг ведущего и сохранить экшены mc_* в mocap.blend (один раз, фоном).
blender -b --python tools/build_mocap.py -- <hero.blend> <cmu_dir> <mpfb default_fk t-pose.json> <out mocap.blend> [id ...]"""
import bpy, sys, os, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'sets'))
import esk_mocap as MC
argv = sys.argv[sys.argv.index('--') + 1:]
hero, cmu, tp, out = argv[:4]
only = set(argv[4:])
bpy.ops.wm.read_factory_settings(use_empty=True)
with bpy.data.libraries.load(hero, link=False) as (src, dst):
    dst.collections = ['HeroChar']
col = dst.collections[0]
bpy.context.scene.collection.children.link(col)
rig = [o for o in col.objects if o.type == 'ARMATURE'][0]
tpose = json.load(open(tp))
acts = []
for cid, (kind, t0, ln) in MC.CLIPS.items():
    if only and cid not in only:
        continue
    p = os.path.join(cmu, cid + '.bvh')
    if not os.path.exists(p):
        print('MISSING', cid); continue
    a = MC.retarget(rig, p, tpose, kind=kind, t0=t0, length=ln, name='mc_%s_%s' % (kind, cid))
    acts.append(a)
    print('ACT', a.name, a['esk_frames'], round(a['esk_speed'], 2))
bpy.data.libraries.write(out, set(acts), fake_user=True, compress=True)
print('MOCAP_DONE', len(acts), out)
