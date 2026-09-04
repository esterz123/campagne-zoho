# -*- coding: utf-8 -*-
"""QA file restante avec les bons champs (body/subject/to) — chef_qa2_0903.py."""
import json, re, os

os.chdir(r"C:\Users\ulamb\Bureau\prospection\github-campagne")
data = json.load(open("campagne_data.json", encoding="utf-8"))
state = json.load(open("campagne_state.json", encoding="utf-8"))
sent = state["sent"]
restants = [f for i, f in enumerate(data) if str(f.get("num", i)) not in sent]
print("Restants:", len(restants))

bad2019, badtiret, badport, doubledom, vide, sansnom, quandmeme = [], [], [], [], [], [], []
for f in restants:
    num = str(f.get("num"))
    to = str(f.get("to", ""))
    sujet = str(f.get("subject", ""))
    corps = str(f.get("body", ""))
    m = re.search(r"@([a-z0-9.-]+)", to)
    dom = m.group(1).lower() if m else ""
    blob = sujet + " " + corps
    if chr(0x2019) in blob:
        bad2019.append(num)
    if chr(0x2014) in blob or chr(0x2013) in blob:
        badtiret.append(num)
    if "Portfolio" not in corps:
        badport.append(num)
    tete = corps[:500].lower()
    if dom and tete.count(dom) >= 2:
        doubledom.append(num)
    if len(corps.strip()) < 80:
        vide.append(num)
    if "2900" in corps or "2900" in sujet:
        quandmeme.append(num)
    if re.match(r"^Bonjour M", corps) and not f.get("dirigeant"):
        sansnom.append(num)

print("U+2019:", len(bad2019), bad2019[:8])
print("tirets longs:", len(badtiret), badtiret[:8])
print("sans 'Portfolio' en fin:", len(badport), badport[:8])
print("ouverture double domaine:", len(doubledom), doubledom[:8])
print("corps quasi vide:", len(vide), vide[:8])
print("citent 2900 (prix expire):", len(quandmeme), quandmeme[:8])
print("'Bonjour M.' sans champ dirigeant:", len(sansnom), sansnom[:8])

# 5 prochains envois prevus (tri note croissante, la file des plus casses d'abord)
print("\n=== 5 PROCHAINS ENVOIS (note croissante) ===")
cs = json.load(open("constats_sites.json", encoding="utf-8"))
triables = []
for f in restants:
    num = str(f.get("num"))
    c = cs.get(num, {})
    note = c.get("note")
    triables.append((note if isinstance(note, (int, float)) else 999, num, f))
triables.sort(key=lambda x: x[0])
for note, num, f in triables[:5]:
    sujet = str(f.get("subject", ""))[:75]
    prem = str(f.get("body", "")).strip().replace("\n", " | ")[:110]
    print("#%s [note=%s]\n   objet : %s\n   1re ln: %s" % (num, note, sujet, prem))
