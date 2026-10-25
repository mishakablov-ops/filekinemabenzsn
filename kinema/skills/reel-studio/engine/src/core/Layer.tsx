import React from "react";
import { Sequence, useCurrentFrame, useVideoConfig } from "remotion";
import { REGISTRY } from "../blocks";
import { BlockTimeProvider, useReel, useSceneCap } from "./context";
import { resolveBox, stageFor } from "./layout";
import { E, SPR, clamp01, enterLook, exitLook, mergeLooks, springAt } from "./motion";
import { resolve } from "./timing";
import type { LayerSpec } from "./types";

export const ENTER_DUR: Record<string, number> = {
  rise: 0.6, riseBig: 0.75, fade: 0.45, blur: 0.55, drop: 0.5, pop: 0.5, slam: 0.35, zoom: 0.6, slideL: 0.55, slideR: 0.55,
  slideUp: 0.7, slideDown: 0.7, flip: 0.7, flipY: 0.7, swing: 0.7, unfold: 0.55, wipe: 0.6, iris: 0.7, glitch: 0.35, stretch: 0.45, none: 0,
};

export type LayerTiming = { startSec: number; endSec: number };

const LayerInner: React.FC<{ spec: LayerSpec; timing: LayerTiming; sceneEndSec: number }> = ({ spec, timing, sceneEndSec }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const { theme, transcript, beats, total } = useReel();
  const cap = useSceneCap();
  const def = REGISTRY[spec.block];
  if (!def) {
    return (
      <div style={{ position: "absolute", left: 40, top: 40, padding: 20, background: "#f00", color: "#fff", fontSize: 32, fontFamily: "monospace" }}>
        Unknown block: {spec.block}
      </div>
    );
  }
  const dur = Math.max(1, Math.round((timing.endSec - timing.startSec) * fps));
  const at = (a: unknown, fb?: number) => {
    if (a === undefined || a === null) return Math.round((fb ?? 0) * fps);
    const s = resolve(a as never, { transcript, beats, total, from: timing.startSec, base: timing.startSec, end: timing.endSec }, fb);
    return Math.round((s - timing.startSec) * fps);
  };
  const box = resolveBox(spec.pos, def.pos ?? "stage", stageFor(cap.pos, cap.hidden));
  const kind = spec.enter ?? def.enter ?? theme.motion.enter;
  let look: React.CSSProperties = {};
  if (!def.self && kind !== "none") {
    const ed = (ENTER_DUR[kind] ?? 0.55) * fps;
    const p = kind === "pop" ? clamp01(springAt(frame, fps, 0, SPR.pop)) : kind === "slam" ? clamp01(springAt(frame, fps, 0, SPR.slam)) : E.out(clamp01(frame / ed));
    look = enterLook(kind, kind === "pop" || kind === "slam" ? springAt(frame, fps, 0, kind === "pop" ? SPR.pop : SPR.slam) : p, frame);
    if (kind === "pop" || kind === "slam") look.opacity = clamp01(p * 3);
  }
  const endsEarly = timing.endSec < sceneEndSec - 0.05;
  if (spec.exit && endsEarly) {
    const xd = 0.35 * fps;
    const xp = E.in(clamp01((frame - (dur - xd)) / xd));
    if (xp > 0) look = mergeLooks(look, exitLook(spec.exit, xp, frame));
  }
  const Block = def.C;
  return (
    <BlockTimeProvider value={{ f: frame, dur, fps, at, left: dur - frame }}>
      <div
        style={{
          position: "absolute",
          left: box.x,
          top: box.y,
          width: box.w,
          height: box.h,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          zIndex: spec.z ?? 1,
          transform: box.scale !== 1 || box.rotate ? `scale(${box.scale}) rotate(${box.rotate}deg)` : undefined,
        }}
      >
        <div
          data-qa="layer"
          data-qa-id={spec.block}
          data-qa-cat={def.cat}
          data-qa-ok={spec.overlap || def.overlay ? "1" : "0"}
          data-qa-bleed={def.bleed ? "1" : "0"}
          style={{ ...look, width: "100%", height: "100%", display: "flex", alignItems: "center", justifyContent: "center", position: "relative" }}
        >
          <Block {...(spec.props ?? {})} />
        </div>
      </div>
    </BlockTimeProvider>
  );
};

export const Layer: React.FC<{ spec: LayerSpec; timing: LayerTiming; sceneStartSec: number; sceneEndSec: number }> = ({ spec, timing, sceneStartSec, sceneEndSec }) => {
  const { fps } = useVideoConfig();
  const from = Math.round((timing.startSec - sceneStartSec) * fps);
  const dur = Math.max(1, Math.round((timing.endSec - timing.startSec) * fps));
  return (
    <Sequence from={from} durationInFrames={dur} layout="none" name={spec.block}>
      <LayerInner spec={spec} timing={timing} sceneEndSec={sceneEndSec} />
    </Sequence>
  );
};
