# Minecraft Discovery Platform

A long-running background worker that crawls Minecraft mod sites, normalizes mod
metadata, and upserts records into a Lovable-backed API. Admin edits on the
Lovable side override AI forever; everything else is re-synced automatically
every cycle.

## Sources

| Source | Method | Key required? |
| --- | --- | --- |
| [IJAMinecraft](https://ijaminecraft.com/mods) | HTML scrape (server-rendered) | No |
| [CurseForge](https://www.curseforge.com/minecraft/mc-mods) | Official API preferred; HTML fallback | Optional `CURSEFORGE_API_KEY` |
| [Modrinth](https://modrinth.com/mods) | Public REST v2 API (UA required, no key) | No |
| [Planet Minecraft](https://www.planetminecraft.com/mods/) | HTML scrape | No |

Additional sources live in `crawler/new_sources.py` — drop a new module in and
register it there.

## Local quickstart

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then fill in LOVABLE_API_URL / LOVABLE_API_KEY
python loop.py
```

Try a single dry-run cycle first:

```bash
DRY_RUN=true DISCOVERY_MODE=SMOKE python loop.py
```

## Deployment to Railway

1. Push this folder (or connect the repo) to a new Railway service.
2. Choose a **Worker** deploy (no public port is exposed). Railway will use
   `Procfile` / `railway.json` automatically.
3. Set environment variables in the Railway dashboard:
   - `LOVABLE_API_URL` **(required)** – base URL of your Lovable backend.
   - `LOVABLE_API_KEY` **(required)** – bearer token for `/items/upsert`.
   - `CURSEFORGE_API_KEY` *(recommended)* – free key from
     https://console.curseforge.com/ for reliable CurseForge ingestion.
   - `MAX_ITEMS` – cap items per cycle (default `1000`).
   - `SLEEP_BETWEEN_CYCLES` – seconds between cycles (default `3600` = 1h).
   - `DISCOVERY_MODE` – `SMOKE` (debug, 1 page), `FAST` (default), or `FULL`.
   - `DRY_RUN` – `true` to skip all POSTs (log-only).
4. Deploy. The worker starts with `python loop.py` and runs forever.

## Code layout

```
config.py                # env-var configuration
loop.py                  # main infinite loop, signal handling, MAX_ITEMS cap
crawler/
  _http.py               # shared GET/JSON/HTML with retries + rate limit
  ijaminecraft.py        # HTML crawler
  curseforge.py          # Official API + __NEXT_DATA__ HTML fallback
  modrinth.py            # Modrinth v2 API crawler
  planetminecraft.py     # HTML crawler (extra source)
  new_sources.py         # registry for extra sources
parser/
  parse_mod.py           # normalize_item() + HTML-page parser fallback
publisher/
  publish.py             # POST /items/upsert with auth + dry-run
```

Every item published has this shape:

```json
{
  "name": "Mod Name",
  "description": "...",
  "image_url": "https://...",
  "external_url": "https://...",
  "external_hash": "sha256(...)",
  "category": "mods",
  "source": { "name": "Modrinth", "base_url": "https://modrinth.com" },
  "is_verified": true,
  "author": "...",
  "downloads": 12345,
  "categories": ["adventure", "..."],
  "published_at": "..."
}
```

## Admin overrides

The Lovable backend is expected to treat any field that has been manually edited
by an admin as "locked" — future discovery cycles will upsert around those
fields, never overwriting them. `external_hash` is sent so the backend can skip
rewrites when nothing changed.
