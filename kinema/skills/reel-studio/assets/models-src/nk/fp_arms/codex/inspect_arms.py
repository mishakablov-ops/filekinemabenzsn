import bpy,bmesh,json,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(ROOT/'source_arms/scene.gltf'))
obs=[o for o in bpy.context.scene.objects if o.type=='MESH']
for o in obs:
    w=o.matrix_world.copy();o.parent=None;o.matrix_world=w
    bpy.context.view_layer.objects.active=o;o.select_set(True)
    bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
    for v in o.data.vertices:v.co*=.01
for o in list(bpy.context.scene.objects):
    if o.type!='MESH':bpy.data.objects.remove(o,do_unlink=True)
o=obs[0];o.name='source_arms'
bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-5);bm.to_mesh(o.data);bm.free()
v=[list(v.co) for v in o.data.vertices];f=[list(p.vertices) for p in o.data.polygons]
adj=[set() for _ in v]
for face in f:
    for a in face:
        adj[a].update(face)
remaining=set(range(len(v)));components=[]
while remaining:
    stack=[remaining.pop()];part=[]
    while stack:
        a=stack.pop();part.append(a)
        for b in adj[a]:
            if b in remaining:remaining.remove(b);stack.append(b)
    components.append(part)
report={'vertices':v,'faces':f,'components':components}
(ROOT/'source_geometry.json').write_text(json.dumps(report))
print('COMPONENTS',[(len(c),[[min(v[i][k] for i in c),max(v[i][k] for i in c)] for k in range(3)]) for c in components])
s=bpy.context.scene;s.render.engine='BLENDER_EEVEE_NEXT';s.render.resolution_x=1200;s.render.resolution_y=1200;s.render.resolution_percentage=100;s.world=bpy.data.worlds.new('world');s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs[0].default_value=(.2,.2,.2,1)
lo=Vector([min(p[k] for p in v) for k in range(3)]);hi=Vector([max(p[k] for p in v) for k in range(3)]);center=(lo+hi)*.5;span=max(hi-lo)
for i,d in enumerate([(-.6,-.7,1),(.6,.7,1),(.5,-1,-.3)]):
    data=bpy.data.lights.new('light'+str(i),'AREA');data.energy=100;data.size=span
    ob=bpy.data.objects.new('light'+str(i),data);s.collection.objects.link(ob);ob.location=center+Vector(d)*span;ob.rotation_euler=(center-ob.location).to_track_quat('-Z','Y').to_euler()
for name,d in [('top',(0,0,1)),('bottom',(0,0,-1)),('front',(0,-1,0)),('side',(1,0,0)),('threequarter',(.8,-.8,1))]:
    data=bpy.data.cameras.new(name);data.type='ORTHO';data.ortho_scale=span*1.25;cam=bpy.data.objects.new(name,data);s.collection.objects.link(cam);cam.location=center+Vector(d)*span*2;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();s.camera=cam
    s.render.filepath=str(ROOT/(name+'.png'));bpy.ops.render.render(write_still=True)
for im in bpy.data.images:
    if im.source!='VIEWER':im.pack()
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'inspection.blend'))
