#!/bin/bash
# Create a new Blender+Reel Studio project from the kit (run in the Cowork VM):
#   bash new_blender_project.sh <id>
# -> "aipollon claude/<id>/" (worker, blender scripts, tools, data, sfx) + engine/public/projects/<id>/
set -e
ID="$1"; [ -z "$ID" ] && { echo "usage: new_blender_project.sh <id>"; exit 1; }
KIT="$(cd "$(dirname "$0")" && pwd)"
RS="$(cd "$KIT/.." && pwd)"
ROOT="$(cd "$RS/../../.." && pwd)"          # "aipollon claude"
DST="$ROOT/$ID"
[ -e "$DST" ] && { echo "$DST exists"; exit 1; }
mkdir -p "$DST"
cp -r "$KIT"/START_WORKER.bat "$KIT"/worker "$KIT"/blender "$KIT"/tools "$KIT"/data "$KIT"/audio "$KIT"/voice "$KIT"/jobs "$DST/"
mkdir -p "$DST"/{renders,out,_sync,blender/files}
grep -rl "__PROJECT__" "$DST/tools" "$DST/START_WORKER.bat" | while read f; do sed -i "s/__PROJECT__/$ID/g" "$f"; done
# reuse the Blender that is already on this PC, if any
for b in "$ROOT"/*/tools/blender_path.txt; do [ -f "$b" ] && cp "$b" "$DST/tools/blender_path.txt" && break; done
# Replicate token: reuse Reel Studio's secrets (never print it)
[ -f "$RS/.secrets.env" ] && cp "$RS/.secrets.env" "$DST/.secrets.env"
mkdir -p "$RS/engine/public/projects/$ID/clips"
chmod +x "$DST"/tools/*.sh
echo "created $DST"
echo "next: ask the user to double-click $ID\\START_WORKER.bat; if tools/blender_path.txt is missing queue tools/setup_blender.ps1"
