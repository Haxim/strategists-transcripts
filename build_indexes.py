#!/usr/bin/env python3
"""
build_indexes.py

Static site index builder for The Strategists.

Inputs:
  /html/*.html   (already-rendered episode pages)

Outputs:
  /index.html
  /page/N/index.html
  /newest/index.html
  /sitemap.xml

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
NEWEST_DIR = OUT_DIR / "newest"
PER_PAGE = 24

# -------------------------------------------------------------------
# Regex extractors (robust)
# -------------------------------------------------------------------

TITLE_RE = re.compile(r"<title>(.*?)</title>", re.I | re.S)
DATE_RE = re.compile(r'"datePublished"\s*:\s*"([^"]+)"', re.I)

META_DESC_RE = re.compile(
    r'<meta\s+(?:property="og:description"|name="description")\s+content="([^"]+)"',
    re.I | re.S,
)

JSON_DESC_RE = re.compile(
    r'"description"\s*:\s*"([^"]+)"',
    re.I | re.S,
)

EP_NUM_RE = re.compile(r'"episodeNumber"\s*:\s*(\d+)', re.I)

PATREON_RE = re.compile(r"/assets/patreon\.png", re.I)

# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------

def extract_meta(html: str):
    title_m = TITLE_RE.search(html)
    date_m = DATE_RE.search(html)
    desc_m = META_DESC_RE.search(html) or JSON_DESC_RE.search(html)
    epnum_m = EP_NUM_RE.search(html)

    title = title_m.group(1).split("|")[0].strip() if title_m else "Episode"
    published = date_m.group(1) if date_m else ""
    description = desc_m.group(1).strip() if desc_m else ""
    description = re.sub(r"\s+", " ", description)

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
        "episode_number": epnum_m.group(1) if epnum_m else "",
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

# -------------------------------------------------------------------
# Index renderer
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

    prev_link = (
        f'<link rel="prev" href="{"/" if page == 2 else f"/page/{page-1}/"}">'
        if page > 1 else ""
    )

    next_link = (
        f'<link rel="next" href="/page/{page+1}/">'
        if page < total_pages else ""
    )

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
        <a href="https://podcasts.apple.com/ca/podcast/the-strategists/id1514440943" target="_blank">Apple Podcasts</a>
        <span>·</span>
        <a href="https://open.spotify.com/show/7gx7f75pZS38AHWNFj7WGr" target="_blank">Spotify</a>
        <span>·</span>
        <a href="https://www.youtube.com/@strategistspod" target="_blank">YouTube</a>
      </div>
    </aside>
  </div>
</header>
""".strip()

    cards = "\n".join(
        f"""
<a class="card {'patreon' if ep['access']=='patreon' else ''}" href="{ep['url']}">
  <div class="thumb">
    <img src="/assets/{'patreon' if ep['access']=='patreon' else 'public'}.png" loading="lazy" />
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

    pager = ""
    if total_pages > 1:
        pager = f"""
<nav class="pager">
  {f'<a class="newer" href="{"/" if page==2 else f"/page/{page-1}/"}">← Newer</a>' if page>1 else '<span></span>'}
  <div class="page-num">Page {page} of {total_pages}</div>
  {f'<a class="older" href="/page/{page+1}/">Older →</a>' if page<total_pages else '<span></span>'}
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
  --orange:#d7522f;
  --white:#ffffff;
}}

*{{box-sizing:border-box}}

body {{
  margin:0;
  padding:32px 24px 48px;
  font-family:Inter,system-ui,-apple-system,Segoe UI,Roboto,sans-serif;
  color:var(--white);
  background:
    radial-gradient(1200px 700px at 70% -20%, rgba(215,82,47,.25), transparent 60%),
    radial-gradient(900px 600px at -20% 120%, rgba(35,46,65,.6), transparent 60%),
    linear-gradient(160deg,#121826,#0b0f16);
}}

.hero{{margin-bottom:48px}}
.hero-grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:18px}}
.hero-text{{padding-left:8px}}
.listen-on{{align-self:center;text-align:center}}
@media(max-width:860px){{.hero-grid{{grid-template-columns:1fr}}.listen-on{{text-align:left;margin-top:24px}}}}

.grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:18px}}
@media(max-width:720px){{.grid{{grid-template-columns:1fr}}}}

.card{{display:flex;gap:14px;padding:18px;border-radius:18px;background:rgba(255,255,255,.06);color:inherit;text-decoration:none}}
.card:hover{{background:rgba(255,255,255,.1);transform:translateY(-2px)}}
.card.patreon{{box-shadow:0 0 0 1px rgba(215,82,47,.35),0 0 18px rgba(215,82,47,.15)}}
.thumb{{width:64px;height:64px;border-radius:12px;overflow:hidden}}
.thumb img{{width:100%;height:100%;object-fit:cover}}

.pager{{display:grid;grid-template-columns:1fr auto 1fr;margin:48px 0}}
.pager a{{color:#fff;opacity:.75;text-decoration:none}}
.pager a:hover{{opacity:1}}
.page-num{{opacity:.6;text-align:center}}

.site-footer{{margin-top:64px;text-align:center;font-size:13px;opacity:.55}}
.footer-credit{{margin-top:24px}}
.site-footer a{{color:var(--orange);font-weight:600;text-decoration:none}}
</style>
</head>
<body>

{hero}
{pager}
<main class="grid">{cards}</main>
{pager}

<footer class="site-footer">
  <nav class="footer-links">
    <a href="https://www.patreon.com/strategistspod">Patreon</a>
    <a href="https://www.youtube.com/@strategistspod">YouTube</a>
    <a href="https://bsky.app/profile/thestrategists.ca">Bluesky</a>
    <a href="https://www.instagram.com/strategistspod/">Instagram</a>
    <a href="https://www.tiktok.com/@strategistspod">TikTok</a>
    <a href="https://www.linkedin.com/company/106712598/">LinkedIn</a>
  </nav>
  <div class="footer-credit">
    Built with <a href="https://postmic.co">postmic</a> for fast reading, sharing, and search.
  </div>
</footer>

</body>
</html>
"""

# -------------------------------------------------------------------
# Newest + sitemap
# -------------------------------------------------------------------

def render_newest_page(ep):
    return f"<meta http-equiv='refresh' content='0;url={ep['url']}'>"

def write_sitemap(episodes, total_pages):
    base = "https://episodes.thestrategists.ca"
    urls = [f"{base}/"] + \
           [f"{base}/page/{p}/" for p in range(2, total_pages+1)] + \
           [f"{base}{ep['url']}" for ep in episodes] + \
           [f"{base}/newest/"]

    xml = ["<?xml version='1.0' encoding='UTF-8'?>",
           "<urlset xmlns='http://www.sitemaps.org/schemas/sitemap/0.9'>"]

    for u in urls:
        xml.append(f"<url><loc>{u}</loc></url>")

    xml.append("</urlset>")
    (OUT_DIR/"sitemap.xml").write_text("\n".join(xml), encoding="utf-8")

# -------------------------------------------------------------------
# Main
# -------------------------------------------------------------------

def main():
    episodes = load_episodes()
    total_pages = math.ceil(len(episodes)/PER_PAGE)

    for page in range(1, total_pages+1):
        start = (page-1)*PER_PAGE
        end = start+PER_PAGE
        out = OUT_DIR/"index.html" if page==1 else OUT_DIR/"page"/str(page)/"index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(render_index_page(episodes[start:end], page, total_pages), encoding="utf-8")

    NEWEST_DIR.mkdir(parents=True, exist_ok=True)
    (NEWEST_DIR/"index.html").write_text(render_newest_page(episodes[0]), encoding="utf-8")

    write_sitemap(episodes, total_pages)

if __name__ == "__main__":
    main()
