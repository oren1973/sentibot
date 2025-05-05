import os
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("ALPACA_PAPER_BASE_URL", "https://paper-api.alpaca.markets")
API_KEY = os.getenv("ALPACA_API_KEY")
SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")

HEADERS = {
    "APCA-API-KEY-ID": API_KEY,
    "APCA-API-SECRET-KEY": SECRET_KEY
}

print("📡 מנסה לבצע פקודת קנייה לבדיקה...")

test_order = {
    "symbol": "AAPL",
    "qty": 1,
    "side": "buy",
    "type": "market",
    "time_in_force": "gtc"
}

response = requests.post(f"{BASE_URL}/v2/orders", json=test_order, headers=HEADERS)

print(f"🧾 סטטוס: {response.status_code}")
print(f"📬 תגובת השרת:\n{response.text}")
