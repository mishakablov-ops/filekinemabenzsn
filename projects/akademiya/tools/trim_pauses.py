"""Shorten word gaps longer than MAX to KEEP by cutting the middle of the silence (15 ms crossfade, no stretching).
Shifts every start/end in words.json (words and cards) and the duration exactly by the removed time.
    python3 trim_pauses.py <project dir> [max=0.8] [keep=0.5]
"""
import json
import sys
import wave

import numpy as np

pdir = sys.argv[1]
MAX = float(sys.argv[2]) if len(sys.argv) > 2 else 0.8
KEEP = float(sys.argv[3]) if len(sys.argv) > 3 else 0.5
d = json.load(open(f'{pdir}/words.json', encoding='utf-8'))
w = wave.open(f'{pdir}/voice.wav')
sr, ch, sw, n = w.getframerate(), w.getnchannels(), w.getsampwidth(), w.getnframes()
assert sw == 2
x = np.frombuffer(w.readframes(n), dtype=np.int16).astype(np.float32).reshape(-1, ch)
w.close()

cuts = []                                      # (cut start s, cut end s) inside the silence
ws = d['words']
for a, b in zip(ws, ws[1:]):
    g = b['start'] - a['end']
    if g > MAX:
        mid = (a['end'] + b['start']) / 2
        cuts.append((mid - (g - KEEP) / 2, mid + (g - KEEP) / 2))
        print(f'{a["end"]:.2f} gap {g:.2f} -> {KEEP}  {a["text"]} | {b["text"]}')

xf = int(0.015 * sr)
out, pos = [], 0
for c0, c1 in cuts:
    i0, i1 = int(c0 * sr), int(c1 * sr)
    seg = x[pos:i0 + xf].copy()
    if out:
        ramp = np.linspace(0, 1, xf)[:, None]
        out[-1][-xf:] = out[-1][-xf:] * (1 - ramp) + seg[:xf] * ramp
        seg = seg[xf:]
    out.append(seg)
    pos = i1
tail = x[pos:].copy()
if out:
    ramp = np.linspace(0, 1, xf)[:, None]
    out[-1][-xf:] = out[-1][-xf:] * (1 - ramp) + tail[:xf] * ramp
    tail = tail[xf:]
out.append(tail)
y = np.concatenate(out)


def shift(t):
    s = 0.0
    for c0, c1 in cuts:
        if t >= c1:
            s += (c1 - c0)
    return round(t - s, 3)


for it in d['words'] + d['cards']:
    it['start'], it['end'] = shift(it['start']), shift(it['end'])
d['duration'] = round(len(y) / sr, 3)
with wave.open(f'{pdir}/voice.wav', 'wb') as o:
    o.setnchannels(ch)
    o.setsampwidth(2)
    o.setframerate(sr)
    o.writeframes(np.clip(y, -32768, 32767).astype(np.int16).tobytes())
json.dump(d, open(f'{pdir}/words.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('duration', d['duration'], 'removed', round(sum(c1 - c0 for c0, c1 in cuts), 3))
