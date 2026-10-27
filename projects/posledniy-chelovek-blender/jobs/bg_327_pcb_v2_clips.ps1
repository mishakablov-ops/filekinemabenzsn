$ErrorActionPreference = 'Continue'
$B = (Get-Content 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\tools\blender_path.txt' -Raw).Trim()
New-Item -ItemType Directory -Force -Path 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\clips_v2' | Out-Null
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\blender\build_pc.py' -- --shot wake --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\clips_v2\wake.mp4' --scale 1.0 --fps 60 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT wake done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\blender\build_pc.py' -- --shot count --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\clips_v2\count.mp4' --scale 1.0 --fps 60 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT count done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\blender\build_pc.py' -- --shot you --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\clips_v2\you.mp4' --scale 1.0 --fps 60 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT you done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\blender\build_pc.py' -- --shot cafe --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\clips_v2\cafe.mp4' --scale 1.0 --fps 60 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT cafe done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\blender\build_pc.py' -- --shot blackout --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\clips_v2\blackout.mp4' --scale 1.0 --fps 60 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT blackout done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\blender\build_pc.py' -- --shot station --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\clips_v2\station.mp4' --scale 1.0 --fps 60 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT station done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\blender\build_pc.py' -- --shot shops --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\clips_v2\shops.mp4' --scale 1.0 --fps 60 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT shops done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\blender\build_pc.py' -- --shot bread --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\clips_v2\bread.mp4' --scale 1.0 --fps 60 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT bread done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\blender\build_pc.py' -- --shot cans --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\clips_v2\cans.mp4' --scale 1.0 --fps 60 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT cans done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\blender\build_pc.py' -- --shot car --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\clips_v2\car.mp4' --scale 1.0 --fps 60 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT car done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\blender\build_pc.py' -- --shot fuel --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\clips_v2\fuel.mp4' --scale 1.0 --fps 60 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT fuel done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\blender\build_pc.py' -- --shot night --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\clips_v2\night.mp4' --scale 1.0 --fps 60 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT night done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\blender\build_pc.py' -- --shot third --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\clips_v2\third.mp4' --scale 1.0 --fps 60 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT third done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\blender\build_pc.py' -- --shot wolves --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\clips_v2\wolves.mp4' --scale 1.0 --fps 60 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT wolves done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\blender\build_pc.py' -- --shot chernobyl --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\clips_v2\chernobyl.mp4' --scale 1.0 --fps 60 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT chernobyl done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\blender\build_pc.py' -- --shot last --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\clips_v2\last.mp4' --scale 1.0 --fps 60 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT last done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\blender\build_pc.py' -- --shot room --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\clips_v2\room.mp4' --scale 1.0 --fps 60 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT room done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\blender\build_pc.py' -- --shot knock --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\clips_v2\knock.mp4' --scale 1.0 --fps 60 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT knock done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\blender\build_pc.py' -- --shot cta --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\posledniy-chelovek-blender\clips_v2\cta.mp4' --scale 1.0 --fps 60 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT cta done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
