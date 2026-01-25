#!/usr/bin/env python3

from pathlib import Path
from datetime import datetime
import math
import re

SITE_NAME = "The Strategists"
EPISODES_DIR = Path("./episodes")
OUT_DIR = Path(".")
PER_PAGE = 24


TITLE_RE = re.compile(r"<title>(.*?)</title>", re.I | re.S)
DATE_RE = re.compile(
    r'"datePublished"\s*:\s*"([^"]+)"', re.I
)


def extract_meta(html: str):
    title = TITLE_RE.search(html)
    date = DATE_RE.search(html)

    return {
        "title": title.group(1).split("|")[0].strip() if title else "Episode",
        "published": date.group(1) if date else "",
    }


def load_episodes():
    episodes = []

    for path in EPISODES_DIR.glob("*.html"):
        html = path.read_text(encoding="utf-8")

        meta = extract_meta(html)
        try:
            ts = datetime.fromisoformat(
                meta["published"].replace("Z", "+00:00")
            ).timestamp()
        except Exception:
            ts = 0

        episodes.append({
            "title": meta["title"],
            "published": meta["published"],
            "ts": ts,
            "url": f"/episodes/{path.name}",
        })

    episodes.sort(key=lambda e: e["ts"], reverse=True)
    return episodes


def render_page(episodes, page, total_pages):
    cards = "\n".join(
        f"""
        <a class="card" href="{ep['url']}">
          <div class="title">{ep['title']}</div>
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
<html>
<head>
  <meta charset="utf-8">
  <title>{SITE_NAME} – Episodes</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
</head>
<body>
  <h1>{SITE_NAME}</h1>
  <section class="grid">
    {cards}
  </section>
  {nav}
</body>
</html>
"""


def main():
    episodes = load_episodes()
    pages = math.ceil(len(episodes) / PER_PAGE)

    for page in range(1, pages + 1):
        start = (page - 1) * PER_PAGE
        end = start + PER_PAGE

        html = render_page(
            episodes[start:end],
            page,
            pages,
        )

        if page == 1:
            out = OUT_DIR / "index.html"
        else:
            out = OUT_DIR / "page" / str(page) / "index.html"
            out.parent.mkdir(parents=True, exist_ok=True)

        out.write_text(html, encoding="utf-8")

    print(f"✔ Wrote {pages} index pages")


if __name__ == "__main__":
    main()
