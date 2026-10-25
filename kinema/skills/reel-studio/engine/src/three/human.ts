/**
 * Procedural animation for the podezd characters (rigged by assets/models-src/podezd/chars/rig_chars.py, T-pose bind,
 * Mixamo-style bone names, facing +Z, character's left = +X). No clips: every frame the skeleton is reset to the bind
 * pose and rebuilt from a Pose — FK angles for hips / spine / neck in character space, two-bone IK for arms and legs,
 * hand orientation from finger + palm directions, a head look-at, and small life layers (breath, tremble, sobs) added
 * by the caller.
 */
import * as THREE from "three";
import { clone as cloneSkinned } from "three/examples/jsm/utils/SkeletonUtils.js";

export type V3 = [number, number, number];
const v = (a: V3 | THREE.Vector3) => (a instanceof THREE.Vector3 ? a.clone() : new THREE.Vector3(...a));
const X = new THREE.Vector3(1, 0, 0), Y = new THREE.Vector3(0, 1, 0), Z = new THREE.Vector3(0, 0, 1);

export type ArmGoal = {
  /** wrist target, character space (metres from the feet origin); with `rel`: offset from that joint in its bind frame */
  hand: V3;
  /** follow a joint (e.g. "Head"): hand / fingers / palm are given in that joint's bind frame and move with it */
  rel?: string;
  /** elbow points toward this character-space point */
  pole?: V3;
  /** direction the fingers point, character space */
  fingers?: V3;
  /** direction the palm faces, character space */
  palm?: V3;
};
export type LegGoal = { foot: V3; pole?: V3; /** toes pitch down (+) / up (-) rad */ toe?: number; /** foot yaw rad */ yaw?: number };
export type Pose = {
  pos: V3;
  yaw: number;
  /** hips: offset (character space) + rotation [pitch, roll, yaw] */
  hips?: { off?: V3; rot?: V3 };
  /** whole spine bend [pitch (+ forward), roll (+ toward the character's left), yaw], spread over Spine/Spine1/Spine2 */
  spine?: V3;
  /** clavicles: [lift, forward] rad */
  shoulders?: { L?: [number, number]; R?: [number, number] };
  neck?: V3;
  head?: V3;
  /** world point to look at, and how much (0..1) */
  look?: { at: V3; w?: number };
  arms?: { L?: ArmGoal; R?: ArmGoal };
  legs?: { L?: LegGoal; R?: LegGoal };
};

const BONES = ["Hips", "Spine", "Spine1", "Spine2", "Neck", "Head", "LeftShoulder", "LeftArm", "LeftForeArm", "LeftHand", "RightShoulder", "RightArm", "RightForeArm", "RightHand", "LeftUpLeg", "LeftLeg", "LeftFoot", "LeftToeBase", "RightUpLeg", "RightLeg", "RightFoot", "RightToeBase"];

export type Human = ReturnType<typeof createHuman>;
export function createHuman(src: THREE.Object3D, opts: { tint?: string; skin?: (m: THREE.MeshStandardMaterial) => void; selfShadow?: boolean } = {}) {
  const model = cloneSkinned(src);
  const root = new THREE.Group();
  root.add(model);
  const bones: Record<string, THREE.Bone> = {};
  model.traverse((o) => {
    if ((o as THREE.Bone).isBone && BONES.includes(o.name)) bones[o.name] = o as THREE.Bone;
    const m = o as THREE.SkinnedMesh;
    if (m.isMesh) {
      m.castShadow = true;
      m.receiveShadow = opts.selfShadow ?? true;
      m.frustumCulled = false;
      const mat = (m.material as THREE.MeshStandardMaterial).clone();
      if (opts.tint) mat.color = new THREE.Color(opts.tint);
      opts.skin?.(mat);
      m.material = mat;
    }
  });
  for (const n of BONES) if (!bones[n]) throw new Error("bone missing: " + n);
  root.updateMatrixWorld(true);
  const restQ: Record<string, THREE.Quaternion> = {}, restP: Record<string, THREE.Vector3> = {}, restChar: Record<string, THREE.Quaternion> = {};
  const rootInv = new THREE.Quaternion();
  for (const n of BONES) {
    restQ[n] = bones[n].quaternion.clone();
    restP[n] = bones[n].position.clone();
    restChar[n] = bones[n].getWorldQuaternion(new THREE.Quaternion()).premultiply(rootInv);
  }
  const wp = (n: string) => bones[n].getWorldPosition(new THREE.Vector3());
  const len = (a: string, b: string) => wp(a).distanceTo(wp(b));
  const L = {
    upArm: { L: len("LeftArm", "LeftForeArm"), R: len("RightArm", "RightForeArm") },
    foreArm: { L: len("LeftForeArm", "LeftHand"), R: len("RightForeArm", "RightHand") },
    thigh: { L: len("LeftUpLeg", "LeftLeg"), R: len("RightUpLeg", "RightLeg") },
    shin: { L: len("LeftLeg", "LeftFoot"), R: len("RightLeg", "RightFoot") },
  };
  const height = (() => {
    const b = new THREE.Box3().setFromObject(model);
    return b.max.y - b.min.y;
  })();
  // bind-pose joint positions in character space (for building poses relative to the body)
  const bind: Record<string, THREE.Vector3> = {};
  for (const n of BONES) bind[n] = wp(n);

  // ---------------------------------------------------------------- helpers
  const rootQ = () => root.getWorldQuaternion(new THREE.Quaternion());
  const toWorldDir = (d: THREE.Vector3) => d.clone().applyQuaternion(rootQ());
  const toWorld = (p: V3 | THREE.Vector3) => root.localToWorld(v(p));
  /** rotate a bone by a world-space rotation about its own pivot */
  const rotWorld = (b: THREE.Bone, R: THREE.Quaternion) => {
    b.parent!.updateWorldMatrix(true, false);
    const pw = b.parent!.getWorldQuaternion(new THREE.Quaternion());
    const bw = pw.clone().multiply(b.quaternion);
    b.quaternion.copy(pw.invert().multiply(R.clone().multiply(bw)));
    b.updateMatrixWorld(true);
  };
  /** rotate about a character-space axis */
  const rotChar = (n: string, axis: THREE.Vector3, ang: number) => {
    if (Math.abs(ang) < 1e-6) return;
    rotWorld(bones[n], new THREE.Quaternion().setFromAxisAngle(toWorldDir(axis).normalize(), ang));
  };
  const euler = (n: string, r?: V3, k = 1) => {
    if (!r) return;
    rotChar(n, Y, r[2] * k);
    rotChar(n, X, r[0] * k);
    rotChar(n, Z, -r[1] * k);
  };
  /** set a bone's world orientation */
  const setWorldQ = (b: THREE.Bone, q: THREE.Quaternion) => {
    b.parent!.updateWorldMatrix(true, false);
    const pw = b.parent!.getWorldQuaternion(new THREE.Quaternion());
    b.quaternion.copy(pw.invert().multiply(q));
    b.updateMatrixWorld(true);
  };
  /** aim bone `a` (whose child joint is `childName`) so the child joint lands at world point P */
  const aim = (a: string, childName: string, P: THREE.Vector3) => {
    const A = wp(a), C = wp(childName);
    const d0 = C.sub(A).normalize(), d1 = P.clone().sub(A).normalize();
    rotWorld(bones[a], new THREE.Quaternion().setFromUnitVectors(d0, d1));
  };
  const twoBone = (up: string, mid: string, end: string, l1: number, l2: number, Tw: THREE.Vector3, poleW: THREE.Vector3) => {
    const A = wp(up);
    const d = Tw.clone().sub(A);
    const dist = THREE.MathUtils.clamp(d.length(), Math.abs(l1 - l2) + 1e-3, l1 + l2 - 1e-4);
    const dir = d.normalize();
    const T = A.clone().addScaledVector(dir, dist);
    // elbow / knee position in the plane of A, T and the pole
    const cosA = (l1 * l1 + dist * dist - l2 * l2) / (2 * l1 * dist);
    const a = Math.acos(THREE.MathUtils.clamp(cosA, -1, 1));
    const pl = poleW.clone().sub(A);
    const side = pl.sub(dir.clone().multiplyScalar(pl.dot(dir))).normalize();
    if (side.lengthSq() < 1e-6) side.copy(toWorldDir(Z));
    const B = A.clone().addScaledVector(dir, Math.cos(a) * l1).addScaledVector(side, Math.sin(a) * l1);
    aim(up, mid, B);
    aim(mid, end, T);
  };
  /** orient a hand / foot: rest-basis (f0, n0 in character space at bind) -> (f, n) */
  const orient = (n: string, f0: THREE.Vector3, n0: THREE.Vector3, f: THREE.Vector3, nn: THREE.Vector3) => {
    const basis = (a: THREE.Vector3, b: THREE.Vector3) => {
      const x = a.clone().normalize();
      const z = b.clone().sub(x.clone().multiplyScalar(b.dot(x))).normalize();
      const y = z.clone().cross(x);
      return new THREE.Quaternion().setFromRotationMatrix(new THREE.Matrix4().makeBasis(x, y, z));
    };
    const R = basis(f, nn).multiply(basis(f0, n0).invert()); // character space
    const q = rootQ().multiply(R).multiply(restChar[n]);
    setWorldQ(bones[n], q);
  };

  // ---------------------------------------------------------------- pose
  const pose = (p: Pose) => {
    for (const n of BONES) {
      bones[n].quaternion.copy(restQ[n]);
      bones[n].position.copy(restP[n]);
    }
    root.position.set(...p.pos);
    root.rotation.set(0, p.yaw, 0);
    root.updateMatrixWorld(true);
    // hips: translate in character space
    if (p.hips?.off) {
      const hb = bones.Hips;
      const parentInv = hb.parent!.matrixWorld.clone().invert();
      const w0 = wp("Hips");
      const w1 = toWorld(new THREE.Vector3(...p.hips.off).add(root.worldToLocal(w0.clone())));
      hb.position.copy(w1.applyMatrix4(parentInv));
      hb.updateMatrixWorld(true);
    }
    euler("Hips", p.hips?.rot);
    if (p.spine) for (const n of ["Spine", "Spine1", "Spine2"]) euler(n, p.spine, 1 / 3);
    for (const s of ["L", "R"] as const) {
      const sh = p.shoulders?.[s];
      if (sh) {
        const n = s === "L" ? "LeftShoulder" : "RightShoulder";
        rotChar(n, Z, (s === "L" ? 1 : -1) * sh[0]);
        rotChar(n, Y, (s === "L" ? -1 : 1) * sh[1]);
      }
    }
    // legs
    for (const s of ["L", "R"] as const) {
      const g = p.legs?.[s];
      if (!g) continue;
      const side = s === "L" ? "Left" : "Right";
      const Tw = toWorld(g.foot);
      const pole = toWorld(g.pole ?? [s === "L" ? 0.1 : -0.1, 0.5, 1.5]);
      twoBone(side + "UpLeg", side + "Leg", side + "Foot", L.thigh[s], L.shin[s], Tw, pole);
      // foot: keep the bind orientation in character space (flat), plus yaw / toe pitch
      const R = new THREE.Quaternion().setFromEuler(new THREE.Euler(g.toe ?? 0, g.yaw ?? 0, 0, "YXZ"));
      setWorldQ(bones[side + "Foot"], rootQ().multiply(R).multiply(restChar[side + "Foot"]));
    }
    // spine 2 / neck / head before the arms (the arms hang from the chest)
    euler("Neck", p.neck);
    euler("Head", p.head);
    if (p.look) {
      const w = p.look.w ?? 1;
      const Tw = v(p.look.at);
      for (const [n, k] of [["Neck", 0.4], ["Head", 1]] as const) {
        const H = wp("Head");
        const fwd = Z.clone().applyQuaternion(bones.Head.getWorldQuaternion(new THREE.Quaternion()).multiply(restChar.Head.clone().invert()));
        const want = Tw.clone().sub(H).normalize();
        const R = new THREE.Quaternion().setFromUnitVectors(fwd, want);
        rotWorld(bones[n], new THREE.Quaternion().slerp(R, k * w));
      }
    }
    for (const s of ["L", "R"] as const) {
      const g = p.arms?.[s];
      if (!g) continue;
      const side = s === "L" ? "Left" : "Right";
      const sg = s === "L" ? 1 : -1;
      let Tw: THREE.Vector3, f = v(g.fingers ?? [sg, 0, 0]).normalize(), n = v(g.palm ?? [0, -1, 0]).normalize();
      if (g.rel) {
        // delta rotation of the joint since bind, in character space
        const D = rootQ().invert().multiply(bones[g.rel].getWorldQuaternion(new THREE.Quaternion())).multiply(restChar[g.rel].clone().invert());
        Tw = wp(g.rel).add(toWorldDir(v(g.hand).applyQuaternion(D)));
        f = f.applyQuaternion(D);
        n = n.applyQuaternion(D);
      } else Tw = toWorld(g.hand);
      const pole = toWorld(g.pole ?? [sg * 0.6, 0.6, -0.6]);
      twoBone(side + "Arm", side + "ForeArm", side + "Hand", L.upArm[s], L.foreArm[s], Tw, pole);
      if (g.fingers || g.palm) orient(side + "Hand", new THREE.Vector3(sg, 0, 0), new THREE.Vector3(0, -1, 0), f, n);
    }
    root.updateMatrixWorld(true);
  };
  /** world position of a joint now */
  const joint = (n: string) => wp(n);
  return { root, model, bones, bind, height, L, pose, joint, toWorld };
}

// ---------------------------------------------------------------- pose library (character space, built from the body's own size)
const lerp3 = (a: V3, b: V3, k: number): V3 => [a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k, a[2] + (b[2] - a[2]) * k];
export const mix3 = lerp3;
/** slow organic noise in [-1, 1] */
export const wob = (t: number, seed: number, hz = 0.3) => Math.sin(t * hz * 6.283 + seed) * 0.6 + Math.sin(t * hz * 2.71 * 6.283 + seed * 1.7) * 0.4;

/** standing, face to the corner, hands over the face, shoulders shaking with sobs */
export function poseCornerCry(h: Human, t: number, o: { pos: V3; yaw: number; sob?: number; sway?: number; lookAt?: V3; look?: number; handsDown?: number }): Pose {
  const H = h.height;
  const sob = (o.sob ?? 1) * Math.max(0, Math.sin(t * 7.1)) ** 6 * (0.5 + 0.5 * Math.sin(t * 0.9));
  const sway = (o.sway ?? 1) * wob(t, 1, 0.22);
  const face = (s: number): ArmGoal => ({
    rel: "Head",
    hand: [s * 0.045, -0.03 + sob * 0.01, 0.15],
    pole: [s * 0.45, H * 0.5, 0.1],
    fingers: [-s * 0.3, 0.92, 0.1],
    palm: [-s * 0.1, 0.0, -1],
  });
  const lk = o.look ?? 0, hd = o.handsDown ?? lk;
  const hang = (s: number): ArmGoal => ({ hand: [s * 0.2, H * 0.47, 0.06], pole: [s * 0.6, H * 0.6, -0.6], fingers: [0, -1, 0.1], palm: [-s, 0, 0] });
  const arm = (s: number): ArmGoal => (hd >= 0.999 ? hang(s) : hd <= 0.001 ? face(s) : { ...hang(s), hand: mix3([s * 0.06, H * 0.8, 0.22], hang(s).hand, hd) });
  return {
    pos: o.pos,
    yaw: o.yaw + sway * 0.03,
    hips: { off: [sway * 0.02, -0.01, 0], rot: [0.04, sway * 0.03, 0] },
    spine: [(0.32 + sob * 0.05) * (1 - lk * 0.8), sway * 0.03, 0],
    shoulders: { L: [0.12 + sob * 0.12, 0.12], R: [0.12 + sob * 0.12, 0.12] },
    neck: [0.32 * (1 - lk), 0, 0],
    head: [(0.25 + sob * 0.06) * (1 - lk), 0, sway * 0.05],
    look: o.lookAt && lk > 0 ? { at: o.lookAt, w: lk } : undefined,
    arms: { L: arm(1), R: arm(-1) },
    legs: { L: { foot: [0.11, 0, 0.0] }, R: { foot: [-0.11, 0, 0.02] } },
  };
}

/** crouched in a corner, back to the walls, arms wrapped over the head, rocking */
export function poseCrouch(h: Human, t: number, o: { pos: V3; yaw: number; rock?: number }): Pose {
  const H = h.height;
  const rock = (o.rock ?? 1) * Math.sin(t * 2.4);
  const tr = 0.004 * Math.sin(t * 37);
  return {
    pos: o.pos,
    yaw: o.yaw,
    hips: { off: [0, -H * 0.36, -0.06], rot: [0.5 + rock * 0.06, 0, 0] },
    spine: [0.75 + rock * 0.08, 0, 0],
    shoulders: { L: [0.25, 0.35], R: [0.25, 0.35] },
    neck: [0.35, 0, 0],
    head: [0.35, tr * 10, 0],
    arms: {
      L: { rel: "Head", hand: [0.06, 0.1 + tr, -0.06], pole: [0.5, H * 0.4, 0.8], fingers: [-0.5, 0.2, -0.8], palm: [0, -0.8, -0.5] },
      R: { rel: "Head", hand: [-0.06, 0.12 - tr, -0.05], pole: [-0.5, H * 0.4, 0.8], fingers: [0.5, 0.2, -0.8], palm: [0, -0.8, -0.5] },
    },
    legs: { L: { foot: [0.15, 0, 0.18], pole: [0.4, 0.6, 1.2] }, R: { foot: [-0.15, 0, 0.2], pole: [-0.4, 0.6, 1.2] } },
  };
}

/** sitting on a stair step (seat height s above the feet origin), elbows on the knees, hands holding the head */
export function poseSitHoldHead(h: Human, t: number, o: { pos: V3; yaw: number; seat: number; feetDrop: number; lookUp?: number; lookAt?: V3 }): Pose {
  const H = h.height;
  const b = Math.sin(t * 1.6) * 0.012; // breathing / rocking
  const up = o.lookUp ?? 0;
  const hipY = o.seat + 0.09 - h.bind.Hips.y;
  const headDown = 0.55 * (1 - up);
  return {
    pos: o.pos,
    yaw: o.yaw,
    hips: { off: [0, hipY, -0.05], rot: [0.15, 0, 0] },
    spine: [0.65 * (1 - up * 0.6) + b, 0, 0],
    shoulders: { L: [0.1, 0.25], R: [0.1, 0.25] },
    neck: [headDown * 0.6, 0, 0],
    head: [headDown * 0.6, 0, 0],
    look: o.lookAt && up > 0 ? { at: o.lookAt, w: up } : undefined,
    arms: {
      L: { rel: "Head", hand: [0.1, -0.05, 0.02], pole: [0.45, 0.1, 0.7], fingers: [-0.15, 0.95, 0.2], palm: [-1, 0, 0.05] },
      R: { rel: "Head", hand: [-0.1, -0.05, 0.02], pole: [-0.45, 0.1, 0.7], fingers: [0.15, 0.95, 0.2], palm: [1, 0, 0.05] },
    },
    legs: {
      L: { foot: [0.14, -o.feetDrop, 0.5], pole: [0.3, 1.0, 1.5] },
      R: { foot: [-0.14, -o.feetDrop, 0.47], pole: [-0.3, 1.0, 1.5] },
    },
  };
}

/** sitting on the floor, knees up, hunched; hands over the face (lower = 0) sliding down to the knees (lower = 1) */
export function poseFloorCover(h: Human, t: number, o: { pos: V3; yaw: number; lower?: number; sob?: number; headTurn?: number }): Pose {
  const H = h.height;
  const k = o.lower ?? 0;
  const sob = (o.sob ?? 1) * (1 - k) * Math.max(0, Math.sin(t * 6.3)) ** 6;
  const b = Math.sin(t * 1.1) * 0.01;
  const onFace = (s: number): ArmGoal => ({ rel: "Head", hand: [s * 0.05, -0.04, 0.16], pole: [s * 0.6, H * 0.25, 0.4], fingers: [-s * 0.3, 0.92, 0.1], palm: [-s * 0.1, 0, -1] });
  const down = (s: number): ArmGoal => ({ hand: [s * 0.2, H * 0.2, H * 0.24], pole: [s * 0.7, H * 0.3, 0.1], fingers: [s * 0.1, -0.6, 0.8], palm: [-s * 0.3, -0.8, 0] });
  const arm = (s: number): ArmGoal => {
    const a = onFace(s), d = down(s);
    if (k <= 0) return a;
    if (k >= 1) return d;
    // blend in character space via the face position at this moment: approximate the face point
    const face: V3 = [s * 0.05, H * 0.62 - k * 0.0, H * 0.2];
    return { hand: mix3(face, d.hand, k), pole: d.pole, fingers: mix3(a.fingers!, d.fingers!, k), palm: mix3([-s * 0.1, 0, -1], d.palm!, k) };
  };
  return {
    pos: o.pos,
    yaw: o.yaw,
    hips: { off: [0, 0.13 - h.bind.Hips.y, -0.05], rot: [-0.25, 0, 0] },
    spine: [0.95 + sob * 0.08 + b - k * 0.15, 0, 0],
    shoulders: { L: [0.15 + sob * 0.1, 0.3], R: [0.15 + sob * 0.1, 0.3] },
    neck: [0.45 - k * 0.2, 0, (o.headTurn ?? 0) * 0.4],
    head: [0.35 - k * 0.15, 0, (o.headTurn ?? 0) * 0.6],
    arms: { L: arm(1), R: arm(-1) },
    legs: { L: { foot: [0.22, 0.0, H * 0.3], pole: [0.5, H * 0.5, 1.5] }, R: { foot: [-0.22, 0.0, H * 0.31], pole: [-0.5, H * 0.5, 1.5] } },
  };
}

/** sitting on a chair (seat height above the feet), hands on the desk in front */
export function poseChair(h: Human, t: number, o: { pos: V3; yaw: number; seat?: number; desk?: number; lookAt?: V3; look?: number; handL?: V3; handR?: V3 }): Pose {
  const H = h.height;
  const seat = o.seat ?? 0.46;
  const desk = o.desk ?? 0.77;
  const b = Math.sin(t * 1.3) * 0.006;
  return {
    pos: o.pos,
    yaw: o.yaw,
    hips: { off: [0, seat + 0.08 - h.bind.Hips.y, -0.12], rot: [0.05, 0, 0] },
    spine: [0.22 + b, 0, 0],
    neck: [0.1, 0, 0],
    head: [0.05, 0, 0],
    look: o.lookAt ? { at: o.lookAt, w: o.look ?? 1 } : undefined,
    arms: {
      L: { hand: o.handL ?? [0.17, desk + 0.03, 0.42], pole: [0.6, 0.5, -0.3], fingers: [-0.2, -0.05, 1], palm: [0, -1, 0] },
      R: { hand: o.handR ?? [-0.17, desk + 0.03, 0.4], pole: [-0.6, 0.5, -0.3], fingers: [0.2, -0.05, 1], palm: [0, -1, 0] },
    },
    legs: { L: { foot: [0.13, 0, 0.42], pole: [0.2, 0.5, 1.5] }, R: { foot: [-0.13, 0, 0.44], pole: [-0.2, 0.5, 1.5] } },
  };
  void H;
}

/** standing, pointing with the right arm at a world point (character-space direction from the shoulder is computed by the caller) */
export function posePoint(h: Human, t: number, o: { pos: V3; yaw: number; dir: V3; amount?: number; lean?: number }): Pose {
  const H = h.height;
  const k = o.amount ?? 1;
  const sh = h.bind.RightArm;
  const d = new THREE.Vector3(...o.dir).normalize();
  const reach = (h.L.upArm.R + h.L.foreArm.R) * 0.97;
  const rest: V3 = [-0.22, H * 0.5, 0.05];
  const tip: V3 = [sh.x + d.x * reach, sh.y + d.y * reach - (o.lean ?? 0) * 0.15, sh.z + d.z * reach + (o.lean ?? 0) * 0.15];
  const tr = 0.004 * Math.sin(t * 29);
  return {
    pos: o.pos,
    yaw: o.yaw,
    spine: [0.12 + (o.lean ?? 0) * 0.3, 0, 0],
    head: [0.15, 0, 0],
    arms: {
      R: { hand: mix3(rest, [tip[0], tip[1] + tr, tip[2]], k), pole: [-0.6, H * 0.5, -0.3], fingers: [d.x, d.y, d.z], palm: [0.2, -0.4, -0.1] },
      L: { hand: [0.24, H * 0.49, 0.04], pole: [0.6, H * 0.6, -0.5], fingers: [0.1, -1, 0.1], palm: [-1, 0, 0] },
    },
    legs: { L: { foot: [0.11, 0, 0.02] }, R: { foot: [-0.11, 0, 0.0] } },
  };
}

/** walking from `a` to `b` (world floor points, metres) at `speed` m/s starting at t0; stops at b and stands.
 *  Feet are planted on the floor step by step (no sliding); hips bob and sway; arms swing against the legs. */
export function poseWalk(h: Human, t: number, o: { a: V3; b: V3; t0?: number; speed?: number; step?: number; lookAt?: V3; look?: number }): Pose {
  const H = h.height;
  const A = new THREE.Vector3(...o.a), B = new THREE.Vector3(...o.b);
  const dirV = B.clone().sub(A);
  const L = dirV.length();
  dirV.normalize();
  const yaw = Math.atan2(dirV.x, dirV.z);
  const side = new THREE.Vector3(dirV.z, 0, -dirV.x); // character's left
  const step = o.step ?? 0.55, speed = o.speed ?? 0.65;
  const d = Math.min(L, Math.max(0, (t - (o.t0 ?? 0)) * speed));
  const moving = d > 0 && d < L;
  const root = A.clone().addScaledVector(dirV, d);
  const plant = (j: number) => {
    const s = j % 2 === 0 ? 1 : -1; // even steps: left foot
    return A.clone().addScaledVector(dirV, Math.min(L, Math.max(0, j * step))).addScaledVector(side, s * 0.1);
  };
  const i = Math.floor(d / step), u = (d - i * step) / step;
  const feet: Record<"L" | "R", THREE.Vector3> = { L: new THREE.Vector3(), R: new THREE.Vector3() };
  let bob = 0, sway = 0, swing = 0;
  if (moving) {
    const movingSide: "L" | "R" = (i + 1) % 2 === 0 ? "L" : "R";
    const planted: "L" | "R" = movingSide === "L" ? "R" : "L";
    const from = plant(i - 1), to = plant(i + 1);
    feet[movingSide] = from.clone().lerp(to, u).add(new THREE.Vector3(0, Math.sin(Math.PI * u) * 0.09, 0));
    feet[planted] = plant(i);
    bob = -0.035 + 0.035 * Math.abs(Math.cos(Math.PI * u));
    sway = (planted === "L" ? 1 : -1) * 0.025 * Math.sin(Math.PI * u);
    swing = (movingSide === "L" ? 1 : -1) * Math.sin(Math.PI * u);
  } else {
    feet.L = root.clone().addScaledVector(side, 0.11);
    feet.R = root.clone().addScaledVector(side, -0.11);
  }
  const toChar = (p: THREE.Vector3): V3 => {
    const q = p.clone().sub(root).applyAxisAngle(new THREE.Vector3(0, 1, 0), -yaw);
    return [q.x, q.y, q.z];
  };
  return {
    pos: [root.x, root.y, root.z],
    yaw,
    hips: { off: [sway, bob, 0], rot: [0.03, sway * 2, swing * 0.06] },
    spine: [0.06, -sway * 1.5, -swing * 0.08],
    head: [0.02, 0, 0],
    look: o.lookAt ? { at: o.lookAt, w: o.look ?? 1 } : undefined,
    arms: {
      L: { hand: [0.2, H * 0.48, 0.02 - swing * 0.16], pole: [0.6, H * 0.6, -0.6], fingers: [0, -1, 0.1], palm: [-1, 0, 0] },
      R: { hand: [-0.2, H * 0.48, 0.02 + swing * 0.16], pole: [-0.6, H * 0.6, -0.6], fingers: [0, -1, 0.1], palm: [1, 0, 0] },
    },
    legs: { L: { foot: toChar(feet.L), pole: [0.15, 0.6, 1.5] }, R: { foot: toChar(feet.R), pole: [-0.15, 0.6, 1.5] } },
  };
}

/** standing still, the right hand rising toward the ceiling (k = 0 down .. 1 straight up) */
export function poseRaise(h: Human, t: number, o: { pos: V3; yaw: number; k: number; lookAt?: V3 }): Pose {
  const H = h.height;
  const sh = h.bind.RightArm;
  const reach = h.L.upArm.R + h.L.foreArm.R;
  const down: V3 = [-0.2, H * 0.48, 0.03];
  const up: V3 = [sh.x - 0.04, sh.y + reach * 0.97, sh.z + 0.08];
  const k = Math.min(1, Math.max(0, o.k));
  const b = Math.sin(t * 1.5) * 0.01;
  return {
    pos: o.pos,
    yaw: o.yaw,
    spine: [0.02 - k * 0.06 + b, 0, 0],
    head: [-0.25 * k, 0, 0],
    look: o.lookAt ? { at: o.lookAt, w: 0.8 } : undefined,
    arms: {
      R: { hand: mix3(down, up, k), pole: [-0.7, H * 0.5, -0.3], fingers: mix3([0, -1, 0.1], [0, 1, 0.1], k), palm: mix3([1, 0, 0], [0, 0, 1], k) },
      L: { hand: [0.2, H * 0.48, 0.03], pole: [0.6, H * 0.6, -0.6], fingers: [0, -1, 0.1], palm: [-1, 0, 0] },
    },
    legs: { L: { foot: [0.11, 0, 0.0] }, R: { foot: [-0.11, 0, 0.0] } },
  };
}
