from config import TRADE_THRESHOLD, WHITELISTED_SYMBOLS
from alpaca_trade_api.rest import REST, TimeFrame
import os

ALPACA_API_KEY = os.getenv("ALPACA_API_KEY")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")
ALPACA_BASE_URL = os.getenv("ALPACA_PAPER_BASE_URL", "https://paper-api.alpaca.markets")

api = REST(ALPACA_API_KEY, ALPACA_SECRET_KEY, base_url=ALPACA_BASE_URL)

def execute_trades(sentiment_data):
    print("🔍 סימולציית מסחר:")

    for item in sentiment_data:
        if not isinstance(item, dict):
            print(f"⚠️ דילוג על פריט לא חוקי: {item}")
            continue

        text = item.get("headline", "")
        score = float(item.get("sentiment", 0.0))

        for symbol in WHITELISTED_SYMBOLS:
            if symbol.lower() in text.lower():
                if score > TRADE_THRESHOLD:
                    print(f"🟢 קנייה וירטואלית: {symbol} | ציון סנטימנט: {score:.2f}")
                    try:
                        api.submit_order(
                            symbol=symbol,
                            qty=1,
                            side="buy",
                            type="market",
                            time_in_force="gtc"
                        )
                        print(f"✅ נשלחה פקודת קנייה ל-Alpaca (Paper): {symbol}")
                    except Exception as e:
                        print(f"❌ שגיאה בשליחת פקודת קנייה: {e}")

                elif score < -TRADE_THRESHOLD:
                    print(f"🔴 מכירה וירטואלית: {symbol} | ציון סנטימנט: {score:.2f}")
                    try:
                        api.submit_order(
                            symbol=symbol,
                            qty=1,
                            side="sell",
                            type="market",
                            time_in_force="gtc"
                        )
                        print(f"✅ נשלחה פקודת מכירה ל-Alpaca (Paper): {symbol}")
                    except Exception as e:
                        print(f"❌ שגיאה בשליחת פקודת מכירה: {e}")
