# -*- coding: utf-8 -*-
"""Chef 03/09 : verite file (join data<->state), relances dues, chauds."""
import json
from datetime import datetime, date

REPO = "C:/Users/ulamb/Bureau/prospection/github-campagne"
state = json.load(open(REPO + "/campagne_state.json", encoding="utf-8"))
data = json.load(open(REPO + "/campagne_data.json", encoding="utf-8"))
sent = state.get("sent", {})

prospects = [p for p in data if p.get("type", "prospect") == "prospect"] if isinstance(data, list) else list(data.values())
nums_all = {str(p.get("num")): p for p in prospects if p.get("num") is not None}
envoyes = [n for n in nums_all if n in sent]
restants = [n for n in nums_all if n not in sent]
replied = [n for n in envoyes if sent[n].get("replied")]
bounce = [n for n in envoyes if sent[n].get("bounce")]

print(f"Fiches: {len(nums_all)} | Envoyes: {len(envoyes)} | Restants: {len(restants)} | Replied: {len(replied)} -> {replied} | Bounce: {len(bounce)}")

today = date.today()
def parse(d):
    try:
        return datetime.strptime(str(d)[:10], "%Y-%m-%d").date()
    except Exception:
        return None

dates_envoi = sorted([parse(sent[n].get("on", "")) for n in envoyes if parse(sent[n].get("on", ""))])
print(f"Dernier 1er envoi: {dates_envoi[-1] if dates_envoi else 'aucun'}")
print(f"Envois 7 derniers jours: {sum(1 for d in dates_envoi if d and (today - d).days <= 7)}")
print(f"Envois aujourd'hui: {sum(1 for d in dates_envoi if d == today)}")

# Relances dues (avec exclusions : replied, bounce, relances deja envoyees)
def fu_flag(s):
    for k in ("sent_relance1", "sent_relance2", "sent_relance3"):
        if s.get(k):
            return True
    return False

fu1, fu2, fu3 = [], [], []
for n in envoyes:
    s = sent[n]
    if s.get("replied") or s.get("bounce") or fu_flag(s):
        continue
    d = parse(s.get("on", ""))
    if not d:
        continue
    delta = (today - d).days
    if delta >= 14:
        fu3.append((n, delta))
    elif delta >= 7:
        fu2.append((n, delta))
    elif delta >= 3:
        fu1.append((n, delta))

print(f"Relances dues (hors exclusions): J+3-J+7: {len(fu1)} | J+7-J+14: {len(fu2)} | J+14+: {len(fu3)}")

# Conges
try:
    conges = json.load(open(REPO + "/relances_conges.json", encoding="utf-8"))
    tos = set()
    if isinstance(conges, list):
        for c in conges:
            tos.add(c.get("to", ""))
    elif isinstance(conges, dict):
        tos = set(conges.keys())
    print(f"Conges: {len(tos)} entrees")
except Exception as ex:
    print(f"Conges: n/a ({ex})")

# Chauds = replied actifs
print("\nCHAUDS (replied):")
for n in replied:
    s = sent[n]
    f = nums_all.get(n, {})
    nom = f.get("prospect") or f.get("entreprise") or f.get("to", "")
    print(f"  #{n} {nom} | replied le {s.get('replied') if isinstance(s.get('replied'), str) else '?'} | rel1={bool(s.get('sent_relance1'))} diag={bool(s.get('diag_envoye'))}")

# Relances manuelles envoyees (Gaultier etc.)
print("\nRelance1 manuelle/tracee:", [n for n in envoyes if sent[n].get("sent_relance1")][:20])
