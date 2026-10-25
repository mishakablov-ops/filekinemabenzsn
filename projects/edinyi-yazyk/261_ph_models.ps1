# edinyi-yazyk: download realistic CC0 models from Poly Haven (glTF, 1k textures) into engine\public\models\ph\<id>\
$ErrorActionPreference = 'Continue'
$ProgressPreference = 'SilentlyContinue'
$root = 'C:\Users\Gigabyte\Documents\aipollon claude'
$dst = "$root\AIpollon-Reel-Studio\skills\reel-studio\engine\public\models\ph"
$UA = 'aipollon-asset-sync/1.0 (personal reels)'
New-Item -ItemType Directory -Force $dst | Out-Null
$ids = @('round_wooden_table_01','gallinera_chair','croissant','tea_set_01','potted_plant_01','potted_plant_02','potted_plant_04','standing_chalkboard_01','modern_ceiling_lamp_01','book_encyclopedia_set_01','decorative_book_set_01','desk_lamp_arm_01','modern_coffee_table_01','quiver_tree_01','dead_quiver_trunk','jacaranda_tree','wild_rooibos_bush','side_table_01','street_lamp_01','modular_street_seating','CoffeeCart_01','bar_chair_round_01','modern_arm_chair_01','Sofa_01','hanging_picture_frame_01','fancy_picture_frame_01','shrub_04','lemon','wooden_bowl_01','ceramic_vase_01','throw_pillows_01')
foreach ($id in $ids) {
  $dir = Join-Path $dst $id
  if (Test-Path (Join-Path $dir "$id.gltf")) { "skip $id"; continue }
  try { $f = Invoke-RestMethod -UserAgent $UA -Uri "https://api.polyhaven.com/files/$id" -TimeoutSec 60 } catch { "API FAIL $id $_"; continue }
  $g = $f.gltf.'1k'.gltf
  if (-not $g) { "NO GLTF $id"; continue }
  New-Item -ItemType Directory -Force $dir | Out-Null
  $ok = $true
  foreach ($p in $g.include.PSObject.Properties) {
    $out = Join-Path $dir ($p.Name -replace '/', '\')
    New-Item -ItemType Directory -Force (Split-Path $out) | Out-Null
    & curl.exe -sS -L -f --retry 3 -A $UA -o $out $p.Value.url
    if ($LASTEXITCODE -ne 0) { $ok = $false; "  FAIL $($p.Name)" }
  }
  & curl.exe -sS -L -f --retry 3 -A $UA -o (Join-Path $dir "$id.gltf") $g.url
  if ($LASTEXITCODE -ne 0) { $ok = $false }
  "{0} {1} {2:N1} MB" -f ($(if ($ok) { 'OK  ' } else { 'FAIL' })), $id, ((Get-ChildItem $dir -Recurse | Measure-Object Length -Sum).Sum / 1MB)
}
'MODELS DONE'
