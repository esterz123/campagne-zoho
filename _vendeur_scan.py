# -*- coding: utf-8 -*-
import json, datetime, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

base = r"C:\Users\ulamb\Bureau\prospection\github-campagne"
d = json.load(open(base + r"\campagne_state.json", encoding="utf-8"))
sent = d["sent"]
today = datetime.date(2026, 8, 31)

def pd(s):
    try:
        return datetime.date.fromisoformat(s[:10])
    except Exception:
        return None

cands = []
for num, v in sent.items():
    r2 = v.get("sent_relance2")
    r3 = v.get("sent_relance3")
    if r2 and not r3:
        dt = pd(r2)
        if dt:
            cands.append(((today - dt).days, num, r2))
cands.sort(reverse=True)
print("total sent:", len(sent))
print("candidats relance2 ancienne sans relance3 (jours, num, date):")
for c in cands[:12]:
    print(c)

rkeys = set()
for num, v in sent.items():
    for k in v:
        if "rep" in k.lower() or "repl" in k.lower():
            rkeys.add((num, k))
print("reply-ish keys:", rkeys)

print("--- detail 6 premiers candidats ---")
for _, num, _ in cands[:6]:
    print(num, json.dumps(sent[num], ensure_ascii=False))
