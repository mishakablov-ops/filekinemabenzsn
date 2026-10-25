# Mike asked to turn the PC off when the night's work is done (22.10.2026)
'shutdown requested ' + (Get-Date)
shutdown.exe /s /t 120 /c "Claude: work is done, the PC turns off in 2 minutes"
