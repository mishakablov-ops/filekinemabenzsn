$ErrorActionPreference = 'Continue'
$B = (Get-Content 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\tools\blender_path.txt' -Raw).Trim()
New-Item -ItemType Directory -Force -Path 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\stills' | Out-Null
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\blender\build_pc.py' -- --shot wake --still 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\stills' --scale 1.25 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT wake done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\blender\build_pc.py' -- --shot you --still 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\stills' --scale 1.25 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT you done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\blender\build_pc.py' -- --shot cafe --still 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\stills' --scale 1.25 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT cafe done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\blender\build_pc.py' -- --shot station --still 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\stills' --scale 1.25 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT station done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\blender\build_pc.py' -- --shot shops --still 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\stills' --scale 1.25 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT shops done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\blender\build_pc.py' -- --shot bread --still 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\stills' --scale 1.25 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT bread done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\blender\build_pc.py' -- --shot cans --still 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\stills' --scale 1.25 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT cans done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\blender\build_pc.py' -- --shot car --still 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\stills' --scale 1.25 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT car done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\blender\build_pc.py' -- --shot fuel --still 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\stills' --scale 1.25 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT fuel done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\blender\build_pc.py' -- --shot third --still 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\stills' --scale 1.25 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT third done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\blender\build_pc.py' -- --shot chernobyl --still 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\stills' --scale 1.25 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT chernobyl done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\blender\build_pc.py' -- --shot last --still 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\stills' --scale 1.25 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT last done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\blender\build_pc.py' -- --shot room --still 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\stills' --scale 1.25 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT room done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\blender\build_pc.py' -- --shot knock --still 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\stills' --scale 1.25 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT knock done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\blender\build_pc.py' -- --shot cta --still 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\stills' --scale 1.25 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT cta done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
