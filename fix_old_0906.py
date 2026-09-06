"""Les 3 envois du 06/09 sont partis avec l'ancien generateur : variante OLD honnete."""
import json

ab = json.load(open("ab_test.json"))
for n in ("468", "479", "503"):
    if n in ab:
        ab[n]["variant"] = "OLD"
json.dump(ab, open("ab_test.json", "w"), ensure_ascii=False, indent=1)
print("OK")
