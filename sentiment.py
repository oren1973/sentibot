import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer

nltk.download("vader_lexicon")

analyzer = SentimentIntensityAnalyzer()

def analyze_sentiment():
    sample = [
        "GOOGL faces serious issues with AI trust",
        "AAPL posts record profits for Q1",
        "META is under FTC investigation again",
        "AMZN stock gets upgraded by analysts"
    ]
    results = []
    for headline in sample:
        score = analyzer.polarity_scores(headline)["compound"]
        results.append({
            "headline": headline,
            "sentiment": score
        })
    return results
