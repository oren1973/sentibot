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

print("🔁 מנסה לבדוק גישה לחשבון Alpaca...")
res = requests.get(f"{BASE_URL}/v2/account", headers=HEADERS)
print(f"סטטוס: {res.status_code}")
print(res.text)
