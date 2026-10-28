$ErrorActionPreference = 'Continue'
# 415: both remotion renders crashed in the compositor after 20-41 s, the message was cut by Select -Last; full log here
$root = 'C:\Users\Gigabyte\Documents\aipollon claude'
$rs = "$root\KINEMA\skills\reel-studio"
$py = "$rs\.venv\Scripts\python.exe"
$ffp = "$rs\.runtime\bin\ffprobe.exe"
$env:PYTHONIOENCODING = 'utf-8'
$env:PATH = "$rs\.runtime\bin;" + $env:PATH
foreach ($n in 1, 2) {
  Get-ChildItem "$rs\engine\public\projects\sposobnosti-$n\clips\*.mp4" | ForEach-Object {
    $o = & $ffp -v error -select_streams v:0 -show_entries stream=nb_frames,r_frame_rate,duration,codec_name,has_b_frames -of csv=p=0 $_.FullName
    "PROBE $($_.Name) $o"
  }
}
Push-Location $rs
& $py -I "$rs\scripts\render.py" sposobnosti-2 --concurrency 6 2>&1 | ForEach-Object { "$_" } | Where-Object { $_ -notmatch '^\s*$|^Rendered \d|^Encoded \d' }
"EXIT $LASTEXITCODE"
Pop-Location
