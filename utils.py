import smtplib
from email.mime.text import MIMEText
import os
from datetime import datetime

def send_email(subject, body):
    sender_email = os.getenv("SENDER_EMAIL")
    app_password = os.getenv("APP_PASSWORD")
    receiver_email = os.getenv("RECEIVER_EMAIL")

    if not sender_email or not app_password or not receiver_email:
        print("❌ Missing email environment variables.")
        return

    body = f"""{body}

🕒 נשלח בתאריך: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
📤 על ידי Sentibot | מצב: סימולציה
"""

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = receiver_email

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, app_password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
    except Exception as e:
        print(f"❌ Email send failed: {e}")
