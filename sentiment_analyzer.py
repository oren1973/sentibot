from yahoo_scraper import fetch_yahoo_titles
from investors_scraper import fetch_investors_titles
from sentiment import analyze_sentiment
from investors_scraper import get_investors_news

def analyze_sentiment_for_stocks(symbols):
    results = {}

    for symbol in symbols:
        print(f"🔍 מחשב סנטימנט עבור {symbol}...")

        headlines = []

        # Fetch from Yahoo
        yahoo_titles = fetch_yahoo_titles(symbol)
        headlines.extend([f"{title} [Yahoo]" for title in yahoo_titles])

        # Fetch from Investors.com
        investors_titles = fetch_investors_titles(symbol)
        headlines.extend([f"{title} [Investors]" for title in investors_titles])

        if not headlines:
            print(f"⚠️ לא נמצאו כותרות עבור {symbol}")
            results[symbol] = {"sentiment": 0.0, "decision": "HOLD"}
            continue

        # Analyze each title
        sentiments = [analyze_sentiment(title) for title in headlines]

        # Calculate weighted average
        weighted_sentiment = sum(sentiments) / len(sentiments)

        # Decision logic
        if weighted_sentiment > 0.2:
            decision = "BUY"
        elif weighted_sentiment < -0.2:
            decision = "SELL"
        else:
            decision = "HOLD"

        results[symbol] = {"sentiment": weighted_sentiment, "decision": decision}

        # Print summary
        for title, score in zip(headlines, sentiments):
            print(f"📰 '{title}' → {score:.4f}")
        print(f"📊 {symbol}: סנטימנט משוקלל: {weighted_sentiment:.3f}")
        print(f"📊 {symbol}: החלטה: {decision}")

    return results
