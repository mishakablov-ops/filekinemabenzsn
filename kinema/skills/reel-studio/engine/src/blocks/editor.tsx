import React from "react";
import { random } from "remotion";
import { useBlockTime, useTheme } from "../core/context";
import { E, SPR, clamp01, springAt } from "../core/motion";
import { defineBlock, type BlockDef } from "./registry";

// ------------------------------------------------------------------ EditorTimeline: a video editor (NLE) timeline that fills up with clips
type Track = { id: string; label: string; kind: "video" | "text" | "voice" | "sfx" | "fx" };
const DEFAULT_TRACKS: Track[] = [
  { id: "V2", label: "V2", kind: "video" },
  { id: "V1", label: "V1", kind: "video" },
  { id: "T1", label: "Субтитры", kind: "text" },
  { id: "A1", label: "Голос", kind: "voice" },
  { id: "A2", label: "Звуки", kind: "sfx" },
  { id: "FX", label: "Эффекты", kind: "fx" },
];
const KIND_COL: Record<Track["kind"], string> = { video: "#7A6656", text: "#D9732F", voice: "#6F7E68", sfx: "#8A6E62", fx: "#6E6A80" };

type Add = { track: string; at?: unknown; n?: number };

const EditorTimeline: React.FC<{
  w?: number; h?: number; title?: string; tracks?: Track[]; base?: number; adds?: Add[]; errorAt?: unknown; errorText?: string; seed?: number; speed?: number;
}> = ({ w = 960, h = 560, title = "Ролик_финал_v7.prproj", tracks = DEFAULT_TRACKS, base = 0.45, adds = [], errorAt, errorText = "Ошибка экспорта · 99 %", seed = 3, speed = 0.12 }) => {
  const { f, fps, at } = useBlockTime();
  const th = useTheme();
  const head = 46;
  const ruler = 30;
  const labelW = 120;
  const laneH = (h - head - ruler - 14) / tracks.length;
  const areaW = w - labelW - 18;
  // base clips: deterministic, cover ~`base` of each lane
  const clips: { lane: number; x: number; len: number; start: number; idx: number }[] = [];
  tracks.forEach((t, li) => {
    let x = random(`x${seed}${li}`) * 0.12;
    let k = 0;
    while (x < 0.96) {
      const len = 0.05 + random(`l${seed}${li}${k}`) * 0.16;
      if (random(`p${seed}${li}${k}`) < base) clips.push({ lane: li, x, len: Math.min(len, 0.99 - x), start: -999, idx: k });
      x += len + 0.01 + random(`g${seed}${li}${k}`) * 0.05;
      k++;
    }
  });
  // added clips pile up on their lane at their anchor (staggered)
  adds.forEach((a, ai) => {
    const li = Math.max(0, tracks.findIndex((t) => t.id === a.track || t.label === a.track));
    const s0 = a.at !== undefined ? at(a.at) : Math.round(0.5 * fps);
    for (let k = 0; k < (a.n ?? 6); k++) {
      const x = random(`ax${seed}${ai}${k}`) * 0.9;
      clips.push({ lane: li, x, len: 0.03 + random(`al${seed}${ai}${k}`) * 0.07, start: s0 + k * 3, idx: 100 + ai * 10 + k });
    }
  });
  const ph = ((f / fps) * speed) % 1;
  const err = errorAt !== undefined ? at(errorAt) : 1e9;
  const errP = clamp01((f - err) / (0.25 * fps));
  const tc = (sec: number) => {
    const fr = Math.floor((sec % 1) * 25);
    const s = Math.floor(sec) % 60;
    const m = Math.floor(sec / 60);
    return `00:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}:${String(fr).padStart(2, "0")}`;
  };
  return (
    <div style={{ width: w, height: h, background: th.dark ? "#1C1916" : th.card, borderRadius: th.radius, boxShadow: th.cardShadow, border: `1px solid ${th.cardBorder}`, overflow: "hidden", position: "relative", fontFamily: th.fontUi, color: th.cardInk }}>
      <div style={{ height: head, display: "flex", alignItems: "center", gap: 10, padding: "0 18px", borderBottom: `1px solid ${th.cardBorder}` }}>
        {["#C9654A", "#D9A441", "#7E9A6A"].map((c) => <span key={c} style={{ width: 12, height: 12, borderRadius: 6, background: c }} />)}
        <span style={{ marginLeft: 10, font: `600 18px ${th.fontUi}`, color: th.cardMuted, flex: 1 }}>{title}</span>
        <span style={{ font: `700 20px ${th.fontMono}`, color: th.accent, fontVariantNumeric: "tabular-nums" }}>{tc(ph * 42)}</span>
      </div>
      <div style={{ position: "absolute", left: labelW, top: head, width: areaW, height: ruler, borderBottom: `1px solid ${th.cardBorder}` }}>
        {Array.from({ length: 21 }, (_, i) => (
          <div key={i} style={{ position: "absolute", left: `${i * 5}%`, bottom: 0, width: 1, height: i % 4 === 0 ? 14 : 7, background: th.cardMuted, opacity: 0.6 }} />
        ))}
      </div>
      {tracks.map((t, li) => (
        <div key={t.id} style={{ position: "absolute", left: 0, top: head + ruler + 6 + li * laneH, width: w, height: laneH - 6, display: "flex", alignItems: "center" }}>
          <div style={{ width: labelW - 10, paddingLeft: 16, font: `600 16px ${th.fontUi}`, color: th.cardMuted, whiteSpace: "nowrap", overflow: "hidden" }}>{t.label}</div>
          <div style={{ position: "absolute", left: labelW, width: areaW, height: "100%", borderRadius: 6, background: th.dark ? "rgba(255,240,220,0.035)" : "rgba(0,0,0,0.04)" }} />
        </div>
      ))}
      {clips.map((c, i) => {
        const sp = c.start < 0 ? 1 : clamp01(springAt(f, fps, c.start, SPR.pop));
        if (sp <= 0.001) return null;
        const t = tracks[c.lane];
        const col = KIND_COL[t.kind];
        return (
          <div key={i} style={{
            position: "absolute", left: labelW + c.x * areaW, top: head + ruler + 6 + c.lane * laneH + 3, width: Math.max(10, c.len * areaW), height: laneH - 12,
            borderRadius: 6, background: col, opacity: 0.92, transform: `scaleY(${sp})`, boxShadow: c.start >= 0 ? `0 0 0 2px ${th.accent}55` : undefined,
            overflow: "hidden",
          }}>
            {t.kind === "voice" ? (
              <svg width="100%" height="100%" preserveAspectRatio="none" viewBox="0 0 40 10">
                {Array.from({ length: 20 }, (_, k) => {
                  const a = 1 + random(`w${i}${k}`) * 3.5;
                  return <rect key={k} x={k * 2 + 0.4} y={5 - a} width={1.1} height={a * 2} fill="rgba(20,16,12,0.45)" />;
                })}
              </svg>
            ) : t.kind === "text" ? (
              <div style={{ font: `700 11px ${th.fontUi}`, color: "#1E1712", padding: "3px 6px", whiteSpace: "nowrap" }}>Aa</div>
            ) : null}
          </div>
        );
      })}
      <div style={{ position: "absolute", left: labelW + ph * areaW, top: head, width: 2, height: h - head, background: th.accent }}>
        <div style={{ position: "absolute", top: 0, left: -7, width: 16, height: 16, background: th.accent, clipPath: "polygon(0 0,100% 0,50% 100%)" }} />
      </div>
      {errP > 0 ? (
        <div style={{ position: "absolute", inset: 0, background: `rgba(20,10,8,${0.55 * errP})`, display: "flex", alignItems: "center", justifyContent: "center" }}>
          <div style={{ transform: `scale(${0.9 + 0.1 * E.back(errP)})`, opacity: errP, background: "#2A1714", border: "2px solid #C9654A", borderRadius: 16, padding: "22px 30px", font: `800 32px ${th.fontUi}`, color: "#F0C9B8" }}>
            ⚠ {errorText}
          </div>
        </div>
      ) : null}
    </div>
  );
};

export const EDITOR_BLOCKS: Record<string, BlockDef> = {
  EditorTimeline: defineBlock({
    C: EditorTimeline, cat: "ui",
    desc: "Video-editor (NLE) timeline: tracks V2/V1/Субтитры/Голос/Звуки/Эффекты, moving playhead + timecode; adds:[{track,at,n}] piles clips onto a lane at an anchor (the pain of manual editing); errorAt/errorText = export crash overlay.",
    pos: "stage", enter: "rise", sfx: null,
    events: (p, t) => [
      ...((p.adds ?? []) as { at?: unknown }[]).map((a) => ({ f: a.at !== undefined ? t.at(a.at) : 30, id: "pop-soft", vol: 0.6 })),
      ...(p.errorAt !== undefined ? [{ f: t.at(p.errorAt), id: "error-thud" }] : []),
    ],
    example: { adds: [{ track: "T1", at: 0.6, n: 8 }, { track: "A2", at: 1.2, n: 6 }], errorAt: 2.4 },
  }),
};
