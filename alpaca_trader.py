import os
import alpaca_trade_api as tradeapi

ALPACA_API_KEY = os.getenv("ALPACA_API_KEY")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")
BASE_URL = "https://paper-api.alpaca.markets"

api = tradeapi.REST(ALPACA_API_KEY, ALPACA_SECRET_KEY, BASE_URL, api_version='v2')

def execute_trades(decisions):
    for symbol, decision in decisions.items():
        if decision == "BUY":
            place_order(symbol, qty=1, side="buy")
        elif decision == "SELL":
            place_order(symbol, qty=1, side="sell")

def place_order(symbol, qty, side):
    try:
        api.submit_order(
            symbol=symbol,
            qty=qty,
            side=side,
            type="market",
            time_in_force="gtc"
        )
        print(f"✅ בוצעה פקודת {side.upper()} עבור {symbol}")
    except Exception as e:
        print(f"❌ שגיאה בביצוע פקודת {side} עבור {symbol}: {e}")
