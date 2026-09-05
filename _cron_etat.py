import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = "C:/Users/ulamb/Bureau/prospection/github-campagne/"

s = json.load(open(BASE + "campagne_state.json"))
sent = s.get("sent", {})
rep = [n for n in sent if sent[n].get("replied")]
bounce = [n for n in sent if sent[n].get("bounce")]
print("== CAMPAGNE ==")
print("envoyes total:", len(sent))
print("replied:", len(rep), sorted(rep, key=lambda x: int(x))[:40])
print("bounces:", len(bounce))
import collections
per_day = collections.Counter(v.get("on", "?") for v in sent.values())
for day in sorted(per_day)[-8:]:
    print("  ", day, "->", per_day[day])

d = json.load(open(BASE + "campagne_data.json"))
p = d.get("prospects", d) if isinstance(d, dict) else d
rest = [x for x in p if str(x.get("num")) not in sent]
print("file totale:", len(p), "| restants non envoyes:", len(rest))

# suivi revenus
try:
    rev = json.load(open(BASE + "suivi_revenus.json"))
    encaisse = sum(e["montant"] for e in rev.get("entrees", []) if e.get("statut") == "encaisse")
    print("== REVENUS == encaisse:", encaisse, "| entrees:", len(rev.get("entrees", [])))
    for e in rev.get("entrees", [])[-10:]:
        print("  ", e)
except Exception as ex:
    print("suivi_revenus:", ex)

# relances en attente
try:
    fu = json.load(open(BASE + "followups.json"))
    print("== FOLLOWUPS ==", [k for k in fu.keys()] if isinstance(fu, dict) else type(fu))
except Exception as ex:
    print("followups:", ex)

# ab test
try:
    ab = json.load(open(BASE + "ab_resultats.json"))
    print("== A/B ==", json.dumps(ab)[:400])
except Exception as ex:
    pass
try:
    ab = json.load(open(BASE + "ab_test.json"))
    print("ab_test.json:", json.dumps(ab)[:300])
except Exception:
    pass

# partenaires
try:
    ps = json.load(open(BASE + "partenaires_state.json"))
    pss = ps.get("sent", ps)
    print("== PARTENAIRES == envoyes:", len(pss) if isinstance(pss, dict) else "?")
except Exception as ex:
    print("partenaires:", ex)
