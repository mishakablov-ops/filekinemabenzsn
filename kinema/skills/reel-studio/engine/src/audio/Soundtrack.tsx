import React, { useMemo } from "react";
import { Audio, Sequence, staticFile, useVideoConfig } from "remotion";
import type { SfxPlan } from "../core/plan";
import type { Spec, Transcript } from "../core/types";

const src = (p: string) => (/^https?:|^data:/.test(p) ? p : staticFile(p));

/** per-frame music gain with voice ducking (attack 80ms, release 350ms) */
const duckCurve = (transcript: Transcript | null, frames: number, fps: number, base: number, duck: number, fadeIn: number, fadeOut: number) => {
  const speech = new Float32Array(frames);
  if (transcript) {
    for (const w of transcript.words) {
      const a = Math.max(0, Math.floor((w.start - 0.12) * fps));
      const b = Math.min(frames, Math.ceil((w.end + 0.28) * fps));
      for (let i = a; i < b; i++) speech[i] = 1;
    }
  }
  const out = new Float32Array(frames);
  let g = 1;
  const att = 1 - Math.exp(-1 / (0.08 * fps));
  const rel = 1 - Math.exp(-1 / (0.35 * fps));
  for (let i = 0; i < frames; i++) {
    const target = speech[i] ? duck : 1;
    g += (target - g) * (target < g ? att : rel);
    const fi = fadeIn > 0 ? Math.min(1, i / (fadeIn * fps)) : 1;
    const fo = fadeOut > 0 ? Math.min(1, (frames - i) / (fadeOut * fps)) : 1;
    out[i] = base * g * fi * fo;
  }
  return out;
};

export const Soundtrack: React.FC<{ spec: Spec; transcript: Transcript | null; sfx: SfxPlan[] }> = ({ spec, transcript, sfx }) => {
  const { fps, durationInFrames } = useVideoConfig();
  const m = spec.music;
  const curve = useMemo(
    () => (m ? duckCurve(spec.voice ? transcript : null, durationInFrames, fps, m.volume ?? 0.16, m.duck ?? 0.45, m.fadeIn ?? 0.4, m.fadeOut ?? 1.8) : null),
    [m, transcript, durationInFrames, fps, spec.voice],
  );
  return (
    <>
      {spec.voice ? <Audio src={src(spec.voice.src)} volume={spec.voice.volume ?? 1} /> : null}
      {m && curve ? (
        <Audio src={src(m.src)} loop trimBefore={Math.round((m.offset ?? 0) * fps)} volume={(f) => curve[Math.min(curve.length - 1, Math.max(0, f))]} />
      ) : null}
      {sfx.map((s, i) => {
        const start = Math.round(s.sec * fps);
        const len = s.dur ? Math.max(1, Math.round(s.dur * fps)) : Math.max(1, durationInFrames - start);
        const fade = Math.max(1, Math.round((s.fade ?? 0) * fps));
        return (
          <Sequence key={i} from={start} durationInFrames={Math.min(len, Math.max(1, durationInFrames - start))} layout="none" name={`sfx ${s.id}`}>
            <Audio
              src={staticFile(s.file)}
              trimBefore={s.from ? Math.round(s.from * fps) : undefined}
              volume={s.dur && s.fade ? (f) => s.vol * Math.min(1, (len - f) / fade) : s.vol}
            />
          </Sequence>
        );
      })}
    </>
  );
};
