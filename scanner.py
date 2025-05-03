import requests
from bs4 import BeautifulSoup
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import nltk

nltk.download("vader_lexicon")

NEWS_SOURCES = [
    "https://www.marketwatch.com/",
    "https://www.cnbc.com/world/?region=world",
    "https://www.bloomberg.com/markets",
    "https://www.investors.com/",
    "https://www.fool.com/",
]

def extract_headlines(url):
    try:
        resp = requests.get(url, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        headlines = []

        for tag in soup.find_all(["h1", "h2", "h3", "a"]):
            text = tag.get_text(strip=True)
            if 30 > len(text) > 10:
                headlines.append(text)

        return headlines
    except Exception as e:
        print(f"❌ Error fetching {url}: {e}")
        return []

def analyze_sentiment(texts):
    sia = SentimentIntensityAnalyzer()
    results = []

    for text in texts:
        score = sia.polarity_scores(text)
        compound = score["compound"]
        if abs(compound) >= 0.4:
            sentiment = "חיובי" if compound > 0 else "שלילי"
            results.append((text, sentiment, compound))

    return results

def scan_market_and_generate_report():
    all_headlines = []
    for source in NEWS_SOURCES:
        headlines = extract_headlines(source)
        all_headlines.extend(headlines)

    print(f"DEBUG | headlines found: {len(all_headlines)}")
    if not all_headlines:
        return ""

    insights = analyze_sentiment(all_headlines)

    if not insights:
        return ""

    report = "📰 תובנות חדשותיות מהשוק:\n\n"
    for text, sentiment, score in insights[:10]:
        report += f"• {text}\n  → {sentiment} ({score:.2f})\n\n"

    return report.strip()
