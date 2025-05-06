from yahoo_scraper import fetch_yahoo_titles
from cnbc_scraper import fetch_cnbc_titles
from sentiment import analyze_sentiment

def analyze_sentiment_for_stocks(stock_symbols):
    results = {}

    for symbol in stock_symbols:
        print(f"🔍 מחשב סנטימנט עבור {symbol}...")

        yahoo_titles = fetch_yahoo_titles(symbol)
        cnbc_titles = fetch_cnbc_titles(symbol)
        all_titles = [(t, 'Yahoo') for t in yahoo_titles] + [(t, 'CNBC') for t in cnbc_titles]

        if not all_titles:
            print(f"⚠️ לא נמצאו כותרות עבור {symbol}")
            results[symbol] = {"sentiment": 0, "decision": "HOLD"}
            continue

        weighted_scores = []
        for title, source in all_titles:
            score = analyze_sentiment(title)
            weight = 1.5 if source == 'Yahoo' else 1.0
            weighted_scores.append(score * weight)
            print(f"📰 '{title} [{source}]' → {score:.4f}")

        avg_sentiment = sum(weighted_scores) / len(weighted_scores)
        decision = "BUY" if avg_sentiment > 0.25 else "SELL" if avg_sentiment < -0.25 else "HOLD"

        print(f"📊 {symbol}: סנטימנט משוקלל: {avg_sentiment:.3f}")
        print(f"📊 {symbol}: החלטה: {decision}")
        results[symbol] = {"sentiment": avg_sentiment, "decision": decision}

    return results
