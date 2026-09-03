# -*- coding: utf-8 -*-
"""Probe: structure API + MX + SMTP 25 sortant."""
import json, sys, socket
try:
    import requests
    print("requests OK", requests.__version__)
except ImportError:
    print("requests MISSING")
    sys.exit(1)
try:
    import dns.resolver
    print("dnspython OK")
except ImportError:
    print("dnspython MISSING")

r = requests.get("https://recherche-entreprises.api.gouv.fr/search",
                 params={"q": "337793301"}, timeout=15)
d = r.json()
res = d["results"][0]
print("TOP KEYS:", sorted(res.keys()))
print("COMPLEMENTS KEYS:", sorted(res.get("complements", {}).keys()))
# look for any url-ish field anywhere
blob = json.dumps(d)
import re
urls = set(re.findall(r'https?://[^"\\ ]+', blob))
print("URLS in payload:", list(urls)[:10])

# SMTP test: MX of gmail + mahdi-design.com, try port 25 RCPT handshake
for dom in ["mahdi-design.com", "orange.fr"]:
    try:
        ans = sorted(dns.resolver.resolve(dom, "MX", lifetime=8), key=lambda x: x.preference)
        host = str(ans[0].exchange).rstrip(".")
        print(dom, "MX:", host)
        s = socket.create_connection((host, 25), timeout=8)
        banner = s.recv(200)
        print("  port25 banner:", banner[:60])
        s.close()
    except Exception as e:
        print("  port25 FAIL:", type(e).__name__, str(e)[:120])
