"""Ressuscite 7 bounces nominatifs verifies (site 200 + MX Outlook) vers contact@.
Backup, pas de doublon (fiches reecrites en place, entrees state supprimees -> email 1 frais)."""
import json, shutil, re
from urllib.parse import urlparse

shutil.copy("campagne_state.json", "campagne_state.json.bak_ressus0905")

CIBLES = [96, 102, 107, 111, 113, 116, 267]
data = json.load(open("campagne_data.json"))
state = json.load(open("campagne_state.json"))
diag = json.load(open("diag_pages.json"))
ab = json.load(open("ab_test.json"))
bloq = set()
try:
    bloq = set(json.load(open("domaines_bloques.json")))
except FileNotFoundError:
    pass

for d in data:
    if not isinstance(d, dict) or d.get("num") not in CIBLES:
        continue
    n = d["num"]
    old_to = (state.get("sent", {}).get(str(n)) or {}).get("to", "")
    dom = old_to.split("@")[-1].lower() if "@" in old_to else ""
    assert dom and dom not in {b.lower() for b in bloq}, "domaine bloque: " + dom
    new_to = "contact@" + dom
    # anti-doublon : aucun autre num vivant sur ce generique
    for d2 in data:
        if isinstance(d2, dict) and d2.get("num") != n and (d2.get("to") or "").lower() == new_to:
            raise SystemExit("DOUBLON: " + new_to + " deja sur #" + str(d2.get("num")))
    d["to"] = new_to
    # salutation neutre si le corps nommait l'ex-salarie
    body = d.get("body") or ""
    lines = body.split("\n")
    if lines and lines[0].startswith("Bonjour") and len(lines[0]) > 10:
        lines[0] = "Bonjour,"
        d["body"] = "\n".join(lines)
    # sujet C depuis score frais
    sc = (diag.get(str(n)) or {}).get("score")
    site = d.get("site") or ""
    try:
        sdom = re.sub(r"^www\.", "", urlparse(site).hostname or "")
    except ValueError:
        sdom = ""
    sdom = sdom or dom
    if isinstance(sc, int) and sc < 75:
        d["subject"] = "J'ai audite " + sdom + " : " + str(sc) + "/100"
    else:
        d["subject"] = "Votre diagnostic est pret : " + sdom
    s = d["subject"]
    assert "\u2019" not in s and "\u2014" not in s and "matin" not in s, s
    d["note"] = ((d.get("note") or "") + " | 05/09: ex-salarie " + old_to + " bounced, bascule " + new_to + " (site 200 + MX OK)").strip(" |")
    # retour en file : l'email 1 n'a jamais ete delivre
    if str(n) in state.get("sent", {}):
        del state["sent"][str(n)]
    ab[str(n)] = {"variant": "C", "subject": s, "to": new_to}
    print("#" + str(n), old_to, "->", new_to, "|", s[:60])

json.dump(data, open("campagne_data.json", "w"), ensure_ascii=False, indent=1)
json.dump(state, open("campagne_state.json", "w"), ensure_ascii=False, indent=1)
json.dump(ab, open("ab_test.json", "w"), ensure_ascii=False, indent=1)
print("OK - 7 fiches reactivees")
