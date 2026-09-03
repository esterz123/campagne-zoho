import json
st = json.load(open('campagne_state.json', encoding='utf-8'))
print("STATE keys:", list(st.keys())[:25])
for k in list(st.keys())[:25]:
    v = str(st[k])[:150]
    print(f"  {k} = {v}")
cd = json.load(open('campagne_data.json', encoding='utf-8'))
print("\nDATA keys:", list(cd.keys())[:25])
