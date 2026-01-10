# Minecraft Discovery Platform

## Deployment Instructions

1. Upload this folder to Railway.
2. Set environment variables:
   - LOVABLE_API_URL
   - LOVABLE_API_KEY
   - MAX_ITEMS (default 1000)
   - SLEEP_BETWEEN_CYCLES (default 3600)
3. Start loop.py as a background worker.
4. The system will automatically discover mods from IJAMinecraft, CurseForge, and Modrinth.
5. Admin edits override AI forever; everything else updates automatically.