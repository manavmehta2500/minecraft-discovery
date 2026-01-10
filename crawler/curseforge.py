import requests
from bs4 import BeautifulSoup
from parser.parse_mod import parse_mod_page
from publisher.publish import publish_item

BASE_URL = "https://www.curseforge.com/minecraft/mc-mods"
HEADERS = {"User-Agent": "Mozilla/5.0"}

def get_mod_links(page=1):
    url = f"{BASE_URL}?page={page}"
    html = requests.get(url, headers=HEADERS, timeout=15).text
    soup = BeautifulSoup(html, "lxml")
    links = []
    for card in soup.select("a.project-title"):
        links.append("https://www.curseforge.com" + card["href"])
    return links

def discover_curseforge(max_pages=5):
    for page in range(1, max_pages + 1):
        links = get_mod_links(page)
        for link in links:
            data = parse_mod_page(link)
            data.update({
                "category": "mods",
                "source": {"name": "CurseForge", "base_url": "https://www.curseforge.com"},
                "external_url": link,
                "is_verified": True
            })
            publish_item(data)