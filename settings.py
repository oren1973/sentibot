# settings.py – הגדרות מרכזיות לפרויקט Sentibot

import logging
import sys

# --- הגדרות Logger ---
def setup_logger(name='sentibot', level=logging.INFO): # שיניתי את שם הלוגר ברירת מחדל ל'sentibot'
    """
    Sets up a basic logger.
    """
    logger = logging.getLogger(name)
    
    if logger.hasHandlers():
        logger.handlers.clear()

    logger.setLevel(level)
    handler = logging.StreamHandler(sys.stdout) 
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - [%(module)s.%(funcName)s:%(lineno)d] - %(message)s') # פורמט משופר
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

# --- הגדרות מקורות חדשות (NEWS_SOURCES) ---
# זהו המילון הראשי ש- news_scraper.py ישתמש בו כדי לדעת אילו מקורות להפעיל
# ומה הפונקציה המתאימה לכל מקור.
NEWS_SOURCES_CONFIG = {
    "Yahoo Finance": {
        "enabled": True,
        "scraper_function_name": "get_yahoo_news", # שם הפונקציה שתקרא מ-yahoo_scraper.py
        "rss_url_template": "https://feeds.finance.yahoo.com/rss/2.0/headline?s={symbol}®ion=US&lang=en-US", # URL נשמר כאן
        "weight": 1.0
    },
    "CNBC": {
        "enabled": True,
        "scraper_function_name": "get_cnbc_titles",
        "rss_url_template": "https://www.cnbc.com/id/100003114/device/rss/rss.html", # RSS כללי, הסינון לפי מילות מפתח ב-scraper
        "weight": 1.2
    },
    "Investors.com": {
        "enabled": True, # הפעלתי לבדיקה
        "scraper_function_name": "get_investors_news",
        "rss_url_template": "https://research.investors.com/rss.aspx?kw={symbol}",
        "weight": 1.1
    },
    "MarketWatch": {
        "enabled": True,
        "scraper_function_name": "fetch_marketwatch_titles",
        "base_url_template": "https://www.marketwatch.com/investing/stock/{symbol_lower}", # ל-scraping ישיר
        "weight": 1.0
    }
    # Reddit מטופל כרגע בנפרד ב-main.py שלך. אם תרצה לשלבו כאן, נוסיף אותו.
}

# --- הגדרות Reddit (אם תרצה לרכז אותן כאן במקום משתני סביבה ישירות בקוד ה-scraper) ---
# REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
# REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
# REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "sentibot/0.2 by YourRedditUsername")
# REDDIT_SUBREDDITS = ["stocks", "wallstreetbets", "StockMarket", "investing"]
# REDDIT_LIMIT_PER_SUBREDDIT = 15
# REDDIT_COMMENTS_PER_POST = 3


# --- פרמטרים כלליים לאפליקציה ---
DEFAULT_MAX_HEADLINES_PER_SOURCE = 10
MIN_HEADLINE_LENGTH = 10 # אורך כותרת מינימלי כללי

# אפשר להוסיף כאן גם את ספי הסנטימנט אם תרצה שהם יהיו קונפיגורביליים
# SENTIMENT_THRESHOLD_BUY = 0.2
# SENTIMENT_THRESHOLD_SELL = -0.2
