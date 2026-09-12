"""Fix 12/09 : les sujets C non envoyes affichent des scores >=75 (regle 04/09 violee).
-> bascule en curiosite S. Backup, asserts, flip du mapping C_test."""
import json, shutil, re
from urllib.parse import urlparse

shutil.copy("campagne_data.json", "campagne_data.json.bak_fixC0912")
shutil.copy("ab_test.json", "ab_test.json.bak_fixC0912")

st = json.load(open("campagne_state.json"))["sent"]
data = json.load(open("campagne_data.json"))
ab = json.load(open("ab_test.json"))
ct = ab.get("C_test", {}).get("num_variant", {})

n_fix = 0
for num, var in ct.items():
    if var != "C" or num in st:
        continue
    try:
        d = next(x for x in data if isinstance(x, dict) and str(x.get("num")) == str(num))
    except StopIteration:
        continue
    s = d.get("subject", "")
    m = re.search(r"(\d{2,3})/100", s)
    if not m or int(m.group(1)) < 75:
        continue
    site = d.get("site") or ""
    try:
        dom = re.sub(r"^www\.", "", urlparse(site).hostname or "")
    except ValueError:
        dom = ""
    if not dom:
        mu = re.search(r"https?://([^)/]+)", s)
        dom = mu.group(1) if mu else ""
    if not dom:
        print("SANS DOMAINE:", num)
        continue
    d["subject"] = "Votre diagnostic est pret : " + dom
    assert "\u2019" not in d["subject"] and "matin" not in d["subject"]
    ct[num] = "S"
    if str(num) in ab and isinstance(ab[str(num)], dict):
        ab[str(num)]["subject"] = d["subject"]
    n_fix += 1

json.dump(data, open("campagne_data.json", "w"), ensure_ascii=False, indent=1)
json.dump(ab, open("ab_test.json", "w"), ensure_ascii=False, indent=1)
print("BASCULES C->S:", n_fix)
