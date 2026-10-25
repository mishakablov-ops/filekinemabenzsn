# fr-gibrid: take A of the voice, storyboard -> spec.json, QA stills + contact sheet
$ErrorActionPreference = 'Continue'
$root = 'C:\Users\Gigabyte\Documents\aipollon claude'
$rs = "$root\AIpollon-Reel-Studio\skills\reel-studio"
$py = "$rs\.venv\Scripts\python.exe"
$env:PYTHONIOENCODING = 'utf-8'
$env:PATH = "$rs\.runtime\bin;" + $env:PATH
$P = "$rs\engine\public\projects\fr-gibrid"
foreach ($f in 'voice.wav', 'words.json', 'tts_report.json') { Copy-Item "$P\takes\a\$f" "$P\$f" -Force }
& $py -I "$root\fr-gibrid\storyboard.py" 2>&1 | ForEach-Object { "$_" }
& $py -I "$root\fr-gibrid\stills.py" 2>&1 | ForEach-Object { "$_" } 
'STILLS DONE'
