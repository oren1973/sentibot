# sentibot_v1_3.1 – גרסה מעודכנת עם ניתוח כותרות מ-RSS של Yahoo Finance

import os
import csv
import requests
from datetime import datetime
from dotenv import load_dotenv
from sentiment import get_sentiment_score
from news_scraper import fetch_news_titles

VERSION = "Sentibot v1.3"
DATE = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

print(f"🚀 {VERSION} – {DATE}")

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

def log_action(timestamp, version, symbol, sentiment, action, status):
    with open("log.csv", "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([timestamp, version, symbol, sentiment, action, status])

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

def analyze_sentiment(symbol):
    print(f"\n🔍 מחשב סנטימנט עבור {symbol}...")
    headlines = fetch_news_titles(symbol)

    if not headlines:
        print(f"⚠️ {symbol}: לא נמצאו כותרות חדשות.")
        avg = 0.0
        decision = "HOLD"
    else:
        scores = []
        for h in headlines:
            score = get_sentiment_score(h)
            scores.append(score)
            print(f"📰 '{h}' → {score:.4f}")

        avg = sum(scores) / len(scores)

        if avg >= 0.25:
            decision = "buy"
        elif avg <= -0.25:
            decision = "sell"
        else:
            decision = "hold"

    print(f"📊 ממוצע סנטימנט עבור {symbol}: {avg:.3f}")
    print(f"🧠 {symbol}: ציון סנטימנט: {avg:.3f}")
    print(f"📊 {symbol}: החלטה: {decision.upper()}")

    if decision != "hold":
        status = trade(symbol, decision)
    else:
        status = "no_action"

    log_action(DATE, VERSION, symbol, avg, decision, status)

def main():
    tickers = read_tickers()
    for symbol in tickers:
        analyze_sentiment(symbol)

if __name__ == '__main__':
    main()
