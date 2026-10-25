/**
 * Low-poly kit in flat DARK PASTEL tones: people, furniture, street props.
 * Units ≈ metres. Everything casts soft shadows. No textures, no gradients.
 */
import React, { useMemo } from "react";
import * as THREE from "three";
import { RoundedBoxGeometry } from "three/examples/jsm/geometries/RoundedBoxGeometry.js";
import type { V3 } from "./core";

// ------------------------------------------------------------------ palettes
export type KitPalette = {
  bg: string; wall: string; wall2: string; floor: string; floorLine: string; rug: string; rug2: string; wood: string; woodDark: string; metal: string;
  fabric: string[]; plant: string; plant2: string; pot: string; screen: string; glow: string; lamp: string; windowLight: string; books: string[];
  skin: string[]; hair: string[]; shirts: string[]; pants: string[]; cars: string[]; facades: string[]; road: string; walk: string; curb: string; line: string;
  winDark: string; winLit: string; tree: string[]; trunk: string; sky: string;
};

export const PALETTES: Record<string, KitPalette> = {
  // default: warm charcoal + muted terracotta/sage/dusty blue
  dusk: {
    bg: "#2A2622", wall: "#4F4943", wall2: "#45403B", floor: "#6E5C4E", floorLine: "#64544A", rug: "#7C5F52", rug2: "#56645F", wood: "#8A7160", woodDark: "#5E4C40", metal: "#3A3936",
    fabric: ["#6A7884", "#8E7264", "#76836D", "#7E6A78", "#A08A62"], plant: "#5D7556", plant2: "#4C6447", pot: "#A9785C", screen: "#1C1E22", glow: "#E08A55", lamp: "#E2C29A", windowLight: "#F0D2AE",
    books: ["#8E6A5A", "#5F6E7A", "#7A8468", "#9A8456", "#6E5E70", "#A0704F"],
    skin: ["#D1A88A", "#B78A6C", "#8E6650", "#E0BEA1"], hair: ["#2A231F", "#4A3426", "#6E4F38", "#1F1F23", "#8A6A4E"],
    shirts: ["#6A7884", "#8E7264", "#76836D", "#7E6A78", "#B0905A", "#A15E44", "#5E5A66"], pants: ["#3C3D44", "#4A4038", "#2F3338", "#5A5148"],
    cars: ["#6A7884", "#8E6C5E", "#7A866E", "#C2A06A", "#4A4C52", "#A86A50"], facades: ["#6B5E54", "#5E5A57", "#7A6A5C", "#585E62", "#6E6258", "#80705F"],
    road: "#343332", walk: "#5C5751", curb: "#6E6862", line: "#C9B79A", winDark: "#2B2D33", winLit: "#E8B985", tree: ["#5B7354", "#4F6A4C", "#6A7F5C"], trunk: "#4E3E33", sky: "#2A2622",
  },
  // evening: deeper, more lit windows
  evening: {
    bg: "#1F1C1B", wall: "#433E3A", wall2: "#3A3632", floor: "#5E4F44", floorLine: "#55473D", rug: "#6E5248", rug2: "#4B5753", wood: "#7A6354", woodDark: "#503F35", metal: "#2F2E2C",
    fabric: ["#5E6B76", "#7E6458", "#687560", "#6F5E6A", "#8F7A56"], plant: "#4F6649", plant2: "#42583E", pot: "#966650", screen: "#16181B", glow: "#E8925A", lamp: "#F0C994", windowLight: "#E8A86A",
    books: ["#7E5E50", "#56636E", "#6C755C", "#8A764C", "#625466", "#8F6346"],
    skin: ["#C49C80", "#A87E62", "#825C48", "#D4B396"], hair: ["#231E1B", "#3F2D21", "#5E4431", "#1A1A1E"],
    shirts: ["#5E6B76", "#7E6458", "#687560", "#6F5E6A", "#9C8050", "#8F5440"], pants: ["#33343A", "#3F3730", "#282B30"],
    cars: ["#5E6B76", "#7C5E52", "#6A7660", "#AE8F5E", "#3E4046", "#965E46"], facades: ["#574D46", "#4C4946", "#64584D", "#484D51", "#5A5048", "#6A5D50"],
    road: "#2A2928", walk: "#4C4843", curb: "#5C5752", line: "#B8A68A", winDark: "#24262B", winLit: "#F0B477", tree: ["#4C6247", "#425A40", "#5A6D4E"], trunk: "#3E3129", sky: "#1F1C1B",
  },
  // night: blue-grey with warm lights
  night: {
    bg: "#16181D", wall: "#363A42", wall2: "#2F333A", floor: "#4A4440", floorLine: "#423D39", rug: "#5A4A48", rug2: "#3E4A4E", wood: "#5E5048", woodDark: "#40362F", metal: "#26282C",
    fabric: ["#4E5A66", "#6A5650", "#56624F", "#5E5160", "#7A6A4C"], plant: "#3E5240", plant2: "#344636", pot: "#7E5644", screen: "#101216", glow: "#E8925A", lamp: "#F2C88E", windowLight: "#7F96C8",
    books: ["#6A5046", "#48545E", "#5A6450", "#766644", "#524758", "#7A553E"],
    skin: ["#B48E74", "#9A735A", "#765442", "#C4A488"], hair: ["#1C1916", "#352619", "#4E3A2A", "#151518"],
    shirts: ["#4E5A66", "#6A5650", "#56624F", "#5E5160", "#8A7046", "#7A4A38"], pants: ["#2A2B30", "#342E29", "#212428"],
    cars: ["#4E5A66", "#6A5046", "#5A6450", "#9A7E52", "#33353B", "#82503C"], facades: ["#3E3B3A", "#383A3E", "#4A433D", "#363B40", "#444039", "#4E463E"],
    road: "#202124", walk: "#3A3836", curb: "#47443F", line: "#9E8E76", winDark: "#1C1E23", winLit: "#F2B26E", tree: ["#3A4E3A", "#334632", "#465A40"], trunk: "#30261F", sky: "#16181D",
  },
  // light muted (beige, never white)
  sand: {
    bg: "#D9CCB6", wall: "#CDBEA6", wall2: "#C2B29A", floor: "#A88B6E", floorLine: "#9C8064", rug: "#9E6E58", rug2: "#7E8A78", wood: "#9C7E62", woodDark: "#6E5644", metal: "#5A5652",
    fabric: ["#7D8C96", "#A8806C", "#8C9A7E", "#957E8E", "#BFA06A"], plant: "#6E8A62", plant2: "#5E7854", pot: "#B9805E", screen: "#22252A", glow: "#D9601C", lamp: "#EAD0A8", windowLight: "#F4E3C8",
    books: ["#9E7464", "#6E7E8A", "#8A9476", "#AA9460", "#7E6E82", "#B07A58"],
    skin: ["#D9B293", "#BE9070", "#946C54", "#E6C8AC"], hair: ["#2E2622", "#4E3828", "#74543C", "#24242A"],
    shirts: ["#7D8C96", "#A8806C", "#8C9A7E", "#957E8E", "#BFA06A", "#B06A4C"], pants: ["#4A4B52", "#5A4E44", "#3C4046"],
    cars: ["#7D8C96", "#A8806C", "#8C9A7E", "#CDAE78", "#5A5C62", "#B87658"], facades: ["#B9A68E", "#A99A88", "#C2AE94", "#9EA2A0", "#B4A28C", "#C8B49A"],
    road: "#6A6560", walk: "#B5A894", curb: "#C2B6A2", line: "#EDE2CF", winDark: "#4A4E56", winLit: "#F2D2A4", tree: ["#6E8A62", "#5E7A56", "#7C9268"], trunk: "#5E4A3A", sky: "#D9CCB6",
  },
};

export const pick = <T,>(arr: T[], i: number) => arr[((i % arr.length) + arr.length) % arr.length];

// ------------------------------------------------------------------ materials & geometry caches
const MAT = new Map<string, THREE.MeshStandardMaterial>();
export const mat = (color: string, rough = 0.86, emissive?: string, ei = 1, flat = false) => {
  const k = `${color}|${rough}|${emissive}|${ei}|${flat}`;
  let m = MAT.get(k);
  if (!m) {
    m = new THREE.MeshStandardMaterial({ color, roughness: rough, metalness: 0, emissive: emissive ?? "#000000", emissiveIntensity: ei, flatShading: flat });
    MAT.set(k, m);
  }
  return m;
};
const RB = new Map<string, THREE.BufferGeometry>();
export const rbox = (w: number, h: number, d: number, r = 0.04) => {
  const k = `${w}|${h}|${d}|${r}`;
  let g = RB.get(k);
  if (!g) {
    g = new RoundedBoxGeometry(w, h, d, 3, Math.min(r, w / 2 - 0.001, h / 2 - 0.001, d / 2 - 0.001));
    RB.set(k, g);
  }
  return g;
};

export const Box: React.FC<{ s: V3; p?: V3; r?: V3; c: string; rad?: number; rough?: number; emissive?: string; ei?: number; shadow?: boolean }> = ({ s, p = [0, 0, 0], r = [0, 0, 0], c, rad = 0.03, rough, emissive, ei, shadow = true }) => (
  <mesh geometry={rbox(s[0], s[1], s[2], rad)} material={mat(c, rough, emissive, ei)} position={p} rotation={r} castShadow={shadow} receiveShadow />
);

/** material for thin details lying on a surface (screens, art, labels, windows): drawn in front, never z-fights */
const DECAL = new Map<string, THREE.MeshStandardMaterial>();
export const decal = (color: string, rough = 0.6, emissive?: string, ei = 1) => {
  const k = `${color}|${rough}|${emissive}|${ei}`;
  let m = DECAL.get(k);
  if (!m) {
    m = new THREE.MeshStandardMaterial({ color, roughness: rough, emissive: emissive ?? "#000000", emissiveIntensity: ei, polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -4 });
    DECAL.set(k, m);
  }
  return m;
};

export const Cyl: React.FC<{ rt: number; rb?: number; h: number; p?: V3; r?: V3; c: string; seg?: number; emissive?: string; ei?: number }> = ({ rt, rb, h, p = [0, 0, 0], r = [0, 0, 0], c, seg = 20, emissive, ei }) => (
  <mesh position={p} rotation={r} castShadow receiveShadow material={mat(c, 0.8, emissive, ei)}>
    <cylinderGeometry args={[rt, rb ?? rt, h, seg]} />
  </mesh>
);

export const Ball: React.FC<{ r: number; p?: V3; s?: V3; c: string; detail?: number; flat?: boolean; emissive?: string; ei?: number }> = ({ r, p = [0, 0, 0], s = [1, 1, 1], c, detail = 1, flat = true, emissive, ei }) => (
  <mesh position={p} scale={s} castShadow receiveShadow material={mat(c, 0.9, emissive, ei, flat)}>
    <icosahedronGeometry args={[r, detail]} />
  </mesh>
);

export const Cap: React.FC<{ r: number; len: number; p?: V3; r3?: V3; c: string }> = ({ r, len, p = [0, 0, 0], r3 = [0, 0, 0], c }) => (
  <mesh position={p} rotation={r3} castShadow material={mat(c, 0.85)}>
    <capsuleGeometry args={[r, len, 6, 14]} />
  </mesh>
);

// ------------------------------------------------------------------ PERSON
export type Pose = "stand" | "walk" | "run" | "sit" | "type" | "wave" | "point" | "think" | "idle" | "phone" | "cheer";

/** suit: improvised protective gear (post-fallout outing). true = everything (raincoat with hood unless a cap is worn,
 *  goggles, respirator, gloves, boots); an object puts it on piece by piece (Room3D people `suitAt` animates it). */
export type SuitParts = { coat?: boolean; gloves?: boolean; boots?: boolean; goggles?: boolean; mask?: boolean; hood?: boolean };
/** hero: the recurring main character — a young guy in a white cap (same look in every scene of a reel) */
export type PersonLook = { skin?: string; hair?: string; shirt?: string; pants?: string; hairStyle?: "short" | "long" | "bun" | "bald" | "cap"; shoes?: string; suit?: boolean | SuitParts; capColor?: string; hero?: boolean };
export const HERO: PersonLook = { hairStyle: "cap", capColor: "#ECE5DA", shirt: "#B8612A", pants: "#2E2C2A", shoes: "#E3DCCF", skin: "#D1A88A", hair: "#2A231F" };
const SUIT_ALL: SuitParts = { coat: true, gloves: true, boots: true, goggles: true, mask: true, hood: true };

/** limb = capsule hanging from a pivot */
const Limb: React.FC<{ pivot: V3; rot: V3; len: number; r: number; c: string; lower?: { rot: V3; len: number; r: number; c: string; hand?: string; foot?: string } }> = ({ pivot, rot, len, r, c, lower }) => (
  <group position={pivot} rotation={rot}>
    <Cap r={r} len={len} p={[0, -len / 2 - r * 0.2, 0]} c={c} />
    {lower ? (
      <group position={[0, -len - r * 0.4, 0]} rotation={lower.rot}>
        <Cap r={lower.r} len={lower.len} p={[0, -lower.len / 2 - lower.r * 0.2, 0]} c={lower.c} />
        {lower.hand ? <Ball r={lower.r * 1.15} p={[0, -lower.len - lower.r * 0.9, 0]} c={lower.hand} detail={1} /> : null}
        {lower.foot ? <Box s={[0.13, 0.08, 0.25]} p={[0, -lower.len - lower.r * 1.2, 0.05]} c={lower.foot} rad={0.03} /> : null}
      </group>
    ) : null}
  </group>
);

export const Person: React.FC<{ pos?: V3; rotY?: number; pose?: Pose; t?: number; look?: PersonLook; seed?: number; scale?: number; pal?: KitPalette; eyes?: boolean }> = ({
  pos = [0, 0, 0], rotY = 0, pose = "stand", t = 0, look = {}, seed = 0, scale = 1, pal = PALETTES.dusk, eyes = true,
}) => {
  if (look.hero) look = { ...HERO, ...look };
  const skin = look.skin ?? pick(pal.skin, seed);
  const hair = look.hair ?? pick(pal.hair, seed * 3 + 1);
  const hs = look.hairStyle ?? (["short", "long", "bun", "short", "cap"] as const)[seed % 5];
  const S: SuitParts = look.suit === true ? { ...SUIT_ALL, hood: hs !== "cap" } : look.suit || {};
  const suit = !!S.coat; // raincoat on
  const shirt = suit ? "#A8904A" : look.shirt ?? pick(pal.shirts, seed * 5 + 2);
  const pants = look.pants ?? (look.suit === true && !look.hero ? "#5A5A4E" : pick(pal.pants, seed * 7 + 3));
  const shoes = S.boots ? "#1E1C1A" : look.shoes ?? "#2A2624";
  const hand = S.gloves ? "#33312E" : skin;
  const fore = suit ? shirt : skin;
  const capC = look.capColor ?? pick(pal.fabric, seed + 2);
  const hooded = !!S.hood && suit;
  const ph = t * Math.PI * 2;
  // joint angles (radians): shoulder X/Z, elbow X, hip X, knee X
  let lS: V3 = [0, 0, 0.08], rS: V3 = [0, 0, -0.08], lE: V3 = [0, 0, 0], rE: V3 = [0, 0, 0];
  let lH: V3 = [0, 0, 0], rH: V3 = [0, 0, 0], lK: V3 = [0, 0, 0], rK: V3 = [0, 0, 0];
  let bodyY = 0;
  let lean = 0;
  let headTilt = 0;
  const sitting = pose === "sit" || pose === "type";
  switch (pose) {
    case "walk":
    case "run": {
      const amp = pose === "run" ? 0.9 : 0.5;
      const sp = pose === "run" ? 1.6 : 1;
      const s = Math.sin(ph * sp);
      lH = [s * amp, 0, 0];
      rH = [-s * amp, 0, 0];
      lK = [Math.max(0, -Math.cos(ph * sp)) * amp * 1.2, 0, 0];
      rK = [Math.max(0, Math.cos(ph * sp)) * amp * 1.2, 0, 0];
      lS = [-s * amp * 0.9, 0, 0.1];
      rS = [s * amp * 0.9, 0, -0.1];
      lE = [-0.3 - (pose === "run" ? 0.9 : 0), 0, 0];
      rE = [-0.3 - (pose === "run" ? 0.9 : 0), 0, 0];
      bodyY = Math.abs(Math.cos(ph * sp)) * 0.04 * amp;
      lean = pose === "run" ? 0.18 : 0.03;
      break;
    }
    case "sit":
    case "type":
      lH = [-Math.PI / 2, 0, 0.05];
      rH = [-Math.PI / 2, 0, -0.05];
      lK = [Math.PI / 2, 0, 0];
      rK = [Math.PI / 2, 0, 0];
      if (pose === "type") {
        const k = Math.sin(ph * 6) * 0.06;
        lS = [-0.55, 0, 0.18];
        rS = [-0.55, 0, -0.18];
        lE = [-0.95 + k, 0, 0];
        rE = [-0.95 - k, 0, 0];
        lean = 0.12;
        headTilt = 0.12;
      } else {
        lS = [-0.15, 0, 0.12];
        rS = [-0.15, 0, -0.12];
        lE = [-0.5, 0, 0];
        rE = [-0.5, 0, 0];
      }
      break;
    case "wave":
      rS = [0, 0, -2.6 + Math.sin(ph * 3) * 0.12];
      rE = [0, 0, 0];
      rE = [Math.sin(ph * 3) * 0.35 - 0.2, 0, 0];
      lS = [0, 0, 0.12];
      break;
    case "point":
      rS = [-1.45, 0, -0.15];
      rE = [-0.1, 0, 0];
      break;
    case "think":
      rS = [-0.7, 0, -0.35];
      rE = [-2.1, 0, 0];
      lS = [-0.35, 0, 0.35];
      lE = [-1.4, 0, 0];
      headTilt = 0.1;
      break;
    case "phone":
      rS = [-0.6, 0, -0.2];
      rE = [-1.6, 0, 0];
      headTilt = 0.32;
      break;
    case "cheer":
      lS = [0, 0, 2.7 + Math.sin(ph * 2.5) * 0.1];
      rS = [0, 0, -2.7 - Math.sin(ph * 2.5) * 0.1];
      bodyY = Math.max(0, Math.sin(ph * 2.5)) * 0.08;
      break;
    case "idle":
    case "stand":
    default:
      bodyY = Math.sin(ph * 0.5) * 0.008;
      lS = [0.02, 0, 0.1];
      rS = [0.02, 0, -0.1];
      lE = [-0.12, 0, 0];
      rE = [-0.12, 0, 0];
  }
  const hipY = sitting ? 0.48 : 0.92;
  return (
    <group position={pos} rotation={[0, rotY, 0]} scale={scale}>
      <group position={[0, bodyY, 0]}>
        {/* legs */}
        <Limb pivot={[0.1, hipY, 0]} rot={lH} len={0.38} r={0.075} c={pants} lower={{ rot: lK, len: 0.36, r: 0.065, c: pants, foot: shoes }} />
        <Limb pivot={[-0.1, hipY, 0]} rot={rH} len={0.38} r={0.075} c={pants} lower={{ rot: rK, len: 0.36, r: 0.065, c: pants, foot: shoes }} />
        <group position={[0, hipY, 0]} rotation={[lean, 0, 0]}>
          {/* pelvis + torso */}
          <Box s={[0.34, 0.16, 0.2]} p={[0, 0.02, 0]} c={pants} rad={0.07} />
          <Cap r={0.17} len={0.3} p={[0, 0.33, 0]} c={shirt} />
          {suit ? (
            <>
              {/* backpack + taped seams */}
              <Box s={[0.3, 0.38, 0.16]} p={[0, 0.36, -0.22]} c="#4E4A40" rad={0.05} />
              <Box s={[0.26, 0.1, 0.06]} p={[0, 0.24, -0.31]} c="#5E584C" rad={0.02} />
              <Box s={[0.36, 0.035, 0.36]} p={[0, 0.1, 0]} c="#8C8A86" rad={0.015} />
            </>
          ) : null}
          {/* arms (pivot at shoulders) */}
          <Limb pivot={[0.25, 0.56, 0]} rot={lS} len={0.27} r={0.06} c={shirt} lower={{ rot: lE, len: 0.25, r: 0.052, c: fore, hand }} />
          <Limb pivot={[-0.25, 0.56, 0]} rot={rS} len={0.27} r={0.06} c={shirt} lower={{ rot: rE, len: 0.25, r: 0.052, c: fore, hand }} />
          {/* neck + head */}
          <Cyl rt={0.055} h={0.1} p={[0, 0.66, 0]} c={suit ? shirt : skin} />
          <group position={[0, 0.84, 0]} rotation={[headTilt, 0, 0]}>
            <Ball r={0.15} s={[1, 1.12, 1.02]} c={skin} detail={2} flat={false} />
            {hooded ? <Ball r={0.172} p={[0, 0.02, -0.035]} s={[1.1, 1.16, 1.08]} c={shirt} detail={2} flat={false} /> : null}
            {S.goggles ? (
              <>
                {[-1, 1].map((sx) => (
                  <mesh key={sx} position={[sx * 0.058, 0.03, 0.148]} rotation={[Math.PI / 2, 0, 0]} material={mat("#1C2226", 0.15)}>
                    <cylinderGeometry args={[0.042, 0.042, 0.03, 18]} />
                  </mesh>
                ))}
                <Box s={[0.07, 0.03, 0.03]} p={[0, 0.03, 0.15]} c="#2A2826" rad={0.01} />
                {/* strap round the head */}
                <mesh position={[0, 0.03, -0.005]} rotation={[Math.PI / 2, 0, 0]} material={mat("#2A2826", 0.7)}>
                  <torusGeometry args={[0.152, 0.009, 6, 28]} />
                </mesh>
              </>
            ) : null}
            {S.mask ? (
              <>
                <Ball r={0.06} p={[0, -0.07, 0.13]} s={[1.15, 0.85, 0.8]} c="#3A3836" detail={2} flat={false} />
                {[-1, 1].map((sx) => (
                  <mesh key={`f${sx}`} position={[sx * 0.07, -0.085, 0.15]} rotation={[Math.PI / 2, 0, sx * 0.5]} material={mat("#6E6A64", 0.6)}>
                    <cylinderGeometry args={[0.03, 0.03, 0.035, 14]} />
                  </mesh>
                ))}
              </>
            ) : null}
            {eyes && !S.goggles ? (
              <>
                <Ball r={0.017} p={[0.055, 0.02, 0.145]} c="#1E1A18" detail={1} flat={false} />
                <Ball r={0.017} p={[-0.055, 0.02, 0.145]} c="#1E1A18" detail={1} flat={false} />
              </>
            ) : null}
            {hs !== "bald" && hs !== "cap" && !hooded ? <Ball r={0.158} p={[0, 0.045, -0.015]} s={[1.02, 0.8, 1.04]} c={hair} detail={2} flat={false} /> : null}
            {hs === "long" && !hooded ? <Box s={[0.3, 0.32, 0.12]} p={[0, -0.1, -0.1]} c={hair} rad={0.05} /> : null}
            {hs === "bun" && !hooded ? <Ball r={0.07} p={[0, 0.17, -0.1]} c={hair} detail={1} /> : null}
            {hs === "cap" && !hooded ? (
              <>
                {/* short hair under the cap, crown, forward brim, top button */}
                <Ball r={0.155} p={[0, 0.02, -0.02]} s={[1.02, 0.78, 1.04]} c={hair} detail={2} flat={false} />
                <mesh position={[0, 0.055, -0.006]} scale={[1.06, 0.82, 1.08]} castShadow material={mat(capC, 0.85, undefined, undefined, false)}>
                  <sphereGeometry args={[0.158, 28, 14, 0, Math.PI * 2, 0, Math.PI / 2]} />
                </mesh>
                <mesh position={[0, 0.058, 0.17]} rotation={[0.12, 0, 0]} scale={[1, 0.16, 1]} castShadow material={mat(capC, 0.85, undefined, undefined, false)}>
                  <cylinderGeometry args={[0.105, 0.115, 0.06, 28, 1, false, -Math.PI / 2, Math.PI]} />
                </mesh>
                <Ball r={0.014} p={[0, 0.186, -0.006]} c={capC} detail={1} flat={false} />
              </>
            ) : null}
          </group>
        </group>
      </group>
    </group>
  );
};

// ------------------------------------------------------------------ FURNITURE
export const Desk: React.FC<{ p?: V3; rotY?: number; w?: number; pal: KitPalette }> = ({ p = [0, 0, 0], rotY = 0, w = 1.5, pal }) => (
  <group position={p} rotation={[0, rotY, 0]}>
    <Box s={[w, 0.05, 0.7]} p={[0, 0.74, 0]} c={pal.wood} rad={0.015} />
    {[-1, 1].map((sx) => (
      <Box key={sx} s={[0.05, 0.72, 0.62]} p={[(sx * (w - 0.08)) / 2, 0.36, 0]} c={pal.woodDark} rad={0.01} />
    ))}
  </group>
);

export const Chair: React.FC<{ p?: V3; rotY?: number; c?: string; pal: KitPalette }> = ({ p = [0, 0, 0], rotY = 0, c, pal }) => (
  <group position={p} rotation={[0, rotY, 0]}>
    <Box s={[0.5, 0.08, 0.48]} p={[0, 0.46, 0]} c={c ?? pick(pal.fabric, 0)} rad={0.03} />
    <Box s={[0.5, 0.55, 0.07]} p={[0, 0.76, -0.22]} c={c ?? pick(pal.fabric, 0)} rad={0.03} />
    <Cyl rt={0.03} h={0.42} p={[0, 0.22, 0]} c={pal.metal} />
    <Box s={[0.5, 0.03, 0.06]} p={[0, 0.02, 0]} c={pal.metal} rad={0.01} />
    <Box s={[0.06, 0.03, 0.5]} p={[0, 0.02, 0]} c={pal.metal} rad={0.01} />
  </group>
);

/** Monitor: returns local screen rect (for HTML overlay) via MONITOR_SCREEN */
export const MONITOR_SCREEN = { w: 0.86, h: 0.5, y: 1.12, z: 0.026 };
export const Monitor: React.FC<{ p?: V3; rotY?: number; pal: KitPalette; on?: boolean }> = ({ p = [0, 0, 0], rotY = 0, pal, on = true }) => (
  <group position={p} rotation={[0, rotY, 0]}>
    <Box s={[0.9, 0.54, 0.04]} p={[0, MONITOR_SCREEN.y, 0]} c={pal.metal} rad={0.015} />
    <mesh position={[0, MONITOR_SCREEN.y, 0.021]} material={decal(pal.screen, 0.4, on ? pal.glow : undefined, on ? 0.12 : 0)}>
      <planeGeometry args={[MONITOR_SCREEN.w, MONITOR_SCREEN.h]} />
    </mesh>
    <Box s={[0.06, 0.32, 0.05]} p={[0, 0.92, -0.04]} c={pal.metal} rad={0.01} />
    <Box s={[0.3, 0.02, 0.2]} p={[0, 0.775, -0.02]} c={pal.metal} rad={0.01} />
  </group>
);

export const SmallLaptop: React.FC<{ p?: V3; rotY?: number; pal: KitPalette }> = ({ p = [0, 0, 0], rotY = 0, pal }) => (
  <group position={p} rotation={[0, rotY, 0]}>
    <Box s={[0.42, 0.018, 0.3]} p={[0, 0.775, 0]} c="#8B8C90" rad={0.008} />
    <group position={[0, 0.784, -0.15]} rotation={[-0.3, 0, 0]}>
      <Box s={[0.42, 0.28, 0.012]} p={[0, 0.14, 0]} c="#8B8C90" rad={0.008} />
      <mesh position={[0, 0.14, 0.0065]} material={decal(pal.screen, 0.4, pal.glow, 0.25)}>
        <planeGeometry args={[0.38, 0.24]} />
      </mesh>
    </group>
  </group>
);

export const Sofa: React.FC<{ p?: V3; rotY?: number; c?: string; w?: number; pal: KitPalette }> = ({ p = [0, 0, 0], rotY = 0, c, w = 2.0, pal }) => {
  const col = c ?? pick(pal.fabric, 1);
  return (
    <group position={p} rotation={[0, rotY, 0]}>
      <Box s={[w, 0.4, 0.9]} p={[0, 0.25, 0]} c={col} rad={0.08} />
      <Box s={[w, 0.55, 0.22]} p={[0, 0.6, -0.36]} c={col} rad={0.09} />
      <Box s={[0.22, 0.32, 0.9]} p={[w / 2 - 0.11, 0.55, 0]} c={col} rad={0.08} />
      <Box s={[0.22, 0.32, 0.9]} p={[-w / 2 + 0.11, 0.55, 0]} c={col} rad={0.08} />
      <Box s={[w / 2 - 0.25, 0.12, 0.62]} p={[-(w / 4) + 0.06, 0.5, 0.06]} c={col} rad={0.05} />
      <Box s={[w / 2 - 0.25, 0.12, 0.62]} p={[w / 4 - 0.06, 0.5, 0.06]} c={col} rad={0.05} />
      <Box s={[0.42, 0.34, 0.12]} p={[-w / 2 + 0.45, 0.72, -0.18]} r={[0.2, 0.3, 0]} c={pick(pal.fabric, 4)} rad={0.06} />
    </group>
  );
};

export const Bed: React.FC<{ p?: V3; rotY?: number; pal: KitPalette }> = ({ p = [0, 0, 0], rotY = 0, pal }) => (
  <group position={p} rotation={[0, rotY, 0]}>
    <Box s={[1.6, 0.3, 2.1]} p={[0, 0.2, 0]} c={pal.woodDark} rad={0.04} />
    <Box s={[1.5, 0.2, 2.0]} p={[0, 0.42, 0]} c="#C9BCA8" rad={0.08} />
    <Box s={[1.52, 0.12, 1.3]} p={[0, 0.54, 0.34]} c={pick(pal.fabric, 0)} rad={0.06} />
    <Box s={[0.6, 0.16, 0.36]} p={[-0.38, 0.6, -0.75]} c="#D6CAB6" rad={0.07} />
    <Box s={[0.6, 0.16, 0.36]} p={[0.38, 0.6, -0.75]} c="#D6CAB6" rad={0.07} />
    <Box s={[1.6, 0.9, 0.1]} p={[0, 0.55, -1.03]} c={pal.wood} rad={0.04} />
  </group>
);

export const Table: React.FC<{ p?: V3; r?: number; h?: number; round?: boolean; pal: KitPalette }> = ({ p = [0, 0, 0], r = 0.45, h = 0.45, round = true, pal }) => (
  <group position={p}>
    {round ? <Cyl rt={r} h={0.05} p={[0, h, 0]} c={pal.wood} seg={36} /> : <Box s={[r * 2.4, 0.05, r * 1.4]} p={[0, h, 0]} c={pal.wood} />}
    <Cyl rt={0.04} h={h} p={[0, h / 2, 0]} c={pal.woodDark} />
    <Cyl rt={r * 0.5} h={0.03} p={[0, 0.015, 0]} c={pal.woodDark} seg={24} />
  </group>
);

export const Shelf: React.FC<{ p?: V3; rotY?: number; w?: number; rows?: number; pal: KitPalette; seed?: number }> = ({ p = [0, 0, 0], rotY = 0, w = 1.2, rows = 4, pal, seed = 1 }) => (
  <group position={p} rotation={[0, rotY, 0]}>
    {Array.from({ length: rows + 1 }, (_, i) => (
      <Box key={i} s={[w, 0.04, 0.32]} p={[0, 0.05 + i * 0.42, 0]} c={pal.wood} rad={0.01} />
    ))}
    <Box s={[0.04, rows * 0.42 + 0.06, 0.32]} p={[-w / 2, (rows * 0.42) / 2 + 0.05, 0]} c={pal.woodDark} rad={0.01} />
    <Box s={[0.04, rows * 0.42 + 0.06, 0.32]} p={[w / 2, (rows * 0.42) / 2 + 0.05, 0]} c={pal.woodDark} rad={0.01} />
    {Array.from({ length: rows }, (_, r) => {
      let x = -w / 2 + 0.08;
      const books: React.ReactNode[] = [];
      let k = 0;
      while (x < w / 2 - 0.12 && k < 14) {
        const bw = 0.04 + ((seed * 7 + r * 13 + k * 5) % 5) * 0.012;
        const bh = 0.24 + ((seed * 3 + r * 11 + k * 7) % 4) * 0.03;
        if ((k + r + seed) % 6 === 5) {
          x += 0.1;
          k++;
          continue;
        }
        books.push(<Box key={k} s={[bw, bh, 0.22]} p={[x + bw / 2, 0.07 + r * 0.42 + bh / 2, 0]} c={pick(pal.books, seed + r * 3 + k)} rad={0.006} />);
        x += bw + 0.008;
        k++;
      }
      return <React.Fragment key={r}>{books}</React.Fragment>;
    })}
  </group>
);

export const Plant: React.FC<{ p?: V3; s?: number; pal: KitPalette; kind?: "bush" | "tall" | "cactus" }> = ({ p = [0, 0, 0], s = 1, pal, kind = "bush" }) => (
  <group position={p} scale={s}>
    <Cyl rt={0.17} rb={0.13} h={0.3} p={[0, 0.15, 0]} c={pal.pot} seg={16} />
    {kind === "bush" ? (
      <>
        <Ball r={0.26} p={[0, 0.5, 0]} c={pal.plant} />
        <Ball r={0.2} p={[0.14, 0.66, 0.05]} c={pal.plant2} />
        <Ball r={0.18} p={[-0.13, 0.62, -0.06]} c={pal.plant2} />
      </>
    ) : kind === "tall" ? (
      <>
        <Cyl rt={0.02} h={0.9} p={[0, 0.7, 0]} c={pal.trunk ?? "#4E3E33"} />
        <Ball r={0.3} p={[0, 1.2, 0]} s={[1, 1.3, 1]} c={pal.plant} />
        <Ball r={0.22} p={[0.12, 0.95, 0.08]} c={pal.plant2} />
      </>
    ) : (
      <>
        <Cap r={0.09} len={0.4} p={[0, 0.55, 0]} c={pal.plant} />
        <Cap r={0.05} len={0.15} p={[0.12, 0.6, 0]} r3={[0, 0, -0.8]} c={pal.plant} />
      </>
    )}
  </group>
);

export const Lamp: React.FC<{ p?: V3; floor?: boolean; on?: boolean; pal: KitPalette }> = ({ p = [0, 0, 0], floor = true, on = true, pal }) => (
  <group position={p}>
    {floor ? (
      <>
        <Cyl rt={0.16} h={0.03} p={[0, 0.015, 0]} c={pal.metal} />
        <Cyl rt={0.018} h={1.45} p={[0, 0.73, 0]} c={pal.metal} />
        <Cyl rt={0.14} rb={0.24} h={0.28} p={[0, 1.55, 0]} c={pal.lamp} emissive={on ? pal.lamp : undefined} ei={on ? 0.55 : 0} />
        {on ? <pointLight position={[0, 1.45, 0]} intensity={2.2} distance={5} color={pal.lamp} /> : null}
      </>
    ) : (
      <>
        <Cyl rt={0.07} h={0.02} p={[0, 0.01, 0]} c={pal.metal} />
        <Cyl rt={0.012} h={0.36} p={[0, 0.19, 0]} c={pal.metal} />
        <Cyl rt={0.07} rb={0.12} h={0.14} p={[0, 0.4, 0]} c={pal.lamp} emissive={on ? pal.lamp : undefined} ei={on ? 0.5 : 0} />
        {on ? <pointLight position={[0, 0.35, 0.1]} intensity={1.2} distance={3} color={pal.lamp} /> : null}
      </>
    )}
  </group>
);

export const Rug: React.FC<{ p?: V3; w?: number; d?: number; c?: string; round?: boolean }> = ({ p = [0, 0, 0], w = 2.2, d = 1.6, c = "#7C5F52", round = false }) =>
  round ? (
    <mesh position={[p[0], p[1] + 0.012, p[2]]} rotation={[-Math.PI / 2, 0, 0]} receiveShadow material={mat(c)}>
      <circleGeometry args={[w / 2, 48]} />
    </mesh>
  ) : (
    <Box s={[w, 0.02, d]} p={[p[0], p[1] + 0.01, p[2]]} c={c} rad={0.008} shadow={false} />
  );

export const Frame: React.FC<{ p?: V3; rotY?: number; w?: number; h?: number; c?: string; art?: string }> = ({ p = [0, 0, 0], rotY = 0, w = 0.6, h = 0.8, c = "#3A3632", art = "#8E7264" }) => (
  <group position={p} rotation={[0, rotY, 0]}>
    <Box s={[w, h, 0.04]} c={c} rad={0.01} />
    <mesh position={[0, 0, 0.021]} material={decal(art)}>
      <planeGeometry args={[w - 0.1, h - 0.1]} />
    </mesh>
  </group>
);

export const Mug: React.FC<{ p?: V3; c?: string }> = ({ p = [0, 0, 0], c = "#C9BCA8" }) => (
  <group position={p}>
    <Cyl rt={0.045} h={0.1} p={[0, 0.05, 0]} c={c} seg={16} />
    <mesh position={[0.05, 0.05, 0]} rotation={[0, 0, Math.PI / 2]} material={mat(c)}>
      <torusGeometry args={[0.028, 0.009, 8, 16, Math.PI]} />
    </mesh>
  </group>
);

export const PendantLamp: React.FC<{ p?: V3; pal: KitPalette; drop?: number }> = ({ p = [0, 3, 0], pal, drop = 0.9 }) => (
  <group position={p}>
    <Cyl rt={0.006} h={drop} p={[0, -drop / 2, 0]} c={pal.metal} seg={6} />
    <Cyl rt={0.06} rb={0.22} h={0.2} p={[0, -drop - 0.08, 0]} c={pal.metal} />
    <Ball r={0.07} p={[0, -drop - 0.17, 0]} c={pal.lamp} emissive={pal.lamp} ei={1.2} flat={false} />
    <pointLight position={[0, -drop - 0.3, 0]} intensity={2} distance={4.5} color={pal.lamp} />
  </group>
);

export const Counter: React.FC<{ p?: V3; w?: number; pal: KitPalette }> = ({ p = [0, 0, 0], w = 2.4, pal }) => (
  <group position={p}>
    <Box s={[w, 1.0, 0.6]} p={[0, 0.5, 0]} c={pal.woodDark} rad={0.02} />
    <Box s={[w + 0.08, 0.06, 0.7]} p={[0, 1.03, 0]} c={pal.wood} rad={0.015} />
  </group>
);

export const Stool: React.FC<{ p?: V3; pal: KitPalette; h?: number }> = ({ p = [0, 0, 0], pal, h = 0.75 }) => (
  <group position={p}>
    <Cyl rt={0.18} h={0.05} p={[0, h, 0]} c={pick(pal.fabric, 4)} />
    <Cyl rt={0.025} h={h} p={[0, h / 2, 0]} c={pal.metal} />
    <Cyl rt={0.16} h={0.02} p={[0, 0.01, 0]} c={pal.metal} />
  </group>
);

export const TV_SCREEN = { w: 1.5, h: 0.84, y: 1.5 };
export const TV: React.FC<{ p?: V3; rotY?: number; pal: KitPalette }> = ({ p = [0, 0, 0], rotY = 0, pal }) => (
  <group position={p} rotation={[0, rotY, 0]}>
    <Box s={[1.56, 0.9, 0.05]} p={[0, TV_SCREEN.y, 0]} c={pal.metal} rad={0.012} />
    <mesh position={[0, TV_SCREEN.y, 0.026]} material={decal(pal.screen, 0.4, pal.glow, 0.1)}>
      <planeGeometry args={[TV_SCREEN.w, TV_SCREEN.h]} />
    </mesh>
  </group>
);

// ------------------------------------------------------------------ STREET
export const Car: React.FC<{ p?: V3; rotY?: number; c?: string; lights?: boolean; pal: KitPalette }> = ({ p = [0, 0, 0], rotY = 0, c, lights = false, pal }) => {
  const col = c ?? pick(pal.cars, 0);
  return (
    <group position={p} rotation={[0, rotY, 0]}>
      <Box s={[1.8, 0.55, 4.0]} p={[0, 0.55, 0]} c={col} rad={0.18} />
      <Box s={[1.6, 0.48, 2.1]} p={[0, 1.02, -0.2]} c={col} rad={0.18} />
      <Box s={[1.62, 0.36, 2.0]} p={[0, 1.03, -0.2]} c="#2A2D33" rad={0.12} rough={0.3} />
      {[[-0.82, 1.3], [0.82, 1.3], [-0.82, -1.3], [0.82, -1.3]].map(([x, z], i) => (
        <Cyl key={i} rt={0.34} h={0.26} p={[x, 0.34, z]} r={[0, 0, Math.PI / 2]} c="#1E1E20" seg={18} />
      ))}
      <Box s={[0.36, 0.12, 0.04]} p={[-0.6, 0.62, 2.0]} c="#E8D9B8" emissive={lights ? "#FFE2B0" : undefined} ei={lights ? 2 : 0} rad={0.03} />
      <Box s={[0.36, 0.12, 0.04]} p={[0.6, 0.62, 2.0]} c="#E8D9B8" emissive={lights ? "#FFE2B0" : undefined} ei={lights ? 2 : 0} rad={0.03} />
      <Box s={[0.4, 0.1, 0.04]} p={[-0.6, 0.66, -2.0]} c="#8E3A2E" emissive={lights ? "#C0402A" : undefined} ei={lights ? 1.5 : 0} rad={0.03} />
      <Box s={[0.4, 0.1, 0.04]} p={[0.6, 0.66, -2.0]} c="#8E3A2E" emissive={lights ? "#C0402A" : undefined} ei={lights ? 1.5 : 0} rad={0.03} />
    </group>
  );
};

export const Tree: React.FC<{ p?: V3; s?: number; c?: string; pal: KitPalette; kind?: "round" | "cone" }> = ({ p = [0, 0, 0], s = 1, c, pal, kind = "round" }) => (
  <group position={p} scale={s}>
    <Cyl rt={0.09} rb={0.13} h={2.4} p={[0, 1.2, 0]} c={pal.trunk} seg={8} />
    {kind === "round" ? (
      <>
        <Ball r={0.95} p={[0, 3.0, 0]} c={c ?? pick(pal.tree, 0)} />
        <Ball r={0.7} p={[0.5, 3.4, 0.2]} c={c ?? pick(pal.tree, 1)} />
        <Ball r={0.65} p={[-0.45, 3.3, -0.25]} c={c ?? pick(pal.tree, 2)} />
      </>
    ) : (
      <mesh position={[0, 3.2, 0]} castShadow material={mat(c ?? pick(pal.tree, 1), 0.9, undefined, 1, true)}>
        <coneGeometry args={[0.9, 2.4, 7]} />
      </mesh>
    )}
  </group>
);

export const StreetLamp: React.FC<{ p?: V3; rotY?: number; on?: boolean; pal: KitPalette }> = ({ p = [0, 0, 0], rotY = 0, on = false, pal }) => (
  <group position={p} rotation={[0, rotY, 0]}>
    <Cyl rt={0.06} rb={0.09} h={4.2} p={[0, 2.1, 0]} c={pal.metal} seg={10} />
    <Box s={[0.08, 0.08, 0.9]} p={[0, 4.15, 0.42]} c={pal.metal} rad={0.02} />
    <Box s={[0.3, 0.12, 0.42]} p={[0, 4.08, 0.85]} c={pal.metal} rad={0.04} />
    <mesh position={[0, 4.01, 0.85]} rotation={[Math.PI / 2, 0, 0]} material={decal(pal.lamp, 0.5, on ? pal.lamp : undefined, on ? 2.2 : 0)}>
      <planeGeometry args={[0.24, 0.36]} />
    </mesh>
    {on ? <pointLight position={[0, 3.7, 0.85]} intensity={6} distance={9} color={pal.lamp} /> : null}
  </group>
);

export const Bench: React.FC<{ p?: V3; rotY?: number; pal: KitPalette }> = ({ p = [0, 0, 0], rotY = 0, pal }) => (
  <group position={p} rotation={[0, rotY, 0]}>
    <Box s={[1.6, 0.06, 0.45]} p={[0, 0.45, 0]} c={pal.wood} rad={0.015} />
    <Box s={[1.6, 0.35, 0.05]} p={[0, 0.7, -0.2]} r={[-0.15, 0, 0]} c={pal.wood} rad={0.015} />
    {[-0.7, 0.7].map((x) => (
      <Box key={x} s={[0.06, 0.45, 0.4]} p={[x, 0.22, 0]} c={pal.metal} rad={0.01} />
    ))}
  </group>
);

export const TrafficLight: React.FC<{ p?: V3; rotY?: number; state?: "red" | "green" | "yellow" | "off"; pal: KitPalette }> = ({ p = [0, 0, 0], rotY = 0, state = "green", pal }) => (
  <group position={p} rotation={[0, rotY, 0]}>
    <Cyl rt={0.06} h={3.2} p={[0, 1.6, 0]} c={pal.metal} seg={10} />
    <Box s={[0.32, 0.9, 0.26]} p={[0, 3.3, 0]} c="#24252A" rad={0.05} />
    {(["red", "yellow", "green"] as const).map((k, i) => (
      <mesh key={k} position={[0, 3.58 - i * 0.28, 0.135]} material={decal(k === "red" ? "#5A2A24" : k === "yellow" ? "#5A4A24" : "#2A4A30", 0.5, state === k ? (k === "red" ? "#E0503A" : k === "yellow" ? "#E8B040" : "#6FD08A") : undefined, state === k ? 2.5 : 0)}>
        <circleGeometry args={[0.09, 20]} />
      </mesh>
    ))}
  </group>
);

/** Building facade block with an instanced window grid (lit windows are random but stable) */
export const Building: React.FC<{ p?: V3; w?: number; h?: number; d?: number; c?: string; pal: KitPalette; lit?: number; seed?: number; face?: 1 | -1; awning?: string }> = ({
  p = [0, 0, 0], w = 6, h = 9, d = 6, c, pal, lit = 0.25, seed = 1, face = 1, awning,
}) => {
  const col = c ?? pick(pal.facades, seed);
  const floors = Math.max(1, Math.floor((h - 1.2) / 3));
  const cols = Math.max(1, Math.floor((d - 0.8) / 1.5)); // windows run along the facade (z length = d)
  const wins = useMemo(() => {
    const arr: { x: number; y: number; lit: boolean }[] = [];
    for (let f = 0; f < floors; f++)
      for (let c2 = 0; c2 < cols; c2++) {
        const r = Math.abs(Math.sin(seed * 12.9898 + f * 78.233 + c2 * 37.719) * 43758.5453) % 1;
        arr.push({ x: -d / 2 + 0.8 + (c2 + 0.5) * ((d - 1.6) / cols), y: 3.6 + f * 3, lit: r < lit });
      }
    return arr;
  }, [d, h, floors, cols, seed, lit]);
  // face = +1: windows on the +x side (left-hand street side faces +x)
  const fx = (face * w) / 2 + face * 0.01;
  return (
    <group position={p}>
      <Box s={[w, h, d]} p={[0, h / 2, 0]} c={col} rad={0.04} />
      <Box s={[w + 0.2, 0.25, d + 0.2]} p={[0, h + 0.12, 0]} c={pal.metal} rad={0.03} />
      {wins.map((wi, i) =>
        wi.y < h - 0.6 ? (
          <mesh key={i} position={[fx, wi.y, wi.x]} rotation={[0, (face * Math.PI) / 2, 0]} material={decal(wi.lit ? pal.winLit : pal.winDark, 0.4, wi.lit ? pal.winLit : undefined, wi.lit ? 0.9 : 0)}>
            <planeGeometry args={[0.9, 1.4]} />
          </mesh>
        ) : null,
      )}
      {/* shop front on the ground floor */}
      <mesh position={[fx, 1.35, 0]} rotation={[0, (face * Math.PI) / 2, 0]} material={decal(pal.winDark, 0.3, lit > 0.2 ? pal.winLit : undefined, lit > 0.2 ? 0.35 : 0)}>
        <planeGeometry args={[d * 0.62, 1.9]} />
      </mesh>
      {awning ? <Box s={[0.8, 0.12, d * 0.66]} p={[fx + face * 0.4, 2.55, 0]} r={[0, 0, face * -0.25]} c={awning} rad={0.03} /> : null}
    </group>
  );
};
