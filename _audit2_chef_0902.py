# -*- coding: utf-8 -*-
"""Audit 2 : qualite file restante, objets v2, leads chauds, journaux."""
import json, os, re, io

os.chdir(r"C:/Users/ulamb/Bureau/prospection/github-campagne")

def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

data = load("campagne_data.json")
state = load("campagne_state.json")
cst = load("constats_sites.json")
sent = state.get("sent", {})

restants = [f for f in data if str(f.get("num")) not in sent]
p = print

# 1) objets v2 (domaine dans l'objet) sur les restants
ok_obj, ko_obj = 0, []
for f in restants:
    num = str(f.get("num"))
    subj = f.get("subject", "")
    to = f.get("to", "")
    dom = to.split("@")[-1].lower() if "@" in to else ""
    if dom and dom in subj.lower():
        ok_obj += 1
    else:
        ko_obj.append((num, subj[:60]))
p("restants:", len(restants), "| objet avec domaine:", ok_obj, "| sans domaine:", len(ko_obj))
for x in ko_obj[:8]:
    p("  KO:", x)

# 2) notes restantes: distribution
notes = {}
for f in restants:
    num = str(f.get("num"))
    c = cst.get(num) or {}
    notes[num] = c.get("note")
vals = [v for v in notes.values() if isinstance(v, (int, float))]
buckets = {"0-40": 0, "41-60": 0, "61-79": 0, "80-100": 0, "None/BLOQUE": 0}
for v in vals:
    if v <= 40: buckets["0-40"] += 1
    elif v <= 60: buckets["41-60"] += 1
    elif v <= 79: buckets["61-79"] += 1
    else: buckets["80-100"] += 1
buckets["None/BLOQUE"] = len(restants) - len(vals)
p("notes restants:", buckets)

# 3) corps: doublons d'ouverture / U+2019 / tirets longs sur restants
bad_u, bad_dash, dup_open, short_body = 0, 0, 0, 0
for f in restants:
    body = f.get("body", "") or ""
    subj = f.get("subject", "") or ""
    if "\u2019" in body or "\u2019" in subj: bad_u += 1
    if "\u2014" in body or "\u2014" in subj or "\u2013" in body or "\u2013" in subj: bad_dash += 1
    if len(body) < 150: short_body += 1
    # doublon meme domaine dans 600 premiers chars
    to = f.get("to", "")
    dom = to.split("@")[-1].lower() if "@" in to else ""
    head = body[:600].lower()
    if dom and dom in subj.lower() and head.count(dom.lower()) >= 2:
        dup_open += 1
p(f"U+2019: {bad_u} | tirets longs: {bad_dash} | body<150: {short_body} | doublon ouverture: {dup_open}")

# 4) leads chauds
p("== LEADS CHAUDS ==")
for num in ["63"]:
    f = next((x for x in data if str(x.get("num")) == num), None)
    v = sent.get(num, {})
    p(f"#{num} replied={v.get('replied')} on={v.get('on')} audit_suivi={v.get('audit_suivi','ABSENT')}")
    if f: p("  to:", f.get("to"), "| subj:", (f.get("subject") or "")[:70])
try:
    rel = load("livrable/relance_closing_SIMI.txt")
    p("relance_SIMI.txt:", len(rel), "chars | tiret:", ("\u2014" in rel or "\u2013" in rel), "| U2019:", ("\u2019" in rel), "| fin Portfolio:", rel.strip().endswith("mahdi-design.com") or "Portfolio" in rel[-100:])
except Exception as e:
    p("relance_SIMI err:", e)
try:
    ms = load("messages_livraison.json")
    gault = [m for m in (ms if isinstance(ms, list) else ms.values()) if isinstance(m, dict) and "gaultier" in json.dumps(m, ensure_ascii=False).lower()]
    p("messages gaultier:", len(gault))
except Exception as e:
    p("messages_livraison err:", e)

# 5) suivi gaultier dans etat
for k, v in sent.items():
    if isinstance(v, dict) and "gaultier" in json.dumps(v, ensure_ascii=False).lower():
        p("sent entry gaultier:", k, json.dumps(v, ensure_ascii=False)[:200])

# 6) dernier journal boucle + squad briefing
for jf in ["amelioration_journal.json"]:
    try:
        j = load(jf)
        if isinstance(j, list):
            last = j[-1]
        else:
            last = j
        p(f"== {jf} (dernier) ==", json.dumps(last, ensure_ascii=False)[:500])
    except Exception as e:
        p(jf, "err:", e)

# 7) repondeur/closer etats: dernier traitement
for sf in ["repondeur_state.json", "closer_state.json"]:
    try:
        s = load(sf)
        tr = s.get("traites", [])
        p(f"== {sf}: traites={len(tr)}", "dernier:", tr[-3:] if isinstance(tr, list) else "?")
    except Exception as e:
        p(sf, "err:", e)
