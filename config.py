NEWS_SOURCES = {
    "CNBC": {
        "rss": "https://www.cnbc.com/id/100003114/device/rss/rss.html?query={symbol}",
        "type": "news_article",
        "weight": 1.0,
        "enabled": True,
    },
    "Reuters": {
        "rss": "https://www.reuters.com/site-search/?query={symbol}&sort=relevance&offset=0",
        "type": "news_article",
        "weight": 1.2,
        "enabled": True,
    },
    "Investors": {
        "rss": "https://www.investors.com/feed/?s={symbol}",
        "type": "news_article",
        "weight": 1.1,
        "enabled": True,
    },
    "Reddit": {
        "subreddits": ["wallstreetbets", "stocks", "investing", "options"],
        "type": "user_post",
        "weight": 0.8,
        "enabled": True,
    },
    "GeneralReuters": {
        "url": "https://feeds.reuters.com/reuters/businessNews",
        "type": "general_market",
        "weight": 1.0,
        "enabled": False,  # להפעיל בשלב מאוחר יותר
    }
}
