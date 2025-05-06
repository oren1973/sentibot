import re
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer

# הורדת משאבים נחוצים אם לא קיימים
try:
    nltk.data.find('sentiment/vader_lexicon.zip')
except LookupError:
    nltk.download('vader_lexicon')

# אתחול המנתח
analyzer = SentimentIntensityAnalyzer()

def clean_text(text):
    """
    מנקה טקסט מכותרות לצורך ניתוח סנטימנט:
    - מסיר HTML, לינקים, תווים מיוחדים וכפילויות רווחים
    """
    text = re.sub(r'<[^>]+>', '', text)         # HTML tags
    text = re.sub(r'http\S+', '', text)         # URLs
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text)  # Special characters
    text = re.sub(r'\s+', ' ', text)            # Extra spaces
    return text.strip()

def get_sentiment_score(text):
    """
    מחשב את סנטימנט הכותרת לפי מנתח VADER של NLTK.
    מחזיר ציון בין -1 ל-1 (שלילי עד חיובי)
    """
    cleaned = clean_text(text)
    score = analyzer.polarity_scores(cleaned)['compound']
    return round(score, 4)
