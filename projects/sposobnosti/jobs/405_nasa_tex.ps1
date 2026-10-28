$ErrorActionPreference = 'Continue'
$root = 'C:\Users\Gigabyte\Documents\aipollon claude'
$P = "$root\sposobnosti"
$B = (Get-Content "$P\tools\blender_path.txt" -Raw).Trim()
& $B -b --factory-startup --python "$P\tools\get_nasa_tex.py" -- "$root\kosmos-dlya-vseh\blender\tex\nasa" 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^\s*$' }
Get-ChildItem "$root\kosmos-dlya-vseh\blender\tex\nasa" | ForEach-Object { "$($_.Name) $($_.Length)" }
