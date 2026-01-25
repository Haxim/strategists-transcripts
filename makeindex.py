#!/usr/bin/env python3
"""
render_index.py

Static site post-processor for The Strategists.

Inputs:
  /episodes/*.html   (already-rendered episode pages)

Outputs:
  /index.html
  /page/N/index.html
  /newest/index.html

No templates. No Jinja. Cloudflare-safe.
"""

from pathlib import Path
from datetime import datetime
import math
import re

# -------------------------------------------------------------------
# Config
# -------------------------------------------------------------------

SITE_NAME = "The Strategists"
EPISODES_DIR = Path("html")
OUT_DIR = Path("html")
PER_PAGE = 24
NEWEST_DIR = OUT_DIR / "newest"

# -------------------------------------------------------------------
# Regex extractors (robust against formatting changes)
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
        html = path.read_text(encoding="utf-8")
        meta = extract_meta(html)

        episodes.append({
            **meta,
            "url": f"/episodes/{path.name}",
            "path": path,
            "html": html,
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
# /newest page renderer (your design, automated)
# -------------------------------------------------------------------

def render_newest_page(ep):
    title = ep["title"]
    description = ep["description"] or "Listen to the latest episode of The Strategists."
    epnum = ep["episode_number"]

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>New Episode Out Now – The Strategists</title>

  <meta name="robots" content="noindex, nofollow" />
  <meta property="og:title" content="New Episode Out Now – The Strategists" />
  <meta property="og:description" content="Listen to the latest episode of The Strategists." />

  <style>
    :root {{
      --orange: #d7522f;
      --navy: #232e41;
      --white: #ffffff;
    }}

    body {{
      font-family: Inter, system-ui, -apple-system, sans-serif;
      background:
        radial-gradient(1200px 800px at 80% -20%, rgba(215,82,47,0.35), transparent 60%),
        radial-gradient(1000px 600px at -20% 120%, rgba(35,46,65,0.6), transparent 60%),
        linear-gradient(160deg, #121826, #0b0f16);
      color: var(--white);
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 24px;
    }}

    .card {{
      max-width: 560px;
      background: rgba(15,20,28,0.85);
      border-radius: 24px;
      padding: 40px 32px;
      box-shadow: 0 30px 80px rgba(0,0,0,0.45);
    }}

    .badge {{
      font-size: 13px;
      letter-spacing: 0.08em;
      font-weight: 600;
      color: var(--orange);
      margin-bottom: 14px;
    }}

    h1 {{
      font-size: 34px;
      line-height: 1.15;
      margin-bottom: 10px;
    }}

    .episode-number {{
      opacity: 0.8;
      margin-bottom: 18px;
    }}

    .description {{
      font-size: 16px;
      margin-bottom: 28px;
    }}

    .btn {{
      display: block;
      text-align: center;
      padding: 16px;
      border-radius: 14px;
      background: var(--orange);
      color: var(--white);
      text-decoration: none;
      font-weight: 600;
    }}

    .footer {{
      margin-top: 18px;
      text-align: center;
      font-size: 13px;
      opacity: 0.6;
    }}
  </style>
</head>
<body>

<main class="card">
  <div class="badge">NEW EPISODE OUT NOW</div>
  <h1>{title}</h1>
  {f"<div class='episode-number'>Episode {epnum}</div>" if epnum else ""}
  <p class="description">{description}</p>

  <a class="btn" href="{ep['url']}">🎧 Read transcript & listen</a>

  <div class="footer">
    <a href="/">Browse all episodes</a>
  </div>
</main>

</body>
</html>
"""


# -------------------------------------------------------------------
# Main
# -------------------------------------------------------------------

def main():
    episodes = load_episodes()
    if not episodes:
        raise SystemExit("No episodes found in /episodes")

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
    newest_html = render_newest_page(episodes[0])
    (NEWEST_DIR / "index.html").write_text(newest_html, encoding="utf-8")

    print(f"✔ Wrote index ({total_pages} pages) and /newest")


if __name__ == "__main__":
    main()
