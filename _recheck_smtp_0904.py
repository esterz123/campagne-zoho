# recheck SMTP v2 : MX rapide en parallele, timeout serre
import json, socket, subprocess, sys
from concurrent.futures import ThreadPoolExecutor, as_completed
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

d = json.load(open('campagne_data.json', encoding='utf-8'))
s = json.load(open('campagne_state.json', encoding='utf-8'))
sent = s.get('sent', {})
rest = [e for e in d if str(e.get('num')) not in sent]

def mx_host(domain):
    try:
        r = subprocess.run(['nslookup', '-type=MX', domain], capture_output=True, timeout=6)
        out = (r.stdout or b'').decode('cp850', 'replace')
        for line in out.splitlines():
            if 'mail exchanger' in line.lower():
                return line.split()[-1].strip('.').lower()
    except Exception:
        pass
    return None

def check(email):
    dom = email.split('@')[-1].lower()
    mx = mx_host(dom)
    if not mx:
        return (email, 'NOMX', dom)
    try:
        socket.setdefaulttimeout(5)
        socket.create_connection((mx, 25))
        return (email, 'OK', mx)
    except Exception:
        return (email, 'PORT25KO', mx)

results = {}
with ThreadPoolExecutor(max_workers=12) as ex:
    futs = {ex.submit(check, e['to']): e['num'] for e in rest}
    for f in as_completed(futs, timeout=120):
        try:
            email, verdict, info = f.result()
        except Exception:
            continue
        results[futs[f]] = (email, verdict, info)

from collections import Counter
c = Counter(v for _, v, _ in results.values())
print('verdict SMTP restants:', dict(c), '/', len(rest))
ko = [(n, e, i) for n, (e, v, i) in results.items() if v != 'OK']
print('morts:', ko[:40])
json.dump({str(n): {'email': e, 'verdict': v, 'mx': i} for n, (e, v, i) in results.items()},
          open('_smtp_recheck_0904.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
