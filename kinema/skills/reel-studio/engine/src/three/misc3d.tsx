import React, { useMemo } from "react";
import { AbsoluteFill, random } from "remotion";
import * as THREE from "three";
import { useBlockTime, useTheme } from "../core/context";
import { E, SPR, clamp01, lerp, springAt } from "../core/motion";
import { camAt, ContactShadow, makeCamera, project, Stage3D, type CamKey } from "./core";
import { roundedRectShape, Nested, type NestedBlock } from "./devices";

// ------------------------------------------------------------------ Shapes3D: glossy hero objects
export const Shapes3D: React.FC<{ kind?: "blob" | "torus" | "rings" | "pills" | "cubes" | "knot"; color?: string; color2?: string; glass?: boolean; spin?: number; count?: number }> = ({
  kind = "blob", color, color2, glass = false, spin = 1, count = 7,
}) => {
  const { f, fps } = useBlockTime();
  const th = useTheme();
  const t = f / fps;
  const c1 = color ?? th.accent;
  const c2 = color2 ?? th.accent2;
  const mat = useMemo(
    () =>
      new THREE.MeshPhysicalMaterial({
        color: c1, roughness: glass ? 0.05 : 0.18, metalness: glass ? 0 : 0.15, clearcoat: 1, clearcoatRoughness: 0.08,
        iridescence: 0.7, iridescenceIOR: 1.3, transmission: glass ? 0.92 : 0, thickness: glass ? 1.2 : 0, ior: 1.45,
      }),
    [c1, glass],
  );
  const mat2 = useMemo(() => new THREE.MeshPhysicalMaterial({ color: c2, roughness: 0.2, metalness: 0.2, clearcoat: 1, iridescence: 0.5 }), [c2]);
  const blob = useMemo(() => new THREE.IcosahedronGeometry(1.25, 64), []);
  const base = useMemo(() => Float32Array.from(blob.attributes.position.array as Float32Array), [blob]);
  if (kind === "blob") {
    const pos = blob.attributes.position as THREE.BufferAttribute;
    for (let i = 0; i < pos.count; i++) {
      const x = base[i * 3];
      const y = base[i * 3 + 1];
      const z = base[i * 3 + 2];
      const n = Math.sin(x * 2.1 + t * 1.3) * Math.sin(y * 2.4 + t * 1.1) * Math.sin(z * 2.2 + t * 0.9);
      const s = 1 + n * 0.16;
      pos.setXYZ(i, x * s, y * s, z * s);
    }
    pos.needsUpdate = true;
    blob.computeVertexNormals();
  }
  const ent = clamp01(springAt(f, fps, 0, SPR.soft));
  const cam = { pos: [0, 0.3, 9.5] as [number, number, number], target: [0, 0, 0] as [number, number, number], fov: 32 };
  return (
    <AbsoluteFill>
      <Stage3D cam={cam} lights="studio" env={1.2} shadows={false}>
        <group rotation={[0.3 + t * 0.15 * spin, t * 0.35 * spin, 0]} scale={lerp(0.6, 1, ent)}>
          {kind === "blob" ? <mesh geometry={blob} material={mat} /> : null}
          {kind === "torus" ? (
            <mesh material={mat}>
              <torusGeometry args={[1.1, 0.45, 64, 160]} />
            </mesh>
          ) : null}
          {kind === "knot" ? (
            <mesh material={mat}>
              <torusKnotGeometry args={[0.9, 0.3, 300, 48]} />
            </mesh>
          ) : null}
          {kind === "rings"
            ? Array.from({ length: 4 }, (_, i) => (
                <mesh key={i} material={i % 2 ? mat2 : mat} rotation={[t * (0.4 + i * 0.2), i * 0.8, t * 0.3 * (i + 1)]}>
                  <torusGeometry args={[0.7 + i * 0.32, 0.07, 32, 128]} />
                </mesh>
              ))
            : null}
          {kind === "pills" || kind === "cubes"
            ? Array.from({ length: count }, (_, i) => {
                const a = (i / count) * Math.PI * 2 + t * 0.4;
                const r = 1.6 + Math.sin(i * 3.1) * 0.4;
                return (
                  <mesh key={i} material={i % 3 ? mat : mat2} position={[Math.cos(a) * r, Math.sin(i * 1.7 + t) * 0.9, Math.sin(a) * r]} rotation={[t + i, t * 0.7 + i, 0]}>
                    {kind === "pills" ? <capsuleGeometry args={[0.22, 0.5, 8, 24]} /> : <boxGeometry args={[0.55, 0.55, 0.55]} />}
                  </mesh>
                );
              })
            : null}
        </group>
      </Stage3D>
    </AbsoluteFill>
  );
};

// ------------------------------------------------------------------ Bars3D: growing 3D bar chart with labels
export const Bars3D: React.FC<{ bars: { label: string; value: number; color?: string }[]; max?: number; unit?: string; stagger?: number; cam?: string }> = ({ bars, max, unit = "", stagger = 0.15, cam = "orbit" }) => {
  const { f, fps } = useBlockTime();
  const th = useTheme();
  const t = f / fps;
  const mx = max ?? Math.max(...bars.map((b) => b.value));
  const n = bars.length;
  const gap = 1.25;
  const keys: CamKey[] =
    cam === "front"
      ? [{ t: 0, pos: [0, 3, 14], target: [0, 2, 0], fov: 30 }, { t: 6, pos: [0.6, 3.4, 13], target: [0, 2, 0], fov: 30 }]
      : [{ t: 0, pos: [-8, 6, 12], target: [0, 1.8, 0], fov: 30 }, { t: 6, pos: [6, 5, 12.5], target: [0, 1.8, 0], fov: 30 }];
  const c = camAt(keys, t);
  const camera = makeCamera(c);
  const hs = bars.map((b, i) => (b.value / mx) * 4.2 * E.outExpo(clamp01((t - 0.2 - i * stagger) / 1.1)));
  return (
    <AbsoluteFill>
      <Stage3D cam={c} lights="studio" env={0.9}>
        {bars.map((b, i) => (
          <mesh key={i} position={[(i - (n - 1) / 2) * gap, hs[i] / 2, 0]} castShadow>
            <boxGeometry args={[0.85, Math.max(0.001, hs[i]), 0.85]} />
            <meshPhysicalMaterial color={b.color ?? (i === n - 1 ? th.accent : th.dark ? "#3A3F55" : "#D6DAE6")} roughness={0.3} clearcoat={0.6} />
          </mesh>
        ))}
        <ContactShadow size={n * 1.6} opacity={0.35} />
        <mesh rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
          <planeGeometry args={[40, 40]} />
          <shadowMaterial opacity={0.18} transparent />
        </mesh>
      </Stage3D>
      {bars.map((b, i) => {
        const x = (i - (n - 1) / 2) * gap;
        const [tx, ty] = project(camera, new THREE.Vector3(x, hs[i] + 0.35, 0));
        const [bx, by] = project(camera, new THREE.Vector3(x, -0.05, 0.6));
        const a = clamp01((t - 0.3 - i * stagger) * 3);
        return (
          <React.Fragment key={i}>
            <div style={{ position: "absolute", left: tx - 150, top: ty - 60, width: 300, textAlign: "center", font: `800 52px ${th.fontDisplay}`, color: th.ink, opacity: a, letterSpacing: "-0.03em" }}>
              {Math.round(b.value * E.outExpo(clamp01((t - 0.2 - i * stagger) / 1.1)))}
              {unit}
            </div>
            <div style={{ position: "absolute", left: bx - 150, top: by + 6, width: 300, textAlign: "center", font: `600 30px ${th.fontUi}`, color: th.muted, opacity: a }}>{b.label}</div>
          </React.Fragment>
        );
      })}
    </AbsoluteFill>
  );
};

// ------------------------------------------------------------------ Tunnel3D: fly through glowing rings (intros / transitions)
export const Tunnel3D: React.FC<{ color?: string; color2?: string; speed?: number; shape?: "ring" | "square" | "hex" }> = ({ color, color2, speed = 1, shape = "ring" }) => {
  const { f, fps } = useBlockTime();
  const th = useTheme();
  const t = (f / fps) * speed;
  const n = 40;
  const z0 = (t * 9) % 2;
  const seg = shape === "square" ? 4 : shape === "hex" ? 6 : 96;
  const cam = { pos: [Math.sin(t * 0.8) * 0.15, Math.cos(t * 0.6) * 0.15, 0] as [number, number, number], target: [0, 0, -10] as [number, number, number], fov: 70, roll: Math.sin(t * 0.3) * 0.2 };
  return (
    <AbsoluteFill style={{ background: th.dark ? "#020208" : th.bg }}>
      <Stage3D cam={cam} lights="none" env={0} shadows={false} fog={{ color: th.dark ? "#020208" : th.bg, near: 6, far: 70 }}>
        {Array.from({ length: n }, (_, i) => {
          const z = -i * 2 + z0;
          return (
            <mesh key={i} position={[0, 0, z]} rotation={[0, 0, shape === "ring" ? 0 : i * 0.08 + t * 0.2]}>
              <torusGeometry args={[2.2, 0.025, 8, seg]} />
              <meshBasicMaterial color={i % 4 === 0 ? (color2 ?? th.accent2) : (color ?? th.accent)} toneMapped={false} />
            </mesh>
          );
        })}
      </Stage3D>
    </AbsoluteFill>
  );
};

// ------------------------------------------------------------------ StarRain: 3D stars (or coins) falling and tumbling (GitHub stars, rewards)
export const StarRain: React.FC<{ count?: number; color?: string; kind?: "star" | "coin" | "heart"; dur?: number }> = ({ count = 70, color = "#FFC531", kind = "star", dur = 3 }) => {
  const { f, fps } = useBlockTime();
  const t = f / fps;
  const geo = useMemo(() => {
    const s = new THREE.Shape();
    if (kind === "star") {
      for (let i = 0; i < 10; i++) {
        const r = i % 2 ? 0.22 : 0.5;
        const a = (i / 10) * Math.PI * 2 + Math.PI / 2;
        if (i === 0) s.moveTo(Math.cos(a) * r, Math.sin(a) * r);
        else s.lineTo(Math.cos(a) * r, Math.sin(a) * r);
      }
      s.closePath();
    } else if (kind === "heart") {
      s.moveTo(0, -0.45);
      s.bezierCurveTo(-0.6, -0.05, -0.45, 0.45, 0, 0.2);
      s.bezierCurveTo(0.45, 0.45, 0.6, -0.05, 0, -0.45);
    } else {
      s.absarc(0, 0, 0.42, 0, Math.PI * 2, false);
    }
    const g = new THREE.ExtrudeGeometry(s, { depth: kind === "coin" ? 0.08 : 0.14, bevelEnabled: true, bevelThickness: 0.04, bevelSize: 0.04, bevelSegments: 4 });
    g.center();
    return g;
  }, [kind]);
  const mat = useMemo(() => new THREE.MeshPhysicalMaterial({ color, metalness: 0.65, roughness: 0.25, clearcoat: 1, emissive: color, emissiveIntensity: 0.12 }), [color]);
  const cam = { pos: [0, 0, 14] as [number, number, number], target: [0, 0, 0] as [number, number, number], fov: 40 };
  return (
    <AbsoluteFill>
      <Stage3D cam={cam} lights="studio" env={1.1} shadows={false}>
        {Array.from({ length: count }, (_, i) => {
          const d = random(`sr-d${i}`) * dur * 0.8;
          const tt = t - d;
          if (tt < 0) return null;
          const x = (random(`sr-x${i}`) - 0.5) * 9;
          const z = (random(`sr-z${i}`) - 0.5) * 6;
          const y = 10 - tt * (6 + random(`sr-v${i}`) * 5) - 0.5 * 4 * tt * tt;
          const s = 0.5 + random(`sr-s${i}`) * 0.7;
          return <mesh key={i} geometry={geo} material={mat} position={[x, y, z]} rotation={[tt * 3 * random(`a${i}`), tt * 4 + i, tt * 2]} scale={s} />;
        })}
      </Stage3D>
    </AbsoluteFill>
  );
};

// ------------------------------------------------------------------ Cards3D (CSS 3D, crisp HTML): nested blocks floating in space with a moving camera
type Card3 = { block?: string; props?: Record<string, unknown>; src?: string; x?: number; y?: number; z?: number; rx?: number; ry?: number; rz?: number; w?: number; h?: number; at?: unknown };

export const Cards3D: React.FC<{ items: Card3[]; cam?: { from?: [number, number, number]; to?: [number, number, number]; rx?: [number, number]; ry?: [number, number] }; perspective?: number; shadow?: boolean }> = ({
  items, cam = {}, perspective = 1600, shadow = true,
}) => {
  const { f, fps, dur, at } = useBlockTime();
  const th = useTheme();
  const p = E.inOut(clamp01(f / Math.max(1, dur)));
  const from = cam.from ?? [0, 0, -300];
  const to = cam.to ?? [0, 0, 0];
  const cx = lerp(from[0], to[0], p);
  const cy = lerp(from[1], to[1], p);
  const cz = lerp(from[2], to[2], p);
  const rx = lerp(cam.rx?.[0] ?? 8, cam.rx?.[1] ?? 4, p);
  const ry = lerp(cam.ry?.[0] ?? -14, cam.ry?.[1] ?? 10, p);
  return (
    <AbsoluteFill style={{ perspective, perspectiveOrigin: "50% 45%" }}>
      <div style={{ position: "absolute", left: "50%", top: "50%", transformStyle: "preserve-3d", transform: `translate3d(${-cx}px, ${-cy}px, ${-cz}px) rotateX(${rx}deg) rotateY(${ry}deg)` }}>
        {items.map((it, i) => {
          const s = it.at !== undefined ? at(it.at) : Math.round(i * 0.12 * fps);
          const e = E.outExpo(clamp01((f - s) / (0.7 * fps)));
          const w = it.w ?? 420;
          const h = it.h ?? 560;
          return (
            <div
              key={i}
              style={{
                position: "absolute",
                left: -w / 2,
                top: -h / 2,
                width: w,
                height: h,
                transformStyle: "preserve-3d",
                transform: `translate3d(${it.x ?? 0}px, ${(it.y ?? 0) + (1 - e) * 200}px, ${(it.z ?? 0) - (1 - e) * 400}px) rotateX(${it.rx ?? 0}deg) rotateY(${it.ry ?? 0}deg) rotateZ(${it.rz ?? 0}deg)`,
                opacity: e,
                borderRadius: th.radius,
                overflow: "hidden",
                boxShadow: shadow ? th.cardShadow : undefined,
                background: th.card,
              }}
            >
              <Nested spec={it.block ? ({ block: it.block, props: it.props } as NestedBlock) : undefined} src={it.src} w={w} h={h} bg={th.card} />
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

// ------------------------------------------------------------------ Tilt: wrap any block in a gentle 2.5D perspective tilt (cheap "3D" for flat UI)
export const Tilt: React.FC<{ child: NestedBlock; rx?: [number, number]; ry?: [number, number]; w?: number; h?: number; shadow?: boolean; float?: boolean }> = ({
  child, rx = [14, 6], ry = [-18, 10], w = 760, h = 900, shadow = true, float = true,
}) => {
  const { f, dur } = useBlockTime();
  const th = useTheme();
  const p = E.inOut(clamp01(f / Math.max(1, dur)));
  const bob = float ? Math.sin(f * 0.04) * 8 : 0;
  return (
    <div style={{ perspective: 1800 }}>
      <div style={{ width: w, height: h, transform: `translateY(${bob}px) rotateX(${lerp(rx[0], rx[1], p)}deg) rotateY(${lerp(ry[0], ry[1], p)}deg)`, transformStyle: "preserve-3d", borderRadius: th.radius, boxShadow: shadow ? th.cardShadow : undefined, overflow: "hidden" }}>
        <Nested spec={child} w={w} h={h} bg={th.card} />
      </div>
    </div>
  );
};

export { roundedRectShape };
