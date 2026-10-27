$ErrorActionPreference = 'Continue'
$B = (Get-Content 'C:\Users\Gigabyte\Documents\aipollon claude\metro-city\tools\blender_path.txt' -Raw).Trim()
New-Item -ItemType Directory -Force -Path 'C:\Users\Gigabyte\Documents\aipollon claude\metro-city\stills' | Out-Null
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\metro-city\blender\build_pc.py' -- --shot p01_street --still 'C:\Users\Gigabyte\Documents\aipollon claude\metro-city\stills' --scale 1.0 --shots 'C:\Users\Gigabyte\Documents\aipollon claude\metro-city\blender\shots_places_demo.json' 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT p01_street done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\metro-city\blender\build_pc.py' -- --shot p02_avenue --still 'C:\Users\Gigabyte\Documents\aipollon claude\metro-city\stills' --scale 1.0 --shots 'C:\Users\Gigabyte\Documents\aipollon claude\metro-city\blender\shots_places_demo.json' 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT p02_avenue done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\metro-city\blender\build_pc.py' -- --shot p03_borough --still 'C:\Users\Gigabyte\Documents\aipollon claude\metro-city\stills' --scale 1.0 --shots 'C:\Users\Gigabyte\Documents\aipollon claude\metro-city\blender\shots_places_demo.json' 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT p03_borough done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\metro-city\blender\build_pc.py' -- --shot p04_corner --still 'C:\Users\Gigabyte\Documents\aipollon claude\metro-city\stills' --scale 1.0 --shots 'C:\Users\Gigabyte\Documents\aipollon claude\metro-city\blender\shots_places_demo.json' 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT p04_corner done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\metro-city\blender\build_pc.py' -- --shot p05_lookup --still 'C:\Users\Gigabyte\Documents\aipollon claude\metro-city\stills' --scale 1.0 --shots 'C:\Users\Gigabyte\Documents\aipollon claude\metro-city\blender\shots_places_demo.json' 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT p05_lookup done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\metro-city\blender\build_pc.py' -- --shot p06_waterfront --still 'C:\Users\Gigabyte\Documents\aipollon claude\metro-city\stills' --scale 1.0 --shots 'C:\Users\Gigabyte\Documents\aipollon claude\metro-city\blender\shots_places_demo.json' 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT p06_waterfront done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\metro-city\blender\build_pc.py' -- --shot p07_skyline --still 'C:\Users\Gigabyte\Documents\aipollon claude\metro-city\stills' --scale 1.0 --shots 'C:\Users\Gigabyte\Documents\aipollon claude\metro-city\blender\shots_places_demo.json' 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT p07_skyline done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\metro-city\blender\build_pc.py' -- --shot p08_river --still 'C:\Users\Gigabyte\Documents\aipollon claude\metro-city\stills' --scale 1.0 --shots 'C:\Users\Gigabyte\Documents\aipollon claude\metro-city\blender\shots_places_demo.json' 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT p08_river done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\metro-city\blender\build_pc.py' -- --shot p09_aerial --still 'C:\Users\Gigabyte\Documents\aipollon claude\metro-city\stills' --scale 1.0 --shots 'C:\Users\Gigabyte\Documents\aipollon claude\metro-city\blender\shots_places_demo.json' 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT p09_aerial done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\metro-city\blender\build_pc.py' -- --shot p10_rooftop --still 'C:\Users\Gigabyte\Documents\aipollon claude\metro-city\stills' --scale 1.0 --shots 'C:\Users\Gigabyte\Documents\aipollon claude\metro-city\blender\shots_places_demo.json' 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT p10_rooftop done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\metro-city\blender\build_pc.py' -- --shot p11_bridge --still 'C:\Users\Gigabyte\Documents\aipollon claude\metro-city\stills' --scale 1.0 --shots 'C:\Users\Gigabyte\Documents\aipollon claude\metro-city\blender\shots_places_demo.json' 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT p11_bridge done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\metro-city\blender\build_pc.py' -- --shot p12_deck --still 'C:\Users\Gigabyte\Documents\aipollon claude\metro-city\stills' --scale 1.0 --shots 'C:\Users\Gigabyte\Documents\aipollon claude\metro-city\blender\shots_places_demo.json' 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT p12_deck done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\metro-city\blender\build_pc.py' -- --shot p13_park --still 'C:\Users\Gigabyte\Documents\aipollon claude\metro-city\stills' --scale 1.0 --shots 'C:\Users\Gigabyte\Documents\aipollon claude\metro-city\blender\shots_places_demo.json' 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT p13_park done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
