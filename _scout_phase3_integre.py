#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SCOUT PHASE 3 - integre les emails SMTP-ok des 2 pistes dans la file.
Sorties : _scout_phase2b_etat.json (status ok) + _scout_phase2_etat.json (status ok).
Format exact des fiches campagne_data.json, num a partir de 351, texte standard
(la chaine preuve du Chef les transformera). Dedupe email + domaine. Zero U+2019.
"""
import json
import re
import os

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "campagne_data.json")


def clean(t):
    return (t or "").replace("\u2019", "'").replace("\u2018", "'")


def main():
    data = json.load(open(DATA, encoding="utf-8"))
    st = json.load(open(os.path.join(BASE, "campagne_state.json"), encoding="utf-8"))
    sent = set(str(k) for k in st.get("sent", {}))
    last = max(int(r.get("num", 0)) for r in data)
    doms = {(r.get("to") or "").split("@")[-1].lower() for r in data}
    emails = {(r.get("to") or "").lower() for r in data}

    tous = []
    try:
        b = json.load(open(os.path.join(BASE, "_scout_phase2b_etat.json"), encoding="utf-8"))
        tous += [v for v in b.values() if v.get("verdict") == "ok"]
    except Exception:
        pass
    try:
        a = json.load(open(os.path.join(BASE, "_scout_phase2_etat.json"), encoding="utf-8"))
        tous += [v for v in a.values() if v.get("status") == "ok"]
    except Exception:
        pass

    next_num = last + 1
    integres = []
    for v in tous:
        email = (v.get("email") or "").strip().lower()
        dom = (v.get("site") or "").strip().lower()
        nom = clean((v.get("nom") or "PME industrielle").split("(")[0].strip())[:45] or "PME industrielle"
        if not email or not dom or email in emails or dom in doms:
            continue
        fiche = {
            "num": next_num,
            "prospect": nom,
            "to": email,
            "site": "https://" + dom,
            "subject": "3 points qui coutent des clients a %s" % nom[:30],
            "body": ("Bonjour,\n\nVotre site %s m'a saute aux yeux en le parcourant. "
                     "Plutot que de vous vendre quoi que ce soit, je vous liste gratuitement "
                     "2 ou 3 points qui font fuir vos prospects : vitesse, mobile, confiance.\n\n"
                     "Repondez simplement \"oui\" et je vous envoie le rapport sous 48h, "
                     "vous le gardez, sans engagement.\n\nCordialement,\nMahdi\n"
                     "Portfolio : mahdi-design.com") % dom,
            "to_confirmed": True,
        }
        assert "\u2019" not in json.dumps(fiche) and "\u2014" not in json.dumps(fiche)
        data.append(fiche)
        emails.add(email)
        doms.add(dom)
        integres.append((next_num, email))
        next_num += 1

    if integres:
        json.dump(data, open(DATA, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("integres: %d -> nums %s" % (len(integres), [n for n, _ in integres]))
    for n, e in integres:
        print("  #%s %s" % (n, e))
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
