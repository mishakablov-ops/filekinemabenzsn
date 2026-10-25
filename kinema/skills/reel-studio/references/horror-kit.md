# Horror / analog-tape kit (PS1 lowpoly + VHS)

Two finished reels are the templates: **`podezd`** («Подъезд», 1:57, a Khrushchyovka stairwell, 5 own characters, a creature)
and **`sosed6`** («Сосед с шестого этажа», 1:45, 57 shots ≤ 2.5 s, camcorder night, first-person hands, inserts).
Both are ready to render: `engine/public/projects/<id>/` holds the spec, voice, word timings, rigged characters and textures;
their builders are in `assets/models-src/<id>/`. Sounds are **not** included — see `SOUNDS.md` in each project
(missing project sounds are skipped by the engine, the reel still renders).

## Files
| what | where |
|---|---|
| PS1 look: `psxify(group)` (vertex snap to 184×326, 15-bit colour + 4×4 dither, nearest textures, flat shading) and `VhsLook` (chroma split, wobble, scanlines, grain, tracking noise, OSD `▶ PLAY` + date + counter, or `rec={{clock}}` for a camcorder `● REC`) | `engine/src/three/psx.tsx` |
| Frame wrapper: Stage3D at `dpr 0.17` + `pixelated`, fog, exposure, VHS on top | `PzFrame` in `engine/src/three/podezd.tsx` |
| Sets (stairwell with N floors, block of flats day/night, bedroom, booth, basement, hatch, hallway, mailboxes…) | `podezdSets.ts`, `sosedSets.ts` |
| Shots: one component, a `switch` on a shot id, event times in `ev` (seconds into the shot, from the storyboard) | `podezdShots.tsx` (`PzShot`), `sosedShots.tsx` (`S6Shot`, `S6Insert` for DOM inserts: title card, audio tracks, photo, face match, handwriting) |
| Characters: `createHuman(glb, {tint, selfShadow})`, poses `poseCornerCry poseCrouch poseSitHoldHead poseFloorCover poseChair posePoint poseWalk poseRaise` (FK + two-bone IK, look-at, feet planted while walking) | `engine/src/three/human.ts` |
| First-person hands: `createFPRig`, keyframed hand tracks in camera space, finger poses (`grip pinch point flat relaxed…`), `graspCentre` / `handFrame` to put objects in the hand | `engine/src/three/fphands.ts`, arms `engine/public/models/fp_arms.glb` (CC BY, credit in `models/CREDITS.md`) |
| Storyboard builder: shots anchored to words, `ev` from words, SFX list, CTA | `assets/models-src/sosed6/storyboard.py` (copy this one) |
| Voice: Gemini «Algenib», one call per section with its own direction, 2 takes | `assets/models-src/<id>/voice_sections.py` |
| Quick look at single shots (3–6 moments each, one sheet) | `assets/models-src/sosed6/lab.py shotA shotB --at 0.2,0.6,0.95` |

## Making your own characters (no Mixamo, no stock)
1. `assets/models-src/podezd/chars/gen_chars.py ref <name>` — a T-pose full-body reference (nano-banana-pro, ~$0.30). **T-pose only**: an A-pose with arms near the body cannot be rigged cleanly.
2. `gen_chars.py mesh <name>` — image → textured quad mesh (hyper3d/rodin, ~$1.50).
3. `blender -b --factory-startup --disable-autoexec --python rig_chars.py -- <name> <height_m> in.glb out.glb test.png tris=1800 tex=256` — joints found from the mesh, Mixamo-style bone names, weights, then decimated to ~1800 faceted tris and a 256 px texture. Put `out.glb` in `engine/public/projects/<id>/models/`.
4. In code: `useActor("<name>")` (see `podezdShots.tsx`) → `createHuman`, then pose it every frame with the pose functions. A creature lit by a torch needs `selfShadow: false`.
Textures: `textures/gen_textures.py` (seamless 2048 px) → `textures/make_lo.py <id>` (64–128 px PS1 tiles in `tex_lo/`).
Replicate spending is capped at **$3 per job** (`REPLICATE_JOB=<id>`, cap `REPLICATE_CAP_USD`, ledger `.replicate_budget.json`) — raise it only when the user agrees.

## Rules learned the hard way
- **Hand tracks target the WRIST, not the fingertips.** The index tip is ~0.17 m further along the fingers. Pressing a button: wrist = button + 0.17 m back along the finger direction. Holding a photo by its edge: wrist ~7 cm outside the edge. Targeting the object itself drives the whole hand into it (black frames, a hand covering the picture).
- **Nothing moves on its own.** A held object is placed from the hand every frame (`graspCentre` + `handFrame`); when it is picked up, blend it from its rest pose into the grip over ~0.12 s. A photo turned over = the forearm rolls with the grip on the turn axis — never spin an object in the air.
- **Call `world.g.updateMatrixWorld(true)`** before reading world positions in a shot (mailbox numbers, labels): the first rendered frame otherwise reads identity matrices and the camera points at the floor.
- **No black frames.** Night ≠ unreadable: a cold hemisphere fill + a bounce light, exposure 1.6–1.9, check every shot on a sheet. Dark materials (leatherette door, wardrobe) need their own light.
- **Text on things:** check it reads the right way from the camera (a decal seen from below is mirrored/rotated); paint that should bend with geometry (a dented lid) must live on the same mesh.
- **Doors swing toward one side:** film an open box/door from the hinge side, or the leaf blocks the view.
- **Walks:** `poseWalk` plants feet; size the walk so it ends exactly on the word (`speed = length / (t_stop − t_start)`), and keep the walker inside the camera's view the whole way.
- **Close-ups of lowpoly hands/arms from below read as cones** — film the result (the ceiling pushing down) instead.
- Shots 1–2.5 s, a new thing to look at in every shot; inserts (cards, waveforms, photo, face match) break the 3D rhythm.

## Sound for this style
User packs (scream, drone, steps, creaks, clock, tape…) live in `projects/<id>/sfx-src/` and are cued by name in the storyboard.
"Through the ceiling": `ffmpeg -i x.mp3 -af "lowpass=f=700,lowpass=f=900,aecho=0.8:0.6:45|90:0.35|0.2,volume=2.2" x_muf.mp3`.
Repeat-with-delay tricks are built from the storyboard (his steps on the floor, the same steps above 3 s later).
