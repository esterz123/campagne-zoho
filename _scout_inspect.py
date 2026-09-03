# -*- coding: utf-8 -*-
import json, re
d = json.load(open('campagne_data.json', encoding='utf-8'))
print("entries:", len(d))
nums = [r.get("num") for r in d if isinstance(r.get("num"), int)]
print("max num:", max(nums), "min:", min(nums))
# keys used
allkeys = {}
for r in d:
    for k in r: allkeys[k] = allkeys.get(k,0)+1
print("keys:", allkeys)
# domains from to
doms = set()
for r in d:
    m = re.search(r'@([\w.-]+)', (r.get("to") or "") + ";" + (r.get("cc") or ""))
    for mm in re.finditer(r'@([A-Za-z0-9.-]+)', (r.get("to") or "") + ";" + (r.get("cc") or "")):
        doms.add(mm.group(1).lower())
print("distinct email domains:", len(doms))
# last 3 entries
print(json.dumps(d[-2:], ensure_ascii=False, indent=1)[:2500])
# sirens already present?
sirens = set(str(r.get("siren")) for r in d if r.get("siren"))
print("siren fields present:", len(sirens))
