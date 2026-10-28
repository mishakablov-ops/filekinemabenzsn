$ErrorActionPreference = 'Continue'
$B = (Get-Content 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\tools\blender_path.txt' -Raw).Trim()
New-Item -ItemType Directory -Force -Path 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\clips' | Out-Null
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\blender\build_pc.py' -- --shot a12 --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\clips\a12.mp4' --scale 1.0 --fps 30 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT a12 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\blender\build_pc.py' -- --shot a17 --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\clips\a17.mp4' --scale 1.0 --fps 30 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT a17 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\blender\build_pc.py' -- --shot b06 --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\clips\b06.mp4' --scale 1.0 --fps 30 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT b06 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\blender\build_pc.py' -- --shot b08 --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\clips\b08.mp4' --scale 1.0 --fps 30 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT b08 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\blender\build_pc.py' -- --shot b10 --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\clips\b10.mp4' --scale 1.0 --fps 30 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT b10 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\blender\build_pc.py' -- --shot b16 --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\clips\b16.mp4' --scale 1.0 --fps 30 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT b16 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\blender\build_pc.py' -- --shot b17 --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\clips\b17.mp4' --scale 1.0 --fps 30 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT b17 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\blender\build_pc.py' -- --shot b18 --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\clips\b18.mp4' --scale 1.0 --fps 30 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT b18 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
