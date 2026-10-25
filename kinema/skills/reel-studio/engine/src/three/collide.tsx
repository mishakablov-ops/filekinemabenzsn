import { useThree } from "@react-three/fiber";
import React, { useLayoutEffect } from "react";
import * as THREE from "three";

/**
 * 3D interpenetration check (QA renders only). Groups tagged via userData:
 *   { qa: "person", pose }            a person
 *   { qa: "solid", seat?: boolean }   one piece of furniture / prop
 *   { qa: "furniture" }               container whose direct children are solids
 *   { qa: "walls" }                   container whose meshes are walls / floor
 * Standing/walking people must not intersect anything; seated/typing people may touch seats and desks.
 */
export const CollisionQA: React.FC<{ on?: boolean }> = ({ on }) => {
  const scene = useThree((s) => s.scene);
  useLayoutEffect(() => {
    if (!on) return;
    scene.updateMatrixWorld(true);
    const persons: { id: string; pose: string; box: THREE.Box3 }[] = [];
    const solids: { id: string; seat: boolean; box: THREE.Box3 }[] = [];
    scene.traverse((o) => {
      const u = o.userData ?? {};
      if (u.qa === "person") {
        const b = new THREE.Box3().setFromObject(o);
        // body core only: ignore arms/hair, keep torso + legs
        const c = new THREE.Vector3();
        b.getCenter(c);
        const core = new THREE.Box3(new THREE.Vector3(c.x - 0.17, b.min.y + 0.05, c.z - 0.13), new THREE.Vector3(c.x + 0.17, b.max.y - 0.05, c.z + 0.13));
        persons.push({ id: u.id ?? "person", pose: u.pose ?? "stand", box: core });
      } else if (u.qa === "solid") {
        solids.push({ id: u.id ?? o.name ?? "solid", seat: !!u.seat, box: new THREE.Box3().setFromObject(o).expandByScalar(-0.02) });
      } else if (u.qa === "furniture") {
        o.children.forEach((ch, i) => {
          const b = new THREE.Box3().setFromObject(ch);
          const s = new THREE.Vector3();
          b.getSize(s);
          if (s.y < 0.06 || b.min.y > 1.95) return; // rugs, wall art above heads
          solids.push({ id: `furniture${i}`, seat: s.y < 1.05 && s.y > 0.3, box: b.expandByScalar(-0.03) });
        });
      } else if (u.qa === "walls") {
        o.traverse((m) => {
          if ((m as THREE.Mesh).isMesh) {
            const b = new THREE.Box3().setFromObject(m);
            const s = new THREE.Vector3();
            b.getSize(s);
            if (s.y > 1.0) solids.push({ id: "wall", seat: false, box: b.expandByScalar(-0.01) });
          }
        });
      }
    });
    const issues: string[] = [];
    for (const p of persons) {
      const seated = p.pose === "sit" || p.pose === "type";
      for (const s of solids) {
        if (seated && s.id !== "wall") continue;
        if (p.box.intersectsBox(s.box)) issues.push(`${p.id}(${p.pose}) x ${s.id}`);
      }
    }
    for (let i = 0; i < persons.length; i++)
      for (let j = i + 1; j < persons.length; j++) if (persons[i].box.intersectsBox(persons[j].box)) issues.push(`${persons[i].id} x ${persons[j].id}`);
    // furniture must not interpenetrate furniture. Group boxes are only a pre-filter: a mug on a table sits inside the
    // table's box, so the real test is mesh against mesh (shrunk 1.5 cm: resting on a surface is touching, not clipping)
    const meshBoxes: THREE.Box3[][] = [];
    scene.traverse((o) => {
      if (o.userData?.qa !== "furniture") return;
      o.children.forEach((ch) => {
        const list: THREE.Box3[] = [];
        ch.traverse((m) => {
          if (!(m as THREE.Mesh).isMesh) return;
          const b = new THREE.Box3().setFromObject(m).expandByScalar(-0.015);
          if (!b.isEmpty()) list.push(b);
        });
        meshBoxes.push(list);
      });
    });
    const groupBox = meshBoxes.map((l) => l.reduce((acc, b) => acc.union(b), new THREE.Box3()));
    for (let i = 0; i < meshBoxes.length; i++)
      for (let j = i + 1; j < meshBoxes.length; j++) {
        if (groupBox[i].isEmpty() || groupBox[j].isEmpty() || !groupBox[i].intersectsBox(groupBox[j])) continue;
        if (meshBoxes[i].some((a) => meshBoxes[j].some((b) => a.intersectsBox(b)))) issues.push(`furniture${i} x furniture${j}`);
      }
    if (issues.length) console.log("QA " + JSON.stringify({ frame: -2, collisions3d: issues }));
  });
  return null;
};

/**
 * The camera must never enter or graze geometry (a first-person head-cam pushed into a shelf shows the inside of
 * meshes). Every tagged mesh (walls / furniture / solid / person) must stay `margin` metres from the eye.
 */
export const CameraClipQA: React.FC<{ on?: boolean; margin?: number }> = ({ on, margin = 0.2 }) => {
  const scene = useThree((s) => s.scene);
  const camera = useThree((s) => s.camera);
  useLayoutEffect(() => {
    if (!on) return;
    scene.updateMatrixWorld(true);
    camera.updateMatrixWorld(true);
    const eye = new THREE.Vector3().setFromMatrixPosition(camera.matrixWorld);
    const issues = new Set<string>();
    scene.traverse((o) => {
      const u = o.userData ?? {};
      if (!["walls", "furniture", "solid", "person"].includes(u.qa)) return;
      o.traverse((m) => {
        const mesh = m as THREE.Mesh;
        if (!mesh.isMesh || (mesh as THREE.InstancedMesh).isInstancedMesh) return;
        const d = new THREE.Box3().setFromObject(mesh).distanceToPoint(eye);
        if (d < margin) issues.add(`camera ${Math.round(d * 100)} cm from ${u.id ?? u.qa}`);
      });
    });
    if (issues.size) console.log("QA " + JSON.stringify({ frame: -2, collisions3d: [...issues].slice(0, 6) }));
  });
  return null;
};
