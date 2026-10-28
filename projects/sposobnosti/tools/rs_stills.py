"""Run KINEMA tools/stills.mjs for a project with the JSON props passed safely (PowerShell 5.1 eats the quotes):
    python -I rs_stills.py <project> <out dir> [--seconds 2.9 | --every 1] [--scale 1] [--qa] [--sheet FILE]
KINEMA_RS = path to KINEMA/skills/reel-studio (set by the worker job).
"""
import json
import os
import shutil
import subprocess
import sys

rs = os.environ.get('KINEMA_RS', r'C:\Users\Gigabyte\Documents\aipollon claude\KINEMA\skills\reel-studio')
project, out, *rest = sys.argv[1:]
node = shutil.which('node') or 'node'
args = [node, 'tools/stills.mjs', '--comp', 'Reel', '--props', json.dumps({'project': project, 'fps': 30}), '--out', out] + rest
r = subprocess.run(args, cwd=os.path.join(rs, 'engine'))
sys.exit(r.returncode)
