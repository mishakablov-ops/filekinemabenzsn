"""Shot recipes for «Эскалатор». Each function builds the scene for one shot and animates the camera.
Signature: fn(scene, dur_s, fps, shot_info) -> dict"""
import bpy, math
from mathutils import Vector
import esk_mech as E, esk_studio as S, esk_metro as MT

def ease(u, p=1.8):
    u = max(0.0, min(1.0, u))
    return u ** p / (u ** p + (1 - u) ** p) if 0 < u < 1 else u

def cam_move(sc, dur, fps, a, b, ta, tb, lens=(35, 35), name='Cam', step=1, dof=None):
    """camera from a->b looking from ta->tb, smooth ease, baked every frame (linear between bakes)"""
    cam = S.camera(a, ta, lens=lens[0], name=name)
    tgt = bpy.data.objects.new(name + 'Tgt', None); sc.collection.objects.link(tgt)
    con = cam.constraints.new('TRACK_TO'); con.target = tgt; con.track_axis = 'TRACK_NEGATIVE_Z'; con.up_axis = 'UP_Y'
    if dof:
        cam.data.dof.use_dof = True; cam.data.dof.focus_object = tgt; cam.data.dof.aperture_fstop = dof
    n = sc.frame_end
    for f in range(1, n + 1, step):
        u = ease((f - 1) / max(1, n - 1))
        cam.location = Vector(a).lerp(Vector(b), u); cam.keyframe_insert('location', frame=f)
        tgt.location = Vector(ta).lerp(Vector(tb), u); tgt.keyframe_insert('location', frame=f)
        cam.data.lens = lens[0] + (lens[1] - lens[0]) * u; cam.data.keyframe_insert('lens', frame=f)
    for ob in (cam, tgt, cam.data):
        ad = ob.animation_data
        if ad and ad.action:
            for fc in E.iter_fcurves(ad.action):
                for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'
    return cam

def studio_esk(sc, dur, fps, near_truss=True, s0=0.0, speed=0.75):
    esk = E.Escalator(rise=3.0)
    if not near_truss:
        bpy.data.objects.remove(esk.truss[-1])
    esk.animate(1, sc.frame_end, fps, speed=speed, s0=s0)
    S.world('#F3F1EE', 0.8); S.backdrop(center=(4, 0, 0)); S.lights(center=(4, 0, 1.5))
    return esk

# ----------------------------------------------------------------------------- studio cutaway shots
def S03(sc, dur, fps, info):      # «Эскалатор это одна длинная петля» - whole loop, side
    studio_esk(sc, dur, fps)
    cam_move(sc, dur, fps, (2.6, -13.5, 0.9), (3.8, -11.8, 1.3), (3.0, 0, 0.9), (3.6, 0, 1.0), lens=(30, 30))
    return {}

def S04(sc, dur, fps, info):      # «Ступени сцеплены цепью» - chain close-up on the incline
    studio_esk(sc, dur, fps, near_truss=False)
    cam_move(sc, dur, fps, (2.2, -1.7, 0.45), (3.3, -1.55, 0.95), (3.0, -0.5, 0.95), (4.0, -0.5, 1.5), lens=(40, 44), dof=4.0)
    return {}

def S05(sc, dur, fps, info):      # «наверху каждая ныряет вниз и едет обратно под тобой» - top sprocket
    studio_esk(sc, dur, fps, near_truss=False)
    cam_move(sc, dur, fps, (9.6, -2.6, 3.4), (9.2, -2.0, 2.5), (8.2, 0, 2.6), (8.3, 0, 2.3), lens=(30, 32))
    return {}

def S06(sc, dur, fps, info):      # «как наверху они становятся ровным полом?» - top landing from above
    studio_esk(sc, dur, fps)
    cam_move(sc, dur, fps, (5.0, -1.5, 5.6), (6.6, -1.1, 5.0), (5.6, 0, 3.1), (7.0, 0, 3.3), lens=(28, 30))
    return {}

def S08(sc, dur, fps, info):      # «по двум разным рельсам» - travel along the rails under the steps
    esk = studio_esk(sc, dur, fps, near_truss=False)
    P = esk.path
    a = Vector((1.6, -1.05, P.z_of(1.6) + 0.15)); b = Vector((3.6, -1.05, P.z_of(3.6) + 0.15))
    cam_move(sc, dur, fps, a, b, (2.6, -0.5, P.z_of(2.6) + 0.1), (4.6, -0.5, P.z_of(4.6) + 0.1), lens=(32, 32), dof=1.2)
    return {}

def S09(sc, dur, fps, info):      # «на подъёме рельсы расходятся, ступень встаёт лесенкой» - side x-ray of incline
    studio_esk(sc, dur, fps, near_truss=False)
    cam_move(sc, dur, fps, (2.4, -3.6, 1.2), (3.4, -3.3, 1.8), (2.6, 0, 1.1), (3.6, 0, 1.6), lens=(42, 46))
    return {}

def S10(sc, dur, fps, info):      # «у выхода они сходятся, ступени складываются в плоскую дорожку»
    studio_esk(sc, dur, fps, near_truss=False)
    cam_move(sc, dur, fps, (5.4, -3.4, 2.9), (6.8, -3.2, 3.3), (5.6, 0, 2.7), (7.0, 0, 3.0), lens=(40, 44))
    return {}

def S11(sc, dur, fps, info):      # «эта гребёнка входит в пазы ступени» - comb macro
    esk = studio_esk(sc, dur, fps)
    P = esk.path; z = P.rise + E.TREAD_Z
    x = P.x1 - 0.55
    cam_move(sc, dur, fps, (x - 0.55, -0.55, z + 0.32), (x - 0.35, -0.42, z + 0.18), (x, -0.1, z), (x + 0.02, -0.15, z), lens=(50, 60), dof=2.0)
    return {}

def S13(sc, dur, fps, info):      # «Поручень тянет тот же мотор» - machine room
    esk = studio_esk(sc, dur, fps, near_truss=False)
    P = esk.path
    cam_move(sc, dur, fps, (10.6, -2.3, 1.2), (9.9, -1.9, 1.7), (9.0, 0.3, 1.8), (8.8, 0.3, 2.1), lens=(30, 34))
    return {}

def S07(sc, dur, fps, info):      # «У каждой ступени две пары колёс» - one step, turntable, glowing wheels
    col = E.coll('Hero')
    Mx = E.materials()
    Mx['wheel_a'] = E.mat('EskWheelGlowA', '#39E46B', rough=0.4, emit=3.0)
    Mx['wheel_b'] = E.mat('EskWheelGlowB', '#FF9A1A', rough=0.4, emit=3.0)
    st = E.step_mesh('HeroStep', col, Mx)
    st.location = (0, 0, 0.6)
    n = sc.frame_end
    for f in range(1, n + 1):
        u = (f - 1) / max(1, n - 1)
        st.rotation_euler = (0, 0, math.radians(-35 + 70 * u)); st.keyframe_insert('rotation_euler', frame=f)
    S.world('#F3F1EE', 0.9); S.backdrop(center=(0, 0, 0), wall_y=2.0); S.lights(center=(0, 0, 0.8))
    cam_move(sc, dur, fps, (-0.3, -2.4, 1.45), (-0.2, -2.0, 1.25), (-0.15, 0, 0.75), (-0.15, 0, 0.75), lens=(40, 44), dof=2.2)
    return {}
