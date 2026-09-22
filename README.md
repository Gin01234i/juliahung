# jujuhung.com

Static site for Julia Hung 洪郁雯. Plain HTML and CSS — no build step, no
dependencies, no framework. Deploys to GitHub Pages by pushing.

For a beginner-friendly editing, preview, and publishing workflow, see
[`DEVELOPING_WITH_CODEX.md`](./DEVELOPING_WITH_CODEX.md).


## Running it

```bash
python3 -m http.server 8000     # then open http://localhost:8000
```

That is the whole toolchain. The repo root *is* the site.

## Two addresses

The site has to serve from two roots at once:

- `https://<user>.github.io/juliahung/` — the review copy, on a project path
- `https://jujuhung.com/` — the live site, at the domain root

So no page links to `/assets/css/site.css`: under the project path that
resolves to github.io's own root and 404s. Every internal path is relative to
the page holding it — `../../assets/css/site.css` two directories down,
`assets/css/site.css` at the root — which is correct under both, with no build
step, no `<base>` tag and no JavaScript.

```bash
python3 tools/relativize.py --check    # nothing root-absolute has crept back in
```

`tools/stamp.py` writes root-absolute paths and relativizes on the way out, so
the source stays readable. Paste a `/`-rooted path into a page by hand and
rerun `tools/relativize.py`; it rewrites in place and is safe to run twice.

Absolute `https://www.jujuhung.com/…` URLs are *not* rewritten, on purpose:
`canonical`, `og:url`, `og:image`, the JSON-LD and `sitemap.xml` name the
production page. That is also what keeps the review copy out of search —
every page on github.io canonicals to the domain.

`404.html` is the exception. GitHub Pages serves it for any missing path, so
"relative" there means whatever the visitor typed; it resolves the site root
in a three-line inline script instead — one path segment on a `github.io`
host, `/` everywhere else. Editing its header is a separate step; see
[`PARTIALS.md`](./PARTIALS.md).

### Going live

Nothing in the tree needs changing. Put the custom domain back (a `CNAME`
file holding `jujuhung.com`, or the Pages setting), and the same relative
paths keep working at the root.

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
404.html  robots.txt  sitemap.xml

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
[`PARTIALS.md`](./PARTIALS.md) first — the header is identical across all 55
pages but for its `../` depth, so that one `sed` can update them all, and
`tools/check_site.py` fails if that drifts.

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
| `relativize.py` | Makes every internal path relative to its page |
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
