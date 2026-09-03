# -*- coding: utf-8 -*-
"""Chef 03/09 : audit bounce + couverture preuve des restants + SMTP verify."""
import json, re, os

REPO = "C:/Users/ulamb/Bureau/prospection/github-campagne"
state = json.load(open(REPO + "/campagne_state.json", encoding="utf-8"))
data = json.load(open(REPO + "/campagne_data.json", encoding="utf-8"))
sent = state.get("sent", {})

prospects = [p for p in data if p.get("type", "prospect") == "prospect"] if isinstance(data, list) else list(data.values())
by_num = {str(p.get("num")): p for p in prospects if p.get("num") is not None}

# 1) Echantillon bounces
bounces = [n for n in by_num if n in sent and sent[n].get("bounce")]
print(f"=== BOUNCES: {len(bounces)} ===")
notes_bounce = [str(sent[n].get("note", "")) for n in bounces[:8]]
for n in bounces[:8]:
    f = by_num.get(n, {})
    print(f"  #{n} to={f.get('to','?')[:45]} note={sent[n].get('note','')[:60]}")

# dates des bounces
from datetime import datetime, date
def parse(d):
    try: return datetime.strptime(str(d)[:10], "%Y-%m-%d").date()
    except: return None
bounce_par_jour = {}
for n in bounces:
    d = parse(sent[n].get("bounce_on", sent[n].get("on", "")))
    if d: bounce_par_jour[str(d)] = bounce_par_jour.get(str(d), 0) + 1
print("Bounces par jour:", dict(sorted(bounce_par_jour.items())[-8:]))

# 2) Blacklist
bl = set()
try:
    blj = json.load(open(REPO + "/domaines_bloques.json", encoding="utf-8"))
    bl = set(blj if isinstance(blj, list) else blj.get("domaines", blj.keys()))
except Exception as ex:
    print("domaines_bloques.json:", ex)
print(f"Blacklist domaines: {len(bl)} entrees")

# domains des fiches bounce sont-ils blacklistes ?
def dom(mail): return mail.split("@")[-1].lower().strip() if "@" in str(mail) else ""
pas_bl = [n for n in bounces if dom(by_num.get(n, {}).get("to", "")) not in bl]
print(f"Bounces dont le domaine n'est PAS blacklisté: {len(pas_bl)}")
if pas_bl[:10]:
    print("  ex:", [(n, dom(by_num.get(n, {}).get('to',''))) for n in pas_bl[:10]])

# 3) Emails restants : SMTP-verifiables ? (la chasse verifiait ; les vieux lots pas forcement)
restants = [n for n in by_num if n not in sent]
print(f"\n=== RESTANTS: {len(restants)} ===")
print("Fiches avec fichier SMTP/state:", os.path.exists(REPO + "/smtp_cache.json") or os.path.exists(REPO + "/_smtp_cache.json"))

# 4) Couverture preuve des restants
constats = {}
try:
    cj = json.load(open(REPO + "/constats_sites.json", encoding="utf-8"))
    constats = cj.get("sites", cj) if isinstance(cj, dict) else {}
except Exception as ex:
    print("constats:", ex)
print(f"Constats sites: {len(constats)} entrees")

avec_constat = sum(1 for n in restants if str(n) in constats or by_num.get(n, {}).get("site", "").lower() in {k.lower() for k in constats})
print(f"Restants AVEC constat mesure: {avec_constat}/{len(restants)}")

# U+2019 et tirets longs dans les restants (charset Mahdi)
bad_ch = 0
for n in restants:
    f = by_num.get(n, {})
    body = str(f.get("body", "")) + str(f.get("subject", ""))
    if "\u2019" in body or "\u2014" in body or "\u2013" in body:
        bad_ch += 1
print(f"Restants avec U+2019/tirets longs: {bad_ch}")

# portfolio en fin
sans_port = sum(1 for n in restants if "Portfolio" not in str(by_num.get(n, {}).get("body", "")))
print(f"Restants SANS portfolio dans body: {sans_port}")

# rapports docx couverts
import glob
rapports = set()
for p in glob.glob(REPO + "/livrable/rapports/rapport_*.docx"):
    m = re.search(r"rapport_(\d+)_", os.path.basename(p))
    if m: rapports.add(m.group(1))
couv_rapports = sum(1 for n in restants if n in rapports)
print(f"Restants avec rapport docx: {couv_rapports}/{len(restants)}")
