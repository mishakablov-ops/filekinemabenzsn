#!/bin/bash
# stills.sh JOBNAME "shot:t1,t2" ...   (half-res stills)
P="$HOME/mnt/aipollon claude/kosmos-dlya-vseh"
name=$1; shift; ARR=()
for s in "$@"; do id=${s%%:*}; t=${s#*:}; ARR+=("--shot $id --times $t --scale 0.5"); done
"$P/tools/mkjob.sh" "$name" "${ARR[@]}"
