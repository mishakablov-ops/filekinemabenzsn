#!/bin/bash
# v6: перерендер только low poly (голова отдельной семьёй метаболов, нос ближе к морде), остальное из v5.
cd "$(dirname "$0")/.."
P=bpyenv/bin/python; O=$PWD/dog/v6; X=1080
T0=$(date +%s)
SAMPLES=24 $P dog/scene.py lowpoly $O/lowpoly/f_ 376 443 $X 1 2>&1 | grep -E "DONE|rror|Trace" | sed "s/^/[lowpoly] /"
echo "  ($(( ($(date +%s) - T0) / 60 )) мин)"; echo ALLDONE
