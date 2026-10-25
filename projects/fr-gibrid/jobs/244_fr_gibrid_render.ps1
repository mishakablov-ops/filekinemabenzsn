# fr-gibrid: final render + QA, copy to output\fr-gibrid.mp4
$ErrorActionPreference = 'Continue'
$root = 'C:\Users\Gigabyte\Documents\aipollon claude'
$rs = "$root\AIpollon-Reel-Studio\skills\reel-studio"
$py = "$rs\.venv\Scripts\python.exe"
$env:PYTHONIOENCODING = 'utf-8'
$env:PATH = "$rs\.runtime\bin;" + $env:PATH
Set-Location $rs
$t0 = Get-Date
& $py -I "$rs\scripts\render.py" fr-gibrid --concurrency 6 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^\s*$|^Rendered|^Encoded|Copying public' } | Select-Object -Last 25
"RENDER done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$o = "$rs\engine\out\fr-gibrid.mp4"
if (Test-Path $o) {
  New-Item -ItemType Directory -Force "$root\output" | Out-Null
  Copy-Item $o "$root\output\fr-gibrid.mp4" -Force
  Copy-Item $o "$root\_sync\fr-gibrid.mp4" -Force
  Get-Content "$rs\engine\out\fr-gibrid_qa.md" -ErrorAction SilentlyContinue
  'OUT OK'
}
