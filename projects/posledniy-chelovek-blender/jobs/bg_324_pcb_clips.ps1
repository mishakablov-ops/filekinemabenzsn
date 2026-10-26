$ErrorActionPreference = 'Continue'
$B = (Get-Content 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\tools\blender_path.txt' -Raw).Trim()
New-Item -ItemType Directory -Force -Path 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\clips' | Out-Null
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\blender\build_pc.py' -- --shot wolves --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\clips\wolves.mp4' --scale 1.0 --fps 30 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT wolves done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\blender\build_pc.py' -- --shot blackout --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\clips\blackout.mp4' --scale 1.0 --fps 30 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT blackout done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\blender\build_pc.py' -- --shot count --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\clips\count.mp4' --scale 1.0 --fps 30 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT count done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\blender\build_pc.py' -- --shot night --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\clips\night.mp4' --scale 1.0 --fps 30 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT night done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
