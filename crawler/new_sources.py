"""Placeholder for future discovery sources.

To add a new source:
  1) create crawler/<sitename>.py with a discover_<sitename>() function
     that returns the count of successfully published items.
  2) import and call it from discover_new_sources() below.

Active additional source(s):
  - PlanetMinecraft (see crawler/planetminecraft.py)
"""
import logging

from crawler import planetminecraft

log = logging.getLogger(__name__)


def discover_new_sources():
    """Run discovery for all "extra" sources beyond the big three."""
    total = 0
    try:
        total += planetminecraft.discover_planetminecraft() or 0
    except Exception as e:
        log.exception("[new_sources] PlanetMinecraft failed: %s", e)
    return total
