# Personal Portfolio ⚡️ 
> A clean, beautiful, responsive portfolio template for Software Developers!

> https://varadbhogayata.github.io

## Adding a post to the Writing section ✍️

**Paste a URL, press a button.** Go to **Actions → [Add writing post](../../actions/workflows/add-writing-post.yml)
→ Run workflow**, paste the LinkedIn link, and run it. That's the whole flow — the site updates itself.

The workflow fills in the rest for you:

| Field | Where it comes from |
| --- | --- |
| Date | Decoded from the post id itself — LinkedIn ids are snowflake-style, so `id >> 22` is the publish time. No network needed, always right. |
| Title & summary | LinkedIn's public `/embed/` endpoint, which serves Open Graph tags without a login. |
| Post vs. article | `og:type` on that same page. Articles get their public `/pulse/` link, which reads without a login. |
| Tags | Suggested by keyword match against the title and summary (`TAG_HINTS` in [scripts/add_post.py](./scripts/add_post.py)). |

Any of the optional inputs override what was scraped, so if LinkedIn returns a truncated title or the
auto-tags miss, fill that box in and re-run with the same URL — re-running updates the existing entry
in place rather than duplicating it, and never lets a blocked scrape overwrite values already on file.

**The newest post is automatically featured**: full width, with LinkedIn's embed open on load. Older
posts sit two-up and load their embed only when a visitor clicks, since each iframe pulls roughly a
megabyte of LinkedIn's assets. Add `"featured": false` to a post to opt it out.

### The pieces

- [assets/data/posts.json](./assets/data/posts.json) — the post list, sorted newest-first at render time.
- [scripts/add_post.py](./scripts/add_post.py) — URL → new `posts.json` entry. Also runs locally:
  `python scripts/add_post.py "<url>"`.
- [scripts/build_writing.py](./scripts/build_writing.py) — `posts.json` → static cards in `index.html`.
  `--check` verifies the two are in sync without writing.
- [add-writing-post](./.github/workflows/add-writing-post.yml) — the button described above.
- [build-writing](./.github/workflows/build-writing.yml) — re-renders `index.html` if you edit
  `posts.json` by hand and push.

Stdlib Python only, no dependencies to install. Never edit the markup between the `writing:start` /
`writing:end` markers in `index.html` — it gets overwritten.

## License 📄
This project is licensed under the MIT License - see the [LICENSE.md](./LICENSE) file for details.
