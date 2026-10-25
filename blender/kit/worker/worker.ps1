$ErrorActionPreference = 'Continue'
$proj = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$q    = Join-Path $proj 'jobs\queue'
$done = Join-Path $proj 'jobs\done'
$logs = Join-Path $proj 'jobs\logs'
New-Item -ItemType Directory -Force -Path $q, $done, $logs | Out-Null
$alive = Join-Path $proj 'jobs\worker.alive'
Write-Host "Worker started. Queue: $q"
while ($true) {
  Set-Content -Path $alive -Value (Get-Date -Format o)
  $job = Get-ChildItem -Path $q -Filter *.ps1 -File | Sort-Object Name | Select-Object -First 1
  if ($null -eq $job) { Start-Sleep -Seconds 2; continue }
  $name = $job.BaseName
  $file = Join-Path $done $job.Name
  Move-Item -LiteralPath $job.FullName -Destination $file -Force
  $log = Join-Path $logs "$name.log"
  Write-Host ("[{0}] start  {1}" -f (Get-Date -Format T), $name)
  if ($name -like 'bg_*') {
    Start-Process -FilePath powershell -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',"`"$file`"") -WindowStyle Minimized
  } else {
    & powershell -NoProfile -ExecutionPolicy Bypass -File $file *>&1 | Out-File -FilePath $log -Encoding utf8
    Set-Content -Path (Join-Path $logs "$name.exit") -Value $LASTEXITCODE
  }
  Write-Host ("[{0}] finish {1}" -f (Get-Date -Format T), $name)
}
