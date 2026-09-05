# -*- coding: utf-8 -*-
# Audit verite terrain : file, reponses, cash. Lecture seule.
import json, os
R = r"C:\Users\ulamb\Bureau\prospection\github-campagne"
os.chdir(R)

data = json.load(open("campagne_data.json", encoding="utf-8"))
state = json.load(open("campagne_state.json", encoding="utf-8"))
sent = state.get("sent", {})

fiches = {}
if isinstance(data, dict):
    for k, v in data.items():
        if isinstance(v, dict):
            fiches[str(v.get("num", k))] = v
else:
    for v in data:
        fiches[str(v.get("num"))] = v

tot = len(fiches)
envoyes = [n for n in fiches if n in sent]
restants = [n for n in fiches if n not in sent]
replied = [n for n, s in sent.items() if s.get("replied")]
rel1 = [n for n, s in sent.items() if s.get("sent_relance1")]
rel2 = [n for n, s in sent.items() if s.get("sent_relance2")]

print("File totale: %d fiches" % tot)
print("Envoyes: %d | Restants: %d" % (len(envoyes), len(restants)))
print("Replied: %d -> %s" % (len(replied), replied[:10]))
print("Relance1: %d | Relance2: %d" % (len(rel1), len(rel2)))

try:
    c = json.load(open("constats_sites.json", encoding="utf-8"))
    rest_sans = [n for n in restants if str(n) not in c]
    print("Constats sites: %d | Restants SANS constat: %d" % (len(c), len(rest_sans)))
except Exception as ex:
    print("constats:", ex)

try:
    rev = json.load(open("suivi_revenus.json", encoding="utf-8"))
    entries = rev if isinstance(rev, list) else rev.get("paiements", rev.get("entries", []))
    if isinstance(entries, dict):
        entries = list(entries.values())
    reel = []
    for e in entries:
        note = str(e.get("note", ""))
        payeur = str(e.get("payeur", e.get("de", "")))
        if "TEST" in note.upper() or "mahdi-design" in payeur:
            continue
        reel.append(e)
    total = sum(float(e.get("montant", 0)) for e in reel)
    print("\nCASH REEL: %.0f EUR sur %d paiements (hors tests)" % (total, len(reel)))
    for e in reel[-5:]:
        print("  %s %s EUR %s" % (e.get("date",""), e.get("montant"), str(e.get("note",""))[:60]))
except Exception as ex:
    print("suivi_revenus:", ex)

# Gaultier#63 : etat du fil chaud
s63 = sent.get("63", {})
print("\n#63 (Gaultier): replied=%s audit_suivi=%s" % (s63.get("replied"), str(s63.get("audit_suivi",""))[:100]))

# SIMI : dernier etat
for n, s in sent.items():
    v = str(s)
    if "simi" in v.lower():
        print("#%s: %s" % (n, v[:150]))
