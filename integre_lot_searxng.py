#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Integre les prospects qualifies par chasse_searxng.py dans campagne_data.json (+ fichiers V2).
Lit _chasse_searxng_lot.json, dedup, genere premier message V2 (constats reels + dirigeant), ajoute.
Usage: python3 integre_lot_searxng.py
"""
import json, os, re, sys
BASE = os.path.dirname(os.path.abspath(__file__))
LOT = os.path.join(BASE, "_chasse_searxng_lot.json")
if not os.path.exists(LOT):
    print("Lot absent:", LOT); sys.exit(1)
lot = json.load(open(LOT, encoding="utf-8"))
data = json.load(open(os.path.join(BASE,"campagne_data.json"),encoding="utf-8"))
exem = {(e.get("to") or "").lower() for e in data}

def sais_piege(em):
    BAD = ("groupe-ecomedia","infobel","fabriquons","ouest-france","infoterre","lafrenchfab",
           "brgm","usw.cloud","mairie","lefigaro","cadastre","monbeauvillage","mappy","118712",
           "wikipedia","societe.com","pagesjaunes","annuaire","data.gouv","verif.com","kompass",
           "europages","infogreffe","google","facebook","linkedin","instagram","x.com","pappers",
           "nordvpn","tourisme","footballberry","laprovence","explore-savoie","cdtsavoie",
           "institutfrancais","mecaniqueautofacile","materiel-soudure","eberhard.de","metallerie.com",
           "orange.fr","wanadoo.fr","gmail.com","free.fr","hotmail","laposte.net","domain.fr")
    em = em.lower()
    if any(b in em for b in BAD):
        return True
    if em.split("@")[0].startswith(("abonnement","commande","boutique","vente","newsletter")):
        return True
    return False

added = 0
for r in lot:
    em = (r.get("email") or "").strip().lower()
    if not em or em in exem or sais_piege(em):
        continue
    nom = r.get("nom",""); site = r.get("site",""); dirg = r.get("dirigeant","")
    constats = r.get("constats") or []
    # salutation avec civilite
    sal = "Bonjour,"
    if dirg and dirg != "A CONFIRMER":
        prenom = dirg.split()[0].strip()
        # extraire nom de famille (tout apres prenom) pour civilite
        parts = dirg.split()
        civil = "Mme " if "MME" in dirg.upper() or "MADAME" in dirg.upper() else "M. "
        if len(parts) >= 2:
            sal = f"Bonjour {civil}{prenom.capitalize()} {parts[-1].title()},"
        else:
            sal = f"Bonjour {civil}{prenom.capitalize()},"
    # construire constats textuels
    pts = []
    for c in constats[:3]:
        t = re.sub(r"\s+"," ", c).strip()
        if t and t.lower() not in ("","aucun constat majeur"):
            pts.append(t)
    if not pts:
        pts = ["Votre site ne reflète pas la solidité de votre savoir-faire industriel."]
    clos = "\n".join("1. " + p for p in pts)
    body = f"""{sal}

En travaillant sur un comparatif des sous-traitants industriels, j'ai passé quelques minutes sur {site}. Plusieurs points m'ont frappé, et ils sont vérifiables en 2 minutes :

{clos}

Dans l'industrie, le site est le premier filtre des donneurs d'ordre : il rassure, ou fait douter, avant même un premier échange.

**Ce que je vous propose, gratuitement et sans engagement :**
Un diagnostic de votre image digitale : l'état de votre présence en ligne point par point (disponibilité, sécurité, design), la comparaison avec 2 de vos concurrents, et 5 recommandations concrètes dont plusieurs gratuites. Vous gardez le document, que vous travailliez ou non avec moi.

Il me suffit d'une réponse à cet email pour vous l'envoyer sous 48h.

Cordialement,
Mahdi
Portfolio : mahdi-design.com"""
    num = max(e.get("num") or 0 for e in data) + 1
    entry = {"num":num,"prospect":f"{num} — {nom.title()}","to":em,
             "subject":f"Votre site {site} mérite mieux que ce qu'il montre",
             "body":body,"to_confirmed":True}
    data.append(entry)
    exem.add(em)
    # fichier V2
    v2 = os.path.join(BASE,"premiers_messages_v2",f"premier_msg_v2_prospect_{num}.txt")
    with open(v2,"w",encoding="utf-8") as f:
        f.write(f"OBJET: Votre site {site} mérite mieux que ce qu'il montre\n\n" + body)
    print(f"+ #{num} {nom[:38]} -> {em} (dirg={dirg or 'neutre'}) score={r.get('score')}")
    added += 1

json.dump(data, open(os.path.join(BASE,"campagne_data.json"),"w",encoding="utf-8"), ensure_ascii=False, indent=1)
print("=== %d prospects integres | file totale: %d ===" % (added, len(data)))
