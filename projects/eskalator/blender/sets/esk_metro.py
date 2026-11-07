"""Moscow-metro style inclined escalator tunnel: 3 escalators, wide lamp decks between them, ribbed vault,
granite halls at both ends. Built from code. Detail-rich background (lamps, signs, people placeholders).
"""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix
import esk_mech as E

LANE = 1.75          # distance between escalator centre lines

def M():
    return dict(
        vault=E.mat('MetVault', '#E9E1CF', rough=0.55),
        rib=E.mat('MetRib', '#C9BFA8', rough=0.45, metal=0.3),
        deck=E.mat('MetDeck', '#8C6A45', rough=0.35, coat=0.4),          # polished wood/bronze deck
        deckside=E.mat('MetDeckSide', '#D9D4CC', rough=0.3, metal=0.6),
        bronze=E.mat('MetBronze', '#9A7240', rough=0.3, metal=0.9),
        shade=E.mat('MetShade', '#FFF3DC', rough=0.2, emit=9.0),
        granite=E.mat('MetGranite', '#6F6A66', rough=0.25),
        marble=E.mat('MetMarble', '#E8E2D8', rough=0.2),
        marble2=E.mat('MetMarbleRed', '#8E3B32', rough=0.25),
        light=E.mat('MetLightStrip', '#FFF1D6', rough=0.4, emit=14.0),
        sign=E.mat('MetSignBlue', '#1D4FA0', rough=0.4),
        signw=E.mat('MetSignWhite', '#FFFFFF', rough=0.4, emit=2.0),
        red=E.mat('MetRed', '#D21F26', rough=0.4, emit=1.5),
        metro_m=E.mat('MetLogoRed', '#E21B23', rough=0.3, emit=6.0),
    )

def vault(col, path, y_c, width, ex=3.0, R=None, mm=None, ribs=True, z_up=2.4):
    """half-cylinder vault following the escalator profile (centre line at y_c)"""
    R = R or width / 2
    bm = bmesh.new()
    xs = [path.x0 - ex + i * 0.4 for i in range(int((path.x1 - path.x0 + 2 * ex) / 0.4) + 1)]
    n = 24
    rings = []
    for x in xs:
        zc = path.z_of(min(max(x, path.x0), path.x1)) + z_up
        ring = []
        for k in range(n + 1):
            a = math.pi * k / n
            ring.append(bm.verts.new((x, y_c - R * math.cos(a), zc + R * math.sin(a) * 0.85)))
        # walls down to the floor line
        rings.append(ring)
    for r0, r1 in zip(rings, rings[1:]):
        for k in range(n):
            bm.faces.new([r0[k], r1[k], r1[k + 1], r0[k + 1]])
    # vertical side walls under the springing line
    for sy in (-1, 1):
        prev = None
        for x in xs:
            zc = path.z_of(min(max(x, path.x0), path.x1)) + z_up
            a = bm.verts.new((x, y_c + sy * R, zc)); b = bm.verts.new((x, y_c + sy * R, zc - 3.6))
            if prev: bm.faces.new([prev[0], a, b, prev[1]] if sy < 0 else [prev[1], b, a, prev[0]])
            prev = (a, b)
    ob = E.obj_from_bm(bm, 'Vault', [mm['vault']], col, smooth=True)
    for p in ob.data.polygons: p.use_smooth = True
    if ribs:
        bm = bmesh.new()
        for x in xs[::3]:
            zc = path.z_of(min(max(x, path.x0), path.x1)) + z_up
            pts = [Vector((x, y_c - (R - 0.03) * math.cos(math.pi * k / n), zc + (R - 0.03) * math.sin(math.pi * k / n) * 0.85)) for k in range(n + 1)]
            E.bm_tube(bm, pts, 0.14, 0.07, 0, side=(1, 0, 0))
        E.obj_from_bm(bm, 'VaultRibs', [mm['rib']], col)
        # two warm light strips along the vault
        bm = bmesh.new()
        for sy in (-1, 1):
            pts = []
            for x in xs:
                zc = path.z_of(min(max(x, path.x0), path.x1)) + z_up
                a = math.pi / 2 + sy * 0.55
                pts.append(Vector((x, y_c - (R - 0.06) * math.cos(a), zc + (R - 0.06) * math.sin(a) * 0.85)))
            E.bm_tube(bm, pts, 0.18, 0.04, 0)
        E.obj_from_bm(bm, 'VaultLights', [mm['light']], col)
    return ob

def deck(col, path, y, width, mm, lamps=True, lamp_every=3.2):
    """inclined deck between two escalators (the wide balustrade with the lamp stems)"""
    bm = bmesh.new()
    xs = [path.x0 - 0.8 + i * 0.25 for i in range(int((path.x1 - path.x0 + 1.6) / 0.25) + 1)]
    top = []
    for x in xs:
        z = path.z_of(min(max(x, path.x0), path.x1)) + E.TREAD_Z + 0.95
        top.append((x, z))
    for (xa, za), (xb, zb) in zip(top, top[1:]):
        v = [bm.verts.new((xa, y - width / 2, za)), bm.verts.new((xb, y - width / 2, zb)),
             bm.verts.new((xb, y + width / 2, zb)), bm.verts.new((xa, y + width / 2, za))]
        bm.faces.new(v).material_index = 0
        for sy in (-1, 1):
            yy = y + sy * width / 2
            v = [bm.verts.new((xa, yy, za)), bm.verts.new((xb, yy, zb)),
                 bm.verts.new((xb, yy, zb - 1.0)), bm.verts.new((xa, yy, za - 1.0))]
            bm.faces.new(v).material_index = 1
    E.obj_from_bm(bm, f'Deck{y:+.1f}', [mm['deck'], mm['deckside']], col)
    if lamps:
        bm = bmesh.new(); bs = bmesh.new()
        x = path.x0 + 0.6
        while x < path.x1 - 0.4:
            z = path.z_of(x) + E.TREAD_Z + 0.95
            E.bm_cyl(bm, Vector((x, y, z + 0.55)), 0.025, 1.1, 'Z', 12, 0)
            E.bm_cyl(bm, Vector((x, y, z + 0.03)), 0.09, 0.06, 'Z', 16, 0)
            res = bmesh.ops.create_uvsphere(bs, u_segments=16, v_segments=10, radius=0.13)
            bmesh.ops.transform(bs, matrix=Matrix.Translation((x, y, z + 1.22)) @ Matrix.Diagonal((1, 1, 1.35, 1)), verts=res['verts'])
            x += lamp_every
        E.obj_from_bm(bm, f'LampStems{y:+.1f}', [mm['bronze']], col, smooth=True)
        E.obj_from_bm(bs, f'LampShades{y:+.1f}', [mm['shade']], col, smooth=True)

def hall(col, x_from, x_to, z, y_c, width, mm, columns=True, name='Hall'):
    bm = bmesh.new()
    E.bm_box(bm, (x_from, y_c - width / 2, z - 0.2), (x_to, y_c + width / 2, z), 0)                 # floor
    E.bm_box(bm, (x_from, y_c - width / 2, z + 4.2), (x_to, y_c + width / 2, z + 4.5), 1)           # ceiling
    for sy in (-1, 1):
        E.bm_box(bm, (x_from, y_c + sy * width / 2 - 0.1, z), (x_to, y_c + sy * width / 2 + 0.1, z + 4.2), 1)
    E.obj_from_bm(bm, name, [mm['granite'], mm['marble']], col)
    if columns:
        bm = bmesh.new()
        x = x_from + 1.5
        while x < x_to - 0.5:
            for sy in (-1, 1):
                E.bm_box(bm, (x - 0.35, y_c + sy * (width / 2 - 1.3) - 0.35, z), (x + 0.35, y_c + sy * (width / 2 - 1.3) + 0.35, z + 4.2), 0)
            x += 3.5
        E.obj_from_bm(bm, name + 'Columns', [mm['marble2']], col)
        # ceiling lights
        bm = bmesh.new()
        x = x_from + 1.0
        while x < x_to:
            E.bm_box(bm, (x - 0.6, y_c - 0.15, z + 4.1), (x + 0.6, y_c + 0.15, z + 4.2), 0)
            x += 2.4
        E.obj_from_bm(bm, name + 'Lights', [mm['light']], col)

def sign(col, loc, rot_z, text, mm, w=1.6, h=0.42):
    """blue metro sign with white text (needs a font with cyrillic)"""
    bm = bmesh.new(); E.bm_box(bm, (-w / 2, -0.03, -h / 2), (w / 2, 0.03, h / 2), 0)
    ob = E.obj_from_bm(bm, 'Sign', [mm['sign']], col, loc=loc); ob.rotation_euler = (0, 0, rot_z)
    cu = bpy.data.curves.new('SignTxt', 'FONT'); cu.body = text; cu.size = h * 0.48; cu.align_x = 'CENTER'; cu.align_y = 'CENTER'
    f = font()
    if f: cu.font = f
    t = bpy.data.objects.new('SignTxt', cu); col.objects.link(t)
    t.data.materials.append(mm['signw'])
    t.parent = ob; t.location = (0, -0.035, 0); t.rotation_euler = (math.pi / 2, 0, 0)
    return ob

_FONT = None
def font():
    global _FONT
    if _FONT: return _FONT
    import os
    for p in (r'C:\Windows\Fonts\arialbd.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'):
        if os.path.exists(p):
            _FONT = bpy.data.fonts.load(p, check_existing=True); return _FONT
    return None

def build(rise=6.0, lanes=3, animate=(1, 90, 30), land_lo=3.0, land_hi=3.0, glass=False, chain=False, name='Met'):
    """returns dict with escalators and the path of the middle lane"""
    col = E.coll(name)
    mm = M()
    escs = []
    for i in range(lanes):
        y = (i - (lanes - 1) / 2) * LANE
        e = E.Escalator(origin=(0, y, 0), rise=rise, name=f'{name}Esk{i}', cutaway=False, machine=False, truss=False,
                        chain=chain, rails=False, sprockets=False, glass=glass, land_lo=land_lo, land_hi=land_hi)
        escs.append(e)
    path = escs[0].path
    width = lanes * LANE + 1.6
    vault(col, path, 0.0, width, mm=mm)
    for i in range(lanes - 1):
        y = (i - (lanes - 1) / 2) * LANE + LANE / 2
        deck(col, path, y, LANE - E.STEP_W - 0.28, mm)
    for sy in (-1, 1):
        deck(col, path, sy * (lanes * LANE / 2 + 0.05), 0.3, mm, lamps=False)
    hall(col, path.x0 - 14, path.x0 - 0.6, E.TREAD_Z, 0.0, width + 6, mm, name='HallLow')
    hall(col, path.x1 + 0.6, path.x1 + 14, path.rise + E.TREAD_Z, 0.0, width + 6, mm, name='HallTop')
    if animate:
        f0, f1, fps = animate
        for k, e in enumerate(escs):
            sp = 0.75 if k != 1 else -0.75   # middle lane goes down
            e.animate(f0, f1, fps, speed=sp if sp > 0 else 0.75, s0=k * 0.13)
    return dict(escs=escs, path=path, col=col, mm=mm)
