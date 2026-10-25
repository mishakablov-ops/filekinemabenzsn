# download_assets.ps1 - fills "aipollon claude\assets3d" with free CC0 3D assets.
# Sources: Kenney (kenney.nl), Quaternius (via opengameart.org), Poly Haven (models + HDRI), ambientCG (PBR textures).
# Safe to re-run: anything already downloaded is skipped. Nothing outside assets3d is touched.
param(
  [string]$Root = 'C:\Users\Gigabyte\Documents\aipollon claude\assets3d',
  [string]$Only = ''   # e.g. -Only kenney,quaternius,polyhaven,hdri,ambientcg
)
$ErrorActionPreference = 'Continue'
$ProgressPreference = 'SilentlyContinue'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$UA = 'aipollon-asset-sync/1.0 (personal Blender reels)'
$MinFreeGB = 15

New-Item -ItemType Directory -Force -Path $Root | Out-Null
$manifest = Join-Path $Root 'manifest.csv'
if (-not (Test-Path $manifest)) { 'source,pack,license,path,url' | Set-Content -Path $manifest -Encoding utf8 }
$script:ok = 0; $script:fail = 0; $script:skip = 0
$failLog = Join-Path $Root '_tools\failed.txt'

function Want($k) { return ($Only -eq '') -or (($Only -split ',') -contains $k) }
function Log($m) { Write-Host ("[{0}] {1}" -f (Get-Date -Format T), $m) }
function FreeGB {
  $d = (Get-Item $Root).PSDrive.Name
  return [math]::Round((Get-PSDrive $d).Free / 1GB, 1)
}
function Note($src, $pack, $path, $url) {
  ('"{0}","{1}","CC0","{2}","{3}"' -f $src, $pack, $path.Replace($Root + '\', ''), $url) | Add-Content -Path $manifest -Encoding utf8
}
function Get-File($url, $dst) {
  if ((Test-Path $dst) -and ((Get-Item $dst).Length -gt 0)) { $script:skip++; return $true }
  if ((FreeGB) -lt $MinFreeGB) { Log "STOP: less than $MinFreeGB GB free on disk"; exit 2 }
  New-Item -ItemType Directory -Force -Path (Split-Path $dst) | Out-Null
  $tmp = "$dst.part"
  & curl.exe -sS -L -f --retry 3 --retry-delay 3 -A $UA -o $tmp $url
  if ($LASTEXITCODE -eq 0 -and (Test-Path $tmp)) { Move-Item -Force $tmp $dst; $script:ok++; return $true }
  Remove-Item -Force $tmp -ErrorAction SilentlyContinue
  $script:fail++; "$url -> $dst" | Add-Content $failLog; Log "  FAIL $url"; return $false
}
function Unpack($zip, $dir) {
  if (Test-Path (Join-Path $dir '.unpacked')) { return }
  New-Item -ItemType Directory -Force -Path $dir | Out-Null
  & tar.exe -xf $zip -C $dir 2>$null
  if ($LASTEXITCODE -ne 0) { try { Expand-Archive -Force -LiteralPath $zip -DestinationPath $dir } catch { Log "  UNPACK FAIL $zip"; return } }
  Set-Content (Join-Path $dir '.unpacked') 'ok'
  Remove-Item -Force -LiteralPath $zip -ErrorAction SilentlyContinue
}
function Scrape($page, $pattern) {
  try { $html = (Invoke-WebRequest -UseBasicParsing -UserAgent $UA -Uri $page -TimeoutSec 60).Content }
  catch { Log "  page FAIL $page"; $script:fail++; "$page (page)" | Add-Content $failLog; return @() }
  $base = ([Uri]$page).GetLeftPart([UriPartial]::Authority)
  $found = [regex]::Matches($html, $pattern) | ForEach-Object { $_.Value } | Sort-Object -Unique
  return $found | ForEach-Object { if ($_.StartsWith('/')) { $base + $_ } else { $_ } }
}

# ---------------------------------------------------------------- Kenney
$kenney = @{
  'city'      = 'city-kit-commercial','city-kit-suburban','city-kit-industrial','city-kit-roads','3d-road-tiles','building-kit','modular-buildings','retro-urban-kit','mini-market','factory-kit'
  'vehicles'  = 'car-kit','train-kit','watercraft-kit','racing-kit'
  'people'    = 'animated-characters-protagonists','animated-characters-survivors','animated-characters-retro','mini-characters','blocky-characters'
  'nature'    = 'nature-kit','survival-kit'
  'interior'  = 'furniture-kit','food-kit'
}
if (Want 'kenney') {
  Log '== Kenney'
  foreach ($cat in $kenney.Keys) { foreach ($slug in $kenney[$cat]) {
    $dir = Join-Path $Root "$cat\kenney\$slug"
    if (Test-Path (Join-Path $dir '.unpacked')) { $script:skip++; continue }
    $urls = Scrape "https://kenney.nl/assets/$slug" '(https://kenney\.nl)?/media/pages/assets/[^"''\s<>]+?\.zip'
    if (-not $urls) { Log "  no zip on page $slug"; $script:fail++; "kenney $slug (no zip link)" | Add-Content $failLog; continue }
    $url = @($urls)[0]; $zip = Join-Path $Root "_downloads\kenney\$slug.zip"
    Log "  $slug"
    if (Get-File $url $zip) { Unpack $zip $dir; Note 'Kenney' $slug $dir $url }
  } }
}

# ---------------------------------------------------------------- Quaternius (mirrored by the author on opengameart.org)
$quat = @{
  'people'   = 'animated-characters-pack','animated-human-low-poly','lowpoly-posed-humans','universal-animation-library','universal-animation-library-2'
  'vehicles' = 'lowpoly-cars','low-poly-cars-0','lowpoly-public-transport','lowpoly-ship-pack'
  'city'     = 'lowpoly-buildings','lowpoly-buildings-pack','lowpoly-modular-street-pack'
  'nature'   = 'low-poly-nature-pack-1','lowpoly-nature-pack','lowpoly-textured-trees','stylized-nature-megakit','lowpoly-crops-pack','5-low-poly-trees','low-poly-desert-assets'
  'interior' = 'furniture-low-poly','lowpoly-house-interior-pack','low-poly-furniture-1','low-poly-food-pack'
  'animals'  = 'lowpoly-animated-farm-animal-pack','animated-animales-low-poly','5-low-poly-animals'
}
if (Want 'quaternius') {
  Log '== Quaternius'
  foreach ($cat in $quat.Keys) { foreach ($slug in $quat[$cat]) {
    $dir = Join-Path $Root "$cat\quaternius\$slug"
    if (Test-Path (Join-Path $dir '.unpacked')) { $script:skip++; continue }
    $urls = Scrape "https://opengameart.org/content/$slug" 'https://opengameart\.org/sites/default/files/[^"''\s<>]+?\.(zip|rar|7z|blend)'
    if (-not $urls) { Log "  no files on page $slug"; $script:fail++; "quaternius $slug (no file link)" | Add-Content $failLog; continue }
    Log "  $slug"
    $allOk = $true
    foreach ($u in $urls) {
      $name = [Uri]::UnescapeDataString(($u -split '/')[-1])
      $f = Join-Path $Root "_downloads\quaternius\$slug\$name"
      if (Get-File $u $f) {
        if ($name -match '\.(zip|rar|7z)$') { $sub = Join-Path $dir ([IO.Path]::GetFileNameWithoutExtension($name)); Unpack $f $sub }
        else { New-Item -ItemType Directory -Force -Path $dir | Out-Null; Copy-Item -Force $f $dir }
        Note 'Quaternius' $slug $dir $u
      } else { $allOk = $false }
    }
    if ($allOk) { Set-Content (Join-Path $dir '.unpacked') 'ok' }
  } }
}

# ---------------------------------------------------------------- Poly Haven HDRI (outdoor skies, 2k .hdr)
if (Want 'hdri') {
  Log '== Poly Haven HDRI'
  try { $all = Invoke-RestMethod -UserAgent $UA -Uri 'https://api.polyhaven.com/assets?t=hdris' -TimeoutSec 120 } catch { Log "  HDRI API FAIL: $_"; $all = $null }
  if ($all) {
    $want = 'urban','sunrise-sunset','skies','partially cloudy','clear','overcast'
    foreach ($id in ($all.PSObject.Properties.Name | Sort-Object)) {
      $cats = @($all.$id.categories)
      if (-not ($cats -contains 'outdoor')) { continue }
      if (-not ($cats | Where-Object { $want -contains $_ })) { continue }
      $sub = if ($cats -contains 'urban') { 'urban' } elseif ($cats -contains 'sunrise-sunset') { 'sunset' } else { 'sky' }
      $dst = Join-Path $Root "hdri\$sub\$id`_2k.hdr"
      if (Test-Path $dst) { $script:skip++; continue }
      try { $files = Invoke-RestMethod -UserAgent $UA -Uri "https://api.polyhaven.com/files/$id" -TimeoutSec 60 } catch { $script:fail++; continue }
      $u = $files.hdri.'2k'.hdr.url
      if ($u) { Log "  $id"; if (Get-File $u $dst) { Note 'Poly Haven HDRI' $id $dst "https://polyhaven.com/a/$id" } }
    }
  }
}

# ---------------------------------------------------------------- ambientCG PBR materials (1K-JPG, top 15 per category)
if (Want 'ambientcg') {
  Log '== ambientCG textures'
  $acg = 'Asphalt','Bricks','Concrete','PavingStones','Ground','Grass','Gravel','Rock','Planks','Wood','WoodFloor','Metal','Plaster','Roofing','Tiles','Facade','Fabric','Leather','Paint','Road','Snow','Moss'
  foreach ($c in $acg) {
    $api = "https://ambientcg.com/api/v2/full_json?type=Material&category=$c&include=downloadData&sort=Popular&limit=15"
    try { $r = Invoke-RestMethod -UserAgent $UA -Uri $api -TimeoutSec 120 } catch { Log "  ambientCG API FAIL $c"; $script:fail++; continue }
    Log ("  {0}: {1}" -f $c, @($r.foundAssets).Count)
    foreach ($a in $r.foundAssets) {
      $dir = Join-Path $Root "textures\$c\$($a.assetId)"
      if (Test-Path (Join-Path $dir '.unpacked')) { $script:skip++; continue }
      $d = $a.downloadFolders.default.downloadFiletypeCategories.zip.downloads | Where-Object { $_.attribute -eq '1K-JPG' } | Select-Object -First 1
      if (-not $d) { continue }
      $zip = Join-Path $Root "_downloads\ambientcg\$($a.assetId)_1K-JPG.zip"
      if (Get-File $d.downloadLink $zip) { Unpack $zip $dir; Note 'ambientCG' $a.assetId $dir "https://ambientcg.com/view?id=$($a.assetId)" }
    }
  }
}

# ---------------------------------------------------------------- Poly Haven models (.blend, 1k textures)
$phCat = @{
  'nature' = 'nature','plants','trees','rocks','ground cover','flowers','grass','potted plants','succulent'
  'interior' = 'furniture','seating','table','shelves','bed','office','appliances','electronics','dishes','food','books','vases','wall decoration','decorative','lighting'
  'city' = 'buildings','structures','industrial'
  'vehicles' = 'ships'
}
function PhFolder($cats) {
  foreach ($k in 'city','vehicles','nature','interior') { foreach ($c in $phCat[$k]) { if ($cats -contains $c) { return $k } } }
  return 'props'
}
if (Want 'polyhaven') {
  Log '== Poly Haven models'
  try { $all = Invoke-RestMethod -UserAgent $UA -Uri 'https://api.polyhaven.com/assets?t=models' -TimeoutSec 120 }
  catch { Log "  Poly Haven API FAIL: $_"; $all = $null }
  if ($all) {
    $ids = $all.PSObject.Properties.Name | Sort-Object
    Log ("  {0} models" -f $ids.Count)
    $i = 0
    foreach ($id in $ids) {
      $i++
      $cats = @($all.$id.categories)
      $dir = Join-Path $Root ("{0}\polyhaven\{1}" -f (PhFolder $cats), $id)
      if (Test-Path (Join-Path $dir '.done')) { $script:skip++; continue }
      try { $files = Invoke-RestMethod -UserAgent $UA -Uri "https://api.polyhaven.com/files/$id" -TimeoutSec 60 } catch { Log "  files FAIL $id"; $script:fail++; continue }
      $b = $files.blend.'1k'.blend
      if (-not $b) { Log "  no 1k blend for $id"; continue }
      Log ("  [{0}/{1}] {2}" -f $i, $ids.Count, $id)
      $good = Get-File $b.url (Join-Path $dir "$id`_1k.blend")
      if ($b.include) { foreach ($p in $b.include.PSObject.Properties) {
        $rel = $p.Name -replace '/', '\'
        if (-not (Get-File $p.Value.url (Join-Path $dir $rel))) { $good = $false }
      } }
      if ($good) { Set-Content (Join-Path $dir '.done') ($cats -join ';'); Note 'Poly Haven' $id $dir "https://polyhaven.com/a/$id" }
    }
  }
}

$size = (Get-ChildItem -Recurse -File $Root -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum / 1GB
Log ("DONE  downloaded={0} skipped={1} failed={2}  assets3d size={3:N1} GB  free={4} GB" -f $script:ok, $script:skip, $script:fail, $size, (FreeGB))
if ($script:fail -gt 0) { Log "failed list: $failLog" }
