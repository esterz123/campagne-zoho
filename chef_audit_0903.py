# -*- coding: utf-8 -*-
"""Audit verite terrain du tableau — chef_audit_0903.py (read-only)."""
import json, os, datetime

REPO = r"C:\Users\ulamb\Bureau\prospection\github-campagne"
os.chdir(REPO)
today = datetime.date.today()
print("DATE:", today.isoformat())
print("PAUSE_ENVOIS:", os.path.exists("PAUSE_ENVOIS"))

# ---- File : join data <-> state ----
data = json.load(open("campagne_data.json", encoding="utf-8"))
state = json.load(open("campagne_state.json", encoding="utf-8"))
fiches = data if isinstance(data, list) else data.get("prospects", data)
sent = state.get("sent", {})
print("Total fiches:", len(fiches), "| envoyees:", len(sent))

replied = [n for n, s in sent.items() if s.get("replied")]
print("Replied:", len(replied), "->", replied[:30])

restants = [str(f.get("num", i)) for i, f in enumerate(fiches) if str(f.get("num", i)) not in sent]
print("Restants reel (join):", len(restants))

# ---- Cash reel (filtre TEST) ----
print("\n=== CASH ===")
try:
    rev = json.load(open("suivi_revenus.json", encoding="utf-8"))
    entrees = rev if isinstance(rev, list) else rev.get("paiements", rev.get("entrees", []))
    tot = 0.0
    for e in entrees:
        note = (str(e.get("note", "")) + str(e.get("payeur", ""))).upper()
        if "TEST" in note or "MAHDI-DESIGN" in note:
            continue
        amt = e.get("montant") or e.get("amount") or 0
        tot += float(amt)
        print("REEL:", e.get("date", "?"), amt, "EUR -", str(e.get("note", ""))[:60])
    print("TOTAL CASH REEL:", tot, "EUR")
except FileNotFoundError:
    print("pas de suivi_revenus.json")

# ---- Followups dus ----
print("\n=== FOLLOWUPS ===")
try:
    fu = json.load(open("followups.json", encoding="utf-8"))
    items = fu if isinstance(fu, list) else fu.get("items", [])
    due = [x for x in items if str(x.get("due", "9999")) <= today.isoformat()]
    print("Total:", len(items), "| dus ou passes:", len(due))
    for x in due[:15]:
        print("  DUE:", x.get("due"), str(x.get("num", x.get("prospect", "?"))), str(x.get("quoi", ""))[:80])
except FileNotFoundError:
    print("pas de followups.json")

# ---- Relances auto J+3/J+7 dans l'etat ----
print("\n=== RELANCES DANS STATE ===")
r1 = sum(1 for s in sent.values() if s.get("sent_relance1"))
r2 = sum(1 for s in sent.values() if s.get("sent_relance2"))
print("sent_relance1:", r1, "| sent_relance2:", r2)

# ---- Leads replies : detail + suivi audit ----
print("\n=== LEADS REPLIES (detail) ===")
for n in replied:
    s = sent[n]
    print("  #%s replied=%s audit_suivi=%s" % (n, s.get("replied"), str(s.get("audit_suivi", ""))[:80]))

# ---- Fiches vierges sans preuve (constats_sites.json) ----
try:
    cs = json.load(open("constats_sites.json", encoding="utf-8"))
    print("\nconstats_sites.json:", len(cs), "entrees")
    sans_preuve = [n for n in restants if str(n) not in cs]
    print("Restants SANS constat:", len(sans_preuve))
except FileNotFoundError:
    print("pas de constats_sites.json")

# ---- Stats A/B ----
try:
    with open("verdict_ab_0902.md", encoding="utf-8") as f:
        head = f.read()[:400]
    print("\n=== VERDICT A/B ===")
    print(head)
except FileNotFoundError:
    pass
