$ErrorActionPreference = 'Continue'
$B = (Get-Content 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\tools\blender_path.txt' -Raw).Trim()
New-Item -ItemType Directory -Force -Path 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\stills' | Out-Null
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\blender\build_pc.py' -- --shot a01 --still 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\stills' --scale 0.5 --ts 0.3,0.85 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT a01 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\blender\build_pc.py' -- --shot a02 --still 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\stills' --scale 0.5 --ts 0.3,0.85 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT a02 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\blender\build_pc.py' -- --shot a03 --still 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\stills' --scale 0.5 --ts 0.3,0.85 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT a03 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\blender\build_pc.py' -- --shot a04 --still 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\stills' --scale 0.5 --ts 0.3,0.85 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT a04 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\blender\build_pc.py' -- --shot a05 --still 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\stills' --scale 0.5 --ts 0.3,0.85 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT a05 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\blender\build_pc.py' -- --shot a06 --still 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\stills' --scale 0.5 --ts 0.3,0.85 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT a06 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\blender\build_pc.py' -- --shot a07 --still 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\stills' --scale 0.5 --ts 0.3,0.85 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT a07 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\blender\build_pc.py' -- --shot a08 --still 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\stills' --scale 0.5 --ts 0.3,0.85 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT a08 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\blender\build_pc.py' -- --shot a09 --still 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\stills' --scale 0.5 --ts 0.3,0.85 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT a09 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\blender\build_pc.py' -- --shot a10 --still 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\stills' --scale 0.5 --ts 0.3,0.85 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT a10 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\blender\build_pc.py' -- --shot a11 --still 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\stills' --scale 0.5 --ts 0.3,0.85 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT a11 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\blender\build_pc.py' -- --shot a12 --still 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\stills' --scale 0.5 --ts 0.3,0.85 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT a12 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\blender\build_pc.py' -- --shot a13 --still 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\stills' --scale 0.5 --ts 0.3,0.85 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT a13 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\blender\build_pc.py' -- --shot a14 --still 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\stills' --scale 0.5 --ts 0.3,0.85 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT a14 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\blender\build_pc.py' -- --shot a15 --still 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\stills' --scale 0.5 --ts 0.3,0.85 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT a15 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\blender\build_pc.py' -- --shot a16 --still 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\stills' --scale 0.5 --ts 0.3,0.85 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT a16 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\blender\build_pc.py' -- --shot a17 --still 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\stills' --scale 0.5 --ts 0.3,0.85 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT a17 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\blender\build_pc.py' -- --shot a18 --still 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\stills' --scale 0.5 --ts 0.3,0.85 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT a18 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\blender\build_pc.py' -- --shot a19 --still 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\stills' --scale 0.5 --ts 0.3,0.85 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT a19 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\blender\build_pc.py' -- --shot a20 --still 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\stills' --scale 0.5 --ts 0.3,0.85 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT a20 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\blender\build_pc.py' -- --shot b01 --still 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\stills' --scale 0.5 --ts 0.3,0.85 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT b01 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\blender\build_pc.py' -- --shot b02 --still 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\stills' --scale 0.5 --ts 0.3,0.85 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT b02 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\blender\build_pc.py' -- --shot b03 --still 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\stills' --scale 0.5 --ts 0.3,0.85 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT b03 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\blender\build_pc.py' -- --shot b04 --still 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\stills' --scale 0.5 --ts 0.3,0.85 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT b04 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\blender\build_pc.py' -- --shot b05 --still 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\stills' --scale 0.5 --ts 0.3,0.85 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT b05 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\blender\build_pc.py' -- --shot b06 --still 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\stills' --scale 0.5 --ts 0.3,0.85 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT b06 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\blender\build_pc.py' -- --shot b07 --still 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\stills' --scale 0.5 --ts 0.3,0.85 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT b07 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\blender\build_pc.py' -- --shot b08 --still 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\stills' --scale 0.5 --ts 0.3,0.85 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT b08 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\blender\build_pc.py' -- --shot b09 --still 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\stills' --scale 0.5 --ts 0.3,0.85 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT b09 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\blender\build_pc.py' -- --shot b10 --still 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\stills' --scale 0.5 --ts 0.3,0.85 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT b10 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\blender\build_pc.py' -- --shot b11 --still 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\stills' --scale 0.5 --ts 0.3,0.85 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT b11 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\blender\build_pc.py' -- --shot b12 --still 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\stills' --scale 0.5 --ts 0.3,0.85 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT b12 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\blender\build_pc.py' -- --shot b13 --still 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\stills' --scale 0.5 --ts 0.3,0.85 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT b13 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\blender\build_pc.py' -- --shot b14 --still 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\stills' --scale 0.5 --ts 0.3,0.85 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT b14 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\blender\build_pc.py' -- --shot b15 --still 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\stills' --scale 0.5 --ts 0.3,0.85 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT b15 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\blender\build_pc.py' -- --shot b16 --still 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\stills' --scale 0.5 --ts 0.3,0.85 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT b16 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\blender\build_pc.py' -- --shot b17 --still 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\stills' --scale 0.5 --ts 0.3,0.85 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT b17 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\blender\build_pc.py' -- --shot b18 --still 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\stills' --scale 0.5 --ts 0.3,0.85 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT b18 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\blender\build_pc.py' -- --shot b19 --still 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\stills' --scale 0.5 --ts 0.3,0.85 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT b19 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\blender\build_pc.py' -- --shot b20 --still 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\stills' --scale 0.5 --ts 0.3,0.85 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT b20 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
