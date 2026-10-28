$ErrorActionPreference = 'Continue'
# 28.10.2026 v4: new locations (tiny planet, clouds, roof, courtyard, stairwell), like/subscribe end of part 2;
# warm grade on all 40 clips -> KINEMA projects, new covers, QA sheets, render both parts as -v4
$root = 'C:\Users\Gigabyte\Documents\aipollon claude'
$rs = "$root\KINEMA\skills\reel-studio"
$py = "$rs\.venv\Scripts\python.exe"
$P = "$root\sposobnosti"
$pub = "$rs\engine\public"
$ff = "$rs\.runtime\bin\ffmpeg.exe"
$env:PYTHONIOENCODING = 'utf-8'
$env:PATH = "$rs\.runtime\bin;" + $env:PATH
New-Item -ItemType Directory -Force -Path "$root\output", "$P\qa\v4" | Out-Null

$miss = @()
foreach ($i in 1..20) {
  foreach ($s in @(('a{0:D2}' -f $i), ('b{0:D2}' -f $i))) { if (-not (Test-Path "$P\clips\$s.mp4")) { $miss += $s } }
}
if ($miss.Count) { "MISSING " + ($miss -join ' '); exit 1 }

# warm, a little brighter grade (wish of 28.10: a kind, interesting atmosphere); the Blender clips in sposobnosti\clips stay as they are
$G = 'eq=gamma=1.06:saturation=1.06,colorbalance=rs=0.03:gs=0.0:bs=-0.04:rm=0.04:gm=0.01:bm=-0.03:rh=0.02:bh=-0.03'
$ok = 0
foreach ($n in 1, 2) {
  $L = @('a', 'b')[$n - 1]
  $dst = "$pub\projects\sposobnosti-$n\clips"
  New-Item -ItemType Directory -Force -Path $dst | Out-Null
  foreach ($f in Get-ChildItem "$P\clips\$L*.mp4") {
    & $ff -hide_banner -loglevel error -y -i $f.FullName -vf $G -c:v libx264 -preset medium -crf 16 -pix_fmt yuv420p -bf 0 -g 30 -an "$dst\$($f.Name)"
    if ($LASTEXITCODE -eq 0) { $ok++ } else { "GRADE FAILED $($f.Name)" }
  }
}
"GRADED $ok clips"

# covers: the reel's own frame with the hook caption, 3:4, 540x720
Push-Location "$rs\engine"
$env:KINEMA_RS = $rs
foreach ($c in @(@(1, '2.9'), @(2, '1.25'))) {
  $n = $c[0]; $o = "$rs\engine\out\sp$n" + "_cover"
  & $py -I "$P\tools\rs_stills.py" "sposobnosti-$n" $o --seconds $c[1] --scale 1 2>&1 | ForEach-Object { "$_" } | Select-Object -Last 3
  $png = Get-ChildItem "$o\f*.png" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
  if ($png) {
    & $ff -hide_banner -loglevel error -y -i $png.FullName -vf "crop=1080:1440:0:240,scale=540:720" -q:v 2 "$pub\brand\tiles\cover-sposobnosti-$n.jpg"
    "COVER $n " + (Test-Path "$pub\brand\tiles\cover-sposobnosti-$n.jpg")
  } else { "COVER $n FAILED" }
}
# overlap QA on stills, one per second
foreach ($n in 1, 2) {
  & $py -I "$P\tools\rs_stills.py" "sposobnosti-$n" "$rs\engine\out\sp$n`_st" --every 1 --scale 0.4 --qa --sheet "$P\qa\v4\sp$n`_sheet.png" 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -match 'QA|sheet' }
}
Pop-Location

Push-Location $rs
foreach ($n in 1, 2) {
  $id = "sposobnosti-$n"
  $t0 = Get-Date
  & $py -I "$rs\scripts\render.py" $id --concurrency 6 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^\s*$|^Rendered \d|^Encoded \d|^Copying public|^Bundling|^\S*\s+at ' }
  "RENDER $id exit $LASTEXITCODE in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
  $mp4 = "$rs\engine\out\$id.mp4"
  if ((Test-Path $mp4) -and (Get-Item $mp4).LastWriteTime -gt $t0) {
    $v = 4
    $dst = "$root\output\$id-v$v.mp4"
    while (Test-Path $dst) { $v++; $dst = "$root\output\$id-v$v.mp4" }
    Copy-Item $mp4 $dst
    "DELIVERED $dst"
    & $ff -hide_banner -loglevel error -y -i $mp4 -vf "fps=0.5,scale=360:-1" -q:v 3 "$P\qa\v4\$id`_%02d.jpg"
    & $ff -hide_banner -loglevel error -y -sseof -7 -i $mp4 -vf "fps=2,scale=360:-1" -q:v 3 "$P\qa\v4\$id`_end%02d.jpg"
  } else { "NO NEW MP4 for $id" }
}
Pop-Location
