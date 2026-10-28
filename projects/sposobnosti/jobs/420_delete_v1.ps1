$ErrorActionPreference = 'Continue'
# by the user's direct command (28.10.2026): remove the intermediate v1 of both parts, v2 stays
$o = 'C:\Users\Gigabyte\Documents\aipollon claude\output'
foreach ($f in 'sposobnosti-1.mp4', 'sposobnosti-2.mp4') {
  if (Test-Path "$o\$f") { Remove-Item -LiteralPath "$o\$f"; 'REMOVED ' + $f + ' ' + (-not (Test-Path "$o\$f")) } else { 'ABSENT ' + $f }
}
Get-ChildItem "$o\sposobnosti*" | ForEach-Object { 'LEFT ' + $_.Name }
