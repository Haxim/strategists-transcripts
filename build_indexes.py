#!/usr/bin/env python3
"""
build_indexes_fixed.py

Static index generator for The Strategists.
Outputs index.html identical in structure to the real homepage.
"""

from pathlib import Path
from datetime import datetime
import math
import re

SITE_NAME = "The Strategists"
SITE_TAGLINE = (
    "Canada’s sharpest political insiders break down power, strategy, "
    "and the people who actually run the country."
)

EPISODES_DIR = Path("html")
OUT_DIR = Path("html")
PER_PAGE = 24

TITLE_RE = re.compile(r"<title>(.*?)</title>", re.I | re.S)
DATE_RE = re.compile(r'"datePublished"\s*:\s*"([^"]+)"', re.I)
DESC_RE = re.compile(r'<meta name="description" content="([^"]+)"', re.I)
PATREON_RE = re.compile(r"/assets/patreon\.png", re.I)

def extract_meta(html: str):
    title_m = TITLE_RE.search(html)
    date_m = DATE_RE.search(html)
    desc_m = DESC_RE.search(html)

    title = title_m.group(1).split("|")[0].strip() if title_m else "Episode"
    published = date_m.group(1) if date_m else ""
    description = desc_m.group(1).strip() if desc_m else ""

    try:
        ts = datetime.fromisoformat(published.replace("Z", "+00:00")).timestamp()
    except Exception:
        ts = 0

    return {
        "title": title,
        "published": published[:10],
        "ts": ts,
        "description": description,
    }

def load_episodes():
    episodes = []
    for path in EPISODES_DIR.glob("*.html"):
        html = path.read_text(encoding="utf-8")
        meta = extract_meta(html)
        episodes.append({
            **meta,
            "url": f"/{path.stem}",
            "access": "patreon" if PATREON_RE.search(html) else "public",
        })
    episodes.sort(key=lambda e: e["ts"], reverse=True)
    return episodes

def render_index_page(episodes, page, total_pages):
    is_home = page == 1

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
"""

    cards = "\n".join(
        f"""
<a class="card {ep['access']}" href="{ep['url']}">
  <div class="thumb">
    <img src="/assets/{ep['access']}.png" alt="{ep['access']} episode" loading="lazy">
  </div>
  <div class="card-body">
    <div class="title">{ep['title']}</div>
    <div class="meta">{ep['published']}</div>
    <div class="desc">{ep['description']}</div>
  </div>
</a>
"""
        for ep in episodes
    )

    pager = f"""
<nav class="pager">
  <span></span>
  <div class="page-num">Page {page} of {total_pages}</div>
  {f'<a class="older" href="/page/{page+1}/">Older →</a>' if page < total_pages else '<span></span>'}
</nav>
"""

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{SITE_NAME} – Podcast Transcripts</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="{SITE_TAGLINE}">
  <link rel="canonical" href="/" />
  {f'<link rel="next" href="/page/{page+1}/">' if page < total_pages else ""}
  <link rel="stylesheet" href="/assets/site.css">
</head>
<body>

{hero}
{pager}

<main class="grid">
{cards}
</main>

{pager}

<footer class="site-footer">
  <div class="wrap footer-grid">
    <nav class="footer-links">
      <a href="https://www.patreon.com/strategistspod" target="_blank">Patreon</a>
      <a href="https://www.youtube.com/@strategistspod" target="_blank">YouTube</a>
      <a href="https://bsky.app/profile/thestrategists.ca" target="_blank">Bluesky</a>
      <a href="https://www.instagram.com/strategistspod/" target="_blank">Instagram</a>
      <a href="https://www.tiktok.com/@strategistspod" target="_blank">TikTok</a>
      <a href="https://www.linkedin.com/company/106712598/" target="_blank">LinkedIn</a>
      <a href="https://pinterest.com/strategistspod/" target="_blank">Pinterest</a>
    </nav>

    <div class="footer-credit">
      Built with <a href="https://postmic.co">postmic</a> for fast reading, sharing, and search.
    </div>
  </div>
</footer>

</body>
</html>
"""

BASE_URL = "https://episodes.thestrategists.ca"

def write_sitemap(episodes, total_pages):
    urls = []

    # Home
    urls.append({
        "loc": f"{BASE_URL}/",
        "lastmod": datetime.utcnow().date().isoformat(),
        "priority": "1.0",
    })

    # Paginated index pages
    for page in range(2, total_pages + 1):
        urls.append({
            "loc": f"{BASE_URL}/page/{page}/",
            "priority": "0.6",
        })

    # Episode pages
    for ep in episodes:
        urls.append({
            "loc": f"{BASE_URL}{ep['url']}",
            "lastmod": ep["published"] or None,
            "priority": "0.8",
        })

    xml = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    ]

    for u in urls:
        xml.append("  <url>")
        xml.append(f"    <loc>{u['loc']}</loc>")
        if u.get("lastmod"):
            xml.append(f"    <lastmod>{u['lastmod']}</lastmod>")
        if u.get("priority"):
            xml.append(f"    <priority>{u['priority']}</priority>")
        xml.append("  </url>")

    xml.append("</urlset>")

    (OUT_DIR / "sitemap.xml").write_text(
        "\n".join(xml),
        encoding="utf-8"
    )

def main():
    episodes = load_episodes()
    total_pages = math.ceil(len(episodes) / PER_PAGE)

    for page in range(1, total_pages + 1):
        start = (page - 1) * PER_PAGE
        end = start + PER_PAGE
        html = render_index_page(episodes[start:end], page, total_pages)

        out = OUT_DIR / ("index.html" if page == 1 else f"page/{page}/index.html")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(html, encoding="utf-8")

    write_sitemap(episodes, total_pages)

if __name__ == "__main__":
    main()


