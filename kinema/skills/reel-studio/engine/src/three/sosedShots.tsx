/**
 * "Сосед с шестого этажа", series 1 — every shot (S6Shot) and the tape inserts (S6Insert).
 * Rules followed: nothing floats (anything that moves is held by a hand or hangs / swings on its hinge),
 * shots stay short (1–2.5 s) and every shot brings something new to look at.
 */
import React, { useMemo } from "react";
import { AbsoluteFill, Img, staticFile } from "remotion";
import * as THREE from "three";
import { useBlockTime } from "../core/context";
import { camAt, makeCamera, project, Stage3D, type Cam, type CamKey, type V3 } from "./core";
import type { HandTrack } from "./fphands";
import { poseCornerCry, poseRaise, poseWalk, type Human, type Pose } from "./human";
import { aimFlashlight, PzFrame, stepA, useFlashlight, usePzTextures } from "./podezd";
import { buildPhone, phoneScreen, useActor, useFP } from "./podezdShots";
import { applyLamps, buildBedroom, buildBlock, buildStairwell, FLOOR, FLOOR_H, LOBBY_Y, SH, type Lamp, type Tex } from "./podezdSets";
import { psxify, VhsLook } from "./psx";
import { buildHallway, buildHatch, buildPhoto, heroRoomExtras, mailboxes24 } from "./sosedSets";

const P = "projects/sosed6/";
const sm = (x: number) => {
  const k = Math.min(1, Math.max(0, x));
  return k * k * (3 - 2 * k);
};
const mix = (a: V3, b: V3, k: number): V3 => [a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k, a[2] + (b[2] - a[2]) * k];
const K = (t: number, pos: V3, target: V3, fov = 60, ease?: string): CamKey => ({ t, pos, target, fov, ...(ease ? { ease } : {}) }) as CamKey;
const TOP5 = FLOOR(5) + FLOOR_H - 0.2;

// the hero's room (bedroom coordinates): where he walks, stops and raises his hand (under the ceiling bulge)
const WALK_A: V3 = [-0.2, 0, 0.35], WALK_B: V3 = [0.45, 0, -1.15]; // straight away from the camcorder, in its view the whole way
const WALK_V = 0.27, WALK_STEP = 0.33; // a slow, creeping walk: it ends right on «Я остановился»
const CAMCORDER: Cam = { pos: [-1.08, 1.36, 1.58], target: [0.3, 1.05, -0.9], fov: 64 };
/** the 1974 photo is a render from this camera (shot "mk_photo"), cropped to the middle 1080 x 810 */
export const PHOTO_CAM: Cam = { pos: [-6.6, 2.4, 74], target: [-6.4, 8.4, 0], fov: 36 };
const MAN_X = -7.5 + 1.6; // entrance 2 axis + window offset (buildBlock)

type SetName = "room" | "stair5" | "stair6" | "block5" | "block1974" | "hall";
const SETS: Record<string, SetName[]> = {
  ext_push: ["block5"], ext_win: ["block5"], bed_up: ["room"], chand_close: ["room"], stair_top: ["stair5"], ceil_steps: ["room"], footprints: ["room"],
  crack_grow: ["room"], wardrobe_shake: ["room"], door_dark: ["room"], ceil_corner: ["room"], phone_dial: ["room"], phone_talk: ["room"], roof: ["block5"],
  hatch_wide: ["stair5"], hatch_1998: ["stair5"], climb: ["stair5"], weld_close: ["stair5"], scratches: ["stair5"], dent: ["stair5"], setup_cam: ["room"],
  cam_wide: ["room"], clock_312: ["room"], cam_walk1: ["room"], cam_walk2: ["room"], cam_stop: ["room"], clock_tick: ["room"], face_up: ["room"],
  ceil_wait: ["room"], cam_still: ["room"], raise: ["room"], ceil_creak: ["room"], lower: ["room"], bulge_hold: ["room"], morning_bed: ["room"],
  palm_stain: ["room"], lobby_walk: ["stair5"], box_open: ["stair5"], num24: ["stair5"], pan_numbers: ["stair5"], grab_photo: ["stair5"],
  photo_hold: ["stair5"], photo_flip: ["stair5"], back_text: ["stair5"], neighbor: ["stair5"], neighbor_close: ["stair5"], hall_dark: ["hall"],
  feet_shadow: ["hall"], to_peephole: ["hall"], peep_view: ["stair6"], peep_up: ["stair6"], mk_photo: ["block1974"], mk_manface: ["block1974"], mk_face: ["room"], cover: ["stair6"],
};
// shots filmed by the camcorder on its tripod: REC OSD, night tint
const REC = new Set(["cam_wide", "cam_walk1", "cam_walk2", "cam_stop", "face_up", "cam_still", "raise", "lower", "mk_face"]);

/** the photo texture (rendered + processed offline), shared */
const usePhotoTex = () =>
  useMemo(() => {
    const t = new THREE.TextureLoader().load(staticFile(P + "photo1974.jpg"));
    t.colorSpace = THREE.SRGBColorSpace;
    return t;
  }, []);

export const S6Shot: React.FC<{ shot: string; ev?: Record<string, number>; c0?: number; cam?: CamKey[] }> = ({ shot, ev = {}, c0 = 0, cam: camOverride }) => {
  const { f, fps } = useBlockTime();
  const t = f / fps;
  const tex = usePzTextures();
  const sets = SETS[shot] ?? ["room"];
  const fp = useFP();
  const hero = useActor("serega"), lyuda = useActor("lyuda");
  const flash = useFlashlight();
  const phone = useMemo(buildPhone, []);
  const photoTex = usePhotoTex();
  const photo = useMemo(() => psxify(buildPhoto(photoTex)) as THREE.Mesh, [photoTex]);
  const world = useMemo(() => {
    if (!tex) return null;
    const g = new THREE.Group();
    const w: {
      g: THREE.Group; lamps: Lamp[]; room?: ReturnType<typeof buildBedroom>; extras?: ReturnType<typeof heroRoomExtras>; stair?: ReturnType<typeof buildStairwell>;
      hatch?: ReturnType<typeof buildHatch>; mail?: ReturnType<typeof mailboxes24>; block?: ReturnType<typeof buildBlock>; hall?: ReturnType<typeof buildHallway>;
    } = { g, lamps: [] };
    for (const s of sets) {
      if (s === "room") {
        w.room = buildBedroom(tex as Tex);
        w.extras = heroRoomExtras(tex as Tex);
        g.add(w.room.g, w.extras.g);
      }
      if (s === "stair5" || s === "stair6") {
        w.stair = buildStairwell(tex as Tex, { floors: s === "stair5" ? 5 : 6, mailboxes: false, graffiti: false });
        g.add(w.stair.g);
        w.lamps.push(...w.stair.lamps);
        if (s === "stair5") {
          w.hatch = buildHatch(tex as Tex, 5);
          g.add(w.hatch.g);
        }
        w.mail = mailboxes24(tex as Tex, photoTex);
        w.mail.g.rotation.y = Math.PI / 2;
        w.mail.g.position.set(SH.x0 + 0.01, LOBBY_Y + 1.3, 4.65);
        g.add(w.mail.g);
        const lobbyBulb = new THREE.PointLight("#FFD6A0", 2.6, 3.2, 1.5);
        lobbyBulb.position.set(SH.x0 + 0.75, LOBBY_Y + 2.25, 4.55);
        g.add(lobbyBulb);
        // the dark flat behind the neighbour's door (4th floor, left door)
        const inside = new THREE.Mesh(new THREE.BoxGeometry(1.2, 2.4, 1.4), new THREE.MeshStandardMaterial({ color: "#0A0908", roughness: 1, side: THREE.BackSide }));
        inside.position.set(SH.x0 - 0.6, FLOOR(4) + 1.2, 0.75);
        g.add(inside);
        for (let n = 1; n < (s === "stair5" ? 5 : 6); n++) {
          const l = new THREE.PointLight("#6E86AE", 1.2, 4.5, 1.6);
          l.position.set(0.2, FLOOR(n) + 1.4 + 1.7, 5.0);
          g.add(l);
        }
      }
      if (s === "block5") g.add((w.block = buildBlock(tex as Tex, { heroFloor: 5 })).g);
      if (s === "block1974") g.add((w.block = buildBlock(tex as Tex, { floors: 6, manFloor: 6, day: true })).g);
      if (s === "hall") g.add((w.hall = buildHallway(tex as Tex)).g);
    }
    psxify(g);
    psxify(phone.g);
    return w;
  }, [tex, shot]); // eslint-disable-line react-hooks/exhaustive-deps
  if (!world || !fp || !hero || !lyuda) return <AbsoluteFill style={{ background: "#000" }} />;

  const E = (k: string, d: number) => ev[k] ?? d;
  const objs: THREE.Object3D[] = [world.g];
  const add = (h: Human, p: Pose) => {
    h.pose(p);
    objs.push(h.root);
  };
  const keys = (k: CamKey[]) => camAt(camOverride ?? k, t);
  const REST: HandTrack = [{ t: 0, to: "rest", dur: 0.01 }];
  const camOf = (c: Cam) => makeCamera(c);
  const w2c = (camera: THREE.Camera, p: THREE.Vector3): V3 => p.clone().applyMatrix4(camera.matrixWorldInverse).toArray() as V3;
  const d2c = (camera: THREE.Camera, d: V3): V3 => new THREE.Vector3(...d).transformDirection(camera.matrixWorldInverse).toArray() as V3;
  const hands = (cam: Cam, tracks: { L?: HandTrack; R?: HandTrack }, T = t) => {
    fp.pose(T, camOf(cam), tracks);
  };
  const handMatrix = () => {
    const fr = fp.handFrame("R");
    const { centre } = fp.graspCentre("R");
    const x = fr.fingers.clone().normalize();
    const y = fr.palm.clone().sub(x.clone().multiplyScalar(fr.palm.dot(x))).normalize();
    const z = x.clone().cross(y);
    return new THREE.Matrix4().makeBasis(x, y, z).setPosition(centre);
  };
  const phoneIn = (cam: Cam, mode: "show" | "low", screen: string, o: { timer?: number; shake?: number } = {}) => {
    const camera = camOf(cam);
    const sh = (o.shake ?? 0) * 0.004;
    const at: Record<string, { p: V3; fingers: V3; palm: V3 }> = {
      show: { p: [0.05 + Math.sin(t * 23) * sh, -0.05 + Math.sin(t * 31) * sh, -0.33], fingers: [-0.95, 0.2, -0.1], palm: [0.05, 0.45, 0.89] },
      low: { p: [0.12, -0.25, -0.36], fingers: [-0.85, 0.1, -0.45], palm: [0.1, 0.95, 0.2] },
    };
    const a = at[mode];
    hands(cam, { L: REST, R: [{ t: 0, to: a.p, pose: { thumb: 0.25, index: 0.32, middle: 0.36, ring: 0.4, pinky: 0.44, spread: 0.05, oppose: 0.35 }, aim: { fingers: a.fingers, palm: a.palm }, dur: 0.01, contact: true }] });
    const { centre } = fp.graspCentre("R");
    const cq = camera.quaternion;
    const fwd = new THREE.Vector3(0, 0, -1).applyQuaternion(cq), cup = new THREE.Vector3(0, 1, 0).applyQuaternion(cq);
    const up = mode === "show" ? cup.clone().multiplyScalar(0.75).addScaledVector(fwd, 0.66).normalize() : fwd.clone().addScaledVector(cup, 0.12).normalize();
    const zt = mode === "show" ? fwd.clone().negate().addScaledVector(cup, 0.45).normalize() : cup.clone().addScaledVector(fwd, -0.35).normalize();
    const x = up.clone().cross(zt).normalize();
    const z = x.clone().cross(up).normalize();
    phone.g.quaternion.setFromRotationMatrix(new THREE.Matrix4().makeBasis(x, up, z));
    phone.g.position.copy(centre).addScaledVector(z, 0.014);
    phone.g.updateMatrixWorld(true);
    phoneScreen(phone.ctx, screen, t, o);
    phone.tex.needsUpdate = true;
    objs.push(phone.g, fp.root);
  };
  /** the photo pinched at its right edge by the right hand, fingers behind it (they point left, under the photo), so the
   *  picture stays uncovered; `flip` rolls the forearm about the photo's horizontal axis (0 = front to the eyes, 1 = back) —
   *  the grip sits on that axis, so the hand turns with the photo instead of spinning it in the air */
  const pinchPhoto = (cam: Cam, p: THREE.Vector3, right: THREE.Vector3, up: THREE.Vector3, n: THREE.Vector3, reach?: number) => {
    const camera = camOf(cam);
    // Aim the palm toward the paper, then measure the actual posed fingertips.
    // The rig target is the wrist; a fixed guessed wrist offset overlaps the image.
    const edge = p.clone().addScaledVector(right, 0.073).addScaledVector(up, -0.025);
    const wrist = edge.clone().addScaledVector(right, 0.12).addScaledVector(n, -0.025);
    const aim = { fingers: right.clone().negate().toArray() as V3, palm: n.toArray() as V3 };
    const track = (to: THREE.Vector3): HandTrack => [{ t: -1, to: to.toArray() as V3, pose: "pinch", aim, dur: 0.01, contact: true }];
    hands(cam, { L: REST, R: track(wrist) });
    const tip = fp.bones.RightHandIndex3.getWorldPosition(new THREE.Vector3())
      .add(fp.bones.RightHandThumb3.getWorldPosition(new THREE.Vector3())).multiplyScalar(0.5);
    wrist.add(edge.clone().sub(tip.applyMatrix4(camera.matrixWorldInverse)));
    if (reach !== undefined && reach < 1) wrist.lerp(new THREE.Vector3(0.26, -0.64, -0.2), 1 - reach);
    hands(cam, { L: REST, R: track(wrist) });
    const xw = right.clone().transformDirection(camera.matrixWorld), yw = up.clone().transformDirection(camera.matrixWorld), zw = n.clone().transformDirection(camera.matrixWorld);
    photo.quaternion.setFromRotationMatrix(new THREE.Matrix4().makeBasis(xw, yw, zw));
    photo.position.copy(p.clone().applyMatrix4(camera.matrixWorld));
    photo.updateMatrixWorld(true);
    objs.push(photo, fp.root);
  };
  const photoIn = (cam: Cam, o: { p?: V3; flip?: number; tilt?: number } = {}) => {
    const camera = camOf(cam);
    const p = new THREE.Vector3(...(o.p ?? [-0.03, -0.01, -0.27]));
    const n0 = new THREE.Vector3(0, 0.12 + (o.tilt ?? 0), 1).normalize(); // front faces the eye
    const up0 = new THREE.Vector3(0, 1, 0).addScaledVector(n0, -n0.y).normalize();
    const right = up0.clone().cross(n0).normalize();
    const R = new THREE.Quaternion().setFromAxisAngle(right, (o.flip ?? 0) * Math.PI);
    const n = n0.clone().applyQuaternion(R), up = up0.clone().applyQuaternion(R);
    pinchPhoto(cam, p, right, up, n);
  };
  // walking hero and the steps "above" that repeat his steps 3 s later
  const stepTimes = (t0: number) => {
    const A = new THREE.Vector3(...WALK_A), B = new THREE.Vector3(...WALK_B);
    const L = A.distanceTo(B), out: [number, number, number][] = [];
    for (let j = 0; j * WALK_STEP <= L + 1e-6; j++) {
      const q = A.clone().lerp(B, Math.min(1, (j * WALK_STEP) / L));
      out.push([q.x, q.z, t0 + (j * WALK_STEP) / WALK_V]);
    }
    return out;
  };
  const NIGHT = { lights: 0 };
  let out: { cam: Cam; lamps?: { flicker?: number; breath?: number; dim?: number }; flash?: number; fog?: { color: string; near: number; far: number }; exposure?: number; overlay?: React.ReactNode; wear?: number; light?: React.ReactNode; bg?: string; tint?: string } | null = null;
  const ex = world.extras;
  const room = world.room;
  world.g.updateMatrixWorld(true); // shots read world positions (mailboxes, labels) before the first render
  const lookCeil: V3 = [WALK_B[0], 2.6, WALK_B[2]];
  switch (shot) {
    // ================================================================ exterior
    case "ext_push": {
      const w = world.block!.dimaWin;
      out = { cam: keys([K(0, [w.x - 14, 2.5, 44], [w.x, w.y, 0], 46), K(1.4, [w.x - 8, 6.5, 26], [w.x, w.y, 0], 40, "out")]), fog: { color: "#06080C", near: 25, far: 150 }, exposure: 1.6, bg: "#0A0E16" };
      break;
    }
    case "ext_win": {
      const w = world.block!.dimaWin;
      out = { cam: keys([K(0, [w.x - 3.5, w.y - 1.6, 10], [w.x, w.y, 0], 38), K(1.5, [w.x - 2.2, w.y - 0.9, 6.5], [w.x, w.y + 0.1, 0], 34, "linear")]), fog: { color: "#06080C", near: 25, far: 150 }, exposure: 1.6, bg: "#0A0E16" };
      break;
    }
    case "roof": {
      const w = world.block!.dimaWin;
      const roofY = 0.9 + 5 * FLOOR_H + 0.5;
      out = { cam: keys([K(0, [w.x - 9, roofY + 7, 9], [w.x - 2, roofY, -6], 56), K(2.0, [w.x + 5, roofY + 4, 1], [w.x + 8, roofY, -6], 56, "inOut")]), fog: { color: "#06080C", near: 25, far: 150 }, exposure: 1.9, bg: "#0A0E16",
        light: (<><hemisphereLight args={["#4E6290", "#0C0C0E", 0.9]} /><directionalLight position={[-20, 30, 12]} color="#A2B4DA" intensity={1.1} /></>) };
      break;
    }
    // ================================================================ the room at night: the ceiling
    case "bed_up": {
      const p = room!.pillow.clone().add(new THREE.Vector3(0, 0.12, 0));
      ex!.update(t, { ...NIGHT, steps: [[0.1, -0.2, 0.3], [0.3, 0.1, 0.9], [0.1, 0.4, 1.5]], swing: 0.02 * Math.sin(t * 3) });
      out = { cam: { pos: p.toArray() as V3, target: [0.1, 2.6, -0.3], fov: 66, roll: 0.35 + Math.sin(t * 0.7) * 0.02 }, exposure: 1.5 };
      break;
    }
    case "chand_close": {
      ex!.update(t, { ...NIGHT, steps: [[0.1, -0.2, 0.1], [0.15, -0.1, 0.6], [0.05, -0.25, 1.1], [0.2, -0.15, 1.5]], swing: 0.05 * Math.sin(t * 7) * Math.exp(-((t % 0.5) * 2)) });
      out = { cam: keys([K(0, [0.42, 1.55, 0.35], [0.1, 2.2, -0.2], 48), K(2, [0.36, 1.6, 0.25], [0.1, 2.25, -0.2], 44, "linear")]), exposure: 1.5 };
      break;
    }
    case "ceil_steps": {
      const steps: [number, number, number][] = [0, 1, 2, 3, 4].map((i) => [0.9 - i * 0.3, 1.0 - i * 0.35, 0.15 + i * 0.32]);
      ex!.update(t, { ...NIGHT, steps });
      out = { cam: { pos: [0.25, 1.05, 0.55], target: [0.2, 2.6, 0.1], fov: 72, roll: 0.15 }, exposure: 1.55 };
      break;
    }
    case "footprints": {
      ex!.update(t, NIGHT);
      ex!.setPrints(t, 0.05, 0.16);
      out = { cam: keys([K(0, [0.05, 1.25, -0.4], [0.25, 2.6, 0.45], 70), K(1.2, [0.0, 1.2, -0.5], [0.15, 2.6, 0.3], 66, "linear")]), exposure: 1.55 };
      break;
    }
    case "crack_grow": {
      ex!.update(t, { ...NIGHT, steps: [[-0.4, -0.8, 0.1], [0.1, -0.8, 0.6], [0.4, -0.8, 1.1]] });
      ex!.setCrack(0.35 + sm(t / 1.4) * 0.65);
      ex!.setPrints(99, 0);
      const sh = Math.sin(t * 40) * 0.004 * (1 - sm(t / 1.4));
      out = { cam: { pos: [-0.25 + sh, 1.3, -0.25], target: [-0.15, 2.6, -0.85], fov: 62, roll: 0.1 }, exposure: 1.55 };
      break;
    }
    case "wardrobe_shake": {
      ex!.update(t, { ...NIGHT, steps: [[1.25, 1.35, 0.05], [1.3, 1.5, 0.5], [1.2, 1.4, 0.95]] });
      ex!.setPrints(99, 0);
      const wd = room!.wardrobe;
      const j = Math.sin(t * 46) * 0.011 * (0.6 + 0.4 * Math.sin(t * 3));
      wd.position.set(1.6 - 0.3 + j, 0, 2.1 - 0.7);
      wd.rotation.set(0, -Math.PI / 2, j * 0.5);
      out = { cam: keys([K(0, [-0.45, 1.45, -0.1], [1.3, 1.1, 1.4], 54), K(1.7, [-0.3, 1.45, 0.05], [1.3, 1.15, 1.4], 50, "linear")]), exposure: 1.55,
        light: <pointLight position={[0.55, 1.5, 1.05]} color="#9AAAD0" intensity={5} distance={2.2} decay={1.2} /> };
      break;
    }
    case "door_dark": {
      ex!.update(t, NIGHT);
      ex!.setPrints(99, 0);
      out = { cam: keys([K(0, [-1.05, 1.0, -1.25], [0.05, 1.0, 2.1], 60), K(1.5, [-0.95, 1.02, -1.05], [0.05, 1.05, 2.1], 54, "linear")]), exposure: 1.5 };
      break;
    }
    case "ceil_corner": {
      ex!.update(t, NIGHT);
      ex!.setPrints(99, 0);
      const k = sm(t / 0.9);
      out = { cam: { pos: [-0.95, 1.02, -1.05], target: mix([0.05, 1.1, 2.1], [1.55, 2.6, 2.05], k), fov: 56 - k * 6 }, exposure: 1.5 };
      break;
    }
    case "phone_dial": {
      ex!.update(t, NIGHT);
      ex!.setPrints(99, 0);
      const cam: Cam = { pos: [-0.95, 1.05, -1.1], target: [0.4, 0.75, 0.6], fov: 60, roll: 0.03 };
      phoneIn(cam, "show", "uk", { shake: 0.4 });
      out = { cam, exposure: 1.5 };
      break;
    }
    case "phone_talk": {
      ex!.update(t, NIGHT);
      ex!.setPrints(99, 0);
      const cam: Cam = { pos: [-0.95, 1.05, -1.1], target: [0.2, 0.85, 0.3], fov: 46, roll: -0.03 };
      phoneIn(cam, "show", "ukcall", { timer: 4 + t, shake: 0.6 });
      out = { cam, exposure: 1.5 };
      break;
    }
    // ================================================================ the attic hatch
    case "stair_top": {
      const h = world.hatch!.centre;
      out = { cam: keys([K(0, [-0.65, FLOOR(5) + 1.1, 1.3], [h.x, TOP5 - 0.2, h.z], 62), K(1.9, [-0.5, FLOOR(5) + 1.35, 1.2], [h.x, TOP5, h.z], 58, "linear")]), lamps: { flicker: 0.3 } };
      break;
    }
    case "hatch_wide": {
      const h = world.hatch!.centre;
      out = { cam: keys([K(0, [h.x, FLOOR(5) + 0.45, 0.2], [h.x, TOP5, h.z - 0.1], 66), K(1.4, [h.x, FLOOR(5) + 0.6, 0.25], [h.x, TOP5, h.z], 64, "linear")]), lamps: { flicker: 0.3 } };
      break;
    }
    case "hatch_1998": {
      const h = world.hatch!.centre;
      out = { cam: keys([K(0, [h.x - 0.1, TOP5 - 0.6, h.z - 0.35], [h.x - 0.05, TOP5, h.z - 0.05], 46), K(1.6, [h.x + 0.05, TOP5 - 0.55, h.z - 0.3], [h.x + 0.08, TOP5, h.z + 0.05], 44, "linear")]), lamps: { flicker: 0.35 } };
      break;
    }
    case "climb": {
      const h = world.hatch!;
      const k = sm(t / 1.7);
      const eyeY = FLOOR(5) + 1.55 + k * 0.75;
      const cam: Cam = { pos: [h.centre.x, eyeY, h.ladderZ - 0.38], target: [h.centre.x, eyeY + 0.55, h.ladderZ + 0.6], fov: 62, roll: Math.sin(t * 5) * 0.015 };
      const camera = camOf(cam);
      // each hand grabs the rung just above / below the eyes, hand over hand
      const rungAt = (yy: number) => h.rungs.reduce((b, r) => (Math.abs(r - yy) < Math.abs(b - yy) ? r : b), h.rungs[0]);
      const grab = (side: "L" | "R", phase: number) => (T: number) => {
        const kk = sm(T / 1.7), ey = FLOOR(5) + 1.55 + kk * 0.75;
        const stepUp = Math.floor(T * 2.4 + phase) % 2 === 0 ? 0.05 : -0.25;
        const r = rungAt(ey + stepUp);
        return w2c(camOf({ ...cam, pos: [h.centre.x, ey, h.ladderZ - 0.38], target: [h.centre.x, ey + 0.55, h.ladderZ + 0.6] }), new THREE.Vector3(h.centre.x + (side === "L" ? -0.12 : 0.12), r, h.ladderZ));
      };
      hands(cam, {
        L: [{ t: 0, to: grab("L", 0), pose: "grip", aim: { fingers: d2c(camera, [0.3, 0, 1]), palm: d2c(camera, [0, -0.3, 1]) }, dur: 0.01, contact: true }],
        R: [{ t: 0, to: grab("R", 1), pose: "grip", aim: { fingers: d2c(camera, [-0.3, 0, 1]), palm: d2c(camera, [0, -0.3, 1]) }, dur: 0.01, contact: true }],
      });
      objs.push(fp.root);
      out = { cam, lamps: { flicker: 0.3 } };
      break;
    }
    case "weld_close": {
      const h = world.hatch!.centre;
      const cam: Cam = { pos: [h.x - 0.05, TOP5 - 0.48, h.z - 0.42], target: [h.x + 0.12, TOP5, h.z + 0.1], fov: 54 };
      const camera = camOf(cam);
      const touch = new THREE.Vector3(h.x + 0.25, TOP5 - 0.045, h.z + 0.18);
      hands(cam, { L: REST, R: [{ t: 0, to: "rest", dur: 0.01 }, { t: 0.2, to: w2c(camera, touch), pose: "flat", aim: { fingers: d2c(camera, [0.1, 0, 1]), palm: d2c(camera, [0, 1, 0]) }, dur: 0.55, contact: true }] });
      objs.push(fp.root);
      out = { cam, lamps: { flicker: 0.3 } };
      break;
    }
    case "scratches": {
      const h = world.hatch!.centre;
      out = { cam: keys([K(0, [h.x - 0.02, TOP5 - 0.3, h.z - 0.15], [h.x + 0.06, TOP5, h.z + 0.05], 38), K(1.6, [h.x + 0.04, TOP5 - 0.28, h.z - 0.1], [h.x + 0.1, TOP5, h.z + 0.08], 34, "linear")]), lamps: { flicker: 0.5 } };
      break;
    }
    case "dent": {
      const h = world.hatch!;
      const bang = E("bang", 0.18);
      h.lid.scale.z = sm((t - bang) / 0.06);
      const jolt = t > bang ? Math.exp(-(t - bang) * 9) : 0;
      out = { cam: { pos: [h.centre.x + 0.05 + Math.sin(t * 60) * 0.012 * jolt, TOP5 - 0.8 - jolt * 0.04, h.centre.z - 0.42], target: [h.centre.x + 0.08, TOP5, h.centre.z + 0.02], fov: 52, roll: jolt * 0.06 * Math.sin(t * 40) }, lamps: { flicker: 0.2 + jolt * 0.5 } };
      break;
    }
    // ================================================================ the camcorder nights
    case "setup_cam": {
      ex!.update(t, NIGHT);
      ex!.setPrints(99, 0);
      const cc = ex!.camcorder;
      cc.g.updateMatrixWorld(true);
      const btn = cc.recBtn.getWorldPosition(new THREE.Vector3());
      const back = new THREE.Vector3(0, 0, 1).applyQuaternion(cc.g.quaternion);
      const eye = btn.clone().addScaledVector(back, 0.42).add(new THREE.Vector3(0.1, 0.22, 0));
      const cam: Cam = { pos: eye.toArray() as V3, target: btn.clone().addScaledVector(back, -1.6).add(new THREE.Vector3(0, -0.15, 0)).toArray() as V3, fov: 58 };
      const camera = camOf(cam);
      const press = E("press", 0.75);
      hands(cam, { L: REST, R: [{ t: 0, to: "rest", dur: 0.01 }, { t: 0.15, to: w2c(camera, btn.clone().addScaledVector(back, 0.012 + 0.17)), pose: "point", aim: { fingers: d2c(camera, back.clone().negate().toArray() as V3), palm: d2c(camera, [0, -1, 0]) }, dur: press - 0.15, contact: true }, { t: press + 0.35, to: "rest", dur: 0.5 }] });
      (cc.led.material as THREE.MeshStandardMaterial).emissiveIntensity = t > press ? 2.5 : 0;
      objs.push(fp.root);
      out = { cam, exposure: 1.5 };
      break;
    }
    case "cam_wide":
    case "cam_walk1":
    case "cam_walk2":
    case "cam_stop":
    case "cam_still":
    case "raise":
    case "lower":
    case "face_up":
    case "mk_face": {
      // one continuous night on the tape: t0 = when this shot starts on the walk clock
      const t0 = E("walk0", 0); // seconds into the walk at this shot's start
      const T = t0 + t;
      const walkStart = 0;
      const delayed = stepTimes(walkStart).map(([x, z, st]) => [x, z, st + 3] as [number, number, number]);
      ex!.update(T, { ...NIGHT, steps: delayed.filter((s) => s[2] < E("upStop", 99)) });
      ex!.setPrints(99, 0);
      const raiseK = shot === "raise" ? sm((t - 0.15) / 1.1) : shot === "lower" ? 1 - sm((t - 0.1) / 1.0) : 0;
      if (shot === "cam_wide") add(hero, poseRaise(hero, T, { pos: WALK_A, yaw: Math.atan2(WALK_B[0] - WALK_A[0], WALK_B[2] - WALK_A[2]), k: 0, lookAt: lookCeil }));
      else if (shot === "cam_walk1" || shot === "cam_walk2") add(hero, poseWalk(hero, T, { a: WALK_A, b: WALK_B, t0: walkStart, speed: WALK_V, step: WALK_STEP }));
      else {
        const away = Math.atan2(WALK_B[0] - WALK_A[0], WALK_B[2] - WALK_A[2]);
        const toCam = Math.atan2(CAMCORDER.pos[0] - WALK_B[0], CAMCORDER.pos[2] - WALK_B[2]);
        let dy = toCam - away;
        while (dy > Math.PI) dy -= 2 * Math.PI;
        while (dy < -Math.PI) dy += 2 * Math.PI;
        const turn = shot === "lower" ? sm((t - E("turn", 1.3)) / 0.9) : shot === "mk_face" ? 1 : 0;
        add(hero, poseRaise(hero, T, { pos: WALK_B, yaw: away + dy * turn, k: raiseK, lookAt: turn > 0.5 ? CAMCORDER.pos : lookCeil }));
      }
      ex!.setBulge(shot === "lower" ? 0.4 : 0);
      let cam = CAMCORDER;
      if (shot === "cam_walk2") cam = { ...CAMCORDER, target: [0.1, 1.1, -0.4], fov: 44 };
      if (shot === "raise" || shot === "lower") cam = { ...CAMCORDER, target: [WALK_B[0], 1.5, WALK_B[2]], fov: 38 };
      if (shot === "face_up" || shot === "mk_face") {
        const head = hero.joint("Head");
        cam = { ...CAMCORDER, target: [head.x, head.y - 0.1, head.z], fov: shot === "mk_face" ? 9 : 20 };
      }
      if (shot === "mk_face") {
        return (
          <AbsoluteFill style={{ background: "#000" }}>
            <Stage3D cam={cam} lights="none" env={0} dpr={0.4} pixelated exposure={1.5}>
              <color attach="background" args={["#0B0D0C"]} />
              <hemisphereLight args={["#C8D8C8", "#202020", 0.9]} />
              <pointLight position={[-0.6, 1.9, 1.0]} color="#E8F0E0" intensity={4} distance={5} decay={1.5} />
              {objs.map((o, i) => (
                <primitive key={i} object={o} />
              ))}
            </Stage3D>
          </AbsoluteFill>
        );
      }
      const s = Math.floor(T) + 5;
      out = { cam, exposure: 1.45, tint: "#9FCB98", wear: 0.5, light: <pointLight position={[0.2, 2.3, 0.6]} color="#C8D8C8" intensity={1.6} distance={5} decay={1.5} /> };
      (out as { rec?: string }).rec = `03:12:${String(s % 60).padStart(2, "0")}`;
      break;
    }
    case "clock_312":
    case "clock_tick": {
      ex!.update(E("sec", 0) + t, { ...NIGHT, tick: true });
      ex!.setPrints(99, 0);
      const c = ex!.clock.position;
      out = { cam: keys([K(0, [c.x + 0.05, c.y - 0.02, c.z + 0.55], [c.x, c.y, c.z], 40), K(1.5, [c.x + 0.03, c.y - 0.01, c.z + 0.45], [c.x, c.y, c.z], 38, "linear")]), exposure: 1.6 };
      break;
    }
    case "ceil_wait":
    case "ceil_creak":
    case "bulge_hold": {
      ex!.update(t, { ...NIGHT, steps: shot === "ceil_wait" ? [[WALK_B[0] - 0.1, WALK_B[2] + 0.1, 0.55]] : [] });
      ex!.setPrints(99, 0);
      const b = ex!.bulgeAt;
      const k = shot === "ceil_creak" ? sm((t - E("creak", 0.55)) / 0.25) * 0.45 : shot === "bulge_hold" ? 0.45 + sm(t / 3) * 0.55 : 0;
      ex!.setBulge(k);
      const cam = shot === "bulge_hold" ? keys([K(0, [b.x + 0.35, 1.2, b.z + 0.6], [b.x, 2.6, b.z], 54), K(3.5, [b.x + 0.2, 1.5, b.z + 0.35], [b.x, 2.6, b.z], 42, "linear")]) : { pos: [b.x + 0.4, 1.25, b.z + 0.55] as V3, target: [b.x, 2.6, b.z] as V3, fov: 58 };

      out = { cam, exposure: 1.55 };
      break;
    }
    // ================================================================ morning
    case "morning_bed":
    case "palm_stain": {
      ex!.update(t, { lights: 0, stain: 1, tick: false });
      ex!.setPrints(99, 0);
      ex!.setBulge(0);
      room!.street.color.set("#A9C2E6");
      room!.street.intensity = 40;
      const st = ex!.stain.position;
      const p = room!.pillow.clone().add(new THREE.Vector3(0, 0.12, 0));
      const cam = shot === "morning_bed"
        ? { pos: p.toArray() as V3, target: mix([p.x + 0.4, 2.6, p.z + 1.4], [st.x, 2.6, st.z], sm(t / 1.6)), fov: 66 - 26 * sm((t - 1.2) / 1.3), roll: 0.3 * (1 - sm(t / 1.6)) }
        : keys([K(0, [st.x + 0.1, 1.45, st.z + 0.3], [st.x, 2.6, st.z], 46), K(2.1, [st.x + 0.05, 1.75, st.z + 0.15], [st.x, 2.6, st.z], 38, "linear")]);
      out = { cam, exposure: 1.6, light: (<><hemisphereLight args={["#D6E2F2", "#5A5048", 1.6]} /><pointLight position={[0.4, 1.2, 0.2]} color="#E8EEF6" intensity={2.4} distance={5} decay={1.2} /></>) };
      break;
    }
    // ================================================================ the lobby, box 24, the photo
    case "lobby_walk": {
      const k = sm(t / 1.8);
      const z = 1.6 + k * 2.2, y = 0 - k * RISE_ + 1.62 + Math.abs(Math.sin(t * 7)) * 0.025;
      out = { cam: { pos: [-0.7, y, z], target: [-1.24, LOBBY_Y + 1.15, 4.65], fov: 62, roll: Math.sin(t * 3.5) * 0.015 }, lamps: { flicker: 0.1 } };
      break;
    }
    case "box_open": {
      const m = world.mail!;
      if (m.door24) m.door24.rotation.y = -1.1 - Math.sin(t * 2.2) * 0.12;
      const b = m.box24.clone().applyMatrix4(m.g.matrixWorld);
      out = { cam: keys([K(0, [b.x + 0.85, b.y + 0.4, b.z + 0.55], [b.x, b.y - 0.02, b.z - 0.05], 50), K(1.8, [b.x + 0.62, b.y + 0.28, b.z + 0.38], [b.x, b.y - 0.03, b.z - 0.05], 44, "linear")]), lamps: { flicker: 0.15 } };
      break;
    }
    case "num24": {
      const m = world.mail!;
      if (m.door24) m.door24.rotation.y = -1.1 - Math.sin((t + 2) * 2.2) * 0.12;
      m.g.updateMatrixWorld(true);
      const lblO = m.door24!.children[2];
      const lbl = lblO.getWorldPosition(new THREE.Vector3());
      const nrm = new THREE.Vector3(0, 0, 1).transformDirection(lblO.matrixWorld);
      const side = new THREE.Vector3(0, 1, 0).cross(nrm).normalize();
      const at0 = lbl.clone().addScaledVector(nrm, 0.42).addScaledVector(side, 0.08).add(new THREE.Vector3(0, 0.05, 0));
      const at1 = lbl.clone().addScaledVector(nrm, 0.3).addScaledVector(side, 0.04).add(new THREE.Vector3(0, 0.02, 0));
      out = { cam: keys([K(0, at0.toArray() as V3, lbl.toArray() as V3, 30), K(1.6, at1.toArray() as V3, lbl.toArray() as V3, 26, "linear")]), lamps: { flicker: 0.1 } };
      break;
    }
    case "pan_numbers": {
      const m = world.mail!;
      if (m.door24) m.door24.rotation.y = -1.15;
      const k = sm(t / 1.6);
      const from = new THREE.Vector3(0.15, 0.4, 0.2).applyMatrix4(m.g.matrixWorld), to = new THREE.Vector3(-0.3, -0.38, 0.2).applyMatrix4(m.g.matrixWorld);
      const tg = from.clone().lerp(to, k);
      out = { cam: { pos: [tg.x + 0.55, tg.y + 0.05, tg.z + 0.1], target: tg.toArray() as V3, fov: 34 }, lamps: { flicker: 0.1 } };
      break;
    }
    case "grab_photo": {
      const m = world.mail!;
      if (m.door24) m.door24.rotation.y = -1.15;
      const b = m.box24.clone().applyMatrix4(m.g.matrixWorld);
      const cam: Cam = { pos: [b.x + 0.55, b.y + 0.32, b.z + 0.3], target: [b.x, b.y - 0.05, b.z - 0.04], fov: 56 };
      const camera = camOf(cam);
      const tc = E("grab", 0.55);
      m.photo.updateMatrixWorld(true);
      const p0 = m.photo.getWorldPosition(new THREE.Vector3());
      // Continue from the photo's real resting transform to the next shot's
      // camera-space hold. The paper and fingertips share this one transform.
      const q0 = m.photo.getWorldQuaternion(new THREE.Quaternion())
        .multiply(new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(1, 0, 0), -Math.PI / 2));
      q0.premultiply(camera.quaternion.clone().invert());
      const n1 = new THREE.Vector3(0, 0.12, 1).normalize();
      const up1 = new THREE.Vector3(0, 1, 0).addScaledVector(n1, -n1.y).normalize();
      const right1 = up1.clone().cross(n1).normalize();
      const q1 = new THREE.Quaternion().setFromRotationMatrix(new THREE.Matrix4().makeBasis(right1, up1, n1));
      const k = sm((t - tc) / 1.1);
      const pos = p0.applyMatrix4(camera.matrixWorldInverse).lerp(new THREE.Vector3(-0.03, -0.01, -0.27), k);
      const rot = q0.slerp(q1, k);
      m.photo.visible = false;
      pinchPhoto(cam, pos, new THREE.Vector3(1, 0, 0).applyQuaternion(rot), new THREE.Vector3(0, 1, 0).applyQuaternion(rot), new THREE.Vector3(0, 0, 1).applyQuaternion(rot), sm((t - 0.05) / (tc - 0.05)));
      out = { cam, lamps: { flicker: 0.1 } };
      break;
    }
    case "photo_hold":
    case "photo_flip":
    case "back_text": {
      const base: Cam = { pos: [-0.6, LOBBY_Y + 1.6, 4.0], target: [0.5, LOBBY_Y + 0.9, 3.2], fov: 58 };
      const flip = shot === "photo_flip" ? sm((t - 0.15) / 0.9) : shot === "back_text" ? 1 : 0;
      const cam: Cam = shot === "back_text" ? { ...base, fov: 34, target: [0.2, LOBBY_Y + 1.1, 3.5] } : base;
      photoIn(cam, { flip, p: shot === "back_text" ? [-0.03, -0.01, -0.24] : [-0.03, -0.01, -0.27] });
      out = { cam, lamps: { flicker: 0.1 } };
      break;
    }
    case "neighbor":
    case "neighbor_close": {
      const y = FLOOR(4);
      const dL = world.stair!.doors[(4 - 1) * 3 + 1];
      const close = shot === "neighbor_close" ? sm((t - E("shut", 1.2)) / 0.55) : 0;
      dL.rotation.y = Math.PI / 2 + 1.25 * (1 - close); // opens into her flat
      dL.updateMatrixWorld(true);
      const lp: V3 = [SH.x0 - 0.25, y, 0.72];
      const cam: Cam = shot === "neighbor" ? { pos: [0.55, y + 1.58, 1.15], target: [SH.x0 - 0.2, y + 1.45, 0.72], fov: 52 } : { pos: [-0.25, y + 1.6, 0.85], target: [SH.x0 - 0.2, y + 1.55, 0.72], fov: 38 };
      const p = poseCornerCry(lyuda, t, { pos: lp, yaw: Math.PI / 2, sob: 0, lookAt: cam.pos, look: 1, handsDown: 1 });
      p.pos = [lp[0] - close * 0.35, lp[1], lp[2]];
      // her right hand on the door handle while she shuts it
      if (close > 0) {
        const handle = new THREE.Vector3(0.77, 1.04, 0.1).applyMatrix4(dL.matrixWorld);
        lyuda.root.position.set(...p.pos);
        lyuda.root.rotation.set(0, p.yaw, 0);
        lyuda.root.updateMatrixWorld(true);
        const lh = lyuda.root.worldToLocal(handle.clone());
        p.arms!.R = { hand: [lh.x, lh.y, lh.z], pole: [-0.6, 0.6, -0.3], fingers: [0.2, 0, 1], palm: [-1, 0, 0] };
      }
      add(lyuda, p);
      if (shot === "neighbor") photoIn(cam, { p: [0.06, -0.1, -0.34], flip: 1 });
      out = { cam, lamps: { flicker: 0.15 } };
      break;
    }
    // ================================================================ the night the steps came down
    case "hall_dark": {
      world.hall!.setFeet(0);
      out = { cam: keys([K(0, [0.25, 1.6, 2.9], [0, 0.85, 0], 60), K(1.6, [0.2, 1.55, 2.5], [0, 0.8, 0], 56, "linear")]), exposure: 1.6, light: (<><ambientLight intensity={0.05} /><pointLight position={[0.3, 1.9, 1.8]} color="#7F90B4" intensity={0.9} distance={3.2} decay={1.4} /></>) };
      break;
    }
    case "feet_shadow": {
      world.hall!.setFeet(sm((t - E("feet", 0.4)) / 0.5));
      out = { cam: keys([K(0, [0.02, 0.18, 1.0], [0, 0.025, 0.08], 54), K(1.7, [0, 0.16, 0.88], [0, 0.025, 0.08], 52, "linear")]), exposure: 1.35 }; // low angle with enough elevation to separate the two floor shadows
      break;
    }
    case "to_peephole": {
      world.hall!.setFeet(1);
      const k = sm(t / 1.6);
      const cam: Cam = { pos: [0, 1.58, 1.3 - k * 1.18], target: [0, 1.55, 0], fov: 60 - k * 10 };
      const camera = camOf(cam);
      hands(cam, { R: REST, L: [{ t: 0, to: "rest", dur: 0.01 }, { t: 0.3, to: w2c(camera, new THREE.Vector3(-0.12, 1.34, 0.035)), pose: "flat", aim: { fingers: d2c(camera, [0, 1, 0]), palm: d2c(camera, [0, 0, -1]) }, dur: 0.8, contact: true }] });
      objs.push(fp.root);
      out = { cam, exposure: 1.9, light: (<><pointLight position={[0.35, 2.0, 1.9]} color="#8494B8" intensity={9} distance={4} decay={1.3} /><ambientLight intensity={0.08} /></>) };
      break;
    }
    case "peep_view":
    case "peep_up":
    case "cover": {
      const y = FLOOR(5);
      const up = shot === "peep_up" ? sm((t - 0.2) / 1.4) : shot === "cover" ? 1 : 0;
      const cam: Cam = { pos: [0.0, y + 1.55, 0.09], target: mix([0.6, y + 1.5, 3.5], [0.3, y + 3.6, 3.0], up), fov: 112 };
      // the stairwell is dark except the bulb on the sixth floor, which comes on
      world.lamps.forEach((l) => {
        const six = l.floor === 6;
        l.light.intensity = six ? (shot === "peep_view" ? 0 : (t > 0.35 || shot === "cover" ? 7 : 0)) * (0.8 + 0.2 * Math.sin(t * 40)) : l.floor === 5 ? 1.2 : 0.3;
        l.glassM.emissiveIntensity = l.light.intensity * 0.3;
        l.light.castShadow = six;
      });
      // the one who lives above: on the half landing, looking down at the door
      if (shot !== "peep_view") add(hero, poseRaise(hero, t, { pos: [0.6, y + RISE_, 4.3], yaw: Math.PI, k: 0, lookAt: cam.pos }));
      out = { cam, exposure: 1.4, overlay: <Peephole t={t} /> };
      break;
    }
    // ================================================================ helper renders (no tape look): the 1974 photo
    case "mk_photo":
    case "mk_manface": {
      const b = world.block!;
      const mp = b.manPos ?? new THREE.Vector3(MAN_X, 0.9 + 5 * FLOOR_H, -0.2);
      if (b.manPos) add(hero, poseRaise(hero, 3, { pos: [mp.x, mp.y, mp.z], yaw: 0, k: 0, lookAt: shot === "mk_photo" ? PHOTO_CAM.pos : [mp.x + 0.3, mp.y + 1.55, 6] }));
      const pc: Cam = shot === "mk_photo" ? PHOTO_CAM : { pos: [mp.x + 0.25, mp.y + 1.62, 1.6], target: [mp.x, mp.y + 1.58, mp.z], fov: 24 };
      return (
        <AbsoluteFill style={{ background: "#BFC6C8" }}>
          <Stage3D cam={pc} lights="none" env={0} dpr={0.4} pixelated fog={{ color: "#C8CCCC", near: 40, far: 160 }} exposure={1.1}>
            <color attach="background" args={["#C8CDD0"]} />
            <hemisphereLight args={["#E8ECEE", "#5A564E", 1.4]} />
            <directionalLight position={[-30, 40, 30]} intensity={2.2} castShadow />
            {objs.map((o, i) => (
              <primitive key={i} object={o} />
            ))}
          </Stage3D>
        </AbsoluteFill>
      );
    }
    default:
      out = { cam: { pos: [0, 1.6, 2], target: [0, 1.4, 0], fov: 60 } };
  }
  if (world.lamps.length && out!.lamps) {
    applyLamps(world.lamps, t, out!.lamps);
    const cp = new THREE.Vector3(...out!.cam.pos);
    const near = [...world.lamps].sort((a, b) => a.light.getWorldPosition(new THREE.Vector3()).distanceTo(cp) - b.light.getWorldPosition(new THREE.Vector3()).distanceTo(cp));
    world.lamps.forEach((l) => (l.light.castShadow = near.indexOf(l) < 2));
  }
  if (out!.flash) aimFlashlight(flash, out!.cam, out!.flash, 0.05, t);
  const recClock = (out as { rec?: string }).rec;
  const o = out!;
  // the room at night: cold street light bounced off the ceiling, enough to read shapes
  const roomNight = sets.includes("room") && !REC.has(shot) && shot !== "morning_bed" && shot !== "palm_stain";
  const expo = roomNight ? Math.max(o.exposure ?? 1.35, 1.75) : o.exposure;
  return (
    <AbsoluteFill>
      <PzFrame t={t} cam={o.cam} fog={o.fog} exposure={expo} wear={o.wear} counter0={c0} rec={recClock ? { clock: recClock } : null} bg={o.bg}>
        {o.light}
        {roomNight ? (
          <>
            <hemisphereLight args={["#56699A", "#15120E", 0.6]} />
            <pointLight position={[0.3, 1.0, -0.2]} color="#8A9CC4" intensity={1.3} distance={3.5} decay={1.3} />
          </>
        ) : null}
        {o.flash ? (
          <>
            <primitive object={flash} />
            <primitive object={flash.target} />
          </>
        ) : null}
        {objs.map((ob, i) => (
          <primitive key={i} object={ob} />
        ))}
      </PzFrame>
      {o.tint ? <AbsoluteFill style={{ background: o.tint, mixBlendMode: "multiply", opacity: 0.55, pointerEvents: "none" }} /> : null}
      {o.overlay}
    </AbsoluteFill>
  );
};
const RISE_ = 1.4;
void stepA;

/** door peephole: round fisheye window, dark ring, soft edge */
const Peephole: React.FC<{ t: number }> = ({ t }) => (
  <AbsoluteFill style={{ pointerEvents: "none" }}>
    <AbsoluteFill style={{ background: `radial-gradient(circle at ${50 + Math.sin(t * 1.3) * 0.6}% 46%, rgba(0,0,0,0) 0%, rgba(0,0,0,0) 30%, rgba(0,0,0,0.55) 37%, #000 41%)` }} />
  </AbsoluteFill>
);

// ================================================================ tape inserts (DOM): title cards, two audio tracks, the photo
const PIX = "'Press Start 2P', monospace";
const stepT = (t: number) => Math.floor(t * 12) / 12;
export const S6Insert: React.FC<{ kind: "card" | "tracks" | "count" | "zoom" | "match" | "back"; lines?: string[]; ev?: Record<string, number>; delay?: boolean; c0?: number }> = ({ kind, lines = [], ev = {}, delay = false, c0 = 0 }) => {
  const { f, fps } = useBlockTime();
  const t = f / fps;
  const tq = stepT(t);
  let body: React.ReactNode = null;
  if (kind === "card") {
    body = (
      <AbsoluteFill style={{ background: "#020203", alignItems: "center", justifyContent: "center", flexDirection: "column", gap: 40 }}>
        {lines.map((l, i) => (
          <div key={i} style={{ fontFamily: PIX, fontSize: i === 0 ? 88 : 46, color: i === 0 ? "#F2F2EE" : "#C9C9C2", textShadow: "6px 6px 0 #000, -3px 0 0 rgba(255,40,70,0.6), 3px 0 0 rgba(40,140,255,0.6)", opacity: tq >= i * 0.25 ? 1 : 0 }}>
            {l.slice(0, Math.max(0, Math.floor((tq - i * 0.25) * 22)))}
          </div>
        ))}
      </AbsoluteFill>
    );
  } else if (kind === "tracks") {
    // two channels of the tape's audio: my steps, and the steps above 3 s later
    const span = 8, x0 = 90, wpx = 900;
    const steps = [0.35, 1.52, 2.69, 3.86];
    const head = Math.min(span, 1.5 + t * 1.6);
    const wave = (shift: number, color: string, y: number, label: string) => {
      const pts: string[] = [];
      for (let i = 0; i <= 300; i++) {
        const s = (i / 300) * span;
        let a = 0.06 * Math.sin(s * 91) * Math.sin(s * 13);
        for (const st of steps) {
          const d = s - (st + shift);
          if (d > 0 && d < 0.35) a += Math.exp(-d * 14) * Math.sin(d * 120) * 0.9;
        }
        if (s > head) a = 0;
        pts.push(`${x0 + (i / 300) * wpx},${y - a * 70}`);
      }
      return (
        <g>
          <text x={x0} y={y - 110} fill={color} fontFamily={PIX} fontSize={26}>{label}</text>
          <line x1={x0} y1={y} x2={x0 + wpx} y2={y} stroke={color} strokeOpacity={0.25} strokeWidth={2} />
          <polyline points={pts.join(" ")} fill="none" stroke={color} strokeWidth={4} />
        </g>
      );
    };
    const hx = x0 + (head / span) * wpx;
    const bx0 = x0 + (steps[1] / span) * wpx, bx1 = x0 + ((steps[1] + 3) / span) * wpx;
    body = (
      <AbsoluteFill style={{ background: "#03060A" }}>
        <svg width={1080} height={1920}>
          <text x={90} y={640} fill="#7FE08A" fontFamily={PIX} fontSize={30}>ЗАПИСЬ 03:12  НОЧЬ 1</text>
          {wave(0, "#7FE08A", 860, "КАН.1  МОИ ШАГИ")}
          {wave(3, "#E8D36A", 1140, "КАН.2  СВЕРХУ")}
          <line x1={hx} y1={700} x2={hx} y2={1220} stroke="#FFFFFF" strokeWidth={3} />
          {delay && tq > 0.3 ? (
            <g>
              <line x1={bx0} y1={1235} x2={bx1} y2={1235} stroke="#FF3A2E" strokeWidth={6} />
              <line x1={bx0} y1={1215} x2={bx0} y2={1255} stroke="#FF3A2E" strokeWidth={6} />
              <line x1={bx1} y1={1215} x2={bx1} y2={1255} stroke="#FF3A2E" strokeWidth={6} />
              <text x={(bx0 + bx1) / 2} y={1320} fill="#FF3A2E" fontFamily={PIX} fontSize={48} textAnchor="middle" opacity={Math.floor(t * 4) % 2 ? 1 : 0.6}>3.0 СЕК</text>
            </g>
          ) : null}
        </svg>
      </AbsoluteFill>
    );
  } else if (kind === "back") {
    // the back of the photo, close: the handwriting appears as it is read
    const l1 = "Не позволяйте жильцу сверху", l2 = "узнать, что этаж исчез.";
    const t2 = ev.l2 ?? 1.85, tEnd = ev.end ?? 2.9;
    const n1 = Math.floor(Math.min(1, tq / Math.max(0.3, t2 - 0.15)) * l1.length);
    const n2 = Math.floor(Math.max(0, Math.min(1, (tq - t2) / Math.max(0.3, tEnd - t2))) * l2.length);
    const push = 1 + sm(t / 3.4) * 0.1;
    const HANDF = "'Segoe Script', 'Comic Sans MS', cursive";
    body = (
      <AbsoluteFill style={{ background: "#0A0907" }}>
        <AbsoluteFill style={{ transform: `scale(${push}) rotate(-2.5deg)`, transformOrigin: "50% 52%" }}>
          <div style={{ position: "absolute", left: 50, top: 600, width: 980, height: 735, background: "#E6DEC8", boxShadow: "0 0 0 8px #CDC3AA, 0 30px 60px rgba(0,0,0,0.7)", overflow: "hidden" }}>
            <div style={{ position: "absolute", left: 620, top: 40, width: 260, height: 230, borderRadius: "50%", background: "radial-gradient(circle, rgba(120,95,60,0.28) 0%, rgba(120,95,60,0.12) 55%, rgba(0,0,0,0) 72%)" }} />
            <div style={{ position: "absolute", left: 56, top: 250, fontFamily: HANDF, fontSize: 47, color: "#1E2448", lineHeight: 1.7, whiteSpace: "pre" }}>
              {l1.slice(0, n1) + "\n" + l2.slice(0, n2)}
            </div>
            <div style={{ position: "absolute", right: 90, bottom: 70, fontFamily: HANDF, fontSize: 44, color: "#1E2448" }}>1974</div>
          </div>
        </AbsoluteFill>
      </AbsoluteFill>
    );
  } else if (kind === "count" || kind === "zoom" || kind === "match") {
    // the photo fills the width, centred (the same crop it was made from, so the projected floors line up)
    const cam = makeCamera(PHOTO_CAM);
    const floorY = (n: number) => project(cam, new THREE.Vector3(MAN_X - 3.4, 0.9 + (n - 1) * FLOOR_H + 1.6, 0))[1];
    const winP = project(cam, new THREE.Vector3(MAN_X, 0.9 + 5 * FLOOR_H + 1.55, 0));
    const zoomK = kind === "zoom" ? sm((t - 0.1) / 1.8) : 0;
    const s = 1 + zoomK * 4.2;
    const shown = kind === "count" ? Math.min(6, Math.floor(tq / 0.28) + 1) : 0;
    const six = ev.six ?? 1.7;
    const photoImg = (
      <div style={{ position: "absolute", left: 0, top: 555, width: 1080, height: 810, overflow: "hidden", border: "10px solid #E9E3D2", boxSizing: "border-box" }}>
        <Img src={staticFile(P + "photo1974.jpg")} style={{ width: "100%", height: "100%", objectFit: "cover", filter: "grayscale(1) sepia(0.35) contrast(1.15)" }} />
      </div>
    );
    if (kind === "match") {
      const k = sm((t - 0.2) / 0.5);
      body = (
        <AbsoluteFill style={{ background: "#050505" }}>
          <div style={{ position: "absolute", left: 60, top: 420, width: 960, height: 520, overflow: "hidden", border: "8px solid #E9E3D2", boxSizing: "border-box" }}>
            <Img src={staticFile(P + "man_face.jpg")} style={{ width: "100%", height: "100%", objectFit: "cover", filter: "grayscale(1) sepia(0.4) contrast(1.2)" }} />
          </div>
          <div style={{ position: "absolute", left: 60, top: 980, width: 960, height: 520, overflow: "hidden", border: "8px solid #3A3A3A", boxSizing: "border-box", opacity: k }}>
            <Img src={staticFile(P + "hero_face.jpg")} style={{ width: "100%", height: "100%", objectFit: "cover", filter: "grayscale(1) contrast(1.15)" }} />
          </div>
          <div style={{ position: "absolute", left: 90, top: 440, fontFamily: PIX, fontSize: 34, color: "#F2F2EE", textShadow: "4px 4px 0 #000" }}>1974</div>
          <div style={{ position: "absolute", left: 90, top: 1000, fontFamily: PIX, fontSize: 34, color: "#FF3A2E", textShadow: "4px 4px 0 #000", opacity: k }}>03:12  НОЧЬ 1</div>
        </AbsoluteFill>
      );
    } else {
      body = (
        <AbsoluteFill style={{ background: "#050505" }}>
          <AbsoluteFill style={{ transform: `scale(${s})`, transformOrigin: `${winP[0]}px ${winP[1]}px` }}>
            {photoImg}
            {kind === "count"
              ? [1, 2, 3, 4, 5, 6].slice(0, shown).map((n) => (
                  <div key={n} style={{ position: "absolute", left: 40, top: floorY(n) - 30, fontFamily: PIX, fontSize: 52, color: n === 6 && t >= six ? "#FF3A2E" : "#FFFFFF", textShadow: "5px 5px 0 #000", opacity: n === 6 && t >= six && Math.floor(t * 6) % 2 ? 0.5 : 1 }}>
                    {n}
                  </div>
                ))
              : null}
          </AbsoluteFill>
        </AbsoluteFill>
      );
    }
  }
  return (
    <VhsLook t={t} wear={kind === "card" ? 0.7 : 0.45} counter0={c0} osd={kind !== "card"}>
      {body}
    </VhsLook>
  );
};
