import json, io, sys, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
p = r"C:\Users\ulamb\Bureau\prospection\github-campagne\campagne_data.json"
with open(p, encoding="utf-8") as f:
    data = json.load(f)

# 1) Gaultier #63
for d in data:
    if "gaultier" in str(d.get("prospect","")).lower() or "gaultier" in str(d.get("nom","")).lower() or d.get("num")==63:
        print("### NUM", d.get("num"), d.get("prospect") or d.get("nom"))
        for k,v in d.items():
            print(f"  {k}: {str(v)[:400]}")
        print("=====")

# 2) la note avec 'relance'
for d in data:
    if "relance" in str(d.get("note","")).lower():
        print("### NOTE RELANCE -> NUM", d.get("num"))
        print(str(d.get("note"))[:600])
