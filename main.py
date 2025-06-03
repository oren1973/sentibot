# main.py

from smart_universe import get_smart_universe
from news_scraper import fetch_news_titles
from cnbc_scraper import fetch_cnbc_headlines
from sentiment_analyzer import analyze_sentiment_weighted
from recommender import make_recommendation
from email_sender import send_run_success_email
from diagnostic_report import generate_diagnostic_report
from settings import RUN_ID, TIMESTAMP, OUTPUT_FILE

import pandas as pd
import os

def main():
    symbols = get_smart_universe()
    results = []

    for symbol in symbols:
        try:
            titles_yahoo_investors = fetch_news_titles(symbol)
            titles_cnbc = fetch_cnbc_headlines(symbol)
            all_titles = titles_yahoo_investors + titles_cnbc

            if not all_titles:
                print(f"⚠️ אין כותרות זמינות עבור {symbol}")
                continue

            sentiment_score = analyze_sentiment_weighted(all_titles)
            rec = make_recommendation(sentiment_score)

            results.append({
                "symbol": symbol,
                "sentiment_score": sentiment_score,
                "decision": rec["decision"]
            })

            print(f"{symbol}: {rec['decision']} ({sentiment_score:.3f})")

        except Exception as e:
            print(f"❌ שגיאה בעיבוד {symbol}: {e}")

    if not results:
        print("❌ לא נוצרו תוצאות. ייתכן שאין כותרות או שיש תקלה.")
        return

    df = pd.DataFrame(results)
    df.to_csv(OUTPUT_FILE, index=False)

    send_run_success_email(RUN_ID, attachment_path=OUTPUT_FILE)
    generate_diagnostic_report(results)

    print(f"\n📈 הרצה {RUN_ID} הסתיימה. {len(results)} תוצאות נשמרו ל־{OUTPUT_FILE}")

if __name__ == "__main__":
    main()
