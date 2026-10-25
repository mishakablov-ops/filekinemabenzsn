$ErrorActionPreference = 'Continue'
$root = 'C:\Users\Gigabyte\Documents\aipollon claude'
$proj = "$root\fr-klassika"
$PB = "$root\AIpollon-Reel-Studio\skills\reel-studio\engine\public\projects\fr-test-1b"
$B = (Get-Content "$proj\tools\blender_path.txt" -Raw).Trim()
& $B -b --factory-startup --python "$proj\blender\build.py" -- --shot pa_aerial --times 0 --scale 1.25 --nosave 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting' } | Select-Object -Last 25
& $B -b --factory-startup --python "$proj\blender\build.py" -- --shot pa_cafe --times 1.5 --scale 1.25 --nosave 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting' } | Select-Object -Last 25
Get-ChildItem "$proj\renders\stills" -ErrorAction SilentlyContinue | ForEach-Object { $_.Name }
Copy-Item "$proj\renders\stills\pa_aerial_0001.jpg" "$PB\stills\pa_aerial.jpg" -Force
Copy-Item "$proj\renders\stills\pa_cafe_0091.jpg" "$PB\stills\pa_cafe.jpg" -Force
Get-ChildItem "$PB\stills" | ForEach-Object { $_.Name + ' ' + $_.Length }
