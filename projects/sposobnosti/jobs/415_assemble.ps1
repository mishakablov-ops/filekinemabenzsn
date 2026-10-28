$ErrorActionPreference = 'Continue'
# clips -> KINEMA projects, covers of both parts (3:4 from the reel frame at the hook), render both parts, QA frames
$root = 'C:\Users\Gigabyte\Documents\aipollon claude'
$rs = "$root\KINEMA\skills\reel-studio"
$py = "$rs\.venv\Scripts\python.exe"
$P = "$root\sposobnosti"
$pub = "$rs\engine\public"
$ff = "$rs\.runtime\bin\ffmpeg.exe"
$env:PYTHONIOENCODING = 'utf-8'
$env:PATH = "$rs\.runtime\bin;" + $env:PATH

foreach ($n in 1, 2) { New-Item -ItemType Directory -Force -Path "$pub\projects\sposobnosti-$n\clips" | Out-Null }
New-Item -ItemType Directory -Force -Path "$root\output", "$P\qa" | Out-Null
Get-ChildItem "$P\clips\a*.mp4" | Copy-Item -Destination "$pub\projects\sposobnosti-1\clips\" -Force
Get-ChildItem "$P\clips\b*.mp4" | Copy-Item -Destination "$pub\projects\sposobnosti-2\clips\" -Force
$miss = @()
foreach ($i in 1..20) {
  $a = 'a{0:D2}' -f $i; $b = 'b{0:D2}' -f $i
  if (-not (Test-Path "$pub\projects\sposobnosti-1\clips\$a.mp4")) { $miss += $a }
  if (-not (Test-Path "$pub\projects\sposobnosti-2\clips\$b.mp4")) { $miss += $b }
}
if ($miss.Count) { "MISSING " + ($miss -join ' '); exit 1 }
"CLIPS OK"

# covers: the reel's own frame with the hook caption, cropped 3:4 like render.py does, 540x720
Push-Location "$rs\engine"
# Windows PowerShell 5.1 drops bare quotes in native arguments: \" survives as a quote for node
function Props($n) { return '{\"project\":\"sposobnosti-' + $n + '\",\"fps\":30}' }
foreach ($c in @(@(1, '2.9'), @(2, '1.6'))) {
  $n = $c[0]; $props = Props $n; $o = "$rs\engine\out\sp$n" + "_cover"
  & node tools/stills.mjs --comp Reel --props $props --seconds $c[1] --scale 1 --out $o 2>&1 | ForEach-Object { "$_" } | Select-Object -Last 2
  $png = Get-ChildItem "$o\f*.png" | Select-Object -First 1
  if ($png) {
    & $ff -hide_banner -loglevel error -y -i $png.FullName -vf "crop=1080:1440:0:240,scale=540:720" -q:v 2 "$pub\brand\tiles\cover-sposobnosti-$n.jpg"
    "COVER $n " + (Test-Path "$pub\brand\tiles\cover-sposobnosti-$n.jpg")
  } else { "COVER $n FAILED" }
}
# overlap QA on stills, one per second
foreach ($n in 1, 2) {
  $props = Props $n
  & node tools/stills.mjs --comp Reel --props $props --every 1 --scale 0.4 --qa --out "$rs\engine\out\sp$n`_st" --sheet "$P\qa\sp$n`_sheet.png" 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -match 'QA|sheet' }
}
Pop-Location

Push-Location $rs
foreach ($n in 1, 2) {
  $id = "sposobnosti-$n"
  $t0 = Get-Date
  & $py -I "$rs\scripts\render.py" $id --concurrency 6 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^\s*$|^Rendered|^Encoded|Copying public' } | Select-Object -Last 25
  "RENDER $id done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
  $mp4 = "$rs\engine\out\$id.mp4"
  if (Test-Path $mp4) {
    $dst = "$root\output\$id.mp4"
    $v = 2
    while (Test-Path $dst) { $dst = "$root\output\$id-v$v.mp4"; $v++ }
    Copy-Item $mp4 $dst
    "DELIVERED $dst"
    & $ff -hide_banner -loglevel error -y -i $mp4 -vf "fps=0.4,scale=270:-1" -q:v 4 "$P\qa\$id`_%02d.jpg"
  }
}
Pop-Location
