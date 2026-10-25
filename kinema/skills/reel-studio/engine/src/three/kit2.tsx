/**
 * Kit extension: cozy interiors (library, kitchen, cabin) + survival / post-apocalypse props.
 * Same rules as kit.tsx: metres, flat dark-pastel colours, soft shadows, decals for thin surface details.
 */
import React, { useMemo } from "react";
import { random } from "remotion";
import * as THREE from "three";
import { canvasTexture, type V3 } from "./core";
import { Ball, Box, Cap, Cyl, decal, mat, pick, type KitPalette } from "./kit";

const G: React.FC<{ p?: V3; rotY?: number; children: React.ReactNode }> = ({ p = [0, 0, 0], rotY = 0, children }) => (
  <group position={p} rotation={[0, rotY, 0]}>{children}</group>
);

// ================================================================== COZY
export const Armchair: React.FC<{ p?: V3; rotY?: number; c?: string; pal: KitPalette }> = ({ p, rotY, c, pal }) => {
  const col = c ?? pick(pal.fabric, 3);
  return (
    <G p={p} rotY={rotY}>
      <Box s={[0.9, 0.36, 0.85]} p={[0, 0.24, 0]} c={col} rad={0.08} />
      <Box s={[0.9, 0.62, 0.2]} p={[0, 0.64, -0.33]} c={col} rad={0.09} />
      <Box s={[0.18, 0.3, 0.85]} p={[0.36, 0.52, 0]} c={col} rad={0.07} />
      <Box s={[0.18, 0.3, 0.85]} p={[-0.36, 0.52, 0]} c={col} rad={0.07} />
      <Box s={[0.56, 0.12, 0.6]} p={[0, 0.47, 0.06]} c={col} rad={0.05} />
      {[-0.36, 0.36].map((x) => [-0.32, 0.32].map((z) => <Cyl key={`${x}${z}`} rt={0.025} h={0.08} p={[x, 0.04, z]} c={pal.woodDark} seg={8} />))}
    </G>
  );
};

export const SideTable: React.FC<{ p?: V3; pal: KitPalette; h?: number }> = ({ p, pal, h = 0.55 }) => (
  <G p={p}>
    <Cyl rt={0.26} h={0.04} p={[0, h, 0]} c={pal.wood} seg={28} />
    {[0, 1, 2].map((i) => {
      const a = (i / 3) * Math.PI * 2;
      return <Cyl key={i} rt={0.018} h={h} p={[Math.cos(a) * 0.17, h / 2, Math.sin(a) * 0.17]} c={pal.woodDark} seg={8} />;
    })}
  </G>
);

export const BookStack: React.FC<{ p?: V3; n?: number; pal: KitPalette; seed?: number; rotY?: number }> = ({ p, n = 3, pal, seed = 1, rotY }) => (
  <G p={p} rotY={rotY}>
    {Array.from({ length: n }, (_, i) => (
      <Box key={i} s={[0.24 - (i % 2) * 0.03, 0.045, 0.17]} p={[0, 0.0225 + i * 0.047, 0]} r={[0, (random(`bs${seed}${i}`) - 0.5) * 0.4, 0]} c={pick(pal.books, seed + i * 2)} rad={0.006} />
    ))}
  </G>
);

export const Candle: React.FC<{ p?: V3; t?: number; h?: number }> = ({ p, t = 0, h = 0.14 }) => {
  const fl = 0.85 + Math.sin(t * 17) * 0.08 + Math.sin(t * 29) * 0.05;
  return (
    <G p={p}>
      <Cyl rt={0.03} h={h} p={[0, h / 2, 0]} c="#D9CCB4" seg={12} />
      <Ball r={0.016} p={[0, h + 0.03, 0]} s={[1, 1.8 * fl, 1]} c="#F2B66A" emissive="#F2A04A" ei={2.2} flat={false} />
      <pointLight position={[0, h + 0.06, 0]} intensity={0.55 * fl} distance={2.2} color="#F2A86A" />
    </G>
  );
};

export const Fireplace: React.FC<{ p?: V3; rotY?: number; pal: KitPalette; t?: number }> = ({ p, rotY, pal, t = 0 }) => {
  const brick = "#7A5848";
  const fl = 0.85 + Math.sin(t * 9) * 0.1 + Math.sin(t * 23) * 0.06;
  return (
    <G p={p} rotY={rotY}>
      {/* body with a real firebox cavity: pillars + lintel + hearth + sooty back */}
      <Box s={[0.35, 1.2, 0.55]} p={[-0.675, 0.6, 0]} c={brick} rad={0.03} />
      <Box s={[0.35, 1.2, 0.55]} p={[0.675, 0.6, 0]} c={brick} rad={0.03} />
      <Box s={[1.0, 0.3, 0.55]} p={[0, 1.05, 0]} c={brick} rad={0.02} />
      <Box s={[1.0, 0.1, 0.55]} p={[0, 0.05, 0]} c="#4A3A32" rad={0.01} />
      <Box s={[1.0, 0.8, 0.08]} p={[0, 0.5, -0.235]} c="#1E1814" rad={0.01} />
      <Box s={[1.95, 0.1, 0.7]} p={[0, 1.25, 0.03]} c={pal.woodDark} rad={0.02} />
      <Box s={[1.3, 1.9, 0.4]} p={[0, 2.25, -0.06]} c={brick} rad={0.03} />
      {/* logs + flames inside the cavity */}
      <Cap r={0.06} len={0.5} p={[0, 0.17, 0.0]} r3={[0, 0, Math.PI / 2]} c="#4A3326" />
      <Cap r={0.055} len={0.45} p={[0.04, 0.27, 0.03]} r3={[0, 0.5, Math.PI / 2]} c="#3E2A20" />
      {/* back glow, ember bed, layered flames */}
      <mesh position={[0, 0.5, -0.19]} material={decal("#5A2E1A", 0.9, "#E07030", 0.9 * fl)}><planeGeometry args={[0.9, 0.6]} /></mesh>
      <Box s={[0.7, 0.04, 0.3]} p={[0, 0.12, 0.0]} c="#6A2E1C" emissive="#E06A2A" ei={1.4 * fl} rad={0.015} />
      {[-0.22, -0.08, 0.06, 0.2].map((x, i) => {
        const h = 0.36 + ((i * 37) % 5) * 0.05;
        const w = Math.sin(t * (7 + i) + i) * 0.04;
        return (
          <group key={i} position={[x, 0.2 + h / 2, 0.02]} rotation={[0, 0, w]} scale={[1, fl * (0.9 + 0.2 * Math.sin(t * (5 + i * 1.7))), 1]}>
            <mesh material={mat("#E8863E", 0.5, "#E8742C", 1.25)}><coneGeometry args={[0.1, h, 8]} /></mesh>
            <mesh position={[0, -h * 0.12, 0.02]} material={mat("#F2B868", 0.5, "#F0A850", 1.5)}><coneGeometry args={[0.05, h * 0.6, 8]} /></mesh>
          </group>
        );
      })}
      <pointLight position={[0, 0.55, 0.6]} intensity={3.2 * fl} distance={6} color="#F29A55" />
      {/* mantle décor */}
      <Candle p={[-0.7, 1.3, 0.05]} t={t} />
      <Candle p={[-0.55, 1.3, 0.08]} t={t + 0.7} h={0.1} />
      <BookStack p={[0.6, 1.3, 0.03]} pal={pal} n={3} seed={5} />
    </G>
  );
};

export const WallClock: React.FC<{ p?: V3; rotY?: number; pal: KitPalette }> = ({ p, rotY, pal }) => (
  <G p={p} rotY={rotY}>
    <mesh rotation={[Math.PI / 2, 0, 0]} material={mat(pal.woodDark)}>
      <cylinderGeometry args={[0.24, 0.24, 0.05, 32]} />
    </mesh>
    <mesh position={[0, 0, 0.026]} material={decal("#D9CCB6")}>
      <circleGeometry args={[0.2, 32]} />
    </mesh>
    <mesh position={[0, 0.06, 0.03]} material={decal("#2A2420")}><planeGeometry args={[0.014, 0.13]} /></mesh>
    <mesh position={[0.045, 0, 0.031]} rotation={[0, 0, Math.PI / 2]} material={decal("#2A2420")}><planeGeometry args={[0.012, 0.09]} /></mesh>
  </G>
);

export const Curtain: React.FC<{ p?: V3; rotY?: number; h?: number; c?: string }> = ({ p, rotY, h = 2.3, c = "#7E5E52" }) => (
  <G p={p} rotY={rotY}>
    {Array.from({ length: 5 }, (_, i) => (
      <Cap key={i} r={0.05} len={h - 0.1} p={[0, h / 2, (i - 2) * 0.09]} c={c} />
    ))}
  </G>
);

export const Fridge: React.FC<{ p?: V3; rotY?: number; pal: KitPalette }> = ({ p, rotY, pal }) => (
  <G p={p} rotY={rotY}>
    <Box s={[0.75, 1.95, 0.7]} p={[0, 0.975, 0]} c="#B9AC98" rad={0.05} />
    <mesh position={[0, 1.33, 0.353]} material={decal("#9E927F")}><planeGeometry args={[0.72, 0.012]} /></mesh>
    <Box s={[0.035, 0.42, 0.04]} p={[0.28, 1.6, 0.37]} c={pal.metal} rad={0.015} />
    <Box s={[0.035, 0.55, 0.04]} p={[0.28, 0.85, 0.37]} c={pal.metal} rad={0.015} />
  </G>
);

export const Stove: React.FC<{ p?: V3; rotY?: number; pal: KitPalette; t?: number; pot?: boolean }> = ({ p, rotY, pal, t = 0, pot = true }) => (
  <G p={p} rotY={rotY}>
    <Box s={[0.75, 0.9, 0.65]} p={[0, 0.45, 0]} c="#4A4642" rad={0.03} />
    <Box s={[0.6, 0.42, 0.02]} p={[0, 0.42, 0.33]} c="#1F1D1B" rad={0.01} />
    <Box s={[0.5, 0.03, 0.03]} p={[0, 0.7, 0.35]} c={pal.metal} rad={0.01} />
    {[[-0.18, -0.15], [0.18, -0.15], [-0.18, 0.15], [0.18, 0.15]].map(([x, z], i) => (
      <mesh key={i} position={[x, 0.904, z]} rotation={[-Math.PI / 2, 0, 0]} material={decal("#25221F")}>
        <ringGeometry args={[0.06, 0.1, 24]} />
      </mesh>
    ))}
    {pot ? (
      <>
        <Cyl rt={0.14} rb={0.12} h={0.16} p={[-0.18, 0.99, -0.15]} c="#6E6A64" seg={20} />
        <Cap r={0.012} len={0.16} p={[-0.38, 1.04, -0.15]} r3={[0, 0, Math.PI / 2]} c={pal.metal} />
        {Array.from({ length: 7 }, (_, i) => {
          const k = (t * 0.28 + i / 7) % 1;
          return (
            <mesh key={i} position={[-0.18 + Math.sin(i * 2.3 + t * 1.3) * 0.05 * k, 1.1 + k * 0.7, -0.15 + Math.cos(i * 1.7 + t) * 0.04 * k]} scale={0.04 + k * 0.12}>
              <icosahedronGeometry args={[1, 2]} />
              <meshStandardMaterial color="#D9CCB8" transparent opacity={0.28 * (1 - k) * Math.min(1, k * 5)} roughness={1} depthWrite={false} />
            </mesh>
          );
        })}
      </>
    ) : null}
  </G>
);

export const KitchenCounter: React.FC<{ p?: V3; rotY?: number; w?: number; pal: KitPalette; sink?: boolean; upper?: boolean }> = ({ p, rotY, w = 2.4, pal, sink = true, upper = true }) => {
  const doors = Math.max(1, Math.round(w / 0.6));
  return (
    <G p={p} rotY={rotY}>
      <Box s={[w, 0.86, 0.6]} p={[0, 0.43, 0]} c={pal.wood} rad={0.02} />
      {Array.from({ length: doors }, (_, i) => (
        <React.Fragment key={i}>
          <mesh position={[-w / 2 + (i + 0.5) * (w / doors), 0.43, 0.301]} material={decal(pal.woodDark)}><planeGeometry args={[w / doors - 0.06, 0.74]} /></mesh>
          <Box s={[0.12, 0.02, 0.025]} p={[-w / 2 + (i + 0.5) * (w / doors), 0.74, 0.315]} c={pal.metal} rad={0.008} />
        </React.Fragment>
      ))}
      <Box s={[w + 0.04, 0.05, 0.64]} p={[0, 0.885, 0.01]} c="#C9BCA8" rad={0.01} />
      {sink ? (
        <>
          <Box s={[0.55, 0.012, 0.38]} p={[w * 0.18, 0.912, 0.02]} c="#6E6A64" rad={0.004} />
          <Cyl rt={0.015} h={0.3} p={[w * 0.18, 1.06, -0.2]} c={pal.metal} seg={10} />
          <Cap r={0.013} len={0.16} p={[w * 0.18, 1.2, -0.12]} r3={[Math.PI / 2, 0, 0]} c={pal.metal} />
        </>
      ) : null}
      {upper ? (
        <>
          <Box s={[w, 0.7, 0.34]} p={[0, 1.95, -0.13]} c={pal.wood} rad={0.02} />
          {Array.from({ length: doors }, (_, i) => (
            <mesh key={i} position={[-w / 2 + (i + 0.5) * (w / doors), 1.95, 0.041]} material={decal(pal.woodDark)}><planeGeometry args={[w / doors - 0.06, 0.6]} /></mesh>
          ))}
        </>
      ) : null}
    </G>
  );
};

export const WoodChair: React.FC<{ p?: V3; rotY?: number; pal: KitPalette }> = ({ p, rotY, pal }) => (
  <G p={p} rotY={rotY}>
    <Box s={[0.44, 0.05, 0.42]} p={[0, 0.46, 0]} c={pal.wood} rad={0.015} />
    <Box s={[0.44, 0.42, 0.04]} p={[0, 0.7, -0.2]} c={pal.wood} rad={0.015} />
    {[[-0.19, -0.18], [0.19, -0.18], [-0.19, 0.18], [0.19, 0.18]].map(([x, z], i) => (
      <Box key={i} s={[0.04, 0.46, 0.04]} p={[x, 0.23, z]} c={pal.woodDark} rad={0.01} />
    ))}
  </G>
);

export const DiningTable: React.FC<{ p?: V3; rotY?: number; w?: number; d?: number; pal: KitPalette; chairs?: boolean }> = ({ p, rotY, w = 1.6, d = 0.9, pal, chairs = true }) => (
  <G p={p} rotY={rotY}>
    <Box s={[w, 0.05, d]} p={[0, 0.75, 0]} c={pal.wood} rad={0.015} />
    {[[-1, -1], [1, -1], [-1, 1], [1, 1]].map(([sx, sz], i) => (
      <Box key={i} s={[0.06, 0.73, 0.06]} p={[sx * (w / 2 - 0.08), 0.365, sz * (d / 2 - 0.08)]} c={pal.woodDark} rad={0.01} />
    ))}
    {chairs ? (
      <>
        <WoodChair p={[-w / 4, 0, d / 2 + 0.3]} rotY={Math.PI} pal={pal} />
        <WoodChair p={[w / 4, 0, d / 2 + 0.3]} rotY={Math.PI} pal={pal} />
        <WoodChair p={[-w / 4, 0, -d / 2 - 0.3]} pal={pal} />
        <WoodChair p={[w / 4, 0, -d / 2 - 0.3]} pal={pal} />
      </>
    ) : null}
  </G>
);

/** horizontal log courses on a wall face (cabin) */
export const LogWall: React.FC<{ p?: V3; rotY?: number; w: number; h: number; c: string; c2: string }> = ({ p, rotY, w, h, c, c2 }) => {
  const n = Math.floor(h / 0.24);
  return (
    <G p={p} rotY={rotY}>
      <Box s={[w, h, 0.12]} p={[0, h / 2, -0.06]} c={c2} rad={0.01} />
      {Array.from({ length: n }, (_, i) => (
        <mesh key={i} position={[0, 0.12 + i * 0.24, 0.02]} rotation={[0, 0, Math.PI / 2]} castShadow receiveShadow material={mat(i % 2 ? c : c2, 0.9)}>
          <cylinderGeometry args={[0.115, 0.115, w, 12, 1, false, 0, Math.PI]} />
        </mesh>
      ))}
    </G>
  );
};

// ================================================================== SURVIVAL / SHELTER
/** canvas-textured label sheet */
const useLabelTex = (w: number, h: number, draw: (g: CanvasRenderingContext2D) => void, key: string) =>
  useMemo(() => canvasTexture(w, h, draw), [key]); // eslint-disable-line react-hooks/exhaustive-deps

export const Can: React.FC<{ p?: V3; c?: string; s?: number }> = ({ p, c = "#8E6A5A", s = 1 }) => (
  <group position={p} scale={s}>
    <Cyl rt={0.045} h={0.11} p={[0, 0.055, 0]} c="#9A958C" seg={14} />
    <Cyl rt={0.0465} h={0.07} p={[0, 0.055, 0]} c={c} seg={14} />
  </group>
);

export const WaterBottle: React.FC<{ p?: V3; s?: number }> = ({ p, s = 1 }) => (
  <group position={p} scale={s}>
    <Cyl rt={0.045} h={0.26} p={[0, 0.13, 0]} c="#7E9AA0" seg={14} />
    <Cyl rt={0.018} h={0.04} p={[0, 0.28, 0]} c="#3E5A62" seg={10} />
  </group>
);

export const WaterJug: React.FC<{ p?: V3; rotY?: number }> = ({ p, rotY }) => (
  <G p={p} rotY={rotY}>
    <Box s={[0.28, 0.42, 0.28]} p={[0, 0.21, 0]} c="#6F8E96" rad={0.06} />
    <Cyl rt={0.04} h={0.08} p={[0, 0.46, 0]} c="#3E5A62" seg={10} />
    <Box s={[0.12, 0.03, 0.03]} p={[0, 0.44, -0.1]} c="#3E5A62" rad={0.01} />
  </G>
);

/** steel shelving filled with cans, bottles, boxes */
export const SupplyRack: React.FC<{ p?: V3; rotY?: number; w?: number; levels?: number; seed?: number; pal: KitPalette }> = ({ p, rotY, w = 1.4, levels = 4, seed = 1, pal }) => {
  const steel = "#5E5C58";
  const items = useMemo(() => {
    const out: { k: "can" | "bottle" | "box" | "jug"; x: number; y: number; c: string }[] = [];
    for (let l = 0; l < levels; l++) {
      let x = -w / 2 + 0.1;
      let i = 0;
      const y = 0.08 + l * 0.48 + 0.02;
      while (x < w / 2 - 0.1 && i < 30) {
        const r = random(`sr${seed}${l}${i}`);
        const k = l === 0 ? (r < 0.5 ? "jug" : "box") : r < 0.55 ? "can" : r < 0.85 ? "bottle" : "box";
        const wd = k === "jug" ? 0.3 : k === "box" ? 0.3 : k === "bottle" ? 0.1 : 0.1;
        if (random(`sg${seed}${l}${i}`) < 0.12) { x += 0.12; i++; continue; }
        out.push({ k, x: x + wd / 2, y, c: pick(["#8E6A5A", "#7A8468", "#A0704F", "#6E5E70", "#9A8456"], seed + l * 3 + i) });
        x += wd + 0.015;
        i++;
      }
    }
    return out;
  }, [w, levels, seed]);
  return (
    <G p={p} rotY={rotY}>
      {Array.from({ length: levels + 1 }, (_, l) => (
        <Box key={l} s={[w, 0.03, 0.42]} p={[0, 0.07 + l * 0.48, 0]} c={steel} rad={0.005} />
      ))}
      {[-1, 1].map((sx) => [-1, 1].map((sz) => (
        <Box key={`${sx}${sz}`} s={[0.035, levels * 0.48 + 0.12, 0.035]} p={[sx * (w / 2 - 0.02), (levels * 0.48 + 0.12) / 2, sz * 0.19]} c="#4A4844" rad={0.004} />
      )))}
      {items.map((it, i) =>
        it.k === "can" ? (
          <group key={i}>
            <Can p={[it.x, it.y, 0.05]} c={it.c} />
            {random(`st${seed}${i}`) < 0.5 ? <Can p={[it.x, it.y + 0.11, 0.05]} c={it.c} /> : null}
          </group>
        ) : it.k === "bottle" ? (
          <WaterBottle key={i} p={[it.x, it.y, 0.0]} />
        ) : it.k === "jug" ? (
          <WaterJug key={i} p={[it.x, it.y - 0.02, 0]} />
        ) : (
          <Box key={i} s={[0.28, 0.22, 0.3]} p={[it.x, it.y + 0.11, 0]} c="#8A7058" rad={0.01} />
        ),
      )}
    </G>
  );
};

export const CrankRadio: React.FC<{ p?: V3; rotY?: number; on?: boolean; t?: number }> = ({ p, rotY, on = true, t = 0 }) => {
  const tex = useLabelTex(256, 128, (g) => {
    g.fillStyle = "#2A2622"; g.fillRect(0, 0, 256, 128);
    g.fillStyle = "#3A342E";
    for (let y = 10; y < 118; y += 9) for (let x = 10; x < 120; x += 9) { g.beginPath(); g.arc(x, y, 2.6, 0, 7); g.fill(); }
    g.fillStyle = "#E8A86A"; g.fillRect(140, 30, 100, 26);
    g.fillStyle = "#2A2622"; g.font = "bold 18px monospace"; g.fillText("FM 104.2", 146, 50);
  }, "radio");
  const glow = on ? 0.6 + Math.sin(t * 3) * 0.08 : 0;
  return (
    <G p={p} rotY={rotY}>
      <Box s={[0.36, 0.2, 0.12]} p={[0, 0.1, 0]} c="#5A4E44" rad={0.03} />
      <mesh position={[0, 0.1, 0.061]}>
        <planeGeometry args={[0.32, 0.16]} />
        <meshStandardMaterial map={tex} roughness={0.7} emissive="#E8A86A" emissiveIntensity={glow * 0.25} emissiveMap={tex} polygonOffset polygonOffsetFactor={-2} polygonOffsetUnits={-4} />
      </mesh>
      <Cyl rt={0.006} h={0.4} p={[0.14, 0.38, -0.03]} r={[0, 0, -0.25]} c="#8A877F" seg={6} />
      <group position={[-0.19, 0.1, 0]} rotation={[t * 4, 0, 0]}>
        <Box s={[0.02, 0.12, 0.02]} p={[-0.01, 0.05, 0]} c="#3E3833" rad={0.005} />
        <Cyl rt={0.012} h={0.04} p={[-0.02, 0.1, 0.02]} r={[Math.PI / 2, 0, 0]} c="#8A6A4E" seg={8} />
      </group>
      {on ? <pointLight position={[0, 0.12, 0.25]} intensity={0.35} distance={1.4} color="#E8A86A" /> : null}
    </G>
  );
};

export const Lantern: React.FC<{ p?: V3; t?: number; on?: boolean; intensity?: number }> = ({ p, t = 0, on = true, intensity = 2.6 }) => {
  const fl = 0.92 + Math.sin(t * 11) * 0.05 + Math.sin(t * 27) * 0.03;
  return (
    <G p={p}>
      <Cyl rt={0.09} h={0.03} p={[0, 0.015, 0]} c="#3A3632" seg={16} />
      <Cyl rt={0.07} h={0.2} p={[0, 0.13, 0]} c="#E8C08A" seg={16} emissive={on ? "#F0B060" : undefined} ei={on ? 1.6 * fl : 0} />
      <Cyl rt={0.08} rb={0.09} h={0.04} p={[0, 0.25, 0]} c="#3A3632" seg={16} />
      <mesh position={[0, 0.3, 0]} rotation={[Math.PI / 2, 0, 0]} material={mat("#3A3632")}><torusGeometry args={[0.05, 0.007, 6, 16]} /></mesh>
      {on ? <pointLight position={[0, 0.2, 0]} intensity={intensity * fl} distance={5.5} color="#F2B070" castShadow /> : null}
    </G>
  );
};

export const Bucket: React.FC<{ p?: V3; lid?: boolean; c?: string }> = ({ p, lid = true, c = "#6E7A6A" }) => (
  <G p={p}>
    <Cyl rt={0.16} rb={0.13} h={0.36} p={[0, 0.18, 0]} c={c} seg={18} />
    {lid ? <Cyl rt={0.17} h={0.03} p={[0, 0.375, 0]} c="#4E5A4C" seg={18} /> : null}
    <mesh position={[0, 0.36, 0]} rotation={[0, 0, 0]} material={mat("#4A4844")}><torusGeometry args={[0.15, 0.006, 6, 20, Math.PI]} /></mesh>
  </G>
);

export const Mattress: React.FC<{ p?: V3; rotY?: number; pal: KitPalette }> = ({ p, rotY, pal }) => (
  <G p={p} rotY={rotY}>
    <Box s={[0.95, 0.12, 1.95]} p={[0, 0.07, 0]} c="#5E564C" rad={0.02} />
    <Box s={[0.9, 0.14, 1.9]} p={[0, 0.2, 0]} c="#A89A86" rad={0.06} />
    <Box s={[0.92, 0.06, 1.15]} p={[0, 0.3, 0.35]} c={pick(pal.fabric, 2)} rad={0.04} />
    <Box s={[0.55, 0.12, 0.32]} p={[0, 0.33, -0.7]} c="#C2B6A2" rad={0.06} />
  </G>
);

export const Sandbags: React.FC<{ p?: V3; rotY?: number; rows?: number; cols?: number }> = ({ p, rotY, rows = 3, cols = 4 }) => (
  <G p={p} rotY={rotY}>
    {Array.from({ length: rows }, (_, r) =>
      Array.from({ length: cols - (r % 2) }, (_, c) => (
        <Cap key={`${r}${c}`} r={0.13} len={0.32} p={[(c - (cols - 1 - (r % 2)) / 2) * 0.5, 0.13 + r * 0.22, 0]} r3={[0, 0, Math.PI / 2]} c={pick(["#8A7A60", "#7E705A", "#948468"], r + c)} />
      )),
    )}
  </G>
);

export const WaterHeater: React.FC<{ p?: V3; pal: KitPalette }> = ({ p, pal }) => (
  <G p={p}>
    <Cyl rt={0.28} h={1.5} p={[0, 0.75, 0]} c="#A8A096" seg={24} />
    <Cyl rt={0.29} h={0.06} p={[0, 1.52, 0]} c="#8A847C" seg={24} />
    <Cyl rt={0.025} h={1.4} p={[-0.12, 2.25, 0]} c={pal.metal} seg={8} />
    <Cyl rt={0.025} h={1.4} p={[0.12, 2.25, 0]} c={pal.metal} seg={8} />
    <Cyl rt={0.03} h={0.1} p={[0, 0.2, 0.28]} r={[Math.PI / 2, 0, 0]} c="#B08A4A" seg={10} />
    <mesh position={[0, 0.95, 0.281]} material={decal("#3E3A36")}><planeGeometry args={[0.16, 0.1]} /></mesh>
  </G>
);

/** heavy steel door in a frame; open = 0..1 swings it inward */
export const SteelDoor: React.FC<{ p?: V3; rotY?: number; open?: number; pal: KitPalette }> = ({ p, rotY, open = 0, pal }) => (
  <G p={p} rotY={rotY}>
    <Box s={[1.2, 0.1, 0.25]} p={[0, 2.15, 0]} c="#4A4844" rad={0.01} />
    <Box s={[0.1, 2.2, 0.25]} p={[-0.55, 1.1, 0]} c="#4A4844" rad={0.01} />
    <Box s={[0.1, 2.2, 0.25]} p={[0.55, 1.1, 0]} c="#4A4844" rad={0.01} />
    <group position={[-0.5, 0, 0.05]} rotation={[0, -open * 1.4, 0]}>
      <Box s={[1.0, 2.08, 0.08]} p={[0.5, 1.04, 0]} c="#6A6660" rad={0.02} />
      <Box s={[0.9, 0.05, 0.02]} p={[0.5, 1.5, 0.05]} c="#5A5650" rad={0.01} />
      <Box s={[0.9, 0.05, 0.02]} p={[0.5, 0.55, 0.05]} c="#5A5650" rad={0.01} />
      <mesh position={[0.5, 1.05, 0.08]} material={mat(pal.metal)}><torusGeometry args={[0.13, 0.018, 8, 24]} /></mesh>
      <Box s={[0.26, 0.025, 0.025]} p={[0.5, 1.05, 0.08]} c={pal.metal} rad={0.008} />
      <Box s={[0.025, 0.26, 0.025]} p={[0.5, 1.05, 0.08]} c={pal.metal} rad={0.008} />
    </group>
  </G>
);

export const Stairs: React.FC<{ p?: V3; rotY?: number; steps?: number; w?: number; c?: string }> = ({ p, rotY, steps = 10, w = 1.1, c = "#5E5A55" }) => (
  <G p={p} rotY={rotY}>
    {Array.from({ length: steps }, (_, i) => (
      <Box key={i} s={[w, 0.18 * (i + 1), 0.28]} p={[0, (0.18 * (i + 1)) / 2, -i * 0.28]} c={c} rad={0.01} />
    ))}
  </G>
);

export const Barrel: React.FC<{ p?: V3; c?: string }> = ({ p, c = "#6A5A48" }) => (
  <G p={p}>
    <Cyl rt={0.28} rb={0.28} h={0.88} p={[0, 0.44, 0]} c={c} seg={20} />
    {[0.15, 0.73].map((y) => <Cyl key={y} rt={0.285} h={0.04} p={[0, y, 0]} c="#3E3A36" seg={20} />)}
  </G>
);

export const FirstAid: React.FC<{ p?: V3; rotY?: number }> = ({ p, rotY }) => (
  <G p={p} rotY={rotY}>
    <Box s={[0.36, 0.22, 0.14]} p={[0, 0.11, 0]} c="#B8AE9E" rad={0.03} />
    <mesh position={[0, 0.11, 0.071]} material={decal("#A84E3E")}><planeGeometry args={[0.04, 0.13]} /></mesh>
    <mesh position={[0, 0.11, 0.071]} material={decal("#A84E3E")}><planeGeometry args={[0.13, 0.04]} /></mesh>
    <Box s={[0.12, 0.03, 0.03]} p={[0, 0.235, 0]} c="#6E6A64" rad={0.01} />
  </G>
);

export const DuctTape: React.FC<{ p?: V3; rotX?: number }> = ({ p, rotX = Math.PI / 2 }) => (
  <group position={p} rotation={[rotX, 0, 0]}>
    <mesh material={mat("#8C8A86", 0.6)}><torusGeometry args={[0.05, 0.022, 10, 24]} /></mesh>
  </group>
);

/** plywood boarding over a window opening (local XY plane facing +z) */
export const BoardedWindow: React.FC<{ p?: V3; rotY?: number; w?: number; h?: number; t?: number; light?: string }> = ({ p, rotY, w = 1.0, h = 0.5, t = 0, light = "#C9A27A" }) => (
  <G p={p} rotY={rotY}>
    <mesh material={mat(light, 0.9, light, 0.35 + Math.sin(t * 0.7) * 0.03)}><planeGeometry args={[w, h]} /></mesh>
    {[-0.3, 0.05, 0.36].map((k, i) => (
      <Box key={i} s={[w + 0.14, 0.12, 0.025]} p={[0, k * h, 0.02]} r={[0, 0, (i - 1) * 0.08]} c={pick(["#7A6450", "#6E5A48", "#86705A"], i)} rad={0.008} />
    ))}
  </G>
);

/** wall calendar with tally marks: days counted in the shelter */
export const TallyBoard: React.FC<{ p?: V3; rotY?: number; days?: number }> = ({ p, rotY, days = 9 }) => {
  const tex = useLabelTex(256, 192, (g) => {
    g.fillStyle = "#C9BCA6"; g.fillRect(0, 0, 256, 192);
    g.strokeStyle = "#3A2E26"; g.lineWidth = 6; g.lineCap = "round";
    for (let d = 0; d < days; d++) {
      const grp = Math.floor(d / 5), k = d % 5;
      const x0 = 30 + grp * 80, y0 = 40 + Math.floor(grp / 3) * 70;
      g.beginPath();
      if (k < 4) { g.moveTo(x0 + k * 14, y0); g.lineTo(x0 + k * 14, y0 + 50); } else { g.moveTo(x0 - 8, y0 + 40); g.lineTo(x0 + 52, y0 + 10); }
      g.stroke();
    }
  }, `tally${days}`);
  return (
    <G p={p} rotY={rotY}>
      <mesh>
        <planeGeometry args={[0.5, 0.375]} />
        <meshStandardMaterial map={tex} roughness={0.9} polygonOffset polygonOffsetFactor={-2} polygonOffsetUnits={-4} />
      </mesh>
    </G>
  );
};

/** plastic sheeting taped over a vent / window: translucent with tape strips */
export const PlasticSheet: React.FC<{ p?: V3; rotY?: number; w?: number; h?: number }> = ({ p, rotY, w = 0.8, h = 0.6 }) => (
  <G p={p} rotY={rotY}>
    <mesh>
      <planeGeometry args={[w, h]} />
      <meshStandardMaterial color="#B8C4C2" transparent opacity={0.35} roughness={0.2} polygonOffset polygonOffsetFactor={-2} polygonOffsetUnits={-4} />
    </mesh>
    {[[0, h / 2], [0, -h / 2]].map(([x, y], i) => (
      <mesh key={i} position={[x, y, 0.004]} material={decal("#9A9690")}><planeGeometry args={[w + 0.05, 0.06]} /></mesh>
    ))}
    {[[-w / 2, 0], [w / 2, 0]].map(([x, y], i) => (
      <mesh key={`v${i}`} position={[x, y, 0.004]} material={decal("#9A9690")}><planeGeometry args={[0.06, h + 0.05]} /></mesh>
    ))}
  </G>
);

export const Pipes: React.FC<{ p?: V3; len?: number; n?: number; c?: string }> = ({ p, len = 6, n = 3, c = "#6A645C" }) => (
  <G p={p}>
    {Array.from({ length: n }, (_, i) => (
      <React.Fragment key={i}>
        <Cyl rt={0.045 + i * 0.012} h={len} p={[0, -i * 0.16, i * 0.05]} r={[0, 0, Math.PI / 2]} c={c} seg={12} />
        {Array.from({ length: Math.floor(len / 1.5) }, (_, k) => (
          <Box key={k} s={[0.04, 0.12, 0.1]} p={[-len / 2 + 0.75 + k * 1.5, -i * 0.16 + 0.06, i * 0.05]} c="#4A4640" rad={0.01} />
        ))}
      </React.Fragment>
    ))}
  </G>
);

export const BareBulb: React.FC<{ p?: V3; t?: number; flicker?: boolean; intensity?: number }> = ({ p = [0, 3, 0], t = 0, flicker = true, intensity = 3.2 }) => {
  const k = flicker ? (Math.sin(t * 37) > 0.97 ? 0.35 : 0.95 + Math.sin(t * 13) * 0.05) : 1;
  return (
    <G p={p}>
      <Cyl rt={0.006} h={0.5} p={[0, -0.25, 0]} c="#2A2826" seg={6} />
      <Cyl rt={0.03} h={0.06} p={[0, -0.53, 0]} c="#3A3632" seg={10} />
      <Ball r={0.06} p={[0, -0.6, 0]} c="#F2D29A" emissive="#F2C27A" ei={2.4 * k} flat={false} />
      <pointLight position={[0, -0.7, 0]} intensity={intensity * k} distance={8} color="#F2C28A" castShadow shadow-mapSize-width={1024} shadow-mapSize-height={1024} />
    </G>
  );
};

// ================================================================== OUTDOOR / AFTERMATH
export const Rubble: React.FC<{ p?: V3; n?: number; spread?: number; seed?: number; c?: string[] }> = ({ p, n = 14, spread = 1.6, seed = 1, c = ["#6E655C", "#5E5650", "#7A7066"] }) => (
  <G p={p}>
    {Array.from({ length: n }, (_, i) => {
      const s = 0.12 + random(`rb${seed}${i}`) * 0.35;
      return (
        <Box key={i} s={[s, s * 0.6, s * 0.8]} p={[(random(`rx${seed}${i}`) - 0.5) * spread, s * 0.28, (random(`rz${seed}${i}`) - 0.5) * spread]}
          r={[random(`r1${seed}${i}`) * 0.6, random(`r2${seed}${i}`) * 3, random(`r3${seed}${i}`) * 0.6]} c={pick(c, i)} rad={0.02} />
      );
    })}
  </G>
);

export const DeadTree: React.FC<{ p?: V3; s?: number; seed?: number; c?: string }> = ({ p, s = 1, seed = 1, c = "#3E342C" }) => (
  <group position={p} scale={s}>
    <Cyl rt={0.08} rb={0.14} h={2.6} p={[0, 1.3, 0]} c={c} seg={7} />
    {Array.from({ length: 5 }, (_, i) => {
      const a = random(`dt${seed}${i}`) * Math.PI * 2;
      const y = 1.4 + i * 0.28;
      return <Cyl key={i} rt={0.02} rb={0.045} h={0.9 - i * 0.1} p={[Math.cos(a) * 0.25, y + 0.3, Math.sin(a) * 0.25]} r={[Math.sin(a) * 0.9, 0, -Math.cos(a) * 0.9]} c={c} seg={5} />;
    })}
  </group>
);

export const TrashCan: React.FC<{ p?: V3; fallen?: boolean; rotY?: number }> = ({ p, fallen = false, rotY }) => (
  <G p={p} rotY={rotY}>
    <group rotation={[fallen ? Math.PI / 2 : 0, 0, 0]} position={[0, fallen ? 0.3 : 0, 0]}>
      <Cyl rt={0.3} rb={0.26} h={0.85} p={[0, 0.425, 0]} c="#5A5E58" seg={16} />
      <Cyl rt={0.32} h={0.05} p={[0, 0.87, 0]} c="#4A4E48" seg={16} />
    </group>
  </G>
);

export const Barricade: React.FC<{ p?: V3; rotY?: number }> = ({ p, rotY }) => (
  <G p={p} rotY={rotY}>
    {[-0.7, 0.7].map((x) => <Box key={x} s={[0.08, 1.0, 0.5]} p={[x, 0.5, 0]} r={[0, 0, 0]} c="#5A5650" rad={0.01} />)}
    {[0.8, 0.5].map((y, i) => (
      <group key={y}>
        <Box s={[1.7, 0.18, 0.05]} p={[0, y, 0]} c="#B89A6A" rad={0.01} />
        {Array.from({ length: 4 }, (_, k) => (
          <mesh key={k} position={[-0.6 + k * 0.4, y, 0.027 + i * 0.0]} rotation={[0, 0, 0.6]} material={decal("#5E3A2E")}><planeGeometry args={[0.1, 0.24]} /></mesh>
        ))}
      </group>
    ))}
  </G>
);

/** falling ash / dust: deterministic instanced flakes inside a box around `center` */
export const AshFall: React.FC<{ t: number; center?: V3; size?: V3; n?: number; c?: string; speed?: number }> = ({ t, center = [0, 4, 0], size = [30, 8, 40], n = 900, c = "#B8ADA0", speed = 0.35 }) => {
  const ref = React.useRef<THREE.InstancedMesh>(null);
  const seeds = useMemo(() => Array.from({ length: n }, (_, i) => [random(`ax${i}`), random(`ay${i}`), random(`az${i}`), random(`as${i}`)]), [n]);
  const m4 = useMemo(() => new THREE.Matrix4(), []);
  const q = useMemo(() => new THREE.Quaternion(), []);
  const e = useMemo(() => new THREE.Euler(), []);
  React.useLayoutEffect(() => {
    const mesh = ref.current;
    if (!mesh) return;
    seeds.forEach(([sx, sy, sz, ss], i) => {
      const y = (((sy * size[1] - t * speed * (0.6 + ss)) % size[1]) + size[1]) % size[1];
      const x = (sx - 0.5) * size[0] + Math.sin(t * 0.7 + i) * 0.3;
      const z = (sz - 0.5) * size[2] + Math.cos(t * 0.5 + i * 1.3) * 0.3;
      e.set(t * (1 + ss) + i, t * 0.8 + i * 2, 0);
      q.setFromEuler(e);
      const s = 0.025 + ss * 0.035;
      m4.compose(new THREE.Vector3(center[0] + x, center[1] - size[1] / 2 + y, center[2] + z), q, new THREE.Vector3(s, s, s));
      mesh.setMatrixAt(i, m4);
    });
    mesh.instanceMatrix.needsUpdate = true;
  });
  return (
    <instancedMesh ref={ref} args={[undefined as unknown as THREE.BufferGeometry, undefined as unknown as THREE.Material, n]} frustumCulled={false}>
      <planeGeometry args={[1, 1]} />
      <meshStandardMaterial color={c} roughness={1} side={THREE.DoubleSide} transparent opacity={0.85} depthWrite={false} />
    </instancedMesh>
  );
};

// ================================================================== FIRST-PERSON HANDS
export type HandItem = "none" | "radio" | "can" | "tape" | "bottle" | "lantern" | "geiger" | "mask";
/** two forearms + hands at the bottom of a first-person camera; `cam` = THREE camera to follow */
export const FPHands: React.FC<{ cam: THREE.Camera; item?: HandItem; t: number; skin?: string; sleeve?: string; gloves?: string; raise?: number }> = ({ cam, item = "none", t, skin = "#C49C80", sleeve = "#5E6B76", gloves, raise = 1 }) => {
  const bob = Math.sin(t * 3.2) * 0.008;
  const hand = gloves ?? skin;
  const pos = cam.position.clone();
  const quat = cam.quaternion.clone();
  const lift = (1 - raise) * -0.35;
  const arm = (side: 1 | -1) => (
    <group position={[side * 0.13, -0.17 + bob + lift, -0.5]} rotation={[0.35, side * -0.35, side * -0.25]}>
      <Cap r={0.042} len={0.34} p={[0, -0.11, 0.16]} r3={[Math.PI / 2 - 0.5, 0, 0]} c={sleeve} />
      <Ball r={0.048} p={[0, 0.0, -0.04]} s={[1.05, 0.75, 1.3]} c={hand} detail={2} flat={false} />
      {[-1, 0, 1].map((k) => <Cap key={k} r={0.012} len={0.035} p={[k * 0.022 - side * 0.01, 0.025, -0.085]} r3={[Math.PI / 2 - 0.3, 0, 0]} c={hand} />)}
    </group>
  );
  return (
    <group position={pos} quaternion={quat}>
      {arm(1)}
      {arm(-1)}
      <group position={[0, -0.16 + bob + lift, -0.58]} rotation={[0.3, 0, 0]} scale={0.8}>
        {item === "radio" ? <CrankRadio p={[0, -0.05, 0]} t={t} /> : null}
        {item === "can" ? <Can p={[0, -0.05, 0]} s={1.3} /> : null}
        {item === "bottle" ? <WaterBottle p={[0, -0.08, 0]} s={1.1} /> : null}
        {item === "tape" ? <DuctTape p={[0.02, 0.02, 0]} /> : null}
        {item === "lantern" ? <Lantern p={[0, -0.1, 0]} t={t} intensity={1.6} /> : null}
        {item === "geiger" ? <GeigerCounter p={[0, -0.04, 0]} t={t} /> : null}
        {item === "mask" ? <Respirator p={[0, 0, 0]} /> : null}
      </group>
    </group>
  );
};

export const GeigerCounter: React.FC<{ p?: V3; t?: number; level?: number }> = ({ p, t = 0, level = 0.3 }) => {
  const tex = useLabelTex(200, 120, (g) => {
    g.fillStyle = "#D9CCB4"; g.fillRect(0, 0, 200, 120);
    g.strokeStyle = "#3A2E26"; g.lineWidth = 4;
    g.beginPath(); g.arc(100, 110, 80, Math.PI * 1.1, Math.PI * 1.9); g.stroke();
    g.fillStyle = "#A84E3E"; g.fillRect(150, 30, 30, 10);
    g.fillStyle = "#3A2E26"; g.font = "bold 16px monospace"; g.fillText("µSv/h", 70, 100);
  }, "geiger");
  const needle = -0.9 + level * 1.8 + Math.sin(t * 13) * 0.05;
  return (
    <G p={p}>
      <Box s={[0.2, 0.12, 0.08]} p={[0, 0.06, 0]} c="#B89A5A" rad={0.02} />
      <mesh position={[0, 0.07, 0.041]}>
        <planeGeometry args={[0.15, 0.09]} />
        <meshStandardMaterial map={tex} roughness={0.8} polygonOffset polygonOffsetFactor={-2} polygonOffsetUnits={-4} />
      </mesh>
      <mesh position={[0, 0.035, 0.043]} rotation={[0, 0, needle]} material={decal("#2A2420")}><planeGeometry args={[0.004, 0.07]} /></mesh>
      <Cyl rt={0.018} h={0.2} p={[0.14, 0.06, 0]} r={[0, 0, Math.PI / 2]} c="#5A5650" seg={10} />
    </G>
  );
};

export const Respirator: React.FC<{ p?: V3 }> = ({ p }) => (
  <G p={p}>
    <Ball r={0.07} p={[0, 0, 0]} s={[1.2, 0.9, 0.7]} c="#3E3C3A" detail={2} flat={false} />
    {[-1, 1].map((s) => <Cyl key={s} rt={0.035} h={0.04} p={[s * 0.085, -0.02, 0.02]} r={[Math.PI / 2, 0, s * 0.4]} c="#6E6A64" seg={14} />)}
  </G>
);

// ================================================================== CAFE (coffee shop details)
/** steam puffs rising from a point (translucent, never a solid "snowman") */
export const Steam: React.FC<{ p?: V3; t?: number; n?: number; h?: number; size?: number }> = ({ p = [0, 0, 0], t = 0, n = 6, h = 0.45, size = 0.05 }) => (
  <group position={p}>
    {Array.from({ length: n }, (_, i) => {
      const k = (t * 0.35 + i / n) % 1;
      return (
        <mesh key={i} position={[Math.sin(i * 2.1 + t * 1.4) * 0.025 * k, k * h, Math.cos(i * 1.3 + t) * 0.02 * k]} scale={size * (0.4 + k * 1.6)}>
          <icosahedronGeometry args={[1, 2]} />
          <meshStandardMaterial color="#E3D8C8" transparent opacity={0.22 * (1 - k) * Math.min(1, k * 6)} roughness={1} depthWrite={false} />
        </mesh>
      );
    })}
  </group>
);

/** two-group espresso machine; its FRONT (group heads, gauges) faces +z — turn it toward the barista */
export const EspressoMachine: React.FC<{ p?: V3; rotY?: number; t?: number; steam?: boolean; c?: string }> = ({ p, rotY, t = 0, steam = true, c = "#B65A2E" }) => {
  const plate = useLabelTex(256, 64, (g) => {
    g.fillStyle = "#2A2420"; g.fillRect(0, 0, 256, 64);
    g.fillStyle = "#E8D9C2"; g.font = "bold 34px Inter, Arial"; g.textAlign = "center"; g.fillText("ESPRESSO", 128, 44);
  }, "espresso-plate");
  return (
    <G p={p} rotY={rotY}>
      {/* body, top rail, cup warmer */}
      <Box s={[0.72, 0.42, 0.5]} p={[0, 0.25, 0]} c={c} rad={0.04} />
      <Box s={[0.76, 0.04, 0.54]} p={[0, 0.48, 0]} c="#9A958C" rad={0.015} />
      <Box s={[0.66, 0.035, 0.44]} p={[0, 0.03, 0.02]} c="#5A5650" rad={0.01} />
      {[-0.22, -0.07, 0.08, 0.23].map((x, i) => (
        <group key={i} position={[x, 0.5, -0.02]}>
          <Cyl rt={0.042} rb={0.032} h={0.08} p={[0, 0.04, 0]} c={i % 2 ? "#E6DCCD" : "#D9CCB8"} seg={14} />
          <Cyl rt={0.042} rb={0.032} h={0.08} p={[0, 0.12, 0]} c={i % 2 ? "#D9CCB8" : "#E6DCCD"} seg={14} />
        </group>
      ))}
      {/* front: steel panel, gauges, logo plate */}
      <Box s={[0.6, 0.16, 0.02]} p={[0, 0.36, 0.25]} c="#A8A39A" rad={0.01} />
      {[-0.14, 0.14].map((x) => (
        <mesh key={x} position={[x, 0.36, 0.262]} material={decal("#F1E7D8")}>
          <circleGeometry args={[0.038, 24]} />
        </mesh>
      ))}
      {[-0.14, 0.14].map((x) => (
        <mesh key={`n${x}`} position={[x, 0.36, 0.264]} rotation={[0, 0, -0.6 + Math.sin(t * 0.7 + x * 9) * 0.06]} material={decal("#2A2420")}>
          <planeGeometry args={[0.004, 0.03]} />
        </mesh>
      ))}
      <mesh position={[0, 0.17, 0.252]}>
        <planeGeometry args={[0.3, 0.075]} />
        <meshStandardMaterial map={plate} roughness={0.7} polygonOffset polygonOffsetFactor={-2} polygonOffsetUnits={-4} />
      </mesh>
      {/* group heads + portafilters with handles */}
      {[-0.17, 0.17].map((x) => (
        <group key={x} position={[x, 0.2, 0.27]}>
          <Cyl rt={0.045} h={0.05} p={[0, 0, 0]} c="#C9C4BA" seg={18} />
          <Cyl rt={0.04} h={0.035} p={[0, -0.045, 0.01]} c="#8E8980" seg={18} />
          <Cap r={0.014} len={0.13} p={[0, -0.045, 0.1]} r3={[Math.PI / 2, 0, 0]} c="#2A2420" />
          {/* cup under the spout */}
          <Cyl rt={0.032} rb={0.026} h={0.06} p={[0, -0.135, 0.01]} c="#F0E6D8" seg={16} />
        </group>
      ))}
      {/* steam wand */}
      <Cyl rt={0.008} h={0.22} p={[0.33, 0.19, 0.27]} r={[0.25, 0, 0]} c="#C9C4BA" seg={8} />
      {steam ? <Steam p={[0.33, 0.1, 0.3]} t={t} n={6} h={0.4} size={0.035} /> : null}
      {[-0.17, 0.17].map((x, i) => (steam ? <Steam key={x} p={[x, 0.1, 0.28]} t={t + i * 1.7} n={4} h={0.22} size={0.02} /> : null))}
    </G>
  );
};

/** chalk menu board in a wooden frame (hang on a wall: front faces +z) */
export const MenuBoard: React.FC<{ p?: V3; rotY?: number; w?: number; h?: number; title?: string; items?: [string, string][] }> = ({
  p, rotY, w = 1.1, h = 0.8, title = "МЕНЮ",
  items = [["Эспрессо", "150"], ["Капучино", "220"], ["Латте", "240"], ["Раф", "260"], ["Какао", "200"]],
}) => {
  const tex = useLabelTex(660, 480, (g) => {
    g.fillStyle = "#2E3330"; g.fillRect(0, 0, 660, 480);
    for (let i = 0; i < 400; i++) { g.fillStyle = `rgba(230,224,210,${0.015 + (i % 7) * 0.003})`; g.fillRect((i * 97) % 660, (i * 53) % 480, 3, 2); }
    g.fillStyle = "#EDE3D2"; g.textAlign = "center"; g.font = "italic 700 58px Georgia, serif"; g.fillText(title, 330, 78);
    g.strokeStyle = "rgba(237,227,210,0.55)"; g.lineWidth = 2; g.beginPath(); g.moveTo(200, 98); g.lineTo(460, 98); g.stroke();
    g.font = "600 34px Inter, Arial"; g.textAlign = "left";
    items.forEach(([n, v], i) => {
      const y = 158 + i * 62;
      g.fillStyle = "#E6DCCB"; g.fillText(n, 60, y);
      g.fillStyle = "#E3A06A"; g.textAlign = "right"; g.fillText(v, 600, y); g.textAlign = "left";
      g.fillStyle = "rgba(230,220,200,0.25)"; for (let x = 60 + g.measureText(n).width + 12; x < 540; x += 14) g.fillRect(x, y - 8, 4, 3);
    });
  }, `menu-${title}-${items.map((i) => i.join(":")).join("|")}`);
  return (
    <G p={p} rotY={rotY}>
      <Box s={[w + 0.08, h + 0.08, 0.04]} p={[0, 0, 0.02]} c="#6E5442" rad={0.01} />
      <mesh position={[0, 0, 0.042]}>
        <planeGeometry args={[w, h]} />
        <meshStandardMaterial map={tex} roughness={0.95} polygonOffset polygonOffsetFactor={-2} polygonOffsetUnits={-4} />
      </mesh>
    </G>
  );
};

/** glass pastry case with croissants and buns (sits on a counter) */
export const PastryCase: React.FC<{ p?: V3; rotY?: number; w?: number }> = ({ p, rotY, w = 0.7 }) => (
  <G p={p} rotY={rotY}>
    <Box s={[w, 0.03, 0.42]} p={[0, 0.015, 0]} c="#6E5442" rad={0.008} />
    <Box s={[w - 0.04, 0.012, 0.38]} p={[0, 0.17, 0]} c="#B8AE9E" rad={0.004} />
    {/* pastries: lower shelf croissants, upper shelf buns */}
    {Array.from({ length: Math.max(2, Math.round(w / 0.16)) }, (_, i) => {
      const n = Math.max(2, Math.round(w / 0.16));
      const x = -w / 2 + 0.1 + (i * (w - 0.2)) / (n - 1);
      return (
        <React.Fragment key={i}>
          <Cap r={0.03} len={0.07} p={[x, 0.06, 0.04]} r3={[0, 0.4, Math.PI / 2 - 0.25]} c="#C98A4E" />
          <Ball r={0.04} p={[x, 0.21, -0.03]} s={[1, 0.7, 1]} c={i % 2 ? "#B9784A" : "#D9A066"} detail={1} flat={false} />
        </React.Fragment>
      );
    })}
    <mesh position={[0, 0.17, 0]}>
      <boxGeometry args={[w, 0.34, 0.42]} />
      <meshPhysicalMaterial color="#DDE6E4" transparent opacity={0.16} roughness={0.05} metalness={0} depthWrite={false} />
    </mesh>
  </G>
);
