#!/bin/bash
# v3: облёт камеры и новые движения. Неон (1..75) не меняется — берём готовые кадры v2.
cd "$(dirname "$0")/.."
P=bpyenv/bin/python; O=$PWD/dog/v3
R() { mkdir -p $O/$1; $P dog/scene.py $1 $O/$1/f_ $2 $3 $4 $5 2>&1 | grep -E "DONE|rror|Trace" | sed "s/^/[$1 $2-$3] /"; }
IDS_HIDE=tufts $P dog/scene.py ids $PWD/dog/ids3 136 255 1080 1 2>&1 | grep -E "rror|Trace"; echo "[ids] done"
IDS_HIDE=tufts SAMPLES=8 R shade 196 255 540 1
R silhouette 256 315 1080 1
SAMPLES=20 R soft3d 76 135 720 1
SAMPLES=20 R lowpoly 376 435 720 1
SAMPLES=16 R clay 316 375 720 2
SAMPLES=20 R soft3d 436 525 720 2
echo ALLDONE
