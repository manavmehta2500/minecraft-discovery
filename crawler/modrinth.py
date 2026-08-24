"""Crawler for Modrinth via their public REST API.

Docs: https://docs.modrinth.com/api/
No API key required; we just send a descriptive User-Agent per their rules.
"""
import logging

from config import MODRINTH_USER_AGENT, DISCOVERY_MODE
from crawler._http import get_json
from parser.parse_mod import normalize_item
from publisher.publish import publish_item

BASE_URL = "https://api.modrinth.com/v2"
WEB_BASE = "https://modrinth.com"

PROJECT_TYPES = ["mod"]  # could add "modpack", "resourcepack", "shader", "datapack" later

log = logging.getLogger(__name__)


def _mode_limits():
    mode = DISCOVERY_MODE
    if mode == "SMOKE":
        return {"pages": 1, "per_page": 10}
    if mode == "FULL":
        return {"pages": 10, "per_page": 50}
    # FAST (default)
    return {"pages": 3, "per_page": 30}


def _fetch_page(project_type, offset, limit):
    params = {
        "facets": f'[["project_type:{project_type}"]]',
        "offset": offset,
        "limit": limit,
        "index": "downloads",  # most downloaded first for relevance
    }
    headers = {"User-Agent": MODRINTH_USER_AGENT}
    return get_json(f"{BASE_URL}/search", headers=headers, params=params)


def discover_modrinth(max_pages=None, max_per_page=None):
    limits = _mode_limits()
    pages = max_pages or limits["pages"]
    per_page = max_per_page or limits["per_page"]

    published = 0
    seen = 0

    for project_type in PROJECT_TYPES:
        for page in range(pages):
            offset = page * per_page
            data = _fetch_page(project_type, offset, per_page)
            if not data:
                log.warning("[Modrinth] empty/error response for %s offset=%d", project_type, offset)
                break

            hits = data.get("hits", [])
            if not hits:
                break
            log.info("[Modrinth] page %d %s: %d hits", page + 1, project_type, len(hits))

            for hit in hits:
                seen += 1
                slug = hit.get("slug") or hit.get("project_id")
                if not slug:
                    continue
                web_url = f"{WEB_BASE}/{project_type}/{slug}"

                categories = hit.get("categories", []) + [
                    f"mc_version:{v}" for v in hit.get("versions", [])
                ]
                raw = {
                    "name": hit.get("title"),
                    "description": hit.get("description"),
                    "image_url": hit.get("icon_url"),
                    "external_url": web_url,
                    "author": hit.get("author"),
                    "downloads": hit.get("downloads", 0),
                    "categories": categories,
                    "published_at": hit.get("date_created"),
                    "category": "mods",
                    "source": {"name": "Modrinth", "base_url": WEB_BASE},
                    "is_verified": True,
                }
                item = normalize_item(raw)
                if item and publish_item(item):
                    published += 1

    log.info("[Modrinth] cycle done: scanned=%d published=%d", seen, published)
    return published
