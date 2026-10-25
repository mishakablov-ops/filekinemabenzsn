# diagnostic: can Windows run Remotion's own ffprobe/compositor? (all Remotion renders failed at 09:22)
$rs = 'C:\Users\Gigabyte\Documents\aipollon claude\AIpollon-Reel-Studio\skills\reel-studio'
$c = "$rs\engine\node_modules\@remotion\compositor-win32-x64-msvc"
foreach ($exe in "$c\ffprobe.exe", "$c\ffmpeg.exe", "$c\remotion.exe", "$rs\.runtime\bin\ffprobe.exe") {
  if (-not (Test-Path $exe)) { "MISSING $exe"; continue }
  $p = Start-Process -FilePath $exe -ArgumentList '-version' -NoNewWindow -Wait -PassThru -RedirectStandardOutput "$env:TEMP\cc_out.txt" -RedirectStandardError "$env:TEMP\cc_err.txt" -ErrorAction SilentlyContinue
  if ($p) { "{0} exit=0x{1:X8}" -f (Split-Path $exe -Leaf), $p.ExitCode } else { "START FAILED $exe : $($Error[0])" }
}
Get-ChildItem $c | Select-Object Name, Length | Format-Table -AutoSize | Out-String
try { $s = Get-MpComputerStatus -ErrorAction Stop; "Defender RTP=" + $s.RealTimeProtectionEnabled } catch { "Defender status n/a" }
try { $sac = (Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\CI\Policy' -ErrorAction Stop).VerifiedAndReputablePolicyState; "SmartAppControl state=$sac (0 off, 1 on, 2 evaluation)" } catch { "SmartAppControl state n/a" }
try { Get-WinEvent -LogName 'Microsoft-Windows-CodeIntegrity/Operational' -MaxEvents 6 -ErrorAction Stop | ForEach-Object { "{0} {1} {2}" -f $_.TimeCreated, $_.Id, ($_.Message -split "`n")[0] } } catch { "CI log n/a" }
