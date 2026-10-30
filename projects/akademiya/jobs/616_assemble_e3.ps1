$ErrorActionPreference = 'Continue'
# 30.10.2026: akademiya episode 3 - the same warm grade as sposobnosti v4 on the 29 clips -> KINEMA project akademiya-3,
# cover, overlap QA stills (one per second), render (render.py runs qa.py), deliver to output\
$root = 'C:\Users\Gigabyte\Documents\aipollon claude'
$rs = "$root\KINEMA\skills\reel-studio"
$py = "$rs\.venv\Scripts\python.exe"
$P = "$root\akademiya"
$pub = "$rs\engine\public"
$ff = "$rs\.runtime\bin\ffmpeg.exe"
$id = 'akademiya-3'
$env:PYTHONIOENCODING = 'utf-8'
$env:PATH = "$rs\.runtime\bin;" + $env:PATH
New-Item -ItemType Directory -Force -Path "$root\output", "$P\qa" | Out-Null

$shots = 'c00 c00b c01 c02 c03 c04 c05 c06 c07 c08 c09 c10 c11 c12 c12b c12c c13 c14 c15 c16 c17 c18 c19 c19b c19c c20 c21 c21b c22'.Split(' ')
$miss = @($shots | Where-Object { -not (Test-Path "$P\clips\$_.mp4") })
if ($miss.Count) { "MISSING " + ($miss -join ' '); exit 1 }

$G = 'eq=gamma=1.06:saturation=1.06,colorbalance=rs=0.03:gs=0.0:bs=-0.04:rm=0.04:gm=0.01:bm=-0.03:rh=0.02:bh=-0.03'
$dst = "$pub\projects\$id\clips"
New-Item -ItemType Directory -Force -Path $dst | Out-Null
$ok = 0
foreach ($s in $shots) {
  & $ff -hide_banner -loglevel error -y -i "$P\clips\$s.mp4" -vf $G -c:v libx264 -preset medium -crf 16 -pix_fmt yuv420p -bf 0 -g 30 -an "$dst\$s.mp4"
  if ($LASTEXITCODE -eq 0) { $ok++ } else { "GRADE FAILED $s" }
}
"GRADED $ok clips"

Push-Location "$rs\engine"
$env:KINEMA_RS = $rs
$o = "$rs\engine\out\ak3_cover"
& $py -I "$root\sposobnosti\tools\rs_stills.py" $id $o --seconds 2.9 --scale 1 2>&1 | ForEach-Object { "$_" } | Select-Object -Last 3
$png = Get-ChildItem "$o\f*.png" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if ($png) {
  & $ff -hide_banner -loglevel error -y -i $png.FullName -vf "crop=1080:1440:0:240,scale=540:720" -q:v 2 "$pub\brand\tiles\cover-$id.jpg"
  "COVER " + (Test-Path "$pub\brand\tiles\cover-$id.jpg")
} else { "COVER FAILED" }
& $py -I "$root\sposobnosti\tools\rs_stills.py" $id "$rs\engine\out\ak3_st" --every 1 --scale 0.4 --qa --sheet "$P\qa\ak3_sheet.png" 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -match 'QA|sheet' }
Pop-Location

Push-Location $rs
$t0 = Get-Date
& $py -I "$rs\scripts\render.py" $id --concurrency 6 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^\s*$|^Rendered \d|^Encoded \d|^Copying public|^Bundling|^\S*\s+at ' }
$rc = $LASTEXITCODE
"RENDER $id exit $rc in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$mp4 = "$rs\engine\out\$id.mp4"
Get-Content "$rs\engine\out\$id`_qa.md" -ErrorAction SilentlyContinue | Select-Object -First 40
if ($rc -ne 0) { "QA OR RENDER FAILED - not delivered" }
elseif ((Test-Path $mp4) -and (Get-Item $mp4).LastWriteTime -gt $t0) {
  $v = 1
  $out = "$root\output\$id-v$v.mp4"
  while (Test-Path $out) { $v++; $out = "$root\output\$id-v$v.mp4" }
  Copy-Item $mp4 $out
  "DELIVERED $out"
  & $ff -hide_banner -loglevel error -y -i $mp4 -vf "fps=0.5,scale=360:-1" -q:v 3 "$P\qa\$id`_%02d.jpg"
  & $ff -hide_banner -loglevel error -y -sseof -7 -i $mp4 -vf "fps=2,scale=360:-1" -q:v 3 "$P\qa\$id`_end%02d.jpg"
} else { "NO NEW MP4 for $id" }
Pop-Location
