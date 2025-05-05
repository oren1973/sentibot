import alpaca_trade_api as tradeapi
import os

# קריאה למשתני הסביבה
API_KEY = os.getenv("ALPACA_API_KEY")
API_SECRET = os.getenv("ALPACA_SECRET_KEY")
BASE_URL = "https://paper-api.alpaca.markets"

# יצירת מופע API
api = tradeapi.REST(API_KEY, API_SECRET, BASE_URL, api_version='v2')

def execute_trades(decisions):
    for symbol, action in decisions.items():
        if action == "BUY":
            print(f"✅ בוצעה פקודת BUY עבור {symbol}")
            api.submit_order(
                symbol=symbol,
                qty=1,
                side='buy',
                type='market',
                time_in_force='gtc'
            )
        elif action == "SELL":
            print(f"✅ בוצעה פקודת SELL עבור {symbol}")
            api.submit_order(
                symbol=symbol,
                qty=1,
                side='sell',
                type='market',
                time_in_force='gtc'
            )
        else:
            print(f"ℹ️ {symbol}: לא נדרשת פעולה ({action})")
