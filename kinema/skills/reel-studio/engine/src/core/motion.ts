import type React from "react";
import { Easing, interpolate, spring } from "remotion";

export const E = {
  out: Easing.bezier(0.22, 1, 0.36, 1), // easeOutQuint-ish, the house ease
  outSoft: Easing.bezier(0.25, 0.8, 0.3, 1),
  outExpo: Easing.bezier(0.16, 1, 0.3, 1),
  inOut: Easing.bezier(0.65, 0, 0.35, 1),
  in: Easing.bezier(0.55, 0, 1, 0.45),
  snap: Easing.bezier(0.2, 0.9, 0.1, 1),
  back: Easing.bezier(0.34, 1.56, 0.64, 1),
  linear: (t: number) => t,
};

export const clamp01 = (x: number) => Math.max(0, Math.min(1, x));

/** 0..1 progress of `frame` through [start, start+dur] with easing */
export const prog = (frame: number, start: number, dur: number, ease: (t: number) => number = E.out) =>
  dur <= 0 ? (frame >= start ? 1 : 0) : ease(clamp01((frame - start) / dur));

export const lerp = (a: number, b: number, t: number) => a + (b - a) * t;

export const SPR = {
  soft: { damping: 200, stiffness: 120, mass: 1 },
  ui: { damping: 18, stiffness: 170, mass: 0.9 },
  pop: { damping: 11, stiffness: 190, mass: 0.8 },
  slam: { damping: 14, stiffness: 320, mass: 0.7 },
  heavy: { damping: 22, stiffness: 90, mass: 1.4 },
};

export const springAt = (frame: number, fps: number, delay = 0, cfg = SPR.ui, durationInFrames?: number) =>
  spring({ frame: frame - delay, fps, config: cfg, durationInFrames });

/** Wiggle (smooth pseudo-random) — deterministic, frame based */
export const wiggle = (frame: number, freq = 0.05, seed = 1) => {
  const a = Math.sin(frame * freq * 1.0 + seed * 12.9898) * 0.5;
  const b = Math.sin(frame * freq * 2.31 + seed * 78.233) * 0.3;
  const c = Math.sin(frame * freq * 4.17 + seed * 37.719) * 0.2;
  return a + b + c;
};

/** Camera shake envelope from a list of hit frames */
export const shake = (frame: number, hits: number[], amp = 14, decayFrames = 14) => {
  let x = 0;
  let y = 0;
  let r = 0;
  for (const h of hits) {
    const d = frame - h;
    if (d < 0 || d > decayFrames * 3) continue;
    const e = Math.exp(-d / decayFrames) * amp;
    x += Math.sin(d * 1.9 + h) * e;
    y += Math.cos(d * 2.3 + h * 0.7) * e * 0.8;
    r += Math.sin(d * 1.3 + h * 0.3) * e * 0.04;
  }
  return { x, y, r };
};

export type EnterKind =
  | "none" | "fade" | "rise" | "riseBig" | "drop" | "pop" | "slam" | "zoom" | "blur" | "slideL" | "slideR"
  | "slideUp" | "slideDown" | "flip" | "flipY" | "swing" | "unfold" | "glitch" | "iris" | "wipe" | "stretch";

/**
 * Generic entrance/exit look for a layer. p: 0 (hidden) .. 1 (settled).
 * Returns style fragments that compose with the layer's own transform.
 */
export const enterLook = (kind: string, p: number, frame = 0): React.CSSProperties => {
  const q = 1 - p;
  switch (kind as EnterKind) {
    case "none":
      return {};
    case "fade":
      return { opacity: p };
    case "blur":
      return { opacity: p, filter: `blur(${q * 24}px)` };
    case "rise":
      return { opacity: clamp01(p * 1.6), transform: `translateY(${q * 70}px)`, filter: q > 0.01 ? `blur(${q * 14}px)` : undefined };
    case "riseBig":
      return { opacity: clamp01(p * 1.4), transform: `translateY(${q * 260}px) scale(${lerp(0.92, 1, p)})`, filter: q > 0.01 ? `blur(${q * 18}px)` : undefined };
    case "drop":
      return { opacity: clamp01(p * 2), transform: `translateY(${-q * 220}px)` };
    case "slideUp":
      return { opacity: clamp01(p * 2), transform: `translateY(${q * 1100}px)` };
    case "slideDown":
      return { opacity: clamp01(p * 2), transform: `translateY(${-q * 1100}px)` };
    case "pop":
      return { opacity: clamp01(p * 2.5), transform: `scale(${lerp(0.82, 1, p)})`, filter: q > 0.01 ? `blur(${q * 8}px)` : undefined };
    case "slam":
      return { opacity: clamp01(p * 3), transform: `scale(${lerp(1.45, 1, p)})`, filter: q > 0.01 ? `blur(${q * 26}px)` : undefined };
    case "zoom":
      return { opacity: clamp01(p * 1.5), transform: `scale(${lerp(0.55, 1, p)})`, filter: q > 0.01 ? `blur(${q * 16}px)` : undefined };
    case "stretch":
      return { opacity: clamp01(p * 2), transform: `scaleY(${lerp(0.2, 1, p)}) scaleX(${lerp(1.2, 1, p)})`, filter: q > 0.01 ? `blur(${q * 10}px)` : undefined };
    case "slideL":
      return { opacity: clamp01(p * 1.5), transform: `translateX(${-q * 420}px)`, filter: q > 0.01 ? `blur(${q * 12}px)` : undefined };
    case "slideR":
      return { opacity: clamp01(p * 1.5), transform: `translateX(${q * 420}px)`, filter: q > 0.01 ? `blur(${q * 12}px)` : undefined };
    case "flip":
      return { opacity: clamp01(p * 2), transform: `perspective(1600px) rotateX(${q * 75}deg) translateY(${q * 80}px)`, transformOrigin: "50% 100%" };
    case "flipY":
      return { opacity: clamp01(p * 2), transform: `perspective(1600px) rotateY(${q * -80}deg)`, transformOrigin: "0% 50%" };
    case "swing":
      return { opacity: clamp01(p * 2), transform: `perspective(1400px) rotateZ(${q * -9}deg) translateY(${q * 120}px)`, transformOrigin: "0% 100%" };
    case "unfold":
      return { opacity: clamp01(p * 3), clipPath: `inset(${q * 50}% 0 ${q * 50}% 0 round 24px)` };
    case "wipe":
      return { clipPath: `inset(0 ${q * 100}% 0 0)` };
    case "iris":
      return { clipPath: `circle(${p * 75}% at 50% 50%)` };
    case "glitch": {
      if (p >= 1) return {};
      const j = Math.sin(frame * 7.3) * 30 * q;
      return { opacity: frame % 3 === 0 ? 0.4 : 1, transform: `translateX(${j}px) skewX(${q * 12}deg)`, filter: `hue-rotate(${q * 90}deg) saturate(${1 + q * 2})` };
    }
    default:
      return { opacity: p };
  }
};

/** Exit = entrance reversed with a gentler set of defaults */
export const exitLook = (kind: string, p: number, frame = 0): React.CSSProperties => {
  // p: 0 visible .. 1 gone
  switch (kind) {
    case "sink":
      return { opacity: 1 - p, transform: `translateY(${p * 60}px)`, filter: `blur(${p * 12}px)` };
    case "lift":
      return { opacity: 1 - p, transform: `translateY(${-p * 80}px)`, filter: `blur(${p * 12}px)` };
    case "zoomOut":
      return { opacity: 1 - p, transform: `scale(${1 + p * 0.25})`, filter: `blur(${p * 18}px)` };
    case "shrink":
      return { opacity: 1 - p, transform: `scale(${1 - p * 0.2})`, filter: `blur(${p * 10}px)` };
    case "cut":
      return { opacity: p > 0 ? 0 : 1 };
    default:
      return enterLook(kind, 1 - p, frame);
  }
};

export const mergeLooks = (...looks: React.CSSProperties[]): React.CSSProperties => {
  const out: React.CSSProperties = {};
  const transforms: string[] = [];
  const filters: string[] = [];
  let opacity = 1;
  for (const l of looks) {
    if (!l) continue;
    for (const [k, v] of Object.entries(l)) {
      if (v === undefined) continue;
      if (k === "transform") transforms.push(v as string);
      else if (k === "filter") filters.push(v as string);
      else if (k === "opacity") opacity *= v as number;
      else (out as Record<string, unknown>)[k] = v;
    }
  }
  if (transforms.length) out.transform = transforms.join(" ");
  if (filters.length) out.filter = filters.join(" ");
  out.opacity = opacity;
  return out;
};

/** Number formatting used by counters: 1200 -> "1,2k", 10000 -> "10 000" */
export const fmtNumber = (v: number, format: "int" | "space" | "k" | "dec1" | "pct" = "space", locale = "ru") => {
  const sep = locale === "ru" ? " " : ",";
  const dec = locale === "ru" ? "," : ".";
  if (format === "k") {
    if (v >= 1000) {
      const k = v / 1000;
      const s = k >= 10 ? Math.round(k).toString() : (Math.round(k * 10) / 10).toString().replace(".", dec);
      return s + "k";
    }
    return Math.round(v).toString();
  }
  if (format === "dec1") return (Math.round(v * 10) / 10).toFixed(1).replace(".", dec);
  if (format === "pct") return `${Math.round(v)}%`;
  const n = Math.round(v).toString();
  if (format === "int") return n;
  return n.replace(/\B(?=(\d{3})+(?!\d))/g, sep);
};

export const interp = (f: number, input: number[], output: number[], ease: (t: number) => number = E.out) =>
  interpolate(f, input, output, { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: ease });
