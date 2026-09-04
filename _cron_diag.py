# -*- coding: utf-8 -*-
# Diag run campagne echoue 17:36 + verif kill-switch
import subprocess, os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
r = subprocess.run(['gh', 'run', 'view', '33785571549', '--log-failed'], capture_output=True)
out = (r.stdout or b'').decode('utf-8', 'replace')
lines = [l for l in out.splitlines() if l.strip()]
print('\n'.join(lines[-30:]))
print('---KILLSWITCH---')
print('PAUSE_ENVOIS existe:', os.path.exists('PAUSE_ENVOIS'))
