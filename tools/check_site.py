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
sys.path.insert(0, os.path.join(ROOT, "tools"))
from relativize import absolutize            # noqa: E402

os.chdir(ROOT)

pages = sorted(set(
    [f for f in glob.glob("**/index.html", recursive=True)
     if not f.startswith("_archive")] + ["404.html"]))

# The Stage home page carries its own overlaid header by design.
NO_SHARED_HEADER = {"index.html"}

fail = 0


# Pages carry page-relative links (see tools/relativize.py), so a link only
# means something once it is read back as a site path from the page holding
# it. 404.html is the exception: it resolves its root in the browser, and its
# links are relative to that, which is the site root by definition.
EXTERNAL = ("http://", "https://", "//", "mailto:", "tel:", "#", "data:")


def site_path(page, href):
    p = urllib.parse.unquote(href).split("#")[0].split("?")[0]
    if not p or p.startswith(EXTERNAL):
        return None
    return absolutize(p, "index.html" if page == "404.html" else page)


def resolve(path):
    p = path.strip("/")
    if not p:
        return "index.html"
    return p if os.path.isfile(p) else f"{p}/index.html"


# 1. internal links
SCRIPT = re.compile(r"<script\b.*?</script>", re.S)
broken = []
for f in pages:
    # Skip script bodies: 404.html writes a <base href> from JavaScript.
    markup = SCRIPT.sub("", open(f, encoding="utf-8").read())
    for h in re.findall(r'href="([^"]*)"', markup):
        p = site_path(f, h)
        if p and not os.path.exists(resolve(p)):
            broken.append((f, h))
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
    # Two variants are intentional: the active nav item, and the ../ depth
    # each page needs to reach the same six pages. Read the links back as
    # site paths and both pages' headers say the same thing.
    n = re.sub(r' aria-current="page"', "", m.group(0))
    n = re.sub(r'href="([^"]*)"',
               lambda mm: f'href="{site_path(f, mm.group(1)) or mm.group(1)}"', n)
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
