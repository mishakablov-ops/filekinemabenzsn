import type { WordStyle } from "./types";

/**
 * Inline markup shared by blocks (and mirrored in scripts/script_parse.py for the voiceover):
 *   *слово*      serif italic        [слово]   accent colour
 *   ==слово==    highlight box       ~~слово~~ strike-through
 *   ^слово^      second accent       __слово__ outline
 *   !!слово!!    negative (red)      ++слово++ positive (green)
 *   /            line break          {показ|произношение}  display text | spoken text
 */
export type Tok = { text: string; style: WordStyle[]; line: number };

const PAIRS: [RegExp, WordStyle][] = [
  [/==(.+?)==/g, "mark"],
  [/~~(.+?)~~/g, "strike"],
  [/__(.+?)__/g, "outline"],
  [/!!(.+?)!!/g, "neg"],
  [/\+\+(.+?)\+\+/g, "pos"],
  [/\*(.+?)\*/g, "italic"],
  [/\[(.+?)\]/g, "accent"],
  [/\^(.+?)\^/g, "alt"],
];

export const parseMarkup = (src: string): Tok[] => {
  // display part of {display|spoken}
  let s = src.replace(/\{([^|}]*)\|[^}]*\}/g, "$1");
  // mark spans with sentinels \u0001<style>\u0002 ... \u0003
  for (const [re, st] of PAIRS) s = s.replace(re, (_m, inner: string) => `\u0001${st}\u0002${inner}\u0003`);
  const out: Tok[] = [];
  let line = 0;
  const stack: WordStyle[] = [];
  let buf = "";
  let i = 0;
  const flush = () => {
    if (buf.trim()) out.push({ text: buf.trim(), style: [...stack], line });
    buf = "";
  };
  while (i < s.length) {
    const c = s[i];
    if (c === "\u0001") {
      flush();
      const j = s.indexOf("\u0002", i);
      stack.push(s.slice(i + 1, j) as WordStyle);
      i = j + 1;
      continue;
    }
    if (c === "\u0003") {
      flush();
      stack.pop();
      i++;
      continue;
    }
    if (c === "/" && s[i + 1] !== "/") {
      flush();
      line++;
      i++;
      continue;
    }
    if (c === " " || c === "\n") {
      flush();
      i++;
      continue;
    }
    buf += c;
    i++;
  }
  flush();
  return out;
};

export const plain = (src: string) => parseMarkup(src).map((t) => t.text).join(" ");
