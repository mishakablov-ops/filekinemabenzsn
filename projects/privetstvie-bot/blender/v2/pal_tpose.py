"""Раскраска модели Hunyuan чистой палитрой: цвет каждой грани берём из референса (фронт/тыл, с учётом видимости),
относим к классу (золото / кожа / ткань-волосы / тёмное) и красим чистым цветом класса."""
import bpy, math, numpy as np, colorsys, bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from PIL import Image
S=919/1.956; Z0=-0.998
IMG={k:np.asarray(Image.open('/tmp/claude-0/v2/tex_%s.png'%k).convert('RGB'),float)/255 for k in ('front','back')}
def srgb(h):
    h=h.lstrip('#'); c=[int(h[i:i+2],16)/255 for i in (0,2,4)]
    return tuple(x/12.92 if x<=0.04045 else ((x+0.055)/1.055)**2.4 for x in c)
PAL={'cloth':srgb('#f4ede3'),'hair':srgb('#f3e3c8'),'skin':srgb('#f5d2b8'),'gold':srgb('#e9a43a'),'dark':srgb('#6b4320')}
def sample(view,p):
    if view=='front': u=508.5+0.014*S+p.x*S
    else: u=496-0.014*S-p.x*S
    v=(972 if view=='front' else 969)-(p.z-Z0)*S
    u=int(np.clip(u,0,1023)); v=int(np.clip(v,0,1023))
    return IMG[view][v,u]
def classify(rgb,p,nrm):
    h,s,v=colorsys.rgb_to_hsv(*rgb); hd=h*360
    head = p.z>0.52 and abs(p.x)<0.2
    if abs(p.x)>0.235 and 0.18<p.z<0.5:          # руки в Т-позе: проекции нет, красим правилом
        return 'skin' if abs(p.x)>0.83 else 'cloth'
    hand = False
    if s>0.42 and 25<=hd<=55 and v>0.45: return 'gold'
    if head and v<0.45 and nrm.y<-0.3: return 'dark'
    if (hand and s>0.17) : return 'skin'
    if head and 0.52<p.z<0.80 and abs(p.x)<0.11 and nrm.y<-0.2 and s>0.13: return 'skin'
    if 0.5<p.z<0.62 and abs(p.x)<0.07: return 'skin'   # шея
    return 'hair' if head else 'cloth'
def paint(o):
    me=o.data
    bm=bmesh.new(); bm.from_mesh(me); bm.transform(o.matrix_world); bm.faces.ensure_lookup_table()
    bvh=BVHTree.FromBMesh(bm)
    cls=[]
    for f in bm.faces:
        c=f.calc_center_median(); n=f.normal; got=None
        for view,d in (('front',Vector((0,-1,0))),('back',Vector((0,1,0)))):
            if n.dot(d)<0.0: continue
            if bvh.ray_cast(c+d*0.002,d)[0] is None: got=sample(view,c); break
        if got is None:
            got=sample('front' if n.y<0 else 'back',c)
        cls.append(classify(got,c,n))
    bm.free()
    names=list(PAL); idx={k:i for i,k in enumerate(names)}
    me.materials.clear()
    for k in names:
        m=bpy.data.materials.new('ap_'+k); m.use_nodes=True; b=m.node_tree.nodes['Principled BSDF']
        b.inputs['Base Color'].default_value=(*PAL[k],1); b.inputs['Roughness'].default_value=0.45 if k=='gold' else 0.7
        if k=='gold': b.inputs['Metallic'].default_value=0.5
        if k in('cloth','hair','skin'): b.inputs['Sheen Weight'].default_value=0.3
        me.materials.append(m)
    mi=np.array([idx[c] for c in cls]); me.polygons.foreach_set('material_index',mi)
    for p in me.polygons: p.use_smooth=False
    from collections import Counter; print(Counter(cls))
def load():
    bpy.ops.import_scene.gltf(filepath='/tmp/claude-0/v3/tpose.glb')
    o=[x for x in bpy.context.scene.objects if x.type=='MESH'][0]; o.name='apollon'
    paint(o); return o
if __name__=='__main__':
    import sys
    bpy.ops.wm.read_factory_settings(use_empty=True)
    o=load(); sc=bpy.context.scene
    cam=bpy.data.cameras.new('c'); c=bpy.data.objects.new('c',cam); sc.collection.objects.link(c); sc.camera=c
    l=bpy.data.lights.new('s','SUN'); l.energy=3; lo=bpy.data.objects.new('s',l); sc.collection.objects.link(lo); lo.rotation_euler=(0.9,0.3,-0.6)
    w=bpy.data.worlds.new('w'); sc.world=w; w.use_nodes=True; w.node_tree.nodes['Background'].inputs[1].default_value=0.8
    sc.render.engine='CYCLES'; sc.cycles.samples=16; sc.render.resolution_x=sc.render.resolution_y=500; sc.view_settings.view_transform='Standard'
    shots=(('pf',0,6,0,30),('pq',35,6,0,30),('pb',180,6,0,30),('ph',0,2.2,0.72,85),('phq',30,2.2,0.72,85))
    for name,ang,d,z,lens in shots:
        a=math.radians(ang); cam.lens=lens*(1 if d<3 else 1.7)
        c.location=(d*math.sin(a),-d*math.cos(a),z); c.rotation_euler=(math.pi/2,0,a)
        sc.render.filepath='/tmp/claude-0/v3/%s.png'%name; bpy.ops.render.render(write_still=True)
