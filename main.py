# main.py – Sentibot with Smart Universe & Email Report (with attachment)
import os
import pandas as pd
from datetime import datetime, date
from sentiment_analyzer import analyze_sentiment
from news_scraper import fetch_news_titles
from smart_universe import get_smart_universe
from recommender import make_recommendation
from alpaca_trader import trade_stock
from email_sender import send_run_success_email  # ✅ ייבוא הפונקציה

# הגדרות בסיסיות
DATE_STR = date.today().isoformat()
NOW = datetime.now().isoformat()
RUN_ID = NOW[:19].replace(":", "-")
LOG_PATH = f"learning_log_{DATE_STR}.csv"

def main():
    symbols = get_smart_universe()
    log_rows = []

    for symbol in symbols:
        print(f"\n🔍 Processing {symbol}")
        all_titles = fetch_news_titles(symbol)

        sentiments = []
        for title, source in all_titles:
            score = analyze_sentiment(title, source)
            sentiments.append((title, source, score))

        if not sentiments:
            print(f"No headlines found for {symbol}")
            continue

        avg_score = round(sum(score for _, _, score in sentiments) / len(sentiments), 3)
        recommendation = make_recommendation(avg_score)

        print(f"🧠 Sentiment for {symbol}: {avg_score} → {recommendation}")
        trade_result = trade_stock(symbol, recommendation)

        log_rows.append({
            "timestamp": NOW,
            "symbol": symbol,
            "avg_sentiment": avg_score,
            "recommendation": recommendation,
            "trade_result": trade_result,
            "headlines": "; ".join(f"{s} [{src}]" for s, src, _ in sentiments)
        })

    if log_rows:
        df = pd.DataFrame(log_rows)
        df.to_csv(LOG_PATH, index=False)
        send_run_success_email(RUN_ID, LOG_PATH)  # ✅ שליחת מייל עם קובץ
    else:
        print("⚠️ No data to log or send.")

if __name__ == "__main__":
    main()
