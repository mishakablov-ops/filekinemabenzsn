$ErrorActionPreference = 'Continue'
$B = (Get-Content 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\tools\blender_path.txt' -Raw).Trim()
New-Item -ItemType Directory -Force -Path 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\clips' | Out-Null
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\blender\build_pc.py' -- --shot a03 --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\clips\a03.mp4' --scale 1.0 --fps 30 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT a03 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\blender\build_pc.py' -- --shot a11 --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\clips\a11.mp4' --scale 1.0 --fps 30 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT a11 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\blender\build_pc.py' -- --shot a13 --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\clips\a13.mp4' --scale 1.0 --fps 30 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT a13 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\blender\build_pc.py' -- --shot b13 --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\clips\b13.mp4' --scale 1.0 --fps 30 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT b13 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\blender\build_pc.py' -- --shot b14 --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\clips\b14.mp4' --scale 1.0 --fps 30 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT b14 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\blender\build_pc.py' -- --shot b20 --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\clips\b20.mp4' --scale 1.0 --fps 30 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT b20 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
