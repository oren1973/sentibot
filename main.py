# 📄 main.py
from scanner import scan_market_headlines
from utils import analyze_sentiment, format_headlines
from trader import execute_trades
import os

print("✅ Sentibot starting...")

# 1. סריקה
headlines = scan_market_headlines()
print(f"DEBUG | headlines found: {len(headlines)}")

# 2. ניתוח סנטימנט
sentiment_data = analyze_sentiment(headlines)

# 3. עיצוב הדוח
formatted = format_headlines(sentiment_data)

# 4. מסחר (שלב MVP: הדמיה בלבד)
execute_trades(sentiment_data)

# 5. שליחת אימייל (אם נדרש)
sender_email = os.environ.get("EMAIL_USER")
app_password = os.environ.get("EMAIL_PASS")
receiver_email = os.environ.get("EMAIL_RECEIVER")

if sender_email and app_password and receiver_email:
    from email.mime.text import MIMEText
    import smtplib

    msg = MIMEText(f"""דו"ח יומי של Sentibot:

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
    print("⚠️ לא נשלח מייל – חסר מידע התחברות או כתובת יעד.")
