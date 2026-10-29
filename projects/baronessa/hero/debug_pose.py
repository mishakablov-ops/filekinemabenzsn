import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'blender'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'blender', 'sets'))
import bpy
import lib
lib.reset()
import sila_hero as SH
import baroness as B
b = B.load()
for name in ('stand', 'strict', 'hold_gun'):
    SH.apply(b, B.P(name))
    bpy.context.view_layer.update()
    rig = b['rig']
    for bn in ('LeftArm', 'LeftForeArm', 'RightArm', 'Head'):
        pb = rig.pose.bones[bn]
        d = (pb.tail - pb.head).normalized()
        print(name, bn, 'dir', tuple(round(v, 2) for v in d))
