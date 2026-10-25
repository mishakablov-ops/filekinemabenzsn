/**
 * Extra sets and props for "Сосед с шестого этажа" (series 1), modelled in code (PS1 look applied by psxify):
 * the welded attic hatch over the 5th-floor landing, the hero's room extras (chandelier that sways, wall clock,
 * ceiling crack, the palm-shaped stain, a camcorder on a tripod), the 24-box mail block with box 24 open,
 * the flat's hallway with light under the front door, and the 1974 photo (front image + handwritten back).
 */
import * as THREE from "three";
import { mergeGeometries } from "three/examples/jsm/utils/BufferGeometryUtils.js";
import { FLOOR, FLOOR_H, labelTex, LOBBY_Y, SH, texMat, type Tex } from "./podezdSets";

const at = (g: THREE.BufferGeometry, x: number, y: number, z: number, ry = 0, rx = 0, rz = 0) =>
  g.clone().applyMatrix4(new THREE.Matrix4().compose(new THREE.Vector3(x, y, z), new THREE.Quaternion().setFromEuler(new THREE.Euler(rx, ry, rz)), new THREE.Vector3(1, 1, 1)));
const mk = (g: THREE.BufferGeometry, m: THREE.Material | THREE.Material[], cast = true) => {
  const o = new THREE.Mesh(g, m);
  o.castShadow = cast;
  o.receiveShadow = true;
  return o;
};
const canvasTex = (w: number, h: number, draw: (g: CanvasRenderingContext2D) => void) => {
  const c = document.createElement("canvas");
  c.width = w;
  c.height = h;
  draw(c.getContext("2d")!);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
};
const rnd = (seed: number) => () => ((seed = (seed * 16807) % 2147483647) - 1) / 2147483646;
const HAND = "'Segoe Script', 'Comic Sans MS', cursive";

// ------------------------------------------------------------------ the attic hatch over the top landing
/** steel hatch welded shut, padlock, "1998" painted on it, fresh scratches and a dent pushed from the inside.
 *  Returned group sits in stairwell coordinates under the ceiling of the top floor (floors = 5). */
export function buildHatch(tex: Tex, floors = 5) {
  const g = new THREE.Group();
  const top = FLOOR(floors) + FLOOR_H - 0.2;
  const cx = 0.75, cz = 1.12, W = 0.72, D = 0.62;
  const steel = texMat(tex, "metal_paint", { color: "#6C6F66", rough: 0.6, metal: 0.4 });
  // the lid: a subdivided plate with a dent bulging downward (pushed from above)
  const lidG = new THREE.PlaneGeometry(W, D, 16, 14);
  const lp = lidG.attributes.position as THREE.BufferAttribute;
  for (let i = 0; i < lp.count; i++) {
    const x = lp.getX(i), y = lp.getY(i);
    const r = Math.hypot((x - 0.08) / 0.18, (y + 0.05) / 0.14);
    lp.setZ(i, r < 1 ? Math.cos(r * Math.PI * 0.5) * 0.035 : 0);
  }
  lidG.computeVertexNormals();
  const lid = mk(lidG, steel, false);
  lid.rotation.x = Math.PI / 2; // faces down
  lid.position.set(cx, top - 0.012, cz);
  g.add(lid);
  // frame + weld beads along the seam
  const frame = texMat(tex, "metal_paint", { color: "#4E4F48", rough: 0.6, metal: 0.4 });
  g.add(mk(mergeGeometries([
    at(new THREE.BoxGeometry(W + 0.1, 0.04, 0.05), cx, top - 0.02, cz - D / 2 - 0.025),
    at(new THREE.BoxGeometry(W + 0.1, 0.04, 0.05), cx, top - 0.02, cz + D / 2 + 0.025),
    at(new THREE.BoxGeometry(0.05, 0.04, D), cx - W / 2 - 0.025, top - 0.02, cz),
    at(new THREE.BoxGeometry(0.05, 0.04, D), cx + W / 2 + 0.025, top - 0.02, cz),
  ]), frame));
  const r = rnd(41);
  const beads: THREE.BufferGeometry[] = [];
  const bead = new THREE.SphereGeometry(0.012, 5, 4);
  for (let i = 0; i < 70; i++) {
    const side = i % 4, k = r();
    const x = side < 2 ? cx - W / 2 + k * W : cx + (side === 2 ? -W / 2 : W / 2);
    const z = side < 2 ? cz + (side === 0 ? -D / 2 : D / 2) : cz - D / 2 + k * D;
    beads.push(at(bead, x, top - 0.035, z));
  }
  g.add(mk(mergeGeometries(beads), new THREE.MeshStandardMaterial({ color: "#3A2A1E", roughness: 0.8, metalness: 0.3 })));
  // padlock
  const lockM = new THREE.MeshStandardMaterial({ color: "#5B4A32", roughness: 0.5, metalness: 0.6 });
  g.add(mk(mergeGeometries([at(new THREE.BoxGeometry(0.06, 0.07, 0.025), cx - W / 2 + 0.08, top - 0.12, cz + D / 2 + 0.06), at(new THREE.TorusGeometry(0.022, 0.005, 6, 12, Math.PI), cx - W / 2 + 0.08, top - 0.085, cz + D / 2 + 0.06)]), lockM));
  // painted year + scratches on the underside of the lid
  const paint = canvasTex(512, 448, (c) => {
    c.clearRect(0, 0, 512, 448);
    c.fillStyle = "rgba(235,232,220,0.9)";
    c.font = "bold 110px Arial";
    c.textAlign = "center";
    c.fillText("1998", 256, 150);
    // fingernail marks: groups of four fanned, curved, tapering strokes at different angles, paint chipped around them
    const rr = rnd(7);
    const groups: [number, number, number, number][] = [[120, 215, -0.5, 1], [300, 200, 0.35, 0.9], [215, 300, -0.1, 1.15], [400, 300, 0.7, 0.75], [70, 330, -0.9, 0.8], [330, 390, 0.15, 0.7]];
    for (const [gx, gy, ang, len] of groups) {
      for (let f = 0; f < 4; f++) {
        const ox = (f - 1.5) * 13 * (0.8 + rr() * 0.4);
        const L = (95 + rr() * 50) * len * (f === 0 || f === 3 ? 0.8 : 1);
        const bend = (rr() - 0.4) * 22;
        const pts: [number, number][] = [];
        for (let i = 0; i <= 12; i++) {
          const u = i / 12;
          const x = ox + bend * u * u, y = u * L;
          pts.push([gx + x * Math.cos(ang) - y * Math.sin(ang), gy + x * Math.sin(ang) + y * Math.cos(ang)]);
        }
        for (let i = 0; i < 12; i++) {
          const u = i / 12;
          c.strokeStyle = `rgba(212,206,194,${(0.85 - u * 0.5).toFixed(2)})`;
          c.lineWidth = Math.max(1, 5.5 * (1 - u * 0.8));
          c.beginPath();
          c.moveTo(...pts[i]);
          c.lineTo(...pts[i + 1]);
          c.stroke();
        }
        // flakes of paint torn off at the start of the stroke
        c.fillStyle = "rgba(190,180,165,0.55)";
        for (let k = 0; k < 3; k++) c.fillRect(pts[0][0] + (rr() - 0.5) * 10, pts[0][1] + (rr() - 0.5) * 8, 2 + rr() * 3, 2 + rr() * 2);
      }
    }
  });
  // the paint lives on the lid's own surface (same geometry, child of the lid), so it bends with the dent
  paint.center.set(0.5, 0.5);
  paint.rotation = Math.PI; // reads upright from the ladder
  const dec = new THREE.Mesh(lidG, new THREE.MeshStandardMaterial({ map: paint, transparent: true, roughness: 0.8, polygonOffset: true, polygonOffsetFactor: -4, polygonOffsetUnits: -4 }));
  dec.position.z = 0.003;
  lid.add(dec);
  // vertical steel ladder from the landing to the hatch
  const railM = new THREE.MeshStandardMaterial({ color: "#2E3330", roughness: 0.5, metalness: 0.6 });
  const lad: THREE.BufferGeometry[] = [];
  const y0 = FLOOR(floors), H = top - y0;
  const LZ = cz - D / 2 - 0.1; // on the landing side of the hatch (the other side is the open stair well)
  for (const x of [cx - 0.22, cx + 0.22]) lad.push(at(new THREE.BoxGeometry(0.035, H, 0.035), x, y0 + H / 2, LZ));
  for (let y = y0 + 0.3; y < top - 0.15; y += 0.3) lad.push(at(new THREE.CylinderGeometry(0.012, 0.012, 0.44, 6), cx, y, LZ, 0, 0, Math.PI / 2));
  g.add(mk(mergeGeometries(lad), railM));
  g.traverse((o) => (o.userData.mount = true));
  lid.scale.z = 0; // the dent appears when it is pushed from above
  return { g, lid, centre: new THREE.Vector3(cx, top, cz), ladderZ: LZ, rungs: (() => { const r: number[] = []; for (let y = y0 + 0.3; y < top - 0.15; y += 0.3) r.push(y); return r; })() };
}

// ------------------------------------------------------------------ the hero's room extras (in bedroom coordinates)
function clockTex() {
  return canvasTex(256, 256, (c) => {
    c.fillStyle = "#E8E2D2";
    c.beginPath();
    c.arc(128, 128, 124, 0, 7);
    c.fill();
    c.strokeStyle = "#2A2A2A";
    c.lineWidth = 8;
    c.stroke();
    c.fillStyle = "#1C1C1C";
    c.font = "bold 30px Arial";
    c.textAlign = "center";
    c.textBaseline = "middle";
    for (let i = 1; i <= 12; i++) {
      const a = (i / 12) * Math.PI * 2 - Math.PI / 2;
      c.fillText(String(i), 128 + Math.cos(a) * 96, 128 + Math.sin(a) * 96);
    }
  });
}
function crackTex(seed: number) {
  return canvasTex(512, 512, (c) => {
    c.clearRect(0, 0, 512, 512);
    const r = rnd(seed);
    const branch = (x: number, y: number, a: number, len: number, w: number, d: number) => {
      c.strokeStyle = `rgba(22,18,14,${0.75 + r() * 0.25})`;
      c.lineWidth = w;
      c.beginPath();
      c.moveTo(x, y);
      let px = x, py = y;
      for (let i = 0; i < 8; i++) {
        a += (r() - 0.5) * 0.7;
        px += Math.cos(a) * len / 8;
        py += Math.sin(a) * len / 8;
        c.lineTo(px, py);
      }
      c.stroke();
      if (d > 0) for (let k = 0; k < 2; k++) branch(px, py, a + (r() - 0.5) * 1.6, len * 0.55, w * 0.6, d - 1);
    };
    branch(20, 260, 0.05, 300, 10, 3);
  });
}
/** a damp yellow-brown stain in the shape of an open palm (fingers spread), soft edges */
function palmStainTex() {
  return canvasTex(512, 512, (c) => {
    c.clearRect(0, 0, 512, 512);
    const draw = (blur: number, a: number, grow: number) => {
      c.filter = `blur(${blur}px)`;
      c.fillStyle = `rgba(92,70,36,${a})`;
      c.beginPath();
      c.ellipse(256, 330, 78 + grow, 98 + grow, 0, 0, 7);
      c.fill();
      const fingers: [number, number, number, number][] = [[196, 268, -0.42, 118], [232, 246, -0.16, 152], [268, 240, 0.05, 162], [304, 250, 0.26, 146], [178, 360, -1.15, 112]];
      for (const [x, y, rot, len] of fingers) {
        c.save();
        c.translate(x, y);
        c.rotate(rot);
        c.beginPath();
        c.ellipse(0, -len * 0.42, 21 + grow * 0.4, len * 0.52 + grow * 0.4, 0, 0, 7);
        c.fill();
        c.restore();
      }
    };
    draw(14, 0.3, 12);
    draw(4, 0.45, 0);
    c.globalCompositeOperation = "destination-out";
    draw(10, 0.35, -14); // lighter middle: the water dried from the centre, the edge stays dark
    c.globalCompositeOperation = "source-over";
    c.filter = "none";
  });
}
export function camcorder() {
  const g = new THREE.Group();
  const body = new THREE.MeshStandardMaterial({ color: "#1F2022", roughness: 0.5, metalness: 0.3 });
  const cam = new THREE.Group();
  cam.add(mk(new THREE.BoxGeometry(0.1, 0.11, 0.22), body));
  cam.add(mk(at(new THREE.CylinderGeometry(0.035, 0.04, 0.09, 16), 0, 0.005, -0.15, 0, Math.PI / 2), body));
  const glass = new THREE.Mesh(new THREE.CircleGeometry(0.03, 16), new THREE.MeshStandardMaterial({ color: "#1A2433", roughness: 0.05, metalness: 0.8 }));
  glass.position.set(0, 0.005, -0.196);
  glass.rotation.y = Math.PI;
  cam.add(glass);
  cam.add(mk(at(new THREE.BoxGeometry(0.008, 0.06, 0.08), 0.055, 0.0, 0.02), body)); // flip screen (closed)
  const recBtn = new THREE.Mesh(new THREE.CylinderGeometry(0.008, 0.008, 0.006, 10), new THREE.MeshStandardMaterial({ color: "#B01A12", roughness: 0.4 }));
  recBtn.rotation.x = Math.PI / 2;
  recBtn.position.set(0.0, 0.0, 0.112);
  cam.add(recBtn);
  const led = new THREE.Mesh(new THREE.SphereGeometry(0.005, 8, 6), new THREE.MeshStandardMaterial({ color: "#FF2A1A", emissive: "#FF2A1A", emissiveIntensity: 2 }));
  led.position.set(0.0, 0.06, -0.08);
  cam.add(led);
  cam.position.y = 1.32;
  g.add(cam);
  const legM = new THREE.MeshStandardMaterial({ color: "#2A2B2D", roughness: 0.4, metalness: 0.6 });
  const legs: THREE.BufferGeometry[] = [];
  for (let i = 0; i < 3; i++) {
    const a = (i / 3) * Math.PI * 2;
    const foot = new THREE.Vector3(Math.cos(a) * 0.32, 0, Math.sin(a) * 0.32), head = new THREE.Vector3(0, 1.25, 0);
    const len = foot.distanceTo(head);
    const c = new THREE.CylinderGeometry(0.012, 0.012, len, 6);
    c.translate(0, len / 2, 0);
    c.applyQuaternion(new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 1, 0), head.clone().sub(foot).normalize()));
    c.translate(foot.x, foot.y, foot.z);
    legs.push(c);
  }
  legs.push(at(new THREE.CylinderGeometry(0.03, 0.03, 0.06, 10), 0, 1.25, 0));
  g.add(mk(mergeGeometries(legs), legM));
  return { g, cam, led, recBtn };
}
/** chandelier (swings around its ceiling hook), wall clock (second hand), crack + palm stain on the ceiling, camcorder on a tripod */
export function heroRoomExtras(tex: Tex, room: { X: number; Z: number; H: number } = { X: 1.6, Z: 2.1, H: 2.6 }) {
  const g = new THREE.Group();
  const { X, Z, H } = room;
  // chandelier: rod + three arms with glass shades
  const pivot = new THREE.Group();
  pivot.position.set(0.1, H, -0.2);
  const brass = new THREE.MeshStandardMaterial({ color: "#8E7444", roughness: 0.35, metalness: 0.8 });
  const shadeM = new THREE.MeshStandardMaterial({ color: "#E9DFC6", emissive: "#FFD9A0", emissiveIntensity: 0, roughness: 0.4, transparent: true, opacity: 0.92 });
  const parts: THREE.BufferGeometry[] = [at(new THREE.CylinderGeometry(0.008, 0.008, 0.5, 6), 0, -0.25, 0), at(new THREE.SphereGeometry(0.04, 10, 8), 0, -0.52, 0)];
  const shades: THREE.BufferGeometry[] = [];
  for (let i = 0; i < 3; i++) {
    const a = (i / 3) * Math.PI * 2;
    parts.push(at(new THREE.CylinderGeometry(0.006, 0.006, 0.26, 6), Math.cos(a) * 0.12, -0.53, Math.sin(a) * 0.12, -a, 0, Math.PI / 2));
    shades.push(at(new THREE.CylinderGeometry(0.05, 0.075, 0.1, 10, 1, true), Math.cos(a) * 0.24, -0.5, Math.sin(a) * 0.24));
  }
  pivot.add(mk(mergeGeometries(parts), brass), mk(mergeGeometries(shades), shadeM));
  g.add(pivot);
  // wall clock on the back wall
  const clock = new THREE.Group();
  clock.add(new THREE.Mesh(new THREE.CircleGeometry(0.16, 32), new THREE.MeshStandardMaterial({ map: clockTex(), roughness: 0.5 })));
  const handM = new THREE.MeshStandardMaterial({ color: "#151515" });
  const hourH = new THREE.Mesh(new THREE.BoxGeometry(0.012, 0.08, 0.004), handM);
  hourH.geometry.translate(0, 0.035, 0.004);
  hourH.rotation.z = -(3 / 12) * Math.PI * 2 - (12 / 60) * (Math.PI / 6); // 3:12
  const minH = new THREE.Mesh(new THREE.BoxGeometry(0.008, 0.12, 0.004), handM);
  minH.geometry.translate(0, 0.055, 0.006);
  minH.rotation.z = -(12 / 60) * Math.PI * 2;
  const secH = new THREE.Mesh(new THREE.BoxGeometry(0.004, 0.13, 0.003), new THREE.MeshStandardMaterial({ color: "#A01010" }));
  secH.geometry.translate(0, 0.055, 0.008);
  clock.add(hourH, minH, secH);
  clock.position.set(0.35, 1.95, -Z + 0.01);
  g.add(clock);
  // ceiling: a long crack and (morning only) the palm stain over the bed
  const crackMap = crackTex(5);
  const crackGeo = new THREE.PlaneGeometry(1.6, 1.6);
  crackGeo.translate(0.8, 0, 0); // pivot on the left edge so it can grow
  const crack = new THREE.Mesh(crackGeo, new THREE.MeshStandardMaterial({ map: crackMap, transparent: true, roughness: 1, depthWrite: false, polygonOffset: true, polygonOffsetFactor: -2 }));
  crack.rotation.x = Math.PI / 2;
  crack.position.set(-1.0, H - 0.003, -0.8);
  g.add(crack);
  const setCrack = (k: number) => {
    const c = Math.max(0.001, Math.min(1, k));
    crack.scale.x = c;
    crackMap.repeat.set(c, 1);
    crackMap.offset.set(0, 0);
  };
  // the ceiling pressed down from above in the shape of a hand
  const BW = 0.8;
  const bulgeGeo = new THREE.PlaneGeometry(BW, BW, 40, 40);
  const bp = bulgeGeo.attributes.position as THREE.BufferAttribute;
  const base = Float32Array.from(bp.array as Float32Array);
  const palmMask = (x: number, y: number) => {
    const e = (cx: number, cy: number, rx: number, ry: number, rot = 0) => {
      const c = Math.cos(rot), s2 = Math.sin(rot);
      const dx = (x - cx) * c + (y - cy) * s2, dy = -(x - cx) * s2 + (y - cy) * c;
      const r = Math.hypot(dx / rx, dy / ry);
      return r < 1 ? Math.cos(r * Math.PI * 0.5) : 0;
    };
    let m = e(0, -0.07, 0.085, 0.1);
    for (const [cx, cy, rot, len] of [[-0.1, 0.02, 0.75, 0.07], [-0.05, 0.09, 0.22, 0.09], [0.0, 0.11, 0, 0.1], [0.05, 0.09, -0.2, 0.09], [0.1, 0.03, -0.55, 0.065]] as [number, number, number, number][])
      m = Math.max(m, e(cx + Math.sin(-rot) * len * 0.5, cy + Math.cos(rot) * len * 0.5, 0.022, len, rot));
    return m;
  };
  const bulge = new THREE.Mesh(bulgeGeo, texMat(tex, "whitewash", { rough: 0.95 }));
  bulge.rotation.x = Math.PI / 2;
  bulge.position.set(0.45, H - 0.002, -1.15); // right above where he stops (WALK_B in sosedShots)
  bulge.receiveShadow = true;
  g.add(bulge);
  const setBulge = (k: number) => {
    for (let i = 0; i < bp.count; i++) bp.setZ(i, base[i * 3 + 2] + palmMask(base[i * 3], base[i * 3 + 1]) * 0.05 * k);
    bp.needsUpdate = true;
    bulgeGeo.computeVertexNormals();
  };
  // bare footprints in grime walking across the ceiling, one by one
  const footTex = canvasTex(128, 256, (c) => {
    c.clearRect(0, 0, 128, 256);
    c.fillStyle = "rgba(26,19,13,0.95)";
    c.filter = "blur(2px)";
    c.beginPath();
    c.ellipse(64, 170, 34, 62, 0, 0, 7);
    c.fill();
    for (const [x, y, r] of [[38, 62, 15], [62, 52, 12], [82, 56, 11], [98, 66, 10], [110, 82, 9]] as [number, number, number][]) {
      c.beginPath();
      c.arc(x, y, r, 0, 7);
      c.fill();
    }
  });
  const prints: { m: THREE.Mesh; mat: THREE.MeshStandardMaterial }[] = [];
  for (let i = 0; i < 8; i++) {
    const mat = new THREE.MeshStandardMaterial({ map: footTex, transparent: true, opacity: 0, roughness: 1, depthWrite: false, polygonOffset: true, polygonOffsetFactor: -3 });
    const m = new THREE.Mesh(new THREE.PlaneGeometry(0.13, 0.28), mat);
    m.rotation.set(Math.PI / 2, 0, 0.5);
    if (i % 2) m.scale.x = -1;
    m.position.set(0.9 - i * 0.22 + (i % 2 ? 0.07 : -0.07) * 0.6, H - 0.004, 1.2 - i * 0.3 + (i % 2 ? 0.06 : -0.06));
    g.add(m);
    prints.push({ m, mat });
  }
  const setPrints = (t: number, t0: number, every = 0.28) => prints.forEach((p, i) => (p.mat.opacity = t >= t0 + i * every ? Math.min(1, (t - t0 - i * every) * 8) : 0));
  const stainM = new THREE.MeshStandardMaterial({ map: palmStainTex(), transparent: true, opacity: 0, roughness: 1, depthWrite: false, polygonOffset: true, polygonOffsetFactor: -3 });
  const stain = new THREE.Mesh(new THREE.PlaneGeometry(0.62, 0.62), stainM);
  stain.rotation.x = Math.PI / 2;
  stain.rotation.z = 0.4;
  stain.position.set(-X + 0.55, H - 0.004, -Z + 0.85);
  g.add(stain);
  // camcorder on its tripod in the front-left corner, looking across the room
  const cc = camcorder();
  cc.g.position.set(-X + 0.45, 0, Z - 0.4);
  cc.g.rotation.y = Math.atan2(-1.45, 2.3); // lens (local -Z) toward the room centre and the back wall
  g.add(cc.g);
  // dust that falls from the ceiling
  const dust: THREE.Mesh[] = [];
  const dm = new THREE.MeshBasicMaterial({ color: "#D8D2C4", transparent: true, opacity: 0.85 });
  for (let i = 0; i < 40; i++) {
    const d = new THREE.Mesh(new THREE.BoxGeometry(0.007, 0.007, 0.007), dm);
    d.visible = false;
    g.add(d);
    dust.push(d);
  }
  /** steps above: each step at (x,z,time) sheds dust and nudges the chandelier */
  const update = (t: number, o: { steps?: [number, number, number][]; swing?: number; lights?: number; stain?: number; tick?: boolean } = {}) => {
    const steps = o.steps ?? [];
    let push = 0;
    for (const [, , st] of steps) if (t >= st) push = Math.max(push, Math.exp(-(t - st) * 3) * Math.sin((t - st) * 9));
    const sw = (o.swing ?? 0) + push * 0.05;
    pivot.rotation.set(sw * 0.6, 0, sw);
    shadeM.emissiveIntensity = o.lights ?? 0;
    stainM.opacity = o.stain ?? 0;
    if (o.tick !== false) secH.rotation.z = -Math.floor(t) * (Math.PI / 30) - (44 / 60) * Math.PI * 2;
    dust.forEach((d, i) => {
      const s = steps[i % Math.max(1, steps.length)];
      if (!s) {
        d.visible = false;
        return;
      }
      const k = t - s[2] - (i % 5) * 0.03;
      d.visible = k > 0 && k < 1.0;
      d.position.set(s[0] + Math.sin(i * 7.3) * 0.12, H - 0.02 - 0.5 * 9.8 * k * k * 0.35, s[1] + Math.cos(i * 3.1) * 0.12);
    });
  };
  g.traverse((o) => (o.userData.mount = true));
  setCrack(0.35);
  return { g, pivot, clock, stain, camcorder: cc, update, setCrack, setBulge, setPrints, bulgeAt: bulge.position.clone(), prints: prints.map((p) => p.m.position.clone()), camPos: cc.g.position.clone().add(new THREE.Vector3(0, 1.32, 0)) };
}

// ------------------------------------------------------------------ 24 mailboxes, box 24 hangs open with the photo inside
export function mailboxes24(tex: Tex, photoFront: THREE.Texture | null) {
  const g = new THREE.Group();
  const cols = 4, rows = 6, bw = 0.2, bh = 0.13;
  const paint = texMat(tex, "metal_paint", { color: "#5F7684", rough: 0.6, metal: 0.25 });
  const W = cols * bw + 0.04, Hh = rows * bh + 0.04;
  g.add(mk(at(new THREE.BoxGeometry(W, Hh, 0.2), 0, 0, 0.1), paint));
  const doorM = texMat(tex, "metal_paint", { color: "#6E8796", rough: 0.55, metal: 0.3 });
  const slotM = new THREE.MeshStandardMaterial({ color: "#0B0B0B", roughness: 0.9 });
  let door24: THREE.Group | null = null;
  for (let r = 0; r < rows; r++)
    for (let c = 0; c < cols; c++) {
      const n = r * cols + c + 1;
      const x = -W / 2 + 0.02 + bw * (c + 0.5), y = Hh / 2 - 0.02 - bh * (r + 0.5);
      const d = new THREE.Group();
      d.position.set(x - bw / 2 + 0.005, y, 0.205); // hinge on the left edge
      d.add(mk(at(new THREE.BoxGeometry(bw - 0.012, bh - 0.012, 0.008), (bw - 0.012) / 2, 0, 0), doorM, false));
      d.add(mk(at(new THREE.BoxGeometry(bw * 0.6, 0.006, 0.004), (bw - 0.012) / 2, bh * 0.22, 0.005), slotM, false));
      const lbl = new THREE.Mesh(new THREE.PlaneGeometry(0.05, 0.03), new THREE.MeshBasicMaterial({ map: labelTex(String(n), { w: 96, h: 64, bg: "#D8D2BC", fg: "#151515", font: "bold 44px Arial" }) }));
      lbl.position.set(0.04, -bh * 0.18, 0.0055);
      d.add(lbl);
      if (n === 24) door24 = d;
      g.add(d);
    }
  // the open compartment of box 24: dark inside, the photo sticking out
  const x24 = -W / 2 + 0.02 + bw * 3.5, y24 = Hh / 2 - 0.02 - bh * 5.5;
  g.add(mk(at(new THREE.BoxGeometry(bw - 0.02, bh - 0.02, 0.005), x24, y24, 0.03), slotM, false));
  const photo = new THREE.Mesh(new THREE.BoxGeometry(0.15, 0.002, 0.1125), [slotM, slotM, new THREE.MeshStandardMaterial({ map: photoFront, color: photoFront ? "#FFFFFF" : "#CFC8B4", roughness: 0.6 }), new THREE.MeshStandardMaterial({ color: "#D9D2BE", roughness: 0.8 }), slotM, slotM]);
  photo.position.set(x24 + 0.01, y24 - bh / 2 + 0.03, 0.19); // half out of the box
  photo.rotation.set(-0.15, 0.1, 0.05);
  g.add(photo);
  g.traverse((o) => (o.userData.mount = true));
  return { g, door24: door24 as THREE.Group | null, photo, box24: new THREE.Vector3(x24, y24, 0.2) };
}

// ------------------------------------------------------------------ the flat's hallway: front door from inside, light under it
export function buildHallway(tex: Tex) {
  const g = new THREE.Group();
  const X = 0.65, Z = 3.2, H = 2.55;
  const paper = texMat(tex, "wallpaper", { rough: 0.9 });
  const floorM = texMat(tex, "parquet", { color: "#8C6C4C", rough: 0.6 });
  const f = mk(at(new THREE.BoxGeometry(2 * X, 0.05, Z), 0, -0.025, Z / 2), floorM, false);
  f.userData.ground = true;
  g.add(f);
  g.add(mk(at(new THREE.BoxGeometry(2 * X, 0.05, Z), 0, H + 0.025, Z / 2), texMat(tex, "whitewash"), false));
  for (const s of [-1, 1]) {
    const w = mk(new THREE.PlaneGeometry(Z, H), paper, false);
    w.rotation.y = -s * Math.PI / 2;
    w.position.set(s * X, H / 2, Z / 2);
    g.add(w);
  }
  // end wall around the door (door 0.9 x 2.05, centred)
  const endM = paper;
  g.add(mk(at(new THREE.BoxGeometry((2 * X - 0.9) / 2, H, 0.05), -X + (2 * X - 0.9) / 4, H / 2, -0.025), endM, false));
  g.add(mk(at(new THREE.BoxGeometry((2 * X - 0.9) / 2, H, 0.05), X - (2 * X - 0.9) / 4, H / 2, -0.025), endM, false));
  g.add(mk(at(new THREE.BoxGeometry(0.9, H - 2.05, 0.05), 0, 2.05 + (H - 2.05) / 2, -0.025), endM, false));
  // the front door (inside face: padded leatherette), 2 cm gap at the floor
  const door = mk(at(new THREE.BoxGeometry(0.88, 2.02, 0.06), 0, 0.02 + 1.01, -0.01), texMat(tex, "leatherette", { color: "#5A3626", rough: 0.6 }));
  g.add(door);
  const brass = new THREE.MeshStandardMaterial({ color: "#9C7A3C", roughness: 0.35, metalness: 0.9 });
  const lens = new THREE.Mesh(new THREE.CircleGeometry(0.007, 12), new THREE.MeshBasicMaterial({ color: "#FFE2A8" }));
  lens.position.set(0, 1.55, 0.0455);
  g.add(lens);
  g.add(mk(mergeGeometries([at(new THREE.CylinderGeometry(0.012, 0.012, 0.03, 10), 0, 1.55, 0.03, 0, Math.PI / 2), at(new THREE.BoxGeometry(0.12, 0.02, 0.025), 0.33, 1.0, 0.04), at(new THREE.BoxGeometry(0.03, 0.12, 0.02), 0.3, 1.15, 0.035)]), brass));
  // light from the landing: a warm card behind the gap, and two "feet" that can block it
  const lightM = new THREE.MeshBasicMaterial({ color: "#FFD08A" });
  const card = new THREE.Mesh(new THREE.PlaneGeometry(1.2, 0.05), lightM);
  card.position.set(0, 0.012, -0.12);
  g.add(card);
  const gapL = new THREE.PointLight("#FFC27A", 1.4, 1.4, 1.6);
  gapL.position.set(0, 0.015, -0.05);
  const fill = new THREE.PointLight("#6C7FA6", 0.45, 4, 1.4);
  fill.position.set(0.35, 2.1, 2.7);
  g.add(gapL, fill);
  const shM = new THREE.MeshBasicMaterial({ color: "#000000", transparent: true, opacity: 0, depthWrite: false });
  const shadows = [0, 1].map(() => {
    const m = new THREE.Mesh(new THREE.PlaneGeometry(0.1, 0.55), shM);
    m.rotation.x = -Math.PI / 2;
    m.position.set(0, 0.007, 0.28);
    m.renderOrder = 3;
    g.add(m);
    return m;
  });
  const glowMat = new THREE.MeshBasicMaterial({ color: "#C98C4E", transparent: true, opacity: 0.3, depthWrite: false });
  const glow = new THREE.Mesh(new THREE.PlaneGeometry(0.9, 0.5), glowMat);
  glow.rotation.x = -Math.PI / 2;
  glow.position.set(0, 0.004, 0.22);
  glow.renderOrder = 2;
  g.add(glow);
  const footM = new THREE.MeshBasicMaterial({ color: "#000000" });
  const feet = [new THREE.Mesh(new THREE.BoxGeometry(0.11, 0.06, 0.05), footM), new THREE.Mesh(new THREE.BoxGeometry(0.11, 0.06, 0.05), footM)];
  feet.forEach((m) => {
    m.position.set(0, 0.012, -0.09);
    m.visible = false;
    g.add(m);
  });
  // coat rack with a coat
  const coat = mk(at(new THREE.BoxGeometry(0.4, 0.9, 0.18), -X + 0.12, 1.2, 1.4), new THREE.MeshStandardMaterial({ color: "#2F2B27", roughness: 0.95 }));
  g.add(coat);
  const setFeet = (k: number) => {
    // k: 0 = nobody, 1 = two feet stand right behind the door
    const kk = Math.min(1, k * 1.4);
    feet.forEach((m, i) => {
      m.visible = k > 0.01;
      m.position.x = (i ? 0.12 : -0.12) * kk;
      shadows[i].position.x = m.position.x * 0.85;
    });
    shM.opacity = 0.92 * kk;
    gapL.intensity = 1.4 * (1 - 0.45 * kk);
    glowMat.opacity = 0.3 * (1 - 0.55 * kk);
  };
  g.traverse((o) => (o.userData.mount = true));
  return { g, setFeet, peep: new THREE.Vector3(0, 1.55, 0.05), glowM: glowMat };
}

// ------------------------------------------------------------------ the photo: 1974 front (rendered image) and handwritten back
export function photoBackTex() {
  return canvasTex(900, 600, (c) => {
    c.fillStyle = "#E6DEC8";
    c.fillRect(0, 0, 900, 600);
    const r = rnd(9);
    for (let i = 0; i < 3000; i++) {
      c.fillStyle = `rgba(110,90,60,${r() * 0.07})`;
      c.fillRect(r() * 900, r() * 600, 3, 3);
    }
    c.fillStyle = "rgba(120,95,60,0.25)";
    c.beginPath();
    c.arc(720, 120, 90, 0, 7);
    c.fill();
    c.fillStyle = "#1E2448";
    c.font = `46px ${HAND}`;
    c.fillText("Не позволяйте жильцу сверху", 60, 260);
    c.fillText("узнать, что этаж исчез.", 60, 330);
    c.font = `36px ${HAND}`;
    c.fillText("1974", 640, 520);
  });
}
export function buildPhoto(front: THREE.Texture | null) {
  const back = photoBackTex();
  back.center.set(0.5, 0.5);
  back.rotation = Math.PI; // turned over about its horizontal axis, the writing reads upright
  const edge = new THREE.MeshStandardMaterial({ color: "#D9D2BE", roughness: 0.8 });
  const m = new THREE.Mesh(new THREE.BoxGeometry(0.15, 0.1125, 0.0015), [edge, edge, edge, edge, new THREE.MeshStandardMaterial({ map: front, color: front ? "#FFFFFF" : "#BBB", roughness: 0.55 }), new THREE.MeshStandardMaterial({ map: back, roughness: 0.8 })]);
  m.castShadow = true;
  return m;
}
export { LOBBY_Y, SH };
