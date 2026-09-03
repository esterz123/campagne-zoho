import json, os, urllib.request, urllib.parse

BASE = os.path.expanduser(r"~\Bureau\prospection")
tp = os.path.join(BASE, ".zoho_tokens.json")
tok = json.load(open(tp, encoding="utf-8"))
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
    json.dump(tok, open(tp, "w", encoding="utf-8"), indent=2)
    return j["access_token"]

try:
    folders = zget(f"https://mail.zoho.com/api/accounts/{acct}/folders", tok["access_token"])
except Exception:
    folders = zget(f"https://mail.zoho.com/api/accounts/{acct}/folders", fresh())

for f in folders.get("data", []):
    print(f.get("folderId"), "|", f.get("path") or f.get("folderName"), "| count:", f.get("messageCount"))
