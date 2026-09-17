# Partials

Every page carries the same header markup. Nothing enforces that at runtime —
the site is plain static HTML — so this file is the reference copy. If you
change the navigation, change it here and in every page, or rerun
`python3 tools/stamp.py`.

`tools/check_site.py` fails if any page's header drifts from the others, which
is the practical safety net.

## Header

Two variants are intentional and only these two:

1. The current page's nav link carries `aria-current="page"`.
2. The home page adds `<span class="hdr__mark-zh">洪郁雯</span>` inside the wordmark.

```html
<header class="hdr">
  <a class="hdr__mark" href="/">Julia Hung</a>
  <nav class="hdr__nav t-meta" aria-label="Main">
    <a href="/artworks/"><span lang="en">Works</span><span lang="zh">作品</span></a>
    <a href="/exhibitions/"><span lang="en">Exhibitions</span><span lang="zh">展覽</span></a>
    <a href="/news/"><span lang="en">News</span><span lang="zh">消息</span></a>
    <a href="/blog/"><span lang="en">Press</span><span lang="zh">媒體</span></a>
    <a href="/about/"><span lang="en">About</span><span lang="zh">關於</span></a>
    <a href="/contact/"><span lang="en">Contact</span><span lang="zh">聯絡</span></a>
    <span class="hdr__lang" role="group" aria-label="Language">
      <button type="button" data-set-lang="en" aria-pressed="true">EN</button>
      <span aria-hidden="true">/</span>
      <button type="button" data-set-lang="zh" aria-pressed="false">中文</button>
    </span>
  </nav>
</header>
```

## Changing the navigation by hand

Add a link to every page in one pass:

```bash
# from the repo root
grep -rl '<nav class="hdr__nav' --include=index.html . | \
  xargs sed -i '' 's|<a href="/about/">|<a href="/new-page/">New</a>\n    <a href="/about/">|'
python3 tools/check_site.py     # confirms all 55 headers still match
```

The `sed` only works because the header is byte-identical everywhere. Keep it
that way.

## Closing markup

Every page ends the same way:

```html
</div>
<script src="/assets/js/lang.js" defer></script>
</body>
</html>
```

There is no footer. The spec removes it: "Nothing else, no footer nav."
