$ErrorActionPreference = 'Continue'
$root = 'C:\Users\Gigabyte\Documents\aipollon claude'
$rs = "$root\KINEMA\skills\reel-studio"
$py = "$rs\.venv\Scripts\python.exe"
$P = "$root\sposobnosti"
$env:PYTHONIOENCODING = 'utf-8'
$env:KINEMA_RS = $rs
$env:PATH = "$rs\.runtime\bin;" + $env:PATH
# the key goes into this process only, never printed
foreach ($l in Get-Content "$rs\.secrets.env") { if ($l -match '^\s*REPLICATE_API_TOKEN\s*=\s*(.+)$') { $env:REPLICATE_API_TOKEN = $Matches[1].Trim().Trim('"').Trim("'") } }
