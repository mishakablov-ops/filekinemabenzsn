$ErrorActionPreference = 'Continue'
# 28.10.2026: part 2 ends with a refined like / subscribe line (new section s6l); the voice before it kept in end-profile\
$root = 'C:\Users\Gigabyte\Documents\aipollon claude'
$rs = "$root\KINEMA\skills\reel-studio"
$py = "$rs\.venv\Scripts\python.exe"
$P = "$root\sposobnosti"
$env:PYTHONIOENCODING = 'utf-8'
$env:KINEMA_RS = $rs
$env:PATH = "$rs\.runtime\bin;" + $env:PATH
$W = "$rs\engine\public\projects\sposobnosti-2"
New-Item -ItemType Directory -Force -Path "$W\end-profile" | Out-Null
foreach ($f in 'voice.wav', 'words.json', 'voice_manifest.json', 'tts_report.json', 'spec.json', 'script.md') {
  if ((Test-Path "$W\$f") -and -not (Test-Path "$W\end-profile\$f")) { Copy-Item "$W\$f" "$W\end-profile\$f" }
}
# the key goes into this process only, never printed
foreach ($l in Get-Content "$rs\.secrets.env") { if ($l -match '^\s*REPLICATE_API_TOKEN\s*=\s*(.+)$') { $env:REPLICATE_API_TOKEN = $Matches[1].Trim().Trim('"').Trim("'") } }
$env:REPLICATE_JOB = 'sposobnosti-voice-like'
Set-Location "$P"
& $py -I "$P\engine\voice_sections.py" 2 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch 'symlink|Developer Mode|huggingface_hub' }
if ((Get-Item "$W\words.json").LastWriteTime -gt (Get-Item "$W\end-profile\words.json").LastWriteTime) { "VOICE 2 DONE" } else { "VOICE 2 FAILED" }
