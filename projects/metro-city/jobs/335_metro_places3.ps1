$ErrorActionPreference = 'Continue'
$B = (Get-Content 'C:\Users\Gigabyte\Documents\aipollon claude\metro-city\tools\blender_path.txt' -Raw).Trim()
New-Item -ItemType Directory -Force -Path 'C:\Users\Gigabyte\Documents\aipollon claude\metro-city\stills' | Out-Null
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\metro-city\blender\build_pc.py' -- --shot p01_street --still 'C:\Users\Gigabyte\Documents\aipollon claude\metro-city\stills' --scale 1.0 --shots 'C:\Users\Gigabyte\Documents\aipollon claude\metro-city\blender\shots_places_demo.json' 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT p01_street done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\metro-city\blender\build_pc.py' -- --shot p07_skyline --still 'C:\Users\Gigabyte\Documents\aipollon claude\metro-city\stills' --scale 1.0 --shots 'C:\Users\Gigabyte\Documents\aipollon claude\metro-city\blender\shots_places_demo.json' 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT p07_skyline done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
