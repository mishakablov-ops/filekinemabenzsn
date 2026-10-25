# re-render after Smart App Control is turned off: fr-gibrid (new hybrid style) and fr-test-1 (Blender v3 clips)
$ErrorActionPreference = 'Continue'
$root = 'C:\Users\Gigabyte\Documents\aipollon claude'
$rs = "$root\AIpollon-Reel-Studio\skills\reel-studio"
$py = "$rs\.venv\Scripts\python.exe"
$env:PYTHONIOENCODING = 'utf-8'
$env:PATH = "$rs\.runtime\bin;" + $env:PATH
Set-Location $rs
# wait until Windows lets Remotion's compositor run (Smart App Control off), up to 30 min
$probe = "$rs\engine\node_modules\@remotion\compositor-win32-x64-msvc\ffprobe.exe"
$w = 0
while ($true) {
  $p = Start-Process -FilePath $probe -ArgumentList '-version' -NoNewWindow -Wait -PassThru -RedirectStandardOutput "$env:TEMP\rr_out.txt" -RedirectStandardError "$env:TEMP\rr_err.txt" -ErrorAction SilentlyContinue
  if ($p -and $p.ExitCode -eq 0) { "compositor OK after $w s"; break }
  if ($w -ge 1800) { "compositor still blocked after 30 min, giving up"; exit }
  Start-Sleep -Seconds 20; $w += 20
}
New-Item -ItemType Directory -Force "$root\output" | Out-Null
foreach ($id in 'fr-gibrid', 'fr-test-1') {
  $t0 = Get-Date
  & $py -I "$rs\scripts\render.py" $id --concurrency 6 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^\s*$|^Rendered|^Encoded|Copying public' } | Select-Object -Last 14
  "RENDER $id done in " + [int]((Get-Date) - $t0).TotalSeconds + " s"
  $o = "$rs\engine\out\$id.mp4"
  if ((Test-Path $o) -and (Get-Item $o).LastWriteTime -gt $t0) {
    Copy-Item $o "$root\_sync\$id.mp4" -Force
    Get-Content "$rs\engine\out\${id}_qa.md" -ErrorAction SilentlyContinue
    "OUT OK $id"
  } else { "OUT MISSING $id" }
}
Copy-Item "$root\_sync\fr-gibrid.mp4" "$root\output\fr-gibrid.mp4" -Force -ErrorAction SilentlyContinue
Copy-Item "$root\_sync\fr-test-1.mp4" "$root\output\fr-klassika-blender-v3.mp4" -Force -ErrorAction SilentlyContinue
