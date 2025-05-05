# alpaca_test.py
import os
import requests

# קריאה למשתני הסביבה
API_KEY = os.getenv("ALPACA_API_KEY")
SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")
BASE_URL = os.getenv("ALPACA_PAPER_BASE_URL", "https://paper-api.alpaca.markets/v2")

HEADERS = {
    "APCA-API-KEY-ID": API_KEY,
    "APCA-API-SECRET-KEY": SECRET_KEY
}

# פקודת קנייה לבדיקה
test_order = {
    "symbol": "AAPL",
    "qty": 1,
    "side": "buy",
    "type": "market",
    "time_in_force": "gtc"
}

print("📡 מנסה לבצע פקודת קנייה לבדיקה...")

try:
    response = requests.post(f"{BASE_URL}/orders", json=test_order, headers=HEADERS)
    print(f"🧾 סטטוס: {response.status_code}")
    print("📬 תגובת השרת:")
    print(response.text)
except Exception as e:
    print("❌ שגיאה בעת שליחת הבקשה:")
    print(str(e))
