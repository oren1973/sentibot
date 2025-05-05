# sentibot ver 1.3.1 22:31
import os
from sentiment_analyzer import analyze_sentiment
from alpaca_trade_api.rest import REST

# הגדרת משתני סביבה
API_KEY = os.getenv("ALPACA_API_KEY")
API_SECRET = os.getenv("ALPACA_SECRET_KEY")
BASE_URL = os.getenv("ALPACA_PAPER_BASE_URL")

# התחברות ל-Alpaca
api = REST(API_KEY, API_SECRET, BASE_URL)

# רשימת מניות לניתוח
SYMBOLS = ["AAPL", "TSLA", "NVDA", "MSFT", "META"]
BUY_THRESHOLD = 0.25
SELL_THRESHOLD = -0.25

# שליחת פקודת מסחר
def place_order(symbol, side, qty=1):
    try:
        api.submit_order(
            symbol=symbol,
            qty=qty,
            side=side,
            type='market',
            time_in_force='gtc'
        )
        print(f"✅ פקודת {side.upper()} הוזנה עבור {symbol}")
    except Exception as e:
        print(f"❌ שגיאה בביצוע פקודת {side} ל-{symbol}: {e}")

# הרצת ניתוח סנטימנט וקבלת החלטה
def main():
    print("🚀 Sentibot v1.4 – מופעל ✅")
    for symbol in SYMBOLS:
        print(f"🔍 מחשב סנטימנט עבור {symbol}...")
        score = analyze_sentiment(symbol)
        print(f"🧠 {symbol}: ציון סנטימנט: {score:.3f}")

        if score >= BUY_THRESHOLD:
            decision = "BUY"
            place_order(symbol, "buy")
        elif score <= SELL_THRESHOLD:
            decision = "SELL"
            place_order(symbol, "sell")
        else:
            decision = "HOLD"
        
        print(f"📊 {symbol}: החלטה: {decision}\n")

if __name__ == "__main__":
    main()
