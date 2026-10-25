#!/bin/bash
# mkrender.sh JOBNAME SHOT [SHOT...]  -> full-res animation + H.264 clip into the Reel Studio project
P="$HOME/mnt/aipollon claude/mir-bez-granic"
W='C:\Users\Gigabyte\Documents\aipollon claude\mir-bez-granic'
RP='C:\Users\Gigabyte\Documents\aipollon claude\AIpollon-Reel-Studio\skills\reel-studio\engine\public\projects\mir-bez-granic\clips'
FFW='C:\Users\Gigabyte\Documents\aipollon claude\AIpollon-Reel-Studio\skills\reel-studio\.runtime\bin\ffmpeg.exe'
name="$1"; shift
{
echo "\$ErrorActionPreference = 'Continue'"
echo "\$B = (Get-Content '$W\\tools\\blender_path.txt' -Raw).Trim()"
for s in "$@"; do
echo "if (\$env:MBG_CLEAN -eq '1') { Remove-Item -Recurse -Force '$W\\renders\\$s' -ErrorAction SilentlyContinue }"
echo "\$t0 = Get-Date"
echo "& \$B -b --factory-startup --python '$W\\blender\\build.py' -- --shot $s --anim 2>&1 | ForEach-Object { \"\$_\" } | Where-Object { \$_ -notmatch '^Fra:|^\\s*\$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:' }"
echo "& '$FFW' -hide_banner -loglevel error -y -framerate 60 -i '$W\\renders\\$s\\%04d.jpg' -c:v libx264 -preset medium -crf 15 -bf 0 -g 30 -keyint_min 30 -sc_threshold 0 -pix_fmt yuv420p -movflags +faststart '$RP\\$s.mp4'"
echo "\"CLIP $s done in \" + [int]((Get-Date) - \$t0).TotalSeconds + \" s\""
done
} | sed 's/$/\r/' > "$P/jobs/queue/$name.ps1"
echo "queued $name"
