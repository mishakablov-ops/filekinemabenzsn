$ErrorActionPreference = 'Continue'
# 30.10.2026: akademiya episode 4 "Pyat utra", all 25 Blender clips (beach set akad_e4, shots-4.json; 1080x1920, 30 fps, Eevee 24 samples) -> akademiya\clips
$B = (Get-Content 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\tools\blender_path.txt' -Raw).Trim()
New-Item -ItemType Directory -Force -Path 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\clips' | Out-Null
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\blender\build_pc.py' -- --shot d00 --shots 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\blender\shots-4.json' --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\clips\d00.mp4' --scale 1.0 --fps 30 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT d00 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\blender\build_pc.py' -- --shot d00b --shots 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\blender\shots-4.json' --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\clips\d00b.mp4' --scale 1.0 --fps 30 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT d00b done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\blender\build_pc.py' -- --shot d01 --shots 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\blender\shots-4.json' --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\clips\d01.mp4' --scale 1.0 --fps 30 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT d01 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\blender\build_pc.py' -- --shot d02 --shots 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\blender\shots-4.json' --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\clips\d02.mp4' --scale 1.0 --fps 30 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT d02 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\blender\build_pc.py' -- --shot d03 --shots 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\blender\shots-4.json' --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\clips\d03.mp4' --scale 1.0 --fps 30 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT d03 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\blender\build_pc.py' -- --shot d04 --shots 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\blender\shots-4.json' --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\clips\d04.mp4' --scale 1.0 --fps 30 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT d04 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\blender\build_pc.py' -- --shot d05 --shots 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\blender\shots-4.json' --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\clips\d05.mp4' --scale 1.0 --fps 30 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT d05 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\blender\build_pc.py' -- --shot d05b --shots 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\blender\shots-4.json' --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\clips\d05b.mp4' --scale 1.0 --fps 30 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT d05b done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\blender\build_pc.py' -- --shot d06 --shots 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\blender\shots-4.json' --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\clips\d06.mp4' --scale 1.0 --fps 30 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT d06 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\blender\build_pc.py' -- --shot d07 --shots 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\blender\shots-4.json' --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\clips\d07.mp4' --scale 1.0 --fps 30 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT d07 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\blender\build_pc.py' -- --shot d07b --shots 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\blender\shots-4.json' --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\clips\d07b.mp4' --scale 1.0 --fps 30 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT d07b done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\blender\build_pc.py' -- --shot d08 --shots 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\blender\shots-4.json' --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\clips\d08.mp4' --scale 1.0 --fps 30 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT d08 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\blender\build_pc.py' -- --shot d09 --shots 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\blender\shots-4.json' --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\clips\d09.mp4' --scale 1.0 --fps 30 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT d09 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\blender\build_pc.py' -- --shot d10 --shots 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\blender\shots-4.json' --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\clips\d10.mp4' --scale 1.0 --fps 30 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT d10 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\blender\build_pc.py' -- --shot d11 --shots 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\blender\shots-4.json' --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\clips\d11.mp4' --scale 1.0 --fps 30 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT d11 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\blender\build_pc.py' -- --shot d12 --shots 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\blender\shots-4.json' --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\clips\d12.mp4' --scale 1.0 --fps 30 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT d12 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\blender\build_pc.py' -- --shot d13 --shots 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\blender\shots-4.json' --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\clips\d13.mp4' --scale 1.0 --fps 30 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT d13 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\blender\build_pc.py' -- --shot d14 --shots 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\blender\shots-4.json' --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\clips\d14.mp4' --scale 1.0 --fps 30 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT d14 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\blender\build_pc.py' -- --shot d15 --shots 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\blender\shots-4.json' --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\clips\d15.mp4' --scale 1.0 --fps 30 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT d15 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\blender\build_pc.py' -- --shot d16 --shots 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\blender\shots-4.json' --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\clips\d16.mp4' --scale 1.0 --fps 30 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT d16 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\blender\build_pc.py' -- --shot d17 --shots 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\blender\shots-4.json' --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\clips\d17.mp4' --scale 1.0 --fps 30 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT d17 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\blender\build_pc.py' -- --shot d18 --shots 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\blender\shots-4.json' --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\clips\d18.mp4' --scale 1.0 --fps 30 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT d18 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\blender\build_pc.py' -- --shot d19 --shots 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\blender\shots-4.json' --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\clips\d19.mp4' --scale 1.0 --fps 30 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT d19 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\blender\build_pc.py' -- --shot d19b --shots 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\blender\shots-4.json' --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\clips\d19b.mp4' --scale 1.0 --fps 30 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT d19b done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$t0 = Get-Date
& $B -b --factory-startup --python 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\blender\build_pc.py' -- --shot d20 --shots 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\blender\shots-4.json' --mp4 'C:\Users\Gigabyte\Documents\aipollon claude\akademiya\clips\d20.mp4' --scale 1.0 --fps 30 --samples 24 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }
"SHOT d20 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
