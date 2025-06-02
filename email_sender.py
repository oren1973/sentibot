import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

def send_run_success_email(run_id, attachment_path=None):
    sender = os.getenv("EMAIL_USER")
    receiver = os.getenv("EMAIL_RECEIVER")
    password = os.getenv("EMAIL_PASS")

    subject = f"Sentibot הרצה מס' {run_id} הושלמה בהצלחה"
    body = f"הרצה מס' {run_id} של Sentibot הסתיימה בהצלחה ✅."

    # בניית הודעת מייל מרובת חלקים
    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = receiver
    msg["Subject"] = subject

    # גוף הטקסט
    msg.attach(MIMEText(body, "plain"))

    # צרוף קובץ (אם קיים)
    if attachment_path and os.path.exists(attachment_path):
        with open(attachment_path, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
        encoders.encode_base64(part)
        filename = os.path.basename(attachment_path)
        part.add_header("Content-Disposition", f"attachment; filename={filename}")
        msg.attach(part)
    else:
        print("⚠️ לא נמצא קובץ מצורף לשליחה." if attachment_path else "ℹ️ לא הוגדר קובץ לצרף.")

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, password)
            server.sendmail(sender, receiver, msg.as_string())
        print(f"📧 נשלח מייל אישור הרצה מס' {run_id} כולל קובץ")
    except Exception as e:
        print(f"❌ שגיאה בשליחת המייל: {e}")

def send_email_with_attachment(subject, body, attachment_path=None):
    sender = os.getenv("EMAIL_USER")
    receiver = os.getenv("EMAIL_RECEIVER")
    password = os.getenv("EMAIL_PASS")

    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = receiver
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    if attachment_path and os.path.exists(attachment_path):
        with open(attachment_path, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
        encoders.encode_base64(part)
        filename = os.path.basename(attachment_path)
        part.add_header("Content-Disposition", f"attachment; filename={filename}")
        msg.attach(part)
    else:
        print("⚠️ לא נמצא קובץ מצורף לשליחה." if attachment_path else "ℹ️ לא הוגדר קובץ לצרף.")

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, password)
            server.sendmail(sender, receiver, msg.as_string())
        print(f"📧 Email with attachment sent: {os.path.basename(attachment_path)}")
    except Exception as e:
        print(f"❌ שגיאה בשליחת המייל: {e}")
