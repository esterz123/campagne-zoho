# Verite terrain : balaye les 5 boites Zoho, liste tout message NON-mahdi des 7 derniers jours
import json, os, re, sys, urllib.request, time
os.chdir(r'C:\Users\ulamb\Bureau\prospection\github-campagne')
sys.path.insert(0, os.getcwd())
import repondeur as rp

boites = rp.load_boites()
print("boites:", list(boites.keys()) if isinstance(boites, dict) else [b.get('email') for b in boites])

def norm(b):
    # chaque boite = dict avec email/refresh/client/secret ou mapping
    return b

import datetime
today = datetime.date.today()
semaine = (today - datetime.timedelta(days=7)).isoformat()

results = []
for name, b in (boites.items() if isinstance(boites, dict) else [(x.get('email'), x) for x in boites]):
    try:
        access = rp.refresh_access(b)
    except Exception as e:
        print(name, "refresh KO:", str(e)[:100]); continue
    acc_id = b.get('account') or b.get('account_id') or ''
    if not acc_id:
        # chercher via zoho_get accounts
        try:
            r = rp.zoho_get("https://mail.zoho.com/api/accounts", access)
            data = json.loads(r) if isinstance(r, (str, bytes)) else r
            acc_id = data['data'][0]['accountId']
        except Exception as e:
            print(name, "account KO:", str(e)[:120]); continue
    # inbox folder id
    try:
        r = rp.zoho_get(f"https://mail.zoho.com/api/accounts/{acc_id}/folders", access)
        data = json.loads(r) if isinstance(r, (str, bytes)) else r
        fid = None
        for f in data['data']:
            if f['path'] == 'Inbox':
                fid = f['folderId']; break
        if not fid: continue
        r = rp.zoho_get(f"https://mail.zoho.com/api/accounts/{acc_id}/folders/{fid}/messages?limit=50&sort=desc", access)
        data = json.loads(r) if isinstance(r, (str, bytes)) else r
        for m in data.get('data', []):
            frm = (m.get('fromAddress') or '').lower()
            subj = m.get('subject') or ''
            dt = (m.get('receivedTime') or '')[:10]
            if 'mahdi-design' in frm: continue
            results.append((name, dt, frm, subj[:70], m.get('messageId')))
    except Exception as e:
        print(name, "scan KO:", str(e)[:120])

print("\n=== MESSAGES NON-MAHDI (7 derniers jours, 50 derniers par boite) ===")
for r in results:
    print(r[0], '|', r[1], '|', r[2], '|', r[3])
print("TOTAL:", len(results))
