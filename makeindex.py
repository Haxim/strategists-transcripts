#!/usr/bin/env python3
"""
render_index.py

Generates themed episode index pages that match episode.html.jinja.

Outputs:
- html/index.html
- html/page/N/index.html
- html/episodes.json

Safe for Cloudflare Pages / CI usage.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

from jinja2 import Environment, FileSystemLoader  # type: ignore

from common import (
    JSON_DIR,
    HTML_DIR,
    TEMPLATE_DIR,
    SITE_NAME,
    slugify,
)


# -------------------------------------------------------------------
# Sorting
# -------------------------------------------------------------------

def parse_sort_key(published_iso: str) -> Tuple[int, str]:
    """
    Sort newest first; ISO fallback safe.
    """
    try:
        dt = datetime.fromisoformat(published_iso.replace("Z", "+00:00"))
        return (int(dt.timestamp()), published_iso)
    except Exception:
        return (0, published_iso or "")


# -------------------------------------------------------------------
# Load episode metadata
# -------------------------------------------------------------------

def load_episode_cards() -> List[Dict[str, Any]]:
    episodes: List[Dict[str, Any]] = []

    for jp in JSON_DIR.glob("*.json"):
        try:
            data = json.loads(jp.read_text(encoding="utf-8"))
        except Exception:
            continue

        title = data.get("title", jp.stem)
        published = data.get("published", "")
        published_human = data.get("published_human", "")
        description = data.get("description", "")

        episodes.append(
            {
                "title": title,
                "published": published,
                "published_human": published_human,
                "description": description,
                "url": f"./{slugify(title)}.html",
                "json": jp.name,
            }
        )

    episodes.sort(
        key=lambda e: parse_sort_key(e.get("published", "")),
        reverse=True,
    )

    return episodes


# -------------------------------------------------------------------
# Write one page
# -------------------------------------------------------------------

def write_page(
    template,
    episodes: List[Dict[str, Any]],
    out_dir: Path,
    page_num: int,
    total_pages: int,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    rendered = template.render(
        site_name=SITE_NAME,
        year=datetime.now(timezone.utc).year,
        episodes=episodes,
        page=page_num,
        total_pages=total_pages,
        prev_url=None
        if page_num <= 1
        else ("../index.html" if page_num == 2 else f"../{page_num-1}/index.html"),
        next_url=None
        if page_num >= total_pages
        else f"./page/{page_num+1}/index.html",
    )

    (out_dir / "index.html").write_text(rendered, encoding="utf-8")


# -------------------------------------------------------------------
# Main
# -------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-page", type=int, default=24)
    args = ap.parse_args()

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=True,
    )

    template = env.get_template("index.html.jninja")

    cards = load_episode_cards()
    if not cards:
        raise SystemExit("No episodes found in ./json")

    per = max(1, int(args.per_page))
    total_pages = (len(cards) + per - 1) // per

    # Page 1
    write_page(
        template=template,
        episodes=cards[:per],
        out_dir=HTML_DIR,
        page_num=1,
        total_pages=total_pages,
    )

    # Page N
    for page in range(2, total_pages + 1):
        start = (page - 1) * per
        end = start + per

        write_page(
            template=template,
            episodes=cards[start:end],
            out_dir=HTML_DIR / "page" / str(page),
            page_num=page,
            total_pages=total_pages,
        )

    # Lightweight client feed
    (HTML_DIR / "episodes.json").write_text(
        json.dumps(cards, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"✔ Wrote index pages ({total_pages} total)")


if __name__ == "__main__":
    main()
