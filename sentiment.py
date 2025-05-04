# sentiment.py

from nltk.sentiment.vader import SentimentIntensityAnalyzer
import nltk

# נוודא שהמודול זמין
nltk.download('vader_lexicon')

analyzer = SentimentIntensityAnalyzer()

def analyze_sentiment(text):
    score = analyzer.polarity_scores(text)
    return score["compound"]
