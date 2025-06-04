# settings.py – הגדרות מרכזיות לפרויקט Sentibot

import logging
import sys
import os # הוספתי os לייבוא אם תרצה להשתמש בו להגדרות Reddit בעתיד

# --- הגדרות Logger ---
def setup_logger(name='sentibot', level=logging.INFO):
    logger = logging.getLogger(name)
    
    if logger.hasHandlers():
        logger.handlers.clear()

    logger.setLevel(level)
    handler = logging.StreamHandler(sys.stdout) 
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - [%(module)s.%(funcName)s:%(lineno)d] - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

# --- הגדרות מקורות חדשות (NEWS_SOURCES_CONFIG) ---
NEWS_SOURCES_CONFIG = {
    "Yahoo Finance": {
        "enabled": True,
        "scraper_function_name": "get_yahoo_news", 
        "rss_url_template": "https://feeds.finance.yahoo.com/rss/2.0/headline?s={symbol}®ion=US&lang=en-US",
        "weight": 1.0
    },
    "CNBC": {
        "enabled": True,
        "scraper_function_name": "get_cnbc_titles",
        "rss_url_template": "https://www.cnbc.com/id/100003114/device/rss/rss.html",
        "weight": 1.2
    },
    "Investors.com": {
        "enabled": True, 
        "scraper_function_name": "get_investors_news",
        "rss_url_template": "https://research.investors.com/rss.aspx?kw={symbol}",
        "weight": 1.1
    },
    "MarketWatch": {
        "enabled": True, # שנה ל-False אם הוא עדיין נחסם, עד שנמצא פתרון
        "scraper_function_name": "fetch_marketwatch_titles",
        "base_url_template": "https://www.marketwatch.com/investing/stock/{symbol_lower}",
        "weight": 1.0
    }
}

# --- פרמטרים כלליים לאפליקציה ---
DEFAULT_MAX_HEADLINES_PER_SOURCE = 10 # מגבלה פר מקור ב-news_aggregator
MIN_HEADLINE_LENGTH = 10 # אורך כותרת מינימלי כללי
MAIN_MAX_TOTAL_HEADLINES = 50 # מגבלה כוללת של כותרות לעיבוד ב-main.py

# --- ספי החלטה (עבור recommender.py) ---
# אלו הספים המקוריים שלך, המניחים שהקלט ל-recommender הוא בסקאלת VADER compound (-1 עד +1)
# אם הקלט הוא ממוצע של ציונים משוקללים (עם טווח שונה), יש להתאים ספים אלו!
RECOMMENDER_THRESHOLD_BUY_ORIGINAL_SCALE = 0.2
RECOMMENDER_THRESHOLD_SELL_ORIGINAL_SCALE = -0.2
# אפשר להוסיף ספים לטווח הניטרלי אם רוצים לוגיקה מורכבת יותר ב-recommender:
# RECOMMENDER_NEUTRAL_LOWER_ORIGINAL_SCALE = -0.05 (סתם דוגמה)
# RECOMMENDER_NEUTRAL_UPPER_ORIGINAL_SCALE = 0.05  (סתם דוגמה)


# --- הגדרות Reddit (כרגע לא בשימוש פעיל בלולאת NEWS_SOURCES_CONFIG, אלא אם תשנה את main.py) ---
# אם תרצה להשתמש באלו, הסר את ההערות והגדר את משתני הסביבה המתאימים.
# REDDIT_ENABLED = os.getenv("REDDIT_ENABLED", "False").lower() in ('true', '1', 't')
# REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
# REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
# REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "Sentibot/0.3 by YourRedditUsername") # עדכן את שם המשתמש!
# REDDIT_SUBREDDITS_STR = os.getenv("REDDIT_SUBREDDITS_LIST", "stocks,wallstreetbets,StockMarket,investing")
# REDDIT_SUBREDDITS = [sub.strip() for sub in REDDIT_SUBREDDITS_STR.split(',')]
# try:
#     REDDIT_LIMIT_PER_SUBREDDIT = int(os.getenv("REDDIT_LIMIT_PER_SUBREDDIT", "15"))
#     REDDIT_COMMENTS_PER_POST = int(os.getenv("REDDIT_COMMENTS_PER_POST", "3"))
# except ValueError:
#     REDDIT_LIMIT_PER_SUBREDDIT = 15
#     REDDIT_COMMENTS_PER_POST = 3

# --- רשימת סימולי המניות למעקב (אם לא מיובא מ-smart_universe.py) ---
# אם אתה רוצה להגדיר את SYMBOLS כאן במקום בקובץ נפרד:
# SYMBOLS = ["AAPL", "TSLA", "NVDA", "MSFT", "META", "PFE", "XOM", "JPM", "DIS", "WMT"]
