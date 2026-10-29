# Blender MCP (официальный, Blender Lab) — установлен 29.10.2026

**Где лежит:** на ПК — `C:\Users\Gigabyte\Documents\aipollon claude\blender-mcp\` (скрипт ставит всё рядом с собой и пишет `.mcp.json` в папку уровнем выше), здесь в репозитории (`tools/mcp-blender/`, имя `tools/blender-*` занято правилом `.gitignore` для установок Blender) — только скрипт установки, README и пример `.mcp.json`. Blender 5.2.3, аддон, `server/` и `venv/` в git не храним. Установка на новый ПК: скопировать эту папку в `aipollon claude\blender-mcp\` и запустить `powershell -ExecutionPolicy Bypass -File blender-mcp\install_blender_mcp.ps1`.

mike: «установи mcp сервер блендеру официальный», «чтобы ничего не сломалось и было только лучше».

- Источник: https://www.blender.org/lab/mcp-server/ (код: https://projects.blender.org/lab/blender_mcp, релиз v1.0.3).
- Требует Blender 5.1+, поэтому стоит **отдельная портативная копия Blender 5.2.3** в `blender-mcp/blender-5.2.3-windows-x64/`
  (папка `portable/` рядом с blender.exe: свои настройки, не мешает установленным версиям). Контрольная сумма zip
  сверена с blender.org. Конвейер роликов по-прежнему на Blender 4.5 LTS (`*/tools/blender_path.txt`) — его не трогали.
- Аддон `mcp-1.0.3.zip` установлен и включён в этой копии, «Allow Online Access» включён (без него сервер не
  стартует сам). Мост слушает `localhost:9876`.
- MCP-сервер (`blender-1.0.3.mcpb` → `server/`) установлен в отдельное окружение `blender-mcp/venv/`
  (Python 3.14, пакеты docutils, mcp[cli], pyyaml). Запуск: `venv/Scripts/blender-mcp.exe`.
- Подключение к Claude Code: `aipollon claude/.mcp.json` (сервер `blender`). Claude Code спросит разрешение на этот
  сервер при следующем запуске сессии в папке проекта.

Как пользоваться: открыть `blender-mcp/blender-5.2.3-windows-x64/blender.exe`, в панели аддона MCP должно быть
«Server is running» (иначе Edit → Preferences → Add-ons → MCP → Start). Потом в Claude Code доступны инструменты
`blender` (выполнить Python в Blender, осмотреть сцену, отрендерить, справка по API и мануал).

Важно (предупреждение разработчиков): сервер выполняет код, написанный нейросетью, прямо в Blender без защиты.
Держать открытым только когда нужен; не открывать в нём важные файлы без копии.
