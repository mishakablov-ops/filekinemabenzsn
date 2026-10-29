"""Rig the generated baroness (mesh/baroness_a.glb) with the same bone names as the channel hero (HeroRig), so the pose
code of sila_hero.py (directions of limbs, walk) drives her too.
    blender -b --factory-startup --python rig_baroness.py -- <glb> <out.blend> [<test.jpg>]
Joints are read off the front/side views of the T-pose mesh (inspect_glb.py), in the mesh's own units, then the figure
is put on the floor and scaled to 1.68 m. Front is -Y, her left is +X.
"""
import math
import sys

import bpy
from mathutils import Vector

args = sys.argv[sys.argv.index('--') + 1:]
glb, out = args[0], args[1]
test = args[2] if len(args) > 2 else ''

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
body = next(o for o in bpy.context.scene.objects if o.type == 'MESH')
for o in list(bpy.context.scene.objects):
    if o is not body:
        if o.type != 'MESH':
            body.parent = None
        bpy.data.objects.remove(o)
bpy.context.view_layer.objects.active = body
body.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

V = 'c' if 'baroness_c' in glb else 'a'          # v2 (28.10): the meme's face, very plump, a straight T-pose
LO_Z, H = (-0.866, 1.732) if V == 'c' else (-0.87, 1.735)
S = (1.70 if V == 'c' else 1.68) / H


def P(x, y, z):
    """mesh units (as inspected) -> metres on the floor"""
    return Vector((x * S, y * S, (z - LO_Z) * S))


for v in body.data.vertices:
    v.co = P(*v.co)
body.data.update()
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.remove_doubles(threshold=0.0004)
bpy.ops.object.mode_set(mode='OBJECT')
body.name = 'Baroness'

# joints (mesh units). Arms hang ~38 degrees below horizontal in the reference A-pose.
J = {
    'Hips': (0, 0.01, -0.02), 'Spine': (0, 0.01, 0.10), 'Spine1': (0, 0.01, 0.24), 'Spine2': (0, 0.01, 0.38),
    'Neck': (0, 0.015, 0.56), 'Head': (0, 0.0, 0.64), 'HeadTop': (0, 0.0, 0.865),
}
for s, nm in ((1, 'Left'), (-1, 'Right')):
    J[nm + 'Shoulder'] = (s * 0.05, 0.02, 0.52)
    J[nm + 'Arm'] = (s * 0.18, 0.02, 0.515)
    J[nm + 'ForeArm'] = (s * 0.365, 0.03, 0.34)
    J[nm + 'Hand'] = (s * 0.57, 0.02, 0.18)
    J[nm + 'HandTip'] = (s * 0.72, 0.0, 0.10)
    J[nm + 'UpLeg'] = (s * 0.085, 0.01, -0.06)
    J[nm + 'Leg'] = (s * 0.06, 0.0, -0.50)
    J[nm + 'Foot'] = (s * 0.045, 0.04, -0.77)
    J[nm + 'ToeBase'] = (s * 0.045, -0.12, -0.85)
    J[nm + 'ToeEnd'] = (s * 0.045, -0.17, -0.855)
if V == 'c':   # read off inspect_c_front.jpg: arms straight out at shoulder height, wide hips
    J.update({'Hips': (0, 0.02, -0.04), 'Spine': (0, 0.02, 0.08), 'Spine1': (0, 0.02, 0.22), 'Spine2': (0, 0.02, 0.36),
              'Neck': (0, 0.02, 0.565), 'Head': (0, 0.01, 0.625), 'HeadTop': (0, 0.0, 0.857)})
    for s, nm in ((1, 'Left'), (-1, 'Right')):
        J[nm + 'Shoulder'] = (s * 0.07, 0.03, 0.53)
        J[nm + 'Arm'] = (s * 0.23, 0.03, 0.525)
        J[nm + 'ForeArm'] = (s * 0.475, 0.04, 0.42)
        J[nm + 'Hand'] = (s * 0.675, 0.03, 0.385)
        J[nm + 'HandTip'] = (s * 0.83, 0.0, 0.385)
        J[nm + 'UpLeg'] = (s * 0.11, 0.02, -0.07)
        J[nm + 'Leg'] = (s * 0.105, 0.0, -0.505)
        J[nm + 'Foot'] = (s * 0.1, 0.04, -0.745)
        J[nm + 'ToeBase'] = (s * 0.1, -0.12, -0.845)
        J[nm + 'ToeEnd'] = (s * 0.1, -0.17, -0.85)

CHAIN = [('Hips', 'Spine', None), ('Spine', 'Spine1', 'Hips'), ('Spine1', 'Spine2', 'Spine'), ('Spine2', 'Neck', 'Spine1'),
         ('Neck', 'Head', 'Spine2'), ('Head', 'HeadTop', 'Neck')]
for nm in ('Left', 'Right'):
    CHAIN += [(nm + 'Shoulder', nm + 'Arm', 'Spine2'), (nm + 'Arm', nm + 'ForeArm', nm + 'Shoulder'),
              (nm + 'ForeArm', nm + 'Hand', nm + 'Arm'), (nm + 'Hand', nm + 'HandTip', nm + 'ForeArm'),
              (nm + 'UpLeg', nm + 'Leg', 'Hips'), (nm + 'Leg', nm + 'Foot', nm + 'UpLeg'),
              (nm + 'Foot', nm + 'ToeBase', nm + 'Leg'), (nm + 'ToeBase', nm + 'ToeEnd', nm + 'Foot')]

arm = bpy.data.armatures.new('BaronessRig')
rig = bpy.data.objects.new('BaronessRig', arm)
bpy.context.scene.collection.objects.link(rig)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='EDIT')
eb = arm.edit_bones
for name, tail, par in CHAIN:
    b = eb.new(name)
    b.head, b.tail = P(*J[name]), P(*J[tail])
    if par:
        b.parent = eb[par]
        b.use_connect = (eb[par].tail - b.head).length < 1e-4
    if name == 'Hips':   # Hips points up like the hero's
        b.tail = b.head + Vector((0, 0, 0.1))
    b.roll = 0.0
    # the clavicle bone sits on the upper arm: with heat weights it took the sleeve and the arm would not move
    if name.endswith('Shoulder') or name.endswith('HandTip') or name in ('HeadTop',):
        b.use_deform = False
bpy.ops.object.mode_set(mode='OBJECT')

bpy.ops.object.select_all(action='DESELECT')
body.select_set(True)
rig.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.parent_set(type='ARMATURE_AUTO')
used = {}
unweighted = 0
for v in body.data.vertices:
    if not v.groups:
        unweighted += 1
    for e in v.groups:
        if e.weight > 0.05:
            used[e.group] = used.get(e.group, 0) + 1
print('GROUPS', {g.name: used.get(g.index, 0) for g in body.vertex_groups}, 'unweighted', unweighted, flush=True)
if len(body.vertex_groups) == 0:
    raise SystemExit('auto weights failed')

for m in body.data.materials:
    if m and m.use_nodes:
        for n in m.node_tree.nodes:
            if n.type == 'BSDF_PRINCIPLED':
                n.inputs['Specular IOR Level'].default_value = 0.3
bpy.ops.wm.save_as_mainfile(filepath=out)
print('SAVED', out, flush=True)
