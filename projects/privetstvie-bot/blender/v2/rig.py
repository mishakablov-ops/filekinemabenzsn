import bpy, math, sys
sys.path.insert(0,'/tmp/claude-0/v2'); import pal
from mathutils import Vector
def _weights(o,ad):
    import numpy as np
    me=o.data; co=np.empty(len(me.vertices)*3); me.vertices.foreach_get('co',co); co=co.reshape(-1,3)
    mw=np.array(o.matrix_world); co=co@mw[:3,:3].T+mw[:3,3]
    names=[b.name for b in ad.bones]; W=[]
    def sm(e0,e1,x): t=np.clip((x-e0)/(e1-e0),0,1); return t*t*(3-2*t)
    for b in ad.bones:
        h=np.array(b.head_local); t=np.array(b.tail_local); d=t-h
        u=np.clip(((co-h)@d)/(d@d),0,1); dist=np.linalg.norm(co-(h+u[:,None]*d),axis=1)
        w=1/(dist**4+1e-6)
        if b.name.endswith('.R') and not b.name.startswith('leg'):
            m=sm(-0.17,-0.235,co[:,0]) if b.name!='sh.R' else sm(-0.02,-0.12,co[:,0])
            if b.name!='sh.R': m=m*sm(-0.32,-0.2,co[:,2]) if b.name=='ha.R' else m   # кисть не тащит штанину
            w=w*m
        if b.name.endswith('.L') and not b.name.startswith('leg'):
            w=w*(sm(0.17,0.235,co[:,0]) if b.name!='sh.L' else sm(0.02,0.12,co[:,0]))
        if b.name.startswith('up.') or b.name.startswith('fo.') or b.name.startswith('ha.'):
            w=w*(co[:,2]<0.47)
        W.append(w)
    W=np.array(W)
    # жёсткое разделение руки и корпуса ниже плеча (меш Hunyuan сросся), иначе при подъёме тянутся перепонки
    D={n:i for i,n in enumerate(names)}; cuts=[]
    for side,sg in (('R',-1),('L',1)):
        armi=[D['up.'+side],D['fo.'+side],D['ha.'+side]]
        pts=[np.array(ad.bones['up.'+side].head_local),np.array(ad.bones['fo.'+side].head_local),
             np.array(ad.bones['ha.'+side].head_local),np.array(ad.bones['ha.'+side].tail_local)]
        dm=np.full(len(co),9.0)
        for h,t in zip(pts[:-1],pts[1:]):
            d=t-h; u=np.clip(((co-h)@d)/(d@d),0,1); dm=np.minimum(dm,np.linalg.norm(co-(h+u[:,None]*d),axis=1))
        inarm=(sg*co[:,0]>0.158)&(co[:,2]<0.43)&(dm<0.105)
        cuts.append(inarm)
        low=co[:,2]<0.43
        for i in range(len(names)):
            if i in armi: W[i,low&~inarm]=0
            else: W[i,inarm]=0
    W=W/np.maximum(W.sum(0,keepdims=True),1e-9)
    return W,names,cuts
def build(paint=True):
    if paint: o=pal.load()
    else:
        bpy.ops.import_scene.gltf(filepath='/tmp/claude-0/v2/apollon-hunyuan-white_mesh.glb')
        o=[x for x in bpy.context.scene.objects if x.type=='MESH'][0]
    # чистка: слить дубли вершин, чтобы веса не рвали меш
    bpy.context.view_layer.objects.active=o; o.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.remove_doubles(threshold=0.0005); bpy.ops.object.mode_set(mode='OBJECT')
    ad=bpy.data.armatures.new('rig'); arm=bpy.data.objects.new('rig',ad); bpy.context.scene.collection.objects.link(arm)
    bpy.context.view_layer.objects.active=arm; bpy.ops.object.mode_set(mode='EDIT')
    E=ad.edit_bones
    def bone(n,h,t,parent=None,conn=False):
        b=E.new(n); b.head=h; b.tail=t
        if parent: b.parent=E[parent]; b.use_connect=conn
        return b
    y=-0.06
    bone('hips',(0,y,-0.05),(0,y,0.2)); bone('chest',(0,y,0.2),(0,y,0.5),'hips',True)
    bone('neck',(0,y,0.5),(0,y,0.6),'chest',True); bone('head',(0,y,0.6),(0,y,0.95),'neck',True)
    for s,side in ((-1,'R'),(1,'L')):
        bone('sh.'+side,(s*0.08,y,0.44),(s*0.22,y,0.42),'chest')
        bone('up.'+side,(s*0.23,y,0.41),(s*0.29,y,0.09),'sh.'+side,False)
        bone('fo.'+side,(s*0.29,y,0.09),(s*0.32,y,-0.14),'up.'+side,True)
        bone('ha.'+side,(s*0.32,y,-0.14),(s*0.33,y,-0.27),'fo.'+side,True)
    bone('leg.R',(-0.11,y,-0.05),(-0.13,y,-0.95),'hips'); bone('leg.L',(0.11,y,-0.05),(0.13,y,-0.95),'hips')
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); arm.select_set(True); bpy.context.view_layer.objects.active=arm
    bpy.ops.object.parent_set(type='ARMATURE_NAME')
    W,names,cuts=_weights(o,ad)
    # разрезать грани, которые сшивают руку с корпусом ниже плеча
    import bmesh, numpy as np
    bm=bmesh.new(); bm.from_mesh(o.data); bm.verts.ensure_lookup_table()
    inarm=cuts[0]|cuts[1]
    bad=[f for f in bm.faces if len({bool(inarm[v.index]) for v in f.verts})>1 and min(v.co.z for v in f.verts)<0.41]
    print('cut faces',len(bad)); bmesh.ops.delete(bm,geom=bad,context='FACES_ONLY'); bm.to_mesh(o.data); bm.free()
    W,names,cuts=_weights(o,ad)
    co=None
    for i,n in enumerate(names):
        g=o.vertex_groups.get(n) or o.vertex_groups.new(name=n); idx=np.nonzero(W[i]>0.01)[0]
        for k in idx: g.add([int(k)],float(W[i,k]),'REPLACE')
    nz=sum(1 for v in o.data.vertices if len(v.groups)==0); print('unweighted verts',nz,'of',len(o.data.vertices))
    return o,arm
def aim(arm,name,d):
    from mathutils import Matrix
    pb=arm.pose.bones[name]; rest=pb.bone.matrix_local
    d=Vector(d).normalized(); y=(rest.to_3x3()@Vector((0,1,0))).normalized()
    q=y.rotation_difference(d)
    head=pb.head.copy() if pb.parent is None or not pb.bone.use_connect else pb.parent.tail.copy()
    if pb.bone.use_connect: head=arm.pose.bones[pb.parent.name].tail.copy()
    pb.matrix=Matrix.Translation(head)@(q@rest.to_quaternion()).to_matrix().to_4x4()
    bpy.context.view_layer.update()
def pose(arm,f,N=24):
    for pb in arm.pose.bones: pb.rotation_mode='QUATERNION'
    w=math.sin(math.tau*f/N)
    aim(arm,'up.R',(-0.80,-0.25,0.55+0.03*w))
    a=0.35+0.38*w                       # угол предплечья от вертикали, взмах
    aim(arm,'fo.R',(-math.sin(a),-0.25,math.cos(a)))
    b=a+0.25*math.sin(math.tau*f/N-0.9)
    aim(arm,'ha.R',(-math.sin(b),-0.2,math.cos(b)))
if __name__=='__main__':
    bpy.ops.wm.read_factory_settings(use_empty=True)
    o,arm=build(); sc=bpy.context.scene
    cam=bpy.data.cameras.new('c'); c=bpy.data.objects.new('c',cam); sc.collection.objects.link(c); sc.camera=c
    l=bpy.data.lights.new('s','SUN'); l.energy=3; lo=bpy.data.objects.new('s',l); sc.collection.objects.link(lo); lo.rotation_euler=(0.9,0.3,-0.6)
    w=bpy.data.worlds.new('w'); sc.world=w; w.use_nodes=True; w.node_tree.nodes['Background'].inputs[1].default_value=0.8
    sc.render.engine='CYCLES'; sc.cycles.samples=12; sc.render.resolution_x=sc.render.resolution_y=500; sc.view_settings.view_transform='Standard'
    for name,ang,f in (('r1',0,6),('r2',15,18),('r3',40,6),('r4',-35,18)):
        pose(arm,f); bpy.context.view_layer.update()
        a=math.radians(ang); cam.lens=45
        c.location=(2.2*math.sin(a),-2.2*math.cos(a),0.45); c.rotation_euler=(math.pi/2,0,a)
        sc.render.filepath='/tmp/claude-0/v2/%s.png'%name; bpy.ops.render.render(write_still=True)
