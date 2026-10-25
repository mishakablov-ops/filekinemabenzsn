/**
 * Mixamo-animated soldiers (soldier_mx_kpa.glb / soldier_mx_rok.glb + soldier_mx_clips.json).
 *
 * A soldier plays a PROGRAM: { start, yaw, segs: [{ clip, at, ... }] }. The horizontal root motion was taken out of
 * every clip in Blender and stored as a track; here the soldier is moved exactly along that track (rotated by the
 * segment's yaw), so feet never slide. Loops accumulate their travel; segments crossfade; a clip that really turns
 * (|Δyaw| > 90°, e.g. run_turn) hands its new heading to the next segment. Everything is a pure function of time.
 *
 * Clips: rifle_run, run_to_stop, run_turn, fire, aim_idle, rifle_idle, yell, crawl, pull, pull_low, kneel.
 */
import * as THREE from "three";
import { clone as cloneSkeleton } from "three/examples/jsm/utils/SkeletonUtils.js";

export type V3 = [number, number, number];
export type ClipMeta = { frames: number; fps: number; duration: number; loop: boolean; track: [number, number][]; yaw0: number; yaw1: number; hipsY0: number };
export type Seg = {
  clip: string; at: number; // seconds (program time)
  rate?: number; fade?: number; // playback speed, crossfade in (s)
  yaw?: number; // absolute heading for this segment (default: carried over)
  offset?: number; // start this many seconds into the clip
  shift?: [number, number]; // extra move at the start of this segment, in its own frame (x right?, z forward), blended in by the fade
  rifle?: boolean; // rifle in the hands (default: true for rifle clips)
};
export type Program = { start: V3; yaw: number; segs: Seg[] };

const RIFLE_CLIPS = new Set(["rifle_run", "run_to_stop", "run_turn", "fire", "aim_idle", "rifle_idle"]);
const smooth = (x: number) => {
  const u = Math.min(1, Math.max(0, x));
  return u * u * (3 - 2 * u);
};

/** root travel (clip-local, metres, +Z forward) after tau seconds of playing the clip */
export function clipTravel(m: ClipMeta, tau: number): [number, number] {
  const n = m.track.length;
  const at = (s: number): [number, number] => {
    const f = Math.min(n - 1, Math.max(0, s * m.fps));
    const i = Math.floor(f), k = f - i;
    const a = m.track[i], b = m.track[Math.min(n - 1, i + 1)];
    return [a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k];
  };
  if (!m.loop) return at(Math.min(tau, m.duration));
  const cycles = Math.floor(tau / m.duration);
  const w = at(tau - cycles * m.duration);
  const end = m.track[n - 1];
  return [end[0] * cycles + w[0], end[1] * cycles + w[1]];
}
const rot = (yaw: number, p: [number, number]): [number, number] => [p[0] * Math.cos(yaw) + p[1] * Math.sin(yaw), -p[0] * Math.sin(yaw) + p[1] * Math.cos(yaw)];

/** origin and heading of every segment of a program (cumulative root motion) */
export function layout(prog: Program, meta: Record<string, ClipMeta>) {
  const out: { seg: Seg; T: number; end: number; origin: [number, number]; yaw: number }[] = [];
  let origin: [number, number] = [prog.start[0], prog.start[2]];
  let yaw = prog.yaw;
  prog.segs.forEach((s, i) => {
    if (s.yaw !== undefined) yaw = s.yaw;
    if (s.shift) {
      const d = rot(yaw, s.shift);
      origin = [origin[0] + d[0], origin[1] + d[1]];
    }
    const end = i + 1 < prog.segs.length ? prog.segs[i + 1].at : Infinity;
    out.push({ seg: s, T: s.at, end, origin: [...origin] as [number, number], yaw });
    if (end < Infinity) {
      const m = meta[s.clip];
      const tau = (end - s.at) * (s.rate ?? 1) + (s.offset ?? 0);
      const d = rot(yaw, clipTravel(m, tau));
      const d0 = rot(yaw, clipTravel(m, s.offset ?? 0));
      origin = [origin[0] + d[0] - d0[0], origin[1] + d[1] - d0[1]];
      const turn = m.yaw1 - m.yaw0;
      if (Math.abs(turn) > Math.PI / 2 && tau >= m.duration * 0.98) yaw += turn;
    }
  });
  return out;
}

export function createMxSoldier(gltf: { scene: THREE.Object3D; animations: THREE.AnimationClip[] }, meta: Record<string, ClipMeta>) {
  const root = new THREE.Group();
  const model = cloneSkeleton(gltf.scene);
  root.add(model);
  model.traverse((o) => {
    const m = o as THREE.SkinnedMesh;
    if (m.isMesh) {
      m.castShadow = true;
      m.receiveShadow = true;
      m.frustumCulled = false;
    }
  });
  const bone = (part: string) => {
    let found: THREE.Object3D | null = null;
    model.traverse((o) => {
      if (!found && (o as THREE.Bone).isBone && o.name.replace(/^mixamorig:?/, "") === part) found = o;
    });
    return found as THREE.Object3D | null;
  };
  const B = {
    hips: bone("Hips")!, head: bone("Head")!, rHand: bone("RightHand")!, lHand: bone("LeftHand")!,
    rMid: bone("RightHandMiddle1"), lMid: bone("LeftHandMiddle1"), lFoot: bone("LeftFoot")!, rFoot: bone("RightFoot")!,
    lToe: bone("LeftToeBase"), rToe: bone("RightToeBase"),
  };
  const mixer = new THREE.AnimationMixer(model);
  const clips = new Map(gltf.animations.map((c) => [c.name, c]));

  /** pose the soldier for program time t; returns world root position/yaw and whether a rifle is held */
  function pose(prog: Program, t: number, ground = 0) {
    const lay = layout(prog, meta);
    let i = lay.length - 1;
    while (i > 0 && t < lay[i].T) i--;
    const parts: { l: (typeof lay)[number]; w: number }[] = [];
    const cur = lay[i];
    const fade = cur.seg.fade ?? 0.22;
    const w = i > 0 ? smooth((t - cur.T) / fade) : 1;
    parts.push({ l: cur, w });
    if (w < 1 && i > 0) parts.push({ l: lay[i - 1], w: 1 - w });
    mixer.stopAllAction();
    let px = 0, pz = 0, sx = 0, sz = 0, rifle = 0;
    for (const { l, w: wt } of parts) {
      const m = meta[l.seg.clip];
      const clip = clips.get(l.seg.clip);
      if (!m || !clip) throw new Error("soldier clip missing: " + l.seg.clip);
      const tau = Math.max(0, (t - l.T) * (l.seg.rate ?? 1) + (l.seg.offset ?? 0));
      const a = mixer.clipAction(clip);
      a.reset();
      a.setLoop(m.loop ? THREE.LoopRepeat : THREE.LoopOnce, Infinity);
      a.clampWhenFinished = true;
      a.play();
      a.time = m.loop ? tau % m.duration : Math.min(tau, m.duration - 1e-4);
      a.setEffectiveWeight(wt);
      const d = rot(l.yaw, clipTravel(m, tau));
      const d0 = rot(l.yaw, clipTravel(m, l.seg.offset ?? 0));
      px += (l.origin[0] + d[0] - d0[0]) * wt;
      pz += (l.origin[1] + d[1] - d0[1]) * wt;
      sx += Math.sin(l.yaw) * wt;
      sz += Math.cos(l.yaw) * wt;
      if (l.seg.rifle ?? RIFLE_CLIPS.has(l.seg.clip)) rifle += wt;
    }
    mixer.update(0);
    const yaw = Math.atan2(sx, sz);
    root.position.set(px, ground, pz);
    root.rotation.set(0, yaw, 0);
    root.updateMatrixWorld(true);
    // blending two clips can push a foot below the ground: lift the soldier by exactly that much
    const sink = footY() - ground;
    if (sink < 0) {
      root.position.y -= sink;
      root.updateMatrixWorld(true);
    }
    return { x: px, z: pz, yaw, rifle: rifle > 0.5 };
  }

  const wp = (o: THREE.Object3D | null) => (o ? o.getWorldPosition(new THREE.Vector3()) : new THREE.Vector3());
  const wq = (o: THREE.Object3D) => o.getWorldQuaternion(new THREE.Quaternion());
  const gripPoint = () => wp(B.rHand).lerp(B.rMid ? wp(B.rMid) : wp(B.rHand), 0.7);
  // The rifle is fixed to the right hand like a game weapon socket. The socket offset is calibrated once on the
  // aiming pose (aim_idle, facing +Z): there the barrel points straight ahead (2° down) with its top up.
  const socket = (() => {
    const aim = meta.aim_idle ? { start: [0, 0, 0] as V3, yaw: 0, segs: [{ clip: "aim_idle", at: 0 }] } : null;
    if (!aim) return null;
    pose(aim, 0.5);
    const z = new THREE.Vector3(0, -Math.sin(0.035), 1).normalize();
    const x = new THREE.Vector3(0, 1, 0).cross(z).normalize();
    const y = z.clone().cross(x).normalize();
    const want = new THREE.Quaternion().setFromRotationMatrix(new THREE.Matrix4().makeBasis(x, y, z));
    const hq = wq(B.rHand);
    const inv = hq.clone().invert();
    return { q: inv.clone().multiply(want), p: gripPoint().sub(wp(B.rHand)).addScaledVector(y, 0.02).applyQuaternion(inv) };
  })();
  // per-arm data for IK: lengths and the hand frame (fingers / palm) in the hand bone's local space
  const armOf = (s: "Left" | "Right") => {
    const arm = bone(`${s}Arm`)!, fore = bone(`${s}ForeArm`)!, hand = bone(`${s}Hand`)!;
    const mid = bone(`${s}HandMiddle1`), idx = bone(`${s}HandIndex1`), pnk = bone(`${s}HandPinky1`);
    const f = wp(mid ?? hand).sub(wp(hand)).normalize();
    let p = idx && pnk ? f.clone().cross(wp(idx).sub(wp(pnk))).normalize() : new THREE.Vector3(0, -1, 0);
    if (s === "Right") p.negate(); // mirrored hand: keep "palm" pointing out of the palm on both sides
    const inv = wq(hand).invert();
    return { arm, fore, hand, f: f.applyQuaternion(inv), p: p.applyQuaternion(inv), l1: wp(arm).distanceTo(wp(fore)), l2: wp(fore).distanceTo(wp(hand)) };
  };
  const ARM = { L: armOf("Left"), R: armOf("Right") };
  const setWorldQ = (b: THREE.Object3D, q: THREE.Quaternion) => {
    b.quaternion.copy(wq(b.parent!).invert().multiply(q));
    b.updateMatrixWorld(true);
  };
  const aimBone = (b: THREE.Object3D, child: THREE.Object3D, goal: THREE.Vector3) => {
    const from = wp(b);
    const q = new THREE.Quaternion().setFromUnitVectors(wp(child).sub(from).normalize(), goal.clone().sub(from).normalize());
    setWorldQ(b, q.multiply(wq(b)));
  };
  const basis = (f: THREE.Vector3, p: THREE.Vector3) => {
    const x = f.clone().normalize();
    const y = p.clone().addScaledVector(x, -p.dot(x)).normalize();
    return new THREE.Matrix4().makeBasis(x, y, x.clone().cross(y));
  };
  /** two-bone IK of one arm to a wrist point, elbow towards `pole` (world), then the hand turned to fingers/palm */
  function reach(s: "L" | "R", wrist: THREE.Vector3, pole: THREE.Vector3, fingers: THREE.Vector3, palm: THREE.Vector3, w = 1) {
    const a = ARM[s];
    const target = wp(a.hand).lerp(wrist, w);
    const A = wp(a.arm);
    const raw = target.clone().sub(A);
    const d = Math.min(Math.max(raw.length(), Math.abs(a.l1 - a.l2) + 1e-3), a.l1 + a.l2 - 1e-3);
    const axis = raw.normalize();
    const side = pole.clone().addScaledVector(axis, -pole.dot(axis)).normalize();
    const along = (a.l1 * a.l1 - a.l2 * a.l2 + d * d) / (2 * d);
    const h = Math.sqrt(Math.max(0, a.l1 * a.l1 - along * along));
    aimBone(a.arm, a.fore, A.clone().addScaledVector(axis, along).addScaledVector(side, h));
    aimBone(a.fore, a.hand, A.clone().addScaledVector(axis, d));
    const cur = wq(a.hand);
    const rel = new THREE.Quaternion().setFromRotationMatrix(basis(fingers, palm).multiply(basis(a.f.clone().applyQuaternion(cur), a.p.clone().applyQuaternion(cur)).invert()));
    setWorldQ(a.hand, rel.multiply(cur).slerp(cur, 1 - w));
  }
  /**
   * Put the rifle (soldier.ts makeRifle: origin = grip, +Z muzzle) in the hands.
   *  socket mode (running, idling): fixed to the right hand as Mixamo intended, the left hand pulled onto the handguard;
   *  shoulder mode (aim / fire): butt in the right shoulder pocket, barrel at `target`, both hands placed by IK
   *  (the Mixamo aim pose on this character lifts the hands too high). recoil 0..1 kicks it back and up.
   */
  function holdRifle(rifle: THREE.Object3D, o: { shoulder?: boolean; target?: THREE.Vector3; recoil?: number; support?: number } = {}) {
    if (!socket) return;
    const rq = wq(root);
    const fwdC = new THREE.Vector3(0, 0, 1).applyQuaternion(rq);
    const rightC = new THREE.Vector3(-1, 0, 0).applyQuaternion(rq); // character's right
    if (o.shoulder) {
      const head = wp(B.head), sh = wp(ARM.R.arm);
      const dir = (o.target ? o.target.clone().sub(head) : fwdC.clone()).normalize();
      const right = dir.clone().cross(new THREE.Vector3(0, 1, 0)).normalize(); // rifle's right side
      const r = o.recoil ?? 0;
      const kick = dir.clone().applyAxisAngle(right, -0.06 * r);
      const z = kick.normalize();
      const x = new THREE.Vector3(0, 1, 0).cross(z).normalize();
      const y = z.clone().cross(x).normalize();
      rifle.quaternion.setFromRotationMatrix(new THREE.Matrix4().makeBasis(x, y, z));
      // butt (local z = -0.33) in the shoulder pocket: a little inside the joint, sights near the cheek
      const butt = sh.clone().addScaledVector(rightC, -0.06).addScaledVector(fwdC, 0.05 - 0.04 * r).add(new THREE.Vector3(0, 0.05, 0));
      rifle.position.copy(butt).sub(new THREE.Vector3(0, 0, -0.33).applyQuaternion(rifle.quaternion));
      rifle.updateMatrixWorld(true);
      const ax = (a: number, b: number, c: number) => new THREE.Vector3(a, b, c).applyQuaternion(rifle.quaternion);
      // right hand on the pistol grip: wrist behind and below it, fingers wrapping forward-down, palm towards the grip (rifle -X)
      const gripW = new THREE.Vector3(0, -0.05, 0.0).applyMatrix4(rifle.matrixWorld);
      reach("R", gripW.clone().addScaledVector(ax(0, 0, 1), -0.05).addScaledVector(ax(1, 0, 0), 0.035), rightC.clone().multiplyScalar(1).add(new THREE.Vector3(0, -0.6, 0)), ax(-0.25, -0.75, 0.6), ax(-1, 0, 0));
    } else {
      const hq = wq(B.rHand);
      rifle.quaternion.copy(hq).multiply(socket.q);
      rifle.position.copy(wp(B.rHand)).add(socket.p.clone().applyQuaternion(hq));
      rifle.updateMatrixWorld(true);
    }
    const support = o.support ?? 1;
    if (support > 0) {
      const ax = (a: number, b: number, c: number) => new THREE.Vector3(a, b, c).applyQuaternion(rifle.quaternion);
      const palmPt = new THREE.Vector3(0, -0.045, 0.3).applyMatrix4(rifle.matrixWorld);
      // left wrist behind the palm centre; fingers point across the rifle (its -X), palm up into the handguard
      const wrist = palmPt.clone().addScaledVector(ax(-1, 0, 0), -0.07).addScaledVector(ax(0, -1, 0), 0.015);
      reach("L", wrist, rightC.clone().negate().add(new THREE.Vector3(0, -1.1, 0)).addScaledVector(fwdC, -0.2), ax(-1, 0, 0.25), ax(0, 1, 0), support);
    }
    root.updateMatrixWorld(true);
  }
  /** lowest point of the feet (for the "feet on the ground" check) */
  function footY() {
    return Math.min(wp(B.lFoot).y, wp(B.rFoot).y, B.lToe ? wp(B.lToe).y : 9, B.rToe ? wp(B.rToe).y : 9);
  }
  return { root, model, mixer, pose, holdRifle, footY, bones: B };
}
