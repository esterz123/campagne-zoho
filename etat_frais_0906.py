"""Etat frais : reponses + envois du jour."""
import json, datetime

st = json.load(open("campagne_state.json"))["sent"]
rep = [n for n, v in st.items() if isinstance(v, dict) and v.get("replied")]
print("REPONDUS:", rep)
for n in rep:
    v = st[n]
    print("#" + str(n), "|", v.get("to"), "|", (v.get("note") or "")[:150])
auj = datetime.date.today().isoformat()
print("AUJ:", auj)
for n, v in st.items():
    if isinstance(v, dict) and (v.get("on") or "")[:10] == auj:
        print(" envoi:", "#" + str(n), v.get("to"))
print("TOTAL ENVOYES:", len(st))
