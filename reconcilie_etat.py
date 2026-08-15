#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RECONCILIE ETAT v1 — verite terrain apres incident doublons (16/08).
========================================================================
Lit les 5 boites Zoho (dossier Envoyes du jour) et resynchronise
campagne_state.json : tout email de la file dont le destinataire a VRAIMENT
recu un envoi aujourd hui est marque envoye (via + note), meme si le run
qui l a envoye est mort avant la sauvegarde. Detecte aussi les doublons.

Usage : python3 reconcilie_etat.py [--dry-run]
Securite : lecture seule des boites ; ne cree jamais d envoi.
"""
import json, os, sys, datetime, urllib.request, urllib.parse
from collections import Counter

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
import campagne_zoho as CZ

today = datetime.date.today().isoformat()


def norm(a):
    return CZ._norm_addr(a)


def main():
    dry = "--dry-run" in sys.argv
    boites = CZ.load_boites()
    tokens = {}

    def token_pour(b):
        if b["nom"] not in tokens:
            tokens[b["nom"]] = CZ.refresh_token(b)
        return tokens[b["nom"]]

    # 1. verite terrain : qui a recu quoi aujourd hui, par boite
    recus = Counter()   # email -> nb d envois aujourd hui
    boite_par = {}      # email -> premiere boite
    for b in boites:
        try:
            tok = token_pour(b)
            url = ("https://mail.zoho.com/api/accounts/%s/messages/search"
                   "?searchKey=in%%3Asent&limit=200") % b["account_id"]
            req = urllib.request.Request(url, headers={"Authorization": "Zoho-oauthtoken " + tok})
            msgs = json.load(urllib.request.urlopen(req, timeout=25)).get("data", [])
        except Exception as e:
            print("boite %s : API KO (%s)" % (b["nom"], str(e)[:60]))
            continue
        for m in msgs:
            ts = int(m.get("receivedTime", 0) or 0) / 1000
            if not ts:
                continue
            d = datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
            if d != today:
                continue
            to = norm(m.get("toAddress"))
            if not to:
                continue
            recus[to] += 1
            boite_par.setdefault(to, b["nom"])
    print("VERITE TERRAIN : %d destinataires ont recu un email aujourd hui" % len(recus))

    # 2. synchronisation avec la file
    data = CZ.jload(CZ.DATA, []) if hasattr(CZ, "jload") else json.load(open(CZ.DATA, encoding="utf-8"))
    emails = data if isinstance(data, list) else data.get("emails", [])
    state = CZ.load_state()
    sent = state["sent"]
    doublons = {to: c for to, c in recus.items() if c > 1}
    ajoutes = 0
    for e in emails:
        num = str(e.get("num", ""))
        if num in sent:
            continue
        to = norm(e.get("to"))
        if to in recus:
            sent[num] = {"on": today, "via": boite_par.get(to, "?"),
                         "reconcilie": True,
                         "doublon": recus[to] > 1,
                         "note": "reconcilie depuis la boite (%dx envoye)" % recus[to]}
            ajoutes += 1
            print("  #%s %s -> MARQUE envoye (via %s%s)"
                  % (num, to, boite_par.get(to, "?"), " DOUBLON x%d" % recus[to] if recus[to] > 1 else ""))
    state["sent"] = sent
    if not dry and ajoutes:
        CZ.save_state(state)
    print()
    print("RECONCILIES : %d | DOUBLONS detectes : %d | %s"
          % (ajoutes, len(doublons), "DRY-RUN (rien ecrit)" if dry else "etat mis a jour"))
    for to, c in sorted(doublons.items(), key=lambda x: -x[1]):
        print("  DOUBLON %s x%d" % (to, c))


if __name__ == "__main__":
    main()
