import json, io, os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
d = json.load(io.open('campagne_data.json', encoding='utf-8'))
s = json.load(io.open('campagne_state.json', encoding='utf-8'))
sent = s.get('sent', {})
try:
    constats = json.load(io.open('constats_sites.json', encoding='utf-8'))
except Exception:
    constats = {}
# map num -> site domain depuis les fiches
fiches = d if isinstance(d, list) else []
rest = [f for f in fiches if str(f.get('num')) not in sent]
def domain_of(f):
    url = f.get('site') or f.get('url') or ''
    if not url:
        return ''
    u = str(url).lower()
    u = u.replace('https://', '').replace('http://', '').split('/')[0]
    return u
sans_constat = [f for f in rest if domain_of(f) and domain_of(f) not in constats]
sans_site = [f for f in rest if not domain_of(f)]
print('restants:', len(rest))
print('avec constat:', len(rest) - len(sans_constat) - len(sans_site))
print('sans site:', len(sans_site))
print('sans constat mais site ok:', len(sans_constat))
if sans_constat:
    for f in sans_constat[:12]:
        print('  a-scan num', f.get('num'), domain_of(f))
# relances J+7 dues aujourd'hui (5 jours deja relance1)
today = '2026-09-05'
from datetime import datetime, timedelta
t = datetime(2026, 9, 5)
d3 = (t - timedelta(days=3)).strftime('%Y-%m-%d')
d7 = (t - timedelta(days=7)).strftime('%Y-%m-%d')
r1_due = [k for k, v in sent.items() if str(v.get('on', '')) == d3 and not v.get('sent_relance1') and not v.get('replied') and not v.get('bounce')]
r2_due = [k for k, v in sent.items() if str(v.get('on', '')) == d7 and v.get('sent_relance1') and not v.get('sent_relance2') and not v.get('replied') and not v.get('bounce')]
print('relance1 dues aujourd hui:', len(r1_due), r1_due[:6])
print('relance2 dues aujourd hui:', len(r2_due), r2_due[:6])
# bounces recents
bounces = [k for k, v in sent.items() if v.get('bounce')]
print('bounces cumules:', len(bounces))
