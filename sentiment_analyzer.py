# sentiment_analyzer.py – גרסה עם מנוע משוקלל
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from news_scraper import fetch_news_items
from config import SYMBOLS, SOURCE_WEIGHTS, LAMBDA_DECAY
from sentibot_weighted_sentiment import calculate_weighted_sentiment, Headline
from datetime import datetime

analyzer = SentimentIntensityAnalyzer()

def analyze_sentiment_for_stocks(symbols):
    decisions = {}

    for symbol in symbols:
        print(f"🔍 מחשב סנטימנט עבור {symbol}...")

        raw_items = fetch_news_items(symbol)
        headlines = []

        for item in raw_items:
            title = item['title']
            score = analyzer.polarity_scores(title)["compound"]
            print(f"📰 '{title}' → {score:.4f}")

            headline = Headline(
                symbol=symbol,
                sentiment_score=score,
                source=item.get("source", "Unknown"),
                published_at=item.get("published_at", datetime.now())
            )
            headlines.append(headline)

        weighted_scores = calculate_weighted_sentiment(headlines)
        sentiment = weighted_scores.get(symbol, 0.0)

        print(f"📊 {symbol}: סנטימנט משוקלל: {sentiment:.3f}")

        decision = "HOLD"
        if sentiment >= 0.3:
            decision = "BUY"
        elif sentiment <= -0.1:
            decision = "SELL"

        print(f"📊 {symbol}: החלטה: {decision}")
        decisions[symbol] = decision

    return decisions
