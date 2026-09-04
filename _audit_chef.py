# -*- coding: utf-8 -*-
import json
data = json.load(open("campagne_data.json", encoding="utf-8"))
state = json.load(open("campagne_state.json", encoding="utf-8"))
sent = state.get("sent", {})
items = data.get("prospects") or list(data.values()) if isinstance(data, dict) else data
nums_all = {str(p.get("num")) for p in items if p.get("num") is not None}
sent_keys = set(sent.keys())
remaining = sorted([n for n in nums_all if n not in sent_keys], key=lambda x: int(x))
replied = [n for n, v in sent.items() if v.get("replied")]
print("fiches:", len(nums_all), "| envoyes:", len(sent_keys & nums_all), "| restants:", len(remaining), "| replied:", len(replied), replied)
for n in replied:
    v = sent[n]
    print(n, "| sent:", v.get("on"), "| rel1:", v.get("sent_relance1"), "| rel2:", v.get("sent_relance2"), "| rel3:", v.get("sent_relance3"), "|", (v.get("note") or "")[:100])
# check go2 markers / divers
for k in state:
    if k != "sent":
        print("state key:", k, "=", str(state[k])[:120])
# revenue
try:
    rev = json.load(open("suivi_revenus.json", encoding="utf-8"))
    ent = rev.get("entrees", rev) if isinstance(rev, dict) else rev
    print("REVENU:", json.dumps(ent, ensure_ascii=False)[:500])
except Exception as e:
    print("rev err", e)
