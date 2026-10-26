import { useThree } from "@react-three/fiber";
import { ThreeCanvas } from "@remotion/three";
import React, { useLayoutEffect, useMemo } from "react";
import * as THREE from "three";
import { RoomEnvironment } from "three/examples/jsm/environments/RoomEnvironment.js";
import { H, W } from "../core/layout";
import { E, clamp01, lerp } from "../core/motion";

export type V3 = [number, number, number];
export type CamKey = { t: number; pos: V3; target: V3; fov?: number; ease?: string };
export type Cam = { pos: V3; target: V3; fov: number; roll?: number };

const EASES: Record<string, (t: number) => number> = { inOut: E.inOut, out: E.out, in: E.in, linear: (t) => t, outExpo: E.outExpo };

/** Interpolate camera keyframes (t in seconds, relative to the block start) */
export const camAt = (keys: CamKey[], tSec: number): Cam => {
  if (!keys.length) return { pos: [0, 0, 10], target: [0, 0, 0], fov: 35 };
  if (tSec <= keys[0].t) return { pos: keys[0].pos, target: keys[0].target, fov: keys[0].fov ?? 35 };
  for (let i = 0; i < keys.length - 1; i++) {
    const a = keys[i];
    const b = keys[i + 1];
    if (tSec <= b.t) {
      const p = (EASES[b.ease ?? "inOut"] ?? E.inOut)(clamp01((tSec - a.t) / Math.max(1e-3, b.t - a.t)));
      return {
        pos: [lerp(a.pos[0], b.pos[0], p), lerp(a.pos[1], b.pos[1], p), lerp(a.pos[2], b.pos[2], p)],
        target: [lerp(a.target[0], b.target[0], p), lerp(a.target[1], b.target[1], p), lerp(a.target[2], b.target[2], p)],
        fov: lerp(a.fov ?? 35, b.fov ?? 35, p),
      };
    }
  }
  const l = keys[keys.length - 1];
  return { pos: l.pos, target: l.target, fov: l.fov ?? 35 };
};

/** First-person camera on a head (no hands in frame): eye height comes from the keys, the head adds breathing,
 *  a slow look-around and — when the keys move the eye — a walking bob, sway and roll. fov: wide, like a head-cam. */
export const FPV_FOV = 70;
export const headCam = (keys: CamKey[], tSec: number, o: { fov?: number; amp?: number } = {}): Cam => {
  const c = camAt(keys, tSec);
  const a = camAt(keys, tSec - 0.1);
  const b = camAt(keys, tSec + 0.1);
  const speed = Math.hypot(b.pos[0] - a.pos[0], b.pos[2] - a.pos[2]) / 0.2; // m/s on the floor
  const amp = o.amp ?? 1;
  const walk = clamp01(speed / 0.45) * amp;
  const step = tSec * Math.PI * 2 * 1.8; // ~1.8 steps per second
  const fwd = new THREE.Vector3(c.target[0] - c.pos[0], 0, c.target[2] - c.pos[2]);
  if (fwd.lengthSq() < 1e-6) fwd.set(0, 0, -1);
  fwd.normalize();
  const right = new THREE.Vector3(-fwd.z, 0, fwd.x);
  const dist = Math.hypot(c.target[0] - c.pos[0], c.target[1] - c.pos[1], c.target[2] - c.pos[2]);
  const dy = Math.sin(tSec * 1.7) * 0.005 * amp + (Math.abs(Math.sin(step / 2)) - 0.64) * 0.03 * walk;
  const sway = Math.sin(step / 2) * 0.014 * walk;
  // look drift in radians (yaw, pitch): slow, small, never a shake
  const yaw = (Math.sin(tSec * 0.53 + 0.7) * 0.03 + Math.sin(tSec * 1.31) * 0.01) * amp;
  const pitch = (Math.sin(tSec * 0.71 + 2.1) * 0.02 + Math.sin(step) * 0.006 * walk) * amp;
  const pos: V3 = [c.pos[0] + right.x * sway, c.pos[1] + dy, c.pos[2] + right.z * sway];
  const target: V3 = [c.target[0] + right.x * (sway + yaw * dist), c.target[1] + dy + pitch * dist, c.target[2] + right.z * (sway + yaw * dist)];
  return { pos, target, fov: o.fov ?? c.fov, roll: Math.sin(step / 2) * 0.009 * walk + Math.sin(tSec * 0.6) * 0.004 * amp };
};

/** Same camera as the WebGL one, for projecting 3D points to screen pixels in the DOM */
export const makeCamera = (c: Cam, w = W, h = H) => {
  const cam = new THREE.PerspectiveCamera(c.fov, w / h, 0.05, 500);
  cam.position.set(...c.pos);
  cam.lookAt(new THREE.Vector3(...c.target));
  if (c.roll) cam.rotateZ(c.roll);
  cam.updateMatrixWorld(true);
  cam.updateProjectionMatrix();
  return cam;
};

export const project = (cam: THREE.Camera, p: THREE.Vector3, w = W, h = H): [number, number, number] => {
  const v = p.clone().project(cam);
  return [(v.x * 0.5 + 0.5) * w, (-v.y * 0.5 + 0.5) * h, v.z];
};

/** Solve the 3x3 homography mapping rect (0,0)-(w,h) to quad q (tl,tr,br,bl) and return a CSS matrix3d */
export const quadToMatrix3d = (w: number, h: number, q: [number, number][]): string => {
  const src = [[0, 0], [w, 0], [w, h], [0, h]];
  const A: number[][] = [];
  const b: number[] = [];
  for (let i = 0; i < 4; i++) {
    const [x, y] = src[i];
    const [u, v] = q[i];
    A.push([x, y, 1, 0, 0, 0, -u * x, -u * y]);
    b.push(u);
    A.push([0, 0, 0, x, y, 1, -v * x, -v * y]);
    b.push(v);
  }
  // gaussian elimination
  const n = 8;
  for (let c = 0; c < n; c++) {
    let piv = c;
    for (let r = c + 1; r < n; r++) if (Math.abs(A[r][c]) > Math.abs(A[piv][c])) piv = r;
    [A[c], A[piv]] = [A[piv], A[c]];
    [b[c], b[piv]] = [b[piv], b[c]];
    const d = A[c][c] || 1e-12;
    for (let r = 0; r < n; r++) {
      if (r === c) continue;
      const f = A[r][c] / d;
      for (let k = c; k < n; k++) A[r][k] -= f * A[c][k];
      b[r] -= f * b[c];
    }
  }
  const hh = b.map((v, i) => v / A[i][i]);
  const [a, bb, c, d, e, f, g, hv] = hh;
  // matrix3d is column-major
  return `matrix3d(${a},${d},0,${g},${bb},${e},0,${hv},0,0,1,0,${c},${f},0,1)`;
};

// ------------------------------------------------------------------ scene plumbing
const CamRig: React.FC<{ cam: Cam }> = ({ cam }) => {
  const camera = useThree((s) => s.camera) as THREE.PerspectiveCamera;
  camera.position.set(...cam.pos);
  camera.fov = cam.fov;
  camera.near = 0.05;
  camera.far = 500;
  camera.lookAt(new THREE.Vector3(...cam.target));
  if (cam.roll) camera.rotateZ(cam.roll);
  camera.updateProjectionMatrix();
  camera.updateMatrixWorld(true);
  return null;
};

const Env: React.FC<{ intensity: number }> = ({ intensity }) => {
  const { gl, scene } = useThree();
  const tex = useMemo(() => {
    const pm = new THREE.PMREMGenerator(gl);
    const t = pm.fromScene(new RoomEnvironment(), 0.035).texture;
    pm.dispose();
    return t;
  }, [gl]);
  useLayoutEffect(() => {
    scene.environment = tex;
    scene.environmentIntensity = intensity;
  }, [scene, tex, intensity]);
  return null;
};

export type LightRig = "studio" | "soft" | "night" | "sunset" | "none";

export const Lights: React.FC<{ rig: LightRig; shadow?: boolean; keyPos?: V3; color?: string }> = ({ rig, shadow = true, keyPos, color }) => {
  if (rig === "none") return null;
  const key = keyPos ?? (rig === "sunset" ? [-6, 3, 4] : [4, 8, 6]);
  const kc = color ?? (rig === "sunset" ? "#FFB27A" : rig === "night" ? "#9DB8FF" : "#FFFFFF");
  const ki = rig === "night" ? 1.2 : rig === "soft" ? 1.6 : 2.4;
  return (
    <>
      <ambientLight intensity={rig === "night" ? 0.15 : 0.35} />
      <directionalLight
        position={key}
        intensity={ki}
        color={kc}
        castShadow={shadow}
        shadow-mapSize-width={2048}
        shadow-mapSize-height={2048}
        shadow-camera-left={-8}
        shadow-camera-right={8}
        shadow-camera-top={8}
        shadow-camera-bottom={-8}
        shadow-bias={-0.0004}
        shadow-radius={6}
      />
      <directionalLight position={[-5, 2, -4]} intensity={rig === "night" ? 0.8 : 0.6} color={rig === "night" ? "#4F7BFF" : "#DDE6FF"} />
      <pointLight position={[0, 3, -6]} intensity={rig === "studio" ? 20 : 8} color={rig === "sunset" ? "#FF8A4A" : "#AFC6FF"} distance={30} />
    </>
  );
};

/** Soft fake contact shadow: radial gradient on a ground plane (always looks good, zero cost) */
export const ContactShadow: React.FC<{ y?: number; size?: number; opacity?: number; stretch?: number }> = ({ y = 0, size = 6, opacity = 0.55, stretch = 1 }) => {
  const tex = useMemo(() => {
    const c = document.createElement("canvas");
    c.width = c.height = 256;
    const g = c.getContext("2d")!;
    const grd = g.createRadialGradient(128, 128, 0, 128, 128, 128);
    grd.addColorStop(0, "rgba(0,0,0,1)");
    grd.addColorStop(0.35, "rgba(0,0,0,0.55)");
    grd.addColorStop(1, "rgba(0,0,0,0)");
    g.fillStyle = grd;
    g.fillRect(0, 0, 256, 256);
    const t = new THREE.CanvasTexture(c);
    t.colorSpace = THREE.SRGBColorSpace;
    return t;
  }, []);
  return (
    <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, y + 0.002, 0]} scale={[size * stretch, size, 1]}>
      <planeGeometry args={[1, 1]} />
      <meshBasicMaterial map={tex} transparent opacity={opacity} depthWrite={false} />
    </mesh>
  );
};

/** round soft sprite for THREE.PointsMaterial `map` (without one, points render as squares): stars, city lights, glow */
let dotTex: THREE.Texture | null = null;
export const dotTexture = () => {
  if (!dotTex) {
    const c = document.createElement("canvas");
    c.width = c.height = 64;
    const g = c.getContext("2d")!;
    const grd = g.createRadialGradient(32, 32, 0, 32, 32, 32);
    grd.addColorStop(0, "rgba(255,255,255,1)");
    grd.addColorStop(0.3, "rgba(255,255,255,0.75)");
    grd.addColorStop(0.65, "rgba(255,255,255,0.18)");
    grd.addColorStop(1, "rgba(255,255,255,0)");
    g.fillStyle = grd;
    g.fillRect(0, 0, 64, 64);
    dotTex = new THREE.CanvasTexture(c);
  }
  return dotTex;
};

export const ShadowGround: React.FC<{ y?: number; opacity?: number }> = ({ y = 0, opacity = 0.28 }) => (
  <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, y, 0]} receiveShadow>
    <planeGeometry args={[60, 60]} />
    <shadowMaterial transparent opacity={opacity} />
  </mesh>
);

export const Stage3D: React.FC<{
  cam: Cam;
  children: React.ReactNode;
  env?: number; // environment intensity (0 = off)
  lights?: LightRig;
  shadows?: boolean;
  fog?: { color: string; near: number; far: number };
  exposure?: number;
  style?: React.CSSProperties;
  /** render at a fraction of the frame size (e.g. 0.25 for a PS1-like 270 x 480 buffer) */
  dpr?: number;
  /** upscale the low-res buffer with hard pixels instead of smoothing */
  pixelated?: boolean;
}> = ({ cam, children, env = 1, lights = "studio", shadows = true, fog, exposure = 1, style, dpr, pixelated }) => (
  <ThreeCanvas
    width={W}
    height={H}
    style={{ position: "absolute", inset: 0, ...(pixelated ? { imageRendering: "pixelated" } : {}), ...style }}
    {...(dpr ? { dpr } : {})}
    shadows={shadows ? { type: pixelated ? THREE.PCFShadowMap : THREE.PCFSoftShadowMap } : false}
    // logarithmic depth: thin coplanar details (screens, windows, decals) never z-fight, even 100 m away
    gl={{ antialias: !pixelated, alpha: true, toneMapping: THREE.ACESFilmicToneMapping, toneMappingExposure: exposure, preserveDrawingBuffer: true, logarithmicDepthBuffer: true }}
    camera={{ fov: cam.fov, position: cam.pos, near: 0.05, far: 500 }}
  >
    <CamRig cam={cam} />
    {env > 0 ? <Env intensity={env} /> : null}
    {fog ? <fog attach="fog" args={[fog.color, fog.near, fog.far]} /> : null}
    <Lights rig={lights} shadow={shadows} />
    {children}
  </ThreeCanvas>
);

/** Rounded-rect canvas texture helper (for 2D details on 3D objects) */
export const canvasTexture = (w: number, h: number, draw: (g: CanvasRenderingContext2D) => void) => {
  const c = document.createElement("canvas");
  c.width = w;
  c.height = h;
  draw(c.getContext("2d")!);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  t.anisotropy = 8;
  return t;
};
