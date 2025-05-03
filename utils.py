from nltk.sentiment.vader import SentimentIntensityAnalyzer

def analyze_sentiment(text):
    analyzer = SentimentIntensityAnalyzer()
    return analyzer.polarity_scores(text)

def format_headlines(headlines):
    formatted = []
    for item in headlines:
        sentiment = item.get('sentiment', {})
        compound = sentiment.get('compound', 0)
        label = 'חיובי' if compound > 0 else 'שלילי'
        formatted.append(f"- {item['title']}\n→ ({compound:.2f}) {label}")
    return '\n'.join(formatted)
