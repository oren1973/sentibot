# config.py – הגדרות כלליות של Sentibot

NEWS_SOURCES = {
    "Yahoo": {
        "enabled": True,
        "rss": "https://feeds.finance.yahoo.com/rss/2.0/headline?s={symbol}&region=US&lang=en-US"
    },
    "Investors": {
        "enabled": True,
        "rss": "https://www.investors.com/rss/stock-{symbol}.xml"
    }
}

# שאר הגדרות המייל וכו'
import os

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER")

# שימוש בקובץ חדש לפי תאריך
from datetime import date
LOG_NAME = f"learning_log_{date.today().isoformat()}.csv"
