import React from "react";
import { AbsoluteFill, Img, OffthreadVideo, random, staticFile } from "remotion";
import { useBlockTime, useTheme } from "../core/context";
import { E, clamp01, lerp, wiggle } from "../core/motion";
import { H, W } from "../core/layout";
import { defineBlock, type BlockDef } from "./registry";

export const asset = (p?: string) => (!p ? "" : /^https?:|^data:/.test(p) ? p : staticFile(p));

// ------------------------------------------------------------------ Solid
const Solid: React.FC<{ color?: string }> = ({ color }) => {
  const th = useTheme();
  return <AbsoluteFill style={{ background: color ?? th.bg }} />;
};

// ------------------------------------------------------------------ MeshGradient
const MeshGradient: React.FC<{ palette?: string[]; speed?: number; base?: string; intensity?: number }> = ({ palette, speed = 1, base, intensity = 1 }) => {
  const { f } = useBlockTime();
  const th = useTheme();
  const pal = palette ?? (th.bgProps?.palette as string[]) ?? ["#F4F3FB", "#E6E8FF", "#F1E9FF", "#E9F2FF", "#FFFFFF"];
  const blobs = [
    { x: 0.15, y: 0.18, r: 1.0, c: pal[1] },
    { x: 0.85, y: 0.32, r: 0.9, c: pal[2] },
    { x: 0.3, y: 0.72, r: 1.1, c: pal[3] },
    { x: 0.8, y: 0.88, r: 0.8, c: pal[1] },
    { x: 0.55, y: 0.45, r: 0.7, c: pal[4] ?? "#fff" },
  ];
  return (
    <AbsoluteFill style={{ background: base ?? pal[0], overflow: "hidden" }}>
      {blobs.map((b, i) => {
        const t = f * 0.004 * speed;
        const x = (b.x + Math.sin(t * (1 + i * 0.3) + i) * 0.08) * W;
        const y = (b.y + Math.cos(t * (0.8 + i * 0.25) + i * 2) * 0.06) * H;
        const r = 1100 * b.r;
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: x - r / 2,
              top: y - r / 2,
              width: r,
              height: r,
              borderRadius: "50%",
              opacity: intensity,
              background: `radial-gradient(circle at 50% 50%, ${b.c} 0%, ${b.c}cc 25%, ${b.c}00 68%)`,
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};

// ------------------------------------------------------------------ Aurora (dark flowing light)
const Aurora: React.FC<{ colors?: string[]; base?: string }> = ({ colors, base }) => {
  const { f } = useBlockTime();
  const th = useTheme();
  const cs = colors ?? [th.accent, th.accent2, "#5B2BFF"];
  return (
    <AbsoluteFill style={{ background: base ?? th.bg, overflow: "hidden" }}>
      {cs.map((c, i) => {
        const t = f * 0.006 + i * 2.1;
        const x = W * (0.5 + Math.sin(t) * 0.35);
        const y = H * (0.3 + i * 0.22 + Math.cos(t * 0.7) * 0.08);
        const r = 1300;
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: x - r / 2,
              top: y - r / 2,
              width: r,
              height: r * 0.55,
              borderRadius: "50%",
              transform: `rotate(${Math.sin(t * 0.5) * 25}deg)`,
              background: `radial-gradient(ellipse at 50% 50%, ${c}66 0%, ${c}22 40%, ${c}00 70%)`,
              mixBlendMode: "screen",
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};

// ------------------------------------------------------------------ Studio (warm spotlight + floor)
const Studio: React.FC<{ tint?: string; floor?: string; spot?: number }> = ({ tint = "#C98A55", floor = "#C9A78A", spot = 1 }) => {
  const { f } = useBlockTime();
  const th = useTheme();
  const breathe = 1 + Math.sin(f * 0.02) * 0.02;
  return (
    <AbsoluteFill style={{ background: th.bg, overflow: "hidden" }}>
      <AbsoluteFill
        style={{
          background: `radial-gradient(ellipse ${60 * breathe}% ${28 * breathe}% at 50% 30%, ${tint}${Math.round(110 * spot).toString(16).padStart(2, "0")} 0%, ${tint}22 45%, transparent 75%)`,
        }}
      />
      <div
        style={{
          position: "absolute",
          left: -200,
          right: -200,
          top: H * 0.52,
          bottom: 0,
          background: `linear-gradient(180deg, transparent 0%, ${floor}55 18%, ${floor}aa 60%, ${floor}cc 100%)`,
          filter: "blur(2px)",
        }}
      />
      <AbsoluteFill style={{ background: "radial-gradient(ellipse 90% 50% at 50% 60%, transparent 40%, rgba(0,0,0,0.55) 100%)" }} />
    </AbsoluteFill>
  );
};

// ------------------------------------------------------------------ Starfield + PlanetHorizon
const Stars: React.FC<{ n?: number; seed?: number; twinkle?: boolean; drift?: number }> = ({ n = 260, seed = 3, twinkle = true, drift = 0.15 }) => {
  const { f } = useBlockTime();
  return (
    <AbsoluteFill>
      {Array.from({ length: n }, (_, i) => {
        const x = random(`sx${seed}${i}`) * W;
        const y = ((random(`sy${seed}${i}`) * H + f * drift * (0.3 + random(`sd${i}`))) % H);
        const s = 0.8 + random(`ss${seed}${i}`) ** 3 * 3.2;
        const a = twinkle ? 0.35 + 0.65 * (0.5 + 0.5 * Math.sin(f * (0.03 + random(`st${i}`) * 0.08) + i)) : 0.8;
        return <div key={i} style={{ position: "absolute", left: x, top: y, width: s, height: s, borderRadius: "50%", background: "#fff", opacity: a * (0.4 + s / 5), boxShadow: s > 2.6 ? "0 0 6px rgba(180,200,255,0.9)" : undefined }} />;
      })}
    </AbsoluteFill>
  );
};

const PlanetHorizon: React.FC<{ glow?: string; rise?: number; base?: string; y?: number }> = ({ glow = "#3B7BFF", rise = 1, base, y = 0.86 }) => {
  const { f, fps } = useBlockTime();
  const th = useTheme();
  const p = E.out(clamp01(f / (1.6 * fps)));
  const R = 2600;
  const cy = H * y + R - lerp(80, 0, p * rise) * 1;
  return (
    <AbsoluteFill style={{ background: base ?? `radial-gradient(ellipse 120% 70% at 50% 100%, #0B1640 0%, ${th.bg} 60%)`, overflow: "hidden" }}>
      <Stars />
      <div style={{ position: "absolute", left: W / 2 - R, top: cy - R, width: R * 2, height: R * 2, borderRadius: "50%", boxShadow: `0 0 160px 40px ${glow}55, 0 0 50px 8px ${glow}aa` }} />
      <div
        style={{
          position: "absolute",
          left: W / 2 - R,
          top: cy - R,
          width: R * 2,
          height: R * 2,
          borderRadius: "50%",
          background: `radial-gradient(circle at 50% 0%, #0A1230 0%, #02040C 40%)`,
          boxShadow: `inset 0 18px 30px -6px ${glow}, inset 0 4px 6px -2px #CFE0FF`,
        }}
      />
      <div style={{ position: "absolute", left: 0, right: 0, top: cy - R - 260, height: 520, background: `radial-gradient(ellipse 60% 50% at 50% 50%, ${glow}33, transparent 70%)` }} />
    </AbsoluteFill>
  );
};

// ------------------------------------------------------------------ Sky with procedural clouds
const Sky: React.FC<{ top?: string; horizon?: string; clouds?: number; speed?: number; seed?: number; dense?: boolean }> = ({
  top = "#2A5AC9", horizon = "#BFD6F6", clouds = 14, speed = 1, seed = 1, dense = false,
}) => {
  const { f } = useBlockTime();
  return (
    <AbsoluteFill style={{ background: `linear-gradient(180deg, ${top} 0%, #4F82DE 38%, ${horizon} 100%)`, overflow: "hidden" }}>
      {Array.from({ length: clouds }, (_, i) => {
        const depth = 0.35 + random(`cd${seed}${i}`) * 0.65;
        const cx = ((random(`cx${seed}${i}`) * 1.6 - 0.3) * W + f * speed * depth * 0.6) % (W * 1.6) - W * 0.3;
        const cy = H * (0.25 + depth * 0.7) + random(`cy${seed}${i}`) * 120;
        const scale = (dense ? 1.4 : 1) * (0.6 + depth * 1.3);
        return <CloudPuff key={i} x={cx} y={cy} scale={scale} seed={seed * 100 + i} opacity={0.75 + depth * 0.25} />;
      })}
    </AbsoluteFill>
  );
};

export const CloudPuff: React.FC<{ x: number; y: number; scale: number; seed: number; opacity?: number }> = ({ x, y, scale, seed, opacity = 1 }) => {
  const puffs = Array.from({ length: 9 }, (_, k) => ({
    dx: (random(`px${seed}${k}`) - 0.5) * 520,
    dy: -Math.abs(random(`py${seed}${k}`) - 0.3) * 160,
    r: 140 + random(`pr${seed}${k}`) * 180,
  }));
  return (
    <div style={{ position: "absolute", left: x, top: y, transform: `scale(${scale})`, opacity }}>
      {puffs.map((p, k) => (
        <div
          key={k}
          style={{
            position: "absolute",
            left: p.dx - p.r,
            top: p.dy - p.r,
            width: p.r * 2,
            height: p.r * 2,
            borderRadius: "50%",
            background: "radial-gradient(circle at 45% 35%, #FFFFFF 0%, #F7FAFF 40%, rgba(214,226,246,0.85) 62%, rgba(214,226,246,0) 72%)",
          }}
        />
      ))}
    </div>
  );
};

// ------------------------------------------------------------------ Paper
const Paper: React.FC<{ color?: string; lines?: boolean }> = ({ color, lines = false }) => {
  const th = useTheme();
  return (
    <AbsoluteFill
      style={{
        background: color ?? th.bg,
        backgroundImage: lines ? `repeating-linear-gradient(180deg, transparent 0 63px, rgba(0,0,0,0.06) 63px 64px)` : undefined,
      }}
    >
      <AbsoluteFill style={{ background: "radial-gradient(ellipse 80% 60% at 50% 40%, rgba(255,255,255,0.5), transparent 70%)" }} />
    </AbsoluteFill>
  );
};

// ------------------------------------------------------------------ Grid (flat or perspective floor)
const GridBG: React.FC<{ color?: string; size?: number; floor?: boolean; speed?: number; base?: string }> = ({ color, size = 80, floor = false, speed = 1, base }) => {
  const { f } = useBlockTime();
  const th = useTheme();
  const c = color ?? (th.dark ? "rgba(255,255,255,0.07)" : "rgba(13,15,28,0.06)");
  if (floor) {
    return (
      <AbsoluteFill style={{ background: base ?? th.bg, overflow: "hidden" }}>
        <div
          style={{
            position: "absolute",
            left: -W,
            width: W * 3,
            top: H * 0.45,
            height: H * 1.2,
            transform: "perspective(600px) rotateX(70deg)",
            transformOrigin: "50% 0%",
            backgroundImage: `linear-gradient(${th.accent}88 2px, transparent 2px), linear-gradient(90deg, ${th.accent}88 2px, transparent 2px)`,
            backgroundSize: `${size * 1.5}px ${size * 1.5}px`,
            backgroundPosition: `0 ${(f * 3 * speed) % (size * 1.5)}px`,
            WebkitMaskImage: "linear-gradient(180deg, transparent 0%, #000 30%)",
          }}
        />
        <div style={{ position: "absolute", left: 0, right: 0, top: H * 0.38, height: 300, background: `radial-gradient(ellipse 60% 50% at 50% 70%, ${th.accent}55, transparent 70%)` }} />
      </AbsoluteFill>
    );
  }
  return (
    <AbsoluteFill
      style={{
        background: base ?? th.bg,
        backgroundImage: `linear-gradient(${c} 1px, transparent 1px), linear-gradient(90deg, ${c} 1px, transparent 1px)`,
        backgroundSize: `${size}px ${size}px`,
        backgroundPosition: `${(f * 0.3 * speed) % size}px ${(f * 0.5 * speed) % size}px`,
        WebkitMaskImage: "radial-gradient(ellipse 80% 70% at 50% 45%, #000 40%, transparent 100%)",
      }}
    />
  );
};

// ------------------------------------------------------------------ Photo with Ken Burns + legibility gradient
const PhotoBG: React.FC<{
  src: string; zoom?: [number, number]; pan?: [number, number, number, number]; blur?: number; darken?: number;
  topShade?: number; tint?: string; focus?: string;
}> = ({ src, zoom = [1.04, 1.16], pan = [0, 0, 0, -40], blur = 0, darken = 0, topShade = 0.25, tint, focus = "50% 50%" }) => {
  const { f, dur } = useBlockTime();
  const t = clamp01(f / Math.max(1, dur));
  const s = lerp(zoom[0], zoom[1], t);
  return (
    <AbsoluteFill style={{ overflow: "hidden", background: "#000" }}>
      <Img
        src={asset(src)}
        style={{
          position: "absolute",
          inset: 0,
          width: "100%",
          height: "100%",
          objectFit: "cover",
          objectPosition: focus,
          transform: `translate(${lerp(pan[0], pan[2], t)}px, ${lerp(pan[1], pan[3], t)}px) scale(${s})`,
          filter: blur ? `blur(${blur}px)` : undefined,
        }}
      />
      {tint ? <AbsoluteFill style={{ background: tint, mixBlendMode: "multiply" }} /> : null}
      {darken ? <AbsoluteFill style={{ background: `rgba(0,0,0,${darken})` }} /> : null}
      {topShade ? <AbsoluteFill style={{ background: `linear-gradient(180deg, rgba(0,0,0,${topShade}) 0%, transparent 40%)` }} /> : null}
    </AbsoluteFill>
  );
};

// ------------------------------------------------------------------ Video background
const VideoBG: React.FC<{ src: string; startFrom?: number; rate?: number; zoom?: [number, number]; darken?: number; blur?: number; focus?: string }> = ({
  src, startFrom = 0, rate = 1, zoom = [1, 1.06], darken = 0, blur = 0, focus = "50% 50%",
}) => {
  const { f, dur, fps } = useBlockTime();
  const t = clamp01(f / Math.max(1, dur));
  return (
    <AbsoluteFill style={{ overflow: "hidden", background: "#000" }}>
      <OffthreadVideo
        src={asset(src)}
        muted
        playbackRate={rate}
        trimBefore={Math.round(startFrom * fps)}
        style={{ width: "100%", height: "100%", objectFit: "cover", objectPosition: focus, transform: `scale(${lerp(zoom[0], zoom[1], t)})`, filter: blur ? `blur(${blur}px)` : undefined }}
      />
      {darken ? <AbsoluteFill style={{ background: `rgba(0,0,0,${darken})` }} /> : null}
    </AbsoluteFill>
  );
};

// ------------------------------------------------------------------ Footage in the upper part, fading into black (screen-recording layout)
const FootageTop: React.FC<{ src: string; video?: boolean; height?: number; zoom?: [number, number]; pan?: [number, number, number, number]; startFrom?: number; focus?: string }> = ({
  src, video, height = 0.62, zoom = [1.0, 1.08], pan = [0, 0, 0, 0], startFrom = 0, focus = "50% 50%",
}) => {
  const { f, dur, fps } = useBlockTime();
  const th = useTheme();
  const t = clamp01(f / Math.max(1, dur));
  const h = H * height;
  const st: React.CSSProperties = {
    width: "100%",
    height: "100%",
    objectFit: "cover",
    objectPosition: focus,
    transform: `translate(${lerp(pan[0], pan[2], t)}px, ${lerp(pan[1], pan[3], t)}px) scale(${lerp(zoom[0], zoom[1], t)})`,
  };
  const isVid = video ?? /\.(mp4|mov|webm)$/i.test(src);
  return (
    <AbsoluteFill style={{ background: th.bg }}>
      <div style={{ position: "absolute", left: 0, top: 0, width: W, height: h, overflow: "hidden", WebkitMaskImage: "linear-gradient(180deg, #000 70%, transparent 100%)" }}>
        {isVid ? <OffthreadVideo src={asset(src)} muted trimBefore={Math.round(startFrom * fps)} style={st} /> : <Img src={asset(src)} style={st} />}
      </div>
    </AbsoluteFill>
  );
};

// ------------------------------------------------------------------ Spotlight sweep (light leak accent for dark themes)
const LightSweep: React.FC<{ color?: string; base?: string }> = ({ color, base }) => {
  const { f, fps } = useBlockTime();
  const th = useTheme();
  const x = ((f / (4 * fps)) % 1) * 1.6 - 0.3;
  return (
    <AbsoluteFill style={{ background: base ?? th.bg, overflow: "hidden" }}>
      <div style={{ position: "absolute", top: -400, left: x * W - 400, width: 800, height: H + 800, transform: "rotate(18deg)", background: `linear-gradient(90deg, transparent, ${color ?? th.accent}22, transparent)` }} />
      <AbsoluteFill style={{ background: `radial-gradient(ellipse 70% 40% at 50% 35%, ${color ?? th.accent}18, transparent 70%)` }} />
    </AbsoluteFill>
  );
};

// ------------------------------------------------------------------ Gradient split (two-tone diagonal, editorial)
const DuoTone: React.FC<{ a?: string; b?: string; angle?: number; move?: boolean }> = ({ a, b, angle = 160, move = true }) => {
  const { f } = useBlockTime();
  const th = useTheme();
  const shift = move ? wiggle(f, 0.01, 4) * 6 : 0;
  return <AbsoluteFill style={{ background: `linear-gradient(${angle + shift}deg, ${a ?? th.bg} 0%, ${b ?? th.accent2} 140%)` }} />;
};

// ------------------------------------------------------------------ WarmGlow (default for ember/blaze): dark warm base + slow amber light
const WarmGlow: React.FC<{ intensity?: number; color?: string; base?: string; floor?: boolean }> = ({ intensity = 1, color, base, floor = true }) => {
  const { f } = useBlockTime();
  const th = useTheme();
  const c = color ?? th.accent;
  const x = 50 + Math.sin(f * 0.006) * 10;
  const y = 26 + Math.cos(f * 0.005) * 5;
  const a = (v: number) => Math.round(Math.min(255, v * intensity)).toString(16).padStart(2, "0");
  return (
    <AbsoluteFill style={{ background: base ?? th.bg, overflow: "hidden" }}>
      <AbsoluteFill style={{ background: `radial-gradient(ellipse 85% 42% at ${x}% ${y}%, ${c}${a(70)} 0%, ${c}${a(26)} 38%, transparent 72%)` }} />
      <AbsoluteFill style={{ background: `radial-gradient(ellipse 70% 40% at ${100 - x}% 92%, #E7C79B${a(22)} 0%, transparent 70%)` }} />
      {floor ? <div style={{ position: "absolute", left: 0, right: 0, top: H * 0.62, bottom: 0, background: "linear-gradient(180deg, transparent, rgba(0,0,0,0.35))" }} /> : null}
    </AbsoluteFill>
  );
};

export const BG_BLOCKS: Record<string, BlockDef> = {
  WarmGlow: defineBlock({ C: WarmGlow, cat: "bg", desc: "Default for ember/blaze: near-black warm base with a slow drifting amber glow.", self: true, pos: "full", example: {} }),
  Solid: defineBlock({ C: Solid, cat: "bg", desc: "Flat colour (theme bg by default).", self: true, pos: "full", example: {} }),
  MeshGradient: defineBlock({ C: MeshGradient, cat: "bg", desc: "Soft drifting pastel blobs. Light explainers (cloud/pop).", self: true, pos: "full", example: {} }),
  Aurora: defineBlock({ C: Aurora, cat: "bg", desc: "Dark base with flowing coloured light. Neon/tech.", self: true, pos: "full", example: { base: "#0B0614" } }),
  Studio: defineBlock({ C: Studio, cat: "bg", desc: "Warm spotlight + floor. Hero shots of devices (pair with Laptop3D).", self: true, pos: "full", example: {} }),
  Stars: defineBlock({ C: Stars, cat: "bg", desc: "Twinkling starfield (transparent).", self: true, pos: "full", example: {} }),
  PlanetHorizon: defineBlock({ C: PlanetHorizon, cat: "bg", desc: "Night sky + glowing planet rim. Big questions / mission lines.", self: true, pos: "full", example: {} }),
  Sky: defineBlock({ C: Sky, cat: "bg", desc: "Blue sky with drifting procedural clouds. Calm, optimistic.", self: true, pos: "full", example: {} }),
  Paper: defineBlock({ C: Paper, cat: "bg", desc: "Warm paper. Editorial / magazine.", self: true, pos: "full", example: {} }),
  GridBG: defineBlock({ C: GridBG, cat: "bg", desc: "Faint grid, or `floor:true` synthwave perspective floor.", self: true, pos: "full", example: { floor: true } }),
  PhotoBG: defineBlock({ C: PhotoBG, cat: "bg", desc: "Photo with Ken Burns zoom/pan, optional darken/blur/top shade.", self: true, pos: "full" }),
  VideoBG: defineBlock({ C: VideoBG, cat: "bg", desc: "Muted video background with slow zoom.", self: true, pos: "full" }),
  FootageTop: defineBlock({ C: FootageTop, cat: "bg", desc: "Screen recording/photo in the top 60%, fading to black (subtitles below).", self: true, pos: "full" }),
  LightSweep: defineBlock({ C: LightSweep, cat: "bg", desc: "Dark bg with a slow diagonal light sweep.", self: true, pos: "full", example: {} }),
  DuoTone: defineBlock({ C: DuoTone, cat: "bg", desc: "Two-tone diagonal gradient.", self: true, pos: "full", example: {} }),
};
