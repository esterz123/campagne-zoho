import json, io, sys, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
p = r"C:\Users\ulamb\Bureau\prospection\github-campagne\campagne_data.json"
with open(p, encoding="utf-8") as f:
    data = json.load(f)

# candidats: notes contenant 'relance2 envoyee' ou 'aucune reponse depuis X jours' avec X>=7
pat = re.compile(r"[Rr]elance2 envoyee (\d{2})/(\d{2})", )
pat2 = re.compile(r"aucune reponse depuis (\d+) jour")
for d in data:
    note = str(d.get("note",""))
    m = pat.search(note)
    m2 = pat2.search(note)
    if m or m2:
        print("NUM", d.get("num"), "|", (d.get("prospect") or d.get("nom",""))[:50], "| to:", d.get("to"))
        if m: print("   relance2 le:", m.group(0))
        if m2: print("   silence:", m2.group(0))
        print("   note fin:", note[-300:].replace("\n"," | "))
        print("-----")
