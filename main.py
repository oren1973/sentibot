# main.py
import os
import feedparser
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from scanner import scan_market_headlines
from trader import execute_trades  # תוקן כאן הייבוא
from config import TRADE_THRESHOLD, WHITELISTED_SYMBOLS

# Fetch sentiment data
print("✅ Sentibot starting...")
sentiment_data = scan_market_headlines()
print(f"DEBUG | headlines found: {len(sentiment_data)}")

# Simulate trades
execute_trades(sentiment_data)

# Prepare and send email report
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER")

msg = MIMEMultipart("alternative")
msg["Subject"] = "📊 דו\"ח מסחר יומי | Sentibot"
msg["From"] = EMAIL_USER
msg["To"] = EMAIL_RECEIVER

html_content = "<h3>📈 ניתוח סנטימנט יומי:</h3><ul>"
for item in sentiment_data:
    headline = item["headline"]
    sentiment = item["sentiment"]
    label = "חיובי" if sentiment > 0.1 else "שלילי" if sentiment < -0.1 else "ניטרלי"
    color = "🟢" if label == "חיובי" else "🔴" if label == "שלילי" else "⚪"
    html_content += f"<li>{color} ({sentiment:+.2f}) {label}<br>{headline}</li>"
html_content += "</ul>"

msg.attach(MIMEText(html_content, "html"))

try:
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_USER, EMAIL_PASS)
        server.sendmail(EMAIL_USER, EMAIL_RECEIVER, msg.as_string())
    print("✅ נשלח מייל בהצלחה.")
except Exception as e:
    print("❌ שגיאה בשליחת מייל:", str(e))
