"""Crawler for IJAMinecraft (https://ijaminecraft.com/).

This site is server-rendered, so we scrape with BeautifulSoup.
"""
import logging
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from crawler._http import get_html
from parser.parse_mod import parse_mod_page
from publisher.publish import publish_item

BASE_URL = "https://ijaminecraft.com"
MODS_URL = "https://ijaminecraft.com/mods"

log = logging.getLogger(__name__)


def _discover_links(html):
    soup = BeautifulSoup(html, "lxml")
    links = set()

    # IJAMinecraft uses a mix of card styles; try several selectors.
    selectors = [
        "a.mod-card", ".mod-card a", ".mod-item a", ".post-card a",
        "article a[href*='/mod/']", "a[href*='/mods/']",
    ]
    for sel in selectors:
        for a in soup.select(sel):
            href = a.get("href")
            if not href:
                continue
            if href.startswith("#") or href.startswith("javascript:"):
                continue
            absolute = urljoin(BASE_URL, href)
            if "/mod" in absolute:  # filter to mod pages
                links.add(absolute)
    return list(links)


def discover_ijaminecraft(limit=None, page_state=None):
    """Discover and publish mods from IJAMinecraft."""
    html = get_html(MODS_URL)
    if not html:
        log.warning("[IJAMinecraft] failed to fetch mods index")
        return 0

    links = _discover_links(html)
    log.info("[IJAMinecraft] found %d candidate links", len(links))

    if limit:
        links = links[:limit]

    published = 0
    for link in links:
        try:
            overrides = {
                "category": "mods",
                "source": {"name": "IJAMinecraft", "base_url": BASE_URL},
                "is_verified": True,
            }
            data = parse_mod_page(link, overrides=overrides)
            if data and publish_item(data):
                published += 1
        except Exception as e:  # keep crawling even if one mod blows up
            log.exception("[IJAMinecraft] error processing %s: %s", link, e)

    log.info("[IJAMinecraft] cycle published %d items", published)
    return published
