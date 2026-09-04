# -*- coding: utf-8 -*-
"""Ajoute le P.S. diag express aux restants (levier x1000). Backup + idempotent."""
import json, os, shutil, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
REPO = os.path.dirname(os.path.abspath(__file__))
os.chdir(REPO)
shutil.copy("campagne_data.json", "campagne_data.json.bak_ps_0903")
data = json.load(open("campagne_data.json", encoding="utf-8"))
state = json.load(open("campagne_state.json", encoding="utf-8"))
diag = json.load(open("diag_pages.json", encoding="utf-8"))
sent = set(state.get("sent", {}).keys())
ajoutes, skips = 0, []
for f in data:
    num = str(f["num"])
    if num in sent:
        continue
    body = f.get("body", "")
    if "diag/" in body:
        continue
    if num not in diag:
        skips.append(num)
        continue
    ps = "P.S. J'ai deja prepare le diagnostic express de votre site : https://mahdi-design.com/diag/%s.html" % num
    if "Cordialement" in body:
        body = body.replace("Cordialement", ps + "\n\nCordialement", 1)
    else:
        body = body.rstrip() + "\n\n" + ps
    f["body"] = body
    ajoutes += 1
json.dump(data, open("campagne_data.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("P.S. ajoutes: %d | sans page diag (skips): %s" % (ajoutes, skips))
# verifs
data2 = json.load(open("campagne_data.json", encoding="utf-8"))
bad19 = sum(1 for f in data2 if "\u2019" in f.get("body","") + f.get("subject",""))
badem = sum(1 for f in data2 if "\u2014" in f.get("body","") + f.get("subject","") or "\u2013" in f.get("body","") + f.get("subject",""))
sanspf = [str(f["num"]) for f in data2 if str(f["num"]) not in sent and "Portfolio : mahdi-design.com" not in f.get("body","")]
avecps = sum(1 for f in data2 if str(f["num"]) not in sent and "diag/" in f.get("body",""))
print("U+2019: %d | tirets longs: %d | restants sans portfolio: %d | restants avec P.S.: %d" % (bad19, badem, len(sanspf), avecps))
