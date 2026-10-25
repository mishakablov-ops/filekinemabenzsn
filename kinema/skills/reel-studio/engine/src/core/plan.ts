import { getStaticFiles } from "remotion";
import { REGISTRY } from "../blocks";
import { getTheme, type Theme } from "../theme/styles";
import { getTransition, type Trans } from "../transitions";
import { resolve, type TimeCtx } from "./timing";
import type { BeatGrid, LayerSpec, SceneSpec, SfxMeta, Spec, Transcript, TransitionSpec } from "./types";

export type LayerPlan = { spec: LayerSpec; startSec: number; endSec: number };
export type ScenePlan = {
  i: number;
  spec: SceneSpec;
  theme: Theme;
  startSec: number; // cut-in time
  endSec: number; // cut-out time
  tIn: { t: Trans; dur: number; id: string };
  tOut: { t: Trans; dur: number; id: string };
  layers: LayerPlan[];
  bg: LayerSpec;
  capPos: string;
  capHidden: boolean;
  /** 0 = none, else strength of the legibility scrim behind captions */
  scrim: number;
};
export type SfxPlan = { sec: number; id: string; file: string; vol: number; src: string; from?: number; dur?: number; fade?: number };
export type Plan = { total: number; scenes: ScenePlan[]; sfx: SfxPlan[]; errors: string[] };

const CAT_GAIN: Record<string, number> = {
  whoosh: 0.42, swipe: 0.4, click: 0.55, pop: 0.45, tick: 0.3, type: 0.32, notify: 0.45, result: 0.5, impact: 0.55,
  riser: 0.38, digital: 0.35, shimmer: 0.35, ui: 0.45, sting: 0.5, ambience: 0.22, transition: 0.45, foley: 0.55, alarm: 0.38,
};

/** the "cut" happens a hair before the word so the picture leads the voice */
const PICTURE_LEAD = 0.07;

const warnedMissing = new Set<string>();
/** names of the files in public/ (Studio and renders); null where the list is not available */
const publicFiles = (): Set<string> | null => {
  try {
    const l = getStaticFiles();
    return l.length ? new Set(l.map((f) => f.name.split("\\").join("/").replace(/^\/+/, ""))) : null;
  } catch {
    return null;
  }
};

export const buildPlan = (spec: Spec, transcript: Transcript | null, beats: BeatGrid | null, sfxIndex: SfxMeta[], total: number, fps = 60): Plan => {
  const errors: string[] = [];
  const staticNames = publicFiles();
  const baseTheme = getTheme(spec.style);
  const ctx = (extra: Partial<TimeCtx>): TimeCtx => ({ transcript, beats, total, ...extra });
  const safe = (fn: () => number, fb: number, what: string) => {
    try {
      return fn();
    } catch (e) {
      errors.push(`${what}: ${(e as Error).message}`);
      return fb;
    }
  };

  // ---------------- scene cut times
  let prev = 0;
  const starts = spec.scenes.map((s, i) => {
    if (i === 0) return 0;
    const isWord = typeof s.at === "string" && s.at.startsWith("@");
    const t = safe(() => resolve(s.at, ctx({ from: prev })), prev + 2, `scene ${s.id ?? i} at`);
    const cut = Math.max(prev + 0.3, isWord ? t - PICTURE_LEAD : t);
    prev = cut;
    return cut;
  });
  const ends = starts.map((s, i) => {
    const sc = spec.scenes[i];
    if (sc.until !== undefined) return safe(() => resolve(sc.until, ctx({ from: s })), starts[i + 1] ?? total, `scene ${i} until`);
    return starts[i + 1] ?? total;
  });

  const transOf = (t: TransitionSpec | string | undefined, theme: Theme) => {
    const id = typeof t === "string" ? t : t?.type ?? theme.motion.transition;
    const tr = getTransition(id);
    const dur = typeof t === "object" && t?.dur !== undefined ? t.dur : id === theme.motion.transition ? theme.motion.transDur : tr.dur;
    return { t: tr, dur, id, sfx: typeof t === "object" ? t.sfx : undefined };
  };

  const scenes: ScenePlan[] = spec.scenes.map((s, i) => {
    const theme = s.style ? getTheme(s.style) : baseTheme;
    const len = ends[i] - starts[i];
    const tin = i === 0 ? { t: getTransition("cut"), dur: 0, id: "cut", sfx: undefined } : transOf(s.transition, theme);
    const nextLen = i < spec.scenes.length - 1 ? ends[i + 1] - starts[i + 1] : 0;
    const tout =
      i < spec.scenes.length - 1 ? transOf(spec.scenes[i + 1].transition, spec.scenes[i + 1].style ? getTheme(spec.scenes[i + 1].style) : baseTheme) : { t: getTransition("cut"), dur: 0, id: "cut", sfx: undefined };
    const prevLen = i > 0 ? ends[i - 1] - starts[i - 1] : len;
    tin.dur = Math.min(tin.dur, len * 0.6, prevLen * 0.6);
    tout.dur = Math.min(tout.dur, len * 0.6, nextLen * 0.6);

    const layers: LayerPlan[] = (s.layers ?? []).map((l, k) => {
      const ls = safe(() => resolve(l.at ?? 0, ctx({ from: starts[i], base: starts[i], end: ends[i] })), starts[i], `scene ${s.id ?? i} layer ${k} (${l.block}) at`);
      const le = l.until !== undefined ? safe(() => resolve(l.until, ctx({ from: ls, base: starts[i], end: ends[i] })), ends[i], `layer ${l.block} until`) : ends[i] + tout.dur / 2;
      if (!REGISTRY[l.block]) errors.push(`unknown block "${l.block}" in scene ${s.id ?? i}`);
      return { spec: l, startSec: Math.max(starts[i] - tin.dur / 2, ls), endSec: Math.max(ls + 0.1, le) };
    });
    const bgSpec: LayerSpec =
      typeof s.bg === "string" ? { block: s.bg } : s.bg ?? { block: theme.bgBlock, props: theme.bgProps };
    if (!REGISTRY[bgSpec.block]) errors.push(`unknown bg block "${bgSpec.block}"`);
    const capHidden = s.captions === false || spec.captions?.mode === "none" || !transcript;
    // a %pos directive on the scene's first caption card moves the stage too
    const cardPos = transcript?.cards.find((c) => c.start >= starts[i] - 0.1 && c.start < ends[i])?.pos;
    const capPos = (s.captions && s.captions.pos) || cardPos || (s.style ? theme.captionPos : spec.captions?.pos ?? theme.captionPos);
    const busyBg = ["3d"].includes(REGISTRY[bgSpec.block]?.cat ?? "") || ["PhotoBG", "VideoBG", "ShaderBG"].includes(bgSpec.block);
    const scrimSpec = s.captions && typeof s.captions === "object" ? (s.captions as { scrim?: number | boolean }).scrim : undefined;
    const scrim = capHidden ? 0 : scrimSpec === false ? 0 : typeof scrimSpec === "number" ? scrimSpec : scrimSpec === true || busyBg ? 0.85 : 0;
    return { i, spec: s, theme, startSec: starts[i], endSec: ends[i], tIn: tin, tOut: tout, layers, bg: bgSpec, capPos, capHidden, scrim };
  });

  // ---------------- sound plan
  const meta = new Map(sfxIndex.map((m) => [m.id, m]));
  const sfx: SfxPlan[] = [];
  const vol = spec.sfxVolume ?? 1;
  /** follow alias chains (retired / pack-mapped ids); null = deliberately silent */
  const lookup = (id: string): SfxMeta | null | undefined => {
    let m = meta.get(id);
    for (let k = 0; m && m.alias !== undefined && k < 5; k++) {
      if (m.alias === null) return null;
      m = meta.get(m.alias);
    }
    return m && m.file ? m : m === undefined ? undefined : null;
  };
  const add = (sec: number, id: string | null | undefined, v = 1, alignPeak = true) => {
    if (!id) return;
    const m = lookup(id);
    if (m === null) return;
    if (!m) {
      errors.push(`unknown sfx "${id}"`);
      return;
    }
    const at = alignPeak ? sec - m.peak : sec;
    sfx.push({ sec: Math.max(0, at), id: m.id, file: m.file as string, src: m.category, vol: (CAT_GAIN[m.category] ?? 0.45) * v * vol });
  };
  const auto = spec.autoSfx !== false;
  if (auto) {
    scenes.forEach((sc) => {
      if (sc.i === 0) return;
      const sid = (sc.tIn as { sfx?: string | false }).sfx;
      if (sid === false) return;
      add(sc.startSec, sid ?? sc.tIn.t.sfx, 1);
    });
    scenes.forEach((sc) => {
      sc.layers.forEach((lp) => {
        const def = REGISTRY[lp.spec.block];
        if (!def) return;
        const nearCut = Math.abs(lp.startSec - sc.startSec) < 0.2 && sc.i > 0;
        const id = lp.spec.sfx === false ? null : (lp.spec.sfx as string | undefined) ?? def.sfx ?? null;
        if (id && !nearCut) add(lp.startSec + 0.02, id, 0.9, false);
        if (def.events && lp.spec.sfx !== false) {
          const at = (a: unknown, fb?: number) => {
            if (a === undefined || a === null) return Math.round((fb ?? 0) * fps);
            try {
              return Math.round((resolve(a as never, ctx({ from: lp.startSec, base: lp.startSec, end: lp.endSec }), fb) - lp.startSec) * fps);
            } catch (e) {
              errors.push(`${lp.spec.block} event: ${(e as Error).message}`);
              return 0;
            }
          };
          try {
            def.events(lp.spec.props ?? {}, { fps, dur: Math.round((lp.endSec - lp.startSec) * fps), at }).forEach((ev) =>
              add(lp.startSec + ev.f / fps, ev.id, ev.vol ?? 1, false),
            );
          } catch (e) {
            errors.push(`${lp.spec.block} events failed: ${(e as Error).message}`);
          }
        }
      });
    });
  }
  (spec.sfx ?? []).forEach((c) => {
    const s = safe(() => resolve(c.at, ctx({ from: 0 })), 0, `sfx ${c.id}`);
    if (c.src) {
      // a project file: played as is, trimmed and faded, not mapped through the library.
      // A file missing from public/ (a sound pack not added yet) is skipped instead of breaking the render.
      if (staticNames && !staticNames.has(c.src.replace(/^\/+/, ""))) {
        if (!warnedMissing.has(c.src)) console.warn(`sfx ${c.id}: ${c.src} not found in public/ — skipped`);
        warnedMissing.add(c.src);
        return;
      }
      sfx.push({ sec: Math.max(0, s), id: c.id, file: c.src, vol: (c.volume ?? 1) * vol, src: "project:" + c.id, from: c.from, dur: c.dur, fade: c.fade });
      return;
    }
    add(s, c.id, c.volume ?? 1, c.alignPeak !== false);
  });
  // de-clutter: same category within 90 ms -> drop; > 4 sounds in 1 s -> soften extras
  sfx.sort((a, b) => a.sec - b.sec);
  const kept: SfxPlan[] = [];
  for (const s of sfx) {
    if (kept.some((k) => k.src === s.src && Math.abs(k.sec - s.sec) < 0.09)) continue;
    const dense = kept.filter((k) => s.sec - k.sec < 1).length;
    kept.push(dense >= 4 ? { ...s, vol: s.vol * 0.5 } : s);
  }
  return { total, scenes, sfx: kept, errors };
};
