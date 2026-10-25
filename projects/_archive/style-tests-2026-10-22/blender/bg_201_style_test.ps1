$ErrorActionPreference = 'Continue'
$P = 'C:\Users\Gigabyte\Documents\aipollon claude\style-test'
$L = 'C:\Users\Gigabyte\Documents\aipollon claude\jobs\logs\bg_201_style_test.log'
$B = (Get-Content "$P\tools\blender_path.txt" -Raw).Trim()
"start $(Get-Date -Format o)" | Out-File $L -Encoding utf8
foreach ($s in 'toy_street','toy_close','toy_aerial','lp_street','lp_close','lp_aerial') {
  & $B -b --factory-startup --python "$P\blender\build.py" -- --shot $s --times 1.5,4.5 --scale 0.5 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^Fra:|^\s*$|Synchroniz|Compiling|Loading|Updating|Waiting' } | Out-File $L -Append -Encoding utf8
}
"done $(Get-Date -Format o)" | Out-File $L -Append -Encoding utf8
Set-Content 'C:\Users\Gigabyte\Documents\aipollon claude\jobs\logs\bg_201_style_test.exit' 'done'
