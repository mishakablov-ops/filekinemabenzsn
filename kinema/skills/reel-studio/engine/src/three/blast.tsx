/**
 * Blast3D: a distant city at dusk, a flash, a rising fireball that turns into a mushroom cloud, a ground
 * shockwave that sweeps toward the camera (camera shake + dust when it arrives). Stylized low-poly,
 * warm palette, no gore. Times in seconds from the block start.
 */
import React, { useMemo } from "react";
import { AbsoluteFill, random } from "remotion";
import { useBlockTime } from "../core/context";
import { E, clamp01, lerp } from "../core/motion";
import { camAt, Stage3D, type CamKey, type V3 } from "./core";
import { Box, Building, PALETTES, StreetLamp } from "./kit";
import { AshFall, DeadTree } from "./kit2";

const GZ = -95; // ground zero (z)

const CAMS: Record<string, CamKey[]> = {
  // on a hill outside the city
  hill: [{ t: 0, pos: [-6, 6.5, 34], target: [0, 16, GZ], fov: 44 }, { t: 10, pos: [-4.5, 6.2, 31], target: [0, 20, GZ], fov: 44 }],
  // from a street between houses, looking up
  street: [{ t: 0, pos: [0.8, 1.7, 26], target: [0, 18, GZ], fov: 50 }, { t: 10, pos: [0.6, 1.7, 23], target: [0, 24, GZ], fov: 50 }],
  // far wide shot, the whole cloud
  wide: [{ t: 0, pos: [30, 14, 70], target: [0, 26, GZ], fov: 40 }, { t: 10, pos: [26, 13, 64], target: [0, 32, GZ], fov: 40 }],
};

const SMOKE = ["#5E5048", "#4E433C", "#6A5A4E", "#3E3530"];
const FIRE = "#F29A4E";

export const Blast3D: React.FC<{ cam?: string | CamKey[]; flashAt?: number; waveAt?: number; seed?: string; ash?: boolean }> = ({ cam = "hill", flashAt = 0.6, waveAt, seed = "nk", ash = true }) => {
  const { f, fps } = useBlockTime();
  const t = f / fps;
  const pal = PALETTES.evening;
  const keys = Array.isArray(cam) ? cam : CAMS[cam] ?? CAMS.hill;
  const base = camAt(keys, t);
  const camZ = base.pos[2];
  const hit = waveAt ?? flashAt + 3.2; // when the shockwave reaches the camera
  const dt = t - flashAt;
  // camera shake when the wave arrives
  const sh = t > hit ? Math.exp(-(t - hit) * 2.2) * 0.35 : 0;
  const c = {
    ...base,
    pos: [base.pos[0] + Math.sin(t * 61) * sh, base.pos[1] + Math.sin(t * 47 + 1) * sh * 0.7, base.pos[2]] as V3,
    target: [base.target[0] + Math.sin(t * 53) * sh * 2, base.target[1] + Math.sin(t * 43) * sh * 1.5, base.target[2]] as V3,
  };
  // fireball → cloud growth
  const g = clamp01(dt / 1.4);
  const rise = clamp01(dt / 9);
  const fireR = dt < 0 ? 0 : lerp(0.5, 12, E.outExpo(g));
  const capY = lerp(10, 58, E.out(rise));
  const capR = lerp(8, 26, E.out(clamp01(dt / 7)));
  const capGrow = E.out(clamp01((dt - 0.7) / 3)); // the cap forms after the fireball, not with it
  const stemGrow = E.out(clamp01((dt - 0.3) / 2.5));
  const heat = dt < 0 ? 0 : Math.max(0, 1 - dt / 5); // emissive fades as it cools
  const waveR = dt < 0 ? 0 : (Math.abs(camZ - GZ) + 6) * clamp01(dt / Math.max(0.5, hit - flashAt));
  const flash = dt < 0 ? 0 : Math.exp(-dt * 3.2);

  const skyline = useMemo(() => {
    const out: { x: number; z: number; w: number; h: number; d: number; s: number }[] = [];
    for (let i = 0; i < 46; i++) {
      const x = (random(`${seed}x${i}`) - 0.5) * 150;
      const z = GZ + 20 - random(`${seed}z${i}`) * 70;
      out.push({ x, z, w: 6 + random(`${seed}w${i}`) * 8, h: 10 + random(`${seed}h${i}`) * 34, d: 6 + random(`${seed}d${i}`) * 8, s: i });
    }
    return out;
  }, [seed]);

  const puffs = useMemo(() => Array.from({ length: 22 }, (_, i) => ({ a: (i / 22) * Math.PI * 2 + random(`${seed}pa${i}`) * 0.3, r: 0.75 + random(`${seed}pr${i}`) * 0.35, y: random(`${seed}py${i}`) * 0.35, s: 0.45 + random(`${seed}ps${i}`) * 0.4 })), [seed]);

  return (
    <AbsoluteFill style={{ background: "#2A2420" }}>
      <Stage3D cam={c} lights="sunset" env={0.35} fog={{ color: "#3A302A", near: 40, far: 260 }} exposure={1 + flash * 0.6}>
        {/* ground */}
        <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0, -40]} receiveShadow>
          <planeGeometry args={[600, 400]} />
          <meshStandardMaterial color="#3E3631" roughness={1} />
        </mesh>
        {/* city */}
        {skyline.map((b) => (
          <Building key={b.s} p={[b.x, 0, b.z]} w={b.w} h={b.h} d={b.d} pal={pal} lit={dt < 0.3 ? 0.35 : 0} seed={b.s} face={b.x < 0 ? 1 : -1} />
        ))}
        {/* foreground: road edge, lamps, dead-to-be trees */}
        <Box s={[7, 0.05, 80]} p={[0, 0.02, camZ - 30]} c="#2E2A27" rad={0.01} />
        {[0, 1, 2, 3].map((i) => <StreetLamp key={i} p={[4, 0, camZ - 8 - i * 14]} rotY={-Math.PI / 2} on={dt < 0.2} pal={pal} />)}
        {[0, 1, 2].map((i) => <DeadTree key={i} p={[-6 - i * 3, 0, camZ - 14 - i * 11]} s={1.4} seed={i + 4} />)}
        {/* fireball + stem + cap */}
        {dt >= 0 ? (
          <group position={[0, 0, GZ]}>
            <mesh position={[0, lerp(fireR * 0.6, capY - 4, rise), 0]} scale={fireR * (1 - rise * 0.35)}>
              <icosahedronGeometry args={[1, 3]} />
              <meshStandardMaterial color={heat > 0.3 ? FIRE : SMOKE[0]} emissive="#F07A30" emissiveIntensity={3.5 * heat} roughness={0.9} flatShading />
            </mesh>
            <mesh position={[0, ((capY - 4) * stemGrow) / 2, 0]} scale={[1, 1, 1]}>
              <cylinderGeometry args={[lerp(2, 5, rise), lerp(4, 9, rise), Math.max(0.1, (capY - 4) * stemGrow), 14, 1]} />
              <meshStandardMaterial color={SMOKE[2]} emissive="#C05A28" emissiveIntensity={1.2 * heat} roughness={1} flatShading />
            </mesh>
            {/* cap: torus + puffs */}
            <mesh position={[0, capY, 0]} rotation={[Math.PI / 2, 0, 0]} scale={Math.max(0.001, (capR / 10) * capGrow)}>
              <torusGeometry args={[7, 4.2, 10, 20]} />
              <meshStandardMaterial color={SMOKE[1]} emissive="#E06A2A" emissiveIntensity={1.6 * heat} roughness={1} flatShading />
            </mesh>
            {puffs.map((p, i) => (
              <mesh key={i} position={[Math.cos(p.a) * capR * p.r * capGrow, capY + 2 + p.y * capR * 0.6 * capGrow, Math.sin(p.a) * capR * p.r * capGrow]} scale={Math.max(0.001, capR * p.s * 0.45 * capGrow)}>
                <icosahedronGeometry args={[1, 1]} />
                <meshStandardMaterial color={SMOKE[i % SMOKE.length]} emissive="#D86A30" emissiveIntensity={0.9 * heat} roughness={1} flatShading />
              </mesh>
            ))}
            <pointLight position={[0, capY * 0.5, 10]} intensity={900 * heat + 40} distance={400} color="#F29050" />
          </group>
        ) : null}
        {/* shockwave: dust ring sweeping over the ground toward the camera */}
        {dt > 0 && waveR < Math.abs(camZ - GZ) + 40 ? (
          <group position={[0, 0, GZ]}>
            <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.6, 0]}>
              <ringGeometry args={[Math.max(0.1, waveR - 6), waveR, 96]} />
              <meshStandardMaterial color="#8A7A68" transparent opacity={0.55} roughness={1} depthWrite={false} />
            </mesh>
            {Array.from({ length: 48 }, (_, i) => {
              const a = (i / 48) * Math.PI * 2;
              return (
                <mesh key={i} position={[Math.cos(a) * waveR, 2.2 + (i % 3) * 0.8, Math.sin(a) * waveR]} scale={2.6 + (i % 4) * 0.7}>
                  <icosahedronGeometry args={[1, 1]} />
                  <meshStandardMaterial color="#7A6A5A" transparent opacity={0.45} roughness={1} depthWrite={false} flatShading />
                </mesh>
              );
            })}
          </group>
        ) : null}
        {ash && t > hit ? <AshFall t={t - hit} center={[c.pos[0], 6, c.pos[2] - 12]} size={[30, 14, 30]} n={600} c="#9E9286" speed={0.6} /> : null}
      </Stage3D>
      {/* the flash: warm, never pure white */}
      {flash > 0.01 ? <AbsoluteFill style={{ background: "#F7E7CC", opacity: Math.min(0.97, flash * 1.15) }} /> : null}
      {/* dust haze after the wave */}
      {t > hit ? <AbsoluteFill style={{ background: "#6E5E50", opacity: Math.min(0.45, (t - hit) * 0.5) * Math.exp(-(t - hit) * 0.25) }} /> : null}
    </AbsoluteFill>
  );
};
