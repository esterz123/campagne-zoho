import json
st = json.load(open('campagne_state.json', encoding='utf-8'))
sent = st.get('sent', {})
# structure reelle des valeurs
sample = list(sent.items())[:3]
print('SAMPLE:', sample)
#SIMI present?
print('SIMI (0):', sent.get('0'))
# relances: autre fichier ?
import os
for f in os.listdir('.'):
    if 'relance' in f.lower() or 'state' in f.lower() or 'follow' in f.lower():
        print('FICHIER:', f)
