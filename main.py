import os
from scanner import scan_market_and_generate_report
from utils import send_email

if __name__ == "__main__":
    print("✅ Sentibot starting...")

    body = scan_market_and_generate_report()

    if not body.strip():
        print("⚠️ לא נשלח מייל – הדוח ריק או שגוי.")
    else:
        send_email("Sentibot | דוח אוטומטי", body)
        print("✅ נשלח מייל בהצלחה.")
