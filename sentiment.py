import random

def get_sentiment_score(symbol):
    # כאן בעתיד נשתמש ב־VADER וכותרות אמיתיות
    score = round(random.uniform(-1, 1), 3)
    print(f"🔬 סנטימנט מזויף עבור {symbol}: {score}")
    return score
