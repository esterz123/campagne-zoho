# -*- coding: utf-8 -*-
"""
EXPANSION VOLUME - la regle 100 de Hormozi appliquee a notre machine.
Objectif : passer de 24/jour a 100/jour sans griller les boites.
Strategie : (1) dressage progressif des 5 boites existantes (+2/jour/boite
toutes les 3 jours), (2) demandes de nouveaux sous-domaines Gmail gratuits
reexpedis via Zoho (Mahdi doit creer), (3) warm-up a nos horaires.
Le script calcule le plan de montee et prepare les demandes d'actions humaines.
"""
import json
import datetime
import os

BASE = os.path.dirname(os.path.abspath(__file__))
PLAN = os.path.join(BASE, "plan_volume.json")


def main():
    st = json.load(open(os.path.join(BASE, "campagne_state.json"), encoding="utf-8"))
    s = st.get("sent", {})
    d = json.load(open(os.path.join(BASE, "campagne_data.json"), encoding="utf-8"))
    vierges = sum(1 for r in d if str(r.get("num")) not in s)
    sent_n = len(s)

    # etat actuel : 5 boites actives
    # plafonds : contact 8/j + 4x4/j = 24/j aujourd hui
    # objectif Hormozi : 100/jour
    # strategie : +2/jour/boite toutes les 3 jours (warm-up standard 2x/semaine)
    plan = {
        "date": datetime.date.today().isoformat(),
        "envoyes_total": sent_n,
        "vierges_restants": vierges,
        "boites_actives": 5,
        "volume_actuel_par_jour": 24,
        "objectif_hormozi": 100,
        "escalade": [
            {"jour": 0, "volume": 24, "note": "actuel"},
            {"jour": 3, "volume": 34, "note": "+2/boite"},
            {"jour": 6, "volume": 44, "note": "+2/boite"},
            {"jour": 9, "volume": 54, "note": "+2/boite"},
            {"jour": 12, "volume": 64, "note": "+2/boite"},
            {"jour": 15, "volume": 74, "note": "+2/boite"},
            {"jour": 18, "volume": 84, "note": "+2/boite"},
            {"jour": 21, "volume": 94, "note": "+2/boite"},
            {"jour": 24, "volume": 100, "note": "objectif atteint"},
        ],
        "conditions_pour_monte": [
            "bounce rate < 2% sur les 3 derniers jours (verifier bounce_shield)",
            "spam complaints = 0",
            "replies >= 2% (sinon le volume amplifie un message qui ne marche pas)",
        ],
        "si_replies_toujours_bas": "NE PAS MONTER LE VOLUME - ameliorer le message d'abord (verdict ab_stats 02/09)",
    }
    json.dump(plan, open(PLAN, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("PLAN VOLUME:")
    print("  actuel: 24/jour | objectif Hormozi: 100/jour | escalade sur 24 jours")
    print("  vierges restants:", vierges, "(autonomie ~6 jours a 24/j)")
    print("  condition essentielle:", plan["conditions_pour_monte"][2])
    print("  -> verdict ab_stats demain AVANT de monter le volume")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
