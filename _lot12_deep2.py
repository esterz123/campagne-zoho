#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lot12 : deep check complet (home + toutes pages internes) pour tous les domaines candidats trouves."""
import json, re, time, urllib.request, urllib.error

BASE = r"C:\Users\ulamb\Bureau\prospection\github-campagne"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36",
      "Accept-Language": "fr-FR,fr;q=0.9"}

SITES = {
    161: ("tolerie-du-nord.fr", "441283918"),
    163: ("cntolerie.fr", "554502476"),
    165: ("hexagrill.com", "881652002"),
    166: ("www.mecanique-camblinoise.fr", "318697257"),
    168: ("dmg-france.fr", "328801014"),
    170: ("fonteneaumecaniquegenerale.fr", "490818754"),
    173: ("gaborit.fr", "487180556"),
    174: ("leonolivier.com", "320517493"),
    175: ("acmg.fr", "353247232"),
    176: ("mecagemo.fr", "714501947"),
    177: ("erde.fr", "958504532"),
    181: ("mgo.fr", "330294745"),
    184: ("somg.fr", "301866919"),
    193: ("baxter-injection.com", "399796861"),
    200: ("ouest-injection.fr", "411746977"),
}

def fetch(url, timeout=12):
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read(600000).decode("utf-8", "ignore"), r.geturl()
    except Exception:
        return None, None

def emails_in(html):
    out = set()
    for e in re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", (html or "").lower()):
        if any(x in e for x in ("example", "wixpress", "sentry", "godaddy", ".png", ".jpg", ".jpeg", ".gif",
                                ".js", ".css", ".svg", "schema.org", "w3.org", "sentry.io", "alpinejs",
                                "polyfill", "jquery", "email@domain", ".webp", "bootstrap", "cloudflare",
                                "google", "gstatic", "wp.com", "gravatar", "wordpress", "recrutement",
                                "sitemap", "no-reply", "noreply", "png@", "jpg@")):
            continue
        out.add(e)
    return sorted(out)

results = {}
for idx, (dom, siren) in SITES.items():
    home, final = fetch("https://" + dom)
    if not home:
        home, final = fetch("http://" + dom)
    if not home:
        results[str(idx)] = {"domaine": dom, "erreur": "injoignable"}
        print(idx, dom, "INJOIGNABLE", flush=True)
        continue
    base_dom = re.sub(r"^www\.", "", re.sub(r"^https?://", "", final).split("/")[0])
    html_all = home
    # collecte des pages internes (liens href)
    pages = set()
    for m in re.findall(r'href=["\']([^"\']+)["\']', home):
        u = m.split("#")[0].split("?")[0]
        if not u or len(u) > 120:
            continue
        if u.startswith("/"):
            pages.add("https://" + base_dom + u)
        elif base_dom in u:
            pages.add(u)
    # prioritise contact/mentions puis autres
    pages = sorted(pages, key=lambda u: (0 if any(k in u.lower() for k in ("contact", "mention", "legal", "nous")) else 1, u))[:15]
    for p in pages:
        h, _ = fetch(p)
        if h:
            html_all += h
        time.sleep(0.05)
    low_all = html_all.lower()
    cms = []
    if re.search(r"wp-content|wp-includes|wordpress", low_all): cms.append("WordPress")
    if re.search(r"joomla|com_content", low_all): cms.append("Joomla")
    if re.search(r"prestashop", low_all): cms.append("PrestaShop")
    if re.search(r"drupal", low_all): cms.append("Drupal")
    if re.search(r"generator[^>]*spip|spip\.php", low_all): cms.append("SPIP")
    if re.search(r"httrack", low_all): cms.append("HTTrack copie")
    gen = re.findall(r'<meta[^>]+name=["\']generator["\'][^>]+content=["\']([^"\']+)', low_all)
    if gen: cms.append(gen[0][:45])
    yrs = re.findall(r"copyright[^0-9]{0,30}(?:©|&copy;)?\s*([0-9]{4})", low_all) + \
          re.findall(r"(?:©|&copy;)\s*([0-9]{4})", low_all)
    years = sorted(set(int(y) for y in yrs if 1990 <= int(y) <= 2030))
    tables = low_all.count("<table")
    viewport = bool(re.search(r'name=["\']viewport["\']', low_all))
    siren_hit = siren in re.sub(r"[\s.\-\u00a0]", "", low_all)
    emails = emails_in(html_all)
    title = re.search(r"<title[^>]*>(.*?)</title>", home, re.S)
    # mots-cles d'identite : ville + slug nom
    ville = {"152": "ingrandes", "153": "melesse", "157": "heillecourt", "158": "seiches", "159": "treillieres",
             "160": "saint-paul", "161": "armentieres", "163": "saint-martin", "165": "tarascon", "166": "camblain",
             "167": "ranchot", "168": "meyrargues", "169": "soissons", "170": "maulevrier", "171": "moirans",
             "173": "challans", "174": "saint-ouen", "175": "pagny", "176": "saint-etienne", "177": "pont-remy",
             "181": "varanges", "182": "ennery", "184": "mereau", "186": "brignais", "190": "brieres",
             "191": "carquefou", "193": "vinay", "198": "somloire", "199": "alex", "200": "mamers"}.get(str(idx), "")
    kw_hits = [kw for kw in (ville,) if kw and kw in low_all]
    results[str(idx)] = {"domaine": dom, "final": final, "siren": siren, "cms": cms, "copyright": years,
                         "tables": tables, "viewport": viewport, "siren_hit": siren_hit,
                         "emails": emails, "title": (title.group(1).strip()[:80] if title else "")[:80],
                         "pages_scan": len(pages), "ville_hit": ville in low_all}
    print(idx, dom, "->", final[:60], "| CMS:", cms, "| cop:", years, "| tbl:", tables, "| vp:", viewport,
          "| siren:", siren_hit, "| ville:", ville in low_all, "| emails:", emails[:6], flush=True)
    json.dump(results, open(BASE + r"\_lot12_deep2_tmp.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    time.sleep(0.15)
print("OK")
