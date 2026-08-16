# -*- coding: utf-8 -*-
"""
CHARGEUR OFFICIEL : remplit candidats_bruts.json depuis l'API officielle de l'Etat
(https://recherche-entreprises.api.gouv.fr, gratuite, sans cle, illimitee).
Cible : PME industrielles FR 10-49 salaries (tranches INSEE 11 et 12),
section C (industrie manufacturiere), par mot-cle secteur dans le nom.

La chasseuse_h24.py consomme ensuite cette reserve : la file ne s'epuise JAMAIS.
Idempotent : dedup par SIREN, ne touche pas aux entrees existantes.
"""
import json, os, sys, time, urllib.request, urllib.parse

BASE = os.path.dirname(os.path.abspath(__file__))
BRUTS = os.path.join(BASE, "candidats_bruts.json")

MOTS_CLES = ["usinage", "decolletage", "plasturgie", "injection", "fonderie",
             "tolerie", "outillage", "moule", "decoupe", "chaudronnerie"]
TRANCHES = ["11", "12"]           # INSEE : 11 = 10-19 sal, 12 = 20-49 sal
SECTION = "C"                     # Industrie manufacturiere
PER_PAGE = 25
MAX_PAGES = 8                     # 200 max par (mot-cle, tranche)

UA = {"User-Agent": "hermes-prospecting/1.0 (contact@mahdi-design.com)"}


def api(q, tranche, page):
    url = "https://recherche-entreprises.api.gouv.fr/search?" + urllib.parse.urlencode({
        "q": q, "section_activite_principale": SECTION,
        "tranche_effectif_salarie": tranche, "per_page": PER_PAGE, "page": page})
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def main():
    existants = set()
    if os.path.exists(BRUTS):
        existants = {str(e.get("siren", "")) for e in json.load(open(BRUTS, encoding="utf-8"))}
    nouveaux, total_vus = [], 0
    for q in MOTS_CLES:
        for tranche in TRANCHES:
            for page in range(1, MAX_PAGES + 1):
                try:
                    j = api(q, tranche, page)
                except Exception as e:
                    print("  [ERREUR] %s/%s page %d : %s" % (q, tranche, page, str(e)[:80]))
                    time.sleep(3)
                    break
                res = j.get("results", [])
                total_vus += len(res)
                if not res:
                    break
                for r in res:
                    siren = str(r.get("siren", ""))
                    if not siren or siren in existants:
                        continue
                    naf = r.get("activite_principale", "")
                    nom = (r.get("nom_complet") or r.get("nom_raison_sociale") or "").strip()
                    # filtre : garder les vrais industriels (nom qui ressemble a une societe)
                    if not nom or "association" in nom.lower() or "syndicat" in nom.lower():
                        continue
                    sieg = r.get("siege", {}) or {}
                    existants.add(siren)
                    nouveaux.append({
                        "nom": nom,
                        "ville": sieg.get("libelle_commune", ""),
                        "naf": naf,
                        "siren": siren,
                        "tranche": tranche,
                        "source": "api-officielle",
                    })
                time.sleep(0.4)  # politesse API

    anciens = json.load(open(BRUTS, encoding="utf-8")) if os.path.exists(BRUTS) else []
    total = anciens + nouveaux
    json.dump(total, open(BRUTS, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("CHARGEUR OFFICIEL : %d vus, %d NOUVEAUX ajoutes, reserve = %d"
          % (total_vus, len(nouveaux), len(total)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
