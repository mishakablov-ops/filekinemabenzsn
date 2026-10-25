$ErrorActionPreference = 'Continue'
$root = 'C:\Users\Gigabyte\Documents\aipollon claude'
$log = "$root\jobs\logs\bg_211_fr_clips.log"
$rs = "$root\AIpollon-Reel-Studio\skills\reel-studio"
$ff = "$rs\.runtime\bin\ffmpeg.exe"
$B = (Get-Content "$root\style-test\tools\blender_path.txt" -Raw).Trim()
function L($m) { $m | Add-Content -Path $log -Encoding utf8 }
L ("start " + (Get-Date))
foreach ($s in 'fr2_walk', 'fr2_cafe', 'fr2_reveal', 'fr3_walk', 'fr3_cafe', 'fr3_reveal') {
  $t0 = Get-Date
  $proj = if ($s.StartsWith('fr2')) { 'fr-test-2' } else { 'fr-test-3' }
  Remove-Item -Recurse -Force "$root\style-test\renders\$s" -ErrorAction SilentlyContinue
  & $B -b --factory-startup --python "$root\style-test\blender\build.py" -- --shot $s --anim 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -match 'Error|Traceback|rror:|line \d' } | ForEach-Object { L $_ }
  New-Item -ItemType Directory -Force "$rs\engine\public\projects\$proj\clips" | Out-Null
  & $ff -hide_banner -loglevel error -y -framerate 60 -i "$root\style-test\renders\$s\%04d.jpg" -c:v libx264 -preset medium -crf 15 -bf 0 -g 30 -keyint_min 30 -sc_threshold 0 -pix_fmt yuv420p -movflags +faststart "$rs\engine\public\projects\$proj\clips\$s.mp4" 2>&1 | ForEach-Object { L "$_" }
  L ("CLIP $s done in " + [int]((Get-Date) - $t0).TotalSeconds + " s")
}
# wait for the voice job (normally long done)
for ($i = 0; $i -lt 60 -and -not (Test-Path "$rs\engine\public\projects\fr-test-3\words.json"); $i++) { Start-Sleep 20 }
$py = "$rs\.venv\Scripts\python.exe"
$env:PYTHONIOENCODING = 'utf-8'
$env:PATH = "$rs\.runtime\bin;" + $env:PATH
Set-Location $rs
foreach ($p in 'fr-test-2', 'fr-test-3') {
  $t0 = Get-Date
  & $py -I "$rs\scripts\render.py" $p --concurrency 6 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^\s*$' } | Select-Object -Last 25 | ForEach-Object { L $_ }
  L ("RENDER $p done in " + [int]((Get-Date) - $t0).TotalSeconds + " s")
}
L ("end " + (Get-Date))
"done" | Set-Content "$root\jobs\logs\bg_211_fr_clips.exit"
