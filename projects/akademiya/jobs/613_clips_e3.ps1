$ErrorActionPreference = 'Continue'
# 30.10.2026: akademiya episode 3, all 29 Blender clips (1080x1920, 30 fps, Eevee 24 samples) -> akademiya\clips
$B = (Get-Content 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\tools\blender_path.txt' -Raw).Trim()
New-Item -ItemType Directory -Force -Path 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\clips' | Out-Null
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\blender\build_pc.py' -- --shot c00 --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\clips\c00.mp4' --scale 1.0 --fps 30 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT c00 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\blender\build_pc.py' -- --shot c00b --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\clips\c00b.mp4' --scale 1.0 --fps 30 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT c00b done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\blender\build_pc.py' -- --shot c01 --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\clips\c01.mp4' --scale 1.0 --fps 30 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT c01 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\blender\build_pc.py' -- --shot c02 --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\clips\c02.mp4' --scale 1.0 --fps 30 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT c02 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\blender\build_pc.py' -- --shot c03 --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\clips\c03.mp4' --scale 1.0 --fps 30 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT c03 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\blender\build_pc.py' -- --shot c04 --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\clips\c04.mp4' --scale 1.0 --fps 30 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT c04 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\blender\build_pc.py' -- --shot c05 --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\clips\c05.mp4' --scale 1.0 --fps 30 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT c05 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\blender\build_pc.py' -- --shot c06 --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\clips\c06.mp4' --scale 1.0 --fps 30 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT c06 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\blender\build_pc.py' -- --shot c07 --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\clips\c07.mp4' --scale 1.0 --fps 30 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT c07 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\blender\build_pc.py' -- --shot c08 --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\clips\c08.mp4' --scale 1.0 --fps 30 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT c08 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\blender\build_pc.py' -- --shot c09 --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\clips\c09.mp4' --scale 1.0 --fps 30 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT c09 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\blender\build_pc.py' -- --shot c10 --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\clips\c10.mp4' --scale 1.0 --fps 30 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT c10 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\blender\build_pc.py' -- --shot c11 --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\clips\c11.mp4' --scale 1.0 --fps 30 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT c11 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\blender\build_pc.py' -- --shot c12 --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\clips\c12.mp4' --scale 1.0 --fps 30 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT c12 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\blender\build_pc.py' -- --shot c12b --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\clips\c12b.mp4' --scale 1.0 --fps 30 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT c12b done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\blender\build_pc.py' -- --shot c12c --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\clips\c12c.mp4' --scale 1.0 --fps 30 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT c12c done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\blender\build_pc.py' -- --shot c13 --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\clips\c13.mp4' --scale 1.0 --fps 30 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT c13 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\blender\build_pc.py' -- --shot c14 --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\clips\c14.mp4' --scale 1.0 --fps 30 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT c14 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\blender\build_pc.py' -- --shot c15 --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\clips\c15.mp4' --scale 1.0 --fps 30 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT c15 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\blender\build_pc.py' -- --shot c16 --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\clips\c16.mp4' --scale 1.0 --fps 30 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT c16 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\blender\build_pc.py' -- --shot c17 --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\clips\c17.mp4' --scale 1.0 --fps 30 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT c17 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\blender\build_pc.py' -- --shot c18 --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\clips\c18.mp4' --scale 1.0 --fps 30 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT c18 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\blender\build_pc.py' -- --shot c19 --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\clips\c19.mp4' --scale 1.0 --fps 30 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT c19 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\blender\build_pc.py' -- --shot c19b --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\clips\c19b.mp4' --scale 1.0 --fps 30 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT c19b done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\blender\build_pc.py' -- --shot c19c --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\clips\c19c.mp4' --scale 1.0 --fps 30 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT c19c done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\blender\build_pc.py' -- --shot c20 --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\clips\c20.mp4' --scale 1.0 --fps 30 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT c20 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\blender\build_pc.py' -- --shot c21 --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\clips\c21.mp4' --scale 1.0 --fps 30 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT c21 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\blender\build_pc.py' -- --shot c21b --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\clips\c21b.mp4' --scale 1.0 --fps 30 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT c21b done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\blender\build_pc.py' -- --shot c22 --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\clips\c22.mp4' --scale 1.0 --fps 30 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT c22 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
