# -*- coding: utf-8 -*-
"""
SCOUT CHASSE - PHASE 1 : selection des 100 meilleurs candidats.
Pour chaque SIREN de candidats_bruts.json -> appel API recherche-entreprises.
Filtres : etat_administratif=A, section C (industrie), tranche effectif 11 ou 12
(10-19 / 20-49 salaries), pas association, pas organisme de formation, pas ESS.
Sortie : _scout_selected.json (progressif, resumable).
"""
import json, os, sys, time
import requests

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(BASE, "candidats_bruts.json")
OUT = os.path.join(BASE, "_scout_selected.json")
LOG = os.path.join(BASE, "_scout_phase1.log")

API = "https://recherche-entreprises.api.gouv.fr/search"
TRANCHES_OK = ("11", "12")  # 10-19, 20-49

def log(msg):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(msg + "\n")
    print(msg, flush=True)

def main():
    cands = json.load(open(SRC, encoding="utf-8"))
    log("=== PHASE 1 start: %d candidats bruts ===" % len(cands))

    # resume
    done_sirens = set()
    selected = []
    if os.path.exists(OUT):
        try:
            prev = json.load(open(OUT, encoding="utf-8"))
            selected = prev.get("selected", [])
            done_sirens = set(prev.get("done", []))
            log("reprise: %d deja interroges, %d retenus" % (len(done_sirens), len(selected)))
        except Exception as e:
            log("etat illisible (%s), on repart de zero" % e)

    def save():
        tmp = OUT + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump({"done": sorted(done_sirens), "selected": selected},
                      f, ensure_ascii=False, indent=1)
        os.replace(tmp, OUT)

    kept = 0
    for i, c in enumerate(cands):
        siren = str(c.get("siren", ""))
        if not siren or siren in done_sirens:
            continue
        done_sirens.add(siren)
        rec = None
        try:
            r = requests.get(API, params={"q": siren, "per_page": 1}, timeout=15)
            res = r.json().get("results", [])
            if res and str(res[0].get("siren")) == siren:
                rec = res[0]
            elif res:
                # recherche nominale fallback par siren pas exact -> renomme
                rec = None
        except Exception as e:
            log("API FAIL siren=%s (%s) -> retry once" % (siren, type(e).__name__))
            time.sleep(2)
            try:
                r = requests.get(API, params={"q": siren, "per_page": 1}, timeout=15)
                res = r.json().get("results", [])
                if res and str(res[0].get("siren")) == siren:
                    rec = res[0]
            except Exception:
                pass
        time.sleep(0.4)

        if rec is None:
            log("SKIP %s %s : introuvable/radie API" % (siren, c.get("nom", "")[:40]))
            if (i + 1) % 25 == 0:
                save()
            continue

        comp = rec.get("complements", {}) or {}
        ok = (rec.get("etat_administratif") == "A"
              and rec.get("section_activite_principale") == "C"
              and str(rec.get("tranche_effectif_salarie") or "") in TRANCHES_OK
              and not comp.get("est_association")
              and not comp.get("est_organisme_formation")
              and not comp.get("est_ess")
              and not comp.get("est_service_public"))
        if ok:
            siege = rec.get("siege", {}) or {}
            kept += 1
            selected.append({
                "nom": rec.get("nom_complet") or c.get("nom"),
                "siren": siren,
                "ville": siege.get("libelle_commune") or c.get("ville"),
                "naf": rec.get("activite_principale") or c.get("naf"),
                "tranche": rec.get("tranche_effectif_salarie"),
                "url_api": "https://annuaire-entreprises.data.gouv.fr/entreprise/%s" % siren,
            })
            log("KEEP %3d %s %s (%s, tranche %s)" % (
                kept, siren, (rec.get("nom_complet") or "")[:45],
                (siege.get("libelle_commune") or "")[:20], rec.get("tranche_effectif_salarie")))
        if (i + 1) % 25 == 0:
            save()
            log("--- progress: %d interroges, %d retenus ---" % (len(done_sirens), len(selected)))

    save()
    log("=== PHASE 1 done: %d interroges, %d retenus ===" % (len(done_sirens), len(selected)))

if __name__ == "__main__":
    main()
