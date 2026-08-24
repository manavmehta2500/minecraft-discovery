"""Main discovery loop.

Modes:
  python loop.py            # infinite loop (for Railway/Fly/always-on servers)
  python loop.py --once     # run ONE cycle and exit (for cron / GitHub Actions)
"""
import argparse
import logging
import signal
import sys
import time

from config import SLEEP_BETWEEN_CYCLES, MAX_ITEMS, DISCOVERY_MODE, DRY_RUN
from crawler import curseforge, modrinth, ijaminecraft, new_sources

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("loop")

_shutdown = False


def _handle_signal(signum, frame):
    global _shutdown
    log.info("Received signal %s — will exit after current source", signum)
    _shutdown = True


def _run_cycle():
    """Run one discovery cycle. Returns published_total."""
    published_total = 0

    sources = [
        ("IJAMinecraft",   ijaminecraft.discover_ijaminecraft),
        ("CurseForge",     curseforge.discover_curseforge),
        ("Modrinth",       modrinth.discover_modrinth),
        ("PlanetMC/etc.",  new_sources.discover_new_sources),
    ]

    for name, fn in sources:
        if _shutdown:
            break
        if published_total >= MAX_ITEMS:
            log.info("Reached MAX_ITEMS=%d — stopping cycle early", MAX_ITEMS)
            break
        log.info("--- Discovering %s ---", name)
        try:
            n = fn() or 0
            published_total += n
        except Exception as e:
            log.exception("Source %s raised: %s", name, e)

    return published_total


def main():
    parser = argparse.ArgumentParser(description="Minecraft mod discovery worker")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run a single discovery cycle and exit (use for cron / GitHub Actions).",
    )
    args = parser.parse_args()

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    log.info(
        "Minecraft Discovery starting (mode=%s, max_items=%d, sleep=%ds, dry_run=%s, once=%s)",
        DISCOVERY_MODE, MAX_ITEMS, SLEEP_BETWEEN_CYCLES, DRY_RUN, args.once,
    )

    if args.once:
        start = time.time()
        published = _run_cycle()
        log.info("One-shot cycle complete: published=%d, elapsed=%.1fs", published, time.time() - start)
        return 0

    cycle = 0
    while not _shutdown:
        cycle += 1
        log.info("========== Starting discovery cycle #%d ==========", cycle)
        start = time.time()
        try:
            published = _run_cycle()
        except Exception as e:
            log.exception("Unhandled error in cycle: %s", e)
            published = 0
        elapsed = time.time() - start
        log.info(
            "Cycle #%d complete: published=%d, elapsed=%.1fs. Sleeping %ds.",
            cycle, published, elapsed, SLEEP_BETWEEN_CYCLES,
        )

        slept = 0
        while slept < SLEEP_BETWEEN_CYCLES and not _shutdown:
            time.sleep(min(5, SLEEP_BETWEEN_CYCLES - slept))
            slept += 5

    log.info("Shutting down cleanly.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
