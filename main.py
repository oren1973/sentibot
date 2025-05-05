import os
import csv
import requests
from dotenv import load_dotenv
from sentiment import get_sentiment_score

load_dotenv()

BASE_URL = os.getenv("ALPACA_PAPER_BASE_URL", "https://paper-api.alpaca.markets")
API_KEY = os.getenv("ALPACA_API_KEY")
SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")

HEADERS = {
    "APCA-API-KEY-ID": API_KEY,
    "APCA-API-SECRET-KEY": SECRET_KEY
}

def read_tickers(file_path="tickers.csv"):
    with open(file_path, newline='') as f:
        return [row[0].strip().upper() for row in csv.reader(f) if row]

def log_action(symbol, sentiment, action, response_status):
    with open("log.csv", "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([symbol, sentiment, action, response_status])

def trade(symbol, action, qty=1):
    order = {
        "symbol": symbol,
        "qty": qty,
        "side": action,
        "type": "market",
        "time_in_force": "gtc"
    }
    print(f"📡 {symbol}: שולח פקודת {action.upper()}...")
    res = requests.post(f"{BASE_URL}/v2/orders", json=order, headers=HEADERS)
    print(f"🧾 {symbol}: סטטוס: {res.status_code}")
    print(f"📬 {symbol}: תגובת השרת:\n{res.text}")
    return res.status_code

# === Loop over tickers ===
tickers = read_tickers()

for symbol in tickers:
    print(f"\n🔍 מחשב סנטימנט עבור {symbol}...")
    score = get_sentiment_score(symbol)
    print(f"🧠 {symbol}: ציון סנטימנט: {score}")

    if score > 0.4:
        action = "buy"
    elif score < -0.4:
        action = "sell"
    else:
        action = "hold"

    print(f"📊 {symbol}: החלטה: {action.upper()}")

    if action != "hold":
        status = trade(symbol, action)
    else:
        status = "no_action"

    log_action(symbol, score, action, status)
