#!/bin/bash
# v4: + аниме (кадры сцены 436..495: камера разворачивается к морде, такса подпрыгивает), концовка сдвинута на 496..585.
# Остальные стили берутся из v3 (кадры 76..435 не менялись).
cd "$(dirname "$0")/.."
P=bpyenv/bin/python; O=$PWD/dog/v4
R() { mkdir -p $O/$1; $P dog/scene.py $1 $O/$1/f_ $2 $3 $4 $5 2>&1 | grep -E "DONE|rror|Trace" | sed "s/^/[$1 $2-$3] /"; }
IDS_HIDE=tufts $P dog/scene.py ids $PWD/dog/ids4 436 495 1080 1 2>&1 | grep -E "rror|Trace"; echo "[ids] done"
IDS_HIDE=tufts SAMPLES=8 R shade 436 495 540 1
echo PASSES_DONE
SAMPLES=20 R soft3d 496 585 720 2
echo ALLDONE
