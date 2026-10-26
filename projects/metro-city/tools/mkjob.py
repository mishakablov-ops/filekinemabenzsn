"""Write a worker job (.ps1, ASCII) that renders spots of the city «Метрополис» (metro-city) with build_pc.py.
    python3 mkjob.py NAME still|clip|clip60 SCALE shot[:t] ...
    python3 mkjob.py NAME still 1.0 --shots shots_places_demo.json p01_street p02_avenue   (shots file in blender/)
"""
import sys
name, mode, scale, *shots = sys.argv[1:]
sfile = ''
if shots and shots[0] == '--shots':
    sfile, shots = shots[1], shots[2:]
P = r'C:\Users\Gigabyte\Documents\aipollon claude\metro-city'
out = {'proof': P + r'\renders\proof', 'still': P + r'\stills', 'clip': P + r'\clips', 'clip60': P + r'\clips_v2'}[mode]
L = ["$ErrorActionPreference = 'Continue'",
     f"$B = (Get-Content '{P}\\tools\\blender_path.txt' -Raw).Trim()",
     f"New-Item -ItemType Directory -Force -Path '{out}' | Out-Null"]
flt = "| ForEach-Object { \"$_\" } | Where-Object { $_ -notmatch '^Fra:|^\\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }"
for s in shots:
    sid, _, rest = s.partition(':')
    t, _, tag = rest.partition(':')
    sarg = f" --shots '{P}\\blender\\{sfile}'" if sfile else ''
    if mode in ('clip', 'clip60'):
        fps = 60 if mode == 'clip60' else 30
        args = f"--shot {sid} --mp4 '{out}\\{sid}.mp4' --scale {scale} --fps {fps} --samples 24"
    else:
        args = f"--shot {sid} --still '{out}' --scale {scale}" + (f" --t {t}" if t else '') + (f" --tag {tag}" if tag else '')
    L += ["$t0 = Get-Date",
          f"& $B -b --factory-startup --python '{P}\\blender\\build_pc.py' -- {args}{sarg} 2>&1 {flt}",
          f"\"SHOT {sid} done in \" + [int]((Get-Date) - $t0).TotalSeconds + \" s\""]
open(name, 'w', encoding='ascii', newline='\r\n').write('\n'.join(L) + '\n')
print('wrote', name)
