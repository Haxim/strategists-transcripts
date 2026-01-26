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
PATREON_RE = re.compile(r'class="[^"]*\bpatreon-lock\b', re.I)

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

    newer = (
        '<a class="newer" href="/">← Newer</a>'
        if page == 2
        else f'<a class="newer" href="/page/{page-1}/">← Newer</a>'
        if page > 2
        else '<span></span>'
    )

    older = (
        f'<a class="older" href="/page/{page+1}/">Older →</a>'
        if page < total_pages
        else '<span></span>'
    )

    pager = f"""
<nav class="pager">
  {newer}
  <div class="page-num">Page {page} of {total_pages}</div>
  {older}
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

def render_newest_page(latest):
    """
    Build /newest/index.html for the most recent episode.
    """

    title = latest["title"]
    description = latest["description"] or "Listen to the latest episode of The Strategists."
    episode_number = ""
    m = re.search(r"(Episode\s+\d+)", title, re.I)
    if m:
        episode_number = m.group(1)

    # Best-effort links (safe fallbacks)
    apple = "https://podcasts.apple.com/ca/podcast/the-strategists/id1514440943"
    spotify = "https://open.spotify.com/show/7gx7f75pZS38AHWNFj7WGr"
    youtube = "https://www.youtube.com/@strategistspod"
    web = f"https://shows.acast.com/strategistspod/episodes/{latest['url'].lstrip('/')}"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>New Episode Out Now – The Strategists</title>

  <!-- Basic SEO / Social -->
  <meta name="robots" content="noindex, nofollow" />
  <meta property="og:title" content="New Episode Out Now – The Strategists" />
  <meta property="og:description" content="Listen to the latest episode of The Strategists." />

  <style>
    :root {{
      --orange: #d7522f;
      --navy: #232e41;
      --bg-dark: #0f141c;
      --white: #ffffff;
    }}

    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}

    body {{
      font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
      background: radial-gradient(1200px 800px at 80% -20%, rgba(215,82,47,0.35), transparent 60%),
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
      width: 100%;
      max-width: 560px;
      background: rgba(15,20,28,0.85);
      border-radius: 24px;
      padding: 40px 32px 36px;
      box-shadow: 0 30px 80px rgba(0,0,0,0.45);
      backdrop-filter: blur(8px);
      animation: floatIn 0.6s ease-out;
    }}

    @keyframes floatIn {{
      from {{ opacity: 0; transform: translateY(12px) scale(0.98); }}
      to {{ opacity: 1; transform: translateY(0) scale(1); }}
    }}

    .badge {{
      display: inline-block;
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
      font-size: 15px;
      opacity: 0.8;
      margin-bottom: 18px;
    }}

    .description {{
      font-size: 16px;
      line-height: 1.5;
      opacity: 0.9;
      margin-bottom: 28px;
    }}

    .buttons {{
      display: grid;
      gap: 14px;
      margin-bottom: 20px;
    }}

    .btn {{
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 10px;
      padding: 16px 18px;
      border-radius: 14px;
      font-size: 16px;
      font-weight: 600;
      text-decoration: none;
      transition: transform 0.15s ease, box-shadow 0.15s ease, background 0.15s ease;
    }}

    .btn-primary {{
      background: var(--orange);
      color: var(--white);
      box-shadow: 0 10px 30px rgba(215,82,47,0.35);
    }}

    .btn-primary:hover {{
      transform: translateY(-1px);
      box-shadow: 0 16px 40px rgba(215,82,47,0.45);
    }}

    .btn-secondary {{
      background: rgba(255,255,255,0.08);
      color: var(--white);
    }}

    .btn-secondary:hover {{
      background: rgba(255,255,255,0.14);
      transform: translateY(-1px);
    }}

    .footer {{
      text-align: center;
      font-size: 13px;
      opacity: 0.6;
      margin-top: 8px;
    }}

    .footer a {{
      color: inherit;
      text-decoration: underline;
    }}

    @media (max-width: 420px) {{
      h1 {{ font-size: 28px; }}
      .card {{ padding: 32px 24px; }}
    }}
  </style>
</head>
<body>

  <main class="card">
    <div class="badge">NEW EPISODE OUT NOW</div>

    <h1>{title}</h1>
    {f'<div class="episode-number">{episode_number}</div>' if episode_number else ''}

    <p class="description">{description}</p>

    <div class="buttons">
      <a class="btn btn-primary" href="{web}" target="_blank">▶️ Listen & Read the Transcript</a>
      <a class="btn btn-secondary" href="{apple}" target="_blank">🎧 Listen on Apple Podcasts</a>
      <a class="btn btn-secondary" href="{spotify}" target="_blank">🎧 Listen on Spotify</a>
      <a class="btn btn-secondary" href="{youtube}" target="_blank">▶️ Watch / Listen on YouTube</a>
    </div>

    <div class="footer">
      <a href="/">Browse all episodes</a>
    </div>
  </main>
</body>
</html>
"""
    
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

    if episodes:
        newest_html = render_newest_page(episodes[0])
        newest_out = OUT_DIR / "newest/index.html"
        newest_out.parent.mkdir(parents=True, exist_ok=True)
        newest_out.write_text(newest_html, encoding="utf-8")

if __name__ == "__main__":
    main()
    # Build /newest/index.html




