$ErrorActionPreference = 'Continue'
$root = 'C:\Users\Gigabyte\Documents\aipollon claude'
$proj = "$root\fr-klassika"
$log = "$root\jobs\logs\bg_220_fr_klassika.log"
$rs = "$root\AIpollon-Reel-Studio\skills\reel-studio"
$P1 = "$rs\engine\public\projects\fr-test-1"
$ff = "$rs\.runtime\bin\ffmpeg.exe"
$B = (Get-Content "$proj\tools\blender_path.txt" -Raw).Trim()
function L($m) { $m | Add-Content -Path $log -Encoding utf8 }
L ("start " + (Get-Date))
# same voice as the style 2/3 tests
foreach ($f in 'voice.wav', 'words.json', 'tts_report.json') { Copy-Item "$rs\engine\public\projects\fr-test-2\$f" "$P1\$f" -Force }
foreach ($s in 'pa_aerial', 'pa_cafe', 'pa_blvd') {
  $t0 = Get-Date
  Remove-Item -Recurse -Force "$proj\renders\$s" -ErrorAction SilentlyContinue
  & $B -b --factory-startup --python "$proj\blender\build.py" -- --shot $s --anim 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -match 'Error|Traceback|rror:|line \d|BUILD|ANIM' } | ForEach-Object { L $_ }
  New-Item -ItemType Directory -Force "$P1\clips" | Out-Null
  & $ff -hide_banner -loglevel error -y -framerate 60 -i "$proj\renders\$s\%04d.jpg" -c:v libx264 -preset medium -crf 15 -bf 0 -g 30 -keyint_min 30 -sc_threshold 0 -pix_fmt yuv420p -movflags +faststart "$P1\clips\$s.mp4" 2>&1 | ForEach-Object { L "$_" }
  L ("CLIP $s done in " + [int]((Get-Date) - $t0).TotalSeconds + " s")
}
$py = "$rs\.venv\Scripts\python.exe"
$env:PYTHONIOENCODING = 'utf-8'
$env:PATH = "$rs\.runtime\bin;" + $env:PATH
Set-Location $rs
$t0 = Get-Date
& $py -I "$rs\scripts\render.py" fr-test-1 --concurrency 6 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^\s*$|^Rendered|^Encoded' } | Select-Object -Last 20 | ForEach-Object { L $_ }
L ("RENDER fr-test-1 done in " + [int]((Get-Date) - $t0).TotalSeconds + " s")
L ("end " + (Get-Date))
"done" | Set-Content "$root\jobs\logs\bg_220_fr_klassika.exit"
