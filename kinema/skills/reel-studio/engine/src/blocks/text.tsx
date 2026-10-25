import { measureText } from "@remotion/layout-utils";
import React from "react";
import { random } from "remotion";
import { useBlockTime, useTheme } from "../core/context";
import { E, SPR, clamp01, fmtNumber, lerp, prog, springAt } from "../core/motion";
import { parseMarkup, type Tok } from "../core/markup";
import type { Theme } from "../theme/styles";
import { asset } from "./bg";
import { pluralize } from "./plural";
import { defineBlock, type BlockDef } from "./registry";

const MAXW = 920;

export const fit = (text: string, family: string, weight: number, maxW: number, max: number, min = 40, tracking = "-0.03em") => {
  let lo = min;
  let hi = max;
  for (let k = 0; k < 14; k++) {
    const mid = (lo + hi) / 2;
    const w = measureText({ text, fontFamily: family, fontSize: mid, fontWeight: weight, letterSpacing: tracking, validateFontIsLoaded: false }).width;
    if (w * 1.03 <= maxW) lo = mid;
    else hi = mid;
  }
  return Math.floor(lo);
};

export const tokLook = (t: Tok, th: Theme, size: number, ink: string, f = 0, revealF = 0): React.CSSProperties => {
  const s: React.CSSProperties = { color: ink };
  const st = t.style;
  if (st.includes("italic")) Object.assign(s, { fontFamily: th.fontSerif, fontStyle: "italic", fontWeight: th.serifWeight, letterSpacing: "-0.01em", fontSize: size * 1.1, textTransform: "none" });
  if (st.includes("accent")) s.color = th.accent;
  if (st.includes("alt")) s.color = th.accent2;
  if (st.includes("neg")) s.color = th.neg;
  if (st.includes("pos")) s.color = th.pos;
  if (st.includes("outline")) Object.assign(s, { color: "transparent", WebkitTextStroke: `${Math.max(2, size / 30)}px ${ink}` });
  if (st.includes("mark")) {
    const p = E.out(clamp01((f - revealF) / 16));
    Object.assign(s, {
      color: p > 0.4 ? th.markInk : s.color === th.markBg ? ink : s.color,
      backgroundImage: `linear-gradient(${th.markBg}, ${th.markBg})`,
      backgroundRepeat: "no-repeat",
      backgroundSize: `${p * 100}% 100%`,
      padding: "0 0.14em 0.04em",
      borderRadius: "0.16em",
    });
  }
  return s;
};

// ------------------------------------------------------------------ Title: blur-in words, markup aware
const Title: React.FC<{
  text: string; lead?: string; size?: number; align?: "center" | "left"; stagger?: number; color?: string; leadColor?: string;
  weight?: number; upper?: boolean; at?: unknown[]; lineHeight?: number; maxWidth?: number;
}> = ({ text, lead, size, align = "center", stagger = 0.09, color, leadColor, weight, upper, at, lineHeight = 1.04, maxWidth = MAXW }) => {
  const { f, fps, at: resolveAt } = useBlockTime();
  const th = useTheme();
  const toks = parseMarkup(text);
  const ink = color ?? th.ink;
  const plainT = toks.map((t) => t.text).join(" ");
  const sz = size ?? Math.min(130, fit(plainT, th.fontDisplay, weight ?? th.displayWeight, maxWidth * (plainT.length > 18 ? 1.8 : 1), 130, 56, th.displayTracking));
  const lines: Tok[][] = [];
  toks.forEach((t) => (lines[t.line] ??= []).push(t));
  let k = 0;
  return (
    <div style={{ textAlign: align, maxWidth, width: "100%" }}>
      {lead ? (
        <div style={{ font: `600 ${Math.round(sz * 0.42)}px ${th.fontDisplay}`, color: leadColor ?? th.muted, letterSpacing: "-0.015em", marginBottom: sz * 0.14, opacity: E.out(clamp01(f / 14)), filter: `blur(${(1 - E.out(clamp01(f / 14))) * 10}px)` }}>
          {lead}
        </div>
      ) : null}
      {lines.filter(Boolean).map((ln, li) => (
        <div key={li} style={{ textWrap: "balance" } as React.CSSProperties}>
          {ln.map((t, ti) => {
            const idx = k++;
            const startF = at?.[idx] !== undefined ? resolveAt(at[idx]) : Math.round(idx * stagger * fps) + (lead ? 6 : 0);
            const p = E.out(clamp01((f - startF) / (0.34 * fps)));
            return (
              <React.Fragment key={ti}>
                <span
                  style={{
                    display: "inline-block",
                    fontFamily: th.fontDisplay,
                    fontWeight: weight ?? th.displayWeight,
                    fontSize: sz,
                    letterSpacing: th.displayTracking,
                    lineHeight,
                    textTransform: upper ?? th.uppercase ? "uppercase" : "none",
                    ...tokLook(t, th, sz, ink, f, startF),
                    opacity: clamp01(p * 1.3),
                    filter: p < 0.99 ? `blur(${(1 - p) * 16}px)` : undefined,
                    transform: `translateY(${(1 - p) * 16}px)`,
                  }}
                >
                  {t.text}
                </span>
                {ti < ln.length - 1 ? " " : null}
              </React.Fragment>
            );
          })}
        </div>
      ))}
    </div>
  );
};

// ------------------------------------------------------------------ Kicker: small label chip
const Kicker: React.FC<{ text: string; dot?: boolean; color?: string }> = ({ text, dot = true, color }) => {
  const th = useTheme();
  const c = color ?? th.accent;
  return (
    <div style={{ display: "inline-flex", alignItems: "center", gap: 14, padding: "14px 26px", borderRadius: 999, background: th.dark ? "rgba(255,255,255,0.08)" : "rgba(13,15,28,0.05)", border: `1px solid ${th.cardBorder}`, font: `700 30px ${th.fontUi}`, letterSpacing: "0.08em", textTransform: "uppercase", color: th.dark ? th.ink : th.ink }}>
      {dot ? <span style={{ width: 14, height: 14, borderRadius: 7, background: c, boxShadow: `0 0 16px ${c}` }} /> : null}
      {text}
    </div>
  );
};

// ------------------------------------------------------------------ Counter: rolling number with optional star / steps
const Star: React.FC<{ size: number; color: string; p?: number }> = ({ size, color, p = 1 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" style={{ transform: `scale(${p}) rotate(${(1 - p) * -40}deg)`, filter: `drop-shadow(0 6px 18px ${color}88)` }}>
    <path d="M12 2.2l2.95 6.3 6.85.75-5.1 4.65 1.4 6.75L12 17.2l-6.1 3.45 1.4-6.75L2.2 9.25l6.85-.75L12 2.2z" fill={color} />
  </svg>
);

const Counter: React.FC<{
  from?: number; to: number; steps?: { at: unknown; value: number }[]; dur?: number; format?: "space" | "k" | "int" | "dec1" | "pct";
  prefix?: string; suffix?: string; label?: string; size?: number; color?: string; icon?: "star" | "none"; startAt?: unknown; labelAbove?: boolean;
}> = ({ from = 0, to, steps, dur = 1.4, format = "space", prefix = "", suffix = "", label, size = 260, color, icon = "none", startAt, labelAbove }) => {
  const { f, fps, at } = useBlockTime();
  const th = useTheme();
  const s0 = startAt !== undefined ? at(startAt) : 4;
  let v: number;
  let bumpF = s0;
  if (steps && steps.length) {
    const pts = [{ f: s0, value: from }, ...steps.map((s) => ({ f: at(s.at), value: s.value }))];
    let i = 0;
    while (i < pts.length - 1 && f >= pts[i + 1].f) i++;
    const a = pts[i];
    const b = pts[Math.min(i + 1, pts.length - 1)];
    bumpF = a.f;
    if (i === pts.length - 1 || f < b.f) {
      const rollStart = a.f;
      const p = E.outExpo(clamp01((f - rollStart) / (dur * fps)));
      const prev = i > 0 ? pts[i - 1].value : from;
      v = i === 0 ? from : lerp(prev, a.value, p);
    } else v = b.value;
  } else {
    const p = E.outExpo(clamp01((f - s0) / (dur * fps)));
    v = lerp(from, to, p);
  }
  const pop = springAt(f - bumpF, fps, 0, SPR.pop);
  const scale = lerp(0.92, 1, clamp01(pop));
  const ink = color ?? th.ink;
  // label may carry Russian plural forms: "минута|минуты|минут"
  const lab = label ? <div style={{ font: `600 ${Math.round(size * 0.17)}px ${th.fontDisplay}`, color: th.muted, letterSpacing: "-0.01em" }}>{pluralize(Math.round(v), label)}</div> : null;
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: size * 0.04 }}>
      {labelAbove ? lab : null}
      <div style={{ display: "flex", alignItems: "center", gap: size * 0.06, transform: `scale(${scale})` }}>
        <span style={{ font: `${Math.max(800, th.displayWeight)} ${size}px ${th.fontDisplay}`, letterSpacing: "-0.055em", color: ink, fontVariantNumeric: "tabular-nums", lineHeight: 1, textShadow: th.dark ? "0 10px 50px rgba(0,0,0,0.35)" : "none" }}>
          {prefix}
          {fmtNumber(v, format)}
          {suffix}
        </span>
        {icon === "star" ? <Star size={size * 0.62} color="#FFC531" p={clamp01(springAt(f - s0 - 6, fps, 0, SPR.pop))} /> : null}
      </div>
      {!labelAbove ? lab : null}
    </div>
  );
};

// ------------------------------------------------------------------ StrikeList: items that get crossed out
const StrikeList: React.FC<{ items: string[]; strikeAt?: unknown[]; showAt?: unknown[]; arrows?: boolean; size?: number; align?: "left" | "center" }> = ({
  items, strikeAt = [], showAt = [], arrows = true, size = 92, align = "center",
}) => {
  const { f, fps, at } = useBlockTime();
  const th = useTheme();
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: align === "center" ? "center" : "flex-start", gap: size * 0.18 }}>
      {items.map((it, i) => {
        const s = showAt[i] !== undefined ? at(showAt[i]) : i * 8;
        const p = E.out(clamp01((f - s) / (0.4 * fps)));
        const sk = strikeAt[i] !== undefined ? E.inOut(clamp01((f - at(strikeAt[i])) / (0.28 * fps))) : 0;
        return (
          <div key={i} style={{ display: "flex", alignItems: "center", gap: size * 0.25, opacity: p, transform: `translateX(${(1 - p) * -40}px)`, filter: p < 1 ? `blur(${(1 - p) * 10}px)` : undefined }}>
            {arrows ? <span style={{ color: th.accent, font: `500 ${size * 0.8}px ${th.fontUi}` }}>→</span> : null}
            <span style={{ position: "relative", font: `${th.displayWeight} ${size}px ${th.fontDisplay}`, letterSpacing: th.displayTracking, color: sk > 0.5 ? th.ink : th.ink }}>
              {it}
              <span style={{ position: "absolute", left: "-4%", top: "52%", height: size * 0.09, width: `${sk * 108}%`, background: th.neg, borderRadius: 6, transform: "rotate(-3deg)" }} />
            </span>
          </div>
        );
      })}
    </div>
  );
};

// ------------------------------------------------------------------ ArrowList: focus moves down the list, older items fade
const ArrowList: React.FC<{ items: string[]; showAt?: unknown[]; size?: number }> = ({ items, showAt = [], size = 96 }) => {
  const { f, fps, at } = useBlockTime();
  const th = useTheme();
  const times = items.map((_, i) => (showAt[i] !== undefined ? at(showAt[i]) : i * Math.round(0.6 * fps)));
  const cur = times.filter((t) => f >= t).length - 1;
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-start", gap: size * 0.12 }}>
      {items.map((it, i) => {
        const p = E.out(clamp01((f - times[i]) / (0.4 * fps)));
        const active = i === cur;
        const fade = active ? 1 : i < cur ? 0.32 : 0;
        const sz = active ? size : size * 0.62;
        return (
          <div key={i} style={{ display: "flex", alignItems: "center", gap: size * 0.2, opacity: p * (active ? 1 : 0.9) }}>
            <span style={{ color: th.accent, font: `500 ${sz * 0.75}px ${th.fontUi}`, opacity: active ? 1 : 0 }}>→</span>
            <span style={{ font: `${th.displayWeight} ${sz}px ${th.fontDisplay}`, letterSpacing: th.displayTracking, color: active ? th.ink : th.faint, opacity: fade || p, transition: "none" }}>{it}</span>
          </div>
        );
      })}
    </div>
  );
};

// ------------------------------------------------------------------ Quote card
const Quote: React.FC<{ text: string; author?: string; source?: string; size?: number }> = ({ text, author, source, size = 64 }) => {
  const { f, fps } = useBlockTime();
  const th = useTheme();
  const p = E.out(clamp01(f / (0.6 * fps)));
  return (
    <div style={{ background: th.card, borderRadius: th.radius, padding: "56px 60px", boxShadow: th.cardShadow, maxWidth: 900, border: `1px solid ${th.cardBorder}` }}>
      <div style={{ font: `italic ${th.serifWeight} ${size}px ${th.fontSerif}`, color: th.cardInk, lineHeight: 1.18, letterSpacing: "-0.01em", clipPath: `inset(0 0 ${(1 - p) * 100}% 0)` }}>«{text}»</div>
      {author ? (
        <div style={{ marginTop: 30, font: `600 32px ${th.fontUi}`, color: th.cardMuted, opacity: clamp01((f - 0.4 * fps) / 12) }}>
          — {author}
          {source ? <span style={{ opacity: 0.6 }}> · {source}</span> : null}
        </div>
      ) : null}
    </div>
  );
};

// ------------------------------------------------------------------ Typewriter
const Typewriter: React.FC<{ text: string; cps?: number; size?: number; mono?: boolean; color?: string; caret?: boolean; startAt?: unknown }> = ({
  text, cps = 22, size = 64, mono = false, color, caret = true, startAt,
}) => {
  const { f, fps, at } = useBlockTime();
  const th = useTheme();
  const s = startAt !== undefined ? at(startAt) : 6;
  const n = Math.max(0, Math.floor(((f - s) / fps) * cps));
  const shown = text.slice(0, n);
  const blink = Math.floor(f / 16) % 2 === 0 || n < text.length;
  return (
    <div style={{ font: `${mono ? 500 : th.displayWeight} ${size}px ${mono ? th.fontMono : th.fontDisplay}`, color: color ?? th.ink, letterSpacing: mono ? 0 : th.displayTracking, whiteSpace: "pre-wrap", maxWidth: MAXW, textAlign: "left" }}>
      {shown}
      {caret ? <span style={{ display: "inline-block", width: size * 0.08, height: size * 0.95, background: th.accent, marginLeft: 6, verticalAlign: "text-bottom", opacity: blink ? 1 : 0 }} /> : null}
    </div>
  );
};

// ------------------------------------------------------------------ Pill: "18 экранов"
const Pill: React.FC<{ text: string; value?: number; from?: number; size?: number; icon?: string; dark?: boolean }> = ({ text, value, from = 0, size = 46, icon, dark }) => {
  const { f, fps } = useBlockTime();
  const th = useTheme();
  const v = value !== undefined ? Math.round(lerp(from, value, E.outExpo(clamp01(f / (0.9 * fps))))) : null;
  const isDark = dark ?? th.dark;
  return (
    <div style={{ display: "inline-flex", alignItems: "center", gap: size * 0.3, padding: `${size * 0.32}px ${size * 0.62}px`, borderRadius: 999, background: isDark ? "rgba(255,255,255,0.1)" : "#fff", boxShadow: isDark ? "none" : th.cardShadow, border: `1px solid ${th.cardBorder}`, font: `700 ${size}px ${th.fontDisplay}`, color: isDark ? "#fff" : th.cardInk, letterSpacing: "-0.02em" }}>
      {icon ? <span>{icon}</span> : null}
      {v !== null ? <span style={{ color: th.accent, fontVariantNumeric: "tabular-nums" }}>{v}</span> : null}
      <span>{text}</span>
    </div>
  );
};

// ------------------------------------------------------------------ Chips (tag cloud)
const Chips: React.FC<{ items: string[]; stagger?: number; size?: number; accentIdx?: number[] }> = ({ items, stagger = 0.08, size = 38, accentIdx = [] }) => {
  const { f, fps } = useBlockTime();
  const th = useTheme();
  return (
    <div style={{ display: "flex", flexWrap: "wrap", gap: 18, justifyContent: "center", maxWidth: 940 }}>
      {items.map((it, i) => {
        const sp = springAt(f, fps, Math.round(i * stagger * fps), SPR.pop);
        const acc = accentIdx.includes(i);
        return (
          <div key={i} style={{ transform: `scale(${clamp01(sp) * 0.2 + 0.8 * sp})`, opacity: clamp01(sp * 2), padding: `${size * 0.36}px ${size * 0.7}px`, borderRadius: 999, background: acc ? th.accent : th.card, color: acc ? "#fff" : th.cardInk, font: `600 ${size}px ${th.fontUi}`, boxShadow: th.cardShadow, border: `1px solid ${th.cardBorder}` }}>
            {it}
          </div>
        );
      })}
    </div>
  );
};

// ================================================================== AGGRESSIVE TYPOGRAPHY

/** BigType: giant word(s) fitted to the frame width with brutal entrances */
const BigType: React.FC<{
  lines: string[]; at?: unknown[]; treatment?: ("solid" | "outline" | "mark" | "serif" | "accent")[]; enter?: "slam" | "letters" | "rise" | "split" | "wipe";
  upper?: boolean; maxSize?: number; gap?: number; echo?: boolean; rotate?: number; align?: "center" | "left";
}> = ({ lines, at, treatment = [], enter = "slam", upper, maxSize = 300, gap = 0, echo = false, rotate = 0, align = "center" }) => {
  const { f, fps, at: res } = useBlockTime();
  const th = useTheme();
  const U = upper ?? th.uppercase;
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: align === "center" ? "center" : "flex-start", gap, transform: `rotate(${rotate}deg)` }}>
      {lines.map((raw, i) => {
        const tr = treatment[i] ?? "solid";
        const serif = tr === "serif";
        const text = U && !serif ? raw.toUpperCase() : raw;
        const fam = serif ? th.fontSerif : th.fontDisplay;
        const wgt = serif ? 800 : Math.max(800, th.displayWeight);
        const size = Math.min(maxSize, fit(text, fam, wgt, 960, maxSize, 60, serif ? "-0.02em" : th.displayTracking));
        const s = at?.[i] !== undefined ? res(at[i]) : i * Math.round(0.22 * fps);
        const fl = f - s;
        if (fl < 0) return <div key={i} style={{ height: size * 0.9 }} />;
        const sp = springAt(fl, fps, 0, SPR.slam);
        const base: React.CSSProperties = {
          fontFamily: fam,
          fontWeight: wgt,
          fontStyle: serif ? "italic" : "normal",
          fontSize: size,
          lineHeight: 0.9,
          letterSpacing: serif ? "-0.02em" : th.displayTracking,
          whiteSpace: "nowrap",
          color: tr === "accent" ? th.accent : tr === "mark" ? th.markInk : tr === "outline" ? "transparent" : th.ink,
          WebkitTextStroke: tr === "outline" ? `${Math.max(3, size / 32)}px ${th.ink}` : undefined,
          background: tr === "mark" ? th.markBg : undefined,
          padding: tr === "mark" ? "0.03em 0.1em 0.07em" : undefined,
        };
        let anim: React.CSSProperties = {};
        if (enter === "slam") anim = { transform: `scale(${lerp(1.6, 1, sp)})`, opacity: clamp01(fl / 3), filter: fl < 7 ? `blur(${(1 - fl / 7) * 24}px)` : undefined };
        if (enter === "rise") {
          const p = E.outExpo(clamp01(fl / (0.5 * fps)));
          anim = { transform: `translateY(${(1 - p) * 110}%)`, opacity: 1 };
        }
        if (enter === "wipe") {
          const p = E.outExpo(clamp01(fl / (0.45 * fps)));
          anim = { clipPath: `inset(0 ${(1 - p) * 100}% 0 0)` };
        }
        if (enter === "split") {
          const p = E.outExpo(clamp01(fl / (0.5 * fps)));
          return (
            <div key={i} style={{ position: "relative", ...base, background: undefined, padding: undefined }}>
              <span style={{ ...base, display: "block", clipPath: "inset(0 0 50% 0)", transform: `translateX(${(1 - p) * -60}%)` }}>{text}</span>
              <span style={{ ...base, display: "block", position: "absolute", inset: 0, clipPath: "inset(50% 0 0 0)", transform: `translateX(${(1 - p) * 60}%)` }}>{text}</span>
            </div>
          );
        }
        if (enter === "letters") {
          return (
            <div key={i} style={{ ...base, display: "flex" }}>
              {[...text].map((ch, k) => {
                const lf = fl - k * 2;
                const ls = springAt(lf, fps, 0, SPR.slam);
                return (
                  <span key={k} style={{ display: "inline-block", transform: `translateY(${(1 - clamp01(ls)) * 60}%) scale(${lerp(1.5, 1, ls)})`, opacity: clamp01(lf / 2), whiteSpace: "pre" }}>
                    {ch}
                  </span>
                );
              })}
            </div>
          );
        }
        return (
          <div key={i} style={{ position: "relative", overflow: enter === "rise" ? "hidden" : "visible" }}>
            {echo
              ? [3, 2, 1].map((e) => (
                  <div key={e} style={{ ...base, position: "absolute", inset: 0, color: "transparent", background: undefined, WebkitTextStroke: `2px ${th.accent}`, opacity: 0.25 * (4 - e) * clamp01(fl / 10), transform: `translateY(${-e * size * 0.14 * E.out(clamp01(fl / 20))}px)` }}>
                    {text}
                  </div>
                ))
              : null}
            <div style={{ ...base, ...anim, position: "relative" }}>{text}</div>
          </div>
        );
      })}
    </div>
  );
};

/** Marquee: endless band(s) of repeated text, optionally tilted and crossing */
const Marquee: React.FC<{ text: string; speed?: number; size?: number; angle?: number; band?: boolean; cross?: boolean; color?: string; bandColor?: string; outline?: boolean }> = ({
  text, speed = 6, size = 120, angle = -8, band = true, cross = false, color, bandColor, outline = false,
}) => {
  const { f } = useBlockTime();
  const th = useTheme();
  const t = text.toUpperCase() + "  •  ";
  const unit = measureText({ text: t, fontFamily: th.fontDisplay, fontSize: size, fontWeight: 900, letterSpacing: "-0.03em", validateFontIsLoaded: false }).width;
  const row = (dir: number, ang: number, bg: string, fg: string, key: number) => (
    <div key={key} style={{ position: "absolute", left: -400, right: -400, top: "50%", transform: `translateY(-50%) rotate(${ang}deg)`, background: band ? bg : "transparent", padding: `${size * 0.12}px 0`, overflow: "hidden", boxShadow: band ? "0 20px 60px rgba(0,0,0,0.35)" : undefined }}>
      <div style={{ whiteSpace: "nowrap", transform: `translateX(${(((f * speed * dir) % unit) + unit) % unit - unit}px)`, font: `900 ${size}px ${th.fontDisplay}`, letterSpacing: "-0.03em", lineHeight: 1, color: outline ? "transparent" : fg, WebkitTextStroke: outline ? `3px ${fg}` : undefined }}>
        {t.repeat(Math.ceil(2600 / unit) + 2)}
      </div>
    </div>
  );
  return (
    <div style={{ position: "relative", width: "100%", height: "100%" }}>
      {cross ? row(-1, -angle, th.ink, th.bg, 1) : null}
      {row(1, angle, bandColor ?? th.accent, color ?? th.markInk, 0)}
    </div>
  );
};

/** Extruded pseudo-3D type (stacked shadows) with slow rotation */
const Extruded: React.FC<{ text: string; depth?: number; size?: number; color?: string; side?: string; tilt?: number }> = ({ text, depth = 22, size, color, side, tilt = 1 }) => {
  const { f, fps } = useBlockTime();
  const th = useTheme();
  const T = th.uppercase ? text.toUpperCase() : text;
  const sz = size ?? Math.min(260, fit(T, th.fontDisplay, 900, 900, 260, 60));
  const sideC = side ?? th.accent;
  const shadows = Array.from({ length: depth }, (_, i) => `${i + 1}px ${i + 1}px 0 ${sideC}`).join(",");
  const sp = springAt(f, fps, 0, SPR.slam);
  const ry = Math.sin(f * 0.02) * 10 * tilt;
  const rx = Math.cos(f * 0.017) * 6 * tilt;
  return (
    <div style={{ perspective: 1400 }}>
      <div style={{ font: `900 ${sz}px ${th.fontDisplay}`, letterSpacing: th.displayTracking, color: color ?? th.ink, textShadow: `${shadows}, ${depth + 8}px ${depth + 18}px 40px rgba(0,0,0,0.45)`, transform: `rotateY(${ry}deg) rotateX(${rx}deg) scale(${lerp(1.5, 1, sp)})`, opacity: clamp01(f / 4), whiteSpace: "nowrap" }}>
        {T}
      </div>
    </div>
  );
};

/** Slot-machine letters rolling into place */
const LetterRoll: React.FC<{ text: string; size?: number; stagger?: number; color?: string }> = ({ text, size, stagger = 2.5, color }) => {
  const { f, fps } = useBlockTime();
  const th = useTheme();
  const T = th.uppercase ? text.toUpperCase() : text;
  const sz = size ?? Math.min(240, fit(T, th.fontDisplay, 900, 920, 240, 60));
  const alphabet = "АБВГДЕЖЗИКЛМНОПРСТУФХЦЧШЭЮЯ0123456789";
  return (
    <div style={{ display: "flex", font: `900 ${sz}px ${th.fontDisplay}`, letterSpacing: th.displayTracking, color: color ?? th.ink, lineHeight: 1, overflow: "hidden", height: sz * 1.05 }}>
      {[...T].map((ch, i) => {
        const lf = f - i * stagger;
        const p = E.outExpo(clamp01(lf / (0.55 * fps)));
        const spins = 6;
        const pos = (1 - p) * spins;
        const k = Math.floor(pos);
        const glyph = k === 0 ? ch : alphabet[Math.floor(random(`lr${i}${k}`) * alphabet.length)];
        const frac = pos - k;
        return (
          <span key={i} style={{ display: "inline-block", transform: `translateY(${-frac * 100}%)`, whiteSpace: "pre", opacity: lf < 0 ? 0 : 1, filter: p < 0.95 ? `blur(${(1 - p) * 6}px)` : undefined }}>
            {glyph}
          </span>
        );
      })}
    </div>
  );
};

/** Word Swap: one slot that cycles through words (e.g. "для [дизайнеров/разработчиков/всех]") */
const WordSwap: React.FC<{ lead?: string; words: string[]; at?: unknown[]; size?: number; every?: number }> = ({ lead, words, at, size = 120, every = 0.7 }) => {
  const { f, fps, at: res } = useBlockTime();
  const th = useTheme();
  const times = words.map((_, i) => (at?.[i] !== undefined ? res(at[i]) : Math.round(i * every * fps)));
  const cur = Math.max(0, times.filter((t) => f >= t).length - 1);
  const p = E.outExpo(clamp01((f - times[cur]) / (0.35 * fps)));
  return (
    <div style={{ textAlign: "center" }}>
      {lead ? <div style={{ font: `${th.displayWeight} ${size * 0.55}px ${th.fontDisplay}`, color: th.muted, letterSpacing: th.displayTracking }}>{lead}</div> : null}
      <div style={{ height: size * 1.1, overflow: "hidden", position: "relative" }}>
        {cur > 0 && p < 1 ? (
          <div style={{ position: "absolute", left: 0, right: 0, font: `900 ${size}px ${th.fontDisplay}`, color: th.faint, letterSpacing: th.displayTracking, transform: `translateY(${-p * 100}%)` }}>{words[cur - 1]}</div>
        ) : null}
        <div style={{ font: `900 ${size}px ${th.fontDisplay}`, color: th.accent, letterSpacing: th.displayTracking, transform: `translateY(${(1 - p) * 100}%)` }}>{words[cur]}</div>
      </div>
    </div>
  );
};

/** Text clipped over an image/video (image-in-type) */
const MaskText: React.FC<{ text: string; src: string; size?: number; zoom?: number }> = ({ text, src, size, zoom = 1.2 }) => {
  const { f, dur } = useBlockTime();
  const th = useTheme();
  const T = th.uppercase ? text.toUpperCase() : text;
  const sz = size ?? fit(T, th.fontDisplay, 900, 960, 340, 80);
  const z = lerp(zoom, 1, clamp01(f / Math.max(1, dur)));
  return (
    <div style={{ font: `900 ${sz}px ${th.fontDisplay}`, letterSpacing: th.displayTracking, lineHeight: 0.9, color: "transparent", backgroundImage: `url(${asset(src)})`, backgroundSize: `${z * 100}%`, backgroundPosition: "center", WebkitBackgroundClip: "text", backgroundClip: "text", whiteSpace: "nowrap" }}>
      {T}
    </div>
  );
};

/** Highlight paragraph: body text, chosen words get marker sweeps at anchors */
const Highlight: React.FC<{ text: string; marks: { word: string; at?: unknown }[]; size?: number }> = ({ text, marks, size = 58 }) => {
  const { f, fps, at } = useBlockTime();
  const th = useTheme();
  const words = text.split(" ");
  return (
    <div style={{ font: `600 ${size}px ${th.fontDisplay}`, lineHeight: 1.35, color: th.ink, letterSpacing: "-0.02em", maxWidth: 900, textAlign: "left", textWrap: "pretty" } as React.CSSProperties}>
      {words.map((w, i) => {
        const m = marks.find((mm) => w.toLowerCase().includes(mm.word.toLowerCase()));
        const s = m ? (m.at !== undefined ? at(m.at) : 10 + marks.indexOf(m) * 12) : 0;
        const p = m ? E.inOut(clamp01((f - s) / (0.35 * fps))) : 0;
        return (
          <React.Fragment key={i}>
            <span style={m ? { backgroundImage: `linear-gradient(${th.markBg}, ${th.markBg})`, backgroundRepeat: "no-repeat", backgroundSize: `${p * 100}% 88%`, backgroundPosition: "0 70%", color: p > 0.6 ? th.markInk : th.ink, padding: "0 0.08em", borderRadius: 6 } : undefined}>{w}</span>{" "}
          </React.Fragment>
        );
      })}
    </div>
  );
};

/** Number punch: giant number with unit, rotating slightly, for aggressive stats */
const StatSlam: React.FC<{ value: string; unit?: string; label?: string; color?: string }> = ({ value, unit, label, color }) => {
  const { f, fps } = useBlockTime();
  const th = useTheme();
  const sp = springAt(f, fps, 0, SPR.slam);
  const size = Math.min(420, fit(value, th.fontDisplay, 900, 900, 420, 120));
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", transform: `scale(${lerp(1.8, 1, sp)}) rotate(${(1 - clamp01(sp)) * -6}deg)`, opacity: clamp01(f / 3), filter: f < 6 ? `blur(${(1 - f / 6) * 20}px)` : undefined }}>
      <div style={{ display: "flex", alignItems: "flex-start" }}>
        <span style={{ font: `900 ${size}px ${th.fontDisplay}`, letterSpacing: "-0.06em", color: color ?? th.accent, lineHeight: 0.85 }}>{value}</span>
        {unit ? <span style={{ font: `800 ${size * 0.3}px ${th.fontDisplay}`, color: th.ink, marginTop: size * 0.06, marginLeft: 10 }}>{unit}</span> : null}
      </div>
      {label ? <div style={{ marginTop: 24, font: `700 ${Math.round(size * 0.13)}px ${th.fontDisplay}`, color: th.muted, textTransform: th.uppercase ? "uppercase" : "none", letterSpacing: th.uppercase ? "0.04em" : "-0.01em" }}>{label}</div> : null}
    </div>
  );
};

export const TEXT_BLOCKS: Record<string, BlockDef> = {
  Title: defineBlock({ C: Title, cat: "text", desc: "Headline with blur-in words; markup *italic* [accent] ==mark== / linebreak. `at` = per-word anchors.", pos: "center", self: true, sfx: null, example: { text: "Собери *своё* / приложение [за вечер]", lead: "Теперь можно" } }),
  Kicker: defineBlock({ C: Kicker, cat: "text", desc: "Small uppercase label chip with glowing dot.", pos: "top", enter: "pop", sfx: "pop-high", example: { text: "Новый скилл" } }),
  Counter: defineBlock({
    C: Counter, cat: "text", desc: "Rolling number; `steps:[{at,value}]` for 136→1.2k jumps; icon:'star'; format space|k|pct; label with plural forms «звезда|звезды|звёзд».", pos: "center", enter: "pop", sfx: null,
    events: (p, t) => {
      const s0 = p.startAt !== undefined ? t.at(p.startAt) : 4;
      const pts = [s0, ...((p.steps ?? []) as { at: unknown }[]).map((s) => t.at(s.at))];
      return pts.flatMap((s) => [{ f: s, id: "tick-roll", vol: 0.7 }, { f: s + Math.round((p.dur ?? 1.4) * t.fps * 0.6), id: "pop-soft", vol: 0.6 }]);
    },
    example: { from: 0, to: 1200, format: "k", icon: "star", label: "звёзд на GitHub" },
  }),
  StrikeList: defineBlock({ C: StrikeList, cat: "text", desc: "List whose items get red strike-throughs at anchors (strikeAt).", pos: "center", sfx: null, events: (p, t) => ((p.strikeAt ?? []) as unknown[]).map((a) => ({ f: t.at(a), id: "strike" })), example: { items: ["Код", "Логотип", "Тексты"], strikeAt: [1.2, 1.6, 2.0] } }),
  ArrowList: defineBlock({ C: ArrowList, cat: "text", desc: "List where focus moves down: active item big with →, previous ones fade.", pos: "center", self: true, events: (p, t) => ((p.showAt ?? []) as unknown[]).map((a) => ({ f: t.at(a), id: "tick-soft" })), example: { items: ["Код", "Логотип", "Тексты"] } }),
  Quote: defineBlock({ C: Quote, cat: "text", desc: "Quote card in serif italic with author.", pos: "center", enter: "rise", sfx: "paper-rustle", example: { text: "Нравится, но клиенты забывают про запись", author: "отзыв в App Store" } }),
  Typewriter: defineBlock({ C: Typewriter, cat: "text", desc: "Text typed character by character with caret.", pos: "center", self: true, events: (p, t) => [{ f: p.startAt !== undefined ? t.at(p.startAt) : 6, id: (p.text ?? "").length > 24 ? "typing-long" : "typing-medium" }], example: { text: "найди, где это снято" } }),
  Pill: defineBlock({ C: Pill, cat: "text", desc: "Rounded pill with optional counting number: «18 экранов».", pos: "bottom", enter: "pop", sfx: "pop-soft", example: { value: 18, text: "экранов" } }),
  Chips: defineBlock({ C: Chips, cat: "text", desc: "Tags popping in with stagger.", pos: "center", self: true, events: (p, t) => ((p.items ?? []) as unknown[]).map((_, i) => ({ f: Math.round(i * (p.stagger ?? 0.08) * t.fps), id: "pop-high", vol: 0.5 })), example: { items: ["Reels", "Shorts", "TikTok", "YouTube"], accentIdx: [0] } }),
  BigType: defineBlock({ C: BigType, cat: "text", desc: "AGGRESSIVE: giant lines fitted to full width. enter slam|letters|rise|split|wipe; treatment solid|outline|mark|serif|accent; echo outlines.", pos: "center", self: true, events: (p, t) => ((p.lines ?? []) as unknown[]).map((_, i) => ({ f: p.at?.[i] !== undefined ? t.at(p.at[i]) : i * Math.round(0.22 * t.fps), id: "hit-punch", vol: 0.55 })), example: { lines: ["Ноль", "кода", "100%"], treatment: ["solid", "outline", "mark"] }, exampleDur: 3 }),
  Marquee: defineBlock({ C: Marquee, cat: "text", bleed: true, desc: "AGGRESSIVE: endless tilted text band(s); cross:true for an X of two bands.", pos: "center", self: true, example: { text: "бесплатно", cross: true } }),
  Extruded: defineBlock({ C: Extruded, cat: "text", desc: "AGGRESSIVE: pseudo-3D extruded word, slow tilt.", pos: "center", self: true, sfx: "hit-punch", example: { text: "FREE" } }),
  LetterRoll: defineBlock({ C: LetterRoll, cat: "text", desc: "Slot-machine letters rolling into a word.", pos: "center", self: true, sfx: "tick-roll", example: { text: "СКИЛЛ" } }),
  WordSwap: defineBlock({ C: WordSwap, cat: "text", desc: "One slot cycling through words under a lead line.", pos: "center", self: true, events: (p, t) => ((p.words ?? []) as unknown[]).map((_, i) => ({ f: p.at?.[i] !== undefined ? t.at(p.at[i]) : Math.round(i * (p.every ?? 0.7) * t.fps), id: "swipe-tiny" })), example: { lead: "для", words: ["дизайнеров", "кодеров", "всех"] } }),
  MaskText: defineBlock({ C: MaskText, cat: "text", desc: "Giant word filled with an image (image-in-type).", pos: "center", enter: "slam", sfx: "hit-soft" }),
  Highlight: defineBlock({ C: Highlight, cat: "text", desc: "Paragraph with marker sweeps over chosen words at anchors.", pos: "center", enter: "rise", sfx: null, events: (p, t) => ((p.marks ?? []) as { at?: unknown }[]).map((m, i) => ({ f: m.at !== undefined ? t.at(m.at) : 10 + i * 12, id: "marker" })), example: { text: "Агент читает отзывы и ищет повторяющиеся жалобы", marks: [{ word: "отзывы" }, { word: "жалобы" }] } }),
  StatSlam: defineBlock({ C: StatSlam, cat: "text", desc: "AGGRESSIVE: giant stat slammed in with unit and label.", pos: "center", self: true, sfx: "hit-punch", example: { value: "2", unit: "м", label: "точность" } }),
};
