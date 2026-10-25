"""Ready-made CC0 models from "aipollon claude/assets3d" (styles 2-6; style 1 "Классика" never imports this).

    import assets as A
    A.place('city/kenney/city-kit-commercial/Models/GLB format/building-a.glb', (x, y, 0), rot=0, scale=10)
    A.place(path, loc, rot, height=1.75)      # or length=4.5 (longest horizontal side)
    p = A.character(path, loc, height=1.75, anim='walk')   # real copy with skeleton animation
    A.walk_path(p, [(x0, y0), (x1, y1)], t0=0, speed=1.3)

Static models are imported once into a hidden library collection and placed as collection instances
(cheap, any number of copies). Pivot = bottom centre of the model. Characters are imported per copy.
Forward of glTF/Kenney models = Blender -Y (same as lib.person), so heading h -> rot_z = h + pi/2.
"""
import os, math
import bpy
from mathutils import Vector
import lib

ROOT = os.path.abspath(os.path.join(lib.PROJ, '..', 'assets3d'))
_LIB = {}
_JUNK = {'LIGHT', 'CAMERA'}


def path(rel):
    return rel if os.path.isabs(rel) else os.path.join(ROOT, *rel.replace('\\', '/').split('/'))


def _import(p):
    before = set(bpy.data.objects)
    ext = os.path.splitext(p)[1].lower()
    if ext in ('.glb', '.gltf'):
        bpy.ops.import_scene.gltf(filepath=p)
    elif ext == '.fbx':
        bpy.ops.import_scene.fbx(filepath=p)
    elif ext == '.obj':
        bpy.ops.wm.obj_import(filepath=p)
    elif ext == '.blend':  # Quaternius ships native .blend: correct materials, textures and actions
        with bpy.data.libraries.load(p, link=False) as (src, dst):
            dst.objects = list(src.objects)
            dst.actions = list(src.actions)   # all clips (Walk, Idle, SitDown...), not only the assigned one
        for o in dst.objects:
            if o is not None and not o.users_collection:
                bpy.context.scene.collection.objects.link(o)
    else:
        raise ValueError('unsupported model ' + p)
    new = [o for o in bpy.data.objects if o not in before]
    shapes = set()  # glTF importer adds an Icosphere as bone display shape: not part of the model
    for o in new:
        if o.type == 'ARMATURE' and o.pose:
            for pb in o.pose.bones:
                if pb.custom_shape:
                    shapes.add(pb.custom_shape)
                    pb.custom_shape = None
    junk = [o for o in new if o.type in _JUNK or o in shapes]
    keep = [o for o in new if o not in junk]
    for o in junk:
        bpy.data.objects.remove(o, do_unlink=True)
    seen = set()
    for o in keep:
        for s in getattr(o, 'material_slots', []):
            if s.material and s.material not in seen:
                seen.add(s.material)
                _fix_material(s.material)
    return keep


_ROLE = [(('window', 'glass'), '#6F8FA8'), (('light', 'lamp'), '#FFE3A6'),
         (('bumper', 'bottom', 'wheel', 'tire', 'tyre', 'detail', 'black', 'dark'), '#3B3B40')]


def _retint(objs, tint):
    """Old Quaternius vehicle packs (Blender 2.76 Internal) lost their colours: every material is plain grey/white.
    Give such materials a colour by name (windows, lights, bumpers) and the rest the body tint."""
    for o in objs:
        for s in getattr(o, 'material_slots', []):
            m = s.material
            if not m or not m.use_nodes:
                continue
            p = next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
            if p is None or p.inputs['Base Color'].is_linked:
                continue
            c = p.inputs['Base Color'].default_value
            if not (abs(c[0] - c[1]) < 0.01 and abs(c[1] - c[2]) < 0.01 and c[0] > 0.55):
                continue
            col = next((h for keys, h in _ROLE if any(k in m.name.lower() for k in keys)), tint)
            if col:
                p.inputs['Base Color'].default_value = lib.C(col)


def _fix_material(m):
    """Make any imported material render in Eevee Next: old .blend (2.7x-2.8x) without nodes or without a
    Principled BSDF gets one (colour from diffuse_color or the first image texture); alpha forced to 1
    (FBX TransparencyFactor=1 makes models invisible)."""
    if not m.use_nodes:
        col = tuple(m.diffuse_color)
        m.use_nodes = True
        nt = m.node_tree
        p = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
        if p:
            p.inputs['Base Color'].default_value = (col[0], col[1], col[2], 1.0)
    nt = m.node_tree
    p = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if p is None:
        out = next((n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL'), None) or nt.nodes.new('ShaderNodeOutputMaterial')
        p = nt.nodes.new('ShaderNodeBsdfPrincipled')
        tex = next((n for n in nt.nodes if n.type == 'TEX_IMAGE' and n.image), None)
        if tex:
            nt.links.new(tex.outputs['Color'], p.inputs['Base Color'])
        else:
            c = m.diffuse_color
            p.inputs['Base Color'].default_value = (c[0], c[1], c[2], 1.0)
        nt.links.new(p.outputs['BSDF'], out.inputs['Surface'])
    if not p.inputs['Alpha'].is_linked:
        p.inputs['Alpha'].default_value = 1.0
    if not p.inputs['Roughness'].is_linked and p.inputs['Roughness'].default_value < 0.45:
        p.inputs['Roughness'].default_value = 0.7   # matte, like the approved look
    if not p.inputs['Metallic'].is_linked:
        p.inputs['Metallic'].default_value = min(p.inputs['Metallic'].default_value, 0.2)


def _bbox(objs):
    bpy.context.view_layer.update()
    mn, mx = Vector((1e9,) * 3), Vector((-1e9,) * 3)
    for o in objs:
        if o.type != 'MESH':
            continue
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c)
            mn = Vector(map(min, mn, w)); mx = Vector(map(max, mx, w))
    if mn.x > mx.x:
        mn, mx = Vector((0, 0, 0)), Vector((0, 0, 0))
    return mn, mx


def proto(rel, tint=None):
    """Import once -> (collection, size Vector). Collection is not linked to the scene (hidden source).
    tint: colour for 'lost' plain-white materials of old packs (body paint of a bus etc.)."""
    p = path(rel)
    if p in _LIB:
        return _LIB[p]
    objs = _import(p)
    _retint(objs, tint)
    mn, mx = _bbox(objs)
    coll = bpy.data.collections.new('LIB_' + os.path.splitext(os.path.basename(p))[0])
    for o in objs:
        for c in list(o.users_collection):
            c.objects.unlink(o)
        coll.objects.link(o)
    coll.instance_offset = ((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z)
    _LIB[p] = (coll, mx - mn)
    return _LIB[p]


def size(rel):
    return proto(rel)[1]


def _factor(sz, scale, height, length):
    if height:
        return height / max(sz.z, 1e-4)
    if length:
        return length / max(sz.x, sz.y, 1e-4)
    return scale


def place(rel, loc=(0, 0, 0), rot=0.0, scale=1.0, height=None, length=None, coll=None, name=None, tint=None):
    """Instance of a static model. rot = rotation around Z (radians)."""
    c, sz = proto(rel, tint)
    e = bpy.data.objects.new(name or c.name[4:], None)
    e.instance_type = 'COLLECTION'
    e.instance_collection = c
    e.location = loc
    e.rotation_euler = (0, 0, rot)
    s = _factor(sz, scale, height, length)
    e.scale = (s, s, s)
    lib._link(e, coll)
    return e


def _pick_action(actions, want):
    want = want.lower()
    names = [a for a in actions if want in a.name.lower()]
    exact = [a for a in names if a.name.lower().split('|')[-1].split('.')[0] == want]
    pool = exact or names
    return min(pool, key=lambda a: len(a.name)) if pool else None


def _assign_loop(ad, act, n_frames):
    """Loop an action on an armature through an NLA strip (works with slotted actions in 4.4+)."""
    for t in list(ad.nla_tracks):
        ad.nla_tracks.remove(t)
    ad.action = None
    tr = ad.nla_tracks.new()
    st = tr.strips.new(act.name, 1, act)
    try:
        if getattr(act, 'slots', None) and len(act.slots):
            st.action_slot = act.slots[0]
    except Exception:
        pass
    ln = max(1.0, st.action_frame_end - st.action_frame_start)
    st.repeat = max(1.0, n_frames / ln + 1)
    return st


def character(rel, loc=(0, 0, 0), rot=0.0, height=1.75, anim='walk', speed_mult=1.0, phase=0.0, coll=None, name='Char',
              hold=False):
    """Real copy of a rigged character with a looping animation. Returns the root empty (pivot at feet).
    anim may be a list of candidates ('sit' for Kenney, 'sitdown' for Quaternius); hold=True plays the action
    once and keeps its last pose from the first frame on (e.g. already seated)."""
    acts_before = set(bpy.data.actions)
    objs = _import(path(rel))
    new_acts = [a for a in bpy.data.actions if a not in acts_before]
    mn, mx = _bbox(objs)
    root = bpy.data.objects.new(name, None)
    lib._link(root, coll)
    for o in objs:
        for c in list(o.users_collection):
            c.objects.unlink(o)
        lib._link(o, coll)
    for o in objs:
        if o.parent is None:
            o.location -= Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z))
            o.parent = root
    s = height / max(mx.z - mn.z, 1e-4)
    root.scale = (s, s, s)
    root.location = loc
    root.rotation_euler = (0, 0, rot)
    arm = next((o for o in objs if o.type == 'ARMATURE'), None)
    if arm and anim:
        if new_acts == [] and arm.animation_data and arm.animation_data.action:
            new_acts = [arm.animation_data.action]
        if not new_acts:  # .blend append brings actions that already existed in the file (same data)
            new_acts = list(bpy.data.actions)
        act = None
        for a in ([anim] if isinstance(anim, str) else anim):
            act = act or _pick_action(new_acts, a)
        act = act or _pick_action(new_acts, 'idle')
        if act:
            ad = arm.animation_data or arm.animation_data_create()
            st = _assign_loop(ad, act, bpy.context.scene.frame_end + 60)
            ln = st.action_frame_end - st.action_frame_start
            if hold:
                st.repeat = 1.0
                st.extrapolation = 'HOLD'
                st.frame_start = 1 - ln - 2
            else:
                st.scale = 1.0 / max(speed_mult, 0.05)
                st.frame_start = 1 - phase * ln
    return root


def walk_path(root, pts, t0=0.0, speed=1.3, z=None):
    """Move a character root along a polyline at constant speed (linear keys). Heading follows the path."""
    F = lib.sec2f
    z = root.location.z if z is None else z
    t = t0
    prev = None
    for i, (x, y) in enumerate(pts):
        if prev is not None:
            seg = math.hypot(x - prev[0], y - prev[1])
            t += seg / speed
        h = math.atan2(pts[min(i + 1, len(pts) - 1)][1] - pts[max(i - 1, 0)][1],
                       pts[min(i + 1, len(pts) - 1)][0] - pts[max(i - 1, 0)][0])
        lib.key_obj(root, F(t), loc=(x, y, z), rot=(0, 0, h + math.pi / 2), interp='LINEAR')
        prev = (x, y)
    return t


def drive_line(root, p0, p1, speed, t0=0.0, t1=None):
    """Straight constant-speed move from p0 towards p1 (x, y) over the shot."""
    F = lib.sec2f
    d = Vector((p1[0] - p0[0], p1[1] - p0[1], 0))
    dur = t1 if t1 is not None else bpy.context.scene.frame_end / lib.FPS
    end = Vector((p0[0], p0[1], 0)) + d.normalized() * speed * (dur - t0)
    lib.key_obj(root, F(t0), loc=(p0[0], p0[1], root.location.z), interp='LINEAR')
    lib.key_obj(root, F(dur), loc=(end.x, end.y, root.location.z), interp='LINEAR')
