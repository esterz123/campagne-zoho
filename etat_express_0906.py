"""Etat express : repondus, envois du jour, file partenaires."""
import json, datetime

st = json.load(open("campagne_state.json"))["sent"]
rep = [n for n, v in st.items() if isinstance(v, dict) and v.get("replied")]
print("REPONDUS:", rep)
auj = datetime.date.today().isoformat()
n = 0
for num, v in st.items():
    if isinstance(v, dict) and (v.get("on") or "")[:10] == auj:
        n += 1
        print(" AUJ #" + str(num), v.get("to"), "|", "RELANCE" if any(v.get(k) for k in ("sent_relance1", "sent_relance2", "sent_relance3")) else "PREMIER")
print("ENVOIS AUJOURD HUI:", n, "| TOTAL:", len(st))
pst = json.load(open("partenaires_state.json"))["sent"]
print("PART ENVOYES:", len(pst))
