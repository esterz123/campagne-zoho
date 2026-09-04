# -*- coding: utf-8 -*-
"""Controles qualite file restante — chef_qa_file_0903.py (read-only)."""
import json, re, os

os.chdir(r"C:\Users\ulamb\Bureau\prospection\github-campagne")

data = json.load(open("campagne_data.json", encoding="utf-8"))
state = json.load(open("campagne_state.json", encoding="utf-8"))
sent = state["sent"]

restants = [f for i, f in enumerate(data) if str(f.get("num", i)) not in sent]
print("Restants:", len(restants))

bad2019, badtiret, badport, doubledom, vide, old2900 = [], [], [], [], [], []
for f in restants:
    num = str(f.get("num"))
    to = str(f.get("to", ""))
    sujet = str(f.get("sujet", ""))
    corps = str(f.get("corps", ""))
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
    if "2900" in corps:
        old2900.append(num)

print("U+2019:", len(bad2019), bad2019[:10])
print("tirets longs:", len(badtiret), badtiret[:10])
print("sans Portfolio:", len(badport), badport[:10])
print("ouverture double domaine:", len(doubledom), doubledom[:10])
print("corps quasi vide:", len(vide), vide[:10])
print("citent 2900 (prix rentree expire):", len(old2900), old2900[:10])

# echantillon objet+1re ligne des 5 premiers restants (ordre d'envoi = note croissante)
print("\n=== 5 PROCHAINS ENVOIS PREVUS ===")
cs = json.load(open("constats_sites.json", encoding="utf-8"))
triables = []
for f in restants:
    num = str(f.get("num"))
    c = cs.get(num, {})
    note = c.get("note")
    triables.append((note if isinstance(note, (int, float)) else 999, num, f))
triables.sort(key=lambda x: x[0])
for note, num, f in triables[:5]:
    sujet = str(f.get("sujet", ""))[:70]
    corps = str(f.get("corps", "")).strip().split("\n")[0][:90]
    print("#%s [note=%s] %s" % (num, note, sujet))
    print("   1re ligne: %s" % corps)
