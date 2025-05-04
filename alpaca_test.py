import requests
import os

API_KEY = os.getenv("ALPACA_API_KEY")
SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")
BASE_URL = os.getenv("ALPACA_PAPER_BASE_URL", "https://paper-api.alpaca.markets")

url = f"{BASE_URL}/v2/account"
headers = {
    "APCA-API-KEY-ID": API_KEY,
    "APCA-API-SECRET-KEY": SECRET_KEY
}

print("בודק גישה ל-Alpaca...")
response = requests.get(url, headers=headers)

print("תשובה מהשרת:")
print("סטטוס:", response.status_code)
print("גוף:", response.text)
