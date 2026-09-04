# -*- coding: utf-8 -*-
# Audit 2 : GO2 simi/itplast/fpsa, bounces, activite repondeur/closer aujourd'hui, AB test
import json, os, datetime as dt

BASE = r"C:\Users\ulamb\Bureau\prospection\github-campagne"
os.chdir(BASE)

st = json.load(open("campagne_state.json", encoding="utf-8"))
sent = st.get("sent", {})
for num in ("1", "11", "44", "63"):
    e = sent.get(num, {})
    go2keys = {k: v for k, v in e.items() if k.startswith("go2")}
    print("#%s go2=%s replied=%s on=%s" % (num, json.dumps(go2keys), e.get("replied"), e.get("on")))

# bounces
nb = sum(1 for n, e in sent.items() if isinstance(e, dict) and e.get("bounce"))
print("bounces marques:", nb)

# repondeur/closer states
for f in ("repondeur_state.json", "closer_state.json"):
    try:
        s = json.load(open(f, encoding="utf-8"))
        tr = s.get("traites", [])
        auj = dt.date.today().isoformat()
        print(f, "| traites:", len(tr), "| cles:", [k for k in s.keys()][:8])
        # derniers traites (format inconnu: list ou dict)
        if isinstance(tr, dict):
            items = sorted(tr.items(), key=lambda kv: str(kv[1]), reverse=True)[:5]
            print("  derniers:", items)
    except Exception as ex:
        print(f, "ERR", ex)

# AB test : verdict + config
for f in ("verdict_ab_0902.md", "ab_test.json", "ab_resultats.json", "verdict_ab.txt"):
    p = os.path.join(BASE, f)
    if os.path.exists(p):
        print("---", f, os.path.getsize(p), "octets")
        if f.endswith(".json"):
            print(json.dumps(json.load(open(p, encoding="utf-8")), ensure_ascii=False)[:600])
    else:
        print("---", f, "ABSENT")

# sujets actuels des non-envoyes (echantillon 10)
data = json.load(open("campagne_data.json", encoding="utf-8"))
rest = [e for e in data if isinstance(e, dict) and str(e.get("num")) not in sent]
print("non-envoyes:", len(rest))
for e in rest[:10]:
    print("  #%s sujet=%s" % (e.get("num"), str(e.get("subject", ""))[:80]))

# suite d'envoi du jour par boite (surveiller contact 8/j)
from collections import Counter
c = Counter()
for n, e in sent.items():
    if isinstance(e, dict) and str(e.get("on", "")).startswith(dt.date.today().isoformat()):
        c[e.get("via", "?")] += 1
print("envois du jour par boite:", dict(c))
