# reddit_scraper.py
import requests
from datetime import datetime, timedelta

def get_reddit_posts(symbol):
    """
    מחזיר רשימת טקסטים מתוך פוסטים שהוזכר בהם סימבול המניה ב־r/stocks ו־r/wallstreetbets
    מתוך שלושת הימים האחרונים.
    """
    base_url = "https://api.pushshift.io/reddit/search/submission/"
    end_time = int(datetime.utcnow().timestamp())
    start_time = int((datetime.utcnow() - timedelta(days=3)).timestamp())

    subreddits = ["stocks", "wallstreetbets"]
    posts = []

    for subreddit in subreddits:
        params = {
            "subreddit": subreddit,
            "q": symbol,
            "after": start_time,
            "before": end_time,
            "size": 50,
            "sort": "desc",
            "sort_type": "score"
        }
        try:
            response = requests.get(base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json().get("data", [])
            for post in data:
                title = post.get("title", "")
                selftext = post.get("selftext", "")
                full_text = f"{title}. {selftext}".strip()
                if full_text:
                    posts.append(full_text)
        except Exception as e:
            print(f"⚠️ שגיאה בשליפת פוסטים מ־r/{subreddit} עבור {symbol}: {e}")

    return posts
