# -*- coding: utf-8 -*-
"""Bilan KPI Chef 03/09 : join data<->state, cash reel, etat GO en attente."""
import json, os, subprocess, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = os.path.dirname(os.path.abspath(__file__))
os.chdir(REPO)
subprocess.run(["git","pull","--rebase","--autostash"], capture_output=True)

data = json.load(open("campagne_data.json", encoding="utf-8"))
state = json.load(open("campagne_state.json", encoding="utf-8"))
if isinstance(data, dict):
    prospects = [f for f in (data.get("prospects") or data.get("fiches") or []) if f.get("type","prospect")=="prospect"]
else:
    prospects = [f for f in data if f.get("type","prospect")=="prospect"]
sent = state.get("sent", {})
sent_keys = {k for k in sent.keys() if k.isdigit()}

restants = [f for f in prospects if str(f["num"]) not in sent_keys]
print(f"fiches prospect: {len(prospects)} | envoyes: {len(sent_keys)} | RESTANTS REELS: {len(restants)}")

constats = {}
if os.path.exists("constats_sites.json"):
    constats = json.load(open("constats_sites.json", encoding="utf-8"))
sans_constat, with_note = [], []
for f in restants:
    c = constats.get(str(f["num"]))
    note = c.get("note") if isinstance(c, dict) else None
    (sans_constat if note is None else with_note).append((f["num"], note))
with_note.sort(key=lambda x: x[1])
print(f"restants SANS preuve: {len(sans_constat)} | restants avec preuve (prets a envoyer): {len(with_note)}")
print("top 10 restants par note site (les plus casses):")
for n, note in with_note[:10]:
    print(f"  num {n} note {note}")

replied = sorted([k for k in sent_keys if isinstance(sent[k], dict) and sent[k].get("replied")])
print(f"replies: {len(replied)} -> {replied[:12]}")

total = 0.0
if os.path.exists("suivi_revenus.json"):
    rev = json.load(open("suivi_revenus.json", encoding="utf-8"))
    entries = rev if isinstance(rev, list) else rev.get("paiements", rev.get("entries", []))
    for e in entries:
        blob = (str(e.get("note","")) + str(e.get("payeur","")) + str(e.get("de",""))).upper()
        if "TEST" in blob or "MAHDI-DESIGN" in blob:
            continue
        try: total += float(e.get("montant", 0))
        except (TypeError, ValueError): pass
print(f"CASH REEL cumule: {total:.2f} EUR")

for mot in ("simi", "gaultier", "fpsa", "itplast"):
    hits = [(f["num"], sent.get(str(f["num"]))) for f in prospects if mot in json.dumps(f, ensure_ascii=False).lower()]
    if hits: print(f"{mot.upper()}: {hits}")

# GO en attente : fichiers marquants
for fn in ("relance_closing_SIMI.txt",):
    p = os.path.join("livrable", fn)
    print(f"GO waiting file {p}: {'PRESENT' if os.path.exists(p) else 'ABSENT'}")
# derniere activite repondeur/closer
for fn in ("repondeur_state.json", "closer_state.json"):
    if os.path.exists(fn):
        mtime = os.path.getmtime(fn)
        import datetime
        print(f"{fn}: maj {datetime.datetime.fromtimestamp(mtime):%d/%m %H:%M}")
