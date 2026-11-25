#!/bin/bash
# проходы для аниме (кадры 436..495): ID + глубина + мировые координаты, мягкий свет, только солнце; трава-пучки видны
cd "$(dirname "$0")/.."
P=bpyenv/bin/python; O=$PWD/dog/v4
IDS_POS=1 $P dog/scene.py ids $PWD/dog/ids4a 436 495 1080 1 2>&1 | grep -E "rror|Trace"; echo "[ids] done"
mkdir -p $O/shadeA $O/key
SAMPLES=8 $P dog/scene.py shade $O/shadeA/f_ 436 495 540 1 2>&1 | grep -E "DONE|rror|Trace"
KEYONLY=1 SAMPLES=8 $P dog/scene.py shade $O/key/f_ 436 495 540 1 2>&1 | grep -E "DONE|rror|Trace"
echo ANIME_PASSES_DONE
