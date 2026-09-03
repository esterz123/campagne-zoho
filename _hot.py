import json
# leads chauds du briefing: MPI Mecanique (Olivier, retour NOW), PMC Expertise (partenariat), Gaultier
# Verifier leur presence dans les files + relances_conges
try:
    rc = json.load(open('relances_conges.json', encoding='utf-8'))
    print("relances_conges:", json.dumps(rc, ensure_ascii=False)[:600])
except Exception as e:
    print("relances_conges:", e)
sr = json.load(open('suivi_revenus.json', encoding='utf-8'))
print("\nsuivi_revenus:", json.dumps(sr, ensure_ascii=False)[:400])
# MPI / PMC dans campagne_data?
cd = json.load(open('campagne_data.json', encoding='utf-8'))
for p in cd:
    t = str(p.get('prospect',''))
    if 'MPI' in t or 'PMC' in t:
        print("\nTROUVE:", p['num'], t, '| to:', p.get('to'), '| body:', str(p.get('body'))[:100])
