/**
 * First-person hands that move like a person filmed with a head camera.
 *
 * Asset: models/fp_arms.glb (shared; CC BY 4.0 "Fps arms" by DJMaesen, modified — see models/CREDITS.md) (bones Left/Right Arm, ForeArm, ForeArmTwist, Hand, Hand<Finger>0..3).
 * Root space = camera space: +X right, +Y up, -Z forward, metres. Put the root on the camera every frame.
 *
 * Authoring: one track of keys per hand. A key starts a move at `t` and arrives after `dur` (auto from distance).
 *   to:    [x,y,z] in camera space | "rest" (hangs below the frame = hand not in shot) | (t) => V3 | Grip
 *   aim:   { fingers, palm } directions in camera space (how the hand is held) — preferred over raw rotations
 *   pose:  a POSES name or partial curls; contact: true when the hand holds something (no drift, no lag)
 *   osc:   rhythmic swing on top (running arms), arc: lift of the path (0.12 default)
 * Motion is minimum-jerk along an arc with a small overshoot, the hand pre-opens before a grasp and the fingers
 * close one after another; breathing, micro-tremor and lag behind head turns are added on top.
 * Everything is a pure function of time, so any frame renders the same in any order.
 */
import * as THREE from "three";
import { clone as cloneSkeleton } from "three/examples/jsm/utils/SkeletonUtils.js";

export type V3 = [number, number, number];
export type Side = "L" | "R";
export type Curl = { thumb: number; index: number; middle: number; ring: number; pinky: number; spread: number; oppose: number };
export type Aim = { fingers: V3; palm: V3 };
export type Grip = { p: V3; aim?: Aim };
export type HandTarget = V3 | "rest" | ((t: number) => V3 | Grip);
export type HandKey = {
  t: number; to: HandTarget; aim?: Aim; pose?: string | Partial<Curl>; dur?: number; arc?: number; contact?: boolean;
  pole?: V3; osc?: { hz: number; amp: V3; phase?: number };
};
export type HandTrack = HandKey[];

const FINGERS = ["Thumb", "Index", "Middle", "Ring", "Pinky"] as const;
const LONG = ["Index", "Middle", "Ring", "Pinky"] as const;
const CURL_KEYS = ["thumb", "index", "middle", "ring", "pinky"] as const;

export const POSES: Record<string, Curl> = {
  relaxed: { thumb: 0.15, index: 0.2, middle: 0.26, ring: 0.3, pinky: 0.34, spread: 0.12, oppose: 0.1 },
  open: { thumb: -0.1, index: -0.08, middle: -0.06, ring: -0.06, pinky: -0.04, spread: 0.6, oppose: -0.2 },
  flat: { thumb: 0, index: 0, middle: 0, ring: 0, pinky: 0, spread: 0.1, oppose: 0 },
  grip: { thumb: 0.5, index: 0.68, middle: 0.74, ring: 0.78, pinky: 0.82, spread: -0.05, oppose: 0.55 }, // around a bar: lever, rail
  wheel: { thumb: 0.08, index: 0.7, middle: 0.77, ring: 0.8, pinky: 0.84, spread: -0.04, oppose: 0.22 }, // steering wheel: thumb rests along the rim
  fist: { thumb: 0.75, index: 1, middle: 1, ring: 1, pinky: 1, spread: -0.12, oppose: 0.9 },
  cup: { thumb: 0.32, index: 0.42, middle: 0.46, ring: 0.5, pinky: 0.55, spread: 0, oppose: 0.7 }, // round mug / bottle
  pinch: { thumb: 0.45, index: 0.5, middle: 0.65, ring: 0.75, pinky: 0.8, spread: -0.05, oppose: 0.8 }, // key, small item
  point: { thumb: 0.5, index: 0, middle: 0.9, ring: 0.95, pinky: 1, spread: 0, oppose: 0.7 },
  claw: { thumb: 0.15, index: 0.35, middle: 0.38, ring: 0.4, pinky: 0.42, spread: 0.55, oppose: 0 }, // tense, bracing, falling
  limp: { thumb: 0.2, index: 0.3, middle: 0.38, ring: 0.45, pinky: 0.5, spread: 0.18, oppose: 0.15 },
};

const D = Math.PI / 180;
const clamp = (x: number, a = 0, b = 1) => Math.min(b, Math.max(a, x));
/** human reaching velocity profile (bell-shaped speed) */
export const minJerk = (u: number) => {
  const x = clamp(u);
  return x * x * x * (10 + x * (-15 + 6 * x));
};
const v3 = (a: V3) => new THREE.Vector3(a[0], a[1], a[2]);
const lerp3 = (a: V3, b: V3, k: number): V3 => [a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k, a[2] + (b[2] - a[2]) * k];
const restPos = (s: Side): V3 => [s === "L" ? -0.26 : 0.26, -0.64, -0.2];
const asCurl = (p: string | Partial<Curl> | undefined, base: Curl): Curl =>
  typeof p === "string" ? POSES[p] ?? base : p ? { ...base, ...p } : base;

type State = { pos: V3; aim: Aim | null; curl: Curl; contact: number; osc: { hz: number; amp: V3; phase: number; w: number } | null; pole?: V3 };

export type FPRig = ReturnType<typeof createFPRig>;

export function createFPRig(gltfScene: THREE.Object3D) {
  const root = new THREE.Group();
  root.name = "fp_hands";
  const scene = cloneSkeleton(gltfScene);
  root.add(scene);
  root.updateMatrixWorld(true);
  const bones: Record<string, THREE.Bone> = {};
  const meshes: THREE.SkinnedMesh[] = [];
  scene.traverse((o) => {
    if ((o as THREE.Bone).isBone) bones[o.name] = o as THREE.Bone;
    const m = o as THREE.SkinnedMesh;
    if (m.isSkinnedMesh) {
      m.frustumCulled = false;
      m.castShadow = true;
      m.receiveShadow = true;
      meshes.push(m);
    }
  });
  const P = (s: Side) => (s === "L" ? "Left" : "Right");
  for (const s of ["L", "R"] as Side[]) for (const n of ["Arm", "ForeArm", "Hand", "ForeArmTwist"]) if (!bones[P(s) + n]) throw new Error("fp_arms: missing bone " + P(s) + n);
  const rest: Record<string, { p: THREE.Vector3; q: THREE.Quaternion }> = {};
  for (const [n, b] of Object.entries(bones)) rest[n] = { p: b.position.clone(), q: b.quaternion.clone() };
  const wpos = (n: string) => bones[n].getWorldPosition(new THREE.Vector3());
  const wquat = (n: string) => bones[n].getWorldQuaternion(new THREE.Quaternion());

  // rest-frame geometry of each hand (root space == world space here, the root is at the origin)
  const geo = {} as Record<Side, {
    bindHand: THREE.Quaternion; handInFore: THREE.Quaternion; lengths: [number, number]; fingersDir: THREE.Vector3; palmDir: THREE.Vector3;
    axis: Record<string, THREE.Vector3>; spreadAxis: Record<string, THREE.Vector3>; opposeAxis: THREE.Vector3;
  }>;
  for (const s of ["L", "R"] as Side[]) {
    const p = P(s);
    const flex = new THREE.Vector3();
    const dir = new THREE.Vector3();
    for (const f of LONG) {
      const a = wpos(`${p}Hand${f}1`), b = wpos(`${p}Hand${f}2`), c = wpos(`${p}Hand${f}3`);
      const d1 = b.clone().sub(a), d2 = c.clone().sub(b);
      flex.add(d1.clone().cross(d2)); // rest fingers are slightly curled towards the palm -> + rotation = flexion
      dir.add(d1.normalize());
    }
    flex.normalize();
    dir.normalize();
    const palm = flex.clone().cross(dir).normalize(); // where a flexing finger moves = palm side
    const ta = wpos(`${p}HandThumb1`), tb = wpos(`${p}HandThumb2`), tc = wpos(`${p}HandThumb3`);
    let tflex = tb.clone().sub(ta).cross(tc.clone().sub(tb));
    if (tflex.lengthSq() < 1e-12) tflex = flex.clone();
    tflex.normalize();
    const axis: Record<string, THREE.Vector3> = {};
    const spreadAxis: Record<string, THREE.Vector3> = {};
    for (const f of FINGERS)
      for (let j = 0; j <= 3; j++) {
        const n = `${p}Hand${f}${j}`;
        const inv = wquat(n).invert();
        axis[n] = (f === "Thumb" ? tflex : flex).clone().applyQuaternion(inv).normalize();
        spreadAxis[n] = palm.clone().applyQuaternion(inv).normalize();
      }
    const t0 = `${p}HandThumb0`;
    geo[s] = {
      bindHand: wquat(p + "Hand"),
      handInFore: wquat(p + "ForeArm").invert().multiply(wquat(p + "Hand")),
      lengths: [wpos(p + "Arm").distanceTo(wpos(p + "ForeArm")), wpos(p + "ForeArm").distanceTo(wpos(p + "Hand"))],
      fingersDir: dir, palmDir: palm, axis, spreadAxis,
      opposeAxis: dir.clone().applyQuaternion(wquat(t0).invert()).normalize(),
    };
  }

  const setWorldQ = (bone: THREE.Bone, q: THREE.Quaternion) => {
    const parentQ = bone.parent!.getWorldQuaternion(new THREE.Quaternion());
    bone.quaternion.copy(parentQ.invert().multiply(q));
    bone.updateMatrixWorld(true);
  };
  const aimBone = (bone: THREE.Bone, child: THREE.Bone, goal: THREE.Vector3) => {
    const from = bone.getWorldPosition(new THREE.Vector3());
    const cur = child.getWorldPosition(new THREE.Vector3()).sub(from).normalize();
    const want = goal.clone().sub(from).normalize();
    setWorldQ(bone, new THREE.Quaternion().setFromUnitVectors(cur, want).multiply(bone.getWorldQuaternion(new THREE.Quaternion())));
  };
  const frame = (f: THREE.Vector3, p: THREE.Vector3) => {
    const x = f.clone().normalize();
    const y = p.clone().addScaledVector(x, -p.dot(x)).normalize();
    const z = x.clone().cross(y);
    return new THREE.Matrix4().makeBasis(x, y, z);
  };

  /** two-bone IK to a wrist position (camera space) + hand orientation by finger/palm directions */
  function solveArm(s: Side, target: V3, aim: Aim | null, pole?: V3) {
    const p = P(s), g = geo[s];
    const arm = bones[p + "Arm"], fore = bones[p + "ForeArm"], hand = bones[p + "Hand"], twist = bones[p + "ForeArmTwist"];
    for (const b of [arm, fore, hand, twist]) {
      b.position.copy(rest[b.name].p);
      b.quaternion.copy(rest[b.name].q);
    }
    root.updateMatrixWorld(true);
    const goal = root.localToWorld(v3(target));
    const poleW = root.localToWorld(v3(pole ?? [s === "L" ? -0.55 : 0.55, -0.75, 0.05]));
    const a = arm.getWorldPosition(new THREE.Vector3());
    const raw = goal.clone().sub(a);
    const dist = raw.length();
    const axis = dist > 1e-9 ? raw.clone().divideScalar(dist) : new THREE.Vector3(0, 0, -1);
    const [l1, l2] = g.lengths.map((x) => x * root.getWorldScale(new THREE.Vector3()).x);
    const d = clamp(dist, Math.abs(l1 - l2) + 1e-4, l1 + l2 - 1e-4);
    const side = poleW.sub(a);
    side.addScaledVector(axis, -side.dot(axis));
    if (side.lengthSq() < 1e-10) side.set(0, -1, 0);
    side.normalize();
    const along = (l1 * l1 - l2 * l2 + d * d) / (2 * d);
    const h = Math.sqrt(Math.max(0, l1 * l1 - along * along));
    const elbow = a.clone().addScaledVector(axis, along).addScaledVector(side, h);
    aimBone(arm, fore, elbow);
    aimBone(fore, hand, a.clone().addScaledVector(axis, d));
    const rootQ = root.getWorldQuaternion(new THREE.Quaternion());
    let rel = new THREE.Quaternion();
    if (aim) {
      const m = frame(v3(aim.fingers), v3(aim.palm)).multiply(frame(g.fingersDir, g.palmDir).invert());
      rel = new THREE.Quaternion().setFromRotationMatrix(m);
    }
    const want = rootQ.clone().multiply(rel).multiply(g.bindHand);
    setWorldQ(hand, want);
    // share the wrist roll with the forearm twist bone (no candy-wrapper wrist): roll about the forearm's own +Y
    const relNow = fore.getWorldQuaternion(new THREE.Quaternion()).invert().multiply(want);
    const delta = relNow.multiply(g.handInFore.clone().invert());
    const roll = 2 * Math.atan2(delta.y, delta.w);
    const wrapped = Math.atan2(Math.sin(roll), Math.cos(roll));
    twist.quaternion.copy(rest[twist.name].q).multiply(new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0, 1, 0), clamp(wrapped * 0.55, -1.3, 1.3)));
    twist.updateMatrixWorld(true);
  }

  function setFingers(s: Side, c: Curl) {
    const p = P(s), g = geo[s];
    const spreadDeg: Record<string, number> = { Index: 9, Middle: 1, Ring: -6, Pinky: -13 };
    FINGERS.forEach((f, i) => {
      const v = c[CURL_KEYS[i]];
      const ang = f === "Thumb" ? [0, v * 30, v * 42, v * 55] : v >= 0 ? [0, v * 82, v * 100, v * 68] : [0, v * 18, v * 6, v * 6];
      for (let j = 0; j <= 3; j++) {
        const n = `${p}Hand${f}${j}`;
        const b = bones[n];
        if (!b) continue;
        const q = rest[n].q.clone();
        if (j === 1 && f !== "Thumb") q.multiply(new THREE.Quaternion().setFromAxisAngle(g.spreadAxis[n], spreadDeg[f] * c.spread * D * (s === "L" ? 1 : -1)));
        if (j === 0 && f === "Thumb") q.multiply(new THREE.Quaternion().setFromAxisAngle(g.opposeAxis, c.oppose * 32 * D * (s === "L" ? 1 : -1)));
        if (ang[j]) q.multiply(new THREE.Quaternion().setFromAxisAngle(g.axis[n], ang[j] * D));
        b.quaternion.copy(q);
      }
    });
  }

  // ---------------------------------------------------------------- performance: keys -> state at time t
  const restState = (s: Side): State => ({ pos: restPos(s), aim: null, curl: POSES.relaxed, contact: 0, osc: null });
  const resolve = (to: HandTarget, s: Side, t: number): Grip => {
    if (to === "rest") return { p: restPos(s) };
    if (typeof to === "function") {
      const r = to(t);
      return Array.isArray(r) ? { p: r } : r;
    }
    return { p: to };
  };
  function stateAt(track: HandTrack, s: Side, idx: number, t: number): State {
    if (idx < 0) return restState(s);
    const k = track[idx];
    if (t < k.t) return stateAt(track, s, idx - 1, t);
    const start = stateAt(track, s, idx - 1, k.t);
    const goal = resolve(k.to, s, t);
    const aimGoal = k.aim ?? goal.aim ?? (k.to === "rest" ? null : start.aim);
    const dist = Math.hypot(goal.p[0] - start.pos[0], goal.p[1] - start.pos[1], goal.p[2] - start.pos[2]);
    const dur = k.dur ?? 0.3 + 0.62 * Math.min(dist, 0.9);
    const u = clamp((t - k.t) / dur);
    const m = minJerk(u);
    // path: straight blend + arc lift + a small overshoot that settles back
    const dir = v3(goal.p).sub(v3(start.pos));
    const up = new THREE.Vector3(0, 1, 0).addScaledVector(dir.clone().normalize(), -(dir.y / (dir.length() || 1)));
    if (up.lengthSq() < 1e-6) up.set(s === "L" ? -1 : 1, 0, 0);
    up.normalize();
    const arc = (k.arc ?? (k.to === "rest" ? 0.05 : 0.12)) * dist * Math.sin(Math.PI * u);
    const over = k.to === "rest" ? 0 : 0.035 * Math.sin(Math.PI * clamp((u - 0.68) / 0.32));
    const pos = lerp3(start.pos, goal.p, m);
    pos[0] += up.x * arc + dir.x * over;
    pos[1] += up.y * arc + dir.y * over;
    pos[2] += up.z * arc + dir.z * over;
    // orientation: blend directions (wrist leads a little behind the travel)
    let aim: Aim | null = aimGoal;
    if (start.aim && aimGoal) {
      const w = minJerk(Math.pow(u, 0.85));
      aim = { fingers: lerp3(start.aim.fingers, aimGoal.fingers, w), palm: lerp3(start.aim.palm, aimGoal.palm, w) };
    } else if (!aimGoal) aim = start.aim && u < 1 ? start.aim : null;
    // fingers: pre-open during a reach for a grasp, then close one after another (index first)
    const target = asCurl(k.pose, k.to === "rest" ? POSES.relaxed : start.curl);
    const avg = (c: Curl) => (c.index + c.middle + c.ring + c.pinky) / 4;
    const grasp = avg(target) - avg(start.curl) > 0.2 ? 0.38 * Math.sin(Math.PI * clamp(u / 0.82)) : 0;
    const delay = { thumb: 0.07, index: 0, middle: 0.035, ring: 0.065, pinky: 0.095 };
    const curl = { ...target } as Curl;
    for (const key of CURL_KEYS) {
      const w = minJerk((u - 0.3 - delay[key]) / 0.62);
      curl[key] = start.curl[key] + (target[key] - start.curl[key]) * w - grasp * (key === "thumb" ? 0.5 : 1);
    }
    curl.spread = start.curl.spread + (target.spread - start.curl.spread) * m + grasp * 0.5;
    curl.oppose = start.curl.oppose + (target.oppose - start.curl.oppose) * m - grasp * 0.4;
    const contact = k.contact ? minJerk((u - 0.72) / 0.28) : start.contact * (1 - m);
    let osc = start.osc ? { ...start.osc, w: start.osc.w * (1 - minJerk(u / 0.35)) } : null;
    if (k.osc) osc = { hz: k.osc.hz, amp: k.osc.amp, phase: k.osc.phase ?? 0, w: minJerk(u / 0.45) };
    return { pos, aim, curl, contact, osc, pole: k.pole ?? start.pole };
  }

  const noise = (t: number, seed: number) =>
    Math.sin(t * 1.93 + seed) * 0.55 + Math.sin(t * 3.37 + seed * 2.1) * 0.3 + Math.sin(t * 5.71 + seed * 3.7) * 0.15;

  /**
   * Pose both hands for time t. camera: the three.js camera used for the frame (root is put on it).
   * motion: head angular velocity (rad/s, yaw/pitch) and vertical acceleration, for the hands' inertia.
   */
  function pose(t: number, camera: THREE.Camera, tracks: { L?: HandTrack; R?: HandTrack }, motion: { yaw?: number; pitch?: number; accY?: number } = {}) {
    root.position.copy(camera.position);
    root.quaternion.copy(camera.quaternion);
    root.updateMatrixWorld(true);
    for (const s of ["L", "R"] as Side[]) {
      const track = [...(tracks[s] ?? [])].sort((a, b) => a.t - b.t);
      const st = stateAt(track, s, track.length - 1, t);
      const seed = s === "L" ? 0.7 : 2.9;
      const free = 1 - st.contact;
      const life = 0.0024 * (0.15 + 0.85 * free);
      const pos: V3 = [
        st.pos[0] + noise(t, seed) * life - clamp((motion.yaw ?? 0) * 0.011, -0.02, 0.02) * free,
        st.pos[1] + noise(t, seed + 5) * life + Math.sin(t * Math.PI * 2 * 0.24) * 0.0016 - clamp((motion.pitch ?? 0) * 0.011 + (motion.accY ?? 0) * 0.0018, -0.02, 0.02) * free,
        st.pos[2] + noise(t, seed + 9) * life * 0.7,
      ];
      if (st.osc && st.osc.w > 0) {
        const ph = t * Math.PI * 2 * st.osc.hz + st.osc.phase;
        pos[0] += Math.sin(ph) * st.osc.amp[0] * st.osc.w;
        pos[1] += Math.sin(ph * 2) * st.osc.amp[1] * 0.35 * st.osc.w + Math.cos(ph) * st.osc.amp[1] * st.osc.w;
        pos[2] += Math.sin(ph) * st.osc.amp[2] * st.osc.w;
      }
      let aim = st.aim;
      if (aim) {
        const r = 0.02 * (0.2 + 0.8 * free);
        aim = { fingers: [aim.fingers[0] + noise(t, seed + 13) * r, aim.fingers[1] + noise(t, seed + 17) * r, aim.fingers[2]], palm: aim.palm };
      }
      solveArm(s, pos, aim, st.pole);
      const c = { ...st.curl };
      CURL_KEYS.forEach((k, i) => (c[k] += noise(t * 0.8, seed + 21 + i * 3.3) * 0.028 * (0.3 + 0.7 * free)));
      setFingers(s, c);
    }
    root.updateMatrixWorld(true);
    for (const m of meshes) m.skeleton.update();
  }

  /** where a held object goes this frame: wrist position, finger and palm directions (world space) */
  const handLocalDirs = {} as Record<Side, { f: THREE.Vector3; p: THREE.Vector3 }>;
  for (const s of ["L", "R"] as Side[]) {
    const inv = geo[s].bindHand.clone().invert();
    handLocalDirs[s] = { f: geo[s].fingersDir.clone().applyQuaternion(inv), p: geo[s].palmDir.clone().applyQuaternion(inv) };
  }
  function handFrame(s: Side) {
    const h = bones[P(s) + "Hand"];
    const q = h.getWorldQuaternion(new THREE.Quaternion());
    const fingers = handLocalDirs[s].f.clone().applyQuaternion(q).normalize();
    const palm = handLocalDirs[s].p.clone().applyQuaternion(q).normalize();
    return { wrist: h.getWorldPosition(new THREE.Vector3()), fingers, palm, thumb: palm.clone().cross(fingers).normalize() };
  }
  /** the grasp centre: between the palm and the curled middle phalanges — where a held object really is */
  function graspCentre(s: Side) {
    const fr = handFrame(s);
    const palm = fr.wrist.clone().addScaledVector(fr.fingers, 0.06).addScaledVector(fr.palm, 0.012);
    const tips = new THREE.Vector3();
    for (const f of ["Index", "Middle", "Ring"]) tips.add(bones[`${P(s)}Hand${f}2`].getWorldPosition(new THREE.Vector3()));
    tips.divideScalar(3);
    return { centre: palm.add(tips).multiplyScalar(0.5), fr };
  }
  /** put a held object in the hand. origin: where the object's origin sits relative to its grasped middle
   *  (a cup modelled with its origin at the bottom centre: origin = -halfHeight along its up axis) */
  function holdInHand(s: Side, obj: THREE.Object3D, o: { halfHeight?: number; spin?: number } = {}) {
    const { centre, fr } = graspCentre(s);
    let up = fr.thumb.clone();
    if (up.y < 0) up.negate();
    const fwd = fr.palm.clone().addScaledVector(up, -fr.palm.dot(up)).normalize();
    const m = new THREE.Matrix4().makeBasis(up.clone().cross(fwd).normalize(), up, fwd);
    obj.quaternion.setFromRotationMatrix(m);
    if (o.spin) obj.quaternion.multiply(new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0, 1, 0), o.spin));
    obj.position.copy(centre).addScaledVector(up, -(o.halfHeight ?? 0));
    obj.updateMatrixWorld(true);
  }

  return { root, bones, meshes, geo, pose, solveArm, setFingers, handFrame, graspCentre, holdInHand };
}

/** Wrist position + hand aim for holding a round bar (steering-wheel rim, lever), all in camera space.
 *  point: the spot on the bar; palm: where the palm faces (into the bar); fingersHint: roughly where straight fingers would point */
export function barGrip(point: THREE.Vector3, palm: THREE.Vector3, fingersHint: THREE.Vector3, opts: { back?: number; lift?: number } = {}): Grip {
  const pl = palm.clone().normalize();
  const fingers = fingersHint.clone().addScaledVector(pl, -fingersHint.dot(pl)).normalize();
  const wrist = point.clone().addScaledVector(fingers, -(opts.back ?? 0.075)).addScaledVector(pl, -(opts.lift ?? 0.034));
  return { p: wrist.toArray() as V3, aim: { fingers: fingers.toArray() as V3, palm: pl.toArray() as V3 } };
}
