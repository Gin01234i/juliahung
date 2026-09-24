# jujuhung.com

Static site for Julia Hung 洪郁雯. Plain HTML and CSS — no build step, no
dependencies, no framework. Deploys to GitHub Pages by pushing.

For a beginner-friendly editing, preview, and publishing workflow on macOS
using the Codex desktop app — including first-time setup of Git, Python and
GitHub access — see [`DEVELOPING_WITH_CODEX.md`](./DEVELOPING_WITH_CODEX.md).


## Running it

```bash
./start-local-server.command   # opens http://localhost:8000 automatically
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

Paste a `/`-rooted path into a page by hand and rerun `tools/relativize.py`;
it rewrites in place, is safe to run twice, and `--check` fails the build if
one has crept back in.

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
index.html                     Home — "Stage", one work at a time
artworks/                      Works index + 20 work pages
exhibitions/                   Exhibitions index + 13 exhibition pages
about/  news/  contact/        About + CV, News, Contact
blog/                          Press index
post/<slug>/                   3 press pages (URLs kept from Wix); the other
                               15 entries link straight to the publisher
commission/                    Commission guide — unlisted, noindex
404.html  robots.txt  sitemap.xml

assets/css/site.css            the stylesheet — the spec, in one file
assets/css/stage.css           the Stage home only; loaded by nothing else
assets/js/filter.js            works and exhibitions index filters
assets/js/contact.js           composes the contact form's mailto:
assets/img/<kind>/<slug>/      web derivatives, 800 and 1600px, jpg + webp

content/                       Wix-era records (JSON) — reference, not source
tools/                         the checks, plus derive.py for new images
seo/                           URL map and migration notes
_archive/                      full-resolution originals (gitignored)
```

## Home page

The home page uses **Stage**: one exhibition or work, full bleed, with the
header and caption laid over the picture. It uses `assets/css/stage.css`.
To change the feature, edit the block in `index.html` marked `THE FEATURE`
— picture, label, titles, where-and-when line, link, and credit.

## Editing

Open the `index.html` you want and edit it. The committed HTML *is* the
source — there is no generator behind it and nothing will overwrite what you
write. If you touch the header or nav, read [`PARTIALS.md`](./PARTIALS.md)
first — the header is identical across all 45 pages but for its `../` depth,
so that one `sed` can update them all, and `tools/check_site.py` fails if that
drifts.

A page generator, `tools/stamp.py`, wrote these pages once from `content/`.
It was removed after the pages were edited past what it could reproduce:
re-running it would have restored worse meta descriptions, a mangled heading
and an old typo over the fixes made since. It is in the git history if the
templates are ever wanted for reference —
`git log --diff-filter=D -- tools/stamp.py`.

What is left in `content/` is therefore reference data, not source, with two
exceptions `tools/derive.py` still reads: `content/selection.json` (the 20
works, their display order and categories) and the per-record files under
`content/works/` and `content/exhibitions/`.

## Language

The site is English only. `content/*.json` still carries the Chinese fields
(`title_zh`, `statement_zh`, `text_zh`, …) from the Wix export; no page
uses them. The press pages are the one exception, and not a translation:
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
| `derive.py` | Makes the 800/1600px jpg + webp derivatives. Needs Pillow |
| `relativize.py` | Makes every internal path relative to its page |
| `gen_redirects.py` | Writes `_redirects` from `seo/url-map.csv`. Only useful if the site ends up behind Cloudflare or on Netlify — GitHub Pages ignores the file |
| `check_site.py`, `check_urls.py` | The checks above |

The migration scripts that pulled the site off Wix — `scrape.py`,
`extract_cms.py`, `normalize.py`, `fetch_media.py` — were removed once the
archive was complete. They are in the git history if the chain ever has to run
again; `git log --diff-filter=D -- tools/` finds the commit. With
`normalize.py` gone, `content/cms/` (the raw Wix collections) is read by
nothing and is kept only as the record the normalised files came from.

## Still needed from Julia

1. **Whether any work is public art** — the spec wants that filter; the CMS has
   no such field, so only Sculpture and Installation are offered.
2. **A lighter Selected Press PDF.** `assets/docs/Julia_Hung_Selected_Press_2026-09.pdf`
   is the file from the old site, 42 MB for 29 pages. It works, but it is the
   heaviest thing in the repo by far.

## Not done here

The domain still points at Wix. Cutover, DNS and the 43 redirects are tracked
in [`seo/wix-to-github-pages-migration.md`](./seo/wix-to-github-pages-migration.md).
**Do not cancel the Wix plan** before that is finished — though the images are
already safe: all 333 originals are archived locally at full resolution.
