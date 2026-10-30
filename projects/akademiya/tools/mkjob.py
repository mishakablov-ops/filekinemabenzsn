"""Write a worker job (.ps1, ASCII, CRLF) that renders shots of akademiya with build_pc.py.
    python3 mkjob.py NAME still|clip SCALE shot[:t[:tag]] ...      (t may be a list: c03:0.2,0.6,0.95)
still -> akademiya\\stills\\<shot><tag>.jpg (Eevee, 64 samples), clip -> akademiya\\clips\\<shot>.mp4 (30 fps, 24 samples).
"""
import sys
name, mode, scale, *shots = sys.argv[1:]
P = r'C:\Users\Gigabyte\Documents\aipollon claude\akademiya'
out = {'still': P + r'\stills', 'clip': P + r'\clips'}[mode]
L = ["$ErrorActionPreference = 'Continue'",
     f"$B = (Get-Content '{P}\\tools\\blender_path.txt' -Raw).Trim()",
     f"New-Item -ItemType Directory -Force -Path '{out}' | Out-Null"]
flt = "| ForEach-Object { \"$_\" } | Where-Object { $_ -notmatch '^Fra:|^\\s*$|Synchroniz|Compiling|Loading|Updating|Waiting|Saved:|Time:|Append frame' }"
for s in shots:
    sid, _, rest = s.partition(':')
    t, _, tag = rest.partition(':')
    if mode == 'clip':
        args = f"--shot {sid} --mp4 '{out}\\{sid}.mp4' --scale {scale} --fps 30 --samples 24"
    else:
        tt = (f" --ts {t}" if ',' in t else f" --t {t}") if t else ''
        args = f"--shot {sid} --still '{out}' --scale {scale}" + tt + (f" --tag {tag}" if tag else '')
    L += ["$t0 = Get-Date",
          f"& $B -b --factory-startup --python '{P}\\blender\\build_pc.py' -- {args} 2>&1 {flt}",
          f"\"SHOT {sid} done in \" + [int]((Get-Date) - $t0).TotalSeconds + \" s\""]
open(name, 'w', encoding='ascii', newline='\r\n').write('\n'.join(L) + '\n')
print('wrote', name)
