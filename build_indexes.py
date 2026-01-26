#!/usr/bin/env python3
"""
build_indexes.py

Static site post-processor for The Strategists.
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
NEWEST_DIR = OUT_DIR / "newest"

TITLE_RE = re.compile(r"<title>(.*?)</title>", re.I | re.S)
DATE_RE = re.compile(r'"datePublished"\s*:\s*"([^"]+)"', re.I)
DESC_RE = re.compile(r'<meta property="og:description" content="([^"]+)"', re.I)
PATREON_RE = re.compile(r"/assets/patreon\.jpg", re.I)


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
        "published": published,
        "ts": ts,
        "description": description,
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


def render_index_page(episodes, page, total_pages):
    is_home = page == 1

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
      <a href="https://podcasts.apple.com/ca/podcast/the-strategists/id1514440943" target="_blank">Apple Podcasts</a>
      <span>·</span>
      <a href="https://open.spotify.com/show/7gx7f75pZS38AHWNFj7WGr" target="_blank">Spotify</a>
      <span>·</span>
      <a href="https://www.youtube.com/@strategistspod" target="_blank">YouTube</a>
    </div>
  </aside>
</header>
"""

    cards = "\n".join(
        f"""
<a class="card {'patreon' if ep['access']=='patreon' else ''}" href="{ep['url']}">
  <div class="thumb">
    <img src="/assets/{'patreon' if ep['access']=='patreon' else 'public'}.png" loading="lazy">
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

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{SITE_NAME}</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
:root {{ --orange:#d7522f; --white:#fff; }}
body {{ margin:0; font-family:Inter,system-ui; background:#0b0f16; color:var(--white); }}
.layout {{ max-width:1100px; margin:0 auto; padding:0 24px; }}
.hero-split {{ display:grid; grid-template-columns:1fr 1fr; gap:18px; margin-bottom:48px; }}
.listen-center {{ justify-self:center; text-align:center; }}
.grid {{ display:grid; grid-template-columns:1fr 1fr; gap:18px; }}
.card {{ background:rgba(255,255,255,.06); border-radius:18px; padding:18px; display:flex; gap:14px; color:inherit; text-decoration:none; }}
.thumb {{ width:64px; height:64px; background:rgba(255,255,255,.08); border-radius:12px; }}
@media (max-width:860px) {{ .hero-split,.grid {{ grid-template-columns:1fr; }} .listen-center {{ text-align:left; justify-self:start; }} }}
</style>
</head>
<body>
{hero}
<main class="layout">
  <div class="grid">
    {cards}
  </div>
</main>
</body>
</html>
"""


def main():
    episodes = load_episodes()
    total_pages = math.ceil(len(episodes) / PER_PAGE)
    html = render_index_page(episodes[:PER_PAGE], 1, total_pages)
    (OUT_DIR / "index.html").write_text(html, encoding="utf-8")


if __name__ == "__main__":
    main()
