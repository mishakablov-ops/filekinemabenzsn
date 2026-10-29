# Installs the official Blender Lab MCP server next to the reel pipeline without touching it (29.10.2026):
# a portable Blender 5.2.3 (the MCP add-on needs 5.1+; the reels stay on Blender 4.5 LTS), the add-on, the server in
# its own venv, and the project's .mcp.json entry. Run from "aipollon claude":  powershell -ExecutionPolicy Bypass -File blender-mcp\install_blender_mcp.ps1
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$d = Join-Path $root 'blender-mcp'
$ver = '5.2.3'; $rel = 'v1.0.3'
$zip = "$d\blender-$ver-windows-x64.zip"
if (-not (Test-Path "$d\blender-$ver-windows-x64\blender.exe")) {
  curl.exe -sL -o $zip "https://download.blender.org/release/Blender5.2/blender-$ver-windows-x64.zip"
  curl.exe -sL -o "$d\sha256.txt" "https://download.blender.org/release/Blender5.2/blender-$ver.sha256"
  $h = (Get-FileHash $zip -Algorithm SHA256).Hash.ToLower()
  if (-not (Select-String -Path "$d\sha256.txt" -Pattern $h -Quiet)) { throw 'Blender zip checksum mismatch' }
  Expand-Archive $zip -DestinationPath $d -Force
}
$bd = "$d\blender-$ver-windows-x64"
New-Item -ItemType Directory -Force "$bd\portable" | Out-Null            # own settings, independent of other Blenders
curl.exe -sL -o "$d\mcp-addon.zip" "https://projects.blender.org/lab/blender_mcp/releases/download/$rel/mcp-1.0.3.zip"
curl.exe -sL -o "$d\blender.mcpb" "https://projects.blender.org/lab/blender_mcp/releases/download/$rel/blender-1.0.3.mcpb"
& "$bd\blender.exe" --command extension install-file -r user_default -e "$d\mcp-addon.zip"
$py = @'
import bpy, addon_utils
addon_utils.enable("bl_ext.user_default.mcp", default_set=True, persistent=True)
bpy.context.preferences.system.use_online_access = True
bpy.ops.wm.save_userpref()
'@
Set-Content "$env:TEMP\enable_mcp.py" $py -Encoding utf8
& "$bd\blender.exe" -b --python "$env:TEMP\enable_mcp.py"
Copy-Item "$d\blender.mcpb" "$d\bundle.zip" -Force
Expand-Archive "$d\bundle.zip" -DestinationPath "$d\server" -Force
$base = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $base) { $base = 'C:\Users\Gigabyte\AppData\Local\Programs\Python\Python314\python.exe' }
& $base -m venv "$d\venv"
& "$d\venv\Scripts\python.exe" -m pip install --quiet "$d\server"
$exe = "$d\venv\Scripts\blender-mcp.exe"
@{ mcpServers = @{ blender = @{ command = $exe; args = @() } } } | ConvertTo-Json -Depth 5 |
  Set-Content (Join-Path $root '.mcp.json') -Encoding utf8
"OK: open $bd\blender.exe (MCP panel: Server is running, port 9876), then start Claude Code in $root"
