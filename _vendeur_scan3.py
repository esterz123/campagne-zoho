# -*- coding: utf-8 -*-
# VENDEUR: liste precise des sous-exploites (r2 envoyee, pas de reponse, 7+ jours, pas de relance3)
import json, io, sys, datetime, re, os
sys.stdout.reconfigure(encoding='utf-8')

BASE = r"C:\Users\ulamb\Bureau\prospection\github-campagne"
data = json.load(io.open(BASE + r"\campagne_data.json", encoding='utf-8'))
state = json.load(io.open(BASE + r"\campagne_state.json", encoding='utf-8'))
sent = state.get('sent', {})
today = datetime.date(2026, 8, 31)

def pd(s):
    m = re.match(r'(\d{4})-(\d{2})-(\d{2})', str(s or ''))
    return datetime.date(int(m[1]), int(m[2]), int(m[3])) if m else None

by_num = {str(x.get('num')): x for x in data}
out = []
for num, v in sent.items():
    if not isinstance(v, dict): continue
    if v.get('replied') or v.get('bounce'): continue
    r2 = pd(v.get('sent_relance2'))
    if not r2: continue
    if v.get('sent_relance3'): continue
    days = (today - r2).days
    if days < 7: continue
    x = by_num.get(num, {})
    out.append((days, num, x.get('prospect'), x.get('to'), x.get('dirigeant'), str(x.get('note',''))[:60]))

out.sort(reverse=True)
for o in out:
    print("J+%d | #%s | %s | %s | dir=%s | %s" % o)
print("TOTAL sous-exploites (r2>7j, pas r3):", len(out))
