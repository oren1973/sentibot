import os
import time
import smtplib
import pandas as pd
from datetime import datetime, date
from email.message import EmailMessage
from sentiment_analyzer import analyze_sentiment
from news_scraper import fetch_news_titles
from investors_scraper import get_investors_news
from recommender import make_recommendation
from alpaca_trader import trade_stock
from send_email import send_run_success_email

# --- הגדרות ---
SYMBOLS = ["AAPL", "TSLA", "NVDA", "MSFT", "META", "PFE", "XOM", "JPM", "DIS", "WMT"]
LOG_PATH = "learning_log_full.csv"
DATE_STR = date.today().isoformat()
NOW = datetime.now().isoformat()
RUN_ID = int(datetime.now().timestamp())  # מזהה ריצה ייחודי

# --- איסוף מידע וביצוע מסחר ---
run_log = []

for symbol in SYMBOLS:
    try:
        yahoo_titles = fetch_news_titles(symbol)
        investors_titles = get_investors_news(symbol)
        all_titles = yahoo_titles + investors_titles
        top_titles = sorted(all_titles, key=lambda x: x["weight"], reverse=True)[:10]

        sentiment_score = analyze_sentiment(top_titles)
        recommendation = make_recommendation(symbol, sentiment_score)
        trade_result = trade_stock(symbol, recommendation)

        run_log.append({
            "symbol": symbol,
            "datetime": NOW,
            "sentiment": sentiment_score,
            "recommendation": recommendation,
            "trade_result": trade_result,
            "source_count": len(all_titles),
        })

    except Exception as e:
        print(f"⚠️ שגיאה בטיפול ב־{symbol}: {e}")

# --- שמירת לוג מצטבר כולל run_id ---
log_df = pd.DataFrame(run_log)
log_df.insert(0, "run_id", RUN_ID)

if os.path.exists(LOG_PATH):
    existing_df = pd.read_csv(LOG_PATH)
    updated_df = pd.concat([existing_df, log_df], ignore_index=True)
else:
    updated_df = log_df

updated_df.to_csv(LOG_PATH, index=False)

# --- שליחת מייל ---
send_run_success_email(RUN_ID, attachment_path=LOG_PATH)
