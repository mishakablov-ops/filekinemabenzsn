#!/bin/bash
# mkjob.sh NAME "blender build.py args"   -> jobs/queue/NAME.ps1
P="$HOME/mnt/aipollon claude/kosmos-dlya-vseh"
W='C:\Users\Gigabyte\Documents\aipollon claude\kosmos-dlya-vseh'
name="$1"; shift
{
echo "\$ErrorActionPreference = 'Continue'"
echo "\$B = (Get-Content '$W\\tools\\blender_path.txt' -Raw).Trim()"
for args in "$@"; do
echo "& \$B -b --factory-startup --python '$W\\blender\\build.py' -- $args 2>&1 | ForEach-Object { \"\$_\" } | Where-Object { \$_ -notmatch '^Fra:|^\\s*\$|Synchroniz|Compiling|Loading|Updating|Waiting' }"
done
} | sed 's/$/\r/' > "$P/../jobs/queue/$name.ps1"
echo "queued $name"
