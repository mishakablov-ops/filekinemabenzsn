/**
 * Procedural sets for the nk-escape reel, built from real-world sizes so the first-person camera never meets
 * a wrong scale. Textures: projects/nk-escape/tex/<name>.jpg + <name>_n.png (gen_textures.py), tiled in metres.
 *
 * Coordinates (JSA): metres, +Y up, the Military Demarcation Line (MDL) runs along X at z = 0, NORTH = -Z, SOUTH = +Z.
 * The defector's route and the actors' marks are exported as JSA_MARKS.
 */
import * as THREE from "three";

export type Tex = Record<string, THREE.Texture>;
export const TEX_NAMES = ["concrete", "gravel", "asphalt", "metal_blue", "metal_grey", "granite", "plaster_green", "dry_grass", "floor_paint"];

// ------------------------------------------------------------------ geometry helpers with metre-based UVs
/** box whose UVs repeat every `tile` metres on every face */
export function box(w: number, h: number, d: number, tile = 2): THREE.BufferGeometry {
  const g = new THREE.BoxGeometry(w, h, d);
  const uv = g.attributes.uv as THREE.BufferAttribute;
  const dims: [number, number][] = [[d, h], [d, h], [w, d], [w, d], [w, h], [w, h]];
  for (let f = 0; f < 6; f++)
    for (let i = 0; i < 4; i++) {
      const k = f * 4 + i;
      uv.setXY(k, (uv.getX(k) * dims[f][0]) / tile, (uv.getY(k) * dims[f][1]) / tile);
    }
  uv.needsUpdate = true;
  return g;
}
export function plane(w: number, d: number, tile = 2): THREE.BufferGeometry {
  const g = new THREE.PlaneGeometry(w, d);
  const uv = g.attributes.uv as THREE.BufferAttribute;
  for (let i = 0; i < uv.count; i++) uv.setXY(i, (uv.getX(i) * w) / tile, (uv.getY(i) * d) / tile);
  g.rotateX(-Math.PI / 2);
  return g;
}

type MatOpts = { color?: string; rough?: number; metal?: number; normal?: number; noMap?: boolean };
export function makeMat(tex: Tex, name: string | null, o: MatOpts = {}) {
  const m = new THREE.MeshStandardMaterial({
    map: name && !o.noMap ? tex[name] : null,
    normalMap: name ? tex[name + "_n"] ?? null : null,
    color: o.color ?? "#ffffff",
    roughness: o.rough ?? 0.9,
    metalness: o.metal ?? 0,
  });
  if (m.normalMap) m.normalScale.set(o.normal ?? 0.8, o.normal ?? 0.8);
  return m;
}

const mesh = (g: THREE.BufferGeometry, m: THREE.Material, x = 0, y = 0, z = 0, ry = 0) => {
  const o = new THREE.Mesh(g, m);
  o.position.set(x, y, z);
  o.rotation.y = ry;
  o.castShadow = true;
  o.receiveShadow = true;
  return o;
};

/** seeded random */
export const rng = (seed: number) => () => {
  seed = (seed * 16807) % 2147483647;
  return (seed - 1) / 2147483646;
};

// ------------------------------------------------------------------ props
const WHITE = new THREE.MeshStandardMaterial({ color: "#E9E8E2", roughness: 0.6 });
const GLASS = new THREE.MeshStandardMaterial({ color: "#2B3236", roughness: 0.08, metalness: 0.6 });
const DARK = new THREE.MeshStandardMaterial({ color: "#3A3D3C", roughness: 0.7, metalness: 0.3 });

function windowUnit(w: number, h: number) {
  const g = new THREE.Group();
  g.userData.mount = true; // sits in a wall
  g.add(mesh(new THREE.BoxGeometry(w, h, 0.04), GLASS, 0, 0, 0.0));
  const f = 0.06;
  g.add(mesh(new THREE.BoxGeometry(w + f * 2, f, 0.08), WHITE, 0, h / 2 + f / 2, 0.02));
  g.add(mesh(new THREE.BoxGeometry(w + f * 2, f, 0.12), WHITE, 0, -h / 2 - f / 2, 0.04));
  g.add(mesh(new THREE.BoxGeometry(f, h, 0.08), WHITE, -w / 2 - f / 2, 0, 0.02));
  g.add(mesh(new THREE.BoxGeometry(f, h, 0.08), WHITE, w / 2 + f / 2, 0, 0.02));
  g.add(mesh(new THREE.BoxGeometry(0.035, h, 0.06), WHITE, 0, 0, 0.02));
  return g;
}

/** one conference hut straddling the MDL: long axis N-S, windows on the east and west walls, doors at both ends */
export function conferenceHut(tex: Tex, blue: boolean) {
  const g = new THREE.Group();
  const W = 6.4, L = 11.6, H = 3.1;
  const wall = makeMat(tex, blue ? "metal_blue" : "metal_grey", { rough: 0.55, metal: 0.15, normal: 1.1 });
  g.add(mesh(box(W, H, L, 2.4), wall, 0, H / 2 + 0.25, 0));
  const base = makeMat(tex, "concrete", { color: "#BDBBB4" });
  g.add(mesh(box(W + 0.3, 0.25, L + 0.3, 2), base, 0, 0.125, 0));
  // roof: shallow gable with an overhang
  const roofMat = makeMat(tex, "metal_grey", { color: "#8E9396", rough: 0.6, metal: 0.25 });
  const A = 0.16, rise = (W / 2) * Math.tan(A), top = H + 0.25;
  const tri = new THREE.Shape([new THREE.Vector2(-W / 2, 0), new THREE.Vector2(W / 2, 0), new THREE.Vector2(0, rise)]);
  const gable = new THREE.ExtrudeGeometry(tri, { depth: L, bevelEnabled: false });
  gable.translate(0, 0, -L / 2);
  g.add(mesh(gable, wall, 0, top, 0)); // closes the triangle between the wall tops and the roof
  for (const s of [-1, 1]) {
    const cx = (W / 2 + 0.45) / 2;
    const r = mesh(box(W / 2 + 0.45, 0.08, L + 0.7, 2.4), roofMat, s * cx, top + rise - cx * Math.tan(A) + 0.04 / Math.cos(A), 0);
    r.rotation.z = -s * A;
    r.userData.mount = true;
    g.add(r);
  }
  const cap = mesh(new THREE.BoxGeometry(0.16, 0.08, L + 0.7), roofMat, 0, top + rise + 0.07, 0);
  cap.userData.mount = true;
  g.add(cap);
  // windows along both long walls
  for (const s of [-1, 1])
    for (let i = 0; i < 4; i++) {
      const wu = windowUnit(1.05, 1.15);
      wu.position.set(s * (W / 2 + 0.01), 1.85, -L / 2 + 1.7 + i * 2.75);
      wu.rotation.y = s * Math.PI / 2;
      g.add(wu);
    }
  // doors at both ends + small steps
  for (const s of [-1, 1]) {
    const d = mesh(new THREE.BoxGeometry(0.95, 2.05, 0.06), blue ? WHITE : DARK, 0, 0.25 + 2.05 / 2, s * (L / 2 + 0.03));
    d.userData.mount = true;
    g.add(d);
    const handle = mesh(new THREE.BoxGeometry(0.04, 0.04, 0.12), DARK, 0.36, 1.25, s * (L / 2 + 0.09));
    handle.userData.mount = true;
    g.add(handle);
    g.add(mesh(box(1.6, 0.18, 0.7, 1), base, 0, 0.09, s * (L / 2 + 0.45)));
  }
  // air conditioners on the west wall
  for (const z of [-3.2, 2.4]) g.add(mesh(new THREE.BoxGeometry(0.35, 0.55, 0.8), WHITE, -W / 2 - 0.35, 0.275, z)); // standing on the ground by the wall
  return g;
}

/** Panmungak-like: three-storey grey granite hall with a square colonnade, facing south */
export function northHall(tex: Tex) {
  const g = new THREE.Group();
  const W = 38, D = 14, H = 13;
  const stone = makeMat(tex, "granite", { color: "#D7D6D1", rough: 0.85, normal: 0.6 });
  g.add(mesh(box(W, H, D, 3), stone, 0, H / 2, 0));
  g.add(mesh(box(W + 1.2, 0.7, D + 1.2, 3), stone, 0, H + 0.35, 0)); // cornice
  g.add(mesh(box(W * 0.45, 2.6, D * 0.6, 3), stone, 0, H + 2, -1)); // rooftop pavilion
  for (let i = 0; i < 12; i++) g.add(mesh(box(0.85, H - 0.6, 0.85, 3), stone, -W / 2 + 1.8 + i * ((W - 3.6) / 11), (H - 0.6) / 2, D / 2 + 1.6)); // ground to the beam
  g.add(mesh(box(W, 0.6, 1.6, 3), stone, 0, H - 0.3, D / 2 + 1.6));
  for (let fl = 0; fl < 3; fl++)
    for (let i = 0; i < 11; i++) {
      const wu = windowUnit(1.6, 2.0);
      wu.position.set(-W / 2 + 3.5 + i * ((W - 7) / 10), 2.2 + fl * 3.9, D / 2 + 0.02);
      g.add(wu);
    }
  const steps = makeMat(tex, "concrete", { color: "#C9C7C0" });
  for (let i = 0; i < 4; i++) g.add(mesh(box(16 - i * 1.2, 0.18, 4 - i * 0.6, 2), steps, 0, 0.09 + i * 0.18, D / 2 + 3.4 - i * 0.3));
  return g;
}

/** Freedom House-like: modern pale building with a Korean pagoda roof on top, facing north */
export function southHall(tex: Tex) {
  const g = new THREE.Group();
  const W = 34, D = 16, H = 11;
  const conc = makeMat(tex, "concrete", { color: "#E4E2DC", rough: 0.8 });
  g.add(mesh(box(W, H, D, 3), conc, 0, H / 2, 0));
  for (let fl = 0; fl < 3; fl++) {
    const band = mesh(new THREE.BoxGeometry(W - 2, 1.6, 0.1), GLASS, 0, 2.2 + fl * 3.3, -D / 2 - 0.02);
    band.userData.mount = true;
    g.add(band);
  }
  // pagoda: base box + curved hip roof (squashed 4-sided cone with flared eaves)
  g.add(mesh(box(12, 3, 8, 3), conc, 0, H + 1.5, 0));
  const roofMat = new THREE.MeshStandardMaterial({ color: "#4A4E50", roughness: 0.7, metalness: 0.1 });
  const roof = mesh(new THREE.ConeGeometry(9.2, 3.4, 4, 1, false, Math.PI / 4), roofMat, 0, H + 4.6, 0);
  roof.scale.set(1, 1, 0.7);
  g.add(roof);
  g.add(mesh(new THREE.BoxGeometry(13.6, 0.35, 9.6), roofMat, 0, H + 3 + 0.175, 0)); // rests on the pagoda base
  return g;
}

/** low concrete wall with a cap */
export function lowWall(tex: Tex, len: number, h = 0.85) {
  const g = new THREE.Group();
  const c = makeMat(tex, "concrete", { color: "#C4C1B8" });
  g.add(mesh(box(len, h, 0.32, 1.6), c, 0, h / 2, 0));
  const cap = mesh(box(len + 0.06, 0.08, 0.42, 1.6), c, 0, h + 0.04, 0);
  cap.userData.mount = true;
  g.add(cap);
  return g;
}

export function lampPost() {
  const g = new THREE.Group();
  const m = new THREE.MeshStandardMaterial({ color: "#5B5F5E", roughness: 0.5, metalness: 0.6 });
  g.add(mesh(new THREE.CylinderGeometry(0.06, 0.09, 6, 10), m, 0, 3, 0));
  const arm = mesh(new THREE.CylinderGeometry(0.035, 0.035, 1.2, 8), m, 0.5, 5.9, 0);
  arm.rotation.z = Math.PI / 2;
  g.add(arm);
  g.add(mesh(new THREE.BoxGeometry(0.5, 0.12, 0.25), m, 1.05, 5.85, 0));
  g.add(mesh(new THREE.BoxGeometry(0.42, 0.03, 0.2), new THREE.MeshStandardMaterial({ color: "#F4F1E6", emissive: "#3B392F", roughness: 0.4 }), 1.05, 5.78, 0));
  g.children.slice(1).forEach((c) => (c.userData.mount = true));
  return g;
}

export function guardBooth(tex: Tex) {
  const g = new THREE.Group();
  const c = makeMat(tex, "concrete", { color: "#D2D0C8" });
  g.add(mesh(box(1.6, 2.4, 1.6, 1.6), c, 0, 1.2, 0));
  const roof = mesh(new THREE.BoxGeometry(1.8, 0.15, 1.8), DARK, 0, 2.475, 0);
  roof.userData.mount = true;
  g.add(roof);
  for (const r of [0, Math.PI / 2, Math.PI, -Math.PI / 2]) {
    const wu = windowUnit(0.9, 0.7);
    wu.position.set(Math.sin(r) * 0.81, 1.65, Math.cos(r) * 0.81);
    wu.rotation.y = r;
    g.add(wu);
  }
  return g;
}

// ------------------------------------------------------------------ trees: trunk + branches + leaf cards from the leaves atlas
export function tree(leafMat: THREE.Material, seed: number, h = 9, crown = 3.4) {
  const r = rng(seed * 7919 + 13);
  const g = new THREE.Group();
  const bark = new THREE.MeshStandardMaterial({ color: "#4A4037", roughness: 1 });
  const trunk = mesh(new THREE.CylinderGeometry(0.13, 0.26, h * 0.62, 9), bark, 0, h * 0.31, 0);
  trunk.rotation.z = (r() - 0.5) * 0.06;
  g.add(trunk);
  for (let i = 0; i < 6; i++) {
    const len = crown * (0.7 + r() * 0.5);
    const b = mesh(new THREE.CylinderGeometry(0.03, 0.08, len, 6), bark, 0, 0, 0);
    const a = r() * Math.PI * 2, tilt = 0.6 + r() * 0.5;
    b.position.set(Math.cos(a) * len * 0.35 * Math.sin(tilt), h * (0.5 + r() * 0.15) + len * 0.4 * Math.cos(tilt), Math.sin(a) * len * 0.35 * Math.sin(tilt));
    b.rotation.set(Math.sin(a) * tilt, 0, -Math.cos(a) * tilt);
    b.userData.mount = true;
    g.add(b);
  }
  const N = 3600;
  const card = new THREE.PlaneGeometry(0.3, 0.3);
  const leaves = new THREE.InstancedMesh(card, leafMat, N);
  const m = new THREE.Matrix4(), q = new THREE.Quaternion(), e = new THREE.Euler();
  const cy = h * 0.72;
  for (let i = 0; i < N; i++) {
    // points in an irregular ellipsoid, denser at the shell (that is what you see)
    const u = r() * 2 - 1, th = r() * Math.PI * 2, rad = Math.pow(r(), 0.22);
    const x = Math.sqrt(1 - u * u) * Math.cos(th) * rad * crown;
    const z = Math.sqrt(1 - u * u) * Math.sin(th) * rad * crown;
    const y = u * rad * crown * 0.75;
    e.set(r() * Math.PI, r() * Math.PI, r() * Math.PI);
    q.setFromEuler(e);
    const s = 0.8 + r() * 0.7;
    m.compose(new THREE.Vector3(x, cy + y, z), q, new THREE.Vector3(s, s, s));
    leaves.setMatrixAt(i, m);
  }
  leaves.castShadow = true;
  leaves.receiveShadow = true;
  leaves.userData.mount = true;
  g.add(leaves);
  return g;
}

/** leaf card material from the GPT leaves kit (atlas with alpha), tinted autumn */
export function leafMaterialFrom(kit: THREE.Object3D | null) {
  let src: THREE.MeshStandardMaterial | null = null;
  kit?.traverse((o) => {
    const mm = (o as THREE.Mesh).material as THREE.MeshStandardMaterial | undefined;
    if (!src && mm && mm.map && mm.alphaTest > 0) src = mm;
  });
  const m = src ? (src as THREE.MeshStandardMaterial).clone() : new THREE.MeshStandardMaterial({ color: "#C58A2E" });
  m.side = THREE.DoubleSide;
  m.alphaTest = 0.5;
  m.transparent = false;
  return m;
}

// ------------------------------------------------------------------ flags waving (CPU, deterministic)
export function prepareFlag(flagMesh: THREE.Mesh) {
  const pos = flagMesh.geometry.attributes.position as THREE.BufferAttribute;
  const base = Float32Array.from(pos.array as Float32Array);
  const uv = flagMesh.geometry.attributes.uv as THREE.BufferAttribute;
  return (t: number, strength = 1) => {
    for (let i = 0; i < pos.count; i++) {
      const u = uv.getX(i), v = uv.getY(i);
      const w = Math.sin(u * 7.5 - t * 6.2 + v * 1.3) * 0.11 + Math.sin(u * 13 - t * 9.1) * 0.035;
      pos.setXYZ(i, base[i * 3], base[i * 3 + 1] + Math.sin(u * 5 - t * 4) * 0.02 * u * strength, base[i * 3 + 2] + w * u * strength);
    }
    pos.needsUpdate = true;
    flagMesh.geometry.computeVertexNormals();
  };
}

// ------------------------------------------------------------------ the JSA set
export const JSA_MARKS = {
  jeepStuck: new THREE.Vector3(-17.2, 0, -7.5), // front-left wheel in the ditch, facing south
  ditch: { x: -15.35, z0: -40, z1: -1.2 },
  // he cuts across past the west hut (~3 m from its wall), rounds the east end of the low wall and falls in its
  // shelter on the SOUTH side (the wall hides him from the North), lying along it
  run: [[-16.6, -6.4], [-15.0, -4.2], [-12.8, -1.8], [-11.0, 1.0], [-10.0, 4.6], [-8.6, 8.4], [-7.2, 12.6], [-7.1, 15.6], [-8.4, 16.4]] as [number, number][],
  collapse: new THREE.Vector3(-9.9, 0, 16.4),
  wall: { x: -12.5, z: 15.0, len: 9 },
  kpa: [[-18.5, -18], [-16.8, -21], [-13.5, -19], [-20.5, -23]] as [number, number][],
  rok: [[-6.5, 19.5], [-8.5, 21.0], [-4.5, 21.5]] as [number, number][],
};

export function buildJSA(tex: Tex, opts: { leafMat: THREE.Material; flagTower?: THREE.Object3D | null }) {
  const g = new THREE.Group();
  const gravel = makeMat(tex, "gravel", { color: "#C9C6BF" });
  const asphalt = makeMat(tex, "asphalt", { color: "#9C9A95", normal: 0.5 });
  const conc = makeMat(tex, "concrete", { color: "#CFCCC4" });
  const grass = makeMat(tex, "dry_grass", { color: "#8E8B76", normal: 0.4 });
  // ground: one sheet with a real opening over the drainage ditch (the jeep's wheel drops into it)
  const { x: dx, z0, z1 } = JSA_MARKS.ditch;
  const hw = 0.42; // trench half width incl. its walls
  const sheet = new THREE.Shape([new THREE.Vector2(-1500, -1500), new THREE.Vector2(1500, -1500), new THREE.Vector2(1500, 1500), new THREE.Vector2(-1500, 1500)]); // reaches the flag tower 1 km away
  sheet.holes.push(new THREE.Path([new THREE.Vector2(dx - hw, -z1), new THREE.Vector2(dx + hw, -z1), new THREE.Vector2(dx + hw, -z0), new THREE.Vector2(dx - hw, -z0)])); // shape y = -world z
  const sheetGeo = new THREE.ShapeGeometry(sheet);
  const suv = sheetGeo.attributes.uv as THREE.BufferAttribute;
  for (let i = 0; i < suv.count; i++) suv.setXY(i, suv.getX(i) / 23, suv.getY(i) / 23);
  sheetGeo.rotateX(-Math.PI / 2);
  const ground = mesh(sheetGeo, grass, 0, -0.02, 0);
  ground.castShadow = false;
  ground.userData.ground = true;
  g.add(ground);
  const yardX0 = dx + hw, yardX1 = 61;
  const yard = mesh(plane(yardX1 - yardX0, 76, 3), gravel, (yardX0 + yardX1) / 2, 0.0, 0); // starts right at the ditch's east wall
  yard.castShadow = false;
  yard.userData.ground = true;
  g.add(yard);
  const plaza = mesh(plane(66, 22, 2.5), conc, 23, 0.01, 0);
  plaza.castShadow = false;
  plaza.userData.ground = true;
  g.add(plaza);
  // north-south road on the west side, ending at the ditch's west wall
  const road = mesh(plane(6.2, 240, 7), asphalt, -18.8, 0.015, 0);
  road.castShadow = false;
  road.userData.ground = true;
  g.add(road);
  // the ditch: two walls, a floor and end caps, 0.55 m deep
  const dl = z1 - z0, dz = (z0 + z1) / 2;
  const ditch = new THREE.Group();
  ditch.userData.mount = true; // sunk into the ground on purpose
  ditch.add(mesh(box(0.12, 0.55, dl, 1.5), conc, dx - 0.36, -0.27, dz));
  ditch.add(mesh(box(0.12, 0.55, dl, 1.5), conc, dx + 0.36, -0.27, dz));
  ditch.add(mesh(box(0.84, 0.08, dl, 1.5), makeMat(tex, "concrete", { color: "#8F8C84" }), dx, -0.52, dz));
  for (const z of [z0, z1]) ditch.add(mesh(box(0.84, 0.55, 0.12, 1.5), conc, dx, -0.27, z));
  ditch.traverse((o) => (o.userData.mount = true));
  g.add(ditch);
  // MDL: low concrete curb across the whole area (between the huts too)
  g.add(mesh(box(170, 0.12, 0.5, 1.5), makeMat(tex, "concrete", { color: "#DAD7CE" }), 15, 0.06, 0));
  // conference row: grey, blue, blue, blue, grey ... (T1-T3 blue in the middle)
  const xs = [-4, 5, 14, 23, 32, 41, 50]; // west end ~8 m from the run route, so the huts are in shot
  xs.forEach((x, i) => {
    const hut = conferenceHut(tex, i >= 2 && i <= 4);
    hut.position.set(x, 0, 0);
    g.add(hut);
  });
  const north = northHall(tex);
  north.position.set(23, 0, -52);
  g.add(north);
  const south = southHall(tex);
  south.position.set(23, 0, 48);
  south.rotation.y = Math.PI;
  g.add(south);
  // the wall he falls by, guard booths, lamps
  const w = lowWall(tex, JSA_MARKS.wall.len);
  w.position.set(JSA_MARKS.wall.x, 0, JSA_MARKS.wall.z + 0.35);
  g.add(w);
  for (const [x, z, r] of [[-9, -12, 0], [-9, 12, Math.PI], [60, -10, 0]] as [number, number, number][]) {
    const b = guardBooth(tex);
    b.position.set(x, 0, z);
    b.rotation.y = r;
    g.add(b);
  }
  for (let z = -60; z <= 60; z += 18) {
    const l = lampPost(); // across the road from the run route, arm over the road
    l.position.set(-22.6, 0, z + 4);
    g.add(l);
  }
  // autumn trees along the road and around the halls
  const spots: [number, number, number][] = [];
  for (let z = -70; z <= 70; z += 11) spots.push([-24.5 + ((z * 7) % 3), z, 1], [-10.5, z + 5, 0.85]);
  for (const [x, z] of [[-4, 24], [2, 30], [-2, -26], [8, -30], [50, 30], [62, 24]]) spots.push([x, z, 1.1]);
  spots
    .filter(([x, z]) => !(x > -15 && x < -8 && z > -9 && z < 18)) // keep the run route clear
    .forEach(([x, z, s], i) => {
      const tr = tree(opts.leafMat, i + 1, 8.5 * s, 3.2 * s);
      tr.position.set(x, 0, z);
      tr.rotation.y = i * 1.7;
      g.add(tr);
    });
  if (opts.flagTower) g.add(opts.flagTower);
  return g;
}

/** Kijong-dong flag tower far in the north-west: lattice mast (thin boxes) + a huge flag */
export function flagTower(flag: THREE.Mesh | null) {
  const g = new THREE.Group();
  const m = new THREE.MeshStandardMaterial({ color: "#6E7377", roughness: 0.6, metalness: 0.5 });
  const H = 160;
  for (const [x, z] of [[-2, -2], [2, -2], [2, 2], [-2, 2]]) {
    const leg = new THREE.Mesh(new THREE.BoxGeometry(0.6, H, 0.6), m);
    leg.position.set(x * 0.7, H / 2, z * 0.7);
    g.add(leg);
  }
  for (let y = 6; y < H; y += 9) {
    const bar = new THREE.Mesh(new THREE.BoxGeometry(3.4, 0.35, 3.4), m);
    bar.position.set(0, y, 0);
    bar.userData.mount = true;
    g.add(bar);
  }
  if (flag) {
    const f = flag.clone();
    f.scale.setScalar(13); // 2 x 1 m mesh -> ~26 x 13 m
    f.position.set(1.5, H - 9, 0);
    f.userData.mount = true;
    g.add(f);
    g.userData.flag = f;
  }
  g.position.set(-420, 0, -980);
  return g;
}

// ------------------------------------------------------------------ barracks room (KPA, near the border)
/** red cloth banner with a white Korean slogan, drawn on a canvas */
export function bannerTexture(text = "조국을 위하여!") {
  const c = document.createElement("canvas");
  c.width = 2048;
  c.height = 384;
  const g = c.getContext("2d")!;
  g.fillStyle = "#A3201B";
  g.fillRect(0, 0, c.width, c.height);
  for (let i = 0; i < 2200; i++) {
    g.fillStyle = `rgba(${Math.random() < 0.5 ? "0,0,0" : "255,255,255"},${Math.random() * 0.05})`;
    g.fillRect(Math.random() * c.width, Math.random() * c.height, 2 + Math.random() * 40, 1 + Math.random() * 3);
  }
  g.fillStyle = "#F3EEE2";
  g.font = "bold 230px 'Noto Sans KR','Malgun Gothic','Apple SD Gothic Neo',sans-serif";
  g.textAlign = "center";
  g.textBaseline = "middle";
  g.fillText(text, c.width / 2, c.height / 2 + 10);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}

export const BARRACKS_MARKS = {
  seat: new THREE.Vector3(0.0, 0, 0.55), // the player's stool, facing -Z over the table
  eye: new THREE.Vector3(0.0, 1.22, 0.62),
  table: new THREE.Vector3(0, 0.76, -0.15), // table top centre
  cup: new THREE.Vector3(0.16, 0.76, 0.12),
  window: new THREE.Vector3(-2.0, 1.6, -1.2),
};

export function buildBarracks(tex: Tex, cup: THREE.Object3D | null) {
  const g = new THREE.Group();
  const W = 4.2, L = 6.4, H = 2.9;
  const wall = makeMat(tex, "plaster_green", { color: "#C8D3C0", rough: 0.92 });
  const wallLow = makeMat(tex, "plaster_green", { color: "#6F8466", rough: 0.85 });
  const floor = makeMat(tex, "floor_paint", { rough: 0.8 });
  const ceil = makeMat(tex, "concrete", { color: "#E6E4DD" });
  const fl = mesh(plane(W, L, 1.6), floor, 0, 0, 0);
  fl.userData.ground = true;
  g.add(fl);
  const ce = mesh(plane(W, L, 2), ceil, 0, H, 0);
  ce.rotation.x = Math.PI; // face down
  ce.userData.mount = true;
  g.add(ce);
  // walls (inner faces) with a darker painted lower band; the west wall has a window opening
  const wallAt = (w: number, x: number, z: number, ry: number) => {
    const part = new THREE.Group();
    part.add(mesh(box(w, H - 1.2, 0.12, 1.6), wall, 0, 1.2 + (H - 1.2) / 2, 0));
    part.add(mesh(box(w, 1.2, 0.12, 1.6), wallLow, 0, 0.6, 0));
    part.position.set(x, 0, z);
    part.rotation.y = ry;
    g.add(part);
  };
  wallAt(W, 0, -L / 2, 0);
  wallAt(W, 0, L / 2, Math.PI);
  wallAt(L, W / 2, 0, -Math.PI / 2);
  // west wall: two pieces around a window 1.3 x 1.1 m
  const wx = -W / 2;
  const seg = (z0: number, z1: number) => {
    const p = new THREE.Group();
    const w = z1 - z0;
    p.add(mesh(box(w, H - 1.2, 0.12, 1.6), wall, 0, 1.2 + (H - 1.2) / 2, 0));
    p.add(mesh(box(w, 1.2, 0.12, 1.6), wallLow, 0, 0.6, 0));
    p.position.set(wx, 0, (z0 + z1) / 2);
    p.rotation.y = Math.PI / 2;
    g.add(p);
  };
  const wz = BARRACKS_MARKS.window.z;
  seg(-L / 2, wz - 0.65);
  seg(wz + 0.65, L / 2);
  const sill = new THREE.Group();
  sill.add(mesh(box(1.3, 1.05, 0.12, 1.6), wallLow, 0, 0.525, 0));
  sill.add(mesh(box(1.3, H - 2.15, 0.12, 1.6), wall, 0, 2.15 + (H - 2.15) / 2, 0));
  sill.add(mesh(new THREE.BoxGeometry(1.3, 0.05, 0.08), WHITE, 0, 2.15, 0.04));
  sill.add(mesh(new THREE.BoxGeometry(1.3, 0.05, 0.08), WHITE, 0, 1.075, 0.04));
  sill.add(mesh(new THREE.BoxGeometry(0.05, 1.1, 0.08), WHITE, 0, 1.6, 0.04));
  sill.children.slice(2).forEach((c) => (c.userData.mount = true)); // window frame bars sit in the opening
  sill.position.set(wx, 0, wz);
  sill.rotation.y = Math.PI / 2;
  g.add(sill);
  // iron bunk beds along the east wall
  const iron = new THREE.MeshStandardMaterial({ color: "#3E4A44", roughness: 0.55, metalness: 0.5 });
  const blanket = new THREE.MeshStandardMaterial({ color: "#5D6449", roughness: 1 });
  const sheet = new THREE.MeshStandardMaterial({ color: "#D9D6CB", roughness: 1 });
  for (const z of [-1.9, 0.6]) {
    const b = new THREE.Group();
    for (const [x, zz] of [[-0.42, -0.95], [0.42, -0.95], [-0.42, 0.95], [0.42, 0.95]]) b.add(mesh(new THREE.CylinderGeometry(0.022, 0.022, 1.75, 8), iron, x, 0.875, zz));
    for (const y of [0.42, 1.3]) {
      const deck = mesh(new THREE.BoxGeometry(0.88, 0.04, 1.95), iron, 0, y, 0);
      if (y > 1) deck.userData.mount = true; // the upper bunk is carried by the corner posts
      b.add(deck);
      b.add(mesh(new THREE.BoxGeometry(0.8, 0.12, 1.88), blanket, 0, y + 0.08, 0));
      b.add(mesh(new THREE.BoxGeometry(0.5, 0.1, 0.32), sheet, 0, y + 0.18, -0.72));
    }
    b.position.set(W / 2 - 0.55, 0, z);
    g.add(b);
  }
  // wooden table, stools, foot lockers
  const wood = new THREE.MeshStandardMaterial({ color: "#7A5A3C", roughness: 0.75 });
  const t = BARRACKS_MARKS.table;
  g.add(mesh(new THREE.BoxGeometry(1.5, 0.05, 0.8), wood, t.x, t.y - 0.025, t.z));
  for (const [x, z] of [[-0.68, -0.32], [0.68, -0.32], [-0.68, 0.32], [0.68, 0.32]]) g.add(mesh(new THREE.BoxGeometry(0.06, t.y - 0.05, 0.06), wood, t.x + x, (t.y - 0.05) / 2, t.z + z));
  for (const [x, z] of [[0, 0.55], [-0.45, -0.75], [0.5, -0.78]]) {
    g.add(mesh(new THREE.BoxGeometry(0.36, 0.04, 0.36), wood, x, 0.46, z));
    for (const [a, b2] of [[-0.15, -0.15], [0.15, -0.15], [-0.15, 0.15], [0.15, 0.15]]) g.add(mesh(new THREE.BoxGeometry(0.035, 0.44, 0.035), wood, x + a, 0.22, z + b2));
  }
  for (const z of [-2.6, -1.2]) g.add(mesh(new THREE.BoxGeometry(0.55, 0.35, 0.4), new THREE.MeshStandardMaterial({ color: "#4F5B3E", roughness: 0.8 }), W / 2 - 1.35, 0.175, z));
  // on the table: soju bottles, bowl of corn, the aluminium cup
  const bottleGlass = new THREE.MeshPhysicalMaterial({ color: "#2F7A4C", roughness: 0.12, transmission: 0.0, metalness: 0.1, transparent: true, opacity: 0.88 });
  const label = new THREE.MeshStandardMaterial({ color: "#E8E2CF", roughness: 0.8 });
  const bottle = () => {
    const b = new THREE.Group();
    b.add(mesh(new THREE.CylinderGeometry(0.034, 0.034, 0.16, 18), bottleGlass, 0, 0.08, 0));
    b.add(mesh(new THREE.CylinderGeometry(0.014, 0.034, 0.05, 18), bottleGlass, 0, 0.185, 0));
    b.add(mesh(new THREE.CylinderGeometry(0.0135, 0.0135, 0.04, 12), bottleGlass, 0, 0.23, 0));
    b.add(mesh(new THREE.CylinderGeometry(0.0352, 0.0352, 0.07, 18, 1, true), label, 0, 0.08, 0));
    return b;
  };
  for (const [x, z, tip] of [[-0.32, -0.28, 0], [-0.22, -0.36, 0], [0.42, -0.2, 1.57]] as [number, number, number][]) {
    const b = bottle();
    b.name = "bottle";
    b.userData.base = { x: t.x + x, z: t.z + z, tip };
    if (tip) {
      b.rotation.z = tip;
      b.position.set(t.x + x, t.y + 0.034, t.z + z);
    } else b.position.set(t.x + x, t.y, t.z + z);
    g.add(b);
  }
  const bowl = mesh(new THREE.SphereGeometry(0.1, 20, 10, 0, Math.PI * 2, Math.PI / 2, Math.PI / 2), new THREE.MeshStandardMaterial({ color: "#B9BBB6", roughness: 0.35, metalness: 0.7, side: THREE.DoubleSide }), t.x + 0.05, t.y + 0.1, t.z - 0.18);
  g.add(bowl);
  const corn = new THREE.MeshStandardMaterial({ color: "#E2B73F", roughness: 0.6 });
  for (let i = 0; i < 3; i++) {
    const c = mesh(new THREE.CapsuleGeometry(0.022, 0.12, 4, 10), corn, t.x + 0.02 + i * 0.03, t.y + 0.06, t.z - 0.18 + (i - 1) * 0.02);
    c.rotation.z = Math.PI / 2 + (i - 1) * 0.3;
    g.add(c);
  }
  if (cup) {
    const c = cup.clone();
    c.position.copy(BARRACKS_MARKS.cup);
    g.add(c);
  }
  // slogan banner on the north wall + a bare bulb
  const banner = mesh(new THREE.PlaneGeometry(2.6, 0.48), new THREE.MeshStandardMaterial({ map: bannerTexture(), roughness: 0.95, side: THREE.DoubleSide }), 0, 1.45, -L / 2 + 0.07); // below the caption band in the FP shots
  banner.userData.mount = true;
  g.add(banner);
  const cord = mesh(new THREE.CylinderGeometry(0.004, 0.004, 0.5, 6), DARK, 0, H - 0.25, -0.2);
  const bulb = mesh(new THREE.SphereGeometry(0.04, 16, 12), new THREE.MeshStandardMaterial({ color: "#FFF3D6", emissive: "#FFDFA3", emissiveIntensity: 2.2 }), 0, H - 0.52, -0.2);
  cord.userData.mount = bulb.userData.mount = true; // hangs from the ceiling
  g.add(cord, bulb);
  return g;
}

// ------------------------------------------------------------------ QA: nothing may float
/**
 * Every mesh that is not tagged `userData.mount` (attached to a wall / hanging on purpose) and not ground must rest on
 * something: from 5 points under its bottom (centre + inset corners) a ray goes down; if none finds a surface within
 * `tol` metres (or starts inside another object = overlapping support), the mesh is reported as floating.
 */
export function findFloaters(root: THREE.Object3D, tol = 0.03) {
  root.updateMatrixWorld(true);
  const solids: THREE.Mesh[] = [];
  const checks: { m: THREE.Mesh; path: string }[] = [];
  const walk = (o: THREE.Object3D, path: string, mounted: boolean) => {
    const here = path + "/" + (o.name || o.type);
    const mnt = mounted || !!o.userData.mount;
    const m = o as THREE.Mesh;
    if (m.isMesh && !(m as THREE.InstancedMesh).isInstancedMesh) {
      solids.push(m);
      if (!mnt && !o.userData.ground) checks.push({ m, path: here });
    }
    o.children.forEach((c) => walk(c, here, mnt));
  };
  walk(root, "", false);
  const boxes = new Map(solids.map((m) => [m, new THREE.Box3().setFromObject(m)]));
  const ray = new THREE.Raycaster();
  const down = new THREE.Vector3(0, -1, 0);
  const bad: { path: string; gap: number; at: THREE.Vector3; what: string }[] = [];
  for (const { m, path } of checks) {
    const b = boxes.get(m)!;
    const c = b.getCenter(new THREE.Vector3());
    const sx = (b.max.x - b.min.x) * 0.46, sz = (b.max.z - b.min.z) * 0.46;
    let best = Infinity;
    // something touching its underside (legs under a table top, columns under a beam, posts through a bunk deck)
    const foot = new THREE.Box3(new THREE.Vector3(b.min.x + 0.005, b.min.y - tol, b.min.z + 0.005), new THREE.Vector3(b.max.x - 0.005, b.min.y + tol, b.max.z - 0.005));
    if (solids.some((s) => s !== m && !s.userData.ground && boxes.get(s)!.intersectsBox(foot) && boxes.get(s)!.min.y < b.min.y - 0.002)) best = 0;
    for (const [ox, oz] of best === 0 ? [] : [[0, 0], [-sx, -sz], [sx, -sz], [-sx, sz], [sx, sz]]) {
      const p = new THREE.Vector3(c.x + ox, b.min.y + 0.01, c.z + oz);
      // starts inside another object (overlap = support, e.g. a pole set into a base)
      const inside = solids.some((s) => s !== m && boxes.get(s)!.clone().expandByScalar(0.01).containsPoint(p) && !s.userData.ground);
      if (inside) {
        best = 0;
        break;
      }
      ray.set(p, down);
      ray.far = 50;
      const hit = ray.intersectObjects(solids.filter((s) => s !== m), false)[0];
      if (hit) best = Math.min(best, hit.distance - 0.01);
    }
    if (best > tol) {
      const g = m.geometry as THREE.BufferGeometry & { parameters?: Record<string, number> };
      const prm = g.parameters ? Object.entries(g.parameters).filter(([, v]) => typeof v === "number").slice(0, 3).map(([k, v]) => `${k}=${(+v).toFixed(2)}`).join(",") : "";
      const what = `${g.type}(${prm}) at (${c.x.toFixed(2)},${c.y.toFixed(2)},${c.z.toFixed(2)}) y=${b.min.y.toFixed(2)}..${b.max.y.toFixed(2)}`;
      bad.push({ path, gap: best, at: c, what });
    }
  }
  return bad;
}

// ------------------------------------------------------------------ QA: no body passes through the set
/** boxes of every solid object in a set (walls, huts, booths, trunks, posts...), for body-vs-set checks */
export function solidBoxes(root: THREE.Object3D) {
  root.updateMatrixWorld(true);
  const out: { box: THREE.Box3; name: string }[] = [];
  const walk = (o: THREE.Object3D, path: string) => {
    const here = path + "/" + (o.name || o.type);
    if (o.userData.ground || o.name === "leaf_pile" || o.name === "leaf_scatter") return;
    const m = o as THREE.Mesh;
    if (m.isMesh && !(m as THREE.InstancedMesh).isInstancedMesh) {
      const b = new THREE.Box3().setFromObject(m);
      const s = b.getSize(new THREE.Vector3());
      if (s.x > 0.04 && s.y > 0.04 && s.z > 0.04) out.push({ box: b.expandByScalar(-0.02), name: `${(m.geometry as THREE.BufferGeometry).type} at (${b.getCenter(new THREE.Vector3()).toArray().map((v) => v.toFixed(1)).join(",")})` });
    }
    o.children.forEach((c) => walk(c, here));
  };
  walk(root, "");
  return out;
}
/** first joint of `body` found inside a solid box, or null */
export function jointInside(body: THREE.Object3D, solids: { box: THREE.Box3; name: string }[]) {
  let hit: { joint: string; solid: string } | null = null;
  body.traverse((o) => {
    if (hit || !(o as THREE.Bone).isBone) return;
    const p = o.getWorldPosition(new THREE.Vector3());
    const s = solids.find((x) => x.box.containsPoint(p));
    if (s) hit = { joint: o.name, solid: s.name };
  });
  return hit as { joint: string; solid: string } | null;
}
