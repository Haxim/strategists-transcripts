#!/usr/bin/env python3
"""
build_indexes_fixed_aligned_final_v2.py

Static site post-processor for The Strategists.

Goal: Keep the known-good episode card rendering from build_indexes.py,
but make the top "The Strategists" + tagline and "Listen to the show"
blocks participate in the SAME 2-column grid as episode cards:
- Title/tagline flush with left edge of column 1
- Listen block horizontally centered in column 2
- No vertical shifting tricks
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
        # IMPORTANT: these two blocks are direct children of `.grid`
        # so they occupy row 1, col 1 and row 1, col 2 respectively.
        hero = f"""
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
""".strip()

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

.grid {{ display:grid; grid-template-columns:1fr 1fr; gap:18px; }}

.hero-text h1 {{
  margin: 0 0 10px;
  font-size: 44px;
  letter-spacing: -0.02em;
}}
.tagline {{
  margin: 0;
  font-size: 18px;
  line-height: 1.5;
  opacity: 0.85;
  max-width: 720px;
}}

.listen-center {{ justify-self:center; text-align:center; }}
.listen-label {{ font-size: 15px; font-weight: 600; margin-bottom: 10px; opacity: 0.9; }}
.listen-links {{ font-size: 16px; opacity: 0.8; }}
.listen-links a {{ color: var(--orange); font-weight: 600; text-decoration: none; }}
.listen-links a:hover {{ text-decoration: underline; }}
.listen-links span {{ margin: 0 8px; opacity: 0.4; }}

.card {{ background:rgba(255,255,255,.06); border-radius:18px; padding:18px; display:flex; gap:14px; color:inherit; text-decoration:none; }}
.card:hover {{ background:rgba(255,255,255,.10); }}
.card.patreon {{ box-shadow: 0 0 0 1px rgba(215,82,47,.35), 0 0 18px rgba(215,82,47,.15); }}

.thumb {{ width:64px; height:64px; min-width:64px; background:rgba(255,255,255,.08); border-radius:12px; overflow:hidden; }}
.thumb img {{ width:100%; height:100%; object-fit:cover; display:block; }}

.title {{ font-weight:700; font-size:17px; line-height:1.3; }}
.meta {{ opacity:.6; font-size:14px; margin-top:6px; }}
.desc {{
  margin-top:10px;
  font-size:14px;
  line-height:1.45;
  opacity:.75;
  display:-webkit-box;
  -webkit-line-clamp:3;
  -webkit-box-orient:vertical;
  overflow:hidden;
}}

@media (max-width:860px) {{
  .grid {{ grid-template-columns:1fr; }}
  .listen-center {{ text-align:left; justify-self:start; }}
}}
</style>
</head>
<body>
<main class="layout">
  <div class="grid">
    {hero}
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
