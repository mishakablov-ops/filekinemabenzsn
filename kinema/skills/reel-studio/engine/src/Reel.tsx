import React, { useMemo } from "react";
import { AbsoluteFill, Img, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { Soundtrack } from "./audio/Soundtrack";
import { Captions, captionHits, type CaptionOverride } from "./captions/Captions";
import { ReelProvider } from "./core/context";
import { buildPlan } from "./core/plan";
import { SceneView } from "./core/Scene";
import type { ReelProps } from "./core/types";
import { getTheme } from "./theme/styles";
import { QAOverlay } from "./qa/QAOverlay";

export const Grain: React.FC<{ amount: number }> = ({ amount }) => {
  const f = useCurrentFrame();
  if (amount <= 0) return null;
  const k = f % 4;
  const ox = ((f * 137) % 256) - 128;
  const oy = ((f * 89) % 256) - 128;
  return (
    <AbsoluteFill style={{ opacity: amount * 3, mixBlendMode: "overlay", pointerEvents: "none" }}>
      <Img
        src={staticFile(`fx/grain-${k}.png`)}
        style={{ position: "absolute", left: -128 + ox, top: -128 + oy, width: 1080 + 256, height: 1920 + 256, objectFit: "none", imageRendering: "pixelated" }}
      />
    </AbsoluteFill>
  );
};

export const Vignette: React.FC<{ amount: number }> = ({ amount }) =>
  amount > 0 ? (
    <AbsoluteFill
      style={{ background: `radial-gradient(ellipse 75% 60% at 50% 48%, rgba(0,0,0,0) 55%, rgba(0,0,0,${amount}) 100%)`, pointerEvents: "none" }}
    />
  ) : null;

export const Reel: React.FC<ReelProps> = ({ spec, transcript, beats, sfxIndex, qa }) => {
  const { fps, durationInFrames } = useVideoConfig();
  const total = durationInFrames / fps;
  const theme = getTheme(spec?.style);
  const plan = useMemo(
    () => (spec ? buildPlan(spec, transcript ?? null, beats ?? null, sfxIndex ?? [], total, fps) : null),
    [spec, transcript, beats, sfxIndex, total, fps],
  );
  const override: CaptionOverride = useMemo(
    () => (t: number) => {
      if (!plan) return null;
      const sc = [...plan.scenes].reverse().find((s) => s.startSec <= t + 0.08);
      if (!sc) return null;
      if (sc.spec.captions === false) return { hide: true };
      const st = sc.theme;
      return {
        themeId: sc.spec.style,
        mode: sc.spec.captions?.mode ?? (sc.spec.style ? st.captionMode : undefined),
        pos: sc.spec.captions?.pos ?? (sc.spec.style ? st.captionPos : undefined),
        tone: sc.spec.captions?.tone ?? (sc.spec.style ? (st.dark ? "light" : "dark") : undefined),
        scale: sc.spec.captions?.scale,
        shadow: sc.spec.captions?.shadow,
        align: sc.spec.captions?.align,
        uppercase: sc.spec.captions?.uppercase,
      };
    },
    [plan],
  );
  const hits = useMemo(
    () => (transcript && spec ? captionHits(transcript, theme, spec.captions, override, fps) : []),
    [transcript, spec, theme, override, fps],
  );
  if (!spec || !plan) return <AbsoluteFill style={{ background: "#300", color: "#fff", fontSize: 48, padding: 80 }}>No spec loaded</AbsoluteFill>;

  return (
    <ReelProvider value={{ theme, transcript: transcript ?? null, beats: beats ?? null, total, sfxIndex: sfxIndex ?? [], qa }}>
      <AbsoluteFill style={{ background: theme.bg }}>
        {plan.scenes.map((sc) => (
          <SceneView key={sc.i} plan={sc} hitsAbs={hits} />
        ))}
        <Vignette amount={spec.vignette ?? theme.vignette} />
        {transcript && spec.captions?.mode !== "none" ? <Captions transcript={transcript} theme={theme} spec={spec.captions} override={override} /> : null}
        <Grain amount={spec.grain ?? theme.grain} />
        {plan.errors.length > 0 && process.env.NODE_ENV !== "production" && (spec as { debug?: boolean }).debug ? (
          <AbsoluteFill style={{ justifyContent: "flex-end", padding: 30 }}>
            <div style={{ background: "rgba(200,0,0,0.85)", color: "#fff", font: "24px monospace", padding: 16, whiteSpace: "pre-wrap" }}>
              {plan.errors.join("\n")}
            </div>
          </AbsoluteFill>
        ) : null}
        {qa ? <QAOverlayAt plan={plan} /> : null}
        {qa ? <PlanErrors errors={plan.errors} scenes={plan.scenes.map((sc) => +sc.startSec.toFixed(2))} /> : null}
        <Soundtrack spec={spec} transcript={transcript ?? null} sfx={plan.sfx} />
      </AbsoluteFill>
    </ReelProvider>
  );
};

const QAOverlayAt: React.FC<{ plan: ReturnType<typeof buildPlan> }> = ({ plan }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = f / fps;
  const busy = plan.scenes.some((sc) => sc.i > 0 && Math.abs(t - sc.startSec) <= sc.tIn.dur / 2 + 0.05);
  return <QAOverlay transition={busy} />;
};

const PlanErrors: React.FC<{ errors: string[]; scenes: number[] }> = ({ errors, scenes }) => {
  React.useLayoutEffect(() => {
    if (errors.length) console.log("QA " + JSON.stringify({ frame: -1, plan: errors }));
    console.log("QA " + JSON.stringify({ frame: -1, scenes }));
  }, [errors, scenes]);
  return null;
};
