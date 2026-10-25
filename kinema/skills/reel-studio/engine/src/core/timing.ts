import type { Anchor, BeatGrid, Transcript } from "./types";

export const norm = (s: string) =>
  s
    .toLowerCase()
    .replace(/ё/g, "е")
    .replace(/[ ]/g, " ")
    .replace(/[«»"“”„'’`.,!?…:;()\[\]{}*_=~^|/\\—–-]/g, " ")
    .replace(/\s+/g, " ")
    .trim();

export type TimeCtx = {
  transcript?: Transcript | null;
  beats?: BeatGrid | null;
  total: number; // composition length, seconds
  /** search for "@word" starting at this time (seconds) */
  from?: number;
  /** numbers / "3s" are relative to this (seconds); 0 for absolute */
  base?: number;
  /** what "end" means */
  end?: number;
};

const tokensCache = new WeakMap<object, string[]>();
const wordTokens = (t: Transcript) => {
  let c = tokensCache.get(t);
  if (!c) {
    c = t.words.map((w) => norm(w.text));
    tokensCache.set(t, c);
  }
  return c;
};

/** Find a phrase in the transcript. Returns [startWordIdx, endWordIdx] or null. */
export const findPhrase = (t: Transcript, phrase: string, fromSec: number, occurrence = 1): [number, number] | null => {
  const want = norm(phrase).split(" ").filter(Boolean);
  if (!want.length) return null;
  const toks = wordTokens(t);
  let seen = 0;
  for (let i = 0; i < toks.length; i++) {
    if (t.words[i].start < fromSec - 0.05) continue;
    let ok = true;
    let j = 0;
    let k = i;
    while (j < want.length && k < toks.length) {
      // a display token may contain several spoken words ("10 000") -> compare joined
      const tk = toks[k].split(" ");
      for (const piece of tk) {
        if (j >= want.length) break;
        if (piece !== want[j] && !(j === want.length - 1 && piece.startsWith(want[j]))) {
          ok = false;
          break;
        }
        j++;
      }
      if (!ok) break;
      k++;
    }
    if (ok && j >= want.length) {
      seen++;
      if (seen === occurrence) return [i, k - 1];
    }
  }
  return null;
};

export class AnchorError extends Error {}

const ANCHOR_RE = /^@(.+?)(#(\d+))?(>)?([+-]\d+(?:\.\d+)?)?$/;

/** Resolve an anchor to absolute seconds. */
export const resolve = (a: Anchor | undefined, ctx: TimeCtx, fallback?: number): number => {
  if (a === undefined || a === null || a === "") {
    if (fallback === undefined) throw new AnchorError("empty anchor");
    return fallback;
  }
  const base = ctx.base ?? 0;
  if (typeof a === "number") return base + a;
  const s = a.trim();
  if (/^-?\d+(\.\d+)?s?$/.test(s)) return base + parseFloat(s);
  if (s === "end") return ctx.end ?? ctx.total;
  if (s === "start") return base;
  if (s.startsWith("f:")) return parseInt(s.slice(2), 10) / 60; // caller should prefer seconds
  const offM = s.match(/^(card|beat|bar|drop|section):([\w-]+)([+-]\d+(?:\.\d+)?)?$/);
  if (offM) {
    const [, kind, idxS, offS] = offM;
    const off = offS ? parseFloat(offS) : 0;
    if (kind === "card") {
      const c = ctx.transcript?.cards[parseInt(idxS, 10)];
      if (!c) throw new AnchorError(`no caption card ${idxS}`);
      return c.start + off;
    }
    const g = ctx.beats;
    if (!g) throw new AnchorError(`anchor ${s} needs a music beat grid`);
    if (kind === "section") {
      const sec = g.sections.find((x) => x.name === idxS);
      if (!sec) throw new AnchorError(`no section ${idxS}`);
      return sec.start + off;
    }
    const idx = parseInt(idxS, 10);
    const arr = kind === "beat" ? g.beats : kind === "bar" ? g.bars : g.drops;
    if (idx < arr.length) return arr[idx] + off;
    // extrapolate past the grid
    const step = kind === "beat" ? g.beatSec : g.barSec;
    return arr[arr.length - 1] + (idx - arr.length + 1) * step + off;
  }
  const m = s.match(ANCHOR_RE);
  if (m) {
    const [, phrase, , occS, endFlag, offS] = m;
    const t = ctx.transcript;
    if (!t) throw new AnchorError(`anchor "${s}" needs a transcript (voice/words)`);
    const occ = occS ? parseInt(occS, 10) : 1;
    let hit = findPhrase(t, phrase, ctx.from ?? 0, occ);
    if (!hit) hit = findPhrase(t, phrase, 0, occ);
    if (!hit) throw new AnchorError(`phrase not found in voiceover: "${phrase}"`);
    const tt = endFlag ? t.words[hit[1]].end : t.words[hit[0]].start;
    return tt + (offS ? parseFloat(offS) : 0);
  }
  throw new AnchorError(`cannot parse anchor "${s}"`);
};

export const secToFrame = (s: number, fps: number) => Math.round(s * fps);
