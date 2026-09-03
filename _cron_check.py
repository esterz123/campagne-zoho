import json, io, os, re
from datetime import datetime, timezone, timedelta

os.chdir(r"C:\Users\ulamb\Bureau\prospection\github-campagne")
now = datetime.now(timezone(timedelta(hours=1)))
print("HEURE:", now.strftime("%d/%m %H:%M"))

def load(f):
    try:
        return json.load(io.open(f, encoding="utf-8"))
    except Exception as e:
        return {"__err__": str(e)}

# 1. Etat campagne
s = load("campagne_state.json")
print("\n===== campagne_state.json =====")
for k, v in s.items():
    if isinstance(v, dict):
        print(k, "->", json.dumps(v, ensure_ascii=False)[:600])
    elif isinstance(v, list):
        print(k, "-> list", len(v))
    else:
        print(k, "=", v)

# 2. File d'envoi réelle
data = load("campagne_data.json")
fiches = data if isinstance(data, list) else data.get("fiches") or data.get("prospects") or []
if isinstance(fiches, dict):
    fiches = list(fiches.values())
sent = [f for f in fiches if f.get("sent_at") or f.get("envoye") or f.get("status") in ("sent", "envoye")]
pending = [f for f in fiches if not (f.get("sent_at") or f.get("envoye") or f.get("status") in ("sent", "envoye"))]
print("\n===== FILE =====")
print("total fiches:", len(fiches), "| envoyees:", len(sent), "| en file:", len(pending))
with_conf = [f for f in pending if f.get("to_confirmed")]
print("en file avec to_confirmed:", len(with_conf))
no_mail = [f for f in pending if not f.get("to")]
print("en file SANS email:", len(no_mail))
for f in pending[:5]:
    print(" ex:", f.get("num"), f.get("prospect"), "| to:", f.get("to"), "| conf:", f.get("to_confirmed"), "| status:", f.get("status"))

# 3. Revenus
rev = load("suivi_revenus.json")
print("\n===== revenus =====")
print(json.dumps(rev, ensure_ascii=False)[:800])

# 4. Reponses / repondeur
rep = load("repondeur_state.json")
print("\n===== repondeur (extrait) =====")
print(json.dumps(rep, ensure_ascii=False)[:1200])

# 5. Closer
cl = load("closer_state.json")
print("\n===== closer (extrait) =====")
print(json.dumps(cl, ensure_ascii=False)[:800])

# 6. Chasse du jour : candidats avec email trouve aujourd'hui
try:
    np = load("nouveau_prospects.json")
    nl = np if isinstance(np, list) else np.get("prospects", [])
    print("\n===== nouveau_prospects =====")
    print("count:", len(nl))
    withmail = [x for x in nl if x.get("to") or x.get("email")]
    print("avec email:", len(withmail))
    for x in nl[:3]:
        print(" ex:", json.dumps(x, ensure_ascii=False)[:200])
except Exception as e:
    print("nouveau_prospects ERR", e)

# 7. Derniere activite des bots (mtime des fichiers)
print("\n===== fichiers les plus recents =====")
files = [(os.path.getmtime(f), f) for f in os.listdir(".") if f.endswith((".json", ".py", ".md"))]
files.sort(reverse=True)
for mt, f in files[:12]:
    print(datetime.fromtimestamp(mt).strftime("%d/%m %H:%M"), f)
