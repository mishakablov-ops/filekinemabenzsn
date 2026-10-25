import React, { useMemo } from "react";
import { AbsoluteFill, random } from "remotion";
import * as THREE from "three";
import { useBlockTime, useTheme } from "../core/context";
import { E, clamp01 } from "../core/motion";
import { camAt, makeCamera, project, ShadowGround, Stage3D, type CamKey } from "./core";

const PALETTES = {
  warm: { ground: "#7FA36A", road: "#3B3F46", walk: "#C9C2B6", houses: ["#E9D9C4", "#D8B79A", "#C99A7B", "#EFE6DA", "#B98A6A"], roofs: ["#5E5A57", "#7A4E3C", "#4A4F57"], trees: ["#3E7A45", "#4F8C4E", "#36683C"], blossom: ["#F6B7CF", "#F3C6D8", "#EBA0BE"] },
  white: { ground: "#EEF0F4", road: "#D9DCE3", walk: "#F7F8FA", houses: ["#FFFFFF", "#F4F5F8", "#ECEEF3"], roofs: ["#E2E5EC"], trees: ["#BFD5C4", "#A9C7B1"], blossom: ["#F3C6D8"] },
  night: { ground: "#0C1020", road: "#05070D", walk: "#151B30", houses: ["#1A2240", "#202A4E", "#151C36"], roofs: ["#0E1328"], trees: ["#14304A", "#123A3E"], blossom: ["#7A4DFF"] },
  // dark warm pastel (the house palette): charcoal ground, beige-brown houses, sage trees, terracotta blossom
  dusk: { ground: "#2E2A26", road: "#1C1917", walk: "#3B3530", houses: ["#5A4B40", "#665446", "#4C4038", "#725D4C", "#5F5048"], roofs: ["#2A2420", "#3A2C24", "#8A5440"], trees: ["#55624A", "#626F52", "#4B5743"], blossom: ["#C07A5C", "#D0906E", "#B5705A"] },
  clay: { ground: "#E8D7C3", road: "#CDB8A0", walk: "#F2E6D8", houses: ["#F4E9DC", "#EAD9C6", "#E2CBB2"], roofs: ["#C9A27F", "#B98F6C"], trees: ["#9DB88A", "#86A574"], blossom: ["#F0B6C6"] },
};

// fog = dark pastel haze (never white)
const FOG: Record<string, string> = { warm: "#2A2622", white: "#CFC8BC", night: "#05070D", clay: "#B8A68F", dusk: "#1F1B18" };

type Highlight = { x: number; z: number; label?: string; at?: unknown; radius?: number };

const CAMS: Record<string, CamKey[]> = {
  orbit: [
    { t: 0, pos: [-26, 24, 26], target: [0, 0, 0], fov: 30 },
    { t: 8, pos: [26, 22, 26], target: [0, 0, 0], fov: 30 },
  ],
  dive: [
    { t: 0, pos: [0, 70, 14], target: [0, 0, 0], fov: 30 },
    { t: 4, pos: [10, 15, 18], target: [0, 1, 0], fov: 32, ease: "inOut" },
    { t: 8, pos: [12, 12, 15], target: [0, 1, 0], fov: 32 },
  ],
  street: [
    { t: 0, pos: [-2, 1.6, 16], target: [0, 1.6, 0], fov: 44 },
    { t: 8, pos: [-2, 1.6, 5], target: [0, 1.6, -8], fov: 44 },
  ],
  iso: [
    { t: 0, pos: [36, 36, 36], target: [0, 0, 0], fov: 24 },
    { t: 8, pos: [32, 34, 39], target: [0, 0, 0], fov: 24 },
  ],
  close: [
    { t: 0, pos: [9, 7, 11], target: [1, 0.5, 1], fov: 34 },
    { t: 8, pos: [6, 5.5, 9], target: [1, 0.5, 1], fov: 34 },
  ],
};

export const City3D: React.FC<{
  look?: keyof typeof PALETTES; blocks?: number; seed?: string; cam?: string | CamKey[]; blossom?: number; highlight?: Highlight; grow?: boolean; downtown?: number;
}> = ({ look = "warm", blocks = 7, seed = "c1", cam = "orbit", blossom = 0, highlight, grow = true, downtown = 0.22 }) => {
  const { f, fps, at } = useBlockTime();
  const th = useTheme();
  const t = f / fps;
  const P = PALETTES[look] ?? PALETTES.warm;
  const cell = 4;
  const half = (blocks * cell) / 2;

  const data = useMemo(() => {
    const houses: { x: number; z: number; w: number; d: number; h: number; c: string; roof: string; delay: number }[] = [];
    const trees: { x: number; z: number; s: number; c: string; blossom: boolean }[] = [];
    for (let i = 0; i < blocks; i++) {
      for (let j = 0; j < blocks; j++) {
        const cx = -half + cell * i + cell / 2;
        const cz = -half + cell * j + cell / 2;
        const dist = Math.hypot(cx, cz) / half;
        const tall = Math.max(0, 1 - dist / 0.6) * downtown;
        for (let k = 0; k < 4; k++) {
          const ox = (k % 2 === 0 ? -0.7 : 0.7) + (random(`${seed}ox${i}${j}${k}`) - 0.5) * 0.2;
          const oz = (k < 2 ? -0.7 : 0.7) + (random(`${seed}oz${i}${j}${k}`) - 0.5) * 0.2;
          const r = random(`${seed}h${i}${j}${k}`);
          houses.push({
            x: cx + ox, z: cz + oz, w: 1.0 + r * 0.3, d: 1.0 + random(`${seed}d${i}${j}${k}`) * 0.3,
            h: 0.6 + r * 0.6 + tall * (2 + r * 8),
            c: P.houses[Math.floor(random(`${seed}c${i}${j}${k}`) * P.houses.length)],
            roof: P.roofs[Math.floor(random(`${seed}r${i}${j}${k}`) * P.roofs.length)],
            delay: (dist + random(`${seed}dl${i}${j}${k}`) * 0.3) * 0.9,
          });
        }
        // street trees along block edges
        for (let k = 0; k < 6; k++) {
          const side = k % 4;
          const u = (k / 6) * 3 - 1.5;
          const x = cx + (side === 0 ? -1.75 : side === 1 ? 1.75 : u);
          const z = cz + (side === 2 ? -1.75 : side === 3 ? 1.75 : u);
          const b = random(`${seed}tb${i}${j}${k}`) < blossom;
          trees.push({ x, z, s: 0.32 + random(`${seed}ts${i}${j}${k}`) * 0.18, c: (b ? P.blossom : P.trees)[Math.floor(random(`${seed}tc${i}${j}${k}`) * (b ? P.blossom : P.trees).length)], blossom: b });
        }
      }
    }
    return { houses, trees };
  }, [blocks, seed, look, blossom, downtown]);

  const houseMesh = useMemo(() => {
    const geo = new THREE.BoxGeometry(1, 1, 1);
    geo.translate(0, 0.5, 0);
    const mat = new THREE.MeshStandardMaterial({ roughness: 0.85, metalness: 0 });
    const im = new THREE.InstancedMesh(geo, mat, data.houses.length);
    im.castShadow = true;
    im.receiveShadow = true;
    data.houses.forEach((h, i) => im.setColorAt(i, new THREE.Color(h.c)));
    return im;
  }, [data]);
  const roofMesh = useMemo(() => {
    const geo = new THREE.ConeGeometry(0.75, 0.5, 4);
    geo.rotateY(Math.PI / 4);
    geo.translate(0, 0.25, 0);
    const im = new THREE.InstancedMesh(geo, new THREE.MeshStandardMaterial({ roughness: 0.7 }), data.houses.length);
    im.castShadow = true;
    data.houses.forEach((h, i) => im.setColorAt(i, new THREE.Color(h.roof)));
    return im;
  }, [data]);
  const treeMesh = useMemo(() => {
    const geo = new THREE.IcosahedronGeometry(1, 1);
    const im = new THREE.InstancedMesh(geo, new THREE.MeshStandardMaterial({ roughness: 0.9, flatShading: true }), data.trees.length);
    im.castShadow = true;
    data.trees.forEach((tr, i) => im.setColorAt(i, new THREE.Color(tr.c)));
    return im;
  }, [data]);

  const m = new THREE.Matrix4();
  const q = new THREE.Quaternion();
  data.houses.forEach((h, i) => {
    const g = grow ? E.outExpo(clamp01((t - h.delay * 1.2) / 0.9)) : 1;
    const hh = Math.max(0.001, h.h * g);
    houseMesh.setMatrixAt(i, m.compose(new THREE.Vector3(h.x, 0, h.z), q, new THREE.Vector3(h.w, hh, h.d)));
    const isRoofed = h.h < 1.4;
    roofMesh.setMatrixAt(i, m.compose(new THREE.Vector3(h.x, hh, h.z), q, new THREE.Vector3(isRoofed ? h.w : 0.001, isRoofed ? g : 0.001, isRoofed ? h.d : 0.001)));
  });
  houseMesh.instanceMatrix.needsUpdate = true;
  roofMesh.instanceMatrix.needsUpdate = true;
  data.trees.forEach((tr, i) => {
    const g = grow ? E.out(clamp01((t - 0.6 - (Math.hypot(tr.x, tr.z) / half) * 0.8) / 0.6)) : 1;
    const s = tr.s * g * (tr.blossom ? 1.35 : 1);
    treeMesh.setMatrixAt(i, m.compose(new THREE.Vector3(tr.x, 0.35 + s, tr.z), q, new THREE.Vector3(s, s * 1.1, s)));
  });
  treeMesh.instanceMatrix.needsUpdate = true;

  const keys = Array.isArray(cam) ? cam : CAMS[cam] ?? CAMS.orbit;
  const c = camAt(keys, t);
  const camera = makeCamera(c);
  const hs = highlight ? (highlight.at !== undefined ? at(highlight.at) : Math.round(1.5 * fps)) : 0;
  const hp = highlight ? E.out(clamp01((f - hs) / (0.6 * fps))) : 0;
  const ring = ((f - hs) % 50) / 50;
  return (
    <AbsoluteFill>
      <Stage3D cam={c} lights={look === "night" ? "night" : "soft"} env={0.6} fog={{ color: FOG[look] ?? "#2A2622", near: 45, far: 150 }}>
        <mesh rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
          <planeGeometry args={[half * 2 + 30, half * 2 + 30]} />
          <meshStandardMaterial color={P.road} roughness={0.95} />
        </mesh>
        {Array.from({ length: blocks * blocks }, (_, k) => {
          const i = Math.floor(k / blocks);
          const j = k % blocks;
          return (
            <mesh key={k} position={[-half + cell * i + cell / 2, 0.06, -half + cell * j + cell / 2]} receiveShadow>
              <boxGeometry args={[cell - 0.5, 0.12, cell - 0.5]} />
              <meshStandardMaterial color={P.ground} roughness={0.95} />
            </mesh>
          );
        })}
        <primitive object={houseMesh} />
        <primitive object={roofMesh} />
        <primitive object={treeMesh} />
        <ShadowGround y={0.001} opacity={0.2} />
        {highlight && hp > 0 ? (
          <group position={[highlight.x, 0.15, highlight.z]} rotation={[-Math.PI / 2, 0, 0]}>
            <mesh scale={hp}>
              <ringGeometry args={[(highlight.radius ?? 1.2) * 0.9, highlight.radius ?? 1.2, 64]} />
              <meshBasicMaterial color={th.accent} toneMapped={false} />
            </mesh>
            <mesh scale={1 + ring * 1.6}>
              <ringGeometry args={[(highlight.radius ?? 1.2) * 0.96, highlight.radius ?? 1.2, 64]} />
              <meshBasicMaterial color={th.accent} transparent opacity={(1 - ring) * hp} toneMapped={false} />
            </mesh>
          </group>
        ) : null}
      </Stage3D>
      {highlight?.label && hp > 0
        ? (() => {
            const [x, y] = project(camera, new THREE.Vector3(highlight.x, 0.2, highlight.z));
            return (
              <div style={{ position: "absolute", left: x - 260, top: y + 60, width: 520, textAlign: "center", opacity: hp }}>
                <span style={{ font: `600 30px ${th.fontMono}`, color: "#fff", background: "rgba(10,12,20,0.7)", padding: "10px 18px", borderRadius: 10 }}>{highlight.label}</span>
              </div>
            );
          })()
        : null}
    </AbsoluteFill>
  );
};
