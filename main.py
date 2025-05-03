import os
import smtplib
from email.mime.text import MIMEText
from scanner import scan_news

def send_email(subject, body):
    sender_email = os.getenv("SENDER_EMAIL")
    app_password = os.getenv("APP_PASSWORD")
    receiver_email = os.getenv("RECEIVER_EMAIL")

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = receiver_email

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, app_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())

if __name__ == "__main__":
    report = scan_news()
    if report:
        body = f"""Sentibot - דוח רגשי\n\n{report}"""
        send_email("Sentibot | דוח אוטומטי", body)
