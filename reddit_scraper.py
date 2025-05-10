# reddit_scraper.py
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

def get_reddit_posts(symbol, subreddits=["stocks", "wallstreetbets"], limit=20, comments_per_post=3):
    posts = []

    for sub in subreddits:
        try:
            for submission in reddit.subreddit(sub).search(symbol, sort='top', time_filter='week', limit=limit):
                if submission.stickied or submission.over_18:
                    continue

                # כותרת + גוף הפוסט
                content = submission.title
                if submission.selftext:
                    content += " " + submission.selftext.strip()

                posts.append(content)

                # תגובות מובילות
                submission.comments.replace_more(limit=0)
                top_comments = sorted(
                    submission.comments,
                    key=lambda c: getattr(c, "score", 0),
                    reverse=True
                )[:comments_per_post]

                for comment in top_comments:
                    comment_body = getattr(comment, "body", "").strip()
                    if comment_body:
                        posts.append(comment_body)

        except Exception as e:
            print(f"⚠️ שגיאה בשליפת פוסטים מ־r/{sub} עבור {symbol}: {e}")

    return posts
