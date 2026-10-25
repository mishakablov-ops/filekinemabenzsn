/**
 * Scenes for the "escape from North Korea" first-person reel (project nk-escape).
 * Shared pieces: useGLB (cached, render-blocking load), OutdoorLights (sun whose shadow box follows the camera),
 * the jeep rig (steering wheel + wheels + driver eye) and first-person hands (fphands.ts).
 */
import React, { useEffect, useMemo, useState } from "react";
import { AbsoluteFill, continueRender, delayRender, staticFile } from "remotion";
import * as THREE from "three";
import { GLTFLoader, type GLTF } from "three/examples/jsm/loaders/GLTFLoader.js";
import { useBlockTime } from "../core/context";
import { camAt, headCam, makeCamera, Stage3D, type Cam, type CamKey, type V3 } from "./core";
import { barGrip, createFPRig, type HandTrack } from "./fphands";
import { createMxSoldier, type ClipMeta, type Program } from "./soldierMx";
import { aimRifle, carryRifle, createSoldier, gait, makeRifle, type PathKey } from "./soldier";
import { BARRACKS_MARKS, buildBarracks, buildJSA, findFloaters, flagTower, jointInside, JSA_MARKS, leafMaterialFrom, prepareFlag, solidBoxes, TEX_NAMES, type Tex } from "./nkSets";

const MODELS = "projects/nk-escape/models/";
const cache = new Map<string, Promise<GLTF>>();

/** all set textures (albedo sRGB + normal maps), tiled; the frame waits until they are loaded */
const texCache: { p?: Promise<Tex> } = {};
export const useNkTextures = () => {
  const [tex, setTex] = useState<Tex | null>(null);
  const [handle] = useState(() => delayRender("nk textures", { timeoutInMilliseconds: 180000 }));
  useEffect(() => {
    if (!texCache.p) {
      const loader = new THREE.TextureLoader();
      const one = (file: string, srgb: boolean) =>
        loader.loadAsync(staticFile("projects/nk-escape/tex/" + file)).then((t) => {
          t.wrapS = t.wrapT = THREE.RepeatWrapping;
          t.anisotropy = 8;
          t.colorSpace = srgb ? THREE.SRGBColorSpace : THREE.NoColorSpace;
          return t;
        });
      texCache.p = Promise.all(TEX_NAMES.flatMap((n) => [one(n + ".jpg", true).then((t) => [n, t] as const), one(n + "_n.png", false).then((t) => [n + "_n", t] as const)])).then((pairs) => Object.fromEntries(pairs));
    }
    texCache.p
      .then((t) => {
        setTex(t);
        continueRender(handle);
      })
      .catch((e) => {
        console.error("textures", e);
        continueRender(handle);
      });
  }, [handle]);
  return tex;
};

/** load a GLB once per render process; the frame waits until it is ready */
export const useGLB = (file: string) => {
  const url = /^https?:/.test(file) ? file : staticFile(file);
  const [g, setG] = useState<GLTF | null>(null);
  const [handle] = useState(() => delayRender("glb " + file, { timeoutInMilliseconds: 180000 }));
  useEffect(() => {
    if (!cache.has(url)) cache.set(url, new GLTFLoader().loadAsync(url));
    cache
      .get(url)!
      .then((x) => {
        setG(x);
        continueRender(handle);
      })
      .catch((e) => {
        console.error("GLB failed", file, e);
        continueRender(handle);
      });
  }, [url, handle, file]);
  return g;
};

/** overcast daylight: sky/ground hemisphere + a soft sun whose shadow box follows `focus` */
export const OutdoorLights: React.FC<{ focus: V3; sun?: V3; intensity?: number; warm?: string }> = ({ focus, sun = [-18, 30, -10], intensity = 1.9, warm = "#FFF1DD" }) => {
  const light = useMemo(() => {
    const l = new THREE.DirectionalLight(warm, intensity);
    l.castShadow = true;
    l.shadow.mapSize.set(4096, 4096);
    const c = l.shadow.camera as THREE.OrthographicCamera;
    c.left = -14;
    c.right = 14;
    c.top = 14;
    c.bottom = -14;
    c.near = 1;
    c.far = 120;
    l.shadow.bias = -0.0002;
    l.shadow.normalBias = 0.02;
    l.shadow.radius = 4;
    return l;
  }, [warm, intensity]);
  light.position.set(focus[0] + sun[0], focus[1] + sun[1], focus[2] + sun[2]);
  light.target.position.set(...focus);
  light.target.updateMatrixWorld();
  return (
    <>
      <hemisphereLight args={["#C9D3DC", "#5B5A48", 1.05]} />
      <primitive object={light} />
      <primitive object={light.target} />
    </>
  );
};


/** one look for every nk-escape shot: muted overcast colour, soft vignette, fine moving film grain */
export const NkLook: React.FC<{ t: number; children: React.ReactNode; vignette?: number; grain?: number }> = ({ t, children, vignette = 0.36, grain = 0.07 }) => {
  const seed = Math.floor(t * 30) % 97;
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{ filter: "saturate(0.84) contrast(1.07) brightness(0.98) sepia(0.06)" }}>{children}</AbsoluteFill>
      <AbsoluteFill style={{ background: `radial-gradient(ellipse 75% 62% at 50% 46%, rgba(0,0,0,0) 58%, rgba(8,10,12,${vignette}) 100%)`, pointerEvents: "none" }} />
      <AbsoluteFill style={{ opacity: grain, mixBlendMode: "overlay", pointerEvents: "none" }}>
        <svg width="100%" height="100%">
          <filter id={"nkgrain" + seed}>
            <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed={seed} stitchTiles="stitch" />
            <feColorMatrix type="saturate" values="0" />
          </filter>
          <rect width="100%" height="100%" filter={`url(#nkgrain${seed})`} />
        </svg>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

// ------------------------------------------------------------------ jeep
type JeepRig = {
  root: THREE.Group; model: THREE.Object3D; body: THREE.Object3D; bodyY: number; wheelY: number; wheel: THREE.Object3D; wheelQ: THREE.Quaternion; wheelLocal: THREE.Matrix4;
  eye: THREE.Vector3; grip: { L: THREE.Vector3; R: THREE.Vector3 }; tyres: { o: THREE.Object3D; q: THREE.Quaternion; front: boolean }[];
};
export const useJeep = (): JeepRig | null => {
  const g = useGLB(MODELS + "jeep_kpa.glb");
  return useMemo(() => {
    if (!g) return null;
    const model = g.scene.clone(true);
    model.traverse((o) => {
      const m = o as THREE.Mesh;
      if (m.isMesh) {
        m.castShadow = true;
        m.receiveShadow = true;
      }
    });
    model.updateMatrixWorld(true);
    const get = (n: string) => model.getObjectByName(n)!;
    const wheel = get("steering_wheel");
    const wheelLocal = wheel.matrix.clone();
    const inv = wheelLocal.clone().invert();
    // rim frame from the two GLB grip markers (they sit at 10 and 2 o'clock): right = R - L, up = R + L
    const gl = get("GRIP_L").position.clone().applyMatrix4(inv).setY(0);
    const gr = get("GRIP_R").position.clone().applyMatrix4(inv).setY(0);
    const right = gr.clone().sub(gl).normalize();
    const up = gr.clone().add(gl).normalize();
    /** point on the rim at a clock angle in degrees (0 = 3 o'clock, 90 = 12 o'clock) */
    const rim = (deg: number) => right.clone().multiplyScalar(Math.cos((deg * Math.PI) / 180)).addScaledVector(up, Math.sin((deg * Math.PI) / 180)).multiplyScalar(0.212);
    const toRim = (n: string) => rim(n === "GRIP_L" ? 136 : 44); // ~10:30 and 1:30 keep both hands inside a 9:16 frame
    const root = new THREE.Group();
    root.add(model);
    const body = get("body");
    return {
      root, model, body, bodyY: body.position.y, wheelY: wheel.position.y, wheel, wheelQ: wheel.quaternion.clone(), wheelLocal, eye: get("DRIVER_EYE").position.clone(),
      grip: { L: toRim("GRIP_L"), R: toRim("GRIP_R") },
      tyres: ["wheel_FL", "wheel_FR", "wheel_RL", "wheel_RR"].map((n) => ({ o: get(n), q: get(n).quaternion.clone(), front: n.includes("F") })),
    };
  }, [g]);
};

// ------------------------------------------------------------------ test: driving with both hands, one hand leaves and returns
const smooth = (a: number, b: number, t: number) => {
  const x = Math.min(1, Math.max(0, (t - a) / (b - a)));
  return x * x * x * (x * (x * 6 - 15) + 10);
};

export const JeepDriveTest: React.FC<{ speed?: number; debug?: boolean; eye?: V3; camFrom?: V3 }> = ({ speed = 7, debug = false, eye: eyeOverride, camFrom }) => {
  const { f, fps } = useBlockTime();
  const t = f / fps;
  const jeepRig = useJeep();
  // a seated driver's eyes are ~0.55 m behind the wheel hub (the GLB marker sits closer)
  const jeep = useMemo(() => (jeepRig ? { ...jeepRig, eye: new THREE.Vector3(...(eyeOverride ?? [0.263, 1.47, -0.56])) } : null), [jeepRig, eyeOverride?.[0], eyeOverride?.[1], eyeOverride?.[2]]);
  const armsG = useGLB("models/fp_arms.glb");
  const rig = useMemo(() => (armsG ? createFPRig(armsG.scene) : null), [armsG]);

  const world = useMemo(() => {
    const g = new THREE.Group();
    const ground = new THREE.Mesh(new THREE.PlaneGeometry(600, 600), new THREE.MeshStandardMaterial({ color: "#727552", roughness: 1 }));
    ground.rotation.x = -Math.PI / 2;
    ground.position.z = 200;
    ground.receiveShadow = true;
    const road = new THREE.Mesh(new THREE.PlaneGeometry(6.5, 600), new THREE.MeshStandardMaterial({ color: "#46453F", roughness: 0.95 }));
    road.rotation.x = -Math.PI / 2;
    road.position.set(0, 0.01, 200);
    road.receiveShadow = true;
    g.add(ground, road);
    const dash = new THREE.InstancedMesh(new THREE.BoxGeometry(0.14, 0.012, 2.2), new THREE.MeshStandardMaterial({ color: "#C9C4B0", roughness: 0.8 }), 90);
    const trunk = new THREE.InstancedMesh(new THREE.CylinderGeometry(0.12, 0.18, 4, 7), new THREE.MeshStandardMaterial({ color: "#4B3F33", roughness: 1 }), 80);
    const crown = new THREE.InstancedMesh(new THREE.IcosahedronGeometry(1.9, 1), new THREE.MeshStandardMaterial({ color: "#B07A2E", roughness: 0.9, flatShading: true }), 80);
    const m = new THREE.Matrix4();
    for (let i = 0; i < 90; i++) dash.setMatrixAt(i, m.makeTranslation(0, 0.016, -10 + i * 6));
    for (let i = 0; i < 80; i++) {
      const side = i % 2 ? 1 : -1;
      const x = side * (6.5 + ((i * 37) % 7) * 0.6);
      const z = -10 + Math.floor(i / 2) * 11 + ((i * 13) % 5);
      trunk.setMatrixAt(i, m.makeTranslation(x, 2, z));
      crown.setMatrixAt(i, m.compose(new THREE.Vector3(x, 4.6, z), new THREE.Quaternion(), new THREE.Vector3(1, 1.25 + ((i * 7) % 4) * 0.1, 1)));
    }
    for (const im of [trunk, crown]) {
      im.castShadow = true;
      im.receiveShadow = true;
    }
    g.add(dash, trunk, crown);
    return g;
  }, []);

  // ---- pure functions of time: steering, car pose, camera
  // a lazy S-bend: left, back, a little right to straighten, then a one-handed correction at the end
  const steerDeg = (T: number) =>
    26 * smooth(1.9, 2.7, T) - 26 * smooth(2.9, 3.6, T) - 22 * smooth(3.6, 4.2, T) + 22 * smooth(4.4, 5.0, T) + 6 * smooth(6.2, 6.8, T) - 6 * smooth(7.0, 7.6, T);
  const carPose = (T: number) => {
    let x = 0, z = 0, yaw = 0;
    const dt = 1 / 60;
    for (let s = 0; s < T; s += dt) {
      const h = Math.min(dt, T - s);
      yaw += (speed * Math.tan((steerDeg(s) / 16) * (Math.PI / 180)) / 2.03) * h;
      x += Math.sin(yaw) * speed * h;
      z += Math.cos(yaw) * speed * h;
    }
    // the wheels stay on the road; only the body rides the suspension (bob), the head and wheel go with the body
    const bob = 0.008 * Math.sin(T * 8.3) + 0.005 * Math.sin(T * 13.1 + 1);
    const ground = new THREE.Matrix4().compose(new THREE.Vector3(x, 0, z), new THREE.Quaternion().setFromEuler(new THREE.Euler(0, yaw, 0)), new THREE.Vector3(1, 1, 1));
    const m = ground.clone().multiply(new THREE.Matrix4().makeTranslation(0, bob, 0));
    return { m, ground, bob, yaw, dist: speed * T };
  };
  const camAtT = (T: number): Cam => {
    const { m } = carPose(T);
    const head = new THREE.Vector3(0.004 * Math.sin(T * 1.3), 0.003 * Math.sin(T * 7.9), 0);
    const eye = jeep ? jeep.eye.clone().add(head).applyMatrix4(m) : new THREE.Vector3(0, 1.5, 0);
    const glance = 0.06 * Math.sin(T * 0.7) - 0.1 * (smooth(5.0, 5.4, T) - smooth(5.8, 6.2, T)); // a look down at the lever
    const fwd = new THREE.Vector3(0.05 * Math.sin(T * 0.45), -0.12 + glance, 1).normalize().transformDirection(m);
    const target = eye.clone().addScaledVector(fwd, 10);
    return { pos: eye.toArray() as V3, target: target.toArray() as V3, fov: 70 };
  };
  const cameraAt = (T: number) => makeCamera(camAtT(T));
  const wheelWorld = (T: number) =>
    carPose(T).m.clone().multiply(jeep!.wheelLocal).multiply(new THREE.Matrix4().makeRotationY((steerDeg(T) * Math.PI) / 180));
  const gripAt = (side: "L" | "R") => (T: number) => {
    const W = wheelWorld(T);
    const inv = cameraAt(T).matrixWorldInverse;
    const p = jeep!.grip[side].clone().applyMatrix4(W).applyMatrix4(inv);
    const c = new THREE.Vector3().applyMatrix4(W).applyMatrix4(inv);
    const axis = new THREE.Vector3(0, 1, 0).transformDirection(W).transformDirection(inv); // towards the driver
    const radial = p.clone().sub(c).normalize();
    const palm = axis.clone().multiplyScalar(-0.85).addScaledVector(radial, -0.3).normalize();
    return barGrip(p, palm, radial.clone().addScaledVector(axis, -0.35));
  };

  if (!jeep || !rig) return <AbsoluteFill />;
  const car = carPose(t);
  car.ground.decompose(jeep.root.position, jeep.root.quaternion, jeep.root.scale);
  jeep.body.position.y = jeep.bodyY + car.bob;
  jeep.wheel.position.y = jeep.wheelY + car.bob;
  jeep.wheel.quaternion.copy(jeep.wheelQ).multiply(new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0, 1, 0), (steerDeg(t) * Math.PI) / 180));
  for (const ty of jeep.tyres) {
    ty.o.quaternion.copy(ty.q);
    if (ty.front) ty.o.quaternion.premultiply(new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0, 1, 0), (steerDeg(t) / 16) * (Math.PI / 180)));
    ty.o.quaternion.multiply(new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(1, 0, 0), car.dist / 0.39));
  }
  jeep.root.updateMatrixWorld(true);

  const tracks: { L: HandTrack; R: HandTrack } = {
    R: [
      { t: 0.35, to: gripAt("R"), pose: "wheel", contact: true },
      { t: 5.15, to: [0.12, -0.45, -0.3], pose: "grip", aim: { fingers: [-0.1, -0.75, -0.65], palm: [-0.85, -0.2, 0.3] } }, // down to the gear lever
      { t: 6.05, to: gripAt("R"), pose: "wheel", contact: true },
    ],
    L: [
      { t: 0.8, to: gripAt("L"), pose: "wheel", contact: true },
      { t: 6.6, to: "rest", pose: "relaxed" }, // drives on with one hand
    ],
  };
  const cam = camAtT(t);
  const camera = makeCamera(cam);
  // head angular velocity for the hands' inertia
  const a = cameraAt(t - 1 / 30), b = cameraAt(t + 1 / 30);
  const qd = a.quaternion.clone().invert().multiply(b.quaternion);
  const e = new THREE.Euler().setFromQuaternion(qd, "YXZ");
  rig.pose(t, camera, tracks, { yaw: e.y * 15, pitch: e.x * 15 });

  // debug: red = rim grip points, blue = wrist targets; camFrom = look at the cab from outside (camera-space offset)
  const marks: React.ReactNode[] = [];
  if (debug) {
    const W = wheelWorld(t);
    for (const s of ["L", "R"] as const) {
      const pw = jeep.grip[s].clone().applyMatrix4(W);
      const wr = new THREE.Vector3(...(gripAt(s)(t) as { p: V3 }).p).applyMatrix4(camera.matrixWorld);
      marks.push(<mesh key={"g" + s} position={pw}><sphereGeometry args={[0.012]} /><meshBasicMaterial color="red" /></mesh>);
      marks.push(<mesh key={"w" + s} position={wr}><sphereGeometry args={[0.01]} /><meshBasicMaterial color="blue" /></mesh>);
    }
  }
  const view: Cam = camFrom
    ? { pos: new THREE.Vector3(...camFrom).applyMatrix4(camera.matrixWorld).toArray() as V3, target: new THREE.Vector3(0, -0.25, -0.45).applyMatrix4(camera.matrixWorld).toArray() as V3, fov: 40 }
    : cam;

  return (
    <NkLook t={t}>
      <Stage3D cam={view} lights="none" env={0.55} fog={{ color: "#AEB6BA", near: 25, far: 170 }}>
        <color attach="background" args={["#AEB6BA"]} />
        <OutdoorLights focus={cam.pos} />
        <primitive object={world} />
        <primitive object={jeep.root} />
        <primitive object={rig.root} />
        {marks}
      </Stage3D>
    </NkLook>
  );
};


/** QA overlay: log every floating object once and mark it with a red box */
const useFloatQA = (root: THREE.Object3D | null, on: boolean, label: string) =>
  useMemo(() => {
    if (!on || !root) return null;
    // self-test: a cube floating 1 m up must be caught, a cube standing on the ground must pass
    const probe = new THREE.Group();
    probe.add(root.clone());
    const mk = (y: number, name: string) => {
      const m = new THREE.Mesh(new THREE.BoxGeometry(0.5, 0.5, 0.5), new THREE.MeshBasicMaterial());
      m.position.set(0.3, y, 0.4);
      m.name = name;
      probe.add(m);
    };
    mk(1.25, "probe_floating");
    mk(0.25, "probe_standing");
    const pb = findFloaters(probe).map((b) => b.path);
    const ok = pb.some((x) => x.includes("probe_floating")) && !pb.some((x) => x.includes("probe_standing"));
    console.warn(`FLOATQA ${label} selftest ${ok ? "ok" : "FAILED " + pb.filter((x) => x.includes("probe")).join(" ")}`);
    const bad = findFloaters(root);
    console.warn(`FLOATQA ${label}: ${bad.length} floating`);
    bad.forEach((b) => console.warn(`FLOAT ${label} gap=${b.gap === Infinity ? "nothing below" : b.gap.toFixed(3) + "m"} ${b.what}`));
    const g = new THREE.Group();
    bad.forEach((b) => {
      const m = new THREE.Mesh(new THREE.BoxGeometry(0.3, 0.3, 0.3), new THREE.MeshBasicMaterial({ color: "red", wireframe: true }));
      m.position.copy(b.at);
      g.add(m);
    });
    return g;
  }, [root, on, label]);

// ------------------------------------------------------------------ test: the JSA set (overview or the first-person run to the wall)
export const JsaTest: React.FC<{ view?: "overview" | "run" | "keys"; hands?: boolean; qa?: boolean; keys?: CamKey[] }> = ({ view = "run", hands = true, qa = false, keys: camKeys }) => {
  const { f, fps } = useBlockTime();
  const t = f / fps;
  const tex = useNkTextures();
  const leavesG = useGLB(MODELS + "leaves_kit.glb");
  const flagsG = useGLB(MODELS + "flags.glb");
  const armsG = useGLB("models/fp_arms.glb");
  const rig = useMemo(() => (armsG ? createFPRig(armsG.scene) : null), [armsG]);
  const set = useMemo(() => {
    if (!tex || !leavesG || !flagsG) return null;
    const flagSrc = flagsG.scene.getObjectByName("flag_dprk") as THREE.Mesh | null;
    const flag = flagSrc ? (flagSrc.clone() as THREE.Mesh) : null;
    if (flag) flag.geometry = flag.geometry.clone();
    const tower = flagTower(flag);
    const g = buildJSA(tex, { leafMat: leafMaterialFrom(leavesG.scene), flagTower: tower });
    const pile = leavesG.scene.getObjectByName("leaf_pile")?.clone();
    if (pile) {
      pile.position.copy(JSA_MARKS.collapse).add(new THREE.Vector3(0, 0, 0.1));
      pile.traverse((o) => ((o as THREE.Mesh).receiveShadow = true));
      g.add(pile);
    }
    const waveTower = tower.userData.flag ? prepareFlag(tower.userData.flag as THREE.Mesh) : null;
    return { g, waveTower };
  }, [tex, leavesG, flagsG]);
  const qaMarks = useFloatQA(set?.g ?? null, qa, "jsa");
  if (!set) return <AbsoluteFill />;
  set.waveTower?.(t, 1.4);

  let cam: Cam;
  if (view === "keys" && camKeys) cam = camAt(camKeys, t);
  else if (view === "overview") {
    cam = camAt([{ t: 0, pos: [-34, 16, -34], target: [12, 0, 4], fov: 50 }, { t: 6, pos: [-30, 13, 30], target: [12, 0, 0], fov: 50 }], t);
  } else {
    const pts = JSA_MARKS.run;
    const dur = 3.4;
    const keys: CamKey[] = pts.map(([x, z], i) => {
      const nx = pts[Math.min(i + 1, pts.length - 1)];
      return { t: 0.4 + (i / (pts.length - 1)) * dur, pos: [x, 1.66, z] as V3, target: [nx[0] + (i === pts.length - 1 ? 0 : 0), 1.45, nx[1] + 6] as V3, fov: 72, ease: "linear" };
    });
    const c = headCam(keys, t, { amp: 2.2, fov: 72 });
    // a glance left at the conference huts while running, then back to the wall
    const glance = 0.62 * (smooth(1.0, 1.45, t) - smooth(1.75, 2.2, t));
    const d = new THREE.Vector3(c.target[0] - c.pos[0], c.target[1] - c.pos[1], c.target[2] - c.pos[2]).applyAxisAngle(new THREE.Vector3(0, 1, 0), glance);
    cam = { ...c, target: [c.pos[0] + d.x, c.pos[1] + d.y, c.pos[2] + d.z] };
  }
  const camera = makeCamera(cam);
  const pump = (s: "L" | "R"): HandTrack => [
    { t: 0.2, to: [s === "L" ? -0.16 : 0.16, -0.43, -0.3], pose: "fist", aim: { fingers: [s === "L" ? 0.35 : -0.35, 0.55, -0.75], palm: [s === "L" ? 0.85 : -0.85, -0.1, 0.2] }, osc: { hz: 1.45, amp: [0.025, 0.11, 0.13], phase: s === "L" ? 0 : Math.PI } },
  ];
  if (rig && hands && view === "run") rig.pose(t, camera, { L: pump("L"), R: pump("R") });

  return (
    <NkLook t={t}>
      <Stage3D cam={cam} lights="none" env={0.5} fog={{ color: "#B3BABD", near: 30, far: 300 }}>
        <color attach="background" args={["#B3BABD"]} />
        <OutdoorLights focus={cam.pos} sun={[-26, 34, -14]} />
        <primitive object={set.g} />
        {qaMarks ? <primitive object={qaMarks} /> : null}
        {rig && hands && view === "run" ? <primitive object={rig.root} /> : null}
      </Stage3D>
    </NkLook>
  );
};

const CUP_HALF = 0.0435; // the aluminium cup is 8.5 cm tall, origin at the bottom centre

// ------------------------------------------------------------------ test: barracks — one hand takes the cup, drinks, puts it back
export const BarracksTest: React.FC<{ hands?: boolean; qa?: boolean }> = ({ hands = true, qa = false }) => {
  const { f, fps } = useBlockTime();
  const t = f / fps;
  const tex = useNkTextures();
  const cupG = useGLB(MODELS + "cup_aluminium.glb");
  const armsG = useGLB("models/fp_arms.glb");
  const rig = useMemo(() => (armsG ? createFPRig(armsG.scene) : null), [armsG]);
  const set = useMemo(() => {
    if (!tex || !cupG) return null;
    const room = buildBarracks(tex, null);
    const cup = cupG.scene.clone(true);
    cup.traverse((o) => {
      const m = o as THREE.Mesh;
      if (m.isMesh) {
        m.castShadow = true;
        m.receiveShadow = true;
      }
    });
    const bulb = new THREE.PointLight("#FFD9A0", 2.2, 9, 1.6);
    bulb.position.set(0, 2.32, -0.2);
    bulb.castShadow = true;
    bulb.shadow.mapSize.set(1024, 1024);
    room.add(bulb);
    return { room, cup };
  }, [tex, cupG]);
  const qaRoot = useMemo(() => {
    if (!set) return null;
    const g = new THREE.Group();
    g.add(set.room.clone());
    const c = set.cup.clone();
    c.position.copy(BARRACKS_MARKS.cup);
    g.add(c);
    return g;
  }, [set]);
  const qaMarks = useFloatQA(qaRoot, qa, "barracks");
  if (!set) return <AbsoluteFill />;

  const keys: CamKey[] = [
    { t: 0, pos: BARRACKS_MARKS.eye.toArray() as V3, target: [0.05, 0.62, -1.4], fov: 72 },
    { t: 1.2, pos: BARRACKS_MARKS.eye.toArray() as V3, target: [0.12, 0.7, -1.3], fov: 72 },
    { t: 2.4, pos: [0, 1.2, 0.63], target: [0.02, 1.15, -1.2], fov: 72 }, // head up while drinking
    { t: 3.6, pos: BARRACKS_MARKS.eye.toArray() as V3, target: [0.08, 0.66, -1.4], fov: 72 },
    { t: 6, pos: BARRACKS_MARKS.eye.toArray() as V3, target: [-0.2, 0.9, -1.4], fov: 72 },
  ];
  const camAtT = (T: number) => headCam(keys, T, { amp: 0.6, fov: 72 });
  const cam = camAtT(t);
  const camera = makeCamera(cam);
  const cupHome = BARRACKS_MARKS.cup.clone();
  // wrist target for grabbing the cup from its right side, in camera space of time T
  const grabCup = (T: number) => {
    const inv = makeCamera(camAtT(T)).matrixWorldInverse;
    const c = cupHome.clone().add(new THREE.Vector3(0, CUP_HALF, 0)).applyMatrix4(inv); // the cup's middle
    const fingers = new THREE.Vector3(-0.25, -0.05, -1).normalize();
    const palm = new THREE.Vector3(-1, 0, 0.1).normalize();
    const p = c.clone().addScaledVector(fingers, -0.078).addScaledVector(palm, -0.034); // wrist so the grasp centre lands on it
    return { p: p.toArray() as V3, aim: { fingers: fingers.toArray() as V3, palm: palm.toArray() as V3 } };
  };
  const R: HandTrack = [
    { t: 0.5, to: grabCup, pose: "cup", contact: true },
    { t: 1.75, to: [0.06, -0.16, -0.22], pose: "cup", contact: true, aim: { fingers: [-0.55, 0.1, -0.8], palm: [-0.95, 0.05, 0.3] } },
    { t: 2.35, to: [0.04, -0.12, -0.17], pose: "cup", contact: true, dur: 0.5, aim: { fingers: [-0.5, 0.45, -0.7], palm: [-0.95, 0.15, 0.25] } },
    { t: 3.15, to: grabCup, pose: "cup", contact: true },
    { t: 4.35, to: "rest", pose: "relaxed" },
  ];
  if (rig && hands) rig.pose(t, camera, { R });
  // the cup leaves the table when the fingers close (~1.15 s) and lands again at ~4.15 s; short blends, no pop
  set.cup.position.copy(cupHome);
  set.cup.quaternion.identity();
  const w = rig && hands ? smooth(1.05, 1.3, t) * (1 - smooth(4.0, 4.25, t)) : 0;
  if (w > 0) {
    const held = set.cup.clone();
    rig!.holdInHand("R", held, { halfHeight: CUP_HALF });
    set.cup.position.lerp(held.position, w);
    set.cup.quaternion.slerp(held.quaternion, w);
  }

  return (
    <NkLook t={t} vignette={0.42}>
      <Stage3D cam={cam} lights="none" env={0.35} exposure={1.05}>
        <color attach="background" args={["#DCE3E6"]} />
        <OutdoorLights focus={[0, 1, 0]} sun={[-9, 6, -3]} intensity={2.6} warm="#FFF6E8" />
        <primitive object={set.room} />
        <primitive object={set.cup} />
        {qaMarks ? <primitive object={qaMarks} /> : null}
        {rig && hands ? <primitive object={rig.root} /> : null}
      </Stage3D>
    </NkLook>
  );
};

// ------------------------------------------------------------------ test: soldiers (pose gallery)
type Cast = { s: ReturnType<typeof createSoldier>; rifle: THREE.Group };
export const SoldiersTest: React.FC<{ view?: "gallery" }> = () => {
  const { f, fps } = useBlockTime();
  const t = f / fps;
  const tex = useNkTextures();
  const kpaG = useGLB(MODELS + "soldier_kpa.glb");
  const rokG = useGLB(MODELS + "soldier_rok.glb");
  const leavesG = useGLB(MODELS + "leaves_kit.glb");
  const cast = useMemo(() => {
    if (!kpaG || !rokG || !tex || !leavesG) return null;
    const set = buildJSA(tex, { leafMat: leafMaterialFrom(leavesG.scene) });
    const mk = (g: GLTF, n: number): Cast[] => Array.from({ length: n }, () => ({ s: createSoldier(g.scene), rifle: makeRifle() }));
    return { set, kpa: mk(kpaG, 4), rok: mk(rokG, 2) };
  }, [kpaG, rokG, tex, leavesG]);
  if (!cast) return <AbsoluteFill />;
  const objs: THREE.Object3D[] = [];
  const x0 = -6, z0 = 22, yaw = Math.PI; // facing the camera (-Z)
  // 0: standing with the rifle at port arms
  {
    const who = cast.kpa[0], x = x0;
    const base = { pos: [x, 0, z0] as V3, yaw, feet: { L: [x + 0.12, 0, z0] as V3, R: [x - 0.12, 0, z0] as V3 }, hands: {} };
    who.s.pose(base);
    who.s.pose({ ...base, hands: carryRifle(who.s, who.rifle, yaw), curl: { L: 0.8, R: 0.85 } });
    objs.push(who.s.root, who.rifle);
  }
  // 1-2: running, two moments of the stride (gait from a path towards the camera)
  for (const [k, tt] of [[1, 0.9], [2, 1.05]] as [number, number][]) {
    const who = cast.kpa[k], x = x0 + 1.4 * k;
    const keys: PathKey[] = [{ t: 0, p: [x, z0 + 6] }, { t: 1.6, p: [x, z0] }, { t: 3.2, p: [x, z0 - 6] }];
    const gt = gait(keys, tt, { stride: 2.6 });
    const pz = keys[0].p[1] + ((keys[2].p[1] - keys[0].p[1]) * tt) / 3.2;
    const base = { pos: [x, gt.bob, pz] as V3, yaw, lean: 0.22, feet: gt.feet, hands: {} };
    who.s.pose(base);
    who.s.pose({ ...base, hands: carryRifle(who.s, who.rifle, yaw, Math.sin(gt.phase * Math.PI * 2)), curl: { L: 0.8, R: 0.85 } });
    objs.push(who.s.root, who.rifle);
  }
  // 3: aiming, left foot forward
  {
    const who = cast.kpa[3], x = x0 + 4.2;
    const tgt = new THREE.Vector3(x, 1.4, z0 - 20);
    const base = { pos: [x, 0, z0] as V3, yaw, lean: 0.08, feet: { L: [x + 0.14, 0, z0 - 0.18] as V3, R: [x - 0.16, 0, z0 + 0.12] as V3 }, hands: {}, look: tgt.toArray() as V3 };
    who.s.pose(base);
    who.s.pose({ ...base, hands: aimRifle(who.s, who.rifle, tgt), curl: { L: 0.75, R: 0.85 } });
    objs.push(who.s.root, who.rifle);
  }
  // 4: prone (one crawl moment), 5: standing ROK soldier, arms down
  {
    const who = cast.rok[0], x = x0 + 5.8;
    who.s.pose({ pos: [x, 0, z0], yaw, bodyPitch: Math.PI / 2, pelvis: 0.2, feet: { L: [x + 0.25, 0, z0 + 0.95], R: [x - 0.15, 0, z0 + 1.0] }, hands: { L: { p: [x + 0.3, 0.05, z0 - 0.75] }, R: { p: [x - 0.28, 0.05, z0 - 0.45] } }, look: [x, 0.3, z0 - 5], knee: { L: [1, 0, 0], R: [-1, 0, 0] } });
    objs.push(who.s.root);
    const w2 = cast.rok[1], x2 = x0 + 7.6;
    w2.s.pose({ pos: [x2, 0, z0], yaw, feet: { L: [x2 + 0.12, 0, z0], R: [x2 - 0.12, 0, z0] }, hands: { L: { p: [x2 + 0.3, 0.86, z0 + 0.02] }, R: { p: [x2 - 0.3, 0.86, z0 + 0.02] } }, curl: { L: 0.3, R: 0.3 } });
    objs.push(w2.s.root);
  }
  const cam: Cam = { pos: [x0 + 3.8, 1.5, z0 - 8.5], target: [x0 + 3.8, 0.85, z0], fov: 46 };
  return (
    <NkLook t={t}>
      <Stage3D cam={cam} lights="none" env={0.5} fog={{ color: "#B3BABD", near: 30, far: 300 }}>
        <color attach="background" args={["#B3BABD"]} />
        <OutdoorLights focus={cam.target} sun={[-26, 34, -14]} />
        <primitive object={cast.set} />
        {objs.map((o, i) => (
          <primitive key={i} object={o} />
        ))}
      </Stage3D>
    </NkLook>
  );
};

// ------------------------------------------------------------------ Mixamo soldiers: gallery + the chase at the MDL
export const useClipMeta = () => {
  const [meta, setMeta] = useState<Record<string, ClipMeta> | null>(null);
  const [handle] = useState(() => delayRender("soldier clips", { timeoutInMilliseconds: 60000 }));
  useEffect(() => {
    fetch(staticFile(MODELS + "soldier_mx_clips.json"))
      .then((r) => r.json())
      .then((m) => {
        setMeta(m);
        continueRender(handle);
      })
      .catch((e) => {
        console.error(e);
        continueRender(handle);
      });
  }, [handle]);
  return meta;
};

type Actor = { side: "kpa" | "rok"; prog: Program; rifle?: boolean };
/** feet QA: over the whole shot no foot may sink below the ground, and a standing soldier may not hover */
const feetQA = (s: ReturnType<typeof createMxSoldier>, prog: Program, label: string, t0: number, t1: number, airborneOk: boolean) => {
  let sink = 0, hover = 0;
  for (let t = t0; t <= t1; t += 1 / 15) {
    s.pose(prog, t);
    const y = s.footY();
    sink = Math.min(sink, y);
    if (!airborneOk) hover = Math.max(hover, y);
  }
  const bad = sink < -0.03 || (!airborneOk && hover > 0.16);
  console.warn(`FEETQA ${label} ${bad ? "BAD" : "ok"} lowest=${sink.toFixed(3)} highest-standing=${hover.toFixed(3)}`);
};

export const MxTest: React.FC<{ view?: "gallery" | "chase"; qa?: boolean; focus?: number; at?: number; side?: boolean; solo?: boolean }> = ({ view = "gallery", qa = false, focus, at: atT, side, solo }) => {
  const { f, fps } = useBlockTime();
  const t = f / fps;
  const tex = useNkTextures();
  const kpaG = useGLB(MODELS + "soldier_mx_kpa.glb");
  const rokG = useGLB(MODELS + "soldier_mx_rok.glb");
  const leavesG = useGLB(MODELS + "leaves_kit.glb");
  const meta = useClipMeta();
  const actors: Actor[] = useMemo(() => {
    if (view === "gallery") {
      const row = ["rifle_run", "run_to_stop", "fire", "aim_idle", "rifle_idle", "yell", "crawl", "pull", "pull_low", "kneel", "run_turn"];
      return row.map((clip, i) => ({ side: i < 6 || clip === "run_turn" ? "kpa" : "rok", prog: { start: [-3.3 + (i % 4) * 2.2, 0, 19 + Math.floor(i / 4) * 2.8 + (clip.includes("run") ? 2.5 : 0)] as V3, yaw: Math.PI, segs: [{ clip, at: 0 }] } }));
    }
    // the chase: four KPA guards come from the north towards the line; the defector runs away south-west
    const runner = (x: number, z: number, stopAt: number, aimYaw: number, delay: number): Actor => ({
      side: "kpa",
      prog: { start: [x, 0, z], yaw: 0.12, segs: [{ clip: "rifle_idle", at: 0 }, { clip: "rifle_run", at: delay, fade: 0.25 }, { clip: "run_to_stop", at: stopAt, fade: 0.2 }, { clip: "fire", at: stopAt + 0.8, fade: 0.3, yaw: aimYaw }] },
    });
    return [
      runner(-18.5, -22, 2.6, 0.32, 0.2),
      runner(-15.5, -24, 2.9, 0.2, 0.35),
      runner(-21.0, -25, 3.2, 0.4, 0.5),
      // the one who crosses the line, turns and runs back
      { side: "kpa", prog: { start: [-13.6, 0, -21], yaw: 0.05, segs: [{ clip: "rifle_idle", at: 0 }, { clip: "rifle_run", at: 0.25, fade: 0.25 }, { clip: "run_turn", at: 3.6, fade: 0.2 }, { clip: "rifle_run", at: 5.85, fade: 0.25 }] } },
    ];
  }, [view]);
  const cast = useMemo(() => {
    if (!kpaG || !rokG || !tex || !leavesG || !meta) return null;
    const set = buildJSA(tex, { leafMat: leafMaterialFrom(leavesG.scene) });
    const list = actors.map((a) => ({ a, s: createMxSoldier(a.side === "kpa" ? kpaG : rokG, meta), rifle: makeRifle() }));
    if (qa) list.forEach(({ a, s }, i) => feetQA(s, a.prog, `${view}#${i}:${a.prog.segs.map((x) => x.clip).join(">")}`, 0, view === "gallery" ? 3 : 7, false));
    return { set, list };
  }, [kpaG, rokG, tex, leavesG, meta, actors, qa, view]);
  if (!cast) return <AbsoluteFill />;
  const objs: THREE.Object3D[] = [];
  const tt = atT ?? t;
  let focusAt: THREE.Vector3 | null = null;
  for (const [k, { a, s, rifle }] of cast.list.entries()) {
    if (solo && focus !== undefined && k !== focus) continue;
    const r = s.pose(a.prog, tt);
    if (focus === k) focusAt = new THREE.Vector3(r.x, 0, r.z);
    objs.push(s.root);
    if (r.rifle) {
      const clipNow = (() => {
        const segs = a.prog.segs;
        let k = segs.length - 1;
        while (k > 0 && tt < segs[k].at) k--;
        return segs[k];
      })();
      const aiming = clipNow.clip === "fire" || clipNow.clip === "aim_idle";
      const shotPhase = clipNow.clip === "fire" ? ((tt - clipNow.at) % 0.27) / 0.27 : 1;
      s.holdRifle(rifle, { shoulder: aiming, recoil: clipNow.clip === "fire" ? Math.max(0, 1 - shotPhase * 4) : 0 });
      objs.push(rifle);
    }
  }
  const cam: Cam = focusAt
    ? side ? { pos: [focusAt.x + 3.4, 1.4, focusAt.z - 0.2], target: [focusAt.x, 1.1, focusAt.z - 0.2], fov: 45 } : { pos: [focusAt.x + 1.2, 1.5, focusAt.z - 3.4], target: [focusAt.x, 1.05, focusAt.z], fov: 45 }
    : view === "gallery"
      ? { pos: [0, 2.9, 10.5], target: [0, 0.8, 22], fov: 62 }
      : headCam([{ t: 0, pos: [-11.6, 0.35, 14.0], target: [-15, 1.6, -12], fov: 60 }, { t: 8, pos: [-11.6, 0.35, 14.0], target: [-15.5, 1.7, -12], fov: 60 }], t, { amp: 0.6, fov: 60 }); // lying by the wall, looking back
  return (
    <NkLook t={t}>
      <Stage3D cam={cam} lights="none" env={0.5} fog={{ color: "#B3BABD", near: 30, far: 300 }}>
        <color attach="background" args={["#B3BABD"]} />
        <OutdoorLights focus={view === "gallery" ? [-1, 0, 20] : [-15, 0, -8]} sun={[-26, 34, -14]} />
        <primitive object={cast.set} />
        {objs.map((o, i) => (
          <primitive key={i} object={o} />
        ))}
      </Stage3D>
    </NkLook>
  );
};

export const smooth01 = (x: number) => {
  const u = Math.min(1, Math.max(0, x));
  return u * u * (3 - 2 * u);
};

// ------------------------------------------------------------------ test: the rescue, seen by the defector lying on his back
export const RescueTest: React.FC<{ qa?: boolean; from?: "eyes" | "side"; offset?: number; rate?: number }> = ({ qa = false, from = "eyes", offset = 0, rate = 1 }) => {
  const { f, fps } = useBlockTime();
  const t = offset + (f / fps) * rate; // offset/rate: show a part of the rescue, a bit faster, inside a reel shot
  const tex = useNkTextures();
  const rokG = useGLB(MODELS + "soldier_mx_rok.glb");
  const leavesG = useGLB(MODELS + "leaves_kit.glb");
  const meta = useClipMeta();
  // the defector: head at the collapse spot, lying along X with his head to the east (towards the rescuers)
  const head0 = JSA_MARKS.collapse.clone().add(new THREE.Vector3(0.35, 0, 0.25));
  const T_PULL = 4.3;
  const cast = useMemo(() => {
    if (!rokG || !tex || !leavesG || !meta) return null;
    const set = buildJSA(tex, { leafMat: leafMaterialFrom(leavesG.scene) });
    const pile = leavesG.scene.getObjectByName("leaf_pile")?.clone();
    if (pile) {
      pile.position.copy(JSA_MARKS.collapse).add(new THREE.Vector3(-0.75, 0, 0)); // under his body, not his face
      pile.scale.set(0.8, 0.55, 0.8);
      set.add(pile);
    }
    const west = -Math.PI / 2; // facing -X (towards the defector)
    // two pullers (one at each shoulder) + one kneeling cover man
    // each one comes in from a side, turned ~25 degrees towards his head: knees and feet stay beside the head, hands reach in
    const mkPuller = (dz: number): Program => ({
      // wall side (dz<0): straight in along the wall, never across it; open side: angled in from the south-east
      start: [head0.x + 2.1, 0, head0.z + dz], yaw: west + (dz < 0 ? 0 : -0.6),
      segs: [{ clip: "crawl", at: 0, rate: 1.6 }, { clip: "kneel", at: 3.4, fade: 0.6 }, { clip: "pull_low", at: T_PULL, fade: 0.5, shift: [0, 0.82] }], // crawls to ~1 m, kneels there, lunges in as he grabs the vest
    });
    const progs = [mkPuller(-0.3), mkPuller(0.62)];
    const list = progs.map((p) => ({ s: createMxSoldier(rokG, meta), prog: p }));
    // shift each puller so that at the first pulling frame his hands are right on the defector's shoulder
    list.forEach(({ s, prog }, i) => {
      s.pose(prog, T_PULL + 0.5);
      const hands = s.bones.lHand.getWorldPosition(new THREE.Vector3()).add(s.bones.rHand.getWorldPosition(new THREE.Vector3())).multiplyScalar(0.5);
      const shoulder = head0.clone().add(new THREE.Vector3(0.04, 0, i === 0 ? -0.31 : 0.26)); // vest straps at the collar line
      prog.start = [prog.start[0] + (shoulder.x - hands.x), 0, prog.start[2] + (shoulder.z - hands.z)];
    });
    const cover = { s: createMxSoldier(rokG, meta), prog: { start: [head0.x + 2.6, 0, head0.z + 1.6] as V3, yaw: -2.2, segs: [{ clip: "kneel", at: 0 }] } };
    list.push(cover);
    if (qa) {
      list.forEach(({ s, prog }, i) => feetQA(s, prog, `rescue#${i}:${prog.segs.map((x) => x.clip).join(">")}`, 0, 8, true));
      // camera clearance: the defector's eyes vs every soldier's joints (head, spine, hands, feet)
      let worst = 9, when = 0;
      for (let tt = 0; tt <= 8; tt += 0.1) {
        list.forEach(({ s, prog }) => s.pose(prog, tt));
        const p0x = list[0];
        const now = p0x.s.pose(p0x.prog, tt), then = p0x.s.pose(p0x.prog, T_PULL + 0.25);
        p0x.s.pose(p0x.prog, tt);
        const trav = tt > T_PULL + 0.25 ? new THREE.Vector3(now.x - then.x, 0, now.z - then.z) : new THREE.Vector3();
        const eye = head0.clone().add(trav).add(new THREE.Vector3(-0.08, 0.2, 0));
        for (const { s } of list)
          s.model.traverse((o) => {
            if (!(o as THREE.Bone).isBone) return;
            const d = o.getWorldPosition(new THREE.Vector3()).distanceTo(eye);
            if (d < worst) {
              worst = d;
              when = tt;
              (globalThis as { __worstJoint?: string }).__worstJoint = o.name;
            }
          });
      }
      const solids = solidBoxes(set);
      list.forEach(({ s, prog }, i) => {
        let first: string | null = null;
        for (let tt = 0; tt <= 8 && !first; tt += 0.1) {
          s.pose(prog, tt);
          const h = jointInside(s.root, solids);
          if (h) first = `t=${tt.toFixed(1)} ${h.joint} in ${h.solid}`;
        }
        console.warn(`BODYQA rescue#${i} ${first ? "BAD " + first : "ok"}`);
      });
      // self-test: a soldier crawling straight through the low wall must be caught
      {
        const probe = createMxSoldier(rokG, meta);
        const prog: Program = { start: [JSA_MARKS.wall.x, 0, JSA_MARKS.wall.z - 1.6], yaw: 0, segs: [{ clip: "crawl", at: 0, rate: 1.6 }] };
        let caught = false;
        for (let tt = 0; tt <= 8 && !caught; tt += 0.1) {
          probe.pose(prog, tt);
          caught = !!jointInside(probe.root, solids);
        }
        console.warn(`BODYQA selftest ${caught ? "ok" : "FAILED (a crawl through the wall was not caught)"}`);
      }
      console.warn(`CAMQA rescue ${worst < 0.25 ? "BAD" : "ok"} closest joint ${worst.toFixed(2)} m at ${when.toFixed(1)} s (${(globalThis as { __worstJoint?: string }).__worstJoint})`);
      for (const tt of [0, 0.8, 1.6, 2.4, 3.2, 3.6, 4.0, 4.4, 5.0, 6.5]) {
        const { s, prog } = list[0];
        const r = s.pose(prog, tt);
        const h = s.bones.lHand.getWorldPosition(new THREE.Vector3());
        const hd = s.bones.head.getWorldPosition(new THREE.Vector3());
        console.warn(`CAMTAB t=${tt.toFixed(1)} root dx=${(r.x - head0.x).toFixed(2)} dz=${(r.z - head0.z).toFixed(2)} | hand dx=${(h.x - head0.x).toFixed(2)} y=${h.y.toFixed(2)} dz=${(h.z - head0.z).toFixed(2)} | head dx=${(hd.x - head0.x).toFixed(2)} y=${hd.y.toFixed(2)}`);
      }
    }
    return { set, list };
  }, [rokG, tex, leavesG, meta, qa]);
  if (!cast || !meta) return <AbsoluteFill />;
  const objs: THREE.Object3D[] = [cast.set];
  for (const { s, prog } of cast.list) {
    s.pose(prog, t);
    objs.push(s.root);
  }
  // the defector is dragged with the pullers: his head follows their travel since the pull began
  const p0 = cast.list[0];
  const travel = (() => {
    if (t <= T_PULL) return new THREE.Vector3();
    const now = p0.s.pose(p0.prog, t), then = p0.s.pose(p0.prog, T_PULL + 0.25);
    p0.s.pose(p0.prog, t);
    return new THREE.Vector3(now.x - then.x, 0, now.z - then.z).multiplyScalar(t > T_PULL + 0.25 ? 1 : 0);
  })();
  const head = head0.clone().add(travel);
  const drag = t > T_PULL + 0.25 ? 1 : 0;
  const jolt = drag * (Math.abs(Math.sin(t * 5.6)) * 0.03 + Math.sin(t * 13) * 0.008);
  // lying on his back: eyes 0.2 m above the ground, looking up and back over his head (towards the rescuers)
  // his gaze: along the ground at the men crawling in, then up at them as they lean over him and pull
  const eyesAt = (h: THREE.Vector3, j: number, tt: number): Cam => {
    const up = smooth01((tt - 3.9) / 1.2);
    const tx = 3.0 - 1.7 * up, ty = 0.5 + 1.6 * up;
    const tz = -1.1 * (1 - up) - 0.35 * up; // first at the man crawling in from the left, then up at the nearer one
    return {
      pos: [h.x - 0.08, 0.2 + j, h.z],
      target: [h.x + tx, ty + j * 2, h.z + tz + 0.15 * Math.sin(tt * 0.6)],
      fov: 76,
      roll: 0.05 * Math.sin(tt * 1.3),
    };
  };
  const cam: Cam = from === "side" ? { pos: [head0.x - 3.2, 1.9, head0.z + 4.2], target: [head0.x + 0.9, 0.4, head0.z], fov: 50 } : eyesAt(head, jolt, t);
  return (
    <NkLook t={t} vignette={0.5}>
      <Stage3D cam={cam} lights="none" env={0.5} fog={{ color: "#B3BABD", near: 30, far: 300 }}>
        <color attach="background" args={["#B3BABD"]} />
        <OutdoorLights focus={[head0.x, 0, head0.z]} sun={[-26, 34, -14]} />
        {objs.map((o, i) => (
          <primitive key={i} object={o} />
        ))}
      </Stage3D>
    </NkLook>
  );
};
