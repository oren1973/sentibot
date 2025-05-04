# 📄 trader.py
from config import TRADE_THRESHOLD, WHITELISTED_SYMBOLS

def execute_trades(sentiment_data):
    print("🔍 סימולציית מסחר:")
    for item in sentiment_data:
        text = item.get("headline", "")
        score = float(item.get("sentiment", 0.0))

        for symbol in WHITELISTED_SYMBOLS:
            if symbol.lower() in text.lower():
                if score > TRADE_THRESHOLD:
                    print(f"🟢 קנייה וירטואלית: {symbol} | ציון סנטימנט: {score:.2f}")
                elif score < -TRADE_THRESHOLD:
                    print(f"🔴 מכירה וירטואלית: {symbol} | ציון סנטימנט: {score:.2f}")
