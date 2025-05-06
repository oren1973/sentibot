from yahoo_scraper import fetch_yahoo_titles
from marketwatch_scraper import fetch_marketwatch_titles
from sentiment import analyze_sentiment

def analyze_sentiment_for_stocks(symbols):
    results = {}

    for symbol in symbols:
        print(f"🔍 מחשב סנטימנט עבור {symbol}...")

        headlines = []
        yahoo_titles = fetch_yahoo_titles(symbol)
        if yahoo_titles:
            headlines.extend(yahoo_titles)

        marketwatch_titles = fetch_marketwatch_titles(symbol)
        if marketwatch_titles:
            headlines.extend(marketwatch_titles)

        sentiment_scores = []
        for title in headlines:
            score = analyze_sentiment(title)
            print(f"📰 '{title}' → {score:.4f}")
            sentiment_scores.append(score)

        if sentiment_scores:
            avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
        else:
            avg_sentiment = 0.0

        if avg_sentiment > 0.15:
            decision = "BUY"
        elif avg_sentiment < -0.15:
            decision = "SELL"
        else:
            decision = "HOLD"

        print(f"📊 {symbol}: סנטימנט משוקלל: {avg_sentiment:.3f}")
        print(f"📊 {symbol}: החלטה: {decision}")
        results[symbol] = {"sentiment": avg_sentiment, "decision": decision}

    return results
