#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CHEF 03/09 00h : repare les pages diag manquantes / 404.
Cible: _fix_diag_48.txt (48 fiches restantes dont le lien P.S. serait 404
+ 31 restants sans entree manifest) et les 33 deja envoyes dont le lien est mort.
Pour chaque num: scan du site -> page HTML dans vitrine/diag -> maj diag_pages.json.
Idempotent, ne supprime rien, zero U+2019."""
import json, os, sys, io

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import genere_pages_diag as G

DATA = os.path.join(BASE, "campagne_data.json")
STATE = os.path.join(BASE, "campagne_state.json")
MANIFEST = G.MANIFEST
DIAG_DIR = G.DIAG_DIR

cible = []
p = os.path.join(BASE, "_fix_diag_48.txt")
if os.path.exists(p):
    cible = [x.strip() for x in io.open(p, encoding="utf-8") if x.strip()]
print("cible:", len(cible), "fiches")

data = {str(e["num"]): e for e in json.load(io.open(DATA, encoding="utf-8"))}
st = json.load(io.open(STATE, encoding="utf-8"))
sent = set(st.get("sent", {}).keys())
man = json.load(io.open(MANIFEST, encoding="utf-8"))

fait, rate = 0, []
for num in cible:
    e = data.get(num)
    if not e:
        rate.append((num, "absent data")); continue
    site = (e.get("site") or e.get("url") or "").strip()
    if not site:
        rate.append((num, "pas de site")); continue
    dom, constats, score = G.scan(site)
    if not dom:
        # site mort: page d'excuse neutre pour que le lien ne soit PAS un 404
        nom = e.get("prospect") or (dom or site).split(".")[0].title()
        fn = os.path.join(DIAG_DIR, "%s.html" % num)
        io.open(fn, "w", encoding="utf-8", newline="").write(
            G.page_html(num, nom, site, [["Site", "momentanement injoignable lors du scan"]],
                        score if score else 0))
        man[num] = {"url": "https://mahdi-design.com/diag/%s.html" % num,
                    "score": score if score else 0, "note": "site injoignable au scan"}
        rate.append((num, "site injoignable -> page neutre"))
    else:
        nom = e.get("prospect") or dom.split(".")[0].title()
        fn = os.path.join(DIAG_DIR, "%s.html" % num)
        io.open(fn, "w", encoding="utf-8", newline="").write(
            G.page_html(num, nom, dom, constats, score))
        man[num] = {"url": "https://mahdi-design.com/diag/%s.html" % num, "score": score}
        fait += 1
    json.dump(man, io.open(MANIFEST, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("  ", num, "->", man[num].get("score"), man[num].get("note", "ok"), flush=True)

print("PAGES regenerees:", fait, "| notes:", len(rate))
for r in rate:
    print("   note:", r)
