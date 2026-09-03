# Verite terrain 03/09 : (1) mail Gaultier parti ? (2) reponses humaines des 5 boites depuis le 02/09 soir
import sys, json, re, html, urllib.request
sys.path.insert(0, '.')
import campagne_zoho as cz

boites = cz.load_boites()
RES = {}

def api_get(url, token):
    req = urllib.request.Request(url, headers={'Authorization': 'Zoho-oauthtoken ' + token})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return json.loads(r.read().decode('utf-8', 'replace'))
    except Exception as e:
        return {'_err': str(e)}

for creds in boites:
    name = creds.get('nom', '?')
    try:
        token = cz.refresh_token(creds)
    except Exception:
        token = None
        for k in ('token', 'access_token'):
            if creds.get(k):
                token = creds[k]
                break
    acc = creds.get('account_id') or creds.get('accountId') or creds.get('zuid') or ''
    if not acc or not token:
        RES[name] = 'pas de compte/token'
        continue
    # 1) sent -> gaultier
    surl = f'https://mail.zoho.com/api/accounts/{acc}/messages/search?searchKey=in%3Asent%20gaultier&limit=10&sortBy=receivedTime'
    sent = api_get(surl, token)
    gsent = []
    for m in (sent.get('data') or []):
        to = html.unescape(str(m.get('toAddress', '')))
        if 'gaultier' in to.lower():
            gsent.append((m.get('receivedTime', '')[:16], to[:60], m.get('subject', '')[:60]))
    # 2) inbox recent hors nous
    iurl = f'https://mail.zoho.com/api/accounts/{acc}/messages/search?searchKey=in%3Ainbox%20is%3Aunread&limit=25&sortBy=receivedTime'
    inbox = api_get(iurl, token)
    humains = []
    for m in (inbox.get('data') or []):
        frm = html.unescape(str(m.get('fromAddress', '')))
        subj = str(m.get('subject', ''))
        if 'mahdi-design.com' in frm.lower():
            continue
        humains.append((m.get('receivedTime', '')[:16], frm[:60], subj[:70]))
    RES[name] = {'gaultier_sent': gsent, 'non_lus_hors_nous': humains}

print(json.dumps(RES, ensure_ascii=False, indent=1))
