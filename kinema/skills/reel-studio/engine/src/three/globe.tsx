import React, { useMemo } from "react";
import { AbsoluteFill, random } from "remotion";
import * as THREE from "three";
import { feature } from "topojson-client";
import landTopo from "world-atlas/land-110m.json";
import { useBlockTime, useTheme } from "../core/context";
import { E, clamp01, lerp } from "../core/motion";
import { dotTexture, makeCamera, project, Stage3D, type Cam } from "./core";

export const ll2v = (lat: number, lon: number, r = 1) => {
  const la = THREE.MathUtils.degToRad(lat);
  const phi = ((lon + 180) / 360) * Math.PI * 2;
  return new THREE.Vector3(-Math.cos(phi) * Math.cos(la) * r, Math.sin(la) * r, Math.sin(phi) * Math.cos(la) * r);
};

type Ring = [number, number][];
let LAND_RINGS: Ring[] | null = null;
const landRings = () => {
  if (LAND_RINGS) return LAND_RINGS;
  const topo = landTopo as unknown as { objects: { land: unknown } };
  const geo = feature(topo as never, topo.objects.land as never) as unknown as { features?: { geometry: { type: string; coordinates: unknown } }[]; geometry?: { type: string; coordinates: unknown } };
  const geoms = geo.features ? geo.features.map((f) => f.geometry) : [geo.geometry!];
  const rings: Ring[] = [];
  geoms.forEach((g) => {
    if (g.type === "Polygon") (g.coordinates as Ring[]).forEach((r) => rings.push(r));
    if (g.type === "MultiPolygon") (g.coordinates as Ring[][]).forEach((p) => p.forEach((r) => rings.push(r)));
  });
  LAND_RINGS = rings;
  return rings;
};

const landCanvas = (w: number, h: number, land: string, ocean: string, outline?: string) => {
  const c = document.createElement("canvas");
  c.width = w;
  c.height = h;
  const g = c.getContext("2d")!;
  g.fillStyle = ocean;
  g.fillRect(0, 0, w, h);
  g.fillStyle = land;
  const X = (lon: number) => ((lon + 180) / 360) * w;
  const Y = (lat: number) => ((90 - lat) / 180) * h;
  g.beginPath();
  landRings().forEach((ring) => {
    ring.forEach(([lon, lat], i) => {
      if (i === 0 || Math.abs(lon - ring[i - 1][0]) > 180) g.moveTo(X(lon), Y(lat));
      else g.lineTo(X(lon), Y(lat));
    });
    g.closePath();
  });
  g.fill("evenodd");
  if (outline) {
    g.strokeStyle = outline;
    g.lineWidth = 2;
    g.stroke();
  }
  return c;
};

const useLandMask = () =>
  useMemo(() => {
    const c = landCanvas(1440, 720, "#fff", "#000");
    const data = c.getContext("2d")!.getImageData(0, 0, 1440, 720).data;
    return (lat: number, lon: number) => {
      const x = Math.min(1439, Math.max(0, Math.floor(((lon + 180) / 360) * 1440)));
      const y = Math.min(719, Math.max(0, Math.floor(((90 - lat) / 180) * 720)));
      return data[(y * 1440 + x) * 4] > 128;
    };
  }, []);

const Atmosphere: React.FC<{ color: string; r?: number; power?: number }> = ({ color, r = 1.16, power = 3.2 }) => {
  const mat = useMemo(
    () =>
      new THREE.ShaderMaterial({
        uniforms: { c: { value: new THREE.Color(color) }, p: { value: power } },
        vertexShader: `varying vec3 vN; varying vec3 vV; void main(){ vec4 mv = modelViewMatrix*vec4(position,1.); vN = normalize(normalMatrix*normal); vV = normalize(-mv.xyz); gl_Position = projectionMatrix*mv; }`,
        fragmentShader: `uniform vec3 c; uniform float p; varying vec3 vN; varying vec3 vV; void main(){ float i = pow(clamp(1.0 - abs(dot(vN, vV)), 0., 1.), p); gl_FragColor = vec4(c*i*1.6, i); }`,
        side: THREE.BackSide,
        blending: THREE.AdditiveBlending,
        transparent: true,
        depthWrite: false,
      }),
    [color, power],
  );
  return (
    <mesh scale={r} material={mat}>
      <sphereGeometry args={[1, 96, 96]} />
    </mesh>
  );
};

const Dots: React.FC<{ color: string; step?: number; size?: number }> = ({ color, step = 1.25, size = 0.0055 }) => {
  const isLand = useLandMask();
  const mesh = useMemo(() => {
    const pts: THREE.Vector3[] = [];
    for (let lat = -84; lat <= 84; lat += step) {
      const ringStep = step / Math.max(0.15, Math.cos(THREE.MathUtils.degToRad(lat)));
      for (let lon = -180; lon < 180; lon += ringStep) if (isLand(lat, lon)) pts.push(ll2v(lat, lon, 1.002));
    }
    const geo = new THREE.CircleGeometry(size, 8);
    const mat = new THREE.MeshBasicMaterial({ color, toneMapped: false });
    const im = new THREE.InstancedMesh(geo, mat, pts.length);
    const m = new THREE.Matrix4();
    const q = new THREE.Quaternion();
    const z = new THREE.Vector3(0, 0, 1);
    pts.forEach((p, i) => {
      q.setFromUnitVectors(z, p.clone().normalize());
      m.compose(p, q, new THREE.Vector3(1, 1, 1));
      im.setMatrixAt(i, m);
    });
    im.instanceMatrix.needsUpdate = true;
    return im;
  }, [isLand, color, step, size]);
  return <primitive object={mesh} />;
};

type Arc = { from: [number, number]; to: [number, number]; at?: unknown; dur?: number; color?: string; height?: number };
type Marker = { lat: number; lon: number; label?: string; at?: unknown; color?: string };
type Focus = { t: number; lat: number; lon: number; dist?: number };

const arcPoints = (a: [number, number], b: [number, number], h: number, n = 96) => {
  const va = ll2v(a[0], a[1]);
  const vb = ll2v(b[0], b[1]);
  const pts: THREE.Vector3[] = [];
  for (let i = 0; i <= n; i++) {
    const t = i / n;
    const v = va.clone().lerp(vb, t).normalize();
    // slerp approximation is fine for display; altitude bump
    const alt = 1 + Math.sin(Math.PI * t) * h;
    pts.push(v.multiplyScalar(alt));
  }
  return pts;
};

const ArcMesh: React.FC<{ arc: Arc; p: number; color: string }> = ({ arc, p, color }) => {
  const { geo, total } = useMemo(() => {
    const d = ll2v(...arc.from).distanceTo(ll2v(...arc.to));
    const curve = new THREE.CatmullRomCurve3(arcPoints(arc.from, arc.to, arc.height ?? Math.min(0.45, 0.12 + d * 0.22)));
    const g = new THREE.TubeGeometry(curve, 160, 0.006, 8, false);
    return { geo: g, total: g.index ? g.index.count : 0, curve };
  }, [arc]);
  geo.setDrawRange(0, Math.floor(total * clamp01(p)));
  const curve = useMemo(() => new THREE.CatmullRomCurve3(arcPoints(arc.from, arc.to, arc.height ?? 0.25)), [arc]);
  const head = curve.getPoint(clamp01(p));
  return (
    <>
      <mesh geometry={geo}>
        <meshBasicMaterial color={color} toneMapped={false} transparent opacity={0.95} />
      </mesh>
      {p > 0 && p < 1 ? (
        <mesh position={head}>
          <sphereGeometry args={[0.016, 16, 16]} />
          <meshBasicMaterial color="#ffffff" toneMapped={false} />
        </mesh>
      ) : null}
    </>
  );
};

const MarkerMesh: React.FC<{ m: Marker; f: number; color: string }> = ({ m, f, color }) => {
  const p = ll2v(m.lat, m.lon, 1.004);
  const q = new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 0, 1), p.clone().normalize());
  const pulse = (f % 50) / 50;
  return (
    <group position={p} quaternion={q}>
      <mesh>
        <circleGeometry args={[0.012, 24]} />
        <meshBasicMaterial color={color} toneMapped={false} />
      </mesh>
      <mesh scale={1 + pulse * 3}>
        <ringGeometry args={[0.016, 0.02, 48]} />
        <meshBasicMaterial color={color} transparent opacity={1 - pulse} toneMapped={false} />
      </mesh>
    </group>
  );
};

// ~130 big metro areas (approximate centres) for the night lights of Earth
const CITIES: [number, number][] = [
  [35.7, 139.7], [28.6, 77.2], [31.2, 121.5], [-23.5, -46.6], [19.4, -99.1], [30.0, 31.2], [19.1, 72.9], [39.9, 116.4], [23.8, 90.4], [34.7, 135.5],
  [40.7, -74.0], [24.9, 67.0], [-34.6, -58.4], [29.6, 106.5], [41.0, 29.0], [22.6, 88.4], [14.6, 121.0], [6.5, 3.4], [-22.9, -43.2], [39.1, 117.2],
  [-4.3, 15.3], [23.1, 113.3], [34.05, -118.25], [55.75, 37.62], [22.5, 114.1], [31.5, 74.3], [12.97, 77.6], [48.86, 2.35], [4.7, -74.1], [-6.2, 106.8],
  [13.1, 80.3], [-12.0, -77.0], [13.75, 100.5], [37.57, 126.98], [35.2, 136.9], [17.4, 78.5], [51.5, -0.13], [35.7, 51.4], [41.9, -87.6], [30.7, 104.1],
  [32.06, 118.8], [30.6, 114.3], [10.8, 106.7], [-8.8, 13.2], [23.0, 72.6], [3.14, 101.7], [34.3, 108.9], [30.3, 120.2], [41.8, 123.4], [24.7, 46.7],
  [33.3, 44.4], [-33.45, -70.67], [21.2, 72.8], [40.4, -3.7], [18.5, 73.9], [45.8, 126.6], [29.76, -95.37], [32.78, -96.8], [43.65, -79.38], [-6.8, 39.3],
  [25.76, -80.19], [-19.9, -43.9], [1.35, 103.8], [39.95, -75.17], [33.75, -84.39], [33.6, 130.4], [15.6, 32.5], [41.39, 2.17], [-26.2, 28.05], [59.94, 30.31],
  [36.07, 120.38], [38.9, 121.6], [38.9, -77.04], [16.8, 96.15], [31.2, 29.9], [36.65, 117.0], [20.67, -103.35], [52.52, 13.4], [41.9, 12.5], [50.45, 30.52],
  [52.23, 21.0], [45.46, 9.19], [-33.87, 151.2], [-37.8, 144.96], [-1.29, 36.82], [33.57, -7.59], [9.03, 38.74], [5.36, -4.0], [37.77, -122.42], [47.6, -122.33],
  [45.5, -73.57], [49.28, -123.12], [55.03, 82.92], [56.84, 60.6], [55.8, 49.1], [43.24, 76.89], [41.3, 69.24], [53.9, 27.56], [52.37, 4.9], [50.85, 4.35],
  [48.2, 16.37], [47.5, 19.04], [37.98, 23.73], [38.72, -9.14], [25.2, 55.27], [34.5, 69.2], [25.03, 121.56], [33.45, -112.07], [39.74, -104.99], [42.33, -83.05],
  [42.36, -71.06], [25.67, -100.31], [10.5, -66.9], [-0.18, -78.47], [5.6, -0.19], [12.0, 8.52], [36.75, 3.06], [36.8, 10.18], [-31.95, 115.86], [-27.47, 153.03],
  [-36.85, 174.76], [56.0, 92.87], [43.12, 131.9], [54.99, 73.37], [53.2, 50.15], [47.23, 39.7], [48.7, 44.5], [56.3, 44.0], [53.48, -2.24], [53.55, 10.0],
  [50.11, 8.68], [48.14, 11.58], [45.76, 4.84], [44.43, 26.1], [59.33, 18.07], [60.17, 24.94], [55.68, 12.57], [59.91, 10.75], [32.08, 34.78], [21.03, 105.85],
];

/** warm city lights; each city dies at its own moment after `out` (frame), flickering for a few frames */
const CityLights: React.FC<{ f: number; fps: number; out: number; color: string }> = ({ f, fps, out, color }) => {
  const base = useMemo(() => {
    const pos: number[] = [];
    const city: number[] = [];
    const b: number[] = [];
    CITIES.forEach(([la, lo], i) => {
      const n = 7 + Math.floor(random(`cn${i}`) * 7);
      for (let k = 0; k < n; k++) {
        const r = k === 0 ? 0 : 0.2 + random(`cr${i}${k}`) * 1.3;
        const a = random(`ca${i}${k}`) * Math.PI * 2;
        const v = ll2v(la + Math.sin(a) * r, lo + (Math.cos(a) * r) / Math.max(0.3, Math.cos((la * Math.PI) / 180)), 1.004);
        pos.push(v.x, v.y, v.z);
        city.push(i);
        b.push(k === 0 ? 1 : 0.5 + random(`cb${i}${k}`) * 0.45);
      }
    });
    const geo = new THREE.BufferGeometry();
    geo.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
    geo.setAttribute("color", new THREE.Float32BufferAttribute(new Array(pos.length).fill(0), 3));
    return { geo, city, b };
  }, []);
  const mtl = useMemo(() => new THREE.PointsMaterial({ size: 13, map: dotTexture(), sizeAttenuation: false, vertexColors: true, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending }), []);
  // soft glow round every light (same points, big and faint) so a city reads as a warm blob, not a pixel
  const halo = useMemo(() => new THREE.PointsMaterial({ size: 40, map: dotTexture(), sizeAttenuation: false, vertexColors: true, transparent: true, opacity: 0.3, depthWrite: false, blending: THREE.AdditiveBlending }), []);
  const c = new THREE.Color(color);
  const attr = base.geo.getAttribute("color") as THREE.BufferAttribute;
  base.city.forEach((ci, k) => {
    const off = out + Math.round((0.05 + random(`co${ci}`) * 1.5) * fps);
    const on = f < off - 6 || (f < off && (f + ci) % 3 !== 0) ? 1 : 0;
    const v = base.b[k] * on;
    attr.setXYZ(k, c.r * v, c.g * v, c.b * v);
  });
  attr.needsUpdate = true;
  return (
    <>
      <points geometry={base.geo} material={halo} />
      <points geometry={base.geo} material={mtl} />
    </>
  );
};

const STYLES = {
  // warm dark Earth for the dusk palette (pairs with cities: true)
  dusk: { ocean: "#221C17", land: "#5E4F42", dot: "", atmo: "#E39A5E" },
  dots: { ocean: "#0A1430", land: "#0A1430", dot: "#8FB4FF", atmo: "#4D86FF" },
  solid: { ocean: "#0E2A5A", land: "#5E8F5A", dot: "", atmo: "#7FB2FF" },
  night: { ocean: "#04060E", land: "#141B33", dot: "", atmo: "#3A64FF" },
  light: { ocean: "#DCE6F7", land: "#FFFFFF", dot: "#2F6BFF", atmo: "#9DB8FF" },
};

export const Globe3D: React.FC<{
  look?: keyof typeof STYLES; focus?: Focus[]; markers?: Marker[]; arcs?: Arc[]; spin?: number; accent?: string; labels?: boolean; dist?: number; tilt?: number;
  /** warm night lights of ~130 big cities; citiesOut (anchor/seconds) switches them off city by city within ~1.5 s */
  cities?: boolean; citiesOut?: unknown;
}> = ({ look = "dots", focus, markers = [], arcs = [], spin = 4, accent, labels = true, dist = 3.6, tilt = 0, cities = false, citiesOut }) => {
  const { f, fps, at } = useBlockTime();
  const th = useTheme();
  const t = f / fps;
  const st = STYLES[look] ?? STYLES.dots;
  const acc = accent ?? th.accent;
  // camera focus path
  const keys: Focus[] = focus && focus.length ? focus : [{ t: 0, lat: 20 + tilt, lon: 20, dist }];
  let cur = keys[0];
  let lat = cur.lat;
  let lon = cur.lon - spin * t;
  let dd = cur.dist ?? dist;
  for (let i = 0; i < keys.length - 1; i++) {
    const a = keys[i];
    const b = keys[i + 1];
    if (t >= a.t) {
      const p = E.inOut(clamp01((t - a.t) / Math.max(0.01, b.t - a.t)));
      let dl = b.lon - a.lon;
      if (dl > 180) dl -= 360;
      if (dl < -180) dl += 360;
      lat = lerp(a.lat, b.lat, p);
      lon = a.lon + dl * p;
      dd = lerp(a.dist ?? dist, b.dist ?? dist, p);
      cur = b;
    }
  }
  if (focus && focus.length && t > keys[keys.length - 1].t) {
    const l = keys[keys.length - 1];
    lat = l.lat;
    lon = l.lon - spin * 0.15 * (t - l.t);
    dd = l.dist ?? dist;
  }
  const camPos = ll2v(lat, lon, dd);
  const cam: Cam = { pos: [camPos.x, camPos.y, camPos.z], target: [0, 0, 0], fov: 30 };
  const tex = useMemo(() => {
    const c = landCanvas(4096, 2048, st.land, st.ocean, look === "night" ? "#3A64FF" : undefined);
    const tx = new THREE.CanvasTexture(c);
    tx.colorSpace = THREE.SRGBColorSpace;
    tx.anisotropy = 8;
    return tx;
  }, [look]);
  const camera = makeCamera(cam);
  return (
    <AbsoluteFill>
      <Stage3D cam={cam} lights="soft" env={look === "light" ? 0.8 : look === "dusk" ? 0.55 : 0.25} shadows={false}>
        <mesh>
          <sphereGeometry args={[1, 128, 128]} />
          <meshStandardMaterial map={tex} roughness={0.85} metalness={0} emissive={look === "night" ? "#0A1640" : "#000"} />
        </mesh>
        {look === "dots" || look === "light" ? <Dots color={st.dot} /> : null}
        {cities ? <CityLights f={f} fps={fps} out={citiesOut !== undefined ? at(citiesOut) : Infinity} color="#FFC48A" /> : null}
        <Atmosphere color={st.atmo} />
        {arcs.map((a, i) => {
          const s = a.at !== undefined ? at(a.at) : Math.round((0.4 + i * 0.5) * fps);
          const p = E.inOut(clamp01((f - s) / ((a.dur ?? 1.2) * fps)));
          return <ArcMesh key={i} arc={a} p={p} color={a.color ?? acc} />;
        })}
        {markers.map((m, i) => {
          const s = m.at !== undefined ? at(m.at) : 0;
          return f >= s ? <MarkerMesh key={i} m={m} f={f - s} color={m.color ?? acc} /> : null;
        })}
      </Stage3D>
      {labels
        ? markers.map((m, i) => {
            const s = m.at !== undefined ? at(m.at) : 0;
            if (!m.label || f < s) return null;
            const p = ll2v(m.lat, m.lon, 1.01);
            const facing = p.clone().normalize().dot(camPos.clone().normalize());
            if (facing < 0.2) return null;
            const [x, y] = project(camera, p);
            const a = E.out(clamp01((f - s - 6) / 14));
            return (
              <div key={i} style={{ position: "absolute", left: x + 26, top: y - 22, opacity: a, transform: `translateX(${(1 - a) * -12}px)`, font: `600 30px ${th.fontMono}`, color: "#fff", padding: "8px 14px", background: "rgba(8,12,28,0.65)", border: "1px solid rgba(255,255,255,0.18)", borderRadius: 10, whiteSpace: "nowrap", letterSpacing: "0.02em" }}>
                {m.label}
              </div>
            );
          })
        : null}
    </AbsoluteFill>
  );
};
