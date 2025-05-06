from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from news_scraper import fetch_news_titles
from alpaca_trader import execute_trades
from config import SYMBOLS

analyzer = SentimentIntensityAnalyzer()

# רגישות מותאמת למניה
SENSITIVITY_FACTORS = {
    "AAPL": 1.0,
    "TSLA": 1.5,
    "NVDA": 1.3,
    "MSFT": 0.8,
    "META": 1.2,
}

# סינון כותרות לא ממוקדות
def is_relevant(title, symbol):
    symbol_keywords = {
        "AAPL": ["Apple"],
        "TSLA": ["Tesla"],
        "NVDA": ["Nvidia"],
        "MSFT": ["Microsoft"],
        "META": ["Meta", "Facebook"],
    }
    return any(keyword.lower() in title.lower() for keyword in symbol_keywords.get(symbol, []))

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
        filtered = [h for h in headlines if is_relevant(h, symbol)]

        for title in filtered:
            score = analyzer.polarity_scores(title)["compound"]
            print(f"📰 '{title}' → {score:.4f}")

        avg_sentiment = compute_sentiment_score(filtered)
        factor = SENSITIVITY_FACTORS.get(symbol, 1.0)
        adjusted_sentiment = avg_sentiment * factor

        print(f"📊 ממוצע סנטימנט עבור {symbol}: {avg_sentiment:.3f} (מותאם: {adjusted_sentiment:.3f})")

        decision = "HOLD"
        if adjusted_sentiment >= 0.3:
            decision = "BUY"
        elif adjusted_sentiment <= -0.1:
            decision = "SELL"

        print(f"🧠 {symbol}: ציון סנטימנט מותאם: {adjusted_sentiment:.3f}")
        print(f"📊 {symbol}: החלטה: {decision}")
        decisions[symbol] = decision

    execute_trades(decisions)
    return decisions
