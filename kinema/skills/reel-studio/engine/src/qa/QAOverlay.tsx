import React, { useLayoutEffect, useRef } from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";

/**
 * Overlap / safe-zone checker. Active only when the composition gets `qa: true`.
 * Measures the INK box (text glyphs + painted elements) of every caption card and every layer,
 * then reports:
 *   overlap   caption ∩ layer, or layer ∩ layer (unless a side is marked overlay/overlap-ok)
 *   edge      text closer than 30 px to the left/right frame edge
 *   offscreen block content leaving the frame
 * Conflicts are drawn in pure magenta (#FF00FF) and logged as `QA {json}` lines.
 */
type R = { x: number; y: number; w: number; h: number };

const isPainted = (cs: CSSStyleDeclaration, tag: string) =>
  (cs.backgroundColor !== "rgba(0, 0, 0, 0)" && cs.backgroundColor !== "transparent") ||
  cs.backgroundImage !== "none" ||
  parseFloat(cs.borderTopWidth) > 0 ||
  ["IMG", "svg", "CANVAS", "VIDEO"].includes(tag);

/** opacity of an element including all ancestors up to `stop` */
const effOpacity = (e: Element | null, stop: Element): number => {
  let o = 1;
  let n: Element | null = e;
  while (n && n !== stop) {
    o *= parseFloat(getComputedStyle(n).opacity || "1");
    if (o < 0.05) return 0;
    n = n.parentElement;
  }
  return o;
};

const inkBox = (root: Element, W: number, H: number): R | null => {
  let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
  const add = (b: DOMRect) => {
    if (b.width <= 0.5 || b.height <= 0.5) return;
    if (b.width * b.height > W * H * 0.85) return; // full-frame helpers are not ink
    x0 = Math.min(x0, b.left); y0 = Math.min(y0, b.top); x1 = Math.max(x1, b.right); y1 = Math.max(y1, b.bottom);
  };
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT | NodeFilter.SHOW_TEXT);
  let n: Node | null;
  let k = 0;
  while ((n = walker.nextNode()) && k < 2500) {
    k++;
    if (n.nodeType === 3) {
      if (!n.textContent?.trim()) continue;
      const pe = n.parentElement;
      if (pe) {
        const cs = getComputedStyle(pe);
        if (parseFloat(cs.opacity) < 0.05 || cs.visibility === "hidden" || cs.color === "rgba(0, 0, 0, 0)") continue;
      }
      const r = document.createRange();
      r.selectNodeContents(n);
      add(r.getBoundingClientRect());
      continue;
    }
    const e = n as HTMLElement;
    const cs = getComputedStyle(e);
    if (parseFloat(cs.opacity) < 0.05 || cs.visibility === "hidden" || cs.display === "none") continue;
    if (isPainted(cs, e.tagName)) add(e.getBoundingClientRect());
  }
  if (!isFinite(x0)) return null;
  return { x: x0, y: y0, w: x1 - x0, h: y1 - y0 };
};

const inter = (a: R, b: R, pad = 0): R | null => {
  const x = Math.max(a.x - pad, b.x - pad);
  const y = Math.max(a.y - pad, b.y - pad);
  const x2 = Math.min(a.x + a.w + pad, b.x + b.w + pad);
  const y2 = Math.min(a.y + a.h + pad, b.y + b.h + pad);
  return x2 > x && y2 > y ? { x, y, w: x2 - x, h: y2 - y } : null;
};

export const QAOverlay: React.FC<{ transition?: boolean }> = ({ transition }) => {
  const frame = useCurrentFrame();
  const { width: W, height: H, fps } = useVideoConfig();
  const ref = useRef<HTMLDivElement>(null);
  useLayoutEffect(() => {
    const measure = () => {
      const host = ref.current;
      if (!host) return;
      if (transition) {
        host.innerHTML = "";
        return; // scenes are mid-transition: motion overlaps are intended
      }
      const root = host.parentElement!;
      // page coords -> composition coords (stills may be rendered scaled)
      const rb = root.getBoundingClientRect();
      const sx = W / rb.width;
      const sy = H / rb.height;
      const norm = (r: R | null): R | null => (r ? { x: (r.x - rb.left) * sx, y: (r.y - rb.top) * sy, w: r.w * sx, h: r.h * sy } : null);
      // anything fading below 35 % opacity is a ghost, not a visible collision
      const caps = Array.from(root.querySelectorAll('[data-qa="caption"]'))
        .filter((e) => effOpacity(e, root) > 0.35)
        .map((e) => ({ id: "caption", box: norm(inkBox(e, rb.width, rb.height)) }))
        .filter((c) => c.box);
      const layers = Array.from(root.querySelectorAll('[data-qa="layer"]'))
        .filter((e) => e.getAttribute("data-qa-cat") !== "bg" && e.getAttribute("data-qa-cat") !== "3d" && effOpacity(e, root) > 0.35)
        .map((e) => {
          const proxy = e.getAttribute("data-qa-proxy") === "1";
          const r = e.getBoundingClientRect();
          const box = proxy ? norm({ x: r.left, y: r.top, w: r.width, h: r.height }) : norm(inkBox(e, rb.width, rb.height));
          return { id: e.getAttribute("data-qa-id") ?? "?", ok: e.getAttribute("data-qa-ok") === "1", bleed: proxy || e.getAttribute("data-qa-bleed") === "1", proxy, box };
        })
        .filter((l) => l.box);
      const issues: { kind: string; a: string; b?: string; r: R }[] = [];
      for (const c of caps) {
        for (const l of layers) {
          if (l.ok) continue;
          const i = inter(c.box!, l.box!, 10);
          if (i && i.w * i.h > 150) issues.push({ kind: "overlap", a: "caption", b: l.id, r: i });
        }
        const cb = c.box!;
        if (cb.x < 30 || cb.x + cb.w > W - 30) issues.push({ kind: "edge", a: "caption", r: cb });
        if (cb.y + cb.h > H * 0.8) issues.push({ kind: "unsafe-bottom", a: "caption", r: cb });
      }
      for (let i = 0; i < layers.length; i++)
        for (let j = i + 1; j < layers.length; j++) {
          const a = layers[i];
          const b = layers[j];
          if (a.ok || b.ok || a.proxy || b.proxy || a.id === "3d-screen" || b.id === "3d-screen") continue;
          const r = inter(a.box!, b.box!, 4);
          if (r && r.w * r.h > 0.02 * Math.min(a.box!.w * a.box!.h, b.box!.w * b.box!.h)) issues.push({ kind: "overlap", a: a.id, b: b.id, r });
        }
      for (const l of layers) {
        if (l.bleed) continue;
        const b = l.box!;
        if (b.x < -2 || b.y < -2 || b.x + b.w > W + 2 || b.y + b.h > H + 2) issues.push({ kind: "offscreen", a: l.id, r: b });
      }
      host.innerHTML = issues
        .map((s) => `<div style="position:absolute;left:${s.r.x}px;top:${s.r.y}px;width:${s.r.w}px;height:${s.r.h}px;outline:8px solid #FF00FF;background:rgba(255,0,255,0.35)"></div>`)
        .join("");
      if (issues.length) console.log("QA " + JSON.stringify({ frame, t: +(frame / fps).toFixed(2), issues: issues.map((s) => ({ kind: s.kind, a: s.a, b: s.b, r: [Math.round(s.r.x), Math.round(s.r.y), Math.round(s.r.w), Math.round(s.r.h)] })) }));
    };
    measure();
    const host = ref.current;
    const root = host?.parentElement;
    if (!root || transition) return;
    // 3D models / images load asynchronously after the first layout: measure again when the DOM changes
    let pending = 0;
    const obs = new MutationObserver((muts) => {
      if (muts.every((m) => host && (m.target === host || host.contains(m.target as Node)))) return;
      cancelAnimationFrame(pending);
      pending = requestAnimationFrame(measure);
    });
    obs.observe(root, { childList: true, subtree: true });
    return () => {
      obs.disconnect();
      cancelAnimationFrame(pending);
    };
  });
  return <AbsoluteFill ref={ref} style={{ pointerEvents: "none", zIndex: 9999 }} />;
};
