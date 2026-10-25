import React from "react";
import { AbsoluteFill } from "remotion";
import { E, clamp01, lerp } from "../core/motion";
import { H, W } from "../core/layout";

/**
 * Scene transitions. Each one gives the look of the INCOMING scene (enter, p 0→1)
 * and the OUTGOING scene (exit, p 0→1), plus an optional overlay drawn on top at the cut.
 * The cut happens at p = 0.5.
 */
export type Trans = {
  dur: number; // default seconds
  sfx: string | null; // default sound id (its peak lands on the cut)
  enter: (p: number) => React.CSSProperties;
  exit: (p: number) => React.CSSProperties;
  overlay?: React.FC<{ p: number; color?: string }>;
  /** z-order: incoming on top (default) */
  incomingOnTop?: boolean;
};

const Flash: React.FC<{ p: number; color?: string }> = ({ p, color = "#F1E4D1" }) => {
  const a = Math.max(0, 1 - Math.abs(p - 0.5) / 0.5) ** 2.2;
  return <AbsoluteFill style={{ background: color, opacity: a }} />;
};

const Fog: React.FC<{ p: number; color?: string }> = ({ p, color = "#EDE6DA" }) => {
  const a = Math.max(0, 1 - Math.abs(p - 0.5) / 0.5);
  const blobs = [
    [0.2, 0.3, 0.9], [0.75, 0.25, 0.8], [0.5, 0.6, 1.1], [0.15, 0.85, 0.8], [0.85, 0.8, 0.9], [0.45, 0.15, 0.7],
  ];
  return (
    <AbsoluteFill style={{ opacity: Math.min(1, a * 1.3) }}>
      {blobs.map(([x, y, s], i) => {
        const drift = (p - 0.5) * (i % 2 ? 260 : -260);
        const r = 900 * s * lerp(0.6, 1.2, a);
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: x * W - r / 2 + drift,
              top: y * H - r / 2,
              width: r,
              height: r,
              borderRadius: "50%",
              background: `radial-gradient(circle, ${color} 0%, ${color}ee 35%, ${color}00 70%)`,
              filter: "blur(30px)",
            }}
          />
        );
      })}
      <AbsoluteFill style={{ background: color, opacity: Math.max(0, a - 0.55) * 2 }} />
    </AbsoluteFill>
  );
};

const Dip: React.FC<{ p: number; color?: string }> = ({ p, color = "#000" }) => {
  const a = clamp01(1 - Math.abs(p - 0.5) / 0.35);
  return <AbsoluteFill style={{ background: color, opacity: a }} />;
};

const Glitch: React.FC<{ p: number }> = ({ p }) => {
  const a = Math.max(0, 1 - Math.abs(p - 0.5) / 0.5);
  if (a <= 0) return null;
  const bars = Array.from({ length: 9 }, (_, i) => {
    const y = ((Math.sin(i * 91.7 + p * 40) + 1) / 2) * H;
    const h = 8 + ((Math.sin(i * 13.1 + p * 70) + 1) / 2) * 90;
    return { y, h, x: Math.sin(i * 7 + p * 90) * 80 * a, c: i % 3 === 0 ? "#ff2bd6" : i % 3 === 1 ? "#21f0ff" : "#ffffff" };
  });
  return (
    <AbsoluteFill style={{ mixBlendMode: "screen", opacity: a }}>
      {bars.map((b, i) => (
        <div key={i} style={{ position: "absolute", left: b.x, top: b.y, width: W, height: b.h, background: b.c, opacity: 0.35 }} />
      ))}
    </AbsoluteFill>
  );
};

const ease = E.inOut;

export const TRANSITIONS: Record<string, Trans> = {
  cut: { dur: 0, sfx: null, enter: () => ({}), exit: () => ({}) },
  hardcut: { dur: 0.02, sfx: "hit-punch", enter: () => ({}), exit: () => ({}) },
  fade: { dur: 0.4, sfx: null, enter: (p) => ({ opacity: p }), exit: () => ({}) },
  blur: {
    dur: 0.5,
    sfx: "whoosh-airy",
    enter: (p) => ({ opacity: E.out(p), filter: p < 1 ? `blur(${(1 - p) * 34}px)` : undefined, transform: `scale(${lerp(1.06, 1, E.out(p))})` }),
    exit: (p) => ({ filter: p > 0 ? `blur(${p * 34}px)` : undefined, transform: `scale(${lerp(1, 0.97, p)})` }),
  },
  zoom: {
    dur: 0.55,
    sfx: "zoom-in",
    enter: (p) => ({ opacity: clamp01(p * 2 - 0.4), transform: `scale(${lerp(0.7, 1, E.outExpo(p))})`, filter: p < 1 ? `blur(${(1 - p) * 26}px)` : undefined }),
    exit: (p) => ({ opacity: 1 - clamp01(p * 1.6 - 0.4), transform: `scale(${lerp(1, 2.2, E.in(p))})`, filter: p > 0 ? `blur(${p * 30}px)` : undefined }),
  },
  zoomOut: {
    dur: 0.55,
    sfx: "zoom-out",
    enter: (p) => ({ opacity: clamp01(p * 2 - 0.4), transform: `scale(${lerp(1.6, 1, E.outExpo(p))})`, filter: p < 1 ? `blur(${(1 - p) * 26}px)` : undefined }),
    exit: (p) => ({ opacity: 1 - clamp01(p * 1.6 - 0.4), transform: `scale(${lerp(1, 0.6, E.in(p))})`, filter: p > 0 ? `blur(${p * 24}px)` : undefined }),
  },
  push: {
    dur: 0.5,
    sfx: "swipe-up",
    enter: (p) => ({ transform: `translateY(${(1 - ease(p)) * H}px)`, filter: p > 0.05 && p < 0.95 ? `blur(${Math.sin(p * Math.PI) * 10}px)` : undefined }),
    exit: (p) => ({ transform: `translateY(${-ease(p) * H * 0.35}px) scale(${lerp(1, 0.92, ease(p))})`, filter: `brightness(${lerp(1, 0.55, ease(p))})` }),
  },
  pushDown: {
    dur: 0.5,
    sfx: "swipe-down",
    enter: (p) => ({ transform: `translateY(${-(1 - ease(p)) * H}px)` }),
    exit: (p) => ({ transform: `translateY(${ease(p) * H * 0.35}px) scale(${lerp(1, 0.92, ease(p))})`, filter: `brightness(${lerp(1, 0.55, ease(p))})` }),
  },
  pushLeft: {
    dur: 0.45,
    sfx: "whoosh-pan-rl",
    enter: (p) => ({ transform: `translateX(${(1 - ease(p)) * W}px)`, filter: p < 0.95 ? `blur(${Math.sin(p * Math.PI) * 14}px)` : undefined }),
    exit: (p) => ({ transform: `translateX(${-ease(p) * W}px)`, filter: p > 0.05 ? `blur(${Math.sin(p * Math.PI) * 14}px)` : undefined }),
  },
  pushRight: {
    dur: 0.45,
    sfx: "whoosh-pan-lr",
    enter: (p) => ({ transform: `translateX(${-(1 - ease(p)) * W}px)`, filter: p < 0.95 ? `blur(${Math.sin(p * Math.PI) * 14}px)` : undefined }),
    exit: (p) => ({ transform: `translateX(${ease(p) * W}px)`, filter: p > 0.05 ? `blur(${Math.sin(p * Math.PI) * 14}px)` : undefined }),
  },
  whip: {
    dur: 0.3,
    sfx: "whoosh-short",
    enter: (p) => ({ opacity: p > 0.5 ? 1 : 0, transform: `translateX(${(1 - E.outExpo(p)) * 600}px) scaleX(${1 + Math.sin(p * Math.PI) * 0.3})`, filter: `blur(${Math.sin(p * Math.PI) * 40}px)` }),
    exit: (p) => ({ transform: `translateX(${-E.in(p) * 600}px) scaleX(${1 + Math.sin(p * Math.PI) * 0.3})`, filter: `blur(${Math.sin(p * Math.PI) * 40}px)` }),
  },
  stack: {
    dur: 0.6,
    sfx: "card-slide",
    enter: (p) => ({ transform: `translateY(${(1 - E.outExpo(p)) * H}px)`, borderRadius: lerp(60, 0, p), overflow: "hidden", boxShadow: "0 -40px 120px rgba(0,0,0,0.35)" }),
    exit: (p) => ({ transform: `scale(${lerp(1, 0.88, E.out(p))})`, filter: `brightness(${lerp(1, 0.4, p)}) blur(${p * 6}px)`, borderRadius: lerp(0, 60, p) }),
  },
  iris: {
    dur: 0.55,
    sfx: "whoosh-up",
    enter: (p) => ({ clipPath: `circle(${E.inOut(p) * 120}% at 50% 50%)` }),
    exit: (p) => ({ transform: `scale(${lerp(1, 1.12, p)})` }),
  },
  wipe: {
    dur: 0.5,
    sfx: "swipe-soft",
    enter: (p) => {
      const x = E.inOut(p) * 140 - 20;
      return { WebkitMaskImage: `linear-gradient(100deg, #000 ${x - 20}%, transparent ${x}%)`, maskImage: `linear-gradient(100deg, #000 ${x - 20}%, transparent ${x}%)` };
    },
    exit: () => ({}),
  },
  flash: {
    dur: 0.35,
    sfx: "hit-soft",
    enter: (p) => ({ opacity: p >= 0.5 ? 1 : 0 }),
    exit: (p) => ({ opacity: p < 0.5 ? 1 : 0 }),
    overlay: Flash,
  },
  dip: {
    dur: 0.6,
    sfx: null,
    enter: (p) => ({ opacity: p >= 0.5 ? 1 : 0 }),
    exit: (p) => ({ opacity: p < 0.5 ? 1 : 0 }),
    overlay: Dip,
  },
  cloud: {
    dur: 1.0,
    sfx: "whoosh-cloud",
    enter: (p) => ({ opacity: clamp01((p - 0.35) / 0.3), transform: `scale(${lerp(1.12, 1, E.out(clamp01((p - 0.3) / 0.7)))})` }),
    exit: (p) => ({ transform: `scale(${lerp(1, 1.18, E.in(p))})`, filter: p > 0 ? `blur(${p * 12}px)` : undefined }),
    overlay: Fog,
  },
  glitch: {
    dur: 0.3,
    sfx: "trans-glitch-cut",
    enter: (p) => ({ opacity: p >= 0.5 ? 1 : 0, transform: `translateX(${Math.sin(p * 60) * 30 * (1 - p)}px)`, filter: `hue-rotate(${(1 - p) * 120}deg) contrast(${1 + (1 - p)})` }),
    exit: (p) => ({ opacity: p < 0.5 ? 1 : 0, transform: `translateX(${Math.sin(p * 50) * 30 * p}px) skewX(${p * 8}deg)` }),
    overlay: Glitch,
  },
  slam: {
    dur: 0.25,
    sfx: "hit-punch",
    enter: (p) => ({ opacity: p >= 0.5 ? 1 : 0, transform: `scale(${lerp(1.35, 1, E.outExpo(clamp01((p - 0.5) * 2)))})`, filter: p < 0.9 ? `blur(${(1 - p) * 20}px)` : undefined }),
    exit: (p) => ({ opacity: p < 0.5 ? 1 : 0, transform: `scale(${lerp(1, 0.85, p)})` }),
    overlay: ({ p, color }) => <Flash p={p * 0.85} color={color ?? "#F1E4D1"} />,
  },
};

export const getTransition = (id?: string): Trans => TRANSITIONS[id ?? "blur"] ?? TRANSITIONS.blur;
