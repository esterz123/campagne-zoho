# -*- coding: utf-8 -*-
"""Audit 4 : les 13 objets sans domaine email citent-ils le domaine SITE ?"""
import json, os, re

os.chdir(r"C:/Users/ulamb/Bureau/prospection/github-campagne")

def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

data = load("campagne_data.json")
state = load("campagne_state.json")
cst = load("constats_sites.json")
sent = state.get("sent", {})

ko_nums = ["252", "264", "284", "286", "293", "321", "326", "366"]
# retrouver les autres KO (5 suivants) : recalcule la liste complete
restants = [f for f in data if str(f.get("num")) not in sent]
kos = []
for f in restants:
    subj = (f.get("subject") or "").lower()
    to = f.get("to", "")
    dom = to.split("@")[-1].lower() if "@" in to else ""
    if not (dom and dom in subj):
        kos.append(str(f.get("num")))

for num in kos:
    f = next((x for x in data if str(x.get("num")) == num), None)
    c = cst.get(num, {})
    site = (c.get("site") or c.get("url") or c.get("domaine") or "").lower()
    subj = f.get("subject") or ""
    site_in_subj = site and site.split("//")[-1].split("/")[0] in subj.lower()
    print(f"#{num} site={site!r} site_dans_objet={bool(site_in_subj)}")
    print(f"   objet: {subj[:80]}")
    print(f"   to: {f.get('to')}")
    # constat 1re ligne
    body = f.get("body") or ""
    m = re.search(r"Bonjour[^\n]*\n+(.{0,160})", body)
    print(f"   1re ligne: {(m.group(1) if m else body[:120])[:130]!r}")
