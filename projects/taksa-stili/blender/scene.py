"""Такса на полянке: сцена из кода для пробы «одна такса — много стилей».
Запуск: python scene.py <style> <out.png|out_dir/> [frame_start frame_end] [res_x]
"""
import bpy, math, sys, random
from mathutils import Vector, Euler

ARGS = sys.argv[1:]
STYLE = ARGS[0] if ARGS else 'soft3d'
OUT = ARGS[1] if len(ARGS) > 1 else '/tmp/dog.png'
F0 = int(ARGS[2]) if len(ARGS) > 2 else 24
F1 = int(ARGS[3]) if len(ARGS) > 3 else F0
RESX = int(ARGS[4]) if len(ARGS) > 4 else 720

bpy.ops.wm.read_factory_settings(use_empty=True)
S = bpy.context.scene
S.render.fps = 30
S.frame_start, S.frame_end = 1, 660
random.seed(7)

# ---------------- палитры по стилям ----------------
BASE = dict(
    body=(0.17, 0.038, 0.010), belly=(0.30, 0.09, 0.03), ear=(0.075, 0.016, 0.005),
    nose=(0.02, 0.02, 0.02), eyew=(0.97, 0.97, 0.95), pupil=(0.01, 0.01, 0.01),
    collar=(0.05, 0.12, 0.45), tag=(0.85, 0.80, 0.08), tagtxt=(0.05, 0.25, 0.05), mouth=(0.10, 0.03, 0.02),
    grass=(0.16, 0.50, 0.08), hill1=(0.22, 0.58, 0.12), hill2=(0.35, 0.65, 0.20), bush=(0.55, 0.20, 0.42),
    bush2=(0.10, 0.35, 0.10), petal=(0.95, 0.80, 0.05), petal2=(0.95, 0.35, 0.45), stem=(0.15, 0.45, 0.08),
    wood=(0.55, 0.35, 0.18), wall=(0.95, 0.88, 0.75), roof=(0.70, 0.18, 0.10), trunk=(0.30, 0.18, 0.08),
    leaf=(0.12, 0.42, 0.10), cloud=(1.0, 1.0, 1.0), sky=(0.95, 0.45, 0.75), sky2=(1.0, 0.75, 0.85),
    butterfly=(0.95, 0.55, 0.05), sun=(1.0, 0.85, 0.4), fcore=(0.45, 0.15, 0.03),
)

# ---------------- материалы ----------------
MATS = {}

def mat(key):
    if key in MATS:
        return MATS[key]
    m = bpy.data.materials.new(key)
    m.use_nodes = True
    MATS[key] = m
    return m


def setup_materials(style, pal):
    for key, m in MATS.items():
        nt = m.node_tree
        nt.nodes.clear()
        out = nt.nodes.new('ShaderNodeOutputMaterial')
        col = pal.get(key, (1, 0, 1))
        if style in ('flat', 'lineart', 'silhouette', 'paper', 'blueprint', 'neon'):
            em = nt.nodes.new('ShaderNodeEmission')
            em.inputs['Color'].default_value = (*col, 1)
            nt.links.new(em.outputs[0], out.inputs[0])
        elif style in ('comic', 'toon'):
            # тун: диффуз -> ступенчатая рампа -> умножить на цвет, без бликов
            d = nt.nodes.new('ShaderNodeBsdfDiffuse')
            s2r = nt.nodes.new('ShaderNodeShaderToRGB')
            ramp = nt.nodes.new('ShaderNodeValToRGB')
            ramp.color_ramp.interpolation = 'CONSTANT'
            ramp.color_ramp.elements[0].position = 0.0
            ramp.color_ramp.elements[0].color = (0.55, 0.55, 0.62, 1)
            ramp.color_ramp.elements[1].position = 0.12
            ramp.color_ramp.elements[1].color = (1, 1, 1, 1)
            mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'; mix.blend_type = 'MULTIPLY'
            mix.inputs['Factor'].default_value = 1.0
            mix.inputs[6].default_value = (*col, 1)
            em = nt.nodes.new('ShaderNodeEmission')
            nt.links.new(d.outputs[0], s2r.inputs[0])
            nt.links.new(s2r.outputs[0], ramp.inputs[0])
            nt.links.new(ramp.outputs[0], mix.inputs[7])
            nt.links.new(mix.outputs[2], em.inputs[0])
            nt.links.new(em.outputs[0], out.inputs[0])
        elif style == 'clay':
            b = nt.nodes.new('ShaderNodeBsdfPrincipled')
            b.inputs['Base Color'].default_value = (*col, 1)
            b.inputs['Roughness'].default_value = 0.8
            b.inputs['Subsurface Weight'].default_value = 0.15
            b.inputs['Subsurface Radius'].default_value = (0.05, 0.03, 0.02)
            # отпечатки пальцев и вмятины пластилина
            tc = nt.nodes.new('ShaderNodeTexCoord')
            vor = nt.nodes.new('ShaderNodeTexVoronoi'); vor.inputs['Scale'].default_value = 5
            vor.feature = 'SMOOTH_F1'
            noi = nt.nodes.new('ShaderNodeTexNoise'); noi.inputs['Scale'].default_value = 140
            noi.inputs['Detail'].default_value = 2
            add = nt.nodes.new('ShaderNodeMath'); add.operation = 'ADD'
            mul = nt.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'; mul.inputs[1].default_value = 0.6
            bump = nt.nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = 0.9
            bump.inputs['Distance'].default_value = 0.02
            nt.links.new(tc.outputs['Object'], vor.inputs['Vector'])
            nt.links.new(tc.outputs['Object'], noi.inputs['Vector'])
            nt.links.new(vor.outputs['Distance'], add.inputs[0])
            nt.links.new(noi.outputs['Fac'], mul.inputs[0])
            nt.links.new(mul.outputs[0], add.inputs[1])
            nt.links.new(add.outputs[0], bump.inputs['Height'])
            nt.links.new(bump.outputs[0], b.inputs['Normal'])
            nt.links.new(b.outputs[0], out.inputs[0])
        elif style == 'gzhel':
            # белый фарфор + кобальтовые мазки
            b = nt.nodes.new('ShaderNodeBsdfPrincipled')
            b.inputs['Roughness'].default_value = 0.12
            b.inputs['Coat Weight'].default_value = 0.6
            tc = nt.nodes.new('ShaderNodeTexCoord')
            wave = nt.nodes.new('ShaderNodeTexWave'); wave.inputs['Scale'].default_value = 1.4
            wave.inputs['Distortion'].default_value = 6; wave.inputs['Detail'].default_value = 3
            wave.wave_profile = 'SIN'; wave.wave_type = 'RINGS'; wave.inputs['Distortion'].default_value = 14
            ramp = nt.nodes.new('ShaderNodeValToRGB')
            e0, e1 = ramp.color_ramp.elements
            e0.position = 0.62; e0.color = (0.95, 0.96, 0.98, 1)
            e1.position = 0.80; e1.color = (0.02, 0.10, 0.55, 1)
            nt.links.new(tc.outputs['Object'], wave.inputs['Vector'])
            nt.links.new(wave.outputs['Fac'], ramp.inputs[0])
            if key in ('nose', 'pupil', 'mouth', 'collar', 'tagtxt', 'ear'):
                b.inputs['Base Color'].default_value = (0.02, 0.08, 0.45, 1)
            elif key in ('grass', 'hill1', 'hill2', 'stem', 'wood', 'trunk', 'wall'):
                b.inputs['Base Color'].default_value = (0.62, 0.70, 0.88, 1) if key != 'hill2' else (0.45, 0.55, 0.85, 1)
            elif key in ('eyew', 'cloud'):
                b.inputs['Base Color'].default_value = (0.96, 0.97, 0.99, 1)
            else:
                nt.links.new(ramp.outputs[0], b.inputs['Base Color'])
            nt.links.new(b.outputs[0], out.inputs[0])
        elif style == 'shade':
            b = nt.nodes.new('ShaderNodeBsdfDiffuse')
            b.inputs['Color'].default_value = (0.8, 0.8, 0.8, 1)
            nt.links.new(b.outputs[0], out.inputs[0])
        else:  # soft3d, lowpoly
            b = nt.nodes.new('ShaderNodeBsdfPrincipled')
            b.inputs['Base Color'].default_value = (*col, 1)
            if style == 'soft3d' and key in ('body', 'belly', 'ear', 'grass', 'hill1', 'hill2', 'bush', 'bush2', 'leaf'):
                # не пластик: лёгкая неравномерность цвета и мелкий рельеф (шерсть / трава)
                tc = nt.nodes.new('ShaderNodeTexCoord')
                nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 6 if key in ('body', 'belly', 'ear') else 3
                nz.inputs['Detail'].default_value = 6
                mx = nt.nodes.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'
                mx.inputs['Factor'].default_value = 0.35
                mx.inputs[6].default_value = (*col, 1)
                nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
                nt.links.new(nz.outputs['Color'], mx.inputs[7])
                ad = nt.nodes.new('ShaderNodeMix'); ad.data_type = 'RGBA'; ad.blend_type = 'MIX'
                ad.inputs['Factor'].default_value = 0.6; ad.inputs[6].default_value = (*col, 1)
                nt.links.new(mx.outputs[2], ad.inputs[7])
                nt.links.new(ad.outputs[2], b.inputs['Base Color'])
                fur = nt.nodes.new('ShaderNodeTexNoise'); fur.inputs['Scale'].default_value = 180 if key in ('body', 'belly', 'ear') else 60
                fur.inputs['Detail'].default_value = 3
                bm = nt.nodes.new('ShaderNodeBump'); bm.inputs['Strength'].default_value = 0.18; bm.inputs['Distance'].default_value = 0.01
                nt.links.new(tc.outputs['Object'], fur.inputs['Vector']); nt.links.new(fur.outputs['Fac'], bm.inputs['Height'])
                nt.links.new(bm.outputs[0], b.inputs['Normal'])
            b.inputs['Roughness'].default_value = 0.08 if key in ('nose', 'eyew', 'pupil') else 0.6
            if style == 'lowpoly':
                gm = nt.nodes.new('ShaderNodeNewGeometry')
                nt.links.new(gm.outputs['True Normal'], b.inputs['Normal'])
                b.inputs['Roughness'].default_value = 0.9
            if style == 'soft3d' and key in ('body', 'belly', 'ear'):
                b.inputs['Sheen Weight'].default_value = 0.5
                b.inputs['Subsurface Weight'].default_value = 0.08
            nt.links.new(b.outputs[0], out.inputs[0])


def assign(ob, key):
    ob.data.materials.clear()
    ob.data.materials.append(mat(key))
    ob['mkey'] = key
    return ob

# ---------------- примитивы ----------------
COLL = S.collection

def uvs(name, loc, scale, key, seg=48, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=seg // 2, location=loc, rotation=rot)
    o = bpy.context.object; o.name = name; o.scale = scale
    bpy.ops.object.shade_smooth()
    return assign(o, key)


def cyl(name, loc, r, depth, key, rot=(0, 0, 0), v=32):
    bpy.ops.mesh.primitive_cylinder_add(vertices=v, radius=r, depth=depth, location=loc, rotation=rot)
    o = bpy.context.object; o.name = name
    return assign(o, key)


def cube(name, loc, scale, key, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=rot)
    o = bpy.context.object; o.name = name; o.scale = scale
    return assign(o, key)


def empty(name, loc, parent=None):
    o = bpy.data.objects.new(name, None); o.location = loc
    COLL.objects.link(o)
    if parent: o.parent = parent
    return o


def parent_keep(ch, par):
    mw = ch.matrix_world.copy(); ch.parent = par; ch.matrix_world = mw

# ---------------- такса (метаболы: одно мягкое тело) ----------------
LOWPOLY = STYLE == 'lowpoly'
USE_FREESTYLE = False

def metaball(name, key, elems, parent=None):
    mb = bpy.data.metaballs.new(name)
    mb.resolution = 0.05; mb.render_resolution = 0.16 if LOWPOLY else 0.025
    mb.threshold = 0.6
    o = bpy.data.objects.new(name, mb); COLL.objects.link(o)
    for typ, co, rad, size, rot in elems:
        e = mb.elements.new(); e.type = typ; e.co = co; e.radius = rad
        if size: e.size_x, e.size_y, e.size_z = size
        if rot: e.rotation = Euler(rot).to_quaternion()
        e.stiffness = 10.0
    mb.materials.append(mat(key)); o['mkey'] = key
    if parent: o.parent = parent
    return o

dog = empty('DogRoot', (0, 0, 0))
R90 = (0, math.radians(90), 0)
body = metaball('Body', 'body', [
    ('ELLIPSOID', (0.0, 0, 0.46), 1.0, (0.92, 0.30, 0.29), None),
    ('BALL', (0.58, 0, 0.48), 0.34, None, None),
    ('BALL', (-0.62, 0, 0.48), 0.31, None, None),
    ('CAPSULE', (0.58, -0.15, 0.20), 0.13, (0.07, 1, 1), R90),
    ('CAPSULE', (0.58, 0.15, 0.20), 0.13, (0.07, 1, 1), R90),
    ('CAPSULE', (-0.62, -0.15, 0.20), 0.13, (0.07, 1, 1), R90),
    ('CAPSULE', (-0.62, 0.15, 0.20), 0.13, (0.07, 1, 1), R90),
    ('ELLIPSOID', (0.66, -0.15, 0.08), 1.0, (0.15, 0.10, 0.07), None),
    ('ELLIPSOID', (0.66, 0.15, 0.08), 1.0, (0.15, 0.10, 0.07), None),
    ('ELLIPSOID', (-0.55, -0.15, 0.08), 1.0, (0.15, 0.10, 0.07), None),
    ('ELLIPSOID', (-0.55, 0.15, 0.08), 1.0, (0.15, 0.10, 0.07), None),
    ('CAPSULE', (0.85, 0, 0.66), 0.24, (0.16, 1, 1), (0, math.radians(-55), 0)),
], parent=dog)

def kid(o, par, loc, rot=None):
    o.parent = par; o.location = loc
    if rot: o.rotation_euler = rot
    return o

headpiv = empty('HeadPivot', (0.92, 0, 0.72), dog)
head = metaball('Body.head', 'body', [
    ('BALL', (0.20, 0, 0.30), 0.40, None, None),
    ('ELLIPSOID', (0.62, 0, 0.18), 1.0, (0.36, 0.165, 0.15), None),
], parent=headpiv)
kid(uvs('Nose', (0, 0, 0), (0.10, 0.105, 0.09), 'nose'), headpiv, (0.99, 0, 0.21))
for side in (-1, 1):
    kid(uvs('EyeW%d' % side, (0, 0, 0), (0.10, 0.07, 0.11), 'eyew'), headpiv, (0.40, side * 0.23, 0.42))
    kid(uvs('Pupil%d' % side, (0, 0, 0), (0.055, 0.03, 0.065), 'pupil'), headpiv, (0.46, side * 0.285, 0.43))
    kid(uvs('Hl%d' % side, (0, 0, 0), (0.018, 0.01, 0.018), 'eyew', seg=16), headpiv, (0.485, side * 0.31, 0.46))
EARS = []
for side in (-1, 1):
    ep = empty('EarPiv%d' % side, (0, 0, 0), headpiv); ep.location = (0.02, side * 0.30, 0.52)
    ear = uvs('Ear%d' % side, (0, 0, 0), (0.15, 0.04, 0.30), 'ear')
    kid(ear, ep, (-0.08, side * 0.03, -0.24), (side * 0.15, 0.35, 0))
    EARS.append(ep)
cu = bpy.data.curves.new('Smile', 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.013
sp = cu.splines.new('BEZIER'); sp.bezier_points.add(2)
for i, (x, z) in enumerate([(0.52, 0.13), (0.66, 0.07), (0.80, 0.11)]):
    p = sp.bezier_points[i]; p.co = (x, -0.135, z); p.handle_left_type = p.handle_right_type = 'AUTO'
smile = bpy.data.objects.new('Smile', cu); COLL.objects.link(smile); smile.parent = headpiv
cu.materials.append(mat('mouth')); smile['mkey'] = 'mouth'
for i, (x, z) in enumerate([(0.80, 0.24), (0.75, 0.20)]):
    kid(uvs('Dot%d' % i, (0, 0, 0), (0.014, 0.01, 0.014), 'eyew', seg=12), headpiv, (x, -0.155, z))
bpy.ops.mesh.primitive_torus_add(major_radius=0.25, minor_radius=0.045)
collar = bpy.context.object; collar.name = 'Collar'; collar.scale = (1, 1.12, 1); bpy.ops.object.shade_smooth()
assign(collar, 'collar'); kid(collar, dog, (0.92, 0, 0.74), (0, math.radians(-35), 0))
tagpiv = empty('TagPiv', (0, 0, 0), dog); tagpiv.location = (1.03, -0.10, 0.55)
tag = cyl('Tag', (0, 0, 0), 0.075, 0.02, 'tag', rot=(math.radians(90), 0, 0)); kid(tag, tagpiv, (0, -0.06, -0.07))
bpy.ops.object.text_add()
tx = bpy.context.object; tx.data.body = 'A'; tx.data.align_x = 'CENTER'; tx.data.size = 0.09
tx.data.extrude = 0.004; tx.data.materials.append(mat('tagtxt')); tx['mkey'] = 'tagtxt'
kid(tx, tagpiv, (0, -0.075, -0.10), (math.radians(90), 0, 0))
# хвост
tailpiv = empty('TailPiv', (0, 0, 0), dog); tailpiv.location = (-0.88, 0, 0.58)
tail = metaball('Body.tail', 'body', [
    ('CAPSULE', (-0.16, 0, 0.10), 0.075, (0.20, 1, 1), (0, math.radians(-35), 0)),
], parent=tailpiv)

# ---------------- окружение ----------------
def ground():
    bpy.ops.mesh.primitive_plane_add(size=80, location=(0, 0, 0))
    g = bpy.context.object; assign(g, 'grass')
    # холмы
    for i, (x, y, r, h, k) in enumerate([(-6, 14, 9, 2.6, 'hill1'), (7, 18, 11, 3.4, 'hill2'),
                                          (0, 26, 14, 5.0, 'hill1'), (-14, 22, 10, 4.0, 'hill2'),
                                          (16, 12, 8, 2.2, 'hill1')]):
        uvs('Hill%d' % i, (x, y, 0), (r, r * 0.7, h), k, seg=64)

def bush(loc, s, key):
    for j in range(5):
        o = uvs('Bush', (loc[0] + random.uniform(-0.5, 0.5) * s, loc[1] + random.uniform(-0.3, 0.3) * s,
                         loc[2] + random.uniform(0.1, 0.45) * s), (0.55 * s,) * 3, key, seg=24)

def flower(x, y, key):
    cyl('Stem', (x, y, 0.09), 0.012, 0.18, 'stem', v=8)
    for k in range(5):
        a = k * 2 * math.pi / 5
        uvs('Petal', (x + 0.045 * math.cos(a), y, 0.19 + 0.045 * math.sin(a)), (0.04, 0.012, 0.04), key, seg=12)
    uvs('FCore', (x, y - 0.01, 0.19), (0.025, 0.015, 0.025), 'fcore', seg=12)

def house(x, y, rz, s=1.0):
    cube('Wall', (x, y, 0.8 * s), (1.0 * s, 0.9 * s, 0.8 * s), 'wall', rot=(0, 0, rz))
    bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=1.6 * s, depth=1.0 * s, location=(x, y, 2.1 * s),
                                    rotation=(0, 0, rz + math.pi / 4))
    assign(bpy.context.object, 'roof')
    cube('Win', (x - 0.0, y - 0.91 * s, 0.9 * s), (0.25 * s, 0.02, 0.25 * s), 'collar', rot=(0, 0, rz))

def tree(x, y, s=1.0):
    cyl('Trunk', (x, y, 0.8 * s), 0.12 * s, 1.6 * s, 'trunk', v=12)
    for j in range(3):
        uvs('Crown', (x + random.uniform(-0.3, 0.3) * s, y, (1.9 + j * 0.35) * s), (0.75 * s,) * 3, 'leaf', seg=24)

def cloud(x, z, s=1.0):
    for j in range(5):
        uvs('Cloud', (x + (j - 2) * 0.6 * s, 30, z + random.uniform(0, 0.4) * s),
            (0.75 * s, 0.4 * s, 0.55 * s), 'cloud', seg=24)

ground()
bush((-2.6, 1.6, 0), 1.0, 'bush'); bush((2.9, 2.2, 0), 1.2, 'bush'); bush((-4.5, 4.5, 0), 1.4, 'bush2')
bush((4.8, 5.0, 0), 1.3, 'bush2')
for i in range(26):
    x = random.uniform(-3.5, 4.0); y = random.uniform(-1.4, 3.5)
    if abs(y) < 0.6 and -1.4 < x < 2.4: continue
    flower(x, y, 'petal' if i % 3 else 'petal2')
# передний план: пучки травы и цветы у камеры
TUFTS = bpy.data.collections.new('Tufts'); S.collection.children.link(TUFTS)
for i in range(220):
    x = random.uniform(-2.2, 3.2); y = random.uniform(-1.5, 2.0)
    if -1.2 < x < 2.0 and -0.45 < y < 0.45: continue
    for k in range(3):
        bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=0.012, depth=random.uniform(0.05, 0.11),
            location=(x + k * 0.02, y, 0.05), rotation=(random.uniform(-0.3, 0.3), random.uniform(-0.3, 0.3), 0))
        o = assign(bpy.context.object, 'stem' if k else 'hill2')
        for c in o.users_collection: c.objects.unlink(o)
        TUFTS.objects.link(o)
for i in range(14):
    x = random.uniform(-1.6, 2.6); y = random.uniform(-1.3, -0.6)
    flower(x, y, 'petal2' if i % 2 else 'petal')
# забор вдали
for i in range(14):
    x = -6 + i * 0.9
    cube('Post', (x, 6.5, 0.45), (0.06, 0.06, 0.45), 'wood')
cube('Rail', (-0.15, 6.5, 0.65), (6.2, 0.04, 0.05), 'wood'); cube('Rail2', (-0.15, 6.5, 0.32), (6.2, 0.04, 0.05), 'wood')
house(-5.5, 13, 0.3, 1.0); house(3.5, 15, -0.2, 1.1); house(9.5, 13, 0.1, 0.9); house(-11, 16, 0.2, 1.2)
tree(-3.2, 9, 1.0); tree(1.2, 10.5, 1.2); tree(6.5, 9.5, 0.9); tree(-8.5, 11, 1.3); tree(12, 14, 1.2)
cloud(-5, 11, 1.4); cloud(6, 14, 1.8); cloud(-1, 17, 1.2)
# бабочка
bfly = empty('Butterfly', (2.1, -0.6, 1.6))
wings = []
for side in (-1, 1):
    w = uvs('Wing', (0, 0, 0), (0.09, 0.012, 0.07), 'butterfly', seg=12); w.parent = bfly
    w.location = (0, side * 0.06, 0); wings.append((w, side))

# ---------------- анимация ----------------
def anim():
    for f in range(1, 721):
        t = f / 30.0
        # голова: нюхает землю, поднимает, смотрит на бабочку
        sniff = 0.5 * (1 - math.cos(min(1, max(0, (t % 6) / 2.0)) * math.pi)) if (t % 6) < 2 else \
                (1 if (t % 6) < 3.2 else 0.5 * (1 + math.cos(min(1, ((t % 6) - 3.2) / 1.2) * math.pi)))
        headpiv.rotation_euler = (0, math.radians(32 * sniff - 4 + 2.5 * math.sin(t * 9) * sniff), 0)
        headpiv.keyframe_insert('rotation_euler', frame=f)
        for ep, side in zip(EARS, (-1, 1)):
            ep.rotation_euler = (side * 0.08 * math.sin(t * 3.1), 0.12 * math.sin(t * 2.3 + side) - 0.3 * sniff, 0)
            ep.keyframe_insert('rotation_euler', frame=f)
        tailpiv.rotation_euler = (0.6 * math.sin(t * 14), 0, 0.5 * math.sin(t * 14))
        tailpiv.keyframe_insert('rotation_euler', frame=f)
        tagpiv.rotation_euler = (0.25 * math.sin(t * 5), 0, 0); tagpiv.keyframe_insert('rotation_euler', frame=f)
        body.scale = (1, 1 + 0.02 * math.sin(t * 4), 1 + 0.02 * math.sin(t * 4)); body.keyframe_insert('scale', frame=f)
        bfly.location = (1.3 + 0.7 * math.sin(t * 0.7), -0.5 + 0.2 * math.sin(t * 1.3), 1.65 + 0.2 * math.sin(t * 2.1))
        bfly.keyframe_insert('location', frame=f)
        for w, side in wings:
            w.rotation_euler = (side * 0.9 * abs(math.sin(t * 18)), 0, 0); w.keyframe_insert('rotation_euler', frame=f)
    for o in bpy.data.objects:
        if o.animation_data and o.animation_data.action:
            for layer in getattr(o.animation_data.action, 'layers', []):
                pass
anim()

# ---------------- камера и свет ----------------
cam_d = bpy.data.cameras.new('Cam'); cam = bpy.data.objects.new('Cam', cam_d); COLL.objects.link(cam)
S.camera = cam
cam_d.sensor_fit = 'HORIZONTAL'; cam_d.lens = 30; cam_d.clip_start = 0.1
cam.location = (0.45, -2.85, 0.62)
cam.rotation_euler = (math.radians(96), 0, 0)
cam.keyframe_insert('location', frame=1)
cam.location = (0.55, -2.45, 0.6); cam.keyframe_insert('location', frame=720)
for fc in getattr(cam.animation_data.action, 'fcurves', []):
    for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'
if STYLE in ('soft3d', 'clay'):
    fo = empty('Focus', (0.7, -0.25, 0.75))
    cam_d.dof.use_dof = True; cam_d.dof.focus_object = fo
    cam_d.dof.aperture_fstop = 1.4 if STYLE == 'soft3d' else 0.9
if STYLE == 'clay':
    # стоп-моушн: каждый снятый кадр собака и свет чуть «дышат» (как руки аниматора)
    rnd = random.Random(11)
    for f in range(1, 721, 2):
        dog.location = (rnd.uniform(-0.004, 0.004), rnd.uniform(-0.004, 0.004), 0)
        dog.rotation_euler = (0, 0, rnd.uniform(-0.006, 0.006))
        dog.keyframe_insert('location', frame=f); dog.keyframe_insert('rotation_euler', frame=f)
    for o in (dog,):
        ad = o.animation_data
        if ad and ad.action:
            for fc in getattr(ad.action, 'fcurves', []):
                for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
import os as _os
if 'tufts' in _os.environ.get('IDS_HIDE', ''):
    TUFTS.hide_render = True

W = bpy.data.worlds.new('W'); S.world = W; W.use_nodes = True
wn = W.node_tree.nodes; wn.clear()
wo = wn.new('ShaderNodeOutputWorld')
bg = wn.new('ShaderNodeBackground')
W.node_tree.links.new(bg.outputs[0], wo.inputs[0])


def light_rig(style, pal):
    # небо: градиент по высоте взгляда камеры
    lp = W.node_tree.links
    tc = wn.new('ShaderNodeTexCoord'); sep = wn.new('ShaderNodeSeparateXYZ'); ramp = wn.new('ShaderNodeValToRGB')
    e0, e1 = ramp.color_ramp.elements
    e0.position = 0.0; e0.color = (*pal['sky2'], 1); e1.position = 0.35; e1.color = (*pal['sky'], 1)
    lp.new(tc.outputs['Window'], sep.inputs[0]); lp.new(sep.outputs['Y'], ramp.inputs[0])
    # для камеры — градиент, для освещения — мягкий светлый
    lpth = wn.new('ShaderNodeLightPath'); mix = wn.new('ShaderNodeMixShader')
    bg2 = wn.new('ShaderNodeBackground'); bg2.inputs['Color'].default_value = (0.9, 0.85, 0.95, 1)
    bg2.inputs['Strength'].default_value = 0.9
    lp.new(ramp.outputs[0], bg.inputs['Color'])
    lp.new(lpth.outputs['Is Camera Ray'], mix.inputs[0])
    lp.new(bg2.outputs[0], mix.inputs[1]); lp.new(bg.outputs[0], mix.inputs[2])
    lp.new(mix.outputs[0], wo.inputs[0])
    sun = bpy.data.lights.new('Sun', 'SUN'); sun.energy = 2.6; sun.angle = math.radians(12)
    sun.color = (1.0, 0.95, 0.88)
    so = bpy.data.objects.new('Sun', sun); COLL.objects.link(so)
    so.rotation_euler = (math.radians(50), math.radians(-25), math.radians(-30))
    area = bpy.data.lights.new('Fill', 'AREA'); area.energy = 250; area.size = 4
    ao = bpy.data.objects.new('Fill', area); COLL.objects.link(ao)
    ao.location = (1, -4, 3); ao.rotation_euler = (math.radians(60), 0, 0)

PAL = dict(BASE)
if STYLE == 'silhouette':
    for k in PAL: PAL[k] = (0.93, 0.86, 0.74)
    for k in ('body', 'ear', 'nose', 'pupil', 'mouth', 'collar'):
        PAL[k] = (0.01, 0.01, 0.01)
    PAL['tag'] = (0.75, 0.05, 0.05); PAL['tagtxt'] = (0.93, 0.86, 0.74)
    PAL['eyew'] = (0.93, 0.86, 0.74)
    for k in ('hill1', 'hill2', 'bush', 'bush2', 'leaf', 'trunk', 'wall', 'roof', 'cloud', 'wood'):
        PAL[k] = (0.86, 0.78, 0.66)
    PAL['sky'] = PAL['sky2'] = (0.93, 0.86, 0.74)
if STYLE == 'lineart':
    for k in PAL: PAL[k] = (0.0, 0.0, 0.0)
if STYLE == 'blueprint':
    for k in PAL: PAL[k] = (0.03, 0.18, 0.45)
if STYLE == 'neon':
    for k in PAL: PAL[k] = (0.003, 0.0, 0.012)
    PAL['sky'] = PAL['sky2'] = (0.004, 0.0, 0.02)
if STYLE == 'flat':
    PAL['sky'] = (0.98, 0.93, 0.85); PAL['sky2'] = (0.98, 0.93, 0.85)
if STYLE == 'paper':
    PAL.update(sky=(0.98, 0.85, 0.30), sky2=(0.98, 0.85, 0.30), body=(0.70, 0.08, 0.08), ear=(0.10, 0.20, 0.65),
               grass=(0.95, 0.94, 0.90), hill1=(0.92, 0.90, 0.86), hill2=(0.85, 0.83, 0.78))
if STYLE == 'clay':
    PAL.update(body=(0.55, 0.16, 0.04), ear=(0.30, 0.07, 0.02), grass=(0.25, 0.60, 0.12), hill1=(0.35, 0.70, 0.20),
               hill2=(0.50, 0.78, 0.30), collar=(0.10, 0.30, 0.85), sky=(0.55, 0.80, 1.0), sky2=(0.85, 0.93, 1.0))
if STYLE == 'gzhel':
    PAL.update(sky=(1.5, 1.65, 2.0), sky2=(2.2, 2.2, 2.4))

setup_materials(STYLE, PAL)
if STYLE in ('soft3d', 'lowpoly', 'clay', 'gzhel', 'comic', 'toon', 'shade'):
    light_rig(STYLE, PAL)
else:
    bg.inputs['Color'].default_value = (*PAL['sky'], 1)

if LOWPOLY:
    for o in bpy.data.objects:
        if o.type == 'MESH':
            for p in o.data.polygons: p.use_smooth = False
            if 'Hill' in o.name or o.name.startswith(('Bush', 'Crown', 'Cloud')):
                m = o.modifiers.new('dec', 'DECIMATE'); m.ratio = 0.06
    for mb in bpy.data.metaballs: mb.render_resolution = 0.2

# ---------------- линии (Freestyle) ----------------
LINES = {'flat': ((0.02, 0.01, 0.0), 2.2), 'lineart': ((1, 1, 1), 2.0), 'comic': ((0.05, 0.03, 0.02), 2.8),
         'blueprint': ((0.85, 0.93, 1.0), 1.4), 'neon': (None, 2.4)}
if STYLE in LINES and USE_FREESTYLE:
    S.render.use_freestyle = True
    S.render.line_thickness_mode = 'RELATIVE'
    vl = S.view_layers[0]; vl.use_freestyle = True
    fs = vl.freestyle_settings
    ls = fs.linesets[0] if len(fs.linesets) else fs.linesets.new('L')
    if ls.linestyle is None: ls.linestyle = bpy.data.linestyles.new('LS')
    ls.select_by_collection = True; ls.collection = TUFTS; ls.collection_negation = 'EXCLUSIVE'
    for mb in bpy.data.metaballs: mb.render_resolution = 0.04
    ls.select_by_visibility = True; ls.select_silhouette = True; ls.select_border = True; ls.select_crease = True
    ls.select_contour = True; ls.select_external_contour = True
    vl.freestyle_settings.crease_angle = math.radians(120)
    col, th = LINES[STYLE]
    lst = ls.linestyle
    lst.thickness = th * RESX / 720
    if col is None:
        lst.color = (1.0, 0.15, 0.8)
    else:
        lst.color = col

# ---------------- рендер ----------------
S.render.engine = 'CYCLES'
S.cycles.device = 'CPU'
S.cycles.samples = int(_os.environ.get('SAMPLES', 28)) if STYLE in ('soft3d', 'clay', 'gzhel', 'lowpoly', 'shade') else 12
S.cycles.use_denoising = STYLE in ('soft3d', 'clay', 'gzhel', 'lowpoly', 'comic', 'toon', 'shade')
S.cycles.max_bounces = 4
S.render.resolution_x = RESX; S.render.resolution_y = int(RESX * 16 / 9)
S.render.film_transparent = False
S.view_settings.view_transform = 'Standard'
S.view_settings.look = 'None'
if STYLE in ('soft3d', 'clay', 'gzhel', 'lowpoly'):
    S.view_settings.look = 'Medium High Contrast'
S.render.image_settings.file_format = 'PNG'
if STYLE == 'gzhel': S.view_settings.exposure = -1.3
if STYLE == 'shade': S.view_settings.exposure = -2.2; S.view_settings.look = 'None'
S.render.filepath = OUT
if STYLE == 'ids':
    # Проходы для неона/контуров: ID материала (R = номер) и глубина (16 бит), без сглаживания.
    import json, os
    keys = sorted(MATS.keys())
    IDX = {k: i + 1 for i, k in enumerate(keys)}
    hide = set(os.environ.get('IDS_HIDE', '').split(',')) - {''}
    if 'tufts' in hide:
        TUFTS.hide_render = True
    def ids_mode(mode):
        for key, m in MATS.items():
            nt = m.node_tree; nt.nodes.clear()
            out = nt.nodes.new('ShaderNodeOutputMaterial'); em = nt.nodes.new('ShaderNodeEmission')
            if mode == 'id':
                em.inputs['Color'].default_value = (IDX[key] / 255.0, 0, 0, 1)
            else:
                cd = nt.nodes.new('ShaderNodeCameraData'); mth = nt.nodes.new('ShaderNodeMath')
                mth.operation = 'DIVIDE'; mth.inputs[1].default_value = 100.0
                nt.links.new(cd.outputs['View Distance'], mth.inputs[0]); nt.links.new(mth.outputs[0], em.inputs['Color'])
            nt.links.new(em.outputs[0], out.inputs[0])
    wn.clear(); wo = wn.new('ShaderNodeOutputWorld'); bgw = wn.new('ShaderNodeBackground')
    W.node_tree.links.new(bgw.outputs[0], wo.inputs[0])
    S.cycles.samples = 1; S.cycles.use_denoising = False; S.cycles.filter_width = 0.01
    S.cycles.max_bounces = 0
    S.view_settings.view_transform = 'Raw'; S.view_settings.look = 'None'; S.view_settings.exposure = 0
    S.render.dither_intensity = 0
    os.makedirs(OUT, exist_ok=True)
    json.dump(IDX, open(os.path.join(OUT, 'ids.json'), 'w'), ensure_ascii=False)
    step = int(ARGS[5]) if len(ARGS) > 5 else 1
    for f in range(F0, F1 + 1, step):
        S.frame_set(f)
        ids_mode('id'); bgw.inputs['Color'].default_value = (0, 0, 0, 1)
        S.render.image_settings.color_mode = 'RGB'; S.render.image_settings.color_depth = '8'
        S.render.filepath = os.path.join(OUT, 'id_%04d.png' % f); bpy.ops.render.render(write_still=True)
        ids_mode('depth'); bgw.inputs['Color'].default_value = (1, 1, 1, 1)
        S.render.image_settings.color_mode = 'BW'; S.render.image_settings.color_depth = '16'
        S.render.filepath = os.path.join(OUT, 'z_%04d.png' % f); bpy.ops.render.render(write_still=True)
elif F0 == F1:
    S.frame_set(F0)
    bpy.ops.render.render(write_still=True)
else:
    S.frame_start, S.frame_end = F0, F1
    S.frame_step = int(ARGS[5]) if len(ARGS) > 5 else 1
    bpy.ops.render.render(animation=True)
print('DONE', STYLE)
