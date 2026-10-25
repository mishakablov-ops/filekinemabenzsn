import bpy,bmesh,math,json,sys
from pathlib import Path
from mathutils import Vector,Quaternion,Matrix

ROOT=Path(__file__).resolve().parent
OUT=ROOT.parent/'fps_arms_kinema'
for folder in ['blend','glb','previews','validation','integration','examples','source']:(OUT/folder).mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'inspection.blend'))
mesh=bpy.data.objects['source_arms']
for o in list(bpy.data.objects):
    if o!=mesh:bpy.data.objects.remove(o,do_unlink=True)
mesh.name='fp_arms_mesh';mesh.data.name='fp_arms_mesh'
# The source is symmetric, in centimetres; inspect_arms converted to metres.
# Rotate by 180 degrees around Z, then place the shoulders below/behind eye origin.
OFFSET=Vector((0,.25,-.40))
raw=[]
for v in mesh.data.vertices:
    v.co.x*=-1;v.co.y*=-1;raw.append(v.co.copy());v.co+=OFFSET
if len(mesh.data.uv_layers)>1:
    for uv in list(mesh.data.uv_layers)[1:]:mesh.data.uv_layers.remove(uv)
mesh.data.uv_layers[0].name='uv0'
mesh.data.materials[0].name='fp_arms_fabric_gloves'
for im in bpy.data.images:
    if im.source!='VIEWER':im.pack()

# Anatomical centers were fitted to the user's actual mesh in three orthographic views.
L={
 'Shoulder':[(-.105,-.226,.131),(-.205,-.226,.131)],
 'Arm':[(-.205,-.226,.131),(-.212,-.005,.045)],
 'ForeArm':[(-.212,-.005,.045),(-.203,.227,-.007)],
 'Hand':[(-.203,.227,-.007),(-.201,.319,-.022)],
 'Thumb':[(-.203,.246,.005),(-.187,.274,.022),(-.157,.305,.034),(-.130,.327,.040),(-.108,.344,.040)],
 'Index':[(-.203,.253,.000),(-.201,.339,.013),(-.178,.387,.005),(-.151,.418,-.004),(-.132,.431,-.014)],
 'Middle':[(-.207,.252,-.013),(-.211,.329,-.018),(-.188,.380,-.036),(-.159,.414,-.049),(-.135,.428,-.056)],
 'Ring':[(-.209,.250,-.028),(-.211,.311,-.045),(-.190,.356,-.064),(-.161,.388,-.076),(-.136,.400,-.080)],
 'Pinky':[(-.211,.246,-.039),(-.208,.288,-.069),(-.185,.328,-.085),(-.159,.352,-.092),(-.141,.367,-.094)],
}
FINGERS=['Thumb','Index','Middle','Ring','Pinky']
bpy.ops.object.armature_add(enter_editmode=True,location=(0,0,0));rig=bpy.context.object;rig.name='fp_arms_rig';rig.data.name='fp_arms_skeleton';rig.show_in_front=True;rig.data.display_type='STICK'
eb=rig.data.edit_bones;eb.remove(eb[0]);root=eb.new('Root');root.head=(0,0,0);root.tail=(0,.08,0)
chains={};specs={}
for side,prefix,sign in [('L','Left',1),('R','Right',-1)]:
    def p(co):return Vector((co[0]*sign,co[1],co[2]))+OFFSET
    def bone(name,a,b,parent):
        ob=eb.new(name);ob.head=p(a);ob.tail=p(b);ob.parent=eb[parent];ob.use_deform=True
        ob.align_roll(Vector((sign,0,0)))
        specs[name]={'head':list(ob.head),'tail':list(ob.tail),'parent':parent,'side':side};return ob
    for part,parent in [('Shoulder','Root'),('Arm',prefix+'Shoulder'),('ForeArm',prefix+'Arm'),('Hand',prefix+'ForeArm')]:bone(prefix+part,*L[part],parent)
    bone(prefix+'ForeArmTwist',*L['ForeArm'],prefix+'ForeArm')
    for finger in FINGERS:
        pts=L[finger]
        for j in range(4):bone(prefix+'Hand'+finger+str(j),pts[j],pts[j+1],prefix+'Hand' if j==0 else prefix+'Hand'+finger+str(j-1))
    chains[side]={'prefix':prefix,'shoulder':prefix+'Arm','elbow':prefix+'ForeArm','wrist':prefix+'Hand','twist':prefix+'ForeArmTwist'}
bpy.ops.object.mode_set(mode='OBJECT')

def clamp(x,a=0,b=1):return min(b,max(a,x))
def smooth(x):x=clamp(x);return x*x*(3-2*x)
def projection(p,a,b):
    a,b=Vector(a),Vector(b);d=b-a;t=clamp((p-a).dot(d)/d.length_squared);return (p-(a+t*d)).length,t
def digit_weights(p,finger):
    pts=[Vector(x) for x in L[finger][1:]]
    distances=[projection(p,pts[j],pts[j+1]) for j in range(3)]
    idx=min(range(3),key=lambda j:distances[j][0]);d,t=distances[idx]
    lengths=[(pts[j+1]-pts[j]).length for j in range(3)];s=sum(lengths[:idx])+lengths[idx]*t
    weights={idx+1:1.0}
    width=.010 if finger!='Thumb' else .009
    for joint in [1,2]:
        boundary=sum(lengths[:joint]);q=(s-boundary)/width
        if abs(q)<1:
            w=smooth((q+1)/2);weights={joint:1-w,joint+1:w};break
    if s<.012:
        bend=smooth((s+.007)/.019);weights={0:1-bend,1:bend}
    return d,weights

groups={name:mesh.vertex_groups.new(name=name) for name in specs}
counts={name:0 for name in specs}
for i,point in enumerate(raw):
    prefix='Left' if point.x<0 else 'Right';p=point.copy();p.x=-abs(p.x);y=p.y
    weights={}
    if y<.205:
        arm=smooth((y+.045)/.080);twist=smooth((y-.055)/.145)*.8
        weights={prefix+'Arm':1-arm,prefix+'ForeArm':arm*(1-twist),prefix+'ForeArmTwist':arm*twist}
        if y>.190:
            hand=smooth((y-.190)/.055);weights={k:v*(1-hand) for k,v in weights.items()};weights[prefix+'Hand']=hand
    else:
        candidates=[]
        for finger in FINGERS:
            mcp=Vector(L[finger][1]);direction=(Vector(L[finger][2])-mcp).normalized()
            d,w=digit_weights(p,finger)
            gate=(p-mcp).dot(direction)>-.012
            if finger=='Thumb':gate=gate and p.x>-.19 and p.z>-.001
            if gate:candidates.append((d,finger,w))
        if candidates and min(candidates)[0]<.028:
            d,finger,w=min(candidates);weights={prefix+'Hand'+finger+str(k):value for k,value in w.items()}
        else:
            hand=smooth((y-.190)/.055);weights={prefix+'ForeArmTwist':1-hand,prefix+'Hand':hand}
            # Allow a modest metacarpal contribution in the upper palm, without cross-finger leakage.
            if y>.263:
                closest=min(FINGERS,key=lambda finger:projection(p,*L[finger][:2])[0]);d,t=projection(p,*L[closest][:2]);w=.45*smooth((t-.30)/.65)
                weights={k:v*(1-w) for k,v in weights.items()};weights[prefix+'Hand'+closest+'0']=w
    weights={k:v for k,v in weights.items() if v>1e-5};weights=dict(sorted(weights.items(),key=lambda kv:-kv[1])[:4]);total=sum(weights.values())
    for name,w in weights.items():groups[name].add([i],w/total,'REPLACE');counts[name]+=1
mod=mesh.modifiers.new('fp_arms_skin','ARMATURE');mod.object=rig;mod.use_deform_preserve_volume=False
mesh.parent=rig
for bone in rig.pose.bones:bone.rotation_mode='QUATERNION'

# Record rest transforms for repeatable world-space FK/IK posing.
REST={b.name:b.matrix.copy() for b in rig.pose.bones}
def reset_pose():
    for b in rig.pose.bones:b.matrix_basis=Matrix.Identity(4)
    bpy.context.view_layer.update()
def set_world_delta(bone,direction):
    q=(bone.tail-bone.head).normalized().rotation_difference(direction.normalized())
    m=bone.matrix.copy();head=m.translation.copy();rot=q.to_matrix().to_4x4();out=Matrix.Translation(head)@rot@Matrix.Translation(-head)@m
    bone.matrix=out;bpy.context.view_layer.update()
def ik(side,target,pole=None,rotation=(0,0,0)):
    prefix=chains[side]['prefix'];arm=rig.pose.bones[prefix+'Arm'];fore=rig.pose.bones[prefix+'ForeArm'];hand=rig.pose.bones[prefix+'Hand']
    shoulder=arm.head.copy();target=Vector(target);pole=Vector(pole or ((-.45 if side=='L' else .45),.20,-.60))
    l1=rig.data.bones[prefix+'Arm'].length;l2=rig.data.bones[prefix+'ForeArm'].length
    delta=target-shoulder;dist=clamp(delta.length,abs(l1-l2)+1e-5,l1+l2-1e-5);axis=delta.normalized()
    sidevec=pole-shoulder;sidevec-=axis*sidevec.dot(axis);sidevec.normalize()
    along=(l1*l1-l2*l2+dist*dist)/(2*dist);height=math.sqrt(max(0,l1*l1-along*along));elbow=shoulder+axis*along+sidevec*height
    set_world_delta(arm,elbow-shoulder);set_world_delta(fore,shoulder+axis*dist-fore.head)
    q=REST[prefix+'Hand'].to_quaternion()
    for ax,angle in zip([(1,0,0),(0,1,0),(0,0,1)],rotation):q=q@Quaternion(ax,math.radians(angle))
    m=q.to_matrix().to_4x4();m.translation=hand.head;hand.matrix=m;bpy.context.view_layer.update()

# All values are offsets from the original modeled relaxed pose. No item-specific grasp is claimed.
POSES={
 'relaxed':{'Thumb':[0,0,0],'Index':[0,0,0],'Middle':[0,0,0],'Ring':[0,0,0],'Pinky':[0,0,0]},
 'open':{'Thumb':[-8,-8,-4],'Index':[-12,-19,-10],'Middle':[-12,-22,-14],'Ring':[-12,-23,-16],'Pinky':[-12,-23,-14]},
 'fist':{'Thumb':[12,15,20],'Index':[55,65,40],'Middle':[57,65,42],'Ring':[60,65,40],'Pinky':[63,65,40]},
 'grip':{'Thumb':[6,12,14],'Index':[30,38,24],'Middle':[36,42,27],'Ring':[40,45,28],'Pinky':[44,48,28]},
 'point':{'Thumb':[6,10,12],'Index':[-12,-19,-10],'Middle':[50,60,38],'Ring':[55,60,38],'Pinky':[58,60,38]},
}
def fingers(side,pose,weight=1):
    prefix=chains[side]['prefix']
    for finger,angles in POSES[pose].items():
        for j,a in enumerate(angles,1):rig.pose.bones[prefix+'Hand'+finger+str(j)].rotation_quaternion=Quaternion((1,0,0),math.radians(a*weight))

# Palm socket transforms: origin at center of palm; local +Y follows middle finger,
# local +Z points into the grip (curl direction), +X completes the right-handed frame.
for side,prefix,sign in [('L','Left',1),('R','Right',-1)]:
    e=bpy.data.objects.new('SOCKET_hand_'+side,None);bpy.context.collection.objects.link(e);e.empty_display_type='ARROWS';e.empty_display_size=.035
    b=rig.pose.bones[prefix+'Hand'];e.parent=rig;e.parent_type='BONE';e.parent_bone=b.name
    # Blender bone-parent coordinates have their origin at the bone tail.
    e.location=(0,-rig.data.bones[b.name].length*.48,.010);e.rotation_euler=(0,0,0)
    e['purpose']='palm_attachment';e['axes']='+Y fingers, +Z inward grip normal'

scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1;scene.render.fps=30;scene.frame_start=0
camdata=bpy.data.cameras.new('FP_Camera');cam=bpy.data.objects.new('FP_Camera',camdata);scene.collection.objects.link(cam);cam.location=(0,0,0);cam.rotation_euler=(math.pi/2,0,0);camdata.sensor_fit='VERTICAL';camdata.sensor_height=24;camdata.lens=12/math.tan(math.radians(35));camdata.clip_start=.03;camdata.clip_end=100
scene.camera=cam;scene.render.resolution_x=1080;scene.render.resolution_y=1920;scene.render.resolution_percentage=100
clips=[('fp_idle',60,True),('fp_open',45,False),('fp_fist',45,False),('fp_point',45,False),('fp_grip',45,False),('fp_reach',60,False),('fp_sprint',30,True)]
report=[]
for name,end,loop in clips:
    action=bpy.data.actions.new(name);action.use_fake_user=True;rig.animation_data_create();rig.animation_data.action=action
    for frame in range(end+1):
        reset_pose();t=frame/end;phase=math.sin(t*math.pi*2);blend=smooth(t*3)
        for side,sgn in [('L',-1),('R',1)]:
            target=Vector((sgn*.155,.475,-.215));rot=(0,0,0)
            pose='relaxed'
            if name=='fp_idle':target.z+=phase*.003;target.y+=math.cos(t*2*math.pi)*.002
            elif name in ['fp_open','fp_fist','fp_point','fp_grip']:pose=name[3:]
            elif name=='fp_reach':
                reach=math.sin(t*math.pi)**2;target+=Vector((-sgn*.04,.045,.135))*reach;pose='open'
            elif name=='fp_sprint':
                wave=phase*sgn;target+=Vector((sgn*.015,-.035+.025*wave,-.025+.075*wave));rot=(0,0,6*wave);pose='grip'
            ik(side,target,rotation=rot);fingers(side,pose,blend if name in ['fp_open','fp_fist','fp_point','fp_grip'] else 1)
        bpy.context.view_layer.update()
        for b in rig.pose.bones:
            b.keyframe_insert('location',frame=frame,group=b.name);b.keyframe_insert('rotation_quaternion',frame=frame,group=b.name);b.keyframe_insert('scale',frame=frame,group=b.name)
    # Frame 0/end are equal for loop clips by construction, numerical roundoff is harmless.
    report.append({'name':name,'frames':[0,end],'fps':30,'seconds':end/30,'loop':loop,'purpose':'rig control demonstration; not choreography for original film brief'})
rig.animation_data.action=bpy.data.actions['fp_idle'];scene.frame_end=60;scene.frame_set(0)

rig['source_author']='DJMaesen';rig['source_license']='CC-BY-4.0';rig['forward_blender']='+Y';rig['forward_gltf']='-Z';rig['units']='meters';rig['camera_vertical_fov']=70
rig['usage']='Read START_HERE_CLAUDE.md. Engine runtime supplies deterministic two-bone IK, fingers and sockets.'

# Export only rig, skin and sockets. No lights, camera or helper meshes in runtime file.
rig.animation_data.action=None;reset_pose()
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);mesh.select_set(True)
for o in scene.objects:
    if o.name.startswith('SOCKET_'):o.select_set(True)
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=str(OUT/'glb/fp_arms.glb'),export_format='GLB',use_selection=True,export_yup=True,export_apply=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_def_bones=True,export_all_influences=False,export_frame_range=False,export_draco_mesh_compression_enable=False,export_extras=True)

# Neutral studio lights for inspectable portrait previews, excluded from GLB.
scene.render.engine='BLENDER_EEVEE_NEXT';scene.view_settings.view_transform='AgX';scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.16,.19,.22,1)
for name,loc,power,size in [('key',(-.8,.1,.7),30,1),('fill',(.8,.4,.1),18,.8),('rim',(0,1,.5),25,.8)]:
    data=bpy.data.lights.new('preview_'+name,'AREA');data.energy=power;data.size=size;o=bpy.data.objects.new(data.name,data);scene.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,.4,-.25))-o.location).to_track_quat('-Z','Y').to_euler()
for name,end,loop in clips:
    rig.animation_data.action=bpy.data.actions[name];scene.frame_set(end//2 if name in ['fp_reach','fp_sprint'] else end)
    scene.render.filepath=str(OUT/'previews'/f'{name}.png');bpy.ops.render.render(write_still=True)
rig.animation_data.action=bpy.data.actions['fp_idle'];scene.frame_set(0)
for im in bpy.data.images:
    if im.source!='VIEWER':im.pack()
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'blend/fp_arms.blend'))
meta={'asset':'fp_arms','authoring_blender':bpy.app.version_string,'source':'Fps arms by DJMaesen','license':'CC-BY-4.0','vertex_count':len(mesh.data.vertices),'triangles':sum(len(p.vertices)-2 for p in mesh.data.polygons),'bones':specs,'bone_count':len(rig.data.bones),'chains':chains,'poses_degrees':POSES,'clips':report,'weights_max':max(len([g for g in v.groups if g.weight>0]) for v in mesh.data.vertices),'unused_deform_bones':[n for n,c in counts.items() if c==0],'scale_note':'Source assumed cm; converted to m with 0.01. Source proportions retained.','offset_blender':list(OFFSET),'camera':{'position':[0,0,0],'forward_gltf':[0,0,-1],'up_gltf':[0,1,0],'vertical_fov_degrees':70,'near_m':.03,'width':1080,'height':1920}}
(OUT/'rig.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf8')
print('RIG_COMPLETE',len(rig.data.bones),'bones',meta['triangles'],'triangles',flush=True)
