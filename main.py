import smtplib
from email.mime.text import MIMEText
from datetime import datetime

def send_status_email():
    sender_email = "oren.waldman@gmail.com"
    app_password = "vpeifrchjagwvxci"
    receiver_email = "oren.waldman@gmail.com"

    body = f"""Sentibot - דוח שעתית
🕒 זמן שליחה: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
📈 מצב תיק: 100,000$ (סביבת סימולציה)
📊 עסקאות: טרם בוצעו
🧠 מניות במעקב: TSLA, NVDA, GME
"""

    msg = MIMEText(body)
    msg["Subject"] = "Sentibot | דוח אוטומטי"
    msg["From"] = sender_email
    msg["To"] = receiver_email

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, app_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())

if __name__ == "__main__":
    while True:
        send_status_email()
        time.sleep(3600)
