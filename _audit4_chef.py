# -*- coding: utf-8 -*-
"""Detail complet sent[63] (audit_suivi) + crons hermes + mailinblack."""
import json, io, sys, subprocess
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

st = json.load(open("campagne_state.json", encoding="utf-8"))
s63 = st.get("sent", {}).get("63", {})
print("SENT 63 COMPLET:")
print(json.dumps(s63, ensure_ascii=False, indent=1))
print()

# Chercher un message collab prepare quelque part
import os
for p in ("livrable/playbook_replies_3chauds.md",):
    if os.path.exists(p):
        txt = open(p, encoding="utf-8", errors="replace").read()
        idx = txt.find("GAULTIER")
        print(f"{p}: section GAULTIER a l'idx {idx}")
        if idx > 0:
            print(txt[idx:idx+600])
        print()
