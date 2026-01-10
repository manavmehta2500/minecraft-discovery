import requests
from bs4 import BeautifulSoup
from parser.parse_mod import parse_mod_page
from publisher.publish import publish_item

BASE_URL = "https://ijaminecraft.com/mods"

def discover_ijaminecraft():
    html = requests.get(BASE_URL, timeout=15).text
    soup = BeautifulSoup(html, "lxml")

    for card in soup.select(".mod-card a"):
        link = card["href"]
        mod_data = parse_mod_page(link)
        mod_data.update({
            "category": "mods",
            "source": {"name": "IJAMinecraft", "base_url": "https://ijaminecraft.com"},
            "external_url": link,
            "is_verified": True
        })
        publish_item(mod_data)