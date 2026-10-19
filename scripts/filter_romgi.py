"""Build romdb.db.gz + version.json for Onion from the romgi catalog.

Usage: python scripts/filter_romgi.py [romdb.db.gz] [out_dir]
  No path: downloads romgi's db from GitHub. Output defaults to the repo root.

Keeps only the platforms Onion emulates (keep in sync with
Onion/src/romDownloader/platforms.h), drops the FTS table (unused by the
Onion app) and VACUUMs. Schema stays romgi v4.
"""
import datetime
import gzip
import json
import os
import shutil
import sqlite3
import sys
import tempfile
import urllib.request

ROMGI = "https://raw.githubusercontent.com/caprado/romgi/main/db"
KEEP = ["nes", "fds", "snes", "gb", "gbc", "gba", "vb", "min", "nds", "smd", "sms", "gg", "32x",
        "scd", "ps1", "a26", "a52", "a78", "lynx", "cv", "intv", "tg16", "tgcd", "ngcd"]
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")


def upstream_version(src):
    """romgi's version string: from version.json next to a local db, else from GitHub."""
    local = os.path.join(os.path.dirname(os.path.abspath(src)), "version.json")
    if os.path.exists(local):
        with open(local, encoding="utf-8") as f:
            return json.load(f)["version"]
    with urllib.request.urlopen(f"{ROMGI}/version.json", timeout=60) as r:
        return json.load(r)["version"]


def main():
    out = sys.argv[2] if len(sys.argv) > 2 else ROOT
    tmp = tempfile.mkdtemp()
    if len(sys.argv) > 1:
        src = sys.argv[1]
    else:
        src = os.path.join(tmp, "romdb.db.gz")
        print("downloading", f"{ROMGI}/romdb.db.gz")
        urllib.request.urlretrieve(f"{ROMGI}/romdb.db.gz", src)
    version = upstream_version(src)

    work = os.path.join(tmp, "romdb.db")
    opener = gzip.open if src.endswith(".gz") else open
    with opener(src, "rb") as s, open(work, "wb") as d:
        shutil.copyfileobj(s, d)

    db = sqlite3.connect(work)
    marks = ",".join("?" * len(KEEP))
    db.execute(f"CREATE TEMP TABLE gone AS SELECT slug FROM entries WHERE platform NOT IN ({marks})", KEEP)
    db.execute("DELETE FROM links WHERE entry IN (SELECT slug FROM gone)")
    db.execute("DELETE FROM regions_entries WHERE entry IN (SELECT slug FROM gone)")
    db.execute("DELETE FROM entry_group_members WHERE entry IN (SELECT slug FROM gone)")
    db.execute("DELETE FROM entries WHERE slug IN (SELECT slug FROM gone)")
    db.execute("DELETE FROM entry_groups WHERE id NOT IN (SELECT group_id FROM entry_group_members)")
    db.execute(f"DELETE FROM platforms WHERE id NOT IN ({marks})", KEEP)
    db.execute("DELETE FROM torrents WHERE infohash NOT IN "
               "(SELECT DISTINCT torrent_infohash FROM links WHERE torrent_infohash IS NOT NULL)")
    db.execute("DROP TABLE IF EXISTS entries_fts")
    db.commit()
    db.execute("VACUUM")
    counts = {t: db.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
              for t in ("entries", "links", "platforms", "sources")}
    db.close()

    gz = os.path.join(out, "romdb.db.gz")
    with open(work, "rb") as s, gzip.open(gz, "wb", compresslevel=9) as d:
        shutil.copyfileobj(s, d)
    now = datetime.datetime.now(datetime.timezone.utc)
    meta = {
        "version": version,
        "generated_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "schema_version": 4,
        "size": os.path.getsize(gz),
        "uncompressed_size": os.path.getsize(work),
        **counts,
    }
    with open(os.path.join(out, "version.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(meta, f, indent=2)
        f.write("\n")
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"OK {version}: {counts['entries']} entries, {counts['links']} links, "
          f"{counts['platforms']} platforms -> {gz} ({meta['size'] // 1024 // 1024} MB)")


if __name__ == "__main__":
    main()
