$ErrorActionPreference = 'Continue'
$proj = 'C:\Users\Gigabyte\Documents\aipollon claude\kosmos-dlya-vseh'
$rs   = 'C:\Users\Gigabyte\Documents\aipollon claude\AIpollon-Reel-Studio\skills\reel-studio'
"== GPU =="
& nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv 2>&1
"== CPU/RAM =="
Get-CimInstance Win32_Processor | ForEach-Object { "$($_.Name) cores=$($_.NumberOfCores) threads=$($_.NumberOfLogicalProcessors)" }
"RAM GB: " + [math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory/1GB,1)
"== Disk C free GB =="
[math]::Round((Get-PSDrive C).Free/1GB,1)
"== tools =="
& node --version 2>&1
& "$rs\.venv\Scripts\python.exe" --version 2>&1
& "$rs\.runtime\bin\ffmpeg.exe" -hide_banner -version 2>&1 | Select-Object -First 1
& "$rs\.runtime\bin\ffmpeg.exe" -hide_banner -filters 2>&1 | Select-String -Pattern ' (ass|subtitles|loudnorm) '
"== existing blender =="
where.exe blender 2>&1
"== download blender 4.5 LTS =="
$idx = & curl.exe -s -L 'https://download.blender.org/release/Blender4.5/'
$vers = [regex]::Matches(($idx -join "`n"), 'blender-4\.5\.(\d+)-windows-x64\.zip') | ForEach-Object { [int]$_.Groups[1].Value } | Sort-Object -Descending -Unique
$v = $vers | Select-Object -First 1
$zip = "blender-4.5.$v-windows-x64.zip"
"latest: $zip"
$dst = Join-Path $proj "tools\$zip"
if (-not (Test-Path $dst)) { & curl.exe -L --retry 3 -o $dst "https://download.blender.org/release/Blender4.5/$zip" 2>&1 | Select-Object -Last 2 }
"zip size MB: " + [math]::Round((Get-Item $dst).Length/1MB,1)
& tar.exe -xf $dst -C (Join-Path $proj 'tools') 2>&1
$bdir = Get-ChildItem (Join-Path $proj 'tools') -Directory | Where-Object { $_.Name -like 'blender-4.5*' } | Select-Object -First 1
$bexe = Join-Path $bdir.FullName 'blender.exe'
Set-Content -Path (Join-Path $proj 'tools\blender_path.txt') -Value $bexe
"blender exe: $bexe"
& $bexe -b --factory-startup --python-expr "import bpy;print('BLENDER',bpy.app.version_string);p=bpy.context.preferences.addons['cycles'].preferences;p.get_devices();print('DEVICES',[(d.name,d.type) for d in p.devices])" 2>&1 | Select-String -Pattern 'BLENDER|DEVICES|Error'
"== done =="
