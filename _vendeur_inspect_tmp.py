import json, os, datetime
os.chdir(r"C:\Users\ulamb\Bureau\prospection\github-campagne")
st = json.load(open('campagne_state.json', encoding='utf-8'))
sent = st['sent']
today = datetime.date(2026, 8, 31)

def d(s):
    try:
        return datetime.date.fromisoformat(s[:10])
    except Exception:
        return None

# prospects relance2 faite sans reponse depuis 7+ jours
cands = []
for num, v in sent.items():
    r2 = d(v.get('sent_relance2', ''))
    if r2 and (today - r2).days >= 7:
        cands.append((num, v.get('sent_relance2'), (today - r2).days, sorted(v.keys())))
print("RELANCE2 >=7j SANS SUITE:", len(cands))
for c in cands:
    print(c)

# check champs extra (reply, closed...)
allkeys = set()
for v in sent.values():
    allkeys.update(v.keys())
print("ALL STATE KEYS:", sorted(allkeys))
