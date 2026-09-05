import json, io, os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.getcwd())
import repondeur as rep

boites = rep.load_boites()
print('boites:', len(boites))
humains = []
for b in boites:
    try:
        name, creds, access = b[0], b[1], b[3] if len(b) > 3 else None
    except Exception:
        continue
    if not access:
        continue
    try:
        msgs = rep.fetch_inbox(b, access, limit=30)
    except Exception as e:
        print('ERR', name, str(e)[:80])
        continue
    for m in msgs or []:
        frm = str(m.get('from', ''))
        subj = str(m.get('subject', ''))
        summ = str(m.get('summary', ''))
        if rep.is_ours(frm):
            continue
        if rep.is_auto(summ, subj):
            continue
        humains.append((name, frm, subj, summ[:90]))
print('messages non-auto non-ours:', len(humains))
for x in humains[:20]:
    print('|', x[0], '|', x[1][:45], '|', x[2][:50], '|', x[3][:70])
