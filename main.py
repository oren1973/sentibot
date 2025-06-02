# main.py – Sentibot עם בדיקת חוזרנות כותרות – גרסה 2025-05-31
import os
import pandas as pd
from datetime import datetime, date
from sentiment_analyzer import analyze_sentiment
from news_scraper import fetch_news_titles
from smart_universe import get_smart_universe
from recommender import make_recommendation
from alpaca_trader import trade_stock
from email_sender import send_run_success_email

# הגדרות בסיסיות
DATE_STR = date.today().isoformat()
NOW = datetime.now().isoformat()
LOG_DIR = "logs"
LOG_FILENAME = f"learning_log_{DATE_STR}.csv"
LOG_PATH = os.path.join(LOG_DIR, LOG_FILENAME)

def main():
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

    symbols = get_smart_universe()
    log_rows = []

    for symbol in symbols:
        print(f"\n🔍 Processing {symbol}")
        all_titles = fetch_news_titles(symbol)

        if not all_titles:
            print(f"⚠️ No headlines to analyze for {symbol}")
            continue

        sentiments = []
        for title, source in all_titles:
            score = analyze_sentiment(title, source)
            sentiments.append((title, source, score))

        if not sentiments:
            print(f"⚠️ No valid sentiments found for {symbol}")
            continue

        scores_only = [s for _, _, s in sentiments]
        if len(set(scores_only)) == 1:
            print(f"⚠️ All sentiment scores identical ({scores_only[0]}) for {symbol}")

        avg_score = round(sum(scores_only) / len(scores_only), 3)
        recommendation = make_recommendation(avg_score)

        print(f"🧠 Sentiment for {symbol}: {avg_score} → {recommendation}")
        trade_result = trade_stock(symbol, recommendation)

        log_rows.append({
            "timestamp": NOW,
            "symbol": symbol,
            "avg_sentiment": avg_score,
            "recommendation": recommendation["decision"],
            "score_used": recommendation["score"],
            "trade_result": trade_result,
            "headlines": "; ".join(f"{s} [{src}]" for s, src, _ in sentiments)
        })

    if log_rows:
        df = pd.DataFrame(log_rows)
        if os.path.exists(LOG_PATH):
            df.to_csv(LOG_PATH, mode='a', header=False, index=False)
        else:
            df.to_csv(LOG_PATH, index=False)
        print(f"\n📁 Log saved to {LOG_PATH}")
    else:
        print("⚠️ No data to log.")

    # שליחת מייל כולל קובץ תוצרים
    run_id = NOW.replace(":", "-").replace("T", "_").split(".")[0]
    send_run_success_email(run_id, LOG_PATH if log_rows else None)

if __name__ == "__main__":
    main()
