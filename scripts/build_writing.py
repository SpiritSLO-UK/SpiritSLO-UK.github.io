#!/usr/bin/env python3
"""Render the Writing section of index.html from assets/data/posts.json.

Usage:
    python scripts/build_writing.py          # rewrite index.html in place
    python scripts/build_writing.py --check  # exit 1 if index.html is stale

Everything between the writing:start and writing:end markers in index.html is
generated. Edit assets/data/posts.json, never the markup between the markers.
"""

import argparse
import html
import json
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POSTS = ROOT / "assets" / "data" / "posts.json"
INDEX = ROOT / "index.html"

START = "<!-- writing:start"
END = "<!-- writing:end -->"

# Matches the whole generated block, including the start marker's own comment.
BLOCK = re.compile(
    r"([ \t]*)" + re.escape(START) + r".*?-->\n.*?[ \t]*" + re.escape(END),
    re.DOTALL,
)

REQUIRED = ("id", "title", "summary", "date", "url")


def esc(value):
    return html.escape(str(value), quote=True)


def pretty_date(iso):
    return datetime.strptime(iso, "%Y-%m-%d").strftime("%d %B %Y").lstrip("0")


def load_posts():
    data = json.loads(POSTS.read_text(encoding="utf-8"))
    posts = data["posts"]
    for post in posts:
        missing = [key for key in REQUIRED if not post.get(key)]
        if missing:
            raise SystemExit(f"posts.json: entry {post.get('id', '?')} is missing {missing}")
        pretty_date(post["date"])  # fail loudly on a bad date rather than at render time
    # Newest first, so the file order does not have to be maintained by hand.
    return sorted(posts, key=lambda post: post["date"], reverse=True)


def render_card(post, indent):
    pad = " " * indent
    lines = [
        f'{pad}<div class="col s12 m12 l6">',
        f'{pad}  <article class="card writing-card">',
        f'{pad}    <div class="card-content">',
        f'{pad}      <div class="post-meta brown-text text-darken-2">'
        f'{esc(post.get("kind", "LinkedIn post"))} &middot; '
        f'<time datetime="{esc(post["date"])}">{esc(pretty_date(post["date"]))}</time></div>',
        f'{pad}      <h3 class="card-title">',
        f'{pad}        <a class="teal-text hoverline" href="{esc(post["url"])}" target="_blank"'
        f' rel="noopener">{esc(post["title"])}</a>',
        f"{pad}      </h3>",
        f'{pad}      <p class="brown-text">{esc(post["summary"])}</p>',
    ]

    tags = post.get("tags") or []
    if tags:
        lines.append(f'{pad}      <div class="skill-tags post-tags">')
        lines += [f"{pad}        <span>{esc(tag)}</span>" for tag in tags]
        lines.append(f"{pad}      </div>")

    lines.append(f"{pad}    </div>")
    lines.append(f'{pad}    <div class="card-action">')
    lines.append(
        f'{pad}      <a href="{esc(post["url"])}" target="_blank" rel="noopener"'
        f' aria-label="Read &quot;{esc(post["title"])}&quot; on LinkedIn">Read on LinkedIn</a>'
    )

    if post.get("urn"):
        embed = f"https://www.linkedin.com/embed/feed/update/{post['urn']}"
        lines += [
            f'{pad}      <button type="button" class="embed-toggle teal-text"'
            f' data-embed="{esc(embed)}" data-title="{esc(post["title"])}"'
            f' aria-expanded="false">Show post here</button>',
            f'{pad}      <div class="li-embed" hidden></div>',
        ]

    lines.append(f"{pad}    </div>")
    lines.append(f"{pad}  </article>")
    lines.append(f"{pad}</div>")
    return "\n".join(lines)


def render_block(posts, indent):
    pad = " " * indent
    body = "\n".join(render_card(post, indent + 2) for post in posts)
    return (
        f"{pad}{START} - generated from assets/data/posts.json by"
        f" scripts/build_writing.py, do not edit by hand -->\n"
        f'{pad}<div class="row">\n'
        f"{body}\n"
        f"{pad}</div>\n"
        f"{pad}{END}"
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="verify index.html is up to date")
    args = parser.parse_args()

    posts = load_posts()
    source = INDEX.read_text(encoding="utf-8")

    match = BLOCK.search(source)
    if not match:
        raise SystemExit(f"index.html: could not find the {START} ... {END} markers")

    updated = source[: match.start()] + render_block(posts, len(match.group(1))) + source[match.end() :]

    if args.check:
        if updated != source:
            print("index.html is out of date - run: python scripts/build_writing.py")
            return 1
        print(f"index.html is up to date ({len(posts)} post(s))")
        return 0

    if updated == source:
        print(f"index.html already up to date ({len(posts)} post(s))")
        return 0

    INDEX.write_text(updated, encoding="utf-8")
    print(f"index.html updated ({len(posts)} post(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
