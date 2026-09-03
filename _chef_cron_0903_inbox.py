import json, os, time, urllib.request

BASE = os.path.expanduser(r"~\Bureau\prospection")
REPO = os.path.join(BASE, "github-campagne")
tp = os.path.join(BASE, ".zoho_tokens.json")
tok = json.load(open(tp, encoding="utf-8"))
refresh = tok.get("refresh_token")
cid, csec = tok.get("client_id"), tok.get("client_secret")

def refresh_access():
    data = urllib.parse.urlencode({
        "refresh_token": refresh, "client_id": cid, "client_secret": csec,
        "grant_type": "refresh_token"}).encode()
    r = urllib.request.urlopen(urllib.request.Request(
        "https://accounts.zoho.com/oauth/v2/token", data=data), timeout=30)
    j = json.loads(r.read())
    tok["access_token"] = j["access_token"]
    json.dump(tok, open(tp, "w", encoding="utf-8"), indent=2)
    return j["access_token"]

import urllib.parse
try:
    at = tok.get("access_token")
    # test
    req = urllib.request.Request(
        "https://mail.zoho.com/api/accounts",
        headers={"Authorization": "Zoho-oauthtoken " + at})
    accounts = json.loads(urllib.request.urlopen(req, timeout=30).read())
except Exception:
    at = refresh_access()
    req = urllib.request.Request(
        "https://mail.zoho.com/api/accounts",
        headers={"Authorization": "Zoho-oauthtoken " + at})
    accounts = json.loads(urllib.request.urlopen(req, timeout=30).read())

acct = accounts["data"][0]["accountId"]
print("accountId:", acct, "| boite:", accounts["data"][0].get("primaryEmailAddress", "?"))

def zget(url):
    req = urllib.request.Request(url, headers={"Authorization": "Zoho-oauthtoken " + at})
    return json.loads(urllib.request.urlopen(req, timeout=30).read())

# inbox
inbox = zget(f"https://mail.zoho.com/api/accounts/{acct}/messages/search?searchKey=in:inbox&limit=30")
msgs = inbox.get("data", [])
print("=== INBOX (30 derniers) ===")
for m in msgs:
    frm = m.get("senderAddress") or m.get("fromAddress") or "?"
    subj = (m.get("subject") or "")[:80]
    dt = m.get("receivedTime") or m.get("sentTime") or ""
    flag = ""
    if "mailinblack" in frm: flag = "[QUARANTAINE]"
    print(f"{dt[:10]} | {frm[:40]:40} | {subj} {flag}")

# sent aujourd'hui
sent = zget(f"https://mail.zoho.com/api/accounts/{acct}/messages/search?searchKey=in:sent&limit=15")
print("=== SENT (15 derniers) ===")
for m in sent.get("data", [])[:15]:
    to = m.get("toAddress") or "?"
    subj = (m.get("subject") or "")[:70]
    dt = m.get("sentTime") or ""
    print(f"{dt[:10]} | {to[:45]:45} | {subj}")
