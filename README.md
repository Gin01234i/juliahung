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
index.html                     Home
artworks/                      Works index + 14 work pages
exhibitions/                   Exhibitions index + 13 exhibition pages
about/  news/  contact/        About + CV, News, Contact
blog/                          Press index
post/<slug>/                   18 press citation pages (URLs kept from Wix)
commission/                    Commission guide — unlisted, noindex
404.html  robots.txt  sitemap.xml  CNAME

assets/css/site.css            the only stylesheet — the spec, in one file
assets/js/lang.js              ~30 lines; sets data-lang, nothing else
assets/js/filter.js            works-index filter
assets/img/<kind>/<slug>/      web derivatives, 800 and 1600px, jpg + webp

content/                       authoring source (JSON) — not read at runtime
tools/                         authoring and checking scripts
seo/                           URL map and migration notes
_archive/                      full-resolution originals (gitignored)
```

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

## Bilingual

English is the default. `<html data-lang="en">` is hard-coded, and the
switching is pure CSS:

```html
<h1><span lang="en">Untamed</span><span lang="zh">「初始狀態」系列</span></h1>
```

`lang.js` only flips `data-lang` and remembers the choice. With JavaScript
disabled the page renders in English and nothing breaks. A record with no
Chinese has no `lang="zh"` span and falls back automatically.

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

1. **A portrait** for the About page — it currently falls back to an install view.
2. **`Julia_Hung_CV_2026-08.pdf`** in `assets/docs/`, then set `cv_pdf` in
   `content/cv.json`.
3. **Sign-off on the 14-work cut** in `content/selection.json`.
4. **Source URLs for the press entries** — the Wix blog reprinted articles and
   stored no link back. Fill `source_url` in `content/press.json`.
5. **Whether any work is public art** — the spec wants that filter; the CMS has
   no such field, so only Sculpture and Installation are offered.

## Not done here

The domain still points at Wix. Cutover, DNS and the 43 redirects are tracked
in [`seo/wix-to-github-pages-migration.md`](./seo/wix-to-github-pages-migration.md).
**Do not cancel the Wix plan** before that is finished — though the images are
already safe: all 333 originals are archived locally at full resolution.
