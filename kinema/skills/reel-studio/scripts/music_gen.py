"""Procedural music beds for reels (royalty-free by construction).

Usage: python music_gen.py [out_dir]   (default ../engine/public/music)
For every track writes <id>.wav and <id>.beats.json:
  {bpm, beatSec, beats[], bars[], sections:[{name,start,end,energy}], drops[]}
Promo mode cuts on `beats`/`bars`, lands title slams on `drops`.
These are clean, unobtrusive beds. For a hero promo, a licensed track + beats.py
is still the stronger option; these are the always-available fallback.
"""
from __future__ import annotations

import json
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from dsp import (SR, env_adsr, env_exp, fm_bell, highpass, karplus, lowpass, n_of, noise, note_hz, pink,  # noqa: E402
                 reverb, saw, seed, sine, softclip, svf, t_axis, taper, to_stereo, tri, widen, write_wav)

# console: always UTF-8 (Windows defaults to cp1251)
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:
        pass

NOTE = {"C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5, "F#": 6, "Gb": 6, "G": 7,
        "G#": 8, "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11}
QUAL = {"": [0, 4, 7], "m": [0, 3, 7], "maj7": [0, 4, 7, 11], "m7": [0, 3, 7, 10], "7": [0, 4, 7, 10],
        "m9": [0, 3, 7, 10, 14], "maj9": [0, 4, 7, 11, 14], "9": [0, 4, 7, 10, 14], "sus2": [0, 2, 7],
        "sus4": [0, 5, 7], "6": [0, 4, 7, 9], "add9": [0, 4, 7, 14], "13": [0, 4, 10, 14, 21]}


def chord_midis(sym: str, octave: int = 4) -> list[int]:
    root = sym[:2] if len(sym) > 1 and sym[1] in "#b" else sym[:1]
    q = sym[len(root):]
    base = 12 * (octave + 1) + NOTE[root]
    return [base + i for i in QUAL[q]]


def mhz(m: float) -> float:
    return 440.0 * 2 ** ((m - 69) / 12)


# ------------------------------------------------------------------ instruments
@lru_cache(maxsize=None)
def kick(punch: float = 1.0, dur: float = 0.45) -> np.ndarray:
    t = t_axis(dur)
    f = 45 + 110 * np.exp(-t / 0.035) * punch
    x = sine(f, dur) * np.exp(-t / 0.16)
    x += highpass(noise(dur), 2000) * np.exp(-t / 0.003) * 0.25
    return taper(softclip(x, 1.6), 0.2)


@lru_cache(maxsize=None)
def snare(dur: float = 0.3) -> np.ndarray:
    t = t_axis(dur)
    body = sine(185, dur) * np.exp(-t / 0.05) * 0.6
    nz = highpass(lowpass(noise(dur), 9000), 1200) * np.exp(-t / 0.09)
    return taper(body + nz * 0.8, 0.2)


@lru_cache(maxsize=None)
def clap(dur: float = 0.35) -> np.ndarray:
    out = np.zeros(n_of(dur))
    for k, off in enumerate([0, 0.011, 0.022]):
        nz = highpass(noise(dur), 900) * env_exp(dur, 0.012 if k < 2 else 0.11, 0.001)
        s = n_of(off)
        out[s:] += nz[: len(out) - s]
    return taper(lowpass(out, 7000), 0.2)


@lru_cache(maxsize=None)
def hat(open_: bool = False) -> np.ndarray:
    dur = 0.35 if open_ else 0.06
    t = t_axis(dur)
    x = highpass(noise(dur), 7000) * np.exp(-t / (0.12 if open_ else 0.014))
    return taper(x, 0.3)


@lru_cache(maxsize=None)
def rim() -> np.ndarray:
    t = t_axis(0.08)
    return (sine(1700, 0.08) * 0.5 + highpass(noise(0.08), 3000) * 0.5) * np.exp(-t / 0.012)


@lru_cache(maxsize=None)
def pluck(midi: int, dur: float = 0.9, bright: float = 0.55) -> np.ndarray:
    return taper(karplus(mhz(midi), dur, bright, 0.994), 0.25)


@lru_cache(maxsize=None)
def epiano(midi: int, dur: float = 1.6) -> np.ndarray:
    f = mhz(midi)
    x = fm_bell(f, dur, ratio=1.0, index=1.4, decay=dur * 0.45)
    x += 0.15 * fm_bell(f * 14, dur, 1.0, 0.3, 0.06)
    return taper(x, 0.2)


@lru_cache(maxsize=None)
def pad_note(midi: int, dur: float, cutoff: float = 1800, soft: bool = True) -> np.ndarray:
    f = mhz(midi)
    x = (saw(f, dur) + saw(f * 1.006, dur) + saw(f * 0.995, dur)) / 3
    if soft:
        x = 0.6 * x + 0.4 * tri(f, dur)
    x = lowpass(x, cutoff, 2)
    return x * env_adsr(dur, min(0.6, dur * 0.3), 0.3, 0.8, min(0.8, dur * 0.3))


@lru_cache(maxsize=None)
def bass_note(midi: int, dur: float, kind: str = "sub") -> np.ndarray:
    f = mhz(midi)
    if kind == "sub":
        x = sine(f, dur) + 0.25 * tri(f * 2, dur)
    elif kind == "808":
        t = t_axis(dur)
        x = softclip(sine(f * (1 + 0.5 * np.exp(-t / 0.03)), dur) * 1.4, 1.8) * np.exp(-t / max(dur * 0.7, 0.2))
        return taper(x, 0.15)
    else:  # saw bass
        x = lowpass(saw(f, dur) * 0.7 + sine(f, dur) * 0.5, 700)
    return taper(x * env_adsr(dur, 0.005, 0.08, 0.85, 0.05), 0.1)


# ------------------------------------------------------------------ sequencer
class Track:
    def __init__(self, bpm: float, bars: int):
        self.bpm = bpm
        self.beat = 60.0 / bpm
        self.bar = self.beat * 4
        self.bars = bars
        self.len = self.bar * bars + 3.0
        self.buses: dict[str, np.ndarray] = {}

    def bus(self, name: str) -> np.ndarray:
        if name not in self.buses:
            self.buses[name] = np.zeros(n_of(self.len))
        return self.buses[name]

    def hit(self, name: str, sample: np.ndarray, t: float, gain: float = 1.0) -> None:
        b = self.bus(name)
        s = n_of(t)
        if s >= len(b):
            return
        e = min(len(b), s + len(sample))
        b[s:e] += sample[: e - s] * gain

    def at(self, bar: float, beat: float = 0.0) -> float:
        return bar * self.bar + beat * self.beat

    def sidechain(self, name: str, depth: float = 0.5, release: float = 0.22, bars: range | None = None) -> None:
        b = self.bus(name)
        env = np.ones(len(b))
        rng_bars = bars or range(self.bars)
        rel = n_of(release)
        curve = 1 - depth * np.exp(-np.linspace(0, 4, rel))
        for br in rng_bars:
            for bt in range(4):
                s = n_of(self.at(br, bt))
                e = min(len(env), s + rel)
                env[s:e] = np.minimum(env[s:e], curve[: e - s])
        b *= env

    def mix(self, gains: dict[str, float], fx: dict[str, dict] | None = None) -> np.ndarray:
        fx = fx or {}
        out = np.zeros((n_of(self.len), 2))
        for name, b in self.buses.items():
            g = gains.get(name, 1.0)
            x = b * g
            f = fx.get(name, {})
            if f.get("hp"):
                x = highpass(x, f["hp"])
            if f.get("lp"):
                x = lowpass(x, f["lp"])
            st = widen(x, f.get("width", 0)) if f.get("width") else to_stereo(x)
            if f.get("verb"):
                st = reverb(st, f["verb"], f.get("rt", 1.8), tail=False)
            out[: len(st)] += st[: len(out)]
        out = softclip(out * 0.9, 1.15)
        tail = n_of(2.5)
        out[-tail:] *= np.linspace(1, 0, tail)[:, None] ** 2
        return out

    def grid(self, sections: list[tuple[str, int, int, float]], drops: list[int]) -> dict:
        return dict(
            bpm=self.bpm, beatSec=round(self.beat, 5), barSec=round(self.bar, 5),
            beats=[round(self.at(0, i), 4) for i in range(self.bars * 4)],
            bars=[round(self.at(i), 4) for i in range(self.bars)],
            sections=[dict(name=n, start=round(self.at(a), 3), end=round(self.at(b), 3), energy=e) for n, a, b, e in sections],
            drops=[round(self.at(d), 3) for d in drops],
            duration=round(self.bar * self.bars + 2.5, 3),
        )


def play_chords(tr: Track, prog: list[str], bars: range, octave=4, bus="pad", cutoff=1800, gain=0.22, bars_per_chord=1):
    for br in bars:
        sym = prog[(br // bars_per_chord) % len(prog)]
        if br % bars_per_chord:
            continue
        dur = tr.bar * bars_per_chord + 0.25
        for m in chord_midis(sym, octave):
            tr.hit(bus, pad_note(m, round(dur, 3), cutoff), tr.at(br), gain)


def play_bass(tr: Track, prog: list[str], bars: range, pattern: list[tuple[float, float]], kind="sub", octave=2, gain=0.5, bars_per_chord=1):
    for br in bars:
        sym = prog[(br // bars_per_chord) % len(prog)]
        root = chord_midis(sym, octave)[0]
        for beat, length in pattern:
            tr.hit("bass", bass_note(root, round(length * tr.beat, 3), kind), tr.at(br, beat), gain)


def play_arp(tr: Track, prog: list[str], bars: range, steps: list[int], div=0.5, octave=5, bus="arp", gain=0.22,
             inst="pluck", bars_per_chord=1, bright=0.55):
    for br in bars:
        notes = chord_midis(prog[(br // bars_per_chord) % len(prog)], octave)
        n_steps = int(4 / div)
        for s in range(n_steps):
            idx = steps[s % len(steps)]
            if idx < 0:
                continue
            m = notes[idx % len(notes)] + 12 * (idx // len(notes))
            smp = pluck(m, 0.9, bright) if inst == "pluck" else epiano(m, 1.2)
            tr.hit(bus, smp, tr.at(br, s * div), gain * (1.0 if s % 2 == 0 else 0.75))


def drums(tr: Track, bars: range, kick_pat=(0, 1, 2, 3), snare_pat=(1, 3), hat_div=0.5, clap_=False, open_hat=False,
          kick_gain=0.9, swing=0.0, hat_gain=0.25):
    for br in bars:
        for b in kick_pat:
            tr.hit("kick", kick(), tr.at(br, b), kick_gain)
        for b in snare_pat:
            tr.hit("snare", clap() if clap_ else snare(), tr.at(br, b), 0.55)
        n = int(4 / hat_div)
        for s in range(n):
            sw = swing * tr.beat * hat_div if s % 2 else 0
            tr.hit("hat", hat(), tr.at(br, s * hat_div) + sw, hat_gain * (1 if s % 2 == 0 else 0.6))
        if open_hat:
            for b in (0.5, 1.5, 2.5, 3.5):
                tr.hit("hat", hat(True), tr.at(br, b), 0.18)


def fill_riser(tr: Track, end_bar: int, bars_len: int = 2, gain: float = 0.25) -> None:
    dur = tr.bar * bars_len
    nz = noise(dur) * 0.5 + pink(dur) * 0.5
    sw = np.geomspace(300, 9000, len(nz))
    x = svf(nz, sw, q=1.0, mode="band") * np.linspace(0, 1, len(nz)) ** 2
    tr.hit("fx", x, tr.at(end_bar - bars_len), gain)


def texture(tr: Track, kind: str = "vinyl", gain: float = 0.04) -> None:
    dur = tr.len
    if kind == "vinyl":
        x = lowpass(highpass(pink(dur), 800), 6000) * 0.5
        crackle = (np.random.default_rng(3).random(n_of(dur)) > 0.9993) * np.random.default_rng(4).uniform(-1, 1, n_of(dur))
        x = x + crackle * 2
    else:
        x = lowpass(pink(dur), 1200)
    tr.hit("tex", x, 0, gain)


# ------------------------------------------------------------------ tracks
def t_pulse_tech():
    seed(11)
    tr = Track(110, 32)
    prog = ["Am", "F", "C", "G"]
    play_chords(tr, prog, range(0, 32), 4, cutoff=1400, gain=0.16)
    play_arp(tr, prog, range(4, 28), [0, 2, 1, 3, 2, 0, 3, 1], 0.5, 5, gain=0.2, bright=0.45)
    play_bass(tr, prog, range(8, 28), [(0, 0.9), (1.5, 0.4), (2, 0.9), (3.5, 0.4)], "sub", 2, 0.55)
    drums(tr, range(8, 15), kick_pat=(0, 2), snare_pat=(), hat_div=0.5)
    drums(tr, range(16, 28), kick_pat=(0, 1, 2, 3), snare_pat=(1, 3), hat_div=0.25, clap_=True, hat_gain=0.18)
    fill_riser(tr, 16, 2)
    tr.sidechain("pad", 0.45, bars=range(16, 28))
    mix = tr.mix({"kick": 0.9, "snare": 0.45, "hat": 0.5, "bass": 0.8, "pad": 0.9, "arp": 0.85, "fx": 0.6},
                 {"pad": dict(verb=0.4, width=14), "arp": dict(verb=0.35, width=9, hp=200), "hat": dict(width=6), "snare": dict(verb=0.2)})
    return mix, tr.grid([("intro", 0, 4, 0.2), ("build", 4, 8, 0.4), ("groove", 8, 16, 0.6), ("main", 16, 28, 0.9), ("outro", 28, 32, 0.3)], [16])


def t_lofi_warm():
    seed(12)
    tr = Track(84, 24)
    prog = ["Dm9", "G13", "Cmaj9", "Am7"]
    for br in range(24):
        for m in chord_midis(prog[br % 4], 3):
            tr.hit("keys", epiano(m, round(tr.bar + 0.4, 3)), tr.at(br), 0.13)
            tr.hit("keys", epiano(m + 12, 0.8), tr.at(br, 2.5), 0.05)
    play_bass(tr, prog, range(4, 22), [(0, 1.4), (2.5, 1.2)], "sub", 2, 0.5)
    drums(tr, range(4, 22), kick_pat=(0, 2.5), snare_pat=(1, 3), hat_div=0.5, swing=0.28, kick_gain=0.75, hat_gain=0.18)
    texture(tr, "vinyl", 0.05)
    mix = tr.mix({"keys": 1.0, "bass": 0.75, "kick": 0.8, "snare": 0.4, "hat": 0.45, "tex": 0.6},
                 {"keys": dict(verb=0.3, width=10, lp=5500), "snare": dict(lp=5000, verb=0.15), "hat": dict(lp=8000)})
    return mix, tr.grid([("intro", 0, 4, 0.2), ("main", 4, 22, 0.6), ("outro", 22, 24, 0.2)], [4])


def t_ambient_air():
    seed(13)
    tr = Track(70, 20)
    prog = ["Cmaj7", "Am9", "Fmaj7", "G6"]
    play_chords(tr, prog, range(20), 4, cutoff=1200, gain=0.17, bars_per_chord=2)
    play_chords(tr, prog, range(20), 3, bus="low", cutoff=600, gain=0.12, bars_per_chord=2)
    rng = np.random.default_rng(5)
    for br in range(2, 18):
        notes = chord_midis(prog[(br // 2) % 4], 6)
        for k in range(3):
            tr.hit("bell", fm_bell(mhz(int(rng.choice(notes))), 2.0, 3.5, 0.8, 0.7), tr.at(br, float(rng.choice([0, 1, 1.5, 2, 3]))), 0.06)
    mix = tr.mix({"pad": 1.0, "low": 0.8, "bell": 1.0},
                 {"pad": dict(verb=0.6, rt=3.0, width=18), "bell": dict(verb=0.7, rt=3.5, width=12), "low": dict(lp=900)})
    return mix, tr.grid([("swell", 0, 4, 0.2), ("float", 4, 16, 0.4), ("fade", 16, 20, 0.2)], [4])


def t_drive_promo():
    seed(14)
    tr = Track(124, 36)
    prog = ["F#m", "D", "A", "E"]
    play_chords(tr, prog, range(0, 36), 4, cutoff=2200, gain=0.14)
    play_arp(tr, prog, range(8, 32), [0, 1, 2, 3, 2, 1, 0, 2], 0.25, 5, gain=0.13, bright=0.7)
    play_bass(tr, prog, range(4, 32), [(0.5, 0.45), (1.5, 0.45), (2.5, 0.45), (3.5, 0.45)], "saw", 2, 0.45)
    drums(tr, range(4, 8), kick_pat=(0, 1, 2, 3), snare_pat=(), hat_div=0.5)
    drums(tr, range(8, 16), kick_pat=(0, 1, 2, 3), snare_pat=(1, 3), hat_div=0.5, clap_=True, open_hat=True)
    drums(tr, range(17, 32), kick_pat=(0, 1, 2, 3), snare_pat=(1, 3), hat_div=0.25, clap_=True, open_hat=True, hat_gain=0.16)
    fill_riser(tr, 17, 1, 0.3)
    fill_riser(tr, 8, 2, 0.25)
    tr.sidechain("pad", 0.6)
    tr.sidechain("bass", 0.3, 0.12)
    mix = tr.mix({"kick": 1.0, "snare": 0.5, "hat": 0.5, "bass": 0.75, "pad": 0.9, "arp": 0.8, "fx": 0.7},
                 {"pad": dict(verb=0.35, width=16), "arp": dict(verb=0.3, width=10, hp=300), "snare": dict(verb=0.18, width=5)})
    return mix, tr.grid([("intro", 0, 4, 0.3), ("pump", 4, 8, 0.5), ("verse", 8, 16, 0.7), ("break", 16, 17, 0.3),
                         ("drop", 17, 32, 1.0), ("outro", 32, 36, 0.3)], [8, 17])


def t_dark_cinematic():
    seed(15)
    tr = Track(90, 24)
    prog = ["Dm", "Bb", "Gm", "A"]
    play_chords(tr, prog, range(24), 3, cutoff=900, gain=0.18, bars_per_chord=2)
    for br in range(4, 22):
        for b in range(4):
            tr.hit("pulse", bass_note(chord_midis(prog[(br // 2) % 4], 1)[0], round(tr.beat * 0.9, 3), "saw"), tr.at(br, b), 0.35)
    for br in (8, 12, 16, 20):
        tr.hit("boom", kick(1.6, 1.2), tr.at(br), 0.9)
    for br in range(12, 22):
        tr.hit("tick", hat(), tr.at(br, 0.5), 0.2)
        tr.hit("tick", hat(), tr.at(br, 2.5), 0.2)
    fill_riser(tr, 12, 2, 0.25)
    mix = tr.mix({"pad": 1.0, "pulse": 0.8, "boom": 1.0, "tick": 0.6, "fx": 0.8},
                 {"pad": dict(verb=0.5, rt=3.0, width=16), "boom": dict(verb=0.4, rt=2.5), "pulse": dict(lp=1200)})
    return mix, tr.grid([("tension", 0, 4, 0.3), ("pulse", 4, 12, 0.6), ("rise", 12, 20, 0.85), ("end", 20, 24, 0.3)], [8, 12])


def t_bright_pop():
    seed(16)
    tr = Track(118, 32)
    prog = ["C", "G", "Am", "F"]
    play_chords(tr, prog, range(32), 4, cutoff=2600, gain=0.13)
    play_arp(tr, prog, range(4, 30), [0, 2, 3, 2, 1, 2, 3, 4], 0.5, 5, gain=0.22, bright=0.8)
    play_bass(tr, prog, range(8, 30), [(0, 0.7), (1, 0.4), (1.5, 0.4), (2, 0.7), (3, 0.4), (3.5, 0.4)], "sub", 2, 0.5)
    drums(tr, range(8, 30), kick_pat=(0, 2), snare_pat=(1, 3), hat_div=0.5, clap_=True, kick_gain=0.85)
    for br in range(16, 30):
        tr.hit("hat", rim(), tr.at(br, 3.75), 0.25)
    fill_riser(tr, 16, 1, 0.2)
    tr.sidechain("pad", 0.35)
    mix = tr.mix({"kick": 0.9, "snare": 0.45, "hat": 0.5, "bass": 0.75, "pad": 0.85, "arp": 0.9, "fx": 0.6},
                 {"pad": dict(verb=0.3, width=14), "arp": dict(verb=0.3, width=10, hp=250)})
    return mix, tr.grid([("intro", 0, 8, 0.4), ("verse", 8, 16, 0.7), ("chorus", 16, 30, 0.9), ("outro", 30, 32, 0.3)], [8, 16])


def t_minimal_keys():
    seed(17)
    tr = Track(96, 24)
    prog = ["Ebmaj7", "Cm7", "Abmaj7", "Bb6"]
    play_arp(tr, prog, range(24), [0, 2, 1, 3, 0, 2, 4, 3], 0.5, 4, bus="keys", gain=0.14, inst="epiano")
    play_chords(tr, prog, range(4, 22), 3, cutoff=800, gain=0.12)
    for br in range(8, 22):
        tr.hit("perc", rim(), tr.at(br, 1), 0.18)
        tr.hit("perc", rim(), tr.at(br, 3), 0.18)
        tr.hit("kick", kick(0.6), tr.at(br, 0), 0.55)
    mix = tr.mix({"keys": 1.0, "pad": 0.8, "perc": 0.6, "kick": 0.7},
                 {"keys": dict(verb=0.35, width=12), "pad": dict(verb=0.4, width=14), "perc": dict(verb=0.25)})
    return mix, tr.grid([("intro", 0, 8, 0.3), ("main", 8, 22, 0.55), ("outro", 22, 24, 0.2)], [8])


def t_trap_hype():
    seed(18)
    tr = Track(140, 32)
    prog = ["Cm", "Ab", "Fm", "G"]
    play_chords(tr, prog, range(32), 4, cutoff=1600, gain=0.13, bars_per_chord=2)
    play_arp(tr, prog, range(8, 30), [0, -1, 2, -1, 1, -1, 3, 2], 0.5, 5, gain=0.18, bright=0.65, bars_per_chord=2)
    for br in range(8, 30):
        root = chord_midis(prog[(br // 2) % 4], 1)[0]
        for b, ln in ((0, 1.5), (2.5, 1.0)):
            tr.hit("bass", bass_note(root, round(ln * tr.beat, 3), "808"), tr.at(br, b), 0.6)
        tr.hit("kick", kick(1.2), tr.at(br, 0), 0.9)
        tr.hit("kick", kick(1.2), tr.at(br, 2.5), 0.8)
        tr.hit("snare", clap(), tr.at(br, 2), 0.6)
        rolls = 0.25 if br % 4 != 3 else 0.125
        for s in range(int(4 / rolls)):
            tr.hit("hat", hat(), tr.at(br, s * rolls), 0.16 if s % 2 else 0.24)
    fill_riser(tr, 8, 2, 0.3)
    fill_riser(tr, 20, 1, 0.25)
    mix = tr.mix({"kick": 1.0, "snare": 0.55, "hat": 0.5, "bass": 0.85, "pad": 0.8, "arp": 0.8, "fx": 0.7},
                 {"pad": dict(verb=0.4, width=16), "arp": dict(verb=0.3, width=10, hp=300), "snare": dict(verb=0.15)})
    return mix, tr.grid([("intro", 0, 8, 0.3), ("drop", 8, 20, 1.0), ("switch", 20, 30, 0.9), ("outro", 30, 32, 0.3)], [8, 20])


TRACKS = {
    "pulse-tech": (t_pulse_tech, "110 bpm, minor, plucky arps + pumping pads. Default for tech explainers."),
    "lofi-warm": (t_lofi_warm, "84 bpm swing, e-piano jazz chords, vinyl. Calm, friendly, cozy products."),
    "ambient-air": (t_ambient_air, "no drums, floating pads + bells. Under voice on light/sky themes."),
    "drive-promo": (t_drive_promo, "124 bpm four-on-floor, builds to a drop at bar 17. Energetic promo."),
    "dark-cinematic": (t_dark_cinematic, "90 bpm pulse, minor drone, booms. Problem statements, security, mystery."),
    "bright-pop": (t_bright_pop, "118 bpm major, happy plucks + claps. Consumer apps, playful."),
    "minimal-keys": (t_minimal_keys, "96 bpm e-piano arps, rim clicks. Thoughtful, product walkthroughs."),
    "trap-hype": (t_trap_hype, "140 bpm half-time 808 + hat rolls. Aggressive typography promos."),
}


def main(out: Path, only: list[str] | None = None) -> None:
    out.mkdir(parents=True, exist_ok=True)
    index = []
    for tid, (fn, desc) in TRACKS.items():
        if only and tid not in only:
            continue
        mix, grid = fn()
        dur = write_wav(out / f"{tid}.wav", mix, peak_db=-1.0)
        # loudness-normalise to -16 LUFS and store as AAC (keeps the render bundle small)
        from loudnorm import normalize
        tmp = out / f"{tid}.norm.wav"
        normalize(str(out / f"{tid}.wav"), str(tmp), -16.0, -1.5)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(tmp), "-c:a", "aac", "-b:a", "256k", str(out / f"{tid}.m4a")], check=True)
        tmp.unlink()
        (out / f"{tid}.wav").unlink()
        grid["desc"] = desc
        (out / f"{tid}.beats.json").write_text(json.dumps(grid), encoding="utf-8")
        index.append(dict(id=tid, file=f"music/{tid}.m4a", beats=f"music/{tid}.beats.json", bpm=grid["bpm"], dur=round(dur, 2), desc=desc))
        print(f"{tid}: {dur:.1f}s @ {grid['bpm']} bpm")
    if not only:
        (out / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    default = Path(__file__).resolve().parent.parent / "engine" / "public" / "music"
    args = sys.argv[1:]
    main(Path(args[0]) if args and not args[0].startswith("-") else default, [a[2:] for a in args if a.startswith("--")] or None)
