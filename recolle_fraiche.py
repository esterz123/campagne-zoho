#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RECOLLE FRAICHE: nouvelles niches jamais chassees -> nouveaux domaines candidats.
Fusionne avec _candidats_domains.json (dedup auto) et sauvegarde."""
import json, os, re, urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
EXA = "69458868-3ce4-42da-873d-43a0465dff11"
CAND = os.path.join(BASE, "_candidats_domains.json")

# Niches FRAICHES (pas dans QUERIES de chasse_hebdo: serrurerie, usinage, etc.)
NEW_QUERIES = (
    "carrosserie industrielle France"
    " | calorifugeage France entreprise"
    " | charpente metallique France"
    " | chaudronnerie inox France"
    " | steamerie chaudronnerie France"
    " | construction metallique France"
    " | decoupe laser metal France"
    " | electromenager professionnel France"
    " | etancheite France entreprise"
    " | forge deprecision France"
    " | garnissage industriel France"
    " | genomie France entreprise"
    " | hydraulique industrielle France"
    " | levage manutention France"
    " | mecanique generale France"
    " | micromecanique France"
    " | montage industriels France"
    " | navigation maritime equipement France"
    " | odbelisterie France"
    " | oxycoupage France"
    " | peinture industrielle France"
    " | plastique injection France"
    " | pneumatique industrielle France"
    " | profilage acier France"
    " | robinetterie industrielle France"
    " | serrurerie fine France"
    " | soudure industrielle France"
    " | tournage fraise France"
    " | traitement thermique metaux France"
    " | vannerie industrielle France"
    " | visserie boulonnerie France"
)

BLACK = ("google", "facebook", "linkedin", "wiki", "youtube", "annuaire", "pagesjaunes",
         "societe", "twitter", "instagram", "wix", "shopify", "mairie", "commune",
         "kompass", "europages", "petitfute", "tripadvisor", "lefigaro", "manageo",
         "compteo", "openbase", "infobel", "pinterest")
TYPES = (".fr", ".com", ".eu", ".net")

def exa_search(q, n=15):
    req = urllib.request.Request(
        "https://api.exa.ai/search",
        data=json.dumps({"query": q, "numResults": n, "type": "auto", "useAutoprompt": True}).encode(),
        headers={"Content-Type": "application/json", "x-api-key": EXA}, method="POST")
    return [r.get("url", "") for r in json.load(urllib.request.urlopen(req, timeout=30)).get("results", [])]

def dom(u):
    return re.sub(r"^https?://(www\.)?", "", u).split("/")[0].lower()

# 1. Charger les existants
cands = json.load(open(CAND, encoding="utf-8")) if os.path.exists(CAND) else {}
avant = len(cands)

# 2. Recolle fraiche
for q in [x.strip() for x in NEW_QUERIES.split("|") if x.strip()]:
    try:
        for u in exa_search(q):
            d = dom(u)
            if d and not any(b in d for b in BLACK) and d.endswith(TYPES):
                cands[d] = "https://" + d
        print("OK ", q, "-> total", len(cands))
    except Exception as e:
        print("ERR", q[:30], str(e)[:60])

# 3. Sauver (fusion dedup)
json.dump(cands, open(CAND, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("TOTAL:", len(cands), "| NOUVEAUX:", len(cands) - avant)
