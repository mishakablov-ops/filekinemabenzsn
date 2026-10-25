import type React from "react";
import type { PosPreset } from "../core/types";

export type SfxEvent = { f: number; id: string; vol?: number };

export type BlockDef = {
  C: React.FC<any>;
  cat: "text" | "ui" | "device" | "data" | "bg" | "3d" | "fx" | "social" | "map";
  desc: string;
  /** default position preset */
  pos?: PosPreset;
  /** default entrance (falls back to the theme's) */
  enter?: string;
  /** block is meant to sit on top of others (cursor, callout): QA overlap check ignores it */
  overlay?: boolean;
  /** block is designed to run past the frame edges (bands, tickers): no off-screen warning */
  bleed?: boolean;
  /** block animates its own entrance; skip the generic one */
  self?: boolean;
  /** entrance sound id (null = silent) */
  sfx?: string | null;
  /** internal sound events, frames relative to layer start */
  events?: (props: any, t: { fps: number; dur: number; at: (a: unknown, fb?: number) => number }) => SfxEvent[];
  /** example props for the gallery / docs */
  example?: Record<string, unknown>;
  /** gallery duration seconds */
  exampleDur?: number;
};

export const defineBlock = <P,>(def: Omit<BlockDef, "C"> & { C: React.FC<P> }) => def as BlockDef;
