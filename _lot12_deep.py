#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lot12 deep check: CMS, copyright, tables, viewport, emails, siren on home+contact+legal pages."""
import json, re, time, urllib.request

BASE = r"C:\Users\ulamb\Bureau\prospection\github-campagne"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36",
      "Accept-Language": "fr-FR,fr;q=0.9"}

SITES = {
    152: ("tifsas.com", "315189597"),
    153: ("gromy.fr", "392316782"),
    157: ("tolerieservice54.com", "414117945"),
    158: ("camega-tolerie.com", "434269411"),
    160: ("smg-decoupage-tolerie.com", "525620332"),
    167: ("dmg-decoupage.com", "352688428"),
    169: ("magmecanique.fr", "715580262"),
    171: ("mgf-grimaldi.com", "313002214"),
    182: ("mggc.fr", "708200175"),
    186: ("fonderie-vincent.com", "957502164"),
    190: ("lory-fonderies.fr", "405223843"),
    191: ("ouest-injection.fr", "775604945"),
    198: ("anjou-injection.fr", "878798552"),
    199: ("groupeinjection74.com", "388781544"),
}

def fetch(url, timeout=10):
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read(500000).decode("utf-8", "ignore")
    except Exception as e:
        return None

def emails_in(html):
    out = set()
    for e in re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", (html or "").lower()):
        if any(x in e for x in ("example", "wixpress", "sentry", "godaddy", ".png", ".jpg", ".jpeg", ".gif",
                                ".js", ".css", ".svg", "schema.org", "w3.org", "sentry.io", "alpinejs",
                                "polyfill", "jquery", "email@domain", ".webp", "bootstrap", "cloudflare",
                                "google", "gstatic", "wp.com", "gravatar", "wordpress", "recrutement",
                                "sitemap", "no-reply", "noreply")):
            continue
        out.add(e)
    return sorted(out)

results = {}
for idx, (dom, siren) in SITES.items():
    home = fetch("https://" + dom)
    if not home:
        home = fetch("http://" + dom)
    if not home:
        results[str(idx)] = {"domaine": dom, "erreur": "injoignable"}
        print(idx, dom, "INJOIGNABLE", flush=True)
        continue
    # pages supplementaires : contact / mentions legales
    pages = []
    for m in re.findall(r'href=["\']([^"\']+)["\']', home):
        u = m.split("#")[0]
        low = u.lower()
        if any(k in low for k in ("contact", "mention", "legal", "infos", "nous")) and len(u) < 120:
            if u.startswith("/"):
                pages.append("https://" + dom + u)
            elif dom in u:
                pages.append(u)
    pages = pages[:6]
    html_all = home
    for p in pages:
        h = fetch(p)
        if h:
            html_all += h
    low_all = html_all.lower()
    cms = []
    if re.search(r"wp-content|wp-includes|wordpress", low_all): cms.append("WordPress")
    if re.search(r"joomla|com_content", low_all): cms.append("Joomla")
    if re.search(r"prestashop", low_all): cms.append("PrestaShop")
    if re.search(r"drupal", low_all): cms.append("Drupal")
    if re.search(r"generator[^>]*spip|spip\.php", low_all): cms.append("SPIP")
    gen = re.findall(r'<meta[^>]+name=["\']generator["\'][^>]+content=["\']([^"\']+)', low_all)
    if gen: cms.append(gen[0][:40])
    # copyright years
    yrs = re.findall(r"copyright[^0-9]{0,30}(?:©|&copy;)?\s*([0-9]{4})", low_all) + \
          re.findall(r"(?:©|&copy;)\s*([0-9]{4})", low_all)
    years = sorted(set(int(y) for y in yrs if 1990 <= int(y) <= 2030))
    tables = low_all.count("<table")
    viewport = bool(re.search(r'name=["\']viewport["\']', low_all))
    siren_hit = siren in re.sub(r"[\s.\-\u00a0]", "", low_all)
    emails = emails_in(html_all)
    title = re.search(r"<title[^>]*>(.*?)</title>", home, re.S)
    results[str(idx)] = {"domaine": dom, "siren": siren, "cms": cms, "copyright": years,
                         "tables": tables, "viewport": viewport, "siren_hit": siren_hit,
                         "emails": emails, "title": (title.group(1).strip()[:80] if title else "")[:80],
                         "pages_extra": len(pages)}
    print(idx, dom, "| CMS:", cms, "| cop:", years, "| tables:", tables, "| viewport:", viewport,
          "| siren:", siren_hit, "| emails:", emails[:6], flush=True)
    time.sleep(0.2)

json.dump(results, open(BASE + r"\_lot12_deep_tmp.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("OK")
