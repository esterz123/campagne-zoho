# -*- coding: utf-8 -*-
"""Verification envoi Gaultier (go2) + dernier cycle boucle journal."""
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# 1. Dernier cycle boucle (structure {cycles: [...]})
j = json.load(open("amelioration_journal.json", encoding="utf-8"))
cyc = j.get("cycles", []) if isinstance(j, dict) else j
if cyc:
    last = cyc[-1]
    print("DERNIER CYCLE BOUCLE (%s):" % last.get("date", "?")[:19])
    m = last.get("mesure", {})
    print("  file:", m.get("file_restante"), "| envoyes:", m.get("envoyes"), "| replies:", m.get("replies"), "| taux:", m.get("taux_reponse_pct"), "% | argent:", m.get("argent_reel_eur"))
    print("  diagnostic:", last.get("diagnostic"))
    print("  action:", last.get("action"))
    print("  resultat:", str(last.get("resultat"))[:200])
print("  total cycles:", len(cyc))

# 2. Trace go2 Gaultier
import os, glob
cands = glob.glob("go2*") + glob.glob("*go2*") + glob.glob("livrable/*go2*") + glob.glob("livrable/message_GAULTIER*")
print("\nFichiers go2/Gaultier:", cands)
for c in cands[:3]:
    if os.path.isfile(c):
        print("--- %s (dernieres lignes) ---" % c)
        lines = open(c, encoding="utf-8", errors="replace").read().splitlines()
        for ln in lines[-8:]:
            print(" ", ln[:160])

# 3. Etat de la relance SIMI: marquee comme envoyee quelque part ?
st = json.load(open("campagne_state.json", encoding="utf-8"))
s0 = st.get("sent", {}).get("0", {})
print("\nSENT 0 (SIMI) note:", str(s0.get("note"))[:250])
print("Cles etat contenant 'simi':", [k for k in st.keys() if "simi" in k.lower()])
for k, v in st.items():
    if isinstance(v, dict):
        for kk, vv in v.items():
            if "simi" in str(kk).lower() or "relance_closing" in str(vv):
                print(f"  {k}/{kk}:", str(vv)[:150])
