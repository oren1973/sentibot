import os
import requests
from dotenv import load_dotenv
from sentiment import get_sentiment_score  # מניח שקיים

load_dotenv()

BASE_URL = os.getenv("ALPACA_PAPER_BASE_URL", "https://paper-api.alpaca.markets")
API_KEY = os.getenv("ALPACA_API_KEY")
SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")

HEADERS = {
    "APCA-API-KEY-ID": API_KEY,
    "APCA-API-SECRET-KEY": SECRET_KEY
}

# === PARAMETERS ===
symbol = "AAPL"
qty = 1

# === STEP 1: get sentiment ===
print(f"🔍 מחשב סנטימנט עבור {symbol}...")
sentiment_score = get_sentiment_score(symbol)
print(f"🧠 ציון סנטימנט: {sentiment_score}")

# === STEP 2: decide ===
if sentiment_score > 0.4:
    action = "buy"
elif sentiment_score < -0.4:
    action = "sell"
else:
    action = "hold"

print(f"📊 החלטה: {action.upper()}")

# === STEP 3: send order ===
if action in ["buy", "sell"]:
    order = {
        "symbol": symbol,
        "qty": qty,
        "side": action,
        "type": "market",
        "time_in_force": "gtc"
    }

    print(f"📡 שולח פקודת {action.upper()}...")
    response = requests.post(f"{BASE_URL}/v2/orders", json=order, headers=HEADERS)
    print(f"🧾 סטטוס: {response.status_code}")
    print(f"📬 תגובת השרת:\n{response.text}")
else:
    print("⏸ אין פעולה. שמירה על מצב קיים.")
