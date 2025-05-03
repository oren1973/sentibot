from scanner import scan_market_and_generate_report
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import os

def send_status_email(body):
    sender_email = os.getenv("EMAIL_USER")
    app_password = os.getenv("EMAIL_PASS")
    receiver_email = os.getenv("EMAIL_RECEIVER")

    # Debugging (optional – remove for production)
    print("DEBUG | SENDER_EMAIL:", sender_email)
    print("DEBUG | APP_PASSWORD is None:", app_password is None)
    print("DEBUG | RECEIVER_EMAIL:", receiver_email)

    msg = MIMEText(body)
    msg["Subject"] = "Sentibot | דוח אוטומטי"
    msg["From"] = sender_email
    msg["To"] = receiver_email

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, app_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())

if __name__ == "__main__":
    report = scan_market_and_generate_report()
    if report:  # נשלח מייל רק אם יש תוכן
        send_status_email(report)
