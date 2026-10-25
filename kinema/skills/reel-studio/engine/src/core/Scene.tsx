import React from "react";
import { AbsoluteFill, Sequence, useCurrentFrame, useVideoConfig } from "remotion";
import { REGISTRY } from "../blocks";
import { BlockTimeProvider, SceneCapProvider, ThemeScope, useReel } from "./context";
import { Layer } from "./Layer";
import { E, clamp01, lerp, shake, wiggle } from "./motion";
import type { ScenePlan } from "./plan";
import { resolve } from "./timing";
import type { CameraSpec } from "./types";

export type CameraState = { scale: number; x: number; y: number; rx: number; ry: number; rz: number; blur: number };

export const cameraAt = (cam: CameraSpec, f: number, len: number, fps: number, energy: number, hits: number[]): CameraState => {
  const t = clamp01(f / Math.max(1, len));
  const a = cam.amount ?? 1;
  const s: CameraState = { scale: 1, x: 0, y: 0, rx: 0, ry: 0, rz: 0, blur: 0 };
  const smooth = E.inOut(t);
  switch (cam.move) {
    case "push":
      s.scale = lerp(1, 1 + 0.07 * a, smooth);
      break;
    case "pull":
      s.scale = lerp(1 + 0.08 * a, 1, smooth);
      break;
    case "pushFast":
      s.scale = lerp(1, 1 + 0.16 * a, E.out(t));
      break;
    case "drift":
      s.x = wiggle(f, 0.012, 3) * 26 * a;
      s.y = wiggle(f, 0.01, 7) * 20 * a;
      s.scale = 1.04 + 0.02 * a * smooth;
      break;
    case "panUp":
      s.y = lerp(50, -50, smooth) * a;
      s.scale = 1.06;
      break;
    case "panDown":
      s.y = lerp(-50, 50, smooth) * a;
      s.scale = 1.06;
      break;
    case "panLeft":
      s.x = lerp(40, -40, smooth) * a;
      s.scale = 1.06;
      break;
    case "panRight":
      s.x = lerp(-40, 40, smooth) * a;
      s.scale = 1.06;
      break;
    case "tilt":
      s.rx = lerp(7, 0, E.out(t)) * a;
      s.scale = lerp(1.06, 1, E.out(t));
      break;
    case "orbit":
      s.ry = lerp(-6, 6, smooth) * a;
      s.rx = 3 * a;
      s.scale = 1.05;
      break;
    case "punch": {
      // aggressive: micro zoom bumps on caption hits + drift
      let bump = 0;
      for (const h of hits) {
        const d = f - h;
        if (d >= 0 && d < 30) bump += Math.exp(-d / 7) * 0.045 * energy;
      }
      s.scale = 1.02 + bump + 0.03 * smooth;
      s.rz = wiggle(f, 0.02, 2) * 0.35 * energy;
      break;
    }
    case "still":
    default:
      break;
  }
  if (cam.focusFrom) s.blur = cam.focusFrom * (1 - E.out(clamp01(f / (0.8 * fps))));
  const sh = shake(f, hits.filter((h) => h <= f), 10 * energy, 9);
  s.x += sh.x;
  s.y += sh.y;
  s.rz += sh.r;
  return s;
};

export const camTransform = (c: CameraState, depth = 1) =>
  `perspective(2400px) translate(${c.x * depth}px, ${c.y * depth}px) scale(${1 + (c.scale - 1) * depth}) rotateX(${c.rx * depth}deg) rotateY(${c.ry * depth}deg) rotateZ(${c.rz * depth}deg)`;

/** soft gradient from the theme background behind the caption band (busy 3D / photo / video backgrounds) */
const CaptionScrim: React.FC<{ pos: string; color: string; strength: number }> = ({ pos, color, strength }) => {
  const a = Math.round(Math.min(1, strength) * 235).toString(16).padStart(2, "0");
  const b = Math.round(Math.min(1, strength) * 120).toString(16).padStart(2, "0");
  const top = pos === "top" || pos === "upper";
  const bottom = pos === "lower" || pos === "bottom";
  const bg = top
    ? `linear-gradient(180deg, ${color}${a} 0%, ${color}${b} 28%, ${color}00 42%)`
    : bottom
      ? `linear-gradient(0deg, ${color}${a} 0%, ${color}${b} 30%, ${color}00 48%)`
      : `radial-gradient(ellipse 90% 22% at 50% 50%, ${color}${a} 0%, ${color}00 100%)`;
  return <AbsoluteFill style={{ background: bg, pointerEvents: "none" }} />;
};

const SceneInner: React.FC<{ plan: ScenePlan; renderFrom: number; hitsAbs: number[] }> = ({ plan, renderFrom, hitsAbs }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const { transcript, beats, total } = useReel();
  const theme = plan.theme;
  const absFrame = f + renderFrom;
  const startF = Math.round(plan.startSec * fps);
  const endF = Math.round(plan.endSec * fps);
  const tinF = Math.round(plan.tIn.dur * fps);
  const toutF = Math.round(plan.tOut.dur * fps);

  // transitions
  let look: React.CSSProperties = {};
  let overlay: React.ReactNode = null;
  if (tinF > 0 && absFrame < startF + tinF / 2) {
    const p = clamp01((absFrame - (startF - tinF / 2)) / tinF);
    look = plan.tIn.t.enter(p);
    if (plan.tIn.t.overlay) {
      const O = plan.tIn.t.overlay;
      // overlay colours come from the palette — never pure white
      const oc = plan.tIn.id === "slam" ? theme.accent : plan.tIn.id === "dip" ? theme.bg : plan.tIn.id === "cloud" ? (theme.dark ? theme.card : "#EDE6DA") : theme.dark ? theme.ink : theme.card;
      overlay = <O p={p} color={oc} />;
    }
  } else if (toutF > 0 && absFrame > endF - toutF / 2) {
    const p = clamp01((absFrame - (endF - toutF / 2)) / toutF);
    look = plan.tOut.t.exit(p);
  }

  // camera
  const camSpec: CameraSpec =
    typeof plan.spec.camera === "string" ? { move: plan.spec.camera } : plan.spec.camera ?? { move: theme.motion.camera };
  const shakeHits = (camSpec.shakeAt ?? []).map((a) => {
    try {
      return Math.round(resolve(a, { transcript, beats, total, from: plan.startSec, base: plan.startSec }) * fps) - renderFrom;
    } catch {
      return -999;
    }
  });
  const localHits = camSpec.move === "punch" ? hitsAbs.map((h) => h - renderFrom) : [];
  const cam = cameraAt(camSpec, f, Math.max(1, endF - renderFrom), fps, theme.motion.energy, [...shakeHits, ...localHits]);

  const bgDef = REGISTRY[plan.bg.block];
  const Bg = bgDef?.C;
  const lenF = Math.round((plan.endSec + plan.tOut.dur / 2) * fps) - renderFrom;
  // timing props inside the background (screens on MacBook/iPhone/Room3D monitors: line "at", pressAt, item "at"…)
  // resolve like layer props: anchors to words, plain numbers = seconds after the scene start; frames relative to f
  const bgAt = (a: unknown, fb?: number) => {
    if (a === undefined || a === null) return Math.round((fb ?? 0) * fps);
    try {
      const s = resolve(a as never, { transcript, beats, total, from: plan.startSec, base: plan.startSec, end: plan.endSec }, fb);
      return Math.round(s * fps) - renderFrom;
    } catch {
      return Math.round((fb ?? 0) * fps);
    }
  };

  return (
    <ThemeScope theme={theme}>
      <AbsoluteFill style={{ ...look, overflow: "hidden" }}>
        <AbsoluteFill style={{ transform: camTransform(cam, plan.bg.depth ?? 0.6), filter: cam.blur > 0.2 ? `blur(${cam.blur}px)` : undefined }}>
          {Bg ? (
            <BlockTimeProvider value={{ f, dur: lenF, fps, at: bgAt, left: lenF - f }}>
              <AbsoluteFill>
                <Bg {...(plan.bg.props ?? {})} />
              </AbsoluteFill>
            </BlockTimeProvider>
          ) : null}
        </AbsoluteFill>
        {plan.bg.dim ? (
          <AbsoluteFill style={{ background: `radial-gradient(ellipse at 50% 62%, ${theme.bg}99 0%, ${theme.bg} 78%)`, opacity: plan.bg.dim * E.inOut(clamp01((f - bgAt(plan.bg.dimAt)) / (0.7 * fps))), pointerEvents: "none" }} />
        ) : null}
        {plan.scrim ? <CaptionScrim pos={plan.capPos} color={theme.bg} strength={plan.scrim} /> : null}
        <AbsoluteFill style={{ transform: camTransform(cam, 1), filter: cam.blur > 0.2 ? `blur(${cam.blur * 0.7}px)` : undefined }}>
          <SceneCapProvider value={{ pos: plan.capPos, hidden: plan.capHidden }}>
            {plan.layers.map((lp, k) => (
              <Layer key={k} spec={lp.spec} timing={lp} sceneStartSec={renderFrom / fps} sceneEndSec={plan.endSec} />
            ))}
          </SceneCapProvider>
        </AbsoluteFill>
      </AbsoluteFill>
      {overlay}
    </ThemeScope>
  );
};

export const SceneView: React.FC<{ plan: ScenePlan; hitsAbs: number[] }> = ({ plan, hitsAbs }) => {
  const { fps } = useVideoConfig();
  const from = Math.max(0, Math.round((plan.startSec - plan.tIn.dur / 2) * fps));
  const to = Math.round((plan.endSec + plan.tOut.dur / 2) * fps);
  return (
    <Sequence from={from} durationInFrames={Math.max(1, to - from)} name={`scene ${plan.spec.id ?? plan.i}`}>
      <SceneInner plan={plan} renderFrom={from} hitsAbs={hitsAbs} />
    </Sequence>
  );
};
