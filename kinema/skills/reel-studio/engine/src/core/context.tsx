import React, { createContext, useContext } from "react";
import type { Theme } from "../theme/styles";
import { getTheme } from "../theme/styles";
import type { BeatGrid, SfxMeta, Transcript } from "./types";

export type ReelCtx = {
  theme: Theme;
  transcript: Transcript | null;
  beats: BeatGrid | null;
  total: number; // seconds
  sfxIndex: SfxMeta[];
  qa?: boolean;
};

const Ctx = createContext<ReelCtx>({ theme: getTheme("dusk"), transcript: null, beats: null, total: 10, sfxIndex: [] });

export const ReelProvider: React.FC<{ value: ReelCtx; children: React.ReactNode }> = ({ value, children }) => (
  <Ctx.Provider value={value}>{children}</Ctx.Provider>
);
export const useReel = () => useContext(Ctx);
export const useTheme = () => useContext(Ctx).theme;

/** Override theme for a subtree (scene-level style switch) */
export const ThemeScope: React.FC<{ theme: Theme; children: React.ReactNode }> = ({ theme, children }) => {
  const v = useContext(Ctx);
  return <Ctx.Provider value={{ ...v, theme }}>{children}</Ctx.Provider>;
};

/** Timing info passed to every block: frame-accurate local time + resolved event frames */
export type BlockTime = {
  /** frames since the layer started */
  f: number;
  /** layer length in frames */
  dur: number;
  fps: number;
  /** resolve an anchor (props like clickAt / beats) to a local frame */
  at: (a: unknown, fallbackSec?: number) => number;
  /** frames until the layer ends (for exit-aware internal animations) */
  left: number;
};

const TimeCtx = createContext<BlockTime>({ f: 0, dur: 1, fps: 60, at: () => 0, left: 1 });
export const BlockTimeProvider: React.FC<{ value: BlockTime; children: React.ReactNode }> = ({ value, children }) => (
  <TimeCtx.Provider value={value}>{children}</TimeCtx.Provider>
);
export const useBlockTime = () => useContext(TimeCtx);

/** caption band of the current scene (layout adapts "stage" to it) */
const SceneCapCtx = createContext<{ pos?: string; hidden?: boolean }>({});
export const SceneCapProvider: React.FC<{ value: { pos?: string; hidden?: boolean }; children: React.ReactNode }> = ({ value, children }) => (
  <SceneCapCtx.Provider value={value}>{children}</SceneCapCtx.Provider>
);
export const useSceneCap = () => useContext(SceneCapCtx);
