import os
import alpaca_trade_api as tradeapi

API_KEY = os.getenv("ALPACA_API_KEY")
SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")
BASE_URL = "https://paper-api.alpaca.markets"

api = tradeapi.REST(API_KEY, SECRET_KEY, BASE_URL, api_version='v2')

def execute_trades(trade_instructions):
    """
    trade_instructions: list of dicts, each with keys:
    - symbol: str
    - side: 'buy' or 'sell'
    - qty: int
    """
    for trade in trade_instructions:
        symbol = trade['symbol']
        side = trade['side']
        qty = trade.get('qty', 1)
        try:
            print(f"➡️ מבצע פקודת {side.upper()} עבור {symbol}")
            api.submit_order(
                symbol=symbol,
                qty=qty,
                side=side,
                type='market',
                time_in_force='gtc'
            )
            print(f"✅ בוצעה פקודת {side.upper()} עבור {symbol}")
        except Exception as e:
            print(f"❌ שגיאה בביצוע פקודת {side.upper()} עבור {symbol}: {e}")
