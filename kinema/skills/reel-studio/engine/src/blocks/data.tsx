import React from "react";
import { useBlockTime, useTheme } from "../core/context";
import { E, clamp01, fmtNumber, lerp } from "../core/motion";
import { defineBlock, type BlockDef } from "./registry";
import { Card } from "./ui";

// ------------------------------------------------------------------ BarChart (horizontal, labelled)
const BarChart: React.FC<{ title?: string; bars: { label: string; value: number; dim?: boolean; note?: string }[]; max?: number; stagger?: number; w?: number; unit?: string }> = ({
  title, bars, max, stagger = 0.12, w = 900, unit = "",
}) => {
  const { f, fps } = useBlockTime();
  const th = useTheme();
  const mx = max ?? Math.max(...bars.map((b) => b.value));
  return (
    <Card th={th} w={w} pad={36}>
      {title ? <div style={{ font: `700 32px ${th.fontUi}`, color: th.cardMuted, marginBottom: 26 }}>{title}</div> : null}
      <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
        {bars.map((b, i) => {
          const p = E.outExpo(clamp01((f - 6 - i * stagger * fps) / (0.9 * fps)));
          const a = clamp01((f - i * stagger * fps) / 8);
          return (
            <div key={i} style={{ display: "flex", alignItems: "center", gap: 20, opacity: a * (b.dim ? 0.45 : 1) }}>
              <div style={{ width: 280, font: `700 32px ${th.fontUi}`, color: b.dim ? th.cardMuted : th.cardInk, lineHeight: 1.15, fontStyle: b.dim ? "italic" : undefined }}>{b.label}</div>
              <div style={{ flex: 1, height: 26, borderRadius: 13, background: th.dark ? "rgba(255,255,255,0.06)" : "rgba(0,0,0,0.05)" }}>
                <div style={{ width: `${(b.value / mx) * 100 * p}%`, height: "100%", borderRadius: 13, background: b.dim ? th.cardMuted : th.accent }} />
              </div>
              <div style={{ width: 90, textAlign: "right", font: `800 36px ${th.fontUi}`, color: b.dim ? th.cardMuted : th.accent, fontVariantNumeric: "tabular-nums" }}>
                {b.note ?? `${Math.round(b.value * p)}${unit}`}
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
};

// ------------------------------------------------------------------ ColumnChart
const ColumnChart: React.FC<{ values: number[]; labels?: string[]; title?: string; highlight?: number; unit?: string; h?: number }> = ({ values, labels = [], title, highlight, unit = "", h = 520 }) => {
  const { f, fps } = useBlockTime();
  const th = useTheme();
  const mx = Math.max(...values);
  const hi = highlight ?? values.length - 1;
  return (
    <Card th={th} w={900} pad={36}>
      {title ? <div style={{ font: `700 32px ${th.fontUi}`, color: th.cardMuted, marginBottom: 20 }}>{title}</div> : null}
      <div style={{ display: "flex", alignItems: "flex-end", gap: 18, height: h }}>
        {values.map((v, i) => {
          const p = E.outExpo(clamp01((f - 4 - i * 3) / (0.8 * fps)));
          return (
            <div key={i} style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "flex-end", height: "100%" }}>
              <div style={{ font: `800 30px ${th.fontUi}`, color: i === hi ? th.accent : th.cardMuted, marginBottom: 8, opacity: p }}>{fmtNumber(v * p)}{unit}</div>
              <div style={{ width: "100%", height: `${(v / mx) * 82 * p}%`, borderRadius: 14, background: i === hi ? th.accent : th.dark ? "rgba(255,255,255,0.12)" : "rgba(0,0,0,0.1)" }} />
              {labels[i] ? <div style={{ font: `600 26px ${th.fontUi}`, color: th.cardMuted, marginTop: 10 }}>{labels[i]}</div> : null}
            </div>
          );
        })}
      </div>
    </Card>
  );
};

// ------------------------------------------------------------------ LineChart (path draws itself, end dot + value)
const LineChart: React.FC<{ values: number[]; title?: string; unit?: string; w?: number; h?: number; area?: boolean }> = ({ values, title, unit = "", w = 900, h = 520, area = true }) => {
  const { f, fps } = useBlockTime();
  const th = useTheme();
  const mx = Math.max(...values);
  const mn = Math.min(...values);
  const pw = w - 72;
  const ph = h - 60;
  const pts = values.map((v, i) => [(i / (values.length - 1)) * pw, ph - ((v - mn) / (mx - mn || 1)) * ph * 0.9 - ph * 0.05] as const);
  const d = pts.map(([x, y], i) => `${i ? "L" : "M"}${x.toFixed(1)},${y.toFixed(1)}`).join(" ");
  const len = pts.reduce((a, p, i) => (i ? a + Math.hypot(p[0] - pts[i - 1][0], p[1] - pts[i - 1][1]) : 0), 0);
  const p = E.inOut(clamp01((f - 6) / (1.4 * fps)));
  const k = p * (values.length - 1);
  const i0 = Math.floor(k);
  const fr = k - i0;
  const end = i0 >= values.length - 1 ? pts[values.length - 1] : [lerp(pts[i0][0], pts[i0 + 1][0], fr), lerp(pts[i0][1], pts[i0 + 1][1], fr)];
  const val = i0 >= values.length - 1 ? values[values.length - 1] : lerp(values[i0], values[i0 + 1], fr);
  return (
    <Card th={th} w={w} pad={36}>
      {title ? <div style={{ font: `700 32px ${th.fontUi}`, color: th.cardMuted, marginBottom: 16 }}>{title}</div> : null}
      <svg width={pw} height={ph} style={{ overflow: "visible" }}>
        {[0.25, 0.5, 0.75].map((g) => (
          <line key={g} x1={0} x2={pw} y1={ph * g} y2={ph * g} stroke={th.cardBorder} strokeWidth={2} />
        ))}
        {area ? <path d={`${d} L${pw},${ph} L0,${ph} Z`} fill={th.accent} opacity={0.12} style={{ clipPath: `inset(0 ${(1 - p) * 100}% 0 0)` }} /> : null}
        <path d={d} fill="none" stroke={th.accent} strokeWidth={7} strokeLinecap="round" strokeLinejoin="round" strokeDasharray={len} strokeDashoffset={len * (1 - p)} />
        <circle cx={end[0]} cy={end[1]} r={14} fill={th.accent} />
        <circle cx={end[0]} cy={end[1]} r={14 + 16 * ((f % 40) / 40)} fill="none" stroke={th.accent} strokeWidth={3} opacity={1 - (f % 40) / 40} />
        <text x={Math.min(end[0], pw - 120)} y={end[1] - 30} fill={th.cardInk} style={{ font: `800 40px ${th.fontUi}` }}>
          {fmtNumber(val)}
          {unit}
        </text>
      </svg>
    </Card>
  );
};

// ------------------------------------------------------------------ Donut / ring
const Donut: React.FC<{ value: number; label?: string; size?: number; color?: string; dur?: number }> = ({ value, label, size = 440, color, dur = 1.4 }) => {
  const { f, fps } = useBlockTime();
  const th = useTheme();
  const p = E.outExpo(clamp01((f - 4) / (dur * fps)));
  const r = size / 2 - 30;
  const c = 2 * Math.PI * r;
  return (
    <div style={{ position: "relative", width: size, height: size }}>
      <svg width={size} height={size} style={{ transform: "rotate(-90deg)" }}>
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke={th.dark ? "rgba(255,255,255,0.08)" : "rgba(0,0,0,0.07)"} strokeWidth={44} />
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke={color ?? th.accent} strokeWidth={44} strokeLinecap="round" strokeDasharray={c} strokeDashoffset={c * (1 - (value / 100) * p)} />
      </svg>
      <div style={{ position: "absolute", inset: 0, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center" }}>
        <div style={{ font: `800 ${size * 0.26}px ${th.fontDisplay}`, letterSpacing: "-0.05em", color: th.ink }}>{Math.round(value * p)}%</div>
        {label ? <div style={{ font: `600 ${size * 0.07}px ${th.fontUi}`, color: th.muted, marginTop: 4, textAlign: "center", maxWidth: size * 0.6 }}>{label}</div> : null}
      </div>
    </div>
  );
};

// ------------------------------------------------------------------ KPI row
const KPIs: React.FC<{ items: { value: number; label: string; prefix?: string; suffix?: string; format?: "space" | "k" | "dec1" }[]; stagger?: number }> = ({ items, stagger = 0.15 }) => {
  const { f, fps } = useBlockTime();
  const th = useTheme();
  return (
    <div style={{ display: "grid", gridTemplateColumns: `repeat(${Math.min(items.length, 2)}, 1fr)`, gap: 22, width: 920 }}>
      {items.map((it, i) => {
        const s = Math.round(i * stagger * fps);
        const p = E.outExpo(clamp01((f - s) / (1.1 * fps)));
        const a = clamp01((f - s) / 10);
        return (
          <div key={i} style={{ padding: 30, borderRadius: 28, background: th.card, border: `1px solid ${th.cardBorder}`, boxShadow: th.cardShadow, opacity: a, transform: `translateY(${(1 - a) * 30}px)` }}>
            <div style={{ font: `800 84px ${th.fontDisplay}`, letterSpacing: "-0.05em", color: i === 0 ? th.accent : th.cardInk, fontVariantNumeric: "tabular-nums" }}>
              {it.prefix}
              {fmtNumber(it.value * p, it.format ?? "space")}
              {it.suffix}
            </div>
            <div style={{ font: `600 30px ${th.fontUi}`, color: th.cardMuted, marginTop: 6 }}>{it.label}</div>
          </div>
        );
      })}
    </div>
  );
};

// ------------------------------------------------------------------ Table with row highlight
const Table: React.FC<{ head: string[]; rows: string[][]; highlight?: number; highlightAt?: unknown }> = ({ head, rows, highlight, highlightAt }) => {
  const { f, fps, at } = useBlockTime();
  const th = useTheme();
  const ha = highlightAt !== undefined ? at(highlightAt) : Math.round(1.2 * fps);
  const hp = clamp01((f - ha) / 10);
  return (
    <Card th={th} w={920} pad={14}>
      <div style={{ display: "grid", gridTemplateColumns: `repeat(${head.length}, 1fr)` }}>
        {head.map((h, i) => (
          <div key={i} style={{ padding: "18px 20px", font: `700 26px ${th.fontUi}`, color: th.cardMuted }}>{h}</div>
        ))}
        {rows.map((r, ri) =>
          r.map((c, ci) => {
            const a = clamp01((f - 4 - ri * 3) / 8);
            const hl = ri === highlight && hp > 0;
            return (
              <div key={`${ri}-${ci}`} style={{ padding: "18px 20px", font: `${ci === 0 ? 700 : 600} 30px ${th.fontUi}`, color: hl ? "#1E1712" : th.cardInk, background: hl ? `${th.accent}` : undefined, opacity: a, borderTop: `1px solid ${th.cardBorder}` }}>{c}</div>
            );
          }),
        )}
      </div>
    </Card>
  );
};

// ------------------------------------------------------------------ Waveform (voice)
const Waveform: React.FC<{ bars?: number; color?: string; h?: number; label?: string }> = ({ bars = 48, color, h = 260, label }) => {
  const { f } = useBlockTime();
  const th = useTheme();
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 20 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8, height: h }}>
        {Array.from({ length: bars }, (_, i) => {
          const env = Math.sin((i / (bars - 1)) * Math.PI);
          const v = 0.15 + env * (0.5 + 0.5 * Math.abs(Math.sin(f * 0.21 + i * 0.7) * Math.cos(f * 0.13 + i * 1.3)));
          return <div key={i} style={{ width: 10, height: h * v, borderRadius: 5, background: color ?? th.accent }} />;
        })}
      </div>
      {label ? <div style={{ font: `700 36px ${th.fontUi}`, color: th.ink }}>{label}</div> : null}
    </div>
  );
};

// ------------------------------------------------------------------ MapPin (2D coordinate tag with error radius)
const MapPin: React.FC<{ coords: string; radius?: string; label?: string }> = ({ coords, radius, label }) => {
  const { f, fps } = useBlockTime();
  const th = useTheme();
  const p = E.out(clamp01(f / (0.5 * fps)));
  const ring = (f % 50) / 50;
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 18 }}>
      <div style={{ position: "relative", width: 260, height: 260 }}>
        <div style={{ position: "absolute", inset: 0, borderRadius: "50%", border: `5px solid ${th.accent}`, transform: `scale(${0.4 + ring * 0.6})`, opacity: 1 - ring }} />
        <div style={{ position: "absolute", inset: 60, borderRadius: "50%", border: `6px solid ${th.accent}`, transform: `scale(${p})` }} />
        <div style={{ position: "absolute", left: 115, top: 115, width: 30, height: 30, borderRadius: 15, background: th.accent, boxShadow: `0 0 24px ${th.accent}` }} />
        {radius ? <div style={{ position: "absolute", left: 200, top: 40, font: `700 34px ${th.fontMono}`, color: th.ink, whiteSpace: "nowrap" }}>±{radius}</div> : null}
      </div>
      <div style={{ font: `600 32px ${th.fontMono}`, color: th.ink, background: th.glass, padding: "12px 22px", borderRadius: 12, border: `1px solid ${th.cardBorder}`, opacity: clamp01((f - 10) / 10) }}>{coords}</div>
      {label ? <div style={{ font: `700 34px ${th.fontUi}`, color: th.muted }}>{label}</div> : null}
    </div>
  );
};

export const DATA_BLOCKS: Record<string, BlockDef> = {
  BarChart: defineBlock({ C: BarChart, cat: "data", desc: "Horizontal labelled bars counting up (complaints, votes). dim:true greys out an outlier, note replaces the number.", pos: "stage", enter: "rise", sfx: "riser-short", example: { title: "О чём жалуются", bars: [{ label: "Нет напоминаний", value: 27 }, { label: "Доплата за сотрудника", value: 21 }, { label: "Путаница с поясом", value: 14 }, { label: "«Ужасный цвет»", value: 1, dim: true, note: "1 отзыв" }] } }),
  ColumnChart: defineBlock({ C: ColumnChart, cat: "data", desc: "Vertical columns growing; highlight index uses the accent.", pos: "stage", enter: "rise", sfx: "riser-short", example: { values: [120, 210, 340, 610], labels: ["янв", "фев", "мар", "апр"] } }),
  LineChart: defineBlock({ C: LineChart, cat: "data", desc: "Line that draws itself with an area fill and a live end value.", pos: "stage", enter: "rise", sfx: "riser-short", example: { values: [10, 14, 13, 22, 31, 48, 75], title: "Звёзды за неделю" } }),
  Donut: defineBlock({ C: Donut, cat: "data", desc: "Progress ring with a counting percentage and label.", pos: "center", enter: "pop", sfx: "tick-roll", example: { value: 94, label: "покрытие тестами" } }),
  KPIs: defineBlock({ C: KPIs, cat: "data", desc: "2–4 KPI tiles counting up (prefix/suffix/format).", pos: "stage", self: true, sfx: "tick-roll", example: { items: [{ value: 14000, label: "точек обзора" }, { value: 2, label: "метра точность", prefix: "±" }] } }),
  Table: defineBlock({ C: Table, cat: "data", desc: "Table that fades in row by row and highlights one row at highlightAt.", pos: "stage", enter: "rise", sfx: null, events: (p, t) => (p.highlight !== undefined ? [{ f: p.highlightAt !== undefined ? t.at(p.highlightAt) : Math.round(1.2 * t.fps), id: "marker" }] : []), example: { head: ["Тариф", "Цена"], rows: [["Старт", "0 ₽"], ["Про", "990 ₽"]], highlight: 1 } }),
  Waveform: defineBlock({ C: Waveform, cat: "data", desc: "Animated voice waveform bars (voice features, podcasts).", pos: "center", enter: "pop", sfx: null, example: { label: "Голос" } }),
  MapPin: defineBlock({ C: MapPin, cat: "map", desc: "Location pin with pulse, error radius (±2 м) and monospace coordinates.", pos: "center", enter: "pop", sfx: "ping-sonar", example: { coords: "23.7351° N · 113.1235° E", radius: "2 м" } }),
};
