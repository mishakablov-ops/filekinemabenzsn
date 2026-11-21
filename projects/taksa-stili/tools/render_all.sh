#!/bin/bash
# рендер всех кадров пробного клипа (15 к/с «на двойках», 720x1280)
cd "$(dirname "$0")/.."
R() { mkdir -p dog/frames/$1; bpyenv/bin/python dog/scene.py $1 $PWD/dog/frames/$1/f_ $2 $3 540 2 2>&1 | grep -E "DONE|rror" | sed "s/^/[$1 $2-$3] /"; }
R soft3d 1 60
R flat 61 180
R soft3d 121 240
R silhouette 241 300
R clay 301 360
R gzhel 361 420
R flat 421 540
R lowpoly 541 600
R soft3d 601 690
echo ALLDONE
