$ErrorActionPreference = 'Continue'
$B = (Get-Content 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\tools\blender_path.txt' -Raw).Trim()
New-Item -ItemType Directory -Force -Path 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\stills' | Out-Null
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\blender\build_pc.py' -- --shot b07 --still 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\stills' --scale 0.5 --t 0.85 --tag _prof 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT b07 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\blender\build_pc.py' -- --shot b08 --still 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\stills' --scale 0.5 --t 0.85 --tag _prof 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT b08 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\blender\build_pc.py' -- --shot b13 --still 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\stills' --scale 0.5 --t 0.3 --tag _prof 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT b13 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\blender\build_pc.py' -- --shot b09 --still 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\stills' --scale 0.5 --t 0.3 --tag _prof 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT b09 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\blender\build_pc.py' -- --shot a03 --still 'C:\Users\Gigabyte\Documents\aipollon claude\sposobnosti\stills' --scale 0.5 --t 0.85 --tag _prof 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT a03 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
