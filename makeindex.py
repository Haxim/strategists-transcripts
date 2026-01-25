#!/usr/bin/env python3
"""
render_index.py

Static site post-processor for The Strategists.

Inputs:
  /html/*.html   (already-rendered episode pages, flat directory)

Outputs:
  /html/index.html
  /html/page/N/index.html
  /html/newest/index.html

Cloudflare Pages–safe.
Pretty URLs via _redirects rewrite.
"""

from pathlib import Path
from datetime import datetime
import math
import re

# -------------------------------------------------------------------
# Config
# -------------------------------------------------------------------

SITE_NAME = "The Strategists"
SITE_ROOT = Path("html")          # Cloudflare Pages root
EPISODES_DIR = SITE_ROOT
OUT_DIR = SITE_ROOT
PER_PAGE = 24
NEWEST_DIR = OUT_DIR / "newest"

EXCLUDE_FILES = {
    "index.html",
    "_redirects",
}

# -------------------------------------------------------------------
# Regex extractors
# -------------------------------------------------------------------

TITLE_RE = re.compile(r"<title>(.*?)</title>", re.I | re.S)
DATE_RE = re.compile(r'"datePublished"\s*:\s*"([^"]+)"', re.I)
DESC_RE = re.compile(r'<meta property="og:description" content="([^"]+)"', re.I)
EP_NUM_RE = re.compile(r'"episodeNumber"\s*:\s*(\d+)', re.I)

# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------

def extract_meta(html: str):
    title_m = TITLE_RE.search(html)
    date_m = DATE_RE.search(html)
    desc_m = DESC_RE.search(html)
    epnum_m = EP_NUM_RE.search(html)

    title = (
        title_m.group(1).split("|")[0].strip()
        if title_m else "Episode"
    )

    published = date_m.group(1) if date_m else ""
    description = desc_m.group(1).strip() if desc_m else ""
    episode_number = epnum_m.group(1) if epnum_m else ""

    try:
        ts = datetime.fromisoformat(
            published.replace("Z", "+00:00")
        ).timestamp()
    except Exception:
        ts = 0

    return {
        "title": title,
        "published": published,
        "ts": ts,
        "description": description,
        "episode_number": episode_number,
    }


def load_episodes():
    episodes = []

    for path in EPISODES_DIR.glob("*.html"):
        if path.name in EXCLUDE_FILES:
            continue
        if path.parent.name in {"page", "newest"}:
            continue

        html = path.read_text(encoding="utf-8")
        meta = extract_meta(html)

        slug = path.stem  # filename without .html

        episodes.append({
            **meta,
            "slug": slug,
            "url": f"/{slug}",   # pretty URL
            "path": path,
        })

    episodes.sort(key=lambda e: e["ts"], reverse=True)
    return episodes

# -------------------------------------------------------------------
# Index page renderer
# -------------------------------------------------------------------

def render_index_page(episodes, page, total_pages):
    cards = "\n".join(
        f"""
        <a class="card" href="{ep['url']}">
          <div class="title">{ep['title']}</div>
          {f"<div class='meta'>{ep['published'][:10]}</div>" if ep['published'] else ""}
        </a>
        """.strip()
        for ep in episodes
    )

    nav = ""
    if total_pages > 1:
        nav = '<nav class="pager">'
        if page > 1:
            nav += f'<a href="/page/{page-1}/">← Newer</a>'
        if page < total_pages:
            nav += f'<a href="/page/{page+1}/">Older →</a>'
        nav += "</nav>"

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{SITE_NAME} – Episode Transcripts</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    body {{
      font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
      background: #0b1020;
      color: #fff;
      margin: 0;
      padding: 24px;
    }}
    h1 {{ margin-bottom: 8px; }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
      gap: 16px;
      margin-top: 24px;
    }}
    .card {{
      background: rgba(255,255,255,0.06);
      border-radius: 18px;
      padding: 16px;
      text-decoration: none;
      color: inherit;
    }}
    .card:hover {{ background: rgba(255,255,255,0.1); }}
    .title {{ font-weight: 700; font-size: 17px; }}
    .meta {{ opacity: 0.65; font-size: 14px; margin-top: 6px; }}
    .pager {{
      display: flex;
      justify-content: space-between;
      margin-top: 32px;
    }}
  </style>
</head>
<body>
  <h1>{SITE_NAME}</h1>
  <div class="grid">
    {cards}
  </div>
  {nav}
</body>
</html>
"""

# -------------------------------------------------------------------
# /newest page renderer
# -------------------------------------------------------------------

def render_newest_page(ep):
    description = ep["description"] or "Listen to the latest episode of The Strategists."
    epnum = ep["episode_number"]

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>New Episode Out Now – The Strategists</title>

  <meta name="robots" content="noindex, nofollow" />

  <style>
    body {{
      font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
      background: #0b1020;
      color: #fff;
      padding: 40px;
    }}
    a {{ color: #d7522f; }}
  </style>
</head>
<body>

  <h1>{ep['title']}</h1>
  {f"<p>Episode {epnum}</p>" if epnum else ""}
  <p>{description}</p>

  <p>
    <a href="{ep['url']}">🎧 Read transcript & listen</a>
  </p>

  <p>
    <a href="/">Browse all episodes</a>
  </p>

</body>
</html>
"""

# -------------------------------------------------------------------
# Main
# -------------------------------------------------------------------

def main():
    episodes = load_episodes()
    if not episodes:
        raise SystemExit("No episodes found in /html")

    total_pages = math.ceil(len(episodes) / PER_PAGE)

    # Index + pagination
    for page in range(1, total_pages + 1):
        start = (page - 1) * PER_PAGE
        end = start + PER_PAGE

        html = render_index_page(
            episodes[start:end],
            page,
            total_pages,
        )

        if page == 1:
            out = OUT_DIR / "index.html"
        else:
            out = OUT_DIR / "page" / str(page) / "index.html"
            out.parent.mkdir(parents=True, exist_ok=True)

        out.write_text(html, encoding="utf-8")

    # Newest page
    NEWEST_DIR.mkdir(parents=True, exist_ok=True)
    (NEWEST_DIR / "index.html").write_text(
        render_newest_page(episodes[0]),
        encoding="utf-8",
    )

    print(f"✔ Wrote index ({total_pages} pages) and /newest")


if __name__ == "__main__":
    main()
