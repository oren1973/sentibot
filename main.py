# main.py – Sentibot with Smart Universe & Email Report May 31, 2025 5:21PM
import os
import pandas as pd
from datetime import datetime, date
from sentiment_analyzer import analyze_sentiment
from news_scraper import fetch_news_titles
from smart_universe import get_smart_universe
from recommender import make_recommendation
from alpaca_trader import trade_stock

# הגדרות בסיסיות
DATE_STR = date.today().isoformat()
NOW = datetime.now().isoformat()
LOG_PATH = "learning_log.csv"

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
        if os.path.exists(LOG_PATH):
            df.to_csv(LOG_PATH, mode='a', header=False, index=False)
        else:
            df.to_csv(LOG_PATH, index=False)

if __name__ == "__main__":
    main()

