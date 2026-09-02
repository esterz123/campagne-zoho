#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
REECRITURE SUJETS A/B MORTS (02/09) : verdict A/B = 0% sur 211 envois.
Les 110 non-envoyes avec sujet "3 points..." / "Question rapide..." reçoivent
un sujet PREUVE honnête bati sur constats_sites.json (meme logique que
objet_pour de injecteur_preuves.py). Idempotent. Charset Mahdi : apostrophe
droite, zero tiret long, zero U+2019.
"""
import json
import os
import shutil
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "campagne_data.json")
PREUVES = os.path.join(BASE, "constats_sites.json")

GEN = ("3 points", "Question rapide")


def sujet_pour(p, dom):
    note = p.get("note")
    etat = p.get("etat")
    if etat == "BLOQUE" or note is None:
        return "Je n'ai pas reussi a ouvrir votre site %s ce matin" % dom
    if note >= 85:
        return "Votre site %s est propre (%d/100). C'est pour la visibilite que j'ecris" % (dom, note)
    return "J'ai audite %s ce matin: %d/100" % (dom, note)


def main():
    data = json.load(open(DATA, encoding="utf-8"))
    preuves = json.load(open(PREUVES, encoding="utf-8"))
    state = json.load(open(os.path.join(BASE, "campagne_state.json"), encoding="utf-8"))
    sent = state.get("sent", {})
    envoyes = {k for k, v in sent.items() if isinstance(v, dict) and v.get("on")}

    changes = 0
    exemples = []
    for r in data:
        if r.get("type", "prospect") != "prospect":
            continue
        num = str(r.get("num"))
        if num in envoyes:
            continue
        sub = r.get("subject", "")
        if not any(g in sub for g in GEN):
            continue
        p = preuves.get(num)
        dom = (p or {}).get("domaine") or (r.get("domaine") or "").replace("https://", "").replace("www.", "")
        if not dom:
            continue
        ns = sujet_pour(p or {}, dom)
        ns = ns.replace("\u2019", "'").replace("\u2014", "-").replace("\u2013", "-")
        if ns != sub:
            r["subject"] = ns
            changes += 1
            if len(exemples) < 5:
                exemples.append((num, ns))

    print("sujets A/B morts reecrits: %d" % changes)
    for n, s in exemples:
        print("  num %s: %s" % (n, s))

    if changes and "--dry" not in sys.argv:
        shutil.copy(DATA, DATA + ".bak-sujets")
        json.dump(data, open(DATA, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("ECRIT (backup .bak-sujets)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
