from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from news_scraper import fetch_news_titles
from alpaca_trader import execute_trade

analyzer = SentimentIntensityAnalyzer()

def analyze_sentiment_for_stocks(symbols):
    for symbol in symbols:
        print(f"🔍 מחשב סנטימנט עבור {symbol}...")
        titles = fetch_news_titles(symbol)

        scores = []
        for title in titles:
            sentiment = analyzer.polarity_scores(title)['compound']
            print(f"📰 '{title}' → {sentiment:.4f}")
            scores.append(sentiment)

        if scores:
            avg_score = sum(scores) / len(scores)
        else:
            avg_score = 0

        print(f"📊 ממוצע סנטימנט עבור {symbol}: {avg_score:.3f}")
        print(f"🧠 {symbol}: ציון סנטימנט: {avg_score:.3f}")

        # החלטה
        if avg_score > 0.3:
            decision = "BUY"
        elif avg_score < -0.3:
            decision = "SELL"
        else:
            decision = "HOLD"

        print(f"📊 {symbol}: החלטה: {decision}")

        if decision == "BUY":
            execute_trade(symbol, "buy")
        elif decision == "SELL":
            execute_trade(symbol, "sell")
