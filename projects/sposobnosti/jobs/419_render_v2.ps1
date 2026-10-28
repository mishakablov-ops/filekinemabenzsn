$ErrorActionPreference = 'Continue'
# renders v2 of both parts: numbers kept out of the right 140 px below y 900 (TikTok buttons), 418 output stays as v1
$root = 'C:\Users\Gigabyte\Documents\aipollon claude'
$rs = "$root\KINEMA\skills\reel-studio"
$py = "$rs\.venv\Scripts\python.exe"
$P = "$root\sposobnosti"
$ff = "$rs\.runtime\bin\ffmpeg.exe"
$env:PYTHONIOENCODING = 'utf-8'
$env:PATH = "$rs\.runtime\bin;" + $env:PATH
New-Item -ItemType Directory -Force -Path "$root\output", "$P\qa" | Out-Null
Push-Location $rs
foreach ($n in 1, 2) {
  $id = "sposobnosti-$n"
  $t0 = Get-Date
  & $py -I "$rs\scripts\render.py" $id --concurrency 6 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^\s*$|^Rendered \d|^Encoded \d|^Copying public|^Bundling|^\S*\s+at ' }
  "RENDER $id exit $LASTEXITCODE in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
  $mp4 = "$rs\engine\out\$id.mp4"
  if ((Test-Path $mp4) -and (Get-Item $mp4).LastWriteTime -gt $t0) {
    $dst = "$root\output\$id.mp4"
    $v = 2
    while (Test-Path $dst) { $dst = "$root\output\$id-v$v.mp4"; $v++ }
    Copy-Item $mp4 $dst
    "DELIVERED $dst"
    & $ff -hide_banner -loglevel error -y -i $mp4 -vf "fps=0.5,scale=360:-1" -q:v 3 "$P\qa\$id`_%02d.jpg"
  } else { "NO NEW MP4 for $id" }
}
Pop-Location
