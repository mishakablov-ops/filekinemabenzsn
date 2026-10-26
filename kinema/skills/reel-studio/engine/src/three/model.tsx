import React, { useEffect, useMemo, useState } from "react";
import { AbsoluteFill, continueRender, delayRender, staticFile } from "remotion";
import * as THREE from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import { useBlockTime } from "../core/context";
import { E, clamp01, lerp } from "../core/motion";
import { camAt, ContactShadow, makeCamera, project, Stage3D, type Cam, type CamKey, type LightRig, type V3 } from "./core";
import { Nested, type NestedBlock } from "./devices";
import { ScreenQuad } from "./room";

/**
 * Model3D — any .glb/.gltf (BlenderKit / Sketchfab / Poly Haven / your own Blender export).
 * Put files in engine/public/models/. Convert .blend with scripts/blend2glb.py (see that file).
 * screenMesh: name of the mesh that is the display -> a LIVE HTML screen is mapped onto it.
 */
type Loaded = { scene: THREE.Group; animations: THREE.AnimationClip[] };
const cache = new Map<string, Promise<Loaded>>();
const load = (url: string) => {
  if (!cache.has(url)) cache.set(url, new GLTFLoader().loadAsync(url).then((g) => ({ scene: g.scene, animations: g.animations })));
  return cache.get(url)!;
};

// presets scale with `fit` (model size) so portrait framing works for any model
const presetCams = (name: string, k: number): CamKey[] => {
  const P: Record<string, CamKey[]> = {
    hero: [
      { t: 0, pos: [0, k * 0.85, k * 4.1], target: [0, k * 0.32, 0], fov: 30 },
      { t: 7, pos: [k * 0.35, k * 0.75, k * 3.7], target: [0, k * 0.32, 0], fov: 30 },
    ],
    orbit: [
      { t: 0, pos: [-k * 2.7, k * 1.0, k * 3.2], target: [0, k * 0.3, 0], fov: 30 },
      { t: 7, pos: [k * 2.7, k * 0.9, k * 3.2], target: [0, k * 0.3, 0], fov: 30 },
    ],
    low: [
      { t: 0, pos: [-k * 0.7, k * 0.12, k * 3.9], target: [0, k * 0.35, 0], fov: 30 },
      { t: 7, pos: [k * 0.5, k * 0.2, k * 3.6], target: [0, k * 0.35, 0], fov: 30 },
    ],
    top: [
      { t: 0, pos: [0, k * 3.8, k * 1.4], target: [0, k * 0.1, 0], fov: 30 },
      { t: 7, pos: [0, k * 3.4, k * 1.1], target: [0, k * 0.1, 0], fov: 30 },
    ],
    close: [
      { t: 0, pos: [0, k * 0.6, k * 2.3], target: [0, k * 0.35, 0], fov: 32 },
      { t: 7, pos: [k * 0.2, k * 0.55, k * 2.0], target: [0, k * 0.35, 0], fov: 32 },
    ],
  };
  const keys = P[name] ?? P.hero;
  if (name === "top") return keys;
  // frame the model in the lower ~60 % of the 9:16 frame (top captions need the upper band)
  return keys.map((kf) => {
    const d = Math.hypot(kf.pos[0] - kf.target[0], kf.pos[1] - kf.target[1], kf.pos[2] - kf.target[2]);
    const lift = 2 * d * Math.tan(THREE.MathUtils.degToRad((kf.fov ?? 30) / 2)) * 0.075;
    return { ...kf, pos: [kf.pos[0], kf.pos[1] + lift, kf.pos[2]] as V3, target: [kf.target[0], kf.target[1] + lift, kf.target[2]] as V3 };
  });
};
/** invisible DOM box = projected 3D bounds of an object, measured by the overlap QA (data-qa-proxy) */
export const qaProxy = (obj: THREE.Object3D, cam: Cam) => {
  const box = new THREE.Box3().setFromObject(obj);
  if (box.isEmpty()) return null;
  const camera = makeCamera(cam);
  const xs: number[] = [];
  const ys: number[] = [];
  for (const x of [box.min.x, box.max.x]) for (const y of [box.min.y, box.max.y]) for (const z of [box.min.z, box.max.z]) {
    const [px, py, pz] = project(camera, new THREE.Vector3(x, y, z));
    if (pz < 1) {
      xs.push(px);
      ys.push(py);
    }
  }
  if (!xs.length) return null;
  const x0 = Math.max(0, Math.min(...xs));
  const y0 = Math.max(0, Math.min(...ys));
  const x1 = Math.min(1080, Math.max(...xs));
  const y1 = Math.min(1920, Math.max(...ys));
  if (x1 - x0 > 1000 && y1 - y0 > 1800) return null; // fills the frame: it's a backdrop, not an object
  return <div data-qa="layer" data-qa-id="3d-object" data-qa-cat="screen" data-qa-proxy="1" style={{ position: "absolute", left: x0, top: y0, width: x1 - x0, height: y1 - y0, pointerEvents: "none" }} />;
};

/** corners (tl,tr,br,bl) of a flat display mesh in world space, using its local bounding box */
const screenCorners = (mesh: THREE.Mesh) => {
  mesh.geometry.computeBoundingBox();
  const bb = mesh.geometry.boundingBox!;
  const size = new THREE.Vector3();
  bb.getSize(size);
  const axes = [0, 1, 2];
  const thin = axes.reduce((a, b) => (size.getComponent(a) < size.getComponent(b) ? a : b));
  const others = axes.filter((a) => a !== thin);
  const m = mesh.matrixWorld;
  const dir = (ax: number) => new THREE.Vector3().setComponent(ax, 1).transformDirection(m);
  const up = Math.abs(dir(others[0]).y) > Math.abs(dir(others[1]).y) ? others[0] : others[1];
  const right = others.find((a) => a !== up)!;
  const c = new THREE.Vector3();
  bb.getCenter(c);
  const half = size.clone().multiplyScalar(0.5);
  const pt = (sr: number, su: number) => {
    const v = c.clone();
    v.setComponent(right, c.getComponent(right) + sr * half.getComponent(right));
    v.setComponent(up, c.getComponent(up) + su * half.getComponent(up));
    v.setComponent(thin, c.getComponent(thin) + half.getComponent(thin));
    return v.applyMatrix4(m);
  };
  const raw = [pt(-1, 1), pt(1, 1), pt(1, -1), pt(-1, -1)];
  // the display's real outward normal (average of vertex normals)
  const nAttr = mesh.geometry.getAttribute("normal") as THREE.BufferAttribute | undefined;
  const face = new THREE.Vector3();
  if (nAttr) for (let i = 0; i < nAttr.count; i++) face.add(new THREE.Vector3(nAttr.getX(i), nAttr.getY(i), nAttr.getZ(i)));
  face.transformDirection(m).normalize();
  if (face.lengthSq() === 0) face.subVectors(raw[1], raw[0]).cross(new THREE.Vector3().subVectors(raw[3], raw[0])).normalize().negate();
  // classify corners in WORLD space: right = up x face, up' = face x right (robust to any model rotation / mirroring)
  const worldUp = Math.abs(face.y) > 0.9 ? dir(up) : new THREE.Vector3(0, 1, 0);
  const rightW = new THREE.Vector3().crossVectors(worldUp, face).normalize();
  const upW = new THREE.Vector3().crossVectors(face, rightW).normalize();
  const cw = c.clone().applyMatrix4(m);
  const score = (p: THREE.Vector3, sr: number, su: number) => sr * p.clone().sub(cw).dot(rightW) + su * p.clone().sub(cw).dot(upW);
  const best = (sr: number, su: number) => raw.reduce((a, q) => (score(q, sr, su) > score(a, sr, su) ? q : a));
  const pts = [best(-1, 1), best(1, 1), best(1, -1), best(-1, -1)];
  return { pts, n: face, c: cw };
};

export const Model3D: React.FC<{
  src?: string; cam?: string | CamKey[]; fit?: number; rot?: V3; spin?: number; screen?: NestedBlock; screenMesh?: string; screenMaterial?: string; screenW?: number; flipScreen?: boolean; screenRadius?: number;
  anim?: boolean; clip?: number; lights?: LightRig; env?: number; shadow?: number;
  /** flip: rises in showing its BACK, then turns 180° onto the screen at flipAt (anchor/seconds) over flipDur */
  enter?: "rise" | "spin" | "none" | "flip"; flipAt?: unknown; flipDur?: number;
  /** island: draw the Dynamic Island over the live screen; float: gentle hover after it lands */
  island?: boolean; float?: boolean;
  /** body colour: repaints every material whose name contains "color" (iPhone body / back), e.g. "#D8C3A2" for beige */
  color?: string;
}> = ({ color: bodyColor, src, cam = "hero", fit = 3, rot = [0, 0, 0], spin = 0, screen, screenMesh, screenMaterial, screenW = 1280, flipScreen = false, screenRadius = 0, anim = true, clip = 0, lights = "studio", env = 1, shadow = 0.45, enter = "rise", flipAt, flipDur = 1.3, island = false, float = false }) => {
  const { f, fps, at } = useBlockTime();
  const t = f / fps;
  const file = src ?? "models/macbook.glb";
  const url = /^https?:/.test(file) ? file : staticFile(file);
  const [data, setData] = useState<Loaded | null>(null);
  const [handle] = useState(() => delayRender(`model ${src}`, { timeoutInMilliseconds: 120000 }));
  useEffect(() => {
    load(url)
      .then((d) => {
        setData(d);
        continueRender(handle);
      })
      .catch((e) => {
        console.error("Model3D failed", src, e);
        continueRender(handle);
      });
  }, [url, handle, src]);
  const prepared = useMemo(() => {
    if (!data) return null;
    const root = data.scene.clone(true);
    // orient first (e.g. a phone modelled lying flat), then measure, so it stands on the floor
    root.rotation.set(rot[0], rot[1], rot[2]);
    root.updateMatrixWorld(true);
    root.traverse((o) => {
      const mesh = o as THREE.Mesh;
      if (mesh.isMesh) {
        mesh.castShadow = true;
        mesh.receiveShadow = true;
        if (bodyColor) {
          const mats = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
          const out = mats.map((m) => {
            if (!/color/i.test(m.name)) return m;
            const c = (m as THREE.MeshStandardMaterial).clone();
            c.map = null;
            c.color = new THREE.Color(bodyColor);
            c.needsUpdate = true;
            return c;
          });
          mesh.material = Array.isArray(mesh.material) ? out : out[0];
        }
      }
    });
    const box = new THREE.Box3().setFromObject(root);
    const size = new THREE.Vector3();
    box.getSize(size);
    const k = fit / Math.max(size.x, size.y, size.z);
    const center = new THREE.Vector3();
    box.getCenter(center);
    const wrap = new THREE.Group();
    const holder = new THREE.Group();
    holder.add(root);
    holder.position.set(-center.x * k, -box.min.y * k, -center.z * k);
    holder.scale.setScalar(k);
    wrap.add(holder);
    const mixer = data.animations.length ? new THREE.AnimationMixer(root) : null;
    if (mixer) mixer.clipAction(data.animations[Math.min(clip, data.animations.length - 1)]).play();
    return { wrap, mixer };
  }, [data, fit, clip, rot[0], rot[1], rot[2], bodyColor]);
  if (!prepared) return <AbsoluteFill />;
  const ent = enter === "none" ? 1 : E.outExpo(clamp01(t / 1.0));
  let yaw = THREE.MathUtils.degToRad(spin * t) + (enter === "spin" ? (1 - ent) * Math.PI : 0);
  let lift = enter === "rise" ? lerp(-0.8, 0, ent) : 0;
  if (enter === "flip") {
    const fa = flipAt !== undefined ? at(flipAt) / fps : 1.2;
    const fp = E.inOut(clamp01((t - fa) / flipDur));
    // back to the camera, drifting slowly, then one smooth half-turn onto the screen (plus a small settle)
    yaw += (Math.PI + 0.32 * (1 - E.out(clamp01(t / Math.max(0.3, fa))))) * (1 - fp) - 0.05 * Math.sin(Math.PI * clamp01((t - fa - flipDur * 0.7) / 0.8));
    lift = lerp(-fit * 0.45, 0, E.outExpo(clamp01(t / 1.1)));
  }
  if (float) lift += Math.sin(t * 1.4) * fit * 0.008;
  prepared.wrap.rotation.set(float ? Math.sin(t * 0.9) * 0.015 : 0, yaw, 0);
  prepared.wrap.position.set(0, lift, 0);
  if (prepared.mixer && anim) prepared.mixer.setTime(t);
  prepared.wrap.updateMatrixWorld(true);
  let overlay: React.ReactNode = null;
  let keys: CamKey[] = Array.isArray(cam) ? cam : presetCams(cam === "toScreen" ? "hero" : cam, fit);
  let c = camAt(keys, t);
  if (screen && (screenMesh || screenMaterial)) {
    let mesh: THREE.Mesh | undefined;
    if (screenMaterial) {
      const want = screenMaterial.toLowerCase();
      prepared.wrap.traverse((o) => {
        const m = o as THREE.Mesh;
        if (mesh || !m.isMesh) return;
        const mats = Array.isArray(m.material) ? m.material : [m.material];
        if (mats.some((mt) => (mt?.name ?? "").toLowerCase().includes(want))) mesh = m;
      });
    }
    if (!mesh && screenMesh) mesh = (prepared.wrap.getObjectByName(screenMesh) ?? prepared.wrap.getObjectByName(screenMesh.replace(/[ .]/g, "_"))) as THREE.Mesh | undefined;
    if (mesh && mesh.isMesh) {
      const sc = screenCorners(mesh);
      if (flipScreen) sc.pts = [sc.pts[1], sc.pts[0], sc.pts[3], sc.pts[2]];
      if (cam === "toScreen") {
        // fly from the hero shot to a point in front of the display so it fills the frame width
        const width = sc.pts[0].distanceTo(sc.pts[1]);
        const hfov = 2 * Math.atan(Math.tan(THREE.MathUtils.degToRad(40) / 2) * (1080 / 1920));
        const dist = (width * 0.55) / Math.tan(hfov / 2);
        // keep the display in the lower part of the frame (top captions need air): lift camera + target together
        const visH = 2 * dist * Math.tan(THREE.MathUtils.degToRad(20));
        const lift = new THREE.Vector3(0, 1, 0).multiplyScalar(visH * 0.09);
        const tgt = sc.c.clone().add(lift);
        const end = sc.c.clone().add(sc.n.clone().multiplyScalar(dist)).add(lift);
        const h0 = presetCams("hero", fit)[0];
        keys = [h0, { t: 1.0, pos: h0.pos, target: h0.target, fov: 30 }, { t: 3.0, pos: [end.x, end.y, end.z], target: [tgt.x, tgt.y, tgt.z], fov: 40, ease: "inOut" }];
        c = camAt(keys, t);
      }
      const camera = makeCamera(c);
      const q = sc.pts.map((p) => project(camera, p)).map(([x, y]) => [x, y] as [number, number]);
      const ar = sc.pts[0].distanceTo(sc.pts[1]) / Math.max(1e-4, sc.pts[0].distanceTo(sc.pts[3]));
      const pxH = Math.round(screenW / ar);
      // display turned away from the camera -> no live HTML (we would be looking at the back of the device)
      const facing = new THREE.Vector3(...c.pos).sub(sc.c).normalize().dot(sc.n);
      const content = (
        <>
          <Nested spec={screen} w={screenW} h={pxH} />
          {island ? <div style={{ position: "absolute", left: screenW / 2 - screenW * 0.16, top: screenW * 0.028, width: screenW * 0.32, height: screenW * 0.094, borderRadius: screenW * 0.05, background: "#050505" }} /> : null}
          {/* glass: soft sheen that moves with the turn + edge darkening at grazing angles */}
          {facing < 0.45 ? <div style={{ position: "absolute", inset: 0, background: "#000", opacity: (0.45 - facing) * 2 }} /> : null}
          <div style={{ position: "absolute", inset: 0, background: `linear-gradient(${120 + yaw * 30}deg, rgba(255,255,255,0.10) 0%, rgba(255,255,255,0) 34%, rgba(255,255,255,0) 72%, rgba(255,255,255,0.05) 100%)`, mixBlendMode: "screen" }} />
        </>
      );
      if (facing > 0.03) overlay = <ScreenQuad q={q} pxW={screenW} pxH={pxH} radius={screenRadius} content={content} />;
    }
  }
  const proxy = qaProxy(prepared.wrap, c);
  return (
    <AbsoluteFill style={{ opacity: clamp01(t * 4) }}>
      {proxy}
      <Stage3D cam={c} lights={lights} env={env}>
        <primitive object={prepared.wrap} />
        <ContactShadow size={fit * 1.6} opacity={shadow} />
      </Stage3D>
      {overlay}
    </AbsoluteFill>
  );
};

/** Ready-made wrappers for the user's imported models (assets/models-src -> public/models). */
export const MacBook: React.FC<React.ComponentProps<typeof Model3D>> = (p) => (
  <Model3D {...p} src={p.src ?? "models/macbook.glb"} screenMaterial={p.screenMaterial ?? "Display"} fit={p.fit ?? 3.2} screenW={p.screenW ?? 1280} cam={p.cam ?? "orbit"} />
);
export const IPhone17: React.FC<React.ComponentProps<typeof Model3D>> = (p) => (
  <Model3D
    island
    {...p}
    src={p.src ?? "models/iphone17pro.glb"}
    screenMaterial={p.screenMaterial ?? "Screen"}
    // stand it up (modelled lying flat) + half-turn in its own plane so the camera plateau is at the TOP
    rot={p.rot ?? [-Math.PI / 2, Math.PI, 0]}
    fit={p.fit ?? 3}
    screenW={p.screenW ?? 390}
    screenRadius={p.screenRadius ?? 44}
    // framed for top captions: phone occupies y ≈ 650–1650 of the 1920 frame
    cam={p.cam ?? [{ t: 0, pos: [0, 2.1, 10.8], target: [0, 2.05, 0], fov: 30 }, { t: 6, pos: [1.1, 2.2, 10.2], target: [0, 2.05, 0], fov: 30 }]}
  />
);
