"""Master and validate the new soundtrack while copying the approved H.264 stream exactly."""
from pathlib import Path
import json
import subprocess
import sys

import numpy as np

P = Path(__file__).resolve().parent
ENGINE = P.parents[2]
RS = ENGINE.parent
OUTPUT = RS.parents[2] / 'output'
sys.path.insert(0, str(RS / 'scripts'))
from loudnorm import normalize, measure

FF = str(RS / '.runtime/bin/ffmpeg.exe')
PROBE = str(RS / '.runtime/bin/ffprobe.exe')
OLD = OUTPUT / 'quiet-evenings-40s-v4.mp4'
FINAL = OUTPUT / 'quiet-evenings-40s-v5.mp4'
MASTER = ENGINE / 'out/quiet-evenings-v5-master.wav'
for stream in (sys.stdout, sys.stderr):
    stream.reconfigure(encoding='utf-8')


def stream_hash(file, stream):
    return subprocess.run([FF, '-v', 'error', '-i', str(file), '-map', stream, '-c', 'copy',
                           '-f', 'hash', '-hash', 'sha256', 'pipe:1'], capture_output=True, text=True, check=True).stdout.strip()


def samples(file):
    raw = subprocess.run([FF, '-v', 'error', '-i', str(file), '-ar', '48000', '-ac', '2',
                          '-f', 'f32le', 'pipe:1'], capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).reshape(-1, 2)


normalization = normalize(str(ENGINE / 'out/quiet-evenings-v5-mix.wav'), str(MASTER), -14, -1)
subprocess.run([FF, '-v', 'error', '-y', '-i', str(OLD), '-i', str(MASTER), '-map', '0:v:0', '-map', '1:a:0',
                '-c:v', 'copy', '-c:a', 'aac', '-b:a', '320k', '-ar', '48000', '-t', '40',
                '-movflags', '+faststart', str(FINAL)], check=True)

info = json.loads(subprocess.run([PROBE, '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(FINAL)],
                                  capture_output=True, text=True, check=True).stdout)
video = next(s for s in info['streams'] if s['codec_type'] == 'video')
audio = next(s for s in info['streams'] if s['codec_type'] == 'audio')
assert abs(float(info['format']['duration']) - 40) < .001
assert (video['width'], video['height'], video['r_frame_rate']) == (1080, 1920, '60/1')
assert (audio['sample_rate'], audio['channels']) == ('48000', 2)
video_equal = stream_hash(OLD, '0:v:0') == stream_hash(FINAL, '0:v:0')
audio_changed = stream_hash(OLD, '0:a:0') != stream_hash(FINAL, '0:a:0')
assert video_equal and audio_changed

spec = json.loads((P / 'spec.json').read_text(encoding='utf-8'))
words = json.loads((P / 'words.json').read_text(encoding='utf-8'))
fps, frames = 60, 2400
speech = np.zeros(frames)
for word in words['words']:
    a = max(0, int(np.floor((word['start'] - .12) * fps)))
    b = min(frames, int(np.ceil((word['end'] + .28) * fps)))
    speech[a:b] = 1
curve = np.zeros(frames)
g, m = 1., spec['music']
attack = 1 - np.exp(-1 / (.08 * fps))
release = 1 - np.exp(-1 / (.35 * fps))
for f in range(frames):
    target = m['duck'] if speech[f] else 1
    g += (target - g) * (attack if target < g else release)
    curve[f] = m['volume'] * g * min(1, f / (m['fadeIn'] * fps)) * min(1, (frames - f) / (m['fadeOut'] * fps))
bed = samples(P / 'success-user-40s.wav')
voice = samples(P / 'voice.wav')
voice = np.pad(voice, ((0, max(0, len(bed) - len(voice))), (0, 0)))[:len(bed)]
levels = {}
for name, a, b in [('learning', 8, 13), ('first_clients', 20.8, 24.9), ('success', 26, 33), ('final_profile', 36, 38.5)]:
    ix = np.arange(round(a * 48000), round(b * 48000))
    gain = np.interp(ix / 48000 * fps, np.arange(frames), curve)
    voice_rms = np.sqrt(np.mean(voice[ix] ** 2))
    music_rms = np.sqrt(np.mean((bed[ix] * gain[:, None]) ** 2))
    levels[name] = round(float(20 * np.log10(voice_rms / max(music_rms, 1e-9))), 2)
assert min(levels.values()) >= 8, levels
loud = measure(str(FINAL), -14, -1)
assert -15 <= float(loud['input_i']) <= -13 and float(loud['input_tp']) <= -1, loud
report = {'status': 'PASS', 'duration': 40, 'video_stream_identical_to_v4': video_equal, 'audio_replaced': audio_changed,
          'loudness_lufs': float(loud['input_i']), 'true_peak_dbtp': float(loud['input_tp']),
          'voice_above_music_db_by_section': levels, 'master': normalization,
          'arrangement': json.loads((P / 'music-arrangement.json').read_text(encoding='utf-8'))}
(OUTPUT / (FINAL.stem + '_qa.json')).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
md = f'''# Проверка {FINAL.name}: PASS

- Длительность: 40 секунд, 1080×1920, 60 кадров/с; AAC 48 кГц стерео.
- Видеопоток побайтово совпадает с одобренной версией v4.
- Звуковая дорожка заменена: исходная озвучка, прежние эффекты и музыка пользователя.
- Громкость: {loud['input_i']} LUFS; истинный пик: {loud['input_tp']} dBTP.
- Музыка приведена к 40 секундам с переходом 0,30 с без изменения темпа и высоты тона.
- В основных сценах речь выше музыкального фона на {min(levels.values()):.1f}–{max(levels.values()):.1f} dB по RMS; применяется приглушение под голосом и плавное затухание.
'''
(OUTPUT / (FINAL.stem + '_qa.md')).write_text(md, encoding='utf-8')
print(json.dumps({k: v for k, v in report.items() if k not in ('arrangement', 'master')}, ensure_ascii=False, indent=2))
