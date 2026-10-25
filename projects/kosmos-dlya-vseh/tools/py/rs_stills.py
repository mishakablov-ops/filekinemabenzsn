import subprocess, sys, json, os
eng = r'C:\Users\Gigabyte\Documents\aipollon claude\AIpollon-Reel-Studio\skills\reel-studio\engine'
secs = sys.argv[1] if len(sys.argv) > 1 else '1,5,10'
tag = sys.argv[2] if len(sys.argv) > 2 else 'a'
args = ['node', 'tools/stills.mjs', '--comp', 'Reel', '--props', json.dumps({'project': 'kosmos-dlya-vseh', 'fps': 30}), '--qa',
        '--seconds', secs, '--scale', '0.4', '--out', f'out/mbg_st_{tag}', '--sheet', f'out/mbg_sheet_{tag}.png', '--cols', '8']
r = subprocess.run(args, cwd=eng, shell=True if os.name == 'nt' else False)
sys.exit(r.returncode)
