from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from news_scraper import fetch_news_titles
from config import SYMBOLS

analyzer = SentimentIntensityAnalyzer()

def compute_sentiment_score(headlines):
    if not headlines:
        return 0.0
    scores = [analyzer.polarity_scores(title)["compound"] for title in headlines]
    return sum(scores) / len(scores)

def adjust_sentiment_score(symbol, avg_sentiment):
    adjustment_factors = {
        "AAPL": 1.0,
        "TSLA": 1.5,
        "NVDA": 1.3,
        "MSFT": 0.8,
        "META": 1.2
    }
    factor = adjustment_factors.get(symbol, 1.0)
    return avg_sentiment * factor

def analyze_sentiment_for_stocks(symbols):
    decisions = {}

    for symbol in symbols:
        print(f"🔍 מחשב סנטימנט עבור {symbol}...")

        headlines = fetch_news_titles(symbol)
        for title in headlines:
            score = analyzer.polarity_scores(title)["compound"]
            print(f"📰 '{title}' → {score:.4f}")

        avg_sentiment = compute_sentiment_score(headlines)
        adjusted_sentiment = adjust_sentiment_score(symbol, avg_sentiment)

        print(f"📊 ממוצע סנטימנט עבור {symbol}: {avg_sentiment:.3f} (מותאם: {adjusted_sentiment:.3f})")
        print(f"🧠 {symbol}: ציון סנטימנט מותאם: {adjusted_sentiment:.3f}")

        decision = "HOLD"
        if adjusted_sentiment >= 0.3:
            decision = "BUY"
        elif adjusted_sentiment <= -0.1:
            decision = "SELL"

        print(f"📊 {symbol}: החלטה: {decision}")
        decisions[symbol] = decision

    return decisions
