# edinyi-yazyk: storyboard -> spec.json, QA stills + contact sheet
$ErrorActionPreference = 'Continue'
$root = 'C:\Users\Gigabyte\Documents\aipollon claude'
$rs = "$root\AIpollon-Reel-Studio\skills\reel-studio"
$py = "$rs\.venv\Scripts\python.exe"
$env:PYTHONIOENCODING = 'utf-8'
$env:PATH = "$rs\.runtime\bin;" + $env:PATH
& $py -I "$root\edinyi-yazyk\storyboard.py" 2>&1 | ForEach-Object { "$_" }
& $py -I "$root\edinyi-yazyk\stills.py" $args 2>&1 | ForEach-Object { "$_" }
'STILLS DONE'
