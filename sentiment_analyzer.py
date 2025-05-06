# sentiment_analyzer.py – גרסה משופרת עם סף SELL וסינון כותרות ניטרליות

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from news_scraper import fetch_news_titles
from config import SYMBOLS

analyzer = SentimentIntensityAnalyzer()

# גבולות לסינון כותרות אפורות
NEUTRAL_MIN = -0.05
NEUTRAL_MAX = 0.05

# סף מותאם ל-SELL חכם
SELL_THRESHOLD = -0.3
BUY_THRESHOLD = 0.3

def compute_sentiment_score(headlines):
    if not headlines:
        return 0.0
    filtered_scores = []
    for title in headlines:
        score = analyzer.polarity_scores(title)["compound"]
        if NEUTRAL_MIN <= score <= NEUTRAL_MAX:
            continue  # דילוג על כותרות אפורות
        filtered_scores.append(score)
    if not filtered_scores:
        return 0.0
    return sum(filtered_scores) / len(filtered_scores)

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

        print(f"📊 {symbol}: סנטימנט משוקלל: {adjusted_sentiment:.3f}")

        decision = "HOLD"
        if adjusted_sentiment >= BUY_THRESHOLD:
            decision = "BUY"
        elif adjusted_sentiment <= SELL_THRESHOLD:
            decision = "SELL"

        print(f"📊 {symbol}: החלטה: {decision}")
        decisions[symbol] = decision

    return decisions
