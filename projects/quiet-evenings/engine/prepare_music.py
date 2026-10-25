"""Arrange the supplied music for this 40-second cut, preserving its original pitch and tempo."""
from pathlib import Path
import json
import shutil
import subprocess
import sys
import wave

import numpy as np

P = Path(__file__).resolve().parent
ENGINE = P.parents[2]
RS = ENGINE.parent
sys.path.insert(0, str(RS / 'scripts'))
from loudnorm import normalize

SOURCE = Path(r'C:\Users\Gigabyte\Downloads\ssstik.io_1792530637838.mp3')
SR = 48000
TARGET = SR * 40
FF = str(RS / '.runtime/bin/ffmpeg.exe')
shutil.copy2(SOURCE, P / 'success-user-original.mp3')
raw = subprocess.run([FF, '-v', 'error', '-i', str(SOURCE), '-ar', str(SR), '-ac', '2', '-f', 'f32le', 'pipe:1'], capture_output=True, check=True).stdout
x = np.frombuffer(raw, dtype=np.float32).reshape(-1, 2)

# Match repeated waveform passages on the beat grid; never restart the quiet intro at the end.
bpm, phase = 93.9, 0.359
beat = 60 / bpm
mono = x.mean(axis=1)[::8].astype(np.float64)
analysis_sr = SR / 8
window = int(0.30 * analysis_sr)
candidates = []
for end in np.arange(phase, len(x) / SR - 0.15, beat):
    if end < 33:
        continue
    ie = round(end * analysis_sr)
    a = mono[ie - window:ie]
    for bars in (2, 3, 4, 6):
        nominal = bars * 4 * beat
        if end - nominal < 8:
            continue
        for correction in np.arange(-0.025, 0.0251, 1 / analysis_sr):
            start = end - nominal + correction
            ib = round(start * analysis_sr)
            b = mono[ib - window:ib]
            corr = float(np.dot(a, b) / max(1e-12, np.linalg.norm(a) * np.linalg.norm(b)))
            candidates.append((corr, end, start, bars))
corr, end, start, bars = max(candidates)
fade = round(0.30 * SR)
ie, ib = round(end * SR), round(start * SR)
weight = ((1 - np.cos(np.linspace(0, np.pi, fade))) / 2)[:, None]
join = x[ie - fade:ie] * (1 - weight) + x[ib - fade:ib] * weight
arranged = np.concatenate([x[:ie - fade], join, x[ib:]])[:TARGET]
assert len(arranged) == TARGET

# Let the story's achievements lift the bed gently, while speech ducking remains in Soundtrack.
keys = [(0, .87), (13, .87), (14, .78), (16.4, .90), (19.5, .92),
        (22, 1.0), (24.93, 1.18), (27, 1.22), (34.89, 1.18), (40, 1.18)]
gain = np.interp(np.arange(TARGET) / SR, [k[0] for k in keys], [k[1] for k in keys])
arranged *= gain[:, None]
unmastered = ENGINE / 'out/success-user-arranged.wav'
with wave.open(str(unmastered), 'wb') as out:
    out.setnchannels(2); out.setsampwidth(2); out.setframerate(SR)
    out.writeframes((np.clip(arranged, -1, 1) * 32767).astype('<i2').tobytes())
eq = ENGINE / 'out/success-user-eq.wav'
subprocess.run([FF, '-v', 'error', '-y', '-i', str(unmastered), '-af',
                'highpass=f=45,equalizer=f=2500:t=q:w=0.7:g=-2.5', '-c:a', 'pcm_s16le', str(eq)], check=True)
destination = P / 'success-user-40s.wav'
normalization = normalize(str(eq), str(destination), -16, -2)
report = {
    'source': SOURCE.name, 'source_duration': len(x) / SR, 'duration': len(arranged) / SR,
    'tempo_changed': False, 'pitch_changed': False, 'analysis_bpm': bpm,
    'loop': {'end': end, 'resume': start, 'crossfade_seconds': fade / SR, 'correlation': corr, 'bars': bars},
    'music_gain_keyframes': keys, 'normalization': normalization,
    'mix': {'volume': .22, 'duck': .40, 'fadeIn': .18, 'fadeOut': 1.25},
}
(P / 'music-arrangement.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(report, ensure_ascii=False, indent=2))
