import os
import sys
import pandas as pd
from datetime import datetime
from news_aggregator import fetch_all_news
from sentiment_analyzer import analyze_sentiment
from recommender import make_recommendation
from smart_universe import SYMBOLS
from config import MAX_TITLES_PER_SOURCE
from email_sender import send_run_success_email

def main(force_run=False):
    run_id = int(datetime.now().timestamp())
    print(f"🚀 Starting Sentibot run #{run_id}")

    all_data = []

    for symbol in SYMBOLS:
        print(f"\n📰 CNBC headlines scanned for {symbol}:")
        try:
            titles_by_source = fetch_news_titles(symbol)

            if not titles_by_source:
                print(f"⚠️ No titles found for {symbol}")
                continue

            for source, titles in titles_by_source.items():
                limited_titles = titles[:MAX_TITLES_PER_SOURCE]
                for title in limited_titles:
                    print(f"- {title}")
                    sentiment = analyze_sentiment(title)
                    all_data.append({
                        "run_id": run_id,
                        "symbol": symbol,
                        "source": source,
                        "title": title,
                        "sentiment": sentiment,
                        "timestamp": datetime.now().isoformat()
                    })
        except Exception as e:
            print(f"⚠️ שגיאה בטיפול ב־{symbol}: {e}")

    if not all_data:
        print("❌ לא נמצאו כותרות או כל הכותרות נכשלו.")
        return

    df = pd.DataFrame(all_data)
    df.to_csv("diagnostic_report.csv", index=False)
    print("📄 Saved full report: diagnostic_report.csv")

    summary = (
        df.groupby("symbol")["sentiment"]
        .mean()
        .reset_index()
        .rename(columns={"sentiment": "avg_sentiment"})
        .sort_values(by="avg_sentiment", ascending=False)
    )
    summary.to_csv("diagnostic_summary.csv", index=False)
    print("📊 Saved summary: diagnostic_summary.csv")

    titles_overview = (
        df.groupby("symbol")
        .apply(lambda x: list(x["title"]))
        .reset_index()
        .rename(columns={0: "titles"})
    )
    titles_overview.to_csv("diagnostic_titles.csv", index=False)
    print("📝 Saved titles overview: diagnostic_titles.csv")

    send_run_success_email(run_id, attachment_path="diagnostic_summary.csv")

if __name__ == "__main__":
    force = False
    if len(sys.argv) > 1 and sys.argv[1] == "force":
        force = True
    main(force)
