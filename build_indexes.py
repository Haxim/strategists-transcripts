#!/usr/bin/env python3
"""
render_index.py

Static site post-processor for The Strategists.

Inputs:
  /html/*.html   (already-rendered episode pages)

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
SITE_TAGLINE = (
    "Canada’s sharpest political insiders break down power, strategy, "
    "and the people who actually run the country."
)

EPISODES_DIR = Path("html")
OUT_DIR = Path("html")
PER_PAGE = 24
NEWEST_DIR = OUT_DIR / "newest"

# -------------------------------------------------------------------
# Regex extractors
# -------------------------------------------------------------------

TITLE_RE = re.compile(r"<title>(.*?)</title>", re.I | re.S)
DATE_RE = re.compile(r'"datePublished"\s*:\s*"([^"]+)"', re.I)
DESC_RE = re.compile(r'<meta property="og:description" content="([^"]+)"', re.I)
EP_NUM_RE = re.compile(r'"episodeNumber"\s*:\s*(\d+)', re.I)

PATREON_RE = re.compile(r"/assets/patreon\.jpg", re.I)

# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------

def extract_meta(html: str):
    title_m = TITLE_RE.search(html)
    date_m = DATE_RE.search(html)
    desc_m = DESC_RE.search(html)
    epnum_m = EP_NUM_RE.search(html)

    title = title_m.group(1).split("|")[0].strip() if title_m else "Episode"
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

        slug = path.stem
        is_patreon = bool(PATREON_RE.search(html))

        episodes.append({
            **meta,
            "url": f"/{slug}",
            "access": "patreon" if is_patreon else "public",
        })

    episodes.sort(key=lambda e: e["ts"], reverse=True)
    return episodes

# -------------------------------------------------------------------
# Index page renderer
# -------------------------------------------------------------------

def render_index_page(episodes, page, total_pages):
    is_home = page == 1

    page_title = (
        f"{SITE_NAME} – Podcast Transcripts"
        if is_home
        else f"{SITE_NAME} – Page {page} of {total_pages}"
    )

    page_desc = (
        SITE_TAGLINE
        if is_home
        else f"{SITE_NAME} podcast transcripts – page {page} of {total_pages}."
    )

    canonical = "/" if is_home else f"/page/{page}/"

    prev_link = ""
    if page > 1:
        prev_url = "/" if page == 2 else f"/page/{page-1}/"
        prev_link = f'<link rel="prev" href="{prev_url}">'

    next_link = ""
    if page < total_pages:
        next_link = f'<link rel="next" href="/page/{page+1}/">'

    hero = ""
    if is_home:
        hero = f"""
        <header class="hero hero-split layout">
          <div class="hero-text">
            <h1>{SITE_NAME}</h1>
            <p class="tagline">{SITE_TAGLINE}</p>
          </div>

          <aside class="listen-center">
            <div class="listen-label">Listen to the show</div>
            <div class="listen-links">
              <a href="https://podcasts.apple.com/ca/podcast/the-strategists/id1514440943" target="_blank" rel="noopener">Apple Podcasts</a>
              <span>·</span>
              <a href="https://open.spotify.com/show/7gx7f75pZS38AHWNFj7WGr" target="_blank" rel="noopener">Spotify</a>
              <span>·</span>
              <a href="https://www.youtube.com/@strategistspod" target="_blank" rel="noopener">YouTube</a>
            </div>
          </aside>
        </header>
        """

    cards = "\n".join(
        f"""
        <a class="card {'patreon' if ep['access']=='patreon' else ''}" href="{ep['url']}">
          <div class="thumb">
            <img src="/assets/{'patreon' if ep['access']=='patreon' else 'public'}.png"
                 alt="{ep['access']} episode"
                 loading="lazy" />
          </div>
          <div class="card-body">
            <div class="title">{ep['title']}</div>
            {f"<div class='meta'>{ep['published'][:10]}</div>" if ep['published'] else ""}
            {f"<div class='desc'>{ep['description']}</div>" if ep['description'] else ""}
          </div>
        </a>
        """.strip()
        for ep in episodes
    )

    nav = ""
    if total_pages > 1:
        newer = (
            f'<a class="newer" href="{"/" if page == 2 else f"/page/{page-1}/"}">← Newer</a>'
            if page > 1 else '<span></span>'
        )
        older = (
            f'<a class="older" href="/page/{page+1}/">Older →</a>'
            if page < total_pages else '<span></span>'
        )

        nav = f"""
        <nav class="pager layout">
          {newer}
          <div class="page-num">Page {page} of {total_pages}</div>
          {older}
        </nav>
        """

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{page_title}</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="{page_desc}">
<link rel="canonical" href="{canonical}">
{prev_link}
{next_link}

<style>
:root {{
  --orange: #d7522f;
  --navy: #232e41;
  --white: #ffffff;
}}

body {{
  font-family: Inter, system-ui, sans-serif;
  margin: 0;
  padding: 32px 0 48px;
  color: var(--white);
  background:
    radial-gradient(1200px 700px at 70% -20%, rgba(215,82,47,0.25), transparent 60%),
    radial-gradient(900px 600px at -20% 120%, rgba(35,46,65,0.6), transparent 60%),
    linear-gradient(160deg, #121826, #0b0f16);
}}

.layout {{
  max-width: 1100px;
  margin: 0 auto;
  padding: 0 clamp(16px, 3vw, 26px);
}}

.hero-split {{
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
  align-items: center;
  margin-bottom: 48px;
}}

.listen-center {{
  justify-self: center;
  text-align: center;
}}

.grid {{
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}}

@media (max-width: 860px) {{
  .hero-split,
  .grid {{
    grid-template-columns: 1fr;
  }}

  .listen-center {{
    justify-self: start;
    text-align: left;
    margin-top: 24px;
  }}
}}
</style>
</head>
<body>

{hero}

{nav}

<main class="layout">
  <div class="grid">
    {cards}
  </div>
</main>

{nav}

</body>
</html>
"""

# -------------------------------------------------------------------
# /newest page renderer (unchanged)
# -------------------------------------------------------------------

def render_newest_page(ep):
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="robots" content="noindex, nofollow">
<title>New Episode Out Now – The Strategists</title>
</head>
<body>
<h1>{ep['title']}</h1>
<p>{ep['description']}</p>
<a href="{ep['url']}">Read transcript</a>
</body>
</html>
"""

# -------------------------------------------------------------------
# Main
# -------------------------------------------------------------------

def main():
    episodes = load_episodes()
    total_pages = math.ceil(len(episodes) / PER_PAGE)

    for page in range(1, total_pages + 1):
        start = (page - 1) * PER_PAGE
        end = start + PER_PAGE

        html = render_index_page(episodes[start:end], page, total_pages)

        if page == 1:
            out = OUT_DIR / "index.html"
        else:
            out = OUT_DIR / "page" / str(page) / "index.html"
            out.parent.mkdir(parents=True, exist_ok=True)

        out.write_text(html, encoding="utf-8")

    NEWEST_DIR.mkdir(parents=True, exist_ok=True)
    (NEWEST_DIR / "index.html").write_text(
        render_newest_page(episodes[0]),
        encoding="utf-8"
    )

    print(f"✔ Wrote index ({total_pages} pages) and /newest")

if __name__ == "__main__":
    main()
