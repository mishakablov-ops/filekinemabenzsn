import type { Pos, PosPreset } from "./types";

/**
 * Layout grid for 1080x1920 vertical video.
 * Platform UI safe zones (Reels/Shorts/TikTok): keep text out of
 *   top 0–200 (status/header), bottom 1500–1920 (caption, nickname, audio),
 *   right 960–1080 below y=900 (like/comment/share rail).
 * Caption bands:
 *   top     y 250–620   (editorial captions, stage below)
 *   middle  y 760–1160
 *   lower   y 1180–1460 (subtitle captions, stage above)
 */
export const W = 1080;
export const H = 1920;
export const SAFE = { top: 200, bottom: 1500, side: 72, rail: 140 };

export type Box = { x: number; y: number; w: number; h: number };

export const PRESETS: Record<PosPreset, Box> = {
  full: { x: 0, y: 0, w: W, h: H },
  stage: { x: 60, y: 680, w: W - 120, h: 820 }, // under top captions (50 px air below the band)
  stageHigh: { x: 60, y: 180, w: W - 120, h: 960 }, // above lower captions (40 px air)
  stageLow: { x: 60, y: 1150, w: W - 120, h: 380 },
  center: { x: 60, y: 460, w: W - 120, h: 1000 },
  top: { x: 72, y: 220, w: W - 144, h: 420 },
  upper: { x: 60, y: 420, w: W - 120, h: 560 },
  lower: { x: 60, y: 1100, w: W - 120, h: 420 },
  bottom: { x: 72, y: 1300, w: W - 144, h: 300 },
  left: { x: 60, y: 560, w: 520, h: 900 },
  right: { x: 500, y: 560, w: 520, h: 900 },
  topLeft: { x: 60, y: 220, w: 480, h: 480 },
  topRight: { x: 540, y: 220, w: 480, h: 480 },
  bottomLeft: { x: 60, y: 1050, w: 480, h: 450 },
  bottomRight: { x: 540, y: 1050, w: 480, h: 450 },
};

export const CAPTION_BANDS = {
  top: { y: 250, h: 380 },
  upper: { y: 420, h: 380 },
  middle: { y: 760, h: 400 },
  lower: { y: 1180, h: 290 },
  bottom: { y: 1320, h: 180 },
} as const;

/** "stage" follows the caption band so blocks never sit under the captions */
export const stageFor = (capPos?: string, hidden?: boolean): PosPreset => {
  if (hidden) return "center";
  if (capPos === "lower" || capPos === "bottom") return "stageHigh";
  if (capPos === "middle") return "stageLow";
  return "stage";
};

export const resolveBox = (pos: Pos | undefined, fallback: PosPreset = "stage", stage: PosPreset = "stage"): Box & { scale: number; rotate: number } => {
  const pick = (p: PosPreset) => PRESETS[p === "stage" ? stage : p] ?? PRESETS[fallback];
  if (!pos) return { ...pick(fallback), scale: 1, rotate: 0 };
  if (typeof pos === "string") return { ...pick(pos), scale: 1, rotate: 0 };
  const b = pick(pos.preset ?? fallback);
  return {
    x: (pos.x ?? b.x) + (pos.dx ?? 0),
    y: (pos.y ?? b.y) + (pos.dy ?? 0),
    w: pos.w ?? b.w,
    h: pos.h ?? b.h,
    scale: pos.scale ?? 1,
    rotate: pos.rotate ?? 0,
  };
};
