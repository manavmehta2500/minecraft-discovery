"""Crawler for Planet Minecraft mods (https://www.planetminecraft.com).

PlanetMinecraft is server-rendered with lots of listings; we use __NEXT_DATA__-style
scripts where available and CSS selectors for the gallery cards on /mods/.
"""
import json
import logging
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from crawler._http import get_html
from parser.parse_mod import parse_mod_page
from publisher.publish import publish_item
from config import DISCOVERY_MODE

BASE_URL = "https://www.planetminecraft.com"
MODS_URL = "https://www.planetminecraft.com/mods/"

log = logging.getLogger(__name__)


def _mode_pages():
    if DISCOVERY_MODE == "SMOKE":
        return 1
    if DISCOVERY_MODE == "FULL":
        return 5
    return 2  # FAST


def _extract_links(html):
    soup = BeautifulSoup(html, "lxml")
    links = set()
    for a in soup.select("a[href*='/mod/']"):
        href = a.get("href")
        if not href:
            continue
        if "/mod/" not in href:
            continue
        full = urljoin(BASE_URL, href.split("?")[0].split("#")[0])
        # must be a detail URL like /mods/<slug>/ or /mod/<slug>/
        if full.rstrip("/").endswith("/mods"):
            continue
        links.add(full)
    return list(links)


def discover_planetminecraft(max_pages=None):
    pages = max_pages or _mode_pages()
    published = 0
    seen = 0

    for page in range(1, pages + 1):
        url = MODS_URL if page == 1 else f"{MODS_URL}?page={page}"
        html = get_html(url)
        if not html:
            log.warning("[PlanetMinecraft] failed to fetch page %d", page)
            break
        links = _extract_links(html)
        log.info("[PlanetMinecraft] page %d: %d candidate links", page, len(links))
        if not links:
            break
        for link in links:
            seen += 1
            try:
                overrides = {
                    "category": "mods",
                    "source": {"name": "Planet Minecraft", "base_url": BASE_URL},
                    "is_verified": False,
                }
                data = parse_mod_page(link, overrides=overrides)
                if data and publish_item(data):
                    published += 1
            except Exception as e:
                log.exception("[PlanetMinecraft] error on %s: %s", link, e)

    log.info("[PlanetMinecraft] cycle done: scanned=%d published=%d", seen, published)
    return published
