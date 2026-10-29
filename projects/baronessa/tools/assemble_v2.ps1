param([int]$V = 1, [switch]$SkipGrade)
# «Баронесса-пулемётчица»: grade the Blender clips -> KINEMA project, music bed, spec, stills QA, render -> output\baronessa-v<V>.mp4
# Grades: warm (like Klassika) everywhere; the 1940s battles c08..c25 as an old newsreel (mike 28.10: «добавь про 40-ые»):
# half-desaturated sepia with grain, the orange jokes still readable.
$ErrorActionPreference = 'Continue'
$root = 'C:\Users\Gigabyte\Documents\aipollon claude'
$rs = "$root\KINEMA\skills\reel-studio"
$py = "$rs\.venv\Scripts\python.exe"
$P = "$root\baronessa"
$pub = "$rs\engine\public"
$ff = 'ffmpeg'
$env:PYTHONIOENCODING = 'utf-8'
$env:PATH = "$rs\.runtime\bin;" + $env:PATH
$J = Get-Content "$P\blender\shots_v2.json" -Raw -Encoding utf8 | ConvertFrom-Json
$miss = @($J.shots | Where-Object { -not (Test-Path "$P\clips_v2\$($_.id).mp4") } | ForEach-Object { $_.id })
if ($miss.Count) { "MISSING " + ($miss -join ' '); exit 1 }

$WARM = 'eq=gamma=1.04:saturation=1.05,colorbalance=rs=0.03:gs=0.0:bs=-0.04:rm=0.04:gm=0.01:bm=-0.03:rh=0.02:bh=-0.03'
$HARD = 'eq=contrast=1.12:saturation=1.12:gamma=0.98,colorbalance=rs=0.05:bs=-0.05:rh=0.04:bh=-0.06:rm=0.03:bm=-0.02,vignette=PI/5'
$NEWS = 'hue=s=0.45,colorbalance=rs=0.07:gs=0.02:bs=-0.07:rm=0.05:bm=-0.05,eq=contrast=1.08:gamma=1.02,noise=alls=9:allf=t,vignette=PI/5'
$dst = "$pub\projects\baronessa-v2\clips"
New-Item -ItemType Directory -Force -Path $dst | Out-Null
$ok = 0
foreach ($s in $J.shots) {
  if ($SkipGrade) { break }
  $g = $HARD
  & $ff -hide_banner -loglevel error -y -i "$P\clips_v2\$($s.id).mp4" -vf $g -c:v libx264 -preset medium -crf 16 -pix_fmt yuv420p -bf 0 -g 30 -keyint_min 30 -an "$dst\$($s.id).mp4"
  if ($LASTEXITCODE -eq 0) { $ok++ } else { "GRADE FAILED $($s.id)" }
}
"GRADED $ok clips"

$dur = [double]$J.end
& $py -I "$P\tools\music_bed.py" --dur $dur --base trap-hype --layer dark-cinematic --up 42:48 --down 126:131 --peak 0.6 --rest 0.25 --out "$pub\projects\baronessa-v2\music-bed.wav"
& $py -I "$P\engine\storyboard_v2.py"

Push-Location $rs
$t0 = Get-Date
& $py -I "$rs\scripts\render.py" baronessa-v2 --concurrency 6 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^\s*$|^Rendered \d|^Encoded \d|^Copying public|^Bundling|^\S*\s+at ' }
"RENDER exit $LASTEXITCODE in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$mp4 = "$rs\engine\out\baronessa-v2.mp4"
if ((Test-Path $mp4) -and (Get-Item $mp4).LastWriteTime -gt $t0) {
  $out = "$root\output\baronessa-v2-$V.mp4"
  while (Test-Path $out) { $V++; $out = "$root\output\baronessa-v2-$V.mp4" }
  Copy-Item $mp4 $out
  Copy-Item $mp4 "$P\out\baronessa-v2-$V.mp4"
  "DELIVERED $out"
  New-Item -ItemType Directory -Force -Path "$P\qa\v$V" | Out-Null
  & $ff -hide_banner -loglevel error -y -i $mp4 -vf "fps=0.5,scale=360:-1" -q:v 3 "$P\qa\v$V\f_%02d.jpg"
  & $py -I "$rs\scripts\qa.py" $out 2>&1 | ForEach-Object { "$_" } | Select-Object -Last 25
} else { "NO NEW MP4" }
Pop-Location
