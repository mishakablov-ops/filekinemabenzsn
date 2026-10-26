import React from "react";
import { Img } from "remotion";
import { useBlockTime, useTheme } from "../core/context";
import { E, SPR, clamp01, fmtNumber, lerp, springAt } from "../core/motion";
import { Nested, type NestedBlock } from "../three/devices";
import { asset } from "./bg";
import { defineBlock, type BlockDef } from "./registry";
import { pluralize } from "./plural";
import { AppIconGlyph, Stars } from "./ui";
import BRAND from "../brand.json";

// screen palettes (never pure white)
export const SCR = {
  light: { bg: "#F1EADF", surface: "#F8F3EB", ink: "#1F1913", muted: "#8A7E70", line: "rgba(31,25,19,0.08)", chip: "#E7DED1", accent: "#D9732F" },
  dark: { bg: "#17140F", surface: "#221D18", ink: "#EDE3D4", muted: "#9B8D7C", line: "rgba(237,227,212,0.08)", chip: "#2C2620", accent: "#E08A55" },
};
type SP = typeof SCR.light;
const sp = (dark?: boolean, accent?: string): SP => ({ ...(dark ? SCR.dark : SCR.light), ...(accent ? { accent } : {}) });

const StatusBar: React.FC<{ s: SP; time?: string }> = ({ s, time = "9:41" }) => (
  <div style={{ height: 50, display: "flex", alignItems: "center", justifyContent: "space-between", padding: "0 30px", font: `600 17px Inter`, color: s.ink, flexShrink: 0 }}>
    <span>{time}</span>
    <span style={{ display: "flex", gap: 6, alignItems: "center" }}>
      <span style={{ display: "inline-flex", gap: 2, alignItems: "flex-end" }}>
        {[5, 8, 11, 14].map((h) => (
          <span key={h} style={{ width: 3.5, height: h, background: s.ink, borderRadius: 1 }} />
        ))}
      </span>
      <span style={{ width: 25, height: 12, border: `1.5px solid ${s.ink}`, borderRadius: 4, padding: 1.5, boxSizing: "border-box" }}>
        <span style={{ display: "block", width: "75%", height: "100%", background: s.ink, borderRadius: 2 }} />
      </span>
    </span>
  </div>
);

// ------------------------------------------------------------------ Phone (2D)
const Phone: React.FC<{ screen?: NestedBlock; src?: string; w?: number; dark?: boolean; frame?: string; tilt?: number; float?: boolean; shadow?: boolean; island?: boolean }> = ({
  screen, src, w = 430, dark, frame = "#1B1A19", tilt = 0, float = false, shadow = true, island = true,
}) => {
  const { f } = useBlockTime();
  const th = useTheme();
  dark = dark ?? th.dark;
  const k = (w - 28) / 390;
  const h = Math.round(844 * k) + 28;
  const bob = float ? Math.sin(f * 0.04) * 6 : 0;
  return (
    <div style={{ perspective: 1800, transform: `translateY(${bob}px)` }}>
      <div style={{ width: w, height: h, borderRadius: w * 0.16, background: frame, padding: 14, boxSizing: "border-box", position: "relative", transform: tilt ? `rotateY(${tilt}deg)` : undefined, boxShadow: `0 0 0 2px #4A4744, inset 0 0 0 2px #2A2928${shadow ? ", 0 50px 90px -30px rgba(0,0,0,0.6)" : ""}` }}>
        <div style={{ width: w - 28, height: h - 28, borderRadius: w * 0.135, overflow: "hidden", position: "relative", background: (dark ? SCR.dark : SCR.light).bg }}>
          <div style={{ width: 390, height: 844, transform: `scale(${k})`, transformOrigin: "0 0", position: "absolute", left: 0, top: 0 }}>
            {src ? <Img src={asset(src)} style={{ width: 390, height: 844, objectFit: "cover" }} /> : <Nested spec={screen} w={390} h={844} bg={(dark ? SCR.dark : SCR.light).bg} />}
          </div>
          {island ? <div style={{ position: "absolute", top: 11 * k, left: "50%", width: 120 * k, height: 35 * k, marginLeft: -60 * k, borderRadius: 20 * k, background: "#000" }} /> : null}
        </div>
      </div>
    </div>
  );
};

// ------------------------------------------------------------------ Window (macOS chrome) + Browser
const Window: React.FC<{ title?: string; body?: NestedBlock; src?: string; w?: number; h?: number; dark?: boolean; url?: string; tabs?: string[] }> = ({ title = "", body, src, w = 940, h = 640, dark, url, tabs }) => {
  const th = useTheme();
  dark = dark ?? th.dark;
  const s = sp(dark);
  const barH = url ? 104 : 54;
  return (
    <div style={{ width: w, height: h, borderRadius: 22, overflow: "hidden", background: s.bg, boxShadow: "0 50px 100px -30px rgba(0,0,0,0.65)", border: `1px solid ${s.line}`, display: "flex", flexDirection: "column", fontFamily: "Inter" }}>
      <div style={{ height: barH, background: s.surface, borderBottom: `1px solid ${s.line}`, flexShrink: 0, padding: "0 20px", boxSizing: "border-box" }}>
        <div style={{ height: 54, display: "flex", alignItems: "center", gap: 10 }}>
          {["#E0695B", "#E3B04B", "#7DB86A"].map((c) => (
            <span key={c} style={{ width: 16, height: 16, borderRadius: 8, background: c }} />
          ))}
          {tabs ? (
            <div style={{ display: "flex", gap: 6, marginLeft: 18 }}>
              {tabs.map((tb, i) => (
                <span key={i} style={{ font: `600 20px Inter`, color: i === 0 ? s.ink : s.muted, background: i === 0 ? s.bg : "transparent", padding: "8px 16px", borderRadius: 10 }}>{tb}</span>
              ))}
            </div>
          ) : (
            <span style={{ flex: 1, textAlign: "center", font: `600 20px Inter`, color: s.muted, marginRight: 60 }}>{title}</span>
          )}
        </div>
        {url ? (
          <div style={{ height: 38, borderRadius: 10, background: s.bg, display: "flex", alignItems: "center", padding: "0 16px", font: `500 20px Inter`, color: s.muted, gap: 10 }}>
            <span>🔒</span>
            {url}
          </div>
        ) : null}
      </div>
      <div style={{ flex: 1, position: "relative", overflow: "hidden" }}>
        {src ? <Img src={asset(src)} style={{ width: "100%", height: "100%", objectFit: "cover", objectPosition: "top" }} /> : <Nested spec={body} w={w} h={h - barH} bg={s.bg} />}
      </div>
    </div>
  );
};

// ------------------------------------------------------------------ AppScreen: build any mobile screen from sections
type Section =
  | { type: "header"; app?: string; icon?: string; color?: string; title?: string }
  | { type: "card"; avatar?: string; name: string; sub?: string; value?: string }
  | { type: "days"; label?: string; days: [string, string][]; selected?: number; selectAt?: unknown }
  | { type: "slots"; label?: string; slots: string[]; selected?: number; selectAt?: unknown }
  | { type: "rows"; rows: { label: string; value: string; status?: "ok" | "bad" | "warn" | "none" }[] }
  | { type: "button"; label: string; pressAt?: unknown; color?: string }
  | { type: "list"; items: { title: string; sub?: string; right?: string }[] }
  | { type: "text"; text: string; size?: number; muted?: boolean }
  | { type: "image"; h?: number; src?: string; label?: string }
  | { type: "bars"; values: number[]; label?: string }
  | { type: "search"; placeholder?: string }
  | { type: "gap"; h?: number };

const AppScreen: React.FC<{ sections: Section[]; dark?: boolean; accent?: string; stagger?: number; skeleton?: boolean; status?: boolean }> = ({ sections, dark, accent, stagger = 0.06, skeleton = false, status = true }) => {
  const { f, fps, at } = useBlockTime();
  const th = useTheme();
  dark = dark ?? th.dark;
  const s = sp(dark, accent);
  const reveal = (i: number) => (skeleton ? 1 : E.out(clamp01((f - i * stagger * fps) / (0.35 * fps))));
  const skel = (w: number | string, h: number) => <div style={{ width: w, height: h, borderRadius: 8, background: s.chip }} />;
  return (
    <div style={{ width: 390, height: 844, background: s.bg, color: s.ink, fontFamily: "Inter", display: "flex", flexDirection: "column", overflow: "hidden" }}>
      {status ? <StatusBar s={s} /> : null}
      <div style={{ padding: "6px 20px", display: "flex", flexDirection: "column", gap: 14, flex: 1 }}>
        {sections.map((sec, i) => {
          const p = reveal(i);
          const wrap = (node: React.ReactNode) => (
            <div key={i} style={{ opacity: p, transform: `translateY(${(1 - p) * 14}px)` }}>
              {node}
            </div>
          );
          switch (sec.type) {
            case "header":
              return wrap(
                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                    <AppIconGlyph letter={sec.icon ?? (sec.app ?? "A")[0]} color={sec.color ?? s.accent} size={30} radius={8} />
                    <span style={{ font: `700 19px Inter` }}>{sec.app}</span>
                    <span style={{ flex: 1 }} />
                    <span style={{ width: 30, height: 30, borderRadius: 15, background: s.chip }} />
                  </div>
                  {sec.title ? <div style={{ font: `800 30px Inter`, marginTop: 14, letterSpacing: "-0.02em" }}>{sec.title}</div> : null}
                </div>,
              );
            case "card":
              return wrap(
                <div style={{ display: "flex", alignItems: "center", gap: 12, background: s.surface, borderRadius: 16, padding: 14, border: `1px solid ${s.line}` }}>
                  <div style={{ width: 44, height: 44, borderRadius: 22, background: s.accent, display: "flex", alignItems: "center", justifyContent: "center", font: `700 16px Inter`, color: "#1E1712" }}>{sec.avatar ?? sec.name.slice(0, 2).toUpperCase()}</div>
                  <div style={{ flex: 1 }}>
                    <div style={{ font: `700 16px Inter` }}>{sec.name}</div>
                    {sec.sub ? <div style={{ font: `500 13px Inter`, color: s.muted }}>{sec.sub}</div> : null}
                  </div>
                  {sec.value ? <div style={{ font: `700 16px Inter` }}>{sec.value}</div> : null}
                </div>,
              );
            case "days": {
              const selF = sec.selectAt !== undefined ? at(sec.selectAt) : -1;
              const sel = selF >= 0 && f < selF ? -1 : sec.selected ?? -1;
              return wrap(
                <div>
                  {sec.label ? <div style={{ font: `600 13px Inter`, color: s.muted, marginBottom: 8 }}>{sec.label}</div> : null}
                  <div style={{ display: "flex", gap: 8 }}>
                    {sec.days.map(([dw, dn], k) => (
                      <div key={k} style={{ flex: 1, textAlign: "center", padding: "8px 0", borderRadius: 12, background: k === sel ? s.accent : s.surface, color: k === sel ? "#1E1712" : s.ink, border: `1px solid ${s.line}`, transform: k === sel && selF >= 0 ? `scale(${1 + 0.1 * Math.sin(clamp01((f - selF) / 8) * Math.PI)})` : undefined }}>
                        <div style={{ font: `500 11px Inter`, opacity: 0.7 }}>{dw}</div>
                        <div style={{ font: `700 19px Inter` }}>{dn}</div>
                      </div>
                    ))}
                  </div>
                </div>,
              );
            }
            case "slots": {
              const selF = sec.selectAt !== undefined ? at(sec.selectAt) : -1;
              const sel = selF >= 0 && f < selF ? -1 : sec.selected ?? -1;
              return wrap(
                <div>
                  {sec.label ? <div style={{ font: `600 13px Inter`, color: s.muted, marginBottom: 8 }}>{sec.label}</div> : null}
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 8 }}>
                    {sec.slots.map((sl, k) => (
                      <div key={k} style={{ textAlign: "center", padding: "10px 0", borderRadius: 10, font: `600 16px Inter`, background: k === sel ? `${s.accent}33` : s.surface, color: k === sel ? s.accent : s.ink, border: `1.5px solid ${k === sel ? s.accent : s.line}` }}>{sl}</div>
                    ))}
                  </div>
                </div>,
              );
            }
            case "rows":
              return wrap(
                <div style={{ background: s.surface, borderRadius: 14, border: `1px solid ${s.line}` }}>
                  {sec.rows.map((r, k) => {
                    const c = r.status === "ok" ? "#7FAF6A" : r.status === "bad" ? "#D9705A" : r.status === "warn" ? "#D9A54A" : s.muted;
                    return (
                      <div key={k} style={{ display: "flex", alignItems: "center", padding: "12px 14px", borderTop: k ? `1px solid ${s.line}` : undefined, font: `500 15px Inter` }}>
                        <span style={{ flex: 1 }}>{r.label}</span>
                        <span style={{ font: `600 13px Inter`, color: c, background: `${c}22`, padding: "4px 9px", borderRadius: 8 }}>
                          {r.status === "ok" ? "✓ " : r.status === "bad" ? "✕ " : ""}
                          {r.value}
                        </span>
                      </div>
                    );
                  })}
                </div>,
              );
            case "button": {
              const pf = sec.pressAt !== undefined ? at(sec.pressAt) : -999;
              const press = clamp01(1 - Math.abs(f - pf - 3) / 6);
              return wrap(<div style={{ textAlign: "center", padding: "15px 0", borderRadius: 16, background: sec.color ?? s.accent, color: "#1E1712", font: `700 17px Inter`, transform: `scale(${1 - press * 0.05})`, marginTop: 6 }}>{sec.label}</div>);
            }
            case "list":
              return wrap(
                <div style={{ background: s.surface, borderRadius: 14, border: `1px solid ${s.line}` }}>
                  {sec.items.map((it, k) => (
                    <div key={k} style={{ display: "flex", alignItems: "center", gap: 12, padding: "12px 14px", borderTop: k ? `1px solid ${s.line}` : undefined }}>
                      <span style={{ width: 34, height: 34, borderRadius: 10, background: s.chip }} />
                      <div style={{ flex: 1 }}>
                        <div style={{ font: `600 15px Inter` }}>{it.title}</div>
                        {it.sub ? <div style={{ font: `500 12px Inter`, color: s.muted }}>{it.sub}</div> : null}
                      </div>
                      {it.right ? <span style={{ font: `600 14px Inter`, color: s.muted }}>{it.right}</span> : null}
                    </div>
                  ))}
                </div>,
              );
            case "text":
              return wrap(<div style={{ font: `${sec.muted ? 500 : 700} ${sec.size ?? 16}px Inter`, color: sec.muted ? s.muted : s.ink, lineHeight: 1.35 }}>{sec.text}</div>);
            case "image":
              return wrap(
                sec.src ? <Img src={asset(sec.src)} style={{ width: "100%", height: sec.h ?? 180, objectFit: "cover", borderRadius: 16 }} /> : <div style={{ height: sec.h ?? 180, borderRadius: 16, background: s.chip, display: "flex", alignItems: "flex-end", padding: 14, boxSizing: "border-box", font: `700 16px Inter`, color: s.muted }}>{sec.label}</div>,
              );
            case "bars":
              return wrap(
                <div style={{ background: s.surface, borderRadius: 14, padding: 14, border: `1px solid ${s.line}` }}>
                  {sec.label ? <div style={{ font: `600 13px Inter`, color: s.muted, marginBottom: 10 }}>{sec.label}</div> : null}
                  <div style={{ display: "flex", alignItems: "flex-end", gap: 8, height: 90 }}>
                    {sec.values.map((v, k) => (
                      <div key={k} style={{ flex: 1, height: `${v * E.out(clamp01((f - 6 - k * 2) / 20)) * 100}%`, borderRadius: 6, background: k === sec.values.length - 1 ? s.accent : s.chip }} />
                    ))}
                  </div>
                </div>,
              );
            case "search":
              return wrap(<div style={{ padding: "11px 14px", borderRadius: 12, background: s.surface, border: `1px solid ${s.line}`, font: `500 15px Inter`, color: s.muted }}>⌕ {sec.placeholder ?? "Поиск"}</div>);
            case "gap":
              return <div key={i} style={{ height: sec.h ?? 10 }} />;
            default:
              return skel("100%", 40);
          }
        })}
      </div>
    </div>
  );
};

// ------------------------------------------------------------------ ScreenGrid: map of screens + click path + counter pill
const ScreenGrid: React.FC<{ cols?: number; rows?: number; path?: number[]; pathAt?: unknown; step?: number; label?: string; countLabel?: (n: number) => string; pill?: string; dark?: boolean; h?: number }> = ({
  cols = 6, rows = 3, path = [], pathAt, step = 0.35, label, pill, dark, h = 740,
}) => {
  const { f, fps, at } = useBlockTime();
  const th = useTheme();
  const s = sp(dark ?? th.dark);
  const n = cols * rows;
  const gap = 18;
  const pillH = pill || label ? 100 : 0;
  // fit inside the given height (default stage 800 px) as well as 940 px width
  const chMax = (h - pillH - rows * (gap + 26)) / rows;
  const cw = Math.min((940 - gap * (cols - 1)) / cols, chMax / 1.75);
  const ch = cw * 1.75;
  const W = cw * cols + gap * (cols - 1);
  const p0 = pathAt !== undefined ? at(pathAt) : Math.round(0.8 * fps);
  const lit = path.filter((_, k) => f >= p0 + k * step * fps).length;
  const pos = (i: number) => ({ x: (i % cols) * (cw + gap) + cw / 2, y: Math.floor(i / cols) * (ch + gap + 26) + ch / 2 });
  return (
    <div style={{ width: W, position: "relative" }}>
      <div style={{ display: "grid", gridTemplateColumns: `repeat(${cols}, ${cw}px)`, gap: `${gap + 26}px ${gap}px` }}>
        {Array.from({ length: n }, (_, i) => {
          const a = E.out(clamp01((f - i * 1.2) / 10));
          const k = path.indexOf(i);
          const on = k >= 0 && k < lit;
          return (
            <div key={i} style={{ position: "relative", opacity: a, transform: `scale(${lerp(0.85, 1, a) * (on ? 1.06 : 1)})` }}>
              <div style={{ height: ch, borderRadius: 12, background: s.surface, border: `${on ? 4 : 1}px solid ${on ? th.accent : s.line}`, padding: 8, boxSizing: "border-box", display: "flex", flexDirection: "column", gap: 5, boxShadow: on ? `0 0 24px ${th.accent}66` : undefined }}>
                <div style={{ height: 6, width: "55%", borderRadius: 3, background: s.chip }} />
                <div style={{ height: 22, borderRadius: 5, background: s.chip }} />
                <div style={{ height: 6, width: "80%", borderRadius: 3, background: s.chip }} />
                <div style={{ height: 6, width: "65%", borderRadius: 3, background: s.chip }} />
                <div style={{ flex: 1 }} />
                <div style={{ height: 12, borderRadius: 4, background: on ? th.accent : `${th.accent}88` }} />
              </div>
              <div style={{ textAlign: "center", font: `600 18px ${th.fontMono}`, color: on ? th.accent : th.muted, marginTop: 6 }}>S{String(i + 1).padStart(2, "0")}</div>
            </div>
          );
        })}
      </div>
      <svg width={W} height={rows * (ch + gap + 26)} style={{ position: "absolute", left: 0, top: 0, pointerEvents: "none" }}>
        {path.slice(1).map((idx, k) => {
          if (k + 1 >= lit) return null;
          const a = pos(path[k]);
          const b = pos(idx);
          return <line key={k} x1={a.x} y1={a.y} x2={b.x} y2={b.y} stroke={th.accent} strokeWidth={5} strokeLinecap="round" strokeDasharray="10 10" opacity={0.9} />;
        })}
      </svg>
      {pill || label ? (
        <div style={{ display: "flex", justifyContent: "center", marginTop: 24 }}>
          <div style={{ padding: "16px 30px", borderRadius: 999, background: th.card, border: `1px solid ${th.cardBorder}`, boxShadow: th.cardShadow, font: `700 38px ${th.fontUi}`, color: th.cardInk }}>
            {path.length ? <span style={{ color: th.accent }}>{lit} </span> : <span style={{ color: th.accent }}>{n} </span>}
            {pluralize(path.length ? lit : n, path.length ? label ?? "клик|клика|кликов" : pill ?? "экран|экрана|экранов")}
          </div>
        </div>
      ) : null}
    </div>
  );
};

// ------------------------------------------------------------------ LockScreen with notifications + actionable live notification
const LockScreen: React.FC<{ time?: string; date?: string; notes?: { app: string; text: string; at?: unknown; actions?: string[]; pressAt?: unknown }[]; wallpaper?: string }> = ({
  time = "19:13", date = "Вс, 11 октября", notes = [], wallpaper,
}) => {
  const { f, fps, at } = useBlockTime();
  const s = SCR.dark;
  return (
    <div style={{ width: 390, height: 844, position: "relative", overflow: "hidden", background: wallpaper ? undefined : "linear-gradient(170deg, #3A3129 0%, #1C1813 60%, #12100D 100%)", fontFamily: "Inter", color: "#EDE3D4" }}>
      {wallpaper ? <Img src={asset(wallpaper)} style={{ position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "cover" }} /> : null}
      <StatusBar s={s} time="" />
      <div style={{ textAlign: "center", marginTop: 34, font: `600 20px Inter`, opacity: 0.85 }}>{date}</div>
      <div style={{ textAlign: "center", font: `700 96px Inter`, letterSpacing: "-0.04em", lineHeight: 1 }}>{time}</div>
      <div style={{ position: "absolute", left: 14, right: 14, bottom: 120, display: "flex", flexDirection: "column", gap: 10 }}>
        {notes.map((n, i) => {
          const st = n.at !== undefined ? at(n.at) : Math.round(i * 0.5 * fps);
          const p = clamp01(springAt(f - st, fps, 0, SPR.ui));
          if (f < st) return null;
          const pf = n.pressAt !== undefined ? at(n.pressAt) : -999;
          const pressed = f >= pf;
          return (
            <div key={i} style={{ padding: 14, borderRadius: 22, background: "rgba(60,52,44,0.72)", backdropFilter: "blur(18px)", transform: `translateY(${(1 - p) * 60}px) scale(${lerp(0.9, 1, p)})`, opacity: p }}>
              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <AppIconGlyph letter={n.app[0]} size={34} radius={9} />
                <div style={{ flex: 1 }}>
                  <div style={{ font: `700 15px Inter` }}>{n.app}</div>
                  <div style={{ font: `500 14px Inter`, opacity: 0.8 }}>{n.text}</div>
                </div>
                <span style={{ font: `500 12px Inter`, opacity: 0.6 }}>сейчас</span>
              </div>
              {n.actions ? (
                <div style={{ display: "flex", gap: 8, marginTop: 10 }}>
                  {n.actions.map((a, k) => (
                    <div key={k} style={{ flex: 1, textAlign: "center", padding: "9px 0", borderRadius: 12, font: `700 14px Inter`, background: k === n.actions!.length - 1 ? (pressed ? "#7FAF6A" : "#5E8A50") : "rgba(217,112,90,0.85)", color: "#1E1712", transform: pressed && k === n.actions!.length - 1 ? `scale(${1 - 0.06 * clamp01(1 - (f - pf) / 8)})` : undefined }}>
                      {k === n.actions!.length - 1 && pressed ? "✓ " : ""}
                      {a}
                    </div>
                  ))}
                </div>
              ) : null}
            </div>
          );
        })}
      </div>
    </div>
  );
};

// ------------------------------------------------------------------ ChatScreen: messenger dialog (390×844)
// messages[].at — bubble appears; failAt — red «!» + «Не доставлено» (before it: «Отправка…»)
const ChatScreen: React.FC<{
  name?: string; sub?: string; avatar?: string; time?: string;
  messages?: { text: string; me?: boolean; at?: unknown; time?: string; failAt?: unknown; status?: "sent" | "read" }[];
}> = ({ name = "Мама", sub = "была в сети вчера", avatar, time = "8:14", messages = [] }) => {
  const { f, fps, at } = useBlockTime();
  const s = SCR.dark;
  const RED = "#D9574A";
  return (
    <div style={{ width: 390, height: 844, position: "relative", overflow: "hidden", background: s.bg, fontFamily: "Inter", color: s.ink, display: "flex", flexDirection: "column" }}>
      <StatusBar s={s} time={time} />
      <div style={{ display: "flex", alignItems: "center", gap: 12, padding: "8px 16px 14px", borderBottom: `1px solid ${s.line}` }}>
        <span style={{ font: "500 30px Inter", color: s.accent, lineHeight: 1, marginTop: -4 }}>‹</span>
        <div style={{ width: 44, height: 44, borderRadius: 22, background: "#5A4A3E", display: "flex", alignItems: "center", justifyContent: "center", font: "700 19px Inter", color: "#EDE3D4" }}>{avatar ?? name[0]}</div>
        <div style={{ flex: 1 }}>
          <div style={{ font: "700 18px Inter" }}>{name}</div>
          <div style={{ font: "500 13px Inter", color: s.muted }}>{sub}</div>
        </div>
      </div>
      <div style={{ flex: 1, display: "flex", flexDirection: "column", justifyContent: "flex-end", gap: 8, padding: "0 14px 18px" }}>
        {messages.map((m, i) => {
          const st = m.at !== undefined ? at(m.at) : Math.round(i * 0.6 * fps);
          if (f < st) return null;
          const p = clamp01(springAt(f - st, fps, 0, SPR.ui));
          const ff = m.failAt !== undefined ? at(m.failAt) : null;
          const failed = ff !== null && f >= ff;
          const pf = failed ? clamp01(springAt(f - (ff as number), fps, 0, SPR.ui)) : 0;
          const sending = ff !== null && !failed;
          return (
            <div key={i} style={{ display: "flex", flexDirection: "column", alignItems: m.me ? "flex-end" : "flex-start", opacity: p, transform: `translateY(${(1 - p) * 24}px) scale(${lerp(0.94, 1, p)})`, transformOrigin: m.me ? "100% 100%" : "0 100%" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8, flexDirection: m.me ? "row" : "row-reverse" }}>
                {failed ? (
                  <div style={{ width: 24, height: 24, borderRadius: 12, background: RED, color: "#1E1712", font: "800 16px Inter", display: "flex", alignItems: "center", justifyContent: "center", transform: `scale(${lerp(0.3, 1, pf)})` }}>!</div>
                ) : null}
                <div style={{ maxWidth: 270, padding: "10px 15px", borderRadius: 20, borderBottomRightRadius: m.me ? 6 : 20, borderBottomLeftRadius: m.me ? 20 : 6, background: m.me ? s.accent : s.chip, color: m.me ? "#1E1712" : s.ink, font: "500 17px Inter", lineHeight: 1.3, opacity: failed ? 0.72 : 1 }}>
                  {m.text}
                </div>
              </div>
              <div style={{ font: "600 12px Inter", marginTop: 4, padding: "0 4px", color: failed ? RED : s.muted, opacity: failed ? pf : 1 }}>
                {failed ? "Не доставлено" : sending ? `Отправка${".".repeat(1 + (Math.floor((f - st) / (fps * 0.3)) % 3))}` : m.time ?? (m.me ? (m.status === "read" ? "Прочитано" : "Доставлено") : "")}
              </div>
            </div>
          );
        })}
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 10, padding: "10px 14px 34px", borderTop: `1px solid ${s.line}` }}>
        <div style={{ flex: 1, height: 40, borderRadius: 20, border: `1px solid ${s.line}`, background: s.surface, display: "flex", alignItems: "center", padding: "0 16px", font: "500 16px Inter", color: s.muted }}>Сообщение</div>
        <div style={{ width: 40, height: 40, borderRadius: 20, background: s.chip }} />
      </div>
    </div>
  );
};

// ------------------------------------------------------------------ SocialProfile (generic — CTA end card)
const SocialProfile: React.FC<{ handle: string; name?: string; bio?: string[]; link?: string; avatar?: string; tiles?: { title: string; sub?: string; color?: string; src?: string }[]; pressAt?: unknown; posts?: number; followers?: number; following?: number }> = ({
  handle, name, bio = [], link, avatar, tiles = [], pressAt, posts = 48, followers = 12400, following = 31,
}) => {
  const { f, at } = useBlockTime();
  const s = SCR.dark;
  const pf = pressAt !== undefined ? at(pressAt) : -999;
  const pressed = f >= pf;
  return (
    <div style={{ width: 390, height: 844, background: s.bg, color: s.ink, fontFamily: "Inter", overflow: "hidden" }}>
      <StatusBar s={s} />
      <div style={{ display: "flex", alignItems: "center", padding: "6px 18px", font: `700 18px Inter` }}>
        <span style={{ opacity: 0.6 }}>‹</span>
        <span style={{ flex: 1, textAlign: "center" }}>{handle}</span>
        <span style={{ opacity: 0.6 }}>···</span>
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 18, padding: "12px 18px" }}>
        <div style={{ width: 82, height: 82, borderRadius: 41, background: "linear-gradient(135deg, #E08A55, #A9B79A)", padding: 3, boxSizing: "border-box" }}>
          <div style={{ width: "100%", height: "100%", borderRadius: 40, background: "#5E5245", border: `3px solid ${s.bg}`, boxSizing: "border-box", overflow: "hidden" }}>
            {avatar ? <Img src={asset(avatar)} style={{ width: "100%", height: "100%", objectFit: "cover" }} /> : null}
          </div>
        </div>
        {[["публикации", posts], ["подписчики", followers], ["подписки", following]].map(([l, v]) => (
          <div key={l as string} style={{ flex: 1, textAlign: "center" }}>
            <div style={{ font: `700 18px Inter` }}>{fmtNumber(v as number, (v as number) > 9999 ? "k" : "space")}</div>
            <div style={{ font: `500 12px Inter`, color: s.muted }}>{l}</div>
          </div>
        ))}
      </div>
      <div style={{ padding: "0 18px", font: `500 14px Inter`, lineHeight: 1.4 }}>
        {name ? <div style={{ font: `700 15px Inter` }}>{name}</div> : null}
        {bio.map((b, i) => (
          <div key={i}>{b}</div>
        ))}
        {link ? <div style={{ color: "#8FB0E0", fontWeight: 600, background: pressed ? "rgba(143,176,224,0.18)" : undefined, borderRadius: 6, display: "inline-block", padding: "0 4px", marginLeft: -4 }}>🔗 {link}</div> : null}
      </div>
      <div style={{ display: "flex", gap: 8, padding: "14px 18px" }}>
        <div style={{ flex: 1, textAlign: "center", padding: "9px 0", borderRadius: 10, background: "#D9732F", color: "#1E1712", font: `700 14px Inter` }}>Подписаться</div>
        <div style={{ flex: 1, textAlign: "center", padding: "9px 0", borderRadius: 10, background: s.chip, font: `700 14px Inter` }}>Сообщение</div>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 2 }}>
        {(tiles.length ? tiles : Array.from({ length: 9 }, (_, i): { title: string; sub?: string; color?: string; src?: string } => ({ title: "", color: ["#3A332C", "#2F2A25", "#463C33"][i % 3] }))).slice(0, 12).map((t, i) => (
          <div key={i} style={{ position: "relative", overflow: "hidden", height: 172, background: t.color ?? ["#3A332C", "#2F2A25", "#463C33", "#33302B"][i % 4], padding: 10, boxSizing: "border-box", display: "flex", flexDirection: "column", justifyContent: "flex-end" }}>
            {t.src ? <Img src={asset(t.src)} style={{ position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "cover", opacity: 0.85 }} /> : null}
            <div style={{ position: "relative", font: `800 15px Inter`, lineHeight: 1.1, textShadow: "0 1px 6px rgba(0,0,0,0.6)" }}>{t.title}</div>
            {t.sub ? <div style={{ position: "relative", font: `500 10px Inter`, color: s.muted }}>{t.sub}</div> : null}
          </div>
        ))}
      </div>
    </div>
  );
};

// ------------------------------------------------------------------ TikTokProfile: the channel's real TikTok profile (light or dark theme, 390×844)
// Layout follows TikTok's 2025 own-profile screen: big name + handle on the left, avatar on the right, bio, link,
// tab icons, 3-column video grid, bottom nav. highlightAt draws an accent frame round bio+link ("ссылка в шапке профиля").
const TT = { bg: "#FBFAF8", ink: "#161823", muted: "#75767C", line: "rgba(22,24,35,0.12)", red: "#FE2C55", cyan: "#20D5EC", icon: "#5A5B62", badge: "#4A4B52", onAccent: "#FBFAF8" };
const TT_DARK: typeof TT = { bg: "#121212", ink: "#F1F1F2", muted: "#9C9CA3", line: "rgba(255,255,255,0.14)", red: "#FE2C55", cyan: "#20D5EC", icon: "#B4B4BA", badge: "#CFCFD4", onAccent: "#FFFFFF" };
const Ico: React.FC<{ d: string; size?: number; sw?: number; fill?: string; color?: string; vb?: number }> = ({ d, size = 22, sw = 2, fill = "none", color = "currentColor", vb = 24 }) => (
  <svg width={size} height={size} viewBox={`0 0 ${vb} ${vb}`} fill={fill} stroke={fill === "none" ? color : "none"} strokeWidth={sw} strokeLinecap="round" strokeLinejoin="round">
    <path d={d} fill={fill === "none" ? "none" : color} />
  </svg>
);
const IC = {
  pencil: "M4 20h4L19 9l-4-4L4 16v4z M14 6l4 4",
  feet: "M7 3c1.7 0 2.6 1.8 2.6 4.2S8.7 12 7 12 4.6 9.6 4.6 7.2 5.3 3 7 3z M5.2 14.2h3.6v2.3a1.8 1.8 0 0 1-3.6 0z M17 6c1.7 0 2.4 2.4 2.4 4.6S18.7 15 17 15s-2.6-2.1-2.6-4.4S15.3 6 17 6z M15.2 17.2h3.6v2.3a1.8 1.8 0 0 1-3.6 0z",
  addUser: "M10 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8z M3 21c0-3.9 3.1-6.5 7-6.5s7 2.6 7 6.5 M19 8v6 M16 11h6",
  menu: "M4 6h16 M4 12h16 M4 18h16",
  bars: "M6 5v14 M12 5v14 M18 5v14",
  shop: "M4 9h16l-1.3 11H5.3z M8 9V7a4 4 0 0 1 8 0v2",
  lock: "M6 11h12v9H6z M8.5 11V8a3.5 3.5 0 0 1 7 0v3",
  bookmark: "M6 3h12v18l-6-4.5L6 21z",
  heart: "M12 20s-7.5-4.6-7.5-10A4.3 4.3 0 0 1 12 7.4 4.3 4.3 0 0 1 19.5 10c0 5.4-7.5 10-7.5 10z",
  home: "M4 11l8-7 8 7v9h-5v-6H9v6H4z",
  compass: "M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18z M15.5 8.5l-2 5-5 2 2-5z",
  inbox: "M4 5h16v11H9l-5 4z M8.5 10.5h7",
  user: "M12 12a4.5 4.5 0 1 0 0-9 4.5 4.5 0 0 0 0 9z M3.5 21c.6-4.4 4-7 8.5-7s7.9 2.6 8.5 7z",
  store: "M3 9l1.5-4.5h15L21 9 M4 9.5V20h16V9.5 M9 20v-5h6v5",
};
const TikTokProfile: React.FC<{
  name?: string; handle?: string; badge?: string; bio?: string; link?: string; avatar?: string; tiles?: string[]; pinned?: number;
  stats?: { following: string; followers: string; likes: string } | null; highlightAt?: unknown; time?: string;
  /** a new video lands in the first grid cell at `at` (cover image, a label like "ЧАСТЬ 2", a NEW badge) */
  newTile?: { src: string; label?: string; at?: unknown };
  /** TikTok's dark theme (near-black screen, light text) */
  dark?: boolean;
}> = ({
  // defaults = the channel set up by scripts/setup.py (engine/src/brand.json)
  name = BRAND.name, handle = BRAND.handle, badge = BRAND.badge, bio = BRAND.bio, link = BRAND.link || undefined, avatar = BRAND.avatar, tiles = BRAND.tiles, pinned = 0, stats = null, highlightAt, time = "9:41", newTile, dark = false,
}) => {
  const T = dark ? TT_DARK : TT;
  const { f, fps, at } = useBlockTime();
  const nf = newTile ? (newTile.at !== undefined ? at(newTile.at) : 0) : 1e9;
  const nIn = E.out(clamp01((f - nf) / (0.5 * fps)));
  const nFlash = f >= nf ? Math.max(0, 1 - (f - nf) / (0.35 * fps)) : 0;
  const nPulse = f >= nf ? 0.5 + 0.5 * Math.sin(((f - nf) / fps) * Math.PI * 2 * 1.4) : 0;
  const hf = highlightAt !== undefined ? at(highlightAt) : -1e9;
  const hp = E.out(clamp01((f - hf) / (0.45 * fps)));
  const pulse = f >= hf ? 0.5 + 0.5 * Math.sin(((f - hf) / fps) * Math.PI * 2 * 1.2) : 0;
  const tap = clamp01((f - hf - 0.35 * fps) / (0.6 * fps));
  return (
    <div style={{ width: 390, height: 844, background: T.bg, color: T.ink, fontFamily: "Inter", overflow: "hidden", position: "relative" }}>
      {/* status bar (the island is drawn by the device) */}
      <div style={{ height: 54, display: "flex", alignItems: "center", justifyContent: "space-between", padding: "8px 34px 0 46px", boxSizing: "border-box", font: `600 16px Inter` }}>
        <span>{time}</span>
        <span style={{ display: "flex", gap: 6, alignItems: "center" }}>
          <span style={{ display: "inline-flex", gap: 2, alignItems: "flex-end" }}>
            {[4, 7, 10, 13].map((h) => <span key={h} style={{ width: 3, height: h, background: T.ink, borderRadius: 1 }} />)}
          </span>
          <svg width="16" height="12" viewBox="0 0 16 12"><path d="M8 11.5 5.6 9a3.4 3.4 0 0 1 4.8 0zM3.4 6.8a6.6 6.6 0 0 1 9.2 0l-1.1 1.1a5 5 0 0 0-7 0zM1.1 4.5a9.8 9.8 0 0 1 13.8 0l-1.1 1.1a8.2 8.2 0 0 0-11.6 0z" fill={T.ink} /></svg>
          <span style={{ width: 25, height: 12, border: `1.4px solid ${T.ink}`, borderRadius: 4, padding: 1.4, boxSizing: "border-box", opacity: 0.9 }}>
            <span style={{ display: "block", width: "62%", height: "100%", background: T.ink, borderRadius: 2 }} />
          </span>
        </span>
      </div>
      {/* top bar */}
      <div style={{ height: 44, display: "flex", alignItems: "center", padding: "0 16px", gap: 18 }}>
        <Ico d={IC.pencil} size={22} />
        <div style={{ flex: 1 }} />
        <Ico d={IC.feet} size={22} sw={1.8} />
        <Ico d={IC.addUser} size={22} sw={1.9} />
        <Ico d={IC.menu} size={22} sw={2.1} />
      </div>
      {/* name, handle, avatar */}
      <div style={{ position: "relative", padding: "6px 16px 0", height: stats ? 132 : 100 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <span style={{ font: `800 27px Inter`, letterSpacing: -0.6 }}>{name}</span>
          <svg width="12" height="8" viewBox="0 0 12 8" style={{ marginTop: 4 }}><path d="M1 1l5 5 5-5" fill={T.ink} /></svg>
          <span style={{ width: 8, height: 8, borderRadius: 4, background: T.red, marginTop: -14, marginLeft: -2 }} />
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 5, marginTop: 4, font: `500 13px Inter`, color: T.muted }}>
          <span>@{handle}</span>
          <span>·</span>
          <Ico d={IC.store} size={13} sw={1.8} color={T.muted} />
          <span style={{ color: T.badge, fontWeight: 600 }}>{badge}</span>
        </div>
        {stats ? (
          <div style={{ display: "flex", gap: 30, marginTop: 16 }}>
            {[[stats.following, "Following"], [stats.followers, "Followers"], [stats.likes, "Likes"]].map(([v, l]) => (
              <div key={l}><div style={{ font: `800 16px Inter` }}>{v}</div><div style={{ font: `500 13px Inter`, color: T.muted }}>{l}</div></div>
            ))}
          </div>
        ) : null}
        <div style={{ position: "absolute", right: 16, top: -4, width: 86, height: 86, borderRadius: 43, overflow: "hidden", background: "#3A1A16" }}>
          {avatar ? <Img src={asset(avatar)} style={{ width: "100%", height: "100%", objectFit: "cover" }} /> : null}
        </div>
        <div style={{ position: "absolute", right: 12, top: 60, width: 26, height: 26, borderRadius: 13, background: T.cyan, border: `3px solid ${T.bg}`, boxSizing: "border-box", display: "flex", alignItems: "center", justifyContent: "center", color: T.onAccent, font: `700 18px Inter`, lineHeight: 1 }}>+</div>
      </div>
      {/* bio + link (the "шапка профиля") */}
      <div style={{ position: "relative", margin: "0 10px", padding: "8px 6px 10px", borderRadius: 14 }}>
        <div style={{ font: `500 14px Inter`, lineHeight: 1.36 }}>{bio}</div>
        {link ? <div style={{ marginTop: 3, font: `700 14px Inter`, color: T.ink, background: tap > 0 && tap < 1 ? `rgba(217,115,47,${0.22 * (1 - tap)})` : undefined, display: "inline-block", borderRadius: 5 }}>{link}</div> : null}
        {hp > 0 ? (
          <div style={{ position: "absolute", inset: -2, borderRadius: 16, border: `3px solid rgba(217,115,47,${hp})`, boxShadow: `0 0 ${10 + 18 * pulse}px rgba(217,115,47,${0.45 * hp})`, transform: `scale(${1.06 - 0.06 * hp})` }} />
        ) : null}
        {tap > 0 && tap < 1 ? (
          <div style={{ position: "absolute", left: 92, bottom: 18, width: 20 + 70 * tap, height: 20 + 70 * tap, marginLeft: -(10 + 35 * tap), marginBottom: -(10 + 35 * tap), borderRadius: "50%", border: `2px solid rgba(217,115,47,${1 - tap})` }} />
        ) : null}
      </div>
      {/* tabs */}
      <div style={{ display: "flex", justifyContent: "space-around", alignItems: "center", height: 44, marginTop: 8, borderBottom: `1px solid ${T.line}`, position: "relative" }}>
        <span style={{ display: "flex", alignItems: "center", gap: 2 }}><Ico d={IC.bars} size={22} sw={2.2} /><svg width="9" height="6" viewBox="0 0 12 8"><path d="M1 1l5 5 5-5" fill={T.ink} /></svg></span>
        <Ico d={IC.shop} size={22} sw={1.8} color={T.icon} />
        <Ico d={IC.lock} size={22} sw={1.8} color={T.icon} />
        <Ico d={IC.bookmark} size={22} sw={1.8} color={T.icon} />
        <Ico d={IC.heart} size={22} sw={1.8} color={T.icon} />
        <div style={{ position: "absolute", left: 22, bottom: -1, width: 44, height: 2.5, background: T.ink, borderRadius: 2 }} />
      </div>
      {/* video grid */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 1.5 }}>
        {(tiles.length ? tiles.slice(0, 12) : Array.from({ length: 9 }, () => "")).map((src, i) => (
          <div key={i} style={{ position: "relative", height: 172, overflow: "hidden", background: ["#2A2522", "#3A2E26", "#4A3A2E", "#33302B"][i % 4] }}>
            {src ? (
              <Img src={asset(src)} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
            ) : (
              // no reels rendered yet: muted cover with a play glyph (render.py adds real covers to brand.json)
              <svg width="26" height="26" viewBox="0 0 24 24" style={{ position: "absolute", left: "50%", top: "50%", marginLeft: -13, marginTop: -13, opacity: 0.5 }}><path d="M8 5v14l11-7z" fill="#E8D9C2" /></svg>
            )}
            {i < pinned ? <div style={{ position: "absolute", left: 6, top: 6, background: T.red, color: T.onAccent, font: `700 10px Inter`, padding: "2px 5px", borderRadius: 3 }}>Pinned</div> : null}
            {i === 0 && newTile && nIn > 0 ? (
              <div style={{ position: "absolute", inset: 0, opacity: nIn, transform: `scale(${1.25 - 0.25 * nIn})` }}>
                <Img src={asset(newTile.src)} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
                <div style={{ position: "absolute", left: 6, top: 6, background: T.red, color: T.onAccent, font: `800 11px Inter`, padding: "2px 6px", borderRadius: 3, boxShadow: `0 0 ${6 + 10 * nPulse}px rgba(254,44,85,0.8)` }}>NEW</div>
                {newTile.label ? <div style={{ position: "absolute", left: 0, right: 0, bottom: 8, textAlign: "center", color: "#fff", font: `900 20px Inter`, letterSpacing: 0.5, textShadow: "0 2px 6px rgba(0,0,0,0.9)" }}>{newTile.label}</div> : null}
                <div style={{ position: "absolute", inset: 0, border: `3px solid rgba(254,44,85,${0.6 + 0.4 * nPulse})` }} />
                <div style={{ position: "absolute", inset: 0, background: "#fff", opacity: nFlash * 0.8 }} />
              </div>
            ) : null}
          </div>
        ))}
      </div>
      {/* bottom nav */}
      <div style={{ position: "absolute", left: 0, right: 0, bottom: 0, height: 82, background: T.bg, borderTop: `1px solid ${T.line}`, display: "flex", justifyContent: "space-around", alignItems: "flex-start", paddingTop: 8, boxSizing: "border-box" }}>
        {[["Home", IC.home], ["Discover", IC.compass], ["+", ""], ["Inbox", IC.inbox], ["Profile", IC.user]].map(([l, d]) =>
          l === "+" ? (
            <div key={l} style={{ position: "relative", width: 46, height: 30, marginTop: 4 }}>
              <div style={{ position: "absolute", top: 0, bottom: 0, left: -3, right: 3, borderRadius: 9, background: T.cyan }} />
              <div style={{ position: "absolute", top: 0, bottom: 0, left: 3, right: -3, borderRadius: 9, background: T.red }} />
              <div style={{ position: "absolute", inset: 0, borderRadius: 9, background: T.ink, color: T.bg, display: "flex", alignItems: "center", justifyContent: "center", font: `700 22px Inter` }}>+</div>
            </div>
          ) : (
            <div key={l} style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 2, position: "relative" }}>
              <Ico d={d} size={24} sw={1.9} fill={l === "Profile" ? "solid" : "none"} />
              <span style={{ font: `${l === "Profile" ? 700 : 500} 10px Inter` }}>{l}</span>
              {l === "Inbox" ? <span style={{ position: "absolute", right: 2, top: -2, width: 8, height: 8, borderRadius: 4, background: T.red }} /> : null}
            </div>
          ),
        )}
      </div>
    </div>
  );
};

// ------------------------------------------------------------------ Story frame
const StoryFrame: React.FC<{ user?: string; src?: string; body?: NestedBlock; caption?: string; progress?: number }> = ({ user = "anya.k", src, body, caption, progress = 3 }) => {
  const { f, dur } = useBlockTime();
  const p = clamp01(f / Math.max(1, dur));
  return (
    <div style={{ width: 390, height: 844, position: "relative", background: "#1C1813", overflow: "hidden", fontFamily: "Inter", color: "#EDE3D4" }}>
      {src ? <Img src={asset(src)} style={{ position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "cover" }} /> : <div style={{ position: "absolute", inset: 0 }}><Nested spec={body} w={390} h={844} bg="#2A2622" /></div>}
      <div style={{ position: "absolute", top: 54, left: 10, right: 10, display: "flex", gap: 4 }}>
        {Array.from({ length: progress }, (_, i) => (
          <div key={i} style={{ flex: 1, height: 3, borderRadius: 2, background: "rgba(237,227,212,0.35)", overflow: "hidden" }}>
            <div style={{ height: "100%", width: i < progress - 1 ? "100%" : `${p * 100}%`, background: "#EDE3D4" }} />
          </div>
        ))}
      </div>
      <div style={{ position: "absolute", top: 68, left: 12, display: "flex", alignItems: "center", gap: 8, font: `700 15px Inter` }}>
        <span style={{ width: 32, height: 32, borderRadius: 16, background: "#A9B79A" }} />
        {user} <span style={{ opacity: 0.6, fontWeight: 500 }}>2 ч</span>
      </div>
      {caption ? <div style={{ position: "absolute", left: 20, right: 20, bottom: 110, textAlign: "center", font: `700 22px Inter` }}>{caption}</div> : null}
      <div style={{ position: "absolute", left: 12, right: 12, bottom: 30, padding: "12px 16px", borderRadius: 24, border: "1px solid rgba(237,227,212,0.5)", font: `500 14px Inter`, opacity: 0.8 }}>Отправить сообщение</div>
    </div>
  );
};

// ------------------------------------------------------------------ PostCard (social post with counting reactions)
const PostCard: React.FC<{ name: string; handle?: string; text: string; likes?: number; reposts?: number; replies?: number; time?: string; w?: number }> = ({ name, handle, text, likes = 1200, reposts = 180, replies = 64, time = "2 ч", w = 900 }) => {
  const { f, fps } = useBlockTime();
  const th = useTheme();
  const k = E.outExpo(clamp01((f - 0.5 * fps) / (1.4 * fps)));
  return (
    <div style={{ width: w, padding: 34, borderRadius: 32, background: th.card, border: `1px solid ${th.cardBorder}`, boxShadow: th.cardShadow, color: th.cardInk, fontFamily: th.fontUi, boxSizing: "border-box" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 18 }}>
        <span style={{ width: 70, height: 70, borderRadius: 35, background: th.accent2 }} />
        <div>
          <div style={{ font: `800 34px ${th.fontUi}` }}>{name}</div>
          <div style={{ font: `500 28px ${th.fontUi}`, color: th.cardMuted }}>
            {handle ? `@${handle} · ` : ""}
            {time}
          </div>
        </div>
      </div>
      <div style={{ font: `600 40px ${th.fontUi}`, lineHeight: 1.3, marginTop: 22 }}>{text}</div>
      <div style={{ display: "flex", gap: 46, marginTop: 26, font: `600 30px ${th.fontUi}`, color: th.cardMuted }}>
        <span>💬 {fmtNumber(replies * k)}</span>
        <span>↻ {fmtNumber(reposts * k)}</span>
        <span style={{ color: th.accent }}>♥ {fmtNumber(likes * k, likes > 9999 ? "k" : "space")}</span>
      </div>
    </div>
  );
};

// ------------------------------------------------------------------ EmailCard
const EmailCard: React.FC<{ from: string; subject: string; preview?: string; time?: string; unread?: boolean }> = ({ from, subject, preview, time = "09:12", unread = true }) => {
  const th = useTheme();
  return (
    <div style={{ width: 900, padding: "28px 32px", borderRadius: 28, background: th.card, border: `1px solid ${th.cardBorder}`, boxShadow: th.cardShadow, fontFamily: th.fontUi, color: th.cardInk, boxSizing: "border-box", display: "flex", gap: 22 }}>
      {unread ? <span style={{ width: 16, height: 16, borderRadius: 8, background: th.accent, marginTop: 14, flexShrink: 0 }} /> : null}
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: "flex", justifyContent: "space-between", font: `800 34px ${th.fontUi}` }}>
          <span>{from}</span>
          <span style={{ font: `500 26px ${th.fontUi}`, color: th.cardMuted }}>{time}</span>
        </div>
        <div style={{ font: `700 32px ${th.fontUi}`, marginTop: 6 }}>{subject}</div>
        {preview ? <div style={{ font: `500 28px ${th.fontUi}`, color: th.cardMuted, marginTop: 6, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{preview}</div> : null}
      </div>
    </div>
  );
};

// ------------------------------------------------------------------ DynamicIsland (big, standalone)
const DynamicIsland: React.FC<{ title: string; sub?: string; icon?: string; actions?: string[]; expandAt?: unknown; pressAt?: unknown; w?: number }> = ({ title, sub, icon = "C", actions, expandAt, pressAt, w = 900 }) => {
  const { f, fps, at } = useBlockTime();
  const e0 = expandAt !== undefined ? at(expandAt) : Math.round(0.4 * fps);
  const p = clamp01(springAt(f - e0, fps, 0, SPR.ui));
  const pf = pressAt !== undefined ? at(pressAt) : -999;
  const wNow = lerp(300, w, p);
  const hNow = lerp(90, actions ? 300 : 200, p);
  return (
    <div style={{ width: wNow, height: hNow, borderRadius: lerp(45, 70, p), background: "#050505", color: "#EDE3D4", padding: lerp(20, 34, p), boxSizing: "border-box", overflow: "hidden", fontFamily: "Inter", boxShadow: "0 30px 80px -20px rgba(0,0,0,0.8)" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 22, opacity: clamp01(p * 1.5 - 0.3) }}>
        <AppIconGlyph letter={icon} size={86} />
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ font: `800 38px Inter`, whiteSpace: "nowrap" }}>{title}</div>
          {sub ? <div style={{ font: `500 30px Inter`, color: "#E08A55", whiteSpace: "nowrap" }}>{sub}</div> : null}
        </div>
      </div>
      {actions ? (
        <div style={{ display: "flex", gap: 16, marginTop: 30, opacity: clamp01(p * 2 - 1) }}>
          {actions.map((a, k) => (
            <div key={k} style={{ flex: 1, textAlign: "center", padding: "20px 0", borderRadius: 30, font: `700 32px Inter`, background: k === actions.length - 1 ? (f >= pf ? "#7FAF6A" : "#5E8A50") : "#3A3530", color: k === actions.length - 1 ? "#1E1712" : "#EDE3D4", transform: k === actions.length - 1 && f >= pf ? `scale(${1 - 0.06 * clamp01(1 - (f - pf) / 8)})` : undefined }}>
              {a}
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
};

// ------------------------------------------------------------------ EmergencyAlert: civil-defence alert screen (390x844)
const Trefoil: React.FC<{ size: number; color: string }> = ({ size, color }) => (
  <svg width={size} height={size} viewBox="-50 -50 100 100">
    <circle r="9" fill={color} />
    {[0, 120, 240].map((a) => (
      <path key={a} transform={`rotate(${a})`} d="M 0 -14 L 0 -46 A 46 46 0 0 1 39.8 23 L 12.1 7 A 14 14 0 0 0 0 -14 Z" fill={color} />
    ))}
  </svg>
);
const EmergencyAlert: React.FC<{ title?: string; text?: string; source?: string; time?: string; level?: string }> = ({
  title = "Угроза ядерного удара", text = "Немедленно спуститесь в подвал или убежище. Держитесь подальше от окон. Ждите указаний по радио.",
  source = "Экстренное оповещение", time = "сейчас", level = "КРАСНЫЙ УРОВЕНЬ",
}) => {
  const { f, fps } = useBlockTime();
  const pulse = 0.5 + 0.5 * Math.sin((f / fps) * Math.PI * 2 * 1.6);
  const appear = E.out(clamp01(f / (0.35 * fps)));
  return (
    <div style={{ width: 390, height: 844, background: "#17110E", color: "#EDE3D4", fontFamily: "Inter", overflow: "hidden", position: "relative" }}>
      <div style={{ position: "absolute", inset: 0, background: `radial-gradient(circle at 50% 30%, rgba(201,74,46,${0.18 + 0.22 * pulse}), transparent 62%)` }} />
      <div style={{ position: "relative", padding: "60px 26px 0", opacity: appear, transform: `translateY(${(1 - appear) * 30}px)` }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", font: "700 14px Inter", color: "#E9B49A", letterSpacing: 1.2 }}>
          <span>{source.toUpperCase()}</span><span style={{ opacity: 0.7 }}>{time}</span>
        </div>
        <div style={{ margin: "56px auto 0", width: 150, height: 150, borderRadius: 75, background: `rgba(201,74,46,${0.2 + 0.25 * pulse})`, display: "flex", alignItems: "center", justifyContent: "center", boxShadow: `0 0 ${40 + 40 * pulse}px rgba(201,74,46,0.55)` }}>
          <Trefoil size={96} color="#F2C2A6" />
        </div>
        <div style={{ marginTop: 40, display: "inline-block", background: "#C94A2E", color: "#1E1210", font: "800 13px Inter", letterSpacing: 1.4, padding: "6px 12px", borderRadius: 8 }}>{level}</div>
        <div style={{ marginTop: 16, font: "800 34px 'Inter Tight', Inter", lineHeight: 1.08 }}>{title}</div>
        <div style={{ marginTop: 16, font: "500 18px Inter", lineHeight: 1.45, color: "#D9C9B6" }}>{text}</div>
      </div>
      <div style={{ position: "absolute", left: 26, right: 26, bottom: 44, height: 54, borderRadius: 16, background: "#2A1F1A", display: "flex", alignItems: "center", justifyContent: "center", font: "700 17px Inter", color: "#E9B49A" }}>Понятно</div>
    </div>
  );
};

export const SCREEN_BLOCKS: Record<string, BlockDef> = {
  EmergencyAlert: defineBlock({ C: EmergencyAlert, cat: "ui", desc: "Civil-defence emergency alert screen (390×844) with pulsing radiation sign, level pill, title and instructions. Put it on IPhone17/Phone3D/Phone screens.", pos: "stage", self: true, sfx: null, example: {} }),
  Phone: defineBlock({ C: Phone, cat: "device", desc: "2D phone (flat, crisp): screen:{block,props} (use AppScreen/LockScreen/…) or src image; w, dark, tilt (deg), float.", pos: "stage", enter: "rise", sfx: "whoosh-airy", example: { screen: { block: "AppScreen", props: { sections: [{ type: "header", app: "Окно", title: "Запись" }, { type: "card", name: "Анна Ковалёва", sub: "Стрижка · 60 мин", value: "1 500 ₽" }, { type: "button", label: "Записаться" }] } } } }),
  Window: defineBlock({ C: Window, cat: "device", desc: "macOS window chrome; body:{block,props} or src; url:'…' turns it into a browser; tabs.", pos: "stage", enter: "rise", sfx: "whoosh-airy", example: { title: "Claude", url: "github.com/you/skill", body: { block: "Title", props: { text: "Окно" } } } }),
  AppScreen: defineBlock({
    C: AppScreen, cat: "ui", desc: "Mobile app screen builder (390×844): sections header|card|days|slots|rows|button|list|text|image|bars|search|gap. selectAt/pressAt anchors animate taps. Use inside Phone/Phone3D.", pos: "stage", self: true, sfx: null,
    events: (p, t) => ((p.sections ?? []) as { selectAt?: unknown; pressAt?: unknown }[]).flatMap((s) => [s.selectAt, s.pressAt].filter((x) => x !== undefined).map((a) => ({ f: t.at(a), id: "click-soft" }))),
    example: { sections: [{ type: "header", app: "Окно", title: "Запись" }, { type: "days", label: "Октябрь", days: [["Пн", "13"], ["Вт", "14"], ["Ср", "15"], ["Чт", "16"], ["Пт", "17"]], selected: 2 }, { type: "slots", label: "Свободное время", slots: ["10:00", "11:30", "13:00", "14:30", "16:00", "17:30"], selected: 3 }, { type: "rows", rows: [{ label: "Напоминание по SMS", value: "нет", status: "bad" }, { label: "Тариф", value: "+500 ₽", status: "bad" }] }, { type: "button", label: "Записаться" }] },
  }),
  ScreenGrid: defineBlock({
    C: ScreenGrid, cat: "ui", desc: "Map of an app's screens (cols×rows wireframes S01…) with a highlighted click path and a counter pill. label with Russian plural forms: «клик|клика|кликов до записи». h = max height (default 740).", pos: "stage", self: true, sfx: "pop-triple",
    events: (p, t) => ((p.path ?? []) as number[]).map((_, k) => ({ f: (p.pathAt !== undefined ? t.at(p.pathAt) : Math.round(0.8 * t.fps)) + Math.round(k * (p.step ?? 0.35) * t.fps), id: "click-tiny" })),
    example: { cols: 6, rows: 3, path: [0, 2, 8, 9, 14, 16], label: "клик|клика|кликов до записи" },
  }),
  ChatScreen: defineBlock({
    C: ChatScreen, cat: "ui", desc: "Messenger dialog (390×844, dark): contact name/sub/avatar letter, messages[{text, me, at, time, failAt}] — bubbles pop in at at; failAt turns a sent message into red «!» + «Не доставлено» (shows «Отправка…» before). Put it on IPhone17/Phone3D/Phone screens.",
    pos: "stage", self: true, sfx: null,
    events: (p, t) => ((p.messages ?? []) as { at?: unknown; failAt?: unknown }[]).flatMap((m, i) => [{ f: m.at !== undefined ? t.at(m.at) : Math.round(i * 0.6 * t.fps), id: "swipe-tiny" }, ...(m.failAt !== undefined ? [{ f: t.at(m.failAt), id: "error-buzz" }] : [])]),
    example: { name: "Мама", messages: [{ text: "Мам, ты где?", me: true, at: 0.3, failAt: 1.6 }] },
  }),
  LockScreen: defineBlock({ C: LockScreen, cat: "ui", desc: "Phone lock screen (390×844) with notifications; actions:['Отклонить','Разрешить'] + pressAt for an approval moment.", pos: "stage", self: true, sfx: null, events: (p, t) => ((p.notes ?? []) as { at?: unknown; pressAt?: unknown }[]).flatMap((n, i) => [{ f: n.at !== undefined ? t.at(n.at) : Math.round(i * 0.5 * t.fps), id: "chime-two-up" }, ...(n.pressAt !== undefined ? [{ f: t.at(n.pressAt), id: "success-check" }] : [])]), example: { notes: [{ app: "VS Code", text: "Claude ждёт разрешения", actions: ["Отклонить", "Разрешить"], pressAt: 1.6 }] } }),
  SocialProfile: defineBlock({ C: SocialProfile, cat: "social", desc: "Generic social profile screen (390×844) for the CTA end card: handle, bio lines, link (highlights at pressAt), tiles.", pos: "stage", self: true, sfx: null, example: { handle: "reel.studio", name: "Ролики, которые собирает агент", bio: ["Объяснялки с голосом", "Промо под музыку"], link: "t.me/reelstudio", tiles: [{ title: "Голос" }, { title: "3D" }, { title: "Промо" }] } }),
  TikTokProfile: defineBlock({
    C: TikTokProfile, cat: "social", desc: "The channel's TikTok profile (light theme, dark: true for TikTok's dark theme; 390×844, 2025 layout): name, @handle · badge, avatar, bio, link, tab icons, video grid (tiles: image srcs, pinned: n first tiles get the Pinned badge), bottom nav. highlightAt draws an accent frame + tap ripple round bio/link — the 'ссылка в шапке профиля' CTA. newTile {src,label,at}: a new video lands in the first cell (NEW badge) — 'продолжение в профиле'. stats only when the real numbers are worth showing. Put it on IPhone17 (enter:'flip').",
    pos: "stage", self: true, sfx: null, events: (p, t) => (p.highlightAt !== undefined ? [{ f: t.at(p.highlightAt), id: "pk-pop-ui-menu" }] : []),
    example: { highlightAt: 1.2 },
  }),
  StoryFrame: defineBlock({ C: StoryFrame, cat: "social", desc: "Story viewer (390×844): progress bars, user, photo src or body block, caption, reply bar.", pos: "stage", self: true }),
  PostCard: defineBlock({ C: PostCard, cat: "social", desc: "Social post card with counting replies/reposts/likes.", pos: "stage", enter: "rise", sfx: "pop-soft", events: () => [{ f: 30, id: "tick-roll", vol: 0.5 }], example: { name: "Мария", handle: "maria", text: "Попросила агента собрать ролик — и он собрал. С голосом." } }),
  EmailCard: defineBlock({ C: EmailCard, cat: "ui", desc: "Inbox email row card: from, subject, preview, unread dot.", pos: "stage", enter: "drop", sfx: "ding-soft", example: { from: "GitHub", subject: "Your repo got 1 000 stars", preview: "Congrats! replica-skill just passed…" } }),
  DynamicIsland: defineBlock({ C: DynamicIsland, cat: "ui", desc: "Big black Dynamic-Island pill expanding with icon/title/sub and optional action buttons (pressAt).", pos: "top", self: true, sfx: "swipe-tiny", events: (p, t) => [{ f: p.expandAt !== undefined ? t.at(p.expandAt) : Math.round(0.4 * t.fps), id: "pop-bubble" }, ...(p.pressAt !== undefined ? [{ f: t.at(p.pressAt), id: "success-check" }] : [])], example: { title: "Claude Code", sub: "требует разрешения", actions: ["Отклонить", "Разрешить"], pressAt: 1.8 } }),
};
