# edinyi-yazyk: storyboard -> final render + QA, copy to output\edinyi-yazyk.mp4
$ErrorActionPreference = 'Continue'
$root = 'C:\Users\Gigabyte\Documents\aipollon claude'
$rs = "$root\AIpollon-Reel-Studio\skills\reel-studio"
$py = "$rs\.venv\Scripts\python.exe"
$env:PYTHONIOENCODING = 'utf-8'
$env:PATH = "$rs\.runtime\bin;" + $env:PATH
Set-Location $rs
& $py -I "$root\edinyi-yazyk\storyboard.py" 2>&1 | ForEach-Object { "$_" }
$t0 = Get-Date
& $py -I "$rs\scripts\render.py" edinyi-yazyk --concurrency 6 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^\s*$|^Rendered|^Encoded|Copying public|Bundling' } | Select-Object -Last 20
"RENDER edinyi-yazyk done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
$o = "$rs\engine\out\edinyi-yazyk.mp4"
if ((Test-Path $o) -and (Get-Item $o).LastWriteTime -gt $t0) {
  New-Item -ItemType Directory -Force "$root\output" | Out-Null
  Copy-Item $o "$root\output\edinyi-yazyk.mp4" -Force
  Copy-Item $o "$root\_sync\edinyi-yazyk.mp4" -Force
  Get-Content "$rs\engine\out\edinyi-yazyk_qa.md" -ErrorAction SilentlyContinue
  'OUT OK'
}
