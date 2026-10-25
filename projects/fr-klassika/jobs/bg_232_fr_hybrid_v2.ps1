# hybrid v2: new stills from the fixed scene (wider café aisle, clip_start) + the boulevard clip, then the reel.
# Waits for bg_231 (full version) so the two Blender renders do not share the GPU.
$ErrorActionPreference = 'Continue'
$root = 'C:\Users\Gigabyte\Documents\aipollon claude'
$proj = "$root\fr-klassika"
$log = "$root\jobs\logs\bg_232_fr_hybrid_v2.log"
$rs = "$root\AIpollon-Reel-Studio\skills\reel-studio"
$PB = "$rs\engine\public\projects\fr-test-1b"
$B = (Get-Content "$proj\tools\blender_path.txt" -Raw).Trim()
$py = "$rs\.venv\Scripts\python.exe"
function L($m) { $m | Add-Content -Path $log -Encoding utf8 }
L ("queued " + (Get-Date))
$w = 0
while (-not (Test-Path "$root\jobs\logs\bg_231_fr_full_v3.exit") -and $w -lt 5400) { Start-Sleep -Seconds 20; $w += 20 }
L ("start " + (Get-Date))
$o = "$rs\engine\out\fr-test-1b.mp4"
if ((Test-Path $o) -and -not (Test-Path "$rs\engine\out\fr-test-1b-v1.mp4")) { Copy-Item $o "$rs\engine\out\fr-test-1b-v1.mp4" }   # keep version 1
New-Item -ItemType Directory -Force "$PB\stills_v1" | Out-Null
foreach ($s in 'pa_aerial', 'pa_cafe') { if (-not (Test-Path "$PB\stills_v1\$s.jpg")) { Copy-Item "$PB\stills\$s.jpg" "$PB\stills_v1\$s.jpg" } }
& $B -b --factory-startup --python "$proj\blender\build.py" -- --shot pa_aerial --times 0 --scale 1.25 --nosave 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -match 'Error|Traceback|STILL' } | ForEach-Object { L $_ }
& $B -b --factory-startup --python "$proj\blender\build.py" -- --shot pa_cafe --times 1.5 --scale 1.25 --nosave 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -match 'Error|Traceback|STILL' } | ForEach-Object { L $_ }
Copy-Item "$proj\renders\stills\pa_aerial_0001.jpg" "$PB\stills\pa_aerial.jpg" -Force
Copy-Item "$proj\renders\stills\pa_cafe_0091.jpg" "$PB\stills\pa_cafe.jpg" -Force
Copy-Item "$PB\stills\pa_cafe.jpg" "$root\_sync\hyb_cafe_v2.jpg" -Force
Copy-Item "$PB\stills\pa_aerial.jpg" "$root\_sync\hyb_aerial_v2.jpg" -Force
L ("STILLS done " + (Get-Date))
$env:PYTHONIOENCODING = 'utf-8'
$env:PATH = "$rs\.runtime\bin;" + $env:PATH
Push-Location $rs
$t0 = Get-Date
& $py -I "$rs\scripts\render.py" fr-test-1b --concurrency 6 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^\s*$|^Rendered|^Encoded|Copying public' } | Select-Object -Last 14 | ForEach-Object { L $_ }
L ("RENDER fr-test-1b done in " + [int]((Get-Date) - $t0).TotalSeconds + " s")
Pop-Location
L ("end " + (Get-Date))
"done" | Set-Content "$root\jobs\logs\bg_232_fr_hybrid_v2.exit"
