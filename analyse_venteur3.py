import json, io, sys, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
p = r"C:\Users\ulamb\Bureau\prospection\github-campagne\campagne_data.json"
with open(p, encoding="utf-8") as f:
    data = json.load(f)

# num 5 Georget : note complete + body + subject actuels
for d in data:
    if d.get("num")==5:
        print("SUBJECT:", d.get("subject"))
        print("BODY:")
        print(d.get("body"))
        print("NOTE COMPLETE:")
        print(d.get("note"))
