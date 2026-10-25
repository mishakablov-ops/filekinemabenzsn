import { ThreeCanvas } from "@remotion/three";
import React, { useMemo } from "react";
import { AbsoluteFill } from "remotion";
import * as THREE from "three";
import { useBlockTime, useTheme } from "../core/context";
import { H, W } from "../core/layout";

const NOISE = /* glsl */ `
float hash(vec2 p){ p = fract(p*vec2(123.34, 456.21)); p += dot(p, p+45.32); return fract(p.x*p.y); }
float noise(vec2 p){ vec2 i=floor(p), f=fract(p); f=f*f*(3.-2.*f);
  float a=hash(i), b=hash(i+vec2(1.,0.)), c=hash(i+vec2(0.,1.)), d=hash(i+vec2(1.,1.));
  return mix(mix(a,b,f.x), mix(c,d,f.x), f.y); }
float fbm(vec2 p){ float v=0., a=.5; mat2 m=mat2(1.6,1.2,-1.2,1.6); for(int i=0;i<7;i++){ v+=a*noise(p); p=m*p; a*=.5;} return v; }
float fbm4(vec2 p){ float v=0., a=.5; mat2 m=mat2(1.6,1.2,-1.2,1.6); for(int i=0;i<4;i++){ v+=a*noise(p); p=m*p; a*=.5;} return v; }
vec3 hex(float r, float g, float b){ return vec3(r,g,b); }
`;

const VERT = /* glsl */ `
varying vec2 vUv;
void main(){ vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }
`;

/** Each preset: fragment shader body computing `col` from uv (0..1, y up), t (seconds), aspect, uniforms c1..c4 */
const PRESETS: Record<string, string> = {
  // flying above a sea of clouds
  skyAbove: /* glsl */ `
    float hz = 0.46 + uHorizon;
    vec3 zen = c1, hor = c2;
    vec3 sky = mix(hor, zen, pow(clamp((uv.y-hz)/(1.-hz),0.,1.), .7));
    col = sky;
    // sun glow
    vec2 sp = vec2(.68, hz+.17);
    float sd = length((uv-sp)*vec2(aspect,1.));
    col += vec3(1.,.93,.8) * (exp(-sd*7.)*.55 + exp(-sd*30.)*.6) * uSun;
    // high thin clouds above horizon
    if (uv.y > hz) {
      vec2 q = vec2((uv.x-.5)*aspect/(uv.y-hz+.08), 1./(uv.y-hz+.08));
      float c = fbm4(q*.6 + vec2(t*.02, -t*.05));
      col = mix(col, vec3(1.), smoothstep(.55,.85,c)*.35*smoothstep(hz, hz+.25, uv.y)*(1.-smoothstep(.8,1.,uv.y)));
    }
    // cloud floor
    if (uv.y < hz + .02) {
      float dy = max(hz - uv.y, .002);
      vec2 p = vec2((uv.x-.5)*aspect/dy, 1./dy) * .42;
      p.y += t * uSpeed * .9;
      vec2 w = vec2(fbm4(p*.9 + t*.02), fbm4(p*.9 + 7.3));
      float d = fbm(p*1.25 + w*.9);
      float d2 = fbm(p*1.25 + w*.9 + vec2(.05,.11));
      float cov = smoothstep(.40, .56, d);
      float shade = clamp(.48 + (d - d2)*8., 0., 1.);
      float tops = smoothstep(.55, .8, d);
      vec3 cl = mix(c3, vec3(1.), shade);
      cl = mix(cl, vec3(1.), tops*.5);
      float far = clamp(1.-dy*5.5, 0., 1.);
      cl = mix(cl, hor, far*.8);  // aerial perspective near horizon
      vec3 below = mix(c4, hor, far);
      col = mix(below, cl, cov);
      col = mix(col, hor, smoothstep(hz-.03, hz+.02, uv.y));
    }
  `,
  // looking up at cumulus clouds
  skyBelow: /* glsl */ `
    vec3 zen = c1, hor = c2;
    col = mix(hor, zen, pow(uv.y, .8));
    vec2 p = vec2(uv.x*aspect, uv.y) * 2.6;
    p += vec2(t*.03*uSpeed, t*.012);
    vec2 w = vec2(fbm4(p*.6 + t*.03), fbm4(p*.6 + 5.2 - t*.02));
    float d = fbm(p + w*.8);
    float d2 = fbm(p + w*.8 + vec2(-.04,.08));
    float cov = smoothstep(.33 + uCover, .52 + uCover, d) * smoothstep(.0, .35, 1. - uv.y + .25);
    float shade = clamp(.58 + (d - d2)*7., 0., 1.);
    vec3 cl = mix(c3, vec3(1.), shade);
    cl = mix(cl, vec3(1.), smoothstep(.62, .85, d)*.45);
    col = mix(col, cl, cov);
  `,
  // white volumetric-looking wall of cloud (backgrounds under text, like an overcast sky)
  cloudWall: /* glsl */ `
    vec2 p = vec2(uv.x*aspect, uv.y)*2.4 + vec2(t*.04*uSpeed, -t*.02);
    vec2 w = vec2(fbm4(p*.6 + t*.02), fbm4(p*.6 + 3.1));
    float d = fbm(p + w*.9);
    float d2 = fbm(p + w*.9 + vec2(.05,.07));
    float shade = clamp(.55 + (d-d2)*7., 0., 1.);
    vec3 base = mix(c2, c1, uv.y);
    vec3 cl = mix(c3, vec3(1.), shade);
    cl = mix(cl, vec3(1.), smoothstep(.6, .85, d)*.5);
    col = mix(base, cl, smoothstep(.27, .5, d));
  `,
  // flowing premium gradient (domain-warped), colours from theme
  liquid: /* glsl */ `
    vec2 p = vec2(uv.x*aspect, uv.y)*1.2;
    float tt = t*.12*uSpeed;
    vec2 q = vec2(fbm4(p + vec2(0., tt)), fbm4(p + vec2(5.2, 1.3) - tt));
    vec2 r = vec2(fbm4(p + 3.5*q + vec2(1.7, 9.2) + tt*.7), fbm4(p + 3.5*q + vec2(8.3, 2.8) - tt*.5));
    float f = fbm4(p + 3.0*r);
    col = mix(c1, c2, clamp(f*f*2.2, 0., 1.));
    col = mix(col, c3, clamp(length(q)*.9, 0., 1.));
    col = mix(col, c4, clamp(r.x*r.x*1.4, 0., 1.)*.8);
  `,
  // northern lights curtains on dark sky
  aurora: /* glsl */ `
    col = mix(c4, c1*.25, uv.y);
    for (int i=0;i<3;i++){
      float fi = float(i);
      float x = uv.x*aspect*1.4 + fi*1.7;
      float band = .55 + .12*sin(x*1.3 + t*.25*uSpeed + fi) + .08*fbm4(vec2(x*.8, t*.1 + fi));
      float d = uv.y - band;
      float curtain = exp(-max(d,0.)*9.) * smoothstep(-.35, 0., d) * (.5 + .5*fbm4(vec2(x*6., t*.3+fi)));
      col += mix(c2, c3, fi/2.) * curtain * .55;
    }
    float s = step(.9985, hash(floor(uv*vec2(aspect,1.)*900.)));
    col += s*.7*smoothstep(.3,1.,uv.y);
  `,
  // animated topographic contour lines (map / data mood)
  contour: /* glsl */ `
    vec2 p = vec2(uv.x*aspect, uv.y)*2.2;
    float h = fbm(p + vec2(t*.02*uSpeed, t*.01));
    float k = 22.;
    float l = abs(fract(h*k) - .5);
    float w = fwidth(h*k);
    float line = 1. - smoothstep(0., w*1.4, l - .02);
    float major = 1. - smoothstep(0., w*1.6, abs(fract(h*k/5.) - .5)*5. - .04);
    col = mix(c4, c1*.6 + c4*.4, h*.6);
    col = mix(col, c2, line*.35);
    col = mix(col, c3, major*.7);
  `,
  // god rays from the top
  rays: /* glsl */ `
    vec2 o = vec2(.5, 1.15);
    vec2 d = uv - o; d.x *= aspect;
    float a = atan(d.x, -d.y);
    float r = length(d);
    float rays = .5 + .5*sin(a*18. + fbm4(vec2(a*4., t*.2))*6.);
    rays = pow(rays, 3.) * exp(-r*1.2);
    col = mix(c4, c1*.4, uv.y*.6) + c2*rays*.5*uSun;
  `,
  // smoke / ink wisps on dark
  smoke: /* glsl */ `
    vec2 p = vec2(uv.x*aspect, uv.y)*1.5;
    vec2 q = vec2(fbm4(p + t*.05*uSpeed), fbm4(p + 4.1 - t*.04));
    float f = fbm(p + 2.6*q + vec2(0., -t*.06));
    col = c4 + c2*pow(f, 2.2)*1.3 + c3*pow(q.x, 3.)*.8;
  `,
};

const FRAG = (body: string) => /* glsl */ `
precision highp float;
varying vec2 vUv;
uniform float uTime, uAspect, uSpeed, uSun, uCover, uHorizon, uGrade;
uniform vec3 c1, c2, c3, c4;
${NOISE}
void main(){
  vec2 uv = vUv; float t = uTime; float aspect = uAspect;
  vec3 col = vec3(0.);
  ${body}
  // gentle filmic grade + dither
  col = pow(col, vec3(1.0/(1.0+uGrade*0.08)));
  col += (hash(gl_FragCoord.xy + t) - .5) / 255.;
  gl_FragColor = vec4(col, 1.);
}
`;

const DEFAULT_COLORS: Record<string, string[]> = {
  skyAbove: ["#1E52C4", "#CFE0F7", "#8EA3C9", "#5E77A8"],
  skyBelow: ["#2457CC", "#9EC0EE", "#A3B3CF", "#ffffff"],
  cloudWall: ["#DCE5F4", "#B9C8E2", "#9AAACA", "#ffffff"],
  liquid: ["#EDEBFF", "#BFD0FF", "#F6E3FF", "#FFFFFF"],
  aurora: ["#1B2A6B", "#3DFFB0", "#8A5BFF", "#04060F"],
  contour: ["#2F6BFF", "#9FB6FF", "#FF8A3D", "#0B0F1E"],
  rays: ["#5A7BFF", "#CFE0FF", "#ffffff", "#060814"],
  smoke: ["#000000", "#6E7BFF", "#FF4FD8", "#05060A"],
};

const Quad: React.FC<{ frag: string; uniforms: Record<string, { value: unknown }> }> = ({ frag, uniforms }) => {
  const mat = useMemo(() => new THREE.ShaderMaterial({ vertexShader: VERT, fragmentShader: frag, uniforms, depthTest: false, depthWrite: false }), [frag]);
  Object.entries(uniforms).forEach(([k, v]) => {
    if (mat.uniforms[k]) mat.uniforms[k].value = v.value;
  });
  return (
    <mesh frustumCulled={false} material={mat}>
      <planeGeometry args={[2, 2]} />
    </mesh>
  );
};

export const ShaderBG: React.FC<{
  preset?: keyof typeof PRESETS | string; colors?: string[]; speed?: number; sun?: number; cover?: number; horizon?: number; grade?: number; timeOffset?: number;
}> = ({ preset = "skyAbove", colors, speed = 1, sun = 1, cover = 0, horizon = 0, grade = 1, timeOffset = 0 }) => {
  const { f, fps } = useBlockTime();
  const th = useTheme();
  const body = PRESETS[preset] ?? PRESETS.skyAbove;
  const frag = useMemo(() => FRAG(body), [body]);
  // mood presets follow the theme palette (warm by default); sky presets keep their natural colours
  const themed: Record<string, string[]> = {
    liquid: [th.bg, th.accent, th.accent2, th.card],
    smoke: ["#000000", th.accent, th.accent2, th.bg],
    aurora: [th.accent, th.accent, th.accent2, th.bg],
    rays: [th.accent2, th.accent, th.accent2, th.bg],
    contour: [th.accent2, th.faint.startsWith("rgba") ? th.accent2 : th.faint, th.accent, th.bg],
  };
  const cs = colors ?? themed[preset] ?? DEFAULT_COLORS[preset] ?? DEFAULT_COLORS.skyAbove;
  const v3 = (c: string) => {
    // raw sRGB values: the canvas is `linear` + `flat`, so no colour management round-trip
    const h = c.replace("#", "").slice(0, 6);
    return new THREE.Vector3(parseInt(h.slice(0, 2), 16) / 255, parseInt(h.slice(2, 4), 16) / 255, parseInt(h.slice(4, 6), 16) / 255);
  };
  const uniforms = {
    uTime: { value: f / fps + timeOffset },
    uAspect: { value: W / H },
    uSpeed: { value: speed },
    uSun: { value: sun },
    uCover: { value: cover },
    uHorizon: { value: horizon },
    uGrade: { value: grade },
    c1: { value: v3(cs[0]) },
    c2: { value: v3(cs[1]) },
    c3: { value: v3(cs[2]) },
    c4: { value: v3(cs[3] ?? cs[2]) },
  };
  return (
    <AbsoluteFill>
      <ThreeCanvas width={W} height={H} style={{ position: "absolute", inset: 0 }} gl={{ antialias: false, preserveDrawingBuffer: true }} linear flat>
        <Quad frag={frag} uniforms={uniforms} />
      </ThreeCanvas>
    </AbsoluteFill>
  );
};

export const SHADER_PRESETS = Object.keys(PRESETS);
