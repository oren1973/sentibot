import os
from alpaca_trade_api.rest import REST, TimeInForce

def trade_stock(symbol, decision):
    key = os.getenv("ALPACA_API_KEY")
    secret = os.getenv("ALPACA_SECRET_KEY")
    base_url = "https://paper-api.alpaca.markets"

    if not key or not secret:
        print("❌ מפתחות Alpaca חסרים")
        return

    api = REST(key, secret, base_url, api_version='v2')

    try:
        qty = 1
        if decision == "buy":
            api.submit_order(symbol=symbol, qty=qty, side="buy", type="market", time_in_force=TimeInForce.DAY)
            print(f"✅ נשלחה הוראת קניה ל־{symbol}")
        elif decision == "sell":
            api.submit_order(symbol=symbol, qty=qty, side="sell", type="market", time_in_force=TimeInForce.DAY)
            print(f"✅ נשלחה הוראת מכירה ל־{symbol}")
    except Exception as e:
        print(f"❌ שגיאה בשליחת הוראה ל־{symbol}: {e}")
