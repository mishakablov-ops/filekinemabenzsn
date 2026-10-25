import React from "react";
import { AbsoluteFill } from "remotion";
import * as THREE from "three";
import { useBlockTime, useReel, useTheme } from "../core/context";
import { CameraClipQA, CollisionQA } from "./collide";
import { E, clamp01 } from "../core/motion";
import { camAt, FPV_FOV, headCam, makeCamera, Stage3D, type CamKey, type V3 } from "./core";
import { Nested, type NestedBlock } from "./devices";
import {
  Bed, Box, Cap, Chair, Counter, Desk, Frame, Lamp, MONITOR_SCREEN, Monitor, Mug, PALETTES, PendantLamp, Person, Plant, Rug, Shelf, SmallLaptop, Sofa, Stool,
  Table, TV, TV_SCREEN, decal, type KitPalette, type Pose, type PersonLook, type SuitParts,
} from "./kit";
import {
  Armchair, BareBulb, Barrel, BoardedWindow, BookStack, Bucket, Candle, CrankRadio, Curtain, DiningTable, Fireplace, FirstAid, FPHands, Fridge, KitchenCounter,
  Lantern, LogWall, Mattress, Pipes, PlasticSheet, Sandbags, SideTable, SteelDoor, Stove, SupplyRack, TallyBoard, WallClock, WaterHeater, type HandItem,
  EspressoMachine, MenuBoard, PastryCase,
} from "./kit2";
import { project } from "./core";

/** suitAt: put the protective suit on piece by piece — { coat: "@Дождевик", gloves: "@перчатки", … } (anchors or seconds) */
export type PersonSpec = { pose?: Pose; pos?: V3; rotY?: number; look?: PersonLook; seed?: number; at?: unknown; walkTo?: V3; walkDur?: number; suitAt?: Partial<Record<keyof SuitParts, unknown>> };

const ROOM = { w: 6, d: 6, h: 3.3, t: 0.16 };

type Preset = "office" | "living" | "bedroom" | "cafe" | "studio" | "library" | "kitchen" | "cabin" | "basement";

// concrete shelter palette (warm greys, never blue)
const BUNKER: KitPalette = {
  ...PALETTES.evening,
  bg: "#16130F", wall: "#5C5650", wall2: "#544E48", floor: "#4A4540", floorLine: "#3E3A35", rug: "#5A4A40", rug2: "#4A4E48", wood: "#7A6656", woodDark: "#4E4036", metal: "#3A3834",
};

/** Cut-away diorama: floor + back wall + left wall (window / logs / concrete) */
const Shell: React.FC<{ pal: KitPalette; window?: boolean; kind?: "plain" | "logs" | "concrete"; t?: number }> = ({ pal, window = true, kind = "plain", t = 0 }) => {
  const { w, d, h, t: th } = ROOM;
  const wx = -w / 2;
  const win = { z0: -1.2, z1: 1.0, y0: 1.0, y1: 2.5 };
  if (kind === "logs") {
    return (
      <group>
        <Box s={[w, 0.2, d]} p={[0, -0.1, 0]} c={pal.floor} rad={0.02} />
        {Array.from({ length: 11 }, (_, i) => (
          <mesh key={i} position={[-w / 2 + (i + 1) * (w / 12), 0.001, 0]} rotation={[-Math.PI / 2, 0, 0]} material={decal(pal.floorLine, 0.9)}>
            <planeGeometry args={[0.012, d]} />
          </mesh>
        ))}
        <LogWall p={[0, 0, -d / 2]} w={w + th} h={h} c={pal.wood} c2={pal.woodDark} />
        <LogWall p={[wx, 0, 0]} rotY={Math.PI / 2} w={d} h={h} c={pal.wood} c2={pal.woodDark} />
        {window ? (
          <group position={[wx + 0.13, 0, -0.1]} rotation={[0, Math.PI / 2, 0]}>
            <mesh position={[0, 1.75, 0]} material={decal(pal.windowLight, 0.9, pal.windowLight, 0.6)}><planeGeometry args={[1.6, 1.2]} /></mesh>
            <Box s={[1.75, 0.08, 0.08]} p={[0, 2.38, 0.02]} c={pal.woodDark} rad={0.01} />
            <Box s={[1.75, 0.08, 0.08]} p={[0, 1.12, 0.02]} c={pal.woodDark} rad={0.01} />
            <Box s={[0.08, 1.3, 0.08]} p={[-0.84, 1.75, 0.02]} c={pal.woodDark} rad={0.01} />
            <Box s={[0.08, 1.3, 0.08]} p={[0.84, 1.75, 0.02]} c={pal.woodDark} rad={0.01} />
            <Box s={[0.05, 1.2, 0.05]} p={[0, 1.75, 0.03]} c={pal.woodDark} rad={0.01} />
          </group>
        ) : null}
      </group>
    );
  }
  if (kind === "concrete") {
    return (
      <group>
        <Box s={[w, 0.2, d]} p={[0, -0.1, 0]} c={pal.floor} rad={0.02} />
        {[-1, 0, 1].map((k) => (
          <mesh key={`x${k}`} position={[k * 2, 0.001, 0]} rotation={[-Math.PI / 2, 0, 0]} material={decal(pal.floorLine, 0.95)}><planeGeometry args={[0.02, d]} /></mesh>
        ))}
        {[-1, 0, 1].map((k) => (
          <mesh key={`z${k}`} position={[0, 0.001, k * 2]} rotation={[-Math.PI / 2, 0, 0]} material={decal(pal.floorLine, 0.95)}><planeGeometry args={[w, 0.02]} /></mesh>
        ))}
        <Box s={[w + th, h, th]} p={[0, h / 2, -d / 2 - th / 2]} c={pal.wall} rad={0.01} />
        <Box s={[th, h, d]} p={[wx - th / 2, h / 2, 0]} c={pal.wall2} rad={0.01} />
        {/* formwork lines on the concrete */}
        {[0.9, 1.8, 2.7].map((y) => (
          <React.Fragment key={y}>
            <mesh position={[0, y, -d / 2 + 0.001]} material={decal("#4E4842", 0.95)}><planeGeometry args={[w, 0.015]} /></mesh>
            <mesh position={[wx + 0.001, y, 0]} rotation={[0, Math.PI / 2, 0]} material={decal("#48423C", 0.95)}><planeGeometry args={[d, 0.015]} /></mesh>
          </React.Fragment>
        ))}
        <BoardedWindow p={[wx + 0.01, 2.62, -1.25]} rotY={Math.PI / 2} w={1.0} h={0.42} t={t} light="#B89A7A" />
        <Pipes p={[0.2, 3.05, -d / 2 + 0.14]} len={5.6} n={3} />
      </group>
    );
  }
  return (
    <group>
      {/* floor slab with plank lines */}
      <Box s={[w, 0.2, d]} p={[0, -0.1, 0]} c={pal.floor} rad={0.02} />
      {Array.from({ length: 11 }, (_, i) => (
        <mesh key={i} position={[-w / 2 + (i + 1) * (w / 12), 0.001, 0]} rotation={[-Math.PI / 2, 0, 0]} material={decal(pal.floorLine, 0.9)}>
          <planeGeometry args={[0.012, d]} />
        </mesh>
      ))}
      {/* back wall */}
      <Box s={[w + th, h, th]} p={[0, h / 2, -d / 2 - th / 2]} c={pal.wall} rad={0.01} />
      <Box s={[w, 0.12, 0.03]} p={[0, 0.06, -d / 2 + 0.015]} c={pal.wall2} rad={0.005} />
      {/* left wall built around a window opening */}
      {window ? (
        <>
          <Box s={[th, win.y0, d]} p={[wx - th / 2, win.y0 / 2, 0]} c={pal.wall2} rad={0.01} />
          <Box s={[th, h - win.y1, d]} p={[wx - th / 2, (h + win.y1) / 2, 0]} c={pal.wall2} rad={0.01} />
          <Box s={[th, win.y1 - win.y0, win.z0 + d / 2]} p={[wx - th / 2, (win.y0 + win.y1) / 2, (-d / 2 + win.z0) / 2]} c={pal.wall2} rad={0.01} />
          <Box s={[th, win.y1 - win.y0, d / 2 - win.z1]} p={[wx - th / 2, (win.y0 + win.y1) / 2, (win.z1 + d / 2) / 2]} c={pal.wall2} rad={0.01} />
          {/* frame + mullions */}
          <Box s={[0.06, 0.06, win.z1 - win.z0]} p={[wx, win.y0, (win.z0 + win.z1) / 2]} c={pal.woodDark} rad={0.01} />
          <Box s={[0.06, 0.05, win.z1 - win.z0]} p={[wx, (win.y0 + win.y1) / 2, (win.z0 + win.z1) / 2]} c={pal.woodDark} rad={0.01} />
          <Box s={[0.06, win.y1 - win.y0, 0.05]} p={[wx, (win.y0 + win.y1) / 2, (win.z0 + win.z1) / 2]} c={pal.woodDark} rad={0.01} />
          <mesh position={[wx - th, (win.y0 + win.y1) / 2, (win.z0 + win.z1) / 2]} rotation={[0, Math.PI / 2, 0]}>
            <planeGeometry args={[win.z1 - win.z0, win.y1 - win.y0]} />
            <meshStandardMaterial color={pal.windowLight} emissive={pal.windowLight} emissiveIntensity={0.55} />
          </mesh>
          <Box s={[0.22, 0.05, win.z1 - win.z0 + 0.2]} p={[wx + 0.08, win.y0 - 0.02, (win.z0 + win.z1) / 2]} c={pal.wood} rad={0.01} />
        </>
      ) : (
        <Box s={[th, h, d]} p={[wx - th / 2, h / 2, 0]} c={pal.wall2} rad={0.01} />
      )}
    </group>
  );
};

/** furniture layout per preset. Every direct child is one solid for the collision QA. */
const Furniture: React.FC<{ preset: Preset; pal: KitPalette; t: number; days?: number; door?: number; lantern?: boolean; held?: string }> = ({ preset, pal, t, days = 9, door = 0, lantern = true, held }) => {
  switch (preset) {
    case "office":
      return (
        <>
          <Rug p={[0.3, 0, -0.3]} w={2.8} d={2.2} c={pal.rug2} />
          <Desk p={[0.3, 0, -1.9]} w={1.9} pal={pal} />
          <Monitor p={[0.3, 0, -2.05]} pal={pal} />
          <Mug p={[1.0, 0.765, -1.75]} />
          <Lamp p={[-0.45, 0.765, -2.05]} floor={false} pal={pal} />
          <Chair p={[0.3, 0, -1.0]} rotY={Math.PI} pal={pal} />
          <Shelf p={[2.15, 0, -2.75]} w={1.3} pal={pal} />
          <Plant p={[-2.3, 0, -2.4]} pal={pal} kind="tall" s={1.25} />
          <Frame p={[-1.0, 2.0, -2.99]} w={0.7} h={0.9} art={pal.fabric[1]} />
          <Frame p={[-0.15, 2.15, -2.99]} w={0.5} h={0.6} art={pal.fabric[2]} />
        </>
      );
    case "living":
      return (
        <>
          <Rug p={[0.2, 0, 0.2]} w={3.2} d={2.4} c={pal.rug} />
          <Sofa p={[0.3, 0, -1.9]} w={2.4} pal={pal} />
          <Table p={[0.3, 0, -0.3]} r={0.5} h={0.4} pal={pal} />
          <Mug p={[0.2, 0.425, -0.3]} />
          <Lamp p={[-1.6, 0, -2.4]} pal={pal} />
          <Plant p={[2.3, 0, -2.4]} pal={pal} s={1.1} />
          <Shelf p={[-2.65, 0, 1.6]} rotY={Math.PI / 2} w={1.4} rows={4} pal={pal} seed={4} />
          <Frame p={[0.3, 2.2, -2.99]} w={1.2} h={0.75} art={pal.fabric[0]} />
        </>
      );
    case "bedroom":
      return (
        <>
          <Bed p={[0.6, 0, -1.8]} pal={pal} />
          <Box s={[0.5, 0.5, 0.42]} p={[-0.6, 0.25, -2.6]} c={pal.wood} rad={0.03} />
          <Lamp p={[-0.6, 0.5, -2.6]} floor={false} pal={pal} />
          <Rug p={[0.6, 0, 0.3]} w={2.2} d={1.4} c={pal.rug2} round />
          <Plant p={[2.4, 0, -2.5]} pal={pal} kind="cactus" s={1.4} />
          <Frame p={[0.6, 2.25, -2.99]} w={0.9} h={0.6} art={pal.fabric[3]} />
        </>
      );
    case "cafe":
      return (
        <>
          {/* counter stands 1.1 m off the back wall so the barista fits between */}
          <Counter p={[0.6, 0, -1.6]} w={3.2} pal={pal} />
          {/* barista side: espresso machine faces the bar (−z), pastry case faces the guests */}
          <EspressoMachine p={[1.55, 1.06, -1.66]} rotY={Math.PI} t={t} />
          <PastryCase p={[-0.38, 1.06, -1.52]} w={0.66} />
          <Mug p={[0.45, 1.06, -1.42]} c="#E6DCCD" />
          <MenuBoard p={[-1.75, 1.9, -2.99]} w={0.95} h={0.72} />
          {[-0.4, 0.6].map((x) => (
            <Stool key={x} p={[x, 0, -0.95]} pal={pal} />
          ))}
          <Table p={[-1.5, 0, 0.9]} r={0.42} h={0.74} pal={pal} />
          <Chair p={[-1.5, 0, 1.6]} rotY={Math.PI} pal={pal} c={pal.fabric[2]} />
          <Chair p={[-1.5, 0, 0.2]} pal={pal} c={pal.fabric[1]} />
          <Mug p={[-1.38, 0.765, 0.98]} />
          <Table p={[1.5, 0, 1.5]} r={0.42} h={0.74} pal={pal} />
          <Chair p={[1.5, 0, 2.2]} rotY={Math.PI} pal={pal} c={pal.fabric[0]} />
          <Mug p={[1.45, 0.765, 1.45]} />
          {[-0.4, 0.8, 2.0].map((x) => (
            <PendantLamp key={x} p={[x, 3.3, -1.6]} pal={pal} drop={0.85} />
          ))}
          <Shelf p={[0.6, 2.1, -2.86]} w={2.6} rows={1} pal={pal} seed={7} />
          <Plant p={[-2.4, 0, -2.4]} pal={pal} s={1.1} />
        </>
      );
    case "library":
      return (
        <>
          {[-1.62, 0, 1.62].map((x, i) => (
            <Shelf key={x} p={[x, 0, -2.82]} w={1.56} rows={6} pal={pal} seed={3 + i * 5} />
          ))}
          <Curtain p={[-2.86, 0.2, -1.45]} rotY={Math.PI / 2} />
          <Curtain p={[-2.86, 0.2, 1.25]} rotY={Math.PI / 2} />
          <Rug p={[0.3, 0, -0.3]} w={2.8} round c={pal.rug} />
          <Armchair p={[0.15, 0, -0.75]} rotY={0.35} pal={pal} />
          <SideTable p={[1.15, 0, -1.0]} pal={pal} />
          <Candle p={[1.2, 0.57, -1.05]} t={t} />
          <BookStack p={[1.05, 0.57, -0.92]} pal={pal} n={4} seed={2} />
          <Lamp p={[-0.95, 0, -1.55]} pal={pal} />
          <Armchair p={[1.55, 0, 0.9]} rotY={-2.3} c={pal.fabric[0]} pal={pal} />
          <Plant p={[2.5, 0, 1.9]} pal={pal} kind="tall" s={1.25} />
          <BookStack p={[-1.6, 0, 0.6]} pal={pal} n={6} seed={8} rotY={0.4} />
        </>
      );
    case "kitchen":
      return (
        <>
          <KitchenCounter p={[0.2, 0, -2.68]} w={3.2} pal={pal} />
          <Stove p={[-1.85, 0, -2.66]} pal={pal} t={t} />
          <Fridge p={[2.3, 0, -2.62]} pal={pal} />
          <Plant p={[1.35, 0.91, -2.62]} pal={pal} s={0.45} />
          <WallClock p={[-1.85, 2.75, -2.97]} pal={pal} />
          <Rug p={[0.4, 0, 0.6]} w={2.6} d={2.0} c={pal.rug2} />
          <DiningTable p={[0.4, 0, 0.6]} pal={pal} />
          <Mug p={[0.65, 0.775, 0.5]} />
          <PendantLamp p={[0.4, 3.3, 0.6]} pal={pal} drop={1.1} />
        </>
      );
    case "cabin":
      return (
        <>
          <Fireplace p={[0.2, 0, -2.58]} pal={pal} t={t} />
          <Rug p={[0.2, 0, -0.85]} w={2.8} d={1.8} c={pal.rug} />
          <Sofa p={[0.2, 0, 0.62]} rotY={Math.PI} w={2.2} pal={pal} />
          <Armchair p={[-1.65, 0, -0.95]} rotY={1.1} pal={pal} />
          <SideTable p={[1.55, 0, 0.0]} pal={pal} />
          <Candle p={[1.6, 0.57, 0.02]} t={t + 1.3} />
          <Mug p={[1.45, 0.57, -0.08]} />
          {/* firewood stack */}
          <group>
            {Array.from({ length: 9 }, (_, i) => (
              <Cap key={i} r={0.07} len={0.5} p={[1.9 + (i % 3) * 0.16, 0.08 + Math.floor(i / 3) * 0.14, -2.55]} r3={[0, 0, Math.PI / 2]} c={i % 2 ? "#6E5442" : "#7E6450"} />
            ))}
          </group>
          <Lamp p={[-2.4, 0, 1.0]} pal={pal} />
          <Plant p={[-2.4, 0, -2.4]} pal={pal} s={1.1} />
        </>
      );
    case "basement":
      return (
        <>
          <SupplyRack p={[-1.0, 0, -2.74]} w={1.4} levels={4} seed={3} pal={pal} />
          <SupplyRack p={[0.6, 0, -2.74]} w={1.4} levels={4} seed={8} pal={pal} />
          <SteelDoor p={[2.2, 0, -2.88]} open={door} pal={pal} />
          <WaterHeater p={[-2.55, 0, -2.55]} pal={pal} />
          <Sandbags p={[-2.75, 0, -1.12]} rotY={Math.PI / 2} rows={3} cols={4} />
          <Mattress p={[-2.15, 0, 0.98]} pal={pal} />
          <Desk p={[1.2, 0, 0.6]} rotY={-Math.PI / 2} w={1.5} pal={pal} />
          {held !== "radio" ? <CrankRadio p={[1.15, 0.765, 0.35]} rotY={-Math.PI / 2} t={t} /> : <group />}
          {held !== "lantern" ? <Lantern p={[1.15, 0.765, 1.0]} t={t} on={lantern} /> : <group />}
          <FirstAid p={[1.25, 0.765, -0.05]} rotY={-Math.PI / 2} />
          <Bucket p={[2.6, 0, 1.75]} />
          <Barrel p={[2.6, 0, 0.55]} />
          <TallyBoard p={[-1.0, 2.5, -2.99]} days={days} />
          <PlasticSheet p={[0.6, 2.55, -2.99]} w={0.6} h={0.4} />
        </>
      );
    case "studio":
    default:
      return (
        <>
          <Desk p={[-1.0, 0, -1.6]} rotY={Math.PI / 2} w={1.7} pal={pal} />
          <SmallLaptop p={[-1.05, 0, -1.6]} rotY={Math.PI / 2} pal={pal} />
          <Chair p={[-0.25, 0, -1.6]} rotY={-Math.PI / 2} pal={pal} />
          <Plant p={[-2.3, 0, 0.6]} pal={pal} kind="tall" s={1.3} />
          <Rug p={[0.6, 0, 0.4]} w={2.0} d={2.0} c={pal.rug} round />
          <Sofa p={[1.6, 0, -2.2]} w={1.6} pal={pal} />
        </>
      );
  }
};

const SCREEN_OF: Partial<Record<Preset, { center: V3; w: number; h: number; rotY: number }>> = {
  office: { center: [0.3, MONITOR_SCREEN.y, -2.05 + MONITOR_SCREEN.z], w: MONITOR_SCREEN.w, h: MONITOR_SCREEN.h, rotY: 0 },
  living: { center: [0.3, TV_SCREEN.y, -2.95], w: TV_SCREEN.w, h: TV_SCREEN.h, rotY: 0 },
};

const CAMS: Record<string, CamKey[]> = {
  // target sits above the room centre so the room lands in the lower 2/3 (clear of top captions)
  diorama: [
    { t: 0, pos: [13, 12.2, 15], target: [0, 3.0, 0], fov: 30 },
    { t: 8, pos: [11.5, 11.2, 16.5], target: [0, 3.0, 0], fov: 30 },
  ],
  front: [
    { t: 0, pos: [0.6, 3.2, 17.5], target: [0, 1.4, 0], fov: 28 },
    { t: 8, pos: [0.2, 3.0, 15.5], target: [0, 1.4, 0], fov: 28 },
  ],
  closeDesk: [
    { t: 0, pos: [3.2, 2.6, 4.2], target: [0.3, 1.05, -1.6], fov: 34 },
    { t: 8, pos: [2.4, 2.3, 3.4], target: [0.3, 1.05, -1.7], fov: 34 },
  ],
  pushIn: [
    { t: 0, pos: [14, 12.5, 16], target: [0, 3.0, 0], fov: 30 },
    { t: 4, pos: [5.2, 3.6, 6.4], target: [0.2, 1.1, -1.4], fov: 32 },
  ],
  top: [
    { t: 0, pos: [0.01, 22, 4], target: [0, 0, 0], fov: 30 },
    { t: 8, pos: [0.01, 20, 3.5], target: [0, 0, 0], fov: 30 },
  ],
  // inside, at eye level, slow drift (cozy presets)
  inside: [
    { t: 0, pos: [2.4, 1.65, 2.6], target: [-0.2, 1.0, -1.2], fov: 50 },
    { t: 8, pos: [1.9, 1.6, 2.1], target: [-0.3, 1.0, -1.4], fov: 50 },
  ],
};

/** per-preset cameras: first-person (fpv*) at eye height 1.6 m, and hero framings */
const PRESET_CAMS: Partial<Record<Preset, Record<string, CamKey[]>>> = {
  library: {
    reading: [{ t: 0, pos: [2.3, 1.55, 1.9], target: [0.1, 0.85, -0.9], fov: 46 }, { t: 8, pos: [1.9, 1.45, 1.5], target: [0.1, 0.85, -1.0], fov: 46 }],
    shelves: [{ t: 0, pos: [-0.4, 1.6, 0.4], target: [-0.6, 1.5, -2.9], fov: 52 }, { t: 8, pos: [0.2, 1.7, -0.6], target: [0.4, 1.6, -2.9], fov: 52 }],
  },
  cafe: {
    // whole bar: barista, machine, menu board; guests in the foreground
    counter: [{ t: 0, pos: [0.25, 2.25, 3.95], target: [0.5, 1.25, -1.6], fov: 46 }, { t: 8, pos: [0.05, 2.15, 3.6], target: [0.5, 1.25, -1.6], fov: 46 }],
    // barista POV behind the bar, looking at the espresso machine (head-cam)
    fpvBar: [{ t: 0, pos: [0.95, 1.66, -2.55], target: [1.55, 1.12, -1.55] }, { t: 6, pos: [1.1, 1.65, -2.48], target: [1.6, 1.1, -1.5] }],
    // the window table, guest on the chair at (-1.5, 0.2) facing the camera; back wall + window behind (never the open side)
    table: [{ t: 0, pos: [-0.5, 1.5, 2.6], target: [-1.55, 1.05, 0.0], fov: 42 }, { t: 8, pos: [-0.65, 1.46, 2.3], target: [-1.55, 1.05, 0.0], fov: 42 }],
  },
  kitchen: {
    counter: [{ t: 0, pos: [1.6, 2.1, 2.9], target: [-0.9, 1.1, -2.3], fov: 46 }, { t: 8, pos: [1.3, 1.95, 2.4], target: [-1.0, 1.1, -2.3], fov: 46 }],
    table: [{ t: 0, pos: [2.6, 2.2, 2.6], target: [0.4, 0.8, 0.5], fov: 44 }, { t: 8, pos: [2.2, 2.0, 2.2], target: [0.4, 0.8, 0.5], fov: 44 }],
  },
  cabin: {
    fire: [{ t: 0, pos: [2.2, 1.7, 1.9], target: [-0.1, 0.9, -2.2], fov: 46 }, { t: 8, pos: [1.9, 1.55, 1.5], target: [-0.1, 0.9, -2.3], fov: 46 }],
  },
  basement: {
    // cut-away rooms have no front/right walls: first-person cameras always look toward the back-left corner
    fpvEnter: [{ t: 0, pos: [2.0, 1.72, 2.0], target: [-1.6, 1.0, -2.4], fov: 62 }, { t: 6, pos: [0.9, 1.62, 0.6], target: [-1.8, 0.95, -2.6], fov: 62 }],
    fpvShelf: [{ t: 0, pos: [-0.2, 1.6, -0.5], target: [-0.4, 1.05, -2.8], fov: 56 }, { t: 6, pos: [-0.25, 1.55, -1.5], target: [-0.5, 0.95, -2.8], fov: 56 }],
    fpvRadio: [{ t: 0, pos: [-0.1, 1.55, 0.45], target: [1.15, 0.85, 0.4], fov: 54 }, { t: 6, pos: [0.3, 1.45, 0.42], target: [1.15, 0.82, 0.4], fov: 54 }],
    fpvDoor: [{ t: 0, pos: [0.7, 1.62, -0.4], target: [2.2, 1.1, -2.9], fov: 56 }, { t: 6, pos: [1.5, 1.62, -1.6], target: [2.2, 1.1, -2.9], fov: 56 }],
    fpvWindow: [{ t: 0, pos: [-1.1, 1.6, -0.4], target: [-2.95, 2.55, -1.25], fov: 56 }, { t: 6, pos: [-1.6, 1.6, -0.8], target: [-2.95, 2.6, -1.25], fov: 56 }],
    fpvBed: [{ t: 0, pos: [-0.6, 1.5, 1.6], target: [-2.2, 0.3, 0.6], fov: 56 }, { t: 6, pos: [-0.9, 1.35, 1.4], target: [-2.2, 0.3, 0.7], fov: 56 }],
    fpvTally: [{ t: 0, pos: [-0.6, 1.62, -0.9], target: [-1.0, 2.45, -2.99], fov: 50 }, { t: 6, pos: [-0.8, 1.62, -1.6], target: [-1.0, 2.5, -2.99], fov: 50 }],
    fpvHands: [{ t: 0, pos: [0.0, 1.6, 0.6], target: [0.2, 1.1, -1.4], fov: 58 }, { t: 6, pos: [0.0, 1.6, 0.4], target: [0.15, 1.05, -1.5], fov: 58 }],
    corner: [{ t: 0, pos: [2.7, 2.4, 2.8], target: [-0.9, 0.95, -0.9], fov: 60 }, { t: 8, pos: [2.4, 2.25, 2.4], target: [-1.0, 0.95, -1.0], fov: 60 }],
  },
};

const DEFAULT_PEOPLE: Record<Preset, PersonSpec[]> = {
  office: [{ pose: "type", pos: [0.3, 0, -1.0], rotY: Math.PI, seed: 1 }],
  living: [{ pose: "sit", pos: [0.0, 0.08, -1.85], rotY: 0, seed: 2 }, { pose: "phone", pos: [1.3, 0, 0.6], rotY: -2.4, seed: 3 }],
  bedroom: [{ pose: "phone", pos: [-1.4, 0, 0.6], rotY: 0.6, seed: 4 }],
  cafe: [{ pose: "stand", pos: [0.6, 0, -2.4], rotY: 0, seed: 5 }, { pose: "sit", pos: [-1.5, 0.05, 1.6], rotY: Math.PI, seed: 6 }, { pose: "stand", pos: [2.4, 0, 0.3], walkTo: [-0.3, 0, 0.35], walkDur: 4.5, rotY: -1.2, seed: 7 }],
  studio: [{ pose: "type", pos: [-0.25, 0, -1.6], rotY: -Math.PI / 2, seed: 8 }],
  library: [{ pose: "sit", pos: [0.12, 0.0, -0.68], rotY: 0.35, seed: 9 }],
  kitchen: [{ pose: "stand", pos: [-1.85, 0, -1.75], rotY: Math.PI, seed: 10 }],
  cabin: [{ pose: "sit", pos: [0.2, 0.08, 0.55], rotY: Math.PI, seed: 11 }],
  basement: [{ pose: "think", pos: [0.2, 0, 1.0], rotY: -0.7, seed: 12 }],
};

export const Room3D: React.FC<{
  preset?: Preset; look?: keyof typeof PALETTES; cam?: string | CamKey[]; people?: PersonSpec[]; screen?: NestedBlock; window?: boolean; build?: boolean; lights?: "day" | "evening" | "night";
  /** first-person hands holding an item. The user disliked fingers in frame — prefer a plain head-cam (no hands). */
  hands?: { item?: HandItem; sleeve?: string; gloves?: string; from?: number };
  /** days: tally marks — a number, or steps [[anchor, n], …] so marks appear on the words (one shot, no flash cuts) */
  days?: number | [unknown, number][]; door?: number | [number, number]; lantern?: boolean;
  /** door: [from, to] animates over the whole shot; with doorAt it lands exactly on that word (doorDur seconds, accelerating like a slam) */
  doorAt?: unknown; doorDur?: number;
  /** head: first-person head-cam for custom cam keys (fpv* presets are head-cams already); fov overrides FPV_FOV */
  head?: boolean; fov?: number;
}> = ({ preset = "office", look, cam = "diorama", people, screen, window = true, build = true, lights, hands, days, door = 0, lantern = true, head, fov, doorAt, doorDur = 0.5 }) => {
  const { f, fps, at, dur } = useBlockTime();
  const th = useTheme();
  const { qa } = useReel();
  const t = f / fps;
  const bunker = preset === "basement";
  const palKey = look ?? (lights === "night" ? "night" : lights === "evening" || preset === "cabin" || preset === "library" ? "evening" : th.dark ? "dusk" : "sand");
  const pal = bunker ? BUNKER : PALETTES[palKey] ?? PALETTES.dusk;
  const camSet = { ...CAMS, ...(PRESET_CAMS[preset] ?? {}) };
  const keys = Array.isArray(cam) ? cam : camSet[cam] ?? CAMS.diorama;
  const fpv = (typeof cam === "string" && cam.startsWith("fpv")) || !!head;
  const c = fpv ? headCam(keys, t, { fov: fov ?? FPV_FOV }) : camAt(keys, t);
  const ppl: PersonSpec[] = people ?? (fpv ? [] : DEFAULT_PEOPLE[preset]);
  const grow = build && !fpv ? E.outExpo(clamp01(t / 1.1)) : 1;
  const sc = SCREEN_OF[preset];
  const camera = makeCamera(c);
  const night = palKey === "night";
  const shellKind = bunker ? "concrete" : preset === "cabin" ? "logs" : "plain";
  const hasWindow = bunker ? false : window;
  const doorP = doorAt !== undefined ? E.in(clamp01((t - (at(doorAt) / fps - doorDur)) / doorDur)) : E.inOut(clamp01(t / Math.max(0.5, dur / fps)));
  const doorOpen = Array.isArray(door) ? door[0] + (door[1] - door[0]) * doorP : door;
  const dayCount = Array.isArray(days) ? days.reduce((n, [a, v]) => (t >= at(a) / fps ? v : n), 0) : days;
  return (
    <AbsoluteFill style={{ background: pal.bg }}>
      <Stage3D cam={c} lights={bunker ? "sunset" : night ? "night" : palKey === "evening" ? "sunset" : "soft"} env={bunker ? 0.12 : night ? 0.25 : 0.55} exposure={bunker ? 0.95 : 1}>
        <group scale={[1, grow, 1]} position={[0, 0, 0]}>
          <group userData={{ qa: "walls" }}>
            <Shell pal={pal} window={hasWindow} kind={shellKind} t={t} />
          </group>
          <group userData={{ qa: "furniture" }}>
            <Furniture preset={preset} pal={pal} t={t} days={dayCount} door={doorOpen} lantern={lantern} held={hands?.item} />
          </group>
          {ppl.map((p, i) => {
            const s = p.at !== undefined ? at(p.at) / fps : 0;
            if (t < s) return null;
            const p0 = p.pos ?? [0, 0, 0];
            let pos = p0;
            let pose = p.pose ?? "stand";
            let rotY = p.rotY ?? 0;
            if (p.walkTo) {
              const k = clamp01((t - s) / (p.walkDur ?? 3));
              pos = [p0[0] + (p.walkTo[0] - p0[0]) * k, p0[1], p0[2] + (p.walkTo[2] - p0[2]) * k];
              if (k < 1) {
                pose = "walk";
                rotY = Math.atan2(p.walkTo[0] - p0[0], p.walkTo[2] - p0[2]);
              }
            }
            let pl = p.look;
            if (p.suitAt) {
              const on = Object.fromEntries(Object.entries(p.suitAt).map(([k, a]) => [k, t >= at(a) / fps]));
              pl = { ...pl, suit: { ...(typeof pl?.suit === "object" ? pl.suit : {}), ...on } };
            }
            return (
              <group key={i} userData={{ qa: "person", pose, id: `person${i}` }}>
                <Person pos={pos} rotY={rotY} pose={pose} t={t + i * 0.37} seed={p.seed ?? i} look={pl} pal={pal} />
              </group>
            );
          })}
        </group>
        {bunker ? <BareBulb p={[0.3, 3.3, -0.4]} t={t} /> : null}
        {hands && t >= (hands.from ?? 0) ? (
          <FPHands cam={camera} item={hands.item} t={t} sleeve={hands.sleeve} gloves={hands.gloves} raise={E.out(clamp01((t - (hands.from ?? 0)) / 0.5))} />
        ) : null}
        <CollisionQA on={qa} />
        <CameraClipQA on={qa} />
        {hasWindow ? <directionalLight position={[-9, 5, 1]} intensity={night ? 0.4 : 1.5} color={pal.windowLight} castShadow shadow-mapSize-width={2048} shadow-mapSize-height={2048} shadow-camera-left={-6} shadow-camera-right={6} shadow-camera-top={6} shadow-camera-bottom={-6} /> : null}
      </Stage3D>
      {screen && sc && grow > 0.98
        ? (() => {
            const [cx, cy, cz] = sc.center;
            const pts = [
              new THREE.Vector3(cx - sc.w / 2, cy + sc.h / 2, cz + 0.004),
              new THREE.Vector3(cx + sc.w / 2, cy + sc.h / 2, cz + 0.004),
              new THREE.Vector3(cx + sc.w / 2, cy - sc.h / 2, cz + 0.004),
              new THREE.Vector3(cx - sc.w / 2, cy - sc.h / 2, cz + 0.004),
            ];
            const q = pts.map((p) => project(camera, p)).map(([x, y]) => [x, y] as [number, number]);
            const pxW = 960;
            const pxH = Math.round((pxW * sc.h) / sc.w);
            return (
              <>
                <ScreenQuad q={q} pxW={pxW} pxH={pxH} content={<Nested spec={screen} w={pxW} h={pxH} bg={th.card} />} />
                {qa ? <ScreenOcclusionQA camera={camera} center={sc.center} w={sc.w} h={sc.h} ppl={ppl} t={t} /> : null}
              </>
            );
          })()
        : null}
    </AbsoluteFill>
  );
};

/** The live HTML screen is drawn over the WebGL canvas, so nothing may stand between the camera and it.
 *  Checks people (the only thing that moves in front of monitors) against rays to a 5x5 grid on the screen. */
const ScreenOcclusionQA: React.FC<{ camera: THREE.Camera; center: V3; w: number; h: number; ppl: PersonSpec[]; t: number }> = ({ camera, center, w, h, ppl }) => {
  React.useLayoutEffect(() => {
    const boxes = ppl.map((p) => {
      const [x, y, z] = p.pos ?? [0, 0, 0];
      const sitting = p.pose === "sit" || p.pose === "type";
      return new THREE.Box3(new THREE.Vector3(x - 0.24, y, z - 0.2), new THREE.Vector3(x + 0.24, y + (sitting ? 1.32 : 1.85), z + 0.2));
    });
    let hit = 0;
    const ray = new THREE.Ray();
    const origin = new THREE.Vector3().setFromMatrixPosition(camera.matrixWorld);
    for (let i = 0; i < 5; i++)
      for (let j = 0; j < 5; j++) {
        const pt = new THREE.Vector3(center[0] - w / 2 + (w * (i + 0.5)) / 5, center[1] - h / 2 + (h * (j + 0.5)) / 5, center[2]);
        const dist = origin.distanceTo(pt);
        ray.set(origin, pt.clone().sub(origin).normalize());
        if (boxes.some((b) => { const v = ray.intersectBox(b, new THREE.Vector3()); return v && origin.distanceTo(v) < dist - 0.02; })) hit++;
      }
    if (hit) console.log("QA " + JSON.stringify({ frame: -2, collisions3d: [`3d-screen occluded by a person (${hit * 4}% of the screen)`] }));
  });
  return null;
};

import { quadToMatrix3d } from "./core";
export const ScreenQuad: React.FC<{ q: [number, number][]; pxW: number; pxH: number; content: React.ReactNode; radius?: number }> = ({ q, pxW, pxH, content, radius = 6 }) => (
  <div data-qa="layer" data-qa-id="3d-screen" data-qa-cat="screen" data-qa-bleed="1" style={{ position: "absolute", left: 0, top: 0, width: pxW, height: pxH, transformOrigin: "0 0", transform: quadToMatrix3d(pxW, pxH, q), overflow: "hidden", borderRadius: radius, background: "#0c0c0c" }}>{content}</div>
);
