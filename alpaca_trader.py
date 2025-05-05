import os
import requests

API_KEY = os.getenv("ALPACA_API_KEY")
SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")
BASE_URL = os.getenv("ALPACA_PAPER_BASE_URL")

HEADERS = {
    "APCA-API-KEY-ID": API_KEY,
    "APCA-API-SECRET-KEY": SECRET_KEY
}


def submit_order(symbol, qty, side, type="market", time_in_force="gtc"):
    url = f"{BASE_URL}/v2/orders"
    order_data = {
        "symbol": symbol,
        "qty": qty,
        "side": side,
        "type": type,
        "time_in_force": time_in_force
    }
    response = requests.post(url, json=order_data, headers=HEADERS)
    if response.status_code != 200:
        print(f"❌ שגיאה בביצוע פקודה ל-{symbol}: {response.text}")
    else:
        print(f"✅ בוצעה פעולה {side.upper()} עבור {symbol} - כמות: {qty}")
