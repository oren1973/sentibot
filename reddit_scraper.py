import praw
import os
from datetime import datetime, timedelta

REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = "sentibot/0.1 by your_username"

reddit = praw.Reddit(
    client_id=REDDIT_CLIENT_ID,
    client_secret=REDDIT_CLIENT_SECRET,
    user_agent=REDDIT_USER_AGENT,
)

def get_reddit_posts(symbol, subreddits=["stocks", "wallstreetbets"], limit=20):
    posts = []
    for sub in subreddits:
        try:
            for submission in reddit.subreddit(sub).search(symbol, sort='top', time_filter='week', limit=limit):
                if not submission.stickied and not submission.over_18:
                    posts.append(submission.title)
        except Exception as e:
            print(f"⚠️ שגיאה בשליפת פוסטים מ־r/{sub} עבור {symbol}: {e}")
    return posts
