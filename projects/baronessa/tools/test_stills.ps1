param([string]$Shots = 'test_all.json', [string]$Only = '', [double]$T = 0.6, [double]$Scale = 0.4, [string]$Out = 'stills\test')
$ErrorActionPreference = 'Continue'
$P = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$B = (Get-Content "$P\tools\blender_path.txt" -Raw).Trim()
$J = Get-Content "$P\blender\$Shots" -Raw | ConvertFrom-Json
New-Item -ItemType Directory -Force "$P\$Out" | Out-Null
foreach ($s in $J.shots) {
  if ($Only -and -not ($Only.Split(',') -contains $s.id)) { continue }
  $t0 = Get-Date
  $log = & $B -b --factory-startup --python "$P\blender\build_pc.py" -- --shot $s.id --shots "$P\blender\$Shots" --still "$P\$Out" --scale $Scale --t $T --samples 16 2>&1 | ForEach-Object { "$_" }
  $err = $log | Where-Object { $_ -match 'Traceback|Error|line \d+, in' } | Select-Object -First 6
  "{0} {1:n0}s {2}" -f $s.id, ((Get-Date) - $t0).TotalSeconds, ($err -join ' | ')
}
