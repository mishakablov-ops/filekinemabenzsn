@echo off
title Claude worker - mir-bez-granic
cd /d "%~dp0"
echo.
echo  This window runs the tasks Claude puts into the jobs\queue folder
echo  (Blender renders, Replicate voice-over, ffmpeg). Close it to stop.
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0worker\worker.ps1"
pause
