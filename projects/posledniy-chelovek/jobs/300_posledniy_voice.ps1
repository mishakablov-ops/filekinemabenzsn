# posledniy-chelovek: voice Algenib (Gemini 3.1 Flash TTS) by sections, 2 takes, Whisper check, pick, words.json.
# Scripts come from the repo copy in _sync\posledniy-chelovek\repo (unpacked from the cloud), python/ffmpeg/whisper from the PC's Reel Studio.
$ErrorActionPreference = 'Continue'
$root = 'C:\Users\Gigabyte\Documents\aipollon claude'
$pcrs = "$root\AIpollon-Reel-Studio\skills\reel-studio"
$py = "$pcrs\.venv\Scripts\python.exe"
$env:PYTHONIOENCODING = 'utf-8'
$env:PATH = "$pcrs\.runtime\bin;" + $env:PATH
$W = "$root\_sync\posledniy-chelovek\repo"
# the key goes into this process only, never printed
foreach ($l in Get-Content "$pcrs\.secrets.env") { if ($l -match '^\s*REPLICATE_API_TOKEN\s*=\s*(.+)$') { $env:REPLICATE_API_TOKEN = $Matches[1].Trim().Trim('"').Trim("'") } }
$env:REPLICATE_JOB = 'posledniy-chelovek'
Set-Location $W
& $py -I "$W\projects\posledniy-chelovek\engine\voice_sections.py" 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch 'symlink|Developer Mode|huggingface_hub' }
$P = "$W\kinema\skills\reel-studio\engine\public\projects\posledniy-chelovek"
if (Test-Path "$P\words.json") { 'VOICE DONE' } else { 'VOICE FAILED' }
