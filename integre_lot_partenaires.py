#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Integre les lots partenaires (cabinets + agences) qualifies par chasse_searxng.py
dans campagne_partenaires.json avec le GABARIT PARTENARIAT (commission 15%).
A NE PAS utiliser pour les industriels (ceux-la vont dans campagne_data via integre_lot_searxng.py).
Usage: python3 integre_lot_partenaires.py --lots _lot_cab_B.json,_lot_ag_C.json
"""
import json, os, re, sys
BASE = os.path.dirname(os.path.abspath(__file__))

def palier():
    for l in sys.argv[sys.argv.index("--lots")+1].split(","):
        yield os.path.join(BASE, l.strip())

def sais_piege(dom):
    """Filtre anti-faux-positifs (validation post-chasse, 18/08).
    Rejette les domaines tiers/parking/homonymes connus et les emails generiques (abonnement@)."""
    BAD = ("groupe-ecomedia","infobel","fabriquons","ouest-france","infoterre","lafrenchfab",
           "brgm","usw.cloud","mairie","lefigaro","cadastre","monbeauvillage","mappy","118712",
           "wikipedia","societe.com","pagesjaunes","annuaire","data.gouv","verif.com","kompass",
           "europages","infogreffe","google","facebook","linkedin","instagram","x.com","pappers",
           "nordvpn","tourisme","footballberry","laprovence","explore-savoie","cdtsavoie",
           "institutfrancais","mecaniqueautofacile","materiel-soudure","eberhard.de","metallerie.com",
           "exemple@","domain.fr","orange.fr","wanadoo.fr","gmail.com","free.fr","hotmail","laposte.net")
    if any(b in dom for b in BAD):
        return True
    if dom.startswith(("abonnement@","commande@","boutique@","vente@","newsletter@","infos@")):
        return True
    return False

def build_email(nom, dirigeant, ville, pool):
    if dirigeant and dirigeant != "A CONFIRMER":
        parts = dirigeant.split()
        civil = "Mme" if "MME" in dirigeant.upper() else "M."
        if len(parts) >= 2:
            sal = "Bonjour %s %s %s," % (civil, parts[0].capitalize(), parts[-1].title())
        else:
            sal = "Bonjour %s %s," % (civil, parts[0].capitalize())
    else:
        sal = "Bonjour,"
    sujet = "Partenariat : je refais le site de vos clients industriels, vous touchez 15%"
    corps = f"""{sal}

Je suis Mahdi, brand designer spécialisé dans les PME industrielles françaises (plasturgie, usinage, décolletage, fonderie). Je travaille depuis {ville or "toute la France"}.

**Vos clients industriels ont probablement des sites qui datent, et la refonte de leur identité n'est pas votre cœur de métier.**

Voici ma proposition : je m'occupe de la refonte complète de leur marque et de leur site (devis, design, livraison), vous gardez la relation client, et vous touchez 15% de commission sur chaque projet signé. Zéro risque pour votre réputation : votre client reçoit d'abord un diagnostic gratuit.

Si cela vous intéresse, une simple réponse suffit et je vous envoie un exemple de projet.

Cordialement,
Mahdi
Portfolio : mahdi-design.com"""
    return sujet, corps

def main():
    part = json.load(open(os.path.join(BASE,"campagne_partenaires.json"),encoding="utf-8"))
    exem = {(p.get("to") or "").lower() for p in part}
    added = 0
    for lot_path in palier():
        if not os.path.exists(lot_path):
            print("lot absent:", lot_path); continue
        lot = json.load(open(lot_path, encoding="utf-8"))
        nxt = max((p.get("num") or 0) for p in part) + 1 if part else 1
        for i, r in enumerate(lot):
            em = (r.get("email") or "").strip().lower()
            if not em or em in exem or sais_piege(em):
                continue
            sujet, corps = build_email(r.get("nom",""), r.get("dirigeant",""), r.get("ville",""), r.get("pool",""))
            entry = {"num": nxt, "prospect": "%d — %s" % (nxt, (r.get("nom") or "").title()),
                     "to": em, "subject": sujet, "body": corps}
            part.append(entry); exem.add(em); nxt += 1; added += 1
            print("+ partenaire %-34s -> %s" % (r.get("nom","")[:34], em))
    json.dump(part, open(os.path.join(BASE,"campagne_partenaires.json"),"w",encoding="utf-8"), ensure_ascii=False, indent=1)
    print("=== %d partenaires integres | file partenaires totale: %d ===" % (added, len(part)))

if __name__ == "__main__":
    main()
