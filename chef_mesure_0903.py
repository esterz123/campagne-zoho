# -*- coding: utf-8 -*-
"""Mesure artefacts salutation (NOM) et objets empiles — chef_mesure_0903.py."""
import json, re, os

os.chdir(r"C:\Users\ulamb\Bureau\prospection\github-campagne")
data = json.load(open("campagne_data.json", encoding="utf-8"))
state = json.load(open("campagne_state.json", encoding="utf-8"))
sent = state["sent"]
restants = [f for i, f in enumerate(data) if str(f.get("num", i)) not in sent]

# Artefact 1 : "(NOM)," ou "(NOM)." dans la 1re ligne (salutation)
salut_artifact = []
for f in restants:
    num = str(f.get("num"))
    prem = str(f.get("body", "")).strip().split("\n")[0]
    if re.search(r"\([A-Z][A-Z'\- ]{1,25}\)\s*[,;.]", prem):
        salut_artifact.append((num, prem[:70]))
print("SALUTATIONS avec artefact (NOM):", len(salut_artifact))
for num, p in salut_artifact[:12]:
    print("  #%s: %s" % (num, p))

# Artefact 2 : objet avec prefixe domaine duplique "domaine.tld : "
obj_dup = []
for f in restants:
    num = str(f.get("num"))
    subj = str(f.get("subject", "")).strip()
    m = re.match(r"^([a-z0-9.-]+\.[a-z]{2,})\s*[:\-]\s*(.+)$", subj, re.IGNORECASE)
    if m and m.group(2).lower().startswith(m.group(1).lower().split(".")[0][:6]):
        obj_dup.append((num, subj[:80]))
print("\nOBJETS avec prefixe domaine duplique:", len(obj_dup))
for num, s in obj_dup[:12]:
    print("  #%s: %s" % (num, s))

# Combien d'objets commencent par "<domaine> : " tout court (tous)
obj_prefix = []
for f in restants:
    subj = str(f.get("subject", "")).strip()
    if re.match(r"^[a-z0-9.-]+\.[a-z]{2,}\s*:", subj, re.IGNORECASE):
        obj_prefix.append(str(f.get("num")))
print("\nOBJETS commencant par domaine+':' (tous):", len(obj_prefix), obj_prefix[:15])
