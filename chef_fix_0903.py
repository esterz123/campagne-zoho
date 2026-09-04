# -*- coding: utf-8 -*-
"""Passe de correction salutations + objets — chef_fix_0903.py.

Corrige UNIQUEMENT les fiches non envoyees (envoyes intouchables).
Backup etiquete AVANT modification. Reversible via le backup.
"""
import json, re, os, shutil, datetime

REPO = r"C:\Users\ulamb\Bureau\prospection\github-campagne"
os.chdir(REPO)

TAG = "salut-objets-0903"
BAK = "campagne_data.json.bak-" + TAG
if not os.path.exists(BAK):
    shutil.copy2("campagne_data.json", BAK)
    print("Backup cree:", BAK)
else:
    print("Backup deja present:", BAK)

data = json.load(open("campagne_data.json", encoding="utf-8"))
state = json.load(open("campagne_state.json", encoding="utf-8"))
sent = state["sent"]

fix_salut = 0
fix_objet = 0
touch = []

for i, f in enumerate(data):
    num = str(f.get("num", i))
    if num in sent:
        continue  # ENVOYE = INTOUCHABLE

    # ---- Fix 1 : salutation "Bonjour M. NOM (NOM)," -> "Bonjour M. NOM," ----
    body = str(f.get("body", ""))
    lines = body.split("\n")
    changed = False
    if lines and "Bonjour" in lines[0] and "(" in lines[0]:
        m = re.search(r"\(([A-Z][A-Z'\- ]{0,25})\)\s*(,|\.|$)", lines[0])
        if m:
            cle = m.group(1).strip()
            avant = lines[0][: m.start()].lower()
            # securite : la cle doit aussi apparaitre avant la parenthese
            if cle.lower() in avant:
                lines[0] = re.sub(r"\s*\(" + re.escape(cle) + r"\)", "", lines[0])
                changed = True
    if changed:
        f["body"] = "\n".join(lines)
        fix_salut += 1
        touch.append(num)

    # ---- Fix 2 : objet "domaine.tld : X" -> "X" si X mentionne deja le domaine ----
    subj = str(f.get("subject", "")).strip()
    m = re.match(r"^([a-z0-9.-]+\.[a-z]{2,})\s*:\s*(.+)$", subj, re.IGNORECASE)
    if m:
        dom, reste = m.group(1).lower(), m.group(2).strip()
        racine = dom.split(".")[0]
        # le reste mentionne-t-il deja le domaine complet ou sa racine (>4c) ?
        if dom in reste.lower() or (len(racine) > 4 and racine.lower() in reste.lower()):
            f["subject"] = reste
            fix_objet += 1
            if num not in touch:
                touch.append(num)

print("Salutations corrigees:", fix_salut)
print("Objets redondants corriges:", fix_objet)
print("Fiches touchees:", len(touch), touch[:20])

json.dump(data, open("campagne_data.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("campagne_data.json sauvegarde.")
