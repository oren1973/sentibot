import re
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer

# ודא שה-lexicon זמין
nltk.download('vader_lexicon')

analyzer = SentimentIntensityAnalyzer()

def clean_text(text):
    """
    מנקה טקסט לפני ניתוח סנטימנט:
    - הסרת HTML, סימנים מיוחדים ולינקים
    - שמירת תווים בסיסיים בלבד
    """
    text = re.sub(r'<.*?>', '', text)
    text = re.sub(r'http\S+', '', text)
    text = re.sub(r'[^a-zA-Z0-9\s.,!?\'\"-]', '', text)
    return text.strip()

def get_sentiment_score(text):
    """
    מחשב ציון סנטימנט בין -1 ל־1.
    """
    cleaned = clean_text(text)
    score = analyzer.polarity_scores(cleaned)
    return score['compound']

# Alias for backward compatibility
analyze_sentiment = get_sentiment_score
