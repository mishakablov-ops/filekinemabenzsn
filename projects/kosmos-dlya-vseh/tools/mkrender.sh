#!/bin/bash
# mkrender.sh JOBNAME SHOT [SHOT...]  -> full-res animation + H.264 clip into the Reel Studio project
# env (optional): PID=kosmos-dlya-vseh-v2  SHOTS=shots_v2.json (in blender\)  OUT=renders_v2 (frames folder in the project)
P="$HOME/mnt/aipollon claude/kosmos-dlya-vseh"
W='C:\Users\Gigabyte\Documents\aipollon claude\kosmos-dlya-vseh'
PID="${PID:-kosmos-dlya-vseh}"
SHOTS="${SHOTS:-shots.json}"
OUT="${OUT:-renders}"
RP="C:\\Users\\Gigabyte\\Documents\\aipollon claude\\AIpollon-Reel-Studio\\skills\\reel-studio\\engine\\public\\projects\\$PID\\clips"
FFW='C:\Users\Gigabyte\Documents\aipollon claude\AIpollon-Reel-Studio\skills\reel-studio\.runtime\bin\ffmpeg.exe'
name="$1"; shift
{
echo "\$ErrorActionPreference = 'Continue'"
echo "\$B = (Get-Content '$W\\tools\\blender_path.txt' -Raw).Trim()"
echo "New-Item -ItemType Directory -Force '$RP' | Out-Null"
for s in "$@"; do
echo "\$t0 = Get-Date"
echo "& \$B -b --factory-startup --python '$W\\blender\\build.py' -- --shot $s --anim --shots '$W\\blender\\$SHOTS' --out '$W\\$OUT' 2>&1 | ForEach-Object { \"\$_\" } | Where-Object { \$_ -notmatch '^Fra:|^\\s*\$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Shadow buffer|RNA_float_set' }"
echo "& '$FFW' -hide_banner -loglevel error -y -framerate 60 -i '$W\\$OUT\\$s\\%04d.jpg' -c:v libx264 -preset medium -crf 15 -bf 0 -g 30 -keyint_min 30 -sc_threshold 0 -pix_fmt yuv420p -movflags +faststart '$RP\\$s.mp4'"
echo "\"CLIP $s done in \" + [int]((Get-Date) - \$t0).TotalSeconds + \" s\""
done
} | sed 's/$/\r/' > "${DEST:-$P/../jobs/queue}/$name.ps1"
echo "queued $name"
