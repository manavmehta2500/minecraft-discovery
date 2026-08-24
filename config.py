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


# ---- Backend (legacy: Lovable HTTP POST) ----
LOVABLE_API_URL = os.getenv("LOVABLE_API_URL", "").rstrip("/")
LOVABLE_API_KEY = os.getenv("LOVABLE_API_KEY", "")

# ---- Storage ----
# "local" = write to data/mods.json (default, for GitHub Pages self-hosted mode)
# "lovable" = POST to LOVABLE_API_URL/items/upsert (legacy)
STORAGE_BACKEND = os.getenv("STORAGE_BACKEND", "local").lower()

# ---- Crawler knobs ----
MAX_ITEMS = _int("MAX_ITEMS", 1000)
SLEEP_BETWEEN_CYCLES = _int("SLEEP_BETWEEN_CYCLES", 3600)
REQUEST_TIMEOUT = _int("REQUEST_TIMEOUT", 20)
REQUEST_DELAY = _float("REQUEST_DELAY", 1.0)
MAX_RETRIES = _int("MAX_RETRIES", 3)

DISCOVERY_MODE = os.getenv("DISCOVERY_MODE", "FAST").upper()

# ---- Source-specific ----
CURSEFORGE_API_KEY = os.getenv("CURSEFORGE_API_KEY", "")
CURSEFORGE_GAME_ID = _int("CURSEFORGE_GAME_ID", 432)
MODRINTH_USER_AGENT = os.getenv(
    "MODRINTH_USER_AGENT",
    "minecraft-discovery/1.0 (+https://github.com/manavmehta2500/minecraft-discovery)",
)
USER_AGENT = os.getenv(
    "USER_AGENT",
    "Mozilla/5.0 (compatible; MinecraftDiscoveryBot/1.0; +https://github.com/manavmehta2500/minecraft-discovery)",
)

DRY_RUN = _bool("DRY_RUN", False)