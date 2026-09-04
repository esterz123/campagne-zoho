# -*- coding: utf-8 -*-
"""Pre-filtre SMTP RCPT des fiches restantes (04/09).
But : zero bounce => economie de quota + reputation domaine.
Idempotent : relance = ne reverifie que les absents de prefilter_smtp.json.
Escrit prefilter_smtp.json, ne touche JAMAIS campagne_data.json.
"""
import json, os, sys, socket, smtplib, time
from concurrent.futures import ThreadPoolExecutor, as_completed

REPO = os.path.dirname(os.path.abspath(__file__))
os.chdir(REPO)
sys.path.insert(0, REPO)

PREF = "prefilter_smtp.json"
RGPD_RE = ("donnees", "privacy", "rgpd", "dpo", "noreply", "no-reply")

def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)

data = load("campagne_data.json")
fiches = {str(f["num"]): f for f in data}
state = load("campagne_state.json")
sent = set(state["sent"].keys())
restants = {k: f for k, f in fiches.items() if k not in sent}

# etat existant (idempotent)
try:
    pref = load(PREF)
except Exception:
    pref = {}

todo = {k: f for k, f in restants.items() if k not in pref}
print("Restants: %d | deja filtres: %d | a verifier: %d" % (len(restants), len(pref), len(todo)))

def check_one(item):
    num, f = item
    email = (f.get("to") or "").strip()
    if not email or "@" not in email:
        return num, {"verdict": "pas_d_email", "email": email}
    local = email.split("@")[0].lower()
    if any(r in local for r in RGPD_RE):
        return num, {"verdict": "hold_rgpd", "email": email}
    try:
        import verify_smtp as vs
        ok, detail = vs.smtp_verify(email)
        if ok is True:
            v = "ok"
        elif ok is False:
            v = "morte"
        else:
            v = "bloque"
        return num, {"verdict": v, "email": email, "detail": str(detail)[:80]}
    except Exception as e:
        return num, {"verdict": "bloque", "email": email, "detail": repr(e)[:80]}

results = {}
done = 0
t0 = time.time()
with ThreadPoolExecutor(max_workers=8) as ex:
    futs = {ex.submit(check_one, it): it[0] for it in todo.items()}
    for fut in as_completed(futs):
        try:
            num, r = fut.result(timeout=120)
        except Exception as e:
            num = futs[fut]
            r = {"verdict": "bloque", "detail": repr(e)[:60]}
        results[num] = r
        done += 1
        if done % 20 == 0:
            pref.update(results)
            with open(PREF, "w", encoding="utf-8") as fo:
                json.dump(pref, fo, ensure_ascii=False, indent=1)
            print("checkpoint %d/%d (%.0fs)" % (done, len(todo), time.time() - t0))

pref.update(results)
with open(PREF, "w", encoding="utf-8") as fo:
    json.dump(pref, fo, ensure_ascii=False, indent=1)

# synthese
from collections import Counter
c = Counter(r["verdict"] for r in pref.values())
print("SYNTHESE TOTALE:", dict(c))
mortes = sorted((int(k), pref[k]["email"]) for k, v in pref.items() if v["verdict"] == "morte")
print("MORTES (%d):" % len(mortes))
for n, e in mortes[:40]:
    print("  %s %s" % (n, e))
