import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import os
import requests

# קבלת משתנים מהמערכת (Render)
ALPACA_API_KEY = os.environ.get("ALPACA_API_KEY")
ALPACA_SECRET_KEY = os.environ.get("ALPACA_SECRET_KEY")
BASE_URL = os.environ.get("ALPACA_BASE_URL")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
APP_PASSWORD = os.environ.get("APP_PASSWORD")
RECEIVER_EMAIL = os.environ.get("RECEIVER_EMAIL")

def get_account_data():
    headers = {
        "APCA-API-KEY-ID": ALPACA_API_KEY,
        "APCA-API-SECRET-KEY": ALPACA_SECRET_KEY
    }
    account_url = f"{BASE_URL}/v2/account"
    positions_url = f"{BASE_URL}/v2/positions"

    account = requests.get(account_url, headers=headers).json()
    positions = requests.get(positions_url, headers=headers).json()

    return account, positions

def build_email(account, positions):
    equity = account.get("equity", "N/A")
    cash = account.get("cash", "N/A")
    buying_power = account.get("buying_power", "N/A")

    position_lines = []
    if isinstance(positions, list) and positions:
        for p in positions:
            line = f"- {p['symbol']}: {p['qty']} יח', רווח: {p['unrealized_pl']} דולר"
            position_lines.append(line)
    else:
        position_lines.append("אין פוזיציות פתוחות כרגע.")

    positions_text = "\n".join(position_lines)

    body = f"""Sentibot - דוח שעתית
🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

💰 Equity: ${equity}
💵 Cash: ${cash}
📈 Buying Power: ${buying_power}

📊 פוזיציות פתוחות:
{positions_text}
"""
    return body

def send_status_email(body):
    msg = MIMEText(body)
    msg["Subject"] = "Sentibot | דוח אוטומטי"
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECEIVER_EMAIL

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(SENDER_EMAIL, APP_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())

if __name__ == "__main__":
    account_data, positions_data = get_account_data()
    report = build_email(account_data, positions_data)
    send_status_email(report)
