/**
 * Every shot of the "podezd" horror reel (part 1). One block, `shot` picks the set, actors, poses, hands, phone,
 * lights and camera. `ev` carries event times (seconds from the scene start, picture lead included) computed by the
 * storyboard from the voice, so actions land on the words.
 */
import React, { useMemo } from "react";
import { AbsoluteFill } from "remotion";
import * as THREE from "three";
import { RoundedBoxGeometry } from "three/examples/jsm/geometries/RoundedBoxGeometry.js";
import { useBlockTime } from "../core/context";
import { camAt, makeCamera, type Cam, type CamKey, type V3 } from "./core";
import { createFPRig, type HandTrack } from "./fphands";
import { createHuman, mix3, poseChair, poseCornerCry, poseCrouch, poseFloorCover, posePoint, poseSitHoldHead, type Human, type Pose } from "./human";
import { useGLB } from "./nk";
import { aimFlashlight, PzFrame, stepA, useFlashlight, usePzTextures, type CharName } from "./podezd";
import { applyLamps, BOOTH, buildBedroom, buildBlock, buildBooth, buildDescent, buildLair, buildPipeCorner, buildStairwell, DOWN, FLOOR, RISE, type Lamp, type Tex } from "./podezdSets";
import { psxify } from "./psx";

const sm = (x: number) => {
  const k = Math.min(1, Math.max(0, x));
  return k * k * (3 - 2 * k);
};
const P = "projects/podezd/";

// ------------------------------------------------------------------ the phone (a 2004 candybar with a torch LED)
export function phoneScreen(g: CanvasRenderingContext2D, mode: string, t: number, o: { bars?: number; timer?: number } = {}) {
  const W = 96, H = 64;
  g.fillStyle = "#9FB94C";
  g.fillRect(0, 0, W, H);
  g.fillStyle = "#18210C";
  const bars = o.bars ?? 5;
  for (let i = 0; i < 5; i++) if (i < bars) g.fillRect(2, 20 - i * 4, 3 + i, 2);
  g.fillRect(88, 4, 6, 14);
  g.fillStyle = "#9FB94C";
  g.fillRect(89, 5, 4, 12 - 9);
  g.fillStyle = "#18210C";
  g.textAlign = "center";
  if (mode === "clock") {
    g.font = "bold 22px monospace";
    g.fillText("03:17", 50, 38);
    g.font = "bold 9px monospace";
    g.fillText("ПТ 26.11", 50, 54);
  } else if (mode === "dial" || mode === "call") {
    g.font = "bold 20px monospace";
    g.fillText("102", 50, 32);
    g.font = "bold 10px monospace";
    const tm = Math.floor(o.timer ?? 0);
    g.fillText(mode === "dial" ? "Вызов" + ".".repeat(1 + (Math.floor(t * 3) % 3)) : `00:${String(tm).padStart(2, "0")}`, 50, 50);
  } else if (mode === "nosig") {
    g.font = "bold 12px monospace";
    g.fillText("Нет сети", 50, 34);
    g.font = "bold 9px monospace";
    g.fillText("Фонарик", 50, 52);
  } else if (mode === "uk" || mode === "ukcall") {
    g.font = "bold 10px monospace";
    g.fillText("ЖИЛСЕРВИС", 50, 26);
    g.font = "bold 9px monospace";
    g.fillText("УК Дом 12", 50, 38);
    g.font = "bold 10px monospace";
    const tm = Math.floor(o.timer ?? 0);
    g.fillText(mode === "uk" ? "Вызов" + ".".repeat(1 + (Math.floor(t * 3) % 3)) : `00:${String(tm).padStart(2, "0")}`, 50, 54);
  } else if (mode === "torch") {
    g.font = "bold 10px monospace";
    g.fillText("Фонарик", 50, 36);
    g.fillText("ВКЛ", 50, 50);
  }
}
export function buildPhone() {
  const g = new THREE.Group();
  const body = new THREE.Mesh(new RoundedBoxGeometry(0.046, 0.106, 0.02, 3, 0.008), new THREE.MeshStandardMaterial({ color: "#2B3340", roughness: 0.45, metalness: 0.25 }));
  g.add(body);
  const c = document.createElement("canvas");
  c.width = 96;
  c.height = 64;
  const ctx = c.getContext("2d")!;
  const tex = new THREE.CanvasTexture(c);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.magFilter = THREE.NearestFilter;
  const scrM = new THREE.MeshStandardMaterial({ map: tex, emissiveMap: tex, emissive: "#FFFFFF", emissiveIntensity: 0.9, roughness: 0.3 });
  const scr = new THREE.Mesh(new THREE.PlaneGeometry(0.03, 0.02), scrM);
  scr.position.set(0, 0.024, 0.0105);
  g.add(scr);
  const kc = document.createElement("canvas");
  kc.width = 64;
  kc.height = 96;
  const kg = kc.getContext("2d")!;
  kg.fillStyle = "#3C4452";
  kg.fillRect(0, 0, 64, 96);
  kg.fillStyle = "#8C97A6";
  for (let r = 0; r < 4; r++) for (let cc = 0; cc < 3; cc++) kg.fillRect(6 + cc * 19, 30 + r * 16, 14, 11);
  kg.beginPath();
  kg.ellipse(32, 14, 20, 9, 0, 0, 7);
  kg.fill();
  const keys = new THREE.Mesh(new THREE.PlaneGeometry(0.04, 0.056), new THREE.MeshStandardMaterial({ map: new THREE.CanvasTexture(kc), roughness: 0.6 }));
  keys.position.set(0, -0.022, 0.0103);
  g.add(keys);
  const led = new THREE.Mesh(new THREE.SphereGeometry(0.0028, 8, 6), new THREE.MeshStandardMaterial({ color: "#FFFFFF", emissive: "#EAF2FF", emissiveIntensity: 0 }));
  led.position.set(0, 0.053, 0.0);
  g.add(led);
  return { g, ctx, tex, led, scrM };
}

// ------------------------------------------------------------------ shared rigs
export const useFP = () => {
  const arms = useGLB("models/fp_arms.glb");
  return useMemo(() => {
    if (!arms) return null;
    const rig = createFPRig(arms.scene);
    rig.meshes.forEach((m) => {
      const mats = Array.isArray(m.material) ? m.material : [m.material];
      mats.forEach((mt) => {
        if (mt.name.includes("sleeve")) (mt as THREE.MeshStandardMaterial).color = new THREE.Color("#5E6676");
      });
    });
    psxify(rig.root);
    return rig;
  }, [arms]);
};
/** each scene instance gets its own clone (two scenes are mounted at once during a transition) */
export const useActor = (name: CharName) => {
  const g = useGLB(P + "models/" + name + ".glb");
  return useMemo(() => {
    if (!g) return null;
    const h = createHuman(g.scene, name === "him" ? { tint: "#8E918C", selfShadow: false } : {});
    psxify(h.root);
    return h;
  }, [g]);
};

const toCam = (camera: THREE.Camera, p: THREE.Vector3): V3 => p.clone().applyMatrix4(camera.matrixWorldInverse).toArray() as V3;

// ------------------------------------------------------------------ actor marks (stairwell coordinates)
const LYUDA: { pos: V3; yaw: number } = { pos: [0.98, FLOOR(2) + RISE, 5.02], yaw: Math.PI / 4 };
const DED: { pos: V3; yaw: number } = { pos: [-0.98, -RISE, 5.0], yaw: (3 * Math.PI) / 4 };
const SEREGA_STEP = stepA(2, 4);
const SEREGA: { pos: V3; yaw: number } = { pos: [0.72, SEREGA_STEP.y, SEREGA_STEP.z + 0.04], yaw: Math.PI };

type Out = { cam: Cam; objs: THREE.Object3D[]; lamps?: { flicker?: number; breath?: number; dim?: number }; flash?: number; fog?: { color: string; near: number; far: number }; exposure?: number; overlay?: React.ReactNode; wear?: number; light?: React.ReactNode };
type SetName = "stair" | "boothB" | "boothA" | "descent" | "lair" | "bedroom" | "pipe" | "block";

const SHOT_SETS: Record<string, SetName[]> = {
  hook: ["stair"], moan: ["stair"], block: ["block"], upgap: ["stair"], landing: ["stair"], boothWindow: ["stair", "boothB"], journal: ["stair", "boothB"],
  serega: ["stair"], ask: ["stair"], graffiti: ["stair"], crane: ["stair"], listen: ["stair"], pipe: ["pipe"], upfast: ["stair"], breath: ["stair"],
  wake: ["bedroom"], bed: ["bedroom"], railing: ["stair"], point: ["stair"], boothEnter: ["stair", "boothA"], journalFloor: ["stair", "boothA"],
  door: ["stair", "boothA"], call: ["stair", "boothA"], cry: ["stair", "boothA"], torch: ["stair", "boothA"], nosig: ["descent"], count: ["descent"],
  scratches: ["descent"], doorway: ["lair"], him: ["lair"], face: ["lair"], scarf: ["lair"], step: ["lair"], lower: ["lair"],
};

export const PzShot: React.FC<{ shot: string; ev?: Record<string, number>; cam?: CamKey[]; c0?: number }> = ({ shot, ev = {}, cam: camOverride, c0 = 0 }) => {
  const { f, fps } = useBlockTime();
  const t = f / fps;
  const tex = usePzTextures();
  const sets = SHOT_SETS[shot] ?? ["stair"];
  const fp = useFP();
  const serega = useActor("serega"), lyuda = useActor("lyuda"), ded = useActor("ded"), valya = useActor("valya"), him = useActor("him");
  const flash = useFlashlight();
  const phone = useMemo(buildPhone, []);
  const world = useMemo(() => {
    if (!tex) return null;
    const g = new THREE.Group();
    const w: {
      g: THREE.Group; lamps: Lamp[]; stair?: ReturnType<typeof buildStairwell>; booth?: ReturnType<typeof buildBooth>; descent?: ReturnType<typeof buildDescent>;
      lair?: ReturnType<typeof buildLair>; bedroom?: ReturnType<typeof buildBedroom>; pipe?: ReturnType<typeof buildPipeCorner>; block?: ReturnType<typeof buildBlock>;
    } = { g, lamps: [] };
    for (const s of sets) {
      if (s === "stair") {
        w.stair = buildStairwell(tex as Tex);
        g.add(w.stair.g);
        w.lamps.push(...w.stair.lamps);
        // cold night light through each half-landing window
        for (let n = 1; n < 5; n++) {
          const l = new THREE.PointLight("#6E86AE", 1.4, 4.5, 1.6);
          l.position.set(0.2, FLOOR(n) + RISE + 1.7, 5.0);
          g.add(l);
        }
      }
      if (s === "boothB" || s === "boothA") {
        w.booth = buildBooth(tex as Tex, s === "boothB" ? "before" : "after");
        g.add(w.booth.g);
        w.lamps.push(w.booth.lamp);
      }
      if (s === "descent") g.add((w.descent = buildDescent(tex as Tex)).g);
      if (s === "lair") g.add((w.lair = buildLair(tex as Tex)).g);
      if (s === "bedroom") g.add((w.bedroom = buildBedroom(tex as Tex)).g);
      if (s === "pipe") {
        w.pipe = buildPipeCorner(tex as Tex);
        g.add(w.pipe.g);
        w.lamps.push(w.pipe.lamp);
      }
      if (s === "block") g.add((w.block = buildBlock(tex as Tex)).g);
    }
    psxify(g);
    psxify(phone.g);
    return w;
  }, [tex, shot]); // eslint-disable-line react-hooks/exhaustive-deps
  if (!world || !fp || !serega || !lyuda || !ded || !valya || !him) return <AbsoluteFill style={{ background: "#000" }} />;

  const E = (k: string, d: number) => ev[k] ?? d;
  const objs: THREE.Object3D[] = [world.g];
  const add = (h: Human, p: Pose) => {
    h.pose(p);
    objs.push(h.root);
  };
  const keys = (k: CamKey[]) => camAt(camOverride ?? k, t);
  const K = (tt: number, pos: V3, target: V3, fov = 60, ease?: string): CamKey => ({ t: tt, pos, target, fov, ...(ease ? { ease } : {}) }) as CamKey;
  const hand = (cam: Cam, tracks: { L?: HandTrack; R?: HandTrack }) => {
    const camera = makeCamera(cam);
    fp.pose(t, camera, tracks);
    objs.push(fp.root);
    return camera;
  };
  const REST: HandTrack = [{ t: 0, to: "rest", dur: 0.01 }];
  /** phone in the right hand: "low" at the hip line, "show" turned to the eyes, "torch" held out and pointing ahead */
  const holdPhone = (cam: Cam, mode: "low" | "show" | "torch", screen: string, o: { bars?: number; timer?: number; led?: number; shake?: number; L?: HandTrack } = {}) => {
    const sh = (o.shake ?? 0) * 0.004;
    const tr = [Math.sin(t * 23) * sh, Math.sin(t * 31) * sh, 0];
    const at: Record<string, { p: V3; fingers: V3; palm: V3 }> = {
      low: { p: [0.12, -0.25, -0.36], fingers: [-0.85, 0.1, -0.45], palm: [0.1, 0.95, 0.2] },
      show: { p: [0.07, -0.15, -0.36], fingers: [-0.95, 0.2, -0.1], palm: [0.05, 0.45, 0.89] },
      torch: { p: [0.13, -0.17, -0.42], fingers: [-0.88, 0.05, -0.45], palm: [0.12, 0.98, 0.1] },
    };
    const a = at[mode];
    const camera = hand(cam, {
      L: o.L ?? REST,
      R: [{ t: 0, to: [a.p[0] + tr[0], a.p[1] + tr[1], a.p[2]], pose: { thumb: 0.25, index: 0.32, middle: 0.36, ring: 0.4, pinky: 0.44, spread: 0.05, oppose: 0.35 }, aim: { fingers: a.fingers, palm: a.palm }, dur: 0.01, contact: true }],
    });
    const { centre } = fp.graspCentre("R");
    // the phone follows the view: "torch" top end forward, screen up; "show" screen turned to the eyes
    const cq = camera.quaternion;
    const fwd = new THREE.Vector3(0, 0, -1).applyQuaternion(cq), cup = new THREE.Vector3(0, 1, 0).applyQuaternion(cq);
    const up = mode === "show" ? cup.clone().multiplyScalar(0.75).addScaledVector(fwd, 0.66).normalize() : fwd.clone().addScaledVector(cup, 0.12).normalize();
    const zt = mode === "show" ? fwd.clone().negate().addScaledVector(cup, 0.45).normalize() : cup.clone().addScaledVector(fwd, -0.35).normalize();
    const x = up.clone().cross(zt).normalize();
    const z = x.clone().cross(up).normalize();
    phone.g.quaternion.setFromRotationMatrix(new THREE.Matrix4().makeBasis(x, up, z));
    phone.g.position.copy(centre).addScaledVector(z, 0.014);
    phone.g.updateMatrixWorld(true);
    phoneScreen(phone.ctx, screen, t, o);
    phone.tex.needsUpdate = true;
    (phone.led.material as THREE.MeshStandardMaterial).emissiveIntensity = (o.led ?? 0) * 3;
    objs.push(phone.g);
    if (o.led) {
      const tip = new THREE.Vector3(0, 0.053, 0).applyMatrix4(phone.g.matrixWorld);
      flash.position.copy(tip);
      flash.target.position.set(...cam.target).add(new THREE.Vector3(Math.sin(t * 2.3) * 0.05, Math.sin(t * 3.1) * 0.03, 0));
      flash.target.updateMatrixWorld();
      flash.intensity = 24 * o.led;
    }
    return camera;
  };

  let out: Out;
  const sw = world.stair;
  switch (shot) {
    // ---------------------------------------------------------------- 1. hook: a neighbour facing the corner, the bulb flickers
    case "hook": {
      add(lyuda, poseCornerCry(lyuda, t, LYUDA));
      add(ded, poseCrouch(ded, t, DED));
      const cam = keys([K(0, [-0.6, FLOOR(2) + RISE + 1.6, 3.35], [0.98, FLOOR(2) + RISE + 1.3, 5.02], 58), K(3.6, [-0.05, FLOOR(2) + RISE + 1.56, 4.0], [0.98, FLOOR(2) + RISE + 1.3, 5.05], 52, "linear")]);
      out = { cam, objs, lamps: { flicker: 0.7 } };
      break;
    }
    // ---------------------------------------------------------------- 2. "и воют": the old man in the lobby corner, rocking
    case "moan": {
      add(ded, poseCrouch(ded, t, { ...DED, rock: 1.4 }));
      const cam = keys([K(0, [0.75, -RISE + 1.15, 3.75], [-0.95, -RISE + 0.5, 4.95], 52), K(2.2, [0.55, -RISE + 1.05, 3.95], [-0.95, -RISE + 0.5, 4.95], 48, "linear")]);
      out = { cam, objs, lamps: { flicker: 0.5 } };
      break;
    }
    // ---------------------------------------------------------------- 3. the Khrushchyovka at night, push to the 4th-floor window
    case "block": {
      const w = world.block!.dimaWin;
      const cam = keys([K(0, [w.x - 9, 3.2, 30], [w.x, w.y, 0], 46), K(3.8, [w.x - 4, 9.2, 13], [w.x, w.y, 0], 38, "linear")]);
      out = { cam, objs, fog: { color: "#06080C", near: 25, far: 140 }, exposure: 1.6, light: <color attach="background" args={["#0A0E16"]} /> };
      break;
    }
    // ---------------------------------------------------------------- 4. "лифта нет": up the stairwell well from the lobby
    case "upgap": {
      const cam: Cam = { pos: [0.0, -RISE + 1.4 + t * 0.15, 2.62], target: [0.02, 14, 2.64], fov: 70, roll: 0.25 + t * 0.12 };
      out = { cam, objs, lamps: { flicker: 0.2 } };
      break;
    }
    // ---------------------------------------------------------------- 5. green walls, a door, the 40-watt bulb
    case "landing": {
      const y = FLOOR(4);
      const cam = keys([K(0, [-0.95, y + 1.55, 1.42], [0.6, y + 1.15, 0.0], 60), K(1.6, [-0.8, y + 1.55, 1.35], [0.3, y + 1.6, 0.1], 58), K(3.4, [-0.65, y + 1.5, 1.3], [0.0, y + 2.42, 0.72], 52)]);
      out = { cam, objs, lamps: { flicker: 0.35 } };
      break;
    }
    // ---------------------------------------------------------------- 6. the booth window, Valentina Petrovna at her desk
    case "boothWindow": {
      const cam = keys([K(0, [-0.75, -RISE + 1.6, 4.95], [1.95, -RISE + 1.15, 4.35], 54), K(4.0, [-0.25, -RISE + 1.6, 4.55], [1.95, -RISE + 1.15, 4.35], 50, "linear")]);
      add(valya, poseChair(valya, t, { pos: [BOOTH.x0 + 1.02, BOOTH.y, 4.37], yaw: -Math.PI / 2, lookAt: cam.pos, look: 0.35 * sm(t / 2) }));
      out = { cam, objs, lamps: { flicker: 0.15 } };
      break;
    }
    // ---------------------------------------------------------------- 7. passing by: she follows me with her eyes and shuts the register
    case "journal": {
      const cam = keys([K(0, [0.35, -RISE + 1.62, 5.0], [1.6, -RISE + 1.0, 4.35], 58), K(3.8, [0.45, -RISE + 1.64, 3.75], [1.6, -RISE + 1.0, 4.3], 56, "linear")]);
      const close = sm((t - E("close", 2.3)) / 0.35);
      const b = world.booth!;
      b.journalCover.rotation.z = Math.PI * (1 - close);
      b.journal.updateMatrixWorld(true);
      const edge = new THREE.Vector3(0.42, 0.01, 0).applyMatrix4(b.journalCover.matrixWorld);
      const pose = poseChair(valya, t, { pos: [BOOTH.x0 + 1.02, BOOTH.y, 4.37], yaw: -Math.PI / 2, lookAt: cam.pos, look: 0.9 });
      valya.root.position.set(...pose.pos);
      valya.root.rotation.set(0, pose.yaw, 0);
      valya.root.updateMatrixWorld(true);
      const local = valya.root.worldToLocal(edge.clone());
      pose.arms!.R = { hand: mix3([-0.17, 0.82, 0.4], [local.x, local.y + 0.03, local.z], sm((t - E("close", 2.3) + 0.6) / 0.5)), pole: [-0.6, 0.5, -0.3], fingers: [0.2, -0.3, 1], palm: [0, -1, 0] };
      add(valya, pose);
      out = { cam, objs, lamps: { flicker: 0.15 } };
      break;
    }
    // ---------------------------------------------------------------- 8. Seryoga on the steps, holding his head
    case "serega": {
      add(serega, poseSitHoldHead(serega, t, { ...SEREGA, seat: 0, feetDrop: SEREGA_STEP.y - stepA(2, 2).y }));
      const cam = keys([K(0, [-0.55, FLOOR(2) + 1.15, 0.55], [0.72, SEREGA_STEP.y + 0.55, SEREGA_STEP.z], 58), K(5.2, [-0.2, FLOOR(2) + 1.2, 1.0], [0.72, SEREGA_STEP.y + 0.6, SEREGA_STEP.z], 52, "linear")]);
      out = { cam, objs, lamps: { flicker: 0.4 } };
      break;
    }
    // ---------------------------------------------------------------- 9. I ask; he slowly lifts his head toward me
    case "ask": {
      const s0 = stepA(2, 0);
      const cam: Cam = { pos: [0.42, s0.y + 1.5, 1.2], target: [0.72, SEREGA_STEP.y + 0.72, SEREGA_STEP.z], fov: 54, roll: Math.sin(t * 0.7) * 0.01 };
      const up = sm((t - E("up", 1.3)) / 1.4);
      add(serega, poseSitHoldHead(serega, t, { ...SEREGA, seat: 0, feetDrop: SEREGA_STEP.y - stepA(2, 2).y, lookUp: up, lookAt: cam.pos }));
      const camera = makeCamera(cam);
      const shoulder = serega.joint("LeftArm").add(new THREE.Vector3(0, 0.05, 0.04));
      hand(cam, { R: [{ t: 0, to: "rest", dur: 0.01 }, { t: 0.35, to: () => toCam(camera, shoulder), pose: "relaxed", aim: { fingers: [-0.2, 0.1, -1], palm: [0.1, -0.8, -0.5] }, dur: 0.7, contact: true }, { t: E("up", 1.3) + 0.6, to: "rest", dur: 0.6 }], L: REST });
      out = { cam, objs, lamps: { flicker: 0.4 } };
      break;
    }
    // ---------------------------------------------------------------- 10. «не смотри вниз» chalked on the wall
    case "graffiti": {
      const y = FLOOR(2) + RISE + 1.1;
      const pan = sm(t / 1.6);
      const cam: Cam = { pos: [0.2 + Math.sin(t * 0.9) * 0.02, y + 0.02, 4.4], target: [-1.25, y + 0.01, 4.82 - pan * 0.8], fov: 40, roll: -0.04 };
      out = { cam, objs, lamps: { flicker: 0.9 } };
      break;
    }
    // ---------------------------------------------------------------- 11. down the well past three of them, each in a corner
    case "crane": {
      add(lyuda, poseCornerCry(lyuda, t, LYUDA));
      add(serega, poseCornerCry(serega, t + 3, { pos: [-0.98, FLOOR(3) + RISE, 5.02], yaw: -Math.PI / 4, sob: 0.6 }));
      add(ded, poseCrouch(ded, t, DED));
      const y0 = FLOOR(3) + RISE + 1.45, y1 = -RISE + 1.0;
      const k = sm(t / 3.3);
      const y = y0 + (y1 - y0) * k;
      const cam: Cam = { pos: [0.0, y, 2.62], target: [0.0, y - 0.55, 5.3], fov: 80 };
      out = { cam, objs, lamps: { flicker: 0.3 } };
      break;
    }
    // ---------------------------------------------------------------- 12. "они слушают": close on her head in the corner
    case "listen": {
      const y = FLOOR(2) + RISE;
      const lk = sm((t - E("listen", 2.4)) / 0.8);
      add(lyuda, poseCornerCry(lyuda, t, { ...LYUDA, lookAt: [1.2, y - 3, 5.2], look: lk * 0.7, handsDown: lk }));
      const cam = keys([K(0, [0.42, y + 1.48, 4.62], [1.08, y + 1.42, 5.12], 50), K(3.8, [0.5, y + 1.46, 4.7], [1.08, y + 1.4, 5.12], 46, "linear")]);
      out = { cam, objs, lamps: { flicker: 0.25 } };
      break;
    }
    // ---------------------------------------------------------------- 13. knocking in the riser pipe
    case "pipe": {
      const hits = [E("k1", 0.85), E("k2", 1.35), E("k3", 1.95), E("k4", 2.85)];
      world.pipe!.knock(t, hits);
      const shake = Math.max(0, ...hits.map((h) => (t >= h ? Math.exp(-(t - h) * 12) : 0)));
      const cam = keys([K(0, [0.78, 0.38, 0.86], [0.16, 2.3, 0.16], 60), K(3.8, [0.66, 0.46, 0.74], [0.16, 2.4, 0.16], 58, "linear")]);
      cam.roll = (cam.roll ?? 0) + shake * 0.02 * Math.sin(t * 70);
      out = { cam, objs, lamps: { flicker: 0.2 + shake } };
      break;
    }
    // ---------------------------------------------------------------- 14. "этаж за этажом": rushing up the well
    case "upfast": {
      const k = sm(t / 1.25);
      const cam: Cam = { pos: [0.0, -0.4 + k * 9.5, 2.62], target: [0.02, 30, 2.64], fov: 72, roll: 0.3 + k * 0.6 };
      out = { cam, objs, lamps: { flicker: 0.6 } };
      break;
    }
    // ---------------------------------------------------------------- 15. all bulbs pulse together, "как будто кто-то дышит"
    case "breath": {
      add(serega, poseCornerCry(serega, t + 3, { pos: [1.0, FLOOR(3), 0.24], yaw: (3 * Math.PI) / 4, sob: 0.4 }));
      const cam = keys([K(0, [0.85, FLOOR(3) + RISE + 1.62, 5.0], [-0.3, FLOOR(3) + 1.1, 0.4], 64), K(5, [0.8, FLOOR(3) + RISE + 1.6, 4.85], [-0.2, FLOOR(3) + 1.25, 0.4], 60, "linear")]);
      out = { cam, objs, lamps: { breath: 1 } };
      break;
    }
    // ---------------------------------------------------------------- 16. woken by a scream
    case "wake": {
      const b = world.bedroom!;
      const open = sm((t - E("scream", 1.6)) / 0.15);
      const look = sm((t - E("scream", 1.6) - 0.1) / 0.5);
      const p = b.pillow.clone().add(new THREE.Vector3(0, 0.12, 0));
      const cam: Cam = { pos: p.toArray() as V3, target: mix3([p.x + 0.2, 2.6, p.z + 0.3], [b.door.x, 1.2, b.door.z], look * 0.7), fov: 66, roll: 0.6 * (1 - look) };
      out = { cam, objs, overlay: <Lids open={0.15 + 0.85 * open} />, exposure: 1.4 };
      break;
    }
    // ---------------------------------------------------------------- 17. sitting up in the dark, the phone says 03:17
    case "bed": {
      const b = world.bedroom!;
      const cam = keys([K(0, [b.pillow.x + 0.15, 0.95, b.pillow.z + 0.45], [b.door.x, 1.1, b.door.z], 62), K(3.9, [b.pillow.x + 0.2, 1.02, b.pillow.z + 0.55], [b.door.x - 0.1, 1.15, b.door.z], 58, "linear")]);
      holdPhone(cam, "low", "clock", { shake: 0.6 });
      out = { cam, objs, exposure: 1.45 };
      break;
    }
    // ---------------------------------------------------------------- 18. over the railing: they all turn up to me at once
    case "railing": {
      const turn = sm((t - E("turn", 3.3)) / 0.18);
      const cam: Cam = { pos: [0.0, FLOOR(4) + 1.42, 1.66], target: [0.05, FLOOR(2), 4.3], fov: 64, roll: Math.sin(t * 0.8) * 0.01 };
      add(lyuda, poseCornerCry(lyuda, t, { pos: [0.45, FLOOR(2) + RISE, 4.05], yaw: 0.2, lookAt: cam.pos, look: turn, handsDown: 1, sob: 0 }));
      add(serega, poseCornerCry(serega, t + 2, { pos: [-0.55, FLOOR(3) + RISE, 4.1], yaw: -0.15, lookAt: cam.pos, look: turn, handsDown: 1, sob: 0 }));
      add(ded, poseCornerCry(ded, t + 5, { pos: [0.05, -RISE, 4.15], yaw: 0, lookAt: cam.pos, look: turn, handsDown: 1, sob: 0 }));
      const camera = makeCamera(cam);
      const railL = new THREE.Vector3(-0.1, FLOOR(4) + 0.945, 1.47), railR = new THREE.Vector3(0.11, FLOOR(4) + 0.945, 1.47);
      hand(cam, {
        L: [{ t: 0, to: () => toCam(camera, railL), pose: "grip", aim: { fingers: [0.2, -0.3, -0.9], palm: [0.1, -0.9, 0.3] }, dur: 0.01, contact: true }],
        R: [{ t: 0, to: () => toCam(camera, railR), pose: "grip", aim: { fingers: [-0.2, -0.3, -0.9], palm: [-0.1, -0.9, 0.3] }, dur: 0.01, contact: true }],
      });
      out = { cam, objs, lamps: { flicker: 0.3 + turn * 0.5 } };
      break;
    }
    // ---------------------------------------------------------------- 19. Seryoga points down, silently
    case "point": {
      const pos: V3 = [-0.62, FLOOR(3) + RISE, 4.45];
      const cam = keys([K(0, [-0.68, FLOOR(3) + RISE + 0.75 + 1.5, 2.55], [-0.5, FLOOR(3) + RISE + 1.1, 4.45], 60), K(2.4, [-0.66, FLOOR(3) + RISE + 0.7 + 1.5, 2.62], [-0.45, FLOOR(3) + RISE + 0.95, 4.45], 58, "linear")]);
      const k = sm((t - E("point", 0.5)) / 0.7);
      const yaw = Math.PI;
      const wd = new THREE.Vector3(0.75, -0.55, -0.35).normalize();
      const cd = wd.clone().applyAxisAngle(new THREE.Vector3(0, 1, 0), -yaw);
      const p = posePoint(serega, t, { pos, yaw, dir: [cd.x, cd.y, cd.z], amount: k, lean: 0.15 });
      p.look = { at: cam.pos, w: 1 };
      add(serega, p);
      out = { cam, objs, lamps: { flicker: 0.4 }, exposure: 1.45 };
      break;
    }
    // ---------------------------------------------------------------- 20. the booth is open, the chair is down, the tea still steams
    case "boothEnter": {
      const b = world.booth!;
      b.updateSteam(t);
      const tea = E("tea", 2.85);
      const cam = keys([K(0, [1.0, -RISE + 1.6, 3.4], [2.5, -RISE + 0.35, 4.1], 60), K(tea - 0.2, [1.38, -RISE + 1.58, 3.55], [2.45, -RISE + 0.3, 4.15], 58), K(tea + 0.6, [1.5, -RISE + 1.42, 3.95], [1.67, -RISE + 0.84, 4.68], 46), K(5, [1.52, -RISE + 1.38, 4.02], [1.67, -RISE + 0.86, 4.68], 42)]);
      out = { cam, objs, lamps: { flicker: 0.5 } };
      break;
    }
    // ---------------------------------------------------------------- 21. the register on the floor; my name, circled in red
    case "journalFloor": {
      const b = world.booth!;
      b.journal.updateMatrixWorld(true);
      b.journalCover.rotation.z = Math.PI;
      const name = new THREE.Vector3(0.088, 0.03, 0.006).applyMatrix4(b.journal.matrixWorld);
      const z = E("name", 2.6);
      const cam = keys([K(0, [2.05, -RISE + 1.05, 2.85], [b.journal.position.x, -RISE, b.journal.position.z], 58), K(z - 0.1, [2.25, -RISE + 0.75, 3.05], [b.journal.position.x, -RISE, b.journal.position.z], 54), K(z + 0.5, [name.x - 0.12, -RISE + 0.38, name.z - 0.12], name.toArray() as V3, 40), K(5, [name.x - 0.1, -RISE + 0.34, name.z - 0.1], name.toArray() as V3, 36)]);
      out = { cam, objs, lamps: { flicker: 0.35 } };
      break;
    }
    // ---------------------------------------------------------------- 22. behind the wardrobe: a door that was never there
    case "door": {
      const cam = keys([K(0, [1.95, -RISE + 1.6, 4.45], [3.75, -RISE + 1.0, 2.5], 58), K(3.8, [2.7, -RISE + 1.6, 3.5], [3.75, -RISE + 0.95, 2.5], 52, "linear")]);
      out = { cam, objs, lamps: { flicker: 0.45 }, exposure: 1.55, light: <pointLight position={[4.3, -RISE - 0.9, 2.5]} color="#5D7396" intensity={4} distance={4} decay={1.4} /> };
      break;
    }
    // ---------------------------------------------------------------- 23-24. calling the police from the phone
    case "call": {
      const cam = keys([K(0, [2.9, -RISE + 1.58, 3.3], [3.75, -RISE + 0.9, 2.5], 60), K(2.8, [2.95, -RISE + 1.56, 3.2], [3.75, -RISE + 0.85, 2.5], 58, "linear")]);
      holdPhone(cam, "show", t < E("beeps", 1.7) ? "dial" : "call", { timer: Math.max(0, t - E("beeps", 1.7)), shake: 0.5 });
      out = { cam, objs, lamps: { flicker: 0.4 } };
      break;
    }
    case "cry": {
      const cam = keys([K(0, [3.0, -RISE + 1.55, 3.15], [3.75, -RISE + 0.8, 2.5], 52), K(3.3, [3.05, -RISE + 1.52, 3.05], [3.75, -RISE + 0.75, 2.5], 48, "linear")]);
      holdPhone(cam, "show", "call", { timer: 3 + t, shake: 1.6 });
      out = { cam, objs, lamps: { flicker: 0.8, dim: 0.7 } };
      break;
    }
    // ---------------------------------------------------------------- 25. torch on; the steps go down
    case "torch": {
      const on = sm((t - E("on", 0.3)) / 0.06);
      const cam = keys([K(0, [3.45, -RISE + 1.6, 2.5], [4.6, -RISE - 0.5, 2.5], 62), K(5, [4.15, -RISE + 1.28, 2.5], [5.2, -RISE - 1.4, 2.5], 60, "linear")]);
      holdPhone(cam, "torch", "torch", { led: on });
      out = { cam, objs, lamps: { flicker: 0.4, dim: 0.5 }, flash: on };
      break;
    }
    // ---------------------------------------------------------------- 26. the signal is gone
    case "nosig": {
      const bars = Math.max(0, 5 - Math.floor(sm((t - 0.3) / 1.2) * 6));
      const cam = keys([K(0, [0.36, 1.25, 0.72], [0.36, -1.3, 2.6], 64), K(2.4, [0.36, 1.0, 1.05], [0.36, -1.5, 2.65], 62, "linear")]);
      holdPhone(cam, "show", bars > 0 ? "torch" : "nosig", { bars, led: 1 });
      out = { cam, objs, flash: 1 };
      break;
    }
    // ---------------------------------------------------------------- 27. counting flights: -6
    case "count": {
      const L = DOWN.land * 2 + DOWN.run;
      const six = E("six", 0.9);
      const cam = keys([K(0, [-0.36, -7.0 + 1.62, 2.55], [-0.2, -8.4 + 1.4, 0.0], 62), K(six, [-0.36, -8.4 + 1.62, 0.95], [0.0, -8.4 + 1.55, 0.0], 56), K(4, [-0.3, -8.4 + 1.6, 0.75], [0.0, -8.4 + 1.55, 0.0], 50)]);
      void L;
      holdPhone(cam, "torch", "nosig", { bars: 0, led: 1 });
      out = { cam, objs, flash: 1 };
      break;
    }
    // ---------------------------------------------------------------- 28. scratches at the height of my face
    case "scratches": {
      const y = -RISE * 5 + RISE * 0.5 + 1.45;
      const cam = keys([K(0, [0.08, y + 0.06, 1.35], [0.7, y, 1.5], 54), K(3.6, [0.1, y + 0.04, 1.55], [0.7, y - 0.02, 1.85], 50, "linear")]);
      holdPhone(cam, "torch", "nosig", { bars: 0, led: 1, shake: 0.8 });
      out = { cam, objs, flash: 1 };
      break;
    }
    // ---------------------------------------------------------------- 29. the doorway at the bottom; crying in the dark
    case "doorway": {
      add(him, poseFloorCover(him, t, { pos: [0, 0, -2.2], yaw: Math.PI }));
      const cam = keys([K(0, [0.05, 1.55, 1.95], [0.0, 0.2, -0.4], 62), K(3.6, [0.05, 1.55, 1.7], [0.0, 0.3, -0.8], 60, "linear")]);
      holdPhone(cam, "torch", "nosig", { bars: 0, led: 1, shake: 0.6 });
      out = { cam, objs, flash: 1 };
      break;
    }
    // ---------------------------------------------------------------- 30. him, from behind
    case "him": {
      add(him, poseFloorCover(him, t, { pos: [0, 0, -2.2], yaw: Math.PI }));
      const cam = keys([K(0, [0.12, 1.55, 1.2], [0.0, 0.85, -2.2], 58), K(E("tall", 1.95), [0.1, 1.55, 0.75], [0.0, 1.05, -2.2], 56), K(4.8, [0.08, 1.5, 0.3], [0.0, 1.0, -2.2], 52)]);
      holdPhone(cam, "torch", "nosig", { bars: 0, led: 1, shake: 0.7 });
      out = { cam, objs, flash: 1 };
      break;
    }
    // ---------------------------------------------------------------- 31. long fingers over the face
    case "face": {
      add(him, poseFloorCover(him, t, { pos: [0, 0, -2.2], yaw: Math.PI }));
      const cam = keys([K(0, [1.35, 1.1, -1.25], [0.0, 1.0, -2.35], 50), K(2.4, [1.25, 1.08, -1.32], [0.0, 1.0, -2.35], 46, "linear")]);
      aimFlashlight(flash, cam, 0.45, 0.04, t);
      out = { cam, objs, flash: 1 };
      break;
    }
    // ---------------------------------------------------------------- 32. her headscarf on the floor
    case "scarf": {
      add(him, poseFloorCover(him, t, { pos: [0, 0, -2.2], yaw: Math.PI }));
      const s = world.lair!.scarf.position;
      const cam = keys([K(0, [1.35, 1.25, -0.55], [s.x, s.y, s.z], 48), K(2.7, [1.25, 1.15, -0.7], [s.x, s.y, s.z], 42, "linear")]);
      aimFlashlight(flash, cam, 1, 0.02, t);
      out = { cam, objs, flash: 1 };
      break;
    }
    // ---------------------------------------------------------------- 33. a step forward; the crying stops
    case "step": {
      const stop = E("stop", 1.65);
      add(him, poseFloorCover(him, t, { pos: [0, 0, -2.2], yaw: Math.PI, sob: t < stop ? 1 : 0 }));
      const st = sm(t / 0.7);
      const bob = Math.sin(Math.min(1, t / 0.7) * Math.PI) * 0.04;
      const cam: Cam = { pos: [0.08, 1.52 - bob, 0.5 - st * 0.45], target: [0.0, 1.0, -2.2], fov: 54 };
      holdPhone(cam, "torch", "nosig", { bars: 0, led: 1, shake: t > stop ? 1.8 : 0.5 });
      out = { cam, objs, flash: 1 };
      break;
    }
    // ---------------------------------------------------------------- 34. he starts to lower his hands
    case "lower": {
      const k = sm((t - 0.25) / 2.6) * 0.85;
      add(him, poseFloorCover(him, t, { pos: [0, 0, -2.2], yaw: Math.PI, lower: k, sob: 0, headTurn: sm((t - 1.6) / 1.4) * 0.35 }));
      const cam = keys([K(0, [0.7, 1.2, -1.0], [0.0, 1.1, -2.25], 46), K(3, [0.62, 1.15, -1.15], [0.0, 1.1, -2.25], 40, "linear")]);
      aimFlashlight(flash, cam, 0.45, 0.05, t);
      out = { cam, objs, flash: 1, wear: 0.6 + k * 0.6 };
      break;
    }
    default: {
      out = { cam: { pos: [0, 1.6, 3], target: [0, 1.2, 0], fov: 60 }, objs };
    }
  }
  if (out.lamps && world.lamps.length) {
    applyLamps(world.lamps, t, out.lamps);
    // shadows from the two bulbs nearest to the camera
    const cp = new THREE.Vector3(...out.cam.pos);
    const near = [...world.lamps].sort((a, b) => a.light.getWorldPosition(new THREE.Vector3()).distanceTo(cp) - b.light.getWorldPosition(new THREE.Vector3()).distanceTo(cp));
    world.lamps.forEach((l) => (l.light.castShadow = near.indexOf(l) < 2));
  }
  if (out.flash === undefined) flash.intensity = 0;
  return (
    <AbsoluteFill>
      <PzFrame t={t} cam={out.cam} fog={out.fog} exposure={out.exposure} wear={out.wear} counter0={c0}>
        {out.light}
        {out.flash !== undefined ? (
          <>
            <primitive object={flash} />
            <primitive object={flash.target} />
            <hemisphereLight args={["#2C3A4A", "#0A0806", 0.32]} />
            {sets.includes("lair") ? (
              <>
                <pointLight position={[0.4, 2.1, -0.6]} color="#5A6E8C" intensity={1.6} distance={6} decay={1.5} />
                <pointLight position={[-0.6, 1.7, -3.7]} color="#6E84A8" intensity={3.2} distance={4} decay={1.4} />
              </>
            ) : null}
          </>
        ) : null}
        {out.objs.map((o, i) => (
          <primitive key={i} object={o} />
        ))}
      </PzFrame>
      {out.overlay}
    </AbsoluteFill>
  );
};

/** eyelids: 0 = shut, 1 = open */
const Lids: React.FC<{ open: number }> = ({ open }) => {
  const c = Math.max(0, Math.min(1, open));
  const cover = (1 - c) * 52;
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <AbsoluteFill style={{ background: `linear-gradient(180deg, #000 ${cover}%, rgba(0,0,0,0) ${cover + 12}%, rgba(0,0,0,0) ${100 - cover - 12}%, #000 ${100 - cover}%)` }} />
    </AbsoluteFill>
  );
};
