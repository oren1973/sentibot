import feedparser
from config import NEWS_SOURCES
from sentiment_analyzer import analyze_sentiment

def fetch_news_titles(symbols):
    all_articles = []

    for source_name, source_data in NEWS_SOURCES.items():
        url = source_data["url"]
        weight = source_data["weight"]

        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                title = entry.title
                lower_title = title.lower()

                for symbol in symbols:
                    if symbol.lower() in lower_title:
                        sentiment = analyze_sentiment(title, source=source_name)
                        all_articles.append({
                            "symbol": symbol,
                            "title": title,
                            "sentiment": sentiment,
                            "source": source_name,
                            "weight": weight
                        })
        except Exception as e:
            print(f"Error fetching from {source_name}: {e}")

    return all_articles
