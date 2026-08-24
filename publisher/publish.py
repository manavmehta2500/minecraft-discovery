"""Publish normalized items to the Lovable backend."""
import logging
import requests

from config import LOVABLE_API_URL, LOVABLE_API_KEY, DRY_RUN, REQUEST_TIMEOUT

log = logging.getLogger(__name__)

_BATCH = []
_BATCH_SIZE = 25


def _headers():
    return {
        "Authorization": f"Bearer {LOVABLE_API_KEY}",
        "Content-Type": "application/json",
    }


def _post(payload):
    if DRY_RUN:
        log.info("[DRY RUN] Would publish %s", payload.get("name"))
        return True

    if not LOVABLE_API_URL:
        log.error("LOVABLE_API_URL is not configured — skipping publish")
        return False
    if not LOVABLE_API_KEY:
        log.error("LOVABLE_API_KEY is not configured — skipping publish")
        return False

    url = f"{LOVABLE_API_URL}/items/upsert"
    try:
        resp = requests.post(url, json=payload, headers=_headers(), timeout=REQUEST_TIMEOUT)
        if resp.status_code in (200, 201):
            log.info("Published: %s", payload.get("name"))
            return True
        log.error(
            "Failed to publish %s: HTTP %s — %s",
            payload.get("name"), resp.status_code, resp.text[:300],
        )
    except requests.RequestException as e:
        log.error("Publish error for %s: %s", payload.get("name"), e)
    return False


def publish_item(data):
    """Publish a single normalized item. Returns True/False."""
    if not data or not data.get("name"):
        return False
    return _post(data)


def publish_batch(items):
    """Publish a list of normalized items sequentially. Returns success count."""
    ok = 0
    for item in items:
        if publish_item(item):
            ok += 1
    return ok


def flush():
    """Hook if you later want buffered batch publishing."""
    global _BATCH
    _BATCH = []
