"""Qualifie max 15 agences (lot lent : 30s entre requetes Brave, anti-ban).
Reprend _agences_qualifiees.json, complete les SIREN manquants."""
import json, os, re, time, urllib.request, urllib.parse

RES = "candidats_agences.json"
OUT = "_agences_qualifiees.json"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
JUNK = ("linkedin.", "facebook.", "instagram.", "pagesjaunes", "societe.com",
        "pappers.", "infogreffe", "verif.", "sirene.", "google.", "brave.com",
        "youtube.", "tiktok.", "x.com", "wikipedia.")
N_MAX = 15
SLEEP_Q = 30

def get(url, timeout=15):
    req = urllib.request.Request(url, headers=UA)
    return urllib.request.urlopen(req, timeout=timeout).read().decode("utf-8", "replace")

reserve = json.load(open(RES))
done = {}
if os.path.exists(OUT):
    for x in json.load(open(OUT)):
        done[x["siren"]] = x
print("deja:", len(done))
todo = [a for a in reserve if a.get("siren") and (a["siren"] not in done or not done[a["siren"]].get("domaine"))][:N_MAX]
print("lot:", len(todo))

for a in todo:
    siren, nom, ville = a.get("siren", ""), a.get("nom", ""), a.get("ville", "")
    rec = {"siren": siren, "nom": nom, "ville": ville, "domaine": "",
           "emails": [], "siren_ok": False, "gerant": "", "note": ""}
    try:
        q = urllib.parse.quote_plus(nom + " " + ville + " agence web")
        html = get("https://search.brave.com/search?q=" + q)
        doms = []
        for m in re.finditer(r"https://(?:www\.)?([a-z0-9][a-z0-9.-]+\.[a-z]{2,10})(?:[/\"?]|$)", html):
            d = m.group(1).lower()
            if not any(j in d for j in JUNK) and d not in doms:
                doms.append(d)
        rec["candidats_domaines"] = doms[:5]
        home, d = "", ""
        for d in doms[:3]:
            try:
                home = get("https://" + d)
                break
            except Exception:
                continue
        if not home:
            rec["note"] = "aucun domaine joignable"
        else:
            rec["domaine"] = d
            rec["emails"] = sorted(set(re.findall(r"[\w.+-]+@" + re.escape(d), home, re.I)))
            for page in ("/mentions-legales", "/mentions-legales/", "/contact"):
                try:
                    ml = get("https://" + d + page)
                    if siren.replace(" ", "") in ml.replace(" ", "").replace(".", ""):
                        rec["siren_ok"] = True
                    gm = re.search(r"(?:[Gg][ée]rant|[Dd]irecteur de la publication|[Pp]r[eé]sident)\s*:?\s*(?:M(?:me|\.)?\.?\s*)?([A-ZÀ-Ü][A-Za-zÀ-ü' -]{2,40})", ml)
                    if gm:
                        rec["gerant"] = gm.group(1).strip()
                    if not rec["emails"]:
                        rec["emails"] = sorted(set(re.findall(r"[\w.+-]+@" + re.escape(d), ml, re.I)))
                    break
                except Exception:
                    continue
    except Exception as e:
        rec["note"] = "erreur: " + type(e).__name__
    done[siren] = rec
    json.dump(list(done.values()), open(OUT, "w"), ensure_ascii=False, indent=1)
    print(siren, "|", rec["domaine"], "|", rec["emails"][:2], "| SIREN:" + str(rec["siren_ok"]), "|", rec["gerant"][:25])
    time.sleep(SLEEP_Q)
print("LOT TERMINE")
