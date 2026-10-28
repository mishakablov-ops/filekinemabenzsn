$ErrorActionPreference = 'Continue'
# cover of part 2 again at 1.25 s: at 1.6 s the push into b02 was already on screen (split frame)
$root = 'C:\Users\Gigabyte\Documents\aipollon claude'
$rs = "$root\KINEMA\skills\reel-studio"
$py = "$rs\.venv\Scripts\python.exe"
$P = "$root\sposobnosti"
$ff = "$rs\.runtime\bin\ffmpeg.exe"
$log = "$root\jobs\logs\bg_416_cover2.log"
$env:PYTHONIOENCODING = 'utf-8'
$env:PATH = "$rs\.runtime\bin;" + $env:PATH
$env:KINEMA_RS = $rs
$tile = "$rs\engine\public\brand\tiles\cover-sposobnosti-2.jpg"
& {
  if (Test-Path $tile) { Copy-Item $tile "$P\qa\cover-sposobnosti-2-1.6s.jpg" -Force }
  Push-Location "$rs\engine"
  $o = "$rs\engine\out\sp2_cover125"
  & $py -I "$P\tools\rs_stills.py" "sposobnosti-2" $o --seconds 1.25 --scale 1 2>&1 | ForEach-Object { "$_" } | Select-Object -Last 3
  $png = Get-ChildItem "$o\f*.png" | Select-Object -First 1
  if ($png) {
    & $ff -hide_banner -loglevel error -y -i $png.FullName -vf "crop=1080:1440:0:240,scale=540:720" -q:v 2 $tile
    "COVER 2 " + (Get-Item $tile).LastWriteTime.ToString('o')
  } else { "COVER 2 FAILED" }
  Pop-Location
  "DONE"
} *>&1 | Out-File -FilePath $log -Encoding utf8
