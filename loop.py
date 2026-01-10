import time
from config import SLEEP_BETWEEN_CYCLES
from crawler import curseforge, modrinth, ijaminecraft

while True:
    print("Starting discovery cycle...")
    ijaminecraft.discover_ijaminecraft()
    curseforge.discover_curseforge(max_pages=5)
    modrinth.discover_modrinth(max_pages=5)
    # future: new_sources.discover_new_site()
    print(f"Cycle complete. Sleeping for {SLEEP_BETWEEN_CYCLES}s")
    time.sleep(SLEEP_BETWEEN_CYCLES)