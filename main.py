from sentiment_analyzer import analyze_sentiment_for_stocks
from alpaca_trader import execute_trades
from config import SYMBOLS

def main():
    print("🚀 Sentibot v1.4 – מופעל ✅")

    decisions = analyze_sentiment_for_stocks(SYMBOLS)

    execute_trades(decisions)

if __name__ == "__main__":
    main()
