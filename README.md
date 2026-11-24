# Personal Portfolio ⚡️ 
> A clean, beautiful, responsive portfolio template for Software Developers!

> https://varadbhogayata.github.io

## What's on the page

Everything lives in one page, [index.html](./index.html), served at [peternel.me](https://peternel.me). Sections, in order:

| Section | What it holds |
| --- | --- |
| Intro | Name, current title (rotating via typed.js) and a two-line summary |
| About | Three short paragraphs: current role, background, how I work |
| Leadership | An impact strip of six headline numbers, then cards on people and hiring, roadmap and budget, planning, incidents, review standards and written decisions |
| Experience | Roles newest first. A company with more than one role lists each role with its own dates (`role-step`) |
| Projects | Two-up cards, each with a status line (in production, proof of concept, design stage) and a stack line; personal projects last |
| Skills | Tag groups, ending with leadership and ways of working |
| Writing | Generated from `posts.json`, see below |
| Education & Certification | School and certification |
| Contact | Email and LinkedIn |

When editing, keep the status lines and the "estimated" or "projected" wording accurate; every figure on the
page should be one I can source. Client names, account IDs and internal repository names stay off the site.

The Resume buttons link to [assets/resume/Blaz_Peternel_Resume.pdf](./assets/resume/Blaz_Peternel_Resume.pdf).
Replace that file in place to update it; the links don't change.

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
