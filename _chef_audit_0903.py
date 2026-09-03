# Audit chef 03/09 : inbox verite terrain + envois 24h + chauds
import json, os, time, urllib.request, urllib.parse

BASE = os.path.expanduser(r"~\Bureau\prospection")
REPO = os.path.join(BASE, "github-campagne")
os.chdir(REPO)

tok = json.load(open(os.path.join(BASE, ".zoho_tokens.json"), encoding="utf-8"))
acct = "7349712000000008002"

def zget(url, at):
    req = urllib.request.Request(url, headers={"Authorization": "Zoho-oauthtoken " + at})
    return json.loads(urllib.request.urlopen(req, timeout=30).read())

def fresh():
    data = urllib.parse.urlencode({
        "refresh_token": tok["refresh_token"], "client_id": tok["client_id"],
        "client_secret": tok["client_secret"], "grant_type": "refresh_token"}).encode()
    j = json.loads(urllib.request.urlopen(urllib.request.Request(
        "https://accounts.zoho.com/oauth/v2/token", data=data), timeout=30).read())
    tok["access_token"] = j["access_token"]
    json.dump(tok, open(os.path.join(BASE, ".zoho_tokens.json"), "w", encoding="utf-8"), indent=2)
    return j["access_token"]

at = tok.get("access_token") or fresh()
try:
    folders = zget(f"https://mail.zoho.com/api/accounts/{acct}/folders", at)
except Exception:
    at = fresh(); folders = zget(f"https://mail.zoho.com/api/accounts/{acct}/folders", at)

inbox_id = None
for f in folders.get("data", []):
    nm = (f.get("path") or f.get("folderName") or "").lower()
    if nm.endswith("inbox"):
        inbox_id = f.get("folderId"); break

if inbox_id:
    url = (f"https://mail.zoho.com/api/accounts/{acct}/folders/{inbox_id}/messages?limit=25&sortColumn=receivedTime")
    try:
        msgs = zget(url, at).get("data", [])
    except Exception:
        msgs = zget(url, fresh()).get("data", [])
    print("=== INBOX contact@ (25 derniers) ===")
    for m in msgs:
        frm = m.get("fromAddress") or "?"
        if "mahdi-design" in str(frm).lower():
            continue
        print(m.get("receivedTime","?")[:16], "|", frm[:40], "|", (m.get("subject") or "")[:70])
else:
    print("inbox non trouvee")

print()
print("=== STATE chauds ===")
s = json.load(open("campagne_state.json", encoding="utf-8"))
sent = s.get("sent", {})
for n, v in sorted(sent.items(), key=lambda kv: kv[1].get("on",""), reverse=True)[:8]:
    flags = [k for k in ("replied","sent_relance1","sent_relance2","diag_envoye","bounce") if v.get(k)]
    print(n, "|", v.get("on","?"), "|", v.get("via","?"), "|", ",".join(flags) or "-", "|", (v.get("note") or "")[:60])
