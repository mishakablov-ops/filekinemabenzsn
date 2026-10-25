"""Generate shared FX textures into engine/public/fx (film grain tiles, soft light-leak, noise).
No PIL needed: tiny PNG writer below."""
from __future__ import annotations

import struct
import sys
import zlib
from pathlib import Path

import numpy as np


def write_png(path: Path, rgba: np.ndarray) -> None:
    h, w, c = rgba.shape
    raw = b"".join(b"\x00" + rgba[y].astype(np.uint8).tobytes() for y in range(h))

    def chunk(t: bytes, d: bytes) -> bytes:
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    color_type = 6 if c == 4 else 2
    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, color_type, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(png)


def main(out: Path) -> None:
    rng = np.random.default_rng(1)
    size = 512
    for k in range(4):
        g = rng.normal(0.5, 0.18, (size, size))
        # slightly soften so it reads as film grain, not digital noise
        g = (g + np.roll(g, 1, 0) * 0.35 + np.roll(g, 1, 1) * 0.35) / 1.7
        v = np.clip(g * 255, 0, 255)
        img = np.stack([v, v, v, np.full_like(v, 255)], axis=-1)
        write_png(out / f"grain-{k}.png", img)
    # radial light leak (warm) 1024x1024 alpha
    y, x = np.mgrid[0:1024, 0:1024] / 1023.0
    d = np.sqrt((x - 0.3) ** 2 + (y - 0.35) ** 2)
    a = np.clip(1 - d / 0.7, 0, 1) ** 2.2
    leak = np.stack([np.full_like(a, 255), np.full_like(a, 170), np.full_like(a, 90), a * 255], axis=-1)
    write_png(out / "leak-warm.png", leak)
    print("fx ->", out)


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / "engine" / "public" / "fx")
