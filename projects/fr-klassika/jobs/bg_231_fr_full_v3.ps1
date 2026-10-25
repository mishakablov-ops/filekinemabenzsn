# full Blender version v3: aerial (clip_start fix, no more road flicker) + café (wider aisle), then the reel
$ErrorActionPreference = 'Continue'
$root = 'C:\Users\Gigabyte\Documents\aipollon claude'
$proj = "$root\fr-klassika"
$log = "$root\jobs\logs\bg_231_fr_full_v3.log"
$rs = "$root\AIpollon-Reel-Studio\skills\reel-studio"
$P1 = "$rs\engine\public\projects\fr-test-1"
$ff = "$rs\.runtime\bin\ffmpeg.exe"
$B = (Get-Content "$proj\tools\blender_path.txt" -Raw).Trim()
$py = "$rs\.venv\Scripts\python.exe"
function L($m) { $m | Add-Content -Path $log -Encoding utf8 }
function Clip($s) {
  $t0 = Get-Date
  Remove-Item -Recurse -Force "$proj\renders\$s" -ErrorAction SilentlyContinue
  & $B -b --factory-startup --python "$proj\blender\build.py" -- --shot $s --anim 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -match 'Error|Traceback|rror:|line \d|BUILD|ANIM' } | ForEach-Object { L $_ }
  & $ff -hide_banner -loglevel error -y -framerate 60 -i "$proj\renders\$s\%04d.jpg" -c:v libx264 -preset medium -crf 15 -bf 0 -g 30 -keyint_min 30 -sc_threshold 0 -pix_fmt yuv420p -movflags +faststart "$P1\clips\$s.mp4" 2>&1 | ForEach-Object { L "$_" }
  L ("CLIP $s done in " + [int]((Get-Date) - $t0).TotalSeconds + " s")
}
function Reel($id) {
  $env:PYTHONIOENCODING = 'utf-8'
  $env:PATH = "$rs\.runtime\bin;" + $env:PATH
  Push-Location $rs
  $t0 = Get-Date
  & $py -I "$rs\scripts\render.py" $id --concurrency 6 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^\s*$|^Rendered|^Encoded|Copying public' } | Select-Object -Last 14 | ForEach-Object { L $_ }
  L ("RENDER $id done in " + [int]((Get-Date) - $t0).TotalSeconds + " s")
  Pop-Location
}
L ("start " + (Get-Date))
$o = "$rs\engine\out\fr-test-1.mp4"
if ((Test-Path $o) -and -not (Test-Path "$rs\engine\out\fr-test-1-v2.mp4")) { Copy-Item $o "$rs\engine\out\fr-test-1-v2.mp4" }   # keep version 2
Clip 'pa_aerial'
Clip 'pa_cafe'
Reel 'fr-test-1'
L ("end " + (Get-Date))
"done" | Set-Content "$root\jobs\logs\bg_231_fr_full_v3.exit"
