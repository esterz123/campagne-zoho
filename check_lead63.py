# Detail lead 63 (Gaultier) : champ replied, contenu de la reponse, historique
import json, os

BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)
cs = json.load(open("campagne_state.json", encoding="utf-8"))
sent = cs.get("sent", {})

v = sent.get("63")
if v:
    print("=== LEAD 63 COMPLET ===")
    print(json.dumps(v, indent=1, ensure_ascii=False)[:3000])
else:
    print("lead 63 absent de sent")

# cherche tout lead contenant gaultier / free.fr
print()
print("=== RECHERCHE GAULTIER / free.fr ===")
for k, vv in sent.items():
    blob = json.dumps(vv, ensure_ascii=False).lower()
    if "gaultier" in blob or "free.fr" in blob:
        print("key:", k)
        print(json.dumps(vv, indent=1, ensure_ascii=False)[:2000])
        print("---")

# toutes les cles avec reponses / statuts
print()
print("=== TOP-LEVEL KEYS campagne_state ===")
print(list(cs.keys()))
