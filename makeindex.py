#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime
from math import ceil
import html
import re
import xml.etree.ElementTree as ET

# ------------------------------------------------------------
# Config
# ------------------------------------------------------------
HTML_DIR = Path("html")
PER_PAGE = 50

SITE_TITLE = "The Strategists"

# Canonical archive URL (episodes + transcripts are the same thing)
ARCHIVE_URL = "https://episodes.thestrategists.ca"

# Brand / distribution
MAIN_SITE_URL = "https://www.thestrategists.ca"
APPLE_PODCASTS_URL = "https://apple.co/4ol8kJD"
PATREON_URL = "https://www.patreon.com/strategistspod"

HERO_SRC = "/assets/hero.png"

# ------------------------------------------------------------
# Regex helpers
# ------------------------------------------------------------
H1_RE = re.compile(r"<h1[^>]*>(.*?)</h1>", re.I | re.S)
META_DESC_RE = re.compile(
    r'<meta[^>]+name=["\']description["\'][^>]+content=["\'](.*?)["\']',
    re.I | re.S,
)
TAG_RE = re.compile(r"<[^>]+>")

# ------------------------------------------------------------
# Extraction helpers
# ------------------------------------------------------------
def extract_h1_title(text: str) -> str | None:
    m = H1_RE.search(text)
    if not m:
        return None
    return html.unescape(TAG_RE.sub("", m.group(1)).strip())


def extract_description(text: str) -> str | None:
    m = META_DESC_RE.search(text)
    if not m:
        return None

    desc = html.unescape(m.group(1))
    desc = TAG_RE.sub("", desc)
    desc = re.sub(r"\s+", " ", desc).strip()

    MAX_LEN = 300
    if len(desc) > MAX_LEN:
        cut = desc.rfind(".", 0, MAX_LEN)
        if cut > 140:
            desc = desc[:cut + 1]
        else:
            desc = desc[:MAX_LEN].rstrip() + "…"

    return desc

# ------------------------------------------------------------
# HTML rendering
# ------------------------------------------------------------
def render_index_page(episodes, page, total_pages):
    cards = []
    for ep in episodes:
        cards.append(
            f"""
            <article class="episode">
              <a class="episode-title" href="/{ep['slug']}.html">
                {html.escape(ep['title'])}
              </a>
              <div class="date">{ep['published_human']}</div>
              {f'<p class="desc">{html.escape(ep["description"])}</p>' if ep.get("description") else ""}
            </article>
            """
        )

    prev_link = ""
    next_link = ""

    if page > 1:
        prev_url = "/" if page == 2 else f"/page/{page - 1}/"
        prev_link = f'<a href="{prev_url}">← Newer</a>'

    if page < total_pages:
        next_link = f'<a href="/page/{page + 1}/">Older →</a>'

    canonical = (
        f"{ARCHIVE_URL}/"
        if page == 1
        else f"{ARCHIVE_URL}/page/{page}/"
    )

    rel_links = []
    if page > 1:
        rel_links.append(f'<link rel="prev" href="{ARCHIVE_URL}{prev_url}">')
    if page < total_pages:
        rel_links.append(f'<link rel="next" href="{ARCHIVE_URL}/page/{page + 1}/">')

    return f"""<!doctype html>
<html lang="en-CA">
<head>
  <meta charset="utf-8">
  <title>Canadian Politics Podcast Transcripts | The Strategists</title>
  <meta name="description" content="Full transcripts of The Strategists, a Canadian politics podcast covering Alberta politics, federal campaigns, elections, political strategy, and public affairs.">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="canonical" href="{canonical}">
  {"".join(rel_links)}

  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "PodcastSeries",
    "name": "The Strategists",
    "description": "A Canadian politics podcast covering Alberta politics, elections, campaigns, and political strategy.",
    "url": "{ARCHIVE_URL}/",
    "inLanguage": "en-CA",
    "publisher": {{
      "@type": "Organization",
      "name": "The Strategists"
    }},
    "sameAs": [
      "{MAIN_SITE_URL}",
      "{ARCHIVE_URL}",
      "{PATREON_URL}",
      "{APPLE_PODCASTS_URL}"
    ]
  }}
  </script>

  <style>
    body {{
      font-family: system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif;
      margin: 0;
      color: #111;
      background: #fff;
    }}
    header.hero img {{
      width: 100%;
      max-height: 260px;
      object-fit: contain;
      display: block;
    }}
    .top-nav {{
      max-width: 960px;
      margin: 0 auto;
      padding: .75rem 1rem 1rem;
      display: flex;
      flex-wrap: wrap;
      gap: 1.25rem;
      font-size: .95rem;
    }}
    .top-nav a {{
      color: #0b57d0;
      font-weight: 500;
      text-decoration: none;
    }}
    header.intro {{
      max-width: 960px;
      margin: 0 auto;
      padding: 2.5rem 1rem;
    }}
    .seo-intro {{
      max-width: 720px;
      margin-top: 1rem;
      font-size: 1.05rem;
      line-height: 1.6;
      color: #444;
    }}
    main {{
      max-width: 960px;
      margin: 0 auto;
      padding: 2.5rem 1rem;
    }}
    .episode {{
      padding: 1.5rem;
      margin-bottom: 1.25rem;
      border: 1px solid #e5e7eb;
      border-radius: 14px;
      background: #fafafa;
    }}
    .episode-title {{
      font-size: 1.15rem;
      font-weight: 600;
      color: #0b57d0;
      text-decoration: none;
    }}
    .date {{
      font-size: .9rem;
      color: #666;
      margin-top: .35rem;
    }}
    .desc {{
      margin-top: .75rem;
      font-size: .95rem;
      line-height: 1.55;
      color: #333;
    }}
    nav.pagination {{
      display: flex;
      justify-content: space-between;
      margin-top: 2.5rem;
    }}
    footer {{
      max-width: 960px;
      margin: 3rem auto 2rem;
      padding: 0 1rem;
      text-align: center;
      color: #666;
      font-size: .9rem;
    }}
  </style>
</head>

<body>

<header class="hero">
  <a href="{MAIN_SITE_URL}">
    <img src="{HERO_SRC}" alt="The Strategists">
  </a>
  <nav class="top-nav">
    <a href="{MAIN_SITE_URL}">Home</a>
    <a href="{ARCHIVE_URL}">Episodes</a>
    <a href="{APPLE_PODCASTS_URL}">Apple Podcasts</a>
    <a href="{PATREON_URL}">Patreon</a>
  </nav>
</header>

<header class="intro">
  <h1>Canadian & Alberta Politics Podcast Transcripts</h1>
  <p class="seo-intro">
    The Strategists is a Canadian politics podcast focused on Alberta politics,
    federal campaigns, elections, and political strategy. This archive contains
    full episode transcripts covering Canadian public affairs and political analysis.
  </p>
</header>

<main>
  <h2>Canadian & Alberta Politics Podcast Episodes</h2>
  {''.join(cards)}
  <nav class="pagination">
    {prev_link}
    {next_link}
  </nav>
</main>

<footer>
  <p>
    <a href="{MAIN_SITE_URL}">TheStrategists.ca</a> ·
    <a href="{ARCHIVE_URL}">Episodes</a> ·
    <a href="{APPLE_PODCASTS_URL}">Apple Podcasts</a> ·
    <a href="{PATREON_URL}">Patreon</a>
  </p>
</footer>

</body>
</html>
"""

# ------------------------------------------------------------
# Sitemap generation
# ------------------------------------------------------------
def write_sitemap(urls):
    urlset = ET.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
    for loc, lastmod in urls:
        url = ET.SubElement(urlset, "url")
        ET.SubElement(url, "loc").text = loc
        ET.SubElement(url, "lastmod").text = lastmod

    tree = ET.ElementTree(urlset)
    tree.write(HTML_DIR / "sitemap.xml", encoding="utf-8", xml_declaration=True)

# ------------------------------------------------------------
# Main
# ------------------------------------------------------------
def main():
    episodes = []
    sitemap_urls = []

    for p in HTML_DIR.glob("*.html"):
        if p.name == "index.html":
            continue

        text = p.read_text(encoding="utf-8", errors="ignore")
        title = extract_h1_title(text)
        if not title:
            continue

        description = extract_description(text)
        published = datetime.fromtimestamp(p.stat().st_mtime)

        episodes.append({
            "slug": p.stem,
            "title": title,
            "description": description,
            "published": published,
            "published_human": published.strftime("%b %d, %Y"),
        })

        sitemap_urls.append(
            (f"{ARCHIVE_URL}/{p.stem}.html", published.date().isoformat())
        )

    episodes.sort(key=lambda e: e["published"], reverse=True)
    total_pages = ceil(len(episodes) / PER_PAGE)

    for page in range(1, total_pages + 1):
        start = (page - 1) * PER_PAGE
        end = start + PER_PAGE
        page_eps = episodes[start:end]

        html_out = render_index_page(page_eps, page, total_pages)

        out_dir = HTML_DIR if page == 1 else HTML_DIR / "page" / str(page)
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "index.html").write_text(html_out, encoding="utf-8")

        sitemap_urls.append(
            (
                f"{ARCHIVE_URL}/" if page == 1 else f"{ARCHIVE_URL}/page/{page}/",
                datetime.utcnow().date().isoformat(),
            )
        )

    write_sitemap(sitemap_urls)
    print(f"✓ Index + sitemap generated ({len(episodes)} episodes, {total_pages} pages)")


if __name__ == "__main__":
    main()
