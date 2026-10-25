import React from "react";
import { useBlockTime, useTheme } from "../core/context";
import { E, SPR, clamp01, fmtNumber, lerp, springAt } from "../core/motion";
import { parseMarkup } from "../core/markup";
import type { Theme } from "../theme/styles";
import { defineBlock, type BlockDef } from "./registry";
import { tokLook } from "./text";

// ------------------------------------------------------------------ shared atoms
export const Card: React.FC<{ children: React.ReactNode; w?: number | string; pad?: number; style?: React.CSSProperties; th: Theme }> = ({ children, w = 900, pad = 36, style, th }) => (
  <div style={{ width: w, background: th.card, color: th.cardInk, borderRadius: th.radius, padding: pad, boxShadow: th.cardShadow, border: `1px solid ${th.cardBorder}`, boxSizing: "border-box", fontFamily: th.fontUi, ...style }}>{children}</div>
);

export const Stars: React.FC<{ n: number; of?: number; size?: number; color?: string; dim?: string }> = ({ n, of = 5, size = 30, color = "#E9A23B", dim }) => (
  <span style={{ display: "inline-flex", gap: size * 0.08 }}>
    {Array.from({ length: of }, (_, i) => (
      <svg key={i} width={size} height={size} viewBox="0 0 24 24">
        <path d="M12 2.2l2.95 6.3 6.85.75-5.1 4.65 1.4 6.75L12 17.2l-6.1 3.45 1.4-6.75L2.2 9.25l6.85-.75L12 2.2z" fill={i < n ? color : dim ?? "rgba(128,128,128,0.25)"} />
      </svg>
    ))}
  </span>
);

export const AppIconGlyph: React.FC<{ letter?: string; color?: string; size?: number; radius?: number; ink?: string }> = ({ letter = "A", color = "#E08A55", size = 84, radius, ink = "#1E1712" }) => (
  <div style={{ width: size, height: size, borderRadius: radius ?? size * 0.26, background: color, display: "flex", alignItems: "center", justifyContent: "center", font: `800 ${size * 0.5}px Inter, sans-serif`, color: ink, flexShrink: 0 }}>{letter}</div>
);

const Check: React.FC<{ p: number; size?: number; color: string; box?: string; ring?: string }> = ({ p, size = 40, color, box, ring }) => (
  <div style={{ width: size, height: size, borderRadius: size * 0.28, border: `3px solid ${p > 0 ? color : ring ?? "rgba(128,128,128,0.45)"}`, background: p > 0 ? color : box ?? "transparent", display: "flex", alignItems: "center", justifyContent: "center", transform: `scale(${1 + Math.sin(clamp01(p) * Math.PI) * 0.18})`, flexShrink: 0 }}>
    <svg width={size * 0.62} height={size * 0.62} viewBox="0 0 24 24" style={{ opacity: p > 0 ? 1 : 0 }}>
      <path d="M4 12.5l5 5L20 6.5" fill="none" stroke="#1E1712" strokeWidth={3.4} strokeLinecap="round" strokeLinejoin="round" strokeDasharray={24} strokeDashoffset={24 * (1 - clamp01(p))} />
    </svg>
  </div>
);

const appear = (f: number, s: number, fps: number, dur = 0.45) => {
  const p = E.out(clamp01((f - s) / (dur * fps)));
  return { p, style: { opacity: p, transform: `translateY(${(1 - p) * 40}px)`, filter: p < 1 ? `blur(${(1 - p) * 8}px)` : undefined } as React.CSSProperties };
};

// ------------------------------------------------------------------ Notification (+ stack)
type Notif = { app?: string; icon?: string; iconColor?: string; title?: string; text: string; time?: string; stars?: number; at?: unknown };

const NotifCard: React.FC<{ n: Notif; th: Theme; w?: number }> = ({ n, th, w = 860 }) => (
  <div style={{ width: w, display: "flex", gap: 26, alignItems: "flex-start", padding: "28px 32px", borderRadius: 40, background: th.glass, border: `1px solid ${th.cardBorder}`, boxShadow: th.cardShadow, backdropFilter: "blur(20px)", boxSizing: "border-box", fontFamily: th.fontUi }}>
    <AppIconGlyph letter={n.icon ?? (n.app ?? "A")[0]} color={n.iconColor ?? th.accent} size={84} />
    <div style={{ flex: 1, minWidth: 0 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", font: `600 30px ${th.fontUi}`, color: th.cardMuted }}>
        <span>
          {n.app ?? "App"}
          {n.time ? ` · ${n.time}` : ""}
        </span>
        {n.stars !== undefined ? <Stars n={n.stars} size={28} /> : null}
      </div>
      {n.title ? <div style={{ font: `700 36px ${th.fontUi}`, color: th.cardInk, marginTop: 6 }}>{n.title}</div> : null}
      <div style={{ font: `600 36px ${th.fontUi}`, color: th.cardInk, marginTop: 6, lineHeight: 1.22 }}>{n.text}</div>
    </div>
  </div>
);

const Notification: React.FC<Notif> = (n) => {
  const th = useTheme();
  return <NotifCard n={n} th={th} />;
};

const NotificationStack: React.FC<{ items: Notif[]; gap?: number; stagger?: number; newestOnTop?: boolean }> = ({ items, gap = 22, stagger = 0.7, newestOnTop = false }) => {
  const { f, fps, at } = useBlockTime();
  const th = useTheme();
  const list = items.map((n, i) => ({ n, s: n.at !== undefined ? at(n.at) : Math.round(i * stagger * fps) }));
  const shown = (newestOnTop ? [...list].reverse() : list).filter((x) => f >= x.s);
  return (
    <div style={{ display: "flex", flexDirection: "column", gap }}>
      {shown.map(({ n, s }, i) => {
        const sp = springAt(f - s, fps, 0, SPR.ui);
        return (
          <div key={i} style={{ transform: `translateY(${(1 - clamp01(sp)) * -80}px) scale(${lerp(0.92, 1, clamp01(sp))})`, opacity: clamp01(sp * 2) }}>
            <NotifCard n={n} th={th} />
          </div>
        );
      })}
    </div>
  );
};

// ------------------------------------------------------------------ Reviews
type Review = { source?: string; stars?: number; text: string; author?: string; at?: unknown; dim?: boolean; highlight?: string };
const SRC_COLORS: Record<string, string> = { "App Store": "#7FA2D9", "Google Play": "#8FBF86", Reddit: "#E58A62", "Отзовик": "#C9A35F", Telegram: "#7FB6D9" };

const ReviewCard: React.FC<Review & { w?: number }> = ({ source = "App Store", stars = 4, text, author, highlight, w = 900 }) => {
  const th = useTheme();
  const toks = highlight ? text.split(highlight) : [text];
  return (
    <Card th={th} w={w} pad={30} style={{ borderRadius: 30 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 18, marginBottom: 12 }}>
        <span style={{ font: `700 26px ${th.fontUi}`, color: "#1E1712", background: SRC_COLORS[source] ?? th.accent2, padding: "6px 14px", borderRadius: 10 }}>{source}</span>
        <Stars n={stars} size={28} />
        <span style={{ flex: 1 }} />
        {author ? <span style={{ font: `500 26px ${th.fontUi}`, color: th.cardMuted }}>{author}</span> : null}
      </div>
      <div style={{ font: `600 36px ${th.fontUi}`, lineHeight: 1.25, color: th.cardInk }}>
        {toks.length > 1 ? (
          <>
            {toks[0]}
            <span style={{ fontFamily: th.fontSerif, fontStyle: "italic", color: "#1E1712", background: th.accent, padding: "0 8px", borderRadius: 8 }}>{highlight}</span>
            {toks.slice(1).join(highlight)}
          </>
        ) : (
          text
        )}
      </div>
    </Card>
  );
};

const ReviewFeed: React.FC<{ items: Review[]; stagger?: number; focus?: { at: unknown; keep: number[] } }> = ({ items, stagger = 0.35, focus }) => {
  const { f, fps, at } = useBlockTime();
  const th = useTheme();
  const fAt = focus ? at(focus.at) : Infinity;
  const fp = E.inOut(clamp01((f - fAt) / (0.5 * fps)));
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
      {items.map((r, i) => {
        const s = r.at !== undefined ? at(r.at) : Math.round(i * stagger * fps);
        const a = appear(f, s, fps);
        const keep = !focus || focus.keep.includes(i);
        const hideP = keep ? 0 : fp;
        if (hideP >= 1) return null;
        return (
          <div key={i} style={{ ...a.style, opacity: a.p * (1 - hideP), maxHeight: lerp(400, 0, hideP), marginBottom: lerp(0, -20, hideP), transform: `${a.style.transform} scale(${keep && fp > 0 ? 1 + 0.02 * fp : 1})` }}>
            <ReviewCard {...r} />
          </div>
        );
      })}

    </div>
  );
};

// ------------------------------------------------------------------ Checklist
const Checklist: React.FC<{ title?: string; items: string[]; checkAt?: unknown[]; showAt?: unknown[]; w?: number }> = ({ title, items, checkAt = [], showAt = [], w = 880 }) => {
  const { f, fps, at } = useBlockTime();
  const th = useTheme();
  return (
    <Card th={th} w={w}>
      {title ? <div style={{ font: `700 32px ${th.fontUi}`, color: th.cardMuted, marginBottom: 22 }}>{title}</div> : null}
      <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
        {items.map((it, i) => {
          const s = showAt[i] !== undefined ? at(showAt[i]) : Math.round(i * 0.18 * fps);
          const a = appear(f, s, fps, 0.4);
          const cp = checkAt[i] !== undefined ? clamp01((f - at(checkAt[i])) / (0.35 * fps)) : 0;
          return (
            <div key={i} style={{ ...a.style, display: "flex", alignItems: "center", gap: 22, padding: "20px 24px", borderRadius: 20, background: th.dark ? "rgba(255,255,255,0.04)" : "rgba(0,0,0,0.03)" }}>
              <Check p={cp} color={th.accent} />
              <span style={{ font: `700 38px ${th.fontUi}`, color: th.cardInk, opacity: cp > 0 ? 0.62 : 1 }}>{it}</span>
            </div>
          );
        })}
      </div>
    </Card>
  );
};

// ------------------------------------------------------------------ ScoreCard ("Сходство 62%")
const ScoreCard: React.FC<{ label: string; value: number; from?: number; unit?: string; status?: string; good?: boolean; cons?: string[]; pros?: string[]; dur?: number; w?: number }> = ({
  label, value, from = 0, unit = "%", status, good, cons = [], pros = [], dur = 1.6, w = 620,
}) => {
  const { f, fps } = useBlockTime();
  const th = useTheme();
  const p = E.outExpo(clamp01((f - 4) / (dur * fps)));
  const v = lerp(from, value, p);
  const ok = good ?? value >= 80;
  const col = ok ? th.pos : th.neg;
  const after = clamp01((f - (dur * fps + 4)) / (0.4 * fps));
  return (
    <Card th={th} w={w} pad={40}>
      <div style={{ font: `700 34px ${th.fontUi}`, color: th.cardMuted, lineHeight: 1.15 }}>{label}</div>
      <div style={{ display: "flex", alignItems: "baseline", marginTop: 10 }}>
        <span style={{ font: `800 168px ${th.fontDisplay}`, letterSpacing: "-0.06em", color: col, lineHeight: 1, fontVariantNumeric: "tabular-nums" }}>{Math.round(v)}</span>
        <span style={{ font: `800 84px ${th.fontDisplay}`, color: col }}>{unit}</span>
      </div>
      <div style={{ height: 16, borderRadius: 8, background: th.dark ? "rgba(255,255,255,0.08)" : "rgba(0,0,0,0.06)", marginTop: 18, overflow: "hidden" }}>
        <div style={{ height: "100%", width: `${v}%`, background: col, borderRadius: 8 }} />
      </div>
      {status ? (
        <div style={{ marginTop: 26, opacity: after, font: `700 34px ${th.fontUi}`, color: col, background: `${col}22`, padding: "12px 18px", borderRadius: 14 }}>{status}</div>
      ) : null}
      {[...cons.map((c) => ["✕", c, th.neg] as const), ...pros.map((c) => ["✓", c, th.pos] as const)].map(([m, c, colr], i) => {
        const a = clamp01((f - (dur * fps + 10 + i * 6)) / 10);
        return (
          <div key={i} style={{ marginTop: 16, display: "flex", gap: 16, alignItems: "center", opacity: a, transform: `translateX(${(1 - a) * -20}px)`, font: `700 36px ${th.fontUi}`, color: th.cardInk }}>
            <span style={{ color: colr }}>{m}</span>
            {c}
          </div>
        );
      })}
    </Card>
  );
};

// ------------------------------------------------------------------ PricingCards
type Tier = { name: string; price: string; period?: string; features?: string[]; hot?: boolean; strike?: string };
const PricingCards: React.FC<{ tiers: Tier[]; stagger?: number }> = ({ tiers, stagger = 0.18 }) => {
  const { f, fps } = useBlockTime();
  const th = useTheme();
  const w = tiers.length >= 3 ? 300 : 420;
  return (
    <div style={{ display: "flex", gap: 22, alignItems: "stretch" }}>
      {tiers.map((t, i) => {
        const a = appear(f, Math.round(i * stagger * fps), fps);
        return (
          <div key={i} style={{ ...a.style, width: w, padding: 30, borderRadius: 30, background: t.hot ? th.accent : th.card, color: t.hot ? "#1E1712" : th.cardInk, border: `1px solid ${th.cardBorder}`, boxShadow: th.cardShadow, fontFamily: th.fontUi, boxSizing: "border-box", transform: `${a.style.transform} scale(${t.hot ? 1.05 : 1})` }}>
            <div style={{ font: `700 32px ${th.fontUi}`, opacity: 0.75 }}>{t.name}</div>
            {t.strike ? <div style={{ font: `600 34px ${th.fontUi}`, opacity: 0.55, textDecoration: "line-through", marginTop: 10 }}>{t.strike}</div> : null}
            <div style={{ font: `800 ${Math.min(w < 320 ? 64 : 80, Math.floor((w - 60) / Math.max(1, (t.price.length + (t.period ? t.period.length * 0.45 : 0)) * 0.6)))}px ${th.fontDisplay}`, letterSpacing: "-0.04em", marginTop: 6, whiteSpace: "nowrap" }}>
              {t.price}
              {t.period ? <span style={{ font: `600 28px ${th.fontUi}`, opacity: 0.65 }}> {t.period}</span> : null}
            </div>
            <div style={{ marginTop: 16, display: "flex", flexDirection: "column", gap: 10 }}>
              {(t.features ?? []).map((ft, k) => (
                <div key={k} style={{ font: `600 28px ${th.fontUi}`, opacity: 0.9 }}>· {ft}</div>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
};

// ------------------------------------------------------------------ Toast
const Toast: React.FC<{ text: string; icon?: "check" | "dot" | "warn"; color?: string }> = ({ text, icon = "check", color }) => {
  const th = useTheme();
  const c = color ?? (icon === "warn" ? th.neg : th.pos);
  return (
    <div style={{ display: "inline-flex", alignItems: "center", gap: 18, padding: "20px 30px", borderRadius: 999, background: th.card, border: `1px solid ${th.cardBorder}`, boxShadow: th.cardShadow, font: `700 36px ${th.fontUi}`, color: th.cardInk }}>
      <span style={{ width: 40, height: 40, borderRadius: 20, background: c, display: "flex", alignItems: "center", justifyContent: "center", color: "#1E1712", font: `900 26px ${th.fontUi}` }}>{icon === "check" ? "✓" : icon === "warn" ? "!" : ""}</span>
      {text}
    </div>
  );
};

// ------------------------------------------------------------------ Cursor: moves along points, clicks with ripple (overlay)
type CPt = { x: number; y: number; at?: unknown; click?: boolean };
const Cursor: React.FC<{ points: CPt[]; size?: number; color?: string; hand?: boolean }> = ({ points, size = 56, color = "#F2E8DA", hand = false }) => {
  const { f, fps, at } = useBlockTime();
  const pts = points.map((p, i) => ({ ...p, f: p.at !== undefined ? at(p.at) : Math.round(i * 0.8 * fps) }));
  let x = pts[0].x;
  let y = pts[0].y;
  for (let i = 0; i < pts.length - 1; i++) {
    const a = pts[i];
    const b = pts[i + 1];
    if (f >= a.f) {
      const move = Math.max(8, Math.min(b.f - a.f, Math.round(0.55 * fps)));
      const p = E.inOut(clamp01((f - (b.f - move)) / move));
      x = lerp(a.x, b.x, p);
      y = lerp(a.y, b.y, p);
    }
  }
  if (f >= pts[pts.length - 1].f) {
    x = pts[pts.length - 1].x;
    y = pts[pts.length - 1].y;
  }
  const clicks = pts.filter((p) => p.click !== false && p !== pts[0]).map((p) => p.f);
  const last = clicks.filter((c) => f >= c).pop();
  const press = last !== undefined ? clamp01(1 - (f - last) / 8) : 0;
  const ring = last !== undefined ? clamp01((f - last) / 22) : 1;
  return (
    <div style={{ position: "absolute", inset: 0, pointerEvents: "none" }}>
      {ring < 1 ? <div style={{ position: "absolute", left: x - 70 * ring, top: y - 70 * ring, width: 140 * ring, height: 140 * ring, borderRadius: "50%", border: `4px solid ${color}`, opacity: 1 - ring }} /> : null}
      <svg width={size} height={size} viewBox="0 0 24 24" style={{ position: "absolute", left: x - 6, top: y - 3, transform: `scale(${1 - press * 0.15})`, transformOrigin: "6px 3px", filter: "drop-shadow(0 4px 10px rgba(0,0,0,0.45))" }}>
        {hand ? (
          <path d="M9 11V5.5a1.5 1.5 0 013 0V10m0-1.5a1.5 1.5 0 013 0V11m0-1a1.5 1.5 0 013 0v4.5a6 6 0 01-6 6h-1a6 6 0 01-5-2.7L4 15a1.6 1.6 0 012.6-1.8L9 15" fill={color} stroke="#1E1712" strokeWidth="1.2" />
        ) : (
          <path d="M3 2l7.5 19 2.6-7.9L21 10.5 3 2z" fill={color} stroke="#1E1712" strokeWidth="1.3" strokeLinejoin="round" />
        )}
      </svg>
    </div>
  );
};

// ------------------------------------------------------------------ Callout: label with a leader line to a point (overlay)
const Callout: React.FC<{ text: string; x: number; y: number; lx: number; ly: number; at?: unknown }> = ({ text, x, y, lx, ly }) => {
  const { f, fps } = useBlockTime();
  const th = useTheme();
  const p = E.inOut(clamp01(f / (0.5 * fps)));
  const q = E.out(clamp01((f - 0.35 * fps) / (0.4 * fps)));
  return (
    <div style={{ position: "absolute", inset: 0, pointerEvents: "none" }}>
      <svg width={1080} height={1920} style={{ position: "absolute", left: 0, top: 0 }}>
        <circle cx={x} cy={y} r={10 * p} fill={th.accent} />
        <line x1={x} y1={y} x2={lerp(x, lx, p)} y2={lerp(y, ly, p)} stroke={th.accent} strokeWidth={4} strokeLinecap="round" />
      </svg>
      <div style={{ position: "absolute", left: lx, top: ly, transform: `translate(${lx > x ? 0 : -100}%, -50%) scale(${lerp(0.8, 1, q)})`, opacity: q, font: `700 34px ${th.fontUi}`, color: "#1E1712", background: th.accent, padding: "12px 20px", borderRadius: 14, whiteSpace: "nowrap" }}>{text}</div>
    </div>
  );
};

// ------------------------------------------------------------------ SearchBar with typed query + results
const SearchBar: React.FC<{ query: string; results?: string[]; cps?: number; placeholder?: string }> = ({ query, results = [], cps = 16, placeholder = "Поиск" }) => {
  const { f, fps } = useBlockTime();
  const th = useTheme();
  const n = Math.max(0, Math.floor(((f - 8) / fps) * cps));
  const typed = query.slice(0, n);
  const done = n >= query.length;
  const doneF = 8 + (query.length / cps) * fps;
  return (
    <div style={{ width: 880 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 20, padding: "26px 30px", borderRadius: 26, background: th.card, border: `1px solid ${th.cardBorder}`, boxShadow: th.cardShadow, font: `600 40px ${th.fontUi}`, color: typed ? th.cardInk : th.cardMuted }}>
        <svg width={40} height={40} viewBox="0 0 24 24">
          <circle cx="10.5" cy="10.5" r="6.5" fill="none" stroke={th.cardMuted} strokeWidth="2.4" />
          <path d="M15.5 15.5L21 21" stroke={th.cardMuted} strokeWidth="2.4" strokeLinecap="round" />
        </svg>
        <span>{typed || placeholder}</span>
        {!done ? <span style={{ width: 3, height: 44, background: th.accent, opacity: Math.floor(f / 15) % 2 ? 1 : 0 }} /> : null}
      </div>
      {results.length ? (
        <div style={{ marginTop: 14, borderRadius: 24, background: th.card, border: `1px solid ${th.cardBorder}`, overflow: "hidden", opacity: clamp01((f - doneF) / 10) }}>
          {results.map((r, i) => {
            const a = clamp01((f - doneF - i * 4) / 10);
            return (
              <div key={i} style={{ padding: "22px 30px", borderTop: i ? `1px solid ${th.cardBorder}` : undefined, font: `600 34px ${th.fontUi}`, color: th.cardInk, opacity: a, background: i === 0 ? `${th.accent}1F` : undefined }}>{r}</div>
            );
          })}
        </div>
      ) : null}
    </div>
  );
};

// ------------------------------------------------------------------ Toggles (settings switching on)
const Toggles: React.FC<{ items: string[]; onAt?: unknown[] }> = ({ items, onAt = [] }) => {
  const { f, fps, at } = useBlockTime();
  const th = useTheme();
  return (
    <Card th={th} w={860} pad={14}>
      {items.map((it, i) => {
        const p = onAt[i] !== undefined ? E.inOut(clamp01((f - at(onAt[i])) / (0.25 * fps))) : 0;
        return (
          <div key={i} style={{ display: "flex", alignItems: "center", padding: "24px 26px", borderTop: i ? `1px solid ${th.cardBorder}` : undefined, font: `600 38px ${th.fontUi}` }}>
            <span style={{ flex: 1 }}>{it}</span>
            <div style={{ width: 104, height: 60, borderRadius: 30, background: p > 0.5 ? th.pos : th.dark ? "rgba(255,255,255,0.14)" : "rgba(0,0,0,0.12)", position: "relative" }}>
              <div style={{ position: "absolute", top: 5, left: lerp(5, 49, p), width: 50, height: 50, borderRadius: 25, background: "#EFE6D8", boxShadow: "0 2px 6px rgba(0,0,0,0.3)" }} />
            </div>
          </div>
        );
      })}
    </Card>
  );
};

// ------------------------------------------------------------------ Timeline / Steps
const Steps: React.FC<{ items: { title: string; sub?: string }[]; showAt?: unknown[]; numbered?: boolean }> = ({ items, showAt = [], numbered = true }) => {
  const { f, fps, at } = useBlockTime();
  const th = useTheme();
  const times = items.map((_, i) => (showAt[i] !== undefined ? at(showAt[i]) : Math.round(i * 0.5 * fps)));
  const prog = clamp01(times.filter((t) => f >= t).length / items.length);
  return (
    <div style={{ position: "relative", width: 880, paddingLeft: 40 }}>
      <div style={{ position: "absolute", left: 78, top: 40, bottom: 40, width: 6, borderRadius: 3, background: th.dark ? "rgba(255,255,255,0.08)" : "rgba(0,0,0,0.08)" }}>
        <div style={{ width: "100%", height: `${prog * 100}%`, background: th.accent, borderRadius: 3 }} />
      </div>
      {items.map((it, i) => {
        const a = appear(f, times[i], fps);
        const done = f >= times[i];
        return (
          <div key={i} style={{ ...a.style, display: "flex", gap: 30, alignItems: "center", marginBottom: 34, position: "relative" }}>
            <div style={{ width: 80, height: 80, borderRadius: 40, background: done ? th.accent : th.card, border: `2px solid ${th.cardBorder}`, display: "flex", alignItems: "center", justifyContent: "center", font: `800 36px ${th.fontUi}`, color: done ? "#1E1712" : th.cardMuted, flexShrink: 0 }}>{numbered ? i + 1 : "•"}</div>
            <div>
              <div style={{ font: `800 46px ${th.fontDisplay}`, color: th.ink, letterSpacing: "-0.02em" }}>{it.title}</div>
              {it.sub ? <div style={{ font: `600 32px ${th.fontUi}`, color: th.muted, marginTop: 4 }}>{it.sub}</div> : null}
            </div>
          </div>
        );
      })}
    </div>
  );
};

// ------------------------------------------------------------------ CompareSplit (before / after)
const CompareSplit: React.FC<{ left: { title: string; items: string[] }; right: { title: string; items: string[] }; revealAt?: unknown }> = ({ left, right, revealAt }) => {
  const { f, fps, at } = useBlockTime();
  const th = useTheme();
  const r = revealAt !== undefined ? at(revealAt) : Math.round(0.8 * fps);
  const col = (side: typeof left, good: boolean, s: number) => {
    const a = appear(f, s, fps);
    return (
      <div style={{ ...a.style, flex: 1, padding: 30, borderRadius: 30, background: good ? th.card : th.dark ? "rgba(255,255,255,0.03)" : "rgba(0,0,0,0.03)", border: `1px solid ${good ? th.accent + "66" : th.cardBorder}`, boxShadow: good ? th.cardShadow : undefined }}>
        <div style={{ font: `800 40px ${th.fontDisplay}`, color: good ? th.accent : th.muted, marginBottom: 18 }}>{side.title}</div>
        {side.items.map((it, i) => (
          <div key={i} style={{ display: "flex", gap: 14, font: `600 32px ${th.fontUi}`, color: good ? th.cardInk : th.muted, marginBottom: 14, opacity: clamp01((f - s - 6 - i * 4) / 8) }}>
            <span style={{ color: good ? th.pos : th.neg }}>{good ? "✓" : "✕"}</span>
            {it}
          </div>
        ))}
      </div>
    );
  };
  return (
    <div style={{ display: "flex", gap: 22, width: 940 }}>
      {col(left, false, 0)}
      {col(right, true, r)}
    </div>
  );
};

// ------------------------------------------------------------------ ProgressBar / install
const Progress: React.FC<{ label?: string; to?: number; dur?: number; done?: string }> = ({ label = "Установка", to = 100, dur = 2.2, done }) => {
  const { f, fps } = useBlockTime();
  const th = useTheme();
  const p = E.inOut(clamp01(f / (dur * fps))) * to;
  const finished = p >= 99.5;
  return (
    <Card th={th} w={820}>
      <div style={{ display: "flex", justifyContent: "space-between", font: `700 36px ${th.fontUi}` }}>
        <span>{finished && done ? done : label}</span>
        <span style={{ color: finished ? th.pos : th.cardMuted, fontVariantNumeric: "tabular-nums" }}>{Math.round(p)}%</span>
      </div>
      <div style={{ height: 18, borderRadius: 9, background: th.dark ? "rgba(255,255,255,0.08)" : "rgba(0,0,0,0.07)", marginTop: 22, overflow: "hidden" }}>
        <div style={{ height: "100%", width: `${p}%`, borderRadius: 9, background: finished ? th.pos : th.accent }} />
      </div>
    </Card>
  );
};

// ------------------------------------------------------------------ AvatarStack + count
const AvatarStack: React.FC<{ count?: number; label?: string; n?: number }> = ({ count = 5, label, n }) => {
  const { f, fps } = useBlockTime();
  const th = useTheme();
  const cols = ["#8E7264", "#6A7884", "#76836D", "#7E6A78", "#A08A62", "#A15E44"];
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 26 }}>
      <div style={{ display: "flex" }}>
        {Array.from({ length: count }, (_, i) => {
          const sp = clamp01(springAt(f, fps, i * 4, SPR.pop));
          return <div key={i} style={{ width: 96, height: 96, borderRadius: 48, background: cols[i % cols.length], border: `5px solid ${th.bg}`, marginLeft: i ? -26 : 0, transform: `scale(${sp})`, display: "flex", alignItems: "center", justifyContent: "center", font: `800 38px ${th.fontUi}`, color: "#1E1712" }}>{"АБВГДЕЖЗ"[i % 8]}</div>;
        })}
      </div>
      {label ? (
        <div style={{ font: `700 40px ${th.fontUi}`, color: th.ink }}>
          {n !== undefined ? <span style={{ color: th.accent }}>{fmtNumber(lerp(0, n, E.outExpo(clamp01(f / (1.2 * fps)))))} </span> : null}
          {label}
        </div>
      ) : null}
    </div>
  );
};

// ------------------------------------------------------------------ Quote bubble from a speaker (chat-like single bubble)
const Bubble: React.FC<{ text: string; side?: "left" | "right"; name?: string; color?: string }> = ({ text, side = "left", name, color }) => {
  const th = useTheme();
  const toks = parseMarkup(text);
  return (
    <div style={{ maxWidth: 820, alignSelf: side === "left" ? "flex-start" : "flex-end" }}>
      {name ? <div style={{ font: `600 28px ${th.fontUi}`, color: th.muted, margin: "0 0 8px 18px" }}>{name}</div> : null}
      <div style={{ padding: "24px 30px", borderRadius: 34, borderBottomLeftRadius: side === "left" ? 8 : 34, borderBottomRightRadius: side === "right" ? 8 : 34, background: color ?? (side === "right" ? th.accent : th.card), color: side === "right" ? "#1E1712" : th.cardInk, font: `600 38px ${th.fontUi}`, lineHeight: 1.25, boxShadow: th.cardShadow }}>
        {toks.map((t, i) => (
          <span key={i} style={tokLook(t, th, 38, side === "right" ? "#1E1712" : th.cardInk, 100, 0)}>
            {t.text}{" "}
          </span>
        ))}
      </div>
    </div>
  );
};

export const UI_BLOCKS: Record<string, BlockDef> = {
  Notification: defineBlock({ C: Notification, cat: "ui", desc: "iOS-style notification banner: app, icon, time, title, text, stars.", pos: "stage", enter: "drop", sfx: "ding-soft", example: { app: "Slotra · новый отзыв", text: "Доплата за каждого сотрудника. Серьёзно?", stars: 1 } }),
  NotificationStack: defineBlock({
    C: NotificationStack, cat: "ui", desc: "Notifications dropping in one by one (items[].at anchors).", pos: "stage", self: true,
    events: (p, t) => ((p.items ?? []) as { at?: unknown }[]).map((n, i) => ({ f: n.at !== undefined ? t.at(n.at) : Math.round(i * (p.stagger ?? 0.7) * t.fps), id: "chime-message", vol: 0.55 })),
    example: { items: [{ app: "Slotra · новый отзыв", text: "Доплата за каждого сотрудника", stars: 1 }, { app: "Slotra · новый отзыв", text: "Клиенты забывают про запись", stars: 2 }] },
  }),
  ReviewCard: defineBlock({ C: ReviewCard, cat: "ui", desc: "Review card: source badge (App Store/Google Play/Reddit/…), stars, text, optional highlight phrase.", pos: "stage", enter: "rise", sfx: "pop-soft", example: { source: "Google Play", stars: 3, text: "Удобно, но клиенты из другого города путают время", highlight: "путают время" } }),
  ReviewFeed: defineBlock({
    C: ReviewFeed, cat: "ui", desc: "List of reviews appearing; focus:{at, keep:[idx]} collapses the rest (filtering).", pos: "stage", self: true,
    events: (p, t) => [...((p.items ?? []) as { at?: unknown }[]).map((r, i) => ({ f: r.at !== undefined ? t.at(r.at) : Math.round(i * (p.stagger ?? 0.35) * t.fps), id: "pop-soft", vol: 0.5 })), ...(p.focus ? [{ f: t.at(p.focus.at), id: "swipe-soft" }] : [])],
    example: { items: [{ source: "App Store", stars: 5, text: "Отличное приложение!" }, { source: "App Store", stars: 4, text: "Нравится, но нет напоминаний" }, { source: "Reddit", stars: 1, text: "Подняли цену. Ухожу" }], focus: { at: 1.8, keep: [1] } },
  }),
  Checklist: defineBlock({
    C: Checklist, cat: "ui", desc: "Plan / todo list; checkAt[] anchors tick boxes.", pos: "stage", enter: "rise", sfx: "paper-rustle",
    events: (p, t) => ((p.checkAt ?? []) as unknown[]).map((a) => ({ f: t.at(a), id: "success-check" })),
    example: { title: "План исправлений", items: ["Напоминания по SMS", "Одна цена для команды", "Часовой пояс"], checkAt: [1, 1.5, 2] },
  }),
  ScoreCard: defineBlock({ C: ScoreCard, cat: "ui", desc: "Big percentage card with bar, status pill and ✕/✓ lists (e.g. «Сходство с оригиналом 62%»).", pos: "right", enter: "rise", sfx: null, events: (p, t) => [{ f: 4, id: "tick-roll", vol: 0.6 }, { f: Math.round((p.dur ?? 1.6) * t.fps) + 4, id: p.good ?? p.value >= 80 ? "success-soft" : "error-down", vol: 0.6 }], example: { label: "Сходство с оригиналом", value: 62, status: "Не готово к выкладке", cons: ["Перенос записи", "Онлайн-оплата"] } }),
  PricingCards: defineBlock({ C: PricingCards, cat: "ui", desc: "2–3 pricing tiers, `hot` tier highlighted, `strike` old price.", pos: "stage", self: true, sfx: "pop-triple", example: { tiers: [{ name: "Старт", price: "0 ₽" }, { name: "Про", price: "990 ₽", period: "/мес", hot: true }, { name: "Команда", price: "+500 ₽", period: "/чел" }] } }),
  Toast: defineBlock({ C: Toast, cat: "ui", desc: "Small confirmation toast pill (check/warn/dot).", pos: "bottom", enter: "pop", sfx: "success-soft", example: { text: "Скилл установлен" } }),
  Cursor: defineBlock({
    C: Cursor, cat: "ui", overlay: true, pos: "full", self: true, sfx: null,
    desc: "OVERLAY mouse pointer (or hand:true) gliding through points [{x,y,at,click}] in frame px, ripple on clicks.",
    events: (p, t) => ((p.points ?? []) as { at?: unknown; click?: boolean }[]).slice(1).filter((q) => q.click !== false).map((q, i) => ({ f: q.at !== undefined ? t.at(q.at) : Math.round((i + 1) * 0.8 * t.fps), id: "click-mouse" })),
    example: { points: [{ x: 300, y: 1300 }, { x: 640, y: 900, at: 1 }, { x: 520, y: 1100, at: 2 }] },
  }),
  Callout: defineBlock({ C: Callout, cat: "ui", overlay: true, pos: "full", self: true, sfx: "pop-high", desc: "OVERLAY label with leader line from point (x,y) to label (lx,ly), frame px.", example: { text: "вот здесь", x: 540, y: 1000, lx: 760, ly: 820 } }),
  SearchBar: defineBlock({ C: SearchBar, cat: "ui", desc: "Search field typing a query, then results drop down (first highlighted).", pos: "stage", enter: "rise", sfx: null, events: (p) => [{ f: 8, id: (p.query ?? "").length > 18 ? "typing-medium" : "typing-short" }], example: { query: "клиника рядом", results: ["Клиника на Ленина, 4.8", "Медцентр «Здоровье», 4.6"] } }),
  Toggles: defineBlock({ C: Toggles, cat: "ui", desc: "Settings list whose switches flip on at onAt[] anchors.", pos: "stage", enter: "rise", sfx: null, events: (p, t) => ((p.onAt ?? []) as unknown[]).map((a) => ({ f: t.at(a), id: "toggle-on" })), example: { items: ["Напоминания", "Онлайн-оплата", "Отзывы"], onAt: [0.8, 1.2, 1.6] } }),
  Steps: defineBlock({ C: Steps, cat: "ui", desc: "Numbered steps on a progress rail; showAt[] anchors.", pos: "stage", self: true, events: (p, t) => ((p.items ?? []) as unknown[]).map((_, i) => ({ f: p.showAt?.[i] !== undefined ? t.at(p.showAt[i]) : Math.round(i * 0.5 * t.fps), id: "tick-soft" })), example: { items: [{ title: "Скажи Claude", sub: "«поставь скилл»" }, { title: "Он сам установит" }, { title: "Пользуйся" }] } }),
  CompareSplit: defineBlock({ C: CompareSplit, cat: "ui", desc: "Before/after columns with ✕ and ✓ lists; right side revealed at revealAt.", pos: "stage", self: true, sfx: "swipe-soft", example: { left: { title: "Было", items: ["3 часа монтажа", "шаблоны"] }, right: { title: "Стало", items: ["10 минут", "свой стиль"] } } }),
  Progress: defineBlock({ C: Progress, cat: "ui", desc: "Progress / install bar counting to 100% then `done` text.", pos: "stage", enter: "rise", sfx: null, events: (p, t) => [{ f: Math.round((p.dur ?? 2.2) * t.fps), id: "success-pluck" }], example: { label: "Устанавливаю скилл", done: "Готово" } }),
  AvatarStack: defineBlock({ C: AvatarStack, cat: "ui", desc: "Overlapping avatars + counting label (users, stars, team).", pos: "stage", self: true, sfx: "pop-triple", example: { count: 5, n: 4800, label: "человек уже пользуются" } }),
  Bubble: defineBlock({ C: Bubble, cat: "ui", desc: "Single chat/speech bubble (left/right), markup supported.", pos: "stage", enter: "pop", sfx: "pop-bubble", example: { text: "А можно *без* монтажа?", side: "right" } }),
};
