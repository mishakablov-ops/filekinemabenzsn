/**
 * Procedural soldiers for the nk-escape reel: one humanoid rig (soldier_kpa.glb / soldier_rok.glb, bones named
 * Hips/Pelvis/Spine/Chest/Neck/Head, Left|Right Shoulder/Arm/ForeArm/Hand/UpLeg/Leg/Foot, fingers) driven by
 * pure functions of time: two-bone IK for legs and arms, a foot-planting gait (feet never slide or hover),
 * torso lean / bob, head look, finger curls, and a rifle in the hands.
 *
 * World units metres, +Y up. A soldier faces +Z at yaw 0.
 */
import * as THREE from "three";
import { clone as cloneSkeleton } from "three/examples/jsm/utils/SkeletonUtils.js";

export type V3 = [number, number, number];
const v3 = (a: V3) => new THREE.Vector3(a[0], a[1], a[2]);
const clamp = (x: number, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const smooth = (x: number) => {
  const u = clamp(x);
  return u * u * (3 - 2 * u);
};

// ------------------------------------------------------------------ rifle (AK pattern, real size), origin = pistol-grip top, +Z = muzzle
export function makeRifle() {
  const g = new THREE.Group();
  const metal = new THREE.MeshStandardMaterial({ color: "#2C2E2F", roughness: 0.45, metalness: 0.7 });
  const wood = new THREE.MeshStandardMaterial({ color: "#6B3F24", roughness: 0.6 });
  const add = (geo: THREE.BufferGeometry, m: THREE.Material, p: V3, r: V3 = [0, 0, 0]) => {
    const o = new THREE.Mesh(geo, m);
    o.position.set(...p);
    o.rotation.set(...r);
    o.castShadow = true;
    g.add(o);
    return o;
  };
  add(new THREE.BoxGeometry(0.05, 0.075, 0.3), metal, [0, 0.03, 0.08]); // receiver
  add(new THREE.CylinderGeometry(0.009, 0.009, 0.42, 10), metal, [0, 0.045, 0.43], [Math.PI / 2, 0, 0]); // barrel
  add(new THREE.CylinderGeometry(0.008, 0.008, 0.24, 8), metal, [0, 0.07, 0.36], [Math.PI / 2, 0, 0]); // gas tube
  add(new THREE.BoxGeometry(0.055, 0.06, 0.2), wood, [0, 0.035, 0.32]); // handguard
  add(new THREE.BoxGeometry(0.04, 0.09, 0.27), wood, [0, 0.0, -0.2], [-0.12, 0, 0]); // stock
  add(new THREE.BoxGeometry(0.03, 0.09, 0.035), wood, [0, -0.04, 0.0], [0.35, 0, 0]); // pistol grip
  add(new THREE.BoxGeometry(0.028, 0.12, 0.05), metal, [0, -0.04, 0.16], [-0.25, 0, 0]); // magazine (upper)
  add(new THREE.BoxGeometry(0.028, 0.09, 0.05), metal, [0, -0.13, 0.19], [-0.55, 0, 0]); // magazine (curve)
  add(new THREE.BoxGeometry(0.008, 0.03, 0.01), metal, [0, 0.07, 0.63]); // front sight
  const muzzle = new THREE.Object3D();
  muzzle.position.set(0, 0.045, 0.65);
  muzzle.name = "MUZZLE";
  g.add(muzzle);
  g.userData.grip = new THREE.Vector3(0, 0, 0); // right hand
  g.userData.fore = new THREE.Vector3(0, 0.02, 0.3); // left hand on the handguard
  g.userData.butt = new THREE.Vector3(0, 0.0, -0.33); // shoulder contact
  return g;
}

// ------------------------------------------------------------------ the rig
export type Pose = {
  pos: V3; // ground point under the pelvis
  yaw: number; // facing (rad, 0 = +Z)
  pelvis?: number; // pelvis height above `pos` (rest ~1.0)
  lean?: number; // torso pitch forward relative to the pelvis (rad)
  bodyPitch?: number; // whole body pitched forward about the pelvis (prone = PI/2)
  twist?: number; // chest twist (rad)
  feet: { L: V3; R: V3 }; // sole points on the ground (world); the ankle sits L.ankle above
  footYaw?: { L?: number; R?: number };
  hands: { L?: { p: V3; aim?: { fingers: V3; palm: V3 } }; R?: { p: V3; aim?: { fingers: V3; palm: V3 } } };
  curl?: { L?: number; R?: number }; // 0 open .. 1 fist
  look?: V3; // world point the head looks at
  knee?: { L?: V3; R?: V3 }; // knee pole directions (world)
  elbow?: { L?: V3; R?: V3 };
};

export type Soldier = ReturnType<typeof createSoldier>;

export function createSoldier(scene: THREE.Object3D) {
  const root = new THREE.Group();
  const model = cloneSkeleton(scene);
  root.add(model);
  root.updateMatrixWorld(true);
  const bones: Record<string, THREE.Bone> = {};
  model.traverse((o) => {
    if ((o as THREE.Bone).isBone) bones[o.name] = o as THREE.Bone;
    const m = o as THREE.SkinnedMesh;
    if (m.isSkinnedMesh) {
      m.frustumCulled = false;
      m.castShadow = true;
      m.receiveShadow = true;
    }
  });
  for (const n of ["Hips", "Pelvis", "Spine", "Chest", "Neck", "Head", "LeftUpLeg", "LeftLeg", "LeftFoot", "RightUpLeg", "RightLeg", "RightFoot", "LeftArm", "LeftForeArm", "LeftHand", "RightArm", "RightForeArm", "RightHand"])
    if (!bones[n]) throw new Error("soldier: missing bone " + n);
  const rest: Record<string, { p: THREE.Vector3; q: THREE.Quaternion; wq: THREE.Quaternion; wp: THREE.Vector3 }> = {};
  for (const [n, b] of Object.entries(bones))
    rest[n] = { p: b.position.clone(), q: b.quaternion.clone(), wq: b.getWorldQuaternion(new THREE.Quaternion()), wp: b.getWorldPosition(new THREE.Vector3()) };
  const len = (a: string, b: string) => rest[a].wp.distanceTo(rest[b].wp);
  const L = {
    thigh: len("LeftUpLeg", "LeftLeg"), shin: len("LeftLeg", "LeftFoot"),
    upper: len("LeftArm", "LeftForeArm"), fore: len("LeftForeArm", "LeftHand"),
    pelvis: rest.Pelvis.wp.y, ankle: rest.LeftFoot.wp.y, hipW: Math.abs(rest.LeftUpLeg.wp.x),
  };
  // hand frames (fingers / palm) at rest, like the first-person rig
  const handDirs = {} as Record<"L" | "R", { f: THREE.Vector3; p: THREE.Vector3 }>;
  const flexAxis: Record<string, THREE.Vector3> = {};
  for (const s of ["L", "R"] as const) {
    const P = s === "L" ? "Left" : "Right";
    const wrist = rest[P + "Hand"].wp;
    const mid = (bones[P + "HandMiddle1"] ? rest[P + "HandMiddle1"].wp : wrist.clone().add(new THREE.Vector3(0, -0.05, 0))).clone();
    const idx = bones[P + "HandIndex1"] ? rest[P + "HandIndex1"].wp : mid;
    const pnk = bones[P + "HandPinky1"] ? rest[P + "HandPinky1"].wp : mid;
    const f = mid.clone().sub(wrist).normalize();
    const across = idx.clone().sub(pnk).normalize();
    let p = f.clone().cross(across).normalize();
    // palm faces the body side in an A-pose: towards -x for the left hand, +x for the right
    if ((s === "L" && p.x > 0) || (s === "R" && p.x < 0)) p.negate();
    const inv = rest[P + "Hand"].wq.clone().invert();
    handDirs[s] = { f: f.clone().applyQuaternion(inv), p: p.clone().applyQuaternion(inv) };
    // flexion axis (rotating a finger about it moves the tip towards the palm), in each finger bone's local frame
    const flex = f.clone().cross(p).normalize();
    for (const fn of ["Index", "Middle", "Ring", "Pinky", "Thumb"])
      for (let j = 0; j <= 3; j++) {
        const n = `${P}Hand${fn}${j}`;
        if (bones[n]) flexAxis[n] = flex.clone().applyQuaternion(rest[n].wq.clone().invert()).normalize();
      }
  }

  const setWorldQ = (b: THREE.Bone, q: THREE.Quaternion) => {
    const pq = b.parent!.getWorldQuaternion(new THREE.Quaternion());
    b.quaternion.copy(pq.invert().multiply(q));
    b.updateMatrixWorld(true);
  };
  const aimBone = (b: THREE.Bone, child: THREE.Bone, goal: THREE.Vector3) => {
    const from = b.getWorldPosition(new THREE.Vector3());
    const cur = child.getWorldPosition(new THREE.Vector3()).sub(from).normalize();
    const want = goal.clone().sub(from).normalize();
    setWorldQ(b, new THREE.Quaternion().setFromUnitVectors(cur, want).multiply(b.getWorldQuaternion(new THREE.Quaternion())));
  };
  const twoBone = (a: THREE.Bone, b: THREE.Bone, c: THREE.Bone, target: THREE.Vector3, pole: THREE.Vector3, l1: number, l2: number) => {
    const A = a.getWorldPosition(new THREE.Vector3());
    const raw = target.clone().sub(A);
    const d = clamp(raw.length(), Math.abs(l1 - l2) + 1e-3, l1 + l2 - 1e-3);
    const axis = raw.normalize();
    const side = pole.clone().addScaledVector(axis, -pole.dot(axis));
    if (side.lengthSq() < 1e-8) side.set(0, 0, 1);
    side.normalize();
    const along = (l1 * l1 - l2 * l2 + d * d) / (2 * d);
    const h = Math.sqrt(Math.max(0, l1 * l1 - along * along));
    aimBone(a, b, A.clone().addScaledVector(axis, along).addScaledVector(side, h));
    aimBone(b, c, A.clone().addScaledVector(axis, d));
  };
  const frame = (f: THREE.Vector3, p: THREE.Vector3) => {
    const x = f.clone().normalize();
    const y = p.clone().addScaledVector(x, -p.dot(x)).normalize();
    return new THREE.Matrix4().makeBasis(x, y, x.clone().cross(y));
  };
  const curlFingers = (P: string, c: number) => {
    for (const f of ["Index", "Middle", "Ring", "Pinky"])
      for (let j = 1; j <= 3; j++) {
        const b = bones[`${P}Hand${f}${j}`];
        if (!b) continue;
        b.quaternion.copy(rest[b.name].q).multiply(new THREE.Quaternion().setFromAxisAngle(flexAxis[b.name], c * (j === 1 ? 1.35 : 1.5)));
      }
    for (let j = 1; j <= 3; j++) {
      const b = bones[`${P}HandThumb${j}`];
      if (b) b.quaternion.copy(rest[b.name].q).multiply(new THREE.Quaternion().setFromAxisAngle(flexAxis[b.name], c * 0.55));
    }
  };

  function pose(p: Pose) {
    for (const [n, b] of Object.entries(bones)) {
      b.position.copy(rest[n].p);
      b.quaternion.copy(rest[n].q);
    }
    root.position.set(0, 0, 0);
    root.quaternion.identity();
    root.updateMatrixWorld(true);
    const yawQ = new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0, 1, 0), p.yaw);
    const fwd = new THREE.Vector3(0, 0, 1).applyQuaternion(yawQ);
    const right = new THREE.Vector3(-1, 0, 0).applyQuaternion(yawQ);
    const pitchQ = new THREE.Quaternion().setFromAxisAngle(right, -(p.bodyPitch ?? 0));
    const leanQ = new THREE.Quaternion().setFromAxisAngle(right, -(p.lean ?? 0));
    const pelvisY = p.pelvis ?? L.pelvis;
    const anchor = v3(p.pos).add(new THREE.Vector3(0, pelvisY, 0));
    // whole body: facing + pitch, then shift so the pelvis joint (body centre) lands on the anchor
    root.quaternion.copy(pitchQ).multiply(yawQ);
    root.updateMatrixWorld(true);
    root.position.add(anchor.clone().sub(bones.Pelvis.getWorldPosition(new THREE.Vector3())));
    root.updateMatrixWorld(true);
    // torso lean and twist happen at the spine (its joint is at the body centre)
    setWorldQ(bones.Spine, leanQ.clone().multiply(bones.Spine.getWorldQuaternion(new THREE.Quaternion())));
    if (p.twist) {
      const up = new THREE.Vector3(0, 1, 0).applyQuaternion(pitchQ).applyQuaternion(leanQ);
      setWorldQ(bones.Chest, new THREE.Quaternion().setFromAxisAngle(up, p.twist).multiply(bones.Chest.getWorldQuaternion(new THREE.Quaternion())));
    }
    for (const s of ["L", "R"] as const) {
      const P = s === "L" ? "Left" : "Right";
      const knee = p.knee?.[s] ? v3(p.knee[s]!) : fwd.clone().add(new THREE.Vector3(0, 0.1, 0));
      twoBone(bones[P + "UpLeg"], bones[P + "Leg"], bones[P + "Foot"], v3(p.feet[s]).add(new THREE.Vector3(0, L.ankle, 0)), knee, L.thigh, L.shin);
      setWorldQ(bones[P + "Foot"], new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0, 1, 0), p.yaw + (p.footYaw?.[s] ?? 0)).multiply(rest[P + "Foot"].wq));
    }
    // arms
    for (const s of ["L", "R"] as const) {
      const h = p.hands[s];
      const P = s === "L" ? "Left" : "Right";
      if (h) {
        const elbow = p.elbow?.[s] ? v3(p.elbow[s]!) : new THREE.Vector3(0, -1, 0).addScaledVector(right, s === "L" ? -0.6 : 0.6).addScaledVector(fwd, -0.3);
        twoBone(bones[P + "Arm"], bones[P + "ForeArm"], bones[P + "Hand"], v3(h.p), elbow, L.upper, L.fore);
        if (h.aim) {
          const want = frame(v3(h.aim.fingers), v3(h.aim.palm));
          const restF = handDirs[s].f.clone().applyQuaternion(rest[P + "Hand"].wq);
          const restP = handDirs[s].p.clone().applyQuaternion(rest[P + "Hand"].wq);
          const rel = new THREE.Quaternion().setFromRotationMatrix(want.multiply(frame(restF, restP).invert()));
          setWorldQ(bones[P + "Hand"], rel.multiply(rest[P + "Hand"].wq.clone()));
        }
      }
      curlFingers(P, p.curl?.[s] ?? 0.25);
    }
    // head looks at a point (neck takes 40 %, head 60 %), clamped
    if (p.look) {
      const head = bones.Head;
      const hpw = head.getWorldPosition(new THREE.Vector3());
      const dir = v3(p.look).sub(hpw).normalize();
      const cur = new THREE.Vector3(0, 0, 1).applyQuaternion(head.getWorldQuaternion(new THREE.Quaternion()).multiply(rest.Head.wq.clone().invert()));
      const q = new THREE.Quaternion().setFromUnitVectors(cur, dir);
      const e = new THREE.Euler().setFromQuaternion(q, "YXZ");
      e.x = clamp(e.x, -0.7, 0.6);
      e.y = clamp(e.y, -1.2, 1.2);
      e.z = 0;
      const qq = new THREE.Quaternion().setFromEuler(e);
      const part = (k: number) => new THREE.Quaternion().slerp(qq, k);
      setWorldQ(bones.Neck, part(0.4).multiply(bones.Neck.getWorldQuaternion(new THREE.Quaternion())));
      setWorldQ(head, part(0.6).multiply(head.getWorldQuaternion(new THREE.Quaternion())));
    }
    root.updateMatrixWorld(true);
  }

  const handFrame = (s: "L" | "R") => {
    const b = bones[s === "L" ? "LeftHand" : "RightHand"];
    const q = b.getWorldQuaternion(new THREE.Quaternion());
    return { wrist: b.getWorldPosition(new THREE.Vector3()), fingers: handDirs[s].f.clone().applyQuaternion(q), palm: handDirs[s].p.clone().applyQuaternion(q) };
  };
  const world = (n: string) => bones[n].getWorldPosition(new THREE.Vector3());

  return { root, bones, L, pose, handFrame, world };
}

// ------------------------------------------------------------------ paths and the gait
export type PathKey = { t: number; p: [number, number] }; // XZ ground points with times
/** position, heading and travelled distance along a timed path (linear between keys, eased start/stop) */
export function pathAt(keys: PathKey[], t: number) {
  if (t <= keys[0].t) return { x: keys[0].p[0], z: keys[0].p[1], yaw: headingOf(keys, 0), dist: 0, speed: 0 };
  let dist = 0;
  for (let i = 0; i < keys.length - 1; i++) {
    const a = keys[i], b = keys[i + 1];
    const seg = Math.hypot(b.p[0] - a.p[0], b.p[1] - a.p[1]);
    if (t <= b.t) {
      const u = (t - a.t) / Math.max(1e-6, b.t - a.t);
      // ease in on the first segment, ease out on the last (no instant starts/stops)
      const first = i === 0, last = i === keys.length - 2;
      // speed rises from 0 to cruise on the first segment and falls back to 0 on the last, with no jumps at the joins
      let w = u;
      if (first && last) w = u * u * (3 - 2 * u);
      else if (first) w = u * u * (2 - u); // w'(0)=0, w'(1)=1
      else if (last) w = u + u * u - u * u * u; // w'(0)=1, w'(1)=0
      return { x: a.p[0] + (b.p[0] - a.p[0]) * w, z: a.p[1] + (b.p[1] - a.p[1]) * w, yaw: headingOf(keys, i), dist: dist + seg * w, speed: seg / Math.max(1e-6, b.t - a.t) };
    }
    dist += seg;
  }
  const l = keys[keys.length - 1];
  return { x: l.p[0], z: l.p[1], yaw: headingOf(keys, keys.length - 2), dist, speed: 0 };
}
function headingOf(keys: PathKey[], i: number) {
  const a = keys[Math.max(0, i)], b = keys[Math.min(keys.length - 1, i + 1)];
  return Math.atan2(b.p[0] - a.p[0], b.p[1] - a.p[1]);
}
/** point at a travelled distance along the path */
function pointAtDist(keys: PathKey[], d: number) {
  let acc = 0;
  for (let i = 0; i < keys.length - 1; i++) {
    const a = keys[i], b = keys[i + 1];
    const seg = Math.hypot(b.p[0] - a.p[0], b.p[1] - a.p[1]);
    if (d <= acc + seg || i === keys.length - 2) {
      const u = seg > 0 ? clamp((d - acc) / seg, 0, 1.5) : 0;
      return { x: a.p[0] + (b.p[0] - a.p[0]) * u, z: a.p[1] + (b.p[1] - a.p[1]) * u, yaw: Math.atan2(b.p[0] - a.p[0], b.p[1] - a.p[1]) };
    }
    acc += seg;
  }
  return { x: keys[0].p[0], z: keys[0].p[1], yaw: 0 };
}

/**
 * Running / walking feet that plant on the ground: each foot touches down at a fixed spot and stays there for the
 * stance part of the cycle, then swings in an arc to its next spot. When the path ends the feet finish their step
 * and settle side by side. ground(x,z) gives the surface height.
 */
export function gait(keys: PathKey[], t: number, o: { stride?: number; stance?: number; lift?: number; width?: number; ground?: (x: number, z: number) => number; endT?: number }) {
  const stride = o.stride ?? 2.4; // full cycle (two steps)
  const stance = o.stance ?? 0.38;
  const lift = o.lift ?? 0.18;
  const width = o.width ?? 0.12;
  const gy = o.ground ?? (() => 0);
  const cur = pathAt(keys, t);
  const res: { feet: { L: V3; R: V3 }; bob: number; phase: number } = { feet: { L: [0, 0, 0], R: [0, 0, 0] }, bob: 0, phase: 0 };
  const u = cur.dist / stride;
  res.phase = u;
  const plant = (k: number, off: number, side: number): V3 => {
    const d = Math.max(0, (k + off) * stride + stride * stance * 0.5);
    const q = pointAtDist(keys, d);
    const rx = -Math.cos(q.yaw) * side * width, rz = Math.sin(q.yaw) * side * width;
    return [q.x + rx, gy(q.x + rx, q.z + rz), q.z + rz];
  };
  const endT = o.endT ?? keys[keys.length - 1].t;
  const settle = smooth((t - endT + 0.05) / 0.3); // after the path ends: both feet to a calm stance
  for (const [s, off, side] of [["L", 0, 1], ["R", 0.5, -1]] as const) {
    const uu = u - off;
    const k = Math.floor(uu);
    const ph = uu - k;
    let p: V3;
    if (cur.dist <= 0.01 || ph < stance) p = plant(Math.max(k, -1), off, side);
    else {
      const a = plant(k, off, side), b = plant(k + 1, off, side);
      const w = smooth((ph - stance) / (1 - stance));
      p = [a[0] + (b[0] - a[0]) * w, a[1] + (b[1] - a[1]) * w + Math.sin(Math.PI * w) * lift, a[2] + (b[2] - a[2]) * w];
    }
    if (settle > 0) {
      const e = pathAt(keys, endT + 10);
      const rx = -Math.cos(e.yaw) * side * (width + 0.03), rz = Math.sin(e.yaw) * side * (width + 0.03);
      const fx = Math.sin(e.yaw) * (s === "L" ? 0.12 : -0.08), fz = Math.cos(e.yaw) * (s === "L" ? 0.12 : -0.08); // left foot a bit forward (shooting stance)
      const st: V3 = [e.x + rx + fx, gy(e.x + rx + fx, e.z + rz + fz), e.z + rz + fz];
      p = [p[0] + (st[0] - p[0]) * settle, p[1] + (st[1] - p[1]) * settle, p[2] + (st[2] - p[2]) * settle];
    }
    res.feet[s] = p;
  }
  res.bob = -Math.cos(u * Math.PI * 4) * 0.035 * (1 - settle) * clamp(cur.speed / 3, 0, 1);
  return res;
}

// ------------------------------------------------------------------ rifle handling helpers
/** rifle shouldered and aimed at `target`; returns both hand grips (world) for the arm IK */
export function aimRifle(sold: Soldier, rifle: THREE.Object3D, target: THREE.Vector3, o: { recoil?: number } = {}) {
  const sh = sold.world("RightArm");
  const head = sold.world("Head");
  const dir = target.clone().sub(head).normalize();
  const up = new THREE.Vector3(0, 1, 0);
  const side = dir.clone().cross(up).normalize(); // to the soldier's right
  const butt = sh.clone().addScaledVector(side, -0.07).addScaledVector(up, -0.02).addScaledVector(dir, 0.04 - (o.recoil ?? 0) * 0.05);
  const fwd = dir.clone().applyAxisAngle(side, (o.recoil ?? 0) * 0.08);
  orient(rifle, fwd);
  const buttLocal = (rifle.userData.butt as THREE.Vector3).clone().applyQuaternion(rifle.quaternion);
  rifle.position.copy(butt).sub(buttLocal);
  rifle.updateMatrixWorld(true);
  return rifleGrips(rifle);
}
/** rifle carried across the chest while running (port arms); swing = -1..1 with the stride */
export function carryRifle(sold: Soldier, rifle: THREE.Object3D, yaw: number, swing = 0) {
  const chest = sold.world("Chest");
  const fwd = new THREE.Vector3(Math.sin(yaw), 0, Math.cos(yaw));
  const right = new THREE.Vector3(-Math.cos(yaw), 0, Math.sin(yaw));
  const grip = chest.clone().addScaledVector(fwd, 0.26).addScaledVector(right, 0.13).add(new THREE.Vector3(0, -0.2 + swing * 0.02, 0));
  orient(rifle, fwd.clone().multiplyScalar(0.55).addScaledVector(right, -0.65).add(new THREE.Vector3(0, 0.5, 0)).normalize());
  rifle.position.copy(grip);
  rifle.updateMatrixWorld(true);
  return rifleGrips(rifle);
}
/** turn the rifle so its +Z (muzzle) points along dir, top up */
function orient(rifle: THREE.Object3D, dir: THREE.Vector3) {
  const z = dir.clone().normalize();
  const x = new THREE.Vector3(0, 1, 0).cross(z).normalize();
  const y = z.clone().cross(x).normalize();
  rifle.quaternion.setFromRotationMatrix(new THREE.Matrix4().makeBasis(x, y, z));
}
function rifleGrips(rifle: THREE.Object3D) {
  const w = (p: THREE.Vector3) => p.clone().applyMatrix4(rifle.matrixWorld);
  const ax = (x: number, y: number, z: number) => new THREE.Vector3(x, y, z).applyQuaternion(rifle.quaternion);
  return {
    R: { p: w(rifle.userData.grip).addScaledVector(ax(0, 1, 0), -0.03).addScaledVector(ax(1, 0, 0), 0.02).toArray() as V3, aim: { fingers: ax(-0.2, -0.75, 0.6).toArray() as V3, palm: ax(-1, 0, 0).toArray() as V3 } },
    L: { p: w(rifle.userData.fore).addScaledVector(ax(0, 1, 0), -0.06).addScaledVector(ax(1, 0, 0), -0.02).toArray() as V3, aim: { fingers: ax(0.7, 0.2, 0.6).toArray() as V3, palm: ax(0, 1, 0).toArray() as V3 } },
  };
}
