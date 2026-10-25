import { noise2D } from "@remotion/noise";
import React, { useMemo } from "react";
import { AbsoluteFill } from "remotion";
import * as THREE from "three";
import { useBlockTime, useTheme } from "../core/context";
import { E, clamp01 } from "../core/motion";
import { camAt, makeCamera, project, Stage3D, type CamKey } from "./core";

const SIZE = 30;

const rawHeight = (x: number, z: number, seed: string) => {
  // ridged multifractal (sharp crests) + soft fbm + a hero massif behind the centre
  let h = 0;
  let a = 1;
  let fq = 0.055;
  let w = 1;
  for (let o = 0; o < 5; o++) {
    let n = 1 - Math.abs(noise2D(seed + o, x * fq, z * fq));
    n = Math.pow(n, 1.7);
    const r = n * w;
    h += r * a;
    w = Math.min(1, Math.max(0, r * 1.6));
    a *= 0.52;
    fq *= 2.1;
  }
  const soft = noise2D(seed + "s", x * 0.025, z * 0.025) * 0.35;
  const d = Math.sqrt(x * x + (z + 4) * (z + 4));
  const massif = Math.exp(-(d * d) / 90) * 0.7;
  return h + soft + massif;
};

const RANGE = new Map<string, [number, number]>();
const rangeOf = (seed: string) => {
  let r = RANGE.get(seed);
  if (!r) {
    let lo = Infinity;
    let hi = -Infinity;
    for (let i = 0; i <= 64; i++)
      for (let j = 0; j <= 64; j++) {
        const v = rawHeight(-SIZE + (i / 64) * SIZE * 2, -SIZE + (j / 64) * SIZE * 2, seed);
        lo = Math.min(lo, v);
        hi = Math.max(hi, v);
      }
    r = [lo, hi];
    RANGE.set(seed, r);
  }
  return r;
};

/** terrain height in world units, normalised to 0..amp */
export const heightAt = (x: number, z: number, seed: string, amp: number) => {
  const [lo, hi] = rangeOf(seed);
  const n = (rawHeight(x, z, seed) - lo) / (hi - lo);
  return Math.pow(Math.max(0, n), 1.15) * amp;
};

const LOOKS = {
  satellite: { low: "#23391F", mid: "#4B6634", rock: "#7A705C", high: "#B3A890", snow: 99, sky: ["#A9C4E8", "#4C79C2"], fog: "#B7CBE3", line: "#FFFFFF", lineA: 0.0 },
  alpine: { low: "#1F3A22", mid: "#3F5F35", rock: "#6E665A", high: "#A49C8E", snow: 0.78, sky: ["#C9DAF0", "#4F84D6"], fog: "#BFD1E8", line: "#FFFFFF", lineA: 0.0 },
  topo: { low: "#070B18", mid: "#0B1224", rock: "#101A33", high: "#18264A", snow: 99, sky: ["#0B1226", "#04060C"], fog: "#080C1A", line: "#5E8BFF", lineA: 0.7 },
  desert: { low: "#8A5A36", mid: "#B37A4A", rock: "#C9946A", high: "#E2B990", snow: 99, sky: ["#F4D6B8", "#8FB3E6"], fog: "#EBD0B4", line: "#FFFFFF", lineA: 0.0 },
  mono: { low: "#E8E8EC", mid: "#D9DAE0", rock: "#C9CBD3", high: "#F4F4F7", snow: 99, sky: ["#F3F3F6", "#E4E6EE"], fog: "#EEEFF3", line: "#2F6BFF", lineA: 0.35 },
};

const terrainMaterial = (look: keyof typeof LOOKS, accent: string) => {
  const L = LOOKS[look];
  return new THREE.ShaderMaterial({
    uniforms: {
      cLow: { value: new THREE.Color(L.low) }, cMid: { value: new THREE.Color(L.mid) }, cRock: { value: new THREE.Color(L.rock) }, cHigh: { value: new THREE.Color(L.high) },
      cFog: { value: new THREE.Color(L.fog) }, cLine: { value: new THREE.Color(L.line) }, cAcc: { value: new THREE.Color(accent) },
      uSnow: { value: L.snow }, uLineA: { value: L.lineA }, uHmax: { value: 4 }, uScan: { value: -100 }, uScanW: { value: 1.2 }, uHi: { value: -100 },
      uK: { value: 1.6 }, uSun: { value: new THREE.Vector3(-0.75, 0.45, 0.3).normalize() }, uFogNear: { value: 16 }, uFogFar: { value: 62 }, uContours: { value: 0 },
    },
    vertexShader: /* glsl */ `
      varying vec3 vW; varying vec3 vN; varying float vD;
      void main(){ vec4 w = modelMatrix*vec4(position,1.); vW = w.xyz; vN = normalize(mat3(modelMatrix)*normal);
        vec4 mv = viewMatrix*w; vD = -mv.z; gl_Position = projectionMatrix*mv; }`,
    fragmentShader: /* glsl */ `
      uniform vec3 cLow,cMid,cRock,cHigh,cFog,cLine,cAcc,uSun; uniform float uSnow,uLineA,uHmax,uScan,uScanW,uHi,uFogNear,uFogFar,uContours,uK;
      varying vec3 vW; varying vec3 vN; varying float vD;
      float hash(vec2 p){ p = fract(p*vec2(123.34, 456.21)); p += dot(p, p+45.32); return fract(p.x*p.y); }
      float vn(vec2 p){ vec2 i=floor(p), f=fract(p); f=f*f*(3.-2.*f); return mix(mix(hash(i),hash(i+vec2(1,0)),f.x), mix(hash(i+vec2(0,1)),hash(i+vec2(1,1)),f.x), f.y); }
      float fb(vec2 p){ float v=0., a=.5; for(int i=0;i<5;i++){ v+=a*vn(p); p*=2.03; a*=.5; } return v; }
      void main(){
        float h = clamp(vW.y / uHmax, 0., 1.);
        float slope = 1. - clamp(vN.y, 0., 1.);
        vec3 col = mix(cLow, cMid, smoothstep(.05, .35, h));
        col = mix(col, cRock, smoothstep(.25, .55, slope + h*.4));
        col = mix(col, cHigh, smoothstep(.55, .9, h));
        col = mix(col, vec3(.96,.97,.99), smoothstep(uSnow, uSnow+.08, h) * (1. - smoothstep(.45,.7,slope)));
        float tex = fb(vW.xz*2.2);
        col *= .78 + .44*tex;                               // rock / vegetation texture
        col = mix(col, cMid*.8, smoothstep(.55,.75, fb(vW.xz*.35)) * (1.-smoothstep(.2,.5,slope)) * .5);
        float dif = clamp(dot(vN, uSun), 0., 1.);
        float sky = .5 + .5*vN.y;
        col *= .22 + 1.05*dif + .18*sky;
        // contour lines
        float lv = vW.y * uK;
        float ln = 1. - smoothstep(0., fwidth(lv)*1.3, abs(fract(lv) - .5) - .47);
        col = mix(col, cLine, ln * max(uLineA, uContours));
        // highlight iso-line (e.g. the horizon silhouette the agent matches)
        float hl = 1. - smoothstep(0., fwidth(vW.y)*2.5, abs(vW.y - uHi) - .02);
        col = mix(col, cAcc, hl);
        // scanning band
        float sb = exp(-pow((vW.z - uScan)/uScanW, 2.));
        col = mix(col, cAcc, sb*.45);
        col += cAcc * sb * ln * .8;
        float fog = smoothstep(uFogNear, uFogFar, vD);
        col = mix(col, cFog, fog);
        gl_FragColor = vec4(col, 1.);
        #include <colorspace_fragment>
      }`,
    extensions: { derivatives: true } as never,
  });
};

const SkyDome: React.FC<{ top: string; bottom: string }> = ({ top, bottom }) => {
  const mat = useMemo(
    () =>
      new THREE.ShaderMaterial({
        uniforms: { a: { value: new THREE.Color(bottom) }, b: { value: new THREE.Color(top) } },
        vertexShader: `varying vec3 vP; void main(){ vP = normalize(position); gl_Position = projectionMatrix*modelViewMatrix*vec4(position,1.); }`,
        fragmentShader: `uniform vec3 a,b; varying vec3 vP; void main(){ float t = clamp(vP.y*1.6+.05,0.,1.); gl_FragColor = vec4(mix(a,b,pow(t,.7)),1.);
          #include <colorspace_fragment>
        }`,
        side: THREE.BackSide,
        depthWrite: false,
      }),
    [top, bottom],
  );
  return (
    <mesh material={mat} scale={120}>
      <sphereGeometry args={[1, 32, 32]} />
    </mesh>
  );
};

const CAMS: Record<string, CamKey[]> = {
  flyover: [
    { t: 0, pos: [0, 3.4, 15], target: [0, 1.6, 0], fov: 38 },
    { t: 8, pos: [0.8, 2.8, 6.5], target: [-0.6, 1.8, -6], fov: 38 },
  ],
  orbit: [
    { t: 0, pos: [-11, 5.5, 9], target: [0, 1.6, -2], fov: 34 },
    { t: 8, pos: [11, 5.0, 9], target: [0, 1.6, -2], fov: 34 },
  ],
  reveal: [
    { t: 0, pos: [0, 24, 3], target: [0, 0, -1], fov: 34 },
    { t: 3.5, pos: [0, 5.0, 13], target: [0, 1.8, -2], fov: 36, ease: "inOut" },
    { t: 8, pos: [1.5, 4.4, 11], target: [0, 1.9, -2], fov: 36 },
  ],
  top: [
    { t: 0, pos: [0, 26, 0.5], target: [0, 0, 0], fov: 34 },
    { t: 8, pos: [0, 21, 0.5], target: [0, 0, 0], fov: 34 },
  ],
  low: [
    { t: 0, pos: [-3, 1.1, 12], target: [0, 2.2, -4], fov: 40 },
    { t: 8, pos: [2, 1.3, 10], target: [0, 2.2, -4], fov: 40 },
  ],
};

export const Terrain3D: React.FC<{
  look?: keyof typeof LOOKS; seed?: string; amp?: number; cam?: string | CamKey[]; contours?: number; scan?: { at?: unknown; dur?: number };
  highlightHeight?: number; points?: { count: number; at?: unknown; dur?: number }; sky?: boolean; pins?: { x: number; z: number; label?: string; at?: unknown }[];
}> = ({ look = "satellite", seed = "alps", amp = 5, cam = "flyover", contours = 0, scan, highlightHeight, points, sky = true, pins = [] }) => {
  const { f, fps, at } = useBlockTime();
  const th = useTheme();
  const t = f / fps;
  const L = LOOKS[look] ?? LOOKS.satellite;
  const geo = useMemo(() => {
    const g = new THREE.PlaneGeometry(SIZE * 2, SIZE * 2, 380, 380);
    g.rotateX(-Math.PI / 2);
    const pos = g.attributes.position as THREE.BufferAttribute;
    for (let i = 0; i < pos.count; i++) pos.setY(i, heightAt(pos.getX(i), pos.getZ(i), seed, amp));
    g.computeVertexNormals();
    return g;
  }, [seed, amp]);
  const mat = useMemo(() => terrainMaterial(look, th.accent), [look, th.accent]);
  mat.uniforms.uHmax.value = amp;
  mat.uniforms.uK.value = 8 / amp;
  mat.uniforms.uContours.value = contours;
  mat.uniforms.uFogFar.value = look === "topo" ? 48 : 62;
  if (scan) {
    const s = scan.at !== undefined ? at(scan.at) : 0;
    const p = clamp01((f - s) / ((scan.dur ?? 3) * fps));
    mat.uniforms.uScan.value = p > 0 && p < 1 ? 12 - p * 30 : -100;
  } else mat.uniforms.uScan.value = -100;
  mat.uniforms.uHi.value = highlightHeight ?? -100;

  const keys = Array.isArray(cam) ? cam : CAMS[cam] ?? CAMS.flyover;
  const c = camAt(keys, t);
  const pts = useMemo(() => {
    if (!points) return null;
    const n = Math.min(points.count, 6000);
    const arr: THREE.Vector3[] = [];
    let k = 0;
    while (arr.length < n && k < n * 4) {
      k++;
      const x = (noise2D("px" + k, k * 0.37, 0.1) * 0.5 + 0.5) * SIZE * 1.4 - SIZE * 0.7;
      const z = (noise2D("pz" + k, 0.2, k * 0.41) * 0.5 + 0.5) * SIZE * 1.4 - SIZE * 0.8;
      const x2 = x + Math.sin(k * 12.9898) * 6;
      const z2 = z + Math.cos(k * 78.233) * 6;
      arr.push(new THREE.Vector3(x2, heightAt(x2, z2, seed, amp) + 0.06, z2));
    }
    return arr;
  }, [points?.count, seed, amp]);
  const ptsMesh = useMemo(() => {
    if (!pts) return null;
    const im = new THREE.InstancedMesh(new THREE.SphereGeometry(0.045, 6, 6), new THREE.MeshBasicMaterial({ color: th.accent, toneMapped: false }), pts.length);
    const m = new THREE.Matrix4();
    pts.forEach((p, i) => im.setMatrixAt(i, m.makeTranslation(p.x, p.y, p.z)));
    im.instanceMatrix.needsUpdate = true;
    return im;
  }, [pts, th.accent]);
  if (ptsMesh && points) {
    const s = points.at !== undefined ? at(points.at) : 0;
    ptsMesh.count = Math.floor(pts!.length * E.out(clamp01((f - s) / ((points.dur ?? 2.5) * fps))));
  }
  const camera = makeCamera(c);
  return (
    <AbsoluteFill>
      <Stage3D cam={c} lights="none" env={0} shadows={false} fog={undefined}>
        {sky ? <SkyDome top={L.sky[1]} bottom={L.sky[0]} /> : null}
        <mesh geometry={geo} material={mat} />
        {ptsMesh ? <primitive object={ptsMesh} /> : null}
      </Stage3D>
      {pins.map((p, i) => {
        const s = p.at !== undefined ? at(p.at) : 0;
        if (f < s) return null;
        const y = heightAt(p.x, p.z, seed, amp);
        const [sx, sy] = project(camera, new THREE.Vector3(p.x, y, p.z));
        const a = E.out(clamp01((f - s) / 12));
        const ring = ((f - s) % 45) / 45;
        return (
          <div key={i} style={{ position: "absolute", left: sx, top: sy, opacity: a }}>
            <div style={{ position: "absolute", left: -10, top: -10, width: 20, height: 20, borderRadius: 10, background: th.accent, boxShadow: `0 0 20px ${th.accent}` }} />
            <div style={{ position: "absolute", left: -40 * (0.4 + ring), top: -40 * (0.4 + ring), width: 80 * (0.4 + ring), height: 80 * (0.4 + ring), borderRadius: "50%", border: `3px solid ${th.accent}`, opacity: 1 - ring }} />
            {p.label ? (
              <div style={{ position: "absolute", left: 24, top: -56, font: `600 30px ${th.fontMono}`, color: "#fff", background: "rgba(10,12,20,0.6)", padding: "8px 14px", borderRadius: 10, whiteSpace: "nowrap" }}>{p.label}</div>
            ) : null}
          </div>
        );
      })}
    </AbsoluteFill>
  );
};
