import os


def _int(name, default):
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


def _float(name, default):
    try:
        return float(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


def _bool(name, default=False):
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in ("1", "true", "yes", "on")


# ---- Lovable (backend) API ----
LOVABLE_API_URL = os.getenv("LOVABLE_API_URL", "").rstrip("/")
LOVABLE_API_KEY = os.getenv("LOVABLE_API_KEY", "")

# ---- Crawler knobs ----
MAX_ITEMS = _int("MAX_ITEMS", 1000)                 # cap items per cycle (total across sources)
SLEEP_BETWEEN_CYCLES = _int("SLEEP_BETWEEN_CYCLES", 3600)
REQUEST_TIMEOUT = _int("REQUEST_TIMEOUT", 20)
REQUEST_DELAY = _float("REQUEST_DELAY", 1.0)        # seconds between requests
MAX_RETRIES = _int("MAX_RETRIES", 3)

# DISCOVERY_MODE: FAST = top pages only; FULL = dig deeper; SMOKE = 1 page per source (debug)
DISCOVERY_MODE = os.getenv("DISCOVERY_MODE", "FAST").upper()

# ---- Source-specific ----
CURSEFORGE_API_KEY = os.getenv("CURSEFORGE_API_KEY", "")  # optional; if set, hits api.curseforge.com
CURSEFORGE_GAME_ID = _int("CURSEFORGE_GAME_ID", 432)      # 432 = Minecraft
MODRINTH_USER_AGENT = os.getenv(
    "MODRINTH_USER_AGENT",
    "minecraft-discovery/1.0 (+https://github.com/manavmehta2500/minecraft-discovery)",
)

USER_AGENT = os.getenv(
    "USER_AGENT",
    "Mozilla/5.0 (compatible; MinecraftDiscoveryBot/1.0; +https://github.com/manavmehta2500/minecraft-discovery)",
)

DRY_RUN = _bool("DRY_RUN", False)
