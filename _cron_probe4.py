# Probe 4 : Exa run log + workflow chasse (input/file?) + vitrine form + strategie planifiee
import json, os, glob, re

# 1. Le run Exa en cours : quel workflow, quel script ?
for f in glob.glob('.github/workflows/*.yml') + glob.glob('.github/workflows/*.yaml'):
    txt = open(f, encoding='utf-8', errors='replace').read()
    if 'Exa' in txt or 'exa' in txt.lower():
        print("=== WF:", f, "===")
        print(txt[:1200])
        print('...')

# 2. strategie / planifie / canaux
for f in ['STRATEGIE_100M_PLANIFIEE.json', 'CANAUX_NOUVEAUX_20260901.md', 'PLAN_ACTION_B2B_100M.md']:
    if os.path.exists(f):
        print("\n===", f, "existe ===")
        print(open(f, encoding='utf-8', errors='replace').read()[:600])

# 3. nouveaux prospects en attente (nouveau_prospects.json)
try:
    np = json.load(open('nouveau_prospects.json'))
    if isinstance(np, list):
        print("\n=== NOUVEAU_PROSPECTS ===", len(np), "entrees")
        for d in np[:3]:
            print(' ', {k: str(v)[:40] for k, v in d.items() if k in ('num', 'email', 'entreprise', 'site')})
    else:
        print("\nnouveau_prospects:", type(np), str(np)[:300])
except Exception as e:
    print("\nnouveau_prospects ERR", e)

# 4. campagne_data : dernier num
data = json.load(open('campagne_data.json'))
pros = [d for d in data if d.get('type', 'prospect') == 'prospect']
nums = [int(d.get('num', 0)) for d in pros]
print("\n=== CAMPAGNE_DATA === max num:", max(nums), "| total pros:", len(pros))
