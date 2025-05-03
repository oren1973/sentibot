from scanner import scan_market_and_generate_report
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import os

def send_email(subject, body):
    sender_email = os.getenv("SENDER_EMAIL")
    app_password = os.getenv("APP_PASSWORD")
    receiver_email = os.getenv("RECEIVER_EMAIL")

    # הדפסת דיאגנוסטיקה
    print("DEBUG | SENDER_EMAIL:", sender_email)
    print("DEBUG | APP_PASSWORD is None:", app_password is None)
    print("DEBUG | RECEIVER_EMAIL:", receiver_email)

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = receiver_email

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, app_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())

if __name__ == "__main__":
    report = scan_market_and_generate_report()
    if report:  # שלח רק אם יש תוכן
        send_email("Sentibot | דוח אוטומטי", report)
