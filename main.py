import os
import time
import smtplib
import pandas as pd
from datetime import datetime, date
from email.message import EmailMessage

from sentiment_analyzer import analyze_sentiment
from news_scraper import fetch_news_titles
from investors_scraper import get_investors_news
from reddit_scraper import get_reddit_posts
from recommender import make_recommendation
from alpaca_trader import trade_stock

# === הגדרת יוניברס חכם ===
from smart_universe import SYMBOLS_SMART as SYMBOLS

# === הגדרות כלליות ===
VOLUME_DIR = "/data"
LOG_NAME = "learning_log.csv"
DATE_STR = date.today().isoformat()
NOW = datetime.now().isoformat()

# === אחסון תוצאות זמניות ===
results = []

# === עיבוד לכל מניה ביוניברס ===
for symbol in SYMBOLS:
    news_yahoo = fetch_news_titles(symbol)
    news_investors = get_investors_news(symbol)
    reddit_posts = get_reddit_posts(symbol)
    
    all_titles = news_yahoo + news_investors + reddit_posts
    sentiment_score = analyze_sentiment(all_titles)

    recommendation = make_recommendation(sentiment_score, symbol)
    
    action = trade_stock(symbol, recommendation)
    
    results.append({
        "date": DATE_STR,
        "symbol": symbol,
        "sentiment": sentiment_score,
        "recommendation": recommendation,
        "action": action,
        "source_count": len(all_titles)
    })

# === שמירת תוצאות ללמידה ===
df = pd.DataFrame(results)
log_path = os.path.join(VOLUME_DIR, LOG_NAME)

if os.path.exists(log_path):
    df.to_csv(log_path, mode='a', header=False, index=False)
else:
    df.to_csv(log_path, index=False)

# === שליחת מייל עם קובץ ===
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
RECIPIENT = os.getenv("EMAIL_RECIPIENT")

msg = EmailMessage()
msg["Subject"] = f"Sentibot Report {DATE_STR}"
msg["From"] = EMAIL_ADDRESS
msg["To"] = RECIPIENT
msg.set_content(f"Sentibot finished run at {NOW}.\n{len(results)} stocks analyzed.")

with open(log_path, "rb") as f:
    msg.add_attachment(f.read(), maintype="application", subtype="octet-stream", filename=LOG_NAME)

with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
    smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
    smtp.send_message(msg)

print(f"Done. Report sent at {NOW}.")
