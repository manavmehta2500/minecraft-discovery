"""Shared HTTP helpers: retries, rate-limiting, user-agent."""
import time
import logging
import requests

from config import REQUEST_TIMEOUT, REQUEST_DELAY, MAX_RETRIES, USER_AGENT

log = logging.getLogger(__name__)

_DEFAULT_HEADERS = {"User-Agent": USER_AGENT, "Accept": "*/*"}


def get(url, headers=None, params=None, timeout=None, expect_json=False):
    """GET with retries + simple delay between calls. Returns Response or None on failure."""
    hdrs = {**_DEFAULT_HEADERS, **(headers or {})}
    to = timeout or REQUEST_TIMEOUT

    last_err = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            if REQUEST_DELAY > 0:
                time.sleep(REQUEST_DELAY)
            resp = requests.get(url, headers=hdrs, params=params, timeout=to)
            if resp.status_code == 429:
                retry_after = int(resp.headers.get("Retry-After", 5))
                log.warning("Rate-limited on %s — sleeping %ds", url, retry_after)
                time.sleep(retry_after)
                continue
            if 500 <= resp.status_code < 600:
                log.warning("Server %d on %s (attempt %d/%d)", resp.status_code, url, attempt, MAX_RETRIES)
                time.sleep(attempt * 2)
                continue
            resp.raise_for_status()
            return resp
        except (requests.RequestException, ValueError) as e:
            last_err = e
            log.warning("HTTP error on %s (attempt %d/%d): %s", url, attempt, MAX_RETRIES, e)
            time.sleep(attempt * 2)

    log.error("Giving up on %s after %d attempts: %s", url, MAX_RETRIES, last_err)
    return None


def get_json(url, headers=None, params=None):
    resp = get(url, headers=headers, params=params, expect_json=True)
    if resp is None:
        return None
    try:
        return resp.json()
    except ValueError as e:
        log.error("Invalid JSON from %s: %s", url, e)
        return None


def get_html(url, headers=None, params=None):
    resp = get(url, headers=headers, params=params)
    if resp is None:
        return None
    return resp.text
