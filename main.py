# main.py – Sentibot v2.0: מסחר רגשי יומי עם תיעוד ודיווח
import os
import time
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

print("🚀 Sentibot v2.0 – מופעל ✅")

log_path = "learning_log.csv"
now = datetime.now().isoformat(timespec="seconds")

# קריאת לוג קיים או יצירת חדש
try:
    log_df = pd.read_csv(log_path)
    run_id = int(log_df["run_id"].max()) + 1
except:
    log_df = pd.DataFrame(columns=["run_id", "symbol", "datetime", "sentiment_avg", "decision", "previous_decision"])
    run_id = 1

new_rows = []
summary_lines = [f"📊 סיכום הרצה #{run_id} – {now}", ""]

for symbol in SYMBOLS:
    print(f"\n🔍 מנתח סנטימנט עבור {symbol}...")

    yahoo_articles = get_yahoo_news(symbol)
    investors_articles = get_investors_news(symbol)
    reddit_posts = get_reddit_posts(symbol)
    all_articles = yahoo_articles + investors_articles + reddit_posts

    if not all_articles:
        print(f"⚠️ לא נמצאו כתבות עבור {symbol}")
        continue

    sentiments = [analyze_sentiment(text) for text in all_articles]
    avg_sentiment = sum(sentiments) / len(sentiments)
    result = make_recommendation(avg_sentiment)
    decision = result["decision"].lower()

    prev = ""
    if symbol in log_df["symbol"].values:
        prev_entries = log_df[log_df["symbol"] == symbol].sort_values("datetime")
        if not prev_entries.empty:
            prev = prev_entries.iloc[-1]["decision"]

    print(f"📈 סנטימנט ממוצע: {avg_sentiment:.3f} → החלטה: {decision.upper()} (קודם: {prev})")

    new_rows.append({
        "run_id": run_id,
        "symbol": symbol,
        "datetime": now,
        "sentiment_avg": avg_sentiment,
        "decision": decision,
        "previous_decision": prev
    })

    if decision in ["buy", "sell"] and decision != str(prev).lower():
        trade_stock(symbol, decision)
        summary_lines.append(f"🔁 {symbol}: {decision.upper()} (סנטימנט: {avg_sentiment:.2f})")

    time.sleep(1)

# עדכון CSV
updated_log_df = pd.concat([log_df, pd.DataFrame(new_rows)], ignore_index=True)
updated_log_df.to_csv(log_path, index=False)
print(f"\n✅ נוצר הקובץ: {log_path}")

# שליחת מייל
EMAIL = os.getenv("EMAIL_USER")
PASS = os.getenv("EMAIL_PASS")
TO = os.getenv("EMAIL_RECEIVER")

try:
    msg = EmailMessage()
    summary_text = "\n".join(summary_lines) if len(summary_lines) > 1 else "לא בוצעו פעולות קנייה/מכירה בהרצה זו."
    msg.set_content(summary_text)
    msg["Subject"] = f"Sentibot • Run #{run_id} Summary"
    msg["From"] = EMAIL
    msg["To"] = TO

    with open(log_path, "rb") as f:
        msg.add_attachment(f.read(), maintype="text", subtype="csv", filename=log_path)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL, PASS)
        smtp.send_message(msg)

    print("📧 נשלח מייל סיכום עם קובץ CSV")
except Exception as e:
    print(f"❌ שגיאה בשליחת מייל: {e}")
