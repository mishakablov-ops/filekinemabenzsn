import React, { useMemo } from "react";
import { AbsoluteFill, Img } from "remotion";
import * as THREE from "three";
import { RoundedBoxGeometry } from "three/examples/jsm/geometries/RoundedBoxGeometry.js";
import { REGISTRY } from "../blocks";
import { asset } from "../blocks/bg";
import { useBlockTime, useTheme } from "../core/context";
import { E, clamp01, lerp, wiggle } from "../core/motion";
import { camAt, canvasTexture, ContactShadow, makeCamera, project, quadToMatrix3d, ShadowGround, Stage3D, type Cam, type CamKey, type LightRig, type V3 } from "./core";
import { qaProxy } from "./model";

export type NestedBlock = { block: string; props?: Record<string, unknown> };

/** Render a registry block as screen content (same timeline as the parent block). */
export const Nested: React.FC<{ spec?: NestedBlock; src?: string; w: number; h: number; bg?: string }> = ({ spec, src, w, h, bg = "#000" }) => {
  if (src) return <Img src={asset(src)} style={{ width: w, height: h, objectFit: "cover", display: "block" }} />;
  if (!spec) return <div style={{ width: w, height: h, background: bg }} />;
  const def = REGISTRY[spec.block];
  if (!def) return <div style={{ width: w, height: h, background: "#300", color: "#fff", fontSize: 28 }}>unknown {spec.block}</div>;
  return (
    <div style={{ width: w, height: h, position: "relative", overflow: "hidden", background: bg, display: "flex", alignItems: "stretch", justifyContent: "stretch" }}>
      <def.C {...(spec.props ?? {})} />
    </div>
  );
};

// ------------------------------------------------------------------ geometry helpers
export const roundedRectShape = (w: number, h: number, r: number) => {
  const s = new THREE.Shape();
  const x = -w / 2;
  const y = -h / 2;
  s.moveTo(x + r, y);
  s.lineTo(x + w - r, y);
  s.quadraticCurveTo(x + w, y, x + w, y + r);
  s.lineTo(x + w, y + h - r);
  s.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
  s.lineTo(x + r, y + h);
  s.quadraticCurveTo(x, y + h, x, y + h - r);
  s.lineTo(x, y + r);
  s.quadraticCurveTo(x, y, x + r, y);
  return s;
};

const slab = (w: number, h: number, depth: number, r: number, bevel: number) => {
  const g = new THREE.ExtrudeGeometry(roundedRectShape(w - bevel * 2, h - bevel * 2, Math.max(0.001, r - bevel)), {
    depth,
    bevelEnabled: true,
    bevelThickness: bevel,
    bevelSize: bevel,
    bevelSegments: 8,
    curveSegments: 24,
  });
  g.translate(0, 0, -depth / 2);
  g.computeVertexNormals();
  return g;
};

const METALS: Record<string, { color: string; rough: number }> = {
  silver: { color: "#D9DBDF", rough: 0.32 },
  space: { color: "#55585E", rough: 0.36 },
  midnight: { color: "#2A3240", rough: 0.34 },
  black: { color: "#1E1F22", rough: 0.3 },
  titanium: { color: "#9A958E", rough: 0.38 },
  white: { color: "#EDEDEF", rough: 0.45 },
  gold: { color: "#E3CFA8", rough: 0.3 },
};
const metal = (c: string) => {
  const m = METALS[c] ?? METALS.space;
  return new THREE.MeshPhysicalMaterial({ color: m.color, metalness: 0.92, roughness: m.rough, clearcoat: 0.25, clearcoatRoughness: 0.4 });
};

// ------------------------------------------------------------------ LAPTOP
const LAP = { w: 3.1, d: 2.15, baseH: 0.09, lidH: 2.06, lidT: 0.045, dispW: 2.84, dispH: 1.775, dispY: 1.05 };

const keyboardTex = () =>
  canvasTexture(1024, 380, (g) => {
    g.fillStyle = "#2a2b2f";
    g.fillRect(0, 0, 1024, 380);
    const rows = [14, 14, 13, 12, 11];
    const kw = 1024 / 14.6;
    rows.forEach((n, r) => {
      const y = 12 + r * 62;
      let x = 14 + (14 - n) * kw * 0.5;
      for (let i = 0; i < n; i++) {
        g.fillStyle = "#0d0d0f";
        const w = kw - 8;
        g.beginPath();
        g.roundRect(x, y, w, 52, 8);
        g.fill();
        x += kw;
      }
    });
    g.fillStyle = "#0d0d0f";
    g.beginPath();
    g.roundRect(1024 * 0.3, 12 + 5 * 62 - 6, 1024 * 0.4, 52, 8);
    g.fill();
  });

export type LaptopPose = { lid: number; yaw: number; pitch: number; y: number; x: number; z: number };

const lidMatrix = (pose: LaptopPose) => {
  const group = new THREE.Object3D();
  group.position.set(pose.x, pose.y, pose.z);
  group.rotation.set(pose.pitch, pose.yaw, 0);
  const pivot = new THREE.Object3D();
  pivot.position.set(0, LAP.baseH, -LAP.d / 2 + 0.06);
  pivot.rotation.set(-pose.lid, 0, 0); // lid: 0 = upright, +90° = closed
  group.add(pivot);
  group.updateMatrixWorld(true);
  return pivot.matrixWorld.clone();
};

const LaptopMesh: React.FC<{ pose: LaptopPose; color: string }> = ({ pose, color }) => {
  const mat = useMemo(() => metal(color), [color]);
  const base = useMemo(() => new RoundedBoxGeometry(LAP.w, LAP.baseH, LAP.d, 4, 0.04), []);
  const lid = useMemo(() => slab(LAP.w, LAP.lidH, LAP.lidT, 0.09, 0.012), []);
  const kb = useMemo(() => keyboardTex(), []);
  return (
    <group position={[pose.x, pose.y, pose.z]} rotation={[pose.pitch, pose.yaw, 0]}>
      <mesh geometry={base} material={mat} position={[0, LAP.baseH / 2, 0]} castShadow receiveShadow />
      {/* keyboard + trackpad */}
      <mesh position={[0, LAP.baseH + 0.001, -0.33]} rotation={[-Math.PI / 2, 0, 0]}>
        <planeGeometry args={[2.62, 0.97]} />
        <meshStandardMaterial map={kb} roughness={0.75} metalness={0.1} />
      </mesh>
      <mesh position={[0, LAP.baseH + 0.001, 0.58]} rotation={[-Math.PI / 2, 0, 0]}>
        <planeGeometry args={[1.25, 0.74]} />
        <meshPhysicalMaterial color={METALS[color]?.color ?? "#555"} metalness={0.6} roughness={0.22} clearcoat={0.6} />
      </mesh>
      {/* hinge */}
      <mesh position={[0, LAP.baseH, -LAP.d / 2 + 0.06]} rotation={[0, 0, Math.PI / 2]}>
        <cylinderGeometry args={[0.035, 0.035, LAP.w * 0.82, 24]} />
        <meshStandardMaterial color="#111" roughness={0.5} metalness={0.6} />
      </mesh>
      <group position={[0, LAP.baseH, -LAP.d / 2 + 0.06]} rotation={[-pose.lid, 0, 0]}>
        <mesh geometry={lid} material={mat} position={[0, LAP.lidH / 2, -LAP.lidT / 2 - 0.012]} castShadow />
        {/* black glass bezel */}
        <mesh position={[0, LAP.lidH / 2, 0.0015]}>
          <shapeGeometry args={[roundedRectShape(LAP.w - 0.04, LAP.lidH - 0.04, 0.08)]} />
          <meshPhysicalMaterial color="#050506" roughness={0.08} metalness={0} clearcoat={1} clearcoatRoughness={0.05} />
        </mesh>
      </group>
    </group>
  );
};

// ------------------------------------------------------------------ PHONE
const PH = { w: 0.76, h: 1.56, t: 0.07, r: 0.125, glassInset: 0.012, dispInset: 0.022 };

const PhoneMesh: React.FC<{ color: string; pos: V3; rot: V3; scale?: number }> = ({ color, pos, rot, scale = 1 }) => {
  const mat = useMemo(() => metal(color), [color]);
  const body = useMemo(() => slab(PH.w, PH.h, PH.t, PH.r, 0.016), []);
  const glassShape = useMemo(() => roundedRectShape(PH.w - PH.glassInset * 2, PH.h - PH.glassInset * 2, PH.r - PH.glassInset), []);
  const bump = useMemo(() => slab(0.34, 0.36, 0.012, 0.07, 0.006), []);
  const glassMat = useMemo(() => new THREE.MeshPhysicalMaterial({ color: "#030304", roughness: 0.06, metalness: 0, clearcoat: 1, clearcoatRoughness: 0.03 }), []);
  const backMat = useMemo(() => new THREE.MeshPhysicalMaterial({ color: METALS[color]?.color ?? "#555", roughness: 0.55, metalness: 0.3, clearcoat: 0.4 }), [color]);
  const z = PH.t / 2 + 0.017;
  return (
    <group position={pos} rotation={rot} scale={scale}>
      <mesh geometry={body} material={mat} castShadow />
      <mesh position={[0, 0, z]} material={glassMat}>
        <shapeGeometry args={[glassShape]} />
      </mesh>
      <mesh position={[0, 0, -z]} rotation={[0, Math.PI, 0]} material={backMat}>
        <shapeGeometry args={[glassShape]} />
      </mesh>
      {/* camera bump + lenses on the back */}
      <mesh geometry={bump} material={backMat} position={[-PH.w / 2 + 0.22, PH.h / 2 - 0.24, -z - 0.006]} />
      {[[-0.07, 0.07], [-0.07, -0.08], [0.07, 0]].map(([dx, dy], i) => (
        <mesh key={i} position={[-PH.w / 2 + 0.22 + dx, PH.h / 2 - 0.24 + dy, -z - 0.018]} rotation={[Math.PI / 2, 0, 0]}>
          <cylinderGeometry args={[0.052, 0.056, 0.02, 32]} />
          <meshPhysicalMaterial color="#0b0b0d" roughness={0.1} metalness={0.5} clearcoat={1} />
        </mesh>
      ))}
      {/* side buttons */}
      <mesh position={[PH.w / 2 + 0.006, 0.25, 0]}>
        <boxGeometry args={[0.012, 0.2, 0.03]} />
        <primitive object={mat} attach="material" />
      </mesh>
      <mesh position={[-PH.w / 2 - 0.006, 0.32, 0]}>
        <boxGeometry args={[0.012, 0.12, 0.03]} />
        <primitive object={mat} attach="material" />
      </mesh>
      <mesh position={[-PH.w / 2 - 0.006, 0.12, 0]}>
        <boxGeometry args={[0.012, 0.12, 0.03]} />
        <primitive object={mat} attach="material" />
      </mesh>
    </group>
  );
};

const phoneDisplayCorners = (pos: V3, rot: V3, scale = 1) => {
  const o = new THREE.Object3D();
  o.position.set(...pos);
  o.rotation.set(...rot);
  o.scale.setScalar(scale);
  o.updateMatrixWorld(true);
  const w = PH.w / 2 - PH.dispInset;
  const h = PH.h / 2 - PH.dispInset;
  const z = PH.t / 2 + 0.018;
  const pts = [new THREE.Vector3(-w, h, z), new THREE.Vector3(w, h, z), new THREE.Vector3(w, -h, z), new THREE.Vector3(-w, -h, z)].map((p) => p.applyMatrix4(o.matrixWorld));
  const n = new THREE.Vector3(0, 0, 1).transformDirection(o.matrixWorld);
  const c = new THREE.Vector3(0, 0, z).applyMatrix4(o.matrixWorld);
  return { pts, n, c };
};

// ------------------------------------------------------------------ HTML screen overlay
const ScreenOverlay: React.FC<{
  cam: Cam; pts: THREE.Vector3[]; normal: THREE.Vector3; center: THREE.Vector3; pxW: number; pxH: number; radius: number;
  content: React.ReactNode; glare?: number; island?: boolean; notch?: boolean; brightness?: number;
}> = ({ cam, pts, normal, center, pxW, pxH, radius, content, glare = 0.18, island, notch, brightness = 1 }) => {
  const camera = makeCamera(cam);
  const toCam = new THREE.Vector3(...cam.pos).sub(center).normalize();
  const facing = normal.dot(toCam);
  if (facing < 0.02) return null;
  const q = pts.map((p) => project(camera, p)).map(([x, y]) => [x, y] as [number, number]);
  const m = quadToMatrix3d(pxW, pxH, q);
  return (
    <div data-qa="layer" data-qa-id="3d-screen" data-qa-cat="screen" data-qa-bleed="1" style={{ position: "absolute", left: 0, top: 0, width: pxW, height: pxH, transformOrigin: "0 0", transform: m, borderRadius: radius, overflow: "hidden", background: "#000", filter: brightness !== 1 ? `brightness(${brightness})` : undefined }}>
      {content}
      {island ? <div style={{ position: "absolute", left: pxW / 2 - 62, top: 11, width: 124, height: 36, borderRadius: 20, background: "#000" }} /> : null}
      {notch ? <div style={{ position: "absolute", left: pxW / 2 - 90, top: 0, width: 180, height: 30, borderRadius: "0 0 14px 14px", background: "#000" }} /> : null}
      <div style={{ position: "absolute", inset: 0, background: `linear-gradient(${115 + (cam.pos[0] * 6)}deg, rgba(255,255,255,${glare}) 0%, rgba(255,255,255,0) 38%, rgba(255,255,255,0) 70%, rgba(255,255,255,${glare * 0.4}) 100%)`, pointerEvents: "none", mixBlendMode: "screen" }} />
      <div style={{ position: "absolute", inset: 0, opacity: clamp01((0.35 - facing) * 3) * 0.6, background: "#000" }} />
    </div>
  );
};

// ------------------------------------------------------------------ camera presets
// portrait frame: horizontal FOV is narrow, so the laptop (3.1 wide) needs ~12 units of distance at fov 30
const LAPTOP_CAMS: Record<string, CamKey[]> = {
  hero: [
    { t: 0, pos: [0.0, 4.4, 12.6], target: [0, 0.95, 0], fov: 30 },
    { t: 7, pos: [1.1, 3.9, 11.4], target: [0, 0.95, 0], fov: 30 },
  ],
  orbit: [
    { t: 0, pos: [-7.6, 4.0, 9.6], target: [0, 0.9, 0], fov: 30 },
    { t: 7, pos: [7.6, 3.6, 9.6], target: [0, 0.9, 0], fov: 30 },
  ],
  lowAngle: [
    { t: 0, pos: [-2.6, 0.9, 11.8], target: [0, 1.1, 0], fov: 30 },
    { t: 7, pos: [1.8, 1.2, 11.0], target: [0, 1.1, 0], fov: 30 },
  ],
  zoomScreen: [
    { t: 0, pos: [0.0, 4.2, 12.4], target: [0, 0.95, 0], fov: 30 },
    { t: 1.0, pos: [0.0, 3.6, 11.2], target: [0, 1.0, -0.3], fov: 32 },
    { t: 2.8, pos: [0.0, 1.35, 5.1], target: [0, 1.06, -0.95], fov: 45, ease: "inOut" },
  ],
  top: [
    { t: 0, pos: [0.0, 12.5, 5.0], target: [0, 0.3, 0.2], fov: 30 },
    { t: 7, pos: [0.0, 11.4, 4.2], target: [0, 0.3, 0.2], fov: 30 },
  ],
  side: [
    { t: 0, pos: [-10.5, 3.2, 5.6], target: [0, 0.9, 0], fov: 30 },
    { t: 7, pos: [-9.0, 3.4, 7.2], target: [0, 0.9, 0], fov: 30 },
  ],
  close: [
    { t: 0, pos: [0.0, 2.2, 7.0], target: [0, 1.0, -0.6], fov: 34 },
    { t: 7, pos: [0.5, 2.0, 6.2], target: [0, 1.0, -0.6], fov: 34 },
  ],
};

const PHONE_CAMS: Record<string, CamKey[]> = {
  hero: [
    { t: 0, pos: [0, 0.05, 4.6], target: [0, 0, 0], fov: 30 },
    { t: 6, pos: [0.25, 0.1, 4.2], target: [0, 0, 0], fov: 30 },
  ],
  close: [
    { t: 0, pos: [0, 0.1, 3.4], target: [0, 0.05, 0], fov: 30 },
    { t: 6, pos: [0, 0.1, 3.0], target: [0, 0.05, 0], fov: 30 },
  ],
  low: [
    { t: 0, pos: [0.6, -1.2, 4.0], target: [0, 0.1, 0], fov: 30 },
    { t: 6, pos: [-0.4, -1.0, 3.8], target: [0, 0.1, 0], fov: 30 },
  ],
  wide: [
    { t: 0, pos: [0, 0.2, 6.4], target: [0, 0, 0], fov: 30 },
    { t: 6, pos: [0, 0.2, 5.8], target: [0, 0, 0], fov: 30 },
  ],
};

const camFrom = (preset: string | CamKey[] | undefined, presets: Record<string, CamKey[]>, def: string) =>
  Array.isArray(preset) ? preset : presets[preset ?? def] ?? presets[def];

// ------------------------------------------------------------------ Laptop3D block
const Laptop3D: React.FC<{
  screen?: NestedBlock; src?: string; cam?: string | CamKey[]; color?: string; open?: boolean; openAt?: unknown; openDur?: number;
  lid?: number; yaw?: number; spin?: number; lights?: LightRig; env?: number; float?: boolean; screenW?: number; glare?: number; shadow?: number;
}> = ({ screen, src, cam, color = "space", open = false, openAt, openDur = 1.3, lid = 12, yaw = 0, spin = 0, lights = "studio", env = 1, float = false, screenW = 1440, glare = 0.16, shadow = 0.5 }) => {
  const { f, fps, at } = useBlockTime();
  const t = f / fps;
  const keys = camFrom(cam, LAPTOP_CAMS, "hero");
  const c = camAt(keys, t);
  const oa = openAt !== undefined ? at(openAt) / fps : 0.15;
  const openP = open ? E.inOut(clamp01((t - oa) / openDur)) : 1;
  const lidRad = THREE.MathUtils.degToRad(lerp(88, -lid, openP));
  const pose: LaptopPose = { lid: lidRad, yaw: THREE.MathUtils.degToRad(yaw + spin * t), pitch: 0, x: 0, y: float ? wiggle(f, 0.02, 2) * 0.05 : 0, z: 0 };
  const mw = lidMatrix(pose);
  const hw = LAP.dispW / 2;
  const pts = [
    new THREE.Vector3(-hw, LAP.dispY + LAP.dispH / 2, 0.003),
    new THREE.Vector3(hw, LAP.dispY + LAP.dispH / 2, 0.003),
    new THREE.Vector3(hw, LAP.dispY - LAP.dispH / 2, 0.003),
    new THREE.Vector3(-hw, LAP.dispY - LAP.dispH / 2, 0.003),
  ].map((p) => p.applyMatrix4(mw));
  const n = new THREE.Vector3(0, 0, 1).transformDirection(mw);
  const center = new THREE.Vector3(0, LAP.dispY, 0).applyMatrix4(mw);
  const pxW = screenW;
  const pxH = Math.round((screenW * LAP.dispH) / LAP.dispW);
  const screenOn = clamp01((openP - 0.55) / 0.3);
  const proxyObj = new THREE.Object3D();
  {
    const g = new THREE.Mesh(new THREE.BoxGeometry(LAP.w, LAP.baseH, LAP.d));
    g.position.set(pose.x, pose.y + LAP.baseH / 2, pose.z);
    g.rotation.set(pose.pitch, pose.yaw, 0);
    proxyObj.add(g);
    const top = new THREE.Mesh(new THREE.BoxGeometry(0.01, 0.01, 0.01));
    top.position.copy(new THREE.Vector3(0, LAP.lidH, 0).applyMatrix4(mw));
    proxyObj.add(top);
    proxyObj.updateMatrixWorld(true);
  }
  return (
    <AbsoluteFill>
      {qaProxy(proxyObj, c)}
      <Stage3D cam={c} lights={lights} env={env}>
        <LaptopMesh pose={pose} color={color} />
        <ContactShadow y={0} size={5.2} stretch={1.1} opacity={shadow} />
        <ShadowGround y={0} opacity={0.22} />
      </Stage3D>
      {screenOn > 0 ? (
        <AbsoluteFill style={{ opacity: screenOn }}>
          <ScreenOverlay cam={c} pts={pts} normal={n} center={center} pxW={pxW} pxH={pxH} radius={pxW * 0.012} notch glare={glare} content={<Nested spec={screen} src={src} w={pxW} h={pxH} />} />
        </AbsoluteFill>
      ) : null}
    </AbsoluteFill>
  );
};

// ------------------------------------------------------------------ Phone3D block (1–3 phones)
type PhoneSpec = { screen?: NestedBlock; src?: string; pos?: V3; rot?: V3; color?: string };

const Phone3D: React.FC<{
  screen?: NestedBlock; src?: string; phones?: PhoneSpec[]; cam?: string | CamKey[]; color?: string; turn?: [number, number]; tilt?: number;
  float?: boolean; lights?: LightRig; env?: number; enterSpin?: boolean; glare?: number; shadowY?: number;
}> = ({ screen, src, phones, cam, color = "titanium", turn = [-18, 8], tilt = 4, float = true, lights = "studio", env = 1, enterSpin = false, glare = 0.14, shadowY }) => {
  const { f, fps, dur } = useBlockTime();
  const t = f / fps;
  const keys = camFrom(cam, PHONE_CAMS, phones && phones.length > 1 ? "wide" : "hero");
  const c = camAt(keys, t);
  const T = dur / fps;
  const list: PhoneSpec[] = phones ?? [{ screen, src, pos: [0, 0, 0], rot: [0, 0, 0], color }];
  const spinP = enterSpin ? E.outExpo(clamp01(t / 1.4)) : 1;
  const items = list.map((p, i) => {
    const bob = float ? wiggle(f + i * 40, 0.02, i + 1) * 0.04 : 0;
    const yawDeg = lerp(turn[0], turn[1], E.inOut(clamp01(t / Math.max(1, T)))) + (p.rot?.[1] ?? 0) + (1 - spinP) * 180;
    const pos: V3 = [p.pos?.[0] ?? 0, (p.pos?.[1] ?? 0) + bob, p.pos?.[2] ?? 0];
    const rot: V3 = [THREE.MathUtils.degToRad(tilt + (p.rot?.[0] ?? 0)), THREE.MathUtils.degToRad(yawDeg), THREE.MathUtils.degToRad(p.rot?.[2] ?? 0)];
    return { p, pos, rot, ...phoneDisplayCorners(pos, rot) };
  });
  const pxW = 390;
  const pxH = Math.round((pxW * (PH.h - PH.dispInset * 2)) / (PH.w - PH.dispInset * 2));
  // draw far phones first
  const camV = new THREE.Vector3(...c.pos);
  const order = [...items].sort((a, b) => b.c.distanceTo(camV) - a.c.distanceTo(camV));
  const proxyObj = new THREE.Object3D();
  items.forEach((it) => {
    const g = new THREE.Mesh(new THREE.BoxGeometry(PH.w, PH.h, PH.t));
    g.position.set(...it.pos);
    g.rotation.set(...it.rot);
    proxyObj.add(g);
  });
  proxyObj.updateMatrixWorld(true);
  return (
    <AbsoluteFill>
      {qaProxy(proxyObj, c)}
      <Stage3D cam={c} lights={lights} env={env}>
        {items.map((it, i) => (
          <PhoneMesh key={i} color={it.p.color ?? color} pos={it.pos} rot={it.rot} />
        ))}
        {shadowY !== undefined ? <ContactShadow y={shadowY} size={2.4} opacity={0.4} /> : null}
      </Stage3D>
      {order.map((it, i) => (
        <ScreenOverlay key={i} cam={c} pts={it.pts} normal={it.n} center={it.c} pxW={pxW} pxH={pxH} radius={48} island glare={glare} content={<Nested spec={it.p.screen} src={it.p.src} w={pxW} h={pxH} bg="#fff" />} />
      ))}
    </AbsoluteFill>
  );
};

export { Laptop3D, Phone3D, LAP, PH };
