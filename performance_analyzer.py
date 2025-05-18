import os
import pandas as pd
from datetime import datetime, timedelta
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
import smtplib
from email.message import EmailMessage

# יצירת לקוח Alpaca
client = StockHistoricalDataClient(
    os.getenv("ALPACA_API_KEY"),
    os.getenv("ALPACA_SECRET_KEY")
)

# פרמטרים
DAYS_FORWARD = 3
SUCCESS_THRESHOLD = 0.5  # אחוז עלייה שנחשב הצלחה

# נתיבים
log_path = "/data/learning_log.csv"
output_path = "/data/performance_results.csv"

# קריאת לוג ההרצות
log_df = pd.read_csv(log_path)
log_df['datetime'] = pd.to_datetime(log_df['datetime'], errors='coerce')

# סינון פעולות BUY בלבד
buy_df = log_df[log_df['decision'].str.lower() == 'buy'].copy()
buy_df['result'] = None
buy_df['buy_price'] = None
buy_df['future_price'] = None
buy_df['change_pct'] = None

# פונקציה לשליפת נתוני שוק
def evaluate_trade(symbol, buy_time):
    start = buy_time.date()
    end = start + timedelta(days=DAYS_FORWARD + 1)

    request = StockBarsRequest(
        symbol_or_symbols=symbol,
        start=start.isoformat(),
        end=end.isoformat(),
        timeframe=TimeFrame.Day
    )

    try:
        bars = client.get_stock_bars(request).df
        if symbol not in bars.index.get_level_values(0):
            return None, None, None

        df = bars.loc[symbol]
        buy_price = df.iloc[0]['open']
        future_price = df.iloc[DAYS_FORWARD]['close']
        change_pct = (future_price - buy_price) / buy_price * 100
        return buy_price, future_price, round(change_pct, 2)
    except:
        return None, None, None

# ניתוח כל פעולת BUY
for idx, row in buy_df.iterrows():
    symbol = row['symbol']
    dt = row['datetime']
    buy_price, future_price, change_pct = evaluate_trade(symbol, dt)

    buy_df.at[idx, 'buy_price'] = buy_price
    buy_df.at[idx, 'future_price'] = future_price
    buy_df.at[idx, 'change_pct'] = change_pct

    if change_pct is not None:
        buy_df.at[idx, 'result'] = 'success' if change_pct > SUCCESS_THRESHOLD else 'fail'

# שמירה לקובץ
buy_df.to_csv(output_path, index=False)

# סיכום
summary = buy_df['result'].value_counts(normalize=True) * 100
avg_change = buy_df['change_pct'].mean()

summary_text = "\n=== סיכום ביצועי BUY ===\n"
summary_text += summary.to_string()
summary_text += f"\n\nממוצע שינוי באחוזים: {avg_change:.2f}%"

print(summary_text)

# שליחת מייל סיכום
EMAIL = os.getenv("EMAIL_USER")
PASS = os.getenv("EMAIL_PASS")
TO = os.getenv("EMAIL_RECEIVER")

if EMAIL and PASS and TO:
    try:
        msg = EmailMessage()
        msg.set_content(summary_text)
        msg["Subject"] = "Sentibot • ניתוח ביצועים"
        msg["From"] = EMAIL
        msg["To"] = TO

        with open(output_path, "rb") as f:
            msg.add_attachment(f.read(), maintype="text", subtype="csv", filename="performance_results.csv")

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(EMAIL, PASS)
            smtp.send_message(msg)

        print("📧 מייל סיכום נשלח עם הקובץ")
    except Exception as e:
        print(f"❌ שגיאה בשליחת מייל: {e}")
else:
    print("📭 פרטי מייל חסרים – מייל לא נשלח")
