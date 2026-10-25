import React from "react";
import { AbsoluteFill, Composition, Sequence, staticFile, useVideoConfig } from "remotion";
import { REGISTRY } from "./blocks";
import { BlockTimeProvider, ReelProvider } from "./core/context";
import { resolveBox } from "./core/layout";
import type { BeatGrid, ReelProps, SfxMeta, Spec, Transcript } from "./core/types";
import { F } from "./fonts";
import { FontGate } from "./FontGate";
import { Grain, Reel } from "./Reel";
import { getTheme, STYLES, type StyleId } from "./theme/styles";
import { useCurrentFrame } from "remotion";

const loadJson = async <T,>(p: string): Promise<T> => {
  const r = await fetch(staticFile(p));
  if (!r.ok) throw new Error(`cannot load ${p}: ${r.status}`);
  return (await r.json()) as T;
};

const ReelWithFonts: React.FC<ReelProps> = (p) => (
  <FontGate>
    <Reel {...p} />
  </FontGate>
);

// ------------------------------------------------------------- block gallery (QA + docs)
type GalleryProps = { style: StyleId; only: string[]; cat: string; per: number; fixed?: boolean };

const GalleryItem: React.FC<{ id: string; dur: number }> = ({ id, dur }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const def = REGISTRY[id];
  const box = resolveBox(undefined, def.pos ?? "stage");
  const Bg = REGISTRY[getTheme().bgBlock]?.C;
  return (
    <BlockTimeProvider value={{ f, dur, fps, at: (a, fb) => (typeof a === "number" ? Math.round(a * fps) : typeof a === "string" && /^\d/.test(a) ? Math.round(parseFloat(a) * fps) : Math.round((fb ?? 0.8) * fps)), left: dur - f }}>
      <AbsoluteFill>
        {def.cat !== "bg" && def.cat !== "3d" && Bg ? <Bg /> : null}
        <div style={{ position: "absolute", left: box.x, top: box.y, width: box.w, height: box.h, display: "flex", alignItems: "center", justifyContent: "center" }}>
          <def.C {...(def.example ?? {})} />
        </div>
        <div style={{ position: "absolute", left: 40, top: 60, font: `600 34px ${F.mono}`, color: "#fff", background: "rgba(0,0,0,0.6)", padding: "8px 16px", borderRadius: 10 }}>
          {id} · {def.cat}
        </div>
      </AbsoluteFill>
    </BlockTimeProvider>
  );
};

const Gallery: React.FC<GalleryProps> = ({ style, only, cat, per, fixed }) => {
  const { fps } = useVideoConfig();
  const ids = Object.keys(REGISTRY).filter((k) => (only.length ? only.includes(k) : true) && (cat ? REGISTRY[k].cat === cat : true));
  const theme = getTheme(style);
  let at = 0;
  return (
    <FontGate>
      <ReelProvider value={{ theme, transcript: null, beats: null, total: 999, sfxIndex: [] }}>
        <AbsoluteFill style={{ background: theme.bg }}>
          {ids.map((id) => {
            const d = Math.round((fixed ? per : REGISTRY[id].exampleDur ?? per) * fps);
            const from = at;
            at += d;
            return (
              <Sequence key={id} from={from} durationInFrames={d} name={id}>
                <GalleryItem id={id} dur={d} />
              </Sequence>
            );
          })}
          <Grain amount={theme.grain} />
        </AbsoluteFill>
      </ReelProvider>
    </FontGate>
  );
};

const galleryLength = (p: GalleryProps, fps: number) =>
  Object.keys(REGISTRY)
    .filter((k) => (p.only.length ? p.only.includes(k) : true) && (p.cat ? REGISTRY[k].cat === p.cat : true))
    .reduce((a, k) => a + Math.round((p.fixed ? p.per : REGISTRY[k].exampleDur ?? p.per) * fps), 0);

export const Root: React.FC = () => (
  <>
    <Composition
      id="Reel"
      component={ReelWithFonts}
      width={1080}
      height={1920}
      fps={60}
      durationInFrames={600}
      defaultProps={{ project: "demo" } as ReelProps}
      calculateMetadata={async ({ props }) => {
        const base = `projects/${props.project}`;
        const spec = await loadJson<Spec>(`${base}/spec.json`);
        const wordsPath = spec.voice?.words ?? spec.words;
        const transcript = wordsPath ? await loadJson<Transcript>(wordsPath) : null;
        let beats = spec.music?.beats ? await loadJson<BeatGrid>(spec.music.beats) : null;
        // music.offset (s) starts the track later — shift the beat grid so "beat:0" is the first beat on screen
        const off = spec.music?.offset ?? 0;
        if (beats && off) {
          const sh = (a: number[]) => a.map((x) => +(x - off).toFixed(4)).filter((x) => x >= -0.01);
          beats = {
            ...beats,
            beats: sh(beats.beats),
            bars: sh(beats.bars),
            drops: sh(beats.drops),
            sections: beats.sections.map((x) => ({ ...x, start: x.start - off, end: x.end - off })).filter((x) => x.end > 0),
            duration: beats.duration - off,
          };
        }
        const sfxIndex = await loadJson<SfxMeta[]>("sfx/index.json");
        const fps = (props as { fps?: number }).fps ?? spec.fps ?? 60;
        const dur = spec.duration ?? (transcript ? transcript.duration + (spec.tail ?? 1.2) : beats ? beats.duration : 15);
        return {
          durationInFrames: Math.ceil(dur * fps),
          fps,
          width: spec.width ?? 1080,
          height: spec.height ?? 1920,
          props: { ...props, spec, transcript, beats, sfxIndex },
        };
      }}
    />
    <Composition
      id="Gallery"
      component={Gallery}
      width={1080}
      height={1920}
      fps={30}
      durationInFrames={300}
      defaultProps={{ style: "cloud", only: [], cat: "", per: 3 } as GalleryProps}
      calculateMetadata={({ props }) => ({ durationInFrames: Math.max(1, galleryLength(props, 30)), props })}
    />
    {Object.keys(STYLES).map((s) => (
      <Composition
        key={s}
        id={`Gallery-${s}`}
        component={Gallery}
        width={1080}
        height={1920}
        fps={30}
        durationInFrames={300}
        defaultProps={{ style: s as StyleId, only: [], cat: "", per: 3 } as GalleryProps}
        calculateMetadata={({ props }) => ({ durationInFrames: Math.max(1, galleryLength(props, 30)), props })}
      />
    ))}
  </>
);
