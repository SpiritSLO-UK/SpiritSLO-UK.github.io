#!/usr/bin/env python3
"""Add a LinkedIn post to assets/data/posts.json from just its URL.

    python scripts/add_post.py "https://www.linkedin.com/feed/update/urn:li:ugcPost:749...392/"

Title, summary, publish date and post type are filled in automatically:

  * The date comes out of the post id itself - LinkedIn ids are snowflake-style,
    so (id >> 22) is the publish time in milliseconds. No network needed.
  * Title and summary come from LinkedIn's public /embed/ endpoint, which serves
    Open Graph tags without a login. Best effort - if LinkedIn blocks the runner
    or changes its markup, the entry is still written and you can fill the gaps in
    by hand (or re-run with --title / --summary).

Anything passed explicitly always wins over what was scraped.
Run scripts/build_writing.py afterwards to render the cards into index.html.
"""

import argparse
import html
import json
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POSTS = ROOT / "assets" / "data" / "posts.json"

EMBED = "https://www.linkedin.com/embed/feed/update/"
# A real-ish UA: LinkedIn serves the embed to browsers and 999s obvious bots.
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)

# Suggested tags, keyed by what has to appear in the title or summary.
TAG_HINTS = {
    "AWS Control Tower": ["control tower"],
    "AFT": ["account factory", "aft"],
    "Terraform": ["terraform"],
    "Account Vending": ["account vending", "vending", "provision"],
    "Governance": ["governance", "guardrail", "scp", "policy"],
    "Landing Zone": ["landing zone"],
    "Security": ["security", "iam", "identity center", "least privilege"],
    "FinOps": ["finops", "cost", "spend", "savings"],
    # Deliberately not bare "pipeline" - that matches data pipelines too.
    "CI/CD": ["ci/cd", "cicd", "gitops", "github actions", "build pipeline", "deployment pipeline"],
    "Observability": ["observability", "monitoring", "cloudwatch", "logging"],
    "Kubernetes": ["kubernetes", "eks", "k8s"],
    "Serverless": ["serverless", "lambda"],
    "AWS": ["aws", "amazon web services"],
}


def urn_from(url):
    """Pull a urn out of any of the URL shapes LinkedIn hands out."""
    for pattern in (
        r"urn:li:(ugcPost|activity|share):(\d{10,25})",  # /feed/update/... and /embed/...
        r"-(activity)-(\d{10,25})",                      # "Copy link to post" form
    ):
        match = re.search(pattern, url)
        if match:
            return f"urn:li:{match.group(1)}:{match.group(2)}"
    bare = re.fullmatch(r"\s*(\d{15,25})\s*", url)
    if bare:
        return f"urn:li:activity:{bare.group(1)}"
    raise SystemExit(
        f"Could not find a LinkedIn post id in: {url}\n"
        "Expected something like https://www.linkedin.com/feed/update/urn:li:ugcPost:123.../ "
        "or the URL from 'Copy link to post'."
    )


def date_from(urn):
    """LinkedIn ids embed their creation time in the high bits."""
    post_id = int(urn.rsplit(":", 1)[1])
    stamp = datetime.fromtimestamp((post_id >> 22) / 1000, timezone.utc)
    if not 2010 < stamp.year < 2100:
        raise SystemExit(f"{urn} did not decode to a sensible date ({stamp.isoformat()})")
    return stamp.strftime("%Y-%m-%d")


def first(pattern, text):
    match = re.search(pattern, text, re.S | re.I)
    return html.unescape(" ".join(match.group(1).split())) if match else ""


def scrape(urn):
    """Best-effort metadata from LinkedIn's public embed page."""
    request = urllib.request.Request(EMBED + urn, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            page = response.read().decode("utf-8", "replace")
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as error:
        print(f"  ! could not read the embed page ({error}) - writing what we know", file=sys.stderr)
        return {}

    meta = {}
    is_article = first(r'property="og:type" content="([^"]*)"', page).lower() == "article"
    meta["kind"] = "LinkedIn article" if is_article else "LinkedIn post"

    # Full, untruncated title for articles; commentary text for plain posts;
    # og:title last because LinkedIn truncates it at ~70 characters.
    title = (
        first(r'data-test-id="article-content__title"[^>]*>(.*?)</span>', page)
        or first(r'data-test-id="main-feed-activity-embed-card__commentary"[^>]*>(.*?)</', page)
        or first(r'property="og:title" content="([^"]*)"', page)
    )
    title = re.sub(r"\s*\|\s*[^|]{1,60}$", "", title)       # " | Blaz Peternel"
    title = re.sub(r"^.{1,60}? on LinkedIn:\s*", "", title)  # "X on LinkedIn: ..."
    meta["title"] = title.rstrip(" .…")

    meta["summary"] = first(r'property="og:description" content="([^"]*)"', page)

    # /pulse/ links read without a login, so prefer them over /feed/update/.
    pulse = re.search(r'href="(https://www\.linkedin\.com/pulse/[^"?]+)', page)
    if pulse:
        meta["url"] = pulse.group(1)

    return {key: value for key, value in meta.items() if value}


def slug(title, taken):
    words = re.findall(r"[a-z0-9]+", title.lower())
    base = "-".join(words[:7]) or "post"
    candidate, n = base, 2
    while candidate in taken:
        candidate, n = f"{base}-{n}", n + 1
    return candidate


def suggest_tags(text):
    lowered = text.lower()
    tags = [tag for tag, hints in TAG_HINTS.items() if any(h in lowered for h in hints)]
    # Drop the generic "AWS" tag when a more specific AWS tag already matched.
    if len(tags) > 1 and "AWS" in tags:
        tags.remove("AWS")
    return tags[:5]


def main():
    parser = argparse.ArgumentParser(description="Add a LinkedIn post to posts.json")
    parser.add_argument("url", help="LinkedIn post URL (or bare post id)")
    parser.add_argument("--title", default="", help="override the scraped title")
    parser.add_argument("--summary", default="", help="override the scraped summary")
    parser.add_argument("--tags", default="", help="comma-separated; overrides the suggestions")
    parser.add_argument("--kind", default="", help='e.g. "LinkedIn article"')
    parser.add_argument("--date", default="", help="YYYY-MM-DD; overrides the id-derived date")
    parser.add_argument("--no-fetch", action="store_true", help="skip LinkedIn, use flags only")
    args = parser.parse_args()

    urn = urn_from(args.url)
    print(f"  post   {urn}")

    found = {} if args.no_fetch else scrape(urn)

    # Explicit flags beat anything scraped.
    for key, value in (
        ("title", args.title),
        ("summary", args.summary),
        ("kind", args.kind),
        ("date", args.date),
    ):
        if value:
            found[key] = value

    data = json.loads(POSTS.read_text(encoding="utf-8"))
    posts = data["posts"]
    existing = next((p for p in posts if p.get("urn") == urn), None)

    # Re-running a URL must never downgrade an entry that is already good: start
    # from what is on file and only let non-empty values overwrite it. Otherwise a
    # blocked scrape would replace a real title with a placeholder and publish it.
    entry = dict(existing) if existing else {}
    entry.update({key: value for key, value in found.items() if value})

    entry["urn"] = urn
    entry.setdefault("url", f"https://www.linkedin.com/feed/update/{urn}/")
    entry.setdefault("kind", "LinkedIn post")
    entry.setdefault("date", date_from(urn))
    entry.setdefault("title", f"LinkedIn post, {entry['date']}")
    entry.setdefault("summary", "")

    if args.tags:
        entry["tags"] = [t.strip() for t in args.tags.split(",") if t.strip()]
    elif not entry.get("tags"):
        entry["tags"] = suggest_tags(f"{entry['title']} {entry['summary']}")

    if existing:
        entry.setdefault("id", slug(entry["title"], set()))
        posts[posts.index(existing)] = entry
        kept = [k for k in ("title", "summary", "tags") if existing.get(k) and k not in found]
        print("  note   already listed - refreshed in place"
              + (f", kept existing {', '.join(kept)}" if kept else ""))
    else:
        entry["id"] = slug(entry["title"], {p.get("id") for p in posts})
        posts.insert(0, entry)

    # Keep a stable key order so diffs stay readable.
    order = ["id", "title", "summary", "date", "kind", "url", "urn", "tags"]
    data["posts"] = [
        {key: post[key] for key in order if key in post} | {k: v for k, v in post.items() if k not in order}
        for post in posts
    ]

    POSTS.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"  title  {entry['title']}")
    print(f"  date   {entry['date']} ({entry['kind']})")
    print(f"  tags   {', '.join(entry['tags']) or '(none)'}")
    if not entry["summary"]:
        print("  ! no summary found - add one to posts.json when you get a chance", file=sys.stderr)
    print(f"\nWrote {POSTS.relative_to(ROOT)}. Now run: python scripts/build_writing.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
