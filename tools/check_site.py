#!/usr/bin/env python3
"""Structural checks on the built site.

Not a linter — these are the four things that would actually break the site
after a careless edit: a broken internal link, a page whose header has drifted
from the others, a surviving Wix CDN reference, or an image without written
alt text.

Usage:  python3 tools/check_site.py
"""
import collections, glob, hashlib, os, re, sys, urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

pages = sorted(set(
    [f for f in glob.glob("**/index.html", recursive=True)
     if not f.startswith("_archive")] + ["404.html"]))

# The alternative home page carries its own overlaid header by design — it is
# a second direction for / , not a page in the Register family. It is the one
# page exempt from the header-identity check below.
NO_SHARED_HEADER = {"stage/index.html"}

fail = 0


def resolve(href):
    p = urllib.parse.unquote(href).split("#")[0].split("?")[0]
    if p in ("", "/"):
        return "index.html"
    p = p.strip("/")
    return p if os.path.isfile(p) else f"{p}/index.html"


# 1. internal links
broken = [(f, h) for f in pages
          for h in re.findall(r'href="(/[^"]*)"', open(f, encoding="utf-8").read())
          if not os.path.exists(resolve(h))]
print(f"internal links     {'OK' if not broken else str(len(broken)) + ' BROKEN'}")
for f, h in broken[:20]:
    print(f"  {f} -> {h}")
fail += bool(broken)

# 2. header drift — the whole maintenance model depends on this
hashes = collections.defaultdict(list)
for f in pages:
    if f in NO_SHARED_HEADER:
        continue
    m = re.search(r'<header class="hdr">.*?</header>',
                  open(f, encoding="utf-8").read(), re.S)
    if not m:
        print(f"  NO HEADER {f}")
        fail += 1
        continue
    # One variant is intentional: the active nav item.
    n = re.sub(r' aria-current="page"', "", m.group(0))
    hashes[hashlib.md5(n.encode()).hexdigest()[:8]].append(f)
print(f"header identity    {'OK' if len(hashes) == 1 else str(len(hashes)) + ' VARIANTS'}")
if len(hashes) > 1:
    for h, fs in hashes.items():
        print(f"  {h}  x{len(fs):3}  e.g. {fs[0]}")
    fail += 1

# 3. Wix CDN references — these die when the plan is cancelled
wix = [f for f in pages + glob.glob("assets/**/*.css", recursive=True)
       + glob.glob("assets/**/*.js", recursive=True)
       if "wixstatic" in open(f, encoding="utf-8").read()]
print(f"wix references     {'OK' if not wix else str(len(wix)) + ' FOUND'}")
for f in wix:
    print(f"  {f}")
fail += bool(wix)

# 4. alt text — written, never a filename
bad_alt = []
for f in pages:
    for tag in re.findall(r"<img[^>]*>", open(f, encoding="utf-8").read()):
        m = re.search(r'alt="([^"]*)"', tag)
        alt = m.group(1) if m else None
        if not alt or re.search(r"\.(jpg|jpeg|png|webp)|_\d{2}-\d+", alt):
            bad_alt.append((f, (alt or "<missing>")[:60]))
print(f"image alt text     {'OK' if not bad_alt else str(len(bad_alt)) + ' BAD'}")
for f, a in bad_alt[:10]:
    print(f"  {f}: {a}")
fail += bool(bad_alt)

print(f"\n{len(pages)} pages checked")
sys.exit(1 if fail else 0)
