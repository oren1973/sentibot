import requests
from bs4 import BeautifulSoup
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import nltk

# ודא שהמודול נשלף רק פעם אחת אם אתה מפעיל כרון כל שעה
nltk.download('vader_lexicon', quiet=True)

def scan_news():
    url = "https://www.bbc.com/news"
    response = requests.get(url)

    if response.status_code != 200:
        raise Exception(f"Failed to fetch BBC News: status code {response.status_code}")

    soup = BeautifulSoup(response.text, 'html.parser')
    headlines = [h.get_text().strip() for h in soup.find_all(['h3', 'h2']) if h.get_text().strip()]
    if not headlines:
        raise Exception("No headlines found on BBC News page.")

    analyzer = SentimentIntensityAnalyzer()
    results = []

    for headline in headlines:
        sentiment = analyzer.polarity_scores(headline)
        results.append({
            'headline': headline,
            'sentiment': sentiment
        })

    return results
