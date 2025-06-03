# settings.py – הגדרות מרכזיות לפרויקט Sentibot

import logging
import sys

# --- הגדרות Logger ---
def setup_logger(name='sentibot_logger', level=logging.INFO):
    """
    Sets up a basic logger.
    """
    logger = logging.getLogger(name)
    
    if logger.hasHandlers():
        logger.handlers.clear()

    logger.setLevel(level)
    handler = logging.StreamHandler(sys.stdout) 
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

# --- הגדרות מקורות חדשות (NEWS_SOURCES) ---
NEWS_SOURCES = {
    "Yahoo Finance": { # שיניתי את השם שיתאים למה שה-scraper מצפה
        "enabled": True,
        "rss": "https://feeds.finance.yahoo.com/rss/2.0/headline?s={symbol}®ion=US&lang=en-US",
        "weight": 1.0
        # "scraper_function_name": "get_yahoo_news" # אפשר להוסיף את זה אם רוצים
    },
    "CNBC": {
        "enabled": True,
        # ל-CNBC אין RSS ספציפי לסמל, ה-scraper שלו מטפל בזה
        "rss": None, # או להשאיר את ה-RSS הכללי: "https://www.cnbc.com/id/100003114/device/rss/rss.html"
        "weight": 1.2
        # "scraper_function_name": "get_cnbc_titles"
    },
    "Investors.com": { # שיניתי את השם שיתאים
        "enabled": True, # שיניתי ל-True כדי שנוכל לבדוק אותו
        "rss": "https://research.investors.com/rss.aspx?kw={symbol}", # תיקנתי את ה-URL לפי ה-scraper
        "weight": 1.1
        # "scraper_function_name": "get_investors_news"
    },
    "MarketWatch": { # הוספתי את MarketWatch
        "enabled": True,
        "rss": None, # MarketWatch משתמש ב-scraping ישיר, לא RSS
        "weight": 1.0
        # "scraper_function_name": "fetch_marketwatch_titles"
    },
    "Reddit": { # נשאר כפי שהיה, כי Reddit מטופל בנפרד ב-main.py כרגע
        "enabled": False, # אפשר להפעיל אם רוצים לשלב אותו דרך הלולאה הזו
        "weight": 1.5
        # Reddit לא משתמש ב-RSS, אז אין צורך ב-"rss" כאן
        # "scraper_function_name": "get_reddit_posts"
    }
}

# --- דוגמה לאתחול לוגר כללי לשימוש במודולים אחרים אם צריך ---
# main_app_logger = setup_logger("SentibotApp") # אפשר להשתמש בזה ב-main.py למשל

# --- פרמטרים נוספים אפשריים ---
# DEFAULT_MAX_HEADLINES_PER_SOURCE = 10
# DEFAULT_SENTIMENT_THRESHOLD_BUY = 0.2
# DEFAULT_SENTIMENT_THRESHOLD_SELL = -0.2
