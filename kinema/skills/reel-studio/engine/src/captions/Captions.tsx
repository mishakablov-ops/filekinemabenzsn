import { measureText } from "@remotion/layout-utils";
import React, { useMemo } from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import { E, clamp01, lerp, prog, SPR, springAt } from "../core/motion";
import { CAPTION_BANDS, W } from "../core/layout";
import type { CaptionMode, CaptionPos, CaptionsSpec, Card, Transcript, Word } from "../core/types";
import { getTheme, type StyleId, type Theme } from "../theme/styles";

// Short Russian/English function words that must never end a line alone.
const GLUE = new Set([
  "в", "во", "и", "а", "но", "на", "по", "за", "из", "до", "от", "к", "ко", "с", "со", "у", "о", "об", "обо", "не", "ни",
  "под", "над", "при", "про", "для", "без", "что", "как", "это", "его", "ее", "её", "их", "мы", "вы", "он", "она", "я",
  "the", "a", "an", "to", "of", "in", "on", "at", "is", "it", "and", "or", "for", "by",
]);
const bare = (s: string) => s.toLowerCase().replace(/[«»"“”.,!?…:;()]/g, "");

export type CaptionOverride = (tSec: number) => (CaptionsSpec & { hide?: boolean; themeId?: StyleId }) | null;

type Resolved = {
  mode: CaptionMode;
  pos: CaptionPos;
  light: boolean; // light text
  shadow: string;
  scale: number;
  upper: boolean;
  align: "center" | "left";
};

/** Split long cards into chunks for subtitle/slam modes (keeps punctuation boundaries) */
const chunk = (ws: Word[], maxChars: number, maxWords: number): Word[][] => {
  const out: Word[][] = [];
  let cur: Word[] = [];
  let len = 0;
  ws.forEach((w, i) => {
    const l = w.text.length + 1;
    const glued = cur.length > 0 && GLUE.has(bare(cur[cur.length - 1].text));
    if (cur.length && !glued && (len + l > maxChars || cur.length >= maxWords)) {
      out.push(cur);
      cur = [];
      len = 0;
    }
    cur.push(w);
    len += l;
    const strong = /[.!?…]$/.test(w.text) || (/[,:;—]$/.test(w.text) && len > maxChars * 0.5);
    if (strong && i < ws.length - 1) {
      out.push(cur);
      cur = [];
      len = 0;
    }
  });
  if (cur.length) out.push(cur);
  return out;
};

/** group words so short function words stick to the next word */
const glueUnits = (ws: Word[]) => {
  const units: Word[][] = [];
  let cur: Word[] = [];
  ws.forEach((w, i) => {
    cur.push(w);
    const isGlue = GLUE.has(bare(w.text)) && i < ws.length - 1 && ws[i + 1].line === w.line;
    const nextIsDash = i < ws.length - 1 && /^[—–-]$/.test(ws[i + 1].text);
    if (!isGlue && !nextIsDash) {
      units.push(cur);
      cur = [];
    }
  });
  if (cur.length) units.push(cur);
  return units;
};

type View = { key: string; words: Word[]; start: number; hideAt: number; mode: CaptionMode; card: Card };

export const Captions: React.FC<{
  transcript: Transcript;
  theme: Theme;
  spec?: CaptionsSpec;
  override?: CaptionOverride;
  /** reports chunk start frames (for camera punch in aggressive modes) */
}> = ({ transcript, theme, spec, override }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;

  const views = useMemo(() => buildViews(transcript, theme, spec, override), [transcript, theme, spec, override]);

  const active = views.filter((v) => t >= v.start - 0.25 && t <= v.hideAt + 0.35);
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      {active.map((v) => {
        const o = override?.(v.start) ?? null;
        if (o?.hide) return null;
        const th = o?.themeId ? getTheme(o.themeId) : theme;
        const r = resolveLook(th, o?.themeId ? undefined : spec, o, v.mode);
        if (v.card.pos) r.pos = v.card.pos; // %top / %lower … in the script wins
        return <CardView key={v.key} view={v} r={r} theme={th} t={t} fps={fps} />;
      })}
    </AbsoluteFill>
  );
};

export const buildViews = (transcript: Transcript, theme: Theme, spec?: CaptionsSpec, override?: CaptionOverride): View[] => {
  const out: View[] = [];
  transcript.cards.forEach((card) => {
    const ws = card.words.map((i) => transcript.words[i]);
    if (!ws.length) return;
    const o = override?.(ws[0].start) ?? null;
    const mode: CaptionMode = card.mode ?? o?.mode ?? spec?.mode ?? theme.captionMode;
    if (mode === "none") return;
    const parts =
      mode === "subtitle" ? chunk(ws, 26, 5) : mode === "slam" ? chunk(ws, 16, 3) : mode === "stack" ? chunk(ws, 34, 6) : [ws];
    parts.forEach((p, k) => out.push({ key: `${card.i}-${k}`, words: p, start: p[0].start, hideAt: 0, mode, card }));
  });
  for (let i = 0; i < out.length; i++) {
    const v = out[i];
    const next = out[i + 1];
    const lastEnd = v.words[v.words.length - 1].end;
    // slam cards cut hard to the next card; with no next card in sight they hold ~2 s
    const hold = v.mode === "slam" ? 2.0 : 2.2;
    v.hideAt = next ? Math.min(next.start - 0.06, lastEnd + hold) : lastEnd + hold;
    if (v.hideAt < lastEnd) v.hideAt = lastEnd;
  }
  return out;
};

const resolveLook = (theme: Theme, spec: CaptionsSpec | undefined, o: CaptionsSpec | null, mode: CaptionMode): Resolved => {
  const tone = o?.tone ?? spec?.tone ?? (theme.dark ? "light" : "dark");
  return {
    mode,
    pos: o?.pos ?? spec?.pos ?? theme.captionPos,
    light: tone === "light",
    shadow: o?.shadow === false || spec?.shadow === false ? "none" : tone === "light" ? theme.captionShadow === "none" ? "0 2px 22px rgba(0,0,0,0.45)" : theme.captionShadow : "none",
    scale: (o?.scale ?? spec?.scale ?? 1) * theme.captionScale,
    upper: o?.uppercase ?? spec?.uppercase ?? theme.uppercase,
    align: o?.align ?? spec?.align ?? "center",
  };
};

const colors = (theme: Theme, r: Resolved) => ({
  ink: r.light ? (theme.dark ? theme.ink : "#FFFFFF") : theme.dark ? "#0D0F1C" : theme.ink,
  muted: r.light ? (theme.dark ? theme.muted : "rgba(255,255,255,0.78)") : theme.dark ? "#5B5F73" : theme.muted,
});

const MAXW = W - 2 * 84;

const fitSize = (text: string, family: string, weight: number, maxW: number, sizes: number[], maxLines: number, tracking: string) => {
  for (const s of sizes) {
    const w = measureText({ text, fontFamily: family, fontSize: s, fontWeight: weight, letterSpacing: tracking, validateFontIsLoaded: false }).width;
    if (Math.ceil((w * 1.04) / maxW) <= maxLines) return s;
  }
  return sizes[sizes.length - 1];
};

const CardView: React.FC<{ view: View; r: Resolved; theme: Theme; t: number; fps: number }> = ({ view, r, theme, t, fps }) => {
  const band = CAPTION_BANDS[r.pos];
  const col = colors(theme, r);
  const exitDur = view.mode === "slam" || view.mode === "vhs" ? 0.001 : 0.22;
  const exitP = clamp01((t - view.hideAt) / exitDur);
  if (exitP >= 1) return null;
  const firstReveal = view.words[0].start - 0.12;
  if (t < firstReveal) return null;

  const exitStyle: React.CSSProperties =
    view.mode === "slam" ? {} : { opacity: 1 - E.in(exitP), filter: exitP > 0 ? `blur(${exitP * 14}px)` : undefined, transform: `translateY(${-exitP * 18}px)` };

  const justify = r.pos === "top" || r.pos === "upper" ? "flex-start" : r.pos === "bottom" ? "flex-end" : "center";
  const box: React.CSSProperties = {
    position: "absolute",
    left: 0,
    right: 0,
    top: band.y,
    height: band.h,
    display: "flex",
    flexDirection: "column",
    justifyContent: justify,
    alignItems: r.align === "left" ? "flex-start" : "center",
    padding: `0 ${84}px`,
    textAlign: r.align,
    ...exitStyle,
  };

  if (view.mode === "slam") return <div data-qa="caption" style={box}><Slam view={view} r={r} theme={theme} col={col} t={t} fps={fps} /></div>;
  if (view.mode === "stack") return <div data-qa="caption" style={box}><Stack view={view} r={r} theme={theme} col={col} t={t} /></div>;
  if (view.mode === "subtitle") return <div data-qa="caption" style={box}><Subtitle view={view} r={r} theme={theme} col={col} t={t} /></div>;
  if (view.mode === "karaoke") return <div data-qa="caption" style={box}><Karaoke view={view} r={r} theme={theme} col={col} t={t} /></div>;
  if (view.mode === "vhs") return <div data-qa="caption" style={{ ...box, opacity: 1, filter: undefined, transform: undefined }}><Vhs view={view} r={r} t={t} /></div>;
  return <div data-qa="caption" style={box}><Editorial view={view} r={r} theme={theme} col={col} t={t} /></div>;
};

type Col = { ink: string; muted: string };

/** blur→sharp per-word reveal (the signature look) */
const reveal = (t: number, w: Word, dur = 0.34, lead = 0.1) => {
  const p = E.out(clamp01((t - (w.start - lead)) / dur));
  return {
    p,
    style: {
      opacity: clamp01(p * 1.25),
      filter: p < 0.999 ? `blur(${(1 - p) * 16}px)` : undefined,
      transform: `translateY(${(1 - p) * 14}px)`,
    } as React.CSSProperties,
  };
};

const wordLook = (w: Word, theme: Theme, col: Col, base: React.CSSProperties, sizePx: number, t: number, light: boolean) => {
  const st = w.style ?? [];
  const s: React.CSSProperties = { ...base };
  if (st.includes("italic")) {
    s.fontFamily = theme.fontSerif;
    s.fontStyle = "italic";
    s.fontWeight = theme.serifWeight;
    s.letterSpacing = "-0.01em";
    s.fontSize = sizePx * 1.1;
    s.textTransform = "none";
    s.paddingRight = "0.04em";
  }
  if (st.includes("accent")) s.color = theme.accent;
  if (st.includes("alt")) s.color = theme.accent2;
  if (st.includes("neg")) s.color = theme.neg;
  if (st.includes("pos")) s.color = theme.pos;
  if (st.includes("big")) s.fontSize = (s.fontSize as number ?? sizePx) * 1.25;
  if (st.includes("outline")) {
    s.color = "transparent";
    s.WebkitTextStroke = `${Math.max(2, sizePx / 28)}px ${light ? "#fff" : col.ink}`;
  }
  if (st.includes("mark")) {
    const p = clamp01((t - w.start + 0.05) / 0.28);
    s.color = theme.markInk;
    s.backgroundImage = `linear-gradient(${theme.markBg}, ${theme.markBg})`;
    s.backgroundRepeat = "no-repeat";
    s.backgroundSize = `${E.out(p) * 100}% 100%`;
    s.padding = "0.02em 0.16em 0.06em";
    s.margin = "0 0.04em";
    s.borderRadius = "0.18em";
    s.textShadow = "none";
    if (p < 0.4) s.color = col.ink; // keep contrast while the box sweeps in
  }
  return s;
};

const Strike: React.FC<{ w: Word; t: number; color: string }> = ({ w, t, color }) => {
  if (!(w.style ?? []).includes("strike")) return null;
  const p = E.inOut(clamp01((t - w.end - 0.05) / 0.3));
  return (
    <span
      style={{
        position: "absolute",
        left: "-3%",
        top: "54%",
        height: "0.09em",
        width: `${p * 106}%`,
        background: color,
        borderRadius: 8,
        transform: "rotate(-2deg)",
      }}
    />
  );
};

const Words: React.FC<{
  ws: Word[]; theme: Theme; col: Col; base: React.CSSProperties; size: number; t: number; light: boolean;
  revealDur?: number; color?: string;
}> = ({ ws, theme, col, base, size, t, light, revealDur = 0.34, color }) => (
  <>
    {glueUnits(ws).map((u, ui) => (
      <React.Fragment key={ui}>
        <span style={{ whiteSpace: "nowrap", display: "inline-block" }}>
          {u.map((w, k) => {
            const rv = reveal(t, w, revealDur);
            const look = wordLook(w, theme, col, { ...base, color: color ?? base.color }, size, t, light);
            return (
              <React.Fragment key={w.i}>
                <span style={{ display: "inline-block", position: "relative", ...look, ...rv.style }}>
                  {w.text}
                  <Strike w={w} t={t} color={theme.neg} />
                </span>
                {k < u.length - 1 ? " " : null}
              </React.Fragment>
            );
          })}
        </span>
        {ui < glueUnits(ws).length - 1 ? " " : null}
      </React.Fragment>
    ))}
  </>
);

const splitLines = (ws: Word[]) => {
  const lines: Word[][] = [];
  ws.forEach((w) => {
    const li = w.line ?? 0;
    (lines[li] ??= []).push(w);
  });
  return lines.filter(Boolean);
};

// ---------------------------------------------------------------- EDITORIAL
const Editorial: React.FC<{ view: View; r: Resolved; theme: Theme; col: Col; t: number }> = ({ view, r, theme, col, t }) => {
  const lead = view.words.filter((w) => w.role === "lead");
  const punch = view.words.filter((w) => w.role === "punch");
  const ptxt = punch.map((w) => w.text).join(" ");
  const upper = r.upper;
  const size =
    fitSize(upper ? ptxt.toUpperCase() : ptxt, theme.fontDisplay, theme.displayWeight, MAXW, [112, 104, 96, 88, 80, 72, 64], ptxt.length > 26 ? 2 : 1, theme.displayTracking) * r.scale;
  const leadSize = Math.round(Math.max(40, Math.min(50, size * 0.48)) * r.scale);
  const shadow = r.shadow;
  const punchBase: React.CSSProperties = {
    fontFamily: theme.fontDisplay,
    fontWeight: theme.displayWeight,
    fontSize: size,
    letterSpacing: theme.displayTracking,
    lineHeight: 1.04,
    color: col.ink,
    textShadow: shadow,
    textTransform: upper ? "uppercase" : "none",
  };
  const leadBase: React.CSSProperties = {
    fontFamily: theme.fontDisplay,
    fontWeight: 600,
    fontSize: leadSize,
    letterSpacing: "-0.015em",
    lineHeight: 1.15,
    color: col.muted,
    textShadow: shadow,
  };
  const plines = splitLines(punch);
  return (
    <>
      {lead.length > 0 && (
        <div style={{ ...leadBase, textWrap: "balance", marginBottom: punch.length ? size * 0.12 : 0, maxWidth: MAXW } as React.CSSProperties}>
          <Words ws={lead} theme={theme} col={col} base={leadBase} size={leadSize} t={t} light={r.light} />
        </div>
      )}
      {plines.map((ln, i) => (
        <div key={i} style={{ ...punchBase, textWrap: "balance", maxWidth: MAXW } as React.CSSProperties}>
          <Words ws={ln} theme={theme} col={col} base={punchBase} size={size} t={t} light={r.light} />
        </div>
      ))}
    </>
  );
};

// ---------------------------------------------------------------- SUBTITLE
const Subtitle: React.FC<{ view: View; r: Resolved; theme: Theme; col: Col; t: number }> = ({ view, r, theme, col, t }) => {
  const txt = view.words.map((w) => w.text).join(" ");
  const size = fitSize(txt, theme.fontDisplay, 700, MAXW, [64, 60, 56, 52], 2, "-0.02em") * r.scale;
  const base: React.CSSProperties = {
    fontFamily: theme.fontDisplay,
    fontWeight: 700,
    fontSize: size,
    letterSpacing: "-0.02em",
    lineHeight: 1.12,
    color: col.ink,
    textShadow: r.shadow,
    textTransform: r.upper ? "uppercase" : "none",
  };
  return (
    <div style={{ ...base, textWrap: "balance", maxWidth: MAXW } as React.CSSProperties}>
      <Words ws={view.words} theme={theme} col={col} base={base} size={size} t={t} light={r.light} revealDur={0.26} />
    </div>
  );
};

// ---------------------------------------------------------------- KARAOKE
const Karaoke: React.FC<{ view: View; r: Resolved; theme: Theme; col: Col; t: number }> = ({ view, r, theme, col, t }) => {
  const txt = view.words.map((w) => w.text).join(" ");
  const size = fitSize(txt, theme.fontDisplay, 800, MAXW, [84, 76, 68, 60, 54], 3, theme.displayTracking) * r.scale;
  const appear = E.out(clamp01((t - view.start + 0.15) / 0.3));
  return (
    <div style={{ textWrap: "balance", maxWidth: MAXW, opacity: appear, transform: `translateY(${(1 - appear) * 20}px)`, fontFamily: theme.fontDisplay, fontWeight: 800, fontSize: size, lineHeight: 1.1 } as React.CSSProperties}>
      {view.words.map((w, k) => {
        const on = t >= w.start - 0.03;
        const cur = on && t < w.end + 0.05;
        const look = wordLook(w, theme, col, {}, size, t, r.light);
        return (
          <React.Fragment key={w.i}>
            <span
              style={{
                display: "inline-block",
                fontFamily: theme.fontDisplay,
                fontWeight: 800,
                fontSize: size,
                letterSpacing: theme.displayTracking,
                lineHeight: 1.1,
                textShadow: r.shadow,
                textTransform: r.upper ? "uppercase" : "none",
                ...look,
                color: cur ? theme.accent : on ? (look.color ?? col.ink) : r.light ? "rgba(255,255,255,0.32)" : "rgba(13,15,28,0.22)",
                transform: `scale(${cur ? 1.06 : 1})`,
              }}
            >
              {w.text}
            </span>
            {k < view.words.length - 1 ? " " : null}
          </React.Fragment>
        );
      })}
    </div>
  );
};

// ---------------------------------------------------------------- SLAM (aggressive)
const Slam: React.FC<{ view: View; r: Resolved; theme: Theme; col: Col; t: number; fps: number }> = ({ view, r, theme, col, t, fps }) => {
  // one word per line unless explicit lines; each line is fitted to the full width
  const lines: Word[][] = view.words.some((w) => (w.line ?? 0) > 0) ? splitLines(view.words) : slamLines(view.words);
  const family = theme.fontDisplay;
  const weight = Math.max(800, theme.displayWeight);
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: r.align === "left" ? "flex-start" : "center", gap: 0 }}>
      {lines.map((ln, li) => {
        const text = ln.map((w) => w.text).join(" ");
        const italic = ln.some((w) => (w.style ?? []).includes("italic"));
        // serif-italic accents stay lowercase: the contrast with the caps is the point
        const shown = r.upper && !italic ? text.toUpperCase() : text;
        const fam = italic ? theme.fontSerif : family;
        const wgt = italic ? 800 : weight;
        const fitted = fitSize(shown, fam, wgt, MAXW, [300, 270, 240, 215, 190, 170, 150, 132, 116, 100, 88], 1, italic ? "-0.02em" : theme.displayTracking);
        // never taller than the caption band (keeps slams off the stage content)
        const bandH = CAPTION_BANDS[r.pos].h;
        const size = Math.min(fitted, lines.length > 2 ? 200 : 260, (bandH * 0.97) / (lines.length * 0.95)) * r.scale;
        const w0 = ln[0];
        const f = (t - (w0.start - 0.06)) * fps;
        const sp = springAt(f, fps, 0, SPR.slam);
        const p = clamp01(sp);
        if (f < 0) return <div key={li} style={{ height: size * 0.92 }} />;
        const st = new Set(ln.flatMap((w) => w.style ?? []));
        const marked = st.has("mark");
        const color = st.has("accent") || st.has("pos") ? theme.accent : st.has("neg") ? theme.neg : st.has("alt") ? theme.accent2 : col.ink;
        const scale = lerp(1.55, 1, sp);
        const blur = (1 - clamp01(f / 7)) * 22;
        return (
          <div
            key={li}
            style={{
              fontFamily: fam,
              fontStyle: italic ? "italic" : "normal",
              fontWeight: wgt,
              fontSize: size,
              lineHeight: 0.92,
              letterSpacing: italic ? "-0.02em" : theme.displayTracking,
              textTransform: r.upper && !italic ? "uppercase" : "none",
              color: marked ? theme.markInk : st.has("outline") ? "transparent" : color,
              WebkitTextStroke: st.has("outline") ? `${Math.max(3, size / 34)}px ${col.ink}` : undefined,
              background: marked ? theme.markBg : undefined,
              padding: marked ? "0.02em 0.12em 0.08em" : undefined,
              transform: `scale(${scale}) rotate(${(1 - p) * (li % 2 ? 3 : -3)}deg)`,
              opacity: clamp01(f / 3),
              filter: blur > 0.3 ? `blur(${blur}px)` : undefined,
              whiteSpace: "nowrap",
              textShadow: r.shadow,
              position: "relative",
            }}
          >
            {shown}
            {st.has("strike") ? (
              <span style={{ position: "absolute", left: "-3%", top: "50%", height: size * 0.1, width: `${E.inOut(clamp01((t - ln[ln.length - 1].end) / 0.25)) * 106}%`, background: theme.neg, transform: "rotate(-4deg)" }} />
            ) : null}
          </div>
        );
      })}
    </div>
  );
};

const slamLines = (ws: Word[]) => {
  const out: Word[][] = [];
  let cur: Word[] = [];
  ws.forEach((w, i) => {
    cur.push(w);
    const short = bare(w.text).length <= 1 && i < ws.length - 1;
    const styledNext = i < ws.length - 1 && (ws[i + 1].style ?? []).length > 0 && !(w.style ?? []).length;
    if (!short && (cur.length >= 2 || cur.reduce((a, x) => a + x.text.length, 0) > 7 || styledNext)) {
      out.push(cur);
      cur = [];
    }
  });
  if (cur.length) out.push(cur);
  return out;
};

// ---------------------------------------------------------------- STACK (lines accumulate, mixed treatments)
const Stack: React.FC<{ view: View; r: Resolved; theme: Theme; col: Col; t: number }> = ({ view, r, theme, col, t }) => {
  const lines: Word[][] = view.words.some((w) => (w.line ?? 0) > 0) ? splitLines(view.words) : groupForStack(view.words);
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: r.align === "left" ? "flex-start" : "center" }}>
      {lines.map((ln, li) => {
        const text = ln.map((w) => w.text).join(" ");
        const st = new Set(ln.flatMap((w) => w.style ?? []));
        const treatment = st.has("italic") ? "serif" : st.has("outline") ? "outline" : "solid";
        const fam = treatment === "serif" ? theme.fontSerif : theme.fontDisplay;
        const wgt = treatment === "serif" ? 600 : Math.max(800, theme.displayWeight);
        const shown = r.upper && treatment !== "serif" ? text.toUpperCase() : text;
        const size = Math.min(fitSize(shown, fam, wgt, MAXW, [200, 180, 160, 140, 124, 110, 96, 84, 74], 1, theme.displayTracking), 190) * r.scale;
        const p = E.outExpo(clamp01((t - ln[0].start + 0.08) / 0.32));
        if (p <= 0) return null;
        const color = st.has("accent") ? theme.accent : st.has("alt") ? theme.accent2 : st.has("neg") ? theme.neg : col.ink;
        return (
          <div
            key={li}
            style={{
              fontFamily: fam,
              fontStyle: treatment === "serif" ? "italic" : "normal",
              fontWeight: wgt,
              fontSize: size,
              lineHeight: 0.98,
              letterSpacing: treatment === "serif" ? "-0.01em" : theme.displayTracking,
              color: treatment === "outline" ? "transparent" : st.has("mark") ? theme.markInk : color,
              background: st.has("mark") ? theme.markBg : undefined,
              padding: st.has("mark") ? "0 0.12em 0.06em" : undefined,
              WebkitTextStroke: treatment === "outline" ? `${Math.max(3, size / 34)}px ${col.ink}` : undefined,
              transform: `translateY(${(1 - p) * 60}px) scale(${lerp(1.12, 1, p)})`,
              opacity: p,
              filter: p < 0.98 ? `blur(${(1 - p) * 14}px)` : undefined,
              whiteSpace: "nowrap",
              textShadow: r.shadow,
            }}
          >
            {shown}
          </div>
        );
      })}
    </div>
  );
};

const groupForStack = (ws: Word[]) => {
  // 1–2 words per line, styled words get their own line
  const out: Word[][] = [];
  let cur: Word[] = [];
  glueUnits(ws).forEach((u) => {
    const styled = u.some((w) => (w.style ?? []).length);
    const len = cur.reduce((a, w) => a + w.text.length, 0);
    if (cur.length && (styled || len + u.reduce((a, w) => a + w.text.length, 0) > 12)) {
      out.push(cur);
      cur = [];
    }
    cur.push(...u);
    if (styled) {
      out.push(cur);
      cur = [];
    }
  });
  if (cur.length) out.push(cur);
  return out;
};

/** frames where slam/stack chunks hit (camera punch / shake / sfx) */
export const captionHits = (transcript: Transcript, theme: Theme, spec: CaptionsSpec | undefined, override: CaptionOverride | undefined, fps: number) =>
  buildViews(transcript, theme, spec, override)
    .filter((v) => v.mode === "slam" || v.mode === "stack")
    .map((v) => Math.round((v.start - 0.06) * fps));

// ---------------------------------------------------------------- VHS: pixel font, typed in steps, square plates growing frame by frame
const VHS_STEP = 1 / 12; // the look updates at 12 fps, like a cheap character generator
const VHS_YELLOW = "#FFE04A";
const VHS_PLATE = "#1B2BD6"; // VCR menu blue
const q12 = (t: number) => Math.floor(t / VHS_STEP) * VHS_STEP;
const Vhs: React.FC<{ view: View; r: Resolved; t: number }> = ({ view, r, t }) => {
  const tq = q12(t);
  const lead = view.words.filter((w) => w.role === "lead");
  const punch = view.words.filter((w) => w.role === "punch");
  const body = punch.length ? punch : view.words;
  const head = punch.length ? lead : [];
  const up = (s: string) => (r.upper ? s.toUpperCase() : s);
  const txt = (ws: Word[]) => up(ws.map((w) => w.text).join(" "));
  const big = fitSize(txt(body), "'Press Start 2P'", 400, MAXW, [60, 56, 52, 48, 44, 40, 36], 3, "0px");
  const small = Math.max(30, Math.round(big * 0.66));
  const jitter = ((Math.floor(t * 12) * 7919) % 3) - 1; // 1 px horizontal wobble per step
  const shadow = (px: number) => {
    const o = Math.max(3, Math.round(px / 11));
    return `${o}px ${o}px 0 #000, -2px 0 0 rgba(255,40,70,0.55), 2px 0 0 rgba(40,140,255,0.55)`;
  };
  // characters typed at ~38 cps from each word's start, quantised to the 12 fps steps
  const typed = (w: Word) => {
    const n = Math.floor(Math.max(0, tq - (w.start - 0.04)) * 38) + (tq >= w.start - 0.04 ? 1 : 0);
    return Math.min(w.text.length, n);
  };
  const renderWords = (ws: Word[], px: number, color: string) =>
    ws.map((w, i) => {
      const n = typed(w);
      if (n <= 0) return null;
      const st = w.style ?? [];
      const mark = st.includes("mark");
      const accent = st.includes("italic") || st.includes("accent") || st.includes("alt");
      const shown = up(w.text).slice(0, n);
      // plate: square, grows in 4 hard steps (25/50/75/100 %), one step per frame of the 12 fps look
      const steps = mark ? Math.min(4, Math.floor(Math.max(0, tq - (w.start - 0.04)) / VHS_STEP) + 1) : 0;
      return (
        <React.Fragment key={w.i}>
          <span
            style={{
              position: "relative",
              display: "inline-block",
              color: mark ? "#FFFFFF" : accent ? VHS_YELLOW : color,
              textShadow: mark ? `${Math.max(3, Math.round(px / 11))}px ${Math.max(3, Math.round(px / 11))}px 0 #000` : shadow(px),
              padding: mark ? `${Math.round(px * 0.16)}px ${Math.round(px * 0.22)}px` : undefined,
              margin: mark ? `0 ${Math.round(px * 0.1)}px` : undefined,
            }}
          >
            {mark ? (
              <span style={{ position: "absolute", left: 0, top: 0, bottom: 0, width: `${steps * 25}%`, background: VHS_PLATE, boxShadow: `${Math.max(3, Math.round(px / 11))}px ${Math.max(3, Math.round(px / 11))}px 0 #000` }} />
            ) : null}
            <span style={{ position: "relative" }}>{shown}</span>
            <span style={{ visibility: "hidden" }}>{up(w.text).slice(n)}</span>
          </span>
          {i < ws.length - 1 ? " " : null}
        </React.Fragment>
      );
    });
  const base: React.CSSProperties = { fontFamily: "'Press Start 2P', monospace", fontWeight: 400, lineHeight: 1.5, letterSpacing: 0, transform: `translateX(${jitter}px)`, WebkitFontSmoothing: "none" };
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: r.align === "left" ? "flex-start" : "center", gap: Math.round(big * 0.45) }}>
      {head.length ? <div style={{ ...base, fontSize: small, color: "#D9D9D2" }}>{renderWords(head, small, "#D9D9D2")}</div> : null}
      <div style={{ ...base, fontSize: big, color: "#FFFFFF" }}>{renderWords(body, big, "#FFFFFF")}</div>
    </div>
  );
};
