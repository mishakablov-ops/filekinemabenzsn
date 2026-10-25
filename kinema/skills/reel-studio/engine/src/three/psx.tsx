/**
 * PS1 + VHS look for the podezd reel.
 *  psxify(root): every material in the tree gets PS1 vertex snapping (vertices jump between screen-pixel positions),
 *    15-bit colour with an ordered 4x4 Bayer dither, and nearest-neighbour textures. Works with the low-res
 *    buffer of <Stage3D dpr={0.25} pixelated> (gl_FragCoord is then the big pixel).
 *  <VhsLook>: tape playback over the scene — chroma bleed, wobble, tracking band, head-switching noise at the
 *    bottom, scanlines, grain, washed blacks, and the VCR on-screen display (PLAY, tape counter, date).
 */
import React, { useLayoutEffect, useRef } from "react";
import { AbsoluteFill } from "remotion";
import * as THREE from "three";

export const PSX = { w: 184, h: 326 };

const patchMaterial = (m: THREE.Material, res: [number, number], levels: number) => {
  if ((m as THREE.Material & { userData: { psx?: boolean } }).userData.psx) return;
  m.userData.psx = true;
  const prev = m.onBeforeCompile?.bind(m);
  const prevKey = m.customProgramCacheKey?.bind(m);
  m.onBeforeCompile = (sh, r) => {
    prev?.(sh, r);
    sh.uniforms.uPsxRes = { value: new THREE.Vector2(res[0] / 2, res[1] / 2) };
    sh.uniforms.uPsxLevels = { value: levels };
    sh.vertexShader = sh.vertexShader
      .replace("#include <common>", "#include <common>\nuniform vec2 uPsxRes;")
      .replace(
        "#include <project_vertex>",
        `#include <project_vertex>
  gl_Position.xy = floor(gl_Position.xy / gl_Position.w * uPsxRes + 0.5) / uPsxRes * gl_Position.w;`,
      );
    sh.fragmentShader = sh.fragmentShader
      .replace("#include <common>", "#include <common>\nuniform float uPsxLevels;")
      .replace(
        "#include <dithering_fragment>",
        `#include <dithering_fragment>
  {
    int bx = int(mod(gl_FragCoord.x, 4.0)), by = int(mod(gl_FragCoord.y, 4.0));
    float bayer[16] = float[16](0.0, 8.0, 2.0, 10.0, 12.0, 4.0, 14.0, 6.0, 3.0, 11.0, 1.0, 9.0, 15.0, 7.0, 13.0, 5.0);
    float d = (bayer[by * 4 + bx] / 16.0 - 0.5) / uPsxLevels;
    gl_FragColor.rgb = floor((gl_FragColor.rgb + d) * uPsxLevels + 0.5) / uPsxLevels;
  }`,
      );
  };
  m.customProgramCacheKey = () => (prevKey ? prevKey() : "") + "|psx";
  m.needsUpdate = true;
  for (const k of ["map", "emissiveMap", "alphaMap"] as const) {
    const t = (m as unknown as Record<string, THREE.Texture | null>)[k];
    if (t && !(t as THREE.Texture & { userData: { psx?: boolean } }).userData.psx) {
      t.magFilter = THREE.NearestFilter;
      t.minFilter = THREE.NearestMipmapNearestFilter;
      t.anisotropy = 1;
      t.userData.psx = true;
      t.needsUpdate = true;
    }
  }
  // PS1: faceted shading, no normal maps
  const sm = m as THREE.MeshStandardMaterial;
  if ("flatShading" in sm) sm.flatShading = true;
  if (sm.normalMap) sm.normalMap = null;
};

/** apply the PS1 look to every material under `root` (idempotent) */
export function psxify(root: THREE.Object3D, o: { res?: [number, number]; levels?: number } = {}) {
  const res = o.res ?? [PSX.w, PSX.h];
  const levels = o.levels ?? 31;
  root.traverse((obj) => {
    const mm = (obj as THREE.Mesh).material;
    if (!mm) return;
    (Array.isArray(mm) ? mm : [mm]).forEach((m) => patchMaterial(m, res, levels));
  });
  return root;
}

// ------------------------------------------------------------------ VHS playback overlay
const rnd = (seed: number) => {
  let s = Math.floor(seed * 9973) % 2147483647 || 1;
  return () => {
    s = (s * 16807) % 2147483647;
    return (s - 1) / 2147483646;
  };
};

/** per-frame noise canvas: tracking band + head-switching noise + sparse dropouts */
const TapeNoise: React.FC<{ t: number; band: number; strength: number }> = ({ t, band, strength }) => {
  const ref = useRef<HTMLCanvasElement>(null);
  useLayoutEffect(() => {
    const c = ref.current;
    if (!c) return;
    const g = c.getContext("2d")!;
    const W = c.width, H = c.height;
    g.clearRect(0, 0, W, H);
    const r = rnd(Math.floor(t * 30) + 7);
    // tracking band rolling down the frame
    const by = band * H, bh = H * 0.05 * strength;
    for (let i = 0; i < 70 * strength; i++) {
      const y = by + (r() - 0.5) * bh;
      const x = r() * W, w = 20 + r() * 260;
      g.fillStyle = `rgba(255,255,255,${0.25 + r() * 0.5})`;
      g.fillRect(x, y, w, 1 + r() * 2);
    }
    g.fillStyle = `rgba(0,0,0,${0.25 * strength})`;
    g.fillRect(0, by + bh * 0.6, W, 3);
    // head-switching noise along the bottom edge
    for (let y = H - 26; y < H; y += 2) {
      const x0 = r() * 40;
      g.fillStyle = `rgba(255,255,255,${0.08 + r() * 0.25})`;
      g.fillRect(x0, y, W * (0.4 + r() * 0.6), 2);
    }
    // sparse dropouts
    for (let i = 0; i < 6; i++) {
      if (r() > 0.5) continue;
      g.fillStyle = `rgba(255,255,255,${0.4 + r() * 0.5})`;
      g.fillRect(r() * W, r() * H, 8 + r() * 70, 1);
    }
  }, [t, band, strength]);
  return <canvas ref={ref} width={540} height={960} style={{ position: "absolute", inset: 0, width: "100%", height: "100%", pointerEvents: "none" }} />;
};

export const VhsLook: React.FC<{
  t: number;
  children: React.ReactNode;
  /** 0..1: how worn the tape is at this moment (tracking, wobble, noise) */
  wear?: number;
  /** show the VCR on-screen display */
  osd?: boolean;
  /** seconds on the tape counter at t = 0 */
  counter0?: number;
  date?: string;
  vignette?: number;
  /** camcorder recording OSD (REC, clock) instead of VCR playback */
  rec?: { clock: string } | null;
}> = ({ t, children, wear = 0.35, osd = true, counter0 = 0, date = "НОЯ.26 2004", vignette = 0.55, rec = null }) => {
  const seed = Math.floor(t * 30);
  const r = rnd(seed + 3);
  const wobble = (Math.sin(t * 2.3) * 0.6 + (r() - 0.5) * 1.4) * (0.6 + wear * 2);
  const band = (t * 0.11 + 0.15) % 1.2 - 0.1;
  const id = "vhs" + (seed % 7);
  const ctr = counter0 + t;
  const hh = Math.floor(ctr / 3600), mm = Math.floor((ctr % 3600) / 60), ss = Math.floor(ctr % 60);
  const fmt = (n: number) => String(n).padStart(2, "0");
  return (
    <AbsoluteFill style={{ background: "#000" }}>
      <svg width="0" height="0" style={{ position: "absolute" }}>
        <filter id={id} x="0" y="0" width="100%" height="100%" colorInterpolationFilters="sRGB">
          <feTurbulence type="fractalNoise" baseFrequency="0 0.035" numOctaves="1" seed={seed % 97} result="wave" />
          <feDisplacementMap in="SourceGraphic" in2="wave" scale={2 + wear * 7} xChannelSelector="R" yChannelSelector="G" result="src" />
          <feColorMatrix in="src" type="matrix" values="1 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 1 0" result="r" />
          <feOffset in="r" dx={4 + wear * 3} dy="0" result="r1" />
          <feGaussianBlur in="r1" stdDeviation="1.3 0" result="r2" />
          <feColorMatrix in="src" type="matrix" values="0 0 0 0 0  0 1 0 0 0  0 0 0 0 0  0 0 0 1 0" result="g" />
          <feColorMatrix in="src" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 1 0 0  0 0 0 1 0" result="b" />
          <feOffset in="b" dx={-3 - wear * 2} dy="0" result="b1" />
          <feGaussianBlur in="b1" stdDeviation="1.5 0" result="b2" />
          <feBlend in="r2" in2="g" mode="screen" result="rg" />
          <feBlend in="rg" in2="b2" mode="screen" />
        </filter>
      </svg>
      <AbsoluteFill style={{ filter: `url(#${id}) saturate(0.78) contrast(1.06) brightness(1.02)`, transform: `translateX(${wobble.toFixed(2)}px)` }}>{children}</AbsoluteFill>
      {/* lifted, slightly green-blue blacks of a worn tape */}
      <AbsoluteFill style={{ background: "rgba(18,26,30,0.18)", mixBlendMode: "screen", pointerEvents: "none" }} />
      <AbsoluteFill style={{ background: "repeating-linear-gradient(0deg, rgba(0,0,0,0.22) 0px, rgba(0,0,0,0.22) 2px, rgba(0,0,0,0) 2px, rgba(0,0,0,0) 6px)", pointerEvents: "none" }} />
      <AbsoluteFill style={{ background: `radial-gradient(ellipse 85% 75% at 50% 50%, rgba(0,0,0,0) 50%, rgba(0,0,0,${vignette}) 100%)`, pointerEvents: "none" }} />
      <AbsoluteFill style={{ opacity: 0.16 + wear * 0.12, mixBlendMode: "overlay", pointerEvents: "none" }}>
        <svg width="100%" height="100%">
          <filter id={"vg" + (seed % 11)}>
            <feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="2" seed={seed % 113} stitchTiles="stitch" />
            <feColorMatrix type="saturate" values="0" />
          </filter>
          <rect width="100%" height="100%" filter={`url(#vg${seed % 11})`} />
        </svg>
      </AbsoluteFill>
      <TapeNoise t={t} band={band} strength={0.4 + wear} />
      {osd && rec ? (
        <>
          <div style={{ position: "absolute", left: 70, top: 120, fontFamily: "'Press Start 2P', monospace", fontSize: 40, color: "#FF3A2E", textShadow: "4px 4px 0 #000", opacity: Math.floor(t * 2) % 2 ? 1 : 0.15 }}>● REC</div>
          <div style={{ position: "absolute", left: 70, bottom: 380, fontFamily: "'Press Start 2P', monospace", fontSize: 34, color: "#F2F2EE", textShadow: "4px 4px 0 #000" }}>SP</div>
          <div style={{ position: "absolute", right: 70, bottom: 380, textAlign: "right", fontFamily: "'Press Start 2P', monospace", fontSize: 34, lineHeight: 1.5, color: "#F2F2EE", textShadow: "4px 4px 0 #000" }}>
            {date}
            <br />
            {rec.clock}
          </div>
        </>
      ) : osd ? (
        <>
          <div style={{ position: "absolute", left: 70, bottom: 380, fontFamily: "'VT323', 'Courier New', monospace", fontWeight: 700, fontSize: 64, color: "#F2F2EE", letterSpacing: 4, textShadow: "3px 0 0 rgba(255,40,60,0.55), -3px 0 0 rgba(40,120,255,0.55), 0 0 10px rgba(255,255,255,0.35)" }}>
            ▶ PLAY
          </div>
          <div style={{ position: "absolute", right: 70, bottom: 380, textAlign: "right", fontFamily: "'VT323', 'Courier New', monospace", fontWeight: 700, fontSize: 54, lineHeight: 1.15, color: "#F2F2EE", letterSpacing: 3, textShadow: "3px 0 0 rgba(255,40,60,0.55), -3px 0 0 rgba(40,120,255,0.55), 0 0 10px rgba(255,255,255,0.35)" }}>
            {date}
            <br />
            {`${hh}:${fmt(mm)}:${fmt(ss)}`}
          </div>
        </>
      ) : null}
    </AbsoluteFill>
  );
};
