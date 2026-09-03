# -*- coding: utf-8 -*-
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from collections import Counter

d = json.load(open('campagne_data.json', encoding='utf-8'))
sent = json.load(open('campagne_state.json', encoding='utf-8'))['sent']

# sent keys are str nums
sent_nums = set(int(k) for k in sent.keys() if str(k).isdigit())
data_nums = set(p['num'] for p in d)
print('sent_nums', len(sent_nums), 'min', min(sent_nums), 'max', max(sent_nums))
print('data_nums', len(data_nums), 'min', min(data_nums), 'max', max(data_nums))
print('sent∩data', len(sent_nums & data_nums))
not_sent = sorted(data_nums - sent_nums)
print('data NOT in sent:', len(not_sent), not_sent[:15])
sent_not_data = sorted(sent_nums - data_nums)
print('sent NOT in data:', len(sent_not_data), sent_not_data[:15])

# to_confirmed False = pas confirmés
tc = Counter(str(p.get('to_confirmed')) for p in d)
print('to_confirmed', dict(tc))
# non-confirmés et non envoyés = ?
nc_ns = [p for p in d if p['num'] not in sent_nums and p.get('to_confirmed') is not True]
print('pas envoyes ET pas confirmes:', len(nc_ns))
