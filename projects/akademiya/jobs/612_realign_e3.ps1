$ErrorActionPreference = 'Continue'
# 30.10.2026: re-align akademiya episode 3 to the new caption markup (one // per line); the takes are kept, no new TTS
$root = 'C:\Users\Gigabyte\Documents\aipollon claude'
$rs = "$root\KINEMA\skills\reel-studio"
$py = "$rs\.venv\Scripts\python.exe"
$P = "$root\akademiya"
$env:PYTHONIOENCODING = 'utf-8'
$env:KINEMA_RS = $rs
$env:PATH = "$rs\.runtime\bin;" + $env:PATH
foreach ($l in Get-Content "$rs\.secrets.env") { if ($l -match '^\s*REPLICATE_API_TOKEN\s*=\s*(.+)$') { $env:REPLICATE_API_TOKEN = $Matches[1].Trim().Trim('"').Trim("'") } }
$env:REPLICATE_JOB = 'akademiya-3-voice'
$W = "$rs\engine\public\projects\akademiya-3"
$before = (Get-Item "$W\words.json").LastWriteTime
Set-Location "$P"
& $py -I "$P\engine\voice_sections.py" 3 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch 'symlink|Developer Mode|huggingface_hub' }
if ((Get-Item "$W\words.json").LastWriteTime -gt $before) { "REALIGN 3 DONE" } else { "REALIGN 3 FAILED" }
