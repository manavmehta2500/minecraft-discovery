import hashlib
from bs4 import BeautifulSoup
import requests

def parse_mod_page(url):
    html = requests.get(url, timeout=15).text
    soup = BeautifulSoup(html, "lxml")

    name_tag = soup.select_one("h1")
    name = name_tag.text.strip() if name_tag else "Unknown Mod"

    desc_tag = soup.find("meta", {"name": "description"})
    description = desc_tag["content"].strip() if desc_tag else "No description"

    image_tag = soup.find("meta", {"property": "og:image"})
    image_url = image_tag["content"] if image_tag else ""

    content_hash = hashlib.sha256(f"{name}{description}{image_url}".encode()).hexdigest()

    return {
        "name": name,
        "description": description,
        "image_url": image_url,
        "external_hash": content_hash
    }