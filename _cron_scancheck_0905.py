import json, io, os, sys, inspect
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.getcwd())
import repondeur as rep
print(inspect.signature(rep.fetch_inbox))
boites = rep.load_boites()
b = boites[0]
print('boite tuple len:', len(b), [type(x).__name__ for x in b])
# try several arg shapes
for shape in ('full', 'split'):
    try:
        if shape == 'full':
            msgs = rep.fetch_inbox(b, None, limit=10)
        else:
            msgs = rep.fetch_inbox(b[0], b[3], limit=10)
        print(shape, '->', len(msgs or []), type(msgs))
        if msgs:
            print('ex:', json.dumps(msgs[0], ensure_ascii=False)[:200])
        break
    except Exception as e:
        print(shape, 'ERR', str(e)[:120])
