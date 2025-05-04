import os
from utils import analyze_sentiment, format_headlines
from scanner import scan_market_headlines
from alpaca_client import buy_stock
import smtplib
from email.mime.text import MIMEText

print("✅ Sentibot starting...")

# סריקה וניתוח
headlines = scan_market_headlines()
print(f"DEBUG | headlines found: {len(headlines)}")

sentiment_data = analyze_sentiment(headlines)
formatted = format_headlines(sentiment_data)

# החלטות קנייה פשוטות (מעל 0.3)
for item in sentiment_data:
    score = item["sentiment"]
    text = item["headline"]
    if score > 0.3:
        if "meta" in text.lower():
            buy_stock("META")
        elif "tesla" in text.lower():
            buy_stock("TSLA")
        elif "nvidia" in text.lower():
            buy_stock("NVDA")

# שליחת מייל
sender_email = os.environ.get("EMAIL_USER")
app_password = os.environ.get("EMAIL_PASS")
receiver_email = os.environ.get("EMAIL_RECEIVER")

if sender_email and app_password and receiver_email:
    msg = MIMEText(f"""דוח יומי Sentibot:

📊 ניתוח סנטימנט יומי:
{formatted}
""")
    msg["Subject"] = "Sentibot | דוח מסחר יומי"
    msg["From"] = sender_email
    msg["To"] = receiver_email

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, app_password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
        print("✅ נשלח מייל בהצלחה.")
    except Exception as e:
        print("❌ שליחת מייל נכשלה:", e)
else:
    print("⚠️ חסרים פרטי התחברות למייל.")
