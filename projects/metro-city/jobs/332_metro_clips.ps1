$ErrorActionPreference = 'Continue'
$B = (Get-Content 'C:\Users\Gigabyte\Documents\aipollon claude\metro-city\tools\blender_path.txt' -Raw).Trim()
New-Item -ItemType Directory -Force -Path 'C:\Users\Gigabyte\Documents\aipollon claude\metro-city\clips' | Out-Null
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\metro-city\blender\build_pc.py' -- --shot avenue_drive --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\metro-city\clips\avenue_drive.mp4' --scale 1.0 --fps 30 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT avenue_drive done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\metro-city\blender\build_pc.py' -- --shot aerial_night_drift --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\metro-city\clips\aerial_night_drift.mp4' --scale 1.0 --fps 30 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT aerial_night_drift done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
