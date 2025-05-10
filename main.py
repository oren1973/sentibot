# main.py – גרסה מתוקנת לשמירת log ושליחת פקודות לאלפאקה
import time
import os
import smtplib
import pandas as pd
from datetime import datetime
from email.message import EmailMessage

from sentiment_analyzer import analyze_sentiment
from yahoo_scraper import get_yahoo_news
from investors_scraper import get_investors_news
from reddit_scraper import get_reddit_posts
from recommender import make_recommendation
from alpaca_trader import trade_stock

SYMBOLS = ["AAPL", "TSLA", "NVDA", "MSFT", "META", "PFE", "XOM", "JPM", "DIS", "WMT"]

print("🚀 Sentibot v1.5 – מופעל ✅")

# שמור את הקובץ בתקיית הבסיס – לא ב־/tmp
log_path = "learning_log.csv"

try:
    log_df = pd.read_csv(log_path)
    run_id = int(log_df["run_id"].max()) + 1
except:
    log_df = pd.DataFrame(columns=["run_id", "symbol", "datetime", "sentiment_avg", "decision", "previous_decision"])
    run_id = 1

new_rows = []
now = datetime.now().isoformat(timespec="seconds")

for symbol in SYMBOLS:
    print(f"🔍 מחשב סנטימנט עבור {symbol}...")

    yahoo_articles = get_yahoo_news(symbol)
    investors_articles = get_investors_news(symbol)
    reddit_posts = get_reddit_posts(symbol)
    all_articles = yahoo_articles + investors_articles + reddit_posts

    if not all_articles:
        print(f"⚠️ לא נמצאו כתבות או פוסטים עבור {symbol}")
        continue

    sentiments = [analyze_sentiment(text) for text in all_articles]
    avg_sentiment = sum(sentiments) / len(sentiments)
    result = make_recommendation(avg_sentiment)

    print(f"📊 {symbol}: סנטימנט משוקלל סופי: {avg_sentiment:.3f}")
    print(f"📈 {symbol}: החלטה: {result['decision'].upper()}")

    prev = log_df[log_df["symbol"] == symbol].sort_values("datetime").iloc[-1]["decision"] if symbol in log_df["symbol"].values else ""
    print(f"🔁 {symbol}: החלטה קודמת: {prev}, החלטה נוכחית: {result['decision']}")

    new_rows.append({
        "run_id": run_id,
        "symbol": symbol,
        "datetime": now,
        "sentiment_avg": avg_sentiment,
        "decision": result["decision"],
        "previous_decision": prev
    })

    if result["decision"] in ["buy", "sell"] and result["decision"] != prev:
        trade_stock(symbol, result["decision"])

    time.sleep(1)

updated_log_df = pd.concat([log_df, pd.DataFrame(new_rows)], ignore_index=True)
updated_log_df.to_csv(log_path, index=False)

print(f"✅ הסתיים בהצלחה.")
print(f"📄 נוצר קובץ log: {log_path}")
print(f"📂 קבצים בתיקייה: {os.listdir('.')}")

# שליחת מייל
EMAIL = os.getenv("EMAIL_USER")
PASS = os.getenv("EMAIL_PASS")
TO = os.getenv("EMAIL_RECEIVER")

try:
    msg = EmailMessage()
    msg.set_content(f"הרצה מספר {run_id} הסתיימה בהצלחה.")
    msg["Subject"] = f"Sentibot Run {run_id} Success"
    msg["From"] = EMAIL
    msg["To"] = TO

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL, PASS)
        smtp.send_message(msg)

    print(f"📧 נשלח מייל לאחר הרצה מספר {run_id}")
except Exception as e:
    print(f"❌ שגיאה בשליחת מייל: {e}")
