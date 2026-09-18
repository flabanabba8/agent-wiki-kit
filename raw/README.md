# raw/ — primary sources (not distributed)

Every claim in `wiki/` traces to a file that belongs in this folder: official documentation,
vendor docs, engineering posts and research papers. Those are other people's copyrighted text, so
this repository does not redistribute them. Everything in `raw/` except this file is gitignored.

Rebuild the folder locally:

```bash
./scripts/sources.py fetch     # download everything listed in sources/manifest.tsv
./scripts/sources.py status    # present, missing, or different from the verified snapshot
```

`sources/manifest.tsv` records each file's origin and a hash of its content when the wiki was last
verified against it. A fetched file that differs is not an error. It means upstream changed after the
page was checked, and `./scripts/freshness.py` lists the pages that cite it.

Rules for this folder: never edit an existing source, only add new ones, and give each a first-line
header such as `<!-- SOURCE: <url> | fetched: <date> -->`. The licenses of the fetched material are
those of its publishers, not this repository's MIT license.
