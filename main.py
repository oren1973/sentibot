# sentibot ver 1.3.1 22:31

from sentiment_analyzer import analyze_sentiment_for_stocks
from alpaca_trader import submit_order
import os

VERSION = "1.4"

STOCKS = ["AAPL", "TSLA", "NVDA", "MSFT", "META"]

THRESHOLD_BUY = 0.35
THRESHOLD_SELL = -0.2


def main():
    print(f"✨ Sentibot v{VERSION} – מופעל ✅")
    for symbol in STOCKS:
        sentiment_score, decision = analyze_sentiment_for_stocks(symbol)

        print(f"🧠 {symbol}: ציון סנטימנט: {sentiment_score:.3f}")
        print(f"📊 {symbol}: החלטה: {decision}")

        if decision == "BUY":
            submit_order(symbol=symbol, qty=1, side="buy")
        elif decision == "SELL":
            submit_order(symbol=symbol, qty=1, side="sell")


if __name__ == "__main__":
    main()
