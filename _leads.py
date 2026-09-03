import json
st = json.load(open('campagne_state.json', encoding='utf-8'))
cd = json.load(open('campagne_data.json', encoding='utf-8'))
bynum = {str(p['num']): p for p in cd}
sent = st['sent']
# chauds: notes + replied + relances_conges
print("== NOTED / CHAUDS dans sent ==")
for k,v in sorted(sent.items(), key=lambda x: int(x[0])):
    note = v.get('note','') or ''
    replied = v.get('replied')
    if replied or note:
        p = bynum.get(k, {})
        print(f"#{k} | replied={replied} | {str(p.get('prospect'))[:40]} | {note[:110]}")
