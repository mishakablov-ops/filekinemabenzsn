import React from "react";
import { Img } from "remotion";
import { useBlockTime, useTheme } from "../core/context";
import { E, clamp01, fmtNumber, lerp } from "../core/motion";
import { asset } from "./bg";
import { defineBlock, type BlockDef } from "./registry";

const MONO = "'JetBrains Mono', Consolas, monospace";
const T = { bg: "#15120F", bar: "#1E1A16", ink: "#E8DED0", dim: "#8C8073", acc: "#E08A55", ok: "#8FBF7A", bad: "#D9705A", blue: "#8FB0E0", line: "rgba(232,222,208,0.09)" };

// ------------------------------------------------------------------ Terminal (agent CLI look)
type TLine =
  | { kind: "prompt"; text: string; at?: unknown; cps?: number }
  | { kind: "tool"; name: string; arg?: string; sub?: string[]; at?: unknown; state?: "run" | "ok" | "err" }
  | { kind: "text"; text: string; at?: unknown; color?: string }
  | { kind: "ask"; title?: string; cmd: string; question?: string; options?: string[]; chooseAt?: unknown; at?: unknown }
  | { kind: "status"; text?: string; at?: unknown; until?: unknown }
  | { kind: "ok"; text: string; at?: unknown }
  | { kind: "diff"; add?: string[]; del?: string[]; at?: unknown };

const Spinner: React.FC<{ f: number }> = ({ f }) => <span style={{ color: T.acc }}>{"✻✼✽✾✿❀"[Math.floor(f / 5) % 6]}</span>;

const Terminal: React.FC<{ lines: TLine[]; title?: string; w?: number; h?: number; welcome?: boolean; cwd?: string; size?: number; gap?: number }> = ({
  lines, title = "my-app — claude", w = 940, h = 1000, welcome = true, cwd = "~/projects/my-app", size = 25, gap = 0.55,
}) => {
  const { f, fps, at } = useBlockTime();
  const times = lines.map((l, i) => (l.at !== undefined ? at(l.at) : Math.round((0.3 + i * gap) * fps)));
  const visible = lines.map((l, i) => ({ l, s: times[i] })).filter((x) => f >= x.s);
  const lh = size * 1.55;
  const rows: React.ReactNode[] = [];
  let rowCount = welcome ? 4 : 0;
  visible.forEach(({ l, s }, i) => {
    const fl = f - s;
    const a = clamp01(fl / 5);
    const key = `l${i}`;
    if (l.kind === "prompt") {
      const cps = l.cps ?? 18;
      const n = Math.floor((fl / fps) * cps);
      const typing = n < l.text.length;
      rows.push(
        <div key={key} style={{ marginTop: lh * 0.5, padding: `${size * 0.4}px ${size * 0.6}px`, border: `1px solid ${T.line}`, borderRadius: 10, color: T.ink }}>
          <span style={{ color: T.dim }}>{">"} </span>
          {l.text.slice(0, n)}
          {typing || Math.floor(f / 16) % 2 ? <span style={{ background: T.ink, color: T.bg }}> </span> : null}
        </div>,
      );
      rowCount += 2;
    } else if (l.kind === "tool") {
      const col = l.state === "err" ? T.bad : l.state === "run" ? T.acc : T.ok;
      rows.push(
        <div key={key} style={{ opacity: a, marginTop: lh * 0.35 }}>
          <span style={{ color: col }}>● </span>
          <span style={{ fontWeight: 700 }}>{l.name}</span>
          {l.arg ? <span style={{ color: T.dim }}>({l.arg})</span> : null}
          {(l.sub ?? []).map((sb, k) => (
            <div key={k} style={{ color: T.dim, paddingLeft: size * 0.9, opacity: clamp01((fl - 6 - k * 4) / 6) }}>
              {k === 0 ? "⎿ " : "  "}
              {sb}
            </div>
          ))}
        </div>,
      );
      rowCount += 1 + (l.sub?.length ?? 0);
    } else if (l.kind === "text") {
      rows.push(<div key={key} style={{ opacity: a, marginTop: lh * 0.35, color: l.color ?? T.ink, whiteSpace: "pre-wrap" }}>{l.text}</div>);
      rowCount += Math.ceil(l.text.length / 48);
    } else if (l.kind === "ok") {
      rows.push(<div key={key} style={{ opacity: a, marginTop: lh * 0.35, color: T.ok }}>✓ {l.text}</div>);
      rowCount += 1;
    } else if (l.kind === "status") {
      const until = l.until !== undefined ? at(l.until) : Infinity;
      if (f < until) {
        rows.push(
          <div key={key} style={{ opacity: a, marginTop: lh * 0.35, color: T.acc }}>
            <Spinner f={f} /> {l.text ?? "Думаю…"} <span style={{ color: T.dim }}>({Math.floor(fl / fps)}s · esc to interrupt)</span>
          </div>,
        );
        rowCount += 1;
      }
    } else if (l.kind === "diff") {
      rows.push(
        <div key={key} style={{ opacity: a, marginTop: lh * 0.25, paddingLeft: size * 0.9 }}>
          {(l.del ?? []).map((d, k) => (
            <div key={`d${k}`} style={{ color: T.bad, background: "rgba(217,112,90,0.12)" }}>- {d}</div>
          ))}
          {(l.add ?? []).map((d, k) => (
            <div key={`a${k}`} style={{ color: T.ok, background: "rgba(143,191,122,0.12)" }}>+ {d}</div>
          ))}
        </div>,
      );
      rowCount += (l.del?.length ?? 0) + (l.add?.length ?? 0);
    } else if (l.kind === "ask") {
      const ch = l.chooseAt !== undefined ? at(l.chooseAt) : Infinity;
      const opts = l.options ?? ["Yes", "No"];
      rows.push(
        <div key={key} style={{ opacity: a, marginTop: lh * 0.5, border: `1px solid ${T.acc}88`, borderRadius: 10, padding: `${size * 0.5}px ${size * 0.7}px` }}>
          <div style={{ fontWeight: 700 }}>{l.title ?? "Bash command"}</div>
          <div style={{ color: T.dim, paddingLeft: size * 0.8 }}>{l.cmd}</div>
          <div style={{ marginTop: size * 0.4 }}>{l.question ?? "Do you want to proceed?"}</div>
          {opts.map((o, k) => (
            <div key={k} style={{ color: k === 0 ? (f >= ch ? T.ok : T.acc) : T.ink }}>
              {k === 0 ? "❯" : " "} {k + 1}. {o}
              {k === 0 && f >= ch ? "  ✓" : ""}
            </div>
          ))}
        </div>,
      );
      rowCount += 4 + opts.length;
    }
  });
  const bodyH = h - 56 - size * 2;
  const contentH = rowCount * lh + lh * 2;
  const scroll = Math.max(0, contentH - bodyH);
  return (
    <div style={{ width: w, height: h, borderRadius: 20, background: T.bg, border: `1px solid ${T.line}`, boxShadow: "0 50px 100px -30px rgba(0,0,0,0.7)", overflow: "hidden", fontFamily: MONO, fontSize: size, color: T.ink, lineHeight: 1.5 }}>
      <div style={{ height: 56, background: T.bar, display: "flex", alignItems: "center", gap: 10, padding: "0 20px", borderBottom: `1px solid ${T.line}` }}>
        {["#E0695B", "#E3B04B", "#7DB86A"].map((c) => (
          <span key={c} style={{ width: 15, height: 15, borderRadius: 8, background: c }} />
        ))}
        <span style={{ flex: 1, textAlign: "center", font: `600 20px Inter`, color: T.dim, marginRight: 50 }}>{title}</span>
      </div>
      <div style={{ padding: size, transform: `translateY(${-scroll}px)` }}>
        {welcome ? (
          <div style={{ border: `1px solid ${T.acc}`, borderRadius: 10, padding: `${size * 0.5}px ${size * 0.7}px` }}>
            <div>
              <span style={{ color: T.acc }}>✻</span> Welcome to <b>Claude Code</b>!
            </div>
            <div style={{ color: T.dim }}>cwd: {cwd}</div>
          </div>
        ) : null}
        {rows}
      </div>
    </div>
  );
};

// ------------------------------------------------------------------ ClaudeChat (desktop chat app)
const ClaudeChat: React.FC<{
  greeting?: string; placeholder?: string; type?: string; typeAt?: unknown; cps?: number; attach?: { src?: string; name?: string; at?: unknown }; chips?: string[]; model?: string;
  reply?: string; replyAt?: unknown; sendAt?: unknown; w?: number; h?: number; dark?: boolean;
}> = ({ greeting = "Добрый вечер", placeholder = "Чем помочь?", type, typeAt, cps = 16, attach, chips = [], model = "Opus 5.5", reply, replyAt, sendAt, w = 940, h = 760, dark }) => {
  const { f, fps, at } = useBlockTime();
  const th = useTheme();
  dark = dark ?? th.dark;
  const C = dark ? { bg: "#1F1C19", card: "#2A2622", ink: "#EDE3D4", dim: "#9B8D7C", line: "rgba(237,227,212,0.1)" } : { bg: "#EFE9DE", card: "#F7F2EA", ink: "#2A231C", dim: "#8D8174", line: "rgba(42,35,28,0.1)" };
  const ts = typeAt !== undefined ? at(typeAt) : Math.round(0.6 * fps);
  const n = type ? Math.max(0, Math.floor(((f - ts) / fps) * cps)) : 0;
  const typed = type ? type.slice(0, n) : "";
  const as = attach ? (attach.at !== undefined ? at(attach.at) : Math.round(0.3 * fps)) : Infinity;
  const ap = clamp01((f - as) / 12);
  const sent = sendAt !== undefined && f >= at(sendAt);
  const rs = replyAt !== undefined ? at(replyAt) : Infinity;
  const rn = reply ? Math.max(0, Math.floor(((f - rs) / fps) * 40)) : 0;
  return (
    <div style={{ width: w, height: h, borderRadius: 24, background: C.bg, border: `1px solid ${C.line}`, boxShadow: "0 50px 100px -30px rgba(0,0,0,0.55)", overflow: "hidden", fontFamily: "Inter", color: C.ink, display: "flex", flexDirection: "column" }}>
      <div style={{ height: 50, display: "flex", alignItems: "center", gap: 9, padding: "0 18px" }}>
        {["#E0695B", "#E3B04B", "#7DB86A"].map((c) => (
          <span key={c} style={{ width: 14, height: 14, borderRadius: 7, background: c }} />
        ))}
        <span style={{ flex: 1, textAlign: "center", font: `600 18px Inter`, color: C.dim, marginRight: 40 }}>Claude</span>
      </div>
      <div style={{ flex: 1, display: "flex", flexDirection: "column", justifyContent: sent ? "flex-start" : "center", padding: "0 44px" }}>
        {!sent ? (
          <div style={{ textAlign: "center", font: `500 52px ${th.fontSerif}`, marginBottom: 34 }}>
            <span style={{ color: "#D9732F" }}>✻</span> {greeting}
          </div>
        ) : (
          <div style={{ marginTop: 20, alignSelf: "flex-end", maxWidth: "80%", background: C.card, padding: "16px 22px", borderRadius: 20, font: `500 28px Inter` }}>{type}</div>
        )}
        {sent && reply && f >= rs ? (
          <div style={{ marginTop: 26, font: `500 30px ${th.fontSerif}`, lineHeight: 1.4 }}>
            <span style={{ color: "#D9732F" }}>✻ </span>
            {reply.slice(0, rn)}
          </div>
        ) : null}
        {!sent ? (
          <div style={{ background: C.card, borderRadius: 24, border: `1px solid ${C.line}`, padding: "22px 24px", boxShadow: "0 10px 30px -12px rgba(0,0,0,0.18)" }}>
            {attach && ap > 0 ? (
              <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 14, opacity: ap, transform: `translateY(${(1 - ap) * -30}px) scale(${lerp(1.3, 1, ap)})` }}>
                {attach.src ? <Img src={asset(attach.src)} style={{ width: 64, height: 64, borderRadius: 10, objectFit: "cover" }} /> : <div style={{ width: 64, height: 64, borderRadius: 10, background: "#CDBEA6" }} />}
                <span style={{ font: `500 20px Inter`, color: C.dim }}>{attach.name ?? "IMG_2041.jpg"}</span>
              </div>
            ) : null}
            <div style={{ font: `500 30px Inter`, color: typed ? C.ink : C.dim, minHeight: 44 }}>
              {typed || placeholder}
              {type && n < type.length && f >= ts ? <span style={{ display: "inline-block", width: 3, height: 32, background: C.ink, marginLeft: 3, verticalAlign: "middle" }} /> : null}
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: 12, marginTop: 18 }}>
              <span style={{ width: 40, height: 40, borderRadius: 20, border: `1px solid ${C.line}`, display: "flex", alignItems: "center", justifyContent: "center", font: `400 26px Inter`, color: C.dim }}>+</span>
              {chips.map((c, i) => (
                <span key={i} style={{ font: `600 20px Inter`, color: C.ink, padding: "8px 14px", borderRadius: 999, border: `1px solid ${C.line}` }}>◎ {c}</span>
              ))}
              <span style={{ flex: 1 }} />
              <span style={{ font: `500 20px Inter`, color: C.dim }}>{model} ⌄</span>
              <span style={{ width: 44, height: 44, borderRadius: 12, background: typed ? "#D9732F" : "#E7C9AE", display: "flex", alignItems: "center", justifyContent: "center", color: "#FFF6EC", font: `700 24px Inter` }}>↑</span>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
};

// ------------------------------------------------------------------ CodeEditor with naive highlighting, typing and diff marks
const KW = /\b(const|let|var|function|return|if|else|for|while|import|from|export|default|async|await|new|class|extends|true|false|null|undefined|def|self|in|of|type|interface)\b/g;
const highlight = (line: string) => {
  const out: React.ReactNode[] = [];
  const re = /(\/\/.*$|#.*$|"[^"]*"|'[^']*'|`[^`]*`|\b\d+(\.\d+)?\b|\b(?:const|let|var|function|return|if|else|for|while|import|from|export|default|async|await|new|class|extends|true|false|null|undefined|def|self|in|of|type|interface)\b)/g;
  let last = 0;
  let m: RegExpExecArray | null;
  let k = 0;
  while ((m = re.exec(line))) {
    if (m.index > last) out.push(<span key={k++}>{line.slice(last, m.index)}</span>);
    const tok = m[0];
    const color = /^(\/\/|#)/.test(tok) ? "#7D7266" : /^["'`]/.test(tok) ? "#A9C08F" : /^\d/.test(tok) ? "#E3B07A" : "#E08A55";
    out.push(<span key={k++} style={{ color, fontStyle: /^(\/\/|#)/.test(tok) ? "italic" : undefined }}>{tok}</span>);
    last = m.index + tok.length;
  }
  if (last < line.length) out.push(<span key={k++}>{line.slice(last)}</span>);
  KW.lastIndex = 0;
  return out;
};

const CodeEditor: React.FC<{ file?: string; code: string; typeFrom?: number; cps?: number; startAt?: unknown; marks?: { line: number; kind: "add" | "del" | "hl"; at?: unknown }[]; w?: number; size?: number; tabs?: string[] }> = ({
  file = "app.ts", code, typeFrom, cps = 40, startAt, marks = [], w = 940, size = 24, tabs,
}) => {
  const { f, fps, at } = useBlockTime();
  const lines = code.replace(/\t/g, "  ").split("\n");
  const s0 = startAt !== undefined ? at(startAt) : 6;
  const tf = typeFrom ?? lines.length;
  const prefix = lines.slice(0, tf).join("\n").length;
  const charsTyped = Math.max(0, Math.floor(((f - s0) / fps) * cps));
  let budget = charsTyped;
  return (
    <div style={{ width: w, borderRadius: 18, background: T.bg, border: `1px solid ${T.line}`, boxShadow: "0 50px 100px -30px rgba(0,0,0,0.7)", overflow: "hidden", fontFamily: MONO, fontSize: size, color: T.ink }}>
      <div style={{ height: 52, background: T.bar, display: "flex", alignItems: "flex-end", gap: 2, padding: "0 14px" }}>
        {(tabs ?? [file]).map((t, i) => (
          <span key={i} style={{ padding: "10px 18px", font: `500 19px Inter`, color: i === 0 ? T.ink : T.dim, background: i === 0 ? T.bg : "transparent", borderRadius: "10px 10px 0 0" }}>{t}</span>
        ))}
      </div>
      <div style={{ padding: "16px 0" }}>
        {lines.map((ln, i) => {
          let shown = ln;
          if (i >= tf) {
            if (budget <= 0) return null;
            shown = ln.slice(0, budget);
            budget -= ln.length + 1;
          }
          const mk = marks.find((m) => m.line === i + 1 && (m.at === undefined || f >= at(m.at)));
          const bg = mk?.kind === "add" ? "rgba(143,191,122,0.14)" : mk?.kind === "del" ? "rgba(217,112,90,0.14)" : mk?.kind === "hl" ? "rgba(224,138,85,0.14)" : undefined;
          return (
            <div key={i} style={{ display: "flex", background: bg, lineHeight: 1.55 }}>
              <span style={{ width: 64, textAlign: "right", paddingRight: 18, color: "#5E554B", flexShrink: 0 }}>{i + 1}</span>
              <span style={{ width: 22, color: mk?.kind === "add" ? T.ok : mk?.kind === "del" ? T.bad : "transparent" }}>{mk?.kind === "add" ? "+" : mk?.kind === "del" ? "-" : " "}</span>
              <span style={{ whiteSpace: "pre", textDecoration: mk?.kind === "del" ? "line-through" : undefined, opacity: mk?.kind === "del" ? 0.6 : 1 }}>{highlight(shown)}</span>
            </div>
          );
        })}
      </div>
      {prefix < 0 ? null : null}
    </div>
  );
};

// ------------------------------------------------------------------ GithubRepo page
const GithubRepo: React.FC<{
  owner: string; repo: string; desc?: string; stars?: [number, number]; starsAt?: unknown; forks?: number; license?: string; topics?: string[];
  files?: { name: string; msg?: string; time?: string; dir?: boolean }[]; ring?: "stars" | "license" | "forks"; ringAt?: unknown; w?: number;
}> = ({ owner, repo, desc, stars = [0, 1200], starsAt, forks = 86, license = "MIT", topics = [], files = [], ring, ringAt, w = 940 }) => {
  const { f, fps, at } = useBlockTime();
  const sa = starsAt !== undefined ? at(starsAt) : Math.round(0.6 * fps);
  const sv = lerp(stars[0], stars[1], E.outExpo(clamp01((f - sa) / (1.3 * fps))));
  const ra = ringAt !== undefined ? at(ringAt) : Math.round(1.6 * fps);
  const rp = E.out(clamp01((f - ra) / 12));
  const ringStyle = (k: string): React.CSSProperties => (ring === k && rp > 0 ? { outline: `4px solid ${T.acc}`, outlineOffset: 6, borderRadius: 10, boxShadow: `0 0 ${30 * rp}px ${T.acc}88` } : {});
  return (
    <div style={{ width: w, borderRadius: 20, background: "#16130F", border: `1px solid ${T.line}`, boxShadow: "0 50px 100px -30px rgba(0,0,0,0.7)", fontFamily: "Inter", color: T.ink, padding: 32, boxSizing: "border-box" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 14, font: `600 32px Inter` }}>
        <span style={{ width: 44, height: 44, borderRadius: 22, background: "#5E5245" }} />
        <span style={{ color: T.blue }}>{owner}</span>
        <span style={{ color: T.dim }}>/</span>
        <span style={{ fontWeight: 800 }}>{repo}</span>
        <span style={{ font: `600 20px Inter`, color: T.dim, border: `1px solid ${T.line}`, borderRadius: 999, padding: "2px 12px" }}>Public</span>
      </div>
      {desc ? <div style={{ font: `500 28px Inter`, color: T.ink, marginTop: 18, lineHeight: 1.35 }}>{desc}</div> : null}
      {topics.length ? (
        <div style={{ display: "flex", flexWrap: "wrap", gap: 10, marginTop: 16 }}>
          {topics.map((t) => (
            <span key={t} style={{ font: `600 21px Inter`, color: T.blue, background: "rgba(143,176,224,0.12)", padding: "5px 14px", borderRadius: 999 }}>{t}</span>
          ))}
        </div>
      ) : null}
      <div style={{ display: "flex", gap: 34, marginTop: 24, font: `600 28px Inter`, color: T.dim, alignItems: "center" }}>
        <span style={ringStyle("stars")}>
          <span style={{ color: "#E9A23B" }}>★</span> <b style={{ color: T.ink, fontVariantNumeric: "tabular-nums" }}>{fmtNumber(sv, sv >= 1000 ? "k" : "int")}</b> stars
        </span>
        <span style={ringStyle("forks")}>⑂ {fmtNumber(forks)} forks</span>
        <span style={ringStyle("license")}>⚖ {license}</span>
      </div>
      {files.length ? (
        <div style={{ marginTop: 26, border: `1px solid ${T.line}`, borderRadius: 14, overflow: "hidden" }}>
          {files.map((fl, i) => {
            const a = clamp01((f - 4 - i * 2.5) / 10);
            return (
              <div key={i} style={{ display: "flex", alignItems: "center", gap: 14, padding: "14px 20px", borderTop: i ? `1px solid ${T.line}` : undefined, font: `500 24px Inter`, opacity: a }}>
                <span style={{ color: fl.dir === false ? T.dim : "#8FA6C9" }}>{fl.dir === false ? "▤" : "▰"}</span>
                <span style={{ fontWeight: 600, minWidth: 260 }}>{fl.name}</span>
                <span style={{ flex: 1, color: T.dim, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{fl.msg ?? ""}</span>
                <span style={{ color: T.dim }}>{fl.time ?? "last week"}</span>
              </div>
            );
          })}
        </div>
      ) : null}
    </div>
  );
};

// ------------------------------------------------------------------ FileTree
const FileTree: React.FC<{ items: { name: string; depth?: number; dir?: boolean; hl?: boolean }[]; stagger?: number }> = ({ items, stagger = 0.08 }) => {
  const { f, fps } = useBlockTime();
  const th = useTheme();
  return (
    <div style={{ width: 760, padding: 26, borderRadius: 22, background: T.bg, border: `1px solid ${T.line}`, fontFamily: MONO, fontSize: 28, color: T.ink, boxShadow: th.cardShadow }}>
      {items.map((it, i) => {
        const a = clamp01((f - i * stagger * fps) / 8);
        return (
          <div key={i} style={{ paddingLeft: (it.depth ?? 0) * 34, opacity: a, lineHeight: 1.65, color: it.hl ? T.acc : it.dir ? "#C9B79A" : T.ink, background: it.hl ? "rgba(224,138,85,0.12)" : undefined, borderRadius: 8 }}>
            {it.dir ? "▾ " : "  "}
            {it.name}
          </div>
        );
      })}
    </div>
  );
};

export const DEV_BLOCKS: Record<string, BlockDef> = {
  Terminal: defineBlock({
    C: Terminal, cat: "ui", pos: "stage", enter: "rise", sfx: "whoosh-airy",
    desc: "Agent CLI terminal: lines[] kinds prompt(typed)|tool(● Name(arg) ⎿ sub)|text|ask(permission box, chooseAt)|status(spinner until)|ok|diff. Auto-scrolls. Each line has `at`.",
    events: (p, t) => ((p.lines ?? []) as { kind: string; at?: unknown; text?: string; chooseAt?: unknown }[]).flatMap((l, i) => {
      const f = l.at !== undefined ? t.at(l.at) : Math.round((0.3 + i * (p.gap ?? 0.55)) * t.fps);
      if (l.kind === "prompt") return [{ f, id: (l.text ?? "").length > 20 ? "typing-terminal" : "typing-short" }];
      if (l.kind === "tool") return [{ f, id: "tick-soft", vol: 0.6 }];
      if (l.kind === "ask") return [{ f, id: "chime-two-up" }, ...(l.chooseAt !== undefined ? [{ f: t.at(l.chooseAt), id: "key-enter" }] : [])];
      if (l.kind === "ok") return [{ f, id: "success-soft" }];
      return [];
    }),
    example: { lines: [{ kind: "prompt", text: "почини форму входа и прогони тесты" }, { kind: "tool", name: "Read", arg: "auth/middleware.ts", sub: ["Read 84 lines"] }, { kind: "tool", name: "Update", arg: "LoginForm.tsx", sub: ["+11 −5"] }, { kind: "ask", cmd: "npm test", chooseAt: 3.2 }, { kind: "ok", text: "23 tests passed" }] },
    exampleDur: 4.5,
  }),
  ClaudeChat: defineBlock({
    C: ClaudeChat, cat: "ui", pos: "stage", enter: "rise", sfx: "whoosh-airy",
    desc: "AI chat desktop app: greeting (serif), input with typed text (type,typeAt), attachment drop (attach:{src,name,at}), skill chips, model label, send (sendAt) then streaming reply (reply,replyAt). dark:true variant.",
    events: (p, t) => [
      ...(p.attach ? [{ f: p.attach.at !== undefined ? t.at(p.attach.at) : Math.round(0.3 * t.fps), id: "drop-in" }] : []),
      ...(p.type ? [{ f: p.typeAt !== undefined ? t.at(p.typeAt) : Math.round(0.6 * t.fps), id: (p.type ?? "").length > 20 ? "typing-medium" : "typing-short" }] : []),
      ...(p.sendAt !== undefined ? [{ f: t.at(p.sendAt), id: "swipe-up" }] : []),
    ],
    example: { type: "найди, где это снято", chips: ["geo-sleuth"], attach: { name: "IMG_2041.jpg", at: 0.2 } },
  }),
  CodeEditor: defineBlock({ C: CodeEditor, cat: "ui", pos: "stage", enter: "rise", sfx: null, desc: "Code editor with tabs, line numbers, naive syntax colours; typeFrom = line index where typing starts; marks:[{line,kind:add|del|hl,at}].", events: (p) => [{ f: 6, id: "typing-long", vol: 0.5 }], example: { file: "skill.md", code: "# geo-sleuth\nconst photo = await read(\"IMG_2041.jpg\")\nconst place = locate(photo) // ±2 м\nreturn place", typeFrom: 1, marks: [{ line: 3, kind: "hl", at: 2 }] } }),
  GithubRepo: defineBlock({ C: GithubRepo, cat: "ui", pos: "stage", enter: "rise", sfx: null, desc: "Repository page: owner/repo, desc, topics, rolling star count stars:[from,to] at starsAt, forks, license, file rows; ring:'stars'|'license'|'forks' circles a metric at ringAt.", events: (p, t) => [{ f: p.starsAt !== undefined ? t.at(p.starsAt) : Math.round(0.6 * t.fps), id: "tick-roll", vol: 0.6 }, ...(p.ring ? [{ f: p.ringAt !== undefined ? t.at(p.ringAt) : Math.round(1.6 * t.fps), id: "marker" }] : [])], example: { owner: "you", repo: "replica-skill", desc: "11 free skills that clone any app", stars: [136, 1200], ring: "stars", files: [{ name: "replica-architect" }, { name: "replica-backend" }, { name: "replica-design" }] } }),
  FileTree: defineBlock({ C: FileTree, cat: "ui", pos: "stage", enter: "rise", sfx: "swipe-soft", desc: "Folder tree with indentation and highlighted entries.", example: { items: [{ name: "skills", dir: true }, { name: "geo-sleuth", depth: 1, dir: true }, { name: "SKILL.md", depth: 2, hl: true }, { name: "terrain.py", depth: 2 }] } }),
};
