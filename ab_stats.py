#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AB STATS - mesure ce qui fait repondre, des que la data existe.
================================================================
Croise campagne_state (envois/replies) avec constats_sites (type de preuve)
et la forme de l'objet. Sort un tableau : taux de reply par categorie.
Zero LLM. A lancer chaque jour ; le verdict se lit quand n>=30 par categorie.
Usage : python3 ab_stats.py
"""
import os
import re
import json
import datetime

BASE = os.path.dirname(os.path.abspath(__file__))


def main():
    data = {str(r.get("num")): r for r in json.load(open(os.path.join(BASE, "campagne_data.json"), encoding="utf-8"))}
    st = json.load(open(os.path.join(BASE, "campagne_state.json"), encoding="utf-8"))
    preuves = {}
    p = os.path.join(BASE, "constats_sites.json")
    if os.path.exists(p):
        preuves = json.load(open(p, encoding="utf-8"))
    sent = st.get("sent", {})

    def cat(num):
        r = data.get(num, {})
        subj = (r.get("subject") or "").lower()
        f = preuves.get(num, {})
        if f.get("pirate"):
            return "objet:pirate"
        if f.get("etat") not in (None, "VIVANT", "BLOQUE"):
            return "objet:mort"
        if "non securise" in subj or f.get("http_seul"):
            return "objet:https"
        if re.search(r"audite .*(\d+)/100", subj):
            return "objet:note"
        if "3 points" in subj or "perd" in subj or "coutent" in subj:
            return "objet:generique-ancien"
        return "objet:autre"

    rows = {}
    for num, v in sent.items():
        if not v.get("on"):
            continue
        c = cat(num)
        e = rows.setdefault(c, {"envoyes": 0, "replies": 0, "relances": 0})
        e["envoyes"] += 1
        if v.get("replied"):
            e["replies"] += 1
        if v.get("sent_relance1") or v.get("sent_relance2"):
            e["relances"] += 1
    print("=== AB STATS %s ===" % datetime.date.today().strftime("%d/%m"))
    print("%-24s %7s %7s %8s" % ("categorie", "envoyes", "replies", "taux"))
    for c in sorted(rows, key=lambda x: -rows[x]["envoyes"]):
        e = rows[c]
        t = 100.0 * e["replies"] / max(1, e["envoyes"])
        flag = " <- n<30, pas de verdict" if e["envoyes"] < 30 else ""
        print("%-24s %7d %7d %7.1f%%%s" % (c, e["envoyes"], e["replies"], t, flag))
    tot_e = sum(e["envoyes"] for e in rows.values())
    tot_r = sum(e["replies"] for e in rows.values())
    print("TOTAL: %d envoyes, %d replies (%.1f%%)" % (tot_e, tot_r, 100.0 * tot_r / max(1, tot_e)))


if __name__ == "__main__":
    main()
