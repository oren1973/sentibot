import os
import smtplib
from email.mime.text import MIMEText
from utils import analyze_sentiment, format_headlines
from scanner import scan_market_and_generate_report

print("✅ Sentibot starting...")

# סריקה וניתוח סנטימנט
headlines = scan_market_and_generate_report()
print(f"DEBUG | headlines found: {len(headlines)}")

sentiment_data = []
for headline in headlines:
    sentiment = analyze_sentiment(headline)
    sentiment_data.append({'title': headline, 'sentiment': sentiment})

formatted = format_headlines(sentiment_data)

# בדיקת משתני סביבה
sender_email = os.environ.get("EMAIL_USER")
app_password = os.environ.get("EMAIL_PASS")
receiver_email = os.environ.get("EMAIL_RECEIVER")

if not all([sender_email, app_password, receiver_email]):
    print("❌ Missing email environment variables.")
else:
    # שליחת מייל
    body = f"""חדשות מהשוק:

{formatted}
"""
    msg = MIMEText(body)
    msg["Subject"] = "Sentibot | דוח אוטומטי"
    msg["From"] = sender_email
    msg["To"] = receiver_email

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, app_password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
        print("✅ נשלח מייל בהצלחה.")
    except Exception as e:
        print("❌ שליחת מייל נכשלה:", e)
