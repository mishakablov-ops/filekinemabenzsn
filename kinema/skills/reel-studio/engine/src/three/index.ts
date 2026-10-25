import { defineBlock, type BlockDef } from "../blocks/registry";
import { City3D } from "./city";
import { Laptop3D, Phone3D } from "./devices";
import { Globe3D } from "./globe";
import { Bars3D, Cards3D, Shapes3D, StarRain, Tilt, Tunnel3D } from "./misc3d";
import { ShaderBG, SHADER_PRESETS } from "./shaders";
import { Terrain3D } from "./terrain";
import { Room3D } from "./room";
import { Street3D } from "./street";
import { Blast3D } from "./blast";
import { Scene3D } from "./scene3d";
import { IPhone17, MacBook, Model3D } from "./model";
import { BarracksTest, JeepDriveTest, JsaTest, MxTest, RescueTest, SoldiersTest } from "./nk";
import { PzPoseTest, PzSetTest, PzTest } from "./podezd";
import { PzShot } from "./podezdShots";
import { S6Insert, S6Shot } from "./sosedShots";
import { NkBarracks, NkBridge, NkChase, NkCctv, NkDitch, NkDrive, NkFall, NkHeli, NkOutro, NkSurgery } from "./nkReel";

export const THREE_BLOCKS: Record<string, BlockDef> = {
  S6Shot: defineBlock({
    C: S6Shot, cat: "3d", pos: "full", self: true, sfx: null,
    desc: "Сосед с шестого этажа: one shot by id (PS1 + VHS), ev = event times, c0 = tape counter.", example: { shot: "bed_up" }, exampleDur: 2,
  }),
  S6Insert: defineBlock({
    C: S6Insert, cat: "3d", pos: "full", self: true, sfx: null,
    desc: "Сосед с шестого этажа: tape inserts (card, tracks, count, zoom, match).", example: { kind: "card", lines: ["НОЧЬ 1"] }, exampleDur: 2,
  }),
  PzPoseTest: defineBlock({
    C: PzPoseTest, cat: "3d", pos: "full", self: true, sfx: null,
    desc: "podezd: debug one actor in one pose under plain light.", example: { who: "him", pose: "floor" }, exampleDur: 2,
  }),
  PzShot: defineBlock({
    C: PzShot, cat: "3d", pos: "full", self: true, sfx: null,
    desc: "podezd horror reel: one shot by id (hook, moan, block, upgap, landing, boothWindow, journal, serega, ask, graffiti, crane, listen, pipe, upfast, breath, wake, bed, railing, point, boothEnter, journalFloor, door, call, cry, torch, nosig, count, scratches, doorway, him, face, scarf, step, lower); ev = event times.",
    example: { shot: "hook" }, exampleDur: 3,
  }),
  PzSetTest: defineBlock({
    C: PzSetTest, cat: "3d", pos: "full", self: true, sfx: null,
    desc: "podezd horror: test of one location (booth, boothAfter, descent, lair, bedroom, pipe, block) with its actor.",
    example: { set: "booth" }, exampleDur: 3,
  }),
  PzTest: defineBlock({
    C: PzTest, cat: "3d", pos: "full", self: true, sfx: null,
    desc: "podezd horror: test of the Khrushchyovka stairwell, residents and poses (PS1 + VHS look). cam keys, who, flicker, breath, look.",
    example: {}, exampleDur: 3,
  }),
  NkChase: defineBlock({
    C: NkChase, cat: "3d", pos: "full", self: true, sfx: null,
    desc: "nk reel: first-person run at Panmunjom on the chase clock. tau0, look:[tau,dur], exit.",
    example: {}, exampleDur: 3,
  }),
  NkCctv: defineBlock({
    C: NkCctv, cat: "3d", pos: "full", self: true, sfx: null,
    desc: "nk reel: UN surveillance-camera shot. tau0, cam keys, label, jeepSpin.",
    example: {}, exampleDur: 3,
  }),
  NkFall: defineBlock({
    C: NkFall, cat: "3d", pos: "full", self: true, sfx: null,
    desc: "nk reel: hit, hit, fall into the leaves. tau0.",
    example: {}, exampleDur: 3,
  }),
  NkBarracks: defineBlock({
    C: NkBarracks, cat: "3d", pos: "full", self: true, sfx: null,
    desc: "nk reel: barracks, first person. mode drink|slam, slamAt, lookAt, dreadAt.",
    example: {}, exampleDur: 3,
  }),
  NkDrive: defineBlock({
    C: NkDrive, cat: "3d", pos: "full", self: true, sfx: null,
    desc: "nk reel: in the jeep on the road. mode start|checkpoint.",
    example: {}, exampleDur: 3,
  }),
  NkBridge: defineBlock({
    C: NkBridge, cat: "3d", pos: "full", self: true, sfx: null,
    desc: "nk reel: drone shot of the jeep on the 72-hour bridge.",
    example: {}, exampleDur: 3,
  }),
  NkDitch: defineBlock({
    C: NkDitch, cat: "3d", pos: "full", self: true, sfx: null,
    desc: "nk reel: Panmunjom by jeep. mode approach|ditch, dropAt, revAt.",
    example: {}, exampleDur: 3,
  }),
  NkHeli: defineBlock({
    C: NkHeli, cat: "3d", pos: "full", self: true, sfx: null,
    desc: "nk reel: looking up at the helicopter from a stretcher.",
    example: {}, exampleDur: 3,
  }),
  NkSurgery: defineBlock({
    C: NkSurgery, cat: "3d", pos: "full", self: true, sfx: null,
    desc: "nk reel: operating lamp, white-out at whiteAt.",
    example: {}, exampleDur: 3,
  }),
  NkOutro: defineBlock({
    C: NkOutro, cat: "3d", pos: "full", self: true, sfx: null,
    desc: "nk reel: last shots over the line. view line|wide.",
    example: {}, exampleDur: 3,
  }),
  RescueTest: defineBlock({
    C: RescueTest, cat: "3d", pos: "full", self: true, sfx: null,
    desc: "nk-escape test: ROK soldiers crawl to the defector and drag him (his eyes or a side view).",
    example: {}, exampleDur: 8,
  }),
  MxTest: defineBlock({
    C: MxTest, cat: "3d", pos: "full", self: true, sfx: null,
    desc: "nk-escape test: Mixamo soldiers. view: gallery|chase; qa logs feet checks.",
    example: {}, exampleDur: 4,
  }),
  SoldiersTest: defineBlock({
    C: SoldiersTest, cat: "3d", pos: "full", self: true, sfx: null,
    desc: "nk-escape test: procedural soldiers (pose gallery).",
    example: {}, exampleDur: 3,
  }),
  BarracksTest: defineBlock({
    C: BarracksTest, cat: "3d", pos: "full", self: true, sfx: null,
    desc: "nk-escape test: KPA barracks room, first person at the table (one hand takes the cup).",
    example: {}, exampleDur: 6,
  }),
  JsaTest: defineBlock({
    C: JsaTest, cat: "3d", pos: "full", self: true, sfx: null,
    desc: "nk-escape test: Panmunjom JSA set. view: overview|run (first-person run to the wall).",
    example: { view: "run" }, exampleDur: 5,
  }),
  JeepDriveTest: defineBlock({
    C: JeepDriveTest, cat: "3d", pos: "full", self: true, sfx: null,
    desc: "nk-escape test: first-person drive in the jeep with live hands on the wheel (project-specific).",
    example: {}, exampleDur: 8,
  }),
  ShaderBG: defineBlock({
    C: ShaderBG, cat: "bg", pos: "full", self: true,
    desc: `GPU shader background. preset: ${SHADER_PRESETS.join("|")}. skyAbove = flying over a sea of clouds; skyBelow = cumulus overhead; cloudWall = soft overcast; liquid = premium flowing gradient (theme colours); aurora; contour = topographic lines; rays; smoke. colors:[c1..c4], speed, sun, cover.`,
    example: { preset: "skyAbove" },
  }),
  Laptop3D: defineBlock({
    C: Laptop3D, cat: "3d", pos: "full", self: true, sfx: null,
    desc: "Real 3D laptop (PBR metal, reflections, shadow) with a LIVE HTML screen: screen:{block,props} or src image. cam: hero|orbit|lowAngle|zoomScreen|top|side|close or keyframes. open:true animates the lid. color: silver|space|midnight|black.",
    events: (p, t) => (p.open ? [{ f: p.openAt !== undefined ? t.at(p.openAt) : 9, id: "whoosh-airy", vol: 0.6 }, { f: (p.openAt !== undefined ? t.at(p.openAt) : 9) + Math.round(1.1 * t.fps), id: "click-soft", vol: 0.6 }] : []),
    example: { screen: { block: "Title", props: { text: "Привет, *3D*" } }, cam: "hero", open: true },
    exampleDur: 4,
  }),
  Phone3D: defineBlock({
    C: Phone3D, cat: "3d", pos: "full", self: true, sfx: "whoosh-airy",
    desc: "Real 3D phone(s) with LIVE HTML screens. phones:[{screen,pos,rot,color}] for a fan of up to 3 (keep them from overlapping). cam: hero|close|low|wide. turn:[fromDeg,toDeg], enterSpin. color: titanium|black|silver|white|gold.",
    example: { screen: { block: "Title", props: { text: "9:41" } }, enterSpin: true },
    exampleDur: 4,
  }),
  Globe3D: defineBlock({
    C: Globe3D, cat: "3d", pos: "full", self: true, sfx: "whoosh-deep",
    desc: "Earth with real coastlines. look: dots|solid|night|light. focus:[{t,lat,lon,dist}] flies the camera; markers:[{lat,lon,label,at}] pulse + HTML label; arcs:[{from:[lat,lon],to:[lat,lon],at,dur}] animated flight lines.",
    events: (p, t) => [
      ...((p.markers ?? []) as { at?: unknown }[]).map((m) => ({ f: m.at !== undefined ? t.at(m.at) : 0, id: "ping-sonar", vol: 0.5 })),
      ...((p.arcs ?? []) as { at?: unknown }[]).map((a, i) => ({ f: a.at !== undefined ? t.at(a.at) : Math.round((0.4 + i * 0.5) * t.fps), id: "whoosh-up", vol: 0.5 })),
    ],
    example: { look: "dots", focus: [{ t: 0, lat: 30, lon: 80, dist: 3.8 }, { t: 2.5, lat: 49, lon: -123, dist: 2.6 }], markers: [{ lat: 49.2, lon: -123.1, label: "49.21° N · 123.11° W", at: 2.4 }], arcs: [{ from: [23.7, 113.1], to: [49.2, -123.1], at: 0.5, dur: 1.8 }] },
    exampleDur: 4,
  }),
  Terrain3D: defineBlock({
    C: Terrain3D, cat: "3d", pos: "full", self: true, sfx: "whoosh-deep",
    desc: "Procedural mountains. look: satellite|alpine|topo|desert|mono. cam: flyover|orbit|reveal|top|low. contours (0..1), scan:{at,dur} sweeping band, highlightHeight (accent iso-line), points:{count,at,dur} viewpoints appearing, pins:[{x,z,label,at}].",
    events: (p, t) => (p.scan ? [{ f: p.scan.at !== undefined ? t.at(p.scan.at) : 0, id: "scan-beep", vol: 0.5 }] : []),
    example: { look: "alpine", cam: "reveal", contours: 0.25, points: { count: 1500, at: 1.5, dur: 2 } },
    exampleDur: 4,
  }),
  City3D: defineBlock({
    C: City3D, cat: "3d", pos: "full", self: true, sfx: "whoosh-medium",
    desc: "Procedural city that grows from the ground. look: warm|white|night|clay. cam: orbit|dive|street|iso. blossom 0..1 = share of pink trees; downtown = tower height; highlight:{x,z,label,at} target ring.",
    events: (p, t) => (p.highlight ? [{ f: p.highlight.at !== undefined ? t.at(p.highlight.at) : Math.round(1.5 * t.fps), id: "ping", vol: 0.6 }] : []),
    example: { look: "warm", cam: "dive", blossom: 0.4, highlight: { x: 2, z: 2, label: "49.2158° N · 123.1087° W", at: 3 } },
    exampleDur: 4,
  }),
  Shapes3D: defineBlock({ C: Shapes3D, cat: "3d", pos: "full", self: true, sfx: "reveal-glow", desc: "Glossy iridescent hero objects: blob|torus|knot|rings|pills|cubes, glass:true for transmission. Use sparingly — abstract shapes read as generic.", example: { kind: "rings" } }),
  Bars3D: defineBlock({ C: Bars3D, cat: "3d", pos: "full", self: true, sfx: "riser-short", desc: "3D bar chart growing with HTML value labels. bars:[{label,value,color}], unit, cam: orbit|front. Last bar uses the accent.", example: { bars: [{ label: "янв", value: 120 }, { label: "фев", value: 210 }, { label: "мар", value: 340 }, { label: "апр", value: 610 }], unit: "" } }),
  Tunnel3D: defineBlock({ C: Tunnel3D, cat: "3d", pos: "full", self: true, sfx: "trans-zoom-through", desc: "Flying through glowing rings/squares/hexes. Intros, 'deep dive' moments, transitions.", example: { shape: "hex" } }),
  StarRain: defineBlock({ C: StarRain, cat: "3d", pos: "full", self: true, sfx: "sparkle-rise", desc: "3D stars / coins / hearts raining and tumbling (GitHub stars, rewards, likes). Transparent — overlay on any scene.", example: { kind: "star" } }),
  Cards3D: defineBlock({ C: Cards3D, cat: "3d", pos: "full", self: true, sfx: "swipe-soft", desc: "CSS-3D (crisp HTML) cards floating in depth with a moving camera. items:[{block,props|src,x,y,z,rx,ry,w,h,at}], cam:{from:[x,y,z],to,rx:[a,b],ry:[a,b]}.", example: { items: [{ block: "Title", props: { text: "Один" }, x: -250, z: -200 }, { block: "Title", props: { text: "Два" }, x: 250, z: 0 }] } }),
  Tilt: defineBlock({ C: Tilt, cat: "3d", pos: "center", self: true, sfx: "whoosh-airy", desc: "Wrap any block in a slow perspective tilt (2.5D). child:{block,props}, rx:[from,to], ry:[from,to], w,h.", example: { child: { block: "Title", props: { text: "Tilt" } } } }),
  Room3D: defineBlock({
    C: Room3D, cat: "3d", pos: "full", self: true, sfx: "whoosh-airy",
    desc: "Cut-away 3D room diorama in dark pastel. preset: office|living|bedroom|cafe|studio + cozy library (wall of books, armchair reader, candle) | kitchen (counter, stove with steam, fridge, dining table) | cabin (log walls, real fireplace) | basement (concrete shelter: supply racks, water, crank radio, lantern, sandbags, steel door, tally board). people:[{pose,pos,rotY,seed,look:{suit:true = improvised protective gear},walkTo}] (fpv cams default to nobody). screen:{block,props} = LIVE HTML on the monitor (office) or TV (living). cam: diorama|front|closeDesk|pushIn|top|inside; library: reading|shelves; kitchen: counter|table; cabin: fire; basement: corner + first-person fpvEnter|fpvShelf|fpvRadio|fpvDoor|fpvWindow|fpvBed|fpvTally|fpvHands. hands:{item:radio|can|bottle|tape|lantern|geiger|mask, gloves, sleeve, from} = your own hands in a first-person shot. basement: days (tally marks), door 0..1 or [from,to] animated, lantern. lights: day|evening|night. build:true pops the room up.",
    example: { preset: "office", cam: "diorama" },
    exampleDur: 4,
  }),
  Street3D: defineBlock({
    C: Street3D, cat: "3d", pos: "full", self: true, sfx: "whoosh-medium",
    desc: "Ordinary city street: buildings with windows, moving cars, walking people, lamps, trees, crosswalk + traffic lights. time: day|evening|night; cam: eye|high|follow|crossing|top|drone; cars, people counts; traffic red|green; highlight:{x,z,label,at}. abandoned:true = after a disaster: empty, dusty fog, abandoned cars with open doors, dead trees, rubble, paper, barricade, falling ash (ash:false to stop), lights dead; walkers:[{x,z,speed,dir,look:{suit:true}}] for a lone survivor.",
    example: { time: "evening", cam: "eye" },
    exampleDur: 4,
  }),
  Blast3D: defineBlock({
    C: Blast3D, cat: "3d", pos: "full", self: true, sfx: null,
    desc: "Nuclear blast over a distant city at dusk (stylized, no gore): flash (warm, never pure white) at flashAt, fireball → mushroom cloud rising for ~9 s, ground shockwave sweeping to the camera at waveAt (default flashAt+3.2) with camera shake, dust haze and falling ash. cam: hill|street|wide or keyframes. Cue your own boom/rumble SFX on flashAt and waveAt.",
    example: { cam: "hill", flashAt: 0.6 },
    exampleDur: 8,
  }),
  Scene3D: defineBlock({
    C: Scene3D, cat: "3d", pos: "full", self: true, sfx: "whoosh-airy",
    desc: "Compose your own low-poly scene: objects:[{type,pos,rotY,at,...}] types person|desk|chair|monitor|laptop|sofa|bed|table|shelf|plant|lamp|rug|frame|mug|pendant|counter|stool|tv|car|tree|streetlamp|bench|traffic|building|box. Persons: pose stand|walk|run|sit|type|wave|point|think|phone|cheer, walkTo. labels:[{text,pos,at}]. cam keyframes.",
    example: { objects: [{ type: "rug", pos: [0, 0, 0], w: 4, d: 3 }, { type: "person", pos: [-0.8, 0, 0], pose: "wave", rotY: 0.4 }, { type: "person", pos: [0.8, 0, 0.2], pose: "think", rotY: -0.4, seed: 3 }, { type: "plant", pos: [2, 0, -1] }], labels: [{ text: "Привет!", pos: [-0.8, 2.3, 0], at: 1 }] },
    exampleDur: 4,
  }),
  Model3D: defineBlock({
    C: Model3D, cat: "3d", pos: "full", self: true, sfx: "whoosh-airy",
    desc: "Import any .glb/.gltf from engine/public/models (BlenderKit/Sketchfab/Poly Haven; convert .blend with scripts/blend2glb.py). fit = size, cam hero|orbit|low|top, spin deg/s, enter rise|spin, anim plays embedded clip. screenMesh + screen:{block,props} maps a LIVE HTML screen onto the model's display mesh.",
    exampleDur: 4,
  }),
  MacBook: defineBlock({
    C: MacBook, cat: "3d", pos: "full", self: true, sfx: "whoosh-airy",
    desc: "The user's real MacBook model (models/macbook.glb) with a LIVE HTML screen. screen:{block,props}; cam: orbit|hero|low|top|close|toScreen (flies into the display) or keyframes; spin; enter rise|spin|none.",
    example: { screen: { block: "Terminal", props: { w: 1280, h: 840, size: 34, lines: [{ kind: "prompt", text: "собери ролик" }] } }, cam: "orbit" },
    exampleDur: 4,
  }),
  IPhone17: defineBlock({
    C: IPhone17, cat: "3d", pos: "full", self: true, sfx: "whoosh-airy",
    desc: "The user's real iPhone 17 Pro model (models/iphone17pro.glb) standing upright with a LIVE 390×844 screen (AppScreen, LockScreen, SocialProfile…). spin deg/s, enter spin|rise, cam keyframes or orbit|hero|close|toScreen.",
    example: { screen: { block: "LockScreen", props: { notes: [{ app: "Claude", text: "Ролик готов", at: 0.5 }] } }, spin: 10, enter: "spin" },
    exampleDur: 4,
  }),
};
