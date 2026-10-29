"""Voice of «Баронесса-пулемётчица» v2 from the files mike generated himself (29.10.2026): narrator blocks
(voice/narr_v2/A..G.mp3) cut at their pauses, the baroness's lines (voice/bar_v2/b1..b9.mp3) put in between, each part
at -16 LUFS, glued with short pauses -> tts.py --engine audio --tighten 0.25 -> KINEMA project baronessa-v2.
    python -I engine/voice_v2.py
"""
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
RS = Path(os.environ.get("KINEMA_RS", r"C:\Users\Gigabyte\Documents\aipollon claude\KINEMA\skills\reel-studio"))
sys.path.insert(0, str(RS / "scripts"))
import fish_tts  # noqa: E402
import loudnorm  # noqa: E402
from tts import write_wav  # noqa: E402

N, B = HERE / "voice" / "narr_v2", HERE / "voice" / "bar_v2"
P = RS / "engine" / "public" / "projects" / "baronessa-v2"
W = HERE / "voice" / "v2_parts"
# (file, start, end) in script order; cuts sit in the middle of the narrator's pauses (silencedetect)
PARTS = [(B / "b1.mp3", None, None), (N / "A.mp3", None, None),
         (N / "B.mp3", None, 10.65), (B / "b2.mp3", None, None), (N / "B.mp3", 10.65, None),
         (N / "C.mp3", None, 15.40), (B / "b3.mp3", None, None), (N / "C.mp3", 15.40, None), (B / "b4.mp3", None, None),
         (N / "D.mp3", None, 5.10), (B / "b5.mp3", None, None), (N / "D.mp3", 5.10, 15.86), (B / "b6.mp3", None, None),
         (N / "D.mp3", 15.86, None),
         (N / "E.mp3", None, 20.70), (B / "b7.mp3", None, None), (N / "E.mp3", 20.70, None),
         (N / "F.mp3", None, 12.45), (B / "b8.mp3", None, None), (N / "F.mp3", 12.45, None),
         (N / "G.mp3", None, None), (B / "b9.mp3", None, None)]


def main():
    W.mkdir(parents=True, exist_ok=True)
    P.mkdir(parents=True, exist_ok=True)
    files = []
    for i, (f, a, b) in enumerate(PARTS):
        raw, out = W / f"{i:02d}_raw.wav", W / f"{i:02d}.wav"
        # 29.10 mike: «обрезал криво» -> no silence removal inside the takes (it ate word endings); cuts sit in the
        # middle of the pauses between words (Whisper word times), 25 ms fades; only the far edges of whole files
        # lose their dead air, gently (-60 dB) and with 80 ms kept
        af = []
        if a is None:
            af.append("silenceremove=start_periods=1:start_threshold=-60dB:start_silence=0.08")
        if b is None:
            af.append("areverse,silenceremove=start_periods=1:start_threshold=-60dB:start_silence=0.08,areverse")
        af.append("afade=t=in:d=0.025")
        cmd = ["ffmpeg", "-v", "error", "-y", "-i", str(f)]
        if a is not None:
            cmd += ["-ss", str(a)]
        if b is not None:
            cmd += ["-to", str(b)]
        cmd += ["-af", ",".join(af), "-ac", "1", "-ar", "48000", str(raw)]
        subprocess.run(cmd, check=True)
        loudnorm.normalize(str(raw), str(out), -16.0, -1.0)
        files.append(out)
    texts = [""] + ["[short pause]"] * (len(files) - 1)
    x = fish_tts.join_takes(files, texts, 48000)
    write_wav(P / "voice_raw.wav", x / (abs(x).max() + 1e-9) * 0.89)
    txt = (HERE / "script-v2.md").read_text(encoding="utf-8")
    (P / "script.md").write_text(re.sub(r"(?m)^Б:\s*", "", txt), encoding="utf-8")
    r = subprocess.run([sys.executable, "-I", str(RS / "scripts" / "tts.py"), str(P), "--engine", "audio",
                        "--audio", str(P / "voice_raw.wav"), "--tighten", "0.25"])
    if r.returncode:
        raise SystemExit("tts.py failed")
    print((P / "tts_report.json").read_text(encoding="utf-8")[:600])


if __name__ == "__main__":
    main()
