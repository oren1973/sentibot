import smtplib
import os
from email.mime.text import MIMEText

def send_run_success_email(run_id):
    sender = os.getenv("EMAIL_USER")
    receiver = os.getenv("EMAIL_RECEIVER")
    password = os.getenv("EMAIL_PASS")

    subject = f"Sentibot הרצה מס' {run_id} הושלמה בהצלחה"
    body = f"הרצה מס' {run_id} של Sentibot הסתיימה בהצלחה ✅."

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = receiver

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, password)
            server.sendmail(sender, receiver, msg.as_string())
        print(f"📧 נשלח מייל אישור הרצה מס' {run_id}")
    except Exception as e:
        print(f"❌ שגיאה בשליחת המייל: {e}")
