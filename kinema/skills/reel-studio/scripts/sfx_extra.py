"""Extra synthesized sounds: disaster / survival / foley. Noise-based and physically modelled — no 8-bit blips.
Appends to engine/public/sfx/index.json (ids replaced if present) without touching the rest of the library.

    python sfx_extra.py            # generate all
    python sfx_extra.py --list
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from dsp import (SR, bandpass, env_bell, env_exp, fade, highpass, log_sweep, lowpass, n_of, noise, pink, place, reverb,  # noqa: E402
                 saw, seed, sine, softclip, svf, to_stereo, widen, write_wav)
import sfx_library as L  # noqa: E402

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:
        pass

EXTRA: list[dict] = []


def item(category: str, name: str, desc: str, tags: str):
    def deco(fn):
        EXTRA.append(dict(category=category, name=name, fn=fn, desc=desc, tags=tags.split()))
        return fn
    return deco


def grains(dur: float, rate, fc: float, width: float = 1.0, glen: float = 0.0006, rng_seed: int = 1, amp_jit: float = 0.6) -> np.ndarray:
    """Poisson clicks: rate may be a function of time (per second). Each click = tiny filtered noise burst."""
    r = np.random.default_rng(rng_seed)
    out = np.zeros(n_of(dur))
    t = 0.0
    while t < dur:
        rt = rate(t) if callable(rate) else rate
        t += r.exponential(1 / max(rt, 0.01))
        if t >= dur:
            break
        n = max(8, int(glen * SR))
        b = r.uniform(-1, 1, n) * np.exp(-np.arange(n) / (n / 4)) * (1 - amp_jit * r.random())
        i = int(t * SR)
        out[i:i + n] += b[: len(out) - i]
    return bandpass(out, fc, width)


# ------------------------------------------------------------------ alarms
def siren(dur: float, f_lo=180.0, f_hi=520.0, rise=2.6, fall=2.4, dist=0.4, seed_n=1) -> np.ndarray:
    seed(seed_n)
    t = np.arange(n_of(dur)) / SR
    cyc = rise + 1.2 + fall
    ph = (t % cyc)
    f = np.where(ph < rise, f_lo + (f_hi - f_lo) * (1 - np.cos(np.pi * ph / rise)) / 2,
                 np.where(ph < rise + 1.2, f_hi, f_hi - (f_hi - f_lo) * (1 - np.cos(np.pi * (ph - rise - 1.2) / fall)) / 2))
    f = f * (1 + 0.004 * np.sin(2 * np.pi * 5.5 * t))
    x = saw(f, dur) * 0.5 + sine(f * 2.0, dur) * 0.15
    x = lowpass(x, 1500 - 900 * dist)
    x = x * (0.75 + 0.25 * np.sin(2 * np.pi * 0.13 * t + seed_n))  # wind-borne swell
    return reverb(x * 0.6, 0.35 + 0.4 * dist, 2.8, 0.7)


@item("alarm", "siren-air-raid", "air-raid siren, rising and falling, city-wide (6 s)", "alarm siren warning disaster")
def _():
    a = siren(7.5, dist=0.25, seed_n=1)
    b = siren(7.5, 170, 495, 2.9, 2.6, dist=0.7, seed_n=2)
    return widen(a * 0.8) + to_stereo(b * 0.45)


@item("alarm", "siren-far", "distant siren over the city, faint (8 s)", "alarm siren distant")
def _():
    return widen(siren(8.0, 175, 480, 3.0, 2.8, dist=0.95, seed_n=3) * 0.7)


# ------------------------------------------------------------------ blast
@item("impact", "nuke-boom", "distant detonation: crack, then a huge rolling rumble (7 s)", "impact explosion blast nuclear rumble")
def _():
    seed(31)
    d = 7.0
    crack = highpass(noise(0.08), 900) * env_exp(0.08, 0.012, 0.0005)
    body = lowpass(pink(d), 140) * env_exp(d, 2.4, 0.03) * 2.2
    sub = sine(log_sweep(55, 24, d, 0.6), d) * env_exp(d, 2.8, 0.01) * 0.9
    roll = lowpass(pink(d), 380) * env_bell(d, 0.12, 1.4) * 0.6
    x = place(np.zeros(n_of(d)), crack * 0.6, 0.0)[: n_of(d)] + body + sub + roll
    return widen(reverb(softclip(x, 1.4), 0.3, 3.2, 0.8))


@item("impact", "shockwave-hit", "shockwave arriving: roaring wind rush, slam, flying debris (3.5 s)", "impact shockwave wind debris blast")
def _():
    seed(32)
    d = 3.5
    rush = svf(noise(d), log_sweep(180, 900, d, 0.5), q=0.9, mode="band") * env_bell(d, 0.22, 2.2) * 1.4
    slam = lowpass(noise(0.4), 220) * env_exp(0.4, 0.12, 0.002) * 2.0
    debris = grains(d, lambda t: 220 * np.exp(-t * 1.4), 2400, 1.6, 0.0012, 7) * 2.5
    x = rush + place(np.zeros(n_of(d)), slam, 0.7)[: n_of(d)] + np.concatenate([np.zeros(n_of(0.7)), debris[: n_of(d) - n_of(0.7)]])
    return widen(reverb(softclip(x, 1.2), 0.25, 1.6, 0.7))


@item("ambience", "rumble-distant", "distant rolling rumble, aftershock thunder (6 s)", "ambience rumble distant thunder")
def _():
    seed(33)
    d = 6.0
    t = np.arange(n_of(d)) / SR
    x = lowpass(pink(d), 160) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.35 * t)) * env_bell(d, 0.35, 1.2) * 1.8
    return widen(reverb(x, 0.3, 2.5, 0.8))


@item("ambience", "wind-ash", "dusty wind over an empty city, gusting (8 s)", "ambience wind empty city")
def _():
    seed(34)
    d = 8.0
    t = np.arange(n_of(d)) / SR
    gust = 0.55 + 0.45 * np.sin(2 * np.pi * 0.18 * t) * np.sin(2 * np.pi * 0.07 * t + 1)
    fc = 420 + 320 * gust
    x = svf(pink(d), fc, q=1.1, mode="band") * gust * 1.6 + highpass(noise(d), 4000) * 0.05 * gust
    return widen(x, 18)


@item("ambience", "bunker-tone", "shelter room tone: low hum, faint vent air, distant creaks (8 s)", "ambience shelter bunker room tone")
def _():
    seed(35)
    d = 8.0
    hum = sum(sine(50 * k, d) * a for k, a in ((1, 0.05), (2, 0.03), (3, 0.015)))
    air = lowpass(pink(d), 400) * 0.25
    creak = grains(d, 0.8, 600, 0.6, 0.01, 9) * 0.6
    return widen(hum + air + creak)


# ------------------------------------------------------------------ survival foley
@item("foley", "geiger-low", "Geiger counter, background level: sparse clicks (3 s)", "foley geiger radiation counter")
def _():
    return widen(grains(3.0, 6, 4200, 1.4, 0.0005, 11) * 3)


@item("foley", "geiger-high", "Geiger counter near a hot spot: dense crackle (3 s)", "foley geiger radiation counter danger")
def _():
    return widen(grains(3.0, 55, 4200, 1.4, 0.0005, 12) * 3)


@item("foley", "geiger-rise", "Geiger counter approaching contamination: clicks speed up (4 s)", "foley geiger radiation counter rising")
def _():
    return widen(grains(4.0, lambda t: 3 + 70 * (t / 4) ** 2, 4200, 1.4, 0.0005, 13) * 3)


def formant_murmur(d: float, s: int) -> np.ndarray:
    seed(s)
    t = np.arange(n_of(d)) / SR
    syl = np.clip(np.sin(2 * np.pi * 4.2 * t + np.sin(2 * np.pi * 0.7 * t) * 2), 0, 1) ** 1.5
    src = pink(d) * syl
    return bandpass(src, 650, 0.6) * 1.2 + bandpass(src, 1500, 0.5) * 0.8 + bandpass(src, 2600, 0.5) * 0.3


@item("foley", "radio-static", "radio static with crackle (4 s)", "foley radio static noise")
def _():
    seed(41)
    d = 4.0
    st = bandpass(noise(d), 1800, 2.6) * 0.35
    crk = grains(d, 25, 2500, 2.0, 0.002, 21) * 1.5
    return widen(st + crk)


@item("foley", "radio-voice", "emergency broadcast under static: distant unintelligible announcer (4 s)", "foley radio voice broadcast emergency")
def _():
    d = 4.0
    seed(42)
    v = formant_murmur(d, 43)
    st = bandpass(noise(d), 1800, 2.6) * 0.18
    return widen(bandpass(v, 1300, 1.8) + st)


@item("foley", "radio-tune", "tuning a radio: static sweeps then catches a voice (2.5 s)", "foley radio tune search")
def _():
    seed(44)
    d = 2.5
    t = np.arange(n_of(d)) / SR
    sweep = svf(noise(d), log_sweep(400, 3200, d, 0.7), q=2.2, mode="band") * 0.8
    voice = formant_murmur(d, 45) * np.clip((t - 1.4) / 0.5, 0, 1)
    return widen(sweep * np.clip(1.6 - t / 1.6, 0.2, 1) + voice)


@item("foley", "crank-wind", "winding a hand-crank radio/flashlight: ratchet clicks (1.6 s)", "foley crank ratchet")
def _():
    d = 1.6
    t = np.arange(n_of(d)) / SR
    clicks = grains(d, 22, 1700, 1.0, 0.003, 46) * 2.2
    whir = bandpass(noise(d), 300, 1.0) * 0.15 * (0.5 + 0.5 * np.sin(2 * np.pi * 2.6 * t))
    return widen(clicks + whir)


@item("foley", "door-heavy-close", "heavy steel door slams shut, bolt engages, concrete room (2.5 s)", "foley door metal heavy shelter")
def _():
    seed(51)
    d = 2.5
    thump = sine(log_sweep(70, 38, 0.6), 0.6) * env_exp(0.6, 0.18, 0.002) * 1.2
    metal = sum(bandpass(noise(d), f, 0.08) * env_exp(d, dec, 0.001) * a for f, dec, a in ((410, 0.9, 1.0), (937, 0.6, 0.7), (1730, 0.4, 0.5), (2610, 0.3, 0.35)))
    bolt = highpass(noise(0.05), 1500) * env_exp(0.05, 0.01, 0.0005) * 0.8
    x = np.zeros(n_of(d))
    x[: len(thump)] += thump
    x += metal * 1.4
    x = place(x, bolt, 0.42)[: n_of(d)]
    return widen(reverb(x, 0.35, 1.3, 0.55))


@item("foley", "door-creak", "slow heavy door creak (2 s)", "foley door creak")
def _():
    seed(52)
    d = 2.0
    t = np.arange(n_of(d)) / SR
    stick = (np.sin(2 * np.pi * (35 + 25 * np.sin(2 * np.pi * 0.6 * t)) * t) > 0.6).astype(float)
    x = svf(noise(d) * stick, 520 + 260 * np.sin(2 * np.pi * 0.45 * t), q=6, mode="band") * env_bell(d, 0.5, 1.2) * 1.6
    return widen(reverb(x, 0.25, 1.0, 0.6))


def steps(d: float, n: int, every: float, crunch: float, s: int) -> np.ndarray:
    seed(s)
    x = np.zeros(n_of(d))
    r = np.random.default_rng(s)
    for k in range(n):
        at = 0.08 + k * every + r.uniform(-0.03, 0.03)
        heel = lowpass(noise(0.09), 260) * env_exp(0.09, 0.025, 0.002) * 1.4
        scuff = np.pad(highpass(noise(0.07), 1800) * env_exp(0.07, 0.02, 0.004) * 0.25, (0, n_of(0.09) - n_of(0.07)))
        x = place(x, heel + scuff, at)[: n_of(d)]
        if crunch:
            x = place(x, grains(0.25, 140, 2600, 1.4, 0.0015, s * 10 + k) * crunch, at + 0.01)[: n_of(d)]
    return x


@item("foley", "steps-concrete", "footsteps on a concrete floor, small room (3 s)", "foley footsteps concrete inside")
def _():
    return widen(reverb(steps(3.0, 5, 0.52, 0.0, 61), 0.25, 0.9, 0.6))


@item("foley", "steps-debris", "careful footsteps over ash and broken glass outside (3 s)", "foley footsteps debris outside crunch")
def _():
    return widen(reverb(steps(3.0, 4, 0.68, 1.4, 62), 0.15, 1.6, 0.7))


@item("foley", "tape-rip", "duct tape pulled off the roll and slapped on (1.2 s)", "foley tape duct seal")
def _():
    d = 1.2
    t = np.arange(n_of(d)) / SR
    rip = grains(0.75, lambda tt: 300 + 500 * tt, 2400, 1.6, 0.0012, 71) * 2.2
    slap = lowpass(noise(0.08), 900) * env_exp(0.08, 0.02, 0.001) * 1.2
    x = np.zeros(n_of(d))
    x[: len(rip)] += rip * np.linspace(0.6, 1, len(rip))
    return widen(place(x, slap, 0.85)[: n_of(d)])


@item("foley", "breath-mask", "breathing through a respirator: muffled inhale, valve, exhale (4 s)", "foley breath mask respirator")
def _():
    seed(81)
    d = 4.0
    inh = bandpass(pink(1.3), 900, 1.4) * env_bell(1.3, 0.6, 1.6) * 1.2
    exh = bandpass(pink(1.4), 600, 1.2) * env_bell(1.4, 0.35, 1.5) * 1.0
    valve = highpass(noise(0.02), 1500) * env_exp(0.02, 0.004, 0.0005) * 0.6
    x = np.zeros(n_of(d))
    x = place(x, inh, 0.1)[: n_of(d)]
    x = place(x, valve, 1.45)[: n_of(d)]
    x = place(x, exh, 1.6)[: n_of(d)]
    return widen(lowpass(x, 2200))


@item("foley", "can-open", "opening a food can: pull-tab crack and short hiss (0.9 s)", "foley can food open")
def _():
    seed(91)
    d = 0.9
    crack = bandpass(noise(0.03), 2200, 1.2) * env_exp(0.03, 0.006, 0.0005) * 1.2
    hiss = highpass(noise(0.35), 3000) * env_exp(0.35, 0.12, 0.003) * 0.35
    tear = grains(0.3, 180, 1800, 1.2, 0.001, 92) * 1.2
    x = np.zeros(n_of(d))
    x = place(x, crack, 0.05)[: n_of(d)]
    x = place(x, hiss, 0.07)[: n_of(d)]
    x = place(x, tear, 0.3)[: n_of(d)]
    return widen(x)


@item("foley", "water-pour", "pouring water into a pot (2 s)", "foley water pour")
def _():
    seed(93)
    d = 2.0
    t = np.arange(n_of(d)) / SR
    stream = bandpass(noise(d), 1100, 1.6) * env_bell(d, 0.5, 1.2) * 0.6
    bub = grains(d, 60, 900, 1.0, 0.004, 94) * 0.9 * env_bell(d, 0.5, 1.2)
    return widen(stream * (0.8 + 0.2 * np.sin(2 * np.pi * 7 * t)) + bub)


@item("foley", "switch-click", "flashlight / lantern switch click (0.25 s)", "foley switch click lantern")
def _():
    seed(95)
    x = bandpass(noise(0.04), 2600, 1.0) * env_exp(0.04, 0.004, 0.0003) + lowpass(noise(0.04), 500) * env_exp(0.04, 0.01, 0.001) * 0.6
    return widen(np.concatenate([x, np.zeros(n_of(0.22))]))


@item("riser", "dread-rise", "dark tension swell: low cluster rising into silence (4 s)", "riser tension dread dark")
def _():
    seed(96)
    d = 4.0
    t = np.arange(n_of(d)) / SR
    drone = sum(lowpass(saw(f * (1 + 0.15 * (t / d) ** 2), d), 500) * 0.12 for f in (55, 58.3, 82.4))
    air = svf(pink(d), log_sweep(200, 2400, d, 1.6), q=1.2, mode="band") * 0.5
    x = (drone + air) * (t / d) ** 1.8
    return widen(reverb(x, 0.25, 2.0, 0.6))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    if a.list:
        for e in EXTRA:
            print(f"{e['category']:9} {e['name']:20} {e['desc']}")
        return
    ix = L.load_index()
    have = {e["id"]: e for e in ix}
    for e in EXTRA:
        x = np.asarray(e["fn"](), dtype=np.float64)
        x = to_stereo(x)
        rel = f"sfx/{e['category']}/{e['name']}.wav"
        dur = write_wav(L.SFX.parent / rel, x, peak_db=-1.0)
        y = L.read_wav(L.SFX.parent / rel)
        # match the library's loudness for that category where one exists
        meta = dict(id=e["name"], file=rel, category=e["category"], desc=e["desc"], tags=e["tags"], dur=round(dur, 3),
                    peak=round(L.peak_time(y), 3), source="gen")
        if e["name"] in have:
            have[e["name"]].clear()
            have[e["name"]].update(meta)
        else:
            ix.append(meta)
        print(f"  {e['category']:9} {e['name']:20} {dur:5.2f}s  peak {meta['peak']:.2f}s")
    L.save_index(ix)
    L.write_docs(ix)
    print(f"{len(EXTRA)} extra sounds")


if __name__ == "__main__":
    main()
