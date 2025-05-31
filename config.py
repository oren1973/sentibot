# config.py – מעודכן לשלב 2

NEWS_SOURCES = {
    "Reuters": {
        "url": "https://feeds.reuters.com/reuters/businessNews",
        "type": "news_article",
        "weight": 1.2
    },
    "CNBC": {
        "url": "https://www.cnbc.com/id/100003114/device/rss/rss.html",
        "type": "news_article",
        "weight": 1.0
    },
    "Reddit": {
        "subreddits": ["wallstreetbets", "stocks", "investing", "options"],
        "type": "user_post",
        "weight": 0.8
    }
}
