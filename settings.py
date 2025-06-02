# settings.py – מקור הגדרת NEWS_SOURCES בלבד

NEWS_SOURCES = {
    "Yahoo": {
        "enabled": True,
        "rss": "https://feeds.finance.yahoo.com/rss/2.0/headline?s={symbol}&region=US&lang=en-US",
        "weight": 1.0
    },
    "CNBC": {
        "enabled": True,
        "rss": "https://www.cnbc.com/id/100003114/device/rss/rss.html",
        "weight": 1.2
    },
    "Investors": {
        "enabled": False,
        "rss": "https://www.investors.com/rss/stock-{symbol}.xml",
        "weight": 1.1
    },
    "Reddit": {
        "enabled": False,
        "weight": 1.5
    }
}
