$ErrorActionPreference = 'Continue'
# 30.10.2026: akademiya episode 3 again after QA: c12c 1.13 s on screen (was 0.98 s), no user-pack sfx (this KINEMA has no
# usr-* sounds). The graded clips from 616 stay. Delivered only when qa.md says PASS.
$root = 'C:\Users\Gigabyte\Documents\aipollon claude'
$rs = "$root\KINEMA\skills\reel-studio"
$py = "$rs\.venv\Scripts\python.exe"
$P = "$root\akademiya"
$ff = "$rs\.runtime\bin\ffmpeg.exe"
$id = 'akademiya-3'
$env:PYTHONIOENCODING = 'utf-8'
$env:PATH = "$rs\.runtime\bin;" + $env:PATH
Push-Location $rs
$t0 = Get-Date
& $py -I "$rs\scripts\render.py" $id --concurrency 6 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^\s*$|^Rendered \d|^Encoded \d|^Copying public|^Bundling|^\S*\s+at ' }
$rc = $LASTEXITCODE
"RENDER $id exit $rc in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$mp4 = "$rs\engine\out\$id.mp4"
$qa = "$rs\engine\out\$id`_qa.md"
$pass = (Test-Path $qa) -and ((Get-Content $qa -TotalCount 1) -match 'PASS')
Get-Content $qa -ErrorAction SilentlyContinue | Select-Object -First 30
if ($rc -ne 0 -or -not $pass) { "QA OR RENDER FAILED - not delivered" }
elseif ((Test-Path $mp4) -and (Get-Item $mp4).LastWriteTime -gt $t0) {
  $v = 1
  $out = "$root\output\$id-v$v.mp4"
  while (Test-Path $out) { $v++; $out = "$root\output\$id-v$v.mp4" }
  Copy-Item $mp4 $out
  "DELIVERED $out"
  & $ff -hide_banner -loglevel error -y -i $mp4 -vf "fps=0.5,scale=360:-1" -q:v 3 "$P\qa\$id`_v$v`_%02d.jpg"
} else { "NO NEW MP4 for $id" }
Pop-Location
