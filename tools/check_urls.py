#!/usr/bin/env python3
"""Check the built site against seo/url-map.csv.

Every KEEP url in the map is a live, indexed page on the Wix site. A 404 on
one of those after migration is a regression, not a design decision — the map
is the contract. DROPPED works are the exception: the cut is deliberate, so
they are reported separately as needing a redirect at cutover.

Usage:  python3 tools/check_urls.py [--base http://localhost:8010]
"""
import csv, json, os, sys, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
base = "http://localhost:8010"
if "--base" in sys.argv:
    base = sys.argv[sys.argv.index("--base") + 1]

sel = json.load(open(f"{ROOT}/content/selection.json", encoding="utf-8"))
dropped = sel["works_dropped"]
orphans = sel["orphans_dropped"]


def status(path):
    if path == "/":
        path = "/index.html"
    url = base + urllib.parse.quote(path, safe="/") + \
        ("" if path.endswith("/") or "." in path.rsplit("/", 1)[-1] else "/")
    try:
        req = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        return 0


ok, missing, deliberate = [], [], []
with open(f"{ROOT}/seo/url-map.csv", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        if not row["action"].startswith("KEEP"):
            continue
        p = row["path_decoded"]
        code = status(p)
        slug = p.rstrip("/").rsplit("/", 1)[-1]
        if code == 200:
            ok.append(p)
        elif p.startswith("/artworks/") and slug in dropped:
            deliberate.append((p, dropped[slug]))
        elif p in orphans:
            deliberate.append((p, orphans[p]))
        else:
            missing.append((p, code))

print(f"200      {len(ok)}")
print(f"cut      {len(deliberate)}  (deliberate — needs a 301 at cutover)")
for p, target in sorted(deliberate):
    print(f"           {p:44} -> {target}")
print(f"MISSING  {len(missing)}")
for p, c in missing:
    print(f"           {c}  {p}")
sys.exit(1 if missing else 0)
