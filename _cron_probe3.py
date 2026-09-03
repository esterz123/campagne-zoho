# Probe 3 : A/B results, relances dues, couverture preuve, boucle auto code
import json, re, os
from datetime import date, datetime

today = date(2026, 9, 2)

print("=== A/B RESULTATS ===")
try:
    ab = json.load(open('ab_resultats.json'))
    print(json.dumps(ab, ensure_ascii=False, indent=1)[:1500])
except Exception as e:
    print("ERR", e)

print("\n=== RELANCES DUES ===")
st = json.load(open('campagne_state.json'))
sent = st.get('sent', {})
data = json.load(open('campagne_data.json'))
by_num = {str(d.get('num')): d for d in data}

# compte envoyes par date
from collections import Counter
dates = Counter()
for k, v in sent.items():
    d = v.get('on') or v.get('date') if isinstance(v, dict) else None
    if d:
        dates[str(d)[:10]] += 1
print("envois par date:", dict(sorted(dates.items())))

# J+3/J+7 calcul: envoyes avant le 30/08 sans relance
import datetime as dt
def parse_d(s):
    try:
        return dt.date.fromisoformat(str(s)[:10])
    except Exception:
        return None

j3_due, j7_due, rel = [], [], 0
for k, v in sent.items():
    if not isinstance(v, dict):
        continue
    d = parse_d(v.get('on') or v.get('date') or '')
    if not d:
        continue
    delta = (today - d).days
    has_r = 'relance' in json.dumps(v)  # approximatif
    if delta >= 7:
        j7_due.append((k, d))
    elif delta >= 3:
        j3_due.append((k, d))
    if any(str(x).startswith('sent_relance') for x in v):
        rel += 1
print("J+7+ possibles:", len(j7_due), "| J+3 possibles:", len(j3_due), "| avec sent_relance*:", rel)
# echantillon valeur d'une entree relancee
for k, v in sent.items():
    if isinstance(v, dict) and any(str(x).startswith('sent_relance') for x in v):
        print("exemple relance:", k, json.dumps(v, ensure_ascii=False)[:200])
        break

print("\n=== COUVERTURE PREUVE (153 restants) ===")
try:
    cons = json.load(open('constats_sites.json'))
    if isinstance(cons, list):
        cons = {str(c.get('num')): c for c in cons}
    print("constats:", len(cons))
    pros = [d for d in data if d.get('type', 'prospect') == 'prospect']
    rest = [d for d in pros if str(d.get('num')) not in sent]
    covered = [d for d in rest if str(d.get('num')) in cons]
    print("restants:", len(rest), "| avec constat:", len(covered))
except Exception as e:
    print("ERR", e)

print("\n=== RELANCES_CONSTATS DIR ===")
try:
    fl = os.listdir('relances_constats')
    print(len(fl), "fichiers:", fl[:5])
except Exception as e:
    print("ERR", e)
