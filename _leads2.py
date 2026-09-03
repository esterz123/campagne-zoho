import json, re
raw = open('C:/Users/ulamb/AppData/Local/hermes/profiles/momba-capitaine/cache/terminal-output/out-1788312000-9812-c2d0.log', encoding='utf-8').read()
# ne garder que les lignes qui ne sont pas SMTP verify user_unknown
lines = [l for l in raw.splitlines() if 'SMTP verify' not in l and l.startswith('#')]
print("notes/humaines:", len(lines))
for l in lines: print(l[:160])
