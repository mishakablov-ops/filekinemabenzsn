"""Живые люди: настоящий мокап CMU (BVH) на риг MakeHuman/MPFB «default» (ведущий и толпа).

Правка mike 08.11.2026: «добавить побольше жизни людям… можешь скачать из инета и довести до ума».
Источник: CMU Graphics Lab Motion Capture Database в BVH (конверсия cgspeed, зеркало github.com/sfd158/cmu-mocap).
Лицензия CMU: данные можно свободно использовать, в том числе в коммерческих продуктах (нельзя перепродавать сами данные).

Как переносится движение (без импорта BVH и без frame_set, всё математикой):
  * BVH разбирается здесь же; у BVH все суставы в покое ориентированы как мир, поэтому мировой поворот сустава
    в кадре D(t) — это и есть поворот «от позы покоя» (T-поза CMU).
  * Риг MPFB ставится в T-позу по data/poses/default_fk/t-pose.json из MPFB (копия: assets/mocap/default_tpose.json).
  * Для каждой пары костей A выравнивает направление сегмента нашей T-позы на сегмент CMU в покое
    (у CMU ноги в покое разведены на ~20°, без A получились бы ноги иксом).
  * Поворот нашей кости в пространстве рига: R(t) = D(t) · A · R_T. Из него и позы родителя считается базис кости.
  * Таз: смещение в метрах по длине ноги; «на месте» — снимается медленный дрейф, остаётся покачивание.
Пальцы в мокапе не трогаются: остаются расслабленными (relax_hands).
"""
import math, os, json
import bpy
from mathutils import Matrix, Quaternion, Vector, Euler

# CMU (cgspeed) -> MPFB default
MAP = {
    'Hips': 'root', 'LowerBack': 'spine05', 'Spine': 'spine03', 'Spine1': 'spine01',
    'Neck': 'neck01', 'Neck1': 'neck02', 'Head': 'head',
    'LHipJoint': 'pelvis.L', 'LeftUpLeg': 'upperleg01.L', 'LeftLeg': 'lowerleg01.L', 'LeftFoot': 'foot.L',
    'RHipJoint': 'pelvis.R', 'RightUpLeg': 'upperleg01.R', 'RightLeg': 'lowerleg01.R', 'RightFoot': 'foot.R',
    'LeftShoulder': 'clavicle.L', 'LeftArm': 'upperarm01.L', 'LeftForeArm': 'lowerarm01.L', 'LeftHand': 'wrist.L',
    'RightShoulder': 'clavicle.R', 'RightArm': 'upperarm01.R', 'RightForeArm': 'lowerarm01.R', 'RightHand': 'wrist.R',
}
# BVH (Y вверх) -> Blender (Z вверх): x -> x, y -> z, z -> -y (как импорт BVH с forward=-Z, up=Y)
C = Matrix(((1, 0, 0), (0, 0, -1), (0, 1, 0)))
CT = C.transposed()

# клипы: id -> (вид, с какой секунды, сколько секунд)
CLIPS = {
    # ожидание/стоят
    '137_28': ('idle', 1.0, 12), '137_32': ('idle', 1.0, 12), '137_23': ('idle', 1.0, 12), '137_19': ('idle', 1.0, 12),
    '140_06': ('idle', 1.0, 12), '140_07': ('idle', 1.0, 6), '141_20': ('idle', 0.5, 4.5), '111_28': ('idle', 1.0, 10),
    '113_21': ('idle', 1.0, 8), '77_02': ('idle', 0.5, 5), '40_10': ('idle', 1.0, 12), '40_11': ('idle', 1.0, 12),
    # разговор, жесты
    '18_08': ('talk', 1.0, 12), '19_08': ('talk', 1.0, 12), '111_25': ('talk', 0.5, 6),
    # телефон
    '79_36': ('phone', 0.5, 8), '80_25': ('phone', 0.5, 8), '79_37': ('phone', 0.5, 8), '80_26': ('phone', 0.5, 8),
    # ходьба (с перемещением)
    '07_01': ('walk', 0.3, 6), '08_01': ('walk', 0.3, 6), '16_15': ('walk', 0.3, 6), '35_01': ('walk', 0.3, 6),
    '39_01': ('walk', 0.3, 6), '02_01': ('walk', 0.3, 6), '17_06': ('walk', 0.3, 6), '69_01': ('walk', 0.3, 6),
}


# ----------------------------------------------------------------------------- BVH
class Joint:
    __slots__ = ('name', 'parent', 'offset', 'channels', 'children', 'end')

    def __init__(self, name, parent):
        self.name, self.parent = name, parent
        self.offset = Vector((0, 0, 0)); self.channels = []; self.children = []; self.end = None


def read_bvh(path):
    tok = open(path, encoding='latin-1').read().split()
    i = 0
    joints, stack, cur = [], [], None
    while tok[i] != 'MOTION':
        t = tok[i]
        if t in ('ROOT', 'JOINT'):
            j = Joint(tok[i + 1], cur); joints.append(j)
            if cur:
                cur.children.append(j)
            cur = j; i += 2
        elif t == 'End':
            i += 2
            assert tok[i] == '{'
            assert tok[i + 1] == 'OFFSET'
            cur.end = Vector([float(x) for x in tok[i + 2:i + 5]])
            i += 6
        elif t == 'OFFSET':
            cur.offset = Vector([float(x) for x in tok[i + 1:i + 4]]); i += 4
        elif t == 'CHANNELS':
            n = int(tok[i + 1]); cur.channels = tok[i + 2:i + 2 + n]; i += 2 + n
        elif t == '}':
            cur = cur.parent if cur else None; i += 1
        else:
            i += 1
    i += 1
    nfr = int(tok[i + 1]); i += 2
    ft = float(tok[i + 2]); i += 3
    nch = sum(len(j.channels) for j in joints)
    vals = tok[i:i + nfr * nch]
    return joints, nfr, ft, nch, vals


def _local(j, v):
    """(позиция, матрица поворота) сустава в координатах BVH по значениям каналов."""
    R = Matrix.Identity(3)
    pos = None
    for c, x in zip(j.channels, v):
        if c.endswith('rotation'):
            R = R @ Matrix.Rotation(math.radians(x), 3, c[0])
        else:
            pos = pos or Vector((0, 0, 0))
            pos['XYZ'.index(c[0])] = x
    return pos, R


def bvh_frames(joints, nfr, nch, vals, idx):
    """для кадров idx: {name: мировой поворот (Blender)}, позиция Hips (Blender, единицы BVH)"""
    order = joints
    offs = []
    o = 0
    for j in joints:
        offs.append(o); o += len(j.channels)
    out = []
    for f in idx:
        base = f * nch
        G, P = {}, {}
        hips = None
        for k, j in enumerate(order):
            v = [float(x) for x in vals[base + offs[k]: base + offs[k] + len(j.channels)]]
            pos, R = _local(j, v)
            if j.parent is None:
                g = R
                p = (pos or Vector((0, 0, 0))) + j.offset
                hips = p
            else:
                gp = G[j.parent.name]
                g = gp @ R
                p = P[j.parent.name] + gp @ j.offset
            G[j.name] = g; P[j.name] = p
        out.append(({n: C @ g @ CT for n, g in G.items()}, C @ hips))
    return out


def bvh_rest_dirs(joints):
    """направление сегмента каждого сустава в покое (Blender): к первому ребёнку или к концу."""
    d = {}
    for j in joints:
        v = None
        for ch in j.children:
            if ch.offset.length > 1e-6:
                v = ch.offset; break
            for g in ch.children:          # нулевые суставы (Spine1, LeftHand): смотрим на внука
                if g.offset.length > 1e-6:
                    v = g.offset; break
            if v is not None:
                break
        if v is None and j.end is not None and j.end.length > 1e-6:
            v = j.end
        d[j.name] = (C @ v).normalized() if v is not None else None
    return d


def leg_len(joints):
    J = {j.name: j for j in joints}
    return J['LeftLeg'].offset.length + J['LeftFoot'].offset.length


# ----------------------------------------------------------------------------- риг MPFB
def _tpose_pose(rig, tpose):
    """матрицы костей (пространство рига) в T-позе MPFB и базисы T-позы."""
    bones = rig.data.bones
    basis = {}
    for b in bones:
        e = tpose['bone_rotations'].get(b.name)
        basis[b.name] = Euler(e, 'XYZ').to_matrix().to_4x4() if e else Matrix.Identity(4)
    P = {}
    for b in bones:                                   # bones идут от родителя к детям
        if b.parent is None:
            P[b.name] = b.matrix_local @ basis[b.name]
        else:
            rel = b.parent.matrix_local.inverted() @ b.matrix_local
            P[b.name] = P[b.parent.name] @ rel @ basis[b.name]
    return P, basis


def _seg_dir(rig, P, name):
    """направление сегмента нашей кости в T-позе: к голове следующей отображённой кости, иначе ось Y кости"""
    inv = {v: k for k, v in MAP.items()}
    b = rig.data.bones[name]
    q = [b]
    child = None
    while q and child is None:
        nxt = []
        for x in q:
            for c in x.children:
                if c.name in inv:
                    child = c; break
                nxt.append(c)
            if child:
                break
        q = nxt
    h = P[name].translation
    if child is not None and name not in ('root',):
        v = P[child.name].translation - h
        if v.length > 1e-5:
            return v.normalized()
    return (P[name].to_3x3() @ Vector((0, 1, 0))).normalized()


def _lowpass(vs, win):
    out = []
    n = len(vs)
    for i in range(n):
        a, b = max(0, i - win), min(n, i + win + 1)
        s = Vector((0, 0, 0))
        for k in range(a, b):
            s += vs[k]
        out.append(s / (b - a))
    return out


def retarget(rig, bvh_path, tpose, kind='idle', t0=1.0, length=8.0, fps=30, name=None):
    """вернуть Action для рига (кватернионы костей + смещение root относительно покоя)."""
    joints, nfr, ft, nch, vals = read_bvh(bvh_path)
    src_fps = 1.0 / ft
    t_end = min((nfr - 1) / src_fps, t0 + length)
    times = [t0 + k / fps for k in range(int((t_end - t0) * fps) + 1)]
    idx = [min(nfr - 1, int(round(t * src_fps))) for t in times]
    frames = bvh_frames(joints, nfr, nch, vals, idx)
    rest_dirs = bvh_rest_dirs(joints)
    P_T, basis_T = _tpose_pose(rig, tpose)
    bones = rig.data.bones
    inv = {v: k for k, v in MAP.items()}
    # выравнивание сегментов T-позы на сегменты CMU в покое
    A = {}
    for b in bones:
        if b.name not in inv:
            continue
        sd = rest_dirs.get(inv[b.name])
        if b.name == 'root' or sd is None:
            A[b.name] = Matrix.Identity(3)
            continue
        dd = _seg_dir(rig, P_T, b.name)
        A[b.name] = dd.rotation_difference(sd).to_matrix()
    # масштаб и курс
    s = 1.0
    try:
        ub = bones['upperleg01.L'].head_local; kb = bones['lowerleg01.L'].head_local; fb = bones['foot.L'].head_local
        s = ((kb - ub).length + (fb - kb).length) / leg_len(joints)
    except KeyError:
        pass
    hips = [h for (_, h) in frames]
    if kind == 'walk':
        d = hips[-1] - hips[0]; d.z = 0
        fwd = d.normalized() if d.length > 1e-3 else Vector((0, -1, 0))
    else:
        fwd = frames[0][0]['Hips'] @ Vector((0, -1, 0)); fwd.z = 0; fwd.normalize()
    yaw = math.atan2(fwd.x, -fwd.y)                   # курс относительно -Y (куда смотрит MakeHuman)
    Rz = Matrix.Rotation(-yaw, 3, 'Z')
    if kind == 'walk':
        loc = [Rz @ (h - hips[0]) for h in hips]
    else:
        lp = _lowpass(hips, int(fps * 1.2))
        loc = [Rz @ (h - m) for h, m in zip(hips, lp)]
    zs = sorted(h.z for h in hips)
    z_med = zs[len(zs) // 2]
    root_rest = bones['root'].matrix_local
    root_h = root_rest.translation
    # кадры -> базисы
    keys = {b.name: [] for b in bones if b.name in inv}
    lkeys = []
    prevq = {}
    for (G, hip), L in zip(frames, loc):
        Pp = {}
        for b in bones:
            rel = (b.parent.matrix_local.inverted() @ b.matrix_local) if b.parent else b.matrix_local
            base = (Pp[b.parent.name] @ rel) if b.parent else rel
            if b.name in inv:
                D = Rz @ G[inv[b.name]]
                Rdes = D @ A[b.name] @ P_T[b.name].to_3x3()
                Bq = (base.to_3x3().inverted() @ Rdes).to_quaternion()
                pq = prevq.get(b.name)
                if pq is not None and pq.dot(Bq) < 0:
                    Bq.negate()
                prevq[b.name] = Bq
                keys[b.name].append(Bq)
                M = base @ Bq.to_matrix().to_4x4()
                if b.name == 'root':
                    z = (hip.z - z_med) * s
                    want = Vector((root_h.x + L.x * s, root_h.y + L.y * s, root_h.z + z))
                    bl = root_rest.to_3x3().inverted() @ (want - root_h)
                    lkeys.append(bl)
                    M = Matrix.Translation(want - root_h) @ M
            else:
                M = base @ basis_T[b.name]
            Pp[b.name] = M
    # Action (слои/слоты Blender 5)
    act = bpy.data.actions.new(name or ('mc_' + os.path.splitext(os.path.basename(bvh_path))[0]))
    slot = act.slots.new(id_type='OBJECT', name='Rig')
    lay = act.layers.new('Layer')
    cb = lay.strips.new(type='KEYFRAME').channelbag(slot, ensure=True)
    n = len(frames)
    fr = list(range(1, n + 1))

    def put(path, i, vs):
        fc = cb.fcurves.new(data_path=path, index=i)
        fc.keyframe_points.add(n)
        co = []
        for f, v in zip(fr, vs):
            co += [f, v]
        fc.keyframe_points.foreach_set('co', co)
        for kp in fc.keyframe_points:
            kp.interpolation = 'LINEAR'
        fc.update()

    for bn, qs in keys.items():
        for i in range(4):
            put('pose.bones["%s"].rotation_quaternion' % bn, i, [q[i] for q in qs])
    for bn in tpose['bone_rotations']:            # неотображённые кости, которые T-поза поворачивает: держать как в расчёте
        if bn in inv or bn not in bones:
            continue
        q = basis_T[bn].to_quaternion()
        for i in range(4):
            put('pose.bones["%s"].rotation_quaternion' % bn, i, [q[i]] * n)
    for i in range(3):
        put('pose.bones["root"].location', i, [v[i] for v in lkeys])
    act['esk_kind'] = kind
    act['esk_frames'] = n
    act['esk_speed'] = ((loc[-1] - loc[0]).length * s / max(1e-3, (n - 1) / fps)) if kind == 'walk' else 0.0
    act.use_fake_user = True
    return act


# ----------------------------------------------------------------------------- в сценах
_ACTS = {}


def load_actions(path):
    if not _ACTS and os.path.exists(path):
        with bpy.data.libraries.load(path, link=False) as (src, dst):
            dst.actions = [a for a in src.actions if a.startswith('mc_')]
        for a in dst.actions:
            _ACTS[a.name] = a
    return _ACTS


def by_kind(kind):
    return [a for n, a in sorted(_ACTS.items()) if a.get('esk_kind') == kind]


def prep_rig(rig, act=None):
    names = set(MAP.values())
    if act is not None:
        from esk_mech import iter_fcurves
        for fc in iter_fcurves(act):
            if fc.data_path.endswith('rotation_quaternion'):
                names.add(fc.data_path.split('"')[1])
    for pb in rig.pose.bones:
        if pb.name in names:
            pb.rotation_mode = 'QUATERNION'


def play(rig, act, offset=0, skip=()):
    """проиграть клип на риге с кадра 1 - offset (NLA-полоска). skip: кости, которые не трогать (рука на поручне)."""
    if act is None or rig is None:
        return None
    if skip:
        act = act.copy()
        for lay in act.layers:
            for st in lay.strips:
                for cb in st.channelbags:
                    for fc in list(cb.fcurves):
                        if any('"%s"' % b in fc.data_path for b in skip):
                            cb.fcurves.remove(fc)
    prep_rig(rig, act)
    ad = rig.animation_data_create()
    tr = ad.nla_tracks.new()
    st = tr.strips.new(act.name, int(1 - offset), act)
    st.extrapolation = 'HOLD'
    st.blend_type = 'REPLACE'
    return st
