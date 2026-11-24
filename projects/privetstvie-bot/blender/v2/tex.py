import bpy, math, numpy as np
from mathutils import Vector
S=919/1.956; Z0=-0.998  # px на метр, низ модели
def setup_model():
    bpy.ops.import_scene.gltf(filepath='/tmp/claude-0/v2/apollon-hunyuan-white_mesh.glb')
    o=[x for x in bpy.context.scene.objects if x.type=='MESH'][0]
    o.name='apollon'; me=o.data
    n=len(me.loops); vi=np.empty(n,int); me.loops.foreach_get('vertex_index',vi)
    co=np.empty(len(me.vertices)*3); me.vertices.foreach_get('co',co); co=co.reshape(-1,3)
    mw=np.array(o.matrix_world); co=co@mw[:3,:3].T+mw[:3,3]
    P=co[vi]
    def uv(cx,sign,bottom):
        u=(cx+sign*P[:,0]*S)/1024; v=1-(bottom-(P[:,2]-Z0)*S)/1024
        return np.stack([u,v],1).ravel()
    for name,cx,sign,bottom in (('front',508.5+0.014*S,1,972),('back',496-0.014*S,-1,969)):
        l=me.uv_layers.new(name=name); l.data.foreach_set('uv',uv(cx,sign,bottom))
    m=bpy.data.materials.new('apollon'); m.use_nodes=True; nt=m.node_tree; N=nt.nodes; L=nt.links
    b=N['Principled BSDF']; b.inputs['Roughness'].default_value=0.7
    tf=N.new('ShaderNodeTexImage'); tf.image=bpy.data.images.load('/tmp/claude-0/v2/tex_front.png')
    tb=N.new('ShaderNodeTexImage'); tb.image=bpy.data.images.load('/tmp/claude-0/v2/tex_back.png')
    for t,nm in ((tf,'front'),(tb,'back')):
        u=N.new('ShaderNodeUVMap'); u.uv_map=nm; L.new(u.outputs[0],t.inputs[0])
    # вес по нормали: смотрит на -Y -> фронт, +Y -> спина (в координатах объекта)
    geo=N.new('ShaderNodeNewGeometry'); sep=N.new('ShaderNodeSeparateXYZ'); L.new(geo.outputs['Normal'],sep.inputs[0])
    mr=N.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value=-0.25; mr.inputs['From Max'].default_value=0.25
    L.new(sep.outputs['Y'],mr.inputs['Value'])
    mix=N.new('ShaderNodeMix'); mix.data_type='RGBA'
    L.new(mr.outputs[0],mix.inputs['Factor']); L.new(tf.outputs[0],mix.inputs[6]); L.new(tb.outputs[0],mix.inputs[7])
    # снять запечённые тени фото: поднять яркость и контраст чуть вниз
    hsv=N.new('ShaderNodeHueSaturation'); hsv.inputs['Value'].default_value=1.08; hsv.inputs['Saturation'].default_value=1.1
    L.new(mix.outputs[2],hsv.inputs['Color']); L.new(hsv.outputs[0],b.inputs['Base Color'])
    # видимость граней из фронт/тыл камеры (лучи BVH), чтобы кулак не отпечатался на бедре
    from mathutils.bvhtree import BVHTree
    import bmesh
    bm=bmesh.new(); bm.from_mesh(me); bm.transform(o.matrix_world); bm.faces.ensure_lookup_table()
    bvh=BVHTree.FromBMesh(bm)
    vis=np.zeros((len(bm.faces),2))
    for f in bm.faces:
        c=f.calc_center_median(); nr=f.normal
        for k,d in enumerate((Vector((0,-1,0)),Vector((0,1,0)))):
            if nr.dot(d) < -0.05: continue
            hit=bvh.ray_cast(c+d*0.002,d)
            vis[f.index,k]= 0.0 if hit[0] is not None else 1.0
    bm.free()
    attr=me.color_attributes.new('vis','FLOAT_COLOR','CORNER')
    fl=np.zeros(len(me.loops)); me.polygons.foreach_get  # noqa
    li=np.empty(len(me.polygons),int); me.polygons.foreach_get('loop_start',li)
    lt=np.empty(len(me.polygons),int); me.polygons.foreach_get('loop_total',lt)
    col=np.zeros((len(me.loops),4)); col[:,3]=1
    for p in range(len(me.polygons)):
        col[li[p]:li[p]+lt[p],0]=vis[p,0]; col[li[p]:li[p]+lt[p],1]=vis[p,1]
    attr.data.foreach_set('color',col.ravel())
    at=N.new('ShaderNodeAttribute'); at.attribute_name='vis'; sv=N.new('ShaderNodeSeparateColor'); L.new(at.outputs[0],sv.inputs[0])
    # фронт виден -> фронт, иначе тыл виден -> тыл, иначе кремовый
    cream=(0.82,0.76,0.68,1)
    m1=N.new('ShaderNodeMix'); m1.data_type='RGBA'; m1.inputs[6].default_value=cream
    L.new(sv.outputs[1],m1.inputs['Factor']); L.new(tb.outputs[0],m1.inputs[7])
    m2=N.new('ShaderNodeMix'); m2.data_type='RGBA'
    # вес фронта: виден спереди и нормаль не смотрит назад
    mul=N.new('ShaderNodeMath'); mul.operation='MULTIPLY'; L.new(sv.outputs[0],mul.inputs[0])
    inv=N.new('ShaderNodeMath'); inv.operation='SUBTRACT'; inv.inputs[0].default_value=1; L.new(mr.outputs[0],inv.inputs[1]); L.new(inv.outputs[0],mul.inputs[1])
    mx=N.new('ShaderNodeMath'); mx.operation='MAXIMUM'; L.new(mul.outputs[0],mx.inputs[0]); L.new(sv.outputs[0],mx.inputs[1])
    fw=N.new('ShaderNodeMath'); fw.operation='MULTIPLY'; L.new(sv.outputs[0],fw.inputs[0])
    bkv=N.new('ShaderNodeMath'); bkv.operation='SUBTRACT'; bkv.inputs[0].default_value=1; L.new(sv.outputs[1],bkv.inputs[1])
    mx2=N.new('ShaderNodeMath'); mx2.operation='MAXIMUM'; L.new(inv.outputs[0],mx2.inputs[0]); L.new(bkv.outputs[0],mx2.inputs[1]); L.new(mx2.outputs[0],fw.inputs[1])
    L.new(fw.outputs[0],m2.inputs['Factor']); L.new(m1.outputs[2],m2.inputs[6]); L.new(tf.outputs[0],m2.inputs[7])
    L.new(m2.outputs[2],hsv.inputs['Color'])
    me.materials.clear(); me.materials.append(m)
    for p in me.polygons: p.use_smooth=False
    return o
if __name__=='__main__':
    bpy.ops.wm.read_factory_settings(use_empty=True)
    o=setup_model(); sc=bpy.context.scene
    cam=bpy.data.cameras.new('c'); cam.type='ORTHO'; cam.ortho_scale=2.1
    c=bpy.data.objects.new('c',cam); sc.collection.objects.link(c); sc.camera=c
    l=bpy.data.lights.new('s','SUN'); l.energy=2.5; lo=bpy.data.objects.new('s',l); sc.collection.objects.link(lo); lo.rotation_euler=(0.9,0.3,-0.6)
    w=bpy.data.worlds.new('w'); sc.world=w; w.use_nodes=True; w.node_tree.nodes['Background'].inputs[1].default_value=1.2
    sc.render.engine='CYCLES'; sc.cycles.samples=12; sc.render.resolution_x=sc.render.resolution_y=600; sc.view_settings.view_transform='Standard'
    for name,ang in (('front',0),('q',35),('side',90),('back',180)):
        a=math.radians(ang); d=6
        c.location=(d*math.sin(a),-d*math.cos(a),0); c.rotation_euler=(math.pi/2,0,a)
        sc.render.filepath='/tmp/claude-0/v2/tx_%s.png'%name; bpy.ops.render.render(write_still=True)
