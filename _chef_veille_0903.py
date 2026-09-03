# -*- coding: utf-8 -*-
"""Chef 0903 veillee : stock chasse, dernieres reponses, conformite derniers envois."""
import json, os, sys, io, datetime, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
os.chdir("C:/Users/ulamb/Bureau/prospection/github-campagne")

# 1) stock entrant : nums les plus eleves = chasse recente
data = json.load(open("campagne_data.json", encoding="utf-8"))
if isinstance(data, dict):
    prospects = [f for f in (data.get("prospects") or data.get("fiches") or [])]
else:
    prospects = data
nums = sorted(int(f["num"]) for f in prospects if str(f.get("num","")).isdigit())
print(f"total fiches: {len(prospects)} | num max: {nums[-1] if nums else '?'}")
recents = [n for n in nums if n > 349]  # phase3 scout = 351+
print(f"fiches post-scout (num>349): {len(recents)}")

# dates d'ajout ? via git log sur campagne_data.json
import subprocess
log = subprocess.run(["git","log","--since=2026-08-30","--oneline","--","campagne_data.json"], capture_output=True, text=True).stdout
print("commits recents campagne_data.json:")
print("\n".join(log.strip().splitlines()[:8]))

# 2) dernieres reponses detectees par repondeur
rp = json.load(open("repondeur_state.json", encoding="utf-8"))
traites = rp.get("traites", [])
print(f"repondeur: {len(traites)} messages traites (etat)")
hist = rp.get("historique") or rp.get("reponses") or []
if isinstance(hist, list) and hist:
    for h in hist[-5:]:
        print("  reponse:", str(h)[:160])
else:
    print("  (pas d'historique detaille dans repondeur_state.json)")

# 3) conformite des 5 derniers envois du jour
state = json.load(open("campagne_state.json", encoding="utf-8"))
sent = state.get("sent", {})
today = datetime.date.today().isoformat()
env_today = [(k, v) for k, v in sent.items() if isinstance(v, dict) and v.get("on") == today]
print(f"envois 'on' today: {len(env_today)}")
dmap = {str(f.get("num")): f for f in prospects}
for k, v in sorted(env_today, key=lambda x: int(x[0]))[-5:]:
    f = dmap.get(k, {})
    corps = (f.get("body") or f.get("corps") or "")
    objet = (f.get("subject") or f.get("objet") or "")
    bad = []
    if "\u2019" in corps or "\u2014" in corps or "\u2014" in objet: bad.append("U+2019/2014")
    if "Portfolio" not in corps: bad.append("PAS-PORTFOLIO")
    if objet.lower().startswith(("prop","demande","offre")): bad.append("OBJET-GENERIC")
    print(f"  num {k}: objet='{objet[:60]}' conformite={'OK' if not bad else bad}")
