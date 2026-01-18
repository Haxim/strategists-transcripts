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
            <article class="episode-card">
              <a class="episode-title" href="/{ep['slug']}.html">
                {html.escape(ep['title'])}
              </a>
              <div class="episode-meta">
                <span class="episode-date">{ep['published_human']}</span>
              </div>
              {f'<p class="episode-desc">{html.escape(ep["description"])}</p>' if ep.get("description") else ""}
            </article>
            """
        )

    prev_link = ""
    next_link = ""
    prev_url = ""

    if page > 1:
        prev_url = "/" if page == 2 else f"/page/{page - 1}/"
        prev_link = f'<a class="pager-link" href="{prev_url}">← Newer</a>'

    if page < total_pages:
        next_link = f'<a class="pager-link" href="/page/{page + 1}/">Older →</a>'

    canonical = f"{ARCHIVE_URL}/" if page == 1 else f"{ARCHIVE_URL}/page/{page}/"

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

  <!-- Typographic vibe closer to the main site -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Assistant:wght@400;600&display=swap" rel="stylesheet">

  <style>
    :root {{
      /* Strategists brand accents */
      --color-base-text: 18, 18, 18;
      --color-base-background-1: 255, 255, 255;
      --color-base-background-2: 243, 243, 243;
      --color-base-accent-1: 35, 46, 65;   /* #232e41 */
      --color-base-accent-2: 217, 82, 46;  /* #d7522f */

      --page-width: 120rem;
      --border-soft: rgba(var(--color-base-text), 0.10);
      --border-softer: rgba(var(--color-base-text), 0.08);
      --text-muted: rgba(var(--color-base-text), 0.75);
      --text-faint: rgba(var(--color-base-text), 0.60);
    }}

    * {{ box-sizing: border-box; }}

    body {{
      margin: 0;
      font-family: Assistant, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif;
      color: rgba(var(--color-base-text), 0.92);
      background: rgb(var(--color-base-background-1));
    }}

    /* Dawn-ish page width container */
    .page-width {{
      max-width: var(--page-width);
      margin: 0 auto;
      padding: 0 1.5rem;
    }}
    @media screen and (min-width: 750px) {{
      .page-width {{ padding: 0 5rem; }}
    }}

    /* Hero */
    header.hero {{
      background: rgb(var(--color-base-background-1));
      border-bottom: 1px solid var(--border-softer);
    }}
    header.hero img {{
      width: 100%;
      max-height: 240px;
      object-fit: contain;
      display: block;
    }}

    /* Nav */
    .site-nav {{
      border-top: 1px solid var(--border-softer);
      background: rgb(var(--color-base-background-1));
    }}

    .nav-row {{
      display: flex;
      justify-content: center;
      align-items: center;
    }}

    .nav-list {{
      margin: 0;
      padding: 0;
      list-style: none;
      display: flex;
      flex-wrap: wrap;
      justify-content: center;
      gap: 0;
    }}

    .nav-list a {{
      display: inline-block;
      padding: 1.05rem 1.2rem;
      color: rgba(var(--color-base-text), 0.78);
      text-decoration: none;
      letter-spacing: 0.06rem;
      font-weight: 400;
      font-size: 1rem;
      line-height: 1;
    }}

    .nav-list a:hover {{
      color: rgb(var(--color-base-text));
    }}

    .nav-list a span {{
      transition: text-decoration-color 120ms ease;
      text-decoration: underline;
      text-underline-offset: 0.3rem;
      text-decoration-color: transparent;
    }}

    .nav-list a:hover span {{
      text-decoration-color: currentColor;
    }}

    .nav-list a:focus-visible {{
      outline: 2px solid rgba(var(--color-base-accent-2), 0.55);
      outline-offset: 3px;
      border-radius: 6px;
    }}

    /* Intro */
    header.intro {{
      padding: 2.5rem 0 1.5rem;
    }}

    header.intro h1 {{
      margin: 0 0 .75rem;
      color: rgb(var(--color-base-text));
      font-weight: 400;
      letter-spacing: 0.06rem;
      font-size: 2rem;
      line-height: 1.15;
    }}

    .seo-intro {{
      max-width: 82rem;
      margin: 0;
      font-size: 1.1rem;
      line-height: 1.65;
      color: rgba(var(--color-base-text), 0.75);
    }}

    /* Main */
    main {{
      padding: 1.5rem 0 3rem;
    }}

    .section-title {{
      margin: 0 0 1.25rem;
      font-size: 1.4rem;
      letter-spacing: 0.06rem;
      color: rgb(var(--color-base-text));
      font-weight: 400;
    }}

    /* Card grid */
    .episode-grid {{
      display: grid;
      grid-template-columns: 1fr;
      gap: 1rem;
    }}

    @media screen and (min-width: 750px) {{
      .episode-grid {{
        gap: 1.25rem;
      }}
    }}

    /* Two columns on big screens */
    @media screen and (min-width: 1000px) {{
      .episode-grid {{
        grid-template-columns: 1fr 1fr;
      }}
    }}

    /* Card-like episodes */
    .episode-card {{
      padding: 1.25rem 1.25rem;
      border: 1px solid var(--border-soft);
      border-radius: 16px;
      background: rgb(var(--color-base-background-1));
      box-shadow: 0 1px 0 rgba(0,0,0,0.03);
      transition: transform 140ms ease, box-shadow 140ms ease, border-color 140ms ease;
    }}

    .episode-card:hover {{
      transform: translateY(-2px);
      box-shadow: 0 10px 24px rgba(0,0,0,0.08);
      border-color: rgba(var(--color-base-text), 0.14);
    }}

    .episode-title {{
      display: inline-block;
      color: rgb(var(--color-base-accent-1));
      text-decoration: none;
      font-weight: 600;
      letter-spacing: 0.02rem;
      font-size: 1.2rem;
      line-height: 1.35;
    }}

    .episode-title:hover {{
      color: rgb(var(--color-base-accent-2));
      text-decoration: underline;
      text-underline-offset: 0.3rem;
    }}

    .episode-meta {{
      margin-top: .45rem;
      font-size: 0.95rem;
      color: rgba(var(--color-base-text), 0.60);
    }}

    .episode-desc {{
      margin: .75rem 0 0;
      max-width: 90rem;
      font-size: 1rem;
      line-height: 1.6;
      color: rgba(var(--color-base-text), 0.75);
    }}

    /* Pagination */
    nav.pagination {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-top: 2.25rem;
      padding-top: 1.5rem;
      border-top: 1px solid var(--border-softer);
    }}

    .pager-link {{
      color: rgb(var(--color-base-accent-1));
      text-decoration: underline;
      text-underline-offset: 0.3rem;
      text-decoration-color: transparent;
      font-weight: 600;
      letter-spacing: 0.02rem;
    }}
    .pager-link:hover {{
      color: rgb(var(--color-base-accent-2));
      text-decoration-color: currentColor;
    }}

    /* Footer */
    footer {{
      margin: 3rem 0 2rem;
      padding-top: 1.5rem;
      border-top: 1px solid var(--border-softer);
      color: rgba(var(--color-base-text), 0.60);
      font-size: 0.95rem;
      text-align: center;
    }}

    footer a {{
      color: rgb(var(--color-base-accent-1));
      text-decoration: underline;
      text-underline-offset: 0.3rem;
      text-decoration-color: transparent;
      font-weight: 600;
    }}
    footer a:hover {{
      color: rgb(var(--color-base-accent-2));
      text-decoration-color: currentColor;
    }}
  </style>
</head>

<body>

<header class="hero">
  <a href="{MAIN_SITE_URL}">
    <img src="{HERO_SRC}" alt="The Strategists">
  </a>

  <div class="site-nav">
    <div class="page-width nav-row">
      <nav aria-label="Primary">
        <ul class="nav-list" role="list">
          <li><a href="{MAIN_SITE_URL}"><span>Home</span></a></li>
          <li><a href="{ARCHIVE_URL}"><span>Episodes</span></a></li>
          <li><a href="{APPLE_PODCASTS_URL}"><span>Apple Podcasts</span></a></li>
          <li><a href="{PATREON_URL}"><span>Patreon</span></a></li>
        </ul>
      </nav>
    </div>
  </div>
</header>

<div class="page-width">
  <header class="intro">
    <h1>Canadian & Alberta Politics Podcast Transcripts</h1>
    <p class="seo-intro">
      The Strategists is a Canadian politics podcast focused on Alberta politics,
      federal campaigns, elections, and political strategy. This archive contains
      full episode transcripts covering Canadian public affairs and political analysis.
    </p>
  </header>

  <main>
    <h2 class="section-title">Episodes</h2>
    <div class="episode-grid">
      {''.join(cards)}
    </div>

    <nav class="pagination" aria-label="Pagination">
      <div>{prev_link}</div>
      <div>{next_link}</div>
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
</div>

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
