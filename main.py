import os
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import nltk
from scanner import scan_market_headlines
from trader import execute_trade
from utils import analyze_sentiment, log_message

nltk.download('vader_lexicon')

def send_email(subject, body):
    msg = MIMEMultipart()
    msg['From'] = os.environ['EMAIL_USER']
    msg['To'] = os.environ['EMAIL_RECEIVER']
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(os.environ['EMAIL_USER'], os.environ['EMAIL_PASS'])
        server.sendmail(msg['From'], msg['To'], msg.as_string())

def main():
    log_message("Sentibot starting...")
    headlines = scan_market_headlines()
    log_message(f"DEBUG | headlines found: {len(headlines)}")

    summary_lines = []
    for symbol, articles in headlines.items():
        scores = [analyze_sentiment(text) for text in articles]
        if not scores:
            continue
        avg_score = round(sum(scores) / len(scores), 2)
        if avg_score >= 0.5:
            result = f"🟢 קנייה אוטומטית: {symbol} | ציון סנטימנט: {avg_score}"
            success = execute_trade(symbol, qty=1)
            if not success:
                result += " ❌ שגיאה בביצוע קנייה"
        else:
            result = f"🔵 ניטרלי: {symbol} | ציון סנטימנט: {avg_score}"
        log_message(result)
        summary_lines.append(f"→ ({avg_score}) {symbol}")

    body = "📊 ניתוח סנטימנט יומי:\n\n" + "\n".join(summary_lines)
    send_email("דוח מסחר יומי | Sentibot", body)
    log_message("✅ שלח מייל בהצלחה.")

if __name__ == "__main__":
    main()
