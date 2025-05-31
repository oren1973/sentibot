# main.py – Sentibot with Smart Universe & Manual Override

import os
import sys
import time
from datetime import datetime, date
from sentiment_analyzer import analyze_sentiment
from news_scraper import fetch_news_titles
from investors_scraper import get_investors_news
from reddit_scraper import get_reddit_posts
from recommender import make_recommendation
from alpaca_trader import trade_stock
from smart_universe import get_smart_universe
from email_utils import send_learning_log

# --- הגדרות כלליות ---
DATE_STR = date.today().isoformat()
NOW = datetime.now()
SYMBOLS = get_smart_universe()
LOG_NAME = f"learning_log_{DATE_STR}.csv"
VOLUME_DIR = "/data"

# --- התנאי להפעלה רגילה / ידנית ---
FORCE = "force" in sys.argv
SCHEDULED_HOURS = [17, 20]  # הרץ בשעות אלה אם לא מופעל ידנית

if FORCE or NOW.hour in SCHEDULED_HOURS:
    print(f"▶ Running Sentibot at {NOW.isoformat()} (Force={FORCE})")

    all_news = []
    for symbol in SYMBOLS:
        titles = fetch_news_titles(symbol)
        reddit = get_reddit_posts(symbol)
        investors = get_investors_news(symbol)
        all_news.extend(titles + reddit + investors)

    sentiment_data = analyze_sentiment(all_news)
    recommendations = make_recommendation(sentiment_data)
    trade_stock(recommendations, log_file=LOG_NAME)

    send_learning_log(LOG_NAME)
    print(f"✅ Sentibot completed and emailed: {LOG_NAME}")

else:
    print(f"⏳ Not scheduled time ({NOW.hour}h) and no force override. Exiting.")
