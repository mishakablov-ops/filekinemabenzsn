$ErrorActionPreference = 'Continue'
$rs = 'C:\Users\Gigabyte\Documents\aipollon claude\AIpollon-Reel-Studio\skills\reel-studio'
$py = "$rs\.venv\Scripts\python.exe"
$env:PYTHONIOENCODING = 'utf-8'
$env:PATH = "$rs\.runtime\bin;" + $env:PATH
Set-Location $rs
$P2 = "$rs\engine\public\projects\fr-test-2"
$P3 = "$rs\engine\public\projects\fr-test-3"
$dir = "$P2\voice_done.txt"
$style = 'Read this Russian script aloud as a native Russian travel narrator for a short holiday video: warm, pleasant, relaxed vacation mood with a gentle smile in the voice. Natural brisk pace, very short pauses, clear diction, never whispering, never theatrical. Perfect native Russian pronunciation, no foreign accent.'
& $py -I "$rs\scripts\tts.py" $P2 --engine replicate --model gemini --voice Algenib --style $style --tighten 0.25 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch 'symlink|Developer|huggingface' }
foreach ($f in 'voice.wav', 'words.json', 'tts_report.json') { if (Test-Path "$P2\$f") { Copy-Item "$P2\$f" "$P3\$f" -Force } }
if (Test-Path "$P3\words.json") { 'VOICE OK' | Set-Content $dir } else { 'VOICE FAILED' }
Get-Content "$P2\tts_report.json" -ErrorAction SilentlyContinue
