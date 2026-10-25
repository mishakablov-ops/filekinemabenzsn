import React from "react";
import { AbsoluteFill } from "remotion";
import * as THREE from "three";
import { useBlockTime, useReel, useTheme } from "../core/context";
import { CollisionQA } from "./collide";
import { E, clamp01 } from "../core/motion";
import { camAt, makeCamera, project, Stage3D, type CamKey, type LightRig, type V3 } from "./core";
import {
  Bed, Bench, Box, Building, Car, Chair, Counter, Desk, Frame, Lamp, Monitor, Mug, PALETTES, PendantLamp, Person, Plant, Rug, Shelf, SmallLaptop, Sofa,
  Stool, StreetLamp, Table, TrafficLight, Tree, TV, type KitPalette, type Pose, type PersonLook,
} from "./kit";

/**
 * Scene3D — build any low-poly scene from a list of kit objects.
 * objects: [{ type, pos:[x,y,z], rotY, at, ...type props }]
 * types: person (pose, look, seed, walkTo, walkDur) | desk | chair | monitor | laptop | sofa | bed | table | shelf | plant | lamp | rug |
 *        frame | mug | pendant | counter | stool | tv | car (drive:[dx,dz], dur) | tree | streetlamp | bench | traffic | building | box (size,color)
 * labels: [{ text, pos:[x,y,z], at }] -> HTML labels pinned to 3D points
 */
type Obj = { type: string; pos?: V3; rotY?: number; at?: unknown; [k: string]: unknown };

export const Scene3D: React.FC<{
  objects: Obj[]; cam?: CamKey[]; look?: keyof typeof PALETTES; ground?: { size?: number; color?: string } | false; lights?: LightRig; env?: number; pop?: boolean;
  labels?: { text: string; pos: V3; at?: unknown }[]; fog?: boolean;
}> = ({ objects, cam, look, ground = { size: 14 }, lights, env = 0.5, pop = true, labels = [], fog = false }) => {
  const { f, fps, at } = useBlockTime();
  const th = useTheme();
  const { qa } = useReel();
  const t = f / fps;
  const pal: KitPalette = PALETTES[look ?? (th.dark ? "dusk" : "sand")] ?? PALETTES.dusk;
  const keys: CamKey[] = cam ?? [
    { t: 0, pos: [9, 7.5, 11], target: [0, 0.9, 0], fov: 30 },
    { t: 8, pos: [7.8, 6.8, 12.2], target: [0, 0.9, 0], fov: 30 },
  ];
  const c = camAt(keys, t);
  const camera = makeCamera(c);
  const render = (o: Obj, i: number) => {
    const s = o.at !== undefined ? at(o.at) / fps : 0;
    if (t < s) return null;
    const k = pop ? E.outExpo(clamp01((t - s) / 0.5)) : 1;
    let pos = o.pos ?? [0, 0, 0];
    const rotY = o.rotY ?? 0;
    const common = { pal };
    let node: React.ReactNode = null;
    switch (o.type) {
      case "person": {
        let pose = (o.pose as Pose) ?? "stand";
        let ry = rotY;
        if (o.walkTo) {
          const to = o.walkTo as V3;
          const q = clamp01((t - s) / ((o.walkDur as number) ?? 3));
          pos = [pos[0] + (to[0] - pos[0]) * q, pos[1], pos[2] + (to[2] - pos[2]) * q];
          if (q < 1) {
            pose = "walk";
            ry = Math.atan2(to[0] - (o.pos ?? [0, 0, 0])[0], to[2] - (o.pos ?? [0, 0, 0])[2]);
          }
        }
        node = <Person pos={[0, 0, 0]} rotY={ry} pose={pose} t={t + i * 0.37} seed={(o.seed as number) ?? i} look={o.look as PersonLook} pal={pal} scale={(o.scale as number) ?? 1} />;
        break;
      }
      case "desk": node = <Desk w={(o.w as number) ?? 1.5} {...common} />; break;
      case "chair": node = <Chair {...common} c={o.color as string} />; break;
      case "monitor": node = <Monitor {...common} />; break;
      case "laptop": node = <SmallLaptop {...common} />; break;
      case "sofa": node = <Sofa {...common} w={(o.w as number) ?? 2} c={o.color as string} />; break;
      case "bed": node = <Bed {...common} />; break;
      case "table": node = <Table {...common} r={(o.r as number) ?? 0.45} h={(o.h as number) ?? 0.74} round={o.round !== false} />; break;
      case "shelf": node = <Shelf {...common} w={(o.w as number) ?? 1.2} rows={(o.rows as number) ?? 4} seed={(o.seed as number) ?? 1} />; break;
      case "plant": node = <Plant {...common} kind={(o.kind as "bush") ?? "bush"} s={(o.s as number) ?? 1} />; break;
      case "lamp": node = <Lamp {...common} floor={o.floor !== false} />; break;
      case "rug": node = <Rug w={(o.w as number) ?? 2.2} d={(o.d as number) ?? 1.6} c={(o.color as string) ?? pal.rug} round={!!o.round} />; break;
      case "frame": node = <Frame w={(o.w as number) ?? 0.6} h={(o.h as number) ?? 0.8} art={(o.color as string) ?? pal.fabric[1]} />; break;
      case "mug": node = <Mug />; break;
      case "pendant": node = <PendantLamp {...common} p={[0, 0, 0]} />; break;
      case "counter": node = <Counter {...common} w={(o.w as number) ?? 2.4} />; break;
      case "stool": node = <Stool {...common} />; break;
      case "tv": node = <TV {...common} />; break;
      case "car": {
        if (o.drive) {
          const d = o.drive as [number, number];
          const q = E.inOut(clamp01((t - s) / ((o.dur as number) ?? 3)));
          pos = [pos[0] + d[0] * q, pos[1], pos[2] + d[1] * q];
        }
        node = <Car {...common} c={o.color as string} lights={!!o.lights} />;
        break;
      }
      case "tree": node = <Tree {...common} s={(o.s as number) ?? 1} kind={(o.kind as "round") ?? "round"} />; break;
      case "streetlamp": node = <StreetLamp {...common} on={!!o.on} />; break;
      case "bench": node = <Bench {...common} />; break;
      case "traffic": node = <TrafficLight {...common} state={(o.state as "red") ?? "green"} />; break;
      case "building": node = <Building {...common} w={(o.w as number) ?? 6} h={(o.h as number) ?? 9} d={(o.d as number) ?? 6} face={(o.face as 1) ?? 1} lit={(o.lit as number) ?? 0.25} seed={(o.seed as number) ?? i} />; break;
      case "box": node = <Box s={(o.size as V3) ?? [1, 1, 1]} p={[0, ((o.size as V3) ?? [1, 1, 1])[1] / 2, 0]} c={(o.color as string) ?? pal.wood} rad={0.04} />; break;
      default:
        return null;
    }
    const seat = ["chair", "sofa", "bed", "stool", "bench"].includes(o.type);
    const flat = ["rug", "frame", "pendant", "mug", "lamp"].includes(o.type);
    const qaTag = o.type === "person" ? { qa: "person", pose: o.pose ?? "stand", id: `person${i}` } : flat ? {} : { qa: "solid", seat, id: `${o.type}${i}` };
    return (
      <group key={i} userData={qaTag} position={pos} rotation={[0, o.type === "person" ? 0 : rotY, 0]} scale={[1, k, 1]}>
        {node}
      </group>
    );
  };
  return (
    <AbsoluteFill style={{ background: pal.bg }}>
      <Stage3D cam={c} lights={lights ?? (th.dark ? "soft" : "studio")} env={env} fog={fog ? { color: pal.bg, near: 18, far: 60 } : undefined}>
        {ground ? (
          <mesh rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
            <planeGeometry args={[ground.size ?? 14, ground.size ?? 14]} />
            <meshStandardMaterial color={ground.color ?? pal.floor} roughness={0.95} />
          </mesh>
        ) : null}
        {objects.map(render)}
        <CollisionQA on={qa} />
      </Stage3D>
      {labels.map((l, i) => {
        const s = l.at !== undefined ? at(l.at) : 0;
        if (f < s) return null;
        const [x, y] = project(camera, new THREE.Vector3(...l.pos));
        const a = E.out(clamp01((f - s) / 12));
        return (
          <div key={i} style={{ position: "absolute", left: x - 300, top: y - 30, width: 600, textAlign: "center", opacity: a, transform: `translateY(${(1 - a) * 12}px)` }}>
            <span style={{ font: `700 34px ${th.fontUi}`, color: th.cardInk, background: th.card, padding: "10px 20px", borderRadius: 14, boxShadow: th.cardShadow, whiteSpace: "nowrap" }}>{l.text}</span>
          </div>
        );
      })}
    </AbsoluteFill>
  );
};
