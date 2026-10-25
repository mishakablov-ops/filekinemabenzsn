/**
 * Procedural sets for the "podezd" horror reel: a 1960s five-storey Khrushchyovka stairwell (real sizes), the concierge
 * booth with a hidden door, the stair that goes six flights down, and the room at the bottom.
 * Textures: projects/podezd/tex/<name>.jpg + <name>_n.png (assets/models-src/podezd/textures/gen_textures.py).
 *
 * Stairwell frame (metres, +Y up): x across the shaft (-1.25 .. 1.25), z from the apartment wall (0) to the outer wall (5.3).
 *   floor landing  z 0 .. 1.5   at y = FLOOR(n)            doors on the three walls
 *   flight A       z 1.5 .. 3.74, x 0.15 .. 1.25           floor n -> half landing (y + 1.4)
 *   half landing   z 3.74 .. 5.3 at y = FLOOR(n) + 1.4     window in the outer wall
 *   flight B       z 3.74 .. 1.5, x -1.25 .. -0.15         half landing -> floor n + 1
 * The lobby is the half landing below floor 1 (y -1.4): entrance door, mailboxes, the booth behind the right wall.
 */
import * as THREE from "three";
import { mergeGeometries } from "three/examples/jsm/utils/BufferGeometryUtils.js";

export type Tex = Record<string, THREE.Texture>;
export const PZ_TEX = ["wall_green", "whitewash", "terrazzo", "metlakh", "brick_white", "leatherette", "parquet", "wallpaper", "concrete_damp", "metal_paint", "wood_dark", "tiles_blue", "carpet", "concrete"];

export const FLOOR_H = 2.8;
export const RISE = 1.4;
export const STEPS = 9;
export const TREAD = 0.28;
export const RUN = (STEPS - 1) * TREAD; // 2.24
export const SH = { x0: -1.25, x1: 1.25, zLand: 1.5, zHalf: 1.5 + RUN, z1: 5.3, gap: 0.15, wall: 0.25 };
export const FLOOR = (n: number) => (n - 1) * FLOOR_H;
export const LOBBY_Y = -RISE;
export const BOOTH = { x0: 1.25, x1: 3.75, z0: 1.6, z1: 5.3, y: LOBBY_Y, h: 2.45 };
export const DESCENT = { x0: 3.75, x1: 5.05, z0: 1.0, z1: 4.3, flights: 6, w: 0.95 };

// ------------------------------------------------------------------ small helpers
function uvBox(w: number, h: number, d: number, tile = 1.5) {
  const g = new THREE.BoxGeometry(w, h, d);
  const uv = g.attributes.uv as THREE.BufferAttribute;
  const dims: [number, number][] = [[d, h], [d, h], [w, d], [w, d], [w, h], [w, h]];
  for (let f = 0; f < 6; f++)
    for (let i = 0; i < 4; i++) {
      const k = f * 4 + i;
      uv.setXY(k, (uv.getX(k) * dims[f][0]) / tile, (uv.getY(k) * dims[f][1]) / tile);
    }
  return g;
}
const at = (g: THREE.BufferGeometry, x: number, y: number, z: number, ry = 0, rx = 0, rz = 0) => {
  const m = new THREE.Matrix4().compose(new THREE.Vector3(x, y, z), new THREE.Quaternion().setFromEuler(new THREE.Euler(rx, ry, rz)), new THREE.Vector3(1, 1, 1));
  return g.clone().applyMatrix4(m);
};
function mk(g: THREE.BufferGeometry, m: THREE.Material, cast = true) {
  const o = new THREE.Mesh(g, m);
  o.castShadow = cast;
  o.receiveShadow = true;
  return o;
}
export function texMat(tex: Tex, name: string | null, o: { color?: string; rough?: number; metal?: number; normal?: number; emissive?: string } = {}) {
  const m = new THREE.MeshStandardMaterial({
    map: name ? tex[name] ?? null : null,
    normalMap: name ? tex[name + "_n"] ?? null : null,
    color: o.color ?? "#ffffff",
    roughness: o.rough ?? 0.9,
    metalness: o.metal ?? 0,
  });
  if (o.emissive) m.emissive = new THREE.Color(o.emissive);
  if (m.normalMap) m.normalScale.set(o.normal ?? 0.8, o.normal ?? 0.8);
  return m;
}
/** flat wall in the XY plane facing +Z, with rectangular openings; UVs in metres / tile */
function wallShape(w: number, h: number, holes: [number, number, number, number][], tile = 1.5) {
  const s = new THREE.Shape([new THREE.Vector2(0, 0), new THREE.Vector2(w, 0), new THREE.Vector2(w, h), new THREE.Vector2(0, h)]);
  for (const [x, y, hw, hh] of holes) s.holes.push(new THREE.Path([new THREE.Vector2(x, y), new THREE.Vector2(x, y + hh), new THREE.Vector2(x + hw, y + hh), new THREE.Vector2(x + hw, y)]));
  const g = new THREE.ShapeGeometry(s);
  const uv = g.attributes.uv as THREE.BufferAttribute;
  for (let i = 0; i < uv.count; i++) uv.setXY(i, uv.getX(i) / tile, uv.getY(i) / tile);
  return g;
}

/**
 * Two-tone stairwell paint: glossy olive oil paint below, whitewash above, with a thin dark stripe between.
 * The paint line follows the floor under the wall point (landings, flights), like in a real stairwell.
 * profile: 0 floor landings (apartment wall), 1 half landings (outer wall), 2 flight A side, 3 flight B side, 4 flat at `base`.
 */
export function paintMat(tex: Tex, profile: number, base = 0, line = 1.5) {
  const m = texMat(tex, "wall_green", { rough: 0.45, normal: 0.7 });
  m.onBeforeCompile = (sh) => {
    sh.uniforms.uWhite = { value: tex.whitewash };
    sh.uniforms.uProfile = { value: profile };
    sh.uniforms.uBase = { value: base };
    sh.uniforms.uLine = { value: line };
    sh.vertexShader = sh.vertexShader
      .replace("#include <common>", "#include <common>\nvarying vec3 vWPos;")
      .replace("#include <begin_vertex>", "#include <begin_vertex>\nvWPos = (modelMatrix * vec4(transformed, 1.0)).xyz;");
    sh.fragmentShader = sh.fragmentShader
      .replace(
        "#include <common>",
        `#include <common>
varying vec3 vWPos;
uniform sampler2D uWhite; uniform int uProfile; uniform float uBase; uniform float uLine;
float pzFloor(vec3 p) {
  float h0 = uBase;
  if (uProfile == 0) h0 = 0.0;
  else if (uProfile == 1) h0 = ${RISE.toFixed(3)};
  else if (uProfile == 2) h0 = clamp((p.z - ${SH.zLand.toFixed(3)}) / ${RUN.toFixed(3)}, 0.0, 1.0) * ${RISE.toFixed(3)};
  else if (uProfile == 3) h0 = ${RISE.toFixed(3)} + clamp((${SH.zHalf.toFixed(3)} - p.z) / ${RUN.toFixed(3)}, 0.0, 1.0) * ${RISE.toFixed(3)};
  if (uProfile == 4) return uBase;
  return h0 + floor((p.y - h0) / ${FLOOR_H.toFixed(3)}) * ${FLOOR_H.toFixed(3)};
}
float pzWhite() { return step(uLine + 0.02, vWPos.y - pzFloor(vWPos)); }`,
      )
      .replace(
        "#include <map_fragment>",
        `#ifdef USE_MAP
  float hh = vWPos.y - pzFloor(vWPos);
  vec4 cg = texture2D(map, vMapUv);
  vec4 cw = texture2D(uWhite, vMapUv * 0.85);
  float wsel = step(uLine + 0.02, hh);
  float stripe = step(uLine, hh) * (1.0 - wsel);
  vec4 c = mix(cg, cw, wsel);
  c.rgb = mix(c.rgb, vec3(0.16, 0.10, 0.08), stripe);
  diffuseColor *= c;
#endif`,
      )
      .replace("#include <roughnessmap_fragment>", "#include <roughnessmap_fragment>\nroughnessFactor = mix(roughnessFactor, 0.95, pzWhite());");
  };
  m.customProgramCacheKey = () => "pzpaint" + profile + "_" + base + "_" + line;
  return m;
}

/** a printed / painted label as a canvas texture */
export function labelTex(text: string, o: { w?: number; h?: number; bg?: string; fg?: string; font?: string; chalk?: boolean; rot?: number } = {}) {
  const c = document.createElement("canvas");
  c.width = o.w ?? 256;
  c.height = o.h ?? 128;
  const g = c.getContext("2d")!;
  if (o.bg) {
    g.fillStyle = o.bg;
    g.fillRect(0, 0, c.width, c.height);
  }
  g.translate(c.width / 2, c.height / 2);
  g.rotate(o.rot ?? 0);
  g.fillStyle = o.fg ?? "#111";
  g.font = o.font ?? "bold 72px Arial";
  g.textAlign = "center";
  g.textBaseline = "middle";
  if (o.chalk) {
    // chalk: many jittered thin passes
    g.globalAlpha = 0.18;
    for (let i = 0; i < 14; i++) g.fillText(text, (Math.random() - 0.5) * 3, (Math.random() - 0.5) * 3);
    g.globalAlpha = 1;
    g.globalCompositeOperation = "destination-out";
    for (let i = 0; i < 900; i++) g.fillRect(Math.random() * c.width - c.width / 2, Math.random() * c.height - c.height / 2, 2, 2);
  } else g.fillText(text, 0, 0);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  t.anisotropy = 8;
  return t;
}
function decal(tex: THREE.Texture, w: number, h: number, opacity = 1) {
  const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshStandardMaterial({ map: tex, transparent: true, opacity, roughness: 0.95, depthWrite: false, polygonOffset: true, polygonOffsetFactor: -2 }));
  m.receiveShadow = true;
  m.userData.mount = true;
  return m;
}

// ------------------------------------------------------------------ props
const metalDark = () => new THREE.MeshStandardMaterial({ color: "#2B302E", roughness: 0.55, metalness: 0.5 });

/** Soviet apartment door: padded leatherette (or painted steel), frame, handle, peephole, number plate. Faces +Z, hinge at x=0. */
export function aptDoor(tex: Tex, num: number, variant: number) {
  const g = new THREE.Group();
  const W = 0.86, Hh = 2.02;
  const frame = new THREE.MeshStandardMaterial({ color: ["#6B4A33", "#3B3A36", "#5A3424"][variant % 3], roughness: 0.6 });
  const leafMat =
    variant % 3 === 1
      ? texMat(tex, "metal_paint", { color: "#8E9A92", rough: 0.6, metal: 0.3 })
      : texMat(tex, "leatherette", { color: variant % 3 === 2 ? "#4A2A22" : "#FFFFFF", rough: 0.55, normal: 1.2 });
  const leafG = uvBox(W, Hh, 0.07, 0.9);
  const leaf = mk(at(leafG, W / 2, Hh / 2, 0.035), leafMat);
  g.add(leaf);
  // frame: jambs + head
  const fG = mergeGeometries([at(uvBox(0.07, Hh + 0.07, 0.1), -0.035, (Hh + 0.07) / 2, 0.02), at(uvBox(0.07, Hh + 0.07, 0.1), W + 0.035, (Hh + 0.07) / 2, 0.02), at(uvBox(W + 0.14, 0.07, 0.1), W / 2, Hh + 0.035, 0.02)]);
  g.add(mk(fG, frame));
  const brass = new THREE.MeshStandardMaterial({ color: "#9C7A3C", roughness: 0.35, metalness: 0.9 });
  const handle = mk(mergeGeometries([at(new THREE.BoxGeometry(0.035, 0.16, 0.02), W - 0.09, 1.0, 0.08), at(new THREE.BoxGeometry(0.11, 0.022, 0.022), W - 0.12, 1.04, 0.105)]), brass);
  g.add(handle);
  const peep = mk(at(new THREE.CylinderGeometry(0.012, 0.012, 0.03, 12), W / 2, 1.55, 0.08, 0, Math.PI / 2), brass);
  g.add(peep);
  const plate = new THREE.Mesh(new THREE.PlaneGeometry(0.12, 0.07), new THREE.MeshStandardMaterial({ map: labelTex(String(num), { w: 128, h: 80, bg: "#C9C2A8", fg: "#1A1A1A", font: "bold 58px Arial" }), roughness: 0.5, metalness: 0.3 }));
  plate.position.set(W / 2, 1.78, 0.073);
  g.add(plate);
  const lock = mk(at(new THREE.CylinderGeometry(0.014, 0.014, 0.02, 14), W - 0.09, 1.2, 0.08, 0, Math.PI / 2), brass);
  g.add(lock);
  g.userData.mount = true;
  g.traverse((o) => (o.userData.mount = true));
  return g;
}

/** cast-iron radiator, `n` sections, standing on the floor, faces +Z */
export function radiator(n = 8) {
  const m = new THREE.MeshStandardMaterial({ color: "#C9C6B8", roughness: 0.55, metalness: 0.2 });
  const gs: THREE.BufferGeometry[] = [];
  for (let i = 0; i < n; i++) gs.push(at(new THREE.BoxGeometry(0.075, 0.5, 0.09), i * 0.085, 0.38, 0), at(new THREE.CylinderGeometry(0.03, 0.03, 0.095, 10), i * 0.085, 0.38, 0, 0, Math.PI / 2));
  gs.push(at(new THREE.CylinderGeometry(0.012, 0.012, 0.13, 8), -0.05, 0.065, 0), at(new THREE.CylinderGeometry(0.012, 0.012, 0.13, 8), (n - 1) * 0.085 + 0.05, 0.065, 0));
  const o = mk(mergeGeometries(gs), m);
  return o;
}

/** stairwell window: white wooden double frame, dark night glass with a far street-lamp glow */
export function stairWindow(w = 1.2, h = 1.35) {
  const g = new THREE.Group();
  const paint = new THREE.MeshStandardMaterial({ color: "#D9D4C4", roughness: 0.75 });
  const glass = new THREE.MeshStandardMaterial({ color: "#10151C", roughness: 0.08, metalness: 0.5, emissive: "#0C1018" });
  g.add(mk(new THREE.PlaneGeometry(w, h), glass, false));
  const bars = [at(new THREE.BoxGeometry(w + 0.1, 0.06, 0.08), 0, h / 2 + 0.03, 0.02), at(new THREE.BoxGeometry(w + 0.1, 0.06, 0.08), 0, -h / 2 - 0.03, 0.02), at(new THREE.BoxGeometry(0.06, h, 0.08), -w / 2 - 0.03, 0, 0.02), at(new THREE.BoxGeometry(0.06, h, 0.08), w / 2 + 0.03, 0, 0.02), at(new THREE.BoxGeometry(0.05, h, 0.06), 0, 0, 0.02), at(new THREE.BoxGeometry(w, 0.045, 0.06), 0, h * 0.22, 0.02)];
  g.add(mk(mergeGeometries(bars), paint));
  const sill = mk(at(uvBox(w + 0.2, 0.05, 0.3), 0, -h / 2 - 0.085, 0.14), new THREE.MeshStandardMaterial({ color: "#B8B3A6", roughness: 0.85 }));
  g.add(sill);
  // sodium street lamp far outside
  const c = document.createElement("canvas");
  c.width = c.height = 128;
  const gg = c.getContext("2d")!;
  const gr = gg.createRadialGradient(64, 64, 2, 64, 64, 64);
  gr.addColorStop(0, "rgba(255,190,110,0.9)");
  gr.addColorStop(0.25, "rgba(255,150,70,0.3)");
  gr.addColorStop(1, "rgba(255,120,40,0)");
  gg.fillStyle = gr;
  gg.fillRect(0, 0, 128, 128);
  const glow = new THREE.Mesh(new THREE.PlaneGeometry(0.5, 0.5), new THREE.MeshBasicMaterial({ map: new THREE.CanvasTexture(c), transparent: true, depthWrite: false, blending: THREE.AdditiveBlending }));
  glow.position.set(w * 0.22, h * 0.18, -0.01);
  glow.rotation.y = Math.PI;
  glow.position.z = -0.005;
  g.add(glow);
  g.userData.mount = true;
  g.traverse((o) => (o.userData.mount = true));
  return g;
}

/** bare bulb on its wire under the ceiling; returns the group, the emissive material and a point light */
export function bulb(drop = 0.25, warm = "#FFD9A0") {
  const g = new THREE.Group();
  const wire = mk(at(new THREE.CylinderGeometry(0.004, 0.004, drop, 6), 0, -drop / 2, 0), new THREE.MeshStandardMaterial({ color: "#151515" }), false);
  const socket = mk(at(new THREE.CylinderGeometry(0.018, 0.022, 0.06, 12), 0, -drop - 0.02, 0), new THREE.MeshStandardMaterial({ color: "#1C1C1C", roughness: 0.6 }), false);
  const glassM = new THREE.MeshStandardMaterial({ color: "#FFF4E0", emissive: warm, emissiveIntensity: 2.4, roughness: 0.2 });
  const glass = mk(at(new THREE.SphereGeometry(0.032, 16, 12), 0, -drop - 0.075, 0), glassM, false);
  g.add(wire, socket, glass);
  const light = new THREE.PointLight(warm, 9, 10, 1.7);
  light.position.set(0, -drop - 0.09, 0);
  light.shadow.mapSize.set(1024, 1024);
  light.shadow.bias = -0.002;
  light.shadow.radius = 3;
  g.add(light);
  g.userData.mount = true;
  return { g, glassM, light };
}

/** mailbox block: 4 x 3 painted steel boxes with slots and numbers */
export function mailboxes(tex: Tex) {
  const g = new THREE.Group();
  const paint = texMat(tex, "metal_paint", { color: "#6F8592", rough: 0.6, metal: 0.25 });
  g.add(mk(at(uvBox(0.9, 0.72, 0.18, 0.6), 0, 0, 0.09), paint));
  const slotM = new THREE.MeshStandardMaterial({ color: "#0B0B0B", roughness: 0.8 });
  for (let r = 0; r < 3; r++)
    for (let c = 0; c < 4; c++) {
      const x = -0.33 + c * 0.22, y = 0.24 - r * 0.24;
      g.add(mk(at(new THREE.BoxGeometry(0.2, 0.005, 0.005), x, y + 0.07, 0.182), slotM, false));
      g.add(mk(at(new THREE.BoxGeometry(0.008, 0.2, 0.005), x + 0.104, y, 0.182), slotM, false));
      const n = new THREE.Mesh(new THREE.PlaneGeometry(0.06, 0.04), new THREE.MeshBasicMaterial({ map: labelTex(String(r * 4 + c + 1), { w: 96, h: 64, fg: "#E8E2D0", font: "bold 44px Arial" }), transparent: true }));
      n.position.set(x - 0.05, y - 0.05, 0.183);
      g.add(n);
    }
  g.userData.mount = true;
  g.traverse((o) => (o.userData.mount = true));
  return g;
}

/** steel electrical panel door on the wall with a bundle of wires going up */
export function elPanel() {
  const g = new THREE.Group();
  const m = new THREE.MeshStandardMaterial({ color: "#7D847C", roughness: 0.55, metalness: 0.35 });
  g.add(mk(at(new THREE.BoxGeometry(0.55, 0.75, 0.12), 0, 0, 0.06), m));
  g.add(mk(at(new THREE.BoxGeometry(0.02, 0.06, 0.02), 0.22, 0, 0.13), metalDark()));
  const wires = new THREE.MeshStandardMaterial({ color: "#1B1B1B", roughness: 0.7 });
  for (let i = 0; i < 4; i++) g.add(mk(at(new THREE.CylinderGeometry(0.006, 0.006, 1.6, 6), -0.15 + i * 0.03, 1.17, 0.03), wires, false));
  g.userData.mount = true;
  g.traverse((o) => (o.userData.mount = true));
  return g;
}

// ------------------------------------------------------------------ the stairwell
export type Lamp = { glassM: THREE.MeshStandardMaterial; light: THREE.PointLight; base: number; floor: number };
export function buildStairwell(tex: Tex, opts: { floors?: number; graffiti?: boolean; mailboxes?: boolean } = {}) {
  const floors = opts.floors ?? 5;
  const g = new THREE.Group();
  const terr = texMat(tex, "terrazzo", { rough: 0.7, normal: 0.5 });
  const conc = texMat(tex, "concrete", { color: "#B9B5AC", rough: 0.9 });
  const tile = texMat(tex, "metlakh", { rough: 0.6, normal: 0.6 });
  const white = texMat(tex, "whitewash", { rough: 0.95 });
  const rail = new THREE.MeshStandardMaterial({ color: "#2A2F2C", roughness: 0.5, metalness: 0.55 });
  const wood = texMat(tex, "wood_dark", { color: "#6A4A35", rough: 0.45 });
  const { x0, x1, zLand, zHalf, z1, gap } = SH;
  const top = FLOOR(floors) + FLOOR_H - 0.2;
  const bottom = LOBBY_Y;

  // ---- walls (inner faces only; the camera never goes outside the shaft)
  const doorsBack: [number, number, number, number][] = [];
  const doorsSide: [number, number, number, number][] = [];
  for (let n = 1; n <= floors; n++) {
    doorsBack.push([-0.43 - x0 - 0.0, FLOOR(n) - bottom, 0.86, 2.02]);
    doorsSide.push([0.32, FLOOR(n) - bottom, 0.86, 2.02]);
  }
  const Hw = top - bottom;
  // back wall (z = 0) facing +Z
  const back = mk(wallShape(x1 - x0, Hw, doorsBack.map(([x, y, w, h]) => [x, y, w, h])), paintMat(tex, 0), false);
  back.position.set(x0, bottom, 0);
  g.add(back);
  // side walls: right (x = x1) faces -X, left (x = x0) faces +X; width along z
  const right = mk(wallShape(z1, Hw, [...doorsSide, [3.0, BOOTH.y - bottom, 0.8, 1.9], [3.82, BOOTH.y - bottom + 0.82, 1.1, 0.95]]), paintMat(tex, 2), false);
  right.rotation.y = -Math.PI / 2;
  right.position.set(x1, bottom, 0);
  g.add(right);
  const left = mk(wallShape(z1, Hw, doorsSide.map(([x, y, w, h]) => [z1 - x - w, y, w, h])), paintMat(tex, 3), false);
  left.rotation.y = Math.PI / 2;
  left.position.set(x0, bottom, z1);
  g.add(left);
  // outer wall (z = z1) facing -Z, with half-landing windows and the entrance door
  const winHoles: [number, number, number, number][] = [];
  for (let n = 1; n < floors; n++) winHoles.push([(x1 - x0) / 2 - 0.6, FLOOR(n) + RISE + 0.9 - bottom, 1.2, 1.35]);
  winHoles.push([(x1 - x0) / 2 - 0.5, 0, 1.0, 2.05]);
  const outer = mk(wallShape(x1 - x0, Hw, winHoles), paintMat(tex, 1), false);
  outer.rotation.y = Math.PI;
  outer.position.set(x1, bottom, z1);
  g.add(outer);
  // reveals (thickness) around the openings so they read as deep walls
  const rev = new THREE.MeshStandardMaterial({ color: "#A9A79C", roughness: 0.9 });
  const revealBox = (w: number, h: number, d: number) => uvBox(w, h, d);
  for (let n = 1; n < floors; n++) {
    const cy = FLOOR(n) + RISE + 0.9 + 0.675;
    const win = stairWindow();
    win.rotation.y = Math.PI;
    win.position.set(0, cy, z1 + 0.12);
    g.add(win);
    g.add(mk(mergeGeometries([at(revealBox(0.02, 1.35, 0.25), -0.61, cy, z1 + 0.125), at(revealBox(0.02, 1.35, 0.25), 0.61, cy, z1 + 0.125), at(revealBox(1.24, 0.02, 0.25), 0, cy + 0.685, z1 + 0.125)]), rev));
    const rad = radiator(9);
    rad.rotation.y = Math.PI;
    rad.position.set(0.34, FLOOR(n) + RISE, z1 - 0.12);
    g.add(rad);
  }

  // ---- slabs: floor landings, half landings, lobby; their undersides are the ceilings
  const slab = (xA: number, xB: number, zA: number, zB: number, y: number, mat: THREE.Material) => {
    const s = mk(at(uvBox(xB - xA, 0.18, zB - zA, 1.0), (xA + xB) / 2, y - 0.09, (zA + zB) / 2), [conc, conc, mat, white, conc, conc] as unknown as THREE.Material);
    s.userData.ground = true;
    return s;
  };
  for (let n = 1; n <= floors; n++) g.add(slab(x0, x1, 0, zLand, FLOOR(n), tile));
  for (let n = 0; n < floors; n++) g.add(slab(x0, x1, zHalf, z1, FLOOR(n) + RISE, terr));
  g.add(slab(x0, x1, 0, zHalf, LOBBY_Y, tile)); // lobby floor under the first flights
  const ceil = mk(at(uvBox(x1 - x0, 0.2, z1, 1.5), 0, top + 0.1, z1 / 2), white, false);
  g.add(ceil);

  // ---- flights
  const flight = (side: 1 | -1, yA: number, upToHalf: boolean) => {
    // side 1 = flight A (x > 0) rising toward +z; side -1 = flight B rising toward -z
    const xA = side > 0 ? gap : x0, xB = side > 0 ? x1 : -gap;
    const w = xB - xA, xc = (xA + xB) / 2;
    const r = RISE / STEPS;
    const treads: THREE.BufferGeometry[] = [], risers: THREE.BufferGeometry[] = [];
    for (let i = 0; i < STEPS - 1; i++) {
      const y = yA + r * (i + 1);
      const zc = side > 0 ? zLand + TREAD * (i + 0.5) : zHalf - TREAD * (i + 0.5);
      treads.push(at(uvBox(w, 0.04, TREAD + 0.02, 0.8), xc, y - 0.02, zc));
      risers.push(at(uvBox(w, r, 0.03, 0.8), xc, y - r / 2, side > 0 ? zLand + TREAD * i + 0.015 : zHalf - TREAD * i - 0.015));
    }
    const fl = new THREE.Group();
    fl.add(mk(mergeGeometries(treads), terr), mk(mergeGeometries(risers), conc));
    // inclined slab under the steps
    const len = Math.hypot(RUN, RISE);
    const ang = Math.atan2(RISE, RUN);
    const sl = mk(at(uvBox(w, 0.16, len + 0.05, 1.2), xc, yA + RISE / 2 - 0.14, (zLand + zHalf) / 2, 0, side > 0 ? -ang : ang), [conc, conc, conc, white, conc, conc] as unknown as THREE.Material);
    fl.add(sl);
    // the stringer edge along the gap
    const sx = side > 0 ? gap : -gap;
    fl.add(mk(at(uvBox(0.06, 0.32, len, 1), sx + (side > 0 ? 0.03 : -0.03), yA + RISE / 2 - 0.02, (zLand + zHalf) / 2, 0, side > 0 ? -ang : ang), conc));
    // railing: bars from each tread to the handrail, wooden handrail on top
    const bars: THREE.BufferGeometry[] = [];
    for (let i = 0; i < STEPS - 1; i++) {
      for (const k of [0.25, 0.75]) {
        const zz = side > 0 ? zLand + TREAD * (i + k) : zHalf - TREAD * (i + k);
        const yy = yA + r * (i + 1);
        bars.push(at(new THREE.BoxGeometry(0.016, 0.9, 0.016), sx + (side > 0 ? 0.03 : -0.03), yy + 0.45, zz));
      }
    }
    fl.add(mk(mergeGeometries(bars), rail));
    const hr = mk(at(uvBox(0.06, 0.045, len + 0.1, 0.6), sx + (side > 0 ? 0.03 : -0.03), yA + RISE / 2 + 0.92, (zLand + zHalf) / 2, 0, side > 0 ? -ang : ang), wood);
    fl.add(hr);
    fl.userData.upToHalf = upToHalf;
    return fl;
  };
  for (let n = 1; n < floors; n++) g.add(flight(1, FLOOR(n), true));
  for (let n = 0; n < floors; n++) g.add(flight(-1, FLOOR(n) + RISE, false));
  // railing caps across the gap at the landings
  const caps: THREE.BufferGeometry[] = [];
  for (let n = 1; n <= floors; n++) {
    caps.push(at(uvBox(2 * gap + 0.06, 0.045, 0.06, 0.6), 0, FLOOR(n) + 0.92, zLand - 0.03));
    if (n < floors) caps.push(at(uvBox(2 * gap + 0.06, 0.045, 0.06, 0.6), 0, FLOOR(n) + RISE + 0.92, zHalf + 0.03));
  }
  g.add(mk(mergeGeometries(caps), wood));
  // top floor: guard rail along the landing edge over the last flight A below
  g.add(mk(at(uvBox(x1 - gap, 0.045, 0.06, 0.6), (gap + x1) / 2, FLOOR(floors) + 0.92, zLand + 0.03), wood));
  const topBars: THREE.BufferGeometry[] = [];
  for (let x = gap + 0.06; x < x1 - 0.04; x += 0.12) topBars.push(at(new THREE.BoxGeometry(0.016, 0.9, 0.016), x, FLOOR(floors) + 0.45, zLand + 0.03));
  g.add(mk(mergeGeometries(topBars), rail));

  // ---- doors, lamps, panels, numbers, graffiti
  const lamps: Lamp[] = [];
  const doors: THREE.Object3D[] = [];
  for (let n = 1; n <= floors; n++) {
    const y = FLOOR(n);
    const base = (n - 1) * 3 + 1;
    const dBack = aptDoor(tex, base + 1, n);
    dBack.position.set(-0.43, y, 0.0);
    const dL = aptDoor(tex, base, n + 1);
    dL.rotation.y = Math.PI / 2;
    dL.position.set(x0, y, 0.32 + 0.86);
    const dR = aptDoor(tex, base + 2, n + 2);
    dR.rotation.y = -Math.PI / 2;
    dR.position.set(x1, y, 0.32);
    g.add(dBack, dL, dR);
    doors.push(dBack, dL, dR);
    const b = bulb(0.22);
    b.g.position.set(0, y + FLOOR_H - 0.2, 0.75);
    g.add(b.g);
    lamps.push({ glassM: b.glassM, light: b.light, base: 9, floor: n });
    const num = decal(labelTex(String(n), { w: 128, h: 128, fg: "#3A1E14", font: "bold 100px Arial" }), 0.22, 0.22, 0.9);
    num.position.set(0.85, y + 1.75, 0.006);
    g.add(num);
    const p = elPanel();
    p.position.set(-0.86, y + 1.3, 0.0);
    g.add(p);
  }
  // lobby lamp
  const lb = bulb(0.3);
  lb.g.position.set(0.2, FLOOR(1) + RISE - 0.19, 4.5); // the lobby ceiling is the underside of the floor-1 half landing
  g.add(lb.g);
  lamps.push({ glassM: lb.glassM, light: lb.light, base: 8, floor: 0 });
  const mb = opts.mailboxes === false ? new THREE.Group() : mailboxes(tex);
  mb.rotation.y = Math.PI / 2;
  mb.position.set(x0 + 0.01, LOBBY_Y + 1.3, 4.65);
  g.add(mb);
  // the steel entrance door (inside face), closed
  const ed = new THREE.Group();
  const steel = texMat(tex, "metal_paint", { color: "#5C4A3E", rough: 0.6, metal: 0.3 });
  ed.add(mk(at(uvBox(1.0, 2.05, 0.06, 1.0), 0, 1.025, 0), steel));
  ed.add(mk(at(new THREE.BoxGeometry(0.03, 0.22, 0.05), -0.38, 1.0, -0.05), metalDark()));
  ed.add(mk(at(new THREE.BoxGeometry(0.34, 0.1, 0.08), 0, 1.95, -0.07), metalDark())); // magnetic lock
  ed.position.set(0, LOBBY_Y, z1 + 0.12);
  ed.traverse((o) => (o.userData.mount = true));
  g.add(ed);
  if (opts.graffiti !== false) {
    const t1 = decal(labelTex("НЕ СМОТРИ ВНИЗ", { w: 1024, h: 256, fg: "#E8E4DA", font: "bold 120px 'Comic Sans MS', Arial", chalk: true, rot: -0.06 }), 1.1, 0.28, 0.85);
    t1.rotation.y = Math.PI / 2;
    t1.position.set(x0 + 0.01, FLOOR(2) + RISE + 1.1, 4.4);
    g.add(t1);
    const t2 = decal(labelTex("Цой жив", { w: 512, h: 256, fg: "#2B2B2B", font: "bold 110px Arial", rot: 0.08 }), 0.6, 0.3, 0.75);
    t2.rotation.y = -Math.PI / 2;
    t2.position.set(x1 - 0.01, FLOOR(3) + 1.6, 3.2);
    g.add(t2);
  }
  g.traverse((o) => {
    if ((o as THREE.Mesh).isMesh) (o as THREE.Mesh).receiveShadow = true;
  });
  return { g, lamps, doors };
}

/** deterministic flicker: 1 = steady; `breath` makes all lamps pulse together ("as if someone breathes") */
export function lampLevel(t: number, seed: number, o: { flicker?: number; breath?: number } = {}) {
  const f = o.flicker ?? 0;
  const n = Math.sin(t * 13.1 + seed * 7.3) * Math.sin(t * 7.7 + seed * 3.1) + Math.sin(t * 31.7 + seed);
  const drop = f > 0 && n > 1.35 - f ? 0.12 : 1;
  const br = o.breath ? 0.62 + 0.38 * (0.5 + 0.5 * Math.sin(t * Math.PI * 2 * 0.28)) : 1;
  return drop * br * (1 + 0.03 * Math.sin(t * 50 + seed));
}
export function applyLamps(lamps: Lamp[], t: number, o: { flicker?: number; breath?: number; dim?: number } = {}) {
  lamps.forEach((l, i) => {
    const k = lampLevel(t, i + 1, o) * (o.dim ?? 1);
    l.light.intensity = l.base * k;
    l.glassM.emissiveIntensity = 2.4 * k;
  });
}

// ================================================================== textures drawn in code
const canvasTex = (w: number, h: number, draw: (g: CanvasRenderingContext2D) => void, repeat?: [number, number]) => {
  const c = document.createElement("canvas");
  c.width = w;
  c.height = h;
  draw(c.getContext("2d")!);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  if (repeat) {
    t.wrapS = t.wrapT = THREE.RepeatWrapping;
    t.repeat.set(...repeat);
  }
  return t;
};
const HAND = "'Segoe Script', 'Comic Sans MS', cursive";
/** the concierge's register: ruled page, handwritten flats and names; the last line is Dima */
export function journalTex(last = true) {
  return canvasTex(1024, 720, (g) => {
    g.fillStyle = "#E4DBC2";
    g.fillRect(0, 0, 1024, 720);
    for (let i = 0; i < 2600; i++) {
      g.fillStyle = `rgba(120,95,60,${Math.random() * 0.06})`;
      g.fillRect(Math.random() * 1024, Math.random() * 720, 3, 3);
    }
    g.fillStyle = "rgba(60,40,20,0.35)";
    g.fillRect(508, 0, 8, 720); // spine
    g.strokeStyle = "rgba(70,90,150,0.45)";
    g.lineWidth = 2;
    for (let p = 0; p < 2; p++)
      for (let y = 90; y < 700; y += 42) {
        g.beginPath();
        g.moveTo(p * 516 + 30, y);
        g.lineTo(p * 516 + 486, y);
        g.stroke();
      }
    g.fillStyle = "#1E2A55";
    g.font = `34px ${HAND}`;
    const L = [["кв. 2", "Ершова Т."], ["кв. 4", "Петров А."], ["кв. 5", "Кузнецов С."], ["кв. 7", "Смирнова Л."], ["кв. 8", "Гусев Н."], ["кв. 9", "Белов И."], ["кв. 10", "Орлова Е."]];
    L.forEach(([a, b], i) => {
      g.fillText(a, 46, 82 + 42 * (i + 1));
      g.fillText(b, 170, 82 + 42 * (i + 1));
      g.fillText("слышит", 360, 82 + 42 * (i + 1));
    });
    const R = [["кв. 12", "Зуева М."], ["кв. 13", "Лапин В."], ["кв. 14", "Носова Г."], ["кв. 15", "Фомин П."]];
    R.forEach(([a, b], i) => {
      g.fillText(a, 562, 82 + 42 * (i + 1));
      g.fillText(b, 686, 82 + 42 * (i + 1));
      g.fillText("слышит", 880, 82 + 42 * (i + 1));
    });
    if (last) {
      g.fillStyle = "#8A1010";
      g.font = `bold 40px ${HAND}`;
      g.fillText("кв. 11  Соколов Д.", 562, 82 + 42 * 7);
      g.strokeStyle = "#8A1010";
      g.lineWidth = 4;
      g.beginPath();
      g.ellipse(740, 82 + 42 * 7 - 12, 200, 34, -0.04, 0, Math.PI * 2);
      g.stroke();
    }
  });
}
function newspaperTex(seed: number) {
  let s0 = seed * 7919 + 3;
  const r = () => ((s0 = (s0 * 16807) % 2147483647) - 1) / 2147483646;
  return canvasTex(512, 700, (g) => {
    g.fillStyle = "#CFC6AE";
    g.fillRect(0, 0, 512, 700);
    g.fillStyle = "#222";
    g.font = "bold 46px 'Times New Roman', serif";
    g.fillText(["ВЕЧЕРНИЙ ГОРОД", "ТРУД И ОТДЫХ", "НАШ РАЙОН"][seed % 3], 30, 60);
    g.fillRect(24, 76, 464, 3);
    for (let c = 0; c < 3; c++) for (let y = 100; y < 680; y += 11) if (r() > 0.08) g.fillRect(28 + c * 158, y, 140 * (0.6 + r() * 0.4), 4);
    g.fillStyle = "rgba(90,70,40,0.25)";
    for (let i = 0; i < 5; i++) {
      g.beginPath();
      g.arc(r() * 512, r() * 700, 20 + r() * 80, 0, 7);
      g.fill();
    }
  });
}
export function floralTex(base = "#7A1218") {
  return canvasTex(512, 512, (g) => {
    g.fillStyle = base;
    g.fillRect(0, 0, 512, 512);
    let s0 = 991;
    const r = () => ((s0 = (s0 * 16807) % 2147483647) - 1) / 2147483646;
    for (let i = 0; i < 60; i++) {
      const x = r() * 512, y = r() * 512, s = 10 + r() * 22;
      for (let k = 0; k < 5; k++) {
        g.fillStyle = ["#D9A24A", "#E7D7B4", "#2F5A3A", "#C8505A"][(i + k) % 4];
        g.beginPath();
        g.arc(x + Math.cos(k * 1.26) * s * 0.6, y + Math.sin(k * 1.26) * s * 0.6, s * 0.45, 0, 7);
        g.fill();
      }
    }
    g.strokeStyle = "#E7D7B4";
    g.lineWidth = 10;
    g.strokeRect(10, 10, 492, 492);
  });
}
function scratchTex(seed: number) {
  return canvasTex(512, 256, (g) => {
    let s = seed * 131 + 7;
    const r = () => ((s = (s * 16807) % 2147483647) - 1) / 2147483646;
    for (let k = 0; k < 4; k++) {
      const x0 = 60 + r() * 380, y0 = 30 + r() * 60;
      for (let f = 0; f < 4; f++) {
        g.strokeStyle = `rgba(20,14,10,${0.55 + r() * 0.3})`;
        g.lineWidth = 3 + r() * 3;
        g.beginPath();
        g.moveTo(x0 + f * 14, y0);
        g.bezierCurveTo(x0 + f * 14 + r() * 10, y0 + 60, x0 + f * 16 + r() * 16, y0 + 110, x0 + f * 18 + r() * 20, y0 + 160 + r() * 30);
        g.stroke();
      }
    }
  });
}
function calendarTex() {
  return canvasTex(256, 360, (g) => {
    g.fillStyle = "#EDE7D6";
    g.fillRect(0, 0, 256, 360);
    g.fillStyle = "#A21E1E";
    g.font = "bold 44px Arial";
    g.textAlign = "center";
    g.fillText("2004", 128, 56);
    g.fillStyle = "#222";
    g.font = "bold 26px Arial";
    g.fillText("НОЯБРЬ", 128, 96);
    g.font = "20px Arial";
    let d = 1;
    for (let rr = 0; rr < 5; rr++)
      for (let c = 0; c < 7; c++) {
        if (d > 30) break;
        g.fillStyle = c >= 5 ? "#A21E1E" : "#222";
        g.fillText(String(d++), 30 + c * 33, 140 + rr * 40);
      }
  });
}

// ================================================================== furniture
export function chair(tex: Tex) {
  const g = new THREE.Group();
  const w = texMat(tex, "wood_dark", { color: "#8A6446", rough: 0.6 });
  const gs = [at(uvBox(0.42, 0.04, 0.42, 0.5), 0, 0.45, 0)];
  for (const [x, z] of [[-0.18, -0.18], [0.18, -0.18], [-0.18, 0.18], [0.18, 0.18]]) gs.push(at(uvBox(0.035, 0.45, 0.035, 0.5), x, 0.225, z));
  gs.push(at(uvBox(0.035, 0.5, 0.035, 0.5), -0.18, 0.72, -0.18), at(uvBox(0.035, 0.5, 0.035, 0.5), 0.18, 0.72, -0.18), at(uvBox(0.4, 0.14, 0.025, 0.5), 0, 0.88, -0.19));
  g.add(mk(mergeGeometries(gs), w));
  return g; // seat faces +Z, back at -Z
}
export function teaGlass() {
  const g = new THREE.Group();
  const glass = new THREE.MeshStandardMaterial({ color: "#B97A2C", roughness: 0.1, transparent: true, opacity: 0.75 });
  const metal = new THREE.MeshStandardMaterial({ color: "#B9B2A0", roughness: 0.3, metalness: 0.9 });
  g.add(mk(at(new THREE.CylinderGeometry(0.034, 0.03, 0.1, 18), 0, 0.06, 0), glass, false));
  g.add(mk(mergeGeometries([at(new THREE.CylinderGeometry(0.038, 0.034, 0.06, 18, 1, true), 0, 0.03, 0), at(new THREE.TorusGeometry(0.025, 0.005, 6, 12, Math.PI), 0.045, 0.04, 0, Math.PI / 2, 0, -Math.PI / 2), at(new THREE.CylinderGeometry(0.004, 0.003, 0.15, 6), 0.015, 0.12, 0.0, 0, 0.25)]), metal));
  return g;
}
export function wardrobe(tex: Tex) {
  const g = new THREE.Group();
  const w = texMat(tex, "wood_dark", { color: "#7A5A42", rough: 0.55 });
  g.add(mk(at(uvBox(1.0, 2.0, 0.55, 1), 0, 1.0, 0), w));
  const dark = new THREE.MeshStandardMaterial({ color: "#1A120C", roughness: 0.8 });
  g.add(mk(at(new THREE.BoxGeometry(0.006, 1.8, 0.01), 0, 1.0, 0.278), dark, false));
  const brass = new THREE.MeshStandardMaterial({ color: "#9C7A3C", roughness: 0.35, metalness: 0.9 });
  g.add(mk(mergeGeometries([at(new THREE.BoxGeometry(0.02, 0.1, 0.02), -0.05, 1.05, 0.29), at(new THREE.BoxGeometry(0.02, 0.1, 0.02), 0.05, 1.05, 0.29)]), brass));
  return g; // doors face +Z
}
function crt() {
  const g = new THREE.Group();
  g.add(mk(at(new THREE.BoxGeometry(0.42, 0.36, 0.4), 0, 0.18, 0), new THREE.MeshStandardMaterial({ color: "#2B2A27", roughness: 0.6 })));
  const scr = new THREE.Mesh(new THREE.PlaneGeometry(0.32, 0.25), new THREE.MeshStandardMaterial({ color: "#20282B", emissive: "#1B2A33", emissiveIntensity: 0.6, roughness: 0.15 }));
  scr.position.set(0, 0.19, 0.201);
  g.add(scr);
  return g;
}
const softDot = () => {
  const sc = document.createElement("canvas");
  sc.width = sc.height = 64;
  const sg = sc.getContext("2d")!;
  const gr = sg.createRadialGradient(32, 32, 2, 32, 32, 32);
  gr.addColorStop(0, "rgba(255,255,255,0.5)");
  gr.addColorStop(1, "rgba(255,255,255,0)");
  sg.fillStyle = gr;
  sg.fillRect(0, 0, 64, 64);
  return new THREE.CanvasTexture(sc);
};

/** the concierge booth behind the lobby's right wall (stairwell coordinates). "after": chair down, journal on the floor, wardrobe pushed aside, the hidden door open. */
export function buildBooth(tex: Tex, state: "before" | "after" = "before") {
  const g = new THREE.Group();
  const { x0, x1, z0, z1, y, h } = BOOTH;
  const paper = texMat(tex, "wallpaper", { rough: 0.9, normal: 0.5 });
  const white = texMat(tex, "whitewash", { rough: 0.95 });
  const floor = mk(at(uvBox(x1 - x0, 0.05, z1 - z0, 1.0), (x0 + x1) / 2, y - 0.025, (z0 + z1) / 2), texMat(tex, "parquet", { rough: 0.6 }), false);
  floor.userData.ground = true;
  g.add(floor);
  g.add(mk(at(uvBox(x1 - x0, 0.05, z1 - z0, 1.5), (x0 + x1) / 2, y + h + 0.025, (z0 + z1) / 2), white, false));
  const part = mk(wallShape(z1 - z0, h, [[z1 - 3.8, 0, 0.8, 1.9], [z1 - 4.92, 0.82, 1.1, 0.95]], 1.0), paper, false);
  part.rotation.y = Math.PI / 2;
  part.position.set(x0 + 0.002, y, z1);
  g.add(part);
  const back = mk(wallShape(z1 - z0, h, [[2.1 - z0, 0, 0.8, 2.0]], 1.0), paper, false);
  back.rotation.y = -Math.PI / 2;
  back.position.set(x1, y, z0);
  g.add(back);
  const sideA = mk(wallShape(x1 - x0, h, [], 1.0), paper, false);
  sideA.position.set(x0, y, z0);
  g.add(sideA);
  const sideB = mk(wallShape(x1 - x0, h, [[0.9, 1.0, 0.8, 0.9]], 1.0), paper, false);
  sideB.rotation.y = Math.PI;
  sideB.position.set(x1, y, z1);
  g.add(sideB);
  const win = stairWindow(0.8, 0.9);
  win.rotation.y = Math.PI;
  win.position.set(x1 - 1.3, y + 1.45, z1 + 0.06);
  g.add(win);
  const glassM = new THREE.MeshStandardMaterial({ color: "#9FB4B8", roughness: 0.05, metalness: 0.2, transparent: true, opacity: 0.18 });
  const gl = new THREE.Mesh(new THREE.PlaneGeometry(1.1, 0.95), glassM);
  gl.rotation.y = Math.PI / 2;
  gl.position.set(x0, y + 0.82 + 0.475, 4.37);
  g.add(gl);
  g.add(mk(at(uvBox(0.08, 0.05, 1.2, 0.6), x0 + 0.02, y + 0.8, 4.37), texMat(tex, "wood_dark", { color: "#8A6446" })));
  const wood = texMat(tex, "wood_dark", { color: "#7A5A42", rough: 0.55 });
  const deskG = [at(uvBox(0.65, 0.04, 1.35, 0.8), x0 + 0.35, y + 0.75, 4.37)];
  for (const [dx, dz] of [[0.05, -0.6], [0.6, -0.6], [0.05, 0.6], [0.6, 0.6]]) deskG.push(at(uvBox(0.04, 0.73, 0.04, 0.6), x0 + dx, y + 0.365, 4.37 + dz));
  g.add(mk(mergeGeometries(deskG), wood));
  const top = y + 0.77;
  const journal = new THREE.Group();
  journal.add(mk(at(new THREE.BoxGeometry(0.42, 0.02, 0.3), 0, 0.01, 0), new THREE.MeshStandardMaterial({ color: "#3C2A22", roughness: 0.7 })));
  const pages = new THREE.Mesh(new THREE.PlaneGeometry(0.4, 0.28), new THREE.MeshStandardMaterial({ map: journalTex(), roughness: 0.85 }));
  pages.rotation.x = -Math.PI / 2;
  pages.position.y = 0.022;
  journal.add(pages);
  // hinged cover: pivot on the left edge; rotation.z = PI lies open to the left, 0 = closed over the pages
  const coverPivot = new THREE.Group();
  coverPivot.position.set(-0.21, 0.024, 0);
  const cover = mk(at(new THREE.BoxGeometry(0.42, 0.006, 0.3), 0.21, 0.003, 0), new THREE.MeshStandardMaterial({ color: "#4A2E24", roughness: 0.7 }), false);
  coverPivot.add(cover);
  coverPivot.rotation.z = Math.PI;
  journal.add(coverPivot);
  const tea = teaGlass();
  const lampL = new THREE.PointLight("#FFC880", 3, 4, 1.8);
  const lampGroup = new THREE.Group();
  const lampM = new THREE.MeshStandardMaterial({ color: "#2E4A36", roughness: 0.4, metalness: 0.3 });
  lampGroup.add(mk(mergeGeometries([at(new THREE.CylinderGeometry(0.07, 0.08, 0.02, 16), 0, 0.01, 0), at(new THREE.CylinderGeometry(0.008, 0.008, 0.3, 8), 0, 0.16, 0), at(new THREE.ConeGeometry(0.09, 0.1, 16, 1, true), 0.04, 0.32, 0, 0, 0, 0.6)]), lampM));
  lampL.position.set(0.06, 0.28, 0);
  lampGroup.add(lampL);
  lampGroup.position.set(x0 + 0.2, top, 4.95);
  g.add(lampGroup);
  const tv = crt();
  tv.position.set(x0 + 0.3, top, 3.83);
  tv.rotation.y = Math.PI / 2;
  g.add(tv);
  const cal = decal(calendarTex(), 0.28, 0.4);
  cal.rotation.y = Math.PI;
  cal.position.set(x1 - 0.6, y + 1.6, z1 - 0.01);
  g.add(cal);
  const ch = chair(tex);
  const wd = wardrobe(tex);
  wd.rotation.y = -Math.PI / 2;
  const oldDoor = new THREE.Group();
  const plank = texMat(tex, "wood_dark", { color: "#5A4434", rough: 0.8 });
  oldDoor.add(mk(at(uvBox(0.78, 1.98, 0.05, 0.8), 0.39, 0.99, 0), plank));
  oldDoor.add(mk(at(new THREE.BoxGeometry(0.03, 0.08, 0.04), 0.7, 1.0, 0.04), metalDark()));
  oldDoor.rotation.y = -Math.PI / 2;
  const dark = new THREE.Group();
  const damp = texMat(tex, "concrete_damp", { rough: 0.8 });
  for (let i = 0; i < 6; i++) dark.add(mk(at(uvBox(0.3, 0.16, 0.8, 0.8), x1 + 0.45 + i * 0.28, y - 0.16 * (i + 1) + 0.08, 2.5), damp));
  dark.add(mk(at(uvBox(0.04, 3.2, 1.2, 1), x1 + 1.2, y - 0.4, 1.9), damp), mk(at(uvBox(0.04, 3.2, 1.2, 1), x1 + 1.2, y - 0.4, 3.1), damp));
  const voidM = new THREE.Mesh(new THREE.PlaneGeometry(2, 4), new THREE.MeshBasicMaterial({ color: "#000000" }));
  voidM.rotation.y = -Math.PI / 2;
  voidM.position.set(x1 + 2.4, y - 0.5, 2.5);
  dark.add(voidM);
  g.add(dark);
  const steam: THREE.Sprite[] = [];
  oldDoor.position.set(x1, y, 2.1);
  tea.position.set(x0 + 0.42, top, 4.68);
  if (state === "before") {
    ch.position.set(x0 + 1.0, y, 4.37);
    ch.rotation.y = -Math.PI / 2;
    journal.position.set(x0 + 0.38, top, 4.3);
    journal.rotation.y = Math.PI / 2;
    wd.position.set(x1 - 0.3, y, 2.5);
  } else {
    ch.position.set(x0 + 1.35, y + 0.21, 4.15);
    ch.rotation.set(0, -Math.PI / 2 + 0.5, Math.PI / 2, "YXZ");
    journal.position.set(x0 + 1.25, y + 0.002, 3.35);
    journal.rotation.y = 2.2;
    wd.position.set(x1 - 0.32, y, 3.55);
    wd.rotation.y = -Math.PI / 2 + 0.12;
    oldDoor.rotation.y = -Math.PI / 2 - 1.15; // swung into the booth
    const st = softDot();
    for (let i = 0; i < 6; i++) {
      const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: st, transparent: true, depthWrite: false, opacity: 0.35 }));
      s.scale.setScalar(0.06);
      g.add(s);
      steam.push(s);
    }
  }
  g.add(ch, journal, tea, wd, oldDoor);
  const bulbB = bulb(0.25);
  bulbB.g.position.set((x0 + x1) / 2 + 0.2, y + h, 3.4);
  g.add(bulbB.g);
  g.traverse((o) => {
    if ((o as THREE.Mesh).isMesh) (o as THREE.Mesh).receiveShadow = true;
  });
  const updateSteam = (t: number) =>
    steam.forEach((s, i) => {
      const k = (t * 0.35 + i / steam.length) % 1;
      s.position.set(tea.position.x + Math.sin(t * 1.3 + i) * 0.02 * k, tea.position.y + 0.12 + k * 0.25, tea.position.z + Math.cos(t + i) * 0.015 * k);
      s.scale.setScalar(0.04 + k * 0.1);
      (s.material as THREE.SpriteMaterial).opacity = 0.3 * Math.sin(Math.PI * k);
    });
  return { g, journal, journalCover: coverPivot, journalPage: pages, tea, chair: ch, wardrobe: wd, door: oldDoor, lamp: { glassM: bulbB.glassM, light: bulbB.light, base: 7, floor: 0 } as Lamp, deskLamp: lampL, updateSteam };
}

// ================================================================== the stair down: six flights, damp concrete, numbers, scratches
export const DOWN = { w: 0.7, land: 0.6, run: 2.1, flights: 6 };
export function buildDescent(tex: Tex) {
  const g = new THREE.Group();
  const damp = texMat(tex, "concrete_damp", { rough: 0.75, normal: 1.0 });
  const conc = texMat(tex, "concrete", { color: "#8E8A82", rough: 0.85 });
  const { w, land, run, flights } = DOWN;
  const L = land * 2 + run;
  const r = RISE / 9, tr = run / 8;
  const bottom = -RISE * flights;
  const H = -bottom + 2.6;
  const wN = mk(wallShape(2 * w, H, [], 1.2), damp, false);
  wN.position.set(-w, bottom - 0.2, 0);
  const wS = mk(wallShape(2 * w, H, [], 1.2), damp, false);
  wS.rotation.y = Math.PI;
  wS.position.set(w, bottom - 0.2, L);
  const wE = mk(wallShape(L, H, [], 1.2), damp, false);
  wE.rotation.y = -Math.PI / 2;
  wE.position.set(w, bottom - 0.2, 0);
  const wW = mk(wallShape(L, H, [], 1.2), damp, false);
  wW.rotation.y = Math.PI / 2;
  wW.position.set(-w, bottom - 0.2, L);
  g.add(wN, wS, wE, wW);
  g.add(mk(at(uvBox(2 * w, 0.2, L, 1.2), 0, 2.5, L / 2), conc, false));
  g.add(mk(at(uvBox(0.1, H, run, 1.2), 0, bottom - 0.2 + H / 2, land + run / 2), damp));
  for (let k = 0; k <= flights; k++) {
    const y = -RISE * k;
    const zA = k % 2 === 0 ? 0 : L - land;
    const s = mk(at(uvBox(2 * w, 0.18, land, 1), 0, y - 0.09, zA + land / 2), conc);
    s.userData.ground = true;
    g.add(s);
  }
  for (let k = 0; k < flights; k++) {
    const yTop = -RISE * k;
    const right = k % 2 === 0;
    const xc = right ? w / 2 + 0.025 : -w / 2 - 0.025;
    const steps: THREE.BufferGeometry[] = [];
    for (let i = 0; i < 8; i++) {
      const yy = yTop - r * (i + 1);
      const zc = right ? land + tr * (i + 0.5) : L - land - tr * (i + 0.5);
      steps.push(at(uvBox(w - 0.05, r, tr + 0.01, 0.8), xc, yy + r / 2 - 0.001, zc));
    }
    g.add(mk(mergeGeometries(steps), conc));
    const len = Math.hypot(run, RISE), ang = Math.atan2(RISE, run);
    g.add(mk(at(uvBox(w - 0.05, 0.15, len, 1), xc, yTop - RISE / 2 - 0.16, land + run / 2, 0, right ? ang : -ang), conc));
  }
  for (let k = 1; k <= flights; k++) {
    const y = -RISE * k;
    const atNorth = k % 2 === 0;
    const num = decal(labelTex("-" + k, { w: 256, h: 256, fg: "#7E1410", font: "bold 190px Arial" }), 0.45, 0.45, 0.92);
    if (atNorth) num.position.set(0.0, y + 1.55, 0.01);
    else {
      num.rotation.y = Math.PI;
      num.position.set(0.0, y + 1.55, L - 0.01);
    }
    g.add(num);
    if (k >= 2) {
      const sc = decal(scratchTex(k), 1.0, 0.5, Math.min(1, 0.4 + k * 0.12));
      const right = (k - 1) % 2 === 0;
      sc.rotation.y = right ? -Math.PI / 2 : Math.PI / 2;
      sc.position.set(right ? w - 0.01 : -w + 0.01, y + RISE * 0.5 + 1.45, land + run * 0.5);
      g.add(sc);
    }
  }
  const pipeM = texMat(tex, "metal_paint", { color: "#6E6A60", rough: 0.6, metal: 0.4 });
  g.add(mk(mergeGeometries([at(new THREE.CylinderGeometry(0.045, 0.045, H, 10), w - 0.08, bottom - 0.2 + H / 2, L - 0.12), at(new THREE.CylinderGeometry(0.02, 0.02, H, 8), w - 0.06, bottom - 0.2 + H / 2, L - 0.26)]), pipeM));
  const pud = new THREE.Mesh(new THREE.CircleGeometry(0.45, 24), new THREE.MeshStandardMaterial({ color: "#0B0D0E", roughness: 0.02, metalness: 0.6 }));
  pud.rotation.x = -Math.PI / 2;
  pud.position.set(0.1, bottom + 0.004, 0.3);
  g.add(pud);
  g.traverse((o) => {
    if ((o as THREE.Mesh).isMesh) (o as THREE.Mesh).receiveShadow = true;
  });
  return { g, bottom, L };
}

// ================================================================== the room at the bottom
export function buildLair(tex: Tex) {
  const g = new THREE.Group();
  const damp = texMat(tex, "concrete_damp", { rough: 0.7, normal: 1.0 });
  const floorM = texMat(tex, "concrete", { color: "#5E5B55", rough: 0.35 });
  const X = 3.2, Z0 = -4.2, Z1 = 2.0, H = 2.4;
  const f = mk(at(uvBox(2 * X, 0.1, Z1 - Z0, 1.5), 0, -0.05, (Z0 + Z1) / 2), floorM, false);
  f.userData.ground = true;
  g.add(f);
  g.add(mk(at(uvBox(2 * X, 0.1, Z1 - Z0, 1.5), 0, H + 0.05, (Z0 + Z1) / 2), damp, false));
  const wa = mk(wallShape(2 * X, H, [], 1.2), damp, false);
  wa.position.set(-X, 0, Z0);
  const wb = mk(wallShape(2 * X, H, [[X - 0.45, 0, 0.9, 2.0]], 1.2), damp, false);
  wb.rotation.y = Math.PI;
  wb.position.set(X, 0, Z1);
  const wc = mk(wallShape(Z1 - Z0, H, [], 1.2), damp, false);
  wc.rotation.y = -Math.PI / 2;
  wc.position.set(X, 0, Z0);
  const wd = mk(wallShape(Z1 - Z0, H, [], 1.2), damp, false);
  wd.rotation.y = Math.PI / 2;
  wd.position.set(-X, 0, Z1);
  g.add(wa, wb, wc, wd);
  const pipeM = texMat(tex, "metal_paint", { color: "#5F5A50", rough: 0.6, metal: 0.4 });
  g.add(mk(mergeGeometries([at(new THREE.CylinderGeometry(0.07, 0.07, 2 * X, 10), 0, H - 0.15, -1.0, 0, 0, Math.PI / 2), at(new THREE.CylinderGeometry(0.04, 0.04, 2 * X, 8), 0, H - 0.12, -1.35, 0, 0, Math.PI / 2), at(new THREE.CylinderGeometry(0.05, 0.05, Z1 - Z0, 8), -X + 0.2, H - 0.2, (Z0 + Z1) / 2, 0, Math.PI / 2)]), pipeM));
  const papers = [0, 1, 2].map((i) => new THREE.MeshStandardMaterial({ map: newspaperTex(i), roughness: 0.9, side: THREE.DoubleSide }));
  let s = 77;
  const r = () => ((s = (s * 16807) % 2147483647) - 1) / 2147483646;
  for (let i = 0; i < 46; i++) {
    const p = new THREE.Mesh(new THREE.PlaneGeometry(0.42, 0.58), papers[i % 3]);
    const rad = 0.6 + r() * 2.2, a = r() * Math.PI * 2;
    p.position.set(Math.cos(a) * rad * 1.1, 0.003 + i * 0.0006, -1.8 + Math.sin(a) * rad * 0.9);
    p.rotation.set(-Math.PI / 2 + (r() - 0.5) * 0.08, 0, r() * Math.PI * 2, "XYZ");
    p.receiveShadow = true;
    p.userData.mount = true;
    g.add(p);
  }
  const cloth = new THREE.PlaneGeometry(0.62, 0.62, 12, 12);
  const pos = cloth.attributes.position as THREE.BufferAttribute;
  for (let i = 0; i < pos.count; i++) pos.setZ(i, 0.03 * Math.sin(pos.getX(i) * 17 + pos.getY(i) * 9) + 0.02 * Math.cos(pos.getY(i) * 23));
  cloth.computeVertexNormals();
  const scarf = new THREE.Mesh(cloth, new THREE.MeshStandardMaterial({ map: floralTex(), roughness: 0.95, side: THREE.DoubleSide }));
  scarf.rotation.set(-Math.PI / 2, 0, 0.7);
  scarf.position.set(0.85, 0.04, -1.55);
  scarf.receiveShadow = true;
  scarf.userData.mount = true;
  g.add(scarf);
  const ch = chair(tex);
  ch.rotation.set(0, 0.8, Math.PI / 2);
  ch.position.set(-1.9, 0.22, -2.9);
  g.add(ch);
  g.traverse((o) => {
    if ((o as THREE.Mesh).isMesh) (o as THREE.Mesh).receiveShadow = true;
  });
  return { g, scarf, seat: new THREE.Vector3(0, 0, -2.2), door: new THREE.Vector3(0, 0, Z1) };
}

// ================================================================== Dima's bedroom
export function buildBedroom(tex: Tex) {
  const g = new THREE.Group();
  const X = 1.6, Z = 2.1, H = 2.6;
  const paper = texMat(tex, "wallpaper", { rough: 0.9, normal: 0.5 });
  const fl = mk(at(uvBox(2 * X, 0.05, 2 * Z, 1.0), 0, -0.025, 0), texMat(tex, "parquet", { rough: 0.55 }), false);
  fl.userData.ground = true;
  g.add(fl);
  g.add(mk(at(uvBox(2 * X, 0.05, 2 * Z, 1.5), 0, H + 0.025, 0), texMat(tex, "whitewash"), false));
  const wN = mk(wallShape(2 * X, H, [], 1.0), paper, false);
  wN.position.set(-X, 0, -Z);
  const wS = mk(wallShape(2 * X, H, [[X - 0.5, 0, 0.9, 2.05]], 1.0), paper, false);
  wS.rotation.y = Math.PI;
  wS.position.set(X, 0, Z);
  const wE = mk(wallShape(2 * Z, H, [[Z - 0.8, 0.85, 1.4, 1.45]], 1.0), paper, false);
  wE.rotation.y = -Math.PI / 2;
  wE.position.set(X, 0, -Z);
  const wW = mk(wallShape(2 * Z, H, [], 1.0), paper, false);
  wW.rotation.y = Math.PI / 2;
  wW.position.set(-X, 0, Z);
  g.add(wN, wS, wE, wW);
  const win = stairWindow(1.4, 1.45);
  win.rotation.y = -Math.PI / 2;
  win.position.set(X + 0.06, 0.85 + 0.725, 0.1);
  g.add(win);
  const tul = new THREE.Mesh(new THREE.PlaneGeometry(1.7, 2.2, 24, 4), new THREE.MeshStandardMaterial({ color: "#EDEBE2", transparent: true, opacity: 0.35, roughness: 1, side: THREE.DoubleSide }));
  const tp = tul.geometry.attributes.position as THREE.BufferAttribute;
  for (let i = 0; i < tp.count; i++) tp.setZ(i, 0.04 * Math.sin(tp.getX(i) * 14));
  tul.rotation.y = -Math.PI / 2;
  tul.position.set(X - 0.12, 1.35, 0.1);
  g.add(tul);
  const wood = texMat(tex, "wood_dark", { color: "#6E4E38", rough: 0.6 });
  g.add(mk(mergeGeometries([at(uvBox(0.95, 0.3, 2.05, 0.8), -X + 0.5, 0.15, -Z + 1.04), at(uvBox(0.95, 0.75, 0.05, 0.8), -X + 0.5, 0.375, -Z + 0.02)]), wood));
  const sheet = new THREE.MeshStandardMaterial({ color: "#C9C2B0", roughness: 0.95 });
  const blanket = new THREE.MeshStandardMaterial({ map: floralTex("#3A4E6A"), roughness: 0.95 });
  g.add(mk(at(new THREE.BoxGeometry(0.9, 0.16, 1.95), -X + 0.5, 0.38, -Z + 1.06), sheet));
  const pil = new THREE.SphereGeometry(0.3, 16, 8);
  pil.scale(1.2, 0.3, 0.75);
  g.add(mk(at(pil, -X + 0.5, 0.5, -Z + 0.3), sheet));
  const bl = new THREE.BoxGeometry(0.98, 0.1, 1.35, 8, 1, 8);
  const bp = bl.attributes.position as THREE.BufferAttribute;
  for (let i = 0; i < bp.count; i++) bp.setY(i, bp.getY(i) + 0.03 * Math.sin(bp.getX(i) * 9 + bp.getZ(i) * 5));
  bl.computeVertexNormals();
  g.add(mk(at(bl, -X + 0.5, 0.5, -Z + 1.35), blanket));
  const carpet = new THREE.Mesh(new THREE.PlaneGeometry(1.6, 1.15), new THREE.MeshStandardMaterial({ map: tex.carpet, roughness: 1 }));
  carpet.rotation.y = Math.PI / 2;
  carpet.position.set(-X + 0.012, 1.35, -Z + 1.0);
  carpet.userData.mount = true;
  g.add(carpet);
  const wdr = wardrobe(tex);
  wdr.rotation.y = -Math.PI / 2;
  wdr.position.set(X - 0.3, 0, Z - 0.7);
  g.add(wdr);
  const ch = chair(tex);
  ch.position.set(X - 0.55, 0, -Z + 0.5);
  ch.rotation.y = -2.4;
  g.add(ch);
  const rad = radiator(8);
  rad.rotation.y = -Math.PI / 2;
  rad.position.set(X - 0.1, 0, -0.25);
  g.add(rad);
  const door = new THREE.Group();
  door.add(mk(at(uvBox(0.86, 2.0, 0.04, 0.9), 0.43, 1.0, 0), new THREE.MeshStandardMaterial({ color: "#D8D1BE", roughness: 0.6 })));
  door.rotation.y = Math.PI - 0.45; // hinge on the right edge of the opening, ajar into the room
  door.position.set(0.5, 0, Z);
  g.add(door);
  const hall = new THREE.Mesh(new THREE.PlaneGeometry(1.2, 2.2), new THREE.MeshBasicMaterial({ color: "#020203" }));
  hall.rotation.y = Math.PI;
  hall.position.set(0.05, 1.05, Z + 0.3);
  g.add(hall);
  const stool = mk(mergeGeometries([at(uvBox(0.36, 0.03, 0.36, 0.5), -X + 1.25, 0.45, -Z + 0.35), at(uvBox(0.03, 0.45, 0.03, 0.5), -X + 1.1, 0.225, -Z + 0.2), at(uvBox(0.03, 0.45, 0.03, 0.5), -X + 1.4, 0.225, -Z + 0.2), at(uvBox(0.03, 0.45, 0.03, 0.5), -X + 1.1, 0.225, -Z + 0.5), at(uvBox(0.03, 0.45, 0.03, 0.5), -X + 1.4, 0.225, -Z + 0.5)]), wood);
  g.add(stool);
  const street = new THREE.SpotLight("#FF9C4A", 45, 10, 0.75, 0.8, 1.3);
  street.position.set(X + 1.5, 2.6, 0.4);
  street.target.position.set(-0.6, 0.6, -0.2);
  street.castShadow = true;
  street.shadow.mapSize.set(1024, 1024);
  g.add(street, street.target);
  const nightFill = new THREE.PointLight("#5A6C8C", 1.2, 6, 1.5);
  nightFill.position.set(0.8, 2.2, 0.2);
  g.add(nightFill);
  g.traverse((o) => {
    if ((o as THREE.Mesh).isMesh) (o as THREE.Mesh).receiveShadow = true;
  });
  return { g, pillow: new THREE.Vector3(-X + 0.5, 0.58, -Z + 0.32), door: new THREE.Vector3(0.05, 1.0, Z), nightstand: new THREE.Vector3(-X + 1.25, 0.47, -Z + 0.35), street, wardrobe: wdr, doorLeaf: door };
}

// ================================================================== bathroom corner with the riser pipe
export function buildPipeCorner(tex: Tex) {
  const g = new THREE.Group();
  const tile = texMat(tex, "tiles_blue", { rough: 0.35, normal: 0.6 });
  const W = 1.6, H = 2.5;
  const a = mk(wallShape(W, H, [], 0.9), tile, false);
  const b = mk(wallShape(W, H, [], 0.9), tile, false);
  b.rotation.y = Math.PI / 2;
  b.position.set(0, 0, W);
  g.add(a, b);
  const f = mk(at(uvBox(W, 0.05, W, 0.8), W / 2, -0.025, W / 2), texMat(tex, "metlakh", { rough: 0.6 }), false);
  f.userData.ground = true;
  g.add(f);
  g.add(mk(at(uvBox(W, 0.05, W, 1.2), W / 2, H + 0.025, W / 2), texMat(tex, "whitewash"), false));
  const iron = texMat(tex, "metal_paint", { color: "#6F7472", rough: 0.55, metal: 0.45 });
  const riser = new THREE.Group();
  riser.add(mk(at(new THREE.CylinderGeometry(0.055, 0.055, H + 0.6, 16), 0.16, H / 2, 0.16), iron));
  for (const y of [0.35, 1.4, 2.3]) riser.add(mk(at(new THREE.CylinderGeometry(0.068, 0.068, 0.08, 16), 0.16, y, 0.16), iron));
  riser.add(mk(at(new THREE.CylinderGeometry(0.045, 0.045, 0.6, 12), 0.45, 0.32, 0.16, 0, 0, Math.PI / 2), iron));
  riser.add(mk(mergeGeometries([at(new THREE.CylinderGeometry(0.016, 0.016, H + 0.6, 8), 0.34, H / 2, 0.08), at(new THREE.CylinderGeometry(0.03, 0.03, 0.05, 10), 0.34, 1.1, 0.08), at(new THREE.BoxGeometry(0.07, 0.012, 0.012), 0.34, 1.13, 0.12)]), new THREE.MeshStandardMaterial({ color: "#8C8A80", roughness: 0.4, metalness: 0.7 })));
  g.add(riser);
  const lamp = bulb(0.15, "#FFE2B0");
  lamp.g.position.set(1.2, H, 1.1);
  g.add(lamp.g);
  const dust: THREE.Mesh[] = [];
  const dm = new THREE.MeshBasicMaterial({ color: "#D9D3C4", transparent: true, opacity: 0.8 });
  for (let i = 0; i < 24; i++) {
    const d = new THREE.Mesh(new THREE.BoxGeometry(0.008, 0.008, 0.008), dm);
    g.add(d);
    dust.push(d);
  }
  const knock = (t: number, hits: number[]) => {
    let shake = 0;
    for (const hh of hits) if (t >= hh) shake = Math.max(shake, Math.exp(-(t - hh) * 14));
    riser.position.x = shake * 0.004 * Math.sin(t * 90);
    const last = hits.filter((x) => x <= t).pop();
    dust.forEach((d, i) => {
      if (last === undefined) {
        d.visible = false;
        return;
      }
      const k = t - last;
      d.visible = k < 1.2;
      d.position.set(0.16 + Math.sin(i * 7.1) * 0.08, H - 0.05 - 0.5 * 9.8 * k * k * (0.3 + (i % 5) * 0.08), 0.16 + Math.cos(i * 3.3) * 0.08);
    });
  };
  g.traverse((o) => {
    if ((o as THREE.Mesh).isMesh) (o as THREE.Mesh).receiveShadow = true;
  });
  return { g, knock, lamp: { glassM: lamp.glassM, light: lamp.light, base: 5, floor: 0 } as Lamp };
}

// ================================================================== the Khrushchyovka from outside, at night
function bareTree(seed: number, h = 8) {
  let s = seed * 997 + 1;
  const r = () => ((s = (s * 16807) % 2147483647) - 1) / 2147483646;
  const bark = new THREE.MeshStandardMaterial({ color: "#1E1B18", roughness: 1 });
  const gs: THREE.BufferGeometry[] = [];
  const branch = (p: THREE.Vector3, dir: THREE.Vector3, len: number, rad: number, depth: number) => {
    const end = p.clone().addScaledVector(dir, len);
    const c = new THREE.CylinderGeometry(rad * 0.65, rad, len, 5);
    c.translate(0, len / 2, 0);
    c.applyQuaternion(new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir));
    c.translate(p.x, p.y, p.z);
    gs.push(c);
    if (depth <= 0) return;
    const n = depth > 2 ? 3 : 2;
    for (let i = 0; i < n; i++) {
      const d = dir.clone().add(new THREE.Vector3((r() - 0.5) * 1.3, r() * 0.4, (r() - 0.5) * 1.3)).normalize();
      branch(end, d, len * (0.6 + r() * 0.15), rad * 0.6, depth - 1);
    }
  };
  branch(new THREE.Vector3(0, 0, 0), new THREE.Vector3(0, 1, 0), h * 0.35, 0.16, 4);
  return mk(mergeGeometries(gs), bark);
}
export const BLOCK = { len: 60, depth: 12, floors: 5, entrances: 4, plinth: 0.9 };
export function buildBlock(tex: Tex, o: { floors?: number; heroFloor?: number; manFloor?: number; day?: boolean } = {}) {
  const g = new THREE.Group();
  const floors = o.floors ?? BLOCK.floors;
  const { len, depth, entrances, plinth } = BLOCK;
  let manPos: THREE.Vector3 | null = null;
  const H = plinth + floors * FLOOR_H + 0.4;
  const brick = texMat(tex, "brick_white", { color: "#C8C6BF", rough: 0.9, normal: 0.9 });
  const conc = texMat(tex, "concrete", { color: "#8C8982", rough: 0.9 });
  // facade with window holes; the window grid: per entrance 2 x 3 windows each side of the stairwell column
  const holes: [number, number, number, number][] = [];
  const winList: { x: number; y: number; w: number; h: number; stair: boolean; floor: number }[] = [];
  const seg = len / entrances;
  for (let e = 0; e < entrances; e++) {
    const cx = -len / 2 + seg * (e + 0.5);
    for (let f = 0; f < floors; f++) {
      const y = plinth + f * FLOOR_H + 0.85;
      for (const dx of [-5.8, -3.4, -1.6, 1.6, 3.4, 5.8]) {
        holes.push([cx + dx - 0.7 + len / 2, y, 1.4, 1.45]);
        winList.push({ x: cx + dx, y: y + 0.725, w: 1.4, h: 1.45, stair: false, floor: f + 1 });
      }
      if (f > 0) {
        const ys = plinth + f * FLOOR_H - RISE + 0.9;
        holes.push([cx - 0.5 + len / 2, ys, 1.0, 1.2]);
        winList.push({ x: cx, y: ys + 0.6, w: 1.0, h: 1.2, stair: true, floor: f });
      }
    }
    holes.push([cx - 0.6 + len / 2, 0.1, 1.2, 2.1]);
  }
  const facade = mk(wallShape(len, H, holes, 2.0), brick, false);
  facade.position.set(-len / 2, 0, 0);
  g.add(facade);
  // the box behind (sides, back, roof), dark inside behind the windows
  const box = mk(at(uvBox(len, H, depth - 0.3, 2.0), 0, H / 2, -depth / 2 - 0.15), brick, false); // front face 0.3 m behind the facade: room for the window panes
  g.add(box);
  g.add(mk(at(uvBox(len + 0.2, 0.5, depth + 0.2, 2), 0, H + 0.1, -depth / 2), conc, false));
  g.add(mk(at(uvBox(len + 0.05, plinth, 0.08, 1.5), 0, plinth / 2, 0.03), conc, false));
  // windows: dark glass or warm / TV-blue light, frames
  const frameM = new THREE.MeshStandardMaterial({ color: "#B9B2A3", roughness: 0.8 });
  const darkGlass = new THREE.MeshStandardMaterial({ color: "#0B0E12", roughness: 0.1, metalness: 0.5 });
  const warm = new THREE.MeshStandardMaterial({ color: "#2A1A0C", emissive: "#FFB060", emissiveIntensity: 0.9, roughness: 0.4 });
  const warm2 = new THREE.MeshStandardMaterial({ color: "#2A1A0C", emissive: "#FF8C3A", emissiveIntensity: 0.6, roughness: 0.4 });
  const tv = new THREE.MeshStandardMaterial({ color: "#0A1420", emissive: "#5C86C8", emissiveIntensity: 0.7, roughness: 0.4 });
  const stairLit = new THREE.MeshStandardMaterial({ color: "#20180E", emissive: "#E8C890", emissiveIntensity: 0.55, roughness: 0.4 });
  let s = 5;
  const r = () => ((s = (s * 16807) % 2147483647) - 1) / 2147483646;
  const frames: THREE.BufferGeometry[] = [];
  const panes: Record<string, THREE.BufferGeometry[]> = { dark: [], warm: [], warm2: [], tv: [], stair: [] };
  let dimaWin: THREE.Vector3 | null = null;
  winList.forEach((w, i) => {
    const isDima = !w.stair && w.floor === (o.heroFloor ?? 4) && Math.abs(w.x - (-len / 2 + seg * 1.5 + 1.6)) < 0.01;
    if (o.manFloor && !w.stair && w.floor === o.manFloor && Math.abs(w.x - (-len / 2 + seg * 1.5 + 1.6)) < 0.01) {
      manPos = new THREE.Vector3(w.x, w.y - w.h / 2 - 0.85, -0.2);
      return; // open window: no pane, the man stands in it
    }
    const kind = o.day ? "dark" : isDima ? "warm" : w.stair ? (r() < 0.75 ? "stair" : "dark") : r() < 0.12 ? "warm" : r() < 0.05 ? "warm2" : r() < 0.04 ? "tv" : "dark";
    if (isDima) dimaWin = new THREE.Vector3(w.x, w.y, 0);
    panes[kind].push(at(new THREE.PlaneGeometry(w.w, w.h), w.x, w.y, -0.12));
    frames.push(at(new THREE.BoxGeometry(w.w, 0.06, 0.08), w.x, w.y + w.h / 2 - 0.03, -0.1), at(new THREE.BoxGeometry(w.w, 0.06, 0.08), w.x, w.y - w.h / 2 + 0.03, -0.1), at(new THREE.BoxGeometry(0.05, w.h, 0.08), w.x, w.y, -0.1));
    frames.push(at(new THREE.BoxGeometry(w.w + 0.15, 0.05, 0.2), w.x, w.y - w.h / 2 - 0.03, 0.06));
    void i;
  });
  g.add(mk(mergeGeometries(frames), frameM));
  const pm: Record<string, THREE.Material> = { dark: darkGlass, warm, warm2, tv, stair: stairLit };
  for (const k of Object.keys(panes)) if (panes[k].length) g.add(mk(mergeGeometries(panes[k]), pm[k], false));
  // balconies on some windows (floors 2..5)
  const railM = new THREE.MeshStandardMaterial({ color: "#3C3F3A", roughness: 0.6, metalness: 0.5 });
  const balG: THREE.BufferGeometry[] = [], balR: THREE.BufferGeometry[] = [];
  winList.forEach((w) => {
    if (w.stair || w.floor < 2 || Math.abs(w.x % 15) < 0.1 || r() > 0.3) return;
    const y = w.y - w.h / 2 - 0.85;
    balG.push(at(uvBox(2.2, 0.14, 0.9, 1), w.x, y, 0.45));
    balR.push(at(new THREE.BoxGeometry(2.2, 0.9, 0.03), w.x, y + 0.52, 0.89), at(new THREE.BoxGeometry(0.03, 0.9, 0.9), w.x - 1.09, y + 0.52, 0.45), at(new THREE.BoxGeometry(0.03, 0.9, 0.9), w.x + 1.09, y + 0.52, 0.45));
  });
  if (balG.length) g.add(mk(mergeGeometries(balG), conc), mk(mergeGeometries(balR), railM));
  // entrances: steel doors, concrete canopies, a bulb over each
  const lamps: THREE.PointLight[] = [];
  for (let e = 0; e < entrances; e++) {
    const cx = -len / 2 + seg * (e + 0.5);
    g.add(mk(at(uvBox(1.2, 2.1, 0.06, 1), cx, 1.15, -0.05), texMat(tex, "metal_paint", { color: "#4A3E34", rough: 0.6, metal: 0.3 })));
    g.add(mk(at(uvBox(2.0, 0.14, 1.3, 1), cx, 2.55, 0.65), conc));
    g.add(mk(at(uvBox(2.4, 0.15, 1.6, 1), cx, 0.075, 0.8), conc));
    const lb = new THREE.PointLight("#FFC27A", o.day ? 0 : e === 1 ? 6 : 3.5, 7, 1.8);
    lb.position.set(cx, 2.35, 0.45);
    g.add(lb);
    lamps.push(lb);
    const glass = mk(at(new THREE.SphereGeometry(0.06, 10, 8), cx, 2.42, 0.45), new THREE.MeshStandardMaterial({ color: "#FFF0D0", emissive: "#FFC27A", emissiveIntensity: 2 }), false);
    g.add(glass);
  }
  // ground: asphalt path and dirt
  const asph = mk(at(uvBox(len + 40, 0.05, 30, 3), 0, -0.025, 15), texMat(tex, "concrete", { color: "#3E3C39", rough: 0.6 }), false);
  asph.userData.ground = true;
  g.add(asph);
  // bare trees and a sodium street lamp
  for (let i = 0; i < 9; i++) {
    const t = bareTree(i + 3, 7 + (i % 3));
    t.position.set(-len / 2 + 4 + i * 7.1 + (i % 2) * 1.5, 0, 6.5 + (i % 3) * 1.6);
    g.add(t);
  }
  const pole = mk(at(new THREE.CylinderGeometry(0.07, 0.1, 7, 8), -len / 2 + seg * 1.5 + 6, 3.5, 9), railM);
  g.add(pole);
  const sodium = new THREE.SpotLight("#FF9A3C", o.day ? 0 : 260, 34, 0.95, 0.6, 1.5);
  sodium.position.set(-len / 2 + seg * 1.5 + 6, 7.0, 8.6);
  sodium.target.position.set(-len / 2 + seg * 1.5 + 4, 0, 3);
  sodium.castShadow = true;
  sodium.shadow.mapSize.set(1024, 1024);
  g.add(sodium, sodium.target);
  const moon = new THREE.DirectionalLight("#7E93B8", 0.35);
  moon.position.set(-30, 40, 40);
  g.add(moon);
  // distant blocks for depth
  const far = new THREE.MeshStandardMaterial({ color: "#14171B", roughness: 1 });
  for (let i = 0; i < 6; i++) g.add(mk(at(new THREE.BoxGeometry(40, 15 + (i % 3) * 9, 12), -80 + i * 34, 7.5 + (i % 3) * 4.5, 70 + (i % 2) * 25), far, false));
  g.traverse((o) => {
    if ((o as THREE.Mesh).isMesh) (o as THREE.Mesh).receiveShadow = true;
  });
  return { g, lamps, manPos: manPos as THREE.Vector3 | null, dimaWin: (dimaWin as THREE.Vector3 | null) ?? new THREE.Vector3(-len / 2 + seg * 1.5 + 1.6, plinth + 3 * FLOOR_H + 1.6, 0), entrance2: new THREE.Vector3(-len / 2 + seg * 1.5, 0, 0) };
}
