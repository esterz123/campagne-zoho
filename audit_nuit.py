# -*- coding: utf-8 -*-
"""Audit nuit Chef : chiffres business verifis (lecture seule)."""
import json

st = json.load(open('campagne_state.json', encoding='utf-8'))
sent = st.get('sent', {})
total_sent = len(sent)
replied = [k for k, v in sent.items() if v.get('replied')]
rel1 = [k for k, v in sent.items() if v.get('sent_relance1')]
rel2 = [k for k, v in sent.items() if v.get('sent_relance2')]
print(f"ENVOYES TOTAL: {total_sent}")
print(f"REPLIES: {len(replied)} -> {replied}")
print(f"RELANCE1: {len(rel1)} | RELANCE2: {len(rel2)}")

data = json.load(open('campagne_data.json', encoding='utf-8'))
items = data if isinstance(data, list) else data.get('items', data)
print(f"FILE TOTALE: {len(items)}")
sent_nums = set(sent.keys())
vierges = [it for it in items if str(it.get('num')) not in sent_nums]
print(f"NON ENVOYES (vierges): {len(vierges)}")

# Cash reel (hors tests)
try:
    rev = json.load(open('suivi_revenus.json', encoding='utf-8'))
    entries = rev if isinstance(rev, list) else rev.get('entries', rev)
    if isinstance(entries, dict):
        entries = list(entries.values())
    tot = 0.0
    reel = 0
    for e in entries:
        if not isinstance(e, dict):
            continue
        note = str(e.get('note', '')) + str(e.get('payeur', ''))
        if 'TEST' in note.upper() or 'mahdi-design' in note.lower():
            continue
        amt = e.get('montant') or e.get('montant_eur') or e.get('amount') or 0
        try:
            tot += float(amt)
            reel += 1
        except (TypeError, ValueError):
            pass
    print(f"CASH REEL (hors tests): {tot} EUR ({reel} entrees reelles / {len(entries)} brutes)")
    for e in entries[-6:]:
        print("  REV:", json.dumps(e, ensure_ascii=False)[:220])
except Exception as ex:
    print("suivi_revenus:", ex)

# Journal boucle auto
try:
    j = json.load(open('amelioration_journal.json', encoding='utf-8'))
    cyc = j if isinstance(j, list) else j.get('cycles', j.get('journal', []))
    print(f"\nJOURNAL BOUCLE: {len(cyc)} cycles")
    for c in cyc[-3:]:
        print(json.dumps(c, ensure_ascii=False)[:350])
except Exception as ex:
    print("journal:", ex)

# Constats : combien de vierges ont une preuve (note) ?
try:
    cons = json.load(open('constats_sites.json', encoding='utf-8'))
    n_notes = sum(1 for v in cons.values() if isinstance(v, dict) and v.get('note') is not None)
    print(f"\nCONSTATS: {len(cons)} sites sondes, {n_notes} avec note")
except Exception as ex:
    print("constats:", ex)
