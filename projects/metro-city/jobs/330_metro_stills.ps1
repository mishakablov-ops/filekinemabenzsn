$ErrorActionPreference = 'Continue'
$B = (Get-Content 'C:\Users\Gigabyte\Documents\aipollon claude\metro-city\tools\blender_path.txt' -Raw).Trim()
New-Item -ItemType Directory -Force -Path 'C:\Users\Gigabyte\Documents\aipollon claude\metro-city\stills' | Out-Null
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\metro-city\blender\build_pc.py' -- --shot skyline_dusk --still 'C:\Users\Gigabyte\Documents\aipollon claude\metro-city\stills' --scale 1.0 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT skyline_dusk done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\metro-city\blender\build_pc.py' -- --shot aerial_night --still 'C:\Users\Gigabyte\Documents\aipollon claude\metro-city\stills' --scale 1.0 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT aerial_night done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\metro-city\blender\build_pc.py' -- --shot avenue --still 'C:\Users\Gigabyte\Documents\aipollon claude\metro-city\stills' --scale 1.0 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT avenue done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\metro-city\blender\build_pc.py' -- --shot plaza --still 'C:\Users\Gigabyte\Documents\aipollon claude\metro-city\stills' --scale 1.0 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT plaza done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\metro-city\blender\build_pc.py' -- --shot embankment --still 'C:\Users\Gigabyte\Documents\aipollon claude\metro-city\stills' --scale 1.0 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT embankment done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\metro-city\blender\build_pc.py' -- --shot bridge --still 'C:\Users\Gigabyte\Documents\aipollon claude\metro-city\stills' --scale 1.0 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT bridge done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\metro-city\blender\build_pc.py' -- --shot park --still 'C:\Users\Gigabyte\Documents\aipollon claude\metro-city\stills' --scale 1.0 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT park done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\metro-city\blender\build_pc.py' -- --shot rooftop --still 'C:\Users\Gigabyte\Documents\aipollon claude\metro-city\stills' --scale 1.0 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT rooftop done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
