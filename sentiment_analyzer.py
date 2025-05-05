from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from news_scraper import fetch_news_titles
from alpaca_trader import execute_trades
from config import SYMBOLS

analyzer = SentimentIntensityAnalyzer()

def compute_sentiment_score(headlines):
    if not headlines:
        return 0.0
    scores = [analyzer.polarity_scores(title)["compound"] for title in headlines]
    return sum(scores) / len(scores)

def analyze_sentiment_for_stocks(symbols):
    decisions = {}

    for symbol in symbols:
        print(f"🔍 מחשב סנטימנט עבור {symbol}...")

        headlines = fetch_news_titles(symbol)
        for title in headlines:
            score = analyzer.polarity_scores(title)["compound"]
            print(f"📰 '{title}' → {score:.4f}")

        avg_sentiment = compute_sentiment_score(headlines)
        print(f"📊 ממוצע סנטימנט עבור {symbol}: {avg_sentiment:.3f}")

        decision = "HOLD"
        if avg_sentiment >= 0.3:
            decision = "BUY"
        elif avg_sentiment <= -0.3:
            decision = "SELL"

        print(f"🧠 {symbol}: ציון סנטימנט: {avg_sentiment:.3f}")
        print(f"📊 {symbol}: החלטה: {decision}")
        decisions[symbol] = decision

    execute_trades(decisions)
    return decisions
