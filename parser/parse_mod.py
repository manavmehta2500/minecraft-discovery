"""Normalize a mod/item record before publishing.

Two entry points:
  - normalize_item(fields)   -> clean, hash, dedupe-ready dict
  - parse_mod_page(url)      -> HTML-scrape fallback (used by IJAMinecraft/HTML crawlers)
"""
import hashlib
import logging

from bs4 import BeautifulSoup

log = logging.getLogger(__name__)

REQUIRED_FIELDS = ("name", "description", "external_url")


def _clean_str(value, default=""):
    if value is None:
        return default
    return " ".join(str(value).split()).strip() or default


def normalize_item(raw):
    """Normalize+validate a dict of raw mod fields. Returns None if unusable."""
    if not raw:
        return None

    name = _clean_str(raw.get("name"), "Unknown Mod")
    description = _clean_str(
        raw.get("description") or raw.get("summary") or raw.get("body"),
        "No description",
    )
    # Cap description length so we don't POST huge payloads
    if len(description) > 2000:
        description = description[:1997] + "..."

    image_url = raw.get("image_url") or raw.get("icon_url") or raw.get("logo") or ""
    if isinstance(image_url, dict):
        image_url = image_url.get("url") or image_url.get("thumbnailUrl") or ""
    image_url = _clean_str(image_url)

    external_url = _clean_str(raw.get("external_url") or raw.get("url"))
    if not external_url:
        log.warning("Dropping item with no external_url: %s", name)
        return None

    author_raw = raw.get("author") or raw.get("owner")
    if isinstance(author_raw, dict):
        author = _clean_str(
            author_raw.get("username") or author_raw.get("name")
            or author_raw.get("displayName") or author_raw.get("title")
        )
    else:
        author = _clean_str(author_raw)

    downloads = raw.get("downloads") or raw.get("downloadCount") or 0
    try:
        downloads = int(downloads)
    except (TypeError, ValueError):
        downloads = 0

    categories = raw.get("categories") or []
    if isinstance(categories, list):
        categories = [
            _clean_str(c["name"] if isinstance(c, dict) else c) for c in categories if c
        ]
        categories = [c for c in categories if c]

    # Stable content hash — same input => same output
    hash_key = f"{name}|{description}|{image_url}|{external_url}"
    content_hash = hashlib.sha256(hash_key.encode("utf-8")).hexdigest()

    item = {
        "name": name,
        "description": description,
        "image_url": image_url,
        "external_url": external_url,
        "external_hash": content_hash,
        "category": raw.get("category", "mods"),
        "source": raw.get("source", {"name": "Unknown", "base_url": ""}),
        "is_verified": bool(raw.get("is_verified", False)),
    }
    if author:
        item["author"] = author
    if downloads:
        item["downloads"] = downloads
    if categories:
        item["categories"] = categories
    if raw.get("published_at") or raw.get("date_created") or raw.get("datePublished"):
        item["published_at"] = raw.get("published_at") or raw.get("date_created") or raw.get("datePublished")

    return item


def parse_mod_page(url, overrides=None):
    """HTML fallback: fetch url, pull basic fields from <meta>/<h1>, normalize."""
    # Lazy import to avoid circular dependency with crawler._http
    from crawler._http import get_html  # noqa: WPS433

    html = get_html(url)
    if not html:
        return None

    soup = BeautifulSoup(html, "lxml")

    name_tag = soup.select_one("h1")
    name = name_tag.get_text(strip=True) if name_tag else None

    description = None
    for sel in [
        {"name": "description"},
        {"property": "og:description"},
        {"name": "twitter:description"},
    ]:
        tag = soup.find("meta", sel)
        if tag and tag.get("content"):
            description = tag["content"]
            break

    image_url = None
    for sel in [
        {"property": "og:image"},
        {"name": "twitter:image"},
    ]:
        tag = soup.find("meta", sel)
        if tag and tag.get("content"):
            image_url = tag["content"]
            break

    raw = {
        "name": name,
        "description": description,
        "image_url": image_url,
        "external_url": url,
    }
    if overrides:
        raw.update(overrides)

    return normalize_item(raw)
