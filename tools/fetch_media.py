#!/usr/bin/env python3
"""Download every CMS image at full resolution, before the Wix plan lapses.

Stripping the /v1/<transform>/ segment off a static.wixstatic.com URL returns
the untouched upload — typically 6000px+ and several MB. These files are the
one irreplaceable asset in the migration, so archive all of them regardless of
which make the final cut.

Writes _archive/originals/<media-id> and _archive/originals/_manifest.json.
Resumable: existing non-empty files are skipped.

Usage:  python3 tools/fetch_media.py [--workers N]
"""
import glob, json, os, sys, threading, time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEST = os.path.join(ROOT, "_archive", "originals")
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"}

lock = threading.Lock()
done = {"n": 0, "bytes": 0, "fail": []}


def inventory():
    """Every media id referenced by any normalised record, with its owner."""
    owners = {}
    for f in sorted(glob.glob(os.path.join(ROOT, "content", "*", "*.json"))):
        base = os.path.basename(f)
        if base.startswith("_"):
            continue
        kind = os.path.basename(os.path.dirname(f))
        if kind not in ("works", "exhibitions"):
            continue
        rec = json.load(open(f, encoding="utf-8"))
        for key in ("images", "images_zh"):
            for img in rec.get(key) or []:
                owners.setdefault(img["media"], []).append(f"{kind}/{rec['slug']}")
    return owners


def grab(mid, total):
    path = os.path.join(DEST, mid)
    if os.path.exists(path) and os.path.getsize(path) > 0:
        with lock:
            done["n"] += 1
        return
    url = f"https://static.wixstatic.com/media/{mid}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=90) as r:
                body = r.read()
            tmp = path + ".part"
            with open(tmp, "wb") as fh:
                fh.write(body)
            os.replace(tmp, path)
            with lock:
                done["n"] += 1
                done["bytes"] += len(body)
                print(f"[{done['n']:3}/{total}] {mid[:44]:46} "
                      f"{len(body) // 1024:6}kB", flush=True)
            return
        except Exception as e:
            if attempt == 2:
                with lock:
                    done["n"] += 1
                    done["fail"].append((mid, str(e)))
                    print(f"[{done['n']:3}/{total}] FAIL {mid}: {e}", flush=True)
            else:
                time.sleep(2 * (attempt + 1))


def main():
    workers = 6
    if "--workers" in sys.argv:
        workers = int(sys.argv[sys.argv.index("--workers") + 1])
    os.makedirs(DEST, exist_ok=True)

    owners = inventory()
    ids = sorted(owners)
    print(f"{len(ids)} unique media ids, {workers} workers")

    with ThreadPoolExecutor(max_workers=workers) as pool:
        for mid in ids:
            pool.submit(grab, mid, len(ids))

    manifest = {mid: {"owners": sorted(set(o)),
                      "bytes": os.path.getsize(os.path.join(DEST, mid))
                      if os.path.exists(os.path.join(DEST, mid)) else 0}
                for mid, o in owners.items()}
    with open(os.path.join(DEST, "_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    ok = sum(1 for v in manifest.values() if v["bytes"] > 0)
    print(f"\n{ok}/{len(ids)} archived, {done['bytes'] / 1e9:.2f} GB downloaded")
    for mid, err in done["fail"]:
        print(f"  FAILED {mid}: {err}")


if __name__ == "__main__":
    main()
