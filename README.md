# jujuhung.com

Static site for Julia Hung 洪郁雯. Plain HTML and CSS — no build step, no
dependencies, no framework. Deploys to GitHub Pages by pushing.

Built to the **Direction 1A "Register"** specification: text-first, one ink on
one paper, no accent colour, no dark mode, and no motion except colour. The
work is the only saturated thing on the page.

## Running it

```bash
python3 -m http.server 8000     # then open http://localhost:8000
```

That is the whole toolchain. The repo root *is* the site.

## Layout

```
index.html                     Home — Direction 1A "Register"
stage/                         Home, alternative — "Stage", one work at a time
artworks/                      Works index + 14 work pages
exhibitions/                   Exhibitions index + 13 exhibition pages
about/  news/  contact/        About + CV, News, Contact
blog/                          Press index
post/<slug>/                   18 press citation pages (URLs kept from Wix)
commission/                    Commission guide — unlisted, noindex
404.html  robots.txt  sitemap.xml  CNAME

assets/css/site.css            the stylesheet — the spec, in one file
assets/css/stage.css           the alternative home only; loaded by nothing else
assets/js/filter.js            works-index filter
assets/img/<kind>/<slug>/      web derivatives, 800 and 1600px, jpg + webp

content/                       authoring source (JSON) — not read at runtime
tools/                         authoring and checking scripts
seo/                           URL map and migration notes
_archive/                      full-resolution originals (gitignored)
```

## Two home pages

There are two directions for the home page, and a switch in the bottom-right
corner of each moves between them:

- `/` — **Register.** The 1A spec: recent exhibition, statement, news.
- `/stage/` — **Stage.** One exhibition or work, full bleed, the header and
  the caption laid over the picture. No statement, no news. It is `noindex`
  and canonicals to `/`, so it does not compete with the home page in search.

Stage is deliberately quarantined: its own stylesheet, its own overlaid
header, nothing shared but the image derivatives. To change what it shows,
edit the one block in `stage/index.html` marked `THE FEATURE` — picture,
label, titles, where-and-when line, link, credit. Nothing else on that page
is specific to what is featured.

When a direction is chosen, the loser and the switch both go: the switch is
the `<nav class="switch">` on both pages, the block at the foot of
`site.css`, and the block at the foot of `stage.css`. If Stage wins, move
`stage/index.html` to the root and drop its `noindex`.

## Editing

**By hand.** Open the `index.html` you want and edit it. Nothing will overwrite
it unless you rerun `tools/stamp.py`. If you touch the header or nav, read
[`PARTIALS.md`](./PARTIALS.md) first — the header is byte-identical across all
55 pages so that one `sed` can update them all, and `tools/check_site.py`
fails if that drifts.

**Through the content files.** `content/*.json` holds the records the pages
were stamped from. Edit those and run `python3 tools/stamp.py` to rewrite the
repetitive pages. Useful for a batch change; unnecessary for a one-off fix.

The two places worth knowing:

- `content/selection.json` — which 14 works are featured, how they are
  categorised, and where the dropped ones should redirect.
- `content/cv.json`, `content/news.json`, `content/contact.json` — the
  hand-written copy.

## Language

The site is English only. `content/*.json` still carries the Chinese fields
(`title_zh`, `statement_zh`, `text_zh`, …) from the Wix export; `stamp.py`
ignores them. The press pages are the one exception, and not a translation:
articles published in Chinese keep their own titles and summaries, because
that is what those articles are called.

## Checks

```bash
python3 tools/check_site.py     # links, header drift, Wix refs, alt text
python3 tools/check_urls.py     # every KEEP url in seo/url-map.csv resolves
```

Run both before pushing. `check_urls.py` needs the local server running.

## Tools

None of these are needed to serve or edit the site.

| Script | What it does |
| --- | --- |
| `scrape.py` | Archives the live Wix pages to `_archive/html/` |
| `extract_cms.py` | Pulls the embedded Wix CMS records out of that HTML |
| `normalize.py` | Joins the EN and 中文 collections into `content/works/` etc. |
| `fetch_media.py` | Downloads all 333 originals at full resolution |
| `derive.py` | Makes the 800/1600px jpg + webp derivatives |
| `stamp.py` | Writes the repetitive pages from `content/` |
| `check_site.py`, `check_urls.py` | The checks above |

The scrape and fetch steps are done; they exist so the archive is reproducible,
not because they need rerunning.

## Still needed from Julia

1. **Sign-off on the 14-work cut** in `content/selection.json`.
2. **Source URLs for the press entries** — the Wix blog reprinted articles and
   stored no link back. Fill `source_url` in `content/press.json`.
3. **Whether any work is public art** — the spec wants that filter; the CMS has
   no such field, so only Sculpture and Installation are offered.
4. **A lighter Selected Press PDF.** `assets/docs/Julia_Hung_Selected_Press_2026-09.pdf`
   is the file from the old site, 42 MB for 29 pages. It works, but it is the
   heaviest thing in the repo by far.

## Not done here

The domain still points at Wix. Cutover, DNS and the 43 redirects are tracked
in [`seo/wix-to-github-pages-migration.md`](./seo/wix-to-github-pages-migration.md).
**Do not cancel the Wix plan** before that is finished — though the images are
already safe: all 333 originals are archived locally at full resolution.
