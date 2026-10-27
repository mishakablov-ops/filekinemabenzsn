$ErrorActionPreference = 'Continue'
$B = (Get-Content 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\tools\blender_path.txt' -Raw).Trim()
New-Item -ItemType Directory -Force -Path 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\renders\proof' | Out-Null
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\blender\build_pc.py' -- --shot count --still 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\renders\proof' --scale 0.5 --t 0.15 --tag _a 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT count done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\blender\build_pc.py' -- --shot count --still 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\renders\proof' --scale 0.5 --t 0.9 --tag _b 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT count done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\blender\build_pc.py' -- --shot last --still 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\renders\proof' --scale 0.5 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT last done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\blender\build_pc.py' -- --shot blackout --still 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\renders\proof' --scale 0.5 --t 0.3 --tag _a 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT blackout done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\blender\build_pc.py' -- --shot blackout --still 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\renders\proof' --scale 0.5 --t 0.95 --tag _b 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT blackout done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\blender\build_pc.py' -- --shot night --still 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\renders\proof' --scale 0.5 --t 0.3 --tag _a 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT night done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\blender\build_pc.py' -- --shot night --still 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\renders\proof' --scale 0.5 --t 0.98 --tag _b 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT night done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\blender\build_pc.py' -- --shot third --still 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\renders\proof' --scale 0.5 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT third done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\blender\build_pc.py' -- --shot wolves --still 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\renders\proof' --scale 0.5 --t 0.2 --tag _a 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT wolves done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\blender\build_pc.py' -- --shot wolves --still 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\renders\proof' --scale 0.5 --t 0.9 --tag _b 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT wolves done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\blender\build_pc.py' -- --shot chernobyl --still 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\renders\proof' --scale 0.5 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT chernobyl done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\blender\build_pc.py' -- --shot fuel --still 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\renders\proof' --scale 0.5 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT fuel done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\blender\build_pc.py' -- --shot room --still 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\renders\proof' --scale 0.5 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT room done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
