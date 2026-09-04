# -*- coding: utf-8 -*-
import json, os
BASE = r"C:\Users\ulamb\Bureau\prospection\github-campagne"
state = json.load(open(os.path.join(BASE, "campagne_state.json"), encoding="utf-8"))
v = state.get("sent", {}).get("3", {})
print(json.dumps(v, ensure_ascii=False, indent=1))
# clefs globales mentionnant rouxel
for k in state:
    if k != "sent" and "rouxel" in k.lower():
        print("GLOBAL:", k, str(state[k])[:200])
