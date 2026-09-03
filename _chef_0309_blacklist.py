# -*- coding: utf-8 -*-
"""Chef 03/09 : ajoute les emails morts (bounce) au blacklist _emails_morts.
Additif, reversible, zero envoi. Les domains ne sont PAS blacklistes (un email
mort n'egale pas un domaine mort)."""
import json

REPO = "C:/Users/ulamb/Bureau/prospection/github-campagne"
state = json.load(open(REPO + "/campagne_state.json", encoding="utf-8"))
data = json.load(open(REPO + "/campagne_data.json", encoding="utf-8"))
sent = state.get("sent", {})
prospects = [p for p in data if p.get("type", "prospect") == "prospect"] if isinstance(data, list) else list(data.values())
by_num = {str(p.get("num")): p for p in prospects if p.get("num") is not None}

BL = REPO + "/domaines_bloques.json"
bl = json.load(open(BL, encoding="utf-8"))
morts = set(bl.get("_emails_morts", []))

ajoutes = []
for n, s in sent.items():
    if not s.get("bounce"):
        continue
    note = str(s.get("note", "")).lower()
    f = by_num.get(n, {})
    to = str(f.get("to", "")).lower().strip()
    if not to or "@" not in to:
        continue
    # SMTP-verif pre-envoi ("jamais envoye") : l'email n'a jamais recu rien,
    # le marquer mort est aussi correct (user unknown verifie).
    if to not in morts:
        morts.add(to)
        ajoutes.append(to)

bl["_emails_morts"] = sorted(morts)
bl["_maj_emails_morts"] = "03/09 : sync bounce state -> emails morts (" + str(len(ajoutes)) + " ajoutes)"

with open(BL, "w", encoding="utf-8") as f:
    json.dump(bl, f, ensure_ascii=False, indent=1)

print(f"Emails morts total: {len(morts)} | ajoutes ce tour: {len(ajoutes)}")
for a in ajoutes[:10]:
    print("  +", a)
# revalidation code : domaine_bloque doit les refuser
import campagne_zoho as cz
blq = cz.load_bloquees()
tests = [a for a in ajoutes[:5]]
for t in tests:
    print(f"  check {t} -> bloque={cz.domaine_bloque(t, blq)}")
