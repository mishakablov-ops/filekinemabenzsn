$ErrorActionPreference = 'Continue'
# 30.10.2026: c13 without the kid, c16 with the golem eyes switched off after the crumble (fixed hide keys)
$B = (Get-Content 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\tools\blender_path.txt' -Raw).Trim()
New-Item -ItemType Directory -Force -Path 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\clips' | Out-Null
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\blender\build_pc.py' -- --shot c13 --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\clips\c13.mp4' --scale 1.0 --fps 30 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT c13 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\blender\build_pc.py' -- --shot c16 --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\clips\c16.mp4' --scale 1.0 --fps 30 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT c16 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
