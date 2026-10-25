/**
 * The nk-escape reel: production scenes (first person + a few surveillance / drone shots).
 *
 * Every Panmunjom shot shares one CHASE CLOCK tau (seconds since he leaves the jeep): the defector's route, the KPA
 * squad, the shots and the hits are functions of tau, so the hook, the run, the UN camera and the fall show one world.
 * Scene blocks get `tau0` (tau at the scene's first frame); local time t is added to it.
 */
import React, { useMemo } from "react";
import { AbsoluteFill } from "remotion";
import * as THREE from "three";
import { useBlockTime } from "../core/context";
import { camAt, makeCamera, Stage3D, type Cam, type CamKey, type V3 } from "./core";
import { barGrip, createFPRig, type FPRig, type HandTrack } from "./fphands";
import { NkLook, OutdoorLights, smooth01, useClipMeta, useGLB, useJeep, useNkTextures } from "./nk";
import { BARRACKS_MARKS, box, buildBarracks, buildJSA, flagTower, JSA_MARKS, leafMaterialFrom, makeMat, plane, prepareFlag, tree, type Tex } from "./nkSets";
import { makeRifle } from "./soldier";
import { createMxSoldier, type ClipMeta, type Program } from "./soldierMx";

const M = "projects/nk-escape/models/";
const sm = smooth01;
const lerp = (a: number, b: number, k: number) => a + (b - a) * k;
type GLTFish = { scene: THREE.Object3D; animations: THREE.AnimationClip[] };

// ================================================================== effects
const texCache = new Map<string, THREE.Texture>();
/** radial gradient sprite texture */
function glow(key: string, stops: [number, string][]) {
  if (!texCache.has(key)) {
    const c = document.createElement("canvas");
    c.width = c.height = 128;
    const g = c.getContext("2d")!;
    const gr = g.createRadialGradient(64, 64, 0, 64, 64, 64);
    stops.forEach(([o, col]) => gr.addColorStop(o, col));
    g.fillStyle = gr;
    g.fillRect(0, 0, 128, 128);
    const t = new THREE.CanvasTexture(c);
    t.colorSpace = THREE.SRGBColorSpace;
    texCache.set(key, t);
  }
  return texCache.get(key)!;
}
const flashMat = () =>
  new THREE.SpriteMaterial({ map: glow("flash", [[0, "rgba(255,250,225,1)"], [0.25, "rgba(255,190,90,0.9)"], [0.6, "rgba(255,120,30,0.25)"], [1, "rgba(255,90,0,0)"]]), blending: THREE.AdditiveBlending, depthWrite: false, transparent: true });
const dustMat = () =>
  new THREE.SpriteMaterial({ map: glow("dust", [[0, "rgba(176,160,136,0.9)"], [0.5, "rgba(150,136,116,0.45)"], [1, "rgba(140,126,108,0)"]]), depthWrite: false, transparent: true });

/** dust kicked up by bullets: [tau, x, z] events -> sprites that pop, grow and settle */
function dustPuffs(events: [number, number, number][]) {
  const g = new THREE.Group();
  const sprites = events.map(() => {
    const s = new THREE.Sprite(dustMat());
    s.visible = false;
    g.add(s);
    return s;
  });
  const update = (tau: number) => {
    events.forEach(([t0, x, z], i) => {
      const a = tau - t0, s = sprites[i];
      s.visible = a >= 0 && a < 0.9;
      if (!s.visible) return;
      const k = sm(a / 0.25);
      s.position.set(x, 0.12 + 0.35 * k + a * 0.15, z);
      s.scale.setScalar(0.25 + 0.9 * sm(a / 0.6));
      (s.material as THREE.SpriteMaterial).opacity = (1 - sm((a - 0.2) / 0.7)) * 0.85;
    });
  };
  return { group: g, update };
}

// ================================================================== the chase clock (tau)
const ROUTE = [...JSA_MARKS.run.map(([x, z]) => new THREE.Vector3(x, 0, z)), JSA_MARKS.collapse.clone()];
const routeLen = ROUTE.slice(1).reduce((s, p, i) => s + p.distanceTo(ROUTE[i]), 0);
export const CHASE = { hit1: 4.56, hit2: 5.56, fall: 6.92, exit: 0 };
/** metres run at tau: accelerates out of the jeep, 5 m/s, slower after each hit, stops at the wall */
const runDist = (tau: number) => {
  let s = 0;
  const dt = 1 / 120;
  for (let t = 0; t < tau; t += dt) {
    const v = t < 0.6 ? (t / 0.6) * 5 : t < CHASE.hit1 ? 5 : t < CHASE.hit2 ? 3.4 : 1.9;
    s += v * Math.min(dt, tau - t);
  }
  return Math.min(s, routeLen);
};
const routeAt = (d: number) => {
  let acc = 0;
  for (let i = 1; i < ROUTE.length; i++) {
    const seg = ROUTE[i].distanceTo(ROUTE[i - 1]);
    if (d <= acc + seg || i === ROUTE.length - 1) {
      const k = Math.min(1, Math.max(0, (d - acc) / seg));
      const p = ROUTE[i - 1].clone().lerp(ROUTE[i], k);
      const dir = ROUTE[i].clone().sub(ROUTE[i - 1]).normalize();
      return { p, dir };
    }
    acc += seg;
  }
  return { p: ROUTE[ROUTE.length - 1].clone(), dir: new THREE.Vector3(0, 0, 1) };
};
/** the defector's ground position + heading at tau (smoothed heading so the head-cam does not snap at corners) */
export const defectorAt = (tau: number) => {
  const d = runDist(Math.max(0, tau));
  const a = routeAt(d), b = routeAt(Math.min(routeLen, d + 2.2));
  const dir = b.p.clone().sub(a.p);
  if (dir.lengthSq() < 1e-4) dir.copy(a.dir);
  return { p: a.p, dir: dir.normalize(), d };
};

/** the stuck jeep: front-left wheel in the ditch, nose down-left */
const JEEP_STUCK = { pos: new THREE.Vector3(JSA_MARKS.ditch.x - 0.62, 0, -7.6), yaw: 0.2, roll: -0.09, pitch: 0.06, drop: 0.12 };

/** the KPA squad, in program time = tau + 2 */
const SQUAD_T0 = 2;
const toward = (from: [number, number], to: THREE.Vector3) => Math.atan2(to.x - from[0], to.z - from[1]);
function squadPrograms(): Program[] {
  const target = defectorAt(4.6).p; // where he is when they open fire
  const shooter = (x: number, z: number, runAt: number, stopAt: number, fireAt: number): Program => {
    const yaw = toward([x, z], target) * 0.4 + 0.08;
    return { start: [x, 0, z], yaw, segs: [{ clip: "rifle_idle", at: 0 }, { clip: "rifle_run", at: runAt + SQUAD_T0, fade: 0.25 }, { clip: "run_to_stop", at: stopAt + SQUAD_T0, fade: 0.2 }, { clip: "fire", at: fireAt + SQUAD_T0, fade: 0.3, yaw: toward([x, z + 15], target) }] };
  };
  return [
    shooter(-18.6, -27, -1.0, 2.75, 3.5),
    shooter(-15.6, -29, -0.8, 3.05, 3.8),
    shooter(-21.2, -30, -0.6, 3.35, 4.1),
    // he runs over the line, turns round and runs back
    { start: [-13.6, 0, -15.5], yaw: 0.04, segs: [{ clip: "rifle_idle", at: 0 }, { clip: "rifle_run", at: -0.9 + SQUAD_T0, fade: 0.2 }, { clip: "run_turn", at: 2.0 + SQUAD_T0, fade: 0.2 }, { clip: "rifle_run", at: 4.25 + SQUAD_T0, fade: 0.25 }] },
  ];
}
/** bullets hitting the ground around him (tau, x, z) */
const DUST: [number, number, number][] = (() => {
  const out: [number, number, number][] = [];
  [1.9, 2.35, 2.8, 3.25, 3.7, 4.05, 4.4, 5.0, 5.3, 6.1].forEach((t, i) => {
    const { p, dir } = defectorAt(t + 0.15);
    const side = new THREE.Vector3(-dir.z, 0, dir.x);
    const q = p.clone().addScaledVector(dir, 1.2 + (i % 3) * 0.8).addScaledVector(side, ((i * 37) % 5) - 2);
    out.push([t, q.x, q.z]);
  });
  return out;
})();

type Trooper = { s: ReturnType<typeof createMxSoldier>; rifle: THREE.Group; prog: Program; flash: THREE.Sprite; light: THREE.PointLight };
function useSquad(glb: GLTFish | null, meta: Record<string, ClipMeta> | null, progs: Program[]) {
  return useMemo(() => {
    if (!glb || !meta) return null;
    return progs.map((prog) => {
      const flash = new THREE.Sprite(flashMat());
      flash.visible = false;
      const light = new THREE.PointLight("#FFB060", 0, 6, 2);
      return { s: createMxSoldier(glb, meta), rifle: makeRifle(), prog, flash, light } as Trooper;
    });
  }, [glb, meta, progs]);
}
const segAt = (prog: Program, t: number) => {
  let k = prog.segs.length - 1;
  while (k > 0 && t < prog.segs[k].at) k--;
  return prog.segs[k];
};
/** pose every trooper for program time pt; rifles, muzzle flashes */
function poseSquad(sq: Trooper[], pt: number) {
  const objs: THREE.Object3D[] = [];
  for (const tr of sq) {
    const r = tr.s.pose(tr.prog, pt);
    objs.push(tr.s.root, tr.flash, tr.light);
    const seg = segAt(tr.prog, pt);
    tr.flash.visible = false;
    tr.light.intensity = 0;
    if (r.rifle) {
      const firing = seg.clip === "fire";
      const ph = firing ? ((pt - seg.at) % 0.267) / 0.267 : 1;
      tr.s.holdRifle(tr.rifle, { shoulder: firing || seg.clip === "aim_idle", recoil: firing ? Math.max(0, 1 - ph * 4) : 0 });
      objs.push(tr.rifle);
      if (firing && ph < 0.24 && pt - seg.at > 0.15) {
        const mz = tr.rifle.getObjectByName("MUZZLE")!.getWorldPosition(new THREE.Vector3());
        tr.flash.visible = true;
        tr.flash.position.copy(mz);
        tr.flash.scale.setScalar(0.45 + 0.25 * Math.sin(pt * 91));
        tr.light.position.copy(mz);
        tr.light.intensity = 6;
      }
    }
  }
  return objs;
}

// ================================================================== overlays (DOM)
/** red vignette + white flash at hits; ringing blur after */
export const HitFX: React.FC<{ t: number; hits: number[]; blurFrom?: number }> = ({ t, hits, blurFrom }) => {
  const red = Math.max(0, ...hits.map((h) => (t >= h ? Math.exp(-(t - h) * 3.2) : 0)));
  const white = Math.max(0, ...hits.map((h) => (t >= h && t < h + 0.07 ? 1 : 0)));
  return (
    <>
      <AbsoluteFill style={{ background: `radial-gradient(ellipse 70% 60% at 50% 50%, rgba(120,0,0,0) 35%, rgba(150,8,4,${0.75 * red}) 100%)`, pointerEvents: "none" }} />
      <AbsoluteFill style={{ background: "#FFF6EA", opacity: white * 0.55, pointerEvents: "none" }} />
      {blurFrom !== undefined && t > blurFrom ? <AbsoluteFill style={{ backdropFilter: `blur(${Math.min(5, (t - blurFrom) * 3)}px) saturate(${1 - Math.min(0.6, (t - blurFrom) * 0.35)})`, pointerEvents: "none" }} /> : null}
    </>
  );
};
/** UN surveillance camera look: monochrome, scanlines, date stamp, REC */
export const CctvLook: React.FC<{ t: number; cam: string; clock0: number; children: React.ReactNode }> = ({ t, cam, clock0, children }) => {
  const s = Math.floor(clock0 + t);
  const ss = String(s % 60).padStart(2, "0");
  const mm = String(14 + Math.floor(s / 60)).padStart(2, "0");
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{ filter: "grayscale(1) contrast(1.28) brightness(1.06)" }}>{children}</AbsoluteFill>
      <AbsoluteFill style={{ background: "repeating-linear-gradient(0deg, rgba(0,0,0,0.13) 0px, rgba(0,0,0,0.13) 2px, rgba(0,0,0,0) 2px, rgba(0,0,0,0) 5px)", pointerEvents: "none" }} />
      <AbsoluteFill style={{ background: "radial-gradient(ellipse 80% 70% at 50% 50%, rgba(0,0,0,0) 55%, rgba(0,0,0,0.55) 100%)", pointerEvents: "none" }} />
      <div style={{ position: "absolute", left: 54, bottom: 210, fontFamily: "JetBrains Mono, monospace", fontSize: 38, color: "#E8E8E8", letterSpacing: 2, textShadow: "0 0 6px rgba(0,0,0,0.9)" }}>
        {cam}
        <br />
        2017-11-13 15:{mm}:{ss}
      </div>
      <div style={{ position: "absolute", right: 60, bottom: 220, fontFamily: "JetBrains Mono, monospace", fontSize: 36, color: "#FF4A3A", opacity: Math.floor(t * 2) % 2 ? 1 : 0.25 }}>● REC</div>
    </AbsoluteFill>
  );
};

// ================================================================== Panmunjom: shared world
function usePanmunjom() {
  const tex = useNkTextures();
  const leavesG = useGLB(M + "leaves_kit.glb");
  const flagsG = useGLB(M + "flags.glb");
  return useMemo(() => {
    if (!tex || !leavesG || !flagsG) return null;
    const flagSrc = flagsG.scene.getObjectByName("flag_dprk") as THREE.Mesh | null;
    const flag = flagSrc ? (flagSrc.clone() as THREE.Mesh) : null;
    if (flag) flag.geometry = flag.geometry.clone();
    const tower = flagTower(flag);
    const g = buildJSA(tex, { leafMat: leafMaterialFrom(leavesG.scene), flagTower: tower });
    const pile = leavesG.scene.getObjectByName("leaf_pile")?.clone();
    if (pile) {
      pile.position.copy(JSA_MARKS.collapse).add(new THREE.Vector3(-0.75, 0, 0));
      pile.scale.set(0.8, 0.55, 0.8);
      g.add(pile);
    }
    const waveTower = tower.userData.flag ? prepareFlag(tower.userData.flag as THREE.Mesh) : null;
    return { g, waveTower, leavesG, flagsG, tex };
  }, [tex, leavesG, flagsG]);
}
/** the jeep parked in the ditch (shared by the stuck / run / camera shots) */
function placeStuckJeep(jeep: NonNullable<ReturnType<typeof useJeep>>, spin = 0) {
  const s = JEEP_STUCK;
  jeep.root.position.copy(s.pos).add(new THREE.Vector3(0, -s.drop, 0));
  jeep.root.rotation.set(s.pitch, s.yaw, s.roll, "YXZ");
  for (const ty of jeep.tyres) {
    ty.o.quaternion.copy(ty.q).multiply(new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(1, 0, 0), spin));
  }
  jeep.root.updateMatrixWorld(true);
}

/** where the squad comes from: the look back over the shoulder aims here */
const LOOK_BACK_AT = new THREE.Vector3(-17.5, 1.2, -22);
/** running head-cam for the defector at tau: bob per step, sway, an optional look back over the left shoulder */
function runCam(tau: number, look: { at: number; dur: number } | null, fov = 74): Cam {
  const { p, dir } = defectorAt(tau);
  const moving = sm(tau / 0.4) * (tau < CHASE.fall ? 1 : 0);
  const steps = runDist(Math.max(0, tau)) / 1.55; // steps taken
  const ph = steps * Math.PI;
  const bob = Math.abs(Math.sin(ph)) * 0.06 * moving;
  const side = new THREE.Vector3(-dir.z, 0, dir.x);
  const eye = p.clone().add(new THREE.Vector3(0, 1.62 - 0.03 + bob, 0)).addScaledVector(side, Math.sin(ph) * 0.03 * moving);
  let yaw = 0, lk = 0;
  if (look) {
    lk = sm((tau - look.at) / 0.32) - sm((tau - look.at - look.dur) / 0.36);
    const to = LOOK_BACK_AT.clone().sub(eye);
    yaw = lk * Math.atan2(dir.z * to.x - dir.x * to.z, dir.x * to.x + dir.z * to.z);
  }
  const fwd = dir.clone().applyAxisAngle(new THREE.Vector3(0, 1, 0), yaw);
  const target = eye.clone().addScaledVector(fwd, 8).add(new THREE.Vector3(0, -0.9 + 0.8 * lk, 0));
  return { pos: eye.toArray() as V3, target: target.toArray() as V3, fov, roll: Math.sin(ph) * 0.02 * moving };
}
/** pumping fists while running; off-frame (rest) while looking back */
const pumpTrack = (s: "L" | "R", lookAt?: number, lookDur?: number): HandTrack => {
  const k = (t: number) => ({ t, to: [s === "L" ? -0.13 : 0.13, -0.4, -0.42] as V3, pose: "fist", aim: { fingers: [s === "L" ? 0.22 : -0.22, 0.12, -0.97] as V3, palm: [s === "L" ? 0.95 : -0.95, -0.2, 0.1] as V3 }, osc: { hz: 1.55, amp: [0.02, 0.12, 0.12] as V3, phase: s === "L" ? 0 : Math.PI } });
  const tr: HandTrack = [k(0)];
  if (lookAt !== undefined && lookDur !== undefined) {
    tr.push({ t: lookAt, to: "rest", dur: 0.25 });
    tr.push(k(lookAt + lookDur + 0.2));
  }
  return tr;
};

// ================================================================== scene: the chase on foot (hook / run)
export const NkChase: React.FC<{ tau0?: number; look?: [number, number]; exit?: boolean }> = ({ tau0 = 0, look, exit = false }) => {
  const { f, fps } = useBlockTime();
  const t = f / fps;
  const tau = tau0 + t;
  const world = usePanmunjom();
  const jeepRig = useJeep();
  const kpaG = useGLB(M + "soldier_mx_kpa.glb");
  const armsG = useGLB("models/fp_arms.glb");
  const meta = useClipMeta();
  const progs = useMemo(squadPrograms, []);
  const squad = useSquad(kpaG, meta, progs);
  const rig = useMemo(() => (armsG ? createFPRig(armsG.scene) : null), [armsG]);
  const dust = useMemo(() => dustPuffs(DUST), []);
  if (!world || !jeepRig || !squad || !rig) return <AbsoluteFill />;
  world.waveTower?.(tau + 30, 1.4);
  placeStuckJeep(jeepRig, exit ? Math.max(0, 0 - tau) * 25 : 0);
  const objs = [world.g, jeepRig.root, dust.group, ...poseSquad(squad, tau + SQUAD_T0)];
  dust.update(tau);
  let cam = runCam(tau, look ? { at: look[0], dur: look[1] } : null);
  if (exit && tau < 0.45) {
    // climbing out of the open jeep over the ditch side: from the driver's seat to the first stride
    const seat = jeepRig.eye.clone().applyMatrix4(jeepRig.root.matrixWorld);
    const k = sm((tau + 0.35) / 0.8);
    const c = cam;
    const pos = new THREE.Vector3(...c.pos);
    pos.lerp(seat, 1 - k).add(new THREE.Vector3(0, Math.sin(Math.PI * k) * 0.25, 0));
    cam = { ...c, pos: pos.toArray() as V3 };
  }
  const camera = makeCamera(cam);
  rig.pose(t, camera, { L: pumpTrack("L", look ? look[0] - tau0 : undefined, look?.[1]), R: pumpTrack("R", look ? look[0] - tau0 : undefined, look?.[1]) });
  objs.push(rig.root);
  return (
    <NkLook t={t}>
      <Stage3D cam={cam} lights="none" env={0.5} fog={{ color: "#B3BABD", near: 30, far: 300 }}>
        <color attach="background" args={["#B3BABD"]} />
        <OutdoorLights focus={cam.pos} sun={[-26, 34, -14]} />
        {objs.map((o, i) => (
          <primitive key={i} object={o} />
        ))}
      </Stage3D>
    </NkLook>
  );
};

// ================================================================== scene: the UN surveillance camera
export const NkCctv: React.FC<{ tau0?: number; cam?: CamKey[]; label?: string; clock0?: number; jeepSpin?: boolean }> = ({ tau0 = 0, cam: camKeys, label = "UNC CAM 04 · JSA", clock0 = 12, jeepSpin = false }) => {
  const { f, fps } = useBlockTime();
  const t = f / fps;
  const tau = tau0 + t;
  const world = usePanmunjom();
  const jeepRig = useJeep();
  const kpaG = useGLB(M + "soldier_mx_kpa.glb");
  const meta = useClipMeta();
  const progs = useMemo(squadPrograms, []);
  const squad = useSquad(kpaG, meta, progs);
  const runner = useMemo(() => (kpaG && meta ? createMxSoldier(kpaG, meta) : null), [kpaG, meta]);
  const dust = useMemo(() => dustPuffs(DUST), []);
  if (!world || !jeepRig || !squad || !runner) return <AbsoluteFill />;
  world.waveTower?.(tau + 30, 1.4);
  placeStuckJeep(jeepRig, jeepSpin ? tau * 22 : 0);
  // the jeep rocks while he guns it back and forth
  if (jeepSpin && tau < 0) jeepRig.root.position.addScaledVector(new THREE.Vector3(Math.sin(JEEP_STUCK.yaw), 0, Math.cos(JEEP_STUCK.yaw)), Math.sin(tau * 9) * 0.06);
  jeepRig.root.updateMatrixWorld(true);
  const objs: THREE.Object3D[] = [world.g, jeepRig.root, dust.group, ...poseSquad(squad, tau + SQUAD_T0)];
  dust.update(tau);
  // the defector, small in the frame, running his route (unarmed run pose, placed on the route)
  if (tau > 0.05 && tau < CHASE.fall + 0.3) {
    const { p, dir } = defectorAt(tau);
    runner.pose({ start: [0, 0, 0], yaw: 0, segs: [{ clip: "rifle_run", at: 0, rate: 1.05 }] }, tau);
    runner.root.position.set(p.x, runner.root.position.y, p.z);
    runner.root.rotation.set(0, Math.atan2(dir.x, dir.z), 0);
    runner.root.updateMatrixWorld(true);
    objs.push(runner.root);
  }
  const keys = camKeys ?? [{ t: 0, pos: [-1.5, 9.5, 21] as V3, target: [-14, 0.5, -5] as V3, fov: 46 }, { t: 6, pos: [-1.8, 9.5, 21] as V3, target: [-13.5, 0.5, -4] as V3, fov: 44 }];
  const cam = camAt(keys, t);
  return (
    <CctvLook t={t} cam={label} clock0={clock0}>
      <Stage3D cam={cam} lights="none" env={0.5} fog={{ color: "#B3BABD", near: 30, far: 300 }}>
        <color attach="background" args={["#B3BABD"]} />
        <OutdoorLights focus={[-13, 0, 0]} sun={[-26, 34, -14]} />
        {objs.map((o, i) => (
          <primitive key={i} object={o} />
        ))}
      </Stage3D>
    </CctvLook>
  );
};

// ================================================================== scene: hit, hit, fall into the leaves
export const NkFall: React.FC<{ tau0?: number }> = ({ tau0 = CHASE.hit1 }) => {
  const { f, fps } = useBlockTime();
  const t = f / fps;
  const tau = tau0 + t;
  const world = usePanmunjom();
  const kpaG = useGLB(M + "soldier_mx_kpa.glb");
  const armsG = useGLB("models/fp_arms.glb");
  const meta = useClipMeta();
  const jeepRig = useJeep();
  const progs = useMemo(squadPrograms, []);
  const squad = useSquad(kpaG, meta, progs);
  const rig = useMemo(() => (armsG ? createFPRig(armsG.scene) : null), [armsG]);
  const dust = useMemo(() => dustPuffs(DUST), []);
  if (!world || !squad || !rig || !jeepRig) return <AbsoluteFill />;
  world.waveTower?.(tau + 30, 1.4);
  placeStuckJeep(jeepRig);
  dust.update(tau);
  const objs = [world.g, jeepRig.root, dust.group, ...poseSquad(squad, tau + SQUAD_T0)];
  let cam = runCam(Math.min(tau, CHASE.fall), null, 74);
  // hits: a kick of the head (pitch down, roll), then he stumbles on
  const kick = (h: number, k: number) => (tau >= h ? Math.exp(-(tau - h) * 5) * k * Math.sin(Math.min(1, (tau - h) / 0.08) * Math.PI * 0.5) : 0);
  const k1 = kick(CHASE.hit1, 1), k2 = kick(CHASE.hit2, 1.5);
  const pos = new THREE.Vector3(...cam.pos), tgt = new THREE.Vector3(...cam.target);
  tgt.add(new THREE.Vector3(0, -1.6 * (k1 + k2), 0));
  let roll = (cam.roll ?? 0) + 0.25 * k1 - 0.35 * k2;
  // the fall: down to the ground beside the wall, rolling onto the back, looking along the wall and up
  const fk = sm((tau - CHASE.fall) / 0.5);
  if (fk > 0) {
    const ground = JSA_MARKS.collapse.clone().add(new THREE.Vector3(0.27, 0.2, 0.25));
    pos.lerp(ground, fk);
    const lookAfter = ground.clone().add(new THREE.Vector3(1.6, 2.4, -0.9));
    tgt.lerp(lookAfter, sm((tau - CHASE.fall - 0.15) / 0.6));
    roll = lerp(roll, 0.5, fk) * (1 - sm((tau - CHASE.fall - 0.6) / 0.8)) + 0.1 * Math.sin(tau * 0.8);
    pos.y += Math.sin(Math.min(1, (tau - CHASE.fall) / 0.5) * Math.PI) * -0.05;
  }
  cam = { pos: pos.toArray() as V3, target: tgt.toArray() as V3, fov: cam.fov, roll };
  const camera = makeCamera(cam);
  const lt = (x: number) => x - tau0;
  const hand = (s: "L" | "R"): HandTrack => [
    ...pumpTrack(s),
    { t: lt(CHASE.hit2 + 0.05), to: [s === "L" ? -0.24 : 0.25, -0.34, -0.38], pose: "claw", dur: 0.25 },
    { t: lt(CHASE.fall - 0.1), to: [s === "L" ? -0.27 : 0.28, -0.22, -0.42], pose: "claw", dur: 0.3, aim: { fingers: [s === "L" ? 0.2 : -0.2, -0.3, -0.9], palm: [0, -1, 0] } },
    { t: lt(CHASE.fall + 0.55), to: "rest", dur: 0.5 },
  ];
  rig.pose(t, camera, { L: hand("L"), R: hand("R") });
  objs.push(rig.root);
  return (
    <AbsoluteFill>
      <NkLook t={t} vignette={0.5}>
        <Stage3D cam={cam} lights="none" env={0.5} fog={{ color: "#B3BABD", near: 30, far: 300 }}>
          <color attach="background" args={["#B3BABD"]} />
          <OutdoorLights focus={cam.pos} sun={[-26, 34, -14]} />
          {objs.map((o, i) => (
            <primitive key={i} object={o} />
          ))}
        </Stage3D>
      </NkLook>
      <HitFX t={tau} hits={[CHASE.hit1, CHASE.hit2]} blurFrom={CHASE.fall + 0.4} />
    </AbsoluteFill>
  );
};

// ================================================================== scene: barracks (drink / fist on the table)
export const NkBarracks: React.FC<{ mode?: "drink" | "slam"; slamAt?: number; lookAt?: number; dreadAt?: number }> = ({ mode = "drink", slamAt = 0.9, lookAt = 2.2, dreadAt = 4.2 }) => {
  const { f, fps } = useBlockTime();
  const t = f / fps;
  const tex = useNkTextures();
  const cupG = useGLB(M + "cup_aluminium.glb");
  const armsG = useGLB("models/fp_arms.glb");
  const kpaG = useGLB(M + "soldier_mx_kpa.glb");
  const meta = useClipMeta();
  const rig = useMemo(() => (armsG ? createFPRig(armsG.scene) : null), [armsG]);
  const friend = useMemo(() => (kpaG && meta ? createMxSoldier(kpaG, meta) : null), [kpaG, meta]);
  const set = useMemo(() => {
    if (!tex || !cupG) return null;
    const room = buildBarracks(tex, null);
    const cup = cupG.scene.clone(true);
    cup.traverse((o) => ((o as THREE.Mesh).isMesh ? ((o as THREE.Mesh).castShadow = (o as THREE.Mesh).receiveShadow = true) : null));
    const bulb = new THREE.PointLight("#FFD9A0", 2.2, 9, 1.6);
    bulb.position.set(0, 2.32, -0.2);
    bulb.castShadow = true;
    room.add(bulb);
    const bottles: THREE.Object3D[] = [];
    room.traverse((o) => (o.name === "bottle" ? bottles.push(o) : null));
    return { room, cup, bottles, rest: bottles.map((b) => ({ p: b.position.clone(), r: b.rotation.clone() })) };
  }, [tex, cupG]);
  if (!set || !rig || !friend) return <AbsoluteFill />;
  const CUP_HALF = 0.0435;
  const eye = BARRACKS_MARKS.eye;
  let keys: CamKey[];
  if (mode === "drink")
    keys = [
      { t: 0, pos: eye.toArray() as V3, target: [0.06, 0.64, -1.4], fov: 72 },
      { t: 1.3, pos: eye.toArray() as V3, target: [0.12, 0.72, -1.3], fov: 72 },
      { t: 2.0, pos: [0, 1.2, 0.63], target: [0.02, 1.18, -1.2], fov: 72 },
      { t: 3.2, pos: eye.toArray() as V3, target: [0.05, 0.75, -1.4], fov: 72 },
    ];
  else
    keys = [
      { t: 0, pos: eye.toArray() as V3, target: [0.05, 0.9, -1.4], fov: 72 },
      { t: slamAt, pos: [0, 1.18, 0.6], target: [0.1, 0.55, -1.2], fov: 72, ease: "out" },
      { t: lookAt, pos: eye.toArray() as V3, target: [0.05, 1.3, -1.5], fov: 72 },
      { t: dreadAt + 0.2, pos: [0, 1.24, 0.35], target: [0, 1.7, -3.0], fov: 62 },
      { t: dreadAt + 1.2, pos: [0, 1.25, 0.2], target: [0, 1.85, -3.1], fov: 56 },
    ];
  const cam = camAt(keys, t);
  const camera = makeCamera(cam);
  const cupHome = BARRACKS_MARKS.cup.clone();
  const grabCup = (T: number) => {
    const inv = makeCamera(camAt(keys, T)).matrixWorldInverse;
    const c = cupHome.clone().add(new THREE.Vector3(0, CUP_HALF, 0)).applyMatrix4(inv);
    const fingers = new THREE.Vector3(-0.25, -0.05, -1).normalize();
    const palm = new THREE.Vector3(-1, 0, 0.1).normalize();
    const p = c.clone().addScaledVector(fingers, -0.078).addScaledVector(palm, -0.034);
    return { p: p.toArray() as V3, aim: { fingers: fingers.toArray() as V3, palm: palm.toArray() as V3 } };
  };
  const tableAt = (T: number) => {
    const inv = makeCamera(camAt(keys, T)).matrixWorldInverse;
    return BARRACKS_MARKS.table.clone().add(new THREE.Vector3(0.12, 0.06, 0.22)).applyMatrix4(inv).toArray() as V3;
  };
  let R: HandTrack;
  if (mode === "drink")
    R = [
      { t: 0.25, to: grabCup, pose: "cup", contact: true },
      { t: 1.25, to: [0.06, -0.16, -0.22], pose: "cup", contact: true, aim: { fingers: [-0.55, 0.1, -0.8], palm: [-0.95, 0.05, 0.3] } },
      { t: 1.85, to: [0.04, -0.12, -0.17], pose: "cup", contact: true, dur: 0.5, aim: { fingers: [-0.5, 0.45, -0.7], palm: [-0.95, 0.15, 0.25] } },
      { t: 2.6, to: grabCup, pose: "cup", contact: true },
    ];
  else
    R = [
      { t: 0, to: grabCup, pose: "cup", contact: true },
      { t: 0.15, to: [0.14, -0.2, -0.36], pose: "fist", dur: Math.max(0.3, slamAt - 0.3), aim: { fingers: [-0.3, 0.2, -0.9], palm: [-0.8, -0.3, 0.2] } }, // fist up
      { t: slamAt - 0.12, to: tableAt, pose: "fist", dur: 0.14, contact: true, aim: { fingers: [-0.2, -0.2, -0.95], palm: [-0.85, -0.4, 0.1] } }, // bang
      { t: lookAt - 0.2, to: "rest", dur: 0.6 },
    ];
  rig.pose(t, camera, { R });
  // the cup: on the table, in the hand while drinking
  set.cup.position.copy(cupHome);
  set.cup.quaternion.identity();
  const w = mode === "drink" ? sm((t - 0.6) / 0.25) * (1 - sm((t - 3.15) / 0.25)) : 0;
  if (w > 0) {
    const held = set.cup.clone();
    rig.holdInHand("R", held, { halfHeight: CUP_HALF });
    set.cup.position.lerp(held.position, w);
    set.cup.quaternion.slerp(held.quaternion, w);
  }
  // the bang: bottles and the cup jump and wobble
  const bang = mode === "slam" && t > slamAt ? Math.exp(-(t - slamAt) * 6) : 0;
  set.bottles.forEach((b, i) => {
    const r = set.rest[i];
    b.position.copy(r.p).add(new THREE.Vector3(0, Math.abs(Math.sin((t - slamAt) * 30)) * 0.02 * bang, 0));
    b.rotation.set(r.r.x + Math.sin((t - slamAt) * 24 + i) * 0.12 * bang, r.r.y, r.r.z + Math.sin((t - slamAt) * 19 + i * 2) * 0.1 * bang);
  });
  if (bang > 0) set.cup.position.y += Math.abs(Math.sin((t - slamAt) * 28)) * 0.025 * bang;
  // the friend across the room yelling back (slam only)
  const objs: THREE.Object3D[] = [set.room, set.cup, rig.root];
  if (mode === "slam") {
    friend.pose({ start: [0.35, 0, -1.55], yaw: 0, segs: [{ clip: "yell", at: 0, offset: 1.2 }] }, t);
    objs.push(friend.root);
  }
  const dread = mode === "slam" ? sm((t - dreadAt) / 0.8) : 0;
  return (
    <NkLook t={t} vignette={0.42 + dread * 0.25}>
      <Stage3D cam={cam} lights="none" env={0.35} exposure={1.05 - dread * 0.3}>
        <color attach="background" args={["#DCE3E6"]} />
        <OutdoorLights focus={[0, 1, 0]} sun={[-9, 6, -3]} intensity={2.6} warm="#FFF6E8" />
        {objs.map((o, i) => (
          <primitive key={i} object={o} />
        ))}
      </Stage3D>
    </NkLook>
  );
};

// ================================================================== the road from Kaesong (drive scenes)
const ROAD = { bridge0: 215, bridge1: 275, check: 130, billboard: 70 };
function sloganTexture(text: string) {
  const c = document.createElement("canvas");
  c.width = 2048;
  c.height = 1024;
  const g = c.getContext("2d")!;
  g.fillStyle = "#B8261E";
  g.fillRect(0, 0, c.width, c.height);
  g.strokeStyle = "#F0E6CF";
  g.lineWidth = 26;
  g.strokeRect(40, 40, c.width - 80, c.height - 80);
  g.fillStyle = "#F4ECD8";
  g.font = "bold 210px 'Noto Sans KR','Malgun Gothic',sans-serif";
  g.textAlign = "center";
  g.textBaseline = "middle";
  const lines = text.split("\n");
  lines.forEach((l, i) => g.fillText(l, c.width / 2, c.height / 2 + (i - (lines.length - 1) / 2) * 250));
  for (let i = 0; i < 1800; i++) {
    g.fillStyle = `rgba(0,0,0,${Math.random() * 0.06})`;
    g.fillRect(Math.random() * c.width, Math.random() * c.height, 3 + Math.random() * 60, 2 + Math.random() * 6);
  }
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}
function buildRoad(tex: Tex, leafMat: THREE.Material, flagMesh: THREE.Mesh | null, checkpoint: THREE.Object3D | null) {
  const g = new THREE.Group();
  const grass = makeMat(tex, "dry_grass", { color: "#8E8B76", normal: 0.4 });
  const asphalt = makeMat(tex, "asphalt", { color: "#9C9A95", normal: 0.5 });
  const conc = makeMat(tex, "concrete", { color: "#C9C6BD" });
  const gr = (w: number, d: number, x: number, z: number, y = -0.02) => {
    const m = new THREE.Mesh(plane(w, d, 23), grass);
    m.position.set(x, y, z);
    m.receiveShadow = true;
    m.userData.ground = true;
    g.add(m);
  };
  const { bridge0: b0, bridge1: b1 } = ROAD;
  gr(700, b0 + 300, 0, (b0 - 300) / 2);
  gr(700, 700 - b1, 0, (700 + b1) / 2);
  // the valley under the bridge: two slopes and the river
  const slope = (zTop: number, zBot: number) => {
    const len = Math.hypot(zBot - zTop, 5);
    const m = new THREE.Mesh(plane(700, len, 23), grass);
    m.position.set(0, -2.5, (zTop + zBot) / 2);
    m.rotation.x = Math.atan2(5, Math.abs(zBot - zTop)) * (zBot > zTop ? 1 : -1);
    m.receiveShadow = true;
    m.userData.ground = true;
    g.add(m);
  };
  slope(b0, b0 + 14);
  slope(b1, b1 - 14);
  const water = new THREE.MeshStandardMaterial({ color: "#33433F", roughness: 0.06, metalness: 0.45, normalMap: tex["concrete_n"] ?? null });
  water.normalScale.set(0.12, 0.12);
  const river = new THREE.Mesh(plane(700, b1 - b0 - 26, 9), water);
  river.position.set(0, -4.7, (b0 + b1) / 2);
  river.userData.ground = true;
  g.add(river);
  const stoneMat = makeMat(tex, "granite", { color: "#8A8780" });
  const stones = new THREE.InstancedMesh(new THREE.DodecahedronGeometry(0.5, 0), stoneMat, 160);
  for (let i = 0; i < 160; i++) {
    const r0 = ((i * 9301 + 49297) % 233280) / 233280, r1 = ((i * 4271 + 1731) % 9973) / 9973;
    const bank = i % 2 ? b0 + 13 + r1 * 1.4 : b1 - 13 - r1 * 1.4;
    const sc = 0.4 + r0 * 0.9;
    stones.setMatrixAt(i, new THREE.Matrix4().compose(new THREE.Vector3(-90 + r0 * 180, -4.75, bank), new THREE.Quaternion().setFromEuler(new THREE.Euler(r1 * 3, r0 * 6, 0)), new THREE.Vector3(sc, sc * 0.6, sc)));
  }
  stones.castShadow = true;
  stones.userData.mount = true;
  g.add(stones);
  // road (on the ground and on the bridge deck)
  const road = new THREE.Mesh(plane(6.5, 700, 7), asphalt);
  road.position.set(0, 0.015, 230);
  road.receiveShadow = true;
  road.userData.ground = true;
  g.add(road);
  const dash = new THREE.InstancedMesh(new THREE.BoxGeometry(0.14, 0.012, 2.4), new THREE.MeshStandardMaterial({ color: "#D2CCB4", roughness: 0.8 }), 110);
  for (let i = 0; i < 110; i++) dash.setMatrixAt(i, new THREE.Matrix4().makeTranslation(0, 0.022, -10 + i * 6));
  dash.userData.mount = true;
  g.add(dash);
  // the 72-hour bridge: deck, parapets, two piers
  const deck = new THREE.Mesh(box(7.6, 0.8, b1 - b0 + 2, 2), conc);
  deck.position.set(0, -0.4, (b0 + b1) / 2);
  deck.castShadow = deck.receiveShadow = true;
  g.add(deck);
  for (const s of [-1, 1]) {
    const par = new THREE.Mesh(box(0.28, 0.9, b1 - b0 + 2, 1.5), conc);
    par.position.set(s * 3.66, 0.45, (b0 + b1) / 2);
    par.castShadow = par.receiveShadow = true;
    g.add(par);
  }
  for (const z of [b0 + 20, b1 - 20]) {
    const pier = new THREE.Mesh(box(5.6, 4.6, 1.6, 2), conc);
    pier.position.set(0, -3.1, z);
    pier.castShadow = true;
    g.add(pier);
  }
  // roadside: trees, utility poles with wires, DPRK flags, a slogan billboard
  const r = (i: number) => ((i * 9301 + 49297) % 233280) / 233280;
  const nearCheck = (z: number) => z > ROAD.check - 16 && z < ROAD.check + 16;
  for (let z = -10, i = 0; z < 640; z += 13, i++) {
    if (z > b0 - 12 && z < b1 + 12) continue;
    for (const s of [-1, 1]) {
      if (s < 0 && nearCheck(z)) continue;
      const tr = tree(leafMat, i * 2 + (s > 0 ? 1 : 0), 7.5 + r(i + s) * 3, 2.8 + r(i * 3) * 0.8);
      tr.position.set(s * (8.5 + r(i * 7 + s) * 6), 0, z + r(i * 5) * 5);
      g.add(tr);
    }
  }
  const poleMat = new THREE.MeshStandardMaterial({ color: "#5E5547", roughness: 0.9 });
  const tops: THREE.Vector3[] = [];
  for (let z = -10; z < 640; z += 34) {
    if ((z > b0 - 6 && z < b1 + 6) || nearCheck(z)) continue;
    const p = new THREE.Mesh(new THREE.CylinderGeometry(0.11, 0.15, 8, 8), poleMat);
    p.position.set(-5.6, 4, z);
    p.castShadow = true;
    g.add(p);
    const bar = new THREE.Mesh(new THREE.BoxGeometry(1.6, 0.1, 0.1), poleMat);
    bar.position.set(-5.6, 7.6, z);
    bar.userData.mount = true;
    g.add(bar);
    tops.push(new THREE.Vector3(-5.6, 7.62, z));
  }
  const wireMat = new THREE.LineBasicMaterial({ color: "#2B2B2B" });
  for (let i = 1; i < tops.length; i++) {
    if (tops[i].z - tops[i - 1].z > 40) continue;
    for (const dx of [-0.7, 0.7]) {
      const a = tops[i - 1].clone().add(new THREE.Vector3(dx, 0, 0)), b = tops[i].clone().add(new THREE.Vector3(dx, 0, 0));
      const pts = Array.from({ length: 12 }, (_, k) => a.clone().lerp(b, k / 11).add(new THREE.Vector3(0, -Math.sin((Math.PI * k) / 11) * 0.6, 0)));
      g.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts), wireMat));
    }
  }
  const waves: ((t: number) => void)[] = [];
  if (flagMesh)
    for (let z = 20; z < 640; z += 45) {
      if (z > b0 - 10 && z < b1 + 10) continue;
      const pole = new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.05, 6.5, 8), new THREE.MeshStandardMaterial({ color: "#8A8D8F", metalness: 0.6, roughness: 0.4 }));
      pole.position.set(5.2, 3.25, z);
      g.add(pole);
      const fl = flagMesh.clone() as THREE.Mesh;
      fl.geometry = fl.geometry.clone();
      fl.scale.setScalar(0.8);
      fl.position.set(5.2 - 0.04, 5.6, z);
      fl.rotation.y = Math.PI / 2;
      fl.userData.mount = true;
      g.add(fl);
      waves.push(prepareFlag(fl));
    }
  const bb = new THREE.Group();
  const post = new THREE.MeshStandardMaterial({ color: "#4B4E4F", metalness: 0.5, roughness: 0.6 });
  for (const x of [-2.4, 2.4]) {
    const p = new THREE.Mesh(new THREE.BoxGeometry(0.22, 4.2, 0.22), post);
    p.position.set(x, 2.1, 0);
    bb.add(p);
  }
  const panel = new THREE.Mesh(new THREE.BoxGeometry(7.2, 3.6, 0.15), [post, post, post, post, new THREE.MeshStandardMaterial({ map: sloganTexture("우리 식대로\n살아나가자!"), roughness: 0.85 }), post]);
  panel.position.set(0, 4.6, 0);
  panel.userData.mount = true;
  bb.add(panel);
  bb.position.set(11, 0, ROAD.billboard);
  bb.rotation.y = -0.5;
  g.add(bb);
  // checkpoint compound on the right, building facing the road, a raised barrier across the lane
  if (checkpoint) {
    const cp = checkpoint.clone(true);
    cp.traverse((o) => ((o as THREE.Mesh).isMesh ? ((o as THREE.Mesh).castShadow = (o as THREE.Mesh).receiveShadow = true) : null));
    cp.position.set(-15.5, 0, ROAD.check);
    cp.rotation.y = Math.PI / 2;
    g.add(cp);
  }
  const boomPost = new THREE.Mesh(new THREE.BoxGeometry(0.4, 1.1, 0.4), conc);
  boomPost.position.set(-3.9, 0.55, ROAD.check - 3);
  g.add(boomPost);
  const stripes = document.createElement("canvas");
  stripes.width = 512;
  stripes.height = 32;
  const sg = stripes.getContext("2d")!;
  for (let i = 0; i < 8; i++) {
    sg.fillStyle = i % 2 ? "#F1EEE6" : "#C42A20";
    sg.fillRect(i * 64, 0, 64, 32);
  }
  const st = new THREE.CanvasTexture(stripes);
  st.colorSpace = THREE.SRGBColorSpace;
  const boom = new THREE.Mesh(new THREE.BoxGeometry(0.12, 0.12, 6.8), new THREE.MeshStandardMaterial({ map: st, roughness: 0.6 }));
  boom.geometry.translate(0, 0, -3.4);
  boom.position.set(-3.9, 1.12, ROAD.check - 3);
  boom.rotation.set(1.25, -Math.PI / 2, 0, "YXZ"); // raised, leaning over the lane
  boom.userData.mount = true;
  g.add(boom);
  // far hills
  for (let i = 0; i < 9; i++) {
    const h = new THREE.Mesh(new THREE.IcosahedronGeometry(60 + r(i) * 40, 2), grass);
    h.scale.set(1, 0.28 + r(i * 3) * 0.12, 1);
    h.position.set((i % 2 ? 1 : -1) * (130 + r(i * 5) * 120), -6, 120 + i * 80);
    h.userData.ground = true;
    g.add(h);
  }
  return { g, wave: (t: number) => waves.forEach((w) => w(t)) };
}
function useRoad() {
  const tex = useNkTextures();
  const leavesG = useGLB(M + "leaves_kit.glb");
  const flagsG = useGLB(M + "flags.glb");
  const cpG = useGLB(M + "checkpoint.glb");
  return useMemo(() => {
    if (!tex || !leavesG || !flagsG || !cpG) return null;
    const flag = flagsG.scene.getObjectByName("flag_dprk") as THREE.Mesh | null;
    return buildRoad(tex, leafMaterialFrom(leavesG.scene), flag, cpG.scene);
  }, [tex, leavesG, flagsG, cpG]);
}

/** jeep driving straight along a road (+Z) at x, with a speed profile; returns its matrices for time t */
type DrivePlan = { x: number; z0: number; v0: number; v1: number; accel?: number; startAt?: number; yaw?: number };
const driveZ = (p: DrivePlan, t: number) => {
  const s = Math.max(0, t - (p.startAt ?? 0));
  const a = p.accel ?? 0;
  if (!a) return p.z0 + p.v0 * s;
  const tt = Math.min(s, (p.v1 - p.v0) / a);
  return p.z0 + p.v0 * tt + 0.5 * a * tt * tt + p.v1 * Math.max(0, s - tt);
};
function jeepMatrices(jeep: NonNullable<ReturnType<typeof useJeep>>, p: DrivePlan, t: number, rumble: number) {
  const z = driveZ(p, t);
  const bob = rumble * (0.008 * Math.sin(t * 8.3) + 0.005 * Math.sin(t * 13.1 + 1));
  const ground = new THREE.Matrix4().compose(new THREE.Vector3(p.x, 0, z), new THREE.Quaternion().setFromEuler(new THREE.Euler(0, p.yaw ?? 0, 0)), new THREE.Vector3(1, 1, 1));
  const body = ground.clone().multiply(new THREE.Matrix4().makeTranslation(0, bob, 0));
  return { ground, body, bob, dist: z - p.z0 };
}
function applyJeep(jeep: NonNullable<ReturnType<typeof useJeep>>, m: { ground: THREE.Matrix4; bob: number; dist: number }, steer = 0) {
  m.ground.decompose(jeep.root.position, jeep.root.quaternion, jeep.root.scale);
  jeep.body.position.y = jeep.bodyY + m.bob;
  jeep.wheel.position.y = jeep.wheelY + m.bob;
  jeep.wheel.quaternion.copy(jeep.wheelQ).multiply(new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0, 1, 0), steer));
  for (const ty of jeep.tyres) ty.o.quaternion.copy(ty.q).multiply(new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(1, 0, 0), m.dist / 0.39));
  jeep.root.updateMatrixWorld(true);
}
/** driver's eyes for a body matrix; look ahead with an optional head turn (rad, + = left) */
function driverCam(jeep: NonNullable<ReturnType<typeof useJeep>>, body: THREE.Matrix4, t: number, turn = 0, shake = 0): Cam {
  const eye = new THREE.Vector3(0.263, 1.47, -0.56).add(new THREE.Vector3(0.004 * Math.sin(t * 1.3), 0.003 * Math.sin(t * 7.9) + shake * Math.sin(t * 47) * 0.01, 0)).applyMatrix4(body);
  const fwd = new THREE.Vector3(0, -0.11, 1).normalize().applyAxisAngle(new THREE.Vector3(0, 1, 0), turn).transformDirection(body);
  return { pos: eye.toArray() as V3, target: eye.clone().addScaledVector(fwd, 10).toArray() as V3, fov: 70, roll: shake * Math.sin(t * 31) * 0.01 };
}
/** both hands on the rim of the jeep's wheel (anchors follow the wheel and the camera) */
function wheelGrip(jeep: NonNullable<ReturnType<typeof useJeep>>, bodyAt: (T: number) => THREE.Matrix4, camAtT: (T: number) => Cam, side: "L" | "R") {
  return (T: number) => {
    const W = bodyAt(T).clone().multiply(jeep.wheelLocal);
    const inv = makeCamera(camAtT(T)).matrixWorldInverse;
    const p = jeep.grip[side].clone().applyMatrix4(W).applyMatrix4(inv);
    const c = new THREE.Vector3().applyMatrix4(W).applyMatrix4(inv);
    const axis = new THREE.Vector3(0, 1, 0).transformDirection(W).transformDirection(inv);
    const radial = p.clone().sub(c).normalize();
    const palm = axis.clone().multiplyScalar(-0.85).addScaledVector(radial, -0.3).normalize();
    return barGrip(p, palm, radial.clone().addScaledVector(axis, -0.35));
  };
}

export const NkDrive: React.FC<{ mode?: "start" | "checkpoint" }> = ({ mode = "start" }) => {
  const { f, fps } = useBlockTime();
  const t = f / fps;
  const road = useRoad();
  const jeepRig = useJeep();
  const armsG = useGLB("models/fp_arms.glb");
  const kpaG = useGLB(M + "soldier_mx_kpa.glb");
  const meta = useClipMeta();
  const rig = useMemo(() => (armsG ? createFPRig(armsG.scene) : null), [armsG]);
  const guard = useMemo(() => (kpaG && meta ? createMxSoldier(kpaG, meta) : null), [kpaG, meta]);
  if (!road || !jeepRig || !rig || !guard) return <AbsoluteFill />;
  const plan: DrivePlan = mode === "start" ? { x: -1.7, z0: 2, v0: 0, v1: 16, accel: 7, startAt: 0.95 } : { x: -1.7, z0: ROAD.check - 17, v0: 18, v1: 18 };
  const rumble = mode === "start" ? sm((t - 0.45) / 0.3) : 1;
  const bodyAt = (T: number) => jeepMatrices(jeepRig, plan, T, mode === "start" ? sm((T - 0.45) / 0.3) : 1).body;
  // checkpoint: a glance right at the yelling sentry as the jeep flies by
  const turnAt = (T: number) => (mode === "checkpoint" ? -0.62 * (sm((T - 0.3) / 0.35) - sm((T - 1.45) / 0.45)) : 0);
  const camAtT = (T: number) => driverCam(jeepRig, bodyAt(T), T, turnAt(T), mode === "start" ? sm((T - 0.45) / 0.2) * (1 - sm((T - 1.2) / 0.4)) * 0.6 : 0.15);
  const m = jeepMatrices(jeepRig, plan, t, rumble);
  applyJeep(jeepRig, m);
  road.wave(t + (mode === "start" ? 0 : 10));
  const cam = camAtT(t);
  const camera = makeCamera(cam);
  const gripL = wheelGrip(jeepRig, bodyAt, camAtT, "L"), gripR = wheelGrip(jeepRig, bodyAt, camAtT, "R");
  const tracks: { L: HandTrack; R: HandTrack } =
    mode === "start"
      ? {
          // right hand turns the key (right of the column, low), then both hands take the wheel
          R: [
            { t: 0.05, to: (T: number) => new THREE.Vector3(0.43, 1.06, 0.12).applyMatrix4(bodyAt(T)).applyMatrix4(makeCamera(camAtT(T)).matrixWorldInverse).toArray() as V3, pose: "pinch", dur: 0.38, aim: { fingers: [-0.2, -0.1, -0.97], palm: [-0.95, 0.1, 0.1] } },
            { t: 0.62, to: gripR, pose: "wheel", contact: true, dur: 0.42 },
          ],
          L: [{ t: 0.55, to: gripL, pose: "wheel", contact: true, dur: 0.5 }],
        }
      : { L: [{ t: 0, to: gripL, pose: "wheel", contact: true, dur: 0.01 }], R: [{ t: 0, to: gripR, pose: "wheel", contact: true, dur: 0.01 }] };
  rig.pose(t, camera, tracks);
  const objs: THREE.Object3D[] = [road.g, jeepRig.root, rig.root];
  if (mode === "checkpoint") {
    guard.pose({ start: [-4.7, 0, ROAD.check - 1], yaw: Math.PI / 2 + 0.4, segs: [{ clip: "yell", at: 0, offset: 0.6 }] }, t);
    objs.push(guard.root);
  }
  return (
    <NkLook t={t}>
      <Stage3D cam={cam} lights="none" env={0.5} fog={{ color: "#AEB6BA", near: 30, far: 260 }}>
        <color attach="background" args={["#AEB6BA"]} />
        <OutdoorLights focus={cam.pos} />
        {objs.map((o, i) => (
          <primitive key={i} object={o} />
        ))}
      </Stage3D>
    </NkLook>
  );
};

/** drone shot: the jeep crossing the 72-hour bridge */
export const NkBridge: React.FC = () => {
  const { f, fps } = useBlockTime();
  const t = f / fps;
  const road = useRoad();
  const jeepRig = useJeep();
  if (!road || !jeepRig) return <AbsoluteFill />;
  const plan: DrivePlan = { x: -1.7, z0: ROAD.bridge0 - 14, v0: 19, v1: 19 };
  const m = jeepMatrices(jeepRig, plan, t, 1);
  applyJeep(jeepRig, m);
  road.wave(t + 20);
  const jz = driveZ(plan, t);
  const k = sm(t / 2.8);
  const cam: Cam = { pos: [-17 + k * 4, 1.2 + k * 7.5, jz - 15 + t * 1.6], target: [-1.7, -0.6 - k * 1.2, jz + 5], fov: 50, roll: -0.04 + k * 0.03 };
  return (
    <NkLook t={t}>
      <Stage3D cam={cam} lights="none" env={0.5} fog={{ color: "#AEB6BA", near: 40, far: 320 }}>
        <color attach="background" args={["#AEB6BA"]} />
        <OutdoorLights focus={[-1.7, 0, jz]} />
        <primitive object={road.g} />
        <primitive object={jeepRig.root} />
      </Stage3D>
    </NkLook>
  );
};

// ================================================================== Panmunjom by jeep: the approach and the ditch
export const NkDitch: React.FC<{ mode?: "approach" | "ditch"; dropAt?: number; revAt?: [number, number] }> = ({ mode = "ditch", dropAt = 0.7, revAt = [2.1, 2.76] }) => {
  const { f, fps } = useBlockTime();
  const t = f / fps;
  const world = usePanmunjom();
  const jeepRig = useJeep();
  const armsG = useGLB("models/fp_arms.glb");
  const kpaG = useGLB(M + "soldier_mx_kpa.glb");
  const meta = useClipMeta();
  const progs = useMemo(squadPrograms, []);
  const squad = useSquad(kpaG, meta, progs);
  const rig = useMemo(() => (armsG ? createFPRig(armsG.scene) : null), [armsG]);
  if (!world || !jeepRig || !rig || !squad) return <AbsoluteFill />;
  world.waveTower?.(t + 20, 1.4);
  const S = JEEP_STUCK;
  // body matrix of the jeep over time: approach straight down the road, swerve left into the ditch, drop, rock
  const bodyAt = (T: number) => {
    let pos: THREE.Vector3, yaw = 0, roll = 0, pitch = 0, drop = 0;
    if (mode === "approach") {
      pos = new THREE.Vector3(-18.4, 0, -78 + T * 15);
    } else {
      const k = sm(T / dropAt);
      const start = new THREE.Vector3(-18.4, 0, S.pos.z - 10.5);
      pos = start.clone().lerp(S.pos, k);
      pos.z = start.z + (S.pos.z - start.z) * Math.min(1, T / dropAt);
      yaw = S.yaw * sm((T - 0.15) / (dropAt - 0.15));
      const d = sm((T - dropAt) / 0.12);
      const bounce = T > dropAt ? Math.exp(-(T - dropAt) * 7) * Math.sin((T - dropAt) * 28) : 0;
      roll = S.roll * d + bounce * 0.025;
      pitch = S.pitch * d + bounce * 0.02;
      drop = S.drop * d + bounce * 0.02;
      // gunning it: forward, back
      const rock = (a: number) => (T > a ? Math.exp(-(T - a) * 3) * Math.sin(Math.min(Math.PI, (T - a) * 5)) : 0);
      const fwd = new THREE.Vector3(Math.sin(yaw), 0, Math.cos(yaw));
      pos.addScaledVector(fwd, 0.14 * rock(revAt[0]) - 0.14 * rock(revAt[1]));
      pitch += 0.02 * (rock(revAt[0]) - rock(revAt[1]));
    }
    return new THREE.Matrix4().compose(pos.add(new THREE.Vector3(0, -drop, 0)), new THREE.Quaternion().setFromEuler(new THREE.Euler(pitch, yaw, roll, "YXZ")), new THREE.Vector3(1, 1, 1));
  };
  const jolt = (T: number) => (mode === "ditch" && T > dropAt ? Math.exp(-(T - dropAt) * 6) : 0);
  const camAtT = (T: number): Cam => {
    const c = driverCam(jeepRig, bodyAt(T), T, mode === "ditch" ? 0.12 * sm((T - dropAt - 0.3) / 0.4) : 0, 0.2 + jolt(T) * 2.5);
    return c;
  };
  const B = bodyAt(t);
  B.decompose(jeepRig.root.position, jeepRig.root.quaternion, jeepRig.root.scale);
  jeepRig.body.position.y = jeepRig.bodyY;
  jeepRig.wheel.position.y = jeepRig.wheelY;
  jeepRig.wheel.quaternion.copy(jeepRig.wheelQ).multiply(new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0, 1, 0), mode === "ditch" ? 0.5 * sm((t - 0.1) / 0.4) * (1 - sm((t - dropAt) / 0.3)) : 0));
  const spin = mode === "approach" ? t * 15 / 0.39 : Math.min(t, dropAt) * 15 / 0.39 + (t > revAt[0] ? (t - revAt[0]) * 30 : 0);
  for (const ty of jeepRig.tyres) ty.o.quaternion.copy(ty.q).multiply(new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(1, 0, 0), spin));
  jeepRig.root.updateMatrixWorld(true);
  const cam = camAtT(t);
  const camera = makeCamera(cam);
  const gripL = wheelGrip(jeepRig, bodyAt, camAtT, "L"), gripR = wheelGrip(jeepRig, bodyAt, camAtT, "R");
  const lever = (T: number) => new THREE.Vector3(0.1, 0.78, -0.12).applyMatrix4(bodyAt(T)).applyMatrix4(makeCamera(camAtT(T)).matrixWorldInverse).toArray() as V3;
  const tracks: { L: HandTrack; R: HandTrack } = {
    L: [{ t: 0, to: gripL, pose: "wheel", contact: true, dur: 0.01 }],
    R:
      mode === "ditch"
        ? [
            { t: 0, to: gripR, pose: "wheel", contact: true, dur: 0.01 },
            { t: revAt[0] - 0.35, to: lever, pose: "grip", dur: 0.3, aim: { fingers: [-0.1, -0.75, -0.65], palm: [-0.85, -0.2, 0.3] } },
            { t: revAt[1] - 0.12, to: (T: number) => { const p = lever(T); return [p[0], p[1], p[2] + 0.06] as V3; }, pose: "grip", dur: 0.14, aim: { fingers: [-0.1, -0.75, -0.65], palm: [-0.85, -0.2, 0.3] } },
          ]
        : [{ t: 0, to: gripR, pose: "wheel", contact: true, dur: 0.01 }],
  };
  rig.pose(t, camera, tracks);
  const tau = mode === "ditch" ? t - 3.06 - 1.28 : -6; // the squad is still far off while he drives in
  const objs: THREE.Object3D[] = [world.g, jeepRig.root, rig.root, ...poseSquad(squad, Math.max(0, tau + SQUAD_T0))];
  return (
    <NkLook t={t}>
      <Stage3D cam={cam} lights="none" env={0.5} fog={{ color: "#B3BABD", near: 30, far: 300 }}>
        <color attach="background" args={["#B3BABD"]} />
        <OutdoorLights focus={cam.pos} sun={[-26, 34, -14]} />
        {objs.map((o, i) => (
          <primitive key={i} object={o} />
        ))}
      </Stage3D>
    </NkLook>
  );
};

// ================================================================== the helicopter, the operating table, the last shots
/** on the stretcher, carried across the yard: the Black Hawk drops in over the south hall */
export const NkHeli: React.FC = () => {
  const { f, fps } = useBlockTime();
  const t = f / fps;
  const world = usePanmunjom();
  const heliG = useGLB(M + "heli.glb");
  const heli = useMemo(() => {
    if (!heliG) return null;
    const h = heliG.scene.clone(true);
    h.traverse((o) => ((o as THREE.Mesh).isMesh ? ((o as THREE.Mesh).castShadow = true) : null));
    h.updateMatrixWorld(true);
    const main = h.getObjectByName("main_rotor") ?? null, tail = h.getObjectByName("tail_rotor") ?? null;
    if (main) {
      // rotor blur disc so the blades read as spinning at 60 fps
      const b = new THREE.Box3().setFromObject(main);
      const c = b.getCenter(new THREE.Vector3()), sz = b.getSize(new THREE.Vector3());
      const disc = new THREE.Mesh(new THREE.CircleGeometry(Math.max(sz.x, sz.z) / 2, 64), new THREE.MeshBasicMaterial({ color: "#2C2E2E", transparent: true, opacity: 0.16, depthWrite: false, side: THREE.DoubleSide }));
      disc.rotation.x = -Math.PI / 2;
      disc.position.copy(c);
      h.add(disc);
    }
    const size = new THREE.Box3().setFromObject(h).getSize(new THREE.Vector3());
    if (typeof console !== "undefined") console.log("HELI size", size.toArray().map((v) => v.toFixed(1)).join(" "));
    return { h, main, tail, mq: main?.quaternion.clone(), tq: tail?.quaternion.clone() };
  }, [heliG]);
  if (!world || !heli) return <AbsoluteFill />;
  world.waveTower?.(t + 50, 1.4);
  const hp = new THREE.Vector3(19.5, 9.2 - t * 1.1, 31.5);
  heli.h.position.copy(hp);
  heli.h.rotation.set(0.05 + Math.sin(t * 1.3) * 0.015, -2.5 + t * 0.06, -0.04 + Math.sin(t * 0.9) * 0.02);
  if (heli.main && heli.mq) heli.main.quaternion.copy(heli.mq).multiply(new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0, 1, 0), t * 29));
  if (heli.tail && heli.tq) heli.tail.quaternion.copy(heli.tq).multiply(new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(1, 0, 0), t * 47));
  heli.h.updateMatrixWorld(true);
  // carried feet first: low eyes, the stretcher sways with the bearers' steps, rotor wash shakes it
  const step = t * 4.2;
  const eye = new THREE.Vector3(11.5 + t * 0.9, 1.0 + Math.abs(Math.sin(step)) * 0.035, 19.5 + t * 0.6);
  const shake = 0.02 * Math.sin(t * 37) + 0.012 * Math.sin(t * 53);
  const cam: Cam = { pos: eye.toArray() as V3, target: [hp.x - 1.5, hp.y - 0.4 + shake * 8, hp.z - 1], fov: 68, roll: Math.sin(step) * 0.035 + shake };
  return (
    <AbsoluteFill>
      <NkLook t={t} vignette={0.55}>
        <Stage3D cam={cam} lights="none" env={0.5} fog={{ color: "#B3BABD", near: 40, far: 300 }}>
          <color attach="background" args={["#B3BABD"]} />
          <OutdoorLights focus={[hp.x, 0, hp.z - 8]} sun={[-26, 34, -14]} />
          <primitive object={world.g} />
          <primitive object={heli.h} />
        </Stage3D>
      </NkLook>
      <AbsoluteFill style={{ backdropFilter: `blur(${1.2 + Math.abs(Math.sin(t * 3)) * 1.2}px)`, pointerEvents: "none" }} />
    </AbsoluteFill>
  );
};

function tileTexture() {
  const c = document.createElement("canvas");
  c.width = c.height = 512;
  const g = c.getContext("2d")!;
  g.fillStyle = "#AEB9B3";
  g.fillRect(0, 0, 512, 512);
  for (let i = 0; i < 4000; i++) {
    g.fillStyle = `rgba(60,70,66,${Math.random() * 0.05})`;
    g.fillRect(Math.random() * 512, Math.random() * 512, 2, 2);
  }
  g.strokeStyle = "#7E8984";
  g.lineWidth = 6;
  for (let i = 0; i <= 512; i += 128) {
    g.beginPath(); g.moveTo(i, 0); g.lineTo(i, 512); g.stroke();
    g.beginPath(); g.moveTo(0, i); g.lineTo(512, i); g.stroke();
  }
  const t = new THREE.CanvasTexture(c);
  t.wrapS = t.wrapT = THREE.RepeatWrapping;
  t.repeat.set(4, 4);
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}
/** patient monitor screen, redrawn per frame: ECG trace, HR, falling blood pressure */
function drawMonitor(g: CanvasRenderingContext2D, t: number) {
  const W = 512, H = 384;
  g.fillStyle = "#050807";
  g.fillRect(0, 0, W, H);
  g.strokeStyle = "rgba(60,255,140,0.12)";
  g.lineWidth = 1;
  for (let x = 0; x < W; x += 32) { g.beginPath(); g.moveTo(x, 0); g.lineTo(x, H); g.stroke(); }
  const hr = 138;
  const beat = 60 / hr;
  g.strokeStyle = "#4CFF8E";
  g.lineWidth = 4;
  g.beginPath();
  for (let x = 0; x < 330; x++) {
    const tt = t - (330 - x) / 220;
    const ph = (((tt % beat) + beat) % beat) / beat;
    let y = 0;
    if (ph < 0.06) y = -Math.sin((ph / 0.06) * Math.PI) * 10;
    else if (ph < 0.1) y = 0;
    else if (ph < 0.12) y = 14;
    else if (ph < 0.15) y = -78;
    else if (ph < 0.18) y = 26;
    else if (ph < 0.42 && ph > 0.28) y = -Math.sin(((ph - 0.28) / 0.14) * Math.PI) * 16;
    const yy = 120 + y;
    if (x === 0) g.moveTo(x + 10, yy);
    else g.lineTo(x + 10, yy);
  }
  g.stroke();
  g.font = "bold 74px 'JetBrains Mono', monospace";
  g.fillStyle = "#4CFF8E";
  g.fillText(String(hr + Math.round(Math.sin(t * 2) * 2)), 350, 140);
  g.font = "bold 26px 'JetBrains Mono', monospace";
  g.fillText("HR", 352, 60);
  g.fillStyle = "#FF5A4E";
  g.fillText("NIBP", 24, 250);
  g.font = "bold 66px 'JetBrains Mono', monospace";
  const sys = Math.round(78 - Math.min(14, t * 4)), dia = Math.round(44 - Math.min(9, t * 2.5));
  g.fillText(`${sys}/${dia}`, 24, 326);
  g.fillStyle = "#58C8FF";
  g.font = "bold 26px 'JetBrains Mono', monospace";
  g.fillText("SpO2", 352, 250);
  g.font = "bold 66px 'JetBrains Mono', monospace";
  g.fillText(String(86 - Math.min(4, Math.floor(t * 1.4))), 352, 326);
  if (Math.floor(t * 2.4) % 2 === 0) {
    g.fillStyle = "#FF3B30";
    g.fillRect(W - 40, 14, 26, 26);
  }
}
const SURG_CAM: Cam = { pos: [0.02, 1.02, 0.12], target: [0.18, 3.0, -0.95], fov: 66, roll: 0.12 };
/** on the operating table, looking up: the surgical lamp, the monitor, a blood bag; fading in and out, then white */
export const NkSurgery: React.FC<{ whiteAt?: number }> = ({ whiteAt = 2.96 }) => {
  const { f, fps } = useBlockTime();
  const t = f / fps;
  const set = useMemo(() => {
    const g = new THREE.Group();
    const ceil = new THREE.Mesh(new THREE.PlaneGeometry(10, 10), new THREE.MeshStandardMaterial({ map: tileTexture(), roughness: 0.85 }));
    ceil.rotation.x = Math.PI / 2;
    ceil.position.y = 3.05;
    g.add(ceil);
    const wallMat = new THREE.MeshStandardMaterial({ color: "#7F948C", roughness: 0.9 });
    for (const [x, z, ry] of [[0, -3.2, 0], [3.2, 0, -Math.PI / 2], [-3.2, 0, Math.PI / 2]] as [number, number, number][]) {
      const w = new THREE.Mesh(new THREE.PlaneGeometry(6.4, 3.1), wallMat);
      w.position.set(x, 1.55, z);
      w.rotation.y = ry;
      g.add(w);
    }
    // fluorescent panels further up the ceiling
    const tube = new THREE.MeshStandardMaterial({ color: "#FFFFFF", emissive: "#EAF4FF", emissiveIntensity: 1.1 });
    for (const [x, z] of [[-1.2, -2.0], [1.3, -2.1]]) {
      const p = new THREE.Mesh(new THREE.PlaneGeometry(0.6, 1.2), tube);
      p.rotation.x = Math.PI / 2;
      p.position.set(x, 3.04, z);
      g.add(p);
    }
    const base = makeCamera(SURG_CAM);
    const W = (x: number, y: number, z: number) => new THREE.Vector3(x, y, z).applyMatrix4(base.matrixWorld);
    const eye = new THREE.Vector3(...SURG_CAM.pos);
    const rod = (a: THREE.Vector3, b: THREE.Vector3, r: number, mat: THREE.Material) => {
      const m = new THREE.Mesh(new THREE.CylinderGeometry(r, r, a.distanceTo(b), 12), mat);
      m.position.copy(a).add(b).multiplyScalar(0.5);
      m.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), b.clone().sub(a).normalize());
      return m;
    };
    // the surgical lamp: a wide head with seven LED cells turned to the table, on an arm from the ceiling
    const metal = new THREE.MeshStandardMaterial({ color: "#D4D8DA", metalness: 0.55, roughness: 0.35 });
    const head = new THREE.Group();
    head.add(new THREE.Mesh(new THREE.CylinderGeometry(0.4, 0.44, 0.13, 48), metal));
    const rim = new THREE.Mesh(new THREE.TorusGeometry(0.42, 0.025, 10, 48), new THREE.MeshStandardMaterial({ color: "#9EA6AA", metalness: 0.6, roughness: 0.3 }));
    rim.rotation.x = Math.PI / 2;
    rim.position.y = -0.06;
    head.add(rim);
    const led = new THREE.MeshStandardMaterial({ color: "#FFFFFF", emissive: "#FFF6E6", emissiveIntensity: 1.6 });
    for (let i = 0; i < 7; i++) {
      const a = (i / 6) * Math.PI * 2;
      const r = i === 6 ? 0 : 0.24;
      const cell = new THREE.Mesh(new THREE.CircleGeometry(0.08, 32), led);
      cell.rotation.x = Math.PI / 2;
      cell.position.set(Math.cos(a) * r, -0.067, Math.sin(a) * r);
      head.add(cell);
    }
    const hp = W(0.1, 0.22, -1.7);
    head.position.copy(hp);
    head.lookAt(eye);
    head.rotateX(-Math.PI / 2 + 0.3);
    g.add(head);
    const joint = new THREE.Vector3(hp.x + 0.35, 2.75, hp.z - 0.35);
    g.add(rod(hp.clone().add(new THREE.Vector3(0, 0.08, 0)), joint, 0.035, metal), rod(joint, new THREE.Vector3(joint.x, 3.05, joint.z), 0.07, metal));
    const halo = new THREE.Sprite(new THREE.SpriteMaterial({ map: glow("halo2", [[0, "rgba(255,250,240,0.85)"], [0.3, "rgba(255,246,230,0.25)"], [1, "rgba(255,240,220,0)"]]), blending: THREE.AdditiveBlending, depthWrite: false, transparent: true }));
    halo.position.copy(hp).lerp(eye, 0.06);
    halo.scale.setScalar(1.15);
    g.add(halo);
    const l = new THREE.SpotLight("#FFF6E8", 9, 6, 0.6, 0.5, 1.4);
    l.position.copy(hp);
    l.target.position.set(0, 0.9, 0.1);
    g.add(l, l.target);
    // monitor low on the right, turned to the patient
    const mc = document.createElement("canvas");
    mc.width = 512;
    mc.height = 384;
    const mtex = new THREE.CanvasTexture(mc);
    mtex.colorSpace = THREE.SRGBColorSpace;
    const bezel = new THREE.MeshStandardMaterial({ color: "#2B2F31", roughness: 0.5 });
    const mon = new THREE.Mesh(new THREE.BoxGeometry(0.5, 0.38, 0.07), [bezel, bezel, bezel, bezel, new THREE.MeshBasicMaterial({ map: mtex }), bezel]);
    mon.position.copy(W(0.2, -0.4, -1.05));
    mon.lookAt(eye);
    g.add(mon);
    g.add(rod(mon.position.clone(), new THREE.Vector3(mon.position.x + 0.5, 3.05, mon.position.z), 0.025, metal));
    // blood bag on the IV pole at the left
    const bp = W(-0.3, 0.24, -1.3);
    g.add(rod(new THREE.Vector3(bp.x, bp.y + 0.12, bp.z), new THREE.Vector3(bp.x, 3.05, bp.z), 0.012, metal));
    const bag = new THREE.Mesh(new THREE.CapsuleGeometry(0.07, 0.16, 6, 16), new THREE.MeshStandardMaterial({ color: "#7C0F14", roughness: 0.25, transparent: true, opacity: 0.92 }));
    bag.scale.set(1, 1, 0.45);
    bag.position.copy(bp);
    g.add(bag);
    const tubeEnd = W(-0.25, -0.75, -0.6);
    g.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(bp.x, bp.y - 0.15, bp.z), bp.clone().lerp(tubeEnd, 0.5).add(new THREE.Vector3(0, -0.1, 0)), tubeEnd]), new THREE.LineBasicMaterial({ color: "#5A1014" })));
    return { g, mc, mtex, bag };
  }, []);
  drawMonitor(set.mc.getContext("2d")!, t);
  set.mtex.needsUpdate = true;
  set.bag.rotation.z = Math.sin(t * 1.1) * 0.05;
  const drift = Math.sin(t * 0.8);
  const cam: Cam = { ...SURG_CAM, target: [SURG_CAM.target[0] + drift * 0.1, SURG_CAM.target[1], SURG_CAM.target[2] + Math.sin(t * 0.6) * 0.08], roll: (SURG_CAM.roll ?? 0) + drift * 0.05 };
  const white = sm((t - whiteAt) / 0.5);
  // drifting in and out: slow blinks, the picture swims
  const lid = Math.max(...[0.85, 2.1].map((b) => Math.max(0, 1 - Math.abs(t - b) / 0.32)));
  const blur = 1.5 + Math.abs(Math.sin(t * 1.7)) * 2.2 + lid * 3;
  return (
    <AbsoluteFill>
      <NkLook t={t} vignette={0.7}>
        <Stage3D cam={cam} lights="none" env={0.25}>
          <color attach="background" args={["#7F948C"]} />
          <ambientLight intensity={0.55} color="#DDE8E4" />
          <primitive object={set.g} />
        </Stage3D>
      </NkLook>
      <AbsoluteFill style={{ backdropFilter: `blur(${blur}px)`, pointerEvents: "none" }} />
      <AbsoluteFill style={{ background: `linear-gradient(180deg, #000 ${lid * 48}%, rgba(0,0,0,0) ${lid * 48 + 14}%, rgba(0,0,0,0) ${100 - lid * 48 - 14}%, #000 ${100 - lid * 48}%)`, opacity: lid > 0.01 ? 1 : 0, pointerEvents: "none" }} />
      <AbsoluteFill style={{ background: "#F7F3EA", opacity: white * 0.9, pointerEvents: "none" }} />
    </AbsoluteFill>
  );
};

/** the last shots: guards facing each other over the line between the blue huts. view "line" = through the gap, "wide" = drone */
export const NkOutro: React.FC<{ view?: "line" | "wide" }> = ({ view = "wide" }) => {
  const { f, fps } = useBlockTime();
  const t = f / fps;
  const world = usePanmunjom();
  const kpaG = useGLB(M + "soldier_mx_kpa.glb");
  const rokG = useGLB(M + "soldier_mx_rok.glb");
  const meta = useClipMeta();
  const progsK = useMemo<Program[]>(
    () => [
      { start: [27.2, 0, -7.6], yaw: 0, segs: [{ clip: "rifle_idle", at: 0, offset: 2 }] },
      { start: [18.4, 0, -7.9], yaw: 0, segs: [{ clip: "rifle_idle", at: 0, offset: 5 }] },
      { start: [23.0, 0, -43.5], yaw: 0, segs: [{ clip: "rifle_idle", at: 0, offset: 7 }] },
    ],
    [],
  );
  const progsR = useMemo<Program[]>(
    () => [
      { start: [26.75, 0, 4.6], yaw: Math.PI, segs: [{ clip: "rifle_idle", at: 0, offset: 1 }] },
      { start: [17.75, 0, 4.2], yaw: Math.PI, segs: [{ clip: "rifle_idle", at: 0, offset: 3 }] },
    ],
    [],
  );
  const kpa = useSquad(kpaG, meta, progsK);
  const rok = useSquad(rokG, meta, progsR);
  if (!world || !kpa || !rok) return <AbsoluteFill />;
  world.waveTower?.(t + 40, 1.4);
  const objs = [world.g, ...poseSquad(kpa, t), ...poseSquad(rok, t)];
  const cam: Cam =
    view === "line"
      ? camAt([{ t: 0, pos: [27.9, 1.6, 13.5], target: [27.3, 1.35, -10], fov: 40 }, { t: 3, pos: [27.85, 1.6, 12.2], target: [27.3, 1.35, -10], fov: 40, ease: "linear" }], t)
      : camAt([{ t: 0, pos: [6, 15, 31], target: [24, 0.5, -3], fov: 46 }, { t: 9, pos: [10, 12.5, 27], target: [24, 0.5, -3], fov: 46, ease: "linear" }], t);
  return (
    <NkLook t={t}>
      <Stage3D cam={cam} lights="none" env={0.5} fog={{ color: "#B3BABD", near: 40, far: 320 }}>
        <color attach="background" args={["#B3BABD"]} />
        <OutdoorLights focus={view === "line" ? [27, 0, 0] : [22, 0, 0]} sun={[-26, 34, -14]} />
        {objs.map((o, i) => (
          <primitive key={i} object={o} />
        ))}
      </Stage3D>
    </NkLook>
  );
};
