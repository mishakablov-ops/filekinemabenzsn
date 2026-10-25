import React, { useMemo } from "react";
import { AbsoluteFill, random } from "remotion";
import * as THREE from "three";
import { useBlockTime, useReel } from "../core/context";
import { CameraClipQA, CollisionQA } from "./collide";
import { camAt, makeCamera, project, Stage3D, type CamKey, type V3 } from "./core";
import { Bench, Box, Building, Car, PALETTES, Person, pick, StreetLamp, TrafficLight, Tree, type KitPalette, type PersonLook, type Pose } from "./kit";
import { AshFall, Barricade, DeadTree, Rubble, TrashCan } from "./kit2";

// after the fallout: dusty, desaturated, no lights (warm greys, never blue)
const ASH: KitPalette = {
  ...PALETTES.evening,
  bg: "#3A322C", facades: ["#5A534D", "#4E4944", "#625A52", "#56504A", "#4A4642"], road: "#363230", walk: "#4C4640", curb: "#5A544E", line: "#7E7466",
  winDark: "#1E1C1B", winLit: "#1E1C1B", cars: ["#6A645C", "#5E5852", "#77706A", "#5A5650", "#6E6058"], tree: ["#4A4238", "#433C33"], trunk: "#3A322B", lamp: "#8A8070",
};

const ROAD = 3.6; // half width
const WALK = 3.0;
const Z_FAR = -90;
const Z_NEAR = 24;

const CAMS: Record<string, CamKey[]> = {
  eye: [
    { t: 0, pos: [1.6, 1.65, 16], target: [0.4, 2.6, -30], fov: 46 },
    { t: 8, pos: [1.6, 1.65, 12.5], target: [0.4, 2.6, -30], fov: 46 },
  ],
  high: [
    { t: 0, pos: [0, 11, 22], target: [0, 1, -10], fov: 40 },
    { t: 8, pos: [0, 10, 18], target: [0, 1, -10], fov: 40 },
  ],
  follow: [
    { t: 0, pos: [4.6, 1.7, 18], target: [4.2, 1.9, -20], fov: 44 },
    { t: 8, pos: [4.6, 1.7, 6], target: [4.2, 1.9, -30], fov: 44 },
  ],
  crossing: [
    { t: 0, pos: [13, 2.2, 3], target: [-6, 2.5, -1], fov: 42 },
    { t: 8, pos: [12, 2.4, 1.5], target: [-6, 2.5, -1], fov: 42 },
  ],
  top: [
    { t: 0, pos: [0.01, 46, 2], target: [0, 0, -2], fov: 32 },
    { t: 8, pos: [0.01, 40, 2], target: [0, 0, -2], fov: 32 },
  ],
  drone: [
    { t: 0, pos: [-5, 24, 30], target: [0, 0, -14], fov: 36 },
    { t: 8, pos: [5, 20, 26], target: [0, 0, -14], fov: 36 },
  ],
};

type Walker = { pose?: Pose; x?: number; z?: number; speed?: number; dir?: 1 | -1; seed?: number; look?: PersonLook; label?: string };

export const Street3D: React.FC<{
  time?: "day" | "evening" | "night"; cam?: string | CamKey[]; seed?: string; cars?: number; people?: number; walkers?: Walker[]; crosswalk?: boolean;
  traffic?: "red" | "green"; highlight?: { x: number; z: number; label?: string; at?: unknown };
  /** empty, dusty street after a disaster: parked abandoned cars, dead trees, rubble, falling ash, no lights */
  abandoned?: boolean; ash?: boolean;
}> = ({ time = "evening", cam = "eye", seed = "st", cars = 6, people = 14, walkers, crosswalk = true, traffic = "green", highlight, abandoned = false, ash }) => {
  const { f, fps, at } = useBlockTime();
  const { qa } = useReel();
  const t = f / fps;
  const pal = abandoned ? ASH : time === "night" ? PALETTES.night : time === "evening" ? PALETTES.evening : PALETTES.dusk;
  const lit = abandoned ? 0 : time === "night" ? 0.45 : time === "evening" ? 0.3 : 0.06;
  const lampsOn = !abandoned && time !== "day";

  const blds = useMemo(() => {
    const out: { side: 1 | -1; z: number; w: number; h: number; d: number; seed: number; awning?: string }[] = [];
    for (const side of [-1, 1] as const) {
      let z = Z_NEAR;
      let i = 0;
      while (z > Z_FAR) {
        const w = 5 + random(`${seed}bw${side}${i}`) * 5;
        const h = 7 + random(`${seed}bh${side}${i}`) * 11;
        out.push({ side, z: z - w / 2, w, h, d: 7, seed: i * 7 + (side > 0 ? 3 : 0), awning: random(`${seed}aw${side}${i}`) < 0.4 ? pick(pal.fabric, i) : undefined });
        z -= w + 0.15;
        i++;
      }
    }
    return out;
  }, [seed, time]);

  // Sidewalk lanes (|x|): lamp poles at ROAD+0.45, tree trunks at ROAD+1.6, benches at ROAD+2.7.
  // Lane A (toward camera) runs between poles and trunks, lane B (away) between trunks and benches.
  // One speed per lane + even spacing => nobody walks through anybody or anything.
  const LANE_A = ROAD + 1.0;
  const LANE_B = ROAD + 2.15;
  const ppl: Walker[] =
    walkers ?? (abandoned ? [] : undefined) ??
    (() => {
      const out: Walker[] = [];
      const movers = Math.round(people * 0.8);
      const perLane = Math.max(1, Math.ceil(movers / 4));
      const L = Z_NEAR - Z_FAR;
      let k = 0;
      for (const side of [-1, 1] as const)
        for (const lane of [LANE_A, LANE_B]) {
          const dir: 1 | -1 = lane === LANE_A ? 1 : -1;
          for (let j = 0; j < perLane && k < movers; j++, k++)
            out.push({ x: side * lane, z: Z_NEAR - (j + random(`${seed}pz${k}`) * 0.4) * (L / perLane), speed: lane === LANE_A ? 1.25 : 1.4, dir, seed: k });
        }
      // standing people: on the tree line, midway between trees, never on a lane
      for (let j = 0; k < people; j++, k++) {
        const side = j % 2 ? 1 : -1;
        const z = side < 0 ? 21 - 12 * (j + 1) : 15 - 12 * (j + 1);
        out.push({ x: side * (ROAD + 1.6), z, speed: 0, seed: k, pose: j % 3 === 0 ? "phone" : "stand" });
      }
      return out;
    })();

  const keys = Array.isArray(cam) ? cam : CAMS[cam] ?? CAMS.eye;
  const c = camAt(keys, t);
  const camera = makeCamera(c);
  const wrap = (z: number) => {
    const L = Z_NEAR - Z_FAR;
    return ((((z - Z_FAR) % L) + L) % L) + Z_FAR;
  };
  return (
    <AbsoluteFill style={{ background: pal.bg }}>
      <Stage3D cam={c} lights={abandoned ? "sunset" : time === "night" ? "night" : time === "evening" ? "sunset" : "soft"} env={abandoned ? 0.45 : time === "night" ? 0.2 : 0.5}
        fog={abandoned ? { color: pal.bg, near: 10, far: 72 } : { color: pal.bg, near: 30, far: 105 }} exposure={abandoned ? 1.08 : 1}>
        {/* road, sidewalks, curbs */}
        <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0, (Z_NEAR + Z_FAR) / 2]} receiveShadow>
          <planeGeometry args={[ROAD * 2, Z_NEAR - Z_FAR + 40]} />
          <meshStandardMaterial color={pal.road} roughness={0.95} />
        </mesh>
        {[-1, 1].map((s) => (
          <React.Fragment key={s}>
            <Box s={[WALK, 0.16, Z_NEAR - Z_FAR + 40]} p={[s * (ROAD + WALK / 2), 0.08, (Z_NEAR + Z_FAR) / 2]} c={pal.walk} rad={0.01} />
            <Box s={[0.2, 0.18, Z_NEAR - Z_FAR + 40]} p={[s * (ROAD + 0.1), 0.09, (Z_NEAR + Z_FAR) / 2]} c={pal.curb} rad={0.02} />
          </React.Fragment>
        ))}
        {/* lane dashes */}
        {Array.from({ length: 40 }, (_, i) => (
          <mesh key={i} rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.005, Z_NEAR - i * 3]}>
            <planeGeometry args={[0.14, 1.5]} />
            <meshStandardMaterial color={pal.line} roughness={0.8} />
          </mesh>
        ))}
        {crosswalk
          ? Array.from({ length: 9 }, (_, i) => (
              <mesh key={i} rotation={[-Math.PI / 2, 0, 0]} position={[-ROAD + 0.4 + i * 0.85, 0.006, 2]}>
                <planeGeometry args={[0.5, 3]} />
                <meshStandardMaterial color={pal.line} roughness={0.8} />
              </mesh>
            ))
          : null}
        {crosswalk ? (
          <>
            <TrafficLight p={[ROAD + 0.5, 0.16, 4]} rotY={Math.PI} state={abandoned ? "off" : traffic} pal={pal} />
            <TrafficLight p={[-ROAD - 0.5, 0.16, -0.2]} state={abandoned ? "off" : traffic} pal={pal} />
          </>
        ) : null}
        {/* buildings */}
        {blds.map((b, i) => (
          <Building key={i} p={[b.side * (ROAD + WALK + b.d / 2), 0, b.z]} w={b.d} d={b.w} h={b.h} face={b.side > 0 ? -1 : 1} pal={pal} lit={lit} seed={b.seed} awning={b.awning} />
        ))}
        {/* street furniture */}
        {Array.from({ length: 9 }, (_, i) => {
          const z = Z_NEAR - 6 - i * 12;
          return (
            <React.Fragment key={i}>
              <StreetLamp p={[-(ROAD + 0.45), 0.16, z]} rotY={Math.PI / 2} on={lampsOn} pal={pal} />
              <StreetLamp p={[ROAD + 0.45, 0.16, z - 6]} rotY={-Math.PI / 2} on={lampsOn} pal={pal} />
              {abandoned ? (
                <>
                  <DeadTree p={[-(ROAD + 1.6), 0.16, z - 3]} s={0.9 + random(`${seed}tr${i}`) * 0.3} seed={i} />
                  <DeadTree p={[ROAD + 1.6, 0.16, z - 9]} s={0.9 + random(`${seed}tl${i}`) * 0.3} seed={i + 20} />
                </>
              ) : (
                <>
                  <Tree p={[-(ROAD + 1.6), 0.16, z - 3]} s={0.85 + random(`${seed}tr${i}`) * 0.3} pal={pal} />
                  <Tree p={[ROAD + 1.6, 0.16, z - 9]} s={0.85 + random(`${seed}tl${i}`) * 0.3} pal={pal} />
                </>
              )}
              {i % 3 === 1 ? <Bench p={[ROAD + 2.72, 0.16, z - 2]} rotY={-Math.PI / 2} pal={pal} /> : null}
            </React.Fragment>
          );
        })}
        {abandoned ? <Aftermath seed={seed} pal={pal} t={t} ash={ash !== false} /> : null}
        {/* moving cars: lane x=-1.8 toward camera (+z), lane x=+1.8 away (-z) */}
        {(abandoned ? [] : Array.from({ length: cars })).map((_, i) => {
          // one speed per lane + even spacing: cars never drive through each other
          const dir = i % 2 ? -1 : 1;
          const laneIdx = Math.floor(i / 2);
          const perLane = Math.max(1, Math.ceil(cars / 2));
          const stopAtLight = traffic === "red" && dir === 1;
          const v = dir === 1 ? 8.5 : 7.5;
          const z0 = Z_NEAR - (laneIdx + random(`${seed}cz${i}`) * 0.3) * ((Z_NEAR - Z_FAR) / perLane);
          const z = stopAtLight ? -3.5 - laneIdx * 5.6 : wrap(z0 + dir * v * t);
          return (
            <group key={i} userData={{ qa: "solid", id: `car${i}` }}>
              <Car p={[dir === 1 ? -1.8 : 1.8, 0, z]} rotY={dir === 1 ? 0 : Math.PI} c={pick(pal.cars, i * 3 + 1)} lights={time !== "day"} pal={pal} />
            </group>
          );
        })}
        {/* pedestrians */}
        {ppl.map((p, i) => {
          const v = p.speed ?? 1.2;
          const dir = p.dir ?? 1;
          const z = v ? wrap((p.z ?? 0) + dir * v * t) : p.z ?? 0;
          const pose: Pose = p.pose ?? (v ? "walk" : i % 3 === 0 ? "phone" : "stand");
          return (
            <group key={i} userData={{ qa: "person", pose, id: `walker${i}` }}>
              <Person pos={[p.x ?? ROAD + 1.5, 0.16, z]} rotY={v ? (dir === 1 ? 0 : Math.PI) : (i % 2 ? 1.2 : -2)} pose={pose} t={t * (v ? v / 1.2 : 1) + i * 0.31} seed={p.seed ?? i} look={p.look} pal={pal} />
            </group>
          );
        })}
        <CollisionQA on={qa} />
        <CameraClipQA on={qa} />
      </Stage3D>
      {highlight
        ? (() => {
            const s = highlight.at !== undefined ? at(highlight.at) : 0;
            if (f < s) return null;
            const [x, y] = project(camera, new THREE.Vector3(highlight.x, 0.2, highlight.z));
            const ring = ((f - s) % 45) / 45;
            return (
              <div style={{ position: "absolute", left: x, top: y }}>
                <div style={{ position: "absolute", left: -60 * (0.5 + ring), top: -24 * (0.5 + ring), width: 120 * (0.5 + ring), height: 48 * (0.5 + ring), borderRadius: "50%", border: "4px solid #E08A55", opacity: 1 - ring }} />
                {highlight.label ? <div style={{ position: "absolute", left: -260, width: 520, top: 40, textAlign: "center" }}><span style={{ font: "600 30px 'JetBrains Mono'", color: "#EDE3D4", background: "rgba(30,26,22,0.8)", padding: "8px 16px", borderRadius: 10 }}>{highlight.label}</span></div> : null}
              </div>
            );
          })()
        : null}
    </AbsoluteFill>
  );
};

/** abandoned cars (doors open, skewed, never overlapping), rubble, trash, a barricade, ash */
const Aftermath: React.FC<{ seed: string; pal: KitPalette; t: number; ash: boolean }> = ({ seed, pal, t, ash }) => {
  const parked = [
    { x: -1.9, z: 12, r: 0.25 }, { x: 2.1, z: 3.5, r: Math.PI - 0.35 }, { x: -2.2, z: -9, r: -0.4 }, { x: 1.6, z: -21, r: Math.PI + 0.2 },
    { x: -1.4, z: -34, r: 0.6 }, { x: 2.0, z: -47, r: Math.PI - 0.15 },
  ];
  return (
    <>
      {parked.map((c, i) => (
        <group key={i} userData={{ qa: "solid", id: `wreck${i}` }}>
          <group position={[c.x, 0, c.z]} rotation={[0, c.r, (i % 2 ? 1 : -1) * 0.025]}>
            <Car c={pick(pal.cars, i * 2 + 1)} pal={pal} />
            {/* open driver door */}
            <group position={[0.91, 0.62, 0.55]} rotation={[0, 1.0, 0]}>
              <Box s={[0.05, 0.55, 0.95]} p={[0, 0, -0.45]} c={pick(pal.cars, i * 2 + 1)} rad={0.03} />
            </group>
          </group>
        </group>
      ))}
      {[
        { p: [-2.4, 0, 7] as V3, s: 3 }, { p: [0.4, 0, -4.5] as V3, s: 4 }, { p: [2.6, 0, -15] as V3, s: 5 }, { p: [-0.8, 0, -27] as V3, s: 6 },
        { p: [2.4, 0, -40] as V3, s: 7 }, { p: [-2.6, 0, -52] as V3, s: 8 },
      ].map((r, i) => (
        <group key={i} userData={{ qa: "solid", id: `rubble${i}` }}>
          <Rubble p={r.p} seed={r.s} n={12} spread={1.6} />
        </group>
      ))}
      <group userData={{ qa: "solid", id: "trash1" }}><TrashCan p={[2.9, 0, 9]} fallen rotY={0.8} /></group>
      <group userData={{ qa: "solid", id: "trash2" }}><TrashCan p={[-2.9, 0, -14]} fallen rotY={-2.2} /></group>
      <group userData={{ qa: "solid", id: "barricade" }}><Barricade p={[0.4, 0, -0.6]} rotY={0.15} /></group>
      {/* scattered paper */}
      {Array.from({ length: 26 }, (_, i) => (
        <mesh key={i} position={[(random(`${seed}px${i}`) - 0.5) * 9, 0.01 + (i % 3) * 0.002, 16 - random(`${seed}pz${i}`) * 60]} rotation={[-Math.PI / 2, 0, random(`${seed}pr${i}`) * 3]}>
          <planeGeometry args={[0.22, 0.3]} />
          <meshStandardMaterial color="#8E867A" roughness={1} polygonOffset polygonOffsetFactor={-2} polygonOffsetUnits={-4} />
        </mesh>
      ))}
      {ash ? <AshFall t={t} center={[0, 4.5, 4]} size={[16, 9, 30]} n={700} c="#A89E92" /> : null}
    </>
  );
};

export type { V3 };
