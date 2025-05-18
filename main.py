# main.py – Sentibot v3.1: סוחר רגשי עם Volume, תיעוד מתקדם וסטטיסטיקות סנטימנט
import os
import time
import smtplib
import pandas as pd
from datetime import datetime, date
from email.message import EmailMessage
from sentiment_analyzer import analyze_sentiment
from news_scraper import fetch_news_titles
from reddit_scraper import get_reddit_posts
from investors_scraper import get_investors_news
from recommender import make_recommendation
from alpaca_trader import trade_stock
from collections import Counter

# --- הגדרות ---
SYMBOLS = ["AAPL", "TSLA", "NVDA", "MSFT", "META", "PFE", "XOM", "JPM", "DIS", "WMT"]
VOLUME_DIR = "/data"
LOG_NAME = "learning_log.csv"
DATE_STR = date.today().isoformat()
NOW = datetime.now().isoformat(timespec="seconds")
LOG_PATH = os.path.join(VOLUME_DIR, LOG_NAME)
DAILY_LOG_PATH = os.path.join(VOLUME_DIR, f"learning_log_{DATE_STR}.csv")

# --- הכנה ---
os.makedirs(VOLUME_DIR, exist_ok=True)

try:
    log_df = pd.read_csv(LOG_PATH)
    run_id = int(log_df["run_id"].max()) + 1
except Exception as e:
    print(f"[INFO] יצירת קובץ חדש: {LOG_PATH}")
    log_df = pd.DataFrame(columns=["run_id", "symbol", "datetime", "sentiment_avg", "decision", "previous_decision",
                                    "sentiment_std", "num_articles", "main_source"])
    run_id = 1

new_rows = []
summary_lines = [f"📊 סיכום הרצה #{run_id} – {NOW}", ""]

for symbol in SYMBOLS:
    print(f"\n🔍 ניתוח עבור {symbol}...")

    try:
        yahoo = fetch_news_titles(symbol)
        investors = get_investors_news(symbol)
        reddit = get_reddit_posts(symbol)
        all_articles = yahoo + investors + reddit
    except Exception as e:
        print(f"[ERROR] בעיה בשליפת כתבות עבור {symbol}: {e}")
        continue

    if not all_articles:
        print(f"⚠️ לא נמצאו כתבות עבור {symbol}")
        continue

    sentiments = [analyze_sentiment(text) for text in all_articles]
    avg_sentiment = sum(sentiments) / len(sentiments)
    sentiment_std = pd.Series(sentiments).std()
    num_articles = len(all_articles)

    # זיהוי מקור דומיננטי
    sources = ["Yahoo"] * len(yahoo) + ["Investors"] * len(investors) + ["Reddit"] * len(reddit)
    main_source = Counter(sources).most_common(1)[0][0] if sources else "unknown"

    result = make_recommendation(avg_sentiment)
    decision = result["decision"].lower()

    # החלטה קודמת
    prev = ""
    prev_entries = log_df[log_df["symbol"] == symbol].sort_values("datetime")
    if not prev_entries.empty:
        prev = prev_entries.iloc[-1]["decision"]

    print(f"📈 סנטימנט: {avg_sentiment:.3f} → החלטה: {decision.upper()} (קודם: {prev})")

    new_rows.append({
        "run_id": run_id,
        "symbol": symbol,
        "datetime": NOW,
        "sentiment_avg": avg_sentiment,
        "decision": decision,
        "previous_decision": prev,
        "sentiment_std": sentiment_std,
        "num_articles": num_articles,
        "main_source": main_source
    })

    if decision in ["buy", "sell"] and decision != str(prev).lower():
        trade_stock(symbol, decision)
        summary_lines.append(f"🔁 {symbol}: {decision.upper()} (סנטימנט: {avg_sentiment:.2f})")

    time.sleep(1)

# --- שמירת לוגים ---
try:
    updated_log_df = pd.concat([log_df, pd.DataFrame(new_rows)], ignore_index=True)
    updated_log_df.to_csv(LOG_PATH, index=False)
    updated_log_df.to_csv(DAILY_LOG_PATH, index=False)
    print(f"\n✅ נוצר הקובץ: {LOG_PATH}")
    print(f"🗂️ שמירה גם לקובץ יומי: {DAILY_LOG_PATH}")
except Exception as e:
    print(f"[ERROR] שגיאה בשמירת הלוגים: {e}")

# --- שליחת מייל ---
EMAIL = os.getenv("EMAIL_USER")
PASS = os.getenv("EMAIL_PASS")
TO = os.getenv("EMAIL_RECEIVER")

if EMAIL and PASS and TO:
    try:
        msg = EmailMessage()
        summary_text = "\n".join(summary_lines) if len(summary_lines) > 1 else "לא בוצעו פעולות קנייה/מכירה בהרצה זו."
        msg.set_content(summary_text)
        msg["Subject"] = f"Sentibot • Run #{run_id} Summary"
        msg["From"] = EMAIL
        msg["To"] = TO

        with open(LOG_PATH, "rb") as f:
            msg.add_attachment(f.read(), maintype="text", subtype="csv", filename=LOG_NAME)

        with open(DAILY_LOG_PATH, "rb") as f:
            msg.add_attachment(f.read(), maintype="text", subtype="csv", filename=os.path.basename(DAILY_LOG_PATH))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(EMAIL, PASS)
            smtp.send_message(msg)

        print("📧 מייל סיכום נשלח עם הקבצים")
    except Exception as e:
        print(f"❌ שגיאה בשליחת מייל: {e}")
else:
    print("📭 פרטי מייל חסרים – מייל לא נשלח")
