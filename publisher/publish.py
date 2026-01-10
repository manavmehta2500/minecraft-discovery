import requests
from config import LOVABLE_API_URL, LOVABLE_API_KEY

def publish_item(data):
    headers = {
        "Authorization": f"Bearer {LOVABLE_API_KEY}",
        "Content-Type": "application/json"
    }
    response = requests.post(f"{LOVABLE_API_URL}/items/upsert", json=data, headers=headers)
    if response.status_code == 200:
        print(f"Published: {data['name']}")
    else:
        print(f"Failed to publish {data['name']}: {response.text}")