# fr-gibrid: storyboard without the terrace plants (QA collision), render again
$ErrorActionPreference = 'Continue'
$root = 'C:\Users\Gigabyte\Documents\aipollon claude'
$rs = "$root\AIpollon-Reel-Studio\skills\reel-studio"
$py = "$rs\.venv\Scripts\python.exe"
$env:PYTHONIOENCODING = 'utf-8'
$env:PATH = "$rs\.runtime\bin;" + $env:PATH
Set-Location $rs
& $py -I "$root\fr-gibrid\storyboard.py" 2>&1 | ForEach-Object { "$_" }
$t0 = Get-Date
& $py -I "$rs\scripts\render.py" fr-gibrid --concurrency 6 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^\s*$|^Rendered|^Encoded|Copying public|Bundling' } | Select-Object -Last 14
"RENDER fr-gibrid done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$o = "$rs\engine\out\fr-gibrid.mp4"
if ((Test-Path $o) -and (Get-Item $o).LastWriteTime -gt $t0) {
  Copy-Item $o "$root\_sync\fr-gibrid.mp4" -Force
  Copy-Item $o "$root\output\fr-gibrid.mp4" -Force
  Get-Content "$rs\engine\out\fr-gibrid_qa.md" -ErrorAction SilentlyContinue
  'OUT OK'
}
