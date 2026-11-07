"""Реализм материалов «Эскалатора»: без пластика.

Правка mike 07.11.2026: «без пластиковых людей и обстановки».
apply(scene) вызывается из build_shot.py после сборки плана и настройки рендера:
  - обстановка: фото-текстуры Poly Haven (CC0) в коробочной проекции в реальном размере: цвет из нашей палитры,
    а пятна, прожилки, швы, шероховатость и рельеф из текстуры; грязь в углах (AO); металл со шлифовкой;
    без скачанных текстур тот же класс делается процедурно (шум), чтобы сцена не была гладкой;
  - люди (MPFB): кожа с настоящим подповерхностным рассеянием (5-6 мм, а не 0,5), поры, пятнистость, пушок;
    влажные глаза с бликом; ткань с ворсом; волосы с бликом;
  - фаски 4 мм на острых рёбрах: на гранях появляются блики вместо идеальных «пластиковых» углов;
  - мягкие тени и отражения в Eevee.
fetch_all(tex_dir) запускается один раз на ПК в GUI-Blender: качает текстуры и пишет meta.json
(размер в метрах, средняя яркость и шероховатость), из которых apply() строит материалы.
"""
import bpy, os, re, json, math, hashlib, urllib.request

TEX_DIR = os.environ.get('ESK_TEX', r'D:\aipollon\eskalator\assets\tex')
UA = {'User-Agent': 'aipollon-blender'}

# класс -> (Poly Haven id, k яркости текстуры, разброс шероховатости, сила рельефа, глубина рельефа м)
PBR = {
    'granite':    ('granite_tile', 1.0, 0.12, 0.25, 0.002),
    'marble':     ('marble_01', 1.0, 0.10, 0.15, 0.001),
    'marbletile': ('marble_tiles', 0.9, 0.10, 0.30, 0.002),
    'plaster':    ('painted_plaster_wall', 0.7, 0.10, 0.50, 0.003),
    'concrete':   ('concrete_pavement', 0.9, 0.12, 0.60, 0.004),
    'asphalt':    ('asphalt_02', 1.0, 0.10, 0.60, 0.004),
    'earth':      ('dirt_floor', 1.0, 0.05, 0.80, 0.020),
    'wood':       ('fine_grained_wood', 1.0, 0.12, 0.20, 0.001),
    'parquet':    ('herringbone_parquet', 1.0, 0.12, 0.30, 0.002),
    'fabric':     ('rough_linen', 0.8, 0.05, 0.40, 0.001),
    'paint':      ('metal_plate', 0.25, 0.15, 0.25, 0.0015),
}

CLASS = {
    'MetGranite': 'granite', 'StationGranite': 'granite',
    'MetMarble': 'marble', 'OldMarble': 'marble', 'StationMarble': 'marble', 'MetMarbleRed': 'marble',
    'MallFloor': 'marbletile',
    'MetVault': 'plaster', 'SecVault': 'plaster', 'StoreWall': 'plaster', 'HouseWall': 'plaster',
    'HouseBalc': 'plaster', 'HouseStripe': 'plaster', 'VestRoof': 'plaster', 'MallWhite': 'plaster',
    'Pavement': 'concrete', 'Asphalt': 'asphalt', 'Earth': 'earth',
    'OldWood': 'wood', 'OldWoodDark': 'wood', 'DeskWood': 'wood', 'StampWood': 'wood', 'MetDeck': 'wood',
    'Parquet': 'parquet', 'Fabric': 'fabric', 'Fabric2': 'fabric',
    'EskAlu': 'brushed', 'EskSkirt': 'brushed', 'EskPlate': 'brushed', 'MetDeckSide': 'brushed',
    'SecStep': 'brushed', 'EskGear': 'brushed', 'MetRib': 'brushed', 'MetBronze': 'brushed',
    'OldBrass': 'brushed', 'OldSignGold': 'brushed', 'GlassesFrame': 'brushed',
    'EskTruss': 'paint', 'EskSteel': 'paint', 'EskGearbox': 'paint', 'LampPole': 'paint', 'MetAdFrame': 'paint',
    'EskChain': 'paint', 'EskMotor': 'paint', 'EskYellow': 'paint', 'EskComb': 'paint', 'EskRailChain': 'paint',
    'EskRailTrail': 'paint', 'EskWheelChain': 'paint', 'EskWheelTrail': 'paint', 'EskPanel': 'paint',
    'EskCut': 'paint', 'SecCut': 'paint', 'MetSignBlue': 'paint',
    'EskHandrail': 'rubber', 'EskHandrailPrint': 'rubber', 'EskRubber': 'rubber', 'CarTyre': 'rubber',
    'SecRail': 'rubber',
    'CarGlass': 'skip', 'HouseGlass': 'skip', 'Ink': 'skip', 'InkGrey': 'skip', 'PhoneBlack': 'skip',
    'GlassesLens': 'skip', 'Car': 'carpaint',
    'StudioFloor': 'studio', 'StudioWall': 'studio', 'Paper': 'paper', 'Hatbox': 'paper',
}
NO_AO = {'studio', 'carpaint', 'rubber', 'paper'}


# ============================================================================ скачивание (один раз на ПК)
def _get(url, timeout=120):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout).read()


def _pick(files, key, res):
    d = files.get(key, {}).get(res) or files.get(key, {}).get('1k') or {}
    for fmt in ('jpg', 'png'):
        if fmt in d:
            return d[fmt]['url']
    return None


def _avg(path, noncolor):
    im = bpy.data.images.load(path, check_existing=False)
    im.scale(64, 64)
    px = list(im.pixels)
    bpy.data.images.remove(im)
    n = len(px) // 4
    tot = 0.0
    for i in range(n):
        r, g, b = px[4 * i:4 * i + 3]
        if not noncolor:   # байтовая картинка отдаёт sRGB, шейдер видит линейный цвет
            r, g, b = [(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4) for c in (r, g, b)]
        tot += 0.2126 * r + 0.7152 * g + 0.0722 * b
    return max(1e-3, tot / n)


def fetch_all(tex_dir=TEX_DIR, res='2k', ids=None, log=print):
    os.makedirs(tex_dir, exist_ok=True)
    idx_p = os.path.join(tex_dir, '_polyhaven_index.json')
    if not os.path.exists(idx_p):
        open(idx_p, 'wb').write(_get('https://api.polyhaven.com/assets?t=textures'))
    index = json.load(open(idx_p, encoding='utf-8'))
    done = []
    for tid in (ids or sorted({v[0] for v in PBR.values()})):
        d = os.path.join(tex_dir, tid)
        mp = os.path.join(d, 'meta.json')
        if os.path.exists(mp):
            done.append(tid)
            continue
        os.makedirs(d, exist_ok=True)
        files = json.loads(_get('https://api.polyhaven.com/files/' + tid))
        meta = {'id': tid, 'license': 'CC0', 'source': 'https://polyhaven.com/a/' + tid,
                'authors': list((index.get(tid, {}).get('authors') or {}).keys())}
        for key, short in (('Diffuse', 'diff'), ('Rough', 'rough'), ('Displacement', 'disp')):
            url = _pick(files, key, res)
            if not url:
                continue
            fn = short + os.path.splitext(url)[1]
            open(os.path.join(d, fn), 'wb').write(_get(url))
            meta[short] = fn
        dims = index.get(tid, {}).get('dimensions') or [2000, 2000]
        meta['size'] = max(0.2, max(dims) / 1000.0)
        if 'diff' in meta:
            meta['avg'] = _avg(os.path.join(d, meta['diff']), False)
        if 'rough' in meta:
            meta['avg_r'] = _avg(os.path.join(d, meta['rough']), True)
        json.dump(meta, open(mp, 'w', encoding='utf-8'), indent=1)
        done.append(tid)
        log('tex ok ' + tid)
    return done


# ============================================================================ узлы
def _n(nt, typ, x=0, y=0, **kw):
    n = nt.nodes.new(typ)
    n.location = (x, y)
    for k, v in kw.items():
        setattr(n, k, v)
    return n


def _base(nt, pb):
    """Сокет с текущим цветом (если цвет просто числом — делаем узел RGB)."""
    inp = pb.inputs['Base Color']
    if inp.is_linked:
        return inp.links[0].from_socket
    rgb = _n(nt, 'ShaderNodeRGB', -1400, 300)
    rgb.outputs[0].default_value = tuple(inp.default_value)
    return rgb.outputs[0]


def _scale_col(nt, col, fac, x=-300, y=300):
    vm = _n(nt, 'ShaderNodeVectorMath', x, y, operation='SCALE')
    nt.links.new(col, vm.inputs[0])
    nt.links.new(fac, vm.inputs['Scale'])
    return vm.outputs[0]


def _maprange(nt, src, a0, a1, b0, b1, x=-500, y=0):
    m = _n(nt, 'ShaderNodeMapRange', x, y, clamp=True)
    m.inputs['From Min'].default_value = a0
    m.inputs['From Max'].default_value = a1
    m.inputs['To Min'].default_value = b0
    m.inputs['To Max'].default_value = b1
    nt.links.new(src, m.inputs['Value'])
    return m.outputs['Result']


def _noise(nt, vec, scale, detail=4.0, rough=0.55, x=-900, y=0):
    n = _n(nt, 'ShaderNodeTexNoise', x, y)
    n.inputs['Scale'].default_value = scale
    n.inputs['Detail'].default_value = detail
    n.inputs['Roughness'].default_value = rough
    nt.links.new(vec, n.inputs['Vector'])
    return n.outputs['Fac']


def _bump(nt, pb, height, strength, dist, x=-300, y=-400):
    """Рельеф по цепочке: новый Bump получает прежнюю нормаль материала."""
    b = _n(nt, 'ShaderNodeBump', x, y)
    b.inputs['Strength'].default_value = strength
    b.inputs['Distance'].default_value = dist
    nt.links.new(height, b.inputs['Height'])
    ni = pb.inputs['Normal']
    if ni.is_linked:
        nt.links.new(ni.links[0].from_socket, b.inputs['Normal'])
    nt.links.new(b.outputs['Normal'], ni)


def _ao_dirt(nt, col, lo=0.62, dist=0.35):
    ao = _n(nt, 'ShaderNodeAmbientOcclusion', -700, 600, samples=8)
    ao.inputs['Distance'].default_value = dist
    f = _maprange(nt, ao.outputs['AO'], 0.0, 1.0, lo, 1.0, -500, 600)
    return _scale_col(nt, col, f, -150, 450)


def _seed(name):
    h = hashlib.md5(name.encode()).digest()
    return [b / 255.0 * 7.0 for b in h[:3]]


def _coords(nt, name, scale, stretch=(1, 1, 1)):
    tc = _n(nt, 'ShaderNodeTexCoord', -1700, 0)
    mp = _n(nt, 'ShaderNodeMapping', -1500, 0)
    mp.inputs['Scale'].default_value = tuple(scale * s for s in stretch)
    mp.inputs['Location'].default_value = _seed(name)
    nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
    return mp.outputs['Vector']


_IMG = {}
def _img(path, noncolor):
    im = _IMG.get(path)
    if im is None or im.name not in bpy.data.images:
        im = bpy.data.images.load(path, check_existing=True)
        if noncolor:
            im.colorspace_settings.name = 'Non-Color'
        _IMG[path] = im
    return im


def _teximg(nt, vec, path, noncolor, x, y):
    t = _n(nt, 'ShaderNodeTexImage', x, y)
    t.image = _img(path, noncolor)
    t.projection = 'BOX'
    t.projection_blend = 0.3
    nt.links.new(vec, t.inputs['Vector'])
    return t


# ============================================================================ обстановка
def _pbr(m, pb, cls, tex_dir):
    tid, k, ramt, bstr, bdist = PBR[cls]
    d = os.path.join(tex_dir, tid)
    mp = os.path.join(d, 'meta.json')
    if not os.path.exists(mp):
        return False
    meta = json.load(open(mp, encoding='utf-8'))
    nt = m.node_tree
    vec = _coords(nt, m.name, 1.0 / meta['size'])
    r = pb.inputs['Roughness'].default_value
    col = _base(nt, pb)
    if 'diff' in meta:
        t = _teximg(nt, vec, os.path.join(d, meta['diff']), False, -1200, 300)
        bw = _n(nt, 'ShaderNodeRGBToBW', -950, 300)
        nt.links.new(t.outputs['Color'], bw.inputs[0])
        dv = _n(nt, 'ShaderNodeMath', -800, 300, operation='DIVIDE')
        nt.links.new(bw.outputs[0], dv.inputs[0])
        dv.inputs[1].default_value = meta.get('avg', 0.2)
        pw = _n(nt, 'ShaderNodeMath', -650, 300, operation='POWER', use_clamp=False)
        nt.links.new(dv.outputs[0], pw.inputs[0])
        pw.inputs[1].default_value = k
        mn = _n(nt, 'ShaderNodeMath', -500, 300, operation='MINIMUM')
        nt.links.new(pw.outputs[0], mn.inputs[0])
        mn.inputs[1].default_value = 2.5
        col = _scale_col(nt, col, mn.outputs[0], -350, 300)
    if 'rough' in meta:
        t = _teximg(nt, vec, os.path.join(d, meta['rough']), True, -1200, 0)
        a = meta.get('avg_r', 0.6)
        rr = _maprange(nt, t.outputs['Color'], a - 0.3, a + 0.3, max(0.03, r - ramt), min(1.0, r + ramt))
        nt.links.new(rr, pb.inputs['Roughness'])
    if 'disp' in meta:
        t = _teximg(nt, vec, os.path.join(d, meta['disp']), True, -1200, -300)
        _bump(nt, pb, t.outputs['Color'], bstr, bdist)
    if cls not in NO_AO:
        col = _ao_dirt(nt, col)
    nt.links.new(col, pb.inputs['Base Color'])
    return True


def _proc(m, pb, cls):
    """Процедурный вариант: пятна цвета, разброс шероховатости, микрорельеф (и шлифовка для металла)."""
    nt = m.node_tree
    r = pb.inputs['Roughness'].default_value
    col = _base(nt, pb)
    P = {  # масштаб пятен 1/м, амплитуда цвета, разброс шероховатости, масштаб зерна, сила зерна
        'brushed':  (3.0, 0.05, 0.10, 0, 0.0),
        'paint':    (2.0, 0.07, 0.12, 300, 0.05),
        'rubber':   (4.0, 0.05, 0.10, 700, 0.06),
        'carpaint': (1.0, 0.02, 0.04, 90, 0.015),
        'studio':   (0.6, 0.03, 0.05, 250, 0.02),
        'paper':    (6.0, 0.04, 0.05, 900, 0.10),
    }.get(cls, (2.5, 0.06, 0.10, 400, 0.05))
    sc, ac, ar, gs, gb = P
    vec = _coords(nt, m.name, 1.0)
    blot = _noise(nt, vec, sc, 6.0, 0.6, -1100, 300)
    f = _maprange(nt, blot, 0.3, 0.7, 1.0 - ac, 1.0 + ac, -800, 300)
    col = _scale_col(nt, col, f, -500, 300)
    if cls == 'brushed':
        r = max(r, 0.2)
        vb = _coords(nt, m.name + 'b', 1.0, stretch=(2.0, 260.0, 260.0))
        st = _noise(nt, vb, 1.0, 3.0, 0.5, -1100, 0)
        sm = _noise(nt, vec, 3.0, 4.0, 0.6, -1100, -150)
        add = _n(nt, 'ShaderNodeMath', -800, 0, operation='ADD')
        nt.links.new(st, add.inputs[0]); nt.links.new(sm, add.inputs[1])
        nt.links.new(_maprange(nt, add.outputs[0], 0.7, 1.3, max(0.08, r - ar), min(1.0, r + ar)), pb.inputs['Roughness'])
        _bump(nt, pb, st, 0.03, 0.0003)
    else:
        rv = _noise(nt, vec, sc * 2.3, 5.0, 0.6, -1100, 0)
        nt.links.new(_maprange(nt, rv, 0.3, 0.7, max(0.03, r - ar), min(1.0, r + ar)), pb.inputs['Roughness'])
        if gs:
            gr = _noise(nt, vec, gs, 2.0, 0.5, -1100, -300)
            _bump(nt, pb, gr, gb, 0.0005)
    if cls not in NO_AO:
        col = _ao_dirt(nt, col)
    nt.links.new(col, pb.inputs['Base Color'])


# ============================================================================ люди (MPFB)
def _skin_group(n):
    I = n.inputs
    for k, v in (('SSS strength', 0.85), ('SSS radius scale', 1.0), ('Pore strength', 0.35),
                 ('Roughness', 0.44), ('Clearcoat', 0.12), ('Clearcoat Roughness', 0.35)):
        if k in I:
            I[k].default_value = v
    g = n.node_tree
    if g.get('esk_look'):
        return
    g['esk_look'] = 1
    for pb in [x for x in g.nodes if x.type == 'BSDF_PRINCIPLED']:
        pb.inputs['Subsurface Scale'].default_value = 0.006   # 6 мм красного: кожа просвечивает, а не «пластик»
        for k, v in (('Sheen Weight', 0.12), ('Sheen Roughness', 0.45)):
            if k in pb.inputs:
                pb.inputs[k].default_value = v
        # пятнистость кожи: лёгкое покраснение и неровный тон
        tc = _n(g, 'ShaderNodeTexCoord', -1400, -600)
        nz = _n(g, 'ShaderNodeTexNoise', -1200, -600)
        nz.inputs['Scale'].default_value = 28.0
        nz.inputs['Detail'].default_value = 8.0
        nz.inputs['Roughness'].default_value = 0.6
        g.links.new(tc.outputs['Object'], nz.inputs['Vector'])
        ramp = _n(g, 'ShaderNodeValToRGB', -1000, -600)
        ramp.color_ramp.elements[0].position = 0.35
        ramp.color_ramp.elements[0].color = (1.0, 0.90, 0.88, 1)
        ramp.color_ramp.elements[1].position = 0.70
        ramp.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1)
        g.links.new(nz.outputs['Fac'], ramp.inputs['Fac'])
        inp = pb.inputs['Base Color']
        if inp.is_linked:
            vm = _n(g, 'ShaderNodeVectorMath', -300, -500, operation='MULTIPLY')
            g.links.new(inp.links[0].from_socket, vm.inputs[0])
            g.links.new(ramp.outputs['Color'], vm.inputs[1])
            g.links.new(vm.outputs[0], inp)
        # шероховатость кожи неровная: нос/лоб блестят пятнами, остальное матовее
        rn = _n(g, 'ShaderNodeTexNoise', -1200, -900)
        rn.inputs['Scale'].default_value = 12.0
        g.links.new(tc.outputs['Object'], rn.inputs['Vector'])
        ri = pb.inputs['Roughness']
        if ri.is_linked:
            src = ri.links[0].from_socket
            mr = _n(g, 'ShaderNodeMapRange', -900, -900)
            mr.inputs['From Min'].default_value = 0.3; mr.inputs['From Max'].default_value = 0.7
            mr.inputs['To Min'].default_value = -0.08; mr.inputs['To Max'].default_value = 0.08
            g.links.new(rn.outputs['Fac'], mr.inputs['Value'])
            ad = _n(g, 'ShaderNodeMath', -600, -900, operation='ADD', use_clamp=True)
            g.links.new(src, ad.inputs[0]); g.links.new(mr.outputs['Result'], ad.inputs[1])
            g.links.new(ad.outputs[0], ri)
        _stubble(g, pb)


def _people(m, base):
    nt = m.node_tree
    low = base.lower()
    if 'eyebrow' in low:      # брови гуще и темнее: светлые бровки делают лицо «кукольным»
        for pb in [n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED']:
            inp = pb.inputs['Base Color']
            if inp.is_linked:
                k = _n(nt, 'ShaderNodeValue', -900, -600)
                k.outputs[0].default_value = 0.4
                nt.links.new(_scale_col(nt, inp.links[0].from_socket, k.outputs[0], -600, -400), inp)
            pb.inputs['Roughness'].default_value = 0.6
        return 'brows'
    if 'eyelash' in low:
        return 'skip'
    groups = [n for n in nt.nodes if n.type == 'GROUP' and n.node_tree and 'Pore scale' in n.inputs]
    if groups:
        for n in groups:
            _skin_group(n)
        return 'skin'
    pbs = [n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED']
    if not pbs:
        return 'skip'
    if low.endswith('high-poly') or low.endswith('low-poly'):
        for pb in pbs:    # влажные глаза: блик-«окошко» как у живого человека
            pb.inputs['Roughness'].default_value = 0.12
            pb.inputs['Specular IOR Level'].default_value = 0.6
            pb.inputs['Coat Weight'].default_value = 1.0
            pb.inputs['Coat Roughness'].default_value = 0.03
        return 'eyes'
    if any(k in low for k in ('short0', 'bob0', 'ponytail', 'long0', 'hair', 'braid', 'afro')):
        for pb in pbs:   # матовые, с разнотоном: блестящая «каска» — главный признак пластиковых волос
            pb.inputs['Roughness'].default_value = 0.62
            pb.inputs['Specular IOR Level'].default_value = 0.28
            inp = pb.inputs['Base Color']
            if inp.is_linked:
                tc = _n(nt, 'ShaderNodeTexCoord', -1400, -500)
                nz = _noise(nt, tc.outputs['Object'], 60.0, 6.0, 0.6, -1200, -500)
                f = _maprange(nt, nz, 0.3, 0.7, 0.75, 1.15, -1000, -500)
                nt.links.new(_scale_col(nt, inp.links[0].from_socket, f, -600, -400), inp)
        return 'hair'
    shoes = 'shoe' in low or 'boot' in low
    for pb in pbs:
        if shoes:
            pb.inputs['Roughness'].default_value = 0.45
            pb.inputs['Specular IOR Level'].default_value = 0.4
            pb.inputs['Coat Weight'].default_value = 0.15
            pb.inputs['Coat Roughness'].default_value = 0.25
        else:   # ткань: ворс (sheen), матовость, мелкое плетение
            pb.inputs['Roughness'].default_value = max(0.82, pb.inputs['Roughness'].default_value)
            pb.inputs['Specular IOR Level'].default_value = 0.22
            pb.inputs['Sheen Weight'].default_value = 0.12    # больше 0.2 на тёмной ткани = серый «велюр»
            pb.inputs['Sheen Roughness'].default_value = 0.5
            tc = _n(nt, 'ShaderNodeTexCoord', -1400, -500)
            nz = _noise(nt, tc.outputs['Object'], 900.0, 2.0, 0.5, -1200, -500)
            _bump(nt, pb, nz, 0.08, 0.0004)
    return 'shoes' if shoes else 'cloth'


def _lens(m):
    """Стекло очков: прозрачное с бликом. Пропускание с IOR в Eevee без трассировки преломления даёт
    молочно-серые «солнечные» очки, поэтому линза — почти прозрачный слой с отражением."""
    pb = m.node_tree.nodes.get('Principled BSDF')
    if not pb:
        return
    pb.inputs['Transmission Weight'].default_value = 0.0
    pb.inputs['Base Color'].default_value = (0.02, 0.02, 0.02, 1)
    pb.inputs['Roughness'].default_value = 0.03
    pb.inputs['Specular IOR Level'].default_value = 0.5
    pb.inputs['Alpha'].default_value = 0.10
    try:
        m.surface_render_method = 'BLENDED'
    except Exception:
        pass
    m.use_backface_culling = False


def _smooth(e0, e1, x):
    t = min(1.0, max(0.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


def beard_mask(body, rig):
    """Щетина ведущего (у ведущего образца лёгкая небритость; гладкий подбородок = «манекен»).
    Маска пишется в атрибут вершин 'esk_beard' по позе покоя, ориентиры — кости лица рига MakeHuman
    (лицо смотрит в -Y): губы oris05/oris01, низ носа levator06, подбородок special04, челюсть, уши."""
    me = body.data
    if 'esk_beard' in me.attributes:
        return 0
    B = rig.data.bones
    def hz(n, d):
        return B[n].head_local.z if n in B else d
    nose = hz('levator06.L', 1.6437) - 0.006     # низ носа
    up_lip = hz('oris05', 1.625)
    lo_lip = hz('oris01', 1.5986)
    chin = hz('special04', 1.5629)
    M = rig.matrix_world.inverted() @ body.matrix_world
    cos = [v.co.copy() for v in me.vertices]
    if me.shape_keys:
        kb = me.shape_keys.key_blocks
        base = kb[0]
        for k in kb[1:]:
            if k.value and not k.mute:
                for i, (a, b) in enumerate(zip(k.data, base.data)):
                    cos[i] += (a.co - b.co) * k.value
    vals, lv = [], []
    for co in cos:
        x, y, z = M @ co
        ax = abs(x)
        top = nose + max(0.0, ax - 0.022) * 0.85          # линия щеки: от носа к виску
        m = _smooth(top + 0.004, top - 0.006, z)          # ниже линии щеки
        m *= _smooth(chin - 0.020, chin - 0.002, z)       # и чуть под подбородок на шею
        m *= _smooth(-0.045, -0.075, y)                   # только спереди ушей и шеи
        m *= _smooth(0.074, 0.064, ax)                    # не заходить на уши
        lips = _smooth(0.030, 0.020, ax) * _smooth(lo_lip - 0.008, lo_lip - 0.002, z) \
            * _smooth(up_lip + 0.007, up_lip + 0.002, z) * _smooth(-0.140, -0.152, y)
        m *= 1.0 - lips
        vals.append(m)
        lv.append(lips * _smooth(0.026, 0.016, ax))
    at = me.attributes.new('esk_beard', 'FLOAT', 'POINT')
    at.data.foreach_set('value', vals)
    al = me.attributes.new('esk_lips', 'FLOAT', 'POINT')
    al.data.foreach_set('value', lv)
    return sum(1 for v in vals if v > 0.5)


def _stubble(g, pb):
    """в группу кожи: точки щетины по маске 'esk_beard' (нет атрибута = 0, у толпы ничего не меняется)"""
    at = _n(g, 'ShaderNodeAttribute', -1200, -1200, attribute_type='GEOMETRY', attribute_name='esk_beard')
    tc = _n(g, 'ShaderNodeTexCoord', -1400, -1400)
    nz = _n(g, 'ShaderNodeTexNoise', -1200, -1400)
    nz.inputs['Scale'].default_value = 2600.0
    nz.inputs['Detail'].default_value = 0.0
    g.links.new(tc.outputs['Object'], nz.inputs['Vector'])
    sp = _n(g, 'ShaderNodeMapRange', -1000, -1400)
    sp.inputs['From Min'].default_value = 0.42; sp.inputs['From Max'].default_value = 0.62
    sp.inputs['To Min'].default_value = 0.55; sp.inputs['To Max'].default_value = 1.0
    g.links.new(nz.outputs['Fac'], sp.inputs['Value'])
    mu = _n(g, 'ShaderNodeMath', -800, -1300, operation='MULTIPLY')
    g.links.new(at.outputs['Fac'], mu.inputs[0]); g.links.new(sp.outputs['Result'], mu.inputs[1])
    mix = _n(g, 'ShaderNodeMixRGB', -500, -1200, blend_type='MULTIPLY')
    g.links.new(mu.outputs[0], mix.inputs['Fac'])
    mix.inputs['Color2'].default_value = (0.36, 0.32, 0.30, 1)
    al = _n(g, 'ShaderNodeAttribute', -1200, -1600, attribute_type='GEOMETRY', attribute_name='esk_lips')
    lip = _n(g, 'ShaderNodeMixRGB', -300, -1300, blend_type='MULTIPLY')    # губы чуть темнее и розовее кожи
    g.links.new(al.outputs['Fac'], lip.inputs['Fac'])
    lip.inputs['Color2'].default_value = (0.82, 0.55, 0.52, 1)
    g.links.new(mix.outputs['Color'], lip.inputs['Color1'])
    inp = pb.inputs['Base Color']
    if inp.is_linked:
        g.links.new(inp.links[0].from_socket, mix.inputs['Color1'])
        g.links.new(lip.outputs['Color'], inp)


# ============================================================================ фаски
def bevel_edges(width=0.004, max_polys=4000):
    n = 0
    for ob in bpy.data.objects:
        if ob.type != 'MESH' or ob.get('esk_bevel'):
            continue
        if any(md.type in ('ARMATURE', 'BEVEL', 'SUBSURF') for md in ob.modifiers):
            continue
        me = ob.data
        if not (6 <= len(me.polygons) <= max_polys):
            continue
        names = [s.material.name for s in ob.material_slots if s.material]
        if any(re.match(r'^(P\d\dr|Hero)\.', x) for x in names):
            continue
        md = ob.modifiers.new('EskBevel', 'BEVEL')
        md.width = width
        md.segments = 1
        md.limit_method = 'ANGLE'
        md.angle_limit = math.radians(40)
        md.use_clamp_overlap = True
        ob['esk_bevel'] = 1
        n += 1
    return n


# ============================================================================ рендер
def render_quality(sc):
    ee = sc.eevee
    for k, v in dict(use_raytracing=True, ray_tracing_method='SCREEN', use_fast_gi=True,
                     fast_gi_method='GLOBAL_ILLUMINATION', shadow_ray_count=2, shadow_step_count=10,
                     use_shadows=True).items():
        try:
            setattr(ee, k, v)
        except Exception:
            pass
    ro = getattr(ee, 'ray_tracing_options', None)
    if ro:
        for k, v in dict(resolution_scale='1', use_denoise=True, trace_max_roughness=0.6).items():
            try:
                setattr(ro, k, v)
            except Exception:
                pass
    for ob in bpy.data.objects:
        if ob.type == 'LIGHT':
            try:
                ob.data.use_shadow_jitter = True    # мягкие тени в Eevee, как от настоящих ламп
            except Exception:
                pass
    if sc.render.engine == 'CYCLES':
        try:
            sc.cycles.adaptive_threshold = 0.02
        except Exception:
            pass


# ============================================================================ главное
def classify(base):
    if base in CLASS:
        return CLASS[base]
    for k in sorted(CLASS, key=len, reverse=True):
        if base.startswith(k):
            return CLASS[k]
    return 'generic'


def apply(sc=None, tex_dir=TEX_DIR, bevel=True):
    sc = sc or bpy.context.scene
    stats = {}
    for m in list(bpy.data.materials):
        if not m.use_nodes or m.get('esk_look') or not m.users:
            continue
        m['esk_look'] = 1
        base = re.sub(r'\.\d{3}$', '', m.name)
        nt = m.node_tree
        if base == 'GlassesLens':
            _lens(m)
            stats['lens'] = 1
            continue
        if re.match(r'^(P\d\dr|Hero)\.', base):
            cls = _people(m, base)
            stats[cls] = stats.get(cls, 0) + 1
            continue
        pbs = [n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED']
        if len(pbs) != 1:
            continue
        pb = pbs[0]
        if any(n.type == 'TEX_IMAGE' for n in nt.nodes):
            continue                                  # картинки рекламы и вывесок не трогаем
        if pb.inputs['Emission Strength'].default_value > 0 or pb.inputs['Alpha'].default_value < 1 \
                or pb.inputs['Transmission Weight'].default_value > 0:
            continue                                  # лампы, вывески, стекло
        cls = classify(base)
        if cls == 'skip':
            continue
        ok = cls in PBR and _pbr(m, pb, cls, tex_dir)
        if not ok:
            _proc(m, pb, cls if cls not in PBR else 'generic')
        key = cls + ('' if ok or cls not in PBR else '~proc')
        stats[key] = stats.get(key, 0) + 1
    for ob in bpy.data.objects:                      # щетина только у ведущего
        if ob.type == 'MESH' and ob.parent and ob.parent.type == 'ARMATURE' and \
                any(s.material and s.material.name.startswith('Hero.body') for s in ob.material_slots):
            stats['beard_verts'] = beard_mask(ob, ob.parent)
    nb = bevel_edges() if bevel else 0
    render_quality(sc)
    stats['bevel'] = nb
    print('ESK_LOOK', json.dumps(stats, ensure_ascii=False))
    return stats
