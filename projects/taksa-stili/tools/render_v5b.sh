#!/bin/bash
# v5, вторая часть: 3D-стили в 1080 (без размытия движения: на метаболах оно мылило тело), фокус мягче.
cd "$(dirname "$0")/.."
P=bpyenv/bin/python; O=$PWD/dog/v5; X=1080
R() { mkdir -p $O/$1; $P dog/scene.py $1 $O/$1/f_ $2 $3 $4 $5 2>&1 | grep -E "DONE|rror|Trace" | sed "s/^/[$1 $2-$3] /"; }
T0=$(date +%s); t() { echo "  ($(( ($(date +%s) - T0) / 60 )) мин)"; }
SAMPLES=32 R soft3d 76 143 $X 1; t
SAMPLES=32 R clay 316 383 $X 2; t
SAMPLES=24 R lowpoly 376 443 $X 1; t
mkdir -p $O/ending
SAMPLES=32 $P dog/scene.py soft3d $O/ending/f_ 496 585 $X 2 2>&1 | grep -E "DONE|rror|Trace" | sed "s/^/[ending] /"; t
echo ALLDONE
