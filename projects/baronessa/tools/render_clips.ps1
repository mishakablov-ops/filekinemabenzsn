param([string]$Only = '', [int]$Samples = 24, [double]$Scale = 1.0, [string]$Shots = 'shots.json', [string]$OutDir = 'clips')
# Full mode: every shot of blender/shots.json -> clips/<id>.mp4 (30 fps, H.264, GOP 30, no B-frames). Shots whose clip
# already exists are skipped (delete the clip to re-render). Log: clips/render.log
$ErrorActionPreference = 'Continue'
$P = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$B = (Get-Content "$P\tools\blender_path.txt" -Raw).Trim()
$J = Get-Content "$P\blender\$Shots" -Raw -Encoding utf8 | ConvertFrom-Json
$out = "$P\$OutDir"
New-Item -ItemType Directory -Force $out | Out-Null
$log = "$out\render.log"
foreach ($s in $J.shots) {
  if ($Only -and -not ($Only.Split(',') -contains $s.id)) { continue }
  $mp4 = "$out\$($s.id).mp4"
  if (Test-Path $mp4) { "skip $($s.id)" | Add-Content $log; continue }
  $t0 = Get-Date
  $res = & $B -b --factory-startup --python "$P\blender\build_pc.py" -- --shot $s.id --shots "$P\blender\$Shots" --mp4 $mp4 --scale $Scale --fps 30 --samples $Samples 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -match 'CLIP|BUILD|Traceback|Error|line \d+, in' }
  ("{0} {1:n0}s {2}" -f $s.id, ((Get-Date) - $t0).TotalSeconds, ($res -join ' | ')) | Add-Content $log
}
"DONE" | Add-Content $log
