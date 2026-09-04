# -*- coding: utf-8 -*-
"""Conformite R1-R6 des messages en attente de GO: SIMI relance + Gaultier message."""
import json, io, sys, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

def check(nom, txt):
    # R1: pas de U+2019, R2: pas de tiret long, R3: portfolio, R4: structure
    bad_apos = txt.count("\u2019")
    bad_dash = len(re.findall(r"[\u2013\u2014]", txt))
    has_port = "mahdi-design.com" in txt
    print(f"{nom}: U+2019={bad_apos} tirets_longs={bad_dash} portfolio={'OUI' if has_port else 'NON'} longueur={len(txt)}")

# 1. Relance closing SIMI
txt = open("livrable/relance_closing_SIMI.txt", encoding="utf-8").read()
check("RELANCE SIMI", txt)
print("  TEXTE COMPLET:")
print(txt.strip())
print()

# 2. Message Gaultier (fiche 63, champ note contient ligne1-v2?)
d = json.load(open("campagne_data.json", encoding="utf-8"))
fiches = d if isinstance(d, list) else d.get("campagne", [])
f63 = next((f for f in fiches if str(f.get("num")) == "63"), None)
if f63:
    print("FICHE 63 - tous champs non vides:")
    for k, v in f63.items():
        s = str(v)
        if v and k not in ("corps",):
            print(f"  [{k}] = {s[:200]}")
    corps = f63.get("corps", "")
    if corps:
        check("CORPS GAULTIER (file)", corps)
        print("  CORPS (400 premiers):", corps[:400].replace("\n", " | "))

# 3. Le message collab prepare (commit 478fdae) - chercher dans git
print()
print("Sent 63 detail:", json.dumps(json.load(open("campagne_state.json", encoding="utf-8")).get("sent", {}).get("63", {}), ensure_ascii=False)[:300])
