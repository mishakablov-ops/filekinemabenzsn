# France in the "gibrid" style: project, script lint, two Algenib voice takes (Gemini TTS)
$ErrorActionPreference = 'Continue'
$root = 'C:\Users\Gigabyte\Documents\aipollon claude'
$rs = "$root\AIpollon-Reel-Studio\skills\reel-studio"
$py = "$rs\.venv\Scripts\python.exe"
$env:PYTHONIOENCODING = 'utf-8'
$env:PATH = "$rs\.runtime\bin;" + $env:PATH
Set-Location $rs
$P = "$rs\engine\public\projects\fr-gibrid"
New-Item -ItemType Directory -Force $P, "$P\takes\a", "$P\takes\b" | Out-Null
Copy-Item "$root\fr-gibrid\script.md" "$P\script.md" -Force
& $py -I "$rs\scripts\script_lint.py" $P --mode explainer 2>&1 | ForEach-Object { "$_" }
if ($LASTEXITCODE -ne 0) { 'LINT FAILED'; exit }
$style = 'Read this Russian script aloud as a native Russian narrator of a short travel video about a morning in France: warm, pleasant, relaxed holiday mood with a gentle smile in the voice. Lively and engaging, never theatrical, never whispering. Brisk natural pace, very short pauses. The last two lines are friendly, upbeat and a little playful, talking straight to the viewer. Perfect native Russian pronunciation, no foreign accent.'
foreach ($k in 'a', 'b') {
  & $py -I "$rs\scripts\tts.py" $P --engine replicate --model gemini --voice Algenib --style $style --tighten 0.25 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch 'symlink|Developer|huggingface' } | Select-Object -Last 8
  foreach ($f in 'voice.wav', 'words.json', 'tts_report.json') { if (Test-Path "$P\$f") { Copy-Item "$P\$f" "$P\takes\$k\$f" -Force } }
  "TAKE $k"
  Get-Content "$P\takes\$k\tts_report.json" -ErrorAction SilentlyContinue
}
Copy-Item "$P\takes\a\voice.wav" "$root\_sync\frg_voice_a.wav" -Force
Copy-Item "$P\takes\b\voice.wav" "$root\_sync\frg_voice_b.wav" -Force
Copy-Item "$P\takes\a\words.json" "$root\_sync\frg_words_a.json" -Force
Copy-Item "$P\takes\b\words.json" "$root\_sync\frg_words_b.json" -Force
'VOICE DONE'
