"""Voice audition: the same script read by every voice preset, loudness-matched, plus a profile vs. reference reels.

    python voice_audition.py [--script script.md] [--presets plain,energetic,andrew,remy] [--out folder]
                             [--ref ref1.mp4 ref2.mp4 ...]

Writes <out>/voice-<n>-<preset>.mp3 (all at -16 LUFS so louder != better) and prints voice_profile's table.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:
        pass

HERE = Path(__file__).resolve().parent
DEFAULT_SCRIPT = """# voice audition
Хотите своё приложение, // но боитесь, что выйдет *хуже?*
Этот скилл разбирает // чужое приложение [по косточкам:]
экраны, тексты, // ==отзывы.==
И за {20|двадцать} минут // собирает *план,* как сделать лучше.
Сколько стоит? // !!Нисколько!!
Ссылка // [в шапке профиля.]
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--script", default=None)
    ap.add_argument("--presets", default="plain,energetic,andrew,remy")
    ap.add_argument("--out", default=".")
    ap.add_argument("--ref", nargs="*", default=[])
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="audition_"))
    (tmp / "script.md").write_text(Path(a.script).read_text(encoding="utf-8") if a.script else DEFAULT_SCRIPT, encoding="utf-8")
    made = []
    for n, pr in enumerate(a.presets.split(","), 1):
        r = subprocess.run([sys.executable, "-I", str(HERE / "tts.py"), str(tmp), "--preset", pr], capture_output=True, text=True, encoding="utf-8")
        if r.returncode:
            print(f"{pr}: failed\n{r.stderr[-800:]}")
            continue
        dst = out / f"voice-{n}-{pr}.mp3"
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(tmp / "voice.wav"),
                        "-ar", "48000", "-c:a", "pcm_s16le", str(tmp / "_n.wav")], check=True)
        import loudnorm
        loudnorm.normalize(str(tmp / "_n.wav"), str(dst), -16.0, 0.0)
        shutil.copy(tmp / "voice.wav", tmp / f"{pr}.wav")
        made.append(tmp / f"{pr}.wav")
        print(f"  {dst}")
    if made:
        subprocess.run([sys.executable, "-I", str(HERE / "voice_profile.py"), *map(str, made), *(["--ref", *a.ref] if a.ref else [])])
    shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
