#!/bin/bash
# v5 «к публикации»: все стили в 1080, +8 кадров нахлёста у каждого стиля для перехода-шторки.
# Сегменты сцены: неон 1-75, мягкое 3D 76-135, мультик 136-195, полутон 196-255, силуэт 256-315,
# пластилин 316-375 (через кадр), low poly 376-435, аниме 436-495, концовка 496-585 (через кадр).
cd "$(dirname "$0")/.."
P=bpyenv/bin/python; O=$PWD/dog/v5; X=1080
R() { mkdir -p $O/$1; $P dog/scene.py $1 $O/$1/f_ $2 $3 $4 $5 2>&1 | grep -E "DONE|rror|Trace" | sed "s/^/[$1 $2-$3] /"; }
T0=$(date +%s); t() { echo "  ($(( ($(date +%s) - T0) / 60 )) мин)"; }
IDS_HIDE=tufts $P dog/scene.py ids $PWD/dog/ids5h 1 263 $X 1 2>&1 | grep -E "rror|Trace"; echo "[ids5h] done"; t
IDS_POS=1 $P dog/scene.py ids $PWD/dog/ids5v 436 503 $X 1 2>&1 | grep -E "rror|Trace"; echo "[ids5v] done"; t
IDS_HIDE=tufts SAMPLES=8 R shade 196 263 540 1; t
mkdir -p $O/shadeA $O/key
SAMPLES=8 $P dog/scene.py shade $O/shadeA/f_ 436 503 540 1 2>&1 | grep -E "DONE|rror|Trace" | sed "s/^/[shadeA] /"; t
KEYONLY=1 SAMPLES=8 $P dog/scene.py shade $O/key/f_ 436 503 $X 1 2>&1 | grep -E "DONE|rror|Trace" | sed "s/^/[key] /"; t
echo PASSES_DONE
R silhouette 256 323 $X 1; t
SAMPLES=24 R soft3d 76 143 $X 1; t
SAMPLES=24 R lowpoly 376 443 $X 1; t
SAMPLES=24 R clay 316 383 $X 2; t
mkdir -p $O/ending
SAMPLES=24 $P dog/scene.py soft3d $O/ending/f_ 496 585 $X 2 2>&1 | grep -E "DONE|rror|Trace" | sed "s/^/[ending] /"; t
echo ALLDONE
