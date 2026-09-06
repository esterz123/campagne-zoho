"""Neutralise #464 (email corrompu u002f, hors cible) : marque bounce + note, bloque les relances."""
import json, shutil

shutil.copy("campagne_state.json", "campagne_state.json.bak_464")
st = json.load(open("campagne_state.json"))
e = st["sent"]["464"]
e["bounce"] = True
e["note"] = "06/09: email corrompu u002f (= / encode), Kiloutou hors cible PME, relances bloquees"
json.dump(st, open("campagne_state.json", "w"), ensure_ascii=False, indent=1)
print("OK #464 neutralise")
