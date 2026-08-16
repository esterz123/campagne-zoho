# -*- coding: utf-8 -*-
"""
CHARGEUR CABINETS COMPTABLES : reserve de cabinets d'expertise comptable FR (partenaires).
API officielle de l'Etat. Les cabinets voient les sites de tous leurs clients industriels
et ont leur confiance -> partenaires de reve (commission 15%, diagnostic gratuit pour leur client).
"""
import json, os, sys, time, urllib.request, urllib.parse

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "candidats_cabinets.json")

MOTS_CLES = ["expertise comptable", "cabinet comptable", "expert comptable", "comptabilite"]
TRANCHES = ["01", "02", "03", "11"]   # 1-19 salaries (cabinets avec clients PME)
SECTION = "M"                          # activites specialisees (comptabilite = 69.20Z)
PER_PAGE = 25
MAX_PAGES = 4

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
    if os.path.exists(OUT):
        existants = {str(e.get("siren", "")) for e in json.load(open(OUT, encoding="utf-8"))}
    nouveaux, total_vus = [], 0
    for q in MOTS_CLES:
        for tranche in TRANCHES:
            for page in range(1, MAX_PAGES + 1):
                try:
                    j = api(q, tranche, page)
                except Exception as e:
                    print("  [ERREUR] %s/%s p%d : %s" % (q, tranche, page, str(e)[:60]))
                    time.sleep(2)
                    break
                res = j.get("results", [])
                total_vus += len(res)
                if not res:
                    break
                for r in res:
                    siren = str(r.get("siren", ""))
                    if not siren or siren in existants:
                        continue
                    nom = (r.get("nom_complet") or "").strip()
                    if not nom:
                        continue
                    naf = r.get("activite_principale", "")
                    # garder les vrais cabinets (NAF comptabilite 69.20Z ou nom qui contient comptable)
                    if naf != "69.20Z" and "comptab" not in nom.lower():
                        continue
                    sieg = r.get("siege", {}) or {}
                    existants.add(siren)
                    nouveaux.append({
                        "nom": nom,
                        "ville": sieg.get("libelle_commune", ""),
                        "naf": naf,
                        "siren": siren,
                        "tranche": tranche,
                        "source": "api-officielle-cabinets",
                    })
                time.sleep(0.4)

    anciens = json.load(open(OUT, encoding="utf-8")) if os.path.exists(OUT) else []
    total = anciens + nouveaux
    json.dump(total, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("CHARGEUR CABINETS : %d vus, %d NOUVEAUX, reserve = %d" % (total_vus, len(nouveaux), len(total)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
