# -*- coding: utf-8 -*-
# Controle regles R1-R6 sur le mail num 2 (tires longs, U+2019, portfolio) avant patch.
import json

recs = json.load(open(r"C:\Users\ulamb\Bureau\prospection\github-campagne\campagne_data.json", encoding="utf-8"))
r = [x for x in recs if x["num"] == 2][0]
s = r["subject"] + r["body"]
print("em-dash:", s.count(chr(8212)))
print("en-dash:", s.count(chr(8211)))
print("U+2019:", s.count(chr(8217)))
print("portfolio ok:", "mahdi-design.com" in r["body"])
print("guillemets:", r["body"].count(chr(171)))
