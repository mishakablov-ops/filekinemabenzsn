"""Generate the Reel Studio sound library (all synthesized, royalty-free by construction).

Usage:  python sfx_gen.py <out_dir>          (default: ../engine/public/sfx)
Writes <out_dir>/<category>/<name>.wav and <out_dir>/index.json with
{id, file, category, desc, tags, dur, peak}. `peak` = seconds from file start to
the perceptual hit point, so the engine can land it exactly on a visual event.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from dsp import (SR, taper, bandpass, bitcrush, env_adsr, env_bell, env_exp, fade, fm_bell, highpass,  # noqa: E402
                 karplus, log_sweep, lowpass, n_of, noise, note_hz, pan, pink, place, reverb, saw, seed,
                 silence, sine, softclip, square, stft_filter, svf, t_axis, to_stereo, tri, widen, write_wav)

LIB: list[dict] = []


# console: always UTF-8 (Windows defaults to cp1251)
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:
        pass

def sfx(category: str, name: str, desc: str, tags: str, peak: float | str = 0.0):
    def deco(fn):
        LIB.append(dict(category=category, name=name, fn=fn, desc=desc, tags=tags.split(), peak=peak))
        return fn
    return deco


# =================================================================== WHOOSH
def whoosh_core(dur=0.6, f0=250, f1=4000, peak=0.55, width=1.3, sharp=2.2, airy=0.0, sub=0.0, pan_from=0.0, pan_to=0.0):
    n = noise(dur) * 0.6 + pink(dur) * 0.4
    sweep = log_sweep(f0, f1, dur, 1.0)
    tt = np.linspace(0, dur, len(sweep))

    def g(f, t):
        fc = np.interp(t, tt, sweep)
        band = np.exp(-0.5 * (np.log2(np.maximum(f, 1) / fc) / (width / 2)) ** 2)
        return band + airy * (f > 5000) * 0.35
    x = stft_filter(n, g) * env_bell(dur, peak, sharp)
    if sub:
        s = sine(log_sweep(90, 45, dur), dur) * env_bell(dur, peak, 3) * sub
        x = x + s
    p = np.linspace(pan_from, pan_to, len(x))
    return widen(x) * 0.6 + pan(x, p) * 0.6


for i, (nm, d, f0, f1, pk, desc) in enumerate([
    ("whoosh-short", 0.32, 300, 5000, 0.55, "fast air pass, for quick cuts and card swaps"),
    ("whoosh-medium", 0.6, 250, 4200, 0.55, "standard transition whoosh"),
    ("whoosh-long", 1.1, 180, 3600, 0.6, "slow sweeping transition, scene change"),
    ("whoosh-up", 0.7, 200, 7000, 0.75, "rising whoosh, reveal upward / zoom in"),
    ("whoosh-down", 0.7, 6000, 250, 0.3, "falling whoosh, drop / zoom out"),
    ("whoosh-airy", 0.8, 1500, 9000, 0.5, "light airy breath, soft reveals on light themes"),
]):
    sfx("whoosh", nm, desc, "transition whoosh air", pk * d)(
        lambda d=d, f0=f0, f1=f1, pk=pk, i=i, nm=nm: (seed(100 + i), whoosh_core(d, f0, f1, pk, airy=0.5 if "airy" in nm else 0))[1])

sfx("whoosh", "whoosh-deep", "heavy whoosh with sub body, big scene change", "transition whoosh heavy", 0.5)(
    lambda: whoosh_core(0.9, 120, 1800, 0.55, width=1.6, sub=0.7))
sfx("whoosh", "whoosh-pan-lr", "whoosh panning left to right, horizontal slides", "transition whoosh pan", 0.33)(
    lambda: whoosh_core(0.6, 300, 4000, 0.55, pan_from=-0.9, pan_to=0.9))
sfx("whoosh", "whoosh-pan-rl", "whoosh panning right to left", "transition whoosh pan", 0.33)(
    lambda: whoosh_core(0.6, 300, 4000, 0.55, pan_from=0.9, pan_to=-0.9))
sfx("whoosh", "whoosh-double", "two quick passes, playful double swipe", "transition whoosh", 0.12)(
    lambda: place(to_stereo(whoosh_core(0.3, 400, 5000, 0.5)), whoosh_core(0.35, 300, 4500, 0.5), 0.16, 0.8))
sfx("whoosh", "whoosh-reverse", "reverse swell that sucks into the cut", "transition reverse swell", 0.95)(
    lambda: reverb(whoosh_core(1.0, 200, 6000, 0.97, sharp=3.0), 0.3, 1.0, tail=False))
sfx("whoosh", "whoosh-cloud", "soft wide wind gust, matches cloud/fog wipes", "transition wind cloud soft", 0.6)(
    lambda: reverb(whoosh_core(1.3, 400, 2500, 0.45, width=2.4, sharp=1.6, airy=0.3), 0.35, 1.6))


# =================================================================== SWIPE
def swipe(dur=0.18, f0=2500, f1=8000, peak=0.4):
    x = noise(dur)
    sw = log_sweep(f0, f1, dur)
    x = svf(x, sw, q=1.2, mode="band") * env_bell(dur, peak, 1.6)
    return widen(x)


for i, (nm, d, f0, f1, desc) in enumerate([
    ("swipe-fast", 0.14, 3000, 9000, "phone swipe, very quick"),
    ("swipe-soft", 0.22, 1500, 5000, "soft list scroll / page slide"),
    ("swipe-up", 0.2, 1200, 8000, "card flicked upward"),
    ("swipe-down", 0.2, 7000, 1200, "card flicked downward"),
    ("swipe-paper", 0.3, 800, 2500, "paper sliding over table"),
    ("swipe-tiny", 0.09, 4000, 10000, "micro swish for small UI chips"),
]):
    sfx("swipe", nm, desc, "swipe ui slide", d * 0.4)(lambda d=d, f0=f0, f1=f1, i=i: (seed(200 + i), swipe(d, f0, f1))[1])


# =================================================================== CLICK
def click(body=180, tone=3200, decay=0.012, noise_amt=0.6, body_amt=0.5, dur=0.08):
    t = t_axis(dur)
    nz = highpass(noise(dur), 2500) * np.exp(-t / (decay * 0.5)) * noise_amt
    tn = sine(tone, dur) * np.exp(-t / decay) * 0.5
    bd = sine(body, dur) * np.exp(-t / (decay * 2.5)) * body_amt
    return nz + tn + bd


CLICKS = [
    ("click-crisp", dict(), "crisp UI click, default button press"),
    ("click-soft", dict(tone=1800, noise_amt=0.3, decay=0.01), "soft muted click, light themes"),
    ("click-mouse", None, "mouse press + release pair"),
    ("click-trackpad", dict(tone=1200, noise_amt=0.15, body=120, body_amt=0.7, decay=0.015), "dull trackpad tap"),
    ("click-button", dict(body=140, body_amt=0.9, tone=2400, decay=0.018), "chunky button with body"),
    ("click-glass", dict(tone=5200, noise_amt=0.2, decay=0.02, body_amt=0.1), "glassy high click"),
    ("click-wood", dict(tone=900, noise_amt=0.2, body=320, body_amt=0.6, decay=0.02), "woody knock click"),
    ("click-tiny", dict(tone=6000, noise_amt=0.4, decay=0.005, body_amt=0.0, dur=0.03), "tiny tick-click for chips"),
    ("click-double", None, "quick double click"),
    ("click-select", dict(tone=2600, decay=0.03, body_amt=0.2), "selection confirm click with ring"),
]
for i, (nm, kw, desc) in enumerate(CLICKS):
    if nm == "click-mouse":
        fn = lambda: place(to_stereo(click()), click(tone=2600, noise_amt=0.35, body_amt=0.3), 0.075, 0.6)
    elif nm == "click-double":
        fn = lambda: place(to_stereo(click()), click(), 0.11, 0.9)
    else:
        fn = lambda kw=kw: click(**kw)
    sfx("click", nm, desc, "click ui tap cursor", 0.0)(lambda fn=fn, i=i: (seed(300 + i), fn())[1])


# =================================================================== POP
def pop(f0=900, f1=280, dur=0.12, sweep_t=0.04, decay=0.05, noise_amt=0.15):
    t = t_axis(dur)
    f = f1 + (f0 - f1) * np.exp(-t / sweep_t * 3)
    x = sine(f, dur) * np.exp(-t / decay)
    x += highpass(noise(dur), 3000) * np.exp(-t / 0.004) * noise_amt
    return x


def bubble(f0=300, f1=1200, dur=0.12):
    t = t_axis(dur)
    f = f0 + (f1 - f0) * (t / dur) ** 0.6
    return sine(f, dur) * env_exp(dur, dur * 0.4, 0.004)


POPS = [
    ("pop-soft", lambda: pop(700, 260, decay=0.05), "soft pop, card/element appears"),
    ("pop-high", lambda: pop(1400, 600, decay=0.035), "high pop, small badge appears"),
    ("pop-low", lambda: pop(420, 120, decay=0.07), "low pop, big block lands"),
    ("pop-bubble", lambda: bubble(), "rising bubble blip"),
    ("pop-bubble-high", lambda: bubble(600, 2000, 0.09), "small rising bubble"),
    ("pop-cork", lambda: pop(1600, 180, dur=0.16, sweep_t=0.06, decay=0.06, noise_amt=0.5), "cork pop, playful reveal"),
    ("pop-triple", lambda: place(place(to_stereo(pop(800, 300)), pop(1000, 380), 0.08, 0.8), pop(1250, 460), 0.16, 0.7),
     "three ascending pops, list items appearing"),
    ("pop-plop", lambda: reverb(pop(520, 180, dur=0.18, decay=0.06), 0.2, 0.6), "wet plop, liquid UI"),
]
for i, (nm, fn, desc) in enumerate(POPS):
    sfx("pop", nm, desc, "pop appear ui", 0.005)(lambda fn=fn, i=i: (seed(400 + i), fn())[1])


# =================================================================== TICK
def tick(freq=4200, dur=0.03, decay=0.004, nz=0.3):
    t = t_axis(dur)
    return sine(freq, dur) * np.exp(-t / decay) + highpass(noise(dur), 5000) * np.exp(-t / 0.002) * nz


TICKS = [
    ("tick-digital", lambda: tick(), "digital tick, counters"),
    ("tick-soft", lambda: tick(2600, decay=0.006, nz=0.1), "soft tick, slow counters"),
    ("tick-wood", lambda: bandpass(noise(0.05), 1800, 0.8) * env_exp(0.05, 0.006), "wooden tick"),
    ("tick-clock", lambda: place(to_stereo(tick(3000, 0.04, 0.005)), tick(2200, 0.04, 0.005), 0.5, 0.7), "clock tick-tock"),
    ("tick-meter", lambda: square(1800, 0.025, 6) * env_exp(0.025, 0.006) * 0.4, "meter/score blip"),
    ("tick-roll", None, "fast counter roll (1s of accelerating ticks)"),
]
for i, (nm, fn, desc) in enumerate(TICKS):
    if fn is None:
        def fn():
            out = silence(1.0)
            ts = np.cumsum(np.linspace(0.11, 0.03, 18))
            ts = ts / ts[-1] * 0.92
            for k, tt in enumerate(ts):
                out = place(out, tick(3600 + k * 40), float(tt), 0.5 + 0.5 * k / 18)
            return out
    sfx("tick", nm, desc, "tick counter number", 0.0)(lambda fn=fn, i=i: (seed(500 + i), fn())[1])


# =================================================================== TYPE
def key(kind="key"):
    dur = 0.09
    t = t_axis(dur)
    if kind == "space":
        th = bandpass(noise(dur), 260, 1.2) * np.exp(-t / 0.03) * 1.2
        cl = highpass(noise(dur), 3000) * np.exp(-t / 0.004) * 0.5
    elif kind == "enter":
        th = bandpass(noise(dur), 220, 1.2) * np.exp(-t / 0.035) * 1.4
        cl = highpass(noise(dur), 2500) * np.exp(-t / 0.006) * 0.7
    else:
        f = float(np.random.uniform(380, 620))
        th = bandpass(noise(dur), f, 1.0) * np.exp(-t / 0.018)
        cl = highpass(noise(dur), 4000) * np.exp(-t / 0.003) * 0.8
    return th + cl


def typing(n_keys=10, cps=14.0, jitter=0.35):
    out = silence(n_keys / cps + 0.2)
    tt = 0.0
    for k in range(n_keys):
        kind = "space" if (k % 6 == 5) else "key"
        out = place(out, pan(key(kind), np.random.uniform(-0.25, 0.25)), tt, float(np.random.uniform(0.55, 1.0)))
        tt += (1 / cps) * float(np.random.uniform(1 - jitter, 1 + jitter))
    return out


TYPES = [
    ("key-single", lambda: key(), "one keystroke"),
    ("key-space", lambda: key("space"), "space bar"),
    ("key-enter", lambda: key("enter"), "enter / return, submit prompt"),
    ("typing-short", lambda: typing(6), "short typing burst (~0.5s)"),
    ("typing-medium", lambda: typing(16), "typing a phrase (~1.2s)"),
    ("typing-long", lambda: typing(36, 15), "typing a sentence (~2.5s)"),
    ("typing-fast", lambda: typing(30, 24, 0.25), "fast confident typing (~1.3s)"),
    ("typing-terminal", lambda: place(typing(18, 16), key("enter"), 1.3, 1.0), "type a command then hit enter"),
]
for i, (nm, fn, desc) in enumerate(TYPES):
    sfx("type", nm, desc, "type keyboard terminal", 0.0)(lambda fn=fn, i=i: (seed(600 + i), np.random.seed(600 + i), fn())[2])


# =================================================================== NOTIFY
def chime(notes, gap=0.11, decay=0.5, wet=0.25, shape="bell"):
    out = silence(gap * len(notes) + decay * 3)
    for k, nm in enumerate(notes):
        f = note_hz(nm)
        if shape == "bell":
            s = fm_bell(f, decay * 3, ratio=3.01, index=1.2, decay=decay)
        elif shape == "glass":
            s = (sine(f, decay * 3) + 0.4 * sine(f * 2.76, decay * 3) + 0.2 * sine(f * 5.4, decay * 3)) * env_exp(decay * 3, decay)
        else:  # soft
            s = (tri(f, decay * 3) * 0.6 + sine(f, decay * 3) * 0.4) * env_exp(decay * 3, decay * 0.8, 0.005)
        out = place(out, s, gap * k, 1.0 - 0.1 * k)
    return reverb(out, wet, 1.4)


NOTIFS = [
    ("ding-soft", lambda: chime(["A5"], decay=0.45, shape="soft"), "single soft ding, message arrives"),
    ("ding-bright", lambda: chime(["E6"], decay=0.5), "bright single bell ding"),
    ("chime-two-up", lambda: chime(["E5", "B5"], 0.1), "two-note rising chime, notification"),
    ("chime-two-down", lambda: chime(["B5", "E5"], 0.1), "two-note falling chime, dismiss"),
    ("chime-triad", lambda: chime(["C6", "E6", "G6"], 0.08), "triad arpeggio, friendly alert"),
    ("chime-glass", lambda: chime(["G6", "D7"], 0.07, 0.35, shape="glass"), "glassy notification"),
    ("chime-message", lambda: chime(["D6", "A5", "D6"], 0.07, 0.3, shape="soft"), "messenger-like incoming message"),
    ("chime-calm", lambda: chime(["F5", "A5", "C6"], 0.14, 0.7, 0.35, shape="soft"), "calm reminder chime"),
    ("ping", lambda: reverb(sine(1760, 0.6) * env_exp(0.6, 0.15), 0.3, 1.0), "simple ping, highlight / location found"),
    ("ping-sonar", lambda: reverb(sine(1100, 1.0) * env_exp(1.0, 0.25) + 0.3 * sine(2200, 1.0) * env_exp(1.0, 0.1), 0.45, 2.2),
     "sonar ping, map pin / scanning"),
]
for i, (nm, fn, desc) in enumerate(NOTIFS):
    sfx("notify", nm, desc, "notification ding chime alert", 0.0)(lambda fn=fn, i=i: (seed(700 + i), fn())[1])


# =================================================================== SUCCESS / ERROR
def pluck_arp(notes, gap=0.07, bright=0.7, wet=0.25):
    out = silence(gap * len(notes) + 1.0)
    for k, nm in enumerate(notes):
        out = place(out, karplus(note_hz(nm), 0.9, bright, 0.995) * 0.8, gap * k, 1.0)
    return reverb(out, wet, 1.2)


RESULTS = [
    ("success-pluck", lambda: pluck_arp(["C5", "E5", "G5", "C6"]), "success arpeggio, task done", "success"),
    ("success-chime", lambda: chime(["G5", "C6", "E6", "G6"], 0.06, 0.5), "bright success chime", "success"),
    ("success-check", lambda: place(to_stereo(click(tone=2600)), chime(["E6", "B6"], 0.06, 0.3, shape="soft"), 0.02),
     "checkbox ticked", "success check"),
    ("success-soft", lambda: chime(["D5", "A5"], 0.12, 0.6, 0.3, shape="soft"), "gentle confirmation", "success"),
    ("success-level", lambda: pluck_arp(["G4", "C5", "E5", "G5", "C6", "E6"], 0.05, 0.9), "level-up / unlocked", "success"),
    ("success-coin", lambda: reverb(square(note_hz("B5"), 0.08, 8) * 0.3 * env_exp(0.08, 0.05) if False else
                                   np.concatenate([square(note_hz("B5"), 0.07, 8) * 0.3, square(note_hz("E6"), 0.35, 8) * 0.3 * env_exp(0.35, 0.12)]), 0.15, 0.6),
     "8-bit coin, playful reward", "success retro"),
    ("error-buzz", lambda: (square(140, 0.12, 10) * 0.35 * env_adsr(0.12, 0.005, 0.02, 0.8, 0.03)).tolist() and
     np.concatenate([square(150, 0.11, 10) * 0.3 * env_adsr(0.11, 0.005, 0.02, 0.8, 0.03), np.zeros(n_of(0.04)),
                     square(120, 0.16, 10) * 0.3 * env_adsr(0.16, 0.005, 0.02, 0.8, 0.05)]), "soft double error buzz", "error"),
    ("error-down", lambda: chime(["E5", "C5"], 0.12, 0.35, 0.2, shape="soft"), "falling 'nope' tones", "error"),
    ("error-thud", lambda: lowpass(sine(log_sweep(160, 70, 0.25), 0.25) * env_exp(0.25, 0.08), 600), "dull thud, rejected", "error"),
    ("deny-tap", lambda: place(to_stereo(click(tone=900, body=110)), click(tone=800, body=100), 0.09, 0.8), "two dull taps, denied", "error"),
]
for i, (nm, fn, desc, tg) in enumerate(RESULTS):
    sfx("result", nm, desc, tg + " result", 0.0)(lambda fn=fn, i=i: (seed(800 + i), fn())[1])


# =================================================================== IMPACT
def impact(sub_f0=90, sub_f1=38, dur=1.2, sub_decay=0.35, click_amt=0.5, noise_amt=0.6, lp=2500, wet=0.2):
    t = t_axis(dur)
    sub = sine(sub_f1 + (sub_f0 - sub_f1) * np.exp(-t / 0.06), dur) * np.exp(-t / sub_decay)
    nz = lowpass(noise(dur), lp) * np.exp(-t / 0.08) * noise_amt
    ck = highpass(noise(dur), 3000) * np.exp(-t / 0.003) * click_amt
    x = taper(softclip(sub + nz + ck, 1.4), 0.3)
    return reverb(x, wet, 1.8) if wet else x


IMPACTS = [
    ("hit-soft", lambda: impact(80, 45, 0.6, 0.15, 0.2, 0.3, 1500, 0.1), "soft hit under a title"),
    ("hit-punch", lambda: impact(120, 50, 0.5, 0.12, 0.7, 0.7, 4000, 0.05), "punchy hit, number lands"),
    ("hit-cinematic", lambda: impact(70, 32, 2.5, 0.8, 0.4, 0.8, 1800, 0.35), "big cinematic boom, reveal"),
    ("thud", lambda: impact(110, 60, 0.35, 0.08, 0.1, 0.5, 900, 0.0), "short thud, object drops"),
    ("hit-sub", lambda: impact(60, 30, 1.6, 0.6, 0.0, 0.1, 400, 0.0), "pure sub drop, felt not heard"),
    ("hit-metal", lambda: reverb(impact(100, 45, 0.8, 0.2, 0.6, 0.4, 3000, 0) +
                                 to_stereo(0.25 * fm_bell(523, 0.8, 1.41, 3, 0.25))[:, 0], 0.3, 1.5), "metallic clang hit"),
    ("hit-glitch", lambda: impact(100, 40, 0.6, 0.15, 0.5, 0.5, 3000, 0) + bitcrush(noise(0.6) * env_exp(0.6, 0.06), 4, 12) * 0.4,
     "digital crunchy hit"),
    ("heartbeat", lambda: place(to_stereo(impact(70, 40, 0.4, 0.09, 0, 0.1, 300, 0)), impact(65, 38, 0.5, 0.1, 0, 0.1, 300, 0), 0.24, 0.7),
     "two heartbeat thumps, tension"),
]
for i, (nm, fn, desc) in enumerate(IMPACTS):
    sfx("impact", nm, desc, "impact hit boom", 0.0)(lambda fn=fn, i=i: (seed(900 + i), fn())[1])


# =================================================================== RISER / DOWNLIFTER
def riser(dur=2.0, f0=200, f1=6000, tonal=0.4, base=110):
    nz = noise(dur) * 0.6 + pink(dur) * 0.4
    sw = log_sweep(f0, f1, dur, 1.6)
    tt = np.linspace(0, dur, len(sw))
    x = stft_filter(nz, lambda f, t: np.exp(-0.5 * (np.log2(np.maximum(f, 1) / np.interp(t, tt, sw)) / 0.7) ** 2))
    env = (np.linspace(0, 1, len(x)) ** 2.2)
    x *= env
    if tonal:
        fr = log_sweep(base, base * 4, dur, 1.8)
        tn = (saw(fr, dur) * 0.4 + saw(fr * 1.005, dur) * 0.4)
        tn = lowpass(tn, 3000) * env * tonal
        x = x + tn
    return reverb(x, 0.25, 1.5, tail=False)


RISERS = [
    ("riser-short", lambda: riser(1.0, 300, 7000, 0.3), "1s build into a reveal", 1.0),
    ("riser-medium", lambda: riser(2.0), "2s build", 2.0),
    ("riser-long", lambda: riser(4.0, 150, 8000, 0.5, 80), "4s tension build for promos", 4.0),
    ("riser-noise", lambda: riser(1.6, 400, 10000, 0.0), "noise-only sweep build", 1.6),
    ("riser-tonal", lambda: riser(2.0, 300, 3000, 1.0, 220), "pitch-rising synth build", 2.0),
    ("downlifter", lambda: riser(1.6, 200, 6000, 0.4)[::-1].copy(), "falling sweep after a drop", 0.0),
    ("downlifter-short", lambda: riser(0.8, 300, 7000, 0.2)[::-1].copy(), "short release after a hit", 0.0),
    ("suck-in", lambda: riser(0.6, 500, 9000, 0.0), "quick reverse suck into cut", 0.6),
]
for i, (nm, fn, desc, pk) in enumerate(RISERS):
    sfx("riser", nm, desc, "riser build tension sweep", pk)(lambda fn=fn, i=i: (seed(1000 + i), fn())[1])


# =================================================================== GLITCH / DIGITAL
def glitch_burst(dur=0.4, seed_n=0):
    rng = np.random.default_rng(seed_n)
    out = np.zeros(n_of(dur))
    tt = 0.0
    while tt < dur - 0.02:
        seg = float(rng.uniform(0.01, 0.06))
        kind = rng.integers(0, 3)
        if kind == 0:
            s = square(float(rng.uniform(200, 3000)), seg, 6) * 0.4
        elif kind == 1:
            s = bitcrush(noise(seg), int(rng.integers(3, 6)), int(rng.integers(4, 20))) * 0.5
        else:
            s = sine(float(rng.uniform(800, 6000)), seg) * 0.5
        a = n_of(tt)
        out[a:a + len(s)] += s[: len(out) - a]
        tt += seg + float(rng.uniform(0, 0.03))
    return out


GLITCHES = [
    ("glitch-short", lambda: glitch_burst(0.25, 1), "tiny glitch stutter"),
    ("glitch-medium", lambda: glitch_burst(0.5, 2), "glitch burst for RGB-split transition"),
    ("glitch-long", lambda: glitch_burst(1.0, 3), "longer data corruption"),
    ("data-blips", lambda: np.concatenate([square(float(f), 0.035, 5) * 0.25 * env_exp(0.035, 0.02)
                                           for f in np.random.default_rng(4).uniform(900, 3200, 14)]), "computer processing blips"),
    ("scan-beep", lambda: np.concatenate([sine(2400, 0.06) * 0.4, np.zeros(n_of(0.08)), sine(2400, 0.06) * 0.4, np.zeros(n_of(0.08)), sine(3200, 0.12) * 0.4 * env_exp(0.12, 0.06)]),
     "scanner beeps, found it"),
    ("hum-on", lambda: lowpass(saw(log_sweep(30, 100, 0.8), 0.8), 900) * env_adsr(0.8, 0.3, 0.1, 0.8, 0.2) * 0.6,
     "power-on hum swell"),
    ("power-off", lambda: lowpass(saw(log_sweep(110, 25, 0.9), 0.9), 900) * env_exp(0.9, 0.35, 0.002) * 0.6, "power down"),
    ("modem-chirp", lambda: sine(log_sweep(600, 3200, 0.35, 0.7), 0.35) * env_bell(0.35, 0.2) * 0.5, "single digital chirp"),
]
for i, (nm, fn, desc) in enumerate(GLITCHES):
    sfx("digital", nm, desc, "glitch digital tech computer", 0.0)(lambda fn=fn, i=i: (seed(1100 + i), fn())[1])


# =================================================================== SHIMMER / MAGIC
def sparkle(dur=1.0, n=26, fmin=2500, fmax=9000, seed_n=0, rise=False):
    rng = np.random.default_rng(seed_n)
    out = np.zeros(n_of(dur) + n_of(0.4))
    for k in range(n):
        tt = (k / n) * dur * 0.8 if rise else float(rng.uniform(0, dur * 0.8))
        f = (fmin + (fmax - fmin) * (k / n)) if rise else float(rng.uniform(fmin, fmax))
        s = sine(f, 0.25) * env_exp(0.25, 0.05, 0.002) * float(rng.uniform(0.3, 1.0))
        a = n_of(tt)
        out[a:a + len(s)] += s
    return reverb(out, 0.45, 1.8)


SHIMMERS = [
    ("sparkle", lambda: sparkle(0.8, 22, seed_n=1), "sparkle twinkle, something shiny appears"),
    ("sparkle-rise", lambda: sparkle(0.9, 18, 2000, 9000, 2, True), "rising sparkle, magic reveal"),
    ("shimmer-pad", lambda: reverb(sum(sine(note_hz(n), 2.0) for n in ["E6", "B6", "E7"]) * env_adsr(2.0, 0.6, 0.3, 0.6, 0.8) * 0.3, 0.6, 2.5),
     "soft shimmering pad swell"),
    ("star", lambda: reverb(sine(3520 * (1 + 0.004 * np.sin(2 * np.pi * 9 * t_axis(0.7))), 0.7) * env_exp(0.7, 0.2) * 0.5, 0.4, 1.6),
     "single star twinkle"),
    ("magic-wand", lambda: place(sparkle(0.6, 14, 3000, 8000, 3, True), chime(["C7"], decay=0.4, shape="glass"), 0.5, 0.6),
     "wand swish with sparkle"),
    ("reveal-glow", lambda: reverb(riser(0.7, 1500, 9000, 0.0) * 0.6, 0.4, 1.8), "airy glow reveal"),
]
for i, (nm, fn, desc) in enumerate(SHIMMERS):
    sfx("shimmer", nm, desc, "shimmer sparkle magic", 0.0)(lambda fn=fn, i=i: (seed(1200 + i), fn())[1])


# =================================================================== MECHANICAL / UI MISC
def shutter():
    a = click(tone=1500, body=200, noise_amt=0.9, decay=0.01)
    b = click(tone=1200, body=160, noise_amt=0.7, decay=0.012)
    return place(to_stereo(a), b, 0.06, 0.8)


def toggle(up=True):
    return place(to_stereo(click(tone=2200 if up else 1700, body=200)), pop(900 if up else 600, 500 if up else 300, 0.06), 0.01, 0.3)


def scroll_ticks(n=10, dur=0.6):
    out = silence(dur + 0.05)
    ts = np.linspace(0, dur, n) ** 1.3 / dur ** 0.3
    for k, tt in enumerate(ts):
        out = place(out, tick(3000 + 50 * k, 0.02, 0.003, 0.2), float(tt), 0.5)
    return out


MISC = [
    ("shutter", shutter, "camera shutter, screenshot"),
    ("toggle-on", lambda: toggle(True), "switch toggled on"),
    ("toggle-off", lambda: toggle(False), "switch toggled off"),
    ("scroll", lambda: scroll_ticks(12, 0.7), "scroll wheel ticks, list scrolling"),
    ("card-slide", lambda: lowpass(noise(0.25), 1800) * env_bell(0.25, 0.3) * 0.8, "card slides onto table"),
    ("card-flip", lambda: place(to_stereo(lowpass(noise(0.12), 2500) * env_bell(0.12, 0.4)), click(tone=1400, body=170), 0.1, 0.5),
     "card flips over"),
    ("paper-rustle", lambda: bandpass(noise(0.5), 3500, 2.0) * (0.5 + 0.5 * np.abs(np.sin(np.linspace(0, 18, n_of(0.5))))) * env_bell(0.5, 0.4),
     "paper rustle, document appears"),
    ("lock", lambda: place(to_stereo(click(tone=1800, body=220, body_amt=0.8)), click(tone=1300, body=150), 0.05, 0.7), "phone lock click"),
    ("unlock", lambda: place(to_stereo(swipe(0.15, 2000, 6000)), click(tone=2400, body=200), 0.12, 0.8), "unlock swipe + click"),
    ("cash", lambda: reverb(sum(fm_bell(f, 0.6, 2.4, 1.5, 0.25) for f in (2093, 2637, 3136)) * 0.4, 0.2, 0.8), "coins / payment success"),
    ("zoom-in", lambda: place(whoosh_core(0.5, 400, 6000, 0.8), pop(600, 900, 0.1), 0.38, 0.5), "zoom into detail"),
    ("zoom-out", lambda: whoosh_core(0.5, 5000, 400, 0.25), "zoom out to overview"),
    ("drop-in", lambda: place(to_stereo(swipe(0.15, 3000, 1000)), impact(110, 60, 0.3, 0.07, 0.3, 0.3, 1200, 0), 0.12), "element drops in and lands"),
    ("hover", lambda: sine(1320, 0.08) * env_exp(0.08, 0.03, 0.01) * 0.5, "subtle hover blip"),
    ("cursor-move", lambda: highpass(noise(0.3), 6000) * env_bell(0.3, 0.5) * 0.25, "faint cursor travel air"),
    ("stamp", lambda: place(to_stereo(impact(130, 70, 0.3, 0.06, 0.8, 0.8, 3000, 0)), noise(0.05) * 0.2, 0.0), "rubber stamp, verdict"),
    ("strike", lambda: bandpass(noise(0.28), 2500, 1.5) * env_bell(0.28, 0.2) * 0.9, "marker strikethrough scratch"),
    ("marker", lambda: bandpass(noise(0.35), 1800, 2.0) * (0.6 + 0.4 * np.sin(np.linspace(0, 40, n_of(0.35)))) * env_bell(0.35, 0.3),
     "highlighter marker swipe"),
]
for i, (nm, fn, desc) in enumerate(MISC):
    sfx("ui", nm, desc, "ui mechanical", 0.0 if nm not in ("zoom-in",) else 0.38)(lambda fn=fn, i=i: (seed(1300 + i), fn())[1])


# =================================================================== STINGER / TONAL
def stinger(chord, dur=2.5, hit=True):
    pad = sum(saw(note_hz(n), dur) * 0.15 + saw(note_hz(n) * 1.004, dur) * 0.15 for n in chord)
    pad = lowpass(pad, 2200) * env_adsr(dur, 0.02, 0.4, 0.5, 1.2)
    plk = sum(karplus(note_hz(n) * 2, 1.5, 0.8) for n in chord) * 0.3
    x = pad + np.concatenate([plk, np.zeros(max(0, len(pad) - len(plk)))])[: len(pad)]
    if hit:
        x = x + impact(80, 40, dur, 0.3, 0.3, 0.4, 2000, 0)[: len(x)] * 0.8
    return reverb(x, 0.35, 2.2)


STINGERS = [
    ("sting-logo", lambda: stinger(["C4", "G4", "E5"]), "logo / outro stinger with hit"),
    ("sting-soft", lambda: stinger(["F4", "A4", "E5"], 2.0, False), "soft warm chord, calm ending"),
    ("sting-dark", lambda: stinger(["A3", "C4", "E4"], 2.5), "minor stinger, problem statement"),
    ("sting-bright", lambda: stinger(["D4", "A4", "F#5"], 2.0), "bright major stinger, positive reveal"),
    ("tone-bass-drop", lambda: lowpass(saw(log_sweep(110, 40, 1.0), 1.0), 500) * env_exp(1.0, 0.4) * 0.8, "bass drop tone"),
    ("tone-rise-short", lambda: lowpass(saw(log_sweep(110, 440, 0.5, 1.5), 0.5), 2500) * np.linspace(0, 1, n_of(0.5)) ** 2 * 0.6,
     "short tonal rise into cut"),
]
for i, (nm, fn, desc) in enumerate(STINGERS):
    sfx("sting", nm, desc, "stinger tonal musical", 0.0 if "rise" not in nm else 0.5)(lambda fn=fn, i=i: (seed(1400 + i), fn())[1])


# =================================================================== AMBIENCE
def air_loop(dur=8.0, fc=900, amt=0.6):
    x = pink(dur) * amt
    x = lowpass(x, fc)
    lfo = 0.85 + 0.15 * np.sin(2 * np.pi * 0.11 * t_axis(dur))
    x = x * lfo
    xf = n_of(1.0)
    head, tail = x[:xf].copy(), x[-xf:].copy()
    ramp = np.linspace(0, 1, xf)
    x = x[:-xf].copy()
    x[:xf] = head * ramp + tail * (1 - ramp)  # seamless loop
    return widen(x, 18)


AMBS = [
    ("room-tone", lambda: air_loop(8, 600, 0.4), "quiet room tone loop, glue under voice"),
    ("air-high", lambda: air_loop(8, 4000, 0.3), "airy hiss bed, sky / clouds scenes"),
    ("space-drone", lambda: reverb(sum(sine(f, 10) * 0.2 for f in (55, 82.4, 110.3)) * (0.8 + 0.2 * np.sin(2 * np.pi * 0.07 * t_axis(10))), 0.5, 3.0, tail=False),
     "deep space drone loop, night / planet scenes"),
    ("city-hum", lambda: air_loop(8, 300, 0.7), "low city hum bed, map / city flyovers"),
    ("wind", lambda: (lambda d: widen(stft_filter(pink(d), lambda f, t: np.exp(-0.5 * (np.log2(np.maximum(f, 1) / (500 + 300 * np.sin(t * 0.9))) / 0.8) ** 2))))(8.0),
     "soft wind loop, mountains"),
    ("terminal-hum", lambda: air_loop(8, 250, 0.5) + to_stereo(sine(60, 7.0) * 0.02), "faint computer fan hum"),
]
for i, (nm, fn, desc) in enumerate(AMBS):
    sfx("ambience", nm, desc, "ambience loop bed", 0.0)(lambda fn=fn, i=i: (seed(1500 + i), fn())[1])


# =================================================================== COMBOS (transition packs)
COMBOS = [
    ("trans-whoosh-hit", lambda: place(to_stereo(whoosh_core(0.6, 250, 4000, 0.9)), impact(100, 45, 0.8, 0.15, 0.5, 0.5, 2500, 0.1), 0.54),
     "whoosh landing on a hit, hard scene change", 0.54),
    ("trans-swish-pop", lambda: place(to_stereo(swipe(0.18, 2500, 8000)), pop(800, 300), 0.1), "swish into pop, UI element entrance", 0.1),
    ("trans-riser-hit", lambda: place(to_stereo(riser(1.2, 300, 7000, 0.3)), impact(90, 40, 1.2, 0.3, 0.5, 0.6, 2500, 0.2), 1.2),
     "build then hit, big reveal", 1.2),
    ("trans-glitch-cut", lambda: place(to_stereo(glitch_burst(0.3, 9)), impact(120, 50, 0.4, 0.08, 0.5, 0.3, 3000, 0), 0.25), "glitch into cut", 0.25),
    ("trans-air-sparkle", lambda: place(to_stereo(whoosh_core(0.8, 1500, 9000, 0.5, airy=0.5)), sparkle(0.5, 10, 4000, 9000, 5), 0.35),
     "airy reveal with sparkle", 0.4),
    ("trans-zoom-through", lambda: place(to_stereo(riser(0.5, 400, 8000, 0.0)), whoosh_core(0.5, 6000, 300, 0.15), 0.45),
     "zoom-through tunnel transition", 0.5),
]
for i, (nm, fn, desc, pk) in enumerate(COMBOS):
    sfx("transition", nm, desc, "transition combo", pk)(lambda fn=fn, i=i: (seed(1600 + i), fn())[1])


# =================================================================== VARIANTS (pitch / timing families)
def varispeed(x: np.ndarray, ratio: float) -> np.ndarray:
    x = to_stereo(x)
    n = int(len(x) / ratio)
    idx = np.linspace(0, len(x) - 1, n)
    return np.stack([np.interp(idx, np.arange(len(x)), x[:, c]) for c in range(2)], axis=1)


VARIANT_SRC = [("click", "click-crisp"), ("pop", "pop-soft"), ("tick", "tick-digital"), ("whoosh", "whoosh-short"),
               ("notify", "ding-soft"), ("swipe", "swipe-fast")]


def main(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    catalog = []
    t0 = time.time()
    rendered: dict[str, np.ndarray] = {}
    for item in LIB:
        x = item["fn"]()
        x = to_stereo(np.asarray(x, dtype=np.float64))
        rendered[item["name"]] = x
        rel = f"{item['category']}/{item['name']}.wav"
        dur = write_wav(out_dir / rel, x, peak_db=-1.0)
        catalog.append(dict(id=item["name"], file=f"sfx/{rel}", category=item["category"], desc=item["desc"],
                            tags=item["tags"], dur=round(dur, 3), peak=round(float(item["peak"]), 3)))
    # pitch variants: -3 / +3 semitones for the most used families
    for cat, nm in VARIANT_SRC:
        base = rendered[nm]
        base_item = next(c for c in catalog if c["id"] == nm)
        for st, tag in ((-3, "low"), (3, "high")):
            r = 2 ** (st / 12)
            x = varispeed(base, r)
            vid = f"{nm}-{tag}"
            rel = f"{cat}/{vid}.wav"
            dur = write_wav(out_dir / rel, x)
            catalog.append(dict(id=vid, file=f"sfx/{rel}", category=cat, desc=base_item["desc"] + f" ({tag}er pitch variant)",
                                tags=base_item["tags"] + ["variant"], dur=round(dur, 3), peak=round(base_item["peak"] / r, 3)))
    (out_dir / "index.json").write_text(json.dumps(catalog, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(catalog)} sounds -> {out_dir}  ({time.time() - t0:.1f}s)")
    import sfx_library  # retire the tonal "8-bit" blips again (see sfx_library.RETIRED)
    if out_dir.resolve() == sfx_library.SFX.resolve():
        sfx_library.write_docs(sfx_library.apply_retired())
        if (sfx_library.PACKS_DIR).exists():
            print("re-run: scripts/sfx_library.py import <your pack>  (the regenerated index lost the pack mapping)")


if __name__ == "__main__":
    default = Path(__file__).resolve().parent.parent / "engine" / "public" / "sfx"
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else default)
