"""Music bed of the «Классика» style (28.10.2026): one calm base track under the whole reel and a tense layer that rises
over a few seconds when the story turns dark (disaster, storm, failure) and goes back down when it resolves.
The user's reference is `output/sposobnosti-{1,2}-v4-story.mp4`: ambient-air under everything, dark-cinematic up to
about half the level of the base in the tense part.

The engine then plays the bed as ordinary music (one track, ducked under the voice):
    "music": {"src": "projects/<id>/music-bed.wav", "volume": 0.14, "duck": 0.5, "fadeOut": 0.5}

    python music_bed.py --dur 59.3 --up 5:10 --down 35:42 --rest 0.13 --out <engine>/public/projects/<id>/music-bed.wav
    python music_bed.py --dur 62.3 --up 38:45 --peak 0.45 --out ...      (part 1: tension only at the end)

--up A:B   the layer rises from rest to peak between A and B seconds (linear); --down A:B falls back to rest.
Several --up/--down windows are fine (they are applied in time order). Tracks shorter than the reel loop.
Paths of --base/--layer are files or ids of the engine's music beds (ambient-air, dark-cinematic, ...).
"""
import argparse
import os
import subprocess
import wave

import numpy as np

SR = 48000
HERE = os.path.dirname(os.path.abspath(__file__))
MUSIC_DIRS = [os.environ.get('KINEMA_MUSIC', ''),
              os.path.join(HERE, '..', '..', 'engine', 'public', 'music'),                       # blender-kit inside reel-studio (ПК)
              os.path.join(HERE, '..', '..', 'KINEMA', 'skills', 'reel-studio', 'engine', 'public', 'music'),  # <id>/tools (ПК)
              os.path.join(HERE, '..', '..', '..', 'kinema', 'skills', 'reel-studio', 'engine', 'public', 'music'),
              os.path.join(HERE, '..', '..', '..', '..', 'skills', 'reel-studio', 'engine', 'public', 'music')]


def track(name):
    if os.path.exists(name):
        return name
    for d in MUSIC_DIRS:
        p = os.path.join(d, name if name.endswith('.m4a') else name + '.m4a')
        if d and os.path.exists(p):
            return p
    raise SystemExit(f'music track not found: {name} (set KINEMA_MUSIC to engine/public/music)')


def load(path, n):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-ac', '2', '-ar', str(SR), '-f', 'f32le', '-'],
                         capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.float32).reshape(-1, 2).astype(np.float64)
    if len(x) < n:
        x = np.concatenate([x] * int(np.ceil(n / len(x))))
    return x[:n]


def envelope(n, ups, downs, rest, peak):
    t = np.arange(n) / SR
    env = np.full(n, rest)
    for a, b, lo, hi in sorted([(a, b, rest, peak) for a, b in ups] + [(a, b, peak, rest) for a, b in downs]):
        w = np.clip((t - a) / max(1e-3, b - a), 0.0, 1.0)
        m = t >= a
        env[m] = lo + (hi - lo) * w[m]
    return env


def window(s):
    a, b = s.split(':')
    return float(a), float(b)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--base', default='ambient-air')
    ap.add_argument('--layer', default='dark-cinematic')
    ap.add_argument('--dur', type=float, required=True, help='reel length, s')
    ap.add_argument('--up', type=window, action='append', default=[])
    ap.add_argument('--down', type=window, action='append', default=[])
    ap.add_argument('--peak', type=float, default=0.54, help='layer level at its peak, relative to the base')
    ap.add_argument('--rest', type=float, default=0.0, help='layer level outside the tense part')
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    n = int(a.dur * SR)
    base = load(track(a.base), n)
    layer = load(track(a.layer), n)
    env = envelope(n, a.up, a.down, a.rest, a.peak)
    mix = base + layer * env[:, None]
    mix /= max(1.0, np.abs(mix).max() / 0.98)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with wave.open(a.out, 'wb') as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(mix, -1, 1) * 32767).astype('<i2').tobytes())
    print(f'music bed {a.dur:.1f}s -> {a.out} (base {a.base}, layer {a.layer} up {a.up} down {a.down} peak {a.peak})')


if __name__ == '__main__':
    main()
