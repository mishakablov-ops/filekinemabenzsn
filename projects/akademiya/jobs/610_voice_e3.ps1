$ErrorActionPreference = 'Continue'
# 29.10.2026: voice of akademiya episode 3 (one take per section, a second only on a clear error)
$root = 'C:\Users\Gigabyte\Documents\aipollon claude'
$rs = "$root\KINEMA\skills\reel-studio"
$py = "$rs\.venv\Scripts\python.exe"
$P = "$root\akademiya"
$env:PYTHONIOENCODING = 'utf-8'
$env:KINEMA_RS = $rs
$env:PATH = "$rs\.runtime\bin;" + $env:PATH
# the key goes into this process only, never printed
foreach ($l in Get-Content "$rs\.secrets.env") { if ($l -match '^\s*REPLICATE_API_TOKEN\s*=\s*(.+)$') { $env:REPLICATE_API_TOKEN = $Matches[1].Trim().Trim('"').Trim("'") } }
$env:REPLICATE_JOB = 'akademiya-3-voice'
Set-Location "$P"
& $py -I "$P\engine\voice_sections.py" 3 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch 'symlink|Developer Mode|huggingface_hub' }
$W = "$rs\engine\public\projects\akademiya-3"
if (Test-Path "$W\words.json") { "VOICE 3 DONE" } else { "VOICE 3 FAILED" }
