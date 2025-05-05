import feedparser
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

def fetch_news_titles(symbol):
    url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={symbol}&region=US&lang=en-US"
    feed = feedparser.parse(url)
    return [entry.title for entry in feed.entries[:10]]

def analyze_sentiment(text):
    analyzer = SentimentIntensityAnalyzer()
    score = analyzer.polarity_scores(text)["compound"]
    return score

def analyze_sentiment_for_stocks(symbols):
    decisions = {}
    for symbol in symbols:
        print(f"🔍 מחשב סנטימנט עבור {symbol}...")
        titles = fetch_news_titles(symbol)
        scores = []
        for title in titles:
            score = analyze_sentiment(title)
            print(f"📰 '{title}' → {score:.4f}")
            scores.append(score)

        if scores:
            avg_sentiment = sum(scores) / len(scores)
        else:
            avg_sentiment = 0.0

        print(f"📊 ממוצע סנטימנט עבור {symbol}: {avg_sentiment:.3f}")
        print(f"🧠 {symbol}: ציון סנטימנט: {avg_sentiment:.3f}")

        if avg_sentiment > 0.25:
            decision = "BUY"
        elif avg_sentiment < -0.25:
            decision = "SELL"
        else:
            decision = "HOLD"

        print(f"📊 {symbol}: החלטה: {decision}")
        decisions[symbol] = decision
    return decisions
