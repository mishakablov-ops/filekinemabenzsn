"""Реалистичный ведущий и люди для толпы (MPFB 2 / MakeHuman, ассеты CC0).

Запускать в GUI-Blender 5.2 на ПК, где стоит расширение MPFB (bl_ext.blender_org.mpfb):
    import esk_hero; esk_hero.build_all(r"D:\\aipollon\\eskalator\\assets")
Получается:
    hero.blend   коллекция HeroChar: риг 'Hero' + тело/одежда/волосы/очки (живой, с костями лица)
    crowd.blend  коллекция Crowd: статичные люди P01..Pnn (один меш на человека, поза запечена)
В фоновых рендерах (build_shot.py) MPFB не нужен: всё берётся append из этих .blend.

Правка mike 07.11.2026: «сделай аватара реалистичным, как на видео» — ведущий не чиби, а человек.
Типаж как у ведущего в образце: мужчина ~30 лет, тёмная короткая стрижка, очки, чёрная футболка.
"""
import bpy, math, os
from mathutils import Vector

# ---------------------------------------------------------------- MPFB
def _mpfb():
    from bl_ext.blender_org.mpfb.services.humanservice import HumanService
    from bl_ext.blender_org.mpfb.services.assetservice import AssetService
    return HumanService, AssetService


def _asset(sub, name):
    _, AS = _mpfb()
    return AS.find_asset_absolute_path(name + '/' + name + ('.mhmat' if sub == 'skins' else '.mhclo'), sub)


def tint(ob, rgb, rough=None, spec=0.2):
    """Умножить Base Color всех материалов объекта на цвет (текстура ткани остаётся)."""
    for s in ob.material_slots:
        m = s.material
        if not m or not m.use_nodes:
            continue
        nt = m.node_tree
        for pb in [n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED']:
            inp = pb.inputs['Base Color']
            mix = nt.nodes.new('ShaderNodeMixRGB')
            mix.blend_type = 'MULTIPLY'
            mix.inputs[0].default_value = 1
            mix.inputs['Color2'].default_value = (*rgb, 1)
            if inp.is_linked:
                nt.links.new(inp.links[0].from_socket, mix.inputs['Color1'])
            else:
                mix.inputs['Color1'].default_value = inp.default_value
            nt.links.new(mix.outputs[0], inp)
            if rough is not None:
                pb.inputs['Roughness'].default_value = rough
            pb.inputs['Specular IOR Level'].default_value = spec


def fix_hair(ob, rgb=(0.035, 0.022, 0.014), rough=0.7):
    """Волосы-карточки MPFB: убрать objnorm-нормали (дают белые пряди), затемнить."""
    for s in ob.material_slots:
        m = s.material
        nt = m.node_tree
        for l in list(nt.links):
            if l.to_node.type == 'BSDF_PRINCIPLED' and l.to_socket.name == 'Normal':
                nt.links.remove(l)
        mix = nt.nodes.get('diffuseIntensity')
        if mix:
            mix.blend_type = 'MULTIPLY'
            mix.inputs[0].default_value = 1
            for l in list(nt.links):
                if l.to_node == mix and l.to_socket.name == 'Color1':
                    nt.links.remove(l)
            mix.inputs['Color1'].default_value = (*rgb, 1)
        for n in nt.nodes:
            if n.type == 'BSDF_PRINCIPLED':
                n.inputs['Roughness'].default_value = rough
                n.inputs['Specular IOR Level'].default_value = 0.25


def skin_warm(body, rgb=(0.70, 0.42, 0.28), k=0.42, bright=-0.06, contrast=0.10, rough=0.5):
    for s in body.material_slots:
        g = [n for n in s.material.node_tree.nodes if n.type == 'GROUP']
        if not g:
            continue
        g = g[0]
        ins = g.inputs
        if 'colorMixIn' in ins:
            ins['colorMixIn'].default_value = (*rgb, 1)
            ins['colorMixInStrength'].default_value = k
            ins['Brightness'].default_value = bright
            ins['Contrast'].default_value = contrast
            ins['Roughness'].default_value = rough


def make_human(name, ph, skin, hair, clothes, eyebrows='eyebrow001', eyes='high-poly', subdiv=1,
               hair_rgb=(0.035, 0.022, 0.014), cloth_tints=None, skin_rgb=None):
    HS, AS = _mpfb()
    hi = HS._create_default_human_info_dict()
    hi['phenotype'].update(ph)
    hi['skin_mhmat'] = skin + '/' + skin + '.mhmat'
    hi['skin_material_type'] = 'ENHANCED_SSS'
    hi['eyes'] = eyes + '/' + eyes + '.mhclo'
    hi['eyebrows'] = eyebrows + '/' + eyebrows + '.mhclo'
    hi['eyelashes'] = 'eyelashes01/eyelashes01.mhclo'
    hi['hair'] = None
    hi['clothes'] = []
    hi['rig'] = 'default'
    hi['name'] = name
    ds = HS.get_default_deserialization_settings()
    ds['material_instances'] = 'NEVER'
    body = HS.deserialize_from_dict(hi, ds)
    rig = body.parent
    out = dict(body=body, rig=rig, parts={})
    if hair:
        ob = HS.add_mhclo_asset(_asset('hair', hair), body, asset_type='Hair', subdiv_levels=0, material_type='MAKESKIN')
        fix_hair(ob, hair_rgb)
        out['parts']['hair'] = ob
    for i, c in enumerate(clothes):
        ob = HS.add_mhclo_asset(_asset('clothes', c), body, asset_type='Clothes', subdiv_levels=subdiv, material_type='MAKESKIN')
        t = (cloth_tints or {}).get(c)
        if t:
            tint(ob, t, rough=0.85)
        out['parts'][c] = ob
    if skin_rgb is not None:
        skin_warm(body, skin_rgb)
    else:
        skin_warm(body)
    # брови в тон волосам
    for o in rig.children:
        if 'eyebrow' in o.name:
            tint(o, (0.15, 0.09, 0.05))
    return out


# ---------------------------------------------------------------- поза
def aim(rig, bname, world_dir):
    """Повернуть кость так, чтобы её ось Y смотрела в world_dir (мировые координаты)."""
    pb = rig.pose.bones[bname]
    pb.rotation_mode = 'QUATERNION'
    pb.rotation_quaternion = (1, 0, 0, 0)
    bpy.context.view_layer.update()
    M = (rig.matrix_world @ pb.matrix).to_3x3().normalized()
    cur = M.col[1]
    q = cur.rotation_difference(Vector(world_dir).normalized())
    pb.rotation_quaternion = (M.inverted() @ q.to_matrix() @ M).to_quaternion()
    bpy.context.view_layer.update()


def nudge(rig, bname, dw, k=1.0):
    pb = rig.pose.bones[bname]
    M = (rig.matrix_world @ pb.bone.matrix_local).to_3x3().normalized()
    pb.location = M.inverted() @ Vector(dw) * k


POSES = {
    # MakeHuman смотрит в -Y, левая рука (.L) на +X
    'stand': {'upperarm01.L': (0.18, 0.06, -1.0), 'lowerarm01.L': (0.08, -0.25, -1.0),
              'upperarm01.R': (-0.18, 0.06, -1.0), 'lowerarm01.R': (-0.08, -0.25, -1.0)},
    'rail':  {'upperarm01.L': (0.18, 0.06, -1.0), 'lowerarm01.L': (0.08, -0.25, -1.0),
              'upperarm01.R': (-0.42, -0.10, -1.0), 'lowerarm01.R': (-0.30, -0.95, -0.25)},
    'phone': {'upperarm01.L': (0.10, 0.10, -1.0), 'lowerarm01.L': (-0.30, -0.95, 0.45),
              'upperarm01.R': (-0.10, 0.10, -1.0), 'lowerarm01.R': (0.30, -0.95, 0.45)},
    'pocket': {'upperarm01.L': (0.22, 0.12, -1.0), 'lowerarm01.L': (-0.05, -0.30, -1.0),
               'upperarm01.R': (-0.22, 0.12, -1.0), 'lowerarm01.R': (0.05, -0.30, -1.0)},
}


def pose(rig, name):
    for b, d in POSES[name].items():
        if b in rig.pose.bones:
            aim(rig, b, d)


def smile(rig, k=1.0):
    for side, sx in (('L', 1), ('R', -1)):
        nudge(rig, 'risorius03.' + side, (sx * 0.003, 0.002, 0.0035), k)
        nudge(rig, 'levator05.' + side, (0, 0, 0.0015), k)


# ---------------------------------------------------------------- очки
def glasses(rig, name='Glasses', eye_x=0.0305, plane_y=-0.181, a=0.0235, bh=0.0165, th=0.0018):
    """Очки кривыми с толщиной, привязаны к кости head. Размеры под тело MPFB ростом ~1.67 м."""
    eye_z = (rig.matrix_world @ rig.pose.bones['eye.L'].head).z
    mf = bpy.data.materials.get('GlassesFrame') or bpy.data.materials.new('GlassesFrame')
    mf.use_nodes = True
    b = mf.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.012, 0.010, 0.009, 1)
    b.inputs['Roughness'].default_value = 0.28
    ml = bpy.data.materials.get('GlassesLens') or bpy.data.materials.new('GlassesLens')
    ml.use_nodes = True
    b = ml.node_tree.nodes['Principled BSDF']
    b.inputs['Roughness'].default_value = 0.02
    b.inputs['Transmission Weight'].default_value = 1.0
    b.inputs['IOR'].default_value = 1.08
    cu = bpy.data.curves.new(name + '_frame', 'CURVE')
    cu.dimensions = '3D'
    cu.bevel_depth = th
    cu.bevel_resolution = 2
    cu.use_fill_caps = True
    n = 4.0
    zc = eye_z + 0.003
    lens = {}

    def poly(pts, cyc=False):
        sp = cu.splines.new('POLY')
        sp.points.add(len(pts) - 1)
        for p, co in zip(sp.points, pts):
            p.co = (*co, 1)
        sp.use_cyclic_u = cyc

    for sx in (1, -1):
        cx = sx * eye_x
        pts = []
        for i in range(48):
            t = 2 * math.pi * i / 48
            c, s = math.cos(t), math.sin(t)
            x = a * math.copysign(abs(c) ** (2 / n), c)
            z = bh * math.copysign(abs(s) ** (2 / n), s)
            if z < 0:
                x *= 1 - 0.10 * (-z / bh)
            o = max(0.0, sx * x) / a
            pts.append((cx + x, plane_y + 0.007 * o * o, zc + z))
        poly(pts, True)
        lens[sx] = pts
        hx = sx * (eye_x + a + 0.002)
        poly([(hx, plane_y + 0.008, zc + 0.009), (sx * 0.064, -0.165, zc + 0.009), (sx * 0.069, -0.13, zc + 0.008),
              (sx * 0.072, -0.09, zc + 0.006), (sx * 0.075, -0.06, zc + 0.002), (sx * 0.074, -0.045, zc - 0.010),
              (sx * 0.071, -0.037, zc - 0.026)])
    poly([(-eye_x + a * 0.9, plane_y - 0.0005, zc + 0.006), (-0.005, plane_y - 0.003, zc + 0.009),
          (0.005, plane_y - 0.003, zc + 0.009), (eye_x - a * 0.9, plane_y - 0.0005, zc + 0.006)])
    fr = bpy.data.objects.new(name, cu)
    fr.data.materials.append(mf)
    me = bpy.data.meshes.new(name + '_lens')
    verts, faces = [], []
    for sx, pts in lens.items():
        base = len(verts)
        verts += [(p[0], p[1] + 0.0004, p[2]) for p in pts]
        verts.append((sx * eye_x, plane_y + 0.0012, zc))
        c = len(verts) - 1
        for i in range(len(pts)):
            faces.append((base + i, base + (i + 1) % len(pts), c))
    me.from_pydata(verts, [], faces)
    me.materials.append(ml)
    ln = bpy.data.objects.new(name + '_lens', me)
    col = rig.users_collection[0]
    for o in (fr, ln):
        col.objects.link(o)
        mw = o.matrix_world.copy()
        o.parent = rig
        o.parent_type = 'BONE'
        o.parent_bone = 'head'
        bpy.context.view_layer.update()
        o.matrix_world = mw
    ln.visible_shadow = False
    return fr, ln


# ---------------------------------------------------------------- ведущий
HERO = dict(
    ph=dict(gender=1.0, age=0.5, muscle=0.6, weight=0.45, proportions=0.7, height=0.55,
            race=dict(asian=0.05, caucasian=0.9, african=0.05)),
    skin='young_caucasian_male2', hair='short01',
    clothes=['toigo_basic_tucked_t-shirt', 'toigo_wool_pants', 'shoes06'],
    tints={'toigo_basic_tucked_t-shirt': (0.03, 0.03, 0.033), 'toigo_wool_pants': (0.08, 0.10, 0.16)},
)


def build_hero(name='Hero'):
    h = make_human(name, HERO['ph'], HERO['skin'], HERO['hair'], HERO['clothes'], cloth_tints=HERO['tints'])
    rig = h['rig']
    pose(rig, 'stand')
    glasses(rig)
    return rig


# ---------------------------------------------------------------- толпа
F = 0.0
M = 1.0
CROWD = [
    # name, gender, age, weight, height, skin, hair, clothes, tints, pose, hair_rgb
    ('P01', F, 0.45, 0.50, 0.45, 'young_caucasian_female', 'bob02', ['female_casualsuit01', 'shoes02'], {}, 'phone', (0.10, 0.06, 0.03)),
    ('P02', M, 0.60, 0.60, 0.60, 'middleage_caucasian_male', 'short02', ['male_casualsuit02', 'shoes01'], {}, 'rail', (0.04, 0.03, 0.02)),
    ('P03', F, 0.35, 0.45, 0.40, 'young_caucasian_female2', 'ponytail01', ['female_sportsuit01', 'shoes03'], {}, 'stand', (0.30, 0.18, 0.08)),
    ('P04', M, 0.40, 0.45, 0.55, 'young_caucasian_male', 'short04', ['male_casualsuit04', 'shoes06'], {}, 'phone', (0.05, 0.035, 0.02)),
    ('P05', M, 0.80, 0.65, 0.45, 'old_caucasian_male', 'short03', ['male_worksuit01', 'shoes05'], {}, 'rail', (0.30, 0.30, 0.30)),
    ('P06', F, 0.70, 0.60, 0.35, 'middleage_caucasian_female', 'bob01', ['female_elegantsuit01', 'shoes04'], {}, 'rail', (0.20, 0.10, 0.05)),
    ('P07', M, 0.45, 0.50, 0.65, 'young_asian_male', 'short02', ['male_casualsuit06', 'shoes02'], {}, 'pocket', (0.02, 0.02, 0.02)),
    ('P08', F, 0.40, 0.48, 0.50, 'young_caucasian_female', 'long01', ['female_casualsuit02', 'shoes03'], {}, 'phone', (0.05, 0.03, 0.02)),
    ('P09', M, 0.55, 0.55, 0.50, 'middleage_caucasian_male', 'short01', ['male_casualsuit03', 'shoes01'], {}, 'stand', (0.06, 0.04, 0.03)),
    ('P10', M, 0.30, 0.42, 0.55, 'young_caucasian_male2', 'cortu_short_messy_hair', ['male_casualsuit05', 'shoes06'], {}, 'rail', (0.12, 0.08, 0.04)),
]


def _bake_static(rig, name, phone=False):
    """Запечь позу: все меши человека -> один статичный меш (дешёвые копии для толпы)."""
    dg = bpy.context.evaluated_depsgraph_get()
    parts = []
    for o in [c for c in bpy.data.objects if c.parent == rig and c.type in ('MESH', 'CURVE')]:
        eo = o.evaluated_get(dg)
        me = bpy.data.meshes.new_from_object(eo, preserve_all_data_layers=False, depsgraph=dg)
        me.transform(o.matrix_world)
        ob = bpy.data.objects.new(name + '_part', me)
        bpy.context.scene.collection.objects.link(ob)
        parts.append(ob)
    if phone:
        hl = rig.matrix_world @ rig.pose.bones['wrist.L'].tail if 'wrist.L' in rig.pose.bones else None
        hr = rig.matrix_world @ rig.pose.bones['wrist.R'].tail if 'wrist.R' in rig.pose.bones else None
        if hl and hr:
            c = (hl + hr) / 2 + Vector((0, -0.02, 0.03))
            me = bpy.data.meshes.new(name + '_phone')
            import bmesh
            bm = bmesh.new()
            bmesh.ops.create_cube(bm, size=1.0)
            for v in bm.verts:
                v.co = Vector((v.co.x * 0.072, v.co.y * 0.008, v.co.z * 0.150))
            bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0),
                             matrix=__import__('mathutils').Matrix.Rotation(math.radians(-55), 3, 'X'))
            bm.to_mesh(me)
            bm.free()
            mp = bpy.data.materials.get('PhoneBlack') or bpy.data.materials.new('PhoneBlack')
            mp.use_nodes = True
            mp.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.01, 0.01, 0.012, 1)
            mp.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.25
            me.materials.append(mp)
            ob = bpy.data.objects.new(name + '_part', me)
            ob.location = c
            bpy.context.scene.collection.objects.link(ob)
            parts.append(ob)
    bpy.ops.object.select_all(action='DESELECT')
    for p in parts:
        p.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    res = bpy.context.view_layer.objects.active
    res.name = name
    res.data.name = name
    # убрать исходник
    for o in [c for c in bpy.data.objects if c.parent == rig]:
        bpy.data.objects.remove(o)
    bpy.data.objects.remove(rig)
    return res


def build_crowd(only=None):
    out = []
    for (nm, g, age, w, hgt, skin, hair, clothes, tints, ps, hrgb) in CROWD:
        if only and nm not in only:
            continue
        ph = dict(gender=g, age=age, muscle=0.5, weight=w, proportions=0.6, height=hgt,
                  race=dict(asian=0.9 if 'asian' in skin else 0.05, caucasian=0.05 if 'asian' in skin else 0.9, african=0.05))
        h = make_human(nm + 'r', ph, skin, hair, clothes, eyes='low-poly', subdiv=0, hair_rgb=hrgb, cloth_tints=tints)
        pose(h['rig'], ps)
        out.append(_bake_static(h['rig'], nm, phone=(ps == 'phone')))
    return out


def _scene(name):
    sc = bpy.data.scenes.get(name) or bpy.data.scenes.new(name)
    bpy.context.window.scene = sc
    return sc


def build_all(out_dir, crowd=True):
    os.makedirs(out_dir, exist_ok=True)
    _scene('HeroBuild')
    rig = build_hero('Hero')
    col = bpy.data.collections.get('HeroChar') or bpy.data.collections.new('HeroChar')
    for o in [rig] + list(rig.children_recursive):
        for c in list(o.users_collection):
            c.objects.unlink(o)
        col.objects.link(o)
    bpy.data.libraries.write(os.path.join(out_dir, 'hero.blend'), {col}, fake_user=True, compress=True)
    if crowd:
        _scene('CrowdBuild')
        people = build_crowd()
        cc = bpy.data.collections.get('Crowd') or bpy.data.collections.new('Crowd')
        for p in people:
            for c in list(p.users_collection):
                c.objects.unlink(p)
            cc.objects.link(p)
        bpy.data.libraries.write(os.path.join(out_dir, 'crowd.blend'), {cc}, fake_user=True, compress=True)
    return True


# ---------------------------------------------------------------- для сцен (фоновый рендер)
def load_hero(path, sc, loc=(0, 0, 0), rot_z=0.0):
    with bpy.data.libraries.load(path, link=False) as (src, dst):
        dst.collections = ['HeroChar']
    col = dst.collections[0]
    sc.collection.children.link(col)
    rig = [o for o in col.objects if o.type == 'ARMATURE'][0]
    rig.location = loc
    rig.rotation_euler = (0, 0, rot_z)
    return rig, col


def load_crowd(path):
    """Вернуть словарь name -> mesh (без привязки к сцене); ставить копиями: place_person."""
    with bpy.data.libraries.load(path, link=False) as (src, dst):
        dst.collections = ['Crowd']
    col = dst.collections[0]
    return {o.name: o for o in col.objects}


def place_person(sc, src, loc, rot_z=0.0, col=None, scale=1.0):
    ob = bpy.data.objects.new(src.name + '_i', src.data)
    ob.location = loc
    ob.rotation_euler = (0, 0, rot_z)
    ob.scale = (scale,) * 3
    (col or sc.collection).objects.link(ob)
    return ob
