# KINEMA — установка для Windows
#   powershell -ExecutionPolicy Bypass -File install.ps1             ставит всё прямо в эту папку + мастер подключения
#   powershell -ExecutionPolicy Bypass -File install.ps1 -NoWizard   без вопросов (так ставит агент: Claude Code, Codex…)
#   powershell -ExecutionPolicy Bypass -File install.ps1 -Global     дополнительно ставит скиллы в %USERPROFILE%\.claude\skills
param([switch]$NoWizard, [switch]$Global)
$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$rs = Join-Path $here "skills\reel-studio"

Write-Host "`n=== KINEMA: установка ===`n"

# 0. по желанию — копия скиллов для Claude Code во всех папках (ключи, профиль и проекты при обновлении сохраняются)
if ($Global) {
    $skills = Join-Path $env:USERPROFILE ".claude\skills"
    New-Item -ItemType Directory -Force $skills | Out-Null
    $keep = @(".secrets.env", "engine\src\brand.json", "engine\public\brand")
    $tmp = Join-Path $env:TEMP ("kinema-keep-" + [guid]::NewGuid())
    $grs = Join-Path $skills "reel-studio"
    if (Test-Path $grs) {
        New-Item -ItemType Directory -Force $tmp | Out-Null
        foreach ($k in $keep) { $src = Join-Path $grs $k; if (Test-Path $src) { $dst = Join-Path $tmp $k; New-Item -ItemType Directory -Force (Split-Path -Parent $dst) | Out-Null; Copy-Item -Recurse -Force $src $dst } }
    }
    foreach ($s in "reel-studio", "reel-script", "reel-qa", "reel-analyze") {
        $dst = Join-Path $skills $s
        New-Item -ItemType Directory -Force $dst | Out-Null
        Copy-Item -Recurse -Force (Join-Path $here "skills\$s\*") $dst
    }
    if (Test-Path $tmp) {
        foreach ($k in $keep) { $src = Join-Path $tmp $k; if (Test-Path $src) { $dst = Join-Path $grs $k; if (Test-Path $dst) { Remove-Item -Recurse -Force $dst }; Copy-Item -Recurse -Force $src $dst } }
        Remove-Item -Recurse -Force $tmp
    }
    $rs = $grs
    Write-Host "Скиллы скопированы в $skills"
}

# 1. Python 3.10+ и окружение
$py = $null
foreach ($cand in @("py -3", "python", "python3")) {
    try {
        $v = Invoke-Expression "$cand -c `"import sys; print(sys.version_info >= (3, 10))`"" 2>$null
        if ($v -eq "True") { $py = $cand; break }
    } catch {}
}
if (-not $py) { throw "Нужен Python 3.10+ (https://www.python.org). Установите и запустите установку ещё раз." }
$venvPy = Join-Path $rs ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPy)) {
    Write-Host "Создаю окружение Python…"
    Invoke-Expression "$py -m venv `"$rs\.venv`""
}
Write-Host "Ставлю пакеты Python (распознавание речи, голос)…"
& $venvPy -m pip install --upgrade pip -q
& $venvPy -m pip install -q -r (Join-Path $rs "requirements.txt")

# 2. Node.js 18+ и движок
$node = Get-Command node -ErrorAction SilentlyContinue
if (-not $node) { throw "Нужен Node.js 18+ (https://nodejs.org, версия LTS). Установите и запустите установку ещё раз." }
$nv = [int]((& node --version).TrimStart("v").Split(".")[0])
if ($nv -lt 18) { throw "Node.js $nv слишком старый — нужен 18+." }
Write-Host "Ставлю движок рендера (npm, это пара минут)…"
Push-Location (Join-Path $rs "engine")
& npm.cmd ci --no-audit --no-fund
if ($LASTEXITCODE -ne 0) { & npm.cmd install --no-audit --no-fund }
& npx.cmd remotion browser ensure
Pop-Location

# 3. ffmpeg
if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
    Write-Host "`nffmpeg не найден."
    if ((Get-Command winget -ErrorAction SilentlyContinue) -and -not $NoWizard) {
        $ans = Read-Host "Установить ffmpeg через winget сейчас? (Y/n)"
        if ($ans -ne "n") { winget install --id Gyan.FFmpeg -e --accept-source-agreements; Write-Host "Перезапустите терминал после установки ffmpeg." }
    } else {
        Write-Host "Установите ffmpeg: winget install Gyan.FFmpeg (или https://www.gyan.dev/ffmpeg/builds/) и добавьте его в PATH."
    }
}

# 4. мастер подключения (ключи, канал, звуки)
if (-not $NoWizard) { & $venvPy (Join-Path $rs "scripts\setup.py") } else { & $venvPy (Join-Path $rs "scripts\setup.py") --check }
Write-Host "`nГотово. Откройте эту папку в Claude Code или Codex и напишите: «сделай ролик про …»`n"
