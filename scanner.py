import requests
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer

nltk.download('vader_lexicon')

def fetch_news():
    # דוגמה של מקורות — ניתן לשדרג
    urls = [
        "https://www.cnbc.com/id/100003114/device/rss/rss.html",
        "https://www.marketwatch.com/rss/topstories",
    ]
    headlines = []
    for url in urls:
        try:
            r = requests.get(url)
            for line in r.text.splitlines():
                if "<title>" in line:
                    title = line.strip().replace("<title>", "").replace("</title>", "")
                    if title and "CDATA" not in title:
                        headlines.append(title)
        except Exception as e:
            print(f"Error fetching from {url}: {e}")
    return headlines

def analyze_sentiment(headlines):
    sia = SentimentIntensityAnalyzer()
    results = []
    for headline in headlines:
        score = sia.polarity_scores(headline)["compound"]
        results.append((headline, score))
    return results

def generate_report():
    headlines = fetch_news()
    analyzed = analyze_sentiment(headlines)
    if not analyzed:
        return "לא נמצאו כותרות לניתוח."
    report_lines = ["📊 דוח סנטימנט:"]
    for headline, score in analyzed[:10]:
        emoji = "🟢" if score > 0.2 else "🔴" if score < -0.2 else "🟡"
        report_lines.append(f"{emoji} {headline} (Score: {round(score, 2)})")
    return "\n".join(report_lines)
