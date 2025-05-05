import requests
from bs4 import BeautifulSoup
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import nltk

nltk.download('vader_lexicon', quiet=True)

analyzer = SentimentIntensityAnalyzer()

def get_sentiment_score(symbol):
    url = f"https://finance.yahoo.com/quote/{symbol}?p={symbol}"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.text, "html.parser")
        headlines = soup.find_all("h3")

        scores = []
        for tag in headlines:
            text = tag.get_text().strip()
            if len(text) > 10:
                score = analyzer.polarity_scores(text)["compound"]
                scores.append(score)
                print(f"📰 '{text}' → {score}")

        if scores:
            avg = round(sum(scores) / len(scores), 3)
            print(f"📊 ממוצע סנטימנט עבור {symbol}: {avg}")
            return avg
        else:
            print("⚠️ לא נמצאו כותרות תקפות.")
            return 0.0

    except Exception as e:
        print(f"❌ שגיאה בסריקת כותרות: {e}")
        return 0.0
