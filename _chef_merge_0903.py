# -*- coding: utf-8 -*-
"""Union-merge campagne_state.json : :2 (nous) + :3 (eux), cle la plus riche gagne."""
import json

nous = json.load(open('_nous_state_tmp.json'))
eux = json.load(open('_eux_state_tmp.json'))
print('nous sent:', len(nous.get('sent', {})), '| eux sent:', len(eux.get('sent', {})))

merge_sent = dict(nous.get('sent', {}))
for k, v in eux.get('sent', {}).items():
    if k not in merge_sent or len(json.dumps(v)) > len(json.dumps(merge_sent[k])):
        merge_sent[k] = v

merged = dict(nous)
merged['sent'] = merge_sent
for key in set(nous) | set(eux):
    if key == 'sent':
        continue
    a, b = nous.get(key), eux.get(key)
    if a == b:
        merged[key] = a
    elif isinstance(a, dict) and isinstance(b, dict):
        m = dict(a)
        m.update(b)
        merged[key] = m
    else:
        merged[key] = max([a, b], key=lambda x: len(json.dumps(x)) if x is not None else -1)

json.dump(merged, open('campagne_state.json', 'w'), indent=2, ensure_ascii=False)
print('merged sent:', len(merge_sent))
