import smtplib
from email.mime.text import MIMEText
from datetime import datetime
from scanner import generate_report

import os

sender_email = os.getenv("SENDER_EMAIL")
app_password = os.getenv("APP_PASSWORD")
receiver_email = os.getenv("RECEIVER_EMAIL")

    body = f"""Sentibot - דוח רגשי
🕒 נשלח בתאריך: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{generate_report()}
"""

    msg = MIMEText(body)
    msg["Subject"] = "Sentibot | דוח רגשי מהחדשות"
    msg["From"] = sender_email
    msg["To"] = receiver_email

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, app_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())

if __name__ == "__main__":
    send_status_email()
