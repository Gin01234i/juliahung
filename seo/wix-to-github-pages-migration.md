# Wix → GitHub Pages Migration: jujuhung.com

Working notes from a session on 2026-09-17. Site crawled live; findings below are
from the actual site, not assumptions.

Companion file: [`url-map.csv`](./url-map.csv) — all 101 URLs, classified.

---

## Q1: I have a website on Wix. I want to move it to GitHub Pages. What do I do so SEO won't be affected?

### The one big constraint

**GitHub Pages cannot do 301 redirects.** No `.htaccess`, no `_redirects`, no server
config — it serves static files and that's it. Two viable strategies:

1. **Replicate the Wix URL structure exactly.** No redirects needed. Safest default.
2. **Put Cloudflare (free) in front of GitHub Pages** and do real 301s with Redirect
   Rules / Bulk Redirects. Needed if URLs change; also buys cache headers and HSTS,
   which GH Pages won't let you set.

Fallback for a handful of stragglers: HTML `<meta http-equiv="refresh" content="0">`
plus `rel=canonical`. Google treats it as a redirect, but it consolidates more slowly
and passes signals less reliably.

### 1. Inventory before touching anything

You can't preserve what you didn't record. While Wix is still live, capture:

- `https://yoursite.com/sitemap.xml` — every URL
- Search Console → Pages report (all indexed URLs); Performance → Pages, top pages by
  clicks, last 12 months (this is your priority list)
- A crawl (Screaming Frog free tier does 500 URLs) exporting per page: **URL, title,
  meta description, H1, canonical, og:/twitter: tags, JSON-LD, image alt text,
  internal links, word count**
- Backlink data if available — pages with external links cannot be broken

### 2. Wix URL quirks to replicate

- Blog posts live at `/post/slug`, index at `/blog`. Recreate literally:
  `post/slug/index.html`.
- **Trailing slashes and case.** GitHub Pages is case-sensitive; Wix is forgiving.
  Use `dir/index.html` so URLs serve at `/dir/`, and set `rel=canonical` to exactly
  one form everywhere.
- Multilingual subfolders and dynamic pages with query strings need explicit handling —
  query params don't exist on static hosting.

### 3. Port on-page signals 1:1

Same title, meta description, H1, heading hierarchy, body copy, image alt text, JSON-LD,
OG/Twitter cards, internal linking. Rewriting copy during a migration makes it impossible
to attribute a ranking drop. **Migrate first, improve later.**

Hand-write `robots.txt` and `sitemap.xml` (Wix generated those; they won't exist anymore).
Add `404.html` — GH Pages serves it with a real 404 status.

### 4. Domain and HTTPS

- Keep the exact same domain, including the www-vs-apex choice.
- `CNAME` file in repo root. DNS: apex → A records `185.199.108.153`, `.109.153`,
  `.110.153`, `.111.153` (or ALIAS/ANAME); `www` → CNAME to `<user>.github.io`.
- Enable **Enforce HTTPS**. Cert provisioning can take up to 24h after DNS resolves.
- **Re-verify Search Console with a DNS TXT record** before cutover. Wix's built-in GSC
  verification breaks when DNS moves.

### 5. Cutover sequence

1. Build and test on `<user>.github.io`. If you add `noindex` while staging, set a
   reminder to remove it — launching with `noindex` still in place is the most common
   self-inflicted wound.
2. Drop DNS TTL to 300s a day or two ahead.
3. Crawl staging, diff URL list + titles against the Wix inventory. Zero unexplained
   differences.
4. Flip DNS. Verify HTTPS, spot-check 20 URLs including top-traffic ones.
5. Submit new sitemap in GSC; URL-inspect → Request Indexing on top ~10 pages.
6. Keep the Wix plan active a few weeks for rollback.

### 6. Watch for 4–8 weeks

GSC Coverage (a 404 spike means a URL you missed), Crawl Stats, and Performance
week-over-week. Wobble in the first 2–3 weeks is normal; a sustained drop on specific
URLs means those URLs changed or broke.

**Non-SEO gotcha:** Wix forms, bookings, and store won't survive. A contact form needs
Formspree or similar.

---

## Q2: This is the original website, can you give specific instructions for it? (https://www.jujuhung.com/)

### The finding that changes the plan

The site has **two parallel copies of the entire portfolio**, both indexable, both
self-canonical:

| Live (linked from nav) | Orphan duplicate (sitemap only) |
| --- | --- |
| `/artworks/<slug>` — 20 pages | `/artwork/<slug>` — 22 pages |
| `/exhibitions/<slug>` — 13 pages | `/exhibition/<slug>` — 12 pages |

19 artwork slugs and 10 exhibition slugs exist in **both**. `/artworks/21g` and
`/artwork/21g` are both HTTP 200, both `<meta name="robots" content="index">`, each
canonical to itself. Google picks a winner per pair, uncontrolled.

Index pages are duplicated too: `/artworks`, `/artwork`, and `/copy-of-artworks-1` all
list the identical 20 works — and the nav links to `/copy-of-artworks-1`.

**35 of 101 URLs need a 301**, which rules out plain GitHub Pages.

### Recommended stack

**Cloudflare (free) in front of GitHub Pages.** Nameservers at Cloudflare, DNS to GH
Pages, 35 redirects via **Bulk Redirects** (upload the CSV). Also provides cache-control
headers and HSTS. Cloudflare Pages or Netlify would skip a layer entirely — both support
a native `_redirects` file.

### Three site-specific landmines

**1. Every image is hotlinked from `static.wixstatic.com`.** The homepage pulls 50;
`/artworks/untamed` pulls 23. They keep working after migration — until the Wix plan is
cancelled, at which point the site goes blank. **Download every image before cancelling.**
Wix also serves them pre-resized (`/v1/fill/w_1000,h_750,...`), so responsive sizes must
be generated manually.

**2. 16 of 18 blog posts have non-ASCII URLs**, some with full-width punctuation:

```
/post/編織。重塑-weaving-memories
/post/【gq-go-green】世界海洋日與永續藝術家-julia-hung-一起從有意識減塑消費開始改變世界
/副本-infinite
```

Git and GH Pages can serve UTF-8 filenames, but `。`, `【】`, and the leading `-` in
`/artwork/-inter-symbiosis` are where static hosting breaks. **Test on day one:** commit
`post/編織。重塑-weaving-memories/index.html`, push, confirm it serves. If it fails, the
fallback is ASCII slugs + 301s for all 18 posts — a much bigger job.

**3. `/porfoliotodate`** (typo of "portfolio") returns 200 with an **empty `<title>` and
no canonical**. A blank published page. Delete or `noindex`.

### URL map summary

| Action | Count | What |
| --- | --- | --- |
| **KEEP** | 56 | Migrate 1:1, byte-identical paths: `/`, `/about`, `/contact`, `/blog`, `/blog/categories/curator-s-pick`, 18 `/post/*`, 20 `/artworks/*`, 13 `/exhibitions/*`, both live indexes |
| **301** | 35 | All `/artwork/*` → `/artworks/*`, all `/exhibition/*` → `/exhibitions/*`, `/artwork` → `/artworks`, `/exhibition` → `/exhibitions`, `/copy-of-artworks-1` → `/artworks` |
| **KEEP + 301** | 2 | `/artwork/lost-and-found`, `/artwork/wonders-and-wonderers` |
| **DECIDE** | 8 | `/portfolio`, `/single-project`, `/essence`, `/infinite`, `/color-of-water`, `/副本-infinite`, `/price-list`, `/porfoliotodate` |

Three 301s need manual handling:

- `/artwork/-inter-symbiosis` (leading hyphen) → `/artworks/inter-symbiosis`
- `/exhibition/in-the-mood-for-egg-` (trailing hyphen) → `/exhibitions/in-the-mood-for-egg`
- `/exhibition/未央夜` → `/exhibitions/whennightfalls` — **verify same exhibition first**

**KEEP + 301** explained: `/artwork/lost-and-found` and `/artwork/wonders-and-wonderers`
exist *only* on the orphan collection (`/artworks/lost-and-found` returns 404). Real
content at an about-to-be-retired URL. Rebuild both under `/artworks/`, 301 the old paths.

**DECIDE** explained: pull last-12-months clicks in GSC. Anything with traffic gets
migrated; the rest get 301'd to the nearest real page. `/price-list` should probably be
`noindex` regardless.

### Order of operations

1. **Search Console first.** Re-verify with a **DNS TXT record** now, while Wix still
   controls DNS. Then export Performance → Pages, 12 months, to settle the 8 DECIDE rows.
2. **Test the UTF-8 URL** on a throwaway GH Pages repo. Everything downstream depends on it.
3. **Scrape and archive:** all images at full resolution, plus per-page title / meta
   description / H1 / body copy / OG tags / JSON-LD. Posts carry `BlogPosting`, `Person`,
   `Organization`, `ImageObject` schema — port it; Google uses it for the artist
   knowledge panel.
4. **Build**, matching paths exactly, `dir/index.html` throughout. Preserve
   `/blog-feed.xml` (live, linked, HTTP 200) so RSS subscribers survive.
5. **Cloudflare:** nameservers → redirect list from the CSV → DNS to GH Pages IPs
   (`185.199.108–111.153`), `CNAME` file containing `www.jujuhung.com`. The apex already
   301s to www — keep it; don't switch canonical hosts during a migration.
6. **Cut over.** Verify HTTPS, spot-check 20 URLs, resubmit sitemap, request indexing for
   the top 10.
7. **Watch GSC for 8 weeks.** The duplicate cleanup hands equity from `/artwork/*` to
   `/artworks/*`. Expect 2–4 weeks of churn — that's the redirects working.

---

## Q3: Why do we need to keep the 301 redirect?

The 301s aren't for the 56 URLs that stay the same — those need nothing. They're for the
35 that stop existing. `/artwork/21g` returns 200 today; after migration it returns 404
unless something says where it went.

### What a 404 on those URLs costs

**1. Google may have indexed the singular set, not the plural one.** Both versions of
every pair are indexable and self-canonical, so Google picked a winner per pair on its
own. If it picked `/artwork/untamed`, that's the URL holding the ranking. 404 it and the
ranking is gone, not transferred.

**2. The orphan set is almost certainly older.** It has the generic Chinese meta
description (`作品`) rather than per-work descriptions, and contains two works never
copied to `/artworks/`. Older collection = what historical links point at: press
coverage, gallery pages, an old Instagram bio, a curator's bookmark. Those are the
hardest thing to rebuild in an art portfolio.

**3. A 301 passes accumulated signals to the new URL; a 404 deletes them.** The asymmetry
is the argument: a redirect rule costs one config line. A 404 on a URL that held rankings
or a backlink is permanent, and often unnoticed for months.

### When you can genuinely skip them

Settle it empirically before committing to Cloudflare:

- GSC → Performance → Pages, 12 months, filter `/artwork/` and `/exhibition/`. Zero
  clicks **and** zero impressions across all 34 means Google isn't surfacing them.
- Check external backlinks to those paths (Ahrefs free Backlink Checker, or GSC → Links
  → Top linked pages).

If both come back empty: 404 them, skip Cloudflare. Google drops dead URLs within weeks
and there's no penalty for 404ing something genuinely dead.

### The option that keeps you on plain GitHub Pages

Rebuild the 35 orphan URLs as real pages with `rel="canonical"` pointing at the live
version:

```html
<!-- artwork/21g/index.html -->
<link rel="canonical" href="https://www.jujuhung.com/artworks/21g">
```

Consolidates duplicates with no redirect capability at all — no Cloudflare, no extra
layer. Trade-offs:

- A canonical is a **hint**; Google can ignore it. A 301 is a directive.
- 35 duplicate HTML files to maintain forever, in sync, or the duplication returns.
- Does nothing for a human clicking an old link — they land on the orphan page.

Closing that last gap: add `<meta http-equiv="refresh" content="0;url=/artworks/21g">`
alongside the canonical. Google treats an instant meta refresh as a redirect; slower to
consolidate, less reliable than a real 301.

**Recommendation:** run the GSC check first. Traffic or links on those URLs → Cloudflare,
do it properly. Genuinely dead → 404 them, keep the stack simple. The canonical-tag
approach is the middle option if you want consolidation without extra infrastructure —
legitimate, just weaker.

---

## Open items

- [ ] Re-verify Search Console via DNS TXT record (do before any DNS change)
- [ ] GSC traffic check on the 34 `/artwork/*` + `/exhibition/*` URLs → decides Cloudflare vs 404
- [ ] Test UTF-8 / full-width-punctuation URL on GitHub Pages
- [ ] Confirm `/exhibition/未央夜` and `/exhibitions/whennightfalls` are the same exhibition
- [ ] Resolve the 8 DECIDE URLs from 12-month GSC click data
- [ ] Download all `static.wixstatic.com` images at full resolution before cancelling Wix

---

## Build log — 2026-09-17

The rebuild (Direction 1A "Register") is done. Two open items above are now
settled, and the redirect list has grown.

### Settled

- **`/exhibition/未央夜` and `/exhibitions/whennightfalls` are the same show.**
  The Wix CMS confirms it: the Chinese exhibition record whose slug is
  `未央夜` carries `TitleForUrl2: "whennightfalls"`. The 301 in the map is correct.
- **Images are archived.** All 333 originals pulled at full resolution
  (1.14 GB, up to 6000px) into `_archive/originals/`, which is gitignored.
  Stripping the `/v1/<transform>/` segment off a `static.wixstatic.com` URL
  returns the untouched upload. Wix can now be cancelled without losing them.

### Still open

- Search Console DNS TXT re-verification — do before any DNS change.
- GSC traffic check on the 34 `/artwork/*` + `/exhibition/*` URLs.
- UTF-8 / full-width-punctuation URL test on GitHub Pages. 18 `/post/` pages
  are built locally and serve correctly under `python3 -m http.server`;
  `。`, `【】` and `！` still need confirming on real GitHub Pages.
- The 8 DECIDE URLs.

### New: 8 redirects the redesign creates

The 1A spec cuts the works down to 14. Six existing `/artworks/` pages and the
two unique `/artwork/` orphans are no longer built. `url-map.csv` now carries
`post_redesign` and `redirect_to` columns recording where each goes; the source
of truth is `content/selection.json`, and `tools/check_urls.py` fails the build
if any other KEEP url stops resolving.

| Was | Goes to |
| --- | --- |
| `/artworks/essence` | `/artworks/artificial-phenomena/` |
| `/artworks/aquachroma` | `/artworks/an-unusual-knot/` |
| `/artworks/inter-symbiosis` | `/artworks/will-looped/` |
| `/artworks/dreamy-tide` | `/artworks/will-looped/` |
| `/artworks/biomimicry` | `/artworks/will-looped/` |
| `/artworks/gge-rof-doom-eht-ni` | `/artworks/in-the-mood-for-egg/` |
| `/artwork/lost-and-found` | `/exhibitions/the-miscellaneous-of-being-and-living/` |
| `/artwork/wonders-and-wonderers` | `/artworks/` |

That takes the redirect count from 35 to 43, which strengthens the case for
Cloudflare over plain GitHub Pages rather than weakening it.

**`/blog/categories/curator-s-pick`** is an indexed URL that the live Wix site
renders as "Posts Coming Soon" — an empty category. It is rebuilt as a thin
page carrying `noindex` and `rel=canonical` to `/blog/`, so the URL does not
404 while the signal consolidates onto the real press list.
