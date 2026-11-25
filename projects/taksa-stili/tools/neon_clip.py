"""Тест-клип неона: вывеска загорается (собака → надпись → полянка), гул и щелчки. 30 к/с.
python neon_clip.py <ids_dir> <f0> <f1> <variant> <out.mp4>"""
import os, subprocess, sys, wave
from concurrent.futures import ThreadPoolExecutor
import numpy as np

D = os.path.dirname(os.path.abspath(__file__))
IDS, F0, F1, VAR, MP4 = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4], sys.argv[5]
SEQ = os.path.join(D, 'neon_seq_' + VAR); os.makedirs(SEQ, exist_ok=True)
DARK, RAMP = 6, 48   # кадров темноты и включения


def on_at(i):
    return float(np.clip((i - DARK) / RAMP, 0, 1)) if i >= DARK else 0.0


def job(i):
    f = F0 + i
    on = on_at(i)
    args = [sys.executable, os.path.join(D, 'neon.py'), IDS, str(f), os.path.join(SEQ, 'n_%04d.png' % i), VAR,
            str(on if on < 1 else 1.0)]
    subprocess.run(args, check=True, env=dict(os.environ))
    return i


n = F1 - F0 + 1
with ThreadPoolExecutor(4) as ex:
    for i in ex.map(job, range(n)):
        pass
print('frames ok', flush=True)

# звук: щелчки поджига + гул 50 Гц с гармониками (появляется с первой трубкой) + лёгкий треск
sr = 48000; T = n / 30 + 0.3
aud = np.zeros(int(sr * T)); rng = np.random.default_rng(2)
t = np.arange(aud.size) / sr
hum = (np.sin(2 * np.pi * 50 * t) * 0.5 + np.sin(2 * np.pi * 100 * t) * 0.35 + np.sin(2 * np.pi * 150 * t) * 0.2
       + np.sin(2 * np.pi * 250 * t) * 0.08)
env = np.clip((t - (DARK + 0.04 * RAMP) / 30) * 3, 0, 1) * (0.5 + 0.5 * np.clip((t - (DARK + 0.9 * RAMP) / 30) * 2, 0, 1))
aud += hum * env * 0.10
def click(t0, amp=0.6):
    s0 = int(t0 * sr); L = int(0.03 * sr)
    if s0 + L >= aud.size: return
    burst = rng.normal(0, 1, L) * np.exp(-np.arange(L) / (0.004 * sr))
    aud[s0:s0 + L] += burst * amp
    # короткий «дзынь» трубки
    tt = np.arange(int(0.15 * sr)) / sr
    ring = np.sin(2 * np.pi * 1900 * tt) * np.exp(-tt * 30) * amp * 0.15
    aud[s0:s0 + ring.size] += ring
for tr in (0.04, 0.10, 0.13, 0.15, 0.17, 0.19, 0.22, 0.32, 0.36):
    base = (DARK + tr * RAMP) / 30
    click(base); click(base + 0.05, 0.3); click(base + 0.09, 0.2)
for k in range(10):
    click((DARK + (0.45 + 0.45 * k / 9) * RAMP) / 30, 0.25)
aud += rng.normal(0, 0.004, aud.size) * env
aud = aud / np.abs(aud).max() * 0.8
wp = os.path.join(D, 'neon_%s.wav' % VAR)
with wave.open(wp, 'w') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
    w.writeframes((aud * 32767).astype(np.int16).tobytes())
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', '30', '-i', os.path.join(SEQ, 'n_%04d.png'), '-i', wp,
                '-vf', 'format=yuv420p', '-c:v', 'libx264', '-preset', 'slow', '-b:v', '10M', '-maxrate', '12M',
                '-bufsize', '20M', '-c:a', 'aac', '-b:a', '192k', '-af', 'loudnorm=I=-14:TP=-1.5:LRA=11',
                '-shortest', '-movflags', '+faststart', MP4], check=True)
print('MP4', MP4)
