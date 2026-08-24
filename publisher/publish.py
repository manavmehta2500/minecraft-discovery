"""Publish items by merging them into data/mods.json in the repo."""
import json
import logging
import hashlib
import threading
from datetime import datetime, timezone
from pathlib import Path

log = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
MODS_PATH = DATA_DIR / "mods.json"
LOCKS_PATH = DATA_DIR / "locks.json"

_lock = threading.Lock()
_mods_cache = None
_locks_cache = None


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _load_json(path, default):
    try:
        if path.exists():
            with path.open("r", encoding="utf-8") as f:
                return json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        log.warning("Couldn't read %s: %s - starting fresh", path.name, e)
    return default


def _save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=False)
    tmp.replace(path)


def _load_all():
    global _mods_cache, _locks_cache
    if _mods_cache is None:
        _mods_cache = _load_json(MODS_PATH, [])
        _locks_cache = _load_json(LOCKS_PATH, {})
    return _mods_cache, _locks_cache


def _stable_id(url):
    return hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]


def publish_item(data):
    if not data or not data.get("external_url"):
        return False
    with _lock:
        mods, locks = _load_all()
        url = data["external_url"]
        now = _now()
        locked_fields = locks.get(url, {})
        existing = next((m for m in mods if m.get("external_url") == url), None)
        if existing is None:
            new_item = {
                "id": _stable_id(url),
                "name": data.get("name") or "Unknown Mod",
                "description": data.get("description") or "",
                "image_url": data.get("image_url") or "",
                "external_url": url,
                "external_hash": data.get("external_hash") or "",
                "category": data.get("category") or "mods",
                "source": data.get("source") or {},
                "is_verified": bool(data.get("is_verified")),
                "author": data.get("author") or "",
                "downloads": data.get("downloads") or 0,
                "categories": data.get("categories") or [],
                "published_at": data.get("published_at") or now,
                "discovered_at": now,
                "updated_at": now,
                "admin_locked": sorted(locked_fields.keys()),
            }
            mods.append(new_item)
            _save_json(MODS_PATH, mods)
            log.info("New mod: %s", new_item["name"])
            return True
        changed = False
        if existing.get("external_hash") != data.get("external_hash"):
            for field in ("name", "description", "image_url"):
                if field in locked_fields:
                    continue
                new_val = data.get(field)
                if new_val and new_val != existing.get(field):
                    existing[field] = new_val
                    changed = True
            existing["external_hash"] = data.get("external_hash") or existing.get("external_hash")
            changed = True
        if data.get("downloads") is not None and data.get("downloads") != existing.get("downloads"):
            existing["downloads"] = data.get("downloads")
            changed = True
        if data.get("categories") and data.get("categories") != existing.get("categories") and "categories" not in locked_fields:
            existing["categories"] = data.get("categories")
            changed = True
        existing["is_verified"] = bool(data.get("is_verified", existing.get("is_verified")))
        if data.get("source") and not existing.get("source"):
            existing["source"] = data.get("source")
        existing["admin_locked"] = sorted(locked_fields.keys())
        if changed:
            existing["updated_at"] = now
            _save_json(MODS_PATH, mods)
            log.info("Updated: %s", existing.get("name"))
        return changed


def flush():
    pass