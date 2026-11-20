$ErrorActionPreference = 'Continue'
# 30.10.2026: voice of akademiya episodes 4 and 5 (one take per section, a second only on a clear error)
$root = 'C:\Users\Gigabyte\Documents\aipollon claude'
$rs = "$root\KINEMA\skills\reel-studio"
$py = "$rs\.venv\Scripts\python.exe"
$P = "$root\akademiya"
$env:PYTHONIOENCODING = 'utf-8'
$env:KINEMA_RS = $rs
$env:PATH = "$rs\.runtime\bin;" + $env:PATH
# the key goes into this process only, never printed
foreach ($l in Get-Content "$rs\.secrets.env") { if ($l -match '^\s*REPLICATE_API_TOKEN\s*=\s*(.+)$') { $env:REPLICATE_API_TOKEN = $Matches[1].Trim().Trim('"').Trim("'") } }
Set-Location "$P"
foreach ($ep in 4, 5) {
  $env:REPLICATE_JOB = "akademiya-$ep-voice"
  & $py -I "$P\engine\voice_sections.py" $ep 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch 'symlink|Developer Mode|huggingface_hub' }
  $W = "$rs\engine\public\projects\akademiya-$ep"
  if (Test-Path "$W\words.json") { "VOICE $ep DONE" } else { "VOICE $ep FAILED" }
}
