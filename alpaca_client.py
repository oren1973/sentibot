import os
import alpaca_trade_api as tradeapi

ALPACA_API_KEY = os.environ.get("ALPACA_API_KEY")
ALPACA_SECRET_KEY = os.environ.get("ALPACA_SECRET_KEY")
ALPACA_PAPER_BASE_URL = os.environ.get("ALPACA_PAPER_BASE_URL", "https://paper-api.alpaca.markets")

api = tradeapi.REST(ALPACA_API_KEY, ALPACA_SECRET_KEY, base_url=ALPACA_PAPER_BASE_URL)


def buy_stock(symbol, qty=1):
    try:
        print(f"📈 מנסה לרכוש מניה: {symbol} (כמות: {qty})")
        api.submit_order(
            symbol=symbol,
            qty=qty,
            side='buy',
            type='market',
            time_in_force='gtc'
        )
        print(f"✅ בוצעה קניית מניית {symbol}")
    except Exception as e:
        print(f"❌ שגיאה בקניית {symbol}:", e)


def sell_stock(symbol, qty=1):
    try:
        print(f"📉 מנסה למכור מניה: {symbol} (כמות: {qty})")
        api.submit_order(
            symbol=symbol,
            qty=qty,
            side='sell',
            type='market',
            time_in_force='gtc'
        )
        print(f"✅ בוצעה מכירת מניית {symbol}")
    except Exception as e:
        print(f"❌ שגיאה במכירת {symbol}:", e)
