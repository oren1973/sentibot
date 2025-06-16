# settings.py – הגדרות מרכזיות לפרויקט Sentibot

import logging
import sys
import os

# --- הגדרות Logger ---
def setup_logger(name='sentibot', level=logging.INFO):
    logger = logging.getLogger(name)
    if logger.hasHandlers(): # מנקה handlers קיימים כדי למנוע כפילות בהודעות אם הפונקציה נקראת מספר פעמים
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
        # השינוי כאן: הסרת ®ion=US מה-URL
        "rss_url_template": "https://feeds.finance.yahoo.com/rss/2.0/headline?s={symbol}&lang=en-US", 
        "weight": 1.0 
    },
    "CNBC": {
        "enabled": True,
        "scraper_function_name": "get_cnbc_titles",
        "rss_url_template": "https://www.cnbc.com/id/100003114/device/rss/rss.html",
        "weight": 1.2,
        "max_feed_items_to_scan_cnbc": 100 # הוספתי פרמטר זה, ערך ברירת המחדל בפונקציה הוא 50
    },
    "Investors.com": {
        "enabled": False, 
        "scraper_function_name": "get_investors_news",
        "rss_url_template": "https://research.investors.com/rss.aspx?kw={symbol}",
        "weight": 1.1
    },
    "MarketWatch": {
        "enabled": False, 
        "scraper_function_name": "fetch_marketwatch_titles",
        "base_url_template": "https://www.marketwatch.com/investing/stock/{symbol_lower}",
        "weight": 1.0
    },
    "Reddit_Post": {
        "enabled": False, 
        "scraper_function_name": None, 
        "weight": 1.0  
    },
    "Reddit_Comment": {
        "enabled": False, 
        "scraper_function_name": None, 
        "weight": 0.8  
    }
}

# --- פרמטרים כלליים לאפליקציה ---
DEFAULT_MAX_HEADLINES_PER_SOURCE = 10 
MIN_HEADLINE_LENGTH = 10 
MAIN_MAX_TOTAL_HEADLINES = 50 

# --- ספי החלטה (עבור recommender.py) ---
RECOMMENDER_THRESHOLD_BUY = 0.70
RECOMMENDER_THRESHOLD_SELL = 0.40 

# --- הגדרות Reddit (לקריאה על ידי reddit_scraper.py ו-main.py) ---
REDDIT_ENABLED = os.getenv("REDDIT_ENABLED", "True").lower() in ('true', '1', 't') 
REDDIT_SUBREDDITS_STR = os.getenv("REDDIT_SUBREDDITS_LIST", "stocks,wallstreetbets,StockMarket,investing,options") 
REDDIT_SUBREDDITS = [sub.strip() for sub in REDDIT_SUBREDDITS_STR.split(',')]
try:
    REDDIT_LIMIT_PER_SUBREDDIT = int(os.getenv("REDDIT_LIMIT_PER_SUBREDDIT", "10"))
    REDDIT_COMMENTS_PER_POST = int(os.getenv("REDDIT_COMMENTS_PER_POST", "2"))
except ValueError:
    # שימוש בלוגר שהוגדר למעלה, או לוגר זמני אם זה קורה לפני הגדרת הלוגר הראשי
    # במקרה זה, הפונקציה setup_logger כבר הוגדרה למעלה, אז אפשר להשתמש בה.
    # אם יש חשש שזה רץ לפני שהלוגר הראשי מאותחל, אפשר להשתמש בלוגר מובנה של פייתון.
    settings_init_logger = setup_logger("settings_init", level=logging.WARNING) # שימוש בפונקציה שלנו
    settings_init_logger.warning("Could not parse Reddit limit/comments parameters from environment variables. Using defaults: Limit=10, Comments=2.")
    REDDIT_LIMIT_PER_SUBREDDIT = 10
    REDDIT_COMMENTS_PER_POST = 2

# --- הגדרות Alpaca ---
ALPACA_BASE_URL = "https://paper-api.alpaca.markets" 
TRADE_QUANTITY = 1 

# --- נתיבים לקבצי לוג ודוחות ---
# ודא ששם התיקייה תואם למה ש-Render יוצר או מאפשר לך ליצור
# אם Render משתמש ב- /data כ-persistent storage, עדיף להשתמש בנתיב מוחלט
# לדוגמה, אם Render מקצה /data ואתה רוצה תיקייה בשם sentibot_data שם:
# REPORTS_BASE_DIR = os.getenv("PERSISTENT_STORAGE_DIR", "/data/sentibot_data") 
# כרגע נשאיר את זה יחסי, אבל שים לב שזה יכול להיות המקור לבעיית "קובץ לא נמצא"
REPORTS_BASE_DIR = "sentibot_reports" 

REPORTS_OUTPUT_DIR = REPORTS_BASE_DIR 
LEARNING_LOG_CSV_PATH = os.path.join(REPORTS_OUTPUT_DIR, "learning_log_cumulative.csv")

# --- רשימת סימולי המניות למעקב (מיובאת מ-smart_universe.py ב-main.py) ---
# המשתנה SYMBOLS עצמו מיובא מקובץ smart_universe.py בתוך main.py
