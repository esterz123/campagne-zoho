"""Repare les sujets des non-envoyes depuis diag_pages (source unique = coherence sujet/P.S.).
Regles : score<75 -> angle audit chiffre ; score>=75 -> angle propre/visibilite ;
pas de mention de temps (ce matin/instant), ASCII strict, variante C dans ab_test."""
import json, shutil, re
from urllib.parse import urlparse

import os
if not os.path.exists("campagne_data.json.bak_sujets0905"):
    shutil.copy("campagne_data.json", "campagne_data.json.bak_sujets0905")
if not os.path.exists("ab_test.json.bak_sujets0905"):
    shutil.copy("ab_test.json", "ab_test.json.bak_sujets0905")

st = json.load(open("campagne_state.json"))["sent"]
env = set()
for k in st:
    try:
        env.add(int(k))
    except ValueError:
        pass
data = json.load(open("campagne_data.json"))
diag = json.load(open("diag_pages.json"))
ab = json.load(open("ab_test.json"))

stats = {"audit": 0, "propre": 0, "question": 0, "sautes": 0}
for d in data:
    if not isinstance(d, dict) or d.get("num") in env:
        stats["sautes"] += 1
        continue
    n = d["num"]
    sc = (diag.get(str(n)) or {}).get("score")
    site = d.get("site") or ""
    try:
        dom = urlparse(site).hostname or ""
    except ValueError:
        dom = ""
    dom = re.sub(r"^www\.", "", dom)
    if not dom and d.get("to"):
        dom = d["to"].split("@")[-1]
    nom = (d.get("nom") or "").strip()
    if isinstance(sc, int) and dom:
        if sc < 75:
            d["subject"] = "J'ai audite " + dom + " : " + str(sc) + "/100"
            stats["audit"] += 1
        else:
            # score bon = JAMAIS de compliment chiffre (tue l'ouverture, lecon 04/09) :
            # curiosite alignee sur le P.S. du corps (page diag deja prete)
            d["subject"] = "Votre diagnostic est pret : " + dom
            stats["propre"] += 1
    elif nom:
        d["subject"] = "Question rapide sur votre site, " + nom
        stats["question"] += 1
    else:
        print("SANS SCORE NI NOM : #", n)
        continue
    s = d["subject"]
    assert "\u2019" not in s and "\u2014" not in s and "\u2013" not in s, s
    assert "matin" not in s and "instant" not in s, s
    ab[str(n)] = {"variant": "C", "subject": s, "to": d.get("to")}

json.dump(data, open("campagne_data.json", "w"), ensure_ascii=False, indent=1)
json.dump(ab, open("ab_test.json", "w"), ensure_ascii=False, indent=1)
print(stats)
