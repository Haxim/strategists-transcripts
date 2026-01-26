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
<header class="hero">
  <div class="hero-grid">
    <div class="hero-text">
      <h1>{SITE_NAME}</h1>
      <p class="tagline">{SITE_TAGLINE}</p>
    </div>

    <aside class="listen-on">
      <div class="listen-label">Listen to the show</div>
      <div class="listen-links">
        <a href="https://podcasts.apple.com/ca/podcast/the-strategists/id1514440943" target="_blank" rel="noopener">Apple Podcasts</a>
        <span>·</span>
        <a href="https://open.spotify.com/show/7gx7f75pZS38AHWNFj7WGr" target="_blank" rel="noopener">Spotify</a>
        <span>·</span>
        <a href="https://www.youtube.com/@strategistspod" target="_blank" rel="noopener">YouTube</a>
      </div>
    </aside>
  </div>
</header>
""".strip()

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
<nav class="pager">
  {newer}
  <div class="page-num">Page {page} of {total_pages}</div>
  {older}
</nav>
""".strip()

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

* {{ box-sizing: border-box; }}

body {{
  font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
  margin: 0;
  padding: 32px 24px 48px;
  color: var(--white);
  background:
    radial-gradient(1200px 700px at 70% -20%, rgba(215,82,47,0.25), transparent 60%),
    radial-gradient(900px 600px at -20% 120%, rgba(35,46,65,0.6), transparent 60%),
    linear-gradient(160deg, #121826, #0b0f16);
}}

.hero {{ margin-bottom: 48px; }}

.hero-grid {{
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}}

.hero-text {{
  justify-self: start;
  padding-left: clamp(4px, 1vw, 18px);
}}

.listen-on {{
  justify-self: start;
  width: 100%;
  text-align: center;
  align-self: center;
}}

@media (max-width: 860px) {{
  .hero-grid {{ grid-template-columns: 1fr; }}
  .listen-on {{ margin-top: 24px; text-align: left; }}
}}

.hero h1 {{
  font-size: 44px;
  margin-bottom: 12px;
  letter-spacing: -0.02em;
}}

.tagline {{
  font-size: 18px;
  line-height: 1.5;
  opacity: 0.85;
  max-width: 720px;
}}

.listen-label {{
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 10px;
  opacity: 0.9;
}}

.listen-links {{
  font-size: 16px;
  opacity: 0.8;
}}

.listen-links a {{
  color: var(--orange);
  font-weight: 600;
  text-decoration: none;
}}

.listen-links a:hover {{ text-decoration: underline; }}

.grid {{
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}}

@media (max-width: 720px) {{
  .grid {{ grid-template-columns: 1fr; }}
}}

.card {{
  display: flex;
  gap: 14px;
  background: rgba(255,255,255,0.06);
  border-radius: 18px;
  padding: 18px;
  color: inherit;
  text-decoration: none;
}}

.card:hover {{
  background: rgba(255,255,255,0.1);
  transform: translateY(-2px);
}}

.card.patreon {{
  box-shadow: 0 0 0 1px rgba(215,82,47,0.35),
              0 0 18px rgba(215,82,47,0.15);
}}

.thumb {{
  width: 64px;
  height: 64px;
  border-radius: 12px;
  overflow: hidden;
}}

.thumb img {{
  width: 100%;
  height: 100%;
  object-fit: cover;
}}

.title {{ font-weight: 700; font-size: 17px; }}
.meta {{ opacity: 0.6; font-size: 14px; margin-top: 6px; }}
.desc {{
  margin-top: 10px;
  font-size: 14px;
  line-height: 1.45;
  opacity: 0.75;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}}

.pager {{
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  margin: 48px 0;
}}

.page-num {{ opacity: 0.6; text-align: center; }}

.site-footer {{
  margin-top: 64px;
  text-align: center;
  font-size: 13px;
  opacity: 0.55;
}}
</style>
</head>
<body>

{hero}

{nav}

<main class="grid">
{cards}
</main>

{nav}

<footer class="site-footer">
  Built with <a href="https://postmic.co">postmic</a> for fast reading, sharing, and search.
</footer>

</body>
</html>
"""

# -------------------------------------------------------------------
# /newest page renderer
# -------------------------------------------------------------------

def render_newest_page(ep):
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>New Episode Out Now – The Strategists</title>
<meta name="robots" content="noindex, nofollow">
</head>
<body>
<h1>{ep['title']}</h1>
<p>{ep['description']}</p>
<a href="{ep['url']}">Read transcript</a>
</body>
</html>
"""

def write_sitemap(episodes, total_pages):
    base = "https://episodes.thestrategists.ca"
    urls = []

    urls.append((f"{base}/", "daily", "1.0"))

    for page in range(2, total_pages + 1):
        urls.append((f"{base}/page/{page}/", "weekly", "0.6"))

    for ep in episodes:
        urls.append((f"{base}{ep['url']}", "never", "0.9"))

    urls.append((f"{base}/newest/", "daily", "0.4"))

    xml = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']

    for loc, freq, prio in urls:
        xml.append("<url>")
        xml.append(f"<loc>{loc}</loc>")
        xml.append(f"<changefreq>{freq}</changefreq>")
        xml.append(f"<priority>{prio}</priority>")
        xml.append("</url>")

    xml.append("</urlset>")

    (OUT_DIR / "sitemap.xml").write_text("\n".join(xml), encoding="utf-8")

# -------------------------------------------------------------------
# Main
# -------------------------------------------------------------------

def main():
    episodes = load_episodes()
    total_pages = math.ceil(len(episodes) / PER_PAGE)

    for page in range(1, total_pages + 1):
        start = (page - 1) * PER_PAGE
        end = start + PER_PAGE

        html = render_index_page(
            episodes[start:end],
            page,
            total_pages,
        )

        out = OUT_DIR / ("index.html" if page == 1 else f"page/{page}/index.html")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(html, encoding="utf-8")

    NEWEST_DIR.mkdir(parents=True, exist_ok=True)
    (NEWEST_DIR / "index.html").write_text(
        render_newest_page(episodes[0]),
        encoding="utf-8"
    )

    write_sitemap(episodes, total_pages)
    print(f"✔ Wrote index ({total_pages} pages), /newest, and sitemap.xml")

if __name__ == "__main__":
    main()
