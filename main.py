import os
import smtplib
from email.mime.text import MIMEText
from scanner import scan_market_and_generate_report
from recommender import generate_recommendations
from utils import analyze_sentiment, format_headlines
import nltk

nltk.download("vader_lexicon")

def send_email(subject, body):
    sender_email = os.getenv("EMAIL_USER")
    app_password = os.getenv("EMAIL_PASS")
    receiver_email = os.getenv("EMAIL_RECEIVER")

    print(f"DEBUG | SENDER_EMAIL: {sender_email}")
    print(f"DEBUG | APP_PASSWORD is None: {app_password is None}")
    print(f"DEBUG | RECEIVER_EMAIL: {receiver_email}")

    if not sender_email or not app_password or not receiver_email:
        print("❌ Missing email environment variables.")
        return

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = receiver_email

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, app_password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
        print("✅ נשלחה בהצלחה.")
    except Exception as e:
        print("❌ שגיאה בשליחת המייל:", e)

if __name__ == "__main__":
    print("✅ Sentibot starting...")
    headlines = scan_market_and_generate_report()
    print(f"DEBUG | headlines found: {len(headlines)}")

    if not headlines:
        print("⚠️ לא נשלח מייל – הדוח ריק או שגוי.")
        exit()

    # ניתוח סנטימנט
    sentiment_data = analyze_sentiment(headlines)
    formatted = format_headlines(sentiment_data)

    # המלצות מסחר
    recommendations = generate_recommendations(sentiment_data)
    rec_text = "\n\n📈 המלצות מסחר מבוססות סנטימנט:\n" + "\n".join(recommendations) if recommendations else "\n\n(לא נמצאו המלצות ברורות)"

    # גוף המייל
    body = "📰 כותרות חדשות מהשוק:\n" + formatted + rec_text

    send_email("Sentibot | דוח אוטומטי", body)
