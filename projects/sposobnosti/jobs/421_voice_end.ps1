$ErrorActionPreference = 'Continue'
# 28.10.2026: new last section of both parts (calm invitation to the profile instead of the ad); v2 voice kept in v2\
$root = 'C:\Users\Gigabyte\Documents\aipollon claude'
$rs = "$root\KINEMA\skills\reel-studio"
$py = "$rs\.venv\Scripts\python.exe"
$P = "$root\sposobnosti"
$env:PYTHONIOENCODING = 'utf-8'
$env:KINEMA_RS = $rs
$env:PATH = "$rs\.runtime\bin;" + $env:PATH
foreach ($n in 1, 2) {
  $W = "$rs\engine\public\projects\sposobnosti-$n"
  New-Item -ItemType Directory -Force -Path "$W\v2" | Out-Null
  foreach ($f in 'voice.wav', 'words.json', 'voice_manifest.json', 'tts_report.json', 'spec.json', 'script.md') {
    if ((Test-Path "$W\$f") -and -not (Test-Path "$W\v2\$f")) { Copy-Item "$W\$f" "$W\v2\$f" }
  }
}
# the key goes into this process only, never printed
foreach ($l in Get-Content "$rs\.secrets.env") { if ($l -match '^\s*REPLICATE_API_TOKEN\s*=\s*(.+)$') { $env:REPLICATE_API_TOKEN = $Matches[1].Trim().Trim('"').Trim("'") } }
$env:REPLICATE_JOB = 'sposobnosti-voice-end'
Set-Location "$P"
& $py -I "$P\engine\voice_sections.py" 1 2 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch 'symlink|Developer Mode|huggingface_hub' }
foreach ($n in 1, 2) { $W = "$rs\engine\public\projects\sposobnosti-$n"; if ((Get-Item "$W\words.json").LastWriteTime -gt (Get-Item "$W\v2\words.json").LastWriteTime) { "VOICE $n DONE" } else { "VOICE $n FAILED" } }
