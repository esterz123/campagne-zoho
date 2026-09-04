# -*- coding: utf-8 -*-
# Audit business rapide : file reelle, reponses, cash, Gaultier/SIMI/FPSA
import json, os, re

BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)

def jload(p):
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except Exception as ex:
        print("ERR", p, ex)
        return {}

data = jload("campagne_data.json")
state = jload("campagne_state.json")
sent = state.get("sent", {})

nums_data = {str(e.get("num")) for e in data if isinstance(e, dict)}
envoyes = sorted([n for n in nums_data if n in sent], key=int)
replied = sorted([n for n in envoyes if sent[n].get("replied")], key=int)
restants = sorted(nums_data - set(sent), key=int)
print("file=%d envoyes=%d restants=%d replied=%d" % (len(nums_data), len(envoyes), len(restants), len(replied)))
print("replied nums:", ",".join(replied))

# par date: combien envois aujourd'hui / hier
import datetime as dt
auj = dt.date.today().isoformat()
hier = (dt.date.today() - dt.timedelta(days=1)).isoformat()
def d_count(day):
    return sum(1 for n in envoyes if str(sent[n].get("on","")).startswith(day))
print("envois aujourd'hui(%s): %d | hier(%s): %d" % (auj, d_count(auj), hier, d_count(hier)))

# chauds: detail replied + diag envoye ?
by_num = {str(e.get("num")): e for e in data if isinstance(e, dict)}
for n in replied:
    e = by_num.get(n, {})
    s = sent.get(n, {})
    print("CHAUD #%s | %s | via=%s | on=%s | diag_envoye=%s | notes=%s" % (
        n, e.get("nom", e.get("entreprise", "?")), s.get("via"), s.get("on"),
        s.get("diag_envoye"), {k: v for k, v in s.items() if k not in ("on", "via")}))

# relances en attente (J+3/J+7/J+14 dues mais non envoyees)
import time
now = time.time()
def iso_to_ts(s):
    try:
        return dt.datetime.fromisoformat(str(s)[:10]).timestamp()
    except Exception:
        return None
dues1 = dues2 = dues3 = 0
for n in envoyes:
    s = sent.get(n, {})
    if s.get("replied"):
        continue
    ts = iso_to_ts(s.get("on"))
    if not ts:
        continue
    age_d = (now - ts) / 86400.0
    if age_d >= 3 and not s.get("sent_relance1"):
        dues1 += 1
    if age_d >= 7 and not s.get("sent_relance2"):
        dues2 += 1
    if age_d >= 14 and not s.get("sent_relance3"):
        dues3 += 1
print("relances dues: J+3=%d J+7=%d J+14=%d" % (dues1, dues2, dues3))

# cash reel
rev = jload("suivi_revenus.json")
reels = [e for e in rev.get("entrees", []) if "TEST" not in str(e.get("note", ""))
         and "mahdi-design" not in str(e.get("payeur", e.get("source", "")))]
total = sum(e.get("montant", 0) for e in reels if e.get("statut") == "encaisse")
print("CASH reel encaisse: %s EUR | entrees: %s" % (total, json.dumps(reels, ensure_ascii=False)))

# hot files: relance closing SIMI, Gaultier message
for p in ["livrable/relance_closing_SIMI.txt"]:
    if os.path.exists(p):
        print("PRESENT:", p, os.path.getsize(p), "octets")
    else:
        print("ABSENT:", p)

# Gaultier #63 state detail
print("Gaultier #63 state:", json.dumps(sent.get("63", {}), ensure_ascii=False))
