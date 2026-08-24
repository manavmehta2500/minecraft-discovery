"""Crawler for CurseForge Minecraft mods.

Two strategies:
  1) Official CurseForge API (preferred) if CURSEFORGE_API_KEY is set.
     Docs: https://docs.curseforge.com/  — gameId=432 for Minecraft, classId=6 for mods.
  2) Fallback: scrape the public listing page which ships __NEXT_DATA__ JSON on first load.
     We pull project slugs out of that embedded JSON.
"""
import json
import logging
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from config import (
    CURSEFORGE_API_KEY,
    CURSEFORGE_GAME_ID,
    DISCOVERY_MODE,
    USER_AGENT,
)
from crawler._http import get_json, get_html
from parser.parse_mod import normalize_item
from publisher.publish import publish_item

WEB_BASE = "https://www.curseforge.com"
API_BASE = "https://api.curseforge.com/v1"
MOD_CLASS_ID = 6  # Minecraft mods class

log = logging.getLogger(__name__)


def _mode_limits():
    mode = DISCOVERY_MODE
    if mode == "SMOKE":
        return {"pages": 1, "per_page": 20}
    if mode == "FULL":
        return {"pages": 8, "per_page": 50}
    return {"pages": 3, "per_page": 30}  # FAST


# ---------- Strategy 1: Official API ----------

def _api_headers():
    return {
        "x-api-key": CURSEFORGE_API_KEY,
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
    }


def _api_search(index, page_size):
    params = {
        "gameId": CURSEFORGE_GAME_ID,
        "classId": MOD_CLASS_ID,
        "sortField": 2,  # 2 = Popularity/TotalDownloads
        "sortOrder": "desc",
        "index": index,
        "pageSize": page_size,
    }
    return get_json(f"{API_BASE}/mods/search", headers=_api_headers(), params=params)


def _discover_api(pages, per_page):
    published = 0
    seen = 0
    for page in range(pages):
        data = _api_search(page * per_page, per_page)
        if not data:
            log.warning("[CurseForge:API] empty/error on page %d", page + 1)
            break
        mods = data.get("data", [])
        if not mods:
            break
        log.info("[CurseForge:API] page %d: %d mods", page + 1, len(mods))
        for m in mods:
            seen += 1
            links = m.get("links") or {}
            web_url = links.get("websiteUrl") or m.get("websiteUrl")
            logo = m.get("logo") or {}
            author = (m.get("authors") or [{}])[0] if m.get("authors") else {}
            raw = {
                "name": m.get("name"),
                "description": m.get("summary"),
                "image_url": logo.get("thumbnailUrl") or logo.get("url") or "",
                "external_url": web_url,
                "author": author.get("name") or author.get("username"),
                "downloads": m.get("downloadCount", 0),
                "categories": [c.get("name") for c in (m.get("categories") or []) if c.get("name")],
                "published_at": m.get("dateCreated"),
                "category": "mods",
                "source": {"name": "CurseForge", "base_url": WEB_BASE},
                "is_verified": True,
            }
            item = normalize_item(raw)
            if item and publish_item(item):
                published += 1
    return seen, published


# ---------- Strategy 2: scrape __NEXT_DATA__ ----------

def _scrape_links(page):
    url = f"{WEB_BASE}/minecraft/mc-mods"
    params = {"page": page}
    html = get_html(url, params=params)
    if not html:
        return []

    soup = BeautifulSoup(html, "lxml")

    # CurseForge renders listings via Next.js; the server response embeds JSON in
    # <script id="__NEXT_DATA__">.  We pull that for reliable slug extraction.
    next_data = soup.find("script", id="__NEXT_DATA__")
    if next_data and next_data.string:
        try:
            data = json.loads(next_data.string)
            slugs = []
            # Traverse recursively to find entries with a `slug` + `classId` == 6
            _walk_next_data(data, slugs)
            if slugs:
                return [
                    urljoin(WEB_BASE, f"/minecraft/mc-mods/{slug}") for slug in slugs
                ]
        except json.JSONDecodeError as e:
            log.warning("[CurseForge:scrape] __NEXT_DATA__ parse failed: %s", e)

    # Fallback: any anchor pointing at /minecraft/mc-mods/<slug>
    links = set()
    for a in soup.select("a[href]"):
        href = a.get("href", "")
        if href.startswith("/minecraft/mc-mods/") and href.count("/") == 3:
            links.add(urljoin(WEB_BASE, href))
    return list(links)


def _walk_next_data(obj, out):
    if isinstance(obj, dict):
        if obj.get("classId") == MOD_CLASS_ID and obj.get("slug"):
            out.append(obj["slug"])
        for v in obj.values():
            _walk_next_data(v, out)
    elif isinstance(obj, list):
        for v in obj:
            _walk_next_data(v, out)


def _scrape_mod_detail(url):
    html = get_html(url)
    if not html:
        return None
    soup = BeautifulSoup(html, "lxml")
    name = None
    summary = None
    image = None

    h1 = soup.select_one("h1")
    if h1:
        name = h1.get_text(strip=True)
    ogd = soup.find("meta", property="og:description")
    if ogd and ogd.get("content"):
        summary = ogd["content"]
    ogi = soup.find("meta", property="og:image")
    if ogi and ogi.get("content"):
        image = ogi["content"]

    return normalize_item({
        "name": name,
        "description": summary,
        "image_url": image,
        "external_url": url,
    })


def _discover_scrape(pages, per_page=None):
    published = 0
    seen = 0
    for page in range(1, pages + 1):
        links = _scrape_links(page)
        if not links:
            log.info("[CurseForge:scrape] no links on page %d — stopping", page)
            break
        log.info("[CurseForge:scrape] page %d: %d links", page, len(links))
        for link in links:
            seen += 1
            try:
                base = _scrape_mod_detail(link)
                if not base:
                    continue
                base.update({
                    "category": "mods",
                    "source": {"name": "CurseForge", "base_url": WEB_BASE},
                    "is_verified": True,
                })
                if publish_item(base):
                    published += 1
            except Exception as e:
                log.exception("[CurseForge:scrape] error on %s: %s", link, e)
    return seen, published


# ---------- Public entry point ----------

def discover_curseforge(max_pages=None, max_per_page=None):
    limits = _mode_limits()
    pages = max_pages or limits["pages"]
    per_page = max_per_page or limits["per_page"]

    if CURSEFORGE_API_KEY:
        log.info("[CurseForge] using official API (key present)")
        seen, published = _discover_api(pages, per_page)
    else:
        log.info("[CurseForge] CURSEFORGE_API_KEY not set; using HTML scrape fallback")
        seen, published = _discover_scrape(pages, per_page)

    log.info("[CurseForge] cycle done: scanned=%d published=%d", seen, published)
    return published
