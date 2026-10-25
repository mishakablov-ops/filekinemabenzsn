/**
 * Scenes for the "podezd" horror reel (PS1 + VHS look). Shared loaders, the stairwell world with its residents,
 * and a test block for checking sets, characters and poses.
 */
import React, { useEffect, useMemo, useState } from "react";
import { AbsoluteFill, continueRender, delayRender, staticFile } from "remotion";
import * as THREE from "three";
import { useBlockTime } from "../core/context";
import { camAt, Stage3D, type Cam, type CamKey, type V3 } from "./core";
import { createHuman, poseChair, poseCornerCry, poseCrouch, poseFloorCover, poseSitHoldHead, type Human } from "./human";
import { useGLB } from "./nk";
import { applyLamps, BOOTH, buildBedroom, buildBlock, buildBooth, buildDescent, buildLair, buildPipeCorner, buildStairwell, FLOOR, PZ_TEX, RISE, TREAD, type Lamp, type Tex } from "./podezdSets";
import { psxify, VhsLook } from "./psx";

const P = "projects/podezd/";
const texCache: { p?: Promise<Tex> } = {};
export const usePzTextures = () => {
  const [tex, setTex] = useState<Tex | null>(null);
  const [handle] = useState(() => delayRender("podezd textures", { timeoutInMilliseconds: 180000 }));
  useEffect(() => {
    if (!texCache.p) {
      const loader = new THREE.TextureLoader();
      const one = (file: string, srgb: boolean) =>
        loader.loadAsync(staticFile(P + "tex_lo/" + file)).then((t) => {
          t.wrapS = t.wrapT = THREE.RepeatWrapping;
          t.colorSpace = srgb ? THREE.SRGBColorSpace : THREE.NoColorSpace;
          return t;
        });
      // PS1 look: 64-128 px textures, no normal maps
      texCache.p = Promise.all(PZ_TEX.map((n) => one(n + ".png", true).then((t) => [n, t] as const))).then((pairs) => Object.fromEntries(pairs));
    }
    texCache.p
      .then((t) => {
        setTex(t);
        continueRender(handle);
      })
      .catch((e) => {
        console.error("podezd textures", e);
        continueRender(handle);
      });
  }, [handle]);
  return tex;
};

export const CHARS = ["serega", "lyuda", "ded", "valya", "him"] as const;
export type CharName = (typeof CHARS)[number];
export const useChar = (name: CharName, tint?: string) => {
  const g = useGLB(P + "models/" + name + ".glb");
  return useMemo(() => (g ? createHuman(g.scene, { tint }) : null), [g, tint]);
};

/** a step of flight A of floor n: top surface height and tread centre z (k = 0 is the first step) */
export const stepA = (n: number, k: number) => ({ y: FLOOR(n) + (RISE / 9) * (k + 1), z: 1.5 + TREAD * (k + 0.5) });

/** the stairwell with lamps; memoised per texture set */
export const useStairwell = () => {
  const tex = usePzTextures();
  return useMemo(() => (tex ? buildStairwell(tex) : null), [tex]);
};

/** look of every podezd scene: PS1 low-res render inside a VHS playback */
export const PzFrame: React.FC<{ t: number; cam: Cam; children: React.ReactNode; wear?: number; osd?: boolean; counter0?: number; fog?: { color: string; near: number; far: number }; exposure?: number; rec?: { clock: string } | null; bg?: string }> = ({ t, cam, children, wear, osd = true, counter0 = 0, fog, exposure = 1.35, rec = null, bg = "#030405" }) => (
  <VhsLook t={t} wear={wear} osd={osd} counter0={counter0} rec={rec}>
    <Stage3D cam={cam} lights="none" env={0} dpr={0.17} pixelated fog={fog ?? { color: "#05070A", near: 5, far: 19 }} exposure={exposure}>
      <color attach="background" args={[bg]} />
      <hemisphereLight args={["#4A5866", "#1A1612", 0.45]} />
      {children}
    </Stage3D>
  </VhsLook>
);

/** handheld LED flashlight (phone torch): spot from just below-right of the eye toward where the camera looks */
export const useFlashlight = () =>
  useMemo(() => {
    const l = new THREE.SpotLight("#E6EEFF", 0, 16, 0.42, 0.55, 1.45);
    l.castShadow = true;
    l.shadow.mapSize.set(1024, 1024);
    l.shadow.bias = -0.002;
    return l;
  }, []);
export function aimFlashlight(l: THREE.SpotLight, cam: Cam, on = 1, jitter = 0, t = 0) {
  const p = new THREE.Vector3(...cam.pos), tg = new THREE.Vector3(...cam.target);
  const fwd = tg.clone().sub(p).normalize();
  const right = fwd.clone().cross(new THREE.Vector3(0, 1, 0)).normalize();
  l.position.copy(p).addScaledVector(right, 0.18).add(new THREE.Vector3(0, -0.22, 0)).addScaledVector(fwd, 0.25);
  l.target.position.copy(tg).add(new THREE.Vector3(Math.sin(t * 2.1) * jitter, Math.sin(t * 2.9) * jitter * 0.6, 0));
  l.target.updateMatrixWorld();
  l.intensity = 38 * on;
}

// ------------------------------------------------------------------ test block
export const PzTest: React.FC<{ cam?: CamKey[]; who?: CharName[]; flicker?: number; breath?: number; look?: number; counter0?: number }> = ({ cam: keys, who = ["serega", "lyuda", "ded"], flicker = 0.4, breath = 0, look = 0, counter0 = 0 }) => {
  const { f, fps } = useBlockTime();
  const t = f / fps;
  const sw = useStairwell();
  const serega = useChar("serega");
  const lyuda = useChar("lyuda");
  const ded = useChar("ded");
  const valya = useChar("valya");
  const him = useChar("him");
  const all: Record<CharName, Human | null> = { serega, lyuda, ded, valya, him };
  const ready = sw && who.every((w) => all[w]);
  const world = useMemo(() => (ready ? psxify(sw!.g) : null), [ready, sw]);
  if (!ready || !world) return <AbsoluteFill style={{ background: "#000" }} />;
  applyLamps(sw!.lamps, t, { flicker, breath });
  sw!.lamps.forEach((l, i) => (l.light.castShadow = i === 1 || i === 2));
  const cam = camAt(keys ?? [{ t: 0, pos: [-0.7, FLOOR(2) + 1.62, 0.55], target: [0.7, FLOOR(2) + 0.9, 2.9], fov: 62 }], t);
  const objs: THREE.Object3D[] = [];
  const s4 = stepA(2, 4), s2 = stepA(2, 2);
  if (who.includes("serega") && serega) {
    serega.pose(poseSitHoldHead(serega, t, { pos: [0.72, s4.y, s4.z + 0.04], yaw: Math.PI, seat: 0, feetDrop: s4.y - s2.y, lookUp: look, lookAt: cam.pos }));
    objs.push(psxify(serega.root));
  }
  if (who.includes("lyuda") && lyuda) {
    lyuda.pose(poseCornerCry(lyuda, t, { pos: [0.98, FLOOR(2) + RISE, 5.02], yaw: Math.PI / 4 }));
    objs.push(psxify(lyuda.root));
  }
  if (who.includes("ded") && ded) {
    ded.pose(poseCrouch(ded, t, { pos: [-0.98, -RISE, 5.0], yaw: (3 * Math.PI) / 4 }));
    objs.push(psxify(ded.root));
  }
  for (const n of ["valya", "him"] as const)
    if (who.includes(n) && all[n]) {
      const h = all[n]!;
      h.pose({ pos: n === "him" ? [0, FLOOR(1), 0.9] : [0.0, FLOOR(3), 0.9], yaw: 0 });
      objs.push(psxify(h.root));
    }
  return (
    <PzFrame t={t} cam={cam} counter0={counter0}>
      <primitive object={world} />
      {objs.map((o, i) => (
        <primitive key={i} object={o} />
      ))}
    </PzFrame>
  );
};

// ------------------------------------------------------------------ set test: every location with its actor
export const PzSetTest: React.FC<{ set: "booth" | "boothAfter" | "descent" | "lair" | "bedroom" | "pipe" | "block"; cam?: CamKey[]; lower?: number }> = ({ set, cam: keys, lower = 0 }) => {
  const { f, fps } = useBlockTime();
  const t = f / fps;
  const tex = usePzTextures();
  const valya = useChar("valya");
  const him = useChar("him");
  const built = useMemo(() => {
    if (!tex) return null;
    if (set === "booth" || set === "boothAfter") {
      const b = buildBooth(tex, set === "booth" ? "before" : "after");
      const sw = buildStairwell(tex);
      const g = new THREE.Group();
      g.add(sw.g, b.g);
      return { g, booth: b, lamps: [...sw.lamps, b.lamp] };
    }
    if (set === "descent") {
      const d = buildDescent(tex);
      return { g: d.g, lamps: [] };
    }
    if (set === "lair") return { g: buildLair(tex).g, lamps: [] };
    if (set === "bedroom") return { g: buildBedroom(tex).g, lamps: [] };
    if (set === "pipe") {
      const p = buildPipeCorner(tex);
      return { g: p.g, lamps: [p.lamp], pipe: p };
    }
    return { g: buildBlock(tex).g, lamps: [] };
  }, [tex, set]);
  const world = useMemo(() => (built ? psxify(built.g) : null), [built]);
  const flash = useFlashlight();
  if (!built || !world || !valya || !him) return <AbsoluteFill style={{ background: "#000" }} />;
  applyLamps(built.lamps as Lamp[], t, { flicker: 0.3 });
  const defaults: Record<string, CamKey[]> = {
    booth: [{ t: 0, pos: [3.3, -1.4 + 1.6, 2.2], target: [1.6, -1.4 + 0.9, 4.4], fov: 64 }],
    boothAfter: [{ t: 0, pos: [1.9, -1.4 + 1.6, 4.9], target: [3.6, -1.4 + 0.9, 2.6], fov: 64 }],
    descent: [{ t: 0, pos: [0.35, 1.55, 0.3], target: [0.35, -0.9, 2.6], fov: 66 }],
    lair: [{ t: 0, pos: [0.1, 1.55, 1.6], target: [0, 0.8, -2.2], fov: 62 }],
    bedroom: [{ t: 0, pos: [-1.1, 0.75, -1.75], target: [1.0, 1.4, 1.6], fov: 66 }],
    pipe: [{ t: 0, pos: [0.75, 0.4, 0.8], target: [0.16, 2.3, 0.16], fov: 62 }],
    block: [{ t: 0, pos: [-10, 4.5, 26], target: [-7.5, 8.5, 0], fov: 48 }],
  };
  const cam = camAt(keys ?? defaults[set], t);
  aimFlashlight(flash, cam, 1, 0.08, t);
  const objs: THREE.Object3D[] = [world];
  const fog = set === "block" ? { color: "#06080C", near: 20, far: 120 } : undefined;
  if (set === "booth") {
    valya.pose(poseChair(valya, t, { pos: [BOOTH.x0 + 1.02, BOOTH.y, 4.37], yaw: -Math.PI / 2, lookAt: cam.pos, look: 0.8 }));
    objs.push(psxify(valya.root));
  }
  if (set === "boothAfter" && built.booth) built.booth.updateSteam(t);
  if (set === "lair") {
    him.pose(poseFloorCover(him, t, { pos: [0, 0, -2.2], yaw: Math.PI, lower }));
    objs.push(psxify(him.root));
  }
  if (set === "pipe" && built.pipe) built.pipe.knock(t, [0.3, 0.75, 1.2]);
  return (
    <PzFrame t={t} cam={cam} fog={fog} exposure={set === "block" ? 1.5 : 1.25}>
      {set === "lair" || set === "descent" ? (
        <>
          <primitive object={flash} />
          <primitive object={flash.target} />
          <hemisphereLight args={["#24303C", "#0A0806", 0.25]} />
        </>
      ) : null}
      {set === "block" ? <color attach="background" args={["#0A0E16"]} /> : null}
      {objs.map((o, i) => (
        <primitive key={i} object={o} />
      ))}
    </PzFrame>
  );
};

// ------------------------------------------------------------------ pose debug: one actor, plain light, no PS1/VHS
export const PzPoseTest: React.FC<{ who: CharName; pose: string; lower?: number; cam?: CamKey[] }> = ({ who, pose, lower = 0, cam: keys }) => {
  const { f, fps } = useBlockTime();
  const t = f / fps;
  const h = useChar(who);
  if (!h) return <AbsoluteFill style={{ background: "#333" }} />;
  const P0: V3 = [0, 0, 0];
  const p =
    pose === "floor" ? poseFloorCover(h, t, { pos: P0, yaw: 0, lower }) :
    pose === "crouch" ? poseCrouch(h, t, { pos: P0, yaw: 0 }) :
    pose === "cry" ? poseCornerCry(h, t, { pos: P0, yaw: 0 }) :
    pose === "chair" ? poseChair(h, t, { pos: P0, yaw: 0 }) :
    pose === "sit" ? poseSitHoldHead(h, t, { pos: [0, 0.47, 0], yaw: 0, seat: 0, feetDrop: 0.47 }) :
    { pos: P0, yaw: 0 };
  h.pose(p);
  const cam = camAt(keys ?? [{ t: 0, pos: [1.6, 1.3, 2.4], target: [0, 0.8, 0], fov: 50 }], t);
  return (
    <AbsoluteFill style={{ background: "#3A3A3A" }}>
      <Stage3D cam={cam} lights="studio" env={0.6}>
        <gridHelper args={[4, 8, "#666", "#555"]} />
        <primitive object={h.root} />
      </Stage3D>
    </AbsoluteFill>
  );
};
